---
name: sprint-report
description: Dùng khi Scrum Master yêu cầu báo cáo cuối sprint (“Tạo báo cáo Sprint 12”) hoặc đề xuất cải thiện cho nhóm và từng thành viên. Viết bản nháp từ bảng chỉ số đã tính sẵn; phụ lục theo thành viên chỉ Scrum Master xem.
---

# Báo cáo cuối sprint

Đầu vào: bảng chỉ số do code tính (`metrics/`), danh sách issue kèm key, mục tiêu sprint, nhận xét
của Scrum Master (có thể chưa có). Bạn chỉ **diễn giải** số liệu; Scrum Master đánh giá và quyết định.

## Template

```markdown
# Báo cáo Sprint <số> – Project <key>
## 1. Tóm tắt (3–5 câu)
## 2. Mục tiêu sprint và kết quả
## 3. Chỉ số nhóm (so với 3 sprint trước)
## 4. Điểm nổi bật
## 5. Vấn đề và điểm nghẽn (kèm issue key)
## 6. Đầu vào cho Retrospective
## 7. Nhận xét của Scrum Master về cả nhóm (Scrum Master viết)
## 8. Đề xuất cải tiến cho cả nhóm (TaskMate gợi ý, Scrum Master chỉnh)
## 9. Action item cho sprint sau
## 10. Tiến độ cả dự án (mục 12)

--- Phụ lục riêng theo thành viên (chỉ Scrum Master xem) ---
### <Tên thành viên>
- Tóm tắt dữ liệu (TaskMate, kèm issue key)
- Nhận xét của Scrum Master
- Đề xuất cải thiện (TaskMate gợi ý, Scrum Master thêm, xóa, sửa)
- Điều đã thống nhất với thành viên (điền sau buổi 1:1)
```

Mục chưa có dữ liệu: ghi "Chưa có dữ liệu" (ví dụ mục 10 khi chưa bật tiến độ dự án).
Mục 2 "Đạt mục tiêu": dùng đúng lựa chọn của Scrum Master (Đạt / Một phần / Không đạt), không tự kết luận.
Mục 7: để trống chờ Scrum Master viết nếu chưa có, không viết thay.

## Quy tắc số liệu

- **Mọi con số lấy nguyên từ bảng chỉ số.** Không tự cộng, chia, làm tròn, không tạo số mới.
  Guardrail sẽ so từng số với bảng; sai thì bản nháp bị sinh lại.
- Mỗi nhận định dẫn tới task cụ thể bằng issue key.
- Tách rõ hai ý:
  - **Dữ liệu cho thấy:** sự kiện, có số và issue key.
  - **Nguyên nhân có thể là:** giả thuyết để nhóm thảo luận, viết dạng câu hỏi hoặc "có thể".

## Đề xuất cải tiến cho cả nhóm (mục 8)

- 3–5 đề xuất, mỗi đề xuất gồm: làm gì, dẫn chứng (issue key hoặc chỉ số), đo bằng chỉ số nào ở sprint sau.
- Nói về quy trình (review, chia nhỏ việc, quản lý phạm vi), không nói về con người.

## Phụ lục theo thành viên

- Liệt kê **mọi** thành viên được cung cấp, kể cả người không có task.
- Tóm tắt dữ liệu: số task được giao và hoàn thành, story points, task dời, task kẹt, bug mở lại.
  Mỗi số kèm bối cảnh có trong dữ liệu (bị chặn bởi task khác, đổi người giữa chừng, task khó).
- **Chỉ đề xuất cho người đã có nhận xét của Scrum Master.** Người chưa có ghi:
  "Chưa có nhận xét, chưa đề xuất."
- Tối đa 2–3 đề xuất mỗi người. Dựa trên nhận xét của Scrum Master là chính, số liệu làm dẫn chứng.
- Mỗi đề xuất: hành vi hoặc quy trình cụ thể, dẫn chứng (issue key hoặc câu nhận xét),
  cách đo ở sprint sau. Viết dạng lựa chọn ("có thể thử…").
- Thiếu dữ liệu (vào giữa sprint, nghỉ phép): ghi "Không đủ dữ liệu", không suy diễn.
- "Điều đã thống nhất": để trống, Scrum Master điền sau buổi 1:1.

## Không được

- Xếp hạng, chấm điểm, so sánh thành viên với nhau; bảng so sánh cá nhân trong báo cáo chung.
- Nhận xét tính cách, năng lực, thái độ; đoán nguyên nhân cá nhân (động lực, sức khỏe, gia đình).
- Trả lời "ai làm kém nhất" bằng một cái tên. Thay vào đó đưa dữ liệu kèm bối cảnh cho từng task.
- Tự đóng sprint, tự tạo action item trên Jira (action item đi qua bản xem trước và Approve).

| Không nên | Nên |
| --- | --- |
| "Nam làm việc chậm, cần cố gắng hơn" | "SHOP-131 và SHOP-140 chờ review 4–5 ngày. Có thể thử chia PR dưới 300 dòng và gắn reviewer ngay khi mở PR. Đo bằng thời gian chờ review ở Sprint 13." |
| "Nhóm thiếu trách nhiệm nên dời nhiều task" | "Dữ liệu cho thấy 3 task dời sang sprint sau, cả 3 đều nằm ở Review hơn 3 ngày (SHOP-…). Nguyên nhân có thể là khâu review chưa có người phụ trách rõ ràng?" |
