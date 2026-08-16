from __future__ import annotations

import pytest

from app.config import load_settings
from app.deployment import validate_production_deployment


def _production_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("M_JOURNEY_ENVIRONMENT", "production")
    monkeypatch.setenv("M_JOURNEY_DATABASE_URL", "postgresql+psycopg://user:strong-db-password@db.prod/mjourney")
    monkeypatch.setenv("M_JOURNEY_FRONTEND_BASE_URL", "https://app.mjourney.test")
    monkeypatch.setenv("M_JOURNEY_CORS_ORIGINS", "https://app.mjourney.test,https://staff.mjourney.test")
    monkeypatch.setenv("M_JOURNEY_AUTO_CREATE_SCHEMA", "false")
    return load_settings()


def test_production_preflight_masks_qr_token_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _production_settings(monkeypatch)

    result = validate_production_deployment(
        settings,
        public_api_base_url="https://api.mjourney.test/",
        jwt_secret="jwt-secret-with-at-least-thirty-two-characters",
        demo_password="strong-demo-password",
        demo_qr_token="production-qr-token-with-enough-entropy",
    )

    assert result.public_api_base_url == "https://api.mjourney.test"
    assert result.frontend_base_url == "https://app.mjourney.test"
    assert result.database == "postgresql+psycopg"
    assert result.qr_entry_url == "https://api.mjourney.test/entry/<hidden>"


def test_production_preflight_can_explicitly_show_qr_url(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _production_settings(monkeypatch)

    result = validate_production_deployment(
        settings,
        public_api_base_url="https://api.mjourney.test",
        jwt_secret="jwt-secret-with-at-least-thirty-two-characters",
        demo_password="strong-demo-password",
        demo_qr_token="production-qr-token-with-enough-entropy",
        show_qr_url=True,
    )

    assert result.qr_entry_url.endswith("/entry/production-qr-token-with-enough-entropy")


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"public_api_base_url": "http://api.mjourney.test"}, "HTTPS origin"),
        ({"public_api_base_url": "https://api.example.com"}, "실제 배포 도메인"),
        ({"jwt_secret": "short"}, "JWT_SECRET"),
        ({"demo_password": "short"}, "DEMO_PASSWORD"),
        ({"demo_qr_token": "qr-demo-seoul-001-7f4d0b9e8c2a"}, "DEMO_QR_TOKEN"),
    ],
)
def test_production_preflight_rejects_unsafe_values(
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, str],
    message: str,
) -> None:
    settings = _production_settings(monkeypatch)
    values = {
        "public_api_base_url": "https://api.mjourney.test",
        "jwt_secret": "jwt-secret-with-at-least-thirty-two-characters",
        "demo_password": "strong-demo-password",
        "demo_qr_token": "production-qr-token-with-enough-entropy",
    }
    values.update(overrides)

    with pytest.raises(ValueError, match=message):
        validate_production_deployment(settings, **values)
