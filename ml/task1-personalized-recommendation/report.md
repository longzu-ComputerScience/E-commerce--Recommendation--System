# Slide Content - Personalized Item Recommendation (PIR)

Tài liệu này dùng để dựng slide thuyết trình. Mỗi slide nên giữ ít chữ; phần "Gợi ý trình bày" dùng làm lời nói khi thuyết trình.

## Slide 1 - Bài toán

**Nội dung slide**
- Mục tiêu: recommend 10 sản phẩm cho mỗi `customer_id`.
- Output: `dict[int, list[str]]` trong `submission.pkl`.
- Blind test: tháng `01/2026`.
- Metric chính: `precision@10`.

**Gợi ý trình bày**
- Đây là bài toán gợi ý sản phẩm cá nhân hóa.
- Với mỗi khách hàng, hệ thống cần chọn 10 item có khả năng được mua cao nhất trong tháng tiếp theo.
- Vì giao diện kiosk/web chỉ hiển thị một số slot giới hạn, chất lượng top 10 là phần quan trọng nhất.

## Slide 2 - Dữ liệu

**Nội dung slide**
- `transaction_full_2025.parquet`: lịch sử mua hàng.
- `event_full_2025.parquet`: `view_item`, `add_to_cart`.
- `items.parquet`: metadata sản phẩm.
- Quy mô: khoảng 41.47M transaction, 30.32M event, 29,823 item.

**Gợi ý trình bày**
- Transaction là nguồn label chính vì test đánh giá theo item khách thật sự mua.
- Event giúp biết khách quan tâm item nào dù chưa mua.
- Metadata như brand/category giúp bổ sung tín hiệu sản phẩm.

## Slide 3 - Split theo thời gian

**Nội dung slide**
- Không dùng random split.
- Validation: dùng lịch sử trước tháng 12 để dự đoán purchase tháng 12.
- Final: dùng toàn bộ năm 2025 để dự đoán `01/2026`.
- Mục tiêu: mô phỏng đúng bài toán dự đoán tương lai.

**Gợi ý trình bày**
- Recommendation thực tế luôn dùng dữ liệu quá khứ để dự đoán hành vi tương lai.
- Random split có thể làm lộ thông tin sau thời điểm dự đoán.
- Tháng 12/2025 là validation gần nhất với blind test tháng 01/2026.

## Slide 4 - Metric precision@10

**Nội dung slide**
- Mỗi customer nhận đúng 10 item.
- `precision@10 = số item đoán đúng / 10`.
- Điểm cuối là trung bình trên các customer.
- Thứ tự trong top 10 ít quan trọng hơn việc chọn đúng item.

**Gợi ý trình bày**
- Nếu trong 10 item recommend có 1 item khách mua thật, precision@10 của customer đó là 0.1.
- Metric này phù hợp với kiosk/web vì chỉ có top 10 item được hiển thị.
- Do đó cả ranking model và post-processing top 10 đều ảnh hưởng điểm.

## Slide 5 - Pipeline tổng quan

**Nội dung slide**
- Candidate generation: purchase, event, popular item.
- Feature engineering: user, item, pair, repeat behavior.
- Ranking: LightGBM cho cặp `(customer_id, item_id)`.
- Post-processing: segment fallback và brand tail.
- Export: `submission.pkl`.

**Gợi ý trình bày**
- Không thể rank mọi item cho mọi customer vì số cặp quá lớn.
- Trước hết cần tạo candidate có khả năng liên quan, sau đó model score các candidate đó.
- Fallback xử lý customer ít lịch sử hoặc candidate yếu.

## Slide 6 - Feature chính

**Nội dung slide**
- User signal: activity, recency, số item từng mua/xem.
- Item signal: popularity, repeat rate, recent share.
- Pair signal: purchase/view/add-to-cart giữa user và item.
- Metadata: brand/category/sale status.

**Gợi ý trình bày**
- Feature được chia thành ba nhóm: khách hàng, sản phẩm, và quan hệ khách-sản phẩm.
- Tín hiệu repeat purchase quan trọng vì nhiều sản phẩm bán lẻ có xu hướng được mua lại.
- Event yếu hơn purchase nhưng giúp mở rộng candidate.

## Slide 7 - Post-processing

**Nội dung slide**
- Global fallback: item phổ biến gần đây.
- Segment fallback: fallback theo nhóm `customer_id // 500000`.
- Brand tail: thêm 1 item theo brand mạnh của customer vào cuối top 10.
- Mục tiêu: cải thiện coverage và cá nhân hóa nhẹ.

**Gợi ý trình bày**
- Với customer ít thông tin, fallback theo segment tốt hơn dùng một list phổ biến chung.
- Với customer có lịch sử brand rõ, brand-tail giúp tận dụng sở thích mua lặp theo brand.
- Các bước này không thay model chính, mà chỉnh danh sách cuối để tăng precision@10.

## Slide 8 - Kết quả validation

**Nội dung slide**

| Stage | Validation precision@10 |
| --- | ---: |
| LightGBM baseline | 0.08486 |
| Repeat-aware LightGBM | 0.08574 |
| Distinct-user fallback | 0.08677 |
| Segment fallback | 0.08752 |
| Segment fallback + brand tail | 0.08776 |

**Gợi ý trình bày**
- Mỗi bước cải thiện một phần nhỏ nhưng cộng lại tạo khác biệt.
- Repeat-aware feature giúp model hiểu hành vi mua lặp.
- Segment fallback và brand tail cải thiện top 10 sau khi model đã rank.

## Slide 9 - Submission và kết luận

**Nội dung slide**
- File nộp: `submission.pkl`.
- Format: `dict[int, list[str]]`.
- Mỗi customer có đúng 10 item.
- Bản final hướng tới blind precision@10 khoảng `9.22/100`.

**Gợi ý trình bày**
- Bài toán không chỉ là train model mà là xây pipeline recommendation end-to-end.
- Các phần quan trọng gồm candidate generation, feature, ranking, fallback và kiểm tra format.
- Nếu cải thiện tiếp, nên tune riêng theo nhóm customer active/inactive và dùng rolling validation nhiều tháng.

## Hình nên đưa vào slide

- Dataset overview: số dòng transaction/event/item.
- Sơ đồ time split: history 2025 -> December validation -> January blind.
- Flow pipeline: candidate -> feature -> LightGBM -> post-processing -> submission.
- Bar chart validation precision@10 theo từng stage.
