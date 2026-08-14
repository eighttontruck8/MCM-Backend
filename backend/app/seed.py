from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Customer, Inventory, NfcTag, Product, Store


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


def seed_database(session: Session) -> None:
    if session.scalar(select(func.count()).select_from(Customer)):
        return

    now = datetime.now(timezone.utc)
    store = Store(id="S001", name="MCM 서울 플래그십", timezone="Asia/Seoul")
    session.add(store)
    session.add(NfcTag(token="nfc-demo-seoul-001", store_id=store.id, is_active=True))
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

    session.commit()
