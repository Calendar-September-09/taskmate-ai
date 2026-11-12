"""Kiểm tra MockJira và dữ liệu giả lập."""

from datetime import date

import pytest

from mcp_server.errors import JiraError, JiraNotFound
from mcp_server.mock_jira import MockJira


@pytest.fixture
def jira() -> MockJira:
    return MockJira()


async def test_projects(jira: MockJira) -> None:
    projects = {p.key: p for p in await jira.list_projects()}
    assert set(projects) == {"SHOP", "HR"}
    assert "Bug" in projects["SHOP"].issue_types


async def test_two_nams_in_shop(jira: MockJira) -> None:
    nams = await jira.list_members("SHOP", "nam")
    assert {m.display_name for m in nams} == {"Nguyễn Văn Nam", "Trần Hoài Nam"}
    # Email được che.
    assert all(m.email_masked and "***@" in m.email_masked for m in nams)


async def test_member_query_ignores_accents(jira: MockJira) -> None:
    result = await jira.list_members("SHOP", "Duc")
    assert [m.display_name for m in result] == ["Phạm Minh Đức"]


async def test_lan_only_in_hr(jira: MockJira) -> None:
    assert await jira.list_members("SHOP", "Lan") == []
    assert [m.display_name for m in await jira.list_members("HR", "lan")] == ["Đỗ Thị Lan"]


async def test_unknown_project(jira: MockJira) -> None:
    with pytest.raises(JiraNotFound):
        await jira.list_members("XYZ")


@pytest.mark.parametrize("project", ["SHOP", "HR"])
async def test_each_project_has_three_sprint_states(jira: MockJira, project: str) -> None:
    sprints = await jira.list_sprints(project)
    assert sorted(s.state for s in sprints) == ["active", "closed", "future"]
    active = await jira.list_sprints(project, "active")
    assert len(active) == 1 and active[0].state == "active"


async def test_about_twenty_issues_with_story_points(jira: MockJira) -> None:
    shop = await jira.search_issues("project = SHOP", max_results=100)
    hr = await jira.search_issues("project = HR", max_results=100)
    assert 18 <= len(shop) + len(hr) <= 25
    assert sum(1 for i in shop + hr if i.story_points is not None) >= 15


async def test_search_open_sprints(jira: MockJira) -> None:
    issues = await jira.search_issues("project = SHOP AND sprint in openSprints() ORDER BY key")
    keys = {i.key for i in issues}
    assert "SHOP-105" in keys and "SHOP-114" in keys  # active + future
    assert "SHOP-101" not in keys  # chỉ thuộc sprint đã đóng
    assert "SHOP-104" in keys  # dời từ Sprint 11 sang Sprint 12


async def test_search_updated_since(jira: MockJira) -> None:
    issues = await jira.search_issues('project = SHOP AND updated >= "2026-11-09"')
    keys = {i.key for i in issues}
    assert {"SHOP-110", "SHOP-111"} <= keys
    assert "SHOP-105" not in keys  # thay đổi cuối 06/11


async def test_search_text_ignores_accents(jira: MockJira) -> None:
    issues = await jira.search_issues('project = SHOP AND text ~ "thanh toan"')
    assert {"SHOP-105", "SHOP-107"} <= {i.key for i in issues}


async def test_search_status_and_assignee(jira: MockJira) -> None:
    unassigned = await jira.search_issues("project = SHOP AND assignee is EMPTY")
    assert {i.key for i in unassigned} == {"SHOP-109", "SHOP-114", "SHOP-115"}
    not_done = await jira.search_issues('sprint = 12 AND statusCategory != Done')
    assert all(i.status_category != "done" for i in not_done)
    assert "SHOP-112" not in {i.key for i in not_done}


async def test_unsupported_jql_raises(jira: MockJira) -> None:
    with pytest.raises(JiraError, match="chưa hỗ trợ"):
        await jira.search_issues("project = SHOP OR project = HR")


async def test_stuck_in_review_changelog(jira: MockJira) -> None:
    issue = await jira.get_issue("SHOP-105")
    assert issue.status == "In Review"
    changelog = await jira.get_issue_changelog("SHOP-105")
    last = changelog[-1]
    assert last.items[0].field == "status" and last.items[0].to_value == "In Review"
    assert last.created.date() == date(2026, 11, 6)
    assert (jira.reference_now - last.created).days > 3


async def test_scenarios_present(jira: MockJira) -> None:
    today = jira.reference_now.date()
    overdue = await jira.get_issue("SHOP-106")
    assert overdue.due_date is not None and overdue.due_date < today
    assert overdue.status_category != "done"

    blocked = await jira.get_issue("SHOP-107")
    assert blocked.blocked_by == ["SHOP-105"]
    assert (await jira.get_issue("SHOP-105")).status_category != "done"

    added = await jira.get_issue_changelog("SHOP-108")
    sprint_change = [i for e in added for i in e.items if i.field == "Sprint"]
    assert sprint_change and sprint_change[0].to_value == "SHOP Sprint 12"

    assert (await jira.get_issue("SHOP-111")).flagged is True

    reopened = await jira.get_issue_changelog("SHOP-110")
    transitions = [(i.from_value, i.to_value) for e in reopened for i in e.items]
    assert ("Done", "In Progress") in transitions


async def test_create_issue_increments_key(jira: MockJira) -> None:
    first = await jira.create_issue(
        {
            "project": {"key": "SHOP"},
            "issuetype": {"name": "Task"},
            "summary": "Viết tài liệu API thanh toán",
            "description": "## Mục tiêu\nTài liệu cho đội FE",
            "assignee": {"accountId": "acc-nam-be"},
            "customfield_10016": 2,
            "customfield_10020": 12,
        }
    )
    second = await jira.create_issue(
        {"project": {"key": "SHOP"}, "issuetype": {"name": "Bug"}, "summary": "Lỗi nhỏ"}
    )
    assert first.key == "SHOP-116"
    assert second.key == "SHOP-117"
    assert first.url.endswith("/browse/SHOP-116")

    stored = await jira.get_issue("SHOP-116")
    assert stored.summary == "Viết tài liệu API thanh toán"
    assert stored.status == "To Do"
    assert stored.story_points == 2
    assert stored.sprint_ids == [12]
    assert stored.description_text and "Tài liệu cho đội FE" in stored.description_text


async def test_new_instance_does_not_see_created_issue(jira: MockJira) -> None:
    await jira.create_issue(
        {"project": {"key": "HR"}, "issuetype": {"name": "Task"}, "summary": "Việc mới"}
    )
    assert (await jira.get_issue("HR-6")).summary == "Việc mới"
    with pytest.raises(JiraNotFound):
        await MockJira().get_issue("HR-6")


@pytest.mark.parametrize(
    "fields",
    [
        {"project": {"key": "XYZ"}, "issuetype": {"name": "Task"}, "summary": "A"},
        {"project": {"key": "SHOP"}, "issuetype": {"name": "Task"}, "summary": "  "},
        {"project": {"key": "HR"}, "issuetype": {"name": "Bug"}, "summary": "A"},
        {
            "project": {"key": "SHOP"},
            "issuetype": {"name": "Task"},
            "summary": "A",
            "assignee": {"accountId": "acc-lan"},
        },
        {"project": {"key": "SHOP"}, "issuetype": {"name": "Sub-task"}, "summary": "A"},
    ],
)
async def test_create_issue_rejects_invalid(jira: MockJira, fields: dict) -> None:
    with pytest.raises(JiraError) as info:
        await jira.create_issue(fields)
    assert info.value.status_code == 400


async def test_create_meta(jira: MockJira) -> None:
    meta = {f.field_id: f for f in await jira.get_create_meta("SHOP", "task")}
    assert meta["summary"].required is True
    assert meta["description"].required is False
    assert "High" in meta["priority"].allowed_values
    sub = {f.field_id: f for f in await jira.get_create_meta("SHOP", "Sub-task")}
    assert sub["parent"].required is True
    with pytest.raises(JiraNotFound):
        await jira.get_create_meta("HR", "Bug")


async def test_transitions_and_fields(jira: MockJira) -> None:
    transitions = await jira.get_transitions("SHOP-105")
    assert "In Review" not in {t.to_status for t in transitions}
    assert "Done" in {t.to_status for t in transitions}
    names = {f.name: f.id for f in await jira.list_fields()}
    assert names["Story point estimate"] == "customfield_10016"
