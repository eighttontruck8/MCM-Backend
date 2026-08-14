from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import AuthenticatedUser, current_staff
from app.errors import DomainError
from app.models import Checkin, Consent, Customer, Staff, StaffAssignment, User
from app.schemas import (
    CheckinStatus,
    StaffAssignmentResponse,
    StaffCustomerResponse,
    StaffStatusRequest,
    StaffSummaryResponse,
    StaffVisitListResponse,
    StaffVisitResponse,
)


router = APIRouter(prefix="/api/v1/staff", tags=["staff"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentStaff = Annotated[AuthenticatedUser, Depends(current_staff)]
STAFF_ACTIVE_STATUSES = {
    CheckinStatus.WAITING_FOR_STAFF.value,
    CheckinStatus.ASSIGNED.value,
    CheckinStatus.SERVING.value,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def mask_name(name: str) -> str:
    if not name:
        return "**"
    return f"{name[0]}{'*' * max(2, len(name) - 1)}"


def require_staff_store(authenticated: AuthenticatedUser, store_id: str) -> None:
    if authenticated.store_id != store_id:
        raise DomainError(403, "STAFF_STORE_ACCESS_DENIED", "소속 매장의 정보만 조회할 수 있습니다.")


def staff_summary(staff: Staff, user: User) -> StaffSummaryResponse:
    return StaffSummaryResponse(staff_id=staff.id, name=user.display_name, title=staff.title, experience_years=staff.experience_years)


@router.get("/stores/{store_id}/visits", response_model=StaffVisitListResponse)
def list_visits(
    store_id: str,
    authenticated: CurrentStaff,
    db: DbSession,
    visit_status: CheckinStatus = Query(default=CheckinStatus.WAITING_FOR_STAFF, alias="status"),
) -> StaffVisitListResponse:
    require_staff_store(authenticated, store_id)
    if visit_status.value not in STAFF_ACTIVE_STATUSES:
        raise DomainError(400, "INVALID_VISIT_STATUS", "직원 대기열에서 조회할 수 없는 상태입니다.")
    rows = db.execute(
        select(Checkin, Customer)
        .join(Customer, Customer.id == Checkin.customer_id)
        .where(Checkin.store_id == store_id, Checkin.status == visit_status.value)
        .order_by(Checkin.checked_in_at)
    ).all()
    return StaffVisitListResponse(
        items=[
            StaffVisitResponse(
                checkin_id=checkin.id,
                customer_id=customer.id,
                masked_name=mask_name(customer.name),
                membership=customer.membership,
                visit_purpose=checkin.visit_purpose_code,
                waiting_since=checkin.updated_at,
                ai_guide_status="NOT_STARTED",
            )
            for checkin, customer in rows
        ]
    )


@router.post("/check-ins/{checkin_id}/claim", response_model=StaffAssignmentResponse)
def claim_checkin(checkin_id: str, request: Request, authenticated: CurrentStaff, db: DbSession) -> StaffAssignmentResponse:
    now = utc_now()
    result = db.execute(
        update(Checkin)
        .where(
            Checkin.id == checkin_id,
            Checkin.store_id == authenticated.store_id,
            Checkin.status == CheckinStatus.WAITING_FOR_STAFF.value,
        )
        .values(status=CheckinStatus.ASSIGNED.value, updated_at=now)
    )
    if result.rowcount != 1:
        checkin = db.get(Checkin, checkin_id)
        if checkin is None:
            raise DomainError(404, "CHECKIN_NOT_FOUND", "체크인을 찾을 수 없습니다.")
        if checkin.store_id != authenticated.store_id:
            raise DomainError(403, "STAFF_STORE_ACCESS_DENIED", "소속 매장의 체크인만 수락할 수 있습니다.")
        if db.scalar(select(StaffAssignment).where(StaffAssignment.checkin_id == checkin_id)) is not None:
            raise DomainError(409, "ALREADY_ASSIGNED", "이미 다른 직원이 수락한 방문입니다.")
        raise DomainError(409, "CHECKIN_STATE_CONFLICT", "현재 상태에서는 방문을 수락할 수 없습니다.")

    assignment = StaffAssignment(id=str(uuid4()), checkin_id=checkin_id, staff_id=authenticated.id, assigned_at=now)
    db.add(assignment)
    staff = db.get(Staff, authenticated.id)
    user = db.get(User, authenticated.id)
    if staff is None or user is None:
        raise DomainError(403, "STAFF_PROFILE_NOT_FOUND", "직원 정보를 찾을 수 없습니다.")
    db.commit()
    response = StaffAssignmentResponse(checkin_id=checkin_id, status=CheckinStatus.ASSIGNED, staff=staff_summary(staff, user), assigned_at=now)
    checkin = db.get(Checkin, checkin_id)
    request.app.state.event_broker.publish(
        [f"staff:{checkin.store_id}", f"customer:{checkin.customer_id}"],
        "STAFF_ASSIGNED",
        response.model_dump(mode="json"),
    )
    return response


@router.patch("/check-ins/{checkin_id}/status", response_model=StaffAssignmentResponse)
def update_visit_status(checkin_id: str, body: StaffStatusRequest, request: Request, authenticated: CurrentStaff, db: DbSession) -> StaffAssignmentResponse:
    assignment = db.scalar(select(StaffAssignment).where(StaffAssignment.checkin_id == checkin_id))
    checkin = db.get(Checkin, checkin_id)
    if checkin is None:
        raise DomainError(404, "CHECKIN_NOT_FOUND", "체크인을 찾을 수 없습니다.")
    if checkin.store_id != authenticated.store_id:
        raise DomainError(403, "STAFF_STORE_ACCESS_DENIED", "소속 매장의 체크인만 변경할 수 있습니다.")
    if assignment is None or assignment.staff_id != authenticated.id:
        raise DomainError(403, "ASSIGNED_STAFF_REQUIRED", "배정된 직원만 방문 상태를 변경할 수 있습니다.")
    allowed = {
        CheckinStatus.ASSIGNED.value: CheckinStatus.SERVING,
        CheckinStatus.SERVING.value: CheckinStatus.COMPLETED,
    }
    if allowed.get(checkin.status) is not body.status:
        raise DomainError(409, "CHECKIN_STATE_CONFLICT", "허용되지 않은 방문 상태 변경입니다.")
    now = utc_now()
    checkin.status = body.status.value
    checkin.updated_at = now
    if body.status is CheckinStatus.COMPLETED:
        checkin.completed_at = now
        assignment.ended_at = now
    staff = db.get(Staff, authenticated.id)
    user = db.get(User, authenticated.id)
    db.commit()
    response = StaffAssignmentResponse(checkin_id=checkin.id, status=body.status, staff=staff_summary(staff, user), assigned_at=assignment.assigned_at)
    if body.status is CheckinStatus.COMPLETED:
        request.app.state.event_broker.publish(
            [f"staff:{checkin.store_id}", f"customer:{checkin.customer_id}"],
            "VISIT_COMPLETED",
            {"checkin_id": checkin.id, "status": checkin.status, "completed_at": checkin.completed_at},
        )
    return response


@router.get("/customers/{customer_id}", response_model=StaffCustomerResponse, response_model_exclude_none=True)
def get_customer(customer_id: str, authenticated: CurrentStaff, db: DbSession) -> StaffCustomerResponse:
    row = db.execute(
        select(Checkin, Customer, Consent)
        .join(Customer, Customer.id == Checkin.customer_id)
        .join(Consent, Consent.checkin_id == Checkin.id)
        .where(
            Checkin.customer_id == customer_id,
            Checkin.store_id == authenticated.store_id,
            Checkin.status.in_(STAFF_ACTIVE_STATUSES),
            Consent.revoked_at.is_(None),
        )
    ).first()
    if row is None:
        raise DomainError(403, "STAFF_CUSTOMER_ACCESS_DENIED", "활성 방문과 정보 공유 동의가 필요합니다.")
    checkin, customer, consent = row
    style_allowed = "STYLE_PROFILE" in consent.scopes
    purchase_allowed = "PURCHASE_HISTORY" in consent.scopes
    return StaffCustomerResponse(
        customer_id=customer.id,
        masked_name=mask_name(customer.name),
        membership=customer.membership,
        visit_count=customer.visit_count,
        visit_purpose=checkin.visit_purpose_code,
        preferred_colors=customer.preferred_colors if style_allowed else None,
        preferred_style=customer.preferred_style if style_allowed else None,
        recently_viewed_product_ids=customer.recently_viewed_product_ids if style_allowed else None,
        liked_product_ids=customer.liked_product_ids if style_allowed else None,
        purchase_count=customer.purchase_count if purchase_allowed else None,
    )
