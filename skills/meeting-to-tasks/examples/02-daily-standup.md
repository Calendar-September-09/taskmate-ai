# Ghi chú Daily Stand-up

## Đầu vào

Loại cuộc họp: Daily Stand-up – Project SHOP – Sprint 12

> Nam BE: SHOP-105 chờ review mấy hôm rồi, chưa ai xem. SHOP-111 đang vướng vì thiếu index trên bảng orders, cần DBA hỗ trợ.
> Đức: SHOP-106 xong FE, chiều nay đẩy PR. Phát hiện trang giỏ hàng bị lệch layout trên iPhone SE, cần fix gấp trước demo thứ 6.
> Trần Hoài Nam: em review SHOP-105 trong sáng nay.
> Hà: hôm qua nghỉ, không có cập nhật.

## Đầu ra

```json
{
  "meeting_type": "daily",
  "tasks": [
    {
      "issue_type": "Bug",
      "summary": "Sửa lỗi lệch layout trang giỏ hàng trên iPhone SE",
      "description": "## Mô tả\nTrang giỏ hàng hiển thị lệch layout trên iPhone SE.\n\n## Bước tái hiện\n1. Mở trang giỏ hàng trên iPhone SE\n2. <cần bổ sung>\n\n## Kết quả mong đợi\nLayout hiển thị đúng như trên các thiết bị khác.\n\n## Kết quả thực tế\nLayout bị lệch.\n\n## Môi trường\niPhone SE; trình duyệt hoặc app: <cần bổ sung>\n\n## Mức nghiêm trọng\nTrung bình – ảnh hưởng hiển thị trên một nhóm thiết bị, cần xong trước buổi demo.\n\n## Acceptance Criteria\n- [ ] Trang giỏ hàng hiển thị đúng trên iPhone SE",
      "project_text": "SHOP",
      "assignee_text": null,
      "due_text": "trước demo thứ 6",
      "priority_text": "gấp",
      "sprint_text": "Sprint 12",
      "parent_key": null,
      "story_points": null,
      "labels": ["from-meeting"],
      "quote": "Phát hiện trang giỏ hàng bị lệch layout trên iPhone SE, cần fix gấp trước demo thứ 6.",
      "confidence": 0.85
    }
  ],
  "decisions": [
    "Trần Hoài Nam review SHOP-105 trong sáng nay",
    "Đề nghị gắn Flagged cho SHOP-111: vướng do thiếu index trên bảng orders, cần DBA hỗ trợ"
  ],
  "unclear": [
    "\"cần DBA hỗ trợ\" – chưa rõ ai trong nhóm liên hệ DBA và có cần tạo task riêng không"
  ]
}
```

Ghi chú: SHOP-105, SHOP-106, SHOP-111 đã có trên Jira nên không tạo task mới. Gắn Flagged là thao
tác ghi nên chỉ đưa vào `decisions` để Scrum Master duyệt. `due_text` giữ nguyên "trước demo thứ 6";
code sẽ quy đổi phần "thứ 6" thành ngày cụ thể. Hà không có cập nhật nên không sinh gì.
