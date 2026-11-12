---
name: add-mcp-tool
description: Dùng khi cần thêm một tool mới vào MCP Server của TaskMate.
---
Khi thêm tool mới vào mcp_server/server.py:
1. Định nghĩa input/output bằng Pydantic, docstring nói rõ khi nào agent nên gọi.
2. Viết phần xử lý cho cả JiraClient và MockJira, thêm dữ liệu mock nếu cần.
3. Tool có ghi dữ liệu thì bắt buộc kiểm tra approval_token và idempotency.
4. Thêm test trong tests/test_mcp_tools.py, chạy pytest.
5. Cập nhật bảng tool ở docs/design.md mục 4.3.