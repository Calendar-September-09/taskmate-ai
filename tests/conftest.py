"""Fixture dùng chung cho test MCP Server. Luôn dùng MockJira, không đọc .env."""

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from pydantic import SecretStr

from core.settings import Settings
from domain.schemas import TaskDraft
from mcp_server.cache import TTLCache
from mcp_server.mock_jira import MockJira
from mcp_server.store import ServerStore
from mcp_server.tools import TaskMateTools

TZ = ZoneInfo("Asia/Ho_Chi_Minh")
APPROVAL_SECRET = "test-approval-secret-0123456789"


class FakeClock:
    """Đồng hồ giả: datetime cho approval, số giây cho cache."""

    def __init__(self) -> None:
        self.current = datetime(2026, 11, 12, 9, 0, tzinfo=TZ)
        self.seconds = 1000.0

    def now(self) -> datetime:
        return self.current

    def monotonic(self) -> float:
        return self.seconds

    def advance(self, delta: timedelta) -> None:
        self.current += delta
        self.seconds += delta.total_seconds()


class CountingMockJira(MockJira):
    """MockJira đếm số lần gọi để kiểm tra cache."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: dict[str, int] = {}

    def _count(self, name: str) -> None:
        self.calls[name] = self.calls.get(name, 0) + 1

    async def list_members(self, project_key, query=None):  # type: ignore[no-untyped-def]
        self._count("list_members")
        return await super().list_members(project_key, query)

    async def list_sprints(self, project_key, state=None):  # type: ignore[no-untyped-def]
        self._count("list_sprints")
        return await super().list_sprints(project_key, state)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        jira_mode="mock",
        approval_secret=SecretStr(APPROVAL_SECRET),
        db_path=tmp_path / "taskmate.db",
    )


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def store(settings: Settings) -> ServerStore:
    return ServerStore(settings.db_path)


@pytest.fixture
def jira() -> CountingMockJira:
    return CountingMockJira()


@pytest.fixture
def tools(
    jira: CountingMockJira, settings: Settings, store: ServerStore, clock: FakeClock
) -> TaskMateTools:
    return TaskMateTools(
        jira, settings, store, now=clock.now, cache=TTLCache(clock=clock.monotonic)
    )


@pytest.fixture
def draft() -> TaskDraft:
    return TaskDraft(
        project_key="SHOP",
        issue_type="Task",
        summary="Viết API thanh toán VNPay",
        description="## Mục tiêu\nKết nối cổng VNPay.",
        assignee_id="acc-duc",
        sprint_id=12,
        priority="High",
        due_date=date(2026, 11, 20),
        story_points=3,
        labels=["payment", "backend"],
        confidence=0.9,
    )
