"""Logic các MCP tool của TaskMate (design 4.3, 4.5, 10.2, 13.2).

Docstring của mỗi phương thức public là mô tả tool mà LLM đọc để biết khi nào gọi.
server.py chỉ đăng ký các phương thức này; test gọi trực tiếp với MockJira.
"""

import logging
import re
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from typing import Annotated, TypeVar

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from core.settings import Settings
from domain.schemas import TaskDraft
from mcp_server.approval import ApprovalError, verify_token
from mcp_server.base import JiraBackend
from mcp_server.cache import TTLCache
from mcp_server.drafts import draft_hash, drafts_hash
from mcp_server.errors import JiraError, JiraNotFound
from mcp_server.models import ChangelogEntry, FieldMeta, Issue, Member, Project, Sprint
from mcp_server.store import ServerStore

logger = logging.getLogger("taskmate.mcp")

ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]+-\d+$")
MAX_BULK = 50

T = TypeVar("T")

ProjectKey = Annotated[
    str, Field(pattern=r"^[A-Z][A-Z0-9_]+$", description="Key project Jira, ví dụ SHOP.")
]
IssueKey = Annotated[
    str, Field(pattern=r"^[A-Z][A-Z0-9_]+-\d+$", description="Key issue, ví dụ SHOP-12.")
]
ApprovalToken = Annotated[
    str, Field(description="Mã duyệt do bước Human-in-the-loop sinh ra. Không tự tạo.")
]


class TaskMateToolError(ToolError):
    """Lỗi đã lường trước; MCPServer trả về cho LLM dạng is_error với thông điệp tiếng Việt."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code


# ------------------------------------------------------------------ Output


class IssueSummary(BaseModel):
    """Issue rút gọn, đủ cho stand-up và báo cáo sprint."""

    key: str
    summary: str
    issue_type: str
    status: str
    status_category: str
    assignee_id: str | None = None
    assignee_name: str | None = None
    priority: str | None = None
    story_points: float | None = None
    due_date: date | None = None
    created: datetime | None = None
    updated: datetime | None = None
    sprint_ids: list[int] = Field(default_factory=list)
    flagged: bool = False
    blocked_by: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    parent_key: str | None = None

    @classmethod
    def from_issue(cls, issue: Issue) -> "IssueSummary":
        return cls.model_validate(issue.model_dump(exclude={"id", "description_text"}))


class ProjectList(BaseModel):
    projects: list[Project]


class MemberList(BaseModel):
    members: list[Member]


class SprintList(BaseModel):
    sprints: list[Sprint]


class IssueList(BaseModel):
    count: int
    issues: list[IssueSummary]

    @classmethod
    def of(cls, issues: list[Issue]) -> "IssueList":
        return cls(count=len(issues), issues=[IssueSummary.from_issue(i) for i in issues])


class Changelog(BaseModel):
    issue_key: str
    entries: list[ChangelogEntry]


class CreateMeta(BaseModel):
    project_key: str
    issue_type: str
    fields: list[FieldMeta]


class CreateTaskResult(BaseModel):
    key: str
    url: str
    verified: bool = Field(description="True nếu đọc lại từ Jira thấy các trường chính khớp.")
    mismatches: list[str] = Field(default_factory=list)
    already_existed: bool = Field(
        default=False, description="True nếu bản nháp này đã được tạo trước đó (không tạo lại)."
    )


class BulkItemResult(BaseModel):
    index: int
    ok: bool
    result: CreateTaskResult | None = None
    error: str | None = None


class BulkCreateResult(BaseModel):
    created: int
    failed: int
    items: list[BulkItemResult]


# ------------------------------------------------------------------ Tools


class TaskMateTools:
    def __init__(
        self,
        jira: JiraBackend,
        settings: Settings,
        store: ServerStore,
        *,
        now: Callable[[], datetime] | None = None,
        cache: TTLCache | None = None,
    ) -> None:
        self._jira = jira
        self._settings = settings
        self._store = store
        self._now = now or (lambda: datetime.now(settings.tz))
        self._cache = cache or TTLCache()

    # -------------------------------------------------------------- Đọc

    async def list_projects(self) -> ProjectList:
        """Liệt kê các project Jira mà TaskMate truy cập được, kèm các loại issue cho phép.

        Gọi khi cần xác minh project_key người dùng nói tới, hoặc khi chưa biết project nào.
        """
        return ProjectList(projects=await self._read("list_projects", self._jira.list_projects()))

    async def list_members(
        self,
        project_key: ProjectKey,
        query: Annotated[
            str | None, Field(description="Một phần tên hoặc email, không cần dấu.")
        ] = None,
    ) -> MemberList:
        """Tìm người có thể được giao việc trong project; email đã được che bớt.

        Gọi khi cần đổi tên người (ví dụ "Nam") thành accountId để điền assignee_id.
        Nếu ra nhiều người trùng tên, hãy hỏi lại người dùng, không tự chọn.
        """
        key = ("members", project_key, query or "")
        cached = self._cache.get(key)
        if cached is not None:
            return MemberList(members=cached)
        members = await self._read("list_members", self._jira.list_members(project_key, query))
        self._cache.set(key, members)
        return MemberList(members=members)

    async def list_sprints(
        self,
        project_key: ProjectKey,
        state: Annotated[
            str | None,
            Field(description="'active', 'future', 'closed' hoặc nhiều giá trị cách bởi dấu phẩy."),
        ] = None,
    ) -> SprintList:
        """Liệt kê sprint của project: id, tên, mục tiêu, ngày bắt đầu/kết thúc, trạng thái.

        Gọi khi cần sprint_id cho bản nháp, khi chuẩn bị stand-up hoặc báo cáo cuối sprint.
        """
        key = ("sprints", project_key, state or "")
        cached = self._cache.get(key)
        if cached is not None:
            return SprintList(sprints=cached)
        sprints = await self._read("list_sprints", self._jira.list_sprints(project_key, state))
        self._cache.set(key, sprints)
        return SprintList(sprints=sprints)

    async def search_issues(
        self,
        project_key: ProjectKey,
        text: Annotated[
            str | None, Field(description="Từ khóa trong tiêu đề hoặc mô tả, không cần dấu.")
        ] = None,
        updated_since: Annotated[
            datetime | None,
            Field(description="Chỉ lấy issue cập nhật từ thời điểm này (giờ Việt Nam)."),
        ] = None,
        sprint_id: Annotated[
            int | None, Field(description="Chỉ lấy issue trong sprint này.")
        ] = None,
        max_results: Annotated[int, Field(ge=1, le=100)] = 20,
    ) -> IssueList:
        """Tìm issue trong một project.

        Gọi để (1) kiểm tra task gần trùng trước khi tạo (truyền text là tiêu đề dự định),
        (2) lấy các issue thay đổi từ buổi stand-up trước (truyền updated_since).
        """
        clauses = [f"project = {project_key}"]
        if sprint_id is not None:
            clauses.append(f"sprint = {sprint_id}")
        if updated_since is not None:
            local = (
                updated_since.astimezone(self._settings.tz)
                if updated_since.tzinfo
                else updated_since
            )
            clauses.append(f'updated >= "{local:%Y-%m-%d %H:%M}"')
        if text and (cleaned := _clean_jql_text(text)):
            clauses.append(f'text ~ "{cleaned}"')
        jql = " AND ".join(clauses)
        issues = await self._read(
            "search_issues", self._jira.search_issues(jql, max_results=max_results)
        )
        return IssueList.of(issues)

    async def get_sprint_issues(
        self,
        sprint_id: Annotated[int, Field(description="Id sprint, lấy từ list_sprints.")],
        max_results: Annotated[int, Field(ge=1, le=200)] = 200,
    ) -> IssueList:
        """Lấy các issue trong một sprint: loại, trạng thái, người phụ trách, story points, hạn,
        Flagged, bị chặn bởi issue nào.

        Gọi khi chuẩn bị Daily Stand-up hoặc báo cáo cuối sprint.
        """
        issues = await self._read(
            "get_sprint_issues",
            self._jira.search_issues(f"sprint = {sprint_id}", max_results=max_results),
        )
        return IssueList.of(issues)

    async def get_issue_changelog(self, issue_key: IssueKey) -> Changelog:
        """Lịch sử thay đổi của một issue: chuyển trạng thái, đổi sprint, đổi người phụ trách,
        kèm thời điểm.

        Gọi khi cần biết task nằm yên ở một trạng thái bao lâu hoặc ai đã chuyển gì từ hôm qua.
        """
        entries = await self._read(
            "get_issue_changelog", self._jira.get_issue_changelog(issue_key)
        )
        return Changelog(issue_key=issue_key, entries=entries)

    async def get_create_meta(
        self,
        project_key: ProjectKey,
        issue_type: Annotated[str, Field(description="Story, Task, Bug hoặc Sub-task.")],
    ) -> CreateMeta:
        """Các trường của loại issue trong project: trường nào bắt buộc, giá trị cho phép.

        Gọi trước khi dựng bản nháp nếu chưa chắc trường nào bắt buộc.
        """
        fields = await self._read(
            "get_create_meta", self._jira.get_create_meta(project_key, issue_type)
        )
        return CreateMeta(project_key=project_key, issue_type=issue_type, fields=fields)

    # -------------------------------------------------------------- Ghi

    async def create_task(
        self, draft: TaskDraft, approval_token: ApprovalToken
    ) -> CreateTaskResult:
        """TẠO một issue trên Jira từ bản nháp ĐÃ ĐƯỢC NGƯỜI DÙNG DUYỆT.

        Chỉ gọi sau khi người dùng bấm Approve và có approval_token cho đúng bản nháp này.
        Không sửa bản nháp sau khi duyệt: token sẽ bị từ chối. Tạo lại cùng bản nháp sẽ trả
        issue key đã có, không tạo trùng. Kết quả có verified=false nếu Jira lưu khác bản nháp.
        """
        digest = draft_hash(draft)
        self._verify("create_task", approval_token, digest)
        return await self._create_one(draft, digest)

    async def create_tasks_bulk(
        self,
        drafts: Annotated[list[TaskDraft], Field(min_length=1, max_length=MAX_BULK)],
        approval_token: ApprovalToken,
    ) -> BulkCreateResult:
        """TẠO nhiều issue cùng lúc (ví dụ từ biên bản họp) từ danh sách ĐÃ ĐƯỢC DUYỆT.

        approval_token phải được sinh cho đúng danh sách này, đúng thứ tự. Dòng lỗi được báo
        riêng, các dòng khác vẫn được tạo; chạy lại không tạo trùng các dòng đã tạo.
        """
        self._verify("create_tasks_bulk", approval_token, drafts_hash(drafts))
        items: list[BulkItemResult] = []
        for index, draft in enumerate(drafts):
            try:
                result = await self._create_one(draft, draft_hash(draft))
                items.append(BulkItemResult(index=index, ok=True, result=result))
            except TaskMateToolError as exc:
                items.append(BulkItemResult(index=index, ok=False, error=str(exc)))
        created = sum(1 for item in items if item.ok)
        return BulkCreateResult(created=created, failed=len(items) - created, items=items)

    # ---------------------------------------------------------- nội bộ

    async def _read(self, tool: str, call: Awaitable[T]) -> T:
        try:
            return await call
        except JiraError as exc:
            logger.warning(
                "Lỗi Jira khi đọc",
                extra={"data": {"event": tool, "status": exc.status_code, "error": exc.message}},
            )
            raise TaskMateToolError("jira_error", exc.message) from exc

    def _verify(self, tool: str, token: str, digest: str) -> str:
        """Trả jti của token hợp lệ; sai thì raise TaskMateToolError, không chạm Jira."""
        secret = self._settings.approval_secret.get_secret_value()
        try:
            payload = verify_token(token, digest, secret, self._store, self._now())
        except ApprovalError as exc:
            logger.warning(
                "Từ chối approval_token",
                extra={"data": {"event": tool, "reason": exc.reason}},
            )
            raise TaskMateToolError(f"approval_{exc.reason}", str(exc)) from exc
        logger.info(
            "approval_token hợp lệ",
            extra={"data": {"event": tool, "approver": payload.approver, "jti": payload.jti[:8]}},
        )
        return payload.jti

    async def _create_one(self, draft: TaskDraft, digest: str) -> CreateTaskResult:
        existing = self._store.get_created(digest)
        if existing is not None:
            try:
                issue = await self._jira.get_issue(existing.issue_key)
            except JiraNotFound:
                # Issue đã bị xóa trên Jira: quên bản ghi cũ và tạo lại.
                self._store.forget_created(digest)
            except JiraError as exc:
                raise TaskMateToolError("jira_error", exc.message) from exc
            else:
                logger.info(
                    "Bản nháp đã được tạo trước đó",
                    extra={"data": {"event": "idempotent_hit", "key": existing.issue_key}},
                )
                mismatches = compare_issue(draft, issue)
                return CreateTaskResult(
                    key=existing.issue_key,
                    url=existing.url,
                    verified=not mismatches,
                    mismatches=mismatches,
                    already_existed=True,
                )

        fields = draft.to_jira_fields(
            story_points_field=self._settings.jira_story_points_field,
            sprint_field=self._settings.jira_sprint_field,
        )
        try:
            created = await self._jira.create_issue(fields)
        except JiraError as exc:
            logger.warning(
                "Jira từ chối tạo issue",
                extra={"data": {"event": "create_issue", "status": exc.status_code}},
            )
            raise TaskMateToolError("jira_error", exc.message) from exc
        if not ISSUE_KEY_RE.fullmatch(created.key or ""):
            raise TaskMateToolError(
                "invalid_key", "Jira không trả về issue key hợp lệ; không xác nhận đã tạo."
            )
        self._store.save_created(digest, created.key, created.url, self._now())
        logger.info("Đã tạo issue", extra={"data": {"event": "create_issue", "key": created.key}})

        try:
            issue = await self._jira.get_issue(created.key)
        except JiraError as exc:
            mismatches = [f"Không đọc lại được issue để kiểm tra: {exc.message}"]
        else:
            mismatches = compare_issue(draft, issue)
        if mismatches:
            logger.warning(
                "Issue trên Jira khác bản nháp",
                extra={"data": {"event": "verify", "key": created.key, "fields": mismatches}},
            )
        return CreateTaskResult(
            key=created.key, url=created.url, verified=not mismatches, mismatches=mismatches
        )


def _clean_jql_text(text: str) -> str:
    """Bỏ ký tự có thể thoát khỏi chuỗi JQL (dấu nháy, gạch chéo ngược)."""
    return " ".join(re.sub(r"[\"'\\]", " ", text).split())


def compare_issue(draft: TaskDraft, issue: Issue) -> list[str]:
    """So các trường chính của bản nháp với issue đọc lại từ Jira. Trả danh sách khác biệt."""
    checks: list[tuple[str, object, object]] = [
        ("summary", draft.summary.strip(), issue.summary.strip()),
        ("issue_type", draft.issue_type, issue.issue_type),
        ("assignee_id", draft.assignee_id, issue.assignee_id),
        ("due_date", draft.due_date, issue.due_date),
        ("story_points", draft.story_points, issue.story_points),
        ("parent_key", draft.parent_key, issue.parent_key),
        (
            "labels",
            sorted({label.strip() for label in draft.labels if label.strip()}),
            sorted(issue.labels),
        ),
    ]
    if draft.priority is not None:  # Không đặt thì Jira dùng mặc định.
        checks.append(("priority", draft.priority, issue.priority))
    mismatches = [
        f"{name}: bản nháp '{expected}', Jira '{actual}'"
        for name, expected, actual in checks
        if expected != actual
    ]
    if draft.sprint_id is not None and draft.sprint_id not in issue.sprint_ids:
        mismatches.append(f"sprint_id: bản nháp '{draft.sprint_id}', Jira '{issue.sprint_ids}'")
    return mismatches

