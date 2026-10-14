# Giải thích task Personalized Item Recommendation (PIR)

## 1. Mục tiêu task

PIR là bài toán gợi ý sản phẩm cá nhân hóa cho từng khách hàng. Với mỗi `customer_id`, hệ thống cần trả về đúng 10 `item_id` có khả năng được khách mua trong tháng blind test `01/2026`.

Output nộp là file `submission.pkl` dạng:

```python
{
    customer_id_1: [item_1, item_2, ..., item_10],
    customer_id_2: [item_1, item_2, ..., item_10],
}
```

Nói đơn giản: từ lịch sử năm 2025, dự đoán 10 sản phẩm khách có khả năng mua ở tháng tiếp theo.

## 2. Kiosk/web recommendation

Trong bán hàng, kiosk/web là nơi hệ thống hiển thị sản phẩm gợi ý cho người dùng:

- kiosk: màn hình/thiết bị bán hàng hoặc tra cứu tại cửa hàng;
- web/app: giao diện mua hàng online;
- recommendation area: vùng hiển thị item được gợi ý.

Giao diện chỉ có số slot giới hạn, ví dụ 10 sản phẩm. Vì vậy task tập trung vào top 10 item, không cần dự đoán toàn bộ catalog.

## 3. Dữ liệu sử dụng

| File | Vai trò |
| --- | --- |
| `transaction_full_2025.parquet` | Lịch sử mua hàng, dùng để tạo label purchase. |
| `event_full_2025.parquet` | Hành vi `view_item`, `add_to_cart`, dùng làm tín hiệu quan tâm. |
| `items.parquet` | Metadata sản phẩm như category, brand, sale status. |

Transaction là nguồn quan trọng nhất vì metric đánh giá trên sản phẩm khách thật sự mua. Event và metadata giúp mở rộng candidate và bổ sung feature.

## 4. Split theo thời gian

Task dự đoán tương lai nên validation phải theo thứ tự thời gian:

- validation: dùng dữ liệu trước tháng 12 để dự đoán purchase tháng 12;
- final: dùng dữ liệu năm 2025 để dự đoán tháng `01/2026`.

Không dùng random split vì có thể làm lộ hành vi tương lai vào train, khiến validation cao giả.

## 5. Metric trong đề

### Precision@10

Precision@10 là metric chính:

```text
precision@10 = số item trong top 10 mà khách thật sự mua / 10
```

Ví dụ model recommend 10 item, trong đó có 2 item khách mua thật:

```text
precision@10 = 2 / 10 = 0.2
```

Metric này phù hợp vì output bắt buộc là 10 item và giao diện kiosk/web cũng chỉ hiển thị một số item giới hạn.

### IoU

IoU đo độ giao nhau giữa tập item recommend và tập item mua thật:

```text
IoU = |recommend ∩ actual| / |recommend ∪ actual|
```

IoU hữu ích để xem hai tập giống nhau bao nhiêu, nhưng không trực tiếp tập trung vào 10 slot hiển thị như precision@10.

### Reciprocal rank

Metric `1 / rank(first hit item)` cho điểm cao nếu item đúng đầu tiên nằm ở vị trí cao. Nó phù hợp khi chỉ cần một hit đầu tiên thật sớm, nhưng task này cần tối đa số hit trong 10 item.

### MAP@10

MAP@10 tính cả số hit và vị trí hit trong top 10. Metric này chi tiết hơn precision@10 nhưng khó giải thích hơn. Notebook vẫn theo dõi MAP@10 để tham khảo, còn precision@10 là metric chính để chọn hướng.

## 6. Pipeline trong notebook

Pipeline gồm 5 bước chính.

### 6.1. Candidate generation

Không thể rank toàn bộ `customer_id x item_id` vì số cặp quá lớn. Notebook tạo candidate trước từ:

- item khách từng mua;
- item khách từng view/add-to-cart;
- item phổ biến gần đây;
- item liên quan theo nhóm hành vi.

Bước này giảm bài toán về một tập item có khả năng liên quan đến từng customer.

### 6.2. Feature engineering

Feature được tạo ở ba mức:

- user feature: mức độ active, số item từng tương tác, recency;
- item feature: popularity, repeat rate, recent share;
- pair feature: lịch sử mua/view/add-to-cart giữa customer và item.

Tín hiệu repeat purchase được ưu tiên vì trong retail, nhiều khách có xu hướng mua lại sản phẩm quen.

### 6.3. LightGBM ranking

Mỗi dòng train là một cặp `(customer_id, item_id)` với label:

```text
label = 1 nếu customer mua item trong target month
label = 0 nếu không mua
```

LightGBM học score xác suất/độ phù hợp cho từng cặp. Sau đó các item của mỗi customer được sort theo score để lấy top 10.

### 6.4. Segment fallback

Một số customer có ít lịch sử hoặc candidate yếu. Với nhóm này, notebook dùng fallback theo segment:

```text
segment = customer_id // 500000
```

Mỗi segment có danh sách item phổ biến riêng dựa trên dữ liệu gần thời điểm dự đoán. Cách này tốt hơn dùng một fallback chung cho toàn bộ customer.

### 6.5. Brand tail

Với customer có lịch sử brand rõ ràng, notebook chọn thêm một item từ brand mạnh của customer và chèn vào phần cuối top 10.

Ý tưởng là giữ các vị trí đầu do model tự tin nhất, chỉ điều chỉnh nhẹ phần tail để tăng khả năng hit.

## 7. Kết quả validation

| Stage | Validation precision@10 | Ý nghĩa |
| --- | ---: | --- |
| LightGBM baseline | 0.08486 | Model nền với feature cơ bản. |
| Repeat-aware LightGBM | 0.08574 | Thêm tín hiệu mua lặp lại. |
| Distinct-user fallback | 0.08677 | Fallback theo item có nhiều user mua. |
| Segment fallback | 0.08752 | Fallback theo nhóm customer. |
| Segment fallback + brand tail | 0.08776 | Hướng final được chọn. |

Kết quả blind test của hướng final đạt khoảng `9.22/100` precision@10.

## 8. Kiểm tra submission

File nộp cần thỏa:

- object là `dict`;
- key là `customer_id`;
- value là list `item_id`;
- mỗi list có đúng 10 item;
- không có item trùng trong cùng list.

Kiểm tra format là bước bắt buộc vì model tốt nhưng file sai schema thì vẫn không nộp được.

## 9. Ý chính khi thuyết trình

- Đây là bài toán dự đoán top 10 sản phẩm khách có thể mua trong tháng tiếp theo.
- Purchase là label chính, event và metadata là tín hiệu phụ.
- Split theo thời gian để tránh leak tương lai.
- Precision@10 phù hợp vì giao diện chỉ hiển thị 10 item.
- Pipeline gồm candidate generation, feature engineering, LightGBM ranking và post-processing.
- Segment fallback xử lý customer ít lịch sử.
- Brand tail bổ sung cá nhân hóa nhẹ ở cuối top 10.

## 10. Hướng cải thiện

- Rolling validation nhiều tháng để giảm phụ thuộc vào một tháng validation.
- Tune riêng nhóm customer active/inactive.
- Tăng chất lượng candidate theo category/brand.
- Ensemble nhiều list recommendation.
- Kiểm soát diversity trong top 10 nếu các item quá giống nhau.
