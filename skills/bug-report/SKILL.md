---
name: bug-report
description: Dùng khi yêu cầu nói về lỗi phần mềm: có từ "lỗi", "bug", "crash", "không chạy", "sai", "treo". Viết bản nháp Bug có bước tái hiện, kết quả mong đợi và thực tế, môi trường, mức nghiêm trọng.
---

# Viết Bug report

Dùng chung định dạng JSON của Skill task-writing, với `issue_type` = "Bug".

## Tiêu đề

- Dạng: "Sửa lỗi <hiện tượng> khi <điều kiện>".
- Nêu hiện tượng người dùng thấy, không đoán nguyên nhân trong tiêu đề.

Tốt: "Sửa lỗi sai tổng tiền khi áp mã giảm giá"
Chưa tốt: "Bug do hàm calcTotal làm tròn sai"

## Template mô tả

```markdown
## Mô tả
<1–2 câu: lỗi gì, ảnh hưởng tới ai>

## Bước tái hiện
1. ...
2. ...

## Kết quả mong đợi
...

## Kết quả thực tế
...

## Môi trường
<web/app, trình duyệt hoặc thiết bị, phiên bản, môi trường staging/production>

## Mức nghiêm trọng
<Nghiêm trọng / Cao / Trung bình / Thấp> – <lý do ngắn>

## Acceptance Criteria
- [ ] Thực hiện lại các bước tái hiện thì nhận được kết quả mong đợi
- [ ] Có test tự động cho trường hợp này
```

## Quy tắc

- **Không bịa** bước tái hiện, môi trường hay thông báo lỗi. Thiếu thì ghi `<cần bổ sung>`;
  agent sẽ hỏi lại qua Skill missing-info.
- Có log, ảnh chụp, mã lỗi thì chép nguyên vào "Kết quả thực tế" (che token, mật khẩu nếu có).
- Mức nghiêm trọng chỉ là gợi ý để Scrum Master xem; **không tự đặt priority**. Chỉ chép cụm
  chỉ mức gấp người dùng nói vào `priority_text`.

| Mức nghiêm trọng | Dấu hiệu |
| --- | --- |
| Nghiêm trọng | Sập trang, mất dữ liệu, sai tiền, lỗi bảo mật, chặn luồng chính |
| Cao | Một tính năng chính không dùng được, chưa có cách vòng |
| Trung bình | Có cách vòng, ảnh hưởng một nhóm nhỏ người dùng |
| Thấp | Giao diện lệch, chính tả, ảnh hưởng nhỏ |

- Người dùng chỉ hỏi "có phải lỗi không?" mà không yêu cầu tạo: trả lời ngắn, hỏi có muốn tạo
  Bug không, không tự tạo bản nháp.
