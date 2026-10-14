"""
Script preprocess du lieu cho PJ-SELLING-WEBSITE
================================================

Doc parquet goc va tao cac artifact su dung cho backend API.

Chien luoc phat hien co-purchase (khong co order_id/cart_id):
    Gom transaction theo (customer_id, ngay) de mo phong session mua hang.
    Cac item trong cung session duoc xem la mua cung nhau.
    Session co hon 50 item duy nhat se bi loai de tranh no to hop.

Artifact tao ra (luu trong thu muc data/):
    - products.parquet          : catalog da lam sach + metadata size cho Ta
    - item_cooccurrence.parquet : so lan xuat hien cung nhau giua cap item
"""

import polars as pl
from pathlib import Path
from collections import Counter
from itertools import combinations
import time
import re

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_ITEMS = ROOT / "raw_data" / "items.parquet"
RAW_TRANSACTIONS = ROOT / "raw_data" / "transactions-2025-12.parquet"
DIAPER_CATEGORY = "T\u00e3"

SIZE_RANK: dict[str, int] = {
    "NB": 0,
    "S": 1,
    "M": 2,
    "L": 3,
    "XL": 4,
    "XXL": 5,
    "XXXL": 6,
}
SIZE_PATTERNS = [
    re.compile(r"(?i)\bsize\s*(newborn|nb|xxxl|xxl|xl|l|m|s)\b"),
    re.compile(r"(?i)\(\s*(newborn|nb|xxxl|xxl|xl|l|m|s)\s*[,)\-]"),
    re.compile(r"(?i)\b(newborn|nb|xxxl|xxl|xl)\b"),
    re.compile(r"(?i)\b(l|m|s)\s*\("),
    re.compile(r"(?i)\b(l|m|s)\s*\d+\s*mi(?:e|[\u1ebf])ng\b"),
]


def _normalize_size_token(token: str | None) -> str | None:
    """Chuan hoa alias size ve NB/S/M/L/XL/XXL/XXXL."""
    if token is None:
        return None
    normalized = token.upper().replace(" ", "")
    if normalized == "NEWBORN":
        normalized = "NB"
    return normalized if normalized in SIZE_RANK else None


def _extract_size_from_text(text: str | None) -> str | None:
    """Trich xuat size tu text mo ta bang regex an toan."""
    if not text:
        return None
    cleaned = text.replace("\ufeff", " ")
    for pattern in SIZE_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            size = _normalize_size_token(match.group(1))
            if size:
                return size
    return None


def _derive_diaper_size(values: dict[str, str | None]) -> str | None:
    """Uu tien raw_size, neu khong co thi parse tu description."""
    if values.get("category_l1") != DIAPER_CATEGORY:
        return None
    raw_size = _extract_size_from_text(values.get("raw_size"))
    if raw_size:
        return raw_size
    return _extract_size_from_text(values.get("description"))


def load_raw_data():
    """Tai va lam sach du lieu parquet goc, loai item ngung ban."""
    print("Dang tai du lieu goc...")
    items = pl.read_parquet(RAW_ITEMS)
    transactions = pl.read_parquet(RAW_TRANSACTIONS)

    # Chuyen Decimal ve Float64 de xu ly sau do don gian hon.
    items = items.with_columns(pl.col("price").cast(pl.Float64))
    transactions = transactions.with_columns(
        pl.col("price").cast(pl.Float64),
        pl.col("updated_date").cast(pl.Datetime("us")),
    )

    print(f"  Items (raw): {items.height} dong, {items.width} cot")
    print(f"  Transactions (raw): {transactions.height} dong, {transactions.width} cot")

    # Loai item ngung ban (sale_status == 0).
    items = items.filter(pl.col("sale_status") != 0)
    print(f"  Items sau khi loai ngung ban (sale_status=0): {items.height} dong")

    # Loai transaction tham chieu item da ngung ban.
    active_item_ids = items["item_id"].unique()
    transactions = transactions.filter(
        pl.col("item_id").is_in(active_item_ids.implode())
    )
    print(f"  Transactions sau khi loc: {transactions.height} dong")

    return items, transactions


def build_products(items: pl.DataFrame):
    """Tao va luu catalog san pham da lam sach."""
    print("\nDang tao products catalog...")
    products = items

    if "size" in products.columns:
        products = products.rename({"size": "raw_size"})
    else:
        products = products.with_columns(
            pl.lit(None, dtype=pl.Utf8).alias("raw_size")
        )

    if "description" not in products.columns:
        products = products.with_columns(
            pl.lit(None, dtype=pl.Utf8).alias("description")
        )

    products = (
        products
        .with_columns(
            (pl.col("category_l1") == DIAPER_CATEGORY).alias("is_diaper")
        )
        .with_columns(
            pl.struct(["raw_size", "description", "category_l1"])
            .map_elements(_derive_diaper_size, return_dtype=pl.Utf8)
            .alias("normalized_size")
        )
        .with_columns(
            pl.col("normalized_size")
            .map_elements(lambda v: SIZE_RANK.get(v), return_dtype=pl.Int32)
            .alias("size_rank")
        )
    )

    products.write_parquet(DATA_DIR / "products.parquet")
    print(f"  Da luu {products.height} products")


def build_cooccurrence(transactions: pl.DataFrame):
    """
    Tao ma tran co-occurrence theo pseudo-session.

    Cach lam:
        1. Gom transaction theo (customer_id, ngay)
        2. Giu session co 2-50 item duy nhat
        3. Tao tat ca cap item trong tung session
        4. Dem tan suat xuat hien cua moi cap
        5. Luu 2 chieu A->B va B->A de truy van nhanh
    """
    print("\nDang tao co-occurrence matrix...")
    start = time.time()

    # Tao pseudo-session: cung customer + cung ngay.
    sessions = (
        transactions.with_columns(
            pl.col("updated_date").dt.date().alias("session_date")
        )
        .group_by(["customer_id", "session_date"])
        .agg(pl.col("item_id").unique().alias("items"))
        .filter(pl.col("items").list.len() >= 2)   # Can >= 2 item moi tao duoc cap
        .filter(pl.col("items").list.len() <= 50)   # Gioi han de tranh no to hop
    )

    n_sessions = sessions.height
    print(f"  So session co 2-50 item duy nhat: {n_sessions}")

    # Dem cap co-occurrence bang Python Counter.
    pair_counts: Counter = Counter()
    session_items_list = sessions["items"].to_list()

    for idx, items_in_session in enumerate(session_items_list):
        if idx % 100000 == 0 and idx > 0:
            print(f"    Dang xu ly session {idx}/{n_sessions}...")
        sorted_items = sorted(set(items_in_session))
        for a, b in combinations(sorted_items, 2):
            pair_counts[(a, b)] += 1

    elapsed = time.time() - start
    print(f"  So cap co huong duy nhat: {len(pair_counts)}")
    print(f"  Thoi gian tao cap: {elapsed:.1f}s")

    if pair_counts:
        # Luu ca 2 chieu (a->b va b->a) de truy van de hon.
        items_a, items_b, counts = [], [], []
        for (a, b), count in pair_counts.items():
            items_a.extend([a, b])
            items_b.extend([b, a])
            counts.extend([count, count])

        cooccurrence = (
            pl.DataFrame({
                "item_a": items_a,
                "item_b": items_b,
                "co_count": counts,
            })
            .sort(["item_a", "co_count"], descending=[False, True])
        )
    else:
        cooccurrence = pl.DataFrame({
            "item_a": pl.Series([], dtype=pl.Utf8),
            "item_b": pl.Series([], dtype=pl.Utf8),
            "co_count": pl.Series([], dtype=pl.Int64),
        })

    cooccurrence.write_parquet(DATA_DIR / "item_cooccurrence.parquet")
    print(f"  Tong ban ghi co-occurrence (2 chieu): {cooccurrence.height}")


def main():
    DATA_DIR.mkdir(exist_ok=True)

    items, transactions = load_raw_data()
    build_products(items)
    build_cooccurrence(transactions)

    print("\n" + "=" * 50)
    print("Preprocess hoan tat! Da luu artifact vao data/")
    print("=" * 50)


if __name__ == "__main__":
    main()
