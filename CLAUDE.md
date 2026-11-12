# TaskMate AI – hướng dẫn cho Claude Code

## Dự án
AI Agent hỗ trợ Scrum Master: tạo task trên Jira từ yêu cầu tiếng Việt và biên bản họp,
theo dõi tiến độ, chuẩn bị Daily Stand-up, báo cáo cuối sprint và đầu vào Retro.
Thiết kế đầy đủ ở docs/design.md; mục 14 là phạm vi MVP. Đọc mục liên quan trước khi làm.

## Cấu trúc
- core/: cấu hình chung (settings đọc .env qua pydantic-settings)
- app/: giao diện Streamlit
- agent/: LangGraph (state, nodes, graph)
- mcp_server/: MCP Server (FastMCP) gọi Jira REST API, có chế độ mock
- skills/: Skill runtime của TaskMate (không phải .claude/skills)
- domain/: schema, xử lý ngày tiếng Việt, khớp tên thành viên
- guardrails/, memory/, metrics/, observability/
- evals/: bộ dữ liệu và script đánh giá; tests/: unit test

## Lệnh
- Cài đặt: uv sync
- Test: uv run pytest -q
- Lint: uv run ruff check .
- Chạy giao diện: uv run streamlit run app/main.py
- Chạy MCP Server: uv run python -m mcp_server.server

## Quy tắc bắt buộc
- Python 3.11, type hints đầy đủ, Pydantic v2 cho mọi dữ liệu có cấu trúc.
- Không gọi API ghi của Jira khi không có approval_token hợp lệ (design mục 4.3, 4.5).
- Con số và ngày tháng tính bằng code, không để LLM tự tính.
- Múi giờ Asia/Ho_Chi_Minh.
- Test luôn chạy với JIRA_MODE=mock, không chạm Jira thật.
- Không in, không log token hay API key; cấu hình đọc từ .env qua settings.
- Mọi thay đổi có test; chạy pytest trước khi báo xong.
- Chữ hiển thị cho người dùng bằng tiếng Việt; tên biến, hàm bằng tiếng Anh.