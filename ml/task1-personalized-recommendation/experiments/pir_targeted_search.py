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
ITEM_PATH = RAW_DIR / "items.parquet"
CO_PATH = DATA_DIR / "item_cooccurrence.parquet"
BASE_VAL_TOP_PATH = WORK_DIR / "base_val_top50.pkl"
SUMMARY_PATH = WORK_DIR / "targeted_search_summary.json"

TRAIN_START = datetime(2025, 1, 1)
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


def recent_global_top(mode: str, n: int = 200) -> list[str]:
    sort_cols = ["users", "qty"] if mode == "users" else ["qty", "users"]
    return (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= NOV_2025) & (pl.col("updated_date") < DEC_2025))
        .group_by("item_id")
        .agg(pl.col("customer_id").n_unique().alias("users"), pl.col("quantity").sum().alias("qty"))
        .sort(sort_cols, descending=[True, True])
        .collect()["item_id"]
        .head(n)
        .to_list()
    )


def trim_base(base_all: dict[int, list[str]], users: set[int]) -> dict[int, list[str]]:
    base = {cid: vals[:50] for cid, vals in base_all.items() if cid in users}
    base_all.clear()
    gc.collect()
    return base


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


def build_cobuy(actual_users: list[int], anchors_per_user: int, related_per_item: int) -> dict[int, list[str]]:
    log(f"build cobuy anchors={anchors_per_user} related={related_per_item}")
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
    return list_map_from_scored(scored)


def build_key(actual_users: list[int], keys: list[str], top_per_key: int, max_user_keys: int) -> dict[int, list[str]]:
    log(f"build key={'+'.join(keys)} top_per_key={top_per_key} max_user_keys={max_user_keys}")
    users = pl.DataFrame({"customer_id": actual_users}).with_columns(pl.col("customer_id").cast(pl.Int32)).lazy()
    meta = pl.scan_parquet(ITEM_PATH).select(["item_id", *keys])
    pop = (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= NOV_2025) & (pl.col("updated_date") < DEC_2025))
        .join(meta, on="item_id", how="left")
        .drop_nulls(subset=keys)
        .group_by([*keys, "item_id"])
        .agg(pl.col("customer_id").n_unique().alias("item_users"), pl.col("quantity").sum().alias("item_qty"))
        .sort([*keys, "item_users", "item_qty"], descending=[False] * len(keys) + [True, True])
        .group_by(keys, maintain_order=True)
        .agg(pl.col("item_id").head(top_per_key).alias("item_id"), pl.col("item_users").head(top_per_key).alias("item_users"))
        .explode(["item_id", "item_users"])
    )
    user_keys = (
        pl.scan_parquet(TRANSACTION_PATH)
        .filter((pl.col("updated_date") >= TRAIN_START) & (pl.col("updated_date") < DEC_2025))
        .join(users, on="customer_id", how="inner")
        .with_columns(pl.col("updated_date").dt.month().alias("month"))
        .join(meta, on="item_id", how="left")
        .drop_nulls(subset=keys)
        .group_by(["customer_id", *keys])
        .agg(
            (pl.col("quantity") * (0.70 ** (11 - pl.col("month")))).sum().alias("key_score"),
            pl.col("updated_date").max().alias("last_dt"),
        )
        .sort(["customer_id", "key_score", "last_dt"], descending=[False, True, True])
        .group_by("customer_id", maintain_order=True)
        .agg([pl.col(k).head(max_user_keys).alias(k) for k in keys] + [pl.col("key_score").head(max_user_keys).alias("key_score")])
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
    return list_map_from_scored(scored)


def sequence(base_items: list[str], cand_items: list[str], mode: str, cand_take: int, base_take: int) -> list[str]:
    if mode == "base":
        return base_items
    if mode == "prefix":
        return cand_items[:cand_take] + base_items
    if mode == "replace_tail":
        keep = max(0, K - cand_take)
        return base_items[:keep] + cand_items[:cand_take] + base_items[keep:]
    if mode == "after_base":
        return base_items[:base_take] + cand_items[:cand_take] + base_items[base_take:]
    raise ValueError(mode)


def eval_configs(
    actual: dict[int, set[str]],
    base: dict[int, list[str]],
    cand: dict[int, list[str]] | None,
    fallback: list[str],
    configs: list[dict],
) -> list[dict]:
    hits = [0 for _ in configs]
    hit_users = [0 for _ in configs]
    for cid, true_items in actual.items():
        base_items = base.get(cid, [])
        cand_items = [] if cand is None else cand.get(cid, [])
        for i, cfg in enumerate(configs):
            out: list[str] = []
            seen: set[str] = set()
            for item_id in sequence(base_items, cand_items, cfg["mode"], cfg.get("cand_take", 0), cfg.get("base_take", K)):
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
            hits[i] += h
            hit_users[i] += int(h > 0)
    users = len(actual)
    out_rows = []
    for cfg, h, hu in zip(configs, hits, hit_users):
        out_rows.append({**cfg, "hit_total": int(h), "precision@10": h / (users * K), "hit_user_rate": hu / users, "users": users})
    return out_rows


def configs_for(name: str, fallback: str) -> list[dict]:
    cfgs = [{"name": name, "fallback": fallback, "mode": "base", "cand_take": 0, "base_take": K}]
    for n in range(1, 6):
        cfgs.append({"name": name, "fallback": fallback, "mode": "replace_tail", "cand_take": n, "base_take": K - n})
    for n in range(1, 4):
        cfgs.append({"name": name, "fallback": fallback, "mode": "prefix", "cand_take": n, "base_take": 0})
    for base_take in [3, 5, 7]:
        for n in range(1, 4):
            cfgs.append({"name": name, "fallback": fallback, "mode": "after_base", "cand_take": n, "base_take": base_take})
    return cfgs


def main() -> None:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    actual = actual_sets()
    users = list(actual.keys())
    log(f"actual users={len(users):,}")
    fb_users = recent_global_top("users")
    fb_qty = recent_global_top("qty")
    with BASE_VAL_TOP_PATH.open("rb") as f:
        base_all = pickle.load(f)
    base = trim_base(base_all, set(users))
    log(f"base users={len(base):,}")

    all_results: list[dict] = []
    for fb_name, fb in [("users", fb_users), ("qty", fb_qty)]:
        rows = eval_configs(actual, base, None, fb, [{"name": "base", "fallback": fb_name, "mode": "base", "cand_take": 0, "base_take": K}])
        all_results.extend(rows)
        log(f"base {fb_name}: {rows[0]}")

    builders = [
        ("cobuy_a3_r20", lambda: build_cobuy(users, 3, 20)),
        ("cobuy_a5_r20", lambda: build_cobuy(users, 5, 20)),
        ("cat_l2", lambda: build_key(users, ["category_l2"], 30, 5)),
        ("brand", lambda: build_key(users, ["brand"], 30, 5)),
    ]
    for name, builder in builders:
        cand = builder()
        log(f"{name} users={len(cand):,}")
        for fb_name, fb in [("users", fb_users), ("qty", fb_qty)]:
            rows = eval_configs(actual, base, cand, fb, configs_for(name, fb_name))
            all_results.extend(rows)
        all_results = sorted(all_results, key=lambda r: (float(r["precision@10"]), int(r["hit_total"])), reverse=True)
        log(f"best after {name}: {all_results[0]}")
        SUMMARY_PATH.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")
        del cand
        gc.collect()

    log(f"saved {SUMMARY_PATH}")


if __name__ == "__main__":
    main()