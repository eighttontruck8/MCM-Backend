from __future__ import annotations

import os
import secrets
from dataclasses import dataclass, field
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
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_password: str | None
    smtp_from: str | None
    smtp_starttls: bool
    smtp_use_ssl: bool
    ai_provider: str
    openai_api_key: str | None = field(repr=False)
    openai_model: str
    openai_base_url: str
    visit_personal_data_retention_days: int
    expired_auth_token_retention_days: int
    audit_log_retention_days: int


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
    ai_provider = os.getenv("M_JOURNEY_AI_PROVIDER", "rule_based").strip().lower()
    if ai_provider not in {"rule_based", "openai"}:
        raise ValueError("M_JOURNEY_AI_PROVIDER는 rule_based 또는 openai여야 합니다.")
    openai_api_key = os.getenv("M_JOURNEY_OPENAI_API_KEY") or None
    if ai_provider == "openai" and not openai_api_key:
        raise ValueError("OpenAI Provider를 사용할 때 M_JOURNEY_OPENAI_API_KEY가 필요합니다.")
    retention_values = {
        "M_JOURNEY_VISIT_PERSONAL_DATA_RETENTION_DAYS": int(
            os.getenv("M_JOURNEY_VISIT_PERSONAL_DATA_RETENTION_DAYS", "90")
        ),
        "M_JOURNEY_EXPIRED_AUTH_TOKEN_RETENTION_DAYS": int(
            os.getenv("M_JOURNEY_EXPIRED_AUTH_TOKEN_RETENTION_DAYS", "7")
        ),
        "M_JOURNEY_AUDIT_LOG_RETENTION_DAYS": int(os.getenv("M_JOURNEY_AUDIT_LOG_RETENTION_DAYS", "365")),
    }
    if any(value < 1 for value in retention_values.values()):
        raise ValueError("개인정보 보존 기간은 1일 이상이어야 합니다.")
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
        smtp_host=os.getenv("M_JOURNEY_SMTP_HOST") or None,
        smtp_port=int(os.getenv("M_JOURNEY_SMTP_PORT", "587")),
        smtp_username=os.getenv("M_JOURNEY_SMTP_USERNAME") or None,
        smtp_password=os.getenv("M_JOURNEY_SMTP_PASSWORD") or None,
        smtp_from=os.getenv("M_JOURNEY_SMTP_FROM") or None,
        smtp_starttls=os.getenv("M_JOURNEY_SMTP_STARTTLS", "true").lower() == "true",
        smtp_use_ssl=os.getenv("M_JOURNEY_SMTP_USE_SSL", "false").lower() == "true",
        ai_provider=ai_provider,
        openai_api_key=openai_api_key,
        openai_model=os.getenv("M_JOURNEY_OPENAI_MODEL", "gpt-4o-mini"),
        openai_base_url=os.getenv("M_JOURNEY_OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        visit_personal_data_retention_days=retention_values[
            "M_JOURNEY_VISIT_PERSONAL_DATA_RETENTION_DAYS"
        ],
        expired_auth_token_retention_days=retention_values[
            "M_JOURNEY_EXPIRED_AUTH_TOKEN_RETENTION_DAYS"
        ],
        audit_log_retention_days=retention_values["M_JOURNEY_AUDIT_LOG_RETENTION_DAYS"],
    )
