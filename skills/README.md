# Skills runtime của TaskMate

Mỗi Skill là một thư mục con có `SKILL.md` (frontmatter `name`, `description` nói rõ khi nào dùng,
dưới 300 ký tự, rồi đến phần hướng dẫn) và thư mục `examples/` gồm 1–2 ví dụ đầu vào → đầu ra.
Agent đọc phần mô tả ngắn của mọi Skill, chọn Skill phù hợp rồi mới nạp nội dung đầy đủ (design mục 4.2).
Đây là Skill của sản phẩm TaskMate, không phải `.claude/skills`.

| Skill | Khi nào dùng | Design |
| --- | --- | --- |
| `task-writing` | Tạo Task/Story; định nghĩa JSON bản nháp dùng chung | 4.1, 4.2 |
| `bug-report` | Yêu cầu về lỗi, bug, crash | 4.2 |
| `scrum-conventions` | Luôn nạp kèm | 4.2 |
| `missing-info` | Thiếu trường bắt buộc, tên trùng, ngày không hiểu | 4.2 |
| `meeting-to-tasks` | Biên bản Planning, Daily, Review, Retro | 14.2 |
| `sprint-report` | Báo cáo cuối sprint, phụ lục theo thành viên | 10.4, 10.5 |
| `standup-brief` | Chuẩn bị Daily Stand-up | 13.3 |
| `retro` | Câu hỏi Retro, gom ghi chú, hành động SMART | 10.6 |

Để sau: `story-breakdown`.

## Nguyên tắc chung

LLM chỉ chép nguyên cụm gốc (`due_text`, `assignee_text`, `priority_text`); code quy đổi bằng
`domain.dates.parse_vi_date`, `domain.people.match_member`, `domain.priority.detect_priority`.
Báo cáo, stand-up, retro chỉ dùng con số có trong dữ liệu đầu vào.

## Dùng trong code

```python
from skills import list_skills, load_skill

catalog = list_skills()  # [SkillInfo(name, description), ...] cho bước chọn Skill
skill = load_skill("task-writing")  # hướng dẫn đầy đủ + ví dụ
prompt_block = skill.to_prompt()
```

Kiểm tra định dạng: `uv run pytest -q tests/test_skills.py`.
