from __future__ import annotations

from typing import Annotated

from fastapi import Header

from app.errors import DomainError


def current_customer_id(
    x_customer_id: Annotated[str | None, Header(alias="X-Customer-ID")] = None,
) -> str:
    if not x_customer_id:
        raise DomainError(401, "AUTHENTICATION_REQUIRED", "X-Customer-ID 헤더가 필요합니다.")
    return x_customer_id
