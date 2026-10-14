"""
Solution 3 — Dự báo sản lượng bằng LightGBM
=============================================

Thuật toán (tái hiện từ prediction_problem.ipynb):
    1. Đọc dữ liệu giao dịch thô (transactions-2025-12.parquet).
    2. Tạo cột ``date`` từ ``updated_date``.
    3. Gom nhóm theo ngày → daily sales: (date, location, item_id, qty, avg_price).
    4. Tạo feature: dow, day, is_weekend.
    5. Chia train (trước 22/12) / test (từ 22/12).
    6. Huấn luyện LGBMRegressor (objective=regression_l1, n_estimators=1000).
    7. Dự đoán daily qty trên test, gom nhóm về tổng theo (location, item_id).
    8. Tính MAE so với actual.
    9. Trả kết quả JSON cho API.

Kết quả được cache lại (singleton) vì quá trình train tốn thời gian.
"""

from __future__ import annotations

import polars as pl
from datetime import date
from pathlib import Path

RAW_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "raw_data"


def _run_forecast() -> dict:
    """Chạy toàn bộ pipeline forecast và trả về dict kết quả."""
    import lightgbm as lgb

    # ── 1. Đọc dữ liệu giao dịch ──
    txn_path = RAW_DATA_DIR / "transactions-2025-12.parquet"
    transactions = pl.read_parquet(txn_path).with_columns(
        pl.col("price").cast(pl.Float64),
    )

    # ── 2. Tạo cột date từ updated_date ──
    transactions = transactions.with_columns(
        pl.col("updated_date").dt.date().alias("date"),
    )

    # ── 3. Gom nhóm theo ngày → daily sales ──
    daily_sales = (
        transactions
        .group_by(["date", "location", "item_id"])
        .agg(
            pl.col("quantity").sum().alias("qty"),
            pl.col("price").mean().alias("avg_price"),
        )
    )

    # ── 4. Tạo features ──
    full_df = daily_sales.with_columns(
        pl.col("date").dt.weekday().alias("dow"),
        pl.col("date").dt.day().alias("day"),
        (pl.col("date").dt.weekday() > 5).cast(pl.Int32).alias("is_weekend"),
    )

    # ── 5. Chia train / test ──
    split_date = date(2025, 12, 22)
    train_data = full_df.filter(pl.col("date") < split_date)
    test_data = full_df.filter(pl.col("date") >= split_date)

    # ── 6. Chuẩn bị dữ liệu cho LightGBM ──
    features = ["location", "item_id", "avg_price", "dow", "day", "is_weekend"]
    target = "qty"
    cat_features = ["location", "item_id"]

    X_train = train_data.select(features).to_pandas()
    y_train = train_data.select(target).to_pandas().squeeze()
    X_test = test_data.select(features).to_pandas()
    y_test = test_data.select(target).to_pandas().squeeze()

    for col in cat_features:
        X_train[col] = X_train[col].astype("category")
        X_test[col] = X_test[col].astype("category")

    # ── 7. Huấn luyện mô hình ──
    model = lgb.LGBMRegressor(
        objective="regression_l1",
        n_estimators=1000,
        learning_rate=0.05,
        num_leaves=31,
        random_state=42,
        verbosity=-1,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        eval_metric="mae",
        callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)],
    )

    # ── 8. Dự đoán & gom nhóm ──
    test_data = test_data.with_columns(
        pl.Series(name="pred_qty", values=model.predict(X_test)),
    )

    final_prediction = (
        test_data.group_by(["location", "item_id"])
        .agg(
            pl.col("pred_qty").sum().round(0).cast(pl.Int32).alias("quantity_predict"),
            pl.col("avg_price").mean().round(0).alias("avg_price"),
        )
    )

    actual_totals = (
        test_data.group_by(["location", "item_id"])
        .agg(pl.col("qty").sum().alias("actual_quantity"))
    )

    comparison = final_prediction.join(actual_totals, on=["location", "item_id"])
    mae_score = float(
        (comparison["quantity_predict"] - comparison["actual_quantity"]).abs().mean()
    )

    # ── 9. Xây dựng kết quả ──
    result_df = (
        comparison
        .select(
            "location", "item_id",
            "quantity_predict", "actual_quantity", "avg_price",
        )
        .sort("quantity_predict", descending=True)
    )

    return {
        "strategy": "solution3:lightgbm_daily_forecast",
        "mae": round(mae_score, 4),
        "total_predictions": result_df.height,
        "predictions": result_df.to_dicts(),
    }


# ── Singleton cache ──
_forecast_result: dict | None = None


def get_forecast() -> dict:
    """Trả về kết quả forecast (cache sau lần chạy đầu tiên)."""
    global _forecast_result
    if _forecast_result is None:
        print("Solution3: Đang chạy LightGBM forecast (lần đầu, có thể mất vài phút)...")
        _forecast_result = _run_forecast()
        print(f"Solution3: Hoàn tất. MAE = {_forecast_result['mae']}")
    return _forecast_result
