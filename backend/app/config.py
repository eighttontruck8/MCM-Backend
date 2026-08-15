from __future__ import annotations

import os
import secrets
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
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


def load_settings() -> Settings:
    origins = os.getenv("M_JOURNEY_CORS_ORIGINS", "http://localhost:5173")
    return Settings(
        database_url=os.getenv("M_JOURNEY_DATABASE_URL", "sqlite:///./mjourney.db"),
        cors_origins=tuple(item.strip() for item in origins.split(",") if item.strip()),
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
        frontend_base_url=os.getenv("M_JOURNEY_FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/"),
        demo_qr_token=os.getenv("M_JOURNEY_DEMO_QR_TOKEN", "qr-demo-seoul-001-7f4d0b9e8c2a"),
        auto_create_schema=os.getenv("M_JOURNEY_AUTO_CREATE_SCHEMA", "true").lower() == "true",
        seed_demo_data=os.getenv("M_JOURNEY_SEED_DEMO_DATA", "true").lower() == "true",
    )
