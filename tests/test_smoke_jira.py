"""Kiểm tra cách scripts/smoke_jira.py chọn key project."""

from core.settings import Settings
from scripts.smoke_jira import resolve_project_key


def make_settings(demo_project: str) -> Settings:
    # Không đọc file .env thật trên máy.
    return Settings(_env_file=None, jira_mode="mock", jira_demo_project=demo_project)


def test_uses_demo_project_when_no_argument() -> None:
    assert resolve_project_key(["smoke_jira"], make_settings("DEMO")) == "DEMO"


def test_argument_overrides_demo_project() -> None:
    assert resolve_project_key(["smoke_jira", "ABC"], make_settings("DEMO")) == "ABC"
