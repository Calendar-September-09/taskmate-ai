"""Chuẩn hóa chuỗi tiếng Việt để so khớp không phân biệt dấu và hoa thường."""

import re
import unicodedata

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def normalize_vi(text: str) -> str:
    """'Nguyễn Văn Đức' -> 'nguyen van duc'."""
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    without_marks = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return " ".join(without_marks.lower().split())


def _fold_char(ch: str) -> str:
    if ch in "đĐ":
        return "d"
    decomposed = unicodedata.normalize("NFD", ch)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower()


def fold_with_map(text: str) -> tuple[str, list[int]]:
    """Bỏ dấu, chữ thường, GIỮ khoảng trắng; kèm bảng vị trí về chuỗi gốc.

    Trả về (folded, index_map) với index_map[i] là vị trí trong `text` của ký tự folded[i],
    cộng thêm một phần tử cuối bằng len(text) để cắt span [start, end).
    """
    folded: list[str] = []
    index_map: list[int] = []
    for i, ch in enumerate(text):
        for out in _fold_char(ch):
            folded.append(out)
            index_map.append(i)
    index_map.append(len(text))
    return "".join(folded), index_map


def original_span(text: str, index_map: list[int], start: int, end: int) -> str:
    """Cắt đoạn gốc tương ứng span [start, end) của chuỗi đã fold."""
    if end <= start:
        return ""
    return text[index_map[start] : index_map[end - 1] + 1]


def accents_consistent(segment: str, accented_words: frozenset[str]) -> bool:
    """Mỗi từ trong đoạn phải hoặc không dấu, hoặc đúng một dạng có dấu cho phép.

    Dùng để không nhầm 'gặp' với 'gấp', 'thử' với 'thứ' khi so khớp trên chuỗi đã bỏ dấu.
    """
    for token in _TOKEN_RE.findall(unicodedata.normalize("NFC", segment).lower()):
        if token.isascii():
            continue
        if token not in accented_words:
            return False
    return True
