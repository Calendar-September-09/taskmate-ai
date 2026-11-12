# Retro Sprint 12: gom ghi chú và đề xuất hành động

## Đầu vào

Ẩn tên: bật.

Action item sprint trước: SHOP-98 "Viết checklist Definition of Done" – Done – số bug mở lại: 3 → 1.

Mẫu dữ liệu (do code tính): thời gian chờ review TB 6,0 ngày (TB 3 sprint trước 2,1);
SHOP-108 thêm giữa sprint (+2 điểm); SHOP-107 bị chặn bởi SHOP-105.

Ghi chú dán vào:
> - Nam: Demo lịch sử đơn hàng mượt, PO khen
> - Hà: PR VNPay nằm review gần 1 tuần
> - Đức: Code review chậm quá, PR của em cũng chờ
> - Nam QA: Không biết khi nào API xong để viết test E2E
> - Hà: Checklist DoD dùng tốt, ít bug mở lại hơn
> - Đức: Thử dùng mock VNPay để FE không phải chờ BE
> - Nam: Bug crash giỏ hàng chen vào giữa sprint

## Đầu ra

```markdown
## Action item sprint trước
- SHOP-98 Viết checklist Definition of Done – Done – số bug mở lại: 3 → 1 – đã cải thiện

## Câu hỏi thảo luận từ dữ liệu
1. Thời gian chờ review trung bình là 6,0 ngày, so với 2,1 ngày ở 3 sprint trước. Khâu review đang vướng ở đâu?
2. SHOP-107 bị chặn bởi SHOP-105 gần hết sprint. Nhóm có thể phát hiện phụ thuộc sớm hơn bằng cách nào?
3. SHOP-108 được thêm giữa sprint. Việc phát sinh nên đi vào sprint theo quy trình nào?

## Ghi chú của nhóm
### Làm tốt
- Demo lịch sử đơn hàng mượt, PO đánh giá tốt
- Checklist DoD giúp giảm bug mở lại

### Cần cải thiện
- PR chờ review lâu, có PR gần 1 tuần (×2)
- Không rõ khi nào API xong để bắt đầu test E2E
- Bug phát sinh chen vào giữa sprint

### Ý tưởng
- Dùng mock VNPay để FE và test không phải chờ BE

## Đề xuất hành động (nhóm chọn 1–3)
| # | Làm gì | Ai phụ trách | Hạn | Đo bằng |
| --- | --- | --- | --- | --- |
| 1 | Gắn reviewer ngay khi mở PR, phản hồi review trong 24 giờ làm việc | <nhóm chọn> | Suốt Sprint 13 | Thời gian chờ review TB |
| 2 | Dựng mock VNPay để FE và test E2E làm song song với BE | <nhóm chọn> | <nhóm chọn> | Số task bị chặn cuối sprint |
| 3 | Bug phát sinh giữa sprint vào backlog, PO duyệt trước khi đưa vào sprint (trừ mức Highest) | <nhóm chọn> | Từ Sprint 13 | Story points thêm giữa sprint |
| 4 | Trong Planning, đánh dấu task phụ thuộc và ngày dự kiến bàn giao | <nhóm chọn> | Planning Sprint 13 | Số task bị chặn cuối sprint |
```

Ghi chú: ẩn tên đã bật nên mọi tên người viết bị bỏ. Hai ý về review chậm được gộp thành `(×2)`.
Hành động nhóm chọn sẽ được soạn thành task label `retro-action` và đi qua bản xem trước + Approve.
