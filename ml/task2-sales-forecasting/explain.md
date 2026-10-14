# Giải thích task Location Sale Forecasting (LSF)

## 1. Mục tiêu task

Location Sale Forecasting là bài toán dự báo số lượng sản phẩm bán ra trong tương lai.

Đơn vị dự báo là từng cặp:

```text
(location, item_id)
```

Với mỗi location và item, model cần dự đoán `quantity` bán trong tháng blind test `01/2026`.

Output nộp là `submission.pkl` dạng bảng:

| location | item_id | quantity |
| --- | --- | ---: |
| 42 | 0000280000138 | 1.0 |
| 42 | 0006020000278 | 2.0 |

Nói ngắn gọn: dự đoán "sản phẩm B tại cửa hàng A tháng sau bán được bao nhiêu đơn vị".

## 2. Dữ liệu sử dụng

| File | Vai trò |
| --- | --- |
| `transaction_full_2025.parquet` | Lịch sử mua hàng, dùng để tạo target quantity. |
| `event_full_2025.parquet` | Hành vi view/add-to-cart, dùng làm tín hiệu nhu cầu. |
| `items.parquet` | Metadata sản phẩm như category, brand, sale status. |

Transaction là dữ liệu chính vì target là số lượng bán. Event không phải target, nhưng giúp phát hiện nhu cầu trước khi purchase xảy ra. Metadata giúp model hiểu khác biệt giữa các nhóm sản phẩm.

## 3. Output cần nộp

File submission cần có đúng ba cột:

```text
location, item_id, quantity
```

Các kiểm tra quan trọng:

- object là pandas DataFrame;
- không thiếu cột;
- không null;
- không duplicate cặp `(location, item_id)`;
- `quantity` không âm;
- dtype hợp lệ để evaluator đọc được.

Trong forecasting, alignment giữa prediction và key `(location, item_id)` rất quan trọng. Nếu quantity đúng nhưng gắn nhầm item/location, metric sẽ sai nặng.

## 4. Split theo thời gian

Forecasting là dự đoán tương lai từ quá khứ, nên không dùng random split.

Cách split đúng:

- dùng các tháng trước làm lịch sử;
- tạo feature từ lịch sử đó;
- dự đoán tháng kế tiếp;
- không dùng dữ liệu sau target month.

Final blind dùng dữ liệu năm 2025 để dự báo tháng `01/2026`.

## 5. Metric trong đề

Đề có các metric liên quan đến quantity và revenue. Trong notebook, metric chính là `MAPE_quantity`.

### MAE quantity

```text
MAE = mean(|actual - prediction|)
```

MAE quantity đo trung bình model dự đoán sai bao nhiêu đơn vị sản phẩm. Metric này dễ hiểu nhưng item bán nhiều có thể chi phối kết quả.

### MAE revenue

```text
revenue = quantity * price
MAE_revenue = mean(|actual_revenue - predicted_revenue|)
```

Metric này quan tâm sai số doanh thu, phù hợp nếu mục tiêu kinh doanh chính là tiền. Task hiện tại ưu tiên quantity.

### MAPE quantity

```text
MAPE = mean(|actual - prediction| / actual)
```

MAPE quantity đo sai số tương đối theo phần trăm. Ví dụ actual là 20, dự đoán 15 thì lỗi là:

```text
|20 - 15| / 20 = 0.25
```

Tức là sai 25%.

### MAPE revenue

MAPE revenue tính tương tự nhưng trên doanh thu:

```text
MAPE_revenue = mean(|actual_revenue - predicted_revenue| / actual_revenue)
```

## 6. Vì sao chọn MAPE quantity?

Notebook ưu tiên `MAPE_quantity` vì:

- đề chọn đây là metric chính;
- target nộp là `quantity`;
- location-item có quy mô bán rất khác nhau;
- sai số tương đối giúp item bán ít vẫn được quan tâm.

Ví dụ:

- item A bán 1000, dự đoán sai 50: lỗi 5%;
- item B bán 10, dự đoán sai 5: lỗi 50%.

MAE thấy lỗi 50 lớn hơn lỗi 5, nhưng MAPE cho thấy item B đang bị dự đoán tệ hơn về mặt tương đối.

## 7. Pipeline modeling

Pipeline gồm các bước chính sau.

### 7.1. Monthly aggregation

Transaction gốc là dữ liệu từng giao dịch. Vì target là quantity theo tháng, dữ liệu được gom về mức:

```text
location, item_id, month
```

Các thống kê thường dùng:

- tổng quantity trong tháng;
- số transaction;
- số customer;
- revenue hoặc price-related signal nếu có.

### 7.2. Lag features

Lag là quantity trong các tháng trước:

- `qty_lag_1`: tháng gần nhất;
- `qty_lag_2`: hai tháng trước;
- `qty_lag_3`: ba tháng trước.

Lag quan trọng vì sản phẩm bán tốt gần đây thường có khả năng tiếp tục bán tốt.

### 7.3. Rolling features

Rolling là thống kê trên cửa sổ nhiều tháng:

- rolling mean 3 tháng;
- rolling sum 6 tháng;
- rolling max;
- số tháng gần đây có bán.

Rolling giúp model học xu hướng ổn định hơn, tránh phụ thuộc hoàn toàn vào một tháng gần nhất.

### 7.4. Event features

Event được tổng hợp thành feature như:

- số lượt view gần đây;
- số lượt add-to-cart gần đây;
- tỷ lệ add-to-cart/view.

Event giúp bắt nhu cầu mới trước khi quantity tăng trong transaction.

### 7.5. Item metadata

Metadata bổ sung thông tin:

- category;
- brand;
- sale status;
- đặc điểm sản phẩm.

`sale_status` quan trọng vì item không còn bán thường không nên được dự báo giống item đang bán.

### 7.6. LightGBM regressor

LightGBM học quan hệ:

```text
features(location, item, history, event, metadata) -> quantity tháng sau
```

Lý do dùng LightGBM:

- phù hợp dữ liệu bảng lớn;
- xử lý tốt feature lag/rolling;
- bắt được quan hệ phi tuyến;
- train tương đối nhanh.

### 7.7. Calibration và post-processing

Sau khi model dự đoán, notebook điều chỉnh prediction để phù hợp metric:

- clip quantity không âm;
- scale/calibrate theo validation;
- snap/làm tròn quantity ở một số vùng;
- kiểm tra lại schema output.

Với MAPE, post-processing quan trọng vì lỗi tương đối ở quantity nhỏ có thể ảnh hưởng mạnh.

## 8. Kết quả chính

Notebook ghi nhận:

- validation MAPE quantity khoảng `0.4168`;
- internal test MAPE quantity khoảng `0.4147`;
- output cuối khoảng `2.19M` dòng.

Kết quả này đến từ pipeline kết hợp lịch sử bán, event signal, metadata, LightGBM và calibration.

## 9. Ý chính khi thuyết trình

- Task dự báo quantity theo từng location-item cho tháng `01/2026`.
- Transaction tạo target chính; event là tín hiệu nhu cầu phụ.
- Split theo thời gian để tránh leak tương lai.
- `MAPE_quantity` là metric chính vì đo sai số tương đối của quantity.
- Feature lag/rolling là phần lõi của sale forecasting.
- LightGBM phù hợp với dữ liệu bảng lớn.
- Post-processing giúp prediction hợp lệ và tối ưu hơn theo MAPE.
- Output phải đúng schema và đúng alignment `(location, item_id)`.

## 10. Hướng cải thiện

- Rolling validation nhiều tháng để đánh giá ổn định hơn.
- Tune riêng item bán ít và item bán nhiều.
- Thêm feature seasonality/lễ nếu validation chứng minh có lợi.
- Dùng ensemble nhiều LightGBM seed/feature set.
- Tối ưu calibration theo bucket quantity.
