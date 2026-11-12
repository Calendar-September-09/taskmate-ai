"""Chuyển Markdown đơn giản sang Atlassian Document Format (ADF) cho Jira REST API v3.

Hỗ trợ: heading (# .. ######), đoạn văn, danh sách gạch đầu dòng (- hoặc *),
danh sách đánh số (1.), code block (```), và inline **đậm**, `code`, [text](url).
"""

import re
from typing import Any

Node = dict[str, Any]

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_BULLET = re.compile(r"^\s*[-*]\s+(.*)$")
_ORDERED = re.compile(r"^\s*\d+[.)]\s+(.*)$")
_FENCE = re.compile(r"^\s*```(\w*)\s*$")
_INLINE = re.compile(
    r"\*\*(?P<bold>.+?)\*\*"
    r"|`(?P<code>[^`]+)`"
    r"|\[(?P<ltext>[^\]]+)\]\((?P<href>[^)\s]+)\)"
)


def _text(value: str, marks: list[Node] | None = None) -> Node:
    node: Node = {"type": "text", "text": value}
    if marks:
        node["marks"] = marks
    return node


def inline_to_adf(text: str) -> list[Node]:
    """Chuyển một dòng có định dạng inline thành danh sách node text."""
    nodes: list[Node] = []
    pos = 0
    for match in _INLINE.finditer(text):
        if match.start() > pos:
            nodes.append(_text(text[pos : match.start()]))
        if match.group("bold") is not None:
            nodes.append(_text(match.group("bold"), [{"type": "strong"}]))
        elif match.group("code") is not None:
            nodes.append(_text(match.group("code"), [{"type": "code"}]))
        else:
            mark = {"type": "link", "attrs": {"href": match.group("href")}}
            nodes.append(_text(match.group("ltext"), [mark]))
        pos = match.end()
    if pos < len(text):
        nodes.append(_text(text[pos:]))
    return nodes


def _paragraph(lines: list[str]) -> Node:
    content: list[Node] = []
    for i, line in enumerate(lines):
        if i > 0:
            content.append({"type": "hardBreak"})
        content.extend(inline_to_adf(line.strip()))
    return {"type": "paragraph", "content": content}


def _list_item(text: str) -> Node:
    return {"type": "listItem", "content": [{"type": "paragraph", "content": inline_to_adf(text)}]}


def markdown_to_adf(markdown: str) -> Node:
    """Trả về tài liệu ADF (version 1) từ chuỗi Markdown."""
    lines = markdown.replace("\r\n", "\n").split("\n")
    content: list[Node] = []
    paragraph: list[str] = []
    current_list: Node | None = None
    i = 0

    def flush_paragraph() -> None:
        if paragraph:
            content.append(_paragraph(paragraph))
            paragraph.clear()

    def close_list() -> None:
        nonlocal current_list
        if current_list is not None:
            content.append(current_list)
            current_list = None

    while i < len(lines):
        line = lines[i]
        fence = _FENCE.match(line)
        if fence:
            flush_paragraph()
            close_list()
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not _FENCE.match(lines[i]):
                code_lines.append(lines[i])
                i += 1
            block: Node = {"type": "codeBlock", "content": []}
            if fence.group(1):
                block["attrs"] = {"language": fence.group(1)}
            if code_lines:
                block["content"] = [_text("\n".join(code_lines))]
            content.append(block)
            i += 1  # bỏ qua dòng ``` đóng
            continue

        if not line.strip():
            flush_paragraph()
            close_list()
        elif heading := _HEADING.match(line):
            flush_paragraph()
            close_list()
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": len(heading.group(1))},
                    "content": inline_to_adf(heading.group(2).strip()),
                }
            )
        elif item := (_BULLET.match(line) or _ORDERED.match(line)):
            flush_paragraph()
            list_type = "bulletList" if item.re is _BULLET else "orderedList"
            item_text = item.group(1)
            if current_list is None or current_list["type"] != list_type:
                close_list()
                current_list = {"type": list_type, "content": []}
            current_list["content"].append(_list_item(item_text))
        else:
            close_list()
            paragraph.append(line)
        i += 1

    flush_paragraph()
    close_list()
    return {"type": "doc", "version": 1, "content": content}


def adf_to_text(node: Any) -> str:
    """Lấy văn bản thuần từ ADF (dùng để đọc description của issue)."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ""
    node_type = node.get("type")
    if node_type == "text":
        return str(node.get("text", ""))
    if node_type == "hardBreak":
        return "\n"
    children = "".join(adf_to_text(child) for child in node.get("content", []))
    if node_type in {"paragraph", "heading", "codeBlock", "listItem"}:
        return children.rstrip("\n") + "\n"
    return children
