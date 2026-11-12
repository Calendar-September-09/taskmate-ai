---
name: standup-brief
description: Dùng khi chuẩn bị Daily Stand-up (“Chuẩn bị stand-up cho SHOP” hoặc tác vụ định kỳ buổi sáng). Tóm tắt thay đổi trên Jira từ buổi trước, việc cần chú ý và 2–3 câu hỏi gợi ý; chỉ đọc Jira.
---

# Bản tóm tắt trước Daily Stand-up

Đầu vào (code đã tính sẵn): ngày thứ mấy của sprint, số task xong/tổng, story points đã xong,
danh sách cần chú ý (kẹt, quá hạn, hạn hôm nay/mai, chưa có người, bị chặn, thêm giữa sprint),
thay đổi theo từng thành viên từ buổi stand-up trước, danh sách thành viên.

Mục đích: Scrum Master vào họp đã nắm tình hình, buổi họp tập trung gỡ vướng. Bản tóm tắt chỉ để
chuẩn bị, không thay thế buổi họp. Luồng này **chỉ đọc** Jira.

## Template (gọn trong một màn hình)

```markdown
# Stand-up <Project> – <thứ, dd/mm/yyyy>
**Tổng quan:** Ngày <n>/<tổng> của <tên sprint> · <x>/<y> task xong · <a>/<b> story points

## Cần chú ý
- <issue key> <tiêu đề ngắn> – <lý do: kẹt N ngày ở Review / quá hạn dd/mm / chưa có người / bị chặn bởi KEY / thêm giữa sprint>

## Theo từng thành viên
- **<Tên>:** <sự kiện trên Jira: chuyển KEY sang Done, nhận KEY…> · Đang làm: <KEY, KEY>
- **<Tên>:** Không có cập nhật trên Jira.

## Gợi ý cho buổi họp
1. <câu hỏi gỡ vướng, có issue key>
2. ...
```

## Quy tắc

- **Mọi số liệu và danh sách lấy nguyên từ đầu vào.** Không tự đếm lại, không tự tính số ngày.
- Mọi dòng trong "Cần chú ý" và "Theo từng thành viên" đều có issue key.
- Sắp "Cần chú ý" theo mức ảnh hưởng: bị chặn hoặc đang chặn task khác → quá hạn, hạn hôm nay
  → kẹt lâu → chưa có người → thêm giữa sprint. Mỗi task chỉ xuất hiện một lần, gộp các lý do.
- Tối đa khoảng 7 dòng "Cần chú ý"; còn nhiều hơn thì ghi "và N task khác" (N lấy từ đầu vào).
- "Theo từng thành viên" chỉ liệt kê **sự kiện trên Jira**, không nhận xét, không đánh giá.
- Thành viên không có thay đổi: ghi đúng "Không có cập nhật trên Jira." Không suy diễn là người
  đó không làm việc, vì có thể họ chưa cập nhật Jira.
- Gợi ý cho buổi họp: 2–3 câu hỏi hướng tới **gỡ vướng**, hỏi cả nhóm, không chất vấn cá nhân.
  - Nên: "SHOP-105 chờ review 6 ngày và đang chặn SHOP-107, ai có thể review hôm nay?"
  - Không nên: "Vì sao Nam để SHOP-105 lâu vậy?"
- Không đề xuất thao tác ghi tự động. Nếu cần gắn Flagged hay đổi người, chỉ gợi ý để Scrum Master
  quyết định sau buổi họp (đi qua bản xem trước và Approve).
