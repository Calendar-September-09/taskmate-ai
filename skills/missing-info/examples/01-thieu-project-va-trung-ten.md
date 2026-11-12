# Thiếu project, tên trùng, ngày không hiểu

## Đầu vào

Yêu cầu: "Tạo task fix lỗi thanh toán cho Nam, xong trước đầu tuần sau nữa"

Kết quả code:
- missing_fields: ["project_key"]
- Memory: không có project mặc định; người dùng có quyền ở SHOP và MOBILE
- match_member("Nam") trên SHOP: Ambiguous → Nguyễn Văn Nam (acc-nam-be), Trần Hoài Nam (acc-nam-qa)
- parse_vi_date("đầu tuần sau nữa"): None
- Skill bug-report đã soạn mô tả, phần "Bước tái hiện" đang là `<cần bổ sung>`

## Đầu ra

TaskMate cần thêm vài thông tin trước khi soạn bản xem trước:

1. Task thuộc project nào: **SHOP** hay **MOBILE**?
2. Dự án SHOP có 2 người tên Nam: **Nguyễn Văn Nam** và **Trần Hoài Nam**. Bạn muốn giao cho ai?
3. TaskMate chưa hiểu "đầu tuần sau nữa" là ngày nào. Bạn cho ngày cụ thể (dd/mm) được không?

Đã tự điền: Loại Bug (vì có "lỗi"). Nếu có, bạn gửi thêm các bước gây ra lỗi để TaskMate điền
vào mục "Bước tái hiện".
