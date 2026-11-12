"""Chuẩn hóa chuỗi tiếng Việt để so khớp không phân biệt dấu và hoa thường."""

import unicodedata


def normalize_vi(text: str) -> str:
    """'Nguyễn Văn Đức' -> 'nguyen van duc'."""
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    without_marks = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return " ".join(without_marks.lower().split())
