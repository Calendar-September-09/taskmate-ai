"""Interface chung cho JiraClient (thật) và MockJira."""

from typing import Any, Protocol

from mcp_server.models import (
    ChangelogEntry,
    CreatedIssue,
    FieldMeta,
    Issue,
    JiraField,
    Member,
    Project,
    Sprint,
    Transition,
)


class JiraBackend(Protocol):
    async def list_projects(self) -> list[Project]: ...

    async def list_members(self, project_key: str, query: str | None = None) -> list[Member]:
        """Người có thể được giao việc trong project."""
        ...

    async def list_sprints(self, project_key: str, state: str | None = None) -> list[Sprint]:
        """state: 'active', 'future', 'closed' hoặc nhiều giá trị cách nhau bởi dấu phẩy."""
        ...

    async def search_issues(
        self, jql: str, fields: list[str] | None = None, max_results: int = 50
    ) -> list[Issue]: ...

    async def get_issue(self, key: str) -> Issue: ...

    async def get_issue_changelog(self, key: str) -> list[ChangelogEntry]: ...

    async def get_create_meta(self, project_key: str, issue_type: str) -> list[FieldMeta]: ...

    async def create_issue(self, fields: dict[str, Any]) -> CreatedIssue:
        """Thao tác GHI. Lớp này không kiểm tra approval_token: việc đó do MCP tool
        (mcp_server/server.py) làm trước khi gọi hàm này (design mục 4.3, 4.5)."""
        ...

    async def get_transitions(self, key: str) -> list[Transition]: ...

    async def list_fields(self) -> list[JiraField]: ...

    async def aclose(self) -> None: ...
