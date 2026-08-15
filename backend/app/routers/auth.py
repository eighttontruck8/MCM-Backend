from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.audit import record_audit
from app.database import get_db
from app.dependencies import AuthenticatedUser, current_user
from app.errors import DomainError
from app.models import PasswordResetToken, RefreshToken, Staff, User
from app.schemas import (
    AuthUserResponse,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RefreshRequest,
    TokenResponse,
    UserRole,
)
from app.security import TokenError, create_token, decode_token, hash_password, token_hash, verify_password
from app.rate_limit import rate_limit_key


router = APIRouter(prefix="/api/v1", tags=["auth"])
mailer_logger = logging.getLogger("mjourney.mail")
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
    access_token, _, _ = create_token(secret=request.app.state.jwt_secret, subject=user.id, role=user.role, store_id=staff.store_id if staff else None, token_type="access", expires_delta=timedelta(minutes=access_minutes), auth_version=user.auth_version)
    refresh_token, refresh_id, refresh_expires_at = create_token(secret=request.app.state.jwt_secret, subject=user.id, role=user.role, store_id=staff.store_id if staff else None, token_type="refresh", expires_delta=timedelta(days=refresh_days), auth_version=user.auth_version)
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
    request.app.state.rate_limiter.enforce(
        rate_limit_key("login", request.client.host if request.client else None, body.email),
        limit=request.app.state.rate_limits["login"],
        window_seconds=request.app.state.rate_limit_window_seconds,
    )
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        record_audit(
            db,
            request,
            action="AUTH_LOGIN_FAILED",
            resource_type="USER",
            actor_id=user.id if user else None,
            resource_id=user.id if user else None,
            metadata={"outcome": "DENIED"},
        )
        db.commit()
        raise DomainError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다.")
    record_audit(
        db,
        request,
        action="AUTH_LOGIN_SUCCEEDED",
        resource_type="USER",
        actor_id=user.id,
        resource_id=user.id,
        metadata={"role": user.role},
    )
    return issue_tokens(user, request, db)


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, request: Request, db: DbSession) -> TokenResponse:
    payload, stored = stored_refresh_token(body.refresh_token, request, db)
    user = db.get(User, payload["sub"])
    if user is None or not user.is_active or user.role != payload["role"] or payload.get("ver", 0) != user.auth_version:
        raise DomainError(401, "INVALID_REFRESH_TOKEN", "유효하지 않은 Refresh Token입니다.")
    stored.revoked_at = utc_now()
    return issue_tokens(user, request, db)


@router.post("/auth/logout", response_model=MessageResponse)
def logout(body: LogoutRequest, request: Request, db: DbSession) -> MessageResponse:
    payload, stored = stored_refresh_token(body.refresh_token, request, db)
    stored.revoked_at = utc_now()
    record_audit(
        db,
        request,
        action="AUTH_LOGOUT",
        resource_type="USER",
        actor_id=payload["sub"],
        resource_id=payload["sub"],
    )
    db.commit()
    return MessageResponse(message="로그아웃되었습니다.")


@router.post(
    "/auth/password-reset/request",
    response_model=PasswordResetRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def request_password_reset(
    body: PasswordResetRequest,
    request: Request,
    db: DbSession,
) -> PasswordResetRequestResponse:
    request.app.state.rate_limiter.enforce(
        rate_limit_key("password_reset", request.client.host if request.client else None, body.email),
        limit=request.app.state.rate_limits["password_reset"],
        window_seconds=request.app.state.rate_limit_window_seconds,
    )
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    raw_token = None
    if user is not None and user.is_active:
        now = utc_now()
        db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(used_at=now)
        )
        raw_token = secrets.token_urlsafe(48)
        db.add(
            PasswordResetToken(
                id=secrets.token_hex(16),
                user_id=user.id,
                token_hash=token_hash(raw_token),
                expires_at=now + timedelta(minutes=request.app.state.password_reset_expire_minutes),
                created_at=now,
            )
        )
    record_audit(
        db,
        request,
        action="PASSWORD_RESET_REQUESTED",
        resource_type="USER",
        actor_id=user.id if user else None,
        resource_id=user.id if user else None,
        metadata={"account_matched": user is not None and user.is_active},
    )
    db.commit()
    if raw_token is not None and user is not None:
        reset_url = f"{request.app.state.frontend_base_url}/reset-password?token={quote(raw_token, safe='')}"
        try:
            # [Backend-03-'SMTP 비밀번호 재설정 메일'] 토큰은 메일 본문에만 포함하고 로그에는 남기지 않는다.
            request.app.state.password_reset_mailer.send_password_reset(
                user.email,
                reset_url,
                request.app.state.password_reset_expire_minutes,
            )
        except Exception:
            mailer_logger.exception("비밀번호 재설정 메일 발송에 실패했습니다.")
    return PasswordResetRequestResponse(
        message="계정이 존재하면 비밀번호 재설정 안내가 전송됩니다.",
        reset_token=(
            raw_token
            if raw_token is not None and request.app.state.expose_password_reset_token
            else None
        ),
    )


@router.post("/auth/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(
    body: PasswordResetConfirmRequest,
    request: Request,
    db: DbSession,
) -> MessageResponse:
    reset_token = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash(body.reset_token)
        )
    )
    if (
        reset_token is None
        or reset_token.used_at is not None
        or as_utc(reset_token.expires_at) <= utc_now()
    ):
        raise DomainError(400, "INVALID_PASSWORD_RESET_TOKEN", "유효하지 않거나 만료된 재설정 토큰입니다.")
    user = db.get(User, reset_token.user_id)
    if user is None or not user.is_active:
        raise DomainError(400, "INVALID_PASSWORD_RESET_TOKEN", "유효하지 않거나 만료된 재설정 토큰입니다.")
    if verify_password(body.new_password, user.password_hash):
        raise DomainError(409, "PASSWORD_REUSE_NOT_ALLOWED", "기존 비밀번호와 다른 비밀번호를 사용해주세요.")

    now = utc_now()
    user.password_hash = hash_password(body.new_password)
    user.auth_version += 1
    user.updated_at = now
    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    record_audit(
        db,
        request,
        action="PASSWORD_RESET_COMPLETED",
        resource_type="USER",
        actor_id=user.id,
        resource_id=user.id,
    )
    db.commit()
    return MessageResponse(message="비밀번호가 변경되었습니다. 다시 로그인해주세요.")


@router.get("/me", response_model=AuthUserResponse)
def me(authenticated: CurrentUser) -> AuthUserResponse:
    return AuthUserResponse(id=authenticated.id, role=authenticated.role, display_name=authenticated.display_name, store_id=authenticated.store_id)
