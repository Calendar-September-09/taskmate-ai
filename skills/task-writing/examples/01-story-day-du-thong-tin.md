# Story đủ thông tin

## Đầu vào

> Tạo story trang lịch sử đơn hàng cho Đức, project SHOP, sprint 12, hạn thứ 6 tuần sau, ưu tiên cao.
> Người mua xem được các đơn đã đặt, lọc theo trạng thái, bấm vào xem chi tiết. Chưa cần xuất PDF.

## Đầu ra

```json
{
  "issue_type": "Story",
  "summary": "Xây dựng trang lịch sử đơn hàng cho người mua",
  "description": "## Mục tiêu\nNgười mua xem lại các đơn đã đặt và theo dõi trạng thái mà không cần liên hệ hỗ trợ.\n\n## Phạm vi\n- Trong phạm vi: danh sách đơn đã đặt, lọc theo trạng thái, trang chi tiết đơn\n- Ngoài phạm vi: xuất hóa đơn PDF\n\n## Acceptance Criteria\n- [ ] Given người mua đã đăng nhập và có đơn hàng, When mở trang Lịch sử đơn hàng, Then thấy danh sách đơn mới nhất ở trên cùng\n- [ ] Given đang ở danh sách, When chọn lọc \"Đang giao\", Then chỉ còn các đơn có trạng thái Đang giao\n- [ ] Given đang ở danh sách, When bấm vào một đơn, Then mở trang chi tiết có sản phẩm, tổng tiền và trạng thái\n- [ ] Given người mua chưa có đơn nào, When mở trang, Then thấy thông báo \"Bạn chưa có đơn hàng\"\n\n## Đầu ra\nMàn hình Lịch sử đơn hàng và trang chi tiết đơn, đã merge vào nhánh chính.",
  "project_text": "SHOP",
  "assignee_text": "Đức",
  "due_text": "thứ 6 tuần sau",
  "priority_text": "ưu tiên cao",
  "sprint_text": "sprint 12",
  "parent_key": null,
  "story_points": null,
  "labels": [],
  "quote": "Tạo story trang lịch sử đơn hàng cho Đức, project SHOP, sprint 12, hạn thứ 6 tuần sau, ưu tiên cao.",
  "confidence": 0.95
}
```

Ghi chú: `due_text` giữ nguyên "thứ 6 tuần sau"; code sẽ đổi thành ngày cụ thể.
"Chưa cần xuất PDF" được đưa vào "Ngoài phạm vi".
