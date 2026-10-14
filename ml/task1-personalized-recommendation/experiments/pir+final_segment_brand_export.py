from __future__ import annotations

import gc
import json
import pickle
import time
from datetime import datetime
from pathlib import Path

import polars as pl


ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "raw_data"
OUT_DIR = ROOT / "Additional Doc" / "Personalized Item Recommendation (PIR)"
TRANSACTION_PATH = RAW_DIR / "transaction_full_2025.parquet"
ITEM_PATH = RAW_DIR / "items.parquet"

BASE_SUBMISSION_PATH = OUT_DIR / "submission_all_items_repeat_features.pkl"
OUTPUT_PATH = OUT_DIR / "submission.pkl"
SUMMARY_PATH = OUT_DIR / "pir_final_segment_brand_summary.json"

TRAIN_START = datetime(2025, 1, 1)
DEC_2025 = datetime(2025, 12, 1)
JAN_2026 = datetime(2026, 1, 1)
K = 10
SEGMENT_WIDTH = 500_000


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def global_top(mode: str, n: int = 200) -> list[str]:
    sort_cols = ["users", "qty"] if mode == "users" else ["qty", "users"]
    return (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= DEC_2025) & (pl.col("updated_date") < JAN_2026))
        .group_by("item_id")
        .agg(pl.col("customer_id").n_unique().alias("users"), pl.col("quantity").sum().alias("qty"))
        .sort(sort_cols, descending=[True, True])
        .collect()["item_id"]
        .head(n)
        .to_list()
    )


def segment_fallbacks() -> dict[int, list[str]]:
    df = (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= DEC_2025) & (pl.col("updated_date") < JAN_2026))
        .with_columns((pl.col("customer_id") // SEGMENT_WIDTH).alias("segment"))
        .group_by(["segment", "item_id"])
        .agg(pl.col("customer_id").n_unique().alias("users"), pl.col("quantity").sum().alias("qty"))
        .sort(["segment", "users", "qty"], descending=[False, True, True])
        .group_by("segment", maintain_order=True)
        .agg(pl.col("item_id").head(20).alias("items"))
        .collect()
    )
    return {int(row["segment"]): list(row["items"]) for row in df.iter_rows(named=True)}


def build_brand_top1() -> dict[int, list[str]]:
    log("build final brand top1 candidates")
    meta = pl.scan_parquet(ITEM_PATH).select(["item_id", "brand"])
    pop = (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= DEC_2025) & (pl.col("updated_date") < JAN_2026))
        .join(meta, on="item_id", how="left")
        .drop_nulls("brand")
        .group_by(["brand", "item_id"])
        .agg(pl.col("customer_id").n_unique().alias("item_users"), pl.col("quantity").sum().alias("item_qty"))
        .sort(["brand", "item_users", "item_qty"], descending=[False, True, True])
        .group_by("brand", maintain_order=True)
        .agg(pl.col("item_id").head(30).alias("item_id"), pl.col("item_users").head(30).alias("item_users"))
        .explode(["item_id", "item_users"])
    )
    user_keys = (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= TRAIN_START) & (pl.col("updated_date") < JAN_2026))
        .with_columns(pl.col("updated_date").dt.month().alias("month"))
        .join(meta, on="item_id", how="left")
        .drop_nulls("brand")
        .group_by(["customer_id", "brand"])
        .agg(
            (pl.col("quantity") * (0.70 ** (12 - pl.col("month")))).sum().alias("key_score"),
            pl.col("updated_date").max().alias("last_dt"),
        )
        .sort(["customer_id", "key_score", "last_dt"], descending=[False, True, True])
        .group_by("customer_id", maintain_order=True)
        .agg(pl.col("brand").head(5).alias("brand"), pl.col("key_score").head(5).alias("key_score"))
        .explode(["brand", "key_score"])
    )
    scored = (
        user_keys.join(pop, on="brand", how="inner")
        .group_by(["customer_id", "item_id"])
        .agg(
            (pl.col("key_score").log1p() * pl.col("item_users").log1p()).max().alias("score"),
            pl.col("item_users").max().alias("tie"),
        )
        .collect()
    )
    top = (
        scored.sort(["customer_id", "score", "tie"], descending=[False, True, True])
        .group_by("customer_id", maintain_order=True)
        .agg(pl.col("item_id").head(1).alias("items"))
    )
    out = {int(row["customer_id"]): list(row["items"]) for row in top.iter_rows(named=True)}
    del scored, top
    gc.collect()
    log(f"brand candidate users={len(out):,}")
    return out


def fill_unique(seq: list[str], fallback: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in seq:
        if item not in seen:
            out.append(item)
            seen.add(item)
            if len(out) >= K:
                return out
    for item in fallback:
        if item not in seen:
            out.append(item)
            seen.add(item)
            if len(out) >= K:
                return out
    return out[:K]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    old_fallback_qty = global_top("qty", n=20)[:K]
    fallback_users = global_top("users", n=200)
    segment_fb = segment_fallbacks()
    brand_top1 = build_brand_top1()

    log(f"load base submission: {BASE_SUBMISSION_PATH}")
    with BASE_SUBMISSION_PATH.open("rb") as f:
        submission: dict[int, list[str]] = pickle.load(f)

    old_fallback_tuple = tuple(old_fallback_qty)
    changed_cold = 0
    changed_brand = 0
    segment_replacement_cache: dict[int, list[str]] = {}
    for cid, recs in submission.items():
        segment_id = int(cid) // SEGMENT_WIDTH
        fallback = segment_fb.get(segment_id, fallback_users)
        if tuple(recs[:K]) == old_fallback_tuple:
            new_recs = segment_replacement_cache.get(segment_id)
            if new_recs is None:
                new_recs = fill_unique([], fallback)
                segment_replacement_cache[segment_id] = new_recs
            if new_recs != recs:
                submission[cid] = new_recs
                changed_cold += 1
            continue

        brand_items = brand_top1.get(int(cid), [])
        if brand_items:
            new_recs = fill_unique(recs[:9] + brand_items + recs[9:], fallback)
            if new_recs != recs:
                submission[cid] = new_recs
                changed_brand += 1

    log(f"changed cold/fallback rows={changed_cold:,}; brand-tail rows={changed_brand:,}")
    del segment_fb, brand_top1, segment_replacement_cache
    gc.collect()

    tmp_output = OUTPUT_PATH.with_suffix(".pkl.tmp")
    with tmp_output.open("wb") as f:
        pickle.dump(submission, f, protocol=pickle.HIGHEST_PROTOCOL)
    tmp_output.replace(OUTPUT_PATH)

    summary = {
        "method": "segment_fallback_width_500000_plus_brand_replace_tail1",
        "base_submission": str(BASE_SUBMISSION_PATH),
        "output": str(OUTPUT_PATH),
        "customers": len(submission),
        "changed_cold_or_fallback_rows": changed_cold,
        "changed_brand_tail_rows": changed_brand,
        "validation_reference": {
            "old_repeat_feature_precision@10": 0.08574194804382136,
            "base_lgbm_with_users_fallback_precision@10": 0.08677293680573099,
            "segment_brand_tail1_precision@10": 0.08776417855793676,
        },
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"saved {OUTPUT_PATH} size_mb={OUTPUT_PATH.stat().st_size / (1024 ** 2):.2f}")
    log(f"saved summary {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
