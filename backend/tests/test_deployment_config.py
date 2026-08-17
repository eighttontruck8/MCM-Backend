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
    assert "${PORT:-8000}" in dockerfile


def test_render_blueprint_connects_api_frontend_and_postgres() -> None:
    blueprint = yaml.safe_load((REPOSITORY_ROOT / "render.yaml").read_text(encoding="utf-8"))
    services = {service["name"]: service for service in blueprint["services"]}
    api = services["mjourney-api-eighttontruck8"]
    frontend = services["mjourney-web-eighttontruck8"]

    assert api["runtime"] == "docker"
    assert api["rootDir"] == "backend"
    assert api["healthCheckPath"] == "/health/ready"
    assert api["plan"] == "free"
    api_environment = {item["key"]: item for item in api["envVars"]}
    assert api_environment["M_JOURNEY_DATABASE_URL"]["fromDatabase"] == {
        "name": "mjourney-db-eighttontruck8",
        "property": "connectionString",
    }
    assert api_environment["M_JOURNEY_DEMO_PASSWORD"]["sync"] is False
    assert api_environment["M_JOURNEY_DEMO_QR_TOKEN"]["sync"] is False
    assert api_environment["M_JOURNEY_JWT_SECRET"]["generateValue"] is True

    assert frontend["runtime"] == "static"
    assert frontend["rootDir"] == "frontend"
    # Render의 staticPublishPath는 rootDir가 아닌 저장소 루트를 기준으로 한다.
    assert frontend["staticPublishPath"] == "frontend/dist"
    assert frontend["routes"] == [{"type": "rewrite", "source": "/*", "destination": "/index.html"}]
    frontend_environment = {item["key"]: item for item in frontend["envVars"]}
    assert frontend_environment["VITE_API_BASE_URL"]["value"] == (
        "https://mjourney-api-eighttontruck8.onrender.com"
    )

    assert blueprint["databases"] == [
        {
            "name": "mjourney-db-eighttontruck8",
            "plan": "free",
            "region": "singapore",
            "databaseName": "mjourney",
            "user": "mjourney",
            "ipAllowList": [],
        }
    ]


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
