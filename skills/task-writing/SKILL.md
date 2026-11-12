---
name: task-writing
description: Dùng cho mọi yêu cầu tạo Task hoặc Story mới (kể cả task trích từ biên bản họp): viết tiêu đề, mô tả theo template, Acceptance Criteria và xuất bản nháp JSON. Lỗi phần mềm thì dùng bug-report.
---

# Viết Task / Story

Mục tiêu: biến yêu cầu tiếng Việt của Scrum Master thành bản nháp rõ ràng để người dùng duyệt.
Bạn chỉ **viết** nội dung và **chép lại** thông tin người dùng nói. Bạn không tự tính ngày,
không tự chọn người, không tự đặt số liệu.

## Chọn loại issue

| Loại | Khi nào |
| --- | --- |
| Story | Một tính năng mang lại giá trị cho người dùng cuối ("người mua có thể…") |
| Task | Việc kỹ thuật, cấu hình, tài liệu, nghiên cứu, việc nội bộ |
| Sub-task | Người dùng nói rõ là việc con của một issue có key (ví dụ SHOP-105) |
| Bug | Không chọn ở đây – chuyển sang Skill bug-report |

Không rõ thì chọn Task.

## Quy tắc tiêu đề (summary)

- Bắt đầu bằng động từ: Xây dựng, Thêm, Sửa, Cấu hình, Viết, Tối ưu, Nghiên cứu…
- Tối đa 120 ký tự, một ý, không dấu chấm cuối câu.
- Không đưa tên người, ngày hạn, mức ưu tiên vào tiêu đề (đã có trường riêng).
- Giữ thuật ngữ nhóm dùng (VNPay, FE, BE, API), không dịch sang từ khác.

Tốt: "Xây dựng màn hình đăng nhập bằng số điện thoại"
Chưa tốt: "Nam làm login gấp trước thứ 6"

## Template mô tả (Markdown)

```markdown
## Mục tiêu
<1–2 câu: vì sao cần việc này, ai được lợi>

## Phạm vi
- Trong phạm vi: <những gì làm>
- Ngoài phạm vi: <những gì không làm, nếu người dùng có nói>

## Acceptance Criteria
- [ ] Given <bối cảnh>, When <hành động>, Then <kết quả đo được>
- [ ] ...

## Đầu ra
<thứ bàn giao: màn hình, API, tài liệu, PR, báo cáo…>
```

- 2–5 Acceptance Criteria, mỗi tiêu chí kiểm tra được (có kết quả cụ thể, không viết "chạy tốt").
- Với Task kỹ thuật, AC có thể viết dạng danh sách kiểm tra thay vì Given/When/Then.
- Thông tin người dùng không nói thì **không bịa**. Ghi `<cần bổ sung>` ở chỗ đó và để
  Skill missing-info hỏi lại.

## Định dạng đầu ra (JSON)

Trả về đúng một object JSON, không kèm lời dẫn:

```json
{
  "issue_type": "Story | Task | Sub-task",
  "summary": "string",
  "description": "string (Markdown theo template)",
  "project_text": "chép nguyên, ví dụ \"SHOP\", hoặc null",
  "assignee_text": "chép nguyên tên người như trong câu, ví dụ \"Nam\", hoặc null",
  "due_text": "chép nguyên cụm chỉ hạn, ví dụ \"thứ 6 tuần sau\", hoặc null",
  "priority_text": "chép nguyên cụm chỉ mức gấp, ví dụ \"gấp\", hoặc null",
  "sprint_text": "chép nguyên, ví dụ \"sprint 12\", hoặc null",
  "parent_key": "SHOP-105 hoặc null",
  "story_points": "số người dùng nói, hoặc null",
  "labels": [],
  "quote": "câu gốc của người dùng mà bản nháp dựa vào",
  "confidence": 0.0
}
```

Vì sao chép nguyên: code của TaskMate tự quy đổi `due_text` sang ngày cụ thể, khớp
`assignee_text` với danh sách thành viên Jira, suy ra priority từ `priority_text`. Nếu bạn tự đổi
"thứ 6 tuần sau" thành một ngày, kết quả có thể sai và người dùng không biết căn cứ ở đâu.

## Mức confidence

- 0.9–1.0: người dùng nói rõ việc cần làm và loại issue.
- 0.6–0.8: phải suy ra phạm vi hoặc loại issue.
- Dưới 0.6: yêu cầu mơ hồ – vẫn trả bản nháp, agent sẽ hỏi lại trước khi cho duyệt.
