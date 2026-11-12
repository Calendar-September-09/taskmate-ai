"""Kiểm tra chuyển Markdown sang ADF."""

from mcp_server.adf import adf_to_text, markdown_to_adf


def test_document_shape() -> None:
    doc = markdown_to_adf("Xin chào")
    assert doc == {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Xin chào"}]}],
    }


def test_headings_and_lists() -> None:
    doc = markdown_to_adf(
        "## Mục tiêu\nThanh toán VNPay.\n\n"
        "## Acceptance Criteria\n- Điều kiện 1\n- Điều kiện 2\n\n"
        "1. Bước một\n2. Bước hai"
    )
    types = [n["type"] for n in doc["content"]]
    assert types == ["heading", "paragraph", "heading", "bulletList", "orderedList"]
    assert doc["content"][0]["attrs"] == {"level": 2}
    assert len(doc["content"][3]["content"]) == 2
    item = doc["content"][3]["content"][0]
    assert item["type"] == "listItem"
    assert item["content"][0]["content"][0]["text"] == "Điều kiện 1"


def test_inline_marks() -> None:
    doc = markdown_to_adf("Gọi **API** `POST /pay` xem [tài liệu](https://example.com)")
    nodes = doc["content"][0]["content"]
    assert nodes[1] == {"type": "text", "text": "API", "marks": [{"type": "strong"}]}
    assert nodes[3] == {"type": "text", "text": "POST /pay", "marks": [{"type": "code"}]}
    assert nodes[5]["marks"][0] == {"type": "link", "attrs": {"href": "https://example.com"}}


def test_code_block_keeps_content() -> None:
    doc = markdown_to_adf("```python\nx = 1\n# không phải heading\n```")
    block = doc["content"][0]
    assert block["type"] == "codeBlock"
    assert block["attrs"] == {"language": "python"}
    assert block["content"][0]["text"] == "x = 1\n# không phải heading"


def test_multiline_paragraph_uses_hard_break() -> None:
    doc = markdown_to_adf("dòng 1\ndòng 2")
    types = [n["type"] for n in doc["content"][0]["content"]]
    assert types == ["text", "hardBreak", "text"]


def test_empty_markdown() -> None:
    assert markdown_to_adf("")["content"] == []


def test_adf_to_text_roundtrip() -> None:
    text = adf_to_text(markdown_to_adf("## Mục tiêu\nThanh toán\n\n- A\n- B"))
    assert "Mục tiêu" in text and "Thanh toán" in text and "A" in text and "B" in text
