"""Kiểm tra get_jira chọn backend theo JIRA_MODE."""

import pytest
from pydantic import SecretStr

from core.settings import Settings
from mcp_server.errors import JiraError
from mcp_server.factory import get_jira
from mcp_server.jira_client import JiraClient
from mcp_server.mock_jira import MockJira


def make_settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_mock_by_default() -> None:
    assert isinstance(get_jira(make_settings()), MockJira)


def test_real_missing_config_lists_names_only() -> None:
    settings = make_settings(
        jira_mode="real", jira_email="sm@example.com", jira_api_token=SecretStr("")
    )
    with pytest.raises(JiraError) as info:
        get_jira(settings)
    message = str(info.value)
    assert "JIRA_BASE_URL" in message and "JIRA_API_TOKEN" in message
    assert "sm@example.com" not in message


async def test_real_with_config_returns_client() -> None:
    settings = make_settings(
        jira_mode="real",
        jira_base_url="https://example.atlassian.net",
        jira_email="sm@example.com",
        jira_api_token=SecretStr("tok-123"),
    )
    jira = get_jira(settings)
    try:
        assert isinstance(jira, JiraClient)
        assert "tok-123" not in repr(jira)
    finally:
        await jira.aclose()
