# Lỗi crash giỏ hàng, có đủ bước

## Đầu vào

> Báo bug gấp cho SHOP: trên app Android 2.3.1, thêm sản phẩm hết hàng vào giỏ là app văng ra.
> Mở chi tiết một sản phẩm có tồn kho 0, bấm "Thêm vào giỏ" là crash. Đáng lẽ phải báo "Sản phẩm đã hết hàng".

## Đầu ra

```json
{
  "issue_type": "Bug",
  "summary": "Sửa lỗi crash khi thêm sản phẩm hết hàng vào giỏ",
  "description": "## Mô tả\nỨng dụng Android bị văng khi người mua thêm sản phẩm hết hàng vào giỏ, làm gián đoạn luồng mua hàng.\n\n## Bước tái hiện\n1. Mở ứng dụng Android phiên bản 2.3.1\n2. Mở chi tiết một sản phẩm có tồn kho bằng 0\n3. Bấm \"Thêm vào giỏ\"\n\n## Kết quả mong đợi\nHiện thông báo \"Sản phẩm đã hết hàng\", không thêm vào giỏ.\n\n## Kết quả thực tế\nỨng dụng bị văng (crash).\n\n## Môi trường\nỨng dụng Android 2.3.1; thiết bị và môi trường: <cần bổ sung>\n\n## Mức nghiêm trọng\nCao – chặn một bước của luồng mua hàng, chưa có cách vòng trên app.\n\n## Acceptance Criteria\n- [ ] Thực hiện lại các bước tái hiện thì thấy thông báo \"Sản phẩm đã hết hàng\" và app không văng\n- [ ] Có test tự động cho trường hợp tồn kho bằng 0",
  "project_text": "SHOP",
  "assignee_text": null,
  "due_text": null,
  "priority_text": "gấp",
  "sprint_text": null,
  "parent_key": null,
  "story_points": null,
  "labels": ["android"],
  "quote": "Báo bug gấp cho SHOP: trên app Android 2.3.1, thêm sản phẩm hết hàng vào giỏ là app văng ra.",
  "confidence": 0.9
}
```
