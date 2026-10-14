"""Khai bao API route cho PJ-SELLING-WEBSITE."""

from fastapi import APIRouter, Query, HTTPException
from ..services import Solution1, Solution2, Solution3, product_service

router = APIRouter()


@router.get("/health")
def health_check():
    """API kiem tra trang thai."""
    return {"status": "ok"}


@router.get("/forecast/solution3")
def get_forecast():
    """Lay ket qua du bao san luong theo Solution 3 (LightGBM)."""
    return Solution3.get_forecast()


@router.get("/products")
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = Query(None),
    brand: str | None = Query(None),
    search: str | None = Query(None),
):
    """Lay danh sach san pham co phan trang va bo loc tuy chon."""
    return product_service.list_products(
        page=page,
        page_size=page_size,
        category=category,
        brand=brand,
        search=search,
    )


@router.get("/categories")
def get_categories():
    """Lay danh sach category_l1 duy nhat."""
    return product_service.get_categories()


@router.get("/brands")
def get_brands():
    """Lay danh sach brand duy nhat."""
    return product_service.get_brands()


@router.get("/products/{item_id}")
def get_product(item_id: str):
    """Lay thong tin 1 san pham theo item_id."""
    product = product_service.get_product(item_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/recommendations/{item_id}")
def get_recommendations(
    item_id: str,
    n: int = Query(20, ge=1, le=100),
):
    """
    Lay goi y theo Solution 2.
    - Neu khong phai Ta => fallback Solution 1.
    - Neu la Ta => them xu ly upsale theo size.
    """
    return Solution2.get_recommendations(item_id, n=n)


@router.get("/related/{item_id}")
def get_related_products(
    item_id: str,
    n: int = Query(20, ge=1, le=100),
):
    """
    Lay danh sach related products theo Solution 1:
    co-buy + category tuong tu (uu tien l3, fallback l2).
    """
    return Solution1.get_related_products(item_id, n=n)
