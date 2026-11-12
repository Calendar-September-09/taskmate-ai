"""Khớp tên tiếng Việt người dùng nói ("Nam", "anh Đức") với thành viên Jira (design 4.1, 4.5).

Nhiều người khớp thì trả Ambiguous để agent hỏi lại, không tự chọn.
"""

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict
from rapidfuzz import fuzz

from domain.text import normalize_vi

FUZZY_THRESHOLD = 88.0
FUZZY_MARGIN = 5.0
SUGGESTION_THRESHOLD = 60.0
MAX_SUGGESTIONS = 3

# Xưng hô hay đứng trước tên; chỉ bỏ khi sau đó vẫn còn tên.
_HONORIFICS = frozenset({"anh", "chi", "em", "ban", "co", "chu", "a", "c", "e", "ms", "mr"})


class MemberLike(Protocol):
    """Bất kỳ đối tượng nào có account_id và display_name (ví dụ mcp_server.models.Member)."""

    @property
    def account_id(self) -> str: ...

    @property
    def display_name(self) -> str: ...


class _Result(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)


class Unique(_Result):
    """Khớp đúng một người."""

    member: Any


class Ambiguous(_Result):
    """Nhiều người cùng khớp; agent phải hỏi lại."""

    candidates: list[Any]


class NotFound(_Result):
    """Không ai khớp; kèm vài gợi ý gần giống (có thể rỗng)."""

    suggestions: list[Any] = []


MatchResult = Unique | Ambiguous | NotFound


def _clean_query(name: str) -> list[str]:
    tokens = normalize_vi(name.replace("@", " ")).split()
    while len(tokens) > 1 and tokens[0] in _HONORIFICS:
        tokens = tokens[1:]
    return tokens


def _is_active(member: MemberLike) -> bool:
    return bool(getattr(member, "active", True))


def _one_or_many(members: list[Any]) -> MatchResult:
    return Unique(member=members[0]) if len(members) == 1 else Ambiguous(candidates=members)


def match_member(name: str, members: list[MemberLike]) -> MatchResult:
    """So khớp không dấu: nguyên tên → theo từng từ (ưu tiên tên gọi) → rapidfuzz."""
    tokens = _clean_query(name)
    active = [m for m in members if _is_active(m)]
    if not tokens or not active:
        return NotFound()
    query = " ".join(tokens)
    names = [(m, normalize_vi(m.display_name)) for m in active]

    exact = [m for m, full in names if full == query]
    if exact:
        return _one_or_many(exact)

    query_set = set(tokens)
    by_tokens = [(m, full.split()) for m, full in names if query_set <= set(full.split())]
    if by_tokens:
        given_name_hits = [m for m, parts in by_tokens if parts[-1] == tokens[-1]]
        return _one_or_many(given_name_hits or [m for m, _ in by_tokens])

    # ratio bắt lỗi gõ giữ thứ tự ("nma"), token_sort_ratio bắt đảo thứ tự từ ("Duc Pham Minh").
    scored = sorted(
        (
            (max(fuzz.ratio(query, full), fuzz.token_sort_ratio(query, full)), m)
            for m, full in names
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    best_score = scored[0][0]
    if best_score >= FUZZY_THRESHOLD:
        close = [m for score, m in scored if best_score - score < FUZZY_MARGIN]
        return _one_or_many(close)
    return NotFound(
        suggestions=[m for score, m in scored[:MAX_SUGGESTIONS] if score >= SUGGESTION_THRESHOLD]
    )
