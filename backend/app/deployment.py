from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from urllib.parse import urlsplit

from app.config import Settings, load_settings
from app.database import normalize_database_url


@dataclass(frozen=True, slots=True)
class DeploymentPreflightResult:
    environment: str
    public_api_base_url: str
    frontend_base_url: str
    cors_origins: tuple[str, ...]
    database: str
    qr_entry_url: str


def _production_origin(value: str, variable_name: str) -> str:
    parsed = urlsplit(value.strip())
    blocked_hosts = {"localhost", "127.0.0.1", "::1"}
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.hostname in blocked_hosts
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise ValueError(f"{variable_name}에는 localhost가 아닌 HTTPS origin이 필요합니다.")
    if parsed.hostname == "example.com" or (parsed.hostname or "").endswith(".example.com"):
        raise ValueError(f"{variable_name}의 example.com을 실제 배포 도메인으로 교체해야 합니다.")
    return f"https://{parsed.netloc.lower()}"


def _is_placeholder(value: str | None) -> bool:
    return not value or "<" in value or ">" in value or "replace-with" in value


def validate_production_deployment(
    settings: Settings,
    *,
    public_api_base_url: str | None,
    jwt_secret: str | None,
    demo_password: str | None,
    demo_qr_token: str | None,
    show_qr_url: bool = False,
) -> DeploymentPreflightResult:
    """실제 배포 전에 도메인·DB·비밀값 조합을 검증한다."""
    # [Backend-06-'운영 배포 preflight'] 실제 HTTPS 도메인과 비밀값이 없으면 배포 준비 완료로 판단하지 않는다.
    if settings.environment != "production":
        raise ValueError("배포 preflight는 M_JOURNEY_ENVIRONMENT=production에서만 실행할 수 있습니다.")
    api_origin = _production_origin(public_api_base_url or "", "M_JOURNEY_PUBLIC_API_BASE_URL")
    frontend_origin = _production_origin(settings.frontend_base_url, "M_JOURNEY_FRONTEND_BASE_URL")
    for cors_origin in settings.cors_origins:
        _production_origin(cors_origin, "M_JOURNEY_CORS_ORIGINS")
    normalized_database_url = normalize_database_url(settings.database_url)
    parsed_database = urlsplit(normalized_database_url)
    if (
        not normalized_database_url.startswith("postgresql+psycopg://")
        or not parsed_database.hostname
        or not parsed_database.username
        or _is_placeholder(parsed_database.password)
        or parsed_database.path in {"", "/"}
    ):
        raise ValueError("운영 DB는 PostgreSQL postgresql+psycopg URL이어야 합니다.")
    if settings.auto_create_schema:
        raise ValueError("운영에서는 M_JOURNEY_AUTO_CREATE_SCHEMA=false여야 합니다.")
    if _is_placeholder(jwt_secret) or len(jwt_secret or "") < 32 or jwt_secret == "local-docker-secret-change-before-deploy":
        raise ValueError("운영용 M_JOURNEY_JWT_SECRET은 32자 이상의 별도 비밀값이어야 합니다.")
    if _is_placeholder(demo_password) or len(demo_password or "") < 12:
        raise ValueError("운영용 M_JOURNEY_DEMO_PASSWORD는 12자 이상의 별도 비밀값이어야 합니다.")
    if _is_placeholder(demo_qr_token) or len(demo_qr_token or "") < 24 or demo_qr_token == "qr-demo-seoul-001-7f4d0b9e8c2a":
        raise ValueError("운영용 M_JOURNEY_DEMO_QR_TOKEN은 24자 이상의 별도 난수여야 합니다.")

    qr_token = demo_qr_token if show_qr_url else "<hidden>"
    return DeploymentPreflightResult(
        environment=settings.environment,
        public_api_base_url=api_origin,
        frontend_base_url=frontend_origin,
        cors_origins=settings.cors_origins,
        database="postgresql+psycopg",
        qr_entry_url=f"{api_origin}/entry/{qr_token}",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="M-Journey 운영 배포 환경 사전 검증")
    parser.add_argument(
        "--show-qr-url",
        action="store_true",
        help="실제 QR 제작을 위해 민감한 진입 토큰이 포함된 URL을 표시한다.",
    )
    args = parser.parse_args()
    settings = load_settings()
    result = validate_production_deployment(
        settings,
        public_api_base_url=os.getenv("M_JOURNEY_PUBLIC_API_BASE_URL"),
        jwt_secret=os.getenv("M_JOURNEY_JWT_SECRET"),
        demo_password=os.getenv("M_JOURNEY_DEMO_PASSWORD"),
        demo_qr_token=os.getenv("M_JOURNEY_DEMO_QR_TOKEN"),
        show_qr_url=args.show_qr_url,
    )
    print(json.dumps(asdict(result), ensure_ascii=False))


if __name__ == "__main__":
    main()
