"""Kiểm tra JiraClient bằng respx (giả lập HTTP, không gọi mạng)."""

import json
from collections.abc import AsyncIterator

import httpx
import pytest
import respx

from mcp_server.errors import JiraAuthError, JiraError, JiraNotFound, JiraRateLimited
from mcp_server.jira_client import JiraClient, parse_jira_datetime

BASE = "https://example.atlassian.net"
TOKEN = "super-secret-token-ABC123"
BLOCKS = {"name": "Blocks", "inward": "is blocked by", "outward": "blocks"}


class FakeSleep:
    def __init__(self) -> None:
        self.calls: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


@pytest.fixture
def sleep() -> FakeSleep:
    return FakeSleep()


@pytest.fixture
async def client(sleep: FakeSleep) -> AsyncIterator[JiraClient]:
    jira = JiraClient(BASE, "sm@example.com", TOKEN, sleep=sleep)
    yield jira
    await jira.aclose()


def raw_issue(key: str, **fields: object) -> dict:
    base = {
        "summary": f"Issue {key}",
        "status": {"name": "In Progress", "statusCategory": {"key": "indeterminate"}},
        "issuetype": {"name": "Task"},
        "created": "2026-11-02T09:00:00.000+0700",
        "updated": "2026-11-05T10:30:00.000+0700",
    }
    base.update(fields)
    return {"id": "1", "key": key, "fields": base}


@respx.mock
async def test_retry_on_429_then_success(client: JiraClient, sleep: FakeSleep) -> None:
    route = respx.get(f"{BASE}/rest/api/3/issue/SHOP-1").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "2"}),
            httpx.Response(429),
            httpx.Response(200, json=raw_issue("SHOP-1")),
        ]
    )
    issue = await client.get_issue("SHOP-1")
    assert issue.key == "SHOP-1"
    assert route.call_count == 3
    assert sleep.calls == [2.0, 1.0]  # Retry-After, rồi backoff 0.5 * 2**1


@respx.mock
async def test_429_forever_raises_rate_limited(client: JiraClient, sleep: FakeSleep) -> None:
    route = respx.get(f"{BASE}/rest/api/3/issue/SHOP-1").mock(return_value=httpx.Response(429))
    with pytest.raises(JiraRateLimited):
        await client.get_issue("SHOP-1")
    assert route.call_count == 4  # 1 lần + 3 lần thử lại
    assert len(sleep.calls) == 3


@respx.mock
async def test_5xx_retried_for_reads(client: JiraClient) -> None:
    route = respx.get(f"{BASE}/rest/api/3/issue/SHOP-1").mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json=raw_issue("SHOP-1"))]
    )
    await client.get_issue("SHOP-1")
    assert route.call_count == 2


@respx.mock
async def test_timeout_retried_for_reads(client: JiraClient) -> None:
    route = respx.get(f"{BASE}/rest/api/3/issue/SHOP-1").mock(
        side_effect=[httpx.ConnectTimeout("timeout"), httpx.Response(200, json=raw_issue("SHOP-1"))]
    )
    await client.get_issue("SHOP-1")
    assert route.call_count == 2


@respx.mock
async def test_5xx_not_retried_for_create(client: JiraClient) -> None:
    route = respx.post(f"{BASE}/rest/api/3/issue").mock(return_value=httpx.Response(503))
    with pytest.raises(JiraError) as info:
        await client.create_issue({"summary": "A"})
    assert route.call_count == 1  # không thử lại để tránh tạo trùng
    assert info.value.status_code == 503


@respx.mock
async def test_401_does_not_leak_token(client: JiraClient) -> None:
    respx.get(f"{BASE}/rest/api/3/issue/SHOP-1").mock(
        return_value=httpx.Response(401, json={"errorMessages": [f"bad token {TOKEN}"]})
    )
    with pytest.raises(JiraAuthError) as info:
        await client.get_issue("SHOP-1")
    exc = info.value
    for text in (str(exc), repr(exc), str(exc.args), repr(client)):
        assert TOKEN not in text
    assert "JIRA_API_TOKEN" in str(exc)
    assert exc.status_code == 401


@respx.mock
async def test_error_detail_is_redacted(client: JiraClient) -> None:
    respx.post(f"{BASE}/rest/api/3/issue").mock(
        return_value=httpx.Response(400, json={"errors": {"summary": f"echo {TOKEN}"}})
    )
    with pytest.raises(JiraError) as info:
        await client.create_issue({"summary": "A"})
    assert TOKEN not in str(info.value)
    assert "summary" in str(info.value)


@respx.mock
async def test_404_raises_not_found(client: JiraClient) -> None:
    respx.get(f"{BASE}/rest/api/3/issue/NOPE-1").mock(
        return_value=httpx.Response(404, json={"errorMessages": ["Issue does not exist"]})
    )
    with pytest.raises(JiraNotFound, match="Không tìm thấy"):
        await client.get_issue("NOPE-1")


@respx.mock
async def test_create_issue_converts_description_to_adf(client: JiraClient) -> None:
    route = respx.post(f"{BASE}/rest/api/3/issue").mock(
        return_value=httpx.Response(201, json={"id": "10042", "key": "SHOP-142", "self": "x"})
    )
    created = await client.create_issue(
        {
            "project": {"key": "SHOP"},
            "issuetype": {"name": "Task"},
            "summary": "Xây dựng API thanh toán VNPay",
            "description": "## Mục tiêu\nThanh toán qua VNPay\n\n- AC 1\n- AC 2",
        }
    )
    assert created.key == "SHOP-142"
    assert created.url == f"{BASE}/browse/SHOP-142"
    body = json.loads(route.calls.last.request.content)
    description = body["fields"]["description"]
    assert description["type"] == "doc" and description["version"] == 1
    assert [n["type"] for n in description["content"]] == ["heading", "paragraph", "bulletList"]


@respx.mock
async def test_basic_auth_header_sent(client: JiraClient) -> None:
    route = respx.get(f"{BASE}/rest/api/3/field").mock(return_value=httpx.Response(200, json=[]))
    await client.list_fields()
    assert route.calls.last.request.headers["Authorization"].startswith("Basic ")


@respx.mock
async def test_search_uses_jql_endpoint_and_paginates(client: JiraClient) -> None:
    route = respx.post(f"{BASE}/rest/api/3/search/jql").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "issues": [
                        raw_issue(
                            "SHOP-1",
                            customfield_10016=5,
                            customfield_10020=[{"id": 12, "name": "Sprint 12"}],
                            customfield_10021=[{"value": "Impediment"}],
                            duedate="2026-11-10",
                            issuelinks=[
                                {"type": BLOCKS, "inwardIssue": {"key": "SHOP-9"}},
                                {"type": BLOCKS, "outwardIssue": {"key": "SHOP-7"}},
                            ],
                            assignee={"accountId": "acc-1", "displayName": "Nguyễn Văn Nam"},
                        )
                    ],
                    "nextPageToken": "page-2",
                },
            ),
            httpx.Response(200, json={"issues": [raw_issue("SHOP-2")], "isLast": True}),
        ]
    )
    issues = await client.search_issues("project = SHOP", max_results=10)

    assert [i.key for i in issues] == ["SHOP-1", "SHOP-2"]
    first_body = json.loads(route.calls[0].request.content)
    second_body = json.loads(route.calls[1].request.content)
    assert first_body["jql"] == "project = SHOP"
    assert "customfield_10016" in first_body["fields"]
    assert "nextPageToken" not in first_body
    assert second_body["nextPageToken"] == "page-2"

    issue = issues[0]
    assert issue.story_points == 5.0
    assert issue.sprint_ids == [12]
    assert issue.flagged is True
    assert issue.blocked_by == ["SHOP-9"]  # SHOP-7 là issue bị SHOP-1 chặn, không tính
    assert issue.assignee_name == "Nguyễn Văn Nam"
    assert issue.due_date.isoformat() == "2026-11-10"
    assert issues[1].flagged is False and issues[1].story_points is None


@respx.mock
async def test_search_respects_max_results(client: JiraClient) -> None:
    route = respx.post(f"{BASE}/rest/api/3/search/jql").mock(
        return_value=httpx.Response(
            200, json={"issues": [raw_issue("SHOP-1"), raw_issue("SHOP-2")], "nextPageToken": "x"}
        )
    )
    issues = await client.search_issues("project = SHOP", max_results=2)
    assert len(issues) == 2
    assert route.call_count == 1
    assert json.loads(route.calls[0].request.content)["maxResults"] == 2


@respx.mock
async def test_list_sprints_merges_boards(client: JiraClient) -> None:
    respx.get(f"{BASE}/rest/agile/1.0/board").mock(
        return_value=httpx.Response(200, json={"values": [{"id": 1}, {"id": 2}], "isLast": True})
    )
    sprint = {
        "id": 12,
        "name": "Sprint 12",
        "state": "active",
        "startDate": "2026-11-02T02:00:00.000Z",
        "endDate": "2026-11-13T10:00:00.000Z",
        "originBoardId": 1,
    }
    respx.get(f"{BASE}/rest/agile/1.0/board/1/sprint").mock(
        return_value=httpx.Response(200, json={"values": [sprint], "isLast": True})
    )
    respx.get(f"{BASE}/rest/agile/1.0/board/2/sprint").mock(
        return_value=httpx.Response(
            200,
            json={
                "values": [sprint, {"id": 13, "name": "Sprint 13", "state": "future"}],
                "isLast": True,
            },
        )
    )
    sprints = await client.list_sprints("SHOP", "active,future")
    assert [s.id for s in sprints] == [12, 13]
    assert sprints[0].start_date is not None and sprints[0].start_date.tzinfo is not None


@respx.mock
async def test_list_members_uses_assignable_search(client: JiraClient) -> None:
    route = respx.get(f"{BASE}/rest/api/3/user/assignable/search").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "accountId": "a1",
                    "displayName": "Nguyễn Văn Nam",
                    "emailAddress": "nam@example.com",
                },
                {"accountId": "a2", "displayName": "Trần Hoài Nam"},
            ],
        )
    )
    members = await client.list_members("SHOP", "Nam")
    params = route.calls.last.request.url.params
    assert params["project"] == "SHOP" and params["query"] == "Nam"
    assert members[0].email_masked == "n***@example.com"
    assert members[1].email_masked is None


@respx.mock
async def test_changelog_paginates(client: JiraClient) -> None:
    history = {
        "id": "1",
        "created": "2026-11-06T16:30:00.000+0700",
        "author": {"accountId": "a1"},
        "items": [{"field": "status", "fromString": "In Progress", "toString": "In Review"}],
    }
    respx.get(f"{BASE}/rest/api/3/issue/SHOP-1/changelog").mock(
        side_effect=[
            httpx.Response(200, json={"values": [history], "isLast": False}),
            httpx.Response(200, json={"values": [{**history, "id": "2"}], "isLast": True}),
        ]
    )
    changelog = await client.get_issue_changelog("SHOP-1")
    assert [c.id for c in changelog] == ["1", "2"]
    assert changelog[0].items[0].to_value == "In Review"


@respx.mock
async def test_create_meta(client: JiraClient) -> None:
    base = f"{BASE}/rest/api/3/issue/createmeta/SHOP/issuetypes"
    respx.get(base).mock(
        return_value=httpx.Response(200, json={"issueTypes": [{"id": "10001", "name": "Task"}]})
    )
    respx.get(f"{base}/10001").mock(
        return_value=httpx.Response(
            200,
            json={
                "fields": [
                    {"fieldId": "summary", "name": "Summary", "required": True},
                    {
                        "fieldId": "priority",
                        "name": "Priority",
                        "required": False,
                        "hasDefaultValue": True,
                        "allowedValues": [{"name": "High"}, {"name": "Low"}],
                    },
                ],
                "total": 2,
            },
        )
    )
    meta = {f.field_id: f for f in await client.get_create_meta("SHOP", "task")}
    assert meta["summary"].required is True
    assert meta["priority"].allowed_values == ["High", "Low"]
    with pytest.raises(JiraNotFound):
        await client.get_create_meta("SHOP", "Epic")


@respx.mock
async def test_transitions(client: JiraClient) -> None:
    respx.get(f"{BASE}/rest/api/3/issue/SHOP-1/transitions").mock(
        return_value=httpx.Response(
            200, json={"transitions": [{"id": "31", "name": "Done", "to": {"name": "Done"}}]}
        )
    )
    transitions = await client.get_transitions("SHOP-1")
    assert transitions[0].id == "31" and transitions[0].to_status == "Done"


def test_parse_jira_datetime_formats() -> None:
    a = parse_jira_datetime("2026-11-02T09:00:00.000+0700")
    b = parse_jira_datetime("2026-11-02T02:00:00.000Z")
    assert a == b
    assert parse_jira_datetime(None) is None
