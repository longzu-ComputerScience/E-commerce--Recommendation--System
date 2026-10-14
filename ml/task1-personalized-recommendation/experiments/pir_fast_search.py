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
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "Additional Doc" / "Personalized Item Recommendation (PIR)"
WORK_DIR = OUT_DIR / "_experiments"

TRANSACTION_PATH = RAW_DIR / "transaction_full_2025.parquet"
EVENT_PATH = RAW_DIR / "event_full_2025.parquet"
ITEM_PATH = RAW_DIR / "items.parquet"
CO_PATH = DATA_DIR / "item_cooccurrence.parquet"
BASE_VAL_TOP_PATH = WORK_DIR / "base_val_top50.pkl"
SUMMARY_PATH = WORK_DIR / "fast_search_summary.json"

TRAIN_START = datetime(2025, 1, 1)
NOV_2025 = datetime(2025, 11, 1)
DEC_2025 = datetime(2025, 12, 1)
JAN_2026 = datetime(2026, 1, 1)
K = 10


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def load_actual() -> dict[int, set[str]]:
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


def recent_global_top(start: datetime, end: datetime, mode: str, n: int = 200) -> list[str]:
    sort_cols = ["users", "qty"] if mode == "users" else ["qty", "users"]
    return (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= start) & (pl.col("updated_date") < end))
        .group_by("item_id")
        .agg(
            pl.col("customer_id").n_unique().alias("users"),
            pl.col("quantity").sum().alias("qty"),
        )
        .sort(sort_cols, descending=[True, True])
        .collect()["item_id"]
        .head(n)
        .to_list()
    )


def trim_map(top_map: dict[int, list[str]], users: set[int], n: int = 50) -> dict[int, list[str]]:
    out = {cid: items[:n] for cid, items in top_map.items() if cid in users}
    top_map.clear()
    gc.collect()
    return out


def evaluate(
    actual: dict[int, set[str]],
    fallback: list[str],
    *,
    base: dict[int, list[str]],
    cand: dict[int, list[str]] | None = None,
    mode: str = "base",
    cand_take: int = 0,
    base_take: int = 10,
) -> dict[str, float | int | str]:
    hits = 0
    hit_users = 0
    for cid, true_items in actual.items():
        out: list[str] = []
        seen: set[str] = set()
        base_items = base.get(cid, [])
        cand_items = [] if cand is None else cand.get(cid, [])
        if mode == "base":
            seq = base_items
        elif mode == "prefix":
            seq = cand_items[:cand_take] + base_items
        elif mode == "after_base":
            seq = base_items[:base_take] + cand_items[:cand_take] + base_items[base_take:]
        elif mode == "replace_tail":
            keep = max(0, K - cand_take)
            seq = base_items[:keep] + cand_items[:cand_take] + base_items[keep:]
        else:
            raise ValueError(mode)
        for item_id in seq:
            if item_id not in seen:
                out.append(item_id)
                seen.add(item_id)
                if len(out) >= K:
                    break
        for item_id in fallback:
            if len(out) >= K:
                break
            if item_id not in seen:
                out.append(item_id)
                seen.add(item_id)
        h = len(set(out[:K]) & true_items)
        hits += h
        hit_users += int(h > 0)
    users = len(actual)
    return {
        "hit_total": int(hits),
        "precision@10": hits / (users * K),
        "hit_user_rate": hit_users / users,
        "users": users,
    }


def list_map_from_scored(scored: pl.DataFrame, top_n: int = 50) -> dict[int, list[str]]:
    top = (
        scored.sort(["customer_id", "score", "tie"], descending=[False, True, True])
        .group_by("customer_id", maintain_order=True)
        .agg(pl.col("item_id").head(top_n).alias("items"))
    )
    out = {int(row["customer_id"]): list(row["items"]) for row in top.iter_rows(named=True)}
    del top, scored
    gc.collect()
    return out


def build_cobuy_candidates(actual_users: list[int], anchors_per_user: int, related_per_item: int) -> dict[int, list[str]]:
    log(f"build cobuy anchors={anchors_per_user}, related={related_per_item}")
    users = pl.DataFrame({"customer_id": actual_users}).with_columns(pl.col("customer_id").cast(pl.Int32)).lazy()
    anchors = (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= TRAIN_START) & (pl.col("updated_date") < DEC_2025))
        .join(users, on="customer_id", how="inner")
        .with_columns(pl.col("updated_date").dt.month().alias("month"))
        .group_by(["customer_id", "item_id"])
        .agg(
            (pl.col("quantity") * (0.70 ** (11 - pl.col("month")))).sum().alias("anchor_score"),
            pl.col("updated_date").max().alias("last_dt"),
        )
        .sort(["customer_id", "anchor_score", "last_dt"], descending=[False, True, True])
        .group_by("customer_id", maintain_order=True)
        .agg(
            pl.col("item_id").head(anchors_per_user).alias("item_a"),
            pl.col("anchor_score").head(anchors_per_user).alias("anchor_score"),
        )
        .explode(["item_a", "anchor_score"])
    )
    co_top = (
        pl.scan_parquet(CO_PATH)
        .sort(["item_a", "co_count"], descending=[False, True])
        .group_by("item_a", maintain_order=True)
        .agg(
            pl.col("item_b").head(related_per_item).alias("item_id"),
            pl.col("co_count").head(related_per_item).alias("co_count"),
        )
        .explode(["item_id", "co_count"])
    )
    scored = (
        anchors.join(co_top, on="item_a", how="inner")
        .group_by(["customer_id", "item_id"])
        .agg(
            (pl.col("anchor_score") * pl.col("co_count").log1p()).sum().alias("score"),
            pl.col("co_count").max().alias("tie"),
        )
        .collect()
    )
    return list_map_from_scored(scored, top_n=50)


def build_key_candidates(
    actual_users: list[int],
    keys: list[str],
    *,
    top_per_key: int,
    max_user_keys: int,
) -> dict[int, list[str]]:
    log(f"build key candidates keys={keys}, top_per_key={top_per_key}, max_user_keys={max_user_keys}")
    users = pl.DataFrame({"customer_id": actual_users}).with_columns(pl.col("customer_id").cast(pl.Int32)).lazy()
    item_meta = pl.scan_parquet(ITEM_PATH).select(["item_id", *keys])
    pop = (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= NOV_2025) & (pl.col("updated_date") < DEC_2025))
        .select("customer_id", "item_id", "quantity")
        .join(item_meta, on="item_id", how="left")
        .drop_nulls(subset=keys)
        .group_by([*keys, "item_id"])
        .agg(
            pl.col("customer_id").n_unique().alias("item_users"),
            pl.col("quantity").sum().alias("item_qty"),
        )
        .sort([*keys, "item_users", "item_qty"], descending=[False] * len(keys) + [True, True])
        .group_by(keys, maintain_order=True)
        .agg(
            pl.col("item_id").head(top_per_key).alias("item_id"),
            pl.col("item_users").head(top_per_key).alias("item_users"),
        )
        .explode(["item_id", "item_users"])
    )
    user_keys = (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= TRAIN_START) & (pl.col("updated_date") < DEC_2025))
        .join(users, on="customer_id", how="inner")
        .with_columns(pl.col("updated_date").dt.month().alias("month"))
        .join(item_meta, on="item_id", how="left")
        .drop_nulls(subset=keys)
        .group_by(["customer_id", *keys])
        .agg(
            (pl.col("quantity") * (0.70 ** (11 - pl.col("month")))).sum().alias("key_score"),
            pl.col("updated_date").max().alias("last_dt"),
        )
        .sort(["customer_id", "key_score", "last_dt"], descending=[False, True, True])
        .group_by("customer_id", maintain_order=True)
        .agg(
            [pl.col(k).head(max_user_keys).alias(k) for k in keys]
            + [pl.col("key_score").head(max_user_keys).alias("key_score")]
        )
        .explode([*keys, "key_score"])
    )
    scored = (
        user_keys.join(pop, on=keys, how="inner")
        .group_by(["customer_id", "item_id"])
        .agg(
            (pl.col("key_score").log1p() * pl.col("item_users").log1p()).max().alias("score"),
            pl.col("item_users").max().alias("tie"),
        )
        .collect()
    )
    return list_map_from_scored(scored, top_n=50)


def search_one(name: str, cand: dict[int, list[str]], actual: dict[int, set[str]], base: dict[int, list[str]], fallback: list[str]) -> list[dict]:
    rows: list[dict] = []
    direct_base = {cid: cand.get(cid, []) for cid in actual.keys()}
    direct = evaluate(actual, fallback, base=direct_base, mode="base")
    rows.append({"name": name, "mode": "direct", "cand_take": 10, "base_take": 0, **direct})
    for mode in ["replace_tail", "prefix", "after_base"]:
        for cand_take in range(1, 8):
            base_takes = [1, 2, 3, 5, 7, 9] if mode == "after_base" else [10]
            for base_take in base_takes:
                metrics = evaluate(
                    actual,
                    fallback,
                    base=base,
                    cand=cand,
                    mode=mode,
                    cand_take=cand_take,
                    base_take=base_take,
                )
                rows.append({"name": name, "mode": mode, "cand_take": cand_take, "base_take": base_take, **metrics})
    return rows


def main() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    actual = load_actual()
    actual_users = list(actual.keys())
    actual_user_set = set(actual_users)
    fallback_qty = recent_global_top(NOV_2025, DEC_2025, "qty")
    fallback_users = recent_global_top(NOV_2025, DEC_2025, "users")

    log("load base top50 cache")
    with BASE_VAL_TOP_PATH.open("rb") as f:
        base_all = pickle.load(f)
    base = trim_map(base_all, actual_user_set, n=50)
    log(f"base users after trim={len(base):,}; actual={len(actual):,}")

    results: list[dict] = []
    for fb_name, fallback in [("qty", fallback_qty), ("users", fallback_users)]:
        row = {"name": "base", "fallback": fb_name, "mode": "base", **evaluate(actual, fallback, base=base, mode="base")}
        results.append(row)
        log(str(row))

    candidates = [
        ("cobuy_a3_r20", lambda: build_cobuy_candidates(actual_users, 3, 20)),
        ("cobuy_a5_r20", lambda: build_cobuy_candidates(actual_users, 5, 20)),
        ("cat_l2", lambda: build_key_candidates(actual_users, ["category_l2"], top_per_key=30, max_user_keys=5)),
        ("brand", lambda: build_key_candidates(actual_users, ["brand"], top_per_key=30, max_user_keys=5)),
        ("cat_l3", lambda: build_key_candidates(actual_users, ["category_l3"], top_per_key=25, max_user_keys=5)),
        ("cat_l2_brand", lambda: build_key_candidates(actual_users, ["category_l2", "brand"], top_per_key=20, max_user_keys=5)),
    ]
    for cand_name, builder in candidates:
        cand = builder()
        log(f"{cand_name}: candidate users={len(cand):,}")
        for fb_name, fallback in [("users", fallback_users), ("qty", fallback_qty)]:
            rows = search_one(f"{cand_name}_fb_{fb_name}", cand, actual, base, fallback)
            results.extend(rows)
        results = sorted(results, key=lambda r: (float(r["precision@10"]), int(r["hit_total"])), reverse=True)
        log(f"best after {cand_name}: {results[0]}")
        SUMMARY_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        del cand
        gc.collect()

    log(f"saved {SUMMARY_PATH}")


if __name__ == "__main__":
    main()