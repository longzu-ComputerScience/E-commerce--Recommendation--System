"""
Solution 2 — Upsale tã (bỉm) dựa trên size kết hợp Co-buy
============================================================

Thuật toán:
    1. **Đầu vào**: item_id của sản phẩm đang xem.
    2. **Lấy tập ứng viên nền từ Solution 1** (co-buy + lọc category).
    3. **Kiểm tra điều kiện áp dụng**:
         - Nếu sản phẩm KHÔNG thuộc danh mục "Tã" → trả nguyên Solution 1.
         - Nếu sản phẩm không có normalized_size → trả nguyên Solution 1.
    4. **Chấm điểm upsale cho sản phẩm tã** (chỉ áp dụng khi là Tã):
         a. Lọc ứng viên: chỉ giữ ứng viên thuộc danh mục Tã,
            có normalized_size.
         b. Tính upsale_score dựa trên chênh lệch size:
            - Cùng size → 1.0
            - Lớn hơn → giảm nhẹ: max(0.5, 1 - diff * 0.1)
            - Nhỏ hơn → phạt mạnh: max(0.1, 1 - abs(diff) * 0.3)
            - Không xác định → 0.5
         c. final_score = behavior_score × upsale_score.
    5. **Xếp hạng**: sắp xếp theo final_score giảm dần, rồi co_count
       giảm dần (tie-breaker).
    6. **Fallback**: nếu sau lọc không còn ứng viên tã hợp lệ → trả
       nguyên kết quả Solution 1.

Quy tắc kinh doanh:
    - Mọi sản phẩm đều đi qua Solution 1 trước.
    - Chỉ sản phẩm thuộc category_l1 == "Tã" mới có thêm Solution 2.
    - Sản phẩm không phải Tã → KHÔNG gọi Solution 2, chỉ dùng Solution 1.
"""

import polars as pl
from .data_loader import get_data_store
from . import Solution1

# Hằng số danh mục Tã (category_l1)
DIAPER_CATEGORY = "T\u00e3"

# Thứ tự size chuẩn từ nhỏ → lớn
SIZE_ORDER = ["NB", "S", "M", "L", "XL", "XXL", "XXXL"]


# ---------------------------------------------------------------------------
# Bước phụ: Tính upsale_score theo chênh lệch size
# ---------------------------------------------------------------------------

def _get_upsale_score(base_size: str, target_size: str) -> float:
    """
    Tính điểm upsale dựa trên chênh lệch size.

    Quy tắc:
        - Cùng size (diff=0) → 1.0
        - Target lớn hơn (diff>0) → giảm nhẹ: max(0.5, 1 - diff * 0.1)
        - Target nhỏ hơn (diff<0) → phạt mạnh: max(0.1, 1 - abs(diff) * 0.3)
        - Size không xác định → 0.5

    Args:
        base_size:   Size của sản phẩm đang xem (normalized_size).
        target_size: Size của ứng viên (normalized_size).

    Returns:
        Điểm upsale (float từ 0.1 đến 1.0).
    """
    if base_size not in SIZE_ORDER or target_size not in SIZE_ORDER:
        return 0.5

    base_idx = SIZE_ORDER.index(base_size)
    target_idx = SIZE_ORDER.index(target_size)
    diff = target_idx - base_idx

    if diff == 0:
        return 1.0
    elif diff > 0:
        # Lớn hơn → giảm nhẹ
        return max(0.5, 1 - diff * 0.1)
    else:
        # Nhỏ hơn → phạt mạnh
        return max(0.1, 1 - abs(diff) * 0.3)


# ---------------------------------------------------------------------------
# Bước phụ: Tạo response fallback từ kết quả Solution 1
# ---------------------------------------------------------------------------

def _build_solution1_fallback_response(
    item_id: str,
    candidates: pl.DataFrame | None,
    strategy: str,
    n: int,
    reason: str | None = None,
) -> dict:
    """
    Xây dựng response recommendation từ tập ứng viên Solution 1.

    Hàm này được dùng khi KHÔNG thể áp dụng logic upsale của Solution 2
    (ví dụ: sản phẩm không phải Tã, không có normalized_size, hoặc không tìm
    được ứng viên tã phù hợp).

    Args:
        item_id:    Mã sản phẩm gốc.
        candidates: Tập ứng viên từ Solution 1 (có thể None).
        strategy:   Chiến lược gốc từ Solution 1.
        n:          Số lượng sản phẩm tối đa.
        reason:     Lý do fallback (dùng để ghi vào strategy string).

    Returns:
        Dict response chuẩn cho API endpoint.
    """
    # --- Xây dựng chuỗi strategy mô tả lý do dùng Solution 1 ---
    final_strategy = (
        f"solution1_only:{strategy}"
        if reason is None
        else f"solution1_only:{reason}+{strategy}"
    )

    # --- Không có ứng viên → trả mảng rỗng ---
    if candidates is None or candidates.height == 0:
        return {
            "item_id": item_id,
            "recommendations": [],
            "strategy": final_strategy,
        }

    # --- Lấy top-N và join đầy đủ thông tin từ catalog ---
    store = get_data_store()

    # Chọn các cột cần thiết (bao gồm behavior_score nếu có)
    select_cols = ["item_id", "co_count"]
    if "behavior_score" in candidates.columns:
        select_cols.append("behavior_score")

    top_recommendations = candidates.head(n).select(select_cols)

    result = (
        top_recommendations
        .join(store.products, on="item_id", how="inner")
        .sort("co_count", descending=True)
    )

    return {
        "item_id": item_id,
        "recommendations": result.to_dicts(),
        "strategy": final_strategy,
    }


# ---------------------------------------------------------------------------
# Bước phụ: Chấm điểm upsale theo size cho ứng viên tã
# ---------------------------------------------------------------------------

def _score_diaper_upsale_candidates(
    base_candidates: pl.DataFrame,
    base_size: str,
    store: object,
) -> pl.DataFrame:
    """
    Chấm điểm upsale cho các ứng viên tã dựa trên chênh lệch size.

    Logic chấm điểm (theo notebook):
        1. Lọc: chỉ giữ ứng viên thuộc danh mục Tã, có normalized_size.
        2. Tính upsale_score dựa trên get_score():
           → cùng size → 1.0
           → lớn hơn → max(0.5, 1 - diff * 0.1)
           → nhỏ hơn → max(0.1, 1 - abs(diff) * 0.3)
        3. final_score = behavior_score × upsale_score

    Args:
        base_candidates:   Tập ứng viên từ Solution 1 (có behavior_score).
        base_size:         normalized_size của sản phẩm đang xem.
        store:             DataStore singleton.

    Returns:
        DataFrame ứng viên đã chấm điểm (có thể rỗng).
    """
    # --- Chọn cột cần thiết từ base_candidates ---
    select_cols = ["item_id", "co_count"]
    if "behavior_score" in base_candidates.columns:
        select_cols.append("behavior_score")

    # --- Join metadata size và category_l1 cho từng ứng viên ---
    candidates = (
        base_candidates
        .select(select_cols)
        .join(
            store.products.select("item_id", "category_l1", "normalized_size"),
            on="item_id",
            how="inner",
        )
    )

    # --- Lọc: chỉ giữ ứng viên thuộc danh mục Tã, có normalized_size ---
    filtered = (
        candidates
        .filter(pl.col("category_l1") == DIAPER_CATEGORY)
        .filter(pl.col("normalized_size").is_not_null())
        .filter(pl.col("normalized_size") != "")
    )

    if filtered.height == 0:
        return filtered

    # --- Tính upsale_score bằng map_elements ---
    scored = filtered.with_columns(
        pl.col("normalized_size")
        .map_elements(
            lambda target_size: _get_upsale_score(base_size, target_size),
            return_dtype=pl.Float64,
        )
        .alias("upsale_score")
    )

    # --- Đảm bảo có behavior_score ---
    if "behavior_score" not in scored.columns:
        max_count = scored["co_count"].max()
        if max_count is not None and max_count > 0:
            scored = scored.with_columns(
                (pl.col("co_count").cast(pl.Float64) / float(max_count)).alias("behavior_score")
            )
        else:
            scored = scored.with_columns(pl.lit(0.0).alias("behavior_score"))

    # --- Tính final_score = behavior_score × upsale_score ---
    scored = scored.with_columns(
        (pl.col("behavior_score") * pl.col("upsale_score")).alias("final_score")
    )

    return scored


# ---------------------------------------------------------------------------
# Bước chính: API endpoint — Trả kết quả Solution 2 cho frontend
# ---------------------------------------------------------------------------

def get_recommendations(item_id: str, n: int = 20) -> dict:
    """
    Trả về danh sách recommendation theo Solution 2.

    Đây là endpoint được gọi bởi route ``GET /recommendations/{item_id}``.

    Luồng xử lý:
        1. Gọi Solution 1 để lấy tập ứng viên nền.
        2. Nếu sản phẩm không phải Tã → trả nguyên Solution 1 (fallback).
        3. Nếu là Tã nhưng không có normalized_size → trả nguyên Solution 1.
        4. Nếu là Tã và có normalized_size → chấm điểm upsale, xếp hạng.
        5. Nếu sau chấm điểm không còn ứng viên → fallback Solution 1.

    Args:
        item_id: Mã sản phẩm đang xem.
        n:       Số lượng sản phẩm tối đa trả về (mặc định 20).

    Returns:
        Dict gồm:
            - ``item_id``: mã sản phẩm gốc.
            - ``recommendations``: danh sách sản phẩm gợi ý
              (kèm co_count, upsale_score, behavior_score, final_score).
            - ``strategy``: chuỗi mô tả chiến lược đã dùng.
    """
    store = get_data_store()

    # --- Bước 1: Lấy tập ứng viên nền từ Solution 1 ---
    product, base_candidates, base_strategy = (
        Solution1.get_solution1_candidates(item_id)
    )

    # --- Không tìm thấy sản phẩm ---
    if product is None:
        return {"item_id": item_id, "recommendations": [], "strategy": "not_found"}

    # --- Không có dữ liệu co-buy ---
    if base_candidates is None:
        return {"item_id": item_id, "recommendations": [], "strategy": base_strategy}

    # --- Bước 2: Kiểm tra — không phải Tã → fallback Solution 1 ---
    if product.get("category_l1") != DIAPER_CATEGORY:
        return _build_solution1_fallback_response(
            item_id, base_candidates, base_strategy, n
        )

    # --- Bước 3: Là Tã nhưng không có normalized_size → fallback ---
    base_size = product.get("normalized_size")
    if not base_size:
        return _build_solution1_fallback_response(
            item_id,
            base_candidates,
            base_strategy,
            n,
            reason="size_unknown",
        )

    # --- Bước 4: Chấm điểm upsale cho ứng viên tã ---
    scored = _score_diaper_upsale_candidates(
        base_candidates, base_size, store
    )

    # --- Bước 5: Fallback nếu không còn ứng viên sau lọc ---
    if scored.height == 0:
        return _build_solution1_fallback_response(
            item_id,
            base_candidates,
            base_strategy,
            n,
            reason="no_diaper_candidate",
        )

    # --- Bước 6: Xếp hạng final_score giảm dần, co_count tie-breaker ---
    top_recommendations = (
        scored
        .sort(
            by=["final_score", "co_count"],
            descending=[True, True],
        )
        .head(n)
        .select("item_id", "co_count", "behavior_score", "upsale_score", "final_score")
    )

    # --- Join đầy đủ thông tin catalog ---
    result = (
        top_recommendations
        .join(store.products, on="item_id", how="inner")
        .sort(by=["final_score", "co_count"], descending=[True, True])
    )

    return {
        "item_id": item_id,
        "recommendations": result.to_dicts(),
        "strategy": f"solution2:upsale_on_top_of:{base_strategy}",
    }
