from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.database import get_db
from app.dependencies import current_customer_id
from app.errors import DomainError
from app.mappers import to_store
from app.models import Checkin, Consent, Customer, EntryTag, Recommendation, Staff, StaffAssignment, Store, User
from app.schemas import (
    CheckinCreateRequest,
    CheckinCreateResponse,
    CheckinResponse,
    CheckinStatus,
    ConsentRevocationResponse,
    MessageResponse,
    ServiceRequestCreate,
    ServiceRequestResponse,
    ShoppingMode,
    ShoppingModeRequest,
    ShoppingModeResponse,
    StaffSummaryResponse,
)


router = APIRouter(prefix="/api/v1/check-ins", tags=["check-ins"])
CustomerId = Annotated[str, Depends(current_customer_id)]
DbSession = Annotated[Session, Depends(get_db)]
ACTIVE_STATUSES = {
    CheckinStatus.CHECKED_IN.value,
    CheckinStatus.SELF_SHOPPING.value,
    CheckinStatus.WAITING_FOR_STAFF.value,
    CheckinStatus.ASSIGNED.value,
    CheckinStatus.SERVING.value,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def owned_checkin(checkin_id: str, customer_id: str, db: Session) -> Checkin:
    checkin = db.get(Checkin, checkin_id)
    if checkin is None:
        raise DomainError(404, "CHECKIN_NOT_FOUND", "체크인을 찾을 수 없습니다.")
    if checkin.customer_id != customer_id:
        raise DomainError(403, "CHECKIN_ACCESS_DENIED", "이 체크인에 접근할 수 없습니다.")
    return checkin


def to_checkin_response(checkin: Checkin, db: Session) -> CheckinResponse:
    assigned_staff = None
    assignment = db.scalar(
        select(StaffAssignment).where(
            StaffAssignment.checkin_id == checkin.id,
            StaffAssignment.ended_at.is_(None),
        )
    )
    if assignment is not None:
        staff = db.get(Staff, assignment.staff_id)
        user = db.get(User, assignment.staff_id)
        if staff is not None and user is not None:
            assigned_staff = StaffSummaryResponse(
                staff_id=staff.id,
                name=user.display_name,
                title=staff.title,
                experience_years=staff.experience_years,
            )
    return CheckinResponse(
        checkin_id=checkin.id,
        customer_id=checkin.customer_id,
        store_id=checkin.store_id,
        shopping_mode=checkin.shopping_mode,
        visit_purpose_code=checkin.visit_purpose_code,
        visit_note=checkin.visit_note,
        status=checkin.status,
        checked_in_at=checkin.checked_in_at,
        updated_at=checkin.updated_at,
        assigned_staff=assigned_staff,
    )


@router.post("", response_model=CheckinCreateResponse, status_code=status.HTTP_201_CREATED)
def create_checkin(
    body: CheckinCreateRequest,
    customer_id: CustomerId,
    db: DbSession,
) -> CheckinCreateResponse:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise DomainError(404, "CUSTOMER_NOT_FOUND", "고객을 찾을 수 없습니다.")

    tag = db.get(EntryTag, body.tag_token)
    if tag is None or not tag.is_active:
        raise DomainError(400, "INVALID_ENTRY_TAG", "유효하지 않은 매장 진입 태그입니다.")
    store = db.get(Store, tag.store_id)
    if store is None or not store.is_active:
        raise DomainError(400, "STORE_UNAVAILABLE", "현재 체크인할 수 없는 매장입니다.")

    existing = db.scalar(
        select(Checkin).where(
            Checkin.customer_id == customer_id,
            Checkin.store_id == store.id,
            Checkin.status.in_(ACTIVE_STATUSES),
        )
    )
    if existing is not None:
        raise DomainError(
            409,
            "ACTIVE_CHECKIN_EXISTS",
            "종료되지 않은 체크인이 이미 있습니다.",
            {"checkin_id": existing.id},
        )

    now = utc_now()
    checkin = Checkin(
        id=str(uuid4()),
        customer_id=customer.id,
        store_id=store.id,
        status=CheckinStatus.CHECKED_IN.value,
        checked_in_at=now,
        updated_at=now,
    )
    db.add(checkin)
    db.commit()

    return CheckinCreateResponse(
        checkin_id=checkin.id,
        store=to_store(store),
        customer={"customer_id": customer.id, "display_name": customer.name},
        status=checkin.status,
        checked_in_at=checkin.checked_in_at,
        purchase_count=customer.purchase_count,
        interest_count=len(customer.recently_viewed_product_ids),
    )


@router.post("/demo", response_model=CheckinCreateResponse, status_code=status.HTTP_201_CREATED)
def create_demo_checkin(
    request: Request,
    customer_id: CustomerId,
    db: DbSession,
) -> CheckinCreateResponse:
    """홈 버튼 시연을 위해 서버에 설정된 QR 태그로 동일한 체크인 계약을 실행한다."""
    # [Backend-13-'홈 데모 체크인'] 실제 QR 토큰은 프론트에 하드코딩하지 않고 서버 설정에서만 읽는다.
    return create_checkin(
        CheckinCreateRequest(tag_token=request.app.state.demo_qr_token),
        customer_id,
        db,
    )


@router.get("/{checkin_id}", response_model=CheckinResponse)
def get_checkin(checkin_id: str, customer_id: CustomerId, db: DbSession) -> CheckinResponse:
    return to_checkin_response(owned_checkin(checkin_id, customer_id, db), db)


@router.patch("/{checkin_id}/shopping-mode", response_model=ShoppingModeResponse)
def set_shopping_mode(
    checkin_id: str,
    body: ShoppingModeRequest,
    customer_id: CustomerId,
    db: DbSession,
) -> ShoppingModeResponse:
    checkin = owned_checkin(checkin_id, customer_id, db)
    if checkin.status != CheckinStatus.CHECKED_IN.value:
        raise DomainError(409, "CHECKIN_STATE_CONFLICT", "현재 상태에서는 쇼핑 방식을 바꿀 수 없습니다.")

    checkin.shopping_mode = body.shopping_mode.value
    if body.shopping_mode is ShoppingMode.PRIVATE:
        checkin.status = CheckinStatus.SELF_SHOPPING.value
        next_action = "VIEW_LOOKBOOK"
    else:
        next_action = "SUBMIT_CONSENT_AND_PURPOSE"
    checkin.updated_at = utc_now()
    db.commit()

    return ShoppingModeResponse(
        checkin_id=checkin.id,
        shopping_mode=checkin.shopping_mode,
        status=checkin.status,
        next_action=next_action,
    )


@router.post("/{checkin_id}/service-request", response_model=ServiceRequestResponse, status_code=status.HTTP_202_ACCEPTED)
def create_service_request(
    checkin_id: str,
    body: ServiceRequestCreate,
    request: Request,
    customer_id: CustomerId,
    db: DbSession,
) -> ServiceRequestResponse:
    checkin = owned_checkin(checkin_id, customer_id, db)
    if checkin.shopping_mode != ShoppingMode.STAFF_ASSISTED.value:
        raise DomainError(409, "CHECKIN_STATE_CONFLICT", "직원 응대 방식을 먼저 선택해야 합니다.")
    if checkin.status != CheckinStatus.CHECKED_IN.value:
        raise DomainError(409, "CHECKIN_STATE_CONFLICT", "현재 상태에서는 직원 요청을 만들 수 없습니다.")
    if not body.consent.agreed:
        raise DomainError(403, "PROFILE_SHARE_CONSENT_REQUIRED", "정보 공유 동의가 필요합니다.")

    now = utc_now()
    db.add(
        Consent(
            id=str(uuid4()),
            checkin_id=checkin.id,
            customer_id=customer_id,
            policy_version=body.consent.policy_version,
            scopes=body.consent.scopes,
            agreed_at=now,
        )
    )
    checkin.visit_purpose_code = body.visit_purpose.code.value
    checkin.visit_note = body.visit_purpose.note
    checkin.status = CheckinStatus.WAITING_FOR_STAFF.value
    checkin.updated_at = now
    db.commit()

    customer = db.get(Customer, customer_id)
    request.app.state.event_broker.publish(
        [f"staff:{checkin.store_id}"],
        "VISIT_WAITING",
        {
            "checkin_id": checkin.id,
            "customer_id": customer.id,
            "masked_name": f"{customer.name[0]}{'*' * max(2, len(customer.name) - 1)}",
            "membership": customer.membership,
            "visit_purpose": checkin.visit_purpose_code,
            "waiting_since": now,
            "ai_guide_status": "NOT_STARTED",
        },
    )

    return ServiceRequestResponse(
        checkin_id=checkin.id,
        status=checkin.status,
        ai_guide_status="NOT_STARTED",
        estimated_wait_minutes=3,
    )


@router.post("/{checkin_id}/consent/revoke", response_model=ConsentRevocationResponse)
def revoke_consent(
    checkin_id: str,
    request: Request,
    customer_id: CustomerId,
    db: DbSession,
) -> ConsentRevocationResponse:
    checkin = owned_checkin(checkin_id, customer_id, db)
    consent = db.scalar(select(Consent).where(Consent.checkin_id == checkin.id))
    if consent is None:
        raise DomainError(404, "CONSENT_NOT_FOUND", "철회할 정보 공유 동의를 찾을 수 없습니다.")
    if consent.revoked_at is not None:
        return ConsentRevocationResponse(
            checkin_id=checkin.id,
            consent_status="REVOKED",
            shopping_mode=checkin.shopping_mode,
            checkin_status=checkin.status,
            revoked_at=as_utc(consent.revoked_at),
        )

    now = utc_now()
    consent.revoked_at = now
    checkin.visit_note = None
    if checkin.status in {
        CheckinStatus.WAITING_FOR_STAFF.value,
        CheckinStatus.ASSIGNED.value,
        CheckinStatus.SERVING.value,
    }:
        checkin.shopping_mode = ShoppingMode.PRIVATE.value
        checkin.status = CheckinStatus.SELF_SHOPPING.value
        checkin.updated_at = now

    assignment = db.scalar(select(StaffAssignment).where(StaffAssignment.checkin_id == checkin.id))
    if assignment is not None and assignment.ended_at is None:
        assignment.ended_at = now

    recommendations = db.scalars(
        select(Recommendation).where(
            Recommendation.checkin_id == checkin.id,
            Recommendation.type == "STAFF_GUIDE",
        )
    ).all()
    for recommendation in recommendations:
        recommendation.status = "REVOKED"
        recommendation.output = None
        recommendation.error_code = "CONSENT_REVOKED"
        recommendation.updated_at = now
    record_audit(
        db,
        request,
        action="CONSENT_REVOKED",
        resource_type="CHECKIN",
        actor_id=customer_id,
        resource_id=checkin.id,
        metadata={"policy_version": consent.policy_version},
    )
    db.commit()

    response = ConsentRevocationResponse(
        checkin_id=checkin.id,
        consent_status="REVOKED",
        shopping_mode=checkin.shopping_mode,
        checkin_status=checkin.status,
        revoked_at=now,
    )
    request.app.state.event_broker.publish(
        [f"staff:{checkin.store_id}", f"customer:{checkin.customer_id}"],
        "CONSENT_REVOKED",
        response.model_dump(mode="json"),
    )
    return response


@router.post("/{checkin_id}/cancel", response_model=MessageResponse)
def cancel_checkin(
    checkin_id: str,
    request: Request,
    customer_id: CustomerId,
    db: DbSession,
) -> MessageResponse:
    checkin = owned_checkin(checkin_id, customer_id, db)
    if checkin.status not in ACTIVE_STATUSES:
        raise DomainError(409, "CHECKIN_STATE_CONFLICT", "이미 종료된 체크인입니다.")
    checkin.status = CheckinStatus.CANCELLED.value
    checkin.updated_at = utc_now()
    checkin.completed_at = checkin.updated_at
    assignment = db.scalar(select(StaffAssignment).where(StaffAssignment.checkin_id == checkin.id))
    if assignment is not None:
        assignment.ended_at = checkin.updated_at
    db.commit()
    request.app.state.event_broker.publish(
        [f"staff:{checkin.store_id}", f"customer:{checkin.customer_id}"],
        "VISIT_CANCELLED",
        {"checkin_id": checkin.id, "status": checkin.status},
    )
    return MessageResponse(message="체크인이 취소되었습니다.")
