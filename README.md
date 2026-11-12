# TaskMate AI

AI Agent hỗ trợ Scrum Master: tạo task trên Jira từ yêu cầu tiếng Việt và biên bản họp,
theo dõi tiến độ, chuẩn bị Daily Stand-up và báo cáo cuối sprint. Thiết kế: [docs/design.md](docs/design.md).

## Yêu cầu

- [uv](https://docs.astral.sh/uv/)
- Python 3.11 (uv tự tải nếu máy chưa có: `uv python install 3.11`)

## Cài đặt

```bash
uv sync
cp .env.example .env   # rồi điền giá trị thật
```

## Chạy test và lint

```bash
uv run pytest -q
uv run ruff check .
```

Test luôn chạy với `JIRA_MODE=mock`, không chạm Jira thật.
