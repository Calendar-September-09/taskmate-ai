"""Test parse_vi_date với now cố định: thứ Năm 12/11/2026, giờ Việt Nam."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from domain.dates import format_vi_date, parse_vi_date

TZ = ZoneInfo("Asia/Ho_Chi_Minh")
NOW = datetime(2026, 11, 12, 9, 0, tzinfo=TZ)
SPRINT_END = date(2026, 11, 13)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Tương đối theo ngày
        ("hôm nay", date(2026, 11, 12)),
        ("hom nay", date(2026, 11, 12)),
        ("mai", date(2026, 11, 13)),
        ("ngày mai", date(2026, 11, 13)),
        ("NGAY MAI", date(2026, 11, 13)),
        ("ngày kia", date(2026, 11, 14)),
        ("ngay kia", date(2026, 11, 14)),
        ("ngày mốt", date(2026, 11, 14)),
        ("mốt", date(2026, 11, 14)),
        # Thứ trong tuần: chưa qua → tuần này, đã qua → tuần sau
        ("thứ 6", date(2026, 11, 13)),
        ("thứ sáu", date(2026, 11, 13)),
        ("thu 6", date(2026, 11, 13)),
        ("T6", date(2026, 11, 13)),
        ("thứ 7", date(2026, 11, 14)),
        ("thứ bảy", date(2026, 11, 14)),
        ("chủ nhật", date(2026, 11, 15)),
        ("chu nhat", date(2026, 11, 15)),
        ("CN", date(2026, 11, 15)),
        ("thứ 2", date(2026, 11, 16)),
        ("thứ hai", date(2026, 11, 16)),
        ("thứ 3", date(2026, 11, 17)),
        ("thứ tư", date(2026, 11, 18)),
        ("thu tu", date(2026, 11, 18)),
        # Có "tuần này" / "tuần sau"
        ("thứ 6 tuần sau", date(2026, 11, 20)),
        ("thu 6 tuan sau", date(2026, 11, 20)),
        ("thứ sáu tuần sau", date(2026, 11, 20)),
        ("thu sau tuan sau", date(2026, 11, 20)),
        ("thứ 2 tuần tới", date(2026, 11, 16)),
        ("thứ 5 tuần sau", date(2026, 11, 19)),
        ("chủ nhật tuần sau", date(2026, 11, 22)),
        ("thứ 6 tuần này", date(2026, 11, 13)),
        ("tuần sau", date(2026, 11, 20)),
        ("tuan toi", date(2026, 11, 20)),
        ("cuối tuần", date(2026, 11, 13)),
        ("cuoi tuan", date(2026, 11, 13)),
        ("cuối tuần sau", date(2026, 11, 20)),
        # Cuối tháng, cuối sprint
        ("cuối tháng", date(2026, 11, 30)),
        ("cuoi thang", date(2026, 11, 30)),
        ("cuối tháng sau", date(2026, 12, 31)),
        ("cuối sprint", SPRINT_END),
        ("cuoi sprint", SPRINT_END),
        # Ngày tuyệt đối
        ("20/11", date(2026, 11, 20)),
        ("20-11", date(2026, 11, 20)),
        ("20/11/2026", date(2026, 11, 20)),
        ("5/1/2027", date(2027, 1, 5)),
        ("01/11", date(2026, 11, 1)),  # đã qua: giữ năm nay để guardrail cảnh báo
        ("05/02", date(2027, 2, 5)),  # lệch ≥ 6 tháng về trước → năm sau
        ("ngày 20", date(2026, 11, 20)),
        ("ngay 20", date(2026, 11, 20)),
        ("ngày 12", date(2026, 11, 12)),
        ("ngày 5", date(2026, 12, 5)),
        # Nằm trong câu
        ("hạn thứ 6 tuần sau nhé", date(2026, 11, 20)),
        ("deadline 20/11 nha", date(2026, 11, 20)),
        ("xong trước ngày 20/11", date(2026, 11, 20)),
        ("lam gap, mai phai xong", date(2026, 11, 13)),
        ("Hạn Cuối Tháng", date(2026, 11, 30)),
    ],
)
def test_parse_supported(text: str, expected: date) -> None:
    result = parse_vi_date(text, NOW, TZ, sprint_end=SPRINT_END)
    assert result is not None, text
    assert result.value == expected
    assert expected.strftime("%d/%m/%Y") in result.explanation


@pytest.mark.parametrize(
    "text",
    [
        "",
        "sớm",
        "càng sớm càng tốt",
        "hôm qua",
        "khi nào rảnh",
        "thứ 5",  # trùng hôm nay: không rõ hôm nay hay tuần sau
        "thu nam",
        "31/11",  # ngày không tồn tại
        "29/02/2026",
        "32/12/2026",
        "ngày 31",  # tháng 11 không có ngày 31
        "mai hoặc thứ 6 tuần sau",  # hai mốc khác nhau
        "thử 6 cách",  # 'thử' không phải 'thứ'
        "gặp lại sau",
        "làm một task",  # 'một' không phải 'mốt'
    ],
)
def test_parse_returns_none_when_unsure(text: str) -> None:
    assert parse_vi_date(text, NOW, TZ, sprint_end=SPRINT_END) is None


def test_end_of_sprint_without_sprint_end_is_none() -> None:
    assert parse_vi_date("cuối sprint", NOW, TZ) is None


def test_uses_vietnam_timezone_not_utc() -> None:
    # 18:00 UTC ngày 12/11 = 01:00 ngày 13/11 giờ Việt Nam.
    now_utc = datetime(2026, 11, 12, 18, 0, tzinfo=UTC)
    result = parse_vi_date("mai", now_utc, TZ)
    assert result is not None
    assert result.value == date(2026, 11, 14)


def test_naive_now_is_treated_as_project_timezone() -> None:
    result = parse_vi_date("mai", datetime(2026, 11, 12, 23, 30), TZ)
    assert result is not None
    assert result.value == date(2026, 11, 13)


def test_weekend_end_of_week_is_none() -> None:
    saturday = datetime(2026, 11, 14, 10, 0, tzinfo=TZ)
    assert parse_vi_date("cuối tuần", saturday, TZ) is None


def test_december_short_date_rolls_to_next_year() -> None:
    december = datetime(2026, 12, 20, 9, 0, tzinfo=TZ)
    result = parse_vi_date("05/01", december, TZ)
    assert result is not None
    assert result.value == date(2027, 1, 5)


def test_explanation_shows_original_phrase_and_weekday() -> None:
    result = parse_vi_date("Hạn thứ 6 tuần sau nhé", NOW, TZ)
    assert result is not None
    assert result.matched == "thứ 6 tuần sau"
    assert result.explanation == "‘thứ 6 tuần sau’ → thứ Sáu 20/11/2026 (tuần sau)"


def test_format_vi_date() -> None:
    assert format_vi_date(date(2026, 11, 15)) == "Chủ nhật 15/11/2026"
