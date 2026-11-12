"""Jira giả lập trong bộ nhớ, cùng interface với JiraClient.

Dữ liệu từ evals/fixtures/jira_mock.json.
"""

import copy
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from domain.text import normalize_vi
from mcp_server.adf import adf_to_text, markdown_to_adf
from mcp_server.errors import JiraError, JiraNotFound
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

DEFAULT_FIXTURE = Path(__file__).resolve().parent.parent / "evals" / "fixtures" / "jira_mock.json"
JQL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

_AND = re.compile(r"\s+AND\s+", re.IGNORECASE)
_ORDER_BY = re.compile(r"\s+ORDER\s+BY\s+.*$", re.IGNORECASE)
_VALUE = r"\"(?P<q>[^\"]*)\"|'(?P<s>[^']*)'|(?P<w>[\w.-]+)"
_STATUS_CATEGORY_NAMES = {"to do": "new", "in progress": "indeterminate", "done": "done"}


def _value(match: re.Match[str]) -> str:
    for group in ("q", "s", "w"):
        if match.group(group) is not None:
            return match.group(group)
    return ""


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class MockJira:
    """Jira giả lập. Mỗi instance có bản sao dữ liệu riêng, nên test độc lập với nhau."""

    def __init__(
        self,
        fixture_path: Path | str = DEFAULT_FIXTURE,
        *,
        story_points_field: str = "customfield_10016",
        sprint_field: str = "customfield_10020",
        flagged_field: str = "customfield_10021",
    ) -> None:
        raw = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
        self._data: dict[str, Any] = copy.deepcopy(raw)
        self._story_points_field = story_points_field
        self._sprint_field = sprint_field
        self._flagged_field = flagged_field
        self.base_url: str = self._data["base_url"]
        self.reference_now: datetime = datetime.fromisoformat(self._data["reference_now"])
        self._projects = {p["key"]: p for p in self._data["projects"]}
        self._users = {u["account_id"]: u for u in self._data["users"]}
        self._sprints = {s["id"]: s for s in self._data["sprints"]}
        self._issues: dict[str, dict[str, Any]] = {i["key"]: i for i in self._data["issues"]}
        self._next_id = max(int(i["id"]) for i in self._issues.values()) + 1

    def __repr__(self) -> str:
        return "MockJira()"

    async def aclose(self) -> None:
        return None

    # ---------------------------------------------------------- tiện ích

    def _project(self, key: str) -> dict[str, Any]:
        project = self._projects.get(key)
        if project is None:
            raise JiraNotFound(f"Không tìm thấy project '{key}' trên Jira.", 404)
        return project

    def _raw_issue(self, key: str) -> dict[str, Any]:
        issue = self._issues.get(key)
        if issue is None:
            raise JiraNotFound(f"Không tìm thấy issue '{key}' trên Jira.", 404)
        return issue

    def _updated(self, raw: dict[str, Any]) -> datetime:
        times = [_dt(raw["created"])] + [_dt(c["created"]) for c in raw.get("changelog", [])]
        return max(t for t in times if t is not None)

    def _to_issue(self, raw: dict[str, Any]) -> Issue:
        user = self._users.get(raw.get("assignee") or "")
        description = raw.get("description")
        if isinstance(description, dict):
            description = adf_to_text(description).strip()
        return Issue(
            key=raw["key"],
            id=raw["id"],
            summary=raw["summary"],
            issue_type=raw["type"],
            status=raw["status"],
            status_category=self._data["statuses"][raw["status"]],
            assignee_id=raw.get("assignee"),
            assignee_name=user["display_name"] if user else None,
            priority=raw.get("priority"),
            story_points=raw.get("points"),
            due_date=date.fromisoformat(raw["due"]) if raw.get("due") else None,
            created=_dt(raw["created"]),
            updated=self._updated(raw),
            sprint_ids=list(raw.get("sprints", [])),
            flagged=bool(raw.get("flagged")),
            blocked_by=list(raw.get("blocked_by", [])),
            labels=list(raw.get("labels", [])),
            parent_key=raw.get("parent"),
            description_text=description or None,
        )

    def _member(self, account_id: str) -> Member:
        user = self._users[account_id]
        return Member(
            account_id=account_id,
            display_name=user["display_name"],
            email_masked=mask_email(user.get("email")),
        )

    # -------------------------------------------------------------- Đọc

    async def list_projects(self) -> list[Project]:
        return [
            Project(key=p["key"], id=p["id"], name=p["name"], issue_types=list(p["issue_types"]))
            for p in self._projects.values()
        ]

    async def list_members(self, project_key: str, query: str | None = None) -> list[Member]:
        project = self._project(project_key)
        members = [self._member(acc) for acc in project["members"]]
        if not query:
            return members
        needle = normalize_vi(query)
        return [
            m
            for m in members
            if needle in normalize_vi(m.display_name)
            or needle in normalize_vi(self._users[m.account_id].get("email", ""))
        ]

    async def list_sprints(self, project_key: str, state: str | None = None) -> list[Sprint]:
        board_id = self._project(project_key)["board_id"]
        states = {s.strip() for s in state.split(",")} if state else None
        return [
            Sprint(
                id=s["id"],
                name=s["name"],
                state=s["state"],
                goal=s.get("goal"),
                start_date=_dt(s.get("start_date")),
                end_date=_dt(s.get("end_date")),
                complete_date=_dt(s.get("complete_date")),
                board_id=s["board_id"],
            )
            for s in self._sprints.values()
            if s["board_id"] == board_id and (states is None or s["state"] in states)
        ]

    async def search_issues(
        self, jql: str, fields: list[str] | None = None, max_results: int = 50
    ) -> list[Issue]:
        """Hỗ trợ một tập con JQL, các điều kiện nối bằng AND. `fields` bị bỏ qua (luôn trả đủ)."""
        predicates = [self._parse_clause(c) for c in self._split_jql(jql)]
        matched = [
            raw for raw in self._issues.values() if all(pred(raw) for pred in predicates)
        ]
        matched.sort(key=lambda r: (r["key"].split("-")[0], int(r["key"].split("-")[1])))
        return [self._to_issue(raw) for raw in matched[:max_results]]

    async def get_issue(self, key: str) -> Issue:
        return self._to_issue(self._raw_issue(key))

    async def get_issue_changelog(self, key: str) -> list[ChangelogEntry]:
        raw = self._raw_issue(key)
        return [
            ChangelogEntry(
                id=f"{raw['id']}-{index}",
                created=_dt(entry["created"]),
                author_id=entry.get("author"),
                items=[
                    ChangelogItem(field=i["field"], from_value=i.get("from"), to_value=i.get("to"))
                    for i in entry["items"]
                ],
            )
            for index, entry in enumerate(raw.get("changelog", []), start=1)
        ]

    async def get_create_meta(self, project_key: str, issue_type: str) -> list[FieldMeta]:
        project = self._project(project_key)
        canonical = next(
            (t for t in project["issue_types"] if t.lower() == issue_type.lower()), None
        )
        if canonical is None:
            names = ", ".join(project["issue_types"])
            raise JiraNotFound(
                f"Project {project_key} không có loại issue '{issue_type}'. "
                f"Các loại hiện có: {names}.",
                404,
            )
        meta = [
            FieldMeta(field_id="project", name="Project", required=True),
            FieldMeta(field_id="issuetype", name="Issue Type", required=True),
            FieldMeta(field_id="summary", name="Summary", required=True),
            FieldMeta(field_id="description", name="Description", required=False),
            FieldMeta(field_id="assignee", name="Assignee", required=False),
            FieldMeta(
                field_id="priority",
                name="Priority",
                required=False,
                has_default=True,
                allowed_values=list(self._data["priorities"]),
            ),
            FieldMeta(field_id="duedate", name="Due date", required=False),
            FieldMeta(field_id="labels", name="Labels", required=False),
            FieldMeta(
                field_id=self._story_points_field, name="Story point estimate", required=False
            ),
            FieldMeta(field_id=self._sprint_field, name="Sprint", required=False),
        ]
        if canonical == "Sub-task":
            meta.append(FieldMeta(field_id="parent", name="Parent", required=True))
        return meta

    async def get_transitions(self, key: str) -> list[Transition]:
        current = self._raw_issue(key)["status"]
        return [
            Transition(id=str((index + 1) * 10 + 1), name=status, to_status=status)
            for index, status in enumerate(self._data["statuses"])
            if status != current
        ]

    async def list_fields(self) -> list[JiraField]:
        return [JiraField(**f) for f in self._data["fields"]]

    # -------------------------------------------------------------- Ghi

    async def create_issue(self, fields: dict[str, Any]) -> CreatedIssue:
        """Tạo issue trong bộ nhớ.

        Không kiểm tra approval_token: việc đó do MCP tool làm (design 4.3).
        """
        project_key = (fields.get("project") or {}).get("key")
        issue_type = (fields.get("issuetype") or {}).get("name")
        summary = (fields.get("summary") or "").strip()
        errors: list[str] = []
        if not project_key or project_key not in self._projects:
            errors.append(f"project: project '{project_key}' không tồn tại")
        if not summary:
            errors.append("summary: bắt buộc")
        project = self._projects.get(project_key or "")
        if project and issue_type not in project["issue_types"]:
            errors.append(f"issuetype: '{issue_type}' không hợp lệ cho project {project_key}")
        assignee = (fields.get("assignee") or {}).get("accountId")
        if project and assignee and assignee not in project["members"]:
            errors.append("assignee: người này không thể được giao việc trong project")
        parent = (fields.get("parent") or {}).get("key")
        if issue_type == "Sub-task" and not parent:
            errors.append("parent: Sub-task phải có issue cha")
        if parent and parent not in self._issues:
            errors.append(f"parent: không tìm thấy issue '{parent}'")
        priority = (fields.get("priority") or {}).get("name")
        if priority and priority not in self._data["priorities"]:
            errors.append(f"priority: '{priority}' không hợp lệ")
        sprint_id = fields.get(self._sprint_field)
        if sprint_id is not None and sprint_id not in self._sprints:
            errors.append(f"sprint: không tìm thấy sprint {sprint_id}")
        if errors:
            detail = "; ".join(errors)
            raise JiraError(f"Jira từ chối tạo issue (HTTP 400). Chi tiết: {detail}", 400)

        assert project_key is not None and issue_type is not None
        numbers = [
            int(k.split("-")[1]) for k in self._issues if k.split("-")[0] == project_key
        ]
        key = f"{project_key}-{max(numbers, default=0) + 1}"
        issue_id = str(self._next_id)
        self._next_id += 1

        description = fields.get("description")
        if isinstance(description, str):
            description = markdown_to_adf(description)

        self._issues[key] = {
            "key": key,
            "id": issue_id,
            "summary": summary,
            "type": issue_type,
            "status": "To Do",
            "assignee": assignee,
            "priority": priority or "Medium",
            "points": fields.get(self._story_points_field),
            "due": fields.get("duedate"),
            "sprints": [sprint_id] if sprint_id is not None else [],
            "labels": list(fields.get("labels") or []),
            "parent": parent,
            "description": description,
            "created": self.reference_now.isoformat(),
            "changelog": [],
        }
        return CreatedIssue(key=key, id=issue_id, url=f"{self.base_url}/browse/{key}")

    # ---------------------------------------------------------- JQL mock

    @staticmethod
    def _split_jql(jql: str) -> list[str]:
        body = _ORDER_BY.sub("", jql.strip())
        if body.upper().startswith("ORDER BY"):
            return []
        clauses: list[str] = []
        for part in _AND.split(body):
            clause = part.strip()
            # Bỏ cặp ngoặc bao ngoài, ví dụ "(project = SHOP)"; giữ nguyên "openSprints()".
            while clause.startswith("(") and clause.endswith(")"):
                clause = clause[1:-1].strip()
            if clause:
                clauses.append(clause)
        return clauses

    def _parse_clause(self, clause: str) -> Any:
        def match(pattern: str) -> re.Match[str] | None:
            return re.fullmatch(pattern, clause, flags=re.IGNORECASE)

        if m := match(rf"project\s*=\s*(?:{_VALUE})"):
            key = _value(m).upper()
            return lambda r: r["key"].split("-")[0] == key
        if m := match(r"sprint\s*=\s*(\d+)"):
            sprint_id = int(m.group(1))
            return lambda r: sprint_id in r.get("sprints", [])
        if match(r"sprint\s+in\s+openSprints\(\s*\)"):
            open_ids = {s["id"] for s in self._sprints.values() if s["state"] != "closed"}
            return lambda r: bool(open_ids & set(r.get("sprints", [])))
        if match(r"sprint\s+in\s+closedSprints\(\s*\)"):
            closed_ids = {s["id"] for s in self._sprints.values() if s["state"] == "closed"}
            return lambda r: bool(closed_ids & set(r.get("sprints", [])))
        if match(r"sprint\s+is\s+empty"):
            return lambda r: not r.get("sprints")
        if m := match(rf"status\s*(?P<op>!=|=)\s*(?:{_VALUE})"):
            status, negate = _value(m).lower(), m.group("op") == "!="
            return lambda r: (r["status"].lower() == status) != negate
        if m := match(rf"statusCategory\s*(?P<op>!=|=)\s*(?:{_VALUE})"):
            name = _value(m).lower()
            category = _STATUS_CATEGORY_NAMES.get(name, name)
            negate = m.group("op") == "!="
            return lambda r: (self._data["statuses"][r["status"]] == category) != negate
        if match(r"assignee\s+is\s+empty"):
            return lambda r: not r.get("assignee")
        if m := match(rf"assignee\s*=\s*(?:{_VALUE})"):
            account_id = _value(m)
            return lambda r: r.get("assignee") == account_id
        if m := match(rf"(?:issuetype|type)\s*=\s*(?:{_VALUE})"):
            issue_type = _value(m).lower()
            return lambda r: r["type"].lower() == issue_type
        if m := match(rf"labels\s*=\s*(?:{_VALUE})"):
            label = _value(m)
            return lambda r: label in r.get("labels", [])
        if m := match(rf"key\s*=\s*(?:{_VALUE})"):
            key = _value(m).upper()
            return lambda r: r["key"] == key
        if m := match(r"key\s+in\s*\(?\s*([\w\-,\s]+?)\s*\)?"):
            keys = {k.strip().upper() for k in m.group(1).split(",") if k.strip()}
            return lambda r: r["key"] in keys
        if m := match(rf"updated\s*>=\s*(?:{_VALUE})"):
            since = self._parse_jql_date(_value(m), clause)
            return lambda r: self._updated(r) >= since
        if m := match(rf"(?:text|summary)\s*~\s*(?:{_VALUE})"):
            words = normalize_vi(_value(m)).split()
            return lambda r: all(w in self._search_text(r) for w in words)
        raise JiraError(f"Mock Jira chưa hỗ trợ điều kiện JQL: '{clause}'.", 400)

    @staticmethod
    def _parse_jql_date(value: str, clause: str) -> datetime:
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d %H:%M", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=JQL_TZ)
            except ValueError:
                continue
        raise JiraError(f"Ngày trong JQL không hợp lệ: '{clause}'.", 400)

    @staticmethod
    def _search_text(raw: dict[str, Any]) -> str:
        description = raw.get("description")
        if isinstance(description, dict):
            description = adf_to_text(description)
        return normalize_vi(f"{raw['summary']} {description or ''}")
