"""
Data Loader
===========

Tai cac parquet da preprocess vao RAM.
Dung singleton de chi tai 1 lan khi khoi dong.
Tat ca service se dung chung DataStore nay.
"""

import polars as pl
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


class DataStore:
    """Kho du lieu trong RAM chua cac artifact da preprocess."""

    def __init__(self):
        print(f"Dang tai du lieu tu {DATA_DIR} ...")

        self.products = pl.read_parquet(DATA_DIR / "products.parquet")
        self.cooccurrence = pl.read_parquet(DATA_DIR / "item_cooccurrence.parquet")

        # Dam bao cot gia co kieu Float64.
        if self.products.schema.get("price") != pl.Float64:
            self.products = self.products.with_columns(
                pl.col("price").cast(pl.Float64)
            )

        # Tuong thich nguoc neu products.parquet duoc tao truoc khi
        # co cac cot metadata size.
        optional_columns: dict[str, pl.DataType] = {
            "description": pl.Utf8,
            "raw_size": pl.Utf8,
            "normalized_size": pl.Utf8,
            "size_rank": pl.Int32,
            "is_diaper": pl.Boolean,
        }
        for col_name, dtype in optional_columns.items():
            if col_name not in self.products.columns:
                self.products = self.products.with_columns(
                    pl.lit(None, dtype=dtype).alias(col_name)
                )

        # Tao index dict de tra cuu dong O(1).
        self._product_index: dict[str, int] = {
            val: idx
            for idx, val in enumerate(self.products["item_id"].to_list())
        }

        print(f"  So product:            {self.products.height}")
        print(f"  So ban ghi co-buy:     {self.cooccurrence.height}")
        print("Tai du lieu thanh cong.\n")

    def get_product(self, item_id: str) -> dict | None:
        """Tra ve 1 product theo item_id, khong co thi tra None."""
        idx = self._product_index.get(item_id)
        if idx is None:
            return None
        return self.products.row(idx, named=True)


# Bien singleton o muc module.
_store: DataStore | None = None


def get_data_store() -> DataStore:
    """Lay hoac tao DataStore singleton."""
    global _store
    if _store is None:
        _store = DataStore()
    return _store
