from __future__ import annotations

from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models import Customer, EntryTag, Inventory, Product, Staff, Store, User
from app.seed import PRODUCTS, seed_database


def test_seed_respects_foreign_keys_and_is_idempotent() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)

    with session_factory() as session:
        seed_database(session, demo_password="test-password", demo_qr_token="test-qr-token")
        seed_database(session, demo_password="test-password", demo_qr_token="test-qr-token")

        assert session.scalar(select(func.count()).select_from(Store)) == 3
        assert session.scalar(select(func.count()).select_from(Customer)) == 2
        assert session.scalar(select(func.count()).select_from(Product)) == len(PRODUCTS)
        assert session.scalar(select(func.count()).select_from(Inventory)) == len(PRODUCTS) * 3
        assert session.scalar(select(func.count()).select_from(EntryTag)) == 2
        assert session.scalar(select(func.count()).select_from(User)) == 4
        assert session.scalar(select(func.count()).select_from(Staff)) == 2

    engine.dispose()
