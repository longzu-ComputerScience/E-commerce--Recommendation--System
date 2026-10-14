"""Product Service: xu ly lay danh sach va chi tiet san pham."""

import polars as pl
from .data_loader import get_data_store


def list_products(
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    brand: str | None = None,
    search: str | None = None,
) -> dict:
    """Lay danh sach san pham co phan trang va bo loc."""
    store = get_data_store()
    df = store.products

    if category:
        df = df.filter(pl.col("category_l1") == category)

    if brand:
        df = df.filter(pl.col("brand") == brand)

    if search:
        search_lower = search.lower()
        df = df.filter(
            pl.col("category").str.to_lowercase().str.contains(search_lower, literal=True)
            | pl.col("brand").str.to_lowercase().str.contains(search_lower, literal=True)
            | pl.col("category_l1").str.to_lowercase().str.contains(search_lower, literal=True)
            | pl.col("category_l2").str.to_lowercase().str.contains(search_lower, literal=True)
            | pl.col("item_id").str.contains(search_lower, literal=True)
        )

    total = df.height
    offset = (page - 1) * page_size
    page_df = df.slice(offset, page_size)

    return {
        "products": page_df.to_dicts(),
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_product(item_id: str) -> dict | None:
    """Lay thong tin 1 san pham theo item_id."""
    return get_data_store().get_product(item_id)


def get_categories() -> list[str]:
    """Lay toan bo category_l1 duy nhat, sap xep tang dan."""
    store = get_data_store()
    return store.products["category_l1"].unique().sort().to_list()


def get_brands() -> list[str]:
    """Lay toan bo brand duy nhat, sap xep tang dan."""
    store = get_data_store()
    return store.products["brand"].unique().sort().to_list()
