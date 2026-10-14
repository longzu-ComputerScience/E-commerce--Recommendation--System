"""
Solution 1 — Gợi ý sản phẩm theo Co-buy & Category tương tự
============================================================

Thuật toán:
    1. **Đầu vào**: item_id của sản phẩm đang xem.
    2. **Lấy ứng viên co-buy**: truy xuất bảng co-occurrence, lấy tất cả
       sản phẩm (item_b) từng được mua chung với item_id, kèm co_count
       (số lần mua chung).
    3. **Lọc theo danh mục tương tự** (ưu tiên theo thứ bậc):
         - Nếu tồn tại ứng viên cùng category_l3 → giữ lại nhóm đó.
         - Nếu không, thử category_l2 → giữ lại nhóm đó.
         - Nếu vẫn không → giữ nguyên toàn bộ tập co-buy (co_buy_only).
    4. **Xếp hạng**: sắp xếp theo co_count giảm dần.
    5. **Đầu ra**: top-N sản phẩm kèm thông tin chi tiết từ catalog.

Solution 1 là nền tảng cho MỌI sản phẩm. Solution 2 chỉ bổ sung thêm
layer upsale cho riêng danh mục Tã.
"""

import polars as pl
from .data_loader import get_data_store


# ---------------------------------------------------------------------------
# Bước phụ: Lọc ứng viên theo danh mục tương tự
# ---------------------------------------------------------------------------

def _filter_by_similar_category(
    candidates: pl.DataFrame,
    product: dict,
) -> tuple[pl.DataFrame, str]:
    """
    Lọc ứng viên co-buy theo danh mục sản phẩm gốc.

    Ưu tiên:
        1. category_l3 (cụ thể nhất, ví dụ: "Chăm sóc da")
        2. category_l2 (ví dụ: "Chăm sóc mẹ trước & sau sinh")
        3. Giữ nguyên tập co-buy nếu không khớp danh mục nào

    Args:
        candidates: DataFrame chứa ứng viên co-buy, phải có cột
                    ``category_l2`` và ``category_l3``.
        product:    Dict thông tin sản phẩm gốc (chứa category_l2, l3).

    Returns:
        Tuple gồm (DataFrame đã lọc, tên chiến lược: "category_l3" |
        "category_l2" | "co_buy_only").
    """
    # --- Ưu tiên 1: cùng category_l3 ---
    same_l3 = candidates.filter(pl.col("category_l3") == product["category_l3"])
    if same_l3.height > 0:
        return same_l3, "category_l3"

    # --- Ưu tiên 2: cùng category_l2 ---
    same_l2 = candidates.filter(pl.col("category_l2") == product["category_l2"])
    if same_l2.height > 0:
        return same_l2, "category_l2"

    # --- Fallback: giữ nguyên tập co-buy ---
    return candidates, "co_buy_only"


# ---------------------------------------------------------------------------
# Bước chính A: Tạo tập ứng viên Solution 1 (dùng nội bộ & cho Solution 2)
# ---------------------------------------------------------------------------

def get_solution1_candidates(
    item_id: str,
) -> tuple[dict | None, pl.DataFrame | None, str]:
    """
    Trả về tập ứng viên co-buy đã lọc category theo Solution 1.

    Luồng xử lý:
        1. Tra cứu thông tin sản phẩm theo ``item_id``.
        2. Lấy danh sách co-buy từ bảng co-occurrence.
        3. Join metadata danh mục (category_l2, category_l3) cho mỗi ứng viên.
        4. Lọc theo danh mục tương tự (xem ``_filter_by_similar_category``).
        5. Sắp xếp theo ``co_count`` giảm dần.

    Args:
        item_id: Mã sản phẩm đang xem.

    Returns:
        Tuple gồm:
            - product (dict | None): thông tin sản phẩm gốc.
            - filtered (DataFrame | None): tập ứng viên đã lọc & xếp hạng.
            - strategy (str): chuỗi mô tả chiến lược đã dùng.
    """
    store = get_data_store()
    product = store.get_product(item_id)

    # --- Không tìm thấy sản phẩm ---
    if product is None:
        return None, None, "not_found"

    # --- Bước 2: Truy xuất co-buy từ bảng co-occurrence ---
    co_buy = (
        store.cooccurrence
        .filter(pl.col("item_a") == item_id)
        .select(
            pl.col("item_b").alias("item_id"),
            pl.col("co_count"),
        )
    )

    if co_buy.height == 0:
        return product, None, "no_co_buy"

    # --- Bước 3: Join metadata danh mục của từng ứng viên ---
    candidate_meta = store.products.select("item_id", "category_l2", "category_l3")
    candidates = co_buy.join(candidate_meta, on="item_id", how="inner")

    # --- Bước 4: Lọc theo danh mục tương tự ---
    filtered, category_strategy = _filter_by_similar_category(candidates, product)

    # --- Bước 5: Normalize co_count → behavior_score (0–1) ---
    max_count = filtered["co_count"].max()
    if max_count is not None and max_count > 0:
        filtered = filtered.with_columns(
            (pl.col("co_count").cast(pl.Float64) / float(max_count)).alias("behavior_score")
        )
    else:
        filtered = filtered.with_columns(
            pl.lit(0.0).alias("behavior_score")
        )

    # --- Bước 6: Sắp xếp theo behavior_score giảm dần ---
    return (
        product,
        filtered.sort("behavior_score", descending=True),
        f"solution1:co_buy+{category_strategy}",
    )


# ---------------------------------------------------------------------------
# Bước chính B: API endpoint — Trả kết quả Solution 1 cho frontend
# ---------------------------------------------------------------------------

def get_related_products(item_id: str, n: int = 20) -> dict:
    """
    Trả về danh sách sản phẩm liên quan (Related Products) theo Solution 1.

    Đây là endpoint được gọi bởi route ``GET /related/{item_id}``.
    Kết quả bao gồm thông tin đầy đủ của từng sản phẩm (join với catalog).

    Args:
        item_id: Mã sản phẩm đang xem.
        n:       Số lượng sản phẩm tối đa trả về (mặc định 20).

    Returns:
        Dict gồm:
            - ``item_id``: mã sản phẩm gốc.
            - ``related``: danh sách sản phẩm gợi ý (kèm co_count).
            - ``strategy``: chuỗi mô tả chiến lược đã dùng.
    """
    store = get_data_store()
    product, filtered, strategy = get_solution1_candidates(item_id)

    # --- Không có dữ liệu → trả mảng rỗng ---
    if product is None or filtered is None:
        return {"item_id": item_id, "related": [], "strategy": strategy}

    # --- Lấy top-N ứng viên và join đầy đủ thông tin từ catalog ---
    top_related = (
        filtered
        .sort("co_count", descending=True)
        .head(n)
        .select("item_id", "co_count")
    )

    result = (
        top_related
        .join(store.products, on="item_id", how="inner")
        .sort("co_count", descending=True)
    )

    return {
        "item_id": item_id,
        "related": result.to_dicts(),
        "strategy": strategy,
    }
