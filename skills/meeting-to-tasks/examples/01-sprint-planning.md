# Biên bản Sprint Planning

## Đầu vào

Loại cuộc họp: Sprint Planning – Project SHOP – Sprint 12

> PO: Mục tiêu sprint này là thanh toán VNPay và lịch sử đơn hàng.
> Nam BE: API thanh toán VNPay để em làm, hạn thứ 6 tuần sau.
> Đức: Màn hình lịch sử đơn hàng em nhận.
> Hà: Viết test E2E cho luồng thanh toán thì cần ai đó làm, chắc đợi API xong.
> PO: Xuất hóa đơn PDF để sprint sau, sprint này không làm.
> Ai đó xem lại phần email xác nhận đơn nhé.

## Đầu ra

```json
{
  "meeting_type": "planning",
  "tasks": [
    {
      "issue_type": "Story",
      "summary": "Xây dựng API thanh toán VNPay",
      "description": "## Mục tiêu\nNgười mua thanh toán đơn hàng qua VNPay.\n\n## Phạm vi\n- Trong phạm vi: API tạo giao dịch, nhận kết quả trả về từ VNPay\n- Ngoài phạm vi: <cần bổ sung>\n\n## Acceptance Criteria\n- [ ] Given đơn hàng hợp lệ, When người mua chọn VNPay, Then được chuyển tới trang thanh toán VNPay\n- [ ] Given VNPay báo thành công, When hệ thống nhận kết quả, Then đơn chuyển sang trạng thái Đã thanh toán\n\n## Đầu ra\nAPI thanh toán VNPay chạy trên staging.",
      "project_text": "SHOP",
      "assignee_text": "Nam BE",
      "due_text": "thứ 6 tuần sau",
      "priority_text": null,
      "sprint_text": "Sprint 12",
      "parent_key": null,
      "story_points": null,
      "labels": ["from-meeting"],
      "quote": "Nam BE: API thanh toán VNPay để em làm, hạn thứ 6 tuần sau.",
      "confidence": 0.9
    },
    {
      "issue_type": "Story",
      "summary": "Xây dựng màn hình lịch sử đơn hàng",
      "description": "## Mục tiêu\nNgười mua xem lại các đơn đã đặt.\n\n## Phạm vi\n- Trong phạm vi: <cần bổ sung>\n\n## Acceptance Criteria\n- [ ] Given người mua có đơn hàng, When mở màn hình Lịch sử đơn hàng, Then thấy danh sách đơn đã đặt\n\n## Đầu ra\nMàn hình Lịch sử đơn hàng.",
      "project_text": "SHOP",
      "assignee_text": "Đức",
      "due_text": null,
      "priority_text": null,
      "sprint_text": "Sprint 12",
      "parent_key": null,
      "story_points": null,
      "labels": ["from-meeting"],
      "quote": "Đức: Màn hình lịch sử đơn hàng em nhận.",
      "confidence": 0.85
    },
    {
      "issue_type": "Task",
      "summary": "Viết test E2E luồng thanh toán",
      "description": "## Mục tiêu\nĐảm bảo luồng thanh toán VNPay chạy đúng từ đầu đến cuối.\n\n## Phạm vi\n- Trong phạm vi: test E2E luồng thanh toán\n\n## Acceptance Criteria\n- [ ] Có test E2E cho trường hợp thanh toán thành công và thất bại, chạy được trong CI\n\n## Đầu ra\nBộ test E2E luồng thanh toán.\n\nPhụ thuộc: cần API thanh toán VNPay xong trước.",
      "project_text": "SHOP",
      "assignee_text": null,
      "due_text": null,
      "priority_text": null,
      "sprint_text": "Sprint 12",
      "parent_key": null,
      "story_points": null,
      "labels": ["from-meeting"],
      "quote": "Hà: Viết test E2E cho luồng thanh toán thì cần ai đó làm, chắc đợi API xong.",
      "confidence": 0.75
    }
  ],
  "decisions": [
    "Mục tiêu Sprint 12: thanh toán VNPay và lịch sử đơn hàng",
    "Xuất hóa đơn PDF dời sang sprint sau, không làm trong Sprint 12"
  ],
  "unclear": [
    "\"Ai đó xem lại phần email xác nhận đơn nhé.\" – thiếu người phụ trách và việc cụ thể cần xem lại"
  ]
}
```

Ghi chú: task test E2E không có người phụ trách vì Hà chỉ nói "cần ai đó làm", không tự nhận.
Xuất hóa đơn PDF là quyết định, không phải task của sprint này.
