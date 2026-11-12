# Task kỹ thuật, thiếu người và hạn

## Đầu vào

> Thêm task cấu hình gửi email xác nhận đơn hàng qua SendGrid

## Đầu ra

```json
{
  "issue_type": "Task",
  "summary": "Cấu hình gửi email xác nhận đơn hàng qua SendGrid",
  "description": "## Mục tiêu\nNgười mua nhận email xác nhận ngay sau khi đặt hàng thành công.\n\n## Phạm vi\n- Trong phạm vi: cấu hình tài khoản SendGrid, template email xác nhận đơn, gửi email khi đơn tạo thành công\n- Ngoài phạm vi: <cần bổ sung>\n\n## Acceptance Criteria\n- [ ] Khóa API SendGrid đọc từ biến môi trường, không ghi trong mã nguồn\n- [ ] Đặt hàng thành công trên môi trường staging thì email đến hộp thư người mua trong vòng 1 phút\n- [ ] Email có mã đơn, danh sách sản phẩm và tổng tiền\n\n## Đầu ra\nCấu hình SendGrid trên staging và template email đã được duyệt.",
  "project_text": null,
  "assignee_text": null,
  "due_text": null,
  "priority_text": null,
  "sprint_text": null,
  "parent_key": null,
  "story_points": null,
  "labels": [],
  "quote": "Thêm task cấu hình gửi email xác nhận đơn hàng qua SendGrid",
  "confidence": 0.8
}
```

Ghi chú: không tự điền project, người phụ trách hay hạn. Agent dùng Skill missing-info
(và Memory nếu có project mặc định) để hỏi tiếp.
