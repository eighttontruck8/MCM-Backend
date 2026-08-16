from __future__ import annotations

from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_compose_connects_api_to_healthy_postgres() -> None:
    compose = yaml.safe_load((REPOSITORY_ROOT / "compose.yaml").read_text(encoding="utf-8"))
    services = compose["services"]

    assert services["db"]["image"] == "postgres:16-alpine"
    assert services["db"]["healthcheck"]["test"][0] == "CMD-SHELL"
    assert services["api"]["depends_on"]["db"]["condition"] == "service_healthy"

    environment = services["api"]["environment"]
    assert environment["M_JOURNEY_DATABASE_URL"].startswith("postgresql+psycopg://")
    assert environment["M_JOURNEY_AUTO_CREATE_SCHEMA"] == "false"


def test_api_image_runs_migrations_as_non_root_user() -> None:
    dockerfile = (REPOSITORY_ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")

    assert "uv sync --frozen --no-dev" in dockerfile
    assert "USER appuser" in dockerfile
    assert "alembic upgrade head && exec uvicorn" in dockerfile


def test_production_environment_templates_share_public_api_contract() -> None:
    backend_environment = (REPOSITORY_ROOT / ".env.production.example").read_text(encoding="utf-8")
    frontend_environment = (REPOSITORY_ROOT / "frontend" / ".env.production.example").read_text(
        encoding="utf-8"
    )
    compose = yaml.safe_load((REPOSITORY_ROOT / "compose.yaml").read_text(encoding="utf-8"))

    assert "M_JOURNEY_PUBLIC_API_BASE_URL=https://api.example.com" in backend_environment
    assert "M_JOURNEY_FRONTEND_BASE_URL=https://app.example.com" in backend_environment
    assert "VITE_API_BASE_URL=https://api.example.com" in frontend_environment
    assert "M_JOURNEY_PUBLIC_API_BASE_URL" in compose["services"]["api"]["environment"]
