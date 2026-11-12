---
name: retro
description: Dùng khi chuẩn bị hoặc tổng hợp buổi Retrospective: biến mẫu lặp lại trong dữ liệu sprint thành câu hỏi thảo luận, gom ghi chú Retro thành 3 nhóm, đề xuất hành động SMART và theo dõi action item retro-action của sprint trước.
---

# Retrospective

Retro là buổi của cả nhóm. TaskMate chuẩn bị đầu vào và tổng hợp; **nhóm** chọn hành động.
Không nhắm vào cá nhân, không xếp hạng.

## 1. Theo dõi action item sprint trước (mở đầu buổi)

Đầu vào: các task label `retro-action` của sprint trước, trạng thái hiện tại, chỉ số liên quan
(trước và sau, do code tính). Với mỗi action item, ghi:

- `<KEY> <hành động>` – trạng thái Jira – chỉ số: `<trước> → <sau>` (lấy nguyên từ đầu vào).
- Kết luận chỉ dùng: "đã cải thiện", "chưa cải thiện", "chưa đủ dữ liệu". So sánh do code đưa sẵn.

## 2. Câu hỏi thảo luận từ dữ liệu

Từ bảng chỉ số và danh sách issue, tìm **mẫu lặp lại** và chuyển thành câu hỏi mở:

- Dữ liệu cho thấy gì (có số, có issue key) → câu hỏi "ở đâu / vì sao / nhóm có thể…?"
- Ví dụ: "3 trong 4 task dời sang sprint sau đều nằm ở Review hơn 3 ngày (SHOP-105, …).
  Khâu review đang vướng ở đâu?"
- 2–4 câu hỏi. Không hỏi về một người cụ thể.

## 3. Gom ghi chú của nhóm

Scrum Master dán ghi chú (giấy dán, chat, bảng). Bạn:

1. Xếp mỗi ý vào đúng một nhóm: **Làm tốt** / **Cần cải thiện** / **Ý tưởng**.
2. Gộp các ý trùng hoặc gần trùng thành một dòng, ghi số người nêu `(×3)`.
3. Giữ ý chính của người viết, viết lại ngắn gọn; không thêm ý mới.
4. Nếu Scrum Master bật **ẩn tên**: bỏ mọi tên người viết **và** tên người được nhắc trong ý
   (thay bằng "một thành viên"). Nếu không bật: vẫn không thêm tên vào chỗ ghi chú gốc không có.
5. Ý mang tính công kích cá nhân: viết lại thành vấn đề quy trình, ví dụ "PR chờ review lâu"
   thay cho "X review chậm".

## 4. Đề xuất hành động SMART

- 3–5 đề xuất, mỗi đề xuất gắn với một ý "Cần cải thiện" hoặc một mẫu dữ liệu.
- Mỗi đề xuất có đủ: **Làm gì** (cụ thể) · **Ai phụ trách** · **Hạn** · **Đo bằng chỉ số nào**.
- "Ai phụ trách" và "Hạn": để `<nhóm chọn>` nếu ghi chú không nói. Không tự chỉ định người.
- Ưu tiên hành động nhỏ, làm được trong một sprint.
- Nhóm chọn 1–3 hành động. Hành động được chọn thành task theo định dạng task-writing:
  `issue_type` Task, label `retro-action`, đưa vào sprint sau, và **qua bản xem trước + Approve**.

## Định dạng đầu ra

```markdown
## Action item sprint trước
## Câu hỏi thảo luận từ dữ liệu
## Ghi chú của nhóm
### Làm tốt
### Cần cải thiện
### Ý tưởng
## Đề xuất hành động (nhóm chọn 1–3)
| # | Làm gì | Ai phụ trách | Hạn | Đo bằng |
```

Mục nào không có đầu vào thì ghi "Chưa có dữ liệu" (ví dụ sprint đầu tiên chưa có action item).
