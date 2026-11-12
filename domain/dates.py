"""Chuyển cách nói ngày tiếng Việt sang ngày cụ thể (design mục 4.1).

LLM chỉ trích chuỗi gốc ("thứ 6 tuần sau"); hàm ở đây tính ngày theo múi giờ của dự án.
Nguyên tắc: không chắc thì trả None để agent hỏi lại, không đoán.
"""

import calendar
import re
from collections.abc import Callable
from datetime import date, datetime, timedelta, tzinfo

from pydantic import BaseModel

from domain.text import accents_consistent, fold_with_map, original_span

WEEKDAY_NAMES_VI = ("thứ Hai", "thứ Ba", "thứ Tư", "thứ Năm", "thứ Sáu", "thứ Bảy", "Chủ nhật")
FRIDAY = 4

# Dạng có dấu hợp lệ của các từ chỉ ngày; từ có dấu khác (thử, gặp, mài...) không được coi là ngày.
_ACCENTED_WORDS = frozenset(
    {
        "thứ", "tuần", "này", "sau", "sáu", "tới", "hôm", "nay", "ngày", "mai", "kia", "mốt",
        "cuối", "tháng", "chủ", "nhật", "hai", "ba", "tư", "bốn", "năm", "bảy",
    }
)  # fmt: skip

_WEEKDAY_WORDS = {
    "2": 0, "hai": 0,
    "3": 1, "ba": 1,
    "4": 2, "tu": 2, "bon": 2,
    "5": 3, "nam": 3,
    "6": 4, "sau": 4,
    "7": 5, "bay": 5,
}  # fmt: skip


class ParsedDate(BaseModel):
    """Kết quả parse: ngày cụ thể, cụm gốc đã khớp và lời giải thích cho người dùng."""

    value: date
    matched: str
    explanation: str


def format_vi_date(value: date) -> str:
    """date(2026, 11, 20) -> 'thứ Sáu 20/11/2026'."""
    return f"{WEEKDAY_NAMES_VI[value.weekday()]} {value:%d/%m/%Y}"


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _monday(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _next_month(year: int, month: int) -> tuple[int, int]:
    return (year + 1, 1) if month == 12 else (year, month + 1)


# Mỗi rule nhận (match, today, sprint_end) và trả (ngày, ghi chú) hoặc None nếu không chắc.
_Result = tuple[date, str] | None
_Rule = Callable[[re.Match[str], date, date | None], _Result]


def _full_date(m: re.Match[str], today: date, sprint_end: date | None) -> _Result:
    value = _safe_date(int(m["y"]), int(m["m"]), int(m["d"]))
    return (value, "") if value else None


def _day_month(m: re.Match[str], today: date, sprint_end: date | None) -> _Result:
    day, month = int(m["d"]), int(m["m"])
    year = today.year
    # Lệch từ 6 tháng về trước thì hiểu là năm sau (tháng 12 nói "05/01");
    # còn lại giữ năm nay, kể cả đã qua, để guardrail cảnh báo deadline ở quá khứ.
    if (today.year * 12 + today.month) - (year * 12 + month) >= 6:
        year += 1
    value = _safe_date(year, month, day)
    if value is None:
        return None
    note = "năm sau" if year != today.year else ""
    return value, note


def _day_of_month(m: re.Match[str], today: date, sprint_end: date | None) -> _Result:
    day = int(m["d"])
    if day >= today.day:
        value = _safe_date(today.year, today.month, day)
        return (value, "tháng này") if value else None
    year, month = _next_month(today.year, today.month)
    value = _safe_date(year, month, day)
    return (value, "tháng sau, vì ngày này tháng này đã qua") if value else None


def _weekday(m: re.Match[str], today: date, sprint_end: date | None) -> _Result:
    if m["sun"]:
        target = 6
    else:
        target = _WEEKDAY_WORDS[m["wd"] or m["twd"]]
    week = m["week"]
    if week in ("sau", "toi"):
        return _monday(today) + timedelta(days=7 + target), "tuần sau"
    if week == "nay":
        return _monday(today) + timedelta(days=target), "tuần này"
    if target == today.weekday():
        return None  # Trùng hôm nay: không rõ là hôm nay hay tuần sau.
    if target > today.weekday():
        return _monday(today) + timedelta(days=target), "tuần này"
    return _monday(today) + timedelta(days=7 + target), "tuần sau, vì tuần này đã qua"


def _end_of_week(m: re.Match[str], today: date, sprint_end: date | None) -> _Result:
    if m["week"] in ("sau", "toi"):
        return _monday(today) + timedelta(days=7 + FRIDAY), "ngày làm việc cuối của tuần sau"
    if today.weekday() > FRIDAY:
        return None  # Đã là thứ 7/CN: không rõ cuối tuần này hay tuần sau.
    return _monday(today) + timedelta(days=FRIDAY), "ngày làm việc cuối của tuần này"


def _next_week(m: re.Match[str], today: date, sprint_end: date | None) -> _Result:
    return _monday(today) + timedelta(days=7 + FRIDAY), "ngày làm việc cuối của tuần sau"


def _end_of_month(m: re.Match[str], today: date, sprint_end: date | None) -> _Result:
    year, month = today.year, today.month
    note = "ngày cuối tháng này"
    if m["next"]:
        year, month = _next_month(year, month)
        note = "ngày cuối tháng sau"
    return date(year, month, calendar.monthrange(year, month)[1]), note


def _end_of_sprint(m: re.Match[str], today: date, sprint_end: date | None) -> _Result:
    if sprint_end is None:
        return None
    return sprint_end, "ngày kết thúc sprint"


def _offset(days: int, note: str) -> _Rule:
    def rule(m: re.Match[str], today: date, sprint_end: date | None) -> _Result:
        return today + timedelta(days=days), note

    return rule


_WD = r"(?:thu\s*(?P<wd>[2-7]|hai|ba|tu|bon|nam|sau|bay)|t(?P<twd>[2-7])|(?P<sun>chu\s+nhat|cn))"

# Thứ tự quan trọng: mẫu dài/cụ thể trước, các khớp chồng lấn về sau bị bỏ qua.
_RULES: list[tuple[re.Pattern[str], _Rule]] = [
    (re.compile(r"\b(?P<d>\d{1,2})[/.-](?P<m>\d{1,2})[/.-](?P<y>\d{4})\b"), _full_date),
    (re.compile(r"\b(?P<d>\d{1,2})[/-](?P<m>\d{1,2})\b"), _day_month),
    (re.compile(r"\bngay\s+(?P<d>\d{1,2})\b"), _day_of_month),
    (re.compile(r"\bcuoi\s+tuan(?:\s+(?P<week>nay|sau|toi))?\b"), _end_of_week),
    (re.compile(rf"\b{_WD}(?:\s+tuan\s+(?P<week>nay|sau|toi))?\b"), _weekday),
    (re.compile(r"\bcuoi\s+thang(?:\s+(?:nay|(?P<next>sau|toi)))?\b"), _end_of_month),
    (re.compile(r"\bcuoi\s+sprint\b"), _end_of_sprint),
    (re.compile(r"\btuan\s+(?:sau|toi)\b"), _next_week),
    (re.compile(r"\bhom\s+nay\b"), _offset(0, "hôm nay")),
    (re.compile(r"\bngay\s+(?:kia|mot)\b"), _offset(2, "2 ngày nữa")),
    (re.compile(r"\b(?:ngay\s+)?mai\b"), _offset(1, "ngày mai")),
]

# "mốt" đứng một mình chỉ nhận khi viết có dấu, vì "mot" không dấu trùng với "một".
_MOT_ACCENTED = re.compile(r"(?<!\w)mốt(?!\w)", re.IGNORECASE)


def _today(now: datetime, tz: tzinfo) -> date:
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    return now.astimezone(tz).date()


def parse_vi_date(
    text: str, now: datetime, tz: tzinfo, sprint_end: date | None = None
) -> ParsedDate | None:
    """Parse một mốc ngày tiếng Việt (có dấu hoặc không dấu).

    Trả None khi không nhận ra, khi ngày không tồn tại (31/11), khi cần dữ liệu không có
    (cuối sprint mà thiếu sprint_end), hoặc khi câu có nhiều mốc ngày khác nhau.
    """
    today = _today(now, tz)
    folded, index_map = fold_with_map(text)
    taken: list[tuple[int, int]] = []
    found: list[tuple[date, str, str]] = []

    def overlaps(start: int, end: int) -> bool:
        return any(start < t_end and t_start < end for t_start, t_end in taken)

    for pattern, rule in _RULES:
        for m in pattern.finditer(folded):
            start, end = m.span()
            if overlaps(start, end):
                continue
            segment = original_span(text, index_map, start, end)
            if not accents_consistent(segment, _ACCENTED_WORDS):
                continue  # Ví dụ "thử 6", "mài": không phải từ chỉ ngày.
            taken.append((start, end))
            result = rule(m, today, sprint_end)
            if result is None:
                return None
            found.append((result[0], segment, result[1]))

    for m in _MOT_ACCENTED.finditer(text):
        found.append((today + timedelta(days=2), m.group(0), "2 ngày nữa"))

    if not found or len({value for value, _, _ in found}) > 1:
        return None
    value, segment, note = found[0]
    explanation = f"‘{segment.strip()}’ → {format_vi_date(value)}"
    if note:
        explanation += f" ({note})"
    return ParsedDate(value=value, matched=segment.strip(), explanation=explanation)
