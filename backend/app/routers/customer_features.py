from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import AuthenticatedUser, current_customer
from app.errors import DomainError
from app.mappers import to_product
from app.models import Checkin, Customer, CustomerWishlist, Inventory, Product, PurchaseHistory, Recommendation
from app.schemas import MessageResponse, ProductListResponse, ProductResponse, PurchaseListResponse, PurchaseResponse


router = APIRouter(prefix="/api/v1/customers/me", tags=["customer-features"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentCustomer = Annotated[AuthenticatedUser, Depends(current_customer)]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def active_product(product_id: str, db: Session) -> Product:
    product = db.get(Product, product_id)
    if product is None or not product.is_active:
        raise DomainError(404, "PRODUCT_NOT_FOUND", "상품을 찾을 수 없습니다.")
    return product


@router.get("/wishlist", response_model=ProductListResponse)
def get_wishlist(authenticated: CurrentCustomer, db: DbSession) -> ProductListResponse:
    products = db.scalars(
        select(Product)
        .join(CustomerWishlist, CustomerWishlist.product_id == Product.id)
        .where(CustomerWishlist.customer_id == authenticated.id, Product.is_active.is_(True))
        .order_by(CustomerWishlist.created_at.desc())
    ).all()
    return ProductListResponse(items=[to_product(product) for product in products])


@router.post("/wishlist/{product_id}", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def add_wishlist(product_id: str, authenticated: CurrentCustomer, db: DbSession) -> ProductResponse:
    product = active_product(product_id, db)
    if db.get(CustomerWishlist, (authenticated.id, product_id)) is None:
        db.add(CustomerWishlist(customer_id=authenticated.id, product_id=product_id, created_at=utc_now()))
        customer = db.get(Customer, authenticated.id)
        customer.liked_product_ids = list(dict.fromkeys([*customer.liked_product_ids, product_id]))
        db.commit()
    return to_product(product)


@router.delete("/wishlist/{product_id}", response_model=MessageResponse)
def remove_wishlist(product_id: str, authenticated: CurrentCustomer, db: DbSession) -> MessageResponse:
    wishlist = db.get(CustomerWishlist, (authenticated.id, product_id))
    if wishlist is None:
        raise DomainError(404, "WISHLIST_ITEM_NOT_FOUND", "찜 목록에서 상품을 찾을 수 없습니다.")
    db.delete(wishlist)
    customer = db.get(Customer, authenticated.id)
    customer.liked_product_ids = [item for item in customer.liked_product_ids if item != product_id]
    db.commit()
    return MessageResponse(message="찜 목록에서 삭제되었습니다.")


def recommendation_product_ids(output: dict | None) -> list[str]:
    if not output:
        return []
    candidates = output.get("looks") or output.get("recommended_products") or []
    return [item["product_id"] for item in candidates if isinstance(item, dict) and isinstance(item.get("product_id"), str)]


@router.get("/recommendations", response_model=ProductListResponse)
def get_recommendations(authenticated: CurrentCustomer, db: DbSession) -> ProductListResponse:
    rows = db.execute(
        select(Recommendation, Checkin)
        .join(Checkin, Checkin.id == Recommendation.checkin_id)
        .where(
            Recommendation.customer_id == authenticated.id,
            Recommendation.status.in_(["READY", "FALLBACK"]),
        )
        .order_by(Recommendation.created_at.desc())
    ).all()
    items: list[ProductResponse] = []
    seen: set[str] = set()
    for recommendation, checkin in rows:
        for product_id in recommendation_product_ids(recommendation.output):
            if product_id in seen:
                continue
            product = db.get(Product, product_id)
            inventory = db.get(Inventory, (checkin.store_id, product_id))
            if product is None or not product.is_active or inventory is None or inventory.quantity <= 0:
                continue
            seen.add(product_id)
            items.append(to_product(product, inventory))
    return ProductListResponse(items=items)


@router.get("/purchases", response_model=PurchaseListResponse)
def get_purchases(authenticated: CurrentCustomer, db: DbSession) -> PurchaseListResponse:
    rows = db.execute(
        select(PurchaseHistory, Product)
        .join(Product, Product.id == PurchaseHistory.product_id)
        .where(PurchaseHistory.customer_id == authenticated.id)
        .order_by(PurchaseHistory.purchased_at.desc())
    ).all()
    return PurchaseListResponse(
        items=[
            PurchaseResponse(
                purchase_id=purchase.id,
                product_id=product.id,
                name=product.name,
                category=purchase.category_snapshot,
                price=purchase.price_snapshot,
                image_url=product.image_url,
                channel=purchase.channel,
                purchased_at=purchase.purchased_at,
            )
            for purchase, product in rows
        ]
    )
