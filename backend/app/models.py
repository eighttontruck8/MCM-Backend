from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    membership: Mapped[str] = mapped_column(String(30), default="일반")
    visit_count: Mapped[int] = mapped_column(Integer, default=0)
    preferred_colors: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_style: Mapped[str] = mapped_column(String(100), default="미정")
    recently_viewed_product_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    liked_product_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    purchase_count: Mapped[int] = mapped_column(Integer, default=0)
    upcoming_schedule: Mapped[str] = mapped_column(String(255), default="미입력")


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Seoul")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    line: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(80))
    colors: Mapped[list[str]] = mapped_column(JSON, default=list)
    material: Mapped[str] = mapped_column(String(100))
    price: Mapped[int] = mapped_column(Integer)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    image_url: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Inventory(Base):
    __tablename__ = "inventories"

    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class NfcTag(Base):
    __tablename__ = "nfc_tags"

    token: Mapped[str] = mapped_column(String(255), primary_key=True)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Checkin(Base):
    __tablename__ = "checkins"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), index=True)
    shopping_mode: Mapped[str | None] = mapped_column(String(30), nullable=True)
    visit_purpose_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    visit_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    checked_in_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    checkin_id: Mapped[str] = mapped_column(ForeignKey("checkins.id"), unique=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    policy_version: Mapped[str] = mapped_column(String(80))
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list)
    agreed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
