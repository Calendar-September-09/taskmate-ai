"""Test TaskDraft có nguồn từng trường và MeetingExtraction."""

from datetime import date

import pytest
from pydantic import ValidationError

from domain import schemas
from domain.models import MeetingExtraction, Sourced, TaskDraft


def _full_draft(**overrides: object) -> TaskDraft:
    data: dict[str, object] = {
        "project_key": {"value": "SHOP", "source": "memory"},
        "summary": {"value": "Xây dựng API hoàn tiền", "source": "user"},
        "description": {"value": "## Mục tiêu\n...", "source": "inferred"},
        "assignee_id": {"value": "acc-duc", "source": "user", "evidence": "Đức"},
        "assignee_name": "Phạm Minh Đức",
        "priority": {"value": "High", "source": "inferred", "evidence": "gấp"},
        "due_date": {
            "value": date(2026, 11, 20),
            "source": "inferred",
            "evidence": "thứ 6 tuần sau",
        },
        "story_points": {"value": 3, "source": "user"},
        "labels": {"value": ["payment"], "source": "memory"},
        "sprint_id": {"value": 12, "source": "memory"},
        "confidence": 0.9,
    }
    data.update(overrides)
    return TaskDraft.model_validate(data)


@pytest.mark.parametrize(
    ("source", "evidence", "label"),
    [
        ("inferred", "gấp", "từ ‘gấp’"),
        ("user", "Đức", "từ ‘Đức’"),
        ("user", None, "người dùng nhập"),
        ("inferred", None, "AI suy ra"),
        ("memory", None, "từ bộ nhớ"),
        ("default", None, "mặc định"),
    ],
)
def test_sourced_label(source: str, evidence: str | None, label: str) -> None:
    assert Sourced[str](value="x", source=source, evidence=evidence).label == label


def test_defaults() -> None:
    draft = TaskDraft()
    assert draft.issue_type.value == "Task"
    assert draft.issue_type.label == "mặc định"
    assert draft.priority is None
    assert draft.missing_fields() == ["project_key", "summary", "description"]


def test_subtask_requires_parent() -> None:
    draft = _full_draft(issue_type={"value": "Sub-task", "source": "user"})
    assert draft.missing_fields() == ["parent_key"]
    with pytest.raises(ValueError, match="parent_key"):
        draft.to_payload()


def test_to_payload() -> None:
    payload = _full_draft().to_payload()
    assert isinstance(payload, schemas.TaskDraft)
    assert payload.project_key == "SHOP"
    assert payload.priority == "High"
    assert payload.due_date == date(2026, 11, 20)
    assert payload.assignee_id == "acc-duc"
    assert payload.sprint_id == 12
    assert payload.story_points == 3
    assert payload.labels == ["payment"]
    assert payload.confidence == 0.9


def test_epic_key_becomes_parent() -> None:
    draft = _full_draft(epic_key={"value": "SHOP-100", "source": "memory"})
    assert draft.to_payload().parent_key == "SHOP-100"


@pytest.mark.parametrize(
    "overrides",
    [
        {"summary": {"value": "x" * 121, "source": "user"}},
        {"summary": {"value": "   ", "source": "user"}},
        {"project_key": {"value": "shop", "source": "user"}},
        {"priority": {"value": "Gấp", "source": "inferred"}},
        {"epic_key": {"value": "SHOP", "source": "user"}},
        {"confidence": 1.5},
        {"summary": {"value": "Làm A", "source": "llm"}},
    ],
)
def test_invalid_drafts(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        _full_draft(**overrides)


def test_meeting_extraction_from_json() -> None:
    raw = {
        "tasks": [
            {
                "project_key": {"value": "SHOP", "source": "memory"},
                "summary": {"value": "Viết test E2E thanh toán", "source": "inferred"},
                "due_date": {"value": "2026-11-20", "source": "inferred", "evidence": "thứ 6"},
            }
        ],
        "decisions": ["Dùng VNPay sandbox đến hết sprint"],
        "unclear": ["Ai phụ trách phần email xác nhận?"],
    }
    extraction = MeetingExtraction.model_validate(raw)
    assert extraction.tasks[0].due_date is not None
    assert extraction.tasks[0].due_date.value == date(2026, 11, 20)
    assert extraction.tasks[0].missing_fields() == ["description"]
    assert extraction.decisions == ["Dùng VNPay sandbox đến hết sprint"]
    assert extraction.unclear == ["Ai phụ trách phần email xác nhận?"]
