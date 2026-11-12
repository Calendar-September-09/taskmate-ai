"""Kiểm tra cấu hình đọc từ môi trường."""

from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from core.settings import Settings

ENV_VARS = [
    "JIRA_BASE_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "JIRA_MODE",
    "JIRA_STORY_POINTS_FIELD",
    "JIRA_SPRINT_FIELD",
    "JIRA_FLAGGED_FIELD",
    "JIRA_DEMO_PROJECT",
    "LLM_API_KEY",
    "LLM_MODEL_MAIN",
    "LLM_MODEL_FAST",
    "APPROVAL_SECRET",
    "DB_PATH",
    "TIMEZONE",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_HOST",
]

SECRET = "secret-xyz-123"


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def make_settings() -> Settings:
    # Không đọc file .env thật trên máy.
    return Settings(_env_file=None)


def test_defaults() -> None:
    settings = make_settings()
    assert settings.jira_mode == "mock"
    assert settings.timezone == "Asia/Ho_Chi_Minh"
    assert settings.tz == ZoneInfo("Asia/Ho_Chi_Minh")
    assert settings.db_path == Path("data/taskmate.db")
    assert settings.jira_api_token.get_secret_value() == ""
    assert settings.jira_story_points_field == "customfield_10016"
    assert settings.jira_sprint_field == "customfield_10020"
    assert settings.jira_flagged_field == "customfield_10021"
    assert settings.jira_demo_project == "SHOP"


def test_reads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JIRA_MODE", "real")
    monkeypatch.setenv("JIRA_API_TOKEN", SECRET)
    monkeypatch.setenv("JIRA_STORY_POINTS_FIELD", "customfield_10028")
    monkeypatch.setenv("JIRA_DEMO_PROJECT", "DEMO")
    settings = make_settings()
    assert settings.jira_mode == "real"
    assert settings.jira_story_points_field == "customfield_10028"
    assert settings.jira_demo_project == "DEMO"
    assert settings.jira_api_token.get_secret_value() == SECRET


@pytest.mark.parametrize(
    "env_name", ["JIRA_API_TOKEN", "LLM_API_KEY", "APPROVAL_SECRET", "LANGFUSE_SECRET_KEY"]
)
def test_secrets_not_exposed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], env_name: str
) -> None:
    monkeypatch.setenv(env_name, SECRET)
    settings = make_settings()

    print(settings)
    print(repr(settings))
    output = capsys.readouterr().out

    assert SECRET not in output
    assert SECRET not in str(settings)
    assert SECRET not in settings.model_dump_json()
    assert getattr(settings, env_name.lower()).get_secret_value() == SECRET


@pytest.mark.parametrize(
    ("env_name", "value"), [("JIRA_MODE", "prod"), ("TIMEZONE", "Mars/Base")]
)
def test_invalid_values(monkeypatch: pytest.MonkeyPatch, env_name: str, value: str) -> None:
    monkeypatch.setenv(env_name, value)
    with pytest.raises(ValidationError):
        make_settings()
