from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import DomainError
from app.mappers import to_store
from app.models import EntryTag, Store
from app.schemas import EntryTagResponse


router = APIRouter(tags=["store-entry"])


def valid_entry_tag(tag_token: str, db: Session) -> tuple[EntryTag, Store]:
    entry_tag = db.get(EntryTag, tag_token)
    if entry_tag is None or not entry_tag.is_active:
        raise DomainError(400, "INVALID_ENTRY_TAG", "유효하지 않은 매장 진입 태그입니다.")
    store = db.get(Store, entry_tag.store_id)
    if store is None or not store.is_active:
        raise DomainError(400, "STORE_UNAVAILABLE", "현재 체크인할 수 없는 매장입니다.")
    return entry_tag, store


def frontend_checkin_url(request: Request, tag_token: str) -> str:
    query = urlencode({"tag_token": tag_token})
    return f"{request.app.state.frontend_base_url}/check-in?{query}"


@router.get("/api/v1/entry-tags/{tag_token}", response_model=EntryTagResponse)
def get_entry_tag(
    tag_token: str,
    request: Request,
    db: Session = Depends(get_db),
) -> EntryTagResponse:
    entry_tag, store = valid_entry_tag(tag_token, db)
    return EntryTagResponse(
        tag_token=entry_tag.token,
        channel=entry_tag.channel,
        store=to_store(store),
        checkin_url=frontend_checkin_url(request, entry_tag.token),
    )


@router.get("/entry/{tag_token}", include_in_schema=False)
def enter_store(
    tag_token: str,
    request: Request,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    entry_tag, _ = valid_entry_tag(tag_token, db)
    return RedirectResponse(frontend_checkin_url(request, entry_tag.token), status_code=307)
