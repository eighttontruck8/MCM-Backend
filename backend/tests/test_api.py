from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

TEST_PASSWORD = "test-password-1234"


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
