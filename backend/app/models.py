from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True, nullable=True)
    membership: Mapped[str] = mapped_column(String(30), default="일반")
    visit_count: Mapped[int] = mapped_column(Integer, default=0)
    preferred_colors: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_style: Mapped[str] = mapped_column(String(100), default="미정")
    recently_viewed_product_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    liked_product_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    purchase_count: Mapped[int] = mapped_column(Integer, default=0)
    upcoming_schedule: Mapped[str] = mapped_column(String(255), default="미입력")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('CUSTOMER', 'STAFF')", name="ck_users_role"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(500))
    role: Mapped[str] = mapped_column(String(20), index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auth_version: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), index=True)
    title: Mapped[str] = mapped_column(String(80))
    experience_years: Mapped[int] = mapped_column(Integer, default=0)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


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
    __table_args__ = (CheckConstraint("quantity >= 0", name="ck_inventories_quantity_nonnegative"),)

    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EntryTag(Base):
    __tablename__ = "entry_tags"
    __table_args__ = (CheckConstraint("channel IN ('QR', 'NFC')", name="ck_entry_tags_channel"),)

    token: Mapped[str] = mapped_column(String(255), primary_key=True)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), index=True)
    channel: Mapped[str] = mapped_column(String(20), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Checkin(Base):
    __tablename__ = "checkins"
    __table_args__ = (
        CheckConstraint(
            "status IN ('CHECKED_IN', 'SELF_SHOPPING', 'WAITING_FOR_STAFF', 'ASSIGNED', 'SERVING', 'CANCELLED', 'COMPLETED')",
            name="ck_checkins_status",
        ),
        CheckConstraint(
            "shopping_mode IS NULL OR shopping_mode IN ('PRIVATE', 'STAFF_ASSISTED')",
            name="ck_checkins_shopping_mode",
        ),
    )

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
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class StaffAssignment(Base):
    __tablename__ = "staff_assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    checkin_id: Mapped[str] = mapped_column(ForeignKey("checkins.id"), unique=True, index=True)
    staff_id: Mapped[str] = mapped_column(ForeignKey("staff.id"), index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (
        CheckConstraint("type IN ('LOOKBOOK', 'STAFF_GUIDE')", name="ck_recommendations_type"),
        CheckConstraint(
            "status IN ('READY', 'FALLBACK', 'FAILED', 'REVOKED')",
            name="ck_recommendations_status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    checkin_id: Mapped[str] = mapped_column(ForeignKey("checkins.id"), index=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    type: Mapped[str] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    input_hash: Mapped[str] = mapped_column(String(64), index=True)
    output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CustomerWishlist(Base):
    __tablename__ = "customer_wishlist"

    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    category_snapshot: Mapped[str] = mapped_column(String(80))
    price_snapshot: Mapped[int] = mapped_column(Integer)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    actor_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    resource_type: Mapped[str] = mapped_column(String(80), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
