from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.config import load_settings
from app.database import Database
from app.models import AuditLog, Checkin, PasswordResetToken, Recommendation, RefreshToken


@dataclass(frozen=True, slots=True)
class PurgePolicy:
    visit_personal_data_days: int
    expired_auth_token_days: int
    audit_log_days: int


@dataclass(frozen=True, slots=True)
class PurgeResult:
    dry_run: bool
    visit_payloads: int
    recommendation_payloads: int
    refresh_tokens: int
    password_reset_tokens: int
    audit_logs: int


def _count(session: Session, model: type, *conditions: object) -> int:
    return int(session.scalar(select(func.count()).select_from(model).where(*conditions)) or 0)


def purge_expired_data(
    session: Session,
    *,
    policy: PurgePolicy,
    now: datetime | None = None,
    dry_run: bool = True,
) -> PurgeResult:
    """보존 기간이 지난 민감 payload와 만료된 보안 레코드를 정리한다."""
    # [Backend-05-'개인정보 보존 및 purge'] 감사용 행은 유지하고 자유 입력·AI 출력만 비식별화한다.
    current_time = now or datetime.now(UTC)
    visit_cutoff = current_time - timedelta(days=policy.visit_personal_data_days)
    auth_cutoff = current_time - timedelta(days=policy.expired_auth_token_days)
    audit_cutoff = current_time - timedelta(days=policy.audit_log_days)

    terminal_visit = (
        Checkin.status.in_(("COMPLETED", "CANCELLED")),
        Checkin.updated_at < visit_cutoff,
    )
    visit_payload_condition = (
        *terminal_visit,
        or_(Checkin.visit_note.is_not(None), Checkin.visit_purpose_code.is_not(None)),
    )
    recommendation_condition = (
        Recommendation.checkin_id.in_(select(Checkin.id).where(*terminal_visit)),
        Recommendation.output.is_not(None),
    )
    refresh_condition = (RefreshToken.expires_at < auth_cutoff,)
    reset_condition = (PasswordResetToken.expires_at < auth_cutoff,)
    audit_condition = (AuditLog.created_at < audit_cutoff,)

    result = PurgeResult(
        dry_run=dry_run,
        visit_payloads=_count(session, Checkin, *visit_payload_condition),
        recommendation_payloads=_count(session, Recommendation, *recommendation_condition),
        refresh_tokens=_count(session, RefreshToken, *refresh_condition),
        password_reset_tokens=_count(session, PasswordResetToken, *reset_condition),
        audit_logs=_count(session, AuditLog, *audit_condition),
    )
    if dry_run:
        return result

    session.execute(
        update(Checkin)
        .where(*visit_payload_condition)
        .values(visit_note=None, visit_purpose_code=None)
        .execution_options(synchronize_session=False)
    )
    session.execute(
        update(Recommendation)
        .where(*recommendation_condition)
        .values(output=None, status="REVOKED", error_code="PERSONAL_DATA_PURGED", updated_at=current_time)
        .execution_options(synchronize_session=False)
    )
    session.execute(delete(RefreshToken).where(*refresh_condition))
    session.execute(delete(PasswordResetToken).where(*reset_condition))
    session.execute(delete(AuditLog).where(*audit_condition))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="M-Journey 만료 개인정보 정리")
    parser.add_argument("--execute", action="store_true", help="실제로 변경한다. 생략하면 dry-run만 수행한다.")
    args = parser.parse_args()
    settings = load_settings()
    policy = PurgePolicy(
        visit_personal_data_days=settings.visit_personal_data_retention_days,
        expired_auth_token_days=settings.expired_auth_token_retention_days,
        audit_log_days=settings.audit_log_retention_days,
    )
    database = Database(settings.database_url)
    try:
        with database.session_factory.begin() as session:
            result = purge_expired_data(session, policy=policy, dry_run=not args.execute)
        print(json.dumps(asdict(result), ensure_ascii=False))
    finally:
        database.dispose()


if __name__ == "__main__":
    main()
