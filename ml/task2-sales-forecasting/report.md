# Slide Content - Location Sale Forecasting (LSF)

Tài liệu này dùng để dựng slide thuyết trình. Mỗi slide nên giữ ngắn gọn; phần "Gợi ý trình bày" dùng để nói khi thuyết trình.

## Slide 1 - Bài toán

**Nội dung slide**
- Mục tiêu: dự báo quantity bán ra trong `01/2026`.
- Đơn vị dự báo: từng cặp `(location, item_id)`.
- Output: bảng `location`, `item_id`, `quantity`.
- Metric chính: `MAPE_quantity`.

**Gợi ý trình bày**
- Đây là bài toán sale forecasting theo cửa hàng và sản phẩm.
- Với mỗi location-item, model cần dự đoán số lượng bán trong tháng tiếp theo.
- Kết quả cuối được lưu trong `submission.pkl`.

## Slide 2 - Dữ liệu

**Nội dung slide**
- `transaction_full_2025.parquet`: lịch sử mua hàng.
- `event_full_2025.parquet`: view item và add-to-cart.
- `items.parquet`: metadata sản phẩm.
- Blind test: tháng `01/2026`.

**Gợi ý trình bày**
- Transaction là nguồn target chính vì cần dự báo quantity bán.
- Event là tín hiệu nhu cầu trước khi mua.
- Metadata giúp xử lý item/category/brand/sale status.

## Slide 3 - Output và ràng buộc

**Nội dung slide**
- File nộp: `submission.pkl`.
- Columns: `location`, `item_id`, `quantity`.
- Quantity không âm.
- Không duplicate cặp `(location, item_id)`.
- Đúng dtype/schema theo yêu cầu.

**Gợi ý trình bày**
- Forecast đúng nhưng gắn sai key location-item sẽ làm submission sai.
- Vì vậy sau dự đoán phải kiểm tra schema, null, duplicate và quantity range.

## Slide 4 - Metric MAPE quantity

**Nội dung slide**
- MAE: sai số tuyệt đối.
- MAPE: sai số tương đối.
- `MAPE_quantity = mean(|actual - pred| / actual)`.
- Metric chính là `MAPE_quantity`.

**Gợi ý trình bày**
- MAPE cho biết model sai bao nhiêu phần trăm so với thực tế.
- Vì item/location có quy mô bán khác nhau, MAPE công bằng hơn MAE trong nhiều trường hợp.
- Tối ưu MAPE giúp không bỏ qua item bán ít.

## Slide 5 - Time split

**Nội dung slide**
- Không random split.
- Dùng các tháng trước để dự đoán tháng kế tiếp.
- Validation gần blind: dự đoán các tháng cuối năm 2025.
- Final: dùng lịch sử 2025 để dự báo `01/2026`.

**Gợi ý trình bày**
- Forecasting là dự đoán tương lai nên split phải theo thời gian.
- Random split có nguy cơ leak dữ liệu tương lai vào train.
- Validation theo tháng giúp đánh giá gần với blind test.

## Slide 6 - Feature engineering

**Nội dung slide**
- Monthly aggregation theo `(location, item_id, month)`.
- Lag features: quantity tháng trước.
- Rolling features: mean/sum/max trong nhiều tháng.
- Event features: view/add-to-cart gần đây.
- Item metadata: category, brand, sale status.

**Gợi ý trình bày**
- Dữ liệu giao dịch được gom về mức tháng vì target là quantity theo tháng.
- Lag và rolling giúp model học xu hướng bán gần đây.
- Event giúp bắt tín hiệu nhu cầu trước khi giao dịch xảy ra.

## Slide 7 - Modeling và tuning

**Nội dung slide**
- Model chính: LightGBM regressor.
- Objective: dự báo `quantity`.
- Tuning theo validation `MAPE_quantity`.
- Calibrate/post-process prediction sau model.

**Gợi ý trình bày**
- LightGBM phù hợp với dữ liệu bảng lớn và nhiều feature lịch sử.
- Notebook thử nhiều cấu hình, chọn cấu hình có MAPE validation tốt.
- Sau model cần calibrate để giảm lỗi tương đối theo phân phối quantity.

## Slide 8 - Post-processing

**Nội dung slide**
- Clip prediction không âm.
- Điều chỉnh scale/calibration theo validation.
- Làm tròn/snap quantity hợp lý.
- Kiểm tra lại schema và duplicate key.

**Gợi ý trình bày**
- Post-processing không thay đổi bản chất model nhưng ảnh hưởng trực tiếp MAPE.
- Với MAPE, dự đoán quá cao/quá thấp ở item bán ít đều bị phạt mạnh.
- Bước cuối đảm bảo file nộp hợp lệ và ổn định.

## Slide 9 - Kết quả và kết luận

**Nội dung slide**
- Validation MAPE quantity khoảng `0.4168`.
- Internal test MAPE quantity khoảng `0.4147`.
- Output cuối có khoảng `2.19M` dòng.
- Pipeline: aggregation -> feature -> LightGBM -> calibration -> submission.

**Gợi ý trình bày**
- Điểm chính là xây pipeline forecast theo thời gian, không chỉ train model đơn lẻ.
- Lag/rolling feature là lõi của sale forecasting.
- Nếu tune tiếp, nên dùng rolling validation nhiều tháng và kiểm soát kỹ alignment location-item.

## Hình nên đưa vào slide

- Dataset overview.
- Sơ đồ time split theo tháng.
- Flow pipeline aggregation -> features -> LightGBM -> post-processing.
- Bar chart/bucket chart MAPE theo quantity bucket.
