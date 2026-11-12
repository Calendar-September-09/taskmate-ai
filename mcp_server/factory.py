"""Chọn backend Jira theo JIRA_MODE."""

from core.settings import Settings, get_settings
from mcp_server.base import JiraBackend
from mcp_server.errors import JiraError
from mcp_server.jira_client import JiraClient
from mcp_server.mock_jira import MockJira


def get_jira(settings: Settings | None = None) -> JiraBackend:
    """JIRA_MODE=mock -> MockJira; JIRA_MODE=real -> JiraClient (cần đủ cấu hình)."""
    settings = settings or get_settings()
    if settings.jira_mode == "mock":
        return MockJira(
            story_points_field=settings.jira_story_points_field,
            sprint_field=settings.jira_sprint_field,
            flagged_field=settings.jira_flagged_field,
        )

    missing = [
        name
        for name, value in (
            ("JIRA_BASE_URL", settings.jira_base_url),
            ("JIRA_EMAIL", settings.jira_email),
            ("JIRA_API_TOKEN", settings.jira_api_token.get_secret_value()),
        )
        if not value
    ]
    if missing:
        raise JiraError(
            f"Thiếu cấu hình Jira cho chế độ real: {', '.join(missing)}. Kiểm tra file .env."
        )
    return JiraClient.from_settings(settings)
