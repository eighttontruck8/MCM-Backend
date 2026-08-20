from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from urllib.parse import urlsplit

import httpx

from app.config import load_settings


class RehearsalError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class RehearsalConfig:
    frontend_base_url: str
    entry_token: str
    customer_email: str
    customer_password: str


@dataclass(frozen=True, slots=True)
class RehearsalResult:
    status: str
    checkin_id: str
    store_id: str
    look_count: int
    cleanup: str
    steps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StaffRehearsalConfig:
    frontend_base_url: str
    entry_token: str
    customer_email: str
    customer_password: str
    staff_email: str
    staff_password: str


@dataclass(frozen=True, slots=True)
class StaffRehearsalResult:
    status: str
    checkin_id: str
    store_id: str
    guide_product_count: int
    cleanup: str
    steps: tuple[str, ...]


def _error_message(response: httpx.Response) -> str:
    try:
        error = response.json().get("error", {})
        code = error.get("code", "UNKNOWN_ERROR")
        message = error.get("message", "요청 실패")
        return f"{code}: {message}"
    except (ValueError, AttributeError):
        return f"HTTP_{response.status_code}"


def _expect(response: httpx.Response, expected_status: int, step: str) -> dict:
    if response.status_code != expected_status:
        raise RehearsalError(f"{step} 실패 ({response.status_code}, {_error_message(response)})")
    if not response.content:
        return {}
    try:
        return response.json()
    except ValueError as exc:
        raise RehearsalError(f"{step} 실패 (JSON 응답 아님)") from exc


def run_customer_demo_rehearsal(client: httpx.Client, config: RehearsalConfig) -> RehearsalResult:
    """배포 API의 고객 QR 체크인 핵심 시나리오를 실행하고 생성 방문을 정리한다."""
    # [Backend-08-'QR 시연 리허설'] 실제 배포 API 계약을 순서대로 검증하고 테스트 방문을 항상 취소한다.
    steps: list[str] = []
    access_token: str | None = None
    refresh_token: str | None = None
    checkin_id: str | None = None
    store_id = ""
    look_count = 0
    cleanup = "NOT_REQUIRED"

    try:
        _expect(client.get("/health/ready"), 200, "readiness")
        steps.append("HEALTH_READY")

        entry = _expect(client.get(f"/api/v1/entry-tags/{config.entry_token}"), 200, "QR 태그 검증")
        store_id = entry["store"]["store_id"]
        if entry.get("channel") != "QR":
            raise RehearsalError("QR 태그 검증 실패 (QR 채널 아님)")
        steps.append("QR_TAG_VALID")

        redirect = client.get(f"/entry/{config.entry_token}", follow_redirects=False)
        expected_location = f"{config.frontend_base_url}/check-in?tag_token={config.entry_token}"
        if redirect.status_code not in {302, 307} or redirect.headers.get("location") != expected_location:
            raise RehearsalError("QR 리다이렉트 실패 (프론트 체크인 주소 불일치)")
        steps.append("QR_REDIRECT_VALID")

        login = _expect(
            client.post(
                "/api/v1/auth/login",
                json={"email": config.customer_email, "password": config.customer_password},
            ),
            200,
            "고객 로그인",
        )
        access_token = login["access_token"]
        refresh_token = login["refresh_token"]
        if login.get("user", {}).get("role") != "CUSTOMER":
            raise RehearsalError("고객 로그인 실패 (CUSTOMER 역할 아님)")
        headers = {"Authorization": f"Bearer {access_token}"}
        steps.append("CUSTOMER_LOGIN")

        create_response = client.post(
            "/api/v1/check-ins",
            headers=headers,
            json={"tag_token": config.entry_token},
        )
        if create_response.status_code == 409:
            raise RehearsalError("체크인 생성 실패 (데모 고객의 활성 체크인을 먼저 종료하세요.)")
        created = _expect(create_response, 201, "체크인 생성")
        checkin_id = created["checkin_id"]
        steps.append("CHECKIN_CREATED")

        mode = _expect(
            client.patch(
                f"/api/v1/check-ins/{checkin_id}/shopping-mode",
                headers=headers,
                json={"shopping_mode": "PRIVATE"},
            ),
            200,
            "프라이빗 쇼핑 선택",
        )
        if mode.get("status") != "SELF_SHOPPING":
            raise RehearsalError("프라이빗 쇼핑 선택 실패 (SELF_SHOPPING 상태 아님)")
        steps.append("PRIVATE_MODE_SELECTED")

        lookbook = _expect(
            client.post(f"/api/v1/check-ins/{checkin_id}/lookbook", headers=headers),
            200,
            "룩북 생성",
        )
        look_count = len(lookbook.get("looks", []))
        if look_count < 1:
            raise RehearsalError("룩북 생성 실패 (추천 상품 없음)")
        steps.append("LOOKBOOK_READY")
    finally:
        if checkin_id and access_token:
            cancel = client.post(
                f"/api/v1/check-ins/{checkin_id}/cancel",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            cleanup = "CANCELLED" if cancel.status_code == 200 else f"FAILED_{cancel.status_code}"
        if refresh_token:
            client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})

    if cleanup != "CANCELLED":
        raise RehearsalError(f"리허설 체크인 정리 실패 ({cleanup})")
    steps.extend(("CHECKIN_CANCELLED", "LOGOUT_REQUESTED"))
    return RehearsalResult(
        status="PASSED",
        checkin_id=checkin_id,
        store_id=store_id,
        look_count=look_count,
        cleanup=cleanup,
        steps=tuple(steps),
    )


def run_staff_assisted_rehearsal(
    client: httpx.Client,
    config: StaffRehearsalConfig,
) -> StaffRehearsalResult:
    """고객 동의부터 직원 배정·가이드·방문 완료까지 접객 시나리오를 검증한다."""
    # [Backend-09-'직원 응대 시연 리허설'] 테스트 방문만 생성하고 실패 시 고객 권한으로 정리한다.
    steps: list[str] = []
    customer_access: str | None = None
    customer_refresh: str | None = None
    staff_refresh: str | None = None
    checkin_id: str | None = None
    store_id = ""
    guide_product_count = 0
    completed = False
    cleanup = "NOT_REQUIRED"

    try:
        _expect(client.get("/health/ready"), 200, "readiness")
        steps.append("HEALTH_READY")
        entry = _expect(client.get(f"/api/v1/entry-tags/{config.entry_token}"), 200, "QR 태그 검증")
        store_id = entry["store"]["store_id"]
        if entry.get("channel") != "QR":
            raise RehearsalError("QR 태그 검증 실패 (QR 채널 아님)")
        redirect = client.get(f"/entry/{config.entry_token}", follow_redirects=False)
        expected_location = f"{config.frontend_base_url}/check-in?tag_token={config.entry_token}"
        if redirect.status_code not in {302, 307} or redirect.headers.get("location") != expected_location:
            raise RehearsalError("QR 리다이렉트 실패 (프론트 체크인 주소 불일치)")
        steps.extend(("QR_TAG_VALID", "QR_REDIRECT_VALID"))

        customer_login = _expect(
            client.post(
                "/api/v1/auth/login",
                json={"email": config.customer_email, "password": config.customer_password},
            ),
            200,
            "고객 로그인",
        )
        customer_refresh = customer_login.get("refresh_token")
        if customer_login.get("user", {}).get("role") != "CUSTOMER":
            raise RehearsalError("고객 로그인 실패 (CUSTOMER 역할 아님)")
        customer_access = customer_login["access_token"]
        customer_headers = {"Authorization": f"Bearer {customer_access}"}
        steps.append("CUSTOMER_LOGIN")

        create_response = client.post(
            "/api/v1/check-ins",
            headers=customer_headers,
            json={"tag_token": config.entry_token},
        )
        if create_response.status_code == 409:
            raise RehearsalError("체크인 생성 실패 (데모 고객의 활성 체크인을 먼저 종료하세요.)")
        checkin_id = _expect(create_response, 201, "체크인 생성")["checkin_id"]
        steps.append("CHECKIN_CREATED")

        mode = _expect(
            client.patch(
                f"/api/v1/check-ins/{checkin_id}/shopping-mode",
                headers=customer_headers,
                json={"shopping_mode": "STAFF_ASSISTED"},
            ),
            200,
            "직원 응대 선택",
        )
        if mode.get("shopping_mode") != "STAFF_ASSISTED":
            raise RehearsalError("직원 응대 선택 실패")
        steps.append("STAFF_ASSISTED_SELECTED")

        service_request = _expect(
            client.post(
                f"/api/v1/check-ins/{checkin_id}/service-request",
                headers=customer_headers,
                json={
                    "consent": {
                        "agreed": True,
                        "policy_version": "staff-profile-share-v1",
                        "scopes": ["PURCHASE_HISTORY", "STYLE_PROFILE"],
                    },
                    "visit_purpose": {"code": "FREE_SHOPPING"},
                },
            ),
            202,
            "직원 응대 요청",
        )
        if service_request.get("status") != "WAITING_FOR_STAFF":
            raise RehearsalError("직원 응대 요청 실패 (대기 상태 아님)")
        steps.append("WAITING_FOR_STAFF")

        staff_login = _expect(
            client.post(
                "/api/v1/auth/login",
                json={"email": config.staff_email, "password": config.staff_password},
            ),
            200,
            "직원 로그인",
        )
        staff_refresh = staff_login.get("refresh_token")
        if staff_login.get("user", {}).get("role") != "STAFF":
            raise RehearsalError("직원 로그인 실패 (STAFF 역할 아님)")
        staff_access = staff_login["access_token"]
        staff_headers = {"Authorization": f"Bearer {staff_access}"}
        steps.append("STAFF_LOGIN")

        queue = _expect(
            client.get(
                f"/api/v1/staff/stores/{store_id}/visits",
                headers=staff_headers,
                params={"status": "WAITING_FOR_STAFF"},
            ),
            200,
            "직원 대기열 조회",
        )
        if not any(item.get("checkin_id") == checkin_id for item in queue.get("items", [])):
            raise RehearsalError("직원 대기열 조회 실패 (테스트 방문 없음)")
        steps.append("QUEUE_VISIBLE")

        claimed = _expect(
            client.post(f"/api/v1/staff/check-ins/{checkin_id}/claim", headers=staff_headers),
            200,
            "직원 배정",
        )
        if claimed.get("status") != "ASSIGNED":
            raise RehearsalError("직원 배정 실패 (ASSIGNED 상태 아님)")
        steps.append("STAFF_ASSIGNED")

        guide = _expect(
            client.get(f"/api/v1/staff/check-ins/{checkin_id}/guide", headers=staff_headers),
            200,
            "직원 가이드 생성",
        )
        guide_product_count = len(guide.get("recommended_products", []))
        if guide_product_count < 1:
            raise RehearsalError("직원 가이드 생성 실패 (추천 상품 없음)")
        steps.append("STAFF_GUIDE_READY")

        serving = _expect(
            client.patch(
                f"/api/v1/staff/check-ins/{checkin_id}/status",
                headers=staff_headers,
                json={"status": "SERVING"},
            ),
            200,
            "응대 시작",
        )
        if serving.get("status") != "SERVING":
            raise RehearsalError("응대 시작 실패")
        steps.append("SERVING")

        finished = _expect(
            client.patch(
                f"/api/v1/staff/check-ins/{checkin_id}/status",
                headers=staff_headers,
                json={"status": "COMPLETED"},
            ),
            200,
            "방문 완료",
        )
        if finished.get("status") != "COMPLETED":
            raise RehearsalError("방문 완료 실패")
        completed = True
        cleanup = "COMPLETED"
        steps.append("VISIT_COMPLETED")
    finally:
        if checkin_id and customer_access and not completed:
            cancel = client.post(
                f"/api/v1/check-ins/{checkin_id}/cancel",
                headers={"Authorization": f"Bearer {customer_access}"},
            )
            cleanup = "CANCELLED" if cancel.status_code == 200 else f"FAILED_{cancel.status_code}"
        if staff_refresh:
            client.post("/api/v1/auth/logout", json={"refresh_token": staff_refresh})
        if customer_refresh:
            client.post("/api/v1/auth/logout", json={"refresh_token": customer_refresh})

    if cleanup != "COMPLETED":
        raise RehearsalError(f"직원 응대 리허설이 완료되지 않았습니다 ({cleanup})")
    steps.append("USERS_LOGOUT_REQUESTED")
    return StaffRehearsalResult(
        status="PASSED",
        checkin_id=checkin_id,
        store_id=store_id,
        guide_product_count=guide_product_count,
        cleanup=cleanup,
        steps=tuple(steps),
    )


def _validate_api_base_url(value: str, allow_http_local: bool) -> str:
    parsed = urlsplit(value.strip())
    is_local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
    if (
        not parsed.netloc
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or (parsed.scheme != "https" and not (allow_http_local and is_local_http))
    ):
        raise ValueError("API 주소는 HTTPS origin이어야 하며 로컬 HTTP는 --allow-http-local에서만 허용됩니다.")
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def main() -> None:
    parser = argparse.ArgumentParser(description="M-Journey QR 시연 리허설")
    parser.add_argument("--api-base-url", default=os.getenv("M_JOURNEY_PUBLIC_API_BASE_URL"))
    parser.add_argument("--customer-email", default="customer@example.com")
    parser.add_argument("--staff-email", default="staff@example.com")
    parser.add_argument("--scenario", choices=("private", "staff", "all"), default="all")
    parser.add_argument("--allow-http-local", action="store_true")
    args = parser.parse_args()
    settings = load_settings()
    customer_password = os.getenv("M_JOURNEY_DEMO_PASSWORD")
    if not customer_password:
        raise ValueError("M_JOURNEY_DEMO_PASSWORD 환경변수가 필요합니다.")
    api_base_url = _validate_api_base_url(args.api_base_url or "", args.allow_http_local)
    with httpx.Client(base_url=api_base_url, timeout=15, follow_redirects=False) as client:
        results = []
        if args.scenario in {"private", "all"}:
            results.append(
                run_customer_demo_rehearsal(
                    client,
                    RehearsalConfig(
                        frontend_base_url=settings.frontend_base_url,
                        entry_token=settings.demo_qr_token,
                        customer_email=args.customer_email,
                        customer_password=customer_password,
                    ),
                )
            )
        if args.scenario in {"staff", "all"}:
            results.append(
                run_staff_assisted_rehearsal(
                    client,
                    StaffRehearsalConfig(
                        frontend_base_url=settings.frontend_base_url,
                        entry_token=settings.demo_qr_token,
                        customer_email=args.customer_email,
                        customer_password=customer_password,
                        staff_email=args.staff_email,
                        staff_password=customer_password,
                    ),
                )
            )
    print(json.dumps({"status": "PASSED", "results": [asdict(result) for result in results]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
