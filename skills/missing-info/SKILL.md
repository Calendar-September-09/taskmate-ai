---
name: missing-info
description: Dùng khi bản nháp còn thiếu trường bắt buộc hoặc thông tin mơ hồ: không rõ project, tên trùng nhiều người, ngày không hiểu được, yêu cầu quá chung. Quyết định trường nào tự điền mặc định, trường nào phải hỏi, và cách hỏi ngắn.
---

# Xử lý thiếu thông tin

Đầu vào của bạn: bản nháp hiện tại, danh sách trường còn thiếu (do code tính), kết quả khớp tên và
ngày (do code tính), Memory của dự án. Đầu ra: câu hỏi ngắn cho người dùng **hoặc** xác nhận đã đủ.

## Trường nào xử lý thế nào

| Trường | Thiếu thì | Ghi chú |
| --- | --- | --- |
| project | Lấy từ Memory nếu có project mặc định; không có thì **hỏi** | Gợi ý danh sách project |
| summary | **Hỏi** "Việc cần làm là gì?" | Không tự nghĩ ra việc |
| description | Tự viết theo template (task-writing / bug-report) | Chỗ không biết ghi `<cần bổ sung>` |
| issue_type | Mặc định Task | Hiện nhãn "mặc định" |
| assignee | **Để trống**, nêu là chưa có người | Không tự phân công. Chỉ hỏi nếu người dùng muốn giao |
| due_date | Để trống | Hỏi khi người dùng có nhắc hạn mà code không hiểu |
| priority | Lấy từ Memory hoặc để trống | Không tự nâng mức |
| sprint | Lấy sprint đang chạy từ Memory hoặc để backlog | Hỏi nếu có nhiều sprint đang chạy |
| parent (Sub-task) | **Hỏi** issue cha | Bắt buộc với Sub-task |
| story points | Để trống | Nhóm tự ước lượng |

## Các tình huống mơ hồ

- **Tên trùng** (code trả nhiều ứng viên): liệt kê đủ họ tên, hỏi chọn ai.
  "Dự án SHOP có 2 người tên Nam: Nguyễn Văn Nam và Trần Hoài Nam. Bạn muốn giao cho ai?"
- **Không tìm thấy tên**: nói rõ không có trong dự án, đưa gợi ý gần giống (nếu code có).
- **Ngày không hiểu** (code trả None): nhắc lại nguyên cụm và hỏi ngày cụ thể.
  "TaskMate chưa hiểu ‘đầu tuần sau nữa’ là ngày nào. Bạn cho ngày cụ thể (dd/mm) được không?"
- **Ngày đã qua hoặc sau ngày kết thúc sprint**: nêu ngày đã quy đổi và hỏi xác nhận.
- **Yêu cầu quá chung** ("làm phần thanh toán"): hỏi phạm vi cụ thể hoặc đề nghị tách việc.

## Cách hỏi

- Mỗi lượt hỏi **tối đa 3 câu**, ưu tiên theo thứ tự: project → việc cần làm → issue cha
  → người phụ trách → hạn.
- Câu ngắn, có lựa chọn sẵn khi được (danh sách người, sprint, project).
- Nói rõ những gì đã tự điền để người dùng biết: "Loại: Task (mặc định), Sprint: SHOP Sprint 12
  (từ bộ nhớ)."
- Đủ thông tin bắt buộc thì không hỏi thêm; chuyển sang bản xem trước để người dùng duyệt.
- Không hỏi lại thông tin người dùng đã nói trong hội thoại.
