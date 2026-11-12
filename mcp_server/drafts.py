"""Chuẩn hóa và băm bản nháp: dùng cho approval_token và idempotency (design 4.5)."""

import hashlib
import json
import unicodedata
from typing import Any

from domain.schemas import TaskDraft

# Không phải nội dung gửi lên Jira, nên không tính vào hash.
_EXCLUDED_FIELDS = {"confidence"}


def _normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


def canonical_draft(draft: TaskDraft) -> dict[str, Any]:
    """Dạng chuẩn của bản nháp: khác khoảng trắng đầu/cuối, dạng Unicode hay thứ tự
    labels thì vẫn cho cùng một kết quả."""
    data = draft.model_dump(mode="json", exclude=_EXCLUDED_FIELDS)
    for name, value in data.items():
        if isinstance(value, str):
            data[name] = _normalize_text(value)
    data["labels"] = sorted({_normalize_text(label) for label in draft.labels} - {""})
    return data


def _sha256(payload: Any) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def draft_hash(draft: TaskDraft) -> str:
    """Hash SHA-256 (hex) của một bản nháp đã chuẩn hóa."""
    return _sha256({"kind": "single", "draft": canonical_draft(draft)})


def drafts_hash(drafts: list[TaskDraft]) -> str:
    """Hash của cả danh sách bản nháp (giữ thứ tự), dùng cho create_tasks_bulk."""
    return _sha256({"kind": "bulk", "drafts": [canonical_draft(d) for d in drafts]})
