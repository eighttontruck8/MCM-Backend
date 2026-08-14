from __future__ import annotations

from app.models import Customer, Inventory, Product, Store
from app.schemas import CustomerResponse, InventoryResponse, ProductResponse, StoreResponse


def to_customer(customer: Customer) -> CustomerResponse:
    return CustomerResponse(
        customer_id=customer.id,
        name=customer.name,
        membership=customer.membership,
        visit_count=customer.visit_count,
        preferred_colors=customer.preferred_colors,
        preferred_style=customer.preferred_style,
        recently_viewed_product_ids=customer.recently_viewed_product_ids,
        liked_product_ids=customer.liked_product_ids,
        purchase_count=customer.purchase_count,
        upcoming_schedule=customer.upcoming_schedule,
    )


def to_store(store: Store) -> StoreResponse:
    return StoreResponse(store_id=store.id, name=store.name, timezone=store.timezone)


def to_product(product: Product, inventory: Inventory | None = None) -> ProductResponse:
    inventory_response = None
    if inventory is not None:
        inventory_response = InventoryResponse(
            store_id=inventory.store_id,
            quantity=inventory.quantity,
            in_stock=inventory.quantity > 0,
            updated_at=inventory.updated_at,
        )
    return ProductResponse(
        product_id=product.id,
        name=product.name,
        line=product.line,
        category=product.category,
        colors=product.colors,
        material=product.material,
        price=product.price,
        tags=product.tags,
        image_url=product.image_url,
        inventory=inventory_response,
    )
