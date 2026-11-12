"""Kiểm tra đăng ký tool trên MCPServer và log JSON ra stderr."""

import json
import logging

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from domain.schemas import TaskDraft
from mcp_server.approval import issue_token
from mcp_server.drafts import draft_hash
from mcp_server.logging_setup import configure_logging
from mcp_server.server import READ_TOOLS, WRITE_TOOLS, build_server
from mcp_server.tools import TaskMateTools
from tests.conftest import APPROVAL_SECRET, FakeClock

JIRA_TOKEN = "jira-token-should-never-appear"


async def test_all_tools_registered_with_descriptions(tools: TaskMateTools) -> None:
    server = build_server(tools)
    registered = {t.name: t for t in await server.list_tools()}
    assert set(registered) == set(READ_TOOLS) | set(WRITE_TOOLS)
    assert len(registered) == 9
    for name, tool in registered.items():
        assert tool.description and len(tool.description) > 30, name
    for name in READ_TOOLS:
        assert registered[name].annotations and registered[name].annotations.read_only_hint
    for name in WRITE_TOOLS:
        assert "approval_token" in registered[name].input_schema["required"]


async def test_call_through_server(tools: TaskMateTools) -> None:
    server = build_server(tools)
    result = await server.call_tool("list_members", {"project_key": "SHOP", "query": "duc"})
    assert result.structured_content is not None
    members = result.structured_content["members"]
    assert [m["display_name"] for m in members] == ["Phạm Minh Đức"]


async def test_create_without_valid_token_via_server(tools: TaskMateTools) -> None:
    server = build_server(tools)
    with pytest.raises(ToolError, match="approval"):
        await server.call_tool(
            "create_task",
            {"draft": {"project_key": "SHOP", "summary": "Viết test"}, "approval_token": "x"},
        )


async def test_logs_are_json_on_stderr_without_secrets(
    tools: TaskMateTools,
    draft: TaskDraft,
    clock: FakeClock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    handler = configure_logging([JIRA_TOKEN, APPROVAL_SECRET])
    try:
        token = issue_token(draft_hash(draft), "scrum-master", APPROVAL_SECRET, clock.now())
        await tools.create_task(draft, token)
        with pytest.raises(Exception):  # noqa: B017 - token đã dùng
            await tools.create_task(draft, token)
        logging.getLogger("taskmate.mcp").info(f"thử rò rỉ {JIRA_TOKEN}")
    finally:
        logging.getLogger().removeHandler(handler)

    captured = capsys.readouterr()
    assert captured.out == ""  # stdout dành cho giao thức stdio
    lines = [line for line in captured.err.splitlines() if line.strip()]
    records = [json.loads(line) for line in lines]
    assert any(r.get("event") == "create_issue" for r in records)
    assert any(r.get("reason") == "used" for r in records)
    for secret in (token, JIRA_TOKEN, APPROVAL_SECRET):
        assert secret not in captured.err
