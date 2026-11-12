"""Suy ra priority từ cách nói tiếng Việt (design 4.1: "gấp" → High).

Không có từ khóa thì trả None để Memory hoặc mặc định của dự án quyết định.
"""

import re

from pydantic import BaseModel

from domain.schemas import Priority
from domain.text import accents_consistent, fold_with_map, original_span

_ACCENTED_WORDS = frozenset({"gấp", "khẩn", "cấp", "ưu", "tiên", "cao"})
_HIGH_RE = re.compile(r"\b(?:khan\s+cap|khan|gap|uu\s+tien\s+cao)\b")
_NEGATION_RE = re.compile(r"\b(?:khong|chua|ko|k|cha)\s+(?:qua\s+|lam\s+|can\s+)?$")
_NEGATION_ACCENTED = frozenset({"không", "chưa", "chả", "quá", "lắm", "cần"})


class PriorityMatch(BaseModel):
    """Priority suy ra và cụm gốc để giao diện ghi “từ ‘gấp’”."""

    value: Priority
    matched: str


def detect_priority(text: str) -> PriorityMatch | None:
    """'Làm gấp nhé' -> High (matched='gấp'); 'không gấp' hoặc không có từ khóa -> None."""
    folded, index_map = fold_with_map(text)
    for m in _HIGH_RE.finditer(folded):
        segment = original_span(text, index_map, *m.span())
        if not accents_consistent(segment, _ACCENTED_WORDS):
            continue  # "gặp", "khăn": không phải từ chỉ mức gấp.
        before = folded[: m.start()]
        negation = _NEGATION_RE.search(before)
        if negation:
            neg_segment = original_span(text, index_map, *negation.span())
            if accents_consistent(neg_segment, _NEGATION_ACCENTED):
                continue
        return PriorityMatch(value="High", matched=segment)
    return None
