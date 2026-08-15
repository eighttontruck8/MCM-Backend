from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Customer, CustomerWishlist, EntryTag, Inventory, Product, PurchaseHistory, Staff, Store, User
from app.schemas import EntryChannel, UserRole
from app.security import hash_password


CUSTOMERS = [
    {
        "id": "C001",
        "name": "김서연",
        "membership": "VIP",
        "visit_count": 5,
        "preferred_colors": ["블랙", "코냑"],
        "preferred_style": "미니멀 비즈니스",
        "recently_viewed_product_ids": ["P001", "P006"],
        "liked_product_ids": ["P001"],
        "purchase_count": 2,
        "upcoming_schedule": "다음 주 싱가포르 출장",
    },
    {
        "id": "C002",
        "name": "이지훈",
        "membership": "일반",
        "visit_count": 2,
        "preferred_colors": ["블랙"],
        "preferred_style": "캐주얼 스트리트",
        "recently_viewed_product_ids": ["P003", "P002"],
        "liked_product_ids": ["P003"],
        "purchase_count": 1,
        "upcoming_schedule": "주말 제주 여행",
    },
]

PRODUCTS = [
    ("P001", "스타크 사이드 스터드 비세토스 백팩", "Stark", "백팩", ["코냑", "블랙"], "비세토스", 1490000, ["여행", "비즈니스", "노트북수납", "데일리"], 3),
    ("P002", "아렌 스몰 숄더백", "Aren", "숄더백", ["블랙", "핑크"], "가죽", 890000, ["데일리", "미니멀", "파티"], 2),
    ("P003", "트레이시 비세토스 숄더백", "Tracy", "숄더백", ["코냑", "화이트"], "비세토스", 1670000, ["데일리", "클래식", "비즈니스"], 0),
    ("P004", "비세토스 레더 믹스 다이아몬드 토트백", "Diamond", "토트백", ["블랙"], "비세토스+가죽", 940000, ["비즈니스", "노트북수납", "오피스"], 4),
    ("P005", "토니 미니 캔버스 쇼퍼백", "Tony", "쇼퍼백", ["핑크", "베이지"], "캔버스", 1220000, ["캐주얼", "데일리", "여행"], 1),
    ("P006", "비세토스 위켄더 백", "Weekender", "트래블백", ["코냑", "블랙"], "비세토스", 1850000, ["여행", "기내반입", "출장"], 2),
]


def seed_database(
    session: Session,
    demo_password: str | None = None,
    demo_qr_token: str = "qr-demo-seoul-001-7f4d0b9e8c2a",
) -> None:
    now = datetime.now(timezone.utc)
    if not session.scalar(select(func.count()).select_from(Customer)):
        store = Store(id="S001", name="MCM 서울 플래그십", timezone="Asia/Seoul")
        session.add(store)
        session.add_all(Customer(**customer) for customer in CUSTOMERS)

        for product_id, name, line, category, colors, material, price, tags, quantity in PRODUCTS:
            session.add(
                Product(
                    id=product_id,
                    name=name,
                    line=line,
                    category=category,
                    colors=colors,
                    material=material,
                    price=price,
                    tags=tags,
                    image_url=f"/assets/products/{product_id.lower()}.jpg",
                )
            )
            session.add(
                Inventory(
                    store_id=store.id,
                    product_id=product_id,
                    quantity=quantity,
                    updated_at=now,
                )
            )

    entry_tags = [
        (demo_qr_token, EntryChannel.QR),
        ("nfc-demo-seoul-001", EntryChannel.NFC),
    ]
    for token, channel in entry_tags:
        if session.get(EntryTag, token) is None:
            session.add(EntryTag(token=token, store_id="S001", channel=channel.value, is_active=True))

    if demo_password:
        seed_users = [
            ("C001", "customer@example.com", UserRole.CUSTOMER, "김서연"),
            ("C002", "customer2@example.com", UserRole.CUSTOMER, "이지훈"),
            ("ST001", "staff@example.com", UserRole.STAFF, "박민준"),
            ("ST002", "staff2@example.com", UserRole.STAFF, "최유진"),
        ]
        for user_id, email, role, display_name in seed_users:
            if session.get(User, user_id) is None:
                session.add(User(id=user_id, email=email, password_hash=hash_password(demo_password), role=role.value, display_name=display_name, created_at=now, updated_at=now))
        session.flush()
        if session.get(Staff, "ST001") is None:
            session.add(Staff(id="ST001", store_id="S001", title="Client Advisor", experience_years=4))
        if session.get(Staff, "ST002") is None:
            session.add(Staff(id="ST002", store_id="S001", title="Senior Client Advisor", experience_years=6))

    wishlist_seed = {"C001": ["P001"], "C002": ["P003"]}
    for customer_id, product_ids in wishlist_seed.items():
        for product_id in product_ids:
            if session.get(CustomerWishlist, (customer_id, product_id)) is None:
                session.add(CustomerWishlist(customer_id=customer_id, product_id=product_id, created_at=now))

    if not session.scalar(select(func.count()).select_from(PurchaseHistory)):
        purchase_seed = [
            ("C001", "P004", 120),
            ("C001", "P001", 45),
            ("C002", "P002", 30),
        ]
        for customer_id, product_id, days_ago in purchase_seed:
            product = session.get(Product, product_id)
            session.add(
                PurchaseHistory(
                    id=str(uuid4()),
                    customer_id=customer_id,
                    product_id=product_id,
                    category_snapshot=product.category,
                    price_snapshot=product.price,
                    purchased_at=now - timedelta(days=days_ago),
                )
            )

    session.commit()
