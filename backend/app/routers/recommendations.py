from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import AIProviderUnavailable, RuleBasedAIProvider
from app.database import get_db
from app.dependencies import AuthenticatedUser, current_customer, current_staff
from app.errors import DomainError
from app.models import Checkin, Consent, Customer, Inventory, Product, Recommendation, StaffAssignment
from app.routers.staff import STAFF_ACTIVE_STATUSES, mask_name
from app.schemas import (
    GuideCustomerResponse,
    GuideProductResponse,
    LookbookProductResponse,
    LookbookResponse,
    StaffGuideResponse,
)


router = APIRouter(prefix="/api/v1", tags=["recommendations"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentCustomer = Annotated[AuthenticatedUser, Depends(current_customer)]
CurrentStaff = Annotated[AuthenticatedUser, Depends(current_staff)]
CUSTOMER_ACTIVE_STATUSES = STAFF_ACTIVE_STATUSES | {"CHECKED_IN", "SELF_SHOPPING"}


class AIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RawLook(AIModel):
    product_id: str = Field(min_length=1)
    styling: str = Field(min_length=1)
    product: str | None = None
    image_url: str | None = None
    price: int | None = None
    in_stock: bool | None = None


class RawLookbook(AIModel):
    title: str = Field(min_length=1)
    intro: str = Field(min_length=1)
    looks: list[RawLook]
    closing: str = Field(min_length=1)
    generated_at: datetime | None = None


class RawGuideProduct(AIModel):
    product_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    name: str | None = None
    image_url: str | None = None
    price: int | None = None
    quantity: int | None = None
    in_stock: bool | None = None


class RawGuide(AIModel):
    customer_summary: str = Field(min_length=1)
    recommended_products: list[RawGuideProduct]
    greeting: str = Field(min_length=1)
    cross_sell: str = Field(min_length=1)
    caution: str = Field(min_length=1)
    checkin_id: str | None = None
    customer: dict | None = None
    generated_at: datetime | None = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalized_output(raw: object) -> object:
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("AI 응답이 JSON 형식이 아닙니다.") from exc
    return raw


def candidate_rows(checkin: Checkin, db: Session) -> list[tuple[Product, Inventory]]:
    return db.execute(
        select(Product, Inventory)
        .join(Inventory, Inventory.product_id == Product.id)
        .where(
            Product.is_active.is_(True),
            Inventory.store_id == checkin.store_id,
            Inventory.quantity > 0,
        )
    ).all()


def build_context(
    checkin: Checkin,
    customer: Customer,
    rows: list[tuple[Product, Inventory]],
    *,
    staff_view: bool,
    consent_scopes: set[str] | None = None,
) -> dict:
    style_allowed = not staff_view or "STYLE_PROFILE" in (consent_scopes or set())
    customer_context = {
        "customer_id": customer.id,
        "membership": customer.membership,
        "visit_count": customer.visit_count,
        "preferred_colors": customer.preferred_colors if style_allowed else [],
        "preferred_style": customer.preferred_style if style_allowed else "미정",
        "recently_viewed_product_ids": customer.recently_viewed_product_ids if style_allowed else [],
        "liked_product_ids": customer.liked_product_ids if style_allowed else [],
        "upcoming_schedule": customer.upcoming_schedule if style_allowed else "미공개",
    }
    if staff_view:
        customer_context["masked_name"] = mask_name(customer.name)
    else:
        customer_context["display_name"] = customer.name
    return {
        "customer": customer_context,
        "visit_context": {
            "store_id": checkin.store_id,
            "purpose_code": checkin.visit_purpose_code,
            "purpose_note": checkin.visit_note,
        },
        "candidate_products": [
            {
                "product_id": product.id,
                "name": product.name,
                "category": product.category,
                "colors": product.colors,
                "price": product.price,
                "tags": product.tags,
                "quantity": inventory.quantity,
            }
            for product, inventory in rows
        ],
    }


def context_hash(recommendation_type: str, context: dict) -> str:
    encoded = json.dumps({"type": recommendation_type, "context": context}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def cached_output(recommendation_type: str, input_hash: str, db: Session) -> dict | None:
    recommendation = db.scalar(
        select(Recommendation)
        .where(
            Recommendation.type == recommendation_type,
            Recommendation.input_hash == input_hash,
            Recommendation.status.in_(["READY", "FALLBACK"]),
        )
        .order_by(Recommendation.created_at.desc())
    )
    return recommendation.output if recommendation else None


def save_recommendation(
    *,
    checkin: Checkin,
    recommendation_type: str,
    input_hash: str,
    status: str,
    db: Session,
    output: dict | None = None,
    error_code: str | None = None,
) -> None:
    now = utc_now()
    db.add(
        Recommendation(
            id=str(uuid4()),
            checkin_id=checkin.id,
            customer_id=checkin.customer_id,
            type=recommendation_type,
            status=status,
            input_hash=input_hash,
            output=output,
            error_code=error_code,
            created_at=now,
            updated_at=now,
        )
    )
    db.commit()


def safe_raw_lookbook(context: dict) -> RawLookbook:
    return RawLookbook.model_validate(RuleBasedAIProvider().generate_lookbook(context))


def safe_raw_guide(context: dict) -> RawGuide:
    return RawGuide.model_validate(RuleBasedAIProvider().generate_staff_guide(context))


def validated_lookbook(raw: RawLookbook, context: dict, rows: list[tuple[Product, Inventory]]) -> LookbookResponse:
    products = {product.id: (product, inventory) for product, inventory in rows}
    valid_looks = [look for look in raw.looks if look.product_id in products]
    if not valid_looks:
        valid_looks = safe_raw_lookbook(context).looks
    looks = []
    seen: set[str] = set()
    for look in valid_looks:
        if look.product_id in seen or look.product_id not in products:
            continue
        seen.add(look.product_id)
        product, inventory = products[look.product_id]
        looks.append(LookbookProductResponse(product_id=product.id, product=product.name, styling=look.styling, image_url=product.image_url, price=product.price, in_stock=inventory.quantity > 0))
    return LookbookResponse(title=raw.title, intro=raw.intro, looks=looks, closing=raw.closing, generated_at=utc_now())


def validated_guide(raw: RawGuide, context: dict, checkin: Checkin, customer: Customer, rows: list[tuple[Product, Inventory]]) -> StaffGuideResponse:
    products = {product.id: (product, inventory) for product, inventory in rows}
    valid_products = [item for item in raw.recommended_products if item.product_id in products]
    if not valid_products:
        valid_products = safe_raw_guide(context).recommended_products
    recommendations = []
    seen: set[str] = set()
    for item in valid_products:
        if item.product_id in seen or item.product_id not in products:
            continue
        seen.add(item.product_id)
        product, inventory = products[item.product_id]
        recommendations.append(GuideProductResponse(product_id=product.id, name=product.name, reason=item.reason, image_url=product.image_url, price=product.price, quantity=inventory.quantity, in_stock=inventory.quantity > 0))
    return StaffGuideResponse(
        checkin_id=checkin.id,
        customer=GuideCustomerResponse(customer_id=customer.id, masked_name=mask_name(customer.name), membership=customer.membership, visit_count=customer.visit_count, visit_purpose=checkin.visit_purpose_code),
        customer_summary=raw.customer_summary,
        recommended_products=recommendations,
        greeting=raw.greeting,
        cross_sell=raw.cross_sell,
        caution=raw.caution,
        generated_at=utc_now(),
    )


@router.post("/check-ins/{checkin_id}/lookbook", response_model=LookbookResponse)
def create_lookbook(checkin_id: str, request: Request, authenticated: CurrentCustomer, db: DbSession) -> LookbookResponse:
    checkin = db.get(Checkin, checkin_id)
    if checkin is None:
        raise DomainError(404, "CHECKIN_NOT_FOUND", "체크인을 찾을 수 없습니다.")
    if checkin.customer_id != authenticated.id:
        raise DomainError(403, "CHECKIN_ACCESS_DENIED", "이 체크인에 접근할 수 없습니다.")
    if checkin.status not in CUSTOMER_ACTIVE_STATUSES:
        raise DomainError(409, "CHECKIN_STATE_CONFLICT", "종료된 체크인에서는 룩북을 생성할 수 없습니다.")
    customer = db.get(Customer, checkin.customer_id)
    rows = candidate_rows(checkin, db)
    context = build_context(checkin, customer, rows, staff_view=False)
    input_hash = context_hash("LOOKBOOK", context)
    cached = cached_output("LOOKBOOK", input_hash, db)
    if cached is not None:
        return LookbookResponse.model_validate(cached)
    try:
        raw_output, used_fallback = request.app.state.ai_service.generate("generate_lookbook", context)
        raw = RawLookbook.model_validate(normalized_output(raw_output))
    except (ValidationError, ValueError):
        save_recommendation(checkin=checkin, recommendation_type="LOOKBOOK", input_hash=input_hash, status="FAILED", error_code="AI_RESPONSE_INVALID", db=db)
        raise DomainError(502, "AI_RESPONSE_INVALID", "AI 응답 형식이 올바르지 않습니다.") from None
    except AIProviderUnavailable:
        raise DomainError(503, "AI_SERVICE_UNAVAILABLE", "추천 서비스를 일시적으로 사용할 수 없습니다.") from None
    response = validated_lookbook(raw, context, rows)
    save_recommendation(
        checkin=checkin,
        recommendation_type="LOOKBOOK",
        input_hash=input_hash,
        status="FALLBACK" if used_fallback else "READY",
        output=response.model_dump(mode="json"),
        error_code="AI_PROVIDER_UNAVAILABLE" if used_fallback else None,
        db=db,
    )
    return response


@router.get("/staff/check-ins/{checkin_id}/guide", response_model=StaffGuideResponse)
def get_staff_guide(checkin_id: str, request: Request, authenticated: CurrentStaff, db: DbSession) -> StaffGuideResponse:
    checkin = db.get(Checkin, checkin_id)
    if checkin is None:
        raise DomainError(404, "CHECKIN_NOT_FOUND", "체크인을 찾을 수 없습니다.")
    if checkin.store_id != authenticated.store_id:
        raise DomainError(403, "STAFF_STORE_ACCESS_DENIED", "소속 매장의 체크인만 조회할 수 있습니다.")
    if checkin.status not in STAFF_ACTIVE_STATUSES:
        raise DomainError(403, "STAFF_GUIDE_ACCESS_DENIED", "활성 방문에서만 가이드를 조회할 수 있습니다.")
    consent = db.scalar(select(Consent).where(Consent.checkin_id == checkin.id))
    assignment = db.scalar(select(StaffAssignment).where(StaffAssignment.checkin_id == checkin.id))
    if consent is None:
        raise DomainError(403, "PROFILE_SHARE_CONSENT_REQUIRED", "정보 공유 동의가 필요합니다.")
    if assignment is None or assignment.staff_id != authenticated.id:
        raise DomainError(403, "ASSIGNED_STAFF_REQUIRED", "배정된 직원만 상세 가이드를 조회할 수 있습니다.")
    customer = db.get(Customer, checkin.customer_id)
    rows = candidate_rows(checkin, db)
    context = build_context(checkin, customer, rows, staff_view=True, consent_scopes=set(consent.scopes))
    input_hash = context_hash("STAFF_GUIDE", context)
    cached = cached_output("STAFF_GUIDE", input_hash, db)
    if cached is not None:
        return StaffGuideResponse.model_validate(cached)
    try:
        raw_output, used_fallback = request.app.state.ai_service.generate("generate_staff_guide", context)
        raw = RawGuide.model_validate(normalized_output(raw_output))
    except (ValidationError, ValueError):
        save_recommendation(checkin=checkin, recommendation_type="STAFF_GUIDE", input_hash=input_hash, status="FAILED", error_code="AI_RESPONSE_INVALID", db=db)
        raise DomainError(502, "AI_RESPONSE_INVALID", "AI 응답 형식이 올바르지 않습니다.") from None
    except AIProviderUnavailable:
        raise DomainError(503, "AI_SERVICE_UNAVAILABLE", "추천 서비스를 일시적으로 사용할 수 없습니다.") from None
    response = validated_guide(raw, context, checkin, customer, rows)
    save_recommendation(
        checkin=checkin,
        recommendation_type="STAFF_GUIDE",
        input_hash=input_hash,
        status="FALLBACK" if used_fallback else "READY",
        output=response.model_dump(mode="json"),
        error_code="AI_PROVIDER_UNAVAILABLE" if used_fallback else None,
        db=db,
    )
    request.app.state.event_broker.publish(
        [f"staff:{checkin.store_id}"],
        "AI_GUIDE_READY",
        {"checkin_id": checkin.id, "status": "FALLBACK" if used_fallback else "READY"},
    )
    return response
