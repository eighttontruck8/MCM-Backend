from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import time
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from sqlalchemy import event, select

from app.main import create_app
from app.models import AuditLog, Consent, Customer, PasswordResetToken, Recommendation, Staff, StaffAssignment, User
from app.security import token_hash

TEST_PASSWORD = "test-password-1234"
TEST_QR_TOKEN = "qr-demo-seoul-001-7f4d0b9e8c2a"


class CountingAIProvider:
    def __init__(self) -> None:
        self.lookbook_calls = 0

    def generate_lookbook(self, context: dict) -> object:
        self.lookbook_calls += 1
        return {
            "title": "테스트 룩북",
            "intro": "테스트 소개",
            "looks": [{"product_id": "P003", "styling": "AI 스타일링"}],
            "closing": "테스트 마무리",
        }

    def generate_staff_guide(self, context: dict) -> object:
        raise NotImplementedError


class InvalidAIProvider:
    def generate_lookbook(self, context: dict) -> object:
        return {"title": "필드 누락"}

    def generate_staff_guide(self, context: dict) -> object:
        return {"customer_summary": 123}


class SlowAIProvider:
    def generate_lookbook(self, context: dict) -> object:
        time.sleep(0.05)
        return {}

    def generate_staff_guide(self, context: dict) -> object:
        time.sleep(0.05)
        return {}


class RecordingPasswordResetMailer:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str, int]] = []

    def send_password_reset(self, recipient: str, reset_url: str, expires_minutes: int) -> None:
        self.messages.append((recipient, reset_url, expires_minutes))


def make_client() -> TestClient:
    return TestClient(
        create_app(
            "sqlite+pysqlite:///:memory:",
            jwt_secret="test-jwt-secret-with-sufficient-length",
            demo_password=TEST_PASSWORD,
            demo_qr_token=TEST_QR_TOKEN,
        )
    )


def login(client: TestClient, email: str = "customer@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, response.text
    return response.json()


def headers(client: TestClient, email: str = "customer@example.com") -> dict[str, str]:
    return {"Authorization": f"Bearer {login(client, email)['access_token']}"}


def create_checkin(client: TestClient, auth_headers: dict[str, str] | None = None) -> str:
    response = client.post(
        "/api/v1/check-ins",
        headers=auth_headers or headers(client),
        json={"tag_token": TEST_QR_TOKEN},
    )
    assert response.status_code == 201, response.text
    return response.json()["checkin_id"]


def create_staff_request(client: TestClient, auth_headers: dict[str, str] | None = None) -> str:
    customer_headers = auth_headers or headers(client)
    checkin_id = create_checkin(client, customer_headers)
    mode = client.patch(
        f"/api/v1/check-ins/{checkin_id}/shopping-mode",
        headers=customer_headers,
        json={"shopping_mode": "STAFF_ASSISTED"},
    )
    assert mode.status_code == 200, mode.text
    service_request = client.post(
        f"/api/v1/check-ins/{checkin_id}/service-request",
        headers=customer_headers,
        json={
            "consent": {
                "agreed": True,
                "policy_version": "staff-profile-share-v1",
                "scopes": ["PURCHASE_HISTORY", "STYLE_PROFILE"],
            },
            "visit_purpose": {"code": "BUSINESS_TRIP", "note": "노트북 수납 가방"},
        },
    )
    assert service_request.status_code == 202, service_request.text
    return checkin_id


def test_health_and_seed_catalog() -> None:
    with make_client() as client:
        assert client.get("/health/live").json() == {"status": "ok"}
        assert client.get("/health/ready").json() == {"status": "ready"}

        products = client.get("/api/v1/products", params={"store_id": "S001", "in_stock": True})
        assert products.status_code == 200
        assert len(products.json()["items"]) == 5


def test_customer_signup_creates_profile_and_login_account() -> None:
    with make_client() as client:
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "name": " 신규 고객 ",
                "phone": "010-1234-5678",
                "email": "New.Customer@Example.com",
                "password": "1234",
            },
        )

        assert response.status_code == 201, response.text
        payload = response.json()
        assert payload["user"]["role"] == "CUSTOMER"
        assert payload["user"]["display_name"] == "신규 고객"
        assert payload["access_token"]
        customer_id = payload["user"]["id"]

        with client.app.state.database.session_factory() as session:
            assert session.get(User, customer_id).email == "new.customer@example.com"
            customer = session.get(Customer, customer_id)
            assert customer.name == "신규 고객"
            assert customer.phone == "01012345678"
            assert session.scalar(
                select(AuditLog).where(
                    AuditLog.action == "AUTH_SIGNUP_COMPLETED",
                    AuditLog.actor_id == customer_id,
                )
            ) is not None

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "NEW.CUSTOMER@example.com", "password": "1234"},
        )
        assert login_response.status_code == 200
        assert login_response.json()["user"]["id"] == customer_id


def test_customer_signup_rejects_duplicate_email_and_phone() -> None:
    with make_client() as client:
        signup = {
            "name": "신규 고객",
            "phone": "01012345678",
            "email": "new-customer@example.com",
            "password": "new-customer-password",
        }
        assert client.post("/api/v1/auth/signup", json=signup).status_code == 201

        duplicate_email = client.post(
            "/api/v1/auth/signup",
            json={**signup, "phone": "01087654321"},
        )
        assert duplicate_email.status_code == 409
        assert duplicate_email.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

        duplicate_phone = client.post(
            "/api/v1/auth/signup",
            json={**signup, "email": "other-customer@example.com"},
        )
        assert duplicate_phone.status_code == 409
        assert duplicate_phone.json()["error"]["code"] == "PHONE_ALREADY_REGISTERED"


def test_customer_signup_validates_contact_and_password() -> None:
    with make_client() as client:
        response = client.post(
            "/api/v1/auth/signup",
            json={
                "name": "고객",
                "phone": "1234",
                "email": "not-an-email",
                "password": "short",
            },
        )
        assert response.status_code == 422
        short_password = client.post(
            "/api/v1/auth/signup",
            json={
                "name": "고객",
                "phone": "01012345678",
                "email": "short-password@example.com",
                "password": "123",
            },
        )
        assert short_password.status_code == 422


def test_staff_signup_requires_code_and_creates_store_account() -> None:
    app = create_app(
        "sqlite+pysqlite:///:memory:",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        demo_password=TEST_PASSWORD,
        demo_qr_token=TEST_QR_TOKEN,
        staff_signup_code="1234",
    )
    # PostgreSQL과 동일하게 외래키를 강제해 users보다 staff가 먼저 저장되는 회귀를 검출한다.
    @event.listens_for(app.state.database.engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    with TestClient(app) as client:
        signup = {
            "name": " 신규 직원 ",
            "email": "New.Staff@Example.com",
            "password": "5678",
            "store_id": "S001",
            "signup_code": "1234",
        }
        denied = client.post(
            "/api/v1/auth/staff/signup",
            json={**signup, "signup_code": "0000"},
        )
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "INVALID_STAFF_SIGNUP_CODE"

        response = client.post("/api/v1/auth/staff/signup", json=signup)
        assert response.status_code == 201, response.text
        assert response.json()["message"] == "직원 계정이 생성되었습니다. 로그인해주세요."

        with client.app.state.database.session_factory() as session:
            user = session.scalar(select(User).where(User.email == "new.staff@example.com"))
            assert user.role == "STAFF"
            assert user.display_name == "신규 직원"
            staff = session.get(Staff, user.id)
            assert staff.store_id == "S001"
            assert staff.title == "Client Advisor"

        duplicate = client.post("/api/v1/auth/staff/signup", json=signup)
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "new.staff@example.com", "password": "5678"},
        )
        assert login_response.status_code == 200
        assert login_response.json()["user"]["role"] == "STAFF"


def test_staff_signup_is_disabled_without_configured_code() -> None:
    app = create_app(
        "sqlite+pysqlite:///:memory:",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        demo_password=TEST_PASSWORD,
        demo_qr_token=TEST_QR_TOKEN,
        staff_signup_code="",
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/staff/signup",
            json={
                "name": "신규 직원",
                "email": "new-staff@example.com",
                "password": "new-staff-password",
                "store_id": "S001",
                "signup_code": "approved-staff-code",
            },
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "STAFF_SIGNUP_DISABLED"


def test_qr_entry_validation_redirect_and_nfc_compatibility() -> None:
    app = create_app(
        "sqlite+pysqlite:///:memory:",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        demo_password=TEST_PASSWORD,
        demo_qr_token=TEST_QR_TOKEN,
        frontend_base_url="https://demo.m-journey.example",
    )
    with TestClient(app) as client:
        entry = client.get(f"/api/v1/entry-tags/{TEST_QR_TOKEN}")
        assert entry.status_code == 200
        assert entry.json()["channel"] == "QR"
        assert entry.json()["store"]["store_id"] == "S001"
        assert entry.json()["checkin_url"] == (
            f"https://demo.m-journey.example/check-in?tag_token={TEST_QR_TOKEN}"
        )
        assert "customer_id" not in entry.text

        redirect = client.get(f"/entry/{TEST_QR_TOKEN}", follow_redirects=False)
        assert redirect.status_code == 307
        assert redirect.headers["location"] == entry.json()["checkin_url"]

        invalid = client.get("/api/v1/entry-tags/invalid-qr-token")
        assert invalid.status_code == 400
        assert invalid.json()["error"]["code"] == "INVALID_ENTRY_TAG"

        legacy_nfc = client.get("/api/v1/entry-tags/nfc-demo-seoul-001")
        assert legacy_nfc.status_code == 200
        assert legacy_nfc.json()["channel"] == "NFC"
        customer_headers = headers(client, "customer2@example.com")
        nfc_checkin = client.post(
            "/api/v1/check-ins",
            headers=customer_headers,
            json={"tag_token": "nfc-demo-seoul-001"},
        )
        assert nfc_checkin.status_code == 201


def test_private_shopping_flow() -> None:
    with make_client() as client:
        auth_headers = headers(client)
        checkin_id = create_checkin(client, auth_headers)
        response = client.patch(
            f"/api/v1/check-ins/{checkin_id}/shopping-mode",
            headers=auth_headers,
            json={"shopping_mode": "PRIVATE"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "SELF_SHOPPING"
        assert response.json()["next_action"] == "VIEW_LOOKBOOK"


def test_staff_assisted_flow_records_consent_and_purpose() -> None:
    with make_client() as client:
        auth_headers = headers(client)
        checkin_id = create_checkin(client, auth_headers)
        mode = client.patch(
            f"/api/v1/check-ins/{checkin_id}/shopping-mode",
            headers=auth_headers,
            json={"shopping_mode": "STAFF_ASSISTED"},
        )
        assert mode.status_code == 200

        response = client.post(
            f"/api/v1/check-ins/{checkin_id}/service-request",
            headers=auth_headers,
            json={
                "consent": {
                    "agreed": True,
                    "policy_version": "staff-profile-share-v1",
                    "scopes": ["PURCHASE_HISTORY", "STYLE_PROFILE"],
                },
                "visit_purpose": {
                    "code": "BUSINESS_TRIP",
                    "note": "노트북 수납 가방",
                },
            },
        )
        assert response.status_code == 202
        assert response.json()["status"] == "WAITING_FOR_STAFF"

        saved = client.get(f"/api/v1/check-ins/{checkin_id}", headers=auth_headers)
        assert saved.json()["visit_purpose_code"] == "BUSINESS_TRIP"


def test_consent_is_required() -> None:
    with make_client() as client:
        auth_headers = headers(client)
        checkin_id = create_checkin(client, auth_headers)
        client.patch(
            f"/api/v1/check-ins/{checkin_id}/shopping-mode",
            headers=auth_headers,
            json={"shopping_mode": "STAFF_ASSISTED"},
        )
        response = client.post(
            f"/api/v1/check-ins/{checkin_id}/service-request",
            headers=auth_headers,
            json={
                "consent": {
                    "agreed": False,
                    "policy_version": "staff-profile-share-v1",
                    "scopes": ["STYLE_PROFILE"],
                },
                "visit_purpose": {"code": "FREE_SHOPPING"},
            },
        )
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "PROFILE_SHARE_CONSENT_REQUIRED"


def test_invalid_tag_and_cross_customer_access() -> None:
    with make_client() as client:
        customer_headers = headers(client)
        invalid = client.post(
            "/api/v1/check-ins",
            headers=customer_headers,
            json={"tag_token": "invalid-tag"},
        )
        assert invalid.status_code == 400

        checkin_id = create_checkin(client, customer_headers)
        denied = client.get(f"/api/v1/check-ins/{checkin_id}", headers=headers(client, "customer2@example.com"))
        assert denied.status_code == 403


def test_login_me_refresh_rotation_and_logout() -> None:
    with make_client() as client:
        tokens = login(client)
        me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert me.status_code == 200
        assert me.json() == {"id": "C001", "role": "CUSTOMER", "display_name": "김서연", "store_id": None}

        refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert refreshed.status_code == 200
        assert client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401

        new_refresh = refreshed.json()["refresh_token"]
        assert client.post("/api/v1/auth/logout", json={"refresh_token": new_refresh}).status_code == 200
        assert client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh}).status_code == 401


def test_staff_role_and_customer_endpoint_access_control() -> None:
    with make_client() as client:
        staff_tokens = login(client, "staff@example.com")
        staff_headers = {"Authorization": f"Bearer {staff_tokens['access_token']}"}
        assert staff_tokens["user"]["role"] == "STAFF"
        assert staff_tokens["user"]["store_id"] == "S001"
        denied = client.post("/api/v1/check-ins", headers=staff_headers, json={"tag_token": TEST_QR_TOKEN})
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "CUSTOMER_ROLE_REQUIRED"

        customer_headers = headers(client)
        profile = client.get("/api/v1/customers/me", headers=customer_headers)
        assert profile.status_code == 200
        assert profile.json()["customer_id"] == "C001"


def test_missing_or_invalid_credentials() -> None:
    with make_client() as client:
        missing = client.post("/api/v1/check-ins", json={"tag_token": TEST_QR_TOKEN})
        assert missing.status_code == 401
        assert missing.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
        invalid_login = client.post("/api/v1/auth/login", json={"email": "customer@example.com", "password": "wrong-password"})
        assert invalid_login.status_code == 401


def test_staff_queue_store_access_masking_and_visit_progress() -> None:
    with make_client() as client:
        customer_headers = headers(client)
        checkin_id = create_staff_request(client, customer_headers)
        staff_headers = headers(client, "staff@example.com")
        other_staff_headers = headers(client, "staff2@example.com")

        denied_store = client.get("/api/v1/staff/stores/S002/visits", headers=staff_headers)
        assert denied_store.status_code == 403
        assert denied_store.json()["error"]["code"] == "STAFF_STORE_ACCESS_DENIED"

        queue = client.get("/api/v1/staff/stores/S001/visits", headers=staff_headers)
        assert queue.status_code == 200
        assert queue.json()["items"][0]["checkin_id"] == checkin_id
        assert queue.json()["items"][0]["masked_name"] == "김**"

        profile = client.get("/api/v1/staff/customers/C001", headers=staff_headers)
        assert profile.status_code == 200
        assert profile.json()["masked_name"] == "김**"
        assert profile.json()["purchase_count"] == 2

        claimed = client.post(f"/api/v1/staff/check-ins/{checkin_id}/claim", headers=staff_headers)
        assert claimed.status_code == 200
        assert claimed.json()["status"] == "ASSIGNED"
        assert claimed.json()["staff"]["staff_id"] == "ST001"

        duplicate_checkin = client.post(
            "/api/v1/check-ins",
            headers=customer_headers,
            json={"tag_token": TEST_QR_TOKEN},
        )
        assert duplicate_checkin.status_code == 409
        assert duplicate_checkin.json()["error"]["code"] == "ACTIVE_CHECKIN_EXISTS"

        duplicate = client.post(f"/api/v1/staff/check-ins/{checkin_id}/claim", headers=other_staff_headers)
        assert duplicate.status_code == 409
        assert duplicate.json()["error"]["code"] == "ALREADY_ASSIGNED"

        customer_view = client.get(f"/api/v1/check-ins/{checkin_id}", headers=customer_headers)
        assert customer_view.json()["assigned_staff"]["staff_id"] == "ST001"

        not_assigned = client.patch(
            f"/api/v1/staff/check-ins/{checkin_id}/status",
            headers=other_staff_headers,
            json={"status": "SERVING"},
        )
        assert not_assigned.status_code == 403

        invalid_transition = client.patch(
            f"/api/v1/staff/check-ins/{checkin_id}/status",
            headers=staff_headers,
            json={"status": "COMPLETED"},
        )
        assert invalid_transition.status_code == 409
        assert invalid_transition.json()["error"]["code"] == "CHECKIN_STATE_CONFLICT"

        serving = client.patch(
            f"/api/v1/staff/check-ins/{checkin_id}/status",
            headers=staff_headers,
            json={"status": "SERVING"},
        )
        assert serving.status_code == 200
        completed = client.patch(
            f"/api/v1/staff/check-ins/{checkin_id}/status",
            headers=staff_headers,
            json={"status": "COMPLETED"},
        )
        assert completed.status_code == 200
        assert completed.json()["status"] == "COMPLETED"
        assert client.get("/api/v1/staff/customers/C001", headers=staff_headers).status_code == 403


def test_only_one_concurrent_staff_claim_succeeds(tmp_path: Path) -> None:
    database_path = (tmp_path / "concurrent.db").as_posix()
    app = create_app(
        f"sqlite+pysqlite:///{database_path}",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        demo_password=TEST_PASSWORD,
    )
    with TestClient(app) as client:
        checkin_id = create_staff_request(client)
        staff_headers = headers(client, "staff@example.com")
        other_staff_headers = headers(client, "staff2@example.com")

        def claim(auth_headers: dict[str, str]):
            return client.post(f"/api/v1/staff/check-ins/{checkin_id}/claim", headers=auth_headers)

        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(executor.map(claim, [staff_headers, other_staff_headers]))

        assert sorted(response.status_code for response in responses) == [200, 409]
        failed = next(response for response in responses if response.status_code == 409)
        assert failed.json()["error"]["code"] == "ALREADY_ASSIGNED"


def test_lookbook_filters_inventory_uses_db_values_and_caches() -> None:
    provider = CountingAIProvider()
    app = create_app(
        "sqlite+pysqlite:///:memory:",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        demo_password=TEST_PASSWORD,
        ai_provider=provider,
    )
    with TestClient(app) as client:
        customer_headers = headers(client)
        checkin_id = create_checkin(client, customer_headers)
        first = client.post(f"/api/v1/check-ins/{checkin_id}/lookbook", headers=customer_headers)
        second = client.post(f"/api/v1/check-ins/{checkin_id}/lookbook", headers=customer_headers)

        assert first.status_code == 200
        assert first.json() == second.json()
        assert provider.lookbook_calls == 1
        assert first.json()["looks"]
        assert all(look["product_id"] != "P003" and look["in_stock"] for look in first.json()["looks"])
        assert all(look["price"] > 0 and look["image_url"].startswith("/assets/products/") for look in first.json()["looks"])


def test_staff_guide_requires_assignment_and_uses_masked_customer() -> None:
    with make_client() as client:
        customer_headers = headers(client)
        checkin_id = create_staff_request(client, customer_headers)
        staff_headers = headers(client, "staff@example.com")

        denied = client.get(f"/api/v1/staff/check-ins/{checkin_id}/guide", headers=staff_headers)
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "ASSIGNED_STAFF_REQUIRED"

        assert client.post(f"/api/v1/staff/check-ins/{checkin_id}/claim", headers=staff_headers).status_code == 200
        guide = client.get(f"/api/v1/staff/check-ins/{checkin_id}/guide", headers=staff_headers)
        assert guide.status_code == 200
        assert guide.json()["customer"]["masked_name"] == "김**"
        assert guide.json()["recommended_products"]
        assert all(item["in_stock"] and item["quantity"] > 0 for item in guide.json()["recommended_products"])


def test_invalid_ai_output_returns_safe_502() -> None:
    app = create_app(
        "sqlite+pysqlite:///:memory:",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        demo_password=TEST_PASSWORD,
        ai_provider=InvalidAIProvider(),
        ai_max_retries=0,
    )
    with TestClient(app) as client:
        customer_headers = headers(client)
        checkin_id = create_checkin(client, customer_headers)
        response = client.post(f"/api/v1/check-ins/{checkin_id}/lookbook", headers=customer_headers)
        assert response.status_code == 502
        assert response.json()["error"]["code"] == "AI_RESPONSE_INVALID"
        assert "필드 누락" not in response.text


def test_ai_timeout_returns_in_stock_fallback() -> None:
    app = create_app(
        "sqlite+pysqlite:///:memory:",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        demo_password=TEST_PASSWORD,
        ai_provider=SlowAIProvider(),
        ai_timeout_seconds=0.001,
        ai_max_retries=0,
    )
    with TestClient(app) as client:
        customer_headers = headers(client)
        checkin_id = create_checkin(client, customer_headers)
        response = client.post(f"/api/v1/check-ins/{checkin_id}/lookbook", headers=customer_headers)
        assert response.status_code == 200
        assert response.json()["looks"]
        assert all(look["in_stock"] for look in response.json()["looks"])


def test_staff_and_customer_websocket_event_flow() -> None:
    with make_client() as client:
        customer_tokens = login(client)
        staff_tokens = login(client, "staff@example.com")
        customer_headers = {"Authorization": f"Bearer {customer_tokens['access_token']}"}
        staff_headers = {"Authorization": f"Bearer {staff_tokens['access_token']}"}
        staff_url = f"/api/v1/ws/staff/stores/S001?token={staff_tokens['access_token']}"
        customer_url = f"/api/v1/ws/customers/me?token={customer_tokens['access_token']}"

        with client.websocket_connect(staff_url) as staff_ws, client.websocket_connect(customer_url) as customer_ws:
            checkin_id = create_staff_request(client, customer_headers)
            waiting = staff_ws.receive_json()
            assert waiting["event"] == "VISIT_WAITING"
            assert waiting["data"]["checkin_id"] == checkin_id
            assert waiting["data"]["masked_name"] == "김**"

            claimed = client.post(f"/api/v1/staff/check-ins/{checkin_id}/claim", headers=staff_headers)
            assert claimed.status_code == 200
            staff_assigned = staff_ws.receive_json()
            customer_assigned = customer_ws.receive_json()
            assert staff_assigned["event"] == customer_assigned["event"] == "STAFF_ASSIGNED"
            assert customer_assigned["data"]["staff"]["staff_id"] == "ST001"

            guide = client.get(f"/api/v1/staff/check-ins/{checkin_id}/guide", headers=staff_headers)
            assert guide.status_code == 200
            assert staff_ws.receive_json()["event"] == "AI_GUIDE_READY"

            serving = client.patch(
                f"/api/v1/staff/check-ins/{checkin_id}/status",
                headers=staff_headers,
                json={"status": "SERVING"},
            )
            assert serving.status_code == 200
            completed = client.patch(
                f"/api/v1/staff/check-ins/{checkin_id}/status",
                headers=staff_headers,
                json={"status": "COMPLETED"},
            )
            assert completed.status_code == 200
            assert staff_ws.receive_json()["event"] == "VISIT_COMPLETED"
            assert customer_ws.receive_json()["event"] == "VISIT_COMPLETED"


def test_websocket_auth_store_access_and_ping_pong() -> None:
    with make_client() as client:
        staff_token = login(client, "staff@example.com")["access_token"]
        with client.websocket_connect(f"/api/v1/ws/staff/stores/S001?token={staff_token}") as websocket:
            websocket.send_json({"event": "PING"})
            assert websocket.receive_json()["event"] == "PONG"

        with pytest.raises(WebSocketDisconnect) as invalid:
            with client.websocket_connect("/api/v1/ws/staff/stores/S001?token=invalid-token"):
                pass
        assert invalid.value.code == 4401

        with pytest.raises(WebSocketDisconnect) as wrong_store:
            with client.websocket_connect(f"/api/v1/ws/staff/stores/S002?token={staff_token}"):
                pass
        assert wrong_store.value.code == 4403


def test_visit_cancelled_event_reaches_staff_and_customer() -> None:
    with make_client() as client:
        customer_tokens = login(client)
        staff_tokens = login(client, "staff@example.com")
        customer_headers = {"Authorization": f"Bearer {customer_tokens['access_token']}"}
        staff_url = f"/api/v1/ws/staff/stores/S001?token={staff_tokens['access_token']}"
        customer_url = f"/api/v1/ws/customers/me?token={customer_tokens['access_token']}"

        with client.websocket_connect(staff_url) as staff_ws, client.websocket_connect(customer_url) as customer_ws:
            checkin_id = create_staff_request(client, customer_headers)
            assert staff_ws.receive_json()["event"] == "VISIT_WAITING"
            cancelled = client.post(f"/api/v1/check-ins/{checkin_id}/cancel", headers=customer_headers)
            assert cancelled.status_code == 200
            staff_event = staff_ws.receive_json()
            customer_event = customer_ws.receive_json()
            assert staff_event["event"] == customer_event["event"] == "VISIT_CANCELLED"
            assert customer_event["data"]["checkin_id"] == checkin_id


def test_wishlist_add_is_idempotent_delete_and_customer_isolation() -> None:
    with make_client() as client:
        customer_headers = headers(client)
        other_customer_headers = headers(client, "customer2@example.com")

        initial = client.get("/api/v1/customers/me/wishlist", headers=customer_headers)
        assert [item["product_id"] for item in initial.json()["items"]] == ["P001"]

        first_add = client.post("/api/v1/customers/me/wishlist/P002", headers=customer_headers)
        second_add = client.post("/api/v1/customers/me/wishlist/P002", headers=customer_headers)
        assert first_add.status_code == second_add.status_code == 201
        wishlist = client.get("/api/v1/customers/me/wishlist", headers=customer_headers)
        assert [item["product_id"] for item in wishlist.json()["items"]].count("P002") == 1

        profile = client.get("/api/v1/customers/me", headers=customer_headers)
        assert "P002" in profile.json()["liked_product_ids"]
        other_wishlist = client.get("/api/v1/customers/me/wishlist", headers=other_customer_headers)
        assert "P002" not in [item["product_id"] for item in other_wishlist.json()["items"]]

        removed = client.delete("/api/v1/customers/me/wishlist/P002", headers=customer_headers)
        assert removed.status_code == 200
        assert client.delete("/api/v1/customers/me/wishlist/P002", headers=customer_headers).status_code == 404
        profile = client.get("/api/v1/customers/me", headers=customer_headers)
        assert "P002" not in profile.json()["liked_product_ids"]


def test_saved_recommendations_only_return_current_in_stock_products() -> None:
    with make_client() as client:
        customer_headers = headers(client)
        checkin_id = create_checkin(client, customer_headers)
        lookbook = client.post(f"/api/v1/check-ins/{checkin_id}/lookbook", headers=customer_headers)
        assert lookbook.status_code == 200

        recommendations = client.get("/api/v1/customers/me/recommendations", headers=customer_headers)
        assert recommendations.status_code == 200
        assert recommendations.json()["items"]
        assert all(item["inventory"]["in_stock"] for item in recommendations.json()["items"])
        assert "P003" not in [item["product_id"] for item in recommendations.json()["items"]]


def test_purchase_history_seed_and_customer_role_access() -> None:
    with make_client() as client:
        customer_purchases = client.get("/api/v1/customers/me/purchases", headers=headers(client))
        assert customer_purchases.status_code == 200
        assert len(customer_purchases.json()["items"]) == 2
        assert all(item["price"] > 0 and item["purchased_at"] for item in customer_purchases.json()["items"])

        other_purchases = client.get(
            "/api/v1/customers/me/purchases",
            headers=headers(client, "customer2@example.com"),
        )
        assert len(other_purchases.json()["items"]) == 1

        staff_headers = headers(client, "staff@example.com")
        denied = client.get("/api/v1/customers/me/purchases", headers=staff_headers)
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "CUSTOMER_ROLE_REQUIRED"


def test_consent_revocation_immediately_blocks_staff_and_removes_sensitive_output() -> None:
    with make_client() as client:
        customer_tokens = login(client)
        staff_tokens = login(client, "staff@example.com")
        customer_headers = {"Authorization": f"Bearer {customer_tokens['access_token']}"}
        staff_headers = {"Authorization": f"Bearer {staff_tokens['access_token']}"}
        checkin_id = create_staff_request(client, customer_headers)
        assert client.post(f"/api/v1/staff/check-ins/{checkin_id}/claim", headers=staff_headers).status_code == 200
        assert client.get(f"/api/v1/staff/check-ins/{checkin_id}/guide", headers=staff_headers).status_code == 200

        staff_url = f"/api/v1/ws/staff/stores/S001?token={staff_tokens['access_token']}"
        customer_url = f"/api/v1/ws/customers/me?token={customer_tokens['access_token']}"
        with client.websocket_connect(staff_url) as staff_ws, client.websocket_connect(customer_url) as customer_ws:
            revoked = client.post(f"/api/v1/check-ins/{checkin_id}/consent/revoke", headers=customer_headers)
            assert revoked.status_code == 200
            assert revoked.json()["consent_status"] == "REVOKED"
            assert revoked.json()["shopping_mode"] == "PRIVATE"
            assert revoked.json()["checkin_status"] == "SELF_SHOPPING"
            assert staff_ws.receive_json()["event"] == "CONSENT_REVOKED"
            assert customer_ws.receive_json()["event"] == "CONSENT_REVOKED"

        repeated = client.post(f"/api/v1/check-ins/{checkin_id}/consent/revoke", headers=customer_headers)
        assert repeated.status_code == 200
        assert repeated.json()["revoked_at"] == revoked.json()["revoked_at"]

        staff_profile = client.get("/api/v1/staff/customers/C001", headers=staff_headers)
        assert staff_profile.status_code == 403
        guide = client.get(f"/api/v1/staff/check-ins/{checkin_id}/guide", headers=staff_headers)
        assert guide.status_code == 403
        assert guide.json()["error"]["code"] == "STAFF_GUIDE_ACCESS_DENIED"

        customer_view = client.get(f"/api/v1/check-ins/{checkin_id}", headers=customer_headers)
        assert customer_view.json()["visit_note"] is None
        assert customer_view.json()["status"] == "SELF_SHOPPING"
        assert customer_view.json()["assigned_staff"] is None

        with client.app.state.database.session_factory() as db:
            consent = db.scalar(select(Consent).where(Consent.checkin_id == checkin_id))
            assignment = db.scalar(select(StaffAssignment).where(StaffAssignment.checkin_id == checkin_id))
            recommendation = db.scalar(
                select(Recommendation).where(
                    Recommendation.checkin_id == checkin_id,
                    Recommendation.type == "STAFF_GUIDE",
                )
            )
            assert consent.revoked_at is not None
            assert assignment.ended_at is not None
            assert recommendation.status == "REVOKED"
            assert recommendation.output is None
            assert recommendation.error_code == "CONSENT_REVOKED"


def test_consent_revocation_requires_owner_and_existing_consent() -> None:
    with make_client() as client:
        customer_headers = headers(client)
        checkin_id = create_checkin(client, customer_headers)
        missing = client.post(f"/api/v1/check-ins/{checkin_id}/consent/revoke", headers=customer_headers)
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "CONSENT_NOT_FOUND"

        denied = client.post(
            f"/api/v1/check-ins/{checkin_id}/consent/revoke",
            headers=headers(client, "customer2@example.com"),
        )
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "CHECKIN_ACCESS_DENIED"


def test_password_reset_sends_frontend_link_without_exposing_token() -> None:
    mailer = RecordingPasswordResetMailer()
    app = create_app(
        "sqlite+pysqlite:///:memory:",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        demo_password=TEST_PASSWORD,
        password_reset_mailer=mailer,
        frontend_base_url="https://shop.example.com",
        expose_password_reset_token=False,
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "customer@example.com"},
        )

    assert response.status_code == 202
    assert response.json()["reset_token"] is None
    assert len(mailer.messages) == 1
    recipient, reset_url, expires_minutes = mailer.messages[0]
    parsed = urlsplit(reset_url)
    assert recipient == "customer@example.com"
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == "https://shop.example.com/reset-password"
    assert len(parse_qs(parsed.query)["token"][0]) >= 32
    assert expires_minutes == 15


def test_password_reset_revokes_existing_tokens_and_is_one_time() -> None:
    app = create_app(
        "sqlite+pysqlite:///:memory:",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        demo_password=TEST_PASSWORD,
        expose_password_reset_token=True,
    )
    new_password = "new-test-password-5678"
    with TestClient(app) as client:
        old_tokens = login(client)
        other_tokens = login(client, "customer2@example.com")

        first_request = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "customer@example.com"},
        )
        second_request = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "customer@example.com"},
        )
        assert first_request.status_code == second_request.status_code == 202
        first_token = first_request.json()["reset_token"]
        reset_token = second_request.json()["reset_token"]
        assert first_token and reset_token and first_token != reset_token

        invalidated = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"reset_token": first_token, "new_password": new_password},
        )
        assert invalidated.status_code == 400

        confirmed = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"reset_token": reset_token, "new_password": new_password},
        )
        assert confirmed.status_code == 200

        old_headers = {"Authorization": f"Bearer {old_tokens['access_token']}"}
        assert client.get("/api/v1/me", headers=old_headers).status_code == 401
        assert client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_tokens["refresh_token"]},
        ).status_code == 401
        assert client.post(
            "/api/v1/auth/login",
            json={"email": "customer@example.com", "password": TEST_PASSWORD},
        ).status_code == 401

        new_login = client.post(
            "/api/v1/auth/login",
            json={"email": "customer@example.com", "password": new_password},
        )
        assert new_login.status_code == 200
        assert client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"reset_token": reset_token, "new_password": "another-password-9999"},
        ).status_code == 400

        other_headers = {"Authorization": f"Bearer {other_tokens['access_token']}"}
        assert client.get("/api/v1/me", headers=other_headers).status_code == 200

        with client.app.state.database.session_factory() as db:
            stored = db.scalar(
                select(PasswordResetToken).where(
                    PasswordResetToken.token_hash == token_hash(reset_token)
                )
            )
            assert stored.token_hash != reset_token
            assert len(stored.token_hash) == 64
            assert stored.used_at is not None


def test_password_reset_request_does_not_expose_account_or_token_by_default() -> None:
    with make_client() as client:
        existing = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "customer@example.com"},
        )
        unknown = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "unknown@example.com"},
        )
        assert existing.status_code == unknown.status_code == 202
        assert existing.json() == unknown.json()
        assert existing.json()["reset_token"] is None


def test_password_reset_rejects_current_password() -> None:
    app = create_app(
        "sqlite+pysqlite:///:memory:",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        demo_password=TEST_PASSWORD,
        expose_password_reset_token=True,
    )
    with TestClient(app) as client:
        requested = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "customer@example.com"},
        )
        response = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={
                "reset_token": requested.json()["reset_token"],
                "new_password": TEST_PASSWORD,
            },
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "PASSWORD_REUSE_NOT_ALLOWED"


def test_expired_password_reset_token_is_rejected() -> None:
    app = create_app(
        "sqlite+pysqlite:///:memory:",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        demo_password=TEST_PASSWORD,
        expose_password_reset_token=True,
    )
    with TestClient(app) as client:
        requested = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "customer@example.com"},
        )
        reset_token = requested.json()["reset_token"]
        with client.app.state.database.session_factory() as db:
            stored = db.scalar(
                select(PasswordResetToken).where(
                    PasswordResetToken.token_hash == token_hash(reset_token)
                )
            )
            stored.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.commit()

        response = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"reset_token": reset_token, "new_password": "new-test-password-5678"},
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_PASSWORD_RESET_TOKEN"


def test_rate_limits_login_password_reset_and_ai_generation() -> None:
    app = create_app(
        "sqlite+pysqlite:///:memory:",
        jwt_secret="test-jwt-secret-with-sufficient-length",
        demo_password=TEST_PASSWORD,
        expose_password_reset_token=True,
        rate_limits={"login": 2, "password_reset": 1, "ai": 1},
    )
    with TestClient(app) as client:
        first_login = client.post(
            "/api/v1/auth/login",
            json={"email": "customer@example.com", "password": TEST_PASSWORD},
        )
        assert first_login.status_code == 200
        assert client.post(
            "/api/v1/auth/login",
            json={"email": "customer@example.com", "password": TEST_PASSWORD},
        ).status_code == 200
        limited_login = client.post(
            "/api/v1/auth/login",
            json={"email": "customer@example.com", "password": TEST_PASSWORD},
        )
        assert limited_login.status_code == 429
        assert limited_login.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert int(limited_login.headers["Retry-After"]) >= 1

        reset = client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "customer@example.com"},
        )
        assert reset.status_code == 202
        assert client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "customer@example.com"},
        ).status_code == 429

        customer_headers = {"Authorization": f"Bearer {first_login.json()['access_token']}"}
        checkin_id = create_checkin(client, customer_headers)
        assert client.post(f"/api/v1/check-ins/{checkin_id}/lookbook", headers=customer_headers).status_code == 200
        limited_ai = client.post(f"/api/v1/check-ins/{checkin_id}/lookbook", headers=customer_headers)
        assert limited_ai.status_code == 429


def test_audit_logs_security_events_without_credentials() -> None:
    with make_client() as client:
        failed = client.post(
            "/api/v1/auth/login",
            json={"email": "customer@example.com", "password": "wrong-password"},
        )
        assert failed.status_code == 401
        successful = login(client)
        customer_headers = {"Authorization": f"Bearer {successful['access_token']}"}
        checkin_id = create_staff_request(client, customer_headers)
        staff_headers = headers(client, "staff@example.com")
        assert client.post(f"/api/v1/staff/check-ins/{checkin_id}/claim", headers=staff_headers).status_code == 200
        assert client.post(f"/api/v1/check-ins/{checkin_id}/consent/revoke", headers=customer_headers).status_code == 200

        with client.app.state.database.session_factory() as db:
            audit_logs = db.scalars(select(AuditLog).order_by(AuditLog.created_at)).all()
            actions = {audit.action for audit in audit_logs}
            assert {
                "AUTH_LOGIN_FAILED",
                "AUTH_LOGIN_SUCCEEDED",
                "STAFF_CLAIMED_VISIT",
                "CONSENT_REVOKED",
            }.issubset(actions)
            serialized = json.dumps(
                [audit.metadata_json for audit in audit_logs],
                ensure_ascii=False,
            )
            assert "wrong-password" not in serialized
            assert TEST_PASSWORD not in serialized
            assert "customer@example.com" not in serialized
            assert all(audit.request_id and audit.request_id.startswith("req_") for audit in audit_logs)


def test_structured_request_log_excludes_query_and_body(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="mjourney.request")
    with make_client() as client:
        response = client.post(
            "/api/v1/auth/login?debug_secret=must-not-appear",
            headers={"X-Request-ID": "req_structured_log_test"},
            json={"email": "customer@example.com", "password": TEST_PASSWORD},
        )
        assert response.status_code == 200

    records = [record for record in caplog.records if record.name == "mjourney.request"]
    entry = json.loads(records[-1].message)
    assert entry["request_id"] == "req_structured_log_test"
    assert entry["path"] == "/api/v1/auth/login"
    assert entry["status_code"] == 200
    assert entry["duration_ms"] >= 0
    assert "must-not-appear" not in records[-1].message
    assert TEST_PASSWORD not in records[-1].message


def test_structured_log_masks_qr_token_path(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="mjourney.request")
    with make_client() as client:
        response = client.get(f"/entry/{TEST_QR_TOKEN}", follow_redirects=False)
        assert response.status_code == 307

    records = [record for record in caplog.records if record.name == "mjourney.request"]
    entry = json.loads(records[-1].message)
    assert entry["path"] == "/entry/{tag_token}"
    assert TEST_QR_TOKEN not in records[-1].message
