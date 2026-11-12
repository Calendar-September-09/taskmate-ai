"""Test detect_priority: từ khóa gấp/khẩn/ưu tiên cao → High, còn lại None."""

import pytest

from domain.priority import detect_priority


@pytest.mark.parametrize(
    ("text", "matched"),
    [
        ("làm gấp nhé", "gấp"),
        ("GẤP", "GẤP"),
        ("lam gap giup em", "gap"),
        ("việc khẩn", "khẩn"),
        ("khẩn cấp: sập trang thanh toán", "khẩn cấp"),
        ("khan cap", "khan cap"),
        ("ưu tiên cao", "ưu tiên cao"),
        ("uu tien cao nha", "uu tien cao"),
        ("không gặp lỗi nhưng cần gấp", "gấp"),
    ],
)
def test_high(text: str, matched: str) -> None:
    result = detect_priority(text)
    assert result is not None
    assert result.value == "High"
    assert result.matched == matched


@pytest.mark.parametrize(
    "text",
    [
        "Tạo task làm màn hình login",
        "",
        "không gấp",
        "khong gap lam",
        "chưa cần gấp",
        "không quá gấp",
        "gặp khách hàng chiều nay",
        "mang khăn",
        "ưu tiên thấp",
    ],
)
def test_none(text: str) -> None:
    assert detect_priority(text) is None
