from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import AuthenticatedUser, current_user
from app.errors import DomainError
from app.models import RefreshToken, Staff, User
from app.schemas import AuthUserResponse, LoginRequest, LogoutRequest, MessageResponse, RefreshRequest, TokenResponse, UserRole
from app.security import TokenError, create_token, decode_token, token_hash, verify_password


router = APIRouter(prefix="/api/v1", tags=["auth"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[AuthenticatedUser, Depends(current_user)]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def user_response(user: User, staff: Staff | None) -> AuthUserResponse:
    return AuthUserResponse(id=user.id, role=user.role, display_name=user.display_name, store_id=staff.store_id if staff else None)


def issue_tokens(user: User, request: Request, db: Session) -> TokenResponse:
    staff = db.get(Staff, user.id) if user.role == UserRole.STAFF.value else None
    access_minutes = request.app.state.access_token_expire_minutes
    refresh_days = request.app.state.refresh_token_expire_days
    access_token, _, _ = create_token(secret=request.app.state.jwt_secret, subject=user.id, role=user.role, store_id=staff.store_id if staff else None, token_type="access", expires_delta=timedelta(minutes=access_minutes))
    refresh_token, refresh_id, refresh_expires_at = create_token(secret=request.app.state.jwt_secret, subject=user.id, role=user.role, store_id=staff.store_id if staff else None, token_type="refresh", expires_delta=timedelta(days=refresh_days))
    db.add(RefreshToken(id=refresh_id, user_id=user.id, token_hash=token_hash(refresh_token), expires_at=refresh_expires_at))
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, expires_in=access_minutes * 60, user=user_response(user, staff))


def stored_refresh_token(raw_token: str, request: Request, db: Session) -> tuple[dict, RefreshToken]:
    try:
        payload = decode_token(raw_token, request.app.state.jwt_secret, "refresh")
    except TokenError:
        raise DomainError(401, "INVALID_REFRESH_TOKEN", "유효하지 않은 Refresh Token입니다.") from None
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash(raw_token)))
    if stored is None or stored.id != payload["jti"] or stored.user_id != payload["sub"] or stored.revoked_at is not None or as_utc(stored.expires_at) <= utc_now():
        raise DomainError(401, "INVALID_REFRESH_TOKEN", "유효하지 않은 Refresh Token입니다.")
    return payload, stored


@router.post("/auth/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        raise DomainError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다.")
    return issue_tokens(user, request, db)


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, request: Request, db: DbSession) -> TokenResponse:
    payload, stored = stored_refresh_token(body.refresh_token, request, db)
    user = db.get(User, payload["sub"])
    if user is None or not user.is_active or user.role != payload["role"]:
        raise DomainError(401, "INVALID_REFRESH_TOKEN", "유효하지 않은 Refresh Token입니다.")
    stored.revoked_at = utc_now()
    return issue_tokens(user, request, db)


@router.post("/auth/logout", response_model=MessageResponse)
def logout(body: LogoutRequest, request: Request, db: DbSession) -> MessageResponse:
    _, stored = stored_refresh_token(body.refresh_token, request, db)
    stored.revoked_at = utc_now()
    db.commit()
    return MessageResponse(message="로그아웃되었습니다.")


@router.get("/me", response_model=AuthUserResponse)
def me(authenticated: CurrentUser) -> AuthUserResponse:
    return AuthUserResponse(id=authenticated.id, role=authenticated.role, display_name=authenticated.display_name, store_id=authenticated.store_id)
