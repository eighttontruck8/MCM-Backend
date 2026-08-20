from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import AuthenticatedUser, current_customer
from app.errors import DomainError
from app.mappers import to_customer, to_product, to_store
from app.models import Customer, Inventory, Product, Store
from app.schemas import CustomerResponse, ProductListResponse, ProductResponse, StoreListResponse, StoreResponse


router = APIRouter(prefix="/api/v1", tags=["catalog"])


@router.get("/customers/me", response_model=CustomerResponse)
def get_my_customer(
    authenticated: Annotated[AuthenticatedUser, Depends(current_customer)],
    db: Session = Depends(get_db),
) -> CustomerResponse:
    customer = db.get(Customer, authenticated.id)
    if customer is None:
        raise DomainError(404, "CUSTOMER_NOT_FOUND", "고객을 찾을 수 없습니다.")
    return to_customer(customer)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: str,
    authenticated: Annotated[AuthenticatedUser, Depends(current_customer)],
    db: Session = Depends(get_db),
) -> CustomerResponse:
    if customer_id != authenticated.id:
        raise DomainError(403, "CUSTOMER_ACCESS_DENIED", "다른 고객 정보에 접근할 수 없습니다.")
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise DomainError(404, "CUSTOMER_NOT_FOUND", "고객을 찾을 수 없습니다.")
    return to_customer(customer)


@router.get("/stores/{store_id}", response_model=StoreResponse)
def get_store(store_id: str, db: Session = Depends(get_db)) -> StoreResponse:
    store = db.get(Store, store_id)
    if store is None or not store.is_active:
        raise DomainError(404, "STORE_NOT_FOUND", "매장을 찾을 수 없습니다.")
    return to_store(store)


@router.get("/stores", response_model=StoreListResponse)
def list_stores(db: Session = Depends(get_db)) -> StoreListResponse:
    # [Backend-14-'가까운 매장 체크인'] 클라이언트가 위치 기준으로 정렬할 수 있도록 좌표를 제공한다.
    stores = db.scalars(select(Store).where(Store.is_active.is_(True)).order_by(Store.id)).all()
    return StoreListResponse(items=[to_store(store) for store in stores])


@router.get("/products", response_model=ProductListResponse)
def list_products(
    store_id: str | None = None,
    in_stock: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ProductListResponse:
    if store_id:
        statement = select(Product, Inventory).outerjoin(
            Inventory,
            (Inventory.product_id == Product.id) & (Inventory.store_id == store_id),
        ).where(Product.is_active.is_(True))
        if in_stock is True:
            statement = statement.where(Inventory.quantity > 0)
        elif in_stock is False:
            statement = statement.where((Inventory.quantity <= 0) | (Inventory.quantity.is_(None)))
        items = [to_product(product, inventory) for product, inventory in db.execute(statement).all()]
    else:
        products = db.scalars(select(Product).where(Product.is_active.is_(True))).all()
        items = [to_product(product) for product in products]
    return ProductListResponse(items=items)


@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    store_id: str | None = None,
    db: Session = Depends(get_db),
) -> ProductResponse:
    product = db.get(Product, product_id)
    if product is None or not product.is_active:
        raise DomainError(404, "PRODUCT_NOT_FOUND", "상품을 찾을 수 없습니다.")
    inventory = db.get(Inventory, (store_id, product_id)) if store_id else None
    return to_product(product, inventory)
