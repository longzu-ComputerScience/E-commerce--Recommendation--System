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
WORK_DIR = OUT_DIR / "_experiments"
TRANSACTION_PATH = RAW_DIR / "transaction_full_2025.parquet"
ITEM_PATH = RAW_DIR / "items.parquet"
BASE_VAL_TOP_PATH = WORK_DIR / "base_val_top50.pkl"
SUMMARY_PATH = WORK_DIR / "diversity_search_summary.json"

NOV_2025 = datetime(2025, 11, 1)
DEC_2025 = datetime(2025, 12, 1)
JAN_2026 = datetime(2026, 1, 1)
K = 10


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def actual_sets() -> dict[int, set[str]]:
    df = (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= DEC_2025) & (pl.col("updated_date") < JAN_2026))
        .select("customer_id", "item_id")
        .unique()
        .group_by("customer_id")
        .agg(pl.col("item_id").alias("items"))
        .collect()
    )
    return {int(row["customer_id"]): set(row["items"]) for row in df.iter_rows(named=True)}


def fallback_users() -> list[str]:
    return (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= NOV_2025) & (pl.col("updated_date") < DEC_2025))
        .group_by("item_id")
        .agg(pl.col("customer_id").n_unique().alias("users"), pl.col("quantity").sum().alias("qty"))
        .sort(["users", "qty"], descending=[True, True])
        .collect()["item_id"]
        .head(200)
        .to_list()
    )


def select_diverse(items: list[str], meta: dict[str, tuple], caps: dict[str, int], first_keep: int) -> list[str]:
    out = []
    seen = set()
    counts = {key: {} for key in caps}
    for item in items[:first_keep]:
        if item not in seen:
            out.append(item)
            seen.add(item)
            m = meta.get(item, ())
            for idx, key in enumerate(caps):
                val = m[idx] if idx < len(m) else None
                counts[key][val] = counts[key].get(val, 0) + 1
            if len(out) >= K:
                return out
    for item in items:
        if item in seen:
            continue
        m = meta.get(item, ())
        ok = True
        for idx, key in enumerate(caps):
            val = m[idx] if idx < len(m) else None
            if counts[key].get(val, 0) >= caps[key]:
                ok = False
                break
        if not ok:
            continue
        out.append(item)
        seen.add(item)
        for idx, key in enumerate(caps):
            val = m[idx] if idx < len(m) else None
            counts[key][val] = counts[key].get(val, 0) + 1
        if len(out) >= K:
            return out
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
            if len(out) >= K:
                break
    return out


def main() -> None:
    actual = actual_sets()
    users = set(actual)
    fb = fallback_users()
    item_df = pl.read_parquet(ITEM_PATH, columns=["item_id", "category_l1", "category_l2", "category_l3", "brand"])
    meta_cols = ["category_l1", "category_l2", "category_l3", "brand"]
    meta = {row[0]: tuple(row[1:]) for row in item_df.select(["item_id", *meta_cols]).iter_rows()}
    log("load base")
    with BASE_VAL_TOP_PATH.open("rb") as f:
        base_all = pickle.load(f)
    base = {cid: vals[:50] for cid, vals in base_all.items() if cid in users}
    base_all.clear()
    gc.collect()
    configs = [{"name": "base", "caps": {}, "first_keep": K}]
    for first_keep in [0, 1, 2, 3, 5, 7]:
        for cap1 in [1, 2, 3, 4]:
            configs.append({"name": f"cap_l1_{cap1}_keep{first_keep}", "caps": {"category_l1": cap1}, "first_keep": first_keep})
        for cap2 in [1, 2, 3]:
            configs.append({"name": f"cap_l2_{cap2}_keep{first_keep}", "caps": {"category_l2": cap2}, "first_keep": first_keep})
        for capb in [1, 2, 3]:
            configs.append({"name": f"cap_brand_{capb}_keep{first_keep}", "caps": {"brand": capb}, "first_keep": first_keep})
        configs.append({"name": f"cap_l1_2_brand2_keep{first_keep}", "caps": {"category_l1": 2, "brand": 2}, "first_keep": first_keep})
        configs.append({"name": f"cap_l2_2_brand2_keep{first_keep}", "caps": {"category_l2": 2, "brand": 2}, "first_keep": first_keep})

    hits = [0 for _ in configs]
    hit_users = [0 for _ in configs]
    for cid, true_items in actual.items():
        base_items = base.get(cid, [])
        for i, cfg in enumerate(configs):
            if cfg["name"] == "base":
                out = list(base_items[:K])
            else:
                out = select_diverse(base_items, meta, cfg["caps"], cfg["first_keep"])
            seen = set(out)
            for item in fb:
                if len(out) >= K:
                    break
                if item not in seen:
                    out.append(item)
                    seen.add(item)
            h = len(set(out[:K]) & true_items)
            hits[i] += h
            hit_users[i] += int(h > 0)
    rows = []
    for cfg, h, hu in zip(configs, hits, hit_users):
        rows.append({
            "name": cfg["name"],
            "hit_total": int(h),
            "precision@10": h / (len(actual) * K),
            "hit_user_rate": hu / len(actual),
            "users": len(actual),
        })
    rows.sort(key=lambda r: (r["precision@10"], r["hit_total"]), reverse=True)
    SUMMARY_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"best: {rows[0]}")
    log(f"saved {SUMMARY_PATH}")


if __name__ == "__main__":
    main()