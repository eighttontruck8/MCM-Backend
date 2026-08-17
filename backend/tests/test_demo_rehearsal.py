from __future__ import annotations

import json
from dataclasses import asdict

import httpx
import pytest

from app.demo_rehearsal import (
    RehearsalConfig,
    RehearsalError,
    _validate_api_base_url,
    run_customer_demo_rehearsal,
)


TOKEN = "rehearsal-opaque-qr-token-12345"
CONFIG = RehearsalConfig(
    frontend_base_url="https://app.mjourney.test",
    entry_token=TOKEN,
    customer_email="customer@example.com",
    customer_password="demo-password-secret",
)


def _response(status: int, payload: dict | None = None, **headers: str) -> httpx.Response:
    return httpx.Response(status, json=payload, headers=headers)


def test_customer_demo_rehearsal_runs_full_flow_and_cleans_up() -> None:
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        routes = {
            ("GET", "/health/ready"): _response(200, {"status": "ready"}),
            ("GET", f"/api/v1/entry-tags/{TOKEN}"): _response(
                200,
                {"channel": "QR", "store": {"store_id": "S001"}},
            ),
            ("GET", f"/entry/{TOKEN}"): _response(
                307,
                None,
                location=f"https://app.mjourney.test/check-in?tag_token={TOKEN}",
            ),
            ("POST", "/api/v1/auth/login"): _response(
                200,
                {
                    "access_token": "access-secret",
                    "refresh_token": "refresh-secret",
                    "user": {"role": "CUSTOMER"},
                },
            ),
            ("POST", "/api/v1/check-ins"): _response(201, {"checkin_id": "checkin-1"}),
            ("PATCH", "/api/v1/check-ins/checkin-1/shopping-mode"): _response(
                200,
                {"status": "SELF_SHOPPING"},
            ),
            ("POST", "/api/v1/check-ins/checkin-1/lookbook"): _response(
                200,
                {"looks": [{"product_id": "P001"}, {"product_id": "P002"}]},
            ),
            ("POST", "/api/v1/check-ins/checkin-1/cancel"): _response(200, {"message": "취소"}),
            ("POST", "/api/v1/auth/logout"): _response(200, {"message": "로그아웃"}),
        }
        return routes[(request.method, request.url.path)]

    with httpx.Client(base_url="https://api.mjourney.test", transport=httpx.MockTransport(handler)) as client:
        result = run_customer_demo_rehearsal(client, CONFIG)

    assert result.status == "PASSED"
    assert result.store_id == "S001"
    assert result.look_count == 2
    assert result.cleanup == "CANCELLED"
    assert result.steps[-2:] == ("CHECKIN_CANCELLED", "LOGOUT_REQUESTED")
    assert ("POST", "/api/v1/check-ins/checkin-1/cancel") in calls
    assert ("POST", "/api/v1/auth/logout") in calls
    serialized = json.dumps(asdict(result))
    assert TOKEN not in serialized
    assert "demo-password-secret" not in serialized


def test_rehearsal_cleans_up_checkin_when_lookbook_fails() -> None:
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if request.url.path == "/health/ready":
            return _response(200, {})
        if request.url.path.startswith("/api/v1/entry-tags/"):
            return _response(200, {"channel": "QR", "store": {"store_id": "S001"}})
        if request.url.path.startswith("/entry/"):
            return _response(307, None, location=f"https://app.mjourney.test/check-in?tag_token={TOKEN}")
        if request.url.path == "/api/v1/auth/login":
            return _response(
                200,
                {"access_token": "access", "refresh_token": "refresh", "user": {"role": "CUSTOMER"}},
            )
        if request.url.path == "/api/v1/check-ins":
            return _response(201, {"checkin_id": "checkin-1"})
        if request.url.path.endswith("/shopping-mode"):
            return _response(200, {"status": "SELF_SHOPPING"})
        if request.url.path.endswith("/lookbook"):
            return _response(503, {"error": {"code": "AI_SERVICE_UNAVAILABLE", "message": "AI 장애"}})
        return _response(200, {})

    with httpx.Client(base_url="https://api.mjourney.test", transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(RehearsalError, match="AI_SERVICE_UNAVAILABLE"):
            run_customer_demo_rehearsal(client, CONFIG)

    assert ("POST", "/api/v1/check-ins/checkin-1/cancel") in calls
    assert ("POST", "/api/v1/auth/logout") in calls


def test_rehearsal_does_not_cancel_preexisting_active_checkin() -> None:
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append((request.method, request.url.path))
        if request.url.path == "/health/ready":
            return _response(200, {})
        if request.url.path.startswith("/api/v1/entry-tags/"):
            return _response(200, {"channel": "QR", "store": {"store_id": "S001"}})
        if request.url.path.startswith("/entry/"):
            return _response(307, None, location=f"https://app.mjourney.test/check-in?tag_token={TOKEN}")
        if request.url.path == "/api/v1/auth/login":
            return _response(
                200,
                {"access_token": "access", "refresh_token": "refresh", "user": {"role": "CUSTOMER"}},
            )
        if request.url.path == "/api/v1/check-ins":
            return _response(409, {"error": {"code": "ACTIVE_CHECKIN_EXISTS", "message": "활성 방문"}})
        return _response(200, {})

    with httpx.Client(base_url="https://api.mjourney.test", transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(RehearsalError, match="활성 체크인"):
            run_customer_demo_rehearsal(client, CONFIG)

    assert not any(path.endswith("/cancel") for _, path in calls)
    assert ("POST", "/api/v1/auth/logout") in calls


@pytest.mark.parametrize(
    ("url", "allow_http_local", "expected"),
    [
        ("https://api.mjourney.test/", False, "https://api.mjourney.test"),
        ("http://127.0.0.1:8000", True, "http://127.0.0.1:8000"),
    ],
)
def test_validate_api_base_url(url: str, allow_http_local: bool, expected: str) -> None:
    assert _validate_api_base_url(url, allow_http_local) == expected


@pytest.mark.parametrize("url", ["http://api.mjourney.test", "https://api.mjourney.test/path", ""])
def test_validate_api_base_url_rejects_unsafe_values(url: str) -> None:
    with pytest.raises(ValueError):
        _validate_api_base_url(url, allow_http_local=False)
