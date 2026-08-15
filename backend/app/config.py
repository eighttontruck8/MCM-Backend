from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    database_url: str
    cors_origins: tuple[str, ...]
    jwt_secret: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    demo_password: str | None
    ai_timeout_seconds: float
    ai_max_retries: int
    password_reset_expire_minutes: int
    expose_password_reset_token: bool
    rate_limit_window_seconds: int
    login_rate_limit: int
    password_reset_rate_limit: int
    ai_rate_limit: int
    frontend_base_url: str
    demo_qr_token: str
    auto_create_schema: bool
    seed_demo_data: bool


def _normalize_origin(value: str) -> str:
    parsed = urlsplit(value.strip())
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise ValueError(f"유효하지 않은 CORS origin입니다: {value}")
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


def _load_cors_origins(raw_origins: str, environment: str, frontend_base_url: str) -> tuple[str, ...]:
    values = [item.strip() for item in raw_origins.split(",") if item.strip()]
    if not values or "*" in values:
        raise ValueError("M_JOURNEY_CORS_ORIGINS에는 명시적인 프론트 origin이 필요합니다.")

    origins = tuple(dict.fromkeys(_normalize_origin(value) for value in values))
    if environment == "production":
        # [Backend-02-'운영 CORS 화이트리스트'] 운영에서는 HTTPS 프론트 origin만 허용한다.
        blocked_hosts = {"localhost", "127.0.0.1", "::1"}
        if any(urlsplit(origin).scheme != "https" or urlsplit(origin).hostname in blocked_hosts for origin in origins):
            raise ValueError("운영 CORS origin은 localhost가 아닌 HTTPS 주소여야 합니다.")
        if _normalize_origin(frontend_base_url) not in origins:
            raise ValueError("운영 프론트 주소는 M_JOURNEY_CORS_ORIGINS에 포함되어야 합니다.")
    return origins


def load_settings() -> Settings:
    environment = os.getenv("M_JOURNEY_ENVIRONMENT", "development").strip().lower()
    if environment not in {"development", "test", "production"}:
        raise ValueError("M_JOURNEY_ENVIRONMENT는 development, test, production 중 하나여야 합니다.")

    origins = os.getenv("M_JOURNEY_CORS_ORIGINS", "http://localhost:5173")
    frontend_base_url = os.getenv("M_JOURNEY_FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
    return Settings(
        environment=environment,
        database_url=os.getenv("M_JOURNEY_DATABASE_URL", "sqlite:///./mjourney.db"),
        cors_origins=_load_cors_origins(origins, environment, frontend_base_url),
        jwt_secret=os.getenv("M_JOURNEY_JWT_SECRET") or secrets.token_urlsafe(32),
        access_token_expire_minutes=int(os.getenv("M_JOURNEY_ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        refresh_token_expire_days=int(os.getenv("M_JOURNEY_REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        demo_password=os.getenv("M_JOURNEY_DEMO_PASSWORD"),
        ai_timeout_seconds=float(os.getenv("M_JOURNEY_AI_TIMEOUT_SECONDS", "10")),
        ai_max_retries=int(os.getenv("M_JOURNEY_AI_MAX_RETRIES", "1")),
        password_reset_expire_minutes=int(os.getenv("M_JOURNEY_PASSWORD_RESET_EXPIRE_MINUTES", "15")),
        expose_password_reset_token=os.getenv("M_JOURNEY_EXPOSE_PASSWORD_RESET_TOKEN", "false").lower() == "true",
        rate_limit_window_seconds=int(os.getenv("M_JOURNEY_RATE_LIMIT_WINDOW_SECONDS", "60")),
        login_rate_limit=int(os.getenv("M_JOURNEY_LOGIN_RATE_LIMIT", "10")),
        password_reset_rate_limit=int(os.getenv("M_JOURNEY_PASSWORD_RESET_RATE_LIMIT", "5")),
        ai_rate_limit=int(os.getenv("M_JOURNEY_AI_RATE_LIMIT", "10")),
        frontend_base_url=frontend_base_url,
        demo_qr_token=os.getenv("M_JOURNEY_DEMO_QR_TOKEN", "qr-demo-seoul-001-7f4d0b9e8c2a"),
        auto_create_schema=os.getenv("M_JOURNEY_AUTO_CREATE_SCHEMA", "true").lower() == "true",
        seed_demo_data=os.getenv("M_JOURNEY_SEED_DEMO_DATA", "true").lower() == "true",
    )
