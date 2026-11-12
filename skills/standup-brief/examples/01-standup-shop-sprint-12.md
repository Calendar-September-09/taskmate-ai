# Stand-up SHOP, thứ Năm 12/11/2026

## Đầu vào

```json
{
  "project": "SHOP",
  "date": "2026-11-12",
  "sprint": {"name": "SHOP Sprint 12", "day": 9, "total_days": 10},
  "done_tasks": 2, "total_tasks": 10, "done_points": 7, "total_points": 36,
  "attention": [
    {"key": "SHOP-105", "summary": "Xây dựng API thanh toán VNPay", "reasons": ["Review 6 ngày", "chặn SHOP-107", "hạn 13/11"]},
    {"key": "SHOP-106", "summary": "Xây dựng màn hình giỏ hàng (FE)", "reasons": ["quá hạn 10/11"]},
    {"key": "SHOP-111", "summary": "Tối ưu truy vấn danh sách đơn hàng", "reasons": ["Flagged"]},
    {"key": "SHOP-109", "summary": "Cấu hình email xác nhận đơn hàng", "reasons": ["chưa có người phụ trách"]},
    {"key": "SHOP-108", "summary": "Sửa lỗi crash khi thêm sản phẩm hết hàng vào giỏ", "reasons": ["thêm giữa sprint 07/11"]}
  ],
  "members": [
    {"name": "Nguyễn Văn Nam", "events": ["SHOP-111 cập nhật 10/11"], "in_progress": ["SHOP-104", "SHOP-108", "SHOP-110", "SHOP-111"]},
    {"name": "Phạm Minh Đức", "events": [], "in_progress": ["SHOP-106"]},
    {"name": "Trần Hoài Nam", "events": [], "in_progress": []},
    {"name": "Lê Thu Hà", "events": [], "in_progress": []}
  ]
}
```

## Đầu ra

```markdown
# Stand-up SHOP – thứ Năm, 12/11/2026
**Tổng quan:** Ngày 9/10 của SHOP Sprint 12 · 2/10 task xong · 7/36 story points

## Cần chú ý
- SHOP-105 Xây dựng API thanh toán VNPay – ở Review 6 ngày, đang chặn SHOP-107, hạn 13/11
- SHOP-106 Xây dựng màn hình giỏ hàng (FE) – quá hạn 10/11
- SHOP-111 Tối ưu truy vấn danh sách đơn hàng – đang Flagged
- SHOP-109 Cấu hình email xác nhận đơn hàng – chưa có người phụ trách
- SHOP-108 Sửa lỗi crash khi thêm sản phẩm hết hàng vào giỏ – thêm giữa sprint 07/11

## Theo từng thành viên
- **Nguyễn Văn Nam:** cập nhật SHOP-111 ngày 10/11 · Đang làm: SHOP-104, SHOP-108, SHOP-110, SHOP-111
- **Phạm Minh Đức:** Không có cập nhật trên Jira. · Đang làm: SHOP-106
- **Trần Hoài Nam:** Không có cập nhật trên Jira.
- **Lê Thu Hà:** Không có cập nhật trên Jira.

## Gợi ý cho buổi họp
1. SHOP-105 chờ review 6 ngày và đang chặn SHOP-107, hạn là ngày mai. Ai có thể review trong hôm nay?
2. SHOP-111 đang Flagged: vướng ở đâu, nhóm cần hỗ trợ gì để gỡ?
3. SHOP-109 chưa có người phụ trách và sprint còn 1 ngày: giữ trong sprint hay chuyển về backlog?
```
