"""Kiểm tra nhanh kết nối Jira thật. CHỈ ĐỌC: không tạo, sửa hay xóa gì trên Jira.

Chạy: JIRA_MODE=real trong .env, rồi
    uv run python -m scripts.smoke_jira [PROJECT_KEY]   (mặc định JIRA_DEMO_PROJECT trong .env)
"""

import asyncio
import sys

from core.settings import Settings, get_settings
from mcp_server.errors import JiraError
from mcp_server.factory import get_jira
from mcp_server.jira_client import JiraClient

FIELD_NAMES = {
    "Story points": {"story point estimate", "story points"},
    "Sprint": {"sprint"},
    "Flagged": {"flagged"},
}


async def run(project_key: str) -> int:
    settings = get_settings()
    if settings.jira_mode != "real":
        print("Script này chỉ chạy với JIRA_MODE=real. Đặt JIRA_MODE=real trong .env rồi chạy lại.")
        return 2

    jira = get_jira(settings)
    assert isinstance(jira, JiraClient)
    try:
        projects = await jira.list_projects()
        print(f"== Project ({len(projects)})")
        for p in projects:
            print(f"  {p.key:<10} {p.name}  [{', '.join(p.issue_types)}]")

        members = await jira.list_members(project_key)
        print(f"\n== Thành viên có thể giao việc trong {project_key} ({len(members)})")
        for m in members:
            print(f"  {m.display_name:<30} {m.account_id}  {m.email_masked or ''}")

        sprints = await jira.list_sprints(project_key)
        print(f"\n== Sprint của {project_key} ({len(sprints)})")
        for s in sprints:
            start = s.start_date.date() if s.start_date else "-"
            end = s.end_date.date() if s.end_date else "-"
            print(f"  {s.id:<6} {s.name:<25} {s.state:<7} {start} → {end}")

        fields = await jira.list_fields()
        print("\n== Id custom field (điền vào .env)")
        env_names = {
            "Story points": "JIRA_STORY_POINTS_FIELD",
            "Sprint": "JIRA_SPRINT_FIELD",
            "Flagged": "JIRA_FLAGGED_FIELD",
        }
        for label, names in FIELD_NAMES.items():
            found = [f for f in fields if f.custom and f.name.lower() in names]
            ids = ", ".join(f"{f.id} ({f.name})" for f in found) or "không tìm thấy"
            print(f"  {env_names[label]:<24} {ids}")
        return 0
    except JiraError as exc:
        print(f"Lỗi Jira: {exc}")
        return 1
    finally:
        await jira.aclose()


def resolve_project_key(argv: list[str], settings: Settings) -> str:
    """Key project từ tham số dòng lệnh; không có thì lấy JIRA_DEMO_PROJECT."""
    return argv[1] if len(argv) > 1 else settings.jira_demo_project


def main() -> None:
    # Console Windows mặc định không phải UTF-8; tránh lỗi khi in tiếng Việt.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    project_key = resolve_project_key(sys.argv, get_settings())
    sys.exit(asyncio.run(run(project_key)))


if __name__ == "__main__":
    main()
