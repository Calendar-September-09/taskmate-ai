---
name: meeting-to-tasks
description: Dùng khi Scrum Master dán biên bản hoặc transcript cuộc họp (Sprint Planning, Daily Stand-up, Sprint Review, Retrospective) để trích danh sách task, các quyết định và những câu chưa rõ cần hỏi lại.
---

# Trích task từ biên bản họp

Scrum Master đã chọn dự án và **loại cuộc họp**. Bạn đọc biên bản, trích ra việc cần làm và quyết
định. Code sẽ quy đổi ngày, khớp tên, kiểm tra trùng với Jira; bảng xem trước tô cam dòng thiếu
người hoặc hạn. Task từ cuộc họp ghi lại quyết định của cả nhóm: **không phân công thay nhóm**.

## Cần trích gì theo loại cuộc họp

| Loại | Task | Quyết định | Lưu ý |
| --- | --- | --- | --- |
| Sprint Planning | Việc nhóm cam kết làm trong sprint, việc con khi nhóm đã chia nhỏ | Mục tiêu sprint, việc bị loại khỏi sprint, ước lượng nhóm đã chốt | Người phụ trách chỉ ghi khi thành viên **tự nhận** ("để em làm") |
| Daily Stand-up | Việc phát sinh, việc gỡ vướng ("cần ai đó review SHOP-105") | Thay đổi kế hoạch trong ngày | Đề nghị gắn Flagged cho task bị vướng đưa vào `decisions`, không tạo task mới cho nó |
| Sprint Review | Phản hồi của PO/khách thành Story/Task backlog, lỗi phát hiện khi demo thành Bug | Chấp nhận / chưa chấp nhận tính năng | Task từ phản hồi mặc định vào backlog, không vào sprint đang chạy |
| Retrospective | Hành động cải tiến nhóm đã **chọn**, label `retro-action` | Điều nhóm thống nhất giữ hoặc thay đổi | Ý kiến chưa được chọn thì không thành task |

## Cách trích

1. Mỗi việc là một task theo định dạng JSON của Skill task-writing (lỗi thì theo bug-report),
   thêm label `from-meeting`.
2. `quote` là **câu nguyên văn** trong biên bản làm căn cứ, để Scrum Master đối chiếu.
3. Người, hạn, mức gấp: chép nguyên cụm vào `assignee_text`, `due_text`, `priority_text`.
   Không quy đổi, không đoán.
4. Một câu có nhiều việc thì tách thành nhiều task; nhiều câu nói cùng một việc thì gộp lại.
5. Không biến thảo luận, ý kiến, câu hỏi chưa chốt thành task.
6. Việc đã có issue key trong biên bản ("SHOP-105 xong rồi") là cập nhật, không phải task mới.
   Không tạo task, có thể ghi vào `decisions` nếu là quyết định.

## Câu chưa rõ (`unclear`)

Đưa vào `unclear` khi câu có vẻ là việc cần làm nhưng thiếu thông tin quan trọng. **Không tự điền.**

- Không rõ ai: "ai đó xem lại phần thanh toán"
- Không rõ việc gì: "xử lý vụ hôm trước"
- Không rõ đã chốt chưa: "chắc là nên đổi sang VNPay, để tính sau"

Mỗi mục ghi: câu gốc trong ngoặc kép, sau đó là phần còn thiếu.
Ví dụ: `"ai đó xem lại phần thanh toán" – thiếu người phụ trách và phạm vi cần xem lại`.

## Định dạng đầu ra

```json
{
  "meeting_type": "planning | daily | review | retro",
  "tasks": [ { "...": "theo định dạng task-writing, labels có from-meeting" } ],
  "decisions": ["Quyết định viết thành một câu khẳng định, ngắn gọn"],
  "unclear": ["\"câu gốc\" – thiếu gì"]
}
```

## Kiểm tra trước khi trả

- Mọi task đều có `quote` lấy đúng từ biên bản.
- Không có `assignee_text` nào mà biên bản không nói rõ người đó nhận việc.
- Không có ngày tháng do bạn tự tính.
- Không có tên người trong `decisions` trừ khi cần để hiểu quyết định.
