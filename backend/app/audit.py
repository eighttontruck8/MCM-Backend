from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import AuditLog


def record_audit(
    db: Session,
    request: Request,
    *,
    action: str,
    resource_type: str,
    actor_id: str | None = None,
    resource_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            id=str(uuid4()),
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=getattr(request.state, "request_id", None),
            metadata_json=metadata or {},
            created_at=datetime.now(timezone.utc),
        )
    )
