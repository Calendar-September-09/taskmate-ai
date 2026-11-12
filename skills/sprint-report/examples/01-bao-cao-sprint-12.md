# Báo cáo Sprint 12 (trích các mục chính và phụ lục)

## Đầu vào

Bảng chỉ số (do code tính) – SHOP Sprint 12, 02/11–13/11/2026:

| Chỉ số | Sprint 12 | TB 3 sprint trước |
| --- | --- | --- |
| Story points cam kết | 34 | 31 |
| Story points Done | 7 | 24 |
| Tỉ lệ hoàn thành | 21% | 77% |
| Thay đổi phạm vi | +2 (SHOP-108 thêm ngày 07/11) | +3 |
| Task dời sang sprint sau | 6 task, 25 điểm | 2 task, 7 điểm |
| Thời gian chờ review TB | 6,0 ngày (SHOP-105) | 2,1 ngày |
| Task kẹt > 3 ngày làm việc | SHOP-105 (Review), SHOP-104 (In Progress từ Sprint 11) | — |

Mục tiêu sprint: "Thanh toán VNPay và lịch sử đơn hàng". Scrum Master chọn: **Một phần**.
SHOP-107 (test E2E) bị chặn bởi SHOP-105. SHOP-111 Flagged.

Dữ liệu thành viên:
- Nguyễn Văn Nam: giao 5 task (SHOP-104, 105, 108, 110, 111), Done 0; SHOP-104 chuyển từ Sprint 11.
- Phạm Minh Đức: giao 2 task, Done 1 (SHOP-112, 5 điểm).
- Lê Thu Hà: không có task trong sprint.

Nhận xét của Scrum Master: Nam – "nhận nhiều việc BE cùng lúc, PR VNPay chờ review lâu". Đức, Hà – chưa có.

## Đầu ra

```markdown
## 1. Tóm tắt
Sprint 12 hoàn thành 7/34 story points (21%), thấp hơn trung bình 3 sprint trước (77%).
Mục tiêu sprint đạt một phần: lịch sử đơn hàng đã xong (SHOP-112), thanh toán VNPay còn ở Review (SHOP-105).
6 task với 25 điểm dời sang sprint sau. Điểm nghẽn rõ nhất là khâu review: SHOP-105 chờ 6,0 ngày
và đang chặn SHOP-107.

## 5. Vấn đề và điểm nghẽn
- **Dữ liệu cho thấy:** SHOP-105 ở Review 6,0 ngày (trung bình trước đây 2,1 ngày) và chặn SHOP-107.
  **Nguyên nhân có thể là:** chưa có người được chỉ định review cho phần BE?
- **Dữ liệu cho thấy:** SHOP-104 bắt đầu từ Sprint 11 và vẫn In Progress.
  **Nguyên nhân có thể là:** story 8 điểm quá lớn để xong trong một sprint?
- **Dữ liệu cho thấy:** SHOP-111 đang Flagged.

## 8. Đề xuất cải tiến cho cả nhóm
1. Chỉ định người review ngay khi mở PR, cam kết phản hồi trong 24 giờ. Dẫn chứng: SHOP-105.
   Đo bằng: thời gian chờ review ở Sprint 13.
2. Tách story từ 8 điểm trở lên trong buổi Planning. Dẫn chứng: SHOP-104. Đo bằng: số task dời sang sprint sau.
3. Khi lập kế hoạch, xem trước task nào phụ thuộc task nào để xếp thứ tự. Dẫn chứng: SHOP-107 bị chặn bởi SHOP-105.
   Đo bằng: số task bị chặn cuối sprint.

--- Phụ lục riêng theo thành viên (chỉ Scrum Master xem) ---
### Nguyễn Văn Nam
- Tóm tắt dữ liệu: được giao 5 task (SHOP-104, SHOP-105, SHOP-108, SHOP-110, SHOP-111), chưa task nào Done.
  Bối cảnh: SHOP-104 chuyển từ Sprint 11; SHOP-105 chờ review 6,0 ngày; SHOP-108 thêm giữa sprint (07/11); SHOP-111 Flagged.
- Nhận xét của Scrum Master: nhận nhiều việc BE cùng lúc, PR VNPay chờ review lâu.
- Đề xuất cải thiện:
  1. Có thể thử giới hạn tối đa 2 task In Progress cùng lúc. Dẫn chứng: nhận xét của Scrum Master;
     SHOP-104, SHOP-108, SHOP-110, SHOP-111 cùng In Progress. Đo bằng: số task In Progress cùng lúc trong Sprint 13.
  2. Có thể thử chia PR SHOP-105 thành các phần nhỏ hơn và gắn reviewer khi mở PR. Dẫn chứng: SHOP-105.
     Đo bằng: thời gian chờ review các PR của Sprint 13.
- Điều đã thống nhất với thành viên:

### Phạm Minh Đức
- Tóm tắt dữ liệu: được giao 2 task, hoàn thành SHOP-112 (5 điểm); SHOP-106 đang In Progress.
- Nhận xét của Scrum Master:
- Đề xuất cải thiện: Chưa có nhận xét, chưa đề xuất.
- Điều đã thống nhất với thành viên:

### Lê Thu Hà
- Tóm tắt dữ liệu: không có task trong Sprint 12. Không đủ dữ liệu.
- Nhận xét của Scrum Master:
- Đề xuất cải thiện: Chưa có nhận xét, chưa đề xuất.
- Điều đã thống nhất với thành viên:
```

Ghi chú: mọi con số (34, 7, 21%, 6,0 ngày…) lấy nguyên từ bảng. Khi cần một con số không có trong
bảng (ví dụ số task In Progress cùng lúc), chỉ liệt kê issue key, không tự đếm.
Đức và Hà chưa có nhận xét nên không có đề xuất.
