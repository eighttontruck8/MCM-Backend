from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import time

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import create_app

TEST_PASSWORD = "test-password-1234"


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


def make_client() -> TestClient:
    return TestClient(
        create_app(
            "sqlite+pysqlite:///:memory:",
            jwt_secret="test-jwt-secret-with-sufficient-length",
            demo_password=TEST_PASSWORD,
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
        json={"tag_token": "nfc-demo-seoul-001"},
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
        denied = client.post("/api/v1/check-ins", headers=staff_headers, json={"tag_token": "nfc-demo-seoul-001"})
        assert denied.status_code == 403
        assert denied.json()["error"]["code"] == "CUSTOMER_ROLE_REQUIRED"

        customer_headers = headers(client)
        profile = client.get("/api/v1/customers/me", headers=customer_headers)
        assert profile.status_code == 200
        assert profile.json()["customer_id"] == "C001"


def test_missing_or_invalid_credentials() -> None:
    with make_client() as client:
        missing = client.post("/api/v1/check-ins", json={"tag_token": "nfc-demo-seoul-001"})
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
            json={"tag_token": "nfc-demo-seoul-001"},
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
