from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str
    cors_origins: tuple[str, ...]


def load_settings() -> Settings:
    origins = os.getenv("M_JOURNEY_CORS_ORIGINS", "http://localhost:5173")
    return Settings(
        database_url=os.getenv("M_JOURNEY_DATABASE_URL", "sqlite:///./mjourney.db"),
        cors_origins=tuple(item.strip() for item in origins.split(",") if item.strip()),
    )
