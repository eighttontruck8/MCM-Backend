from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def make_client() -> TestClient:
    return TestClient(create_app("sqlite+pysqlite:///:memory:"))


def headers(customer_id: str = "C001") -> dict[str, str]:
    return {"X-Customer-ID": customer_id}


def create_checkin(client: TestClient, customer_id: str = "C001") -> str:
    response = client.post(
        "/api/v1/check-ins",
        headers=headers(customer_id),
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
        checkin_id = create_checkin(client)
        response = client.patch(
            f"/api/v1/check-ins/{checkin_id}/shopping-mode",
            headers=headers(),
            json={"shopping_mode": "PRIVATE"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "SELF_SHOPPING"
        assert response.json()["next_action"] == "VIEW_LOOKBOOK"


def test_staff_assisted_flow_records_consent_and_purpose() -> None:
    with make_client() as client:
        checkin_id = create_checkin(client)
        mode = client.patch(
            f"/api/v1/check-ins/{checkin_id}/shopping-mode",
            headers=headers(),
            json={"shopping_mode": "STAFF_ASSISTED"},
        )
        assert mode.status_code == 200

        response = client.post(
            f"/api/v1/check-ins/{checkin_id}/service-request",
            headers=headers(),
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

        saved = client.get(f"/api/v1/check-ins/{checkin_id}", headers=headers())
        assert saved.json()["visit_purpose_code"] == "BUSINESS_TRIP"


def test_consent_is_required() -> None:
    with make_client() as client:
        checkin_id = create_checkin(client)
        client.patch(
            f"/api/v1/check-ins/{checkin_id}/shopping-mode",
            headers=headers(),
            json={"shopping_mode": "STAFF_ASSISTED"},
        )
        response = client.post(
            f"/api/v1/check-ins/{checkin_id}/service-request",
            headers=headers(),
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
        invalid = client.post(
            "/api/v1/check-ins",
            headers=headers(),
            json={"tag_token": "invalid-tag"},
        )
        assert invalid.status_code == 400

        checkin_id = create_checkin(client)
        denied = client.get(f"/api/v1/check-ins/{checkin_id}", headers=headers("C002"))
        assert denied.status_code == 403
