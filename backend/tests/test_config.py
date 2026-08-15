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
