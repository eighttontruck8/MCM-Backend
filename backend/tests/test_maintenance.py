from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.database import Database
from app.maintenance import PurgePolicy, purge_expired_data
from app.models import AuditLog, Checkin, PasswordResetToken, Recommendation, RefreshToken


def _checkin(checkin_id: str, *, status: str, updated_at: datetime) -> Checkin:
    return Checkin(
        id=checkin_id,
        customer_id="C001",
        store_id="S001",
        shopping_mode="PRIVATE",
        visit_purpose_code="GIFT",
        visit_note="생일 선물 상담",
        status=status,
        checked_in_at=updated_at - timedelta(hours=1),
        updated_at=updated_at,
        completed_at=updated_at if status == "COMPLETED" else None,
    )


def test_purge_dry_run_and_execute_respect_retention_boundaries() -> None:
    now = datetime(2026, 8, 16, tzinfo=UTC)
    old = now - timedelta(days=100)
    recent = now - timedelta(days=10)
    database = Database("sqlite+pysqlite:///:memory:")
    database.create_schema()

    try:
        with database.session_factory.begin() as session:
            session.add_all(
                [
                    _checkin("old-terminal", status="COMPLETED", updated_at=old),
                    _checkin("recent-terminal", status="COMPLETED", updated_at=recent),
                    _checkin("old-active", status="SELF_SHOPPING", updated_at=old),
                    Recommendation(
                        id="old-recommendation",
                        checkin_id="old-terminal",
                        customer_id="C001",
                        type="LOOKBOOK",
                        status="READY",
                        input_hash="old-hash",
                        output={"title": "민감한 추천 결과"},
                        error_code=None,
                        created_at=old,
                        updated_at=old,
                    ),
                    Recommendation(
                        id="recent-recommendation",
                        checkin_id="recent-terminal",
                        customer_id="C001",
                        type="LOOKBOOK",
                        status="READY",
                        input_hash="recent-hash",
                        output={"title": "최근 추천 결과"},
                        error_code=None,
                        created_at=recent,
                        updated_at=recent,
                    ),
                    RefreshToken(
                        id="expired-refresh",
                        user_id="C001",
                        token_hash="expired-refresh-hash",
                        expires_at=now - timedelta(days=8),
                        revoked_at=None,
                    ),
                    RefreshToken(
                        id="recent-refresh",
                        user_id="C001",
                        token_hash="recent-refresh-hash",
                        expires_at=now - timedelta(days=2),
                        revoked_at=now - timedelta(days=1),
                    ),
                    PasswordResetToken(
                        id="expired-reset",
                        user_id="C001",
                        token_hash="expired-reset-hash",
                        expires_at=now - timedelta(days=8),
                        used_at=None,
                        created_at=old,
                    ),
                    AuditLog(
                        id="expired-audit",
                        actor_id="C001",
                        action="TEST",
                        resource_type="CHECKIN",
                        resource_id="old-terminal",
                        request_id=None,
                        metadata_json={},
                        created_at=now - timedelta(days=366),
                    ),
                ]
            )

        policy = PurgePolicy(visit_personal_data_days=90, expired_auth_token_days=7, audit_log_days=365)
        with database.session_factory.begin() as session:
            dry_run = purge_expired_data(session, policy=policy, now=now)

        assert dry_run.dry_run is True
        assert dry_run.visit_payloads == 1
        assert dry_run.recommendation_payloads == 1
        assert dry_run.refresh_tokens == 1
        assert dry_run.password_reset_tokens == 1
        assert dry_run.audit_logs == 1

        with database.session_factory.begin() as session:
            old_checkin = session.get(Checkin, "old-terminal")
            assert old_checkin is not None and old_checkin.visit_note == "생일 선물 상담"
            executed = purge_expired_data(session, policy=policy, now=now, dry_run=False)

        assert executed.dry_run is False
        with database.session_factory() as session:
            old_checkin = session.get(Checkin, "old-terminal")
            recent_checkin = session.get(Checkin, "recent-terminal")
            active_checkin = session.get(Checkin, "old-active")
            old_recommendation = session.get(Recommendation, "old-recommendation")
            recent_recommendation = session.get(Recommendation, "recent-recommendation")
            assert old_checkin is not None
            assert old_checkin.visit_note is None and old_checkin.visit_purpose_code is None
            assert recent_checkin is not None and recent_checkin.visit_note is not None
            assert active_checkin is not None and active_checkin.visit_note is not None
            assert old_recommendation is not None
            assert old_recommendation.output is None
            assert old_recommendation.status == "REVOKED"
            assert old_recommendation.error_code == "PERSONAL_DATA_PURGED"
            assert recent_recommendation is not None and recent_recommendation.output is not None
            assert session.get(RefreshToken, "expired-refresh") is None
            assert session.get(RefreshToken, "recent-refresh") is not None
            assert session.get(PasswordResetToken, "expired-reset") is None
            assert session.get(AuditLog, "expired-audit") is None
            assert len(session.scalars(select(Checkin)).all()) == 3
    finally:
        database.dispose()
