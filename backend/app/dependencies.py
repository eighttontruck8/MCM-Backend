from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import DomainError
from app.models import Staff, User
from app.schemas import UserRole
from app.security import TokenError, decode_token


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: str
    role: UserRole
    display_name: str
    store_id: str | None = None


def current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise DomainError(401, "AUTHENTICATION_REQUIRED", "Bearer 인증 토큰이 필요합니다.")
    try:
        payload = decode_token(credentials.credentials, request.app.state.jwt_secret, "access")
        role = UserRole(payload["role"])
    except (TokenError, ValueError):
        raise DomainError(401, "INVALID_ACCESS_TOKEN", "유효하지 않은 인증 토큰입니다.") from None
    user = db.get(User, payload["sub"])
    if user is None or not user.is_active or user.role != role.value:
        raise DomainError(401, "INVALID_ACCESS_TOKEN", "유효하지 않은 인증 토큰입니다.")
    staff = db.get(Staff, user.id) if role is UserRole.STAFF else None
    return AuthenticatedUser(
        id=user.id,
        role=role,
        display_name=user.display_name,
        store_id=staff.store_id if staff else None,
    )


def current_customer(user: Annotated[AuthenticatedUser, Depends(current_user)]) -> AuthenticatedUser:
    if user.role is not UserRole.CUSTOMER:
        raise DomainError(403, "CUSTOMER_ROLE_REQUIRED", "고객 권한이 필요합니다.")
    return user


def current_customer_id(user: Annotated[AuthenticatedUser, Depends(current_customer)]) -> str:
    return user.id


def current_staff(user: Annotated[AuthenticatedUser, Depends(current_user)]) -> AuthenticatedUser:
    if user.role is not UserRole.STAFF:
        raise DomainError(403, "STAFF_ROLE_REQUIRED", "직원 권한이 필요합니다.")
    return user
