from __future__ import annotations

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
