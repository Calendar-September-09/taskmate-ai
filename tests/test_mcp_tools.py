"""Gọi trực tiếp các hàm tool của MCP Server với MockJira."""

from datetime import datetime, timedelta

import pytest

from domain.schemas import TaskDraft
from mcp_server.approval import issue_token
from mcp_server.drafts import draft_hash, drafts_hash
from mcp_server.models import Issue
from mcp_server.tools import TaskMateToolError, TaskMateTools, compare_issue
from tests.conftest import APPROVAL_SECRET, TZ, CountingMockJira, FakeClock


def approve(draft: TaskDraft, clock: FakeClock) -> str:
    return issue_token(draft_hash(draft), "scrum-master", APPROVAL_SECRET, clock.now())


def approve_bulk(drafts: list[TaskDraft], clock: FakeClock) -> str:
    return issue_token(drafts_hash(drafts), "scrum-master", APPROVAL_SECRET, clock.now())


async def count_issues(jira: CountingMockJira, project: str = "SHOP") -> int:
    return len(await jira.search_issues(f"project = {project}", max_results=1000))


# ---------------------------------------------------------------- Ghi: từ chối


async def test_wrong_token_rejected(
    tools: TaskMateTools, jira: CountingMockJira, draft: TaskDraft
) -> None:
    before = await count_issues(jira)
    for token in ["", "khong-phai-token", approve(draft, FakeClock()) + "x"]:
        with pytest.raises(TaskMateToolError) as exc:
            await tools.create_task(draft, token)
        assert exc.value.code.startswith("approval_")
    assert await count_issues(jira) == before


async def test_expired_token_rejected(
    tools: TaskMateTools, jira: CountingMockJira, draft: TaskDraft, clock: FakeClock
) -> None:
    token = approve(draft, clock)
    clock.advance(timedelta(minutes=31))
    before = await count_issues(jira)
    with pytest.raises(TaskMateToolError) as exc:
        await tools.create_task(draft, token)
    assert exc.value.code == "approval_expired"
    assert await count_issues(jira) == before


async def test_used_token_rejected(
    tools: TaskMateTools, jira: CountingMockJira, draft: TaskDraft, clock: FakeClock
) -> None:
    token = approve(draft, clock)
    await tools.create_task(draft, token)
    after_first = await count_issues(jira)
    with pytest.raises(TaskMateToolError) as exc:
        await tools.create_task(draft, token)
    assert exc.value.code == "approval_used"
    assert await count_issues(jira) == after_first


async def test_edited_draft_rejected(
    tools: TaskMateTools, jira: CountingMockJira, draft: TaskDraft, clock: FakeClock
) -> None:
    token = approve(draft, clock)
    edited = draft.model_copy(update={"assignee_id": "acc-ha"})
    before = await count_issues(jira)
    with pytest.raises(TaskMateToolError) as exc:
        await tools.create_task(edited, token)
    assert exc.value.code == "approval_draft_changed"
    assert await count_issues(jira) == before


async def test_bulk_token_for_other_list_rejected(
    tools: TaskMateTools, draft: TaskDraft, clock: FakeClock
) -> None:
    other = draft.model_copy(update={"summary": "Viết test thanh toán"})
    token = approve_bulk([draft], clock)
    with pytest.raises(TaskMateToolError) as exc:
        await tools.create_tasks_bulk([draft, other], token)
    assert exc.value.code == "approval_draft_changed"


async def test_single_token_not_valid_for_bulk(
    tools: TaskMateTools, draft: TaskDraft, clock: FakeClock
) -> None:
    with pytest.raises(TaskMateToolError):
        await tools.create_tasks_bulk([draft], approve(draft, clock))


# ---------------------------------------------------------------- Ghi: thành công


async def test_create_verified(
    tools: TaskMateTools, jira: CountingMockJira, draft: TaskDraft, clock: FakeClock
) -> None:
    before = await count_issues(jira)
    result = await tools.create_task(draft, approve(draft, clock))
    assert result.verified is True
    assert result.mismatches == []
    assert result.already_existed is False
    assert result.url == f"{jira.base_url}/browse/{result.key}"
    assert await count_issues(jira) == before + 1

    issue = await jira.get_issue(result.key)
    assert issue.summary == draft.summary
    assert issue.assignee_id == "acc-duc"
    assert 12 in issue.sprint_ids
    assert issue.story_points == 3


async def test_same_draft_twice_creates_one_issue(
    tools: TaskMateTools, jira: CountingMockJira, draft: TaskDraft, clock: FakeClock
) -> None:
    before = await count_issues(jira)
    first = await tools.create_task(draft, approve(draft, clock))
    # Duyệt lại cùng bản nháp (chỉ khác khoảng trắng) và gửi lại.
    again = draft.model_copy(update={"summary": draft.summary + "  "})
    second = await tools.create_task(again, approve(again, clock))
    assert second.key == first.key
    assert second.already_existed is True
    assert second.verified is True
    assert await count_issues(jira) == before + 1


async def test_recreate_when_issue_deleted_on_jira(
    tools: TaskMateTools, jira: CountingMockJira, draft: TaskDraft, clock: FakeClock
) -> None:
    first = await tools.create_task(draft, approve(draft, clock))
    before = await count_issues(jira)
    del jira._issues[first.key]  # người dùng xóa issue trực tiếp trên Jira
    second = await tools.create_task(draft, approve(draft, clock))
    # Không trả key đã chết; tạo issue mới. (Mock có thể cấp lại cùng số, Jira thật thì không.)
    assert second.already_existed is False
    assert (await jira.get_issue(second.key)).summary == draft.summary
    assert await count_issues(jira) == before


async def test_jira_rejects_creation(
    tools: TaskMateTools, draft: TaskDraft, clock: FakeClock
) -> None:
    bad = draft.model_copy(update={"assignee_id": "acc-lan"})  # không thuộc SHOP
    with pytest.raises(TaskMateToolError) as exc:
        await tools.create_task(bad, approve(bad, clock))
    assert exc.value.code == "jira_error"


def test_compare_issue_reports_mismatch(draft: TaskDraft) -> None:
    issue = Issue(
        key="SHOP-99",
        id="1",
        summary=draft.summary,
        issue_type="Task",
        status="To Do",
        status_category="new",
        assignee_id="acc-ha",
        priority="High",
        story_points=3,
        due_date=draft.due_date,
        sprint_ids=[],
        labels=["backend", "payment"],
    )
    mismatches = compare_issue(draft, issue)
    assert any(m.startswith("assignee_id") for m in mismatches)
    assert any(m.startswith("sprint_id") for m in mismatches)
    assert len(mismatches) == 2


async def test_bulk_partial_failure_and_rerun(
    tools: TaskMateTools, jira: CountingMockJira, draft: TaskDraft, clock: FakeClock
) -> None:
    drafts = [
        draft,
        draft.model_copy(update={"summary": "Sửa lỗi giỏ hàng", "assignee_id": "acc-lan"}),
        draft.model_copy(update={"summary": "Viết test thanh toán", "issue_type": "Bug"}),
    ]
    before = await count_issues(jira)
    result = await tools.create_tasks_bulk(drafts, approve_bulk(drafts, clock))
    assert (result.created, result.failed) == (2, 1)
    assert [item.ok for item in result.items] == [True, False, True]
    assert result.items[1].error and "jira_error" in result.items[1].error
    assert await count_issues(jira) == before + 2

    rerun = await tools.create_tasks_bulk(drafts, approve_bulk(drafts, clock))
    assert await count_issues(jira) == before + 2
    assert rerun.items[0].result and rerun.items[0].result.already_existed
    assert rerun.items[0].result.key == result.items[0].result.key  # type: ignore[union-attr]


# ---------------------------------------------------------------- Đọc


async def test_list_members_masks_email(tools: TaskMateTools) -> None:
    result = await tools.list_members("SHOP", "nam")
    assert {m.display_name for m in result.members} == {"Nguyễn Văn Nam", "Trần Hoài Nam"}
    dumped = result.model_dump_json()
    assert "***@" in dumped
    assert "nam.nguyen" not in dumped


async def test_members_and_sprints_cached_5_minutes(
    tools: TaskMateTools, jira: CountingMockJira, clock: FakeClock
) -> None:
    await tools.list_members("SHOP")
    await tools.list_members("SHOP")
    await tools.list_sprints("SHOP", "active")
    await tools.list_sprints("SHOP", "active")
    assert jira.calls == {"list_members": 1, "list_sprints": 1}

    await tools.list_members("SHOP", "duc")  # tham số khác: gọi Jira
    assert jira.calls["list_members"] == 2

    clock.advance(timedelta(seconds=301))
    await tools.list_members("SHOP")
    await tools.list_sprints("SHOP", "active")
    assert jira.calls == {"list_members": 3, "list_sprints": 2}


async def test_list_projects_and_sprints(tools: TaskMateTools) -> None:
    projects = await tools.list_projects()
    assert {p.key for p in projects.projects} == {"SHOP", "HR"}
    sprints = await tools.list_sprints("SHOP", "active")
    assert [s.id for s in sprints.sprints] == [12]


async def test_get_sprint_issues(tools: TaskMateTools) -> None:
    result = await tools.get_sprint_issues(12)
    assert result.count == 10
    assert all(12 in i.sprint_ids for i in result.issues)


async def test_search_issues_text_without_accents(tools: TaskMateTools) -> None:
    exact = await tools.search_issues("SHOP", text="thanh toán")
    plain = await tools.search_issues("SHOP", text="thanh toan")
    assert exact.count > 0
    assert [i.key for i in plain.issues] == [i.key for i in exact.issues]


async def test_search_issues_quotes_cannot_break_jql(tools: TaskMateTools) -> None:
    # Dấu nháy bị bỏ, nên không chèn thêm điều kiện JQL được.
    result = await tools.search_issues("SHOP", text='thanh toan" OR project = "HR')
    assert all(i.key.startswith("SHOP-") for i in result.issues)


async def test_search_issues_updated_since(tools: TaskMateTools) -> None:
    since = datetime(2026, 11, 11, 9, 0, tzinfo=TZ)
    result = await tools.search_issues("SHOP", updated_since=since, max_results=100)
    assert all(i.updated and i.updated >= since for i in result.issues)
    everything = await tools.search_issues("SHOP", max_results=100)
    assert result.count < everything.count


async def test_changelog_and_create_meta(tools: TaskMateTools) -> None:
    sprint = await tools.get_sprint_issues(12)
    key = sprint.issues[0].key
    changelog = await tools.get_issue_changelog(key)
    assert changelog.issue_key == key
    meta = await tools.get_create_meta("SHOP", "Task")
    assert {f.field_id for f in meta.fields if f.required} >= {"project", "summary"}


async def test_read_error_is_tool_error(tools: TaskMateTools) -> None:
    with pytest.raises(TaskMateToolError) as exc:
        await tools.list_members("NOPE")
    assert exc.value.code == "jira_error"
