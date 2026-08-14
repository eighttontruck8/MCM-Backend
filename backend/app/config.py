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


def load_settings() -> Settings:
    origins = os.getenv("M_JOURNEY_CORS_ORIGINS", "http://localhost:5173")
    return Settings(
        database_url=os.getenv("M_JOURNEY_DATABASE_URL", "sqlite:///./mjourney.db"),
        cors_origins=tuple(item.strip() for item in origins.split(",") if item.strip()),
        jwt_secret=os.getenv("M_JOURNEY_JWT_SECRET") or secrets.token_urlsafe(32),
        access_token_expire_minutes=int(os.getenv("M_JOURNEY_ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        refresh_token_expire_days=int(os.getenv("M_JOURNEY_REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        demo_password=os.getenv("M_JOURNEY_DEMO_PASSWORD"),
    )
