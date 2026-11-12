"""MCP Server của TaskMate (design 4.3): giữ token Jira, chỉ lộ tool cho Agent.

Chạy: uv run python -m mcp_server.server   (transport stdio)
Dùng MCPServer của MCP Python SDK 2.x (tên mới của FastMCP).
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from core.settings import Settings, get_settings
from mcp_server.factory import get_jira
from mcp_server.logging_setup import configure_logging
from mcp_server.store import ServerStore
from mcp_server.tools import TaskMateTools

logger = logging.getLogger("taskmate.mcp")

SERVER_NAME = "taskmate-jira"
INSTRUCTIONS = (
    "Công cụ làm việc với Jira cho Scrum Master. Tool đọc dùng thoải mái. "
    "create_task và create_tasks_bulk chỉ gọi khi đã có approval_token do người dùng duyệt; "
    "không bao giờ tự tạo approval_token."
)

READ_TOOLS = (
    "list_projects",
    "list_members",
    "list_sprints",
    "search_issues",
    "get_sprint_issues",
    "get_issue_changelog",
    "get_create_meta",
)
WRITE_TOOLS = ("create_task", "create_tasks_bulk")

_READ = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=True)
# Idempotent: tạo lại cùng bản nháp trả về issue đã có.
_WRITE = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=True
)


def build_server(tools: TaskMateTools, lifespan: Any = None) -> MCPServer:
    """Tạo MCPServer và đăng ký các tool; mô tả tool lấy từ docstring của TaskMateTools."""
    server: MCPServer = MCPServer(SERVER_NAME, instructions=INSTRUCTIONS, lifespan=lifespan)
    for name in READ_TOOLS:
        server.add_tool(getattr(tools, name), name=name, annotations=_READ)
    for name in WRITE_TOOLS:
        server.add_tool(getattr(tools, name), name=name, annotations=_WRITE)
    return server


def _secrets(settings: Settings) -> list[str]:
    return [
        settings.jira_api_token.get_secret_value(),
        settings.approval_secret.get_secret_value(),
        settings.llm_api_key.get_secret_value(),
        settings.langfuse_secret_key.get_secret_value(),
    ]


def create_app(settings: Settings | None = None) -> MCPServer:
    settings = settings or get_settings()
    jira = get_jira(settings)
    tools = TaskMateTools(jira, settings, ServerStore(settings.db_path))

    @asynccontextmanager
    async def lifespan(_: MCPServer) -> AsyncIterator[None]:
        logger.info(
            "MCP Server khởi động",
            extra={"data": {"event": "startup", "jira_mode": settings.jira_mode}},
        )
        try:
            yield
        finally:
            await jira.aclose()
            logger.info("MCP Server dừng", extra={"data": {"event": "shutdown"}})

    return build_server(tools, lifespan=lifespan)


def main() -> None:
    settings = get_settings()
    configure_logging(_secrets(settings))
    create_app(settings).run("stdio")


if __name__ == "__main__":
    main()
