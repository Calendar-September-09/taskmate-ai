"""Client Jira Cloud thật: REST API v3 + Agile API 1.0.

Dùng httpx async, Basic auth (email + API token).
"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from typing import Any

import httpx

from core.settings import Settings
from mcp_server.adf import adf_to_text, markdown_to_adf
from mcp_server.errors import JiraAuthError, JiraError, JiraNotFound, JiraRateLimited, redact
from mcp_server.models import (
    ChangelogEntry,
    ChangelogItem,
    CreatedIssue,
    FieldMeta,
    Issue,
    JiraField,
    Member,
    Project,
    Sprint,
    Transition,
    mask_email,
)

SleepFunc = Callable[[float], Awaitable[None]]

MAX_RETRIES = 3
BACKOFF_BASE = 0.5
MAX_BACKOFF = 30.0
PAGE_SIZE = 50

BASE_ISSUE_FIELDS = [
    "summary",
    "status",
    "issuetype",
    "assignee",
    "priority",
    "duedate",
    "created",
    "updated",
    "labels",
    "parent",
    "issuelinks",
    "description",
]


def parse_jira_datetime(value: str | None) -> datetime | None:
    """Jira trả '2026-11-02T09:00:00.000+0700' hoặc '...Z'; chuyển sang datetime có múi giờ."""
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%f%z")


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


class JiraClient:
    """Truy cập Jira Cloud. Không bao giờ log hay đưa token vào thông điệp lỗi."""

    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        *,
        story_points_field: str = "customfield_10016",
        sprint_field: str = "customfield_10020",
        flagged_field: str = "customfield_10021",
        timeout: float = 10.0,
        max_retries: int = MAX_RETRIES,
        sleep: SleepFunc = asyncio.sleep,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._secrets = [api_token]
        self._story_points_field = story_points_field
        self._sprint_field = sprint_field
        self._flagged_field = flagged_field
        self._max_retries = max_retries
        self._sleep = sleep
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            auth=httpx.BasicAuth(email, api_token),
            timeout=httpx.Timeout(timeout, connect=5.0),
            headers={"Accept": "application/json"},
        )

    @classmethod
    def from_settings(cls, settings: Settings, **kwargs: Any) -> "JiraClient":
        return cls(
            settings.jira_base_url,
            settings.jira_email,
            settings.jira_api_token.get_secret_value(),
            story_points_field=settings.jira_story_points_field,
            sprint_field=settings.jira_sprint_field,
            flagged_field=settings.jira_flagged_field,
            **kwargs,
        )

    def __repr__(self) -> str:
        return f"JiraClient(base_url={self._base_url!r})"

    async def __aenter__(self) -> "JiraClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()

    # ------------------------------------------------------------------ HTTP

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        idempotent: bool = True,
    ) -> Any:
        """Gọi Jira có retry. 429 luôn thử lại; 5xx và lỗi mạng chỉ thử lại khi idempotent."""
        attempt = 0
        while True:
            try:
                response = await self._http.request(method, path, params=params, json=json_body)
            except httpx.TransportError as exc:
                if idempotent and attempt < self._max_retries:
                    await self._sleep(self._backoff(attempt))
                    attempt += 1
                    continue
                raise JiraError(
                    f"Không kết nối được tới Jira ({type(exc).__name__}). "
                    "Kiểm tra mạng và JIRA_BASE_URL."
                ) from None

            status = response.status_code
            retryable = status == 429 or (status >= 500 and idempotent)
            if retryable and attempt < self._max_retries:
                await self._sleep(self._backoff(attempt, response.headers.get("Retry-After")))
                attempt += 1
                continue
            if status >= 400:
                raise self._to_error(response)
            if status == 204 or not response.content:
                return None
            return response.json()

    def _backoff(self, attempt: int, retry_after: str | None = None) -> float:
        if retry_after:
            try:
                return min(float(retry_after), MAX_BACKOFF)
            except ValueError:
                pass
        return min(BACKOFF_BASE * (2**attempt), MAX_BACKOFF)

    def _to_error(self, response: httpx.Response) -> JiraError:
        status = response.status_code
        detail = self._error_detail(response)
        suffix = f" Chi tiết: {detail}" if detail else ""
        if status in (401, 403):
            message = (
                "Không xác thực được với Jira hoặc không đủ quyền "
                f"(HTTP {status}). Kiểm tra JIRA_EMAIL, JIRA_API_TOKEN và quyền của tài khoản."
            )
            return JiraAuthError(redact(message, self._secrets), status)
        if status == 404:
            message = f"Không tìm thấy tài nguyên trên Jira (HTTP 404).{suffix}"
            return JiraNotFound(redact(message, self._secrets), status)
        if status == 429:
            message = "Jira đang giới hạn tần suất gọi (HTTP 429), đã thử lại nhưng chưa được."
            return JiraRateLimited(message, status)
        message = f"Jira trả lỗi HTTP {status}.{suffix}"
        return JiraError(redact(message, self._secrets), status)

    def _error_detail(self, response: httpx.Response) -> str:
        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError):
            return ""
        if not isinstance(data, dict):
            return ""
        parts = [str(m) for m in data.get("errorMessages", [])]
        errors = data.get("errors") or {}
        if isinstance(errors, dict):
            parts.extend(f"{k}: {v}" for k, v in errors.items())
        return redact("; ".join(parts)[:500], self._secrets)

    async def _paged_values(self, path: str, params: dict[str, Any] | None = None) -> list[Any]:
        """Phân trang kiểu startAt/maxResults/isLast/values.

        Dùng cho project search, board, sprint, changelog.
        """
        results: list[Any] = []
        start = 0
        while True:
            page_params = {**(params or {}), "startAt": start, "maxResults": PAGE_SIZE}
            data = await self._request("GET", path, params=page_params)
            values = data.get("values", [])
            results.extend(values)
            if data.get("isLast", True) or not values:
                return results
            start += len(values)

    # ----------------------------------------------------------------- Đọc

    async def list_projects(self) -> list[Project]:
        values = await self._paged_values("/rest/api/3/project/search", {"expand": "issueTypes"})
        return [
            Project(
                key=p["key"],
                id=str(p["id"]),
                name=p["name"],
                issue_types=[t["name"] for t in p.get("issueTypes", [])],
            )
            for p in values
        ]

    async def list_members(self, project_key: str, query: str | None = None) -> list[Member]:
        params: dict[str, Any] = {"project": project_key, "maxResults": 100}
        if query:
            params["query"] = query
        users = await self._request("GET", "/rest/api/3/user/assignable/search", params=params)
        return [
            Member(
                account_id=u["accountId"],
                display_name=u.get("displayName", ""),
                email_masked=mask_email(u.get("emailAddress")),
                active=u.get("active", True),
            )
            for u in users or []
        ]

    async def list_sprints(self, project_key: str, state: str | None = None) -> list[Sprint]:
        boards = await self._paged_values(
            "/rest/agile/1.0/board", {"projectKeyOrId": project_key, "type": "scrum"}
        )
        sprints: dict[int, Sprint] = {}
        params = {"state": state} if state else None
        for board in boards:
            for raw in await self._paged_values(
                f"/rest/agile/1.0/board/{board['id']}/sprint", params
            ):
                if raw["id"] not in sprints:
                    sprints[raw["id"]] = Sprint(
                        id=raw["id"],
                        name=raw["name"],
                        state=raw["state"],
                        goal=raw.get("goal") or None,
                        start_date=parse_jira_datetime(raw.get("startDate")),
                        end_date=parse_jira_datetime(raw.get("endDate")),
                        complete_date=parse_jira_datetime(raw.get("completeDate")),
                        board_id=raw.get("originBoardId", board["id"]),
                    )
        return list(sprints.values())

    def _issue_fields(self, fields: list[str] | None) -> list[str]:
        base = fields or BASE_ISSUE_FIELDS
        extra = [self._story_points_field, self._sprint_field, self._flagged_field]
        return list(dict.fromkeys([*base, *extra]))

    async def search_issues(
        self, jql: str, fields: list[str] | None = None, max_results: int = 50
    ) -> list[Issue]:
        """Tìm issue bằng JQL qua POST /rest/api/3/search/jql (phân trang nextPageToken)."""
        issues: list[Issue] = []
        token: str | None = None
        while len(issues) < max_results:
            body: dict[str, Any] = {
                "jql": jql,
                "fields": self._issue_fields(fields),
                "maxResults": min(PAGE_SIZE, max_results - len(issues)),
            }
            if token:
                body["nextPageToken"] = token
            data = await self._request("POST", "/rest/api/3/search/jql", json_body=body)
            issues.extend(self.issue_from_raw(raw) for raw in data.get("issues", []))
            token = data.get("nextPageToken")
            if not token or data.get("isLast") is True:
                break
        return issues[:max_results]

    async def get_issue(self, key: str) -> Issue:
        raw = await self._request(
            "GET", f"/rest/api/3/issue/{key}", params={"fields": ",".join(self._issue_fields(None))}
        )
        return self.issue_from_raw(raw)

    async def get_issue_changelog(self, key: str) -> list[ChangelogEntry]:
        values = await self._paged_values(f"/rest/api/3/issue/{key}/changelog")
        return [
            ChangelogEntry(
                id=str(h["id"]),
                created=parse_jira_datetime(h["created"]),
                author_id=(h.get("author") or {}).get("accountId"),
                items=[
                    ChangelogItem(
                        field=i.get("field", ""),
                        from_value=i.get("fromString"),
                        to_value=i.get("toString"),
                    )
                    for i in h.get("items", [])
                ],
            )
            for h in values
        ]

    async def get_create_meta(self, project_key: str, issue_type: str) -> list[FieldMeta]:
        base = f"/rest/api/3/issue/createmeta/{project_key}/issuetypes"
        data = await self._request("GET", base, params={"maxResults": 100})
        types = data.get("issueTypes") or data.get("values") or []
        match = next((t for t in types if t["name"].lower() == issue_type.lower()), None)
        if match is None:
            names = ", ".join(t["name"] for t in types)
            raise JiraNotFound(
                f"Project {project_key} không có loại issue '{issue_type}'. "
                f"Các loại hiện có: {names}.",
                404,
            )
        fields: list[dict[str, Any]] = []
        start = 0
        while True:
            page = await self._request(
                "GET", f"{base}/{match['id']}", params={"startAt": start, "maxResults": PAGE_SIZE}
            )
            values = page.get("fields") or page.get("values") or []
            fields.extend(values)
            start += len(values)
            if not values or start >= page.get("total", start):
                break
        return [
            FieldMeta(
                field_id=f.get("fieldId") or f.get("key", ""),
                name=f.get("name", ""),
                required=bool(f.get("required")),
                has_default=bool(f.get("hasDefaultValue")),
                allowed_values=[
                    str(v.get("name") or v.get("value") or v.get("id"))
                    for v in f.get("allowedValues", [])
                ],
            )
            for f in fields
        ]

    async def get_transitions(self, key: str) -> list[Transition]:
        data = await self._request("GET", f"/rest/api/3/issue/{key}/transitions")
        return [
            Transition(id=str(t["id"]), name=t["name"], to_status=t.get("to", {}).get("name", ""))
            for t in data.get("transitions", [])
        ]

    async def list_fields(self) -> list[JiraField]:
        data = await self._request("GET", "/rest/api/3/field")
        return [
            JiraField(id=f["id"], name=f.get("name", ""), custom=bool(f.get("custom")))
            for f in data or []
        ]

    # ----------------------------------------------------------------- Ghi

    async def create_issue(self, fields: dict[str, Any]) -> CreatedIssue:
        """Tạo issue. Không retry khi 5xx/lỗi mạng để tránh tạo trùng.

        Không kiểm tra approval_token ở đây: MCP tool phải kiểm tra trước khi gọi (design 4.3).
        """
        payload = dict(fields)
        if isinstance(payload.get("description"), str):
            payload["description"] = markdown_to_adf(payload["description"])
        data = await self._request(
            "POST", "/rest/api/3/issue", json_body={"fields": payload}, idempotent=False
        )
        key = data["key"]
        return CreatedIssue(key=key, id=str(data["id"]), url=f"{self._base_url}/browse/{key}")

    # ---------------------------------------------------------- Chuẩn hóa

    def issue_from_raw(self, raw: dict[str, Any]) -> Issue:
        f = raw.get("fields", {})
        status = f.get("status") or {}
        assignee = f.get("assignee") or {}
        points = f.get(self._story_points_field)
        sprints = f.get(self._sprint_field) or []
        blocked_by = [
            link["inwardIssue"]["key"]
            for link in f.get("issuelinks", [])
            if "inwardIssue" in link
            and (link.get("type", {}).get("inward", "").lower() == "is blocked by")
        ]
        description = f.get("description")
        return Issue(
            key=raw["key"],
            id=str(raw.get("id", "")),
            summary=f.get("summary", ""),
            issue_type=(f.get("issuetype") or {}).get("name", ""),
            status=status.get("name", ""),
            status_category=(status.get("statusCategory") or {}).get("key", "new"),
            assignee_id=assignee.get("accountId"),
            assignee_name=assignee.get("displayName"),
            priority=(f.get("priority") or {}).get("name"),
            story_points=float(points) if points is not None else None,
            due_date=_parse_date(f.get("duedate")),
            created=parse_jira_datetime(f.get("created")),
            updated=parse_jira_datetime(f.get("updated")),
            sprint_ids=[s["id"] for s in sprints if isinstance(s, dict) and "id" in s],
            flagged=bool(f.get(self._flagged_field)),
            blocked_by=blocked_by,
            labels=f.get("labels", []),
            parent_key=(f.get("parent") or {}).get("key"),
            description_text=adf_to_text(description).strip() or None if description else None,
        )
