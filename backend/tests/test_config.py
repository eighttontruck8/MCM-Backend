from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import load_settings
from app.main import create_app


def test_cors_preflight_allows_only_configured_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("M_JOURNEY_CORS_ORIGINS", "https://shop.example.com/")
    app = create_app(
        "sqlite+pysqlite:///:memory:",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        auto_create_schema=True,
        seed_demo_data=False,
    )

    with TestClient(app) as client:
        allowed = client.options(
            "/health/live",
            headers={
                "Origin": "https://shop.example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization,X-Request-ID",
            },
        )
        denied = client.options(
            "/health/live",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
        )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "https://shop.example.com"
    assert allowed.headers["access-control-allow-credentials"] == "true"
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers


@pytest.mark.parametrize(
    "origins,frontend",
    [
        ("*", "https://shop.example.com"),
        ("http://localhost:5173", "http://localhost:5173"),
        ("https://shop.example.com/path", "https://shop.example.com"),
        ("https://shop.example.com", "https://other.example.com"),
    ],
)
def test_production_rejects_unsafe_cors_configuration(
    monkeypatch: pytest.MonkeyPatch,
    origins: str,
    frontend: str,
) -> None:
    monkeypatch.setenv("M_JOURNEY_ENVIRONMENT", "production")
    monkeypatch.setenv("M_JOURNEY_CORS_ORIGINS", origins)
    monkeypatch.setenv("M_JOURNEY_FRONTEND_BASE_URL", frontend)

    with pytest.raises(ValueError):
        load_settings()


def test_production_accepts_https_frontend_whitelist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("M_JOURNEY_ENVIRONMENT", "production")
    monkeypatch.setenv(
        "M_JOURNEY_CORS_ORIGINS",
        "https://shop.example.com, https://staff.example.com,https://shop.example.com/",
    )
    monkeypatch.setenv("M_JOURNEY_FRONTEND_BASE_URL", "https://shop.example.com/")

    settings = load_settings()

    assert settings.cors_origins == ("https://shop.example.com", "https://staff.example.com")


def test_openai_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("M_JOURNEY_AI_PROVIDER", "openai")
    monkeypatch.delenv("M_JOURNEY_OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="M_JOURNEY_OPENAI_API_KEY"):
        load_settings()


def test_openai_provider_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("M_JOURNEY_AI_PROVIDER", "openai")
    monkeypatch.setenv("M_JOURNEY_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("M_JOURNEY_OPENAI_MODEL", "gpt-4o-mini")

    settings = load_settings()

    assert settings.ai_provider == "openai"
    assert settings.openai_api_key == "test-key"
    assert settings.openai_model == "gpt-4o-mini"


def test_retention_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("M_JOURNEY_VISIT_PERSONAL_DATA_RETENTION_DAYS", "30")
    monkeypatch.setenv("M_JOURNEY_EXPIRED_AUTH_TOKEN_RETENTION_DAYS", "2")
    monkeypatch.setenv("M_JOURNEY_AUDIT_LOG_RETENTION_DAYS", "180")

    settings = load_settings()

    assert settings.visit_personal_data_retention_days == 30
    assert settings.expired_auth_token_retention_days == 2
    assert settings.audit_log_retention_days == 180


def test_retention_configuration_rejects_non_positive_days(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("M_JOURNEY_VISIT_PERSONAL_DATA_RETENTION_DAYS", "0")

    with pytest.raises(ValueError, match="1일 이상"):
        load_settings()
