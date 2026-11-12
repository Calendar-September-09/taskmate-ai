"""Kiểm tra approval_token: ký HMAC, thời hạn, dùng một lần, gắn với bản nháp."""

from datetime import timedelta

import pytest

from domain.schemas import TaskDraft
from mcp_server.approval import ApprovalError, issue_token, verify_token
from mcp_server.drafts import draft_hash, drafts_hash
from mcp_server.store import ServerStore
from tests.conftest import APPROVAL_SECRET, FakeClock


def _issue(draft: TaskDraft, clock: FakeClock, secret: str = APPROVAL_SECRET) -> str:
    return issue_token(draft_hash(draft), "scrum-master", secret, clock.now())


def _reason(exc: pytest.ExceptionInfo[ApprovalError]) -> str:
    return exc.value.reason


def test_valid_token(draft: TaskDraft, store: ServerStore, clock: FakeClock) -> None:
    token = _issue(draft, clock)
    payload = verify_token(token, draft_hash(draft), APPROVAL_SECRET, store, clock.now())
    assert payload.approver == "scrum-master"
    assert payload.h == draft_hash(draft)


def test_tampered_signature(draft: TaskDraft, store: ServerStore, clock: FakeClock) -> None:
    token = _issue(draft, clock)
    tampered = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    with pytest.raises(ApprovalError) as exc:
        verify_token(tampered, draft_hash(draft), APPROVAL_SECRET, store, clock.now())
    assert _reason(exc) == "bad_signature"


def test_wrong_secret(draft: TaskDraft, store: ServerStore, clock: FakeClock) -> None:
    token = _issue(draft, clock, secret="another-secret")
    with pytest.raises(ApprovalError) as exc:
        verify_token(token, draft_hash(draft), APPROVAL_SECRET, store, clock.now())
    assert _reason(exc) == "bad_signature"


@pytest.mark.parametrize("token", ["", "abc", "v1.abc", "v2.a.b"])
def test_malformed(token: str, draft: TaskDraft, store: ServerStore, clock: FakeClock) -> None:
    with pytest.raises(ApprovalError) as exc:
        verify_token(token, draft_hash(draft), APPROVAL_SECRET, store, clock.now())
    assert _reason(exc) in {"missing_token", "malformed"}


def test_expired_after_30_minutes(draft: TaskDraft, store: ServerStore, clock: FakeClock) -> None:
    token = _issue(draft, clock)
    clock.advance(timedelta(minutes=31))
    with pytest.raises(ApprovalError) as exc:
        verify_token(token, draft_hash(draft), APPROVAL_SECRET, store, clock.now())
    assert _reason(exc) == "expired"


def test_still_valid_at_29_minutes(draft: TaskDraft, store: ServerStore, clock: FakeClock) -> None:
    token = _issue(draft, clock)
    clock.advance(timedelta(minutes=29))
    verify_token(token, draft_hash(draft), APPROVAL_SECRET, store, clock.now())


def test_used_twice(draft: TaskDraft, store: ServerStore, clock: FakeClock) -> None:
    token = _issue(draft, clock)
    verify_token(token, draft_hash(draft), APPROVAL_SECRET, store, clock.now())
    with pytest.raises(ApprovalError) as exc:
        verify_token(token, draft_hash(draft), APPROVAL_SECRET, store, clock.now())
    assert _reason(exc) == "used"


def test_used_survives_new_store(
    draft: TaskDraft, store: ServerStore, clock: FakeClock, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    token = _issue(draft, clock)
    verify_token(token, draft_hash(draft), APPROVAL_SECRET, store, clock.now())
    reopened = ServerStore(tmp_path / "taskmate.db")  # mô phỏng khởi động lại server
    with pytest.raises(ApprovalError) as exc:
        verify_token(token, draft_hash(draft), APPROVAL_SECRET, reopened, clock.now())
    assert _reason(exc) == "used"


def test_draft_changed_after_approval(
    draft: TaskDraft, store: ServerStore, clock: FakeClock
) -> None:
    token = _issue(draft, clock)
    edited = draft.model_copy(update={"due_date": None})
    with pytest.raises(ApprovalError) as exc:
        verify_token(token, draft_hash(edited), APPROVAL_SECRET, store, clock.now())
    assert _reason(exc) == "draft_changed"


def test_missing_secret(draft: TaskDraft, store: ServerStore, clock: FakeClock) -> None:
    token = _issue(draft, clock)
    with pytest.raises(ApprovalError) as exc:
        verify_token(token, draft_hash(draft), "", store, clock.now())
    assert _reason(exc) == "missing_secret"
    with pytest.raises(ApprovalError):
        issue_token(draft_hash(draft), "sm", "", clock.now())


def test_message_never_contains_token(
    draft: TaskDraft, store: ServerStore, clock: FakeClock
) -> None:
    token = _issue(draft, clock)
    verify_token(token, draft_hash(draft), APPROVAL_SECRET, store, clock.now())
    with pytest.raises(ApprovalError) as exc:
        verify_token(token, draft_hash(draft), APPROVAL_SECRET, store, clock.now())
    assert token not in str(exc.value)


def test_hash_normalization(draft: TaskDraft) -> None:
    same = draft.model_copy(
        update={
            "summary": f"  {draft.summary}  ",
            "labels": ["backend", " payment", "payment"],
            "confidence": 0.3,  # không phải nội dung Jira
            "description": draft.description.replace("\n", "\r\n"),
        }
    )
    assert draft_hash(same) == draft_hash(draft)
    assert draft_hash(draft.model_copy(update={"summary": "Khác"})) != draft_hash(draft)


def test_bulk_hash_depends_on_order(draft: TaskDraft) -> None:
    other = draft.model_copy(update={"summary": "Viết test thanh toán"})
    assert drafts_hash([draft, other]) != drafts_hash([other, draft])
    assert drafts_hash([draft]) != draft_hash(draft)
