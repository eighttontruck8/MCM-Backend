from __future__ import annotations

from contextlib import asynccontextmanager
import json
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import load_settings
from app.ai import AIProvider, AIService, RuleBasedAIProvider
from app.ai_openai import OpenAIResponsesProvider
from app.database import Database
from app.errors import DomainError
from app.events import EventBroker, InMemoryEventBroker
from app.mail import PasswordResetMailer, build_password_reset_mailer
from app.routers import auth, catalog, checkins, customer_features, entry, health, recommendations, staff, websockets
from app.rate_limit import InMemoryRateLimiter
from app.seed import seed_database


request_logger = logging.getLogger("mjourney.request")
request_logger.setLevel(logging.INFO)


def create_app(
    database_url: str | None = None,
    *,
    jwt_secret: str | None = None,
    demo_password: str | None = None,
    ai_provider: AIProvider | None = None,
    ai_timeout_seconds: float | None = None,
    ai_max_retries: int | None = None,
    event_broker: EventBroker | None = None,
    expose_password_reset_token: bool | None = None,
    rate_limits: dict[str, int] | None = None,
    frontend_base_url: str | None = None,
    demo_qr_token: str | None = None,
    auto_create_schema: bool | None = None,
    seed_demo_data: bool | None = None,
    password_reset_mailer: PasswordResetMailer | None = None,
) -> FastAPI:
    settings = load_settings()
    database = Database(database_url or settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        should_create_schema = auto_create_schema if auto_create_schema is not None else settings.auto_create_schema
        should_seed_demo = seed_demo_data if seed_demo_data is not None else settings.seed_demo_data
        if should_create_schema:
            database.create_schema()
        if should_seed_demo:
            with database.session_factory() as session:
                seed_database(
                    session,
                    demo_password if demo_password is not None else settings.demo_password,
                    demo_qr_token or settings.demo_qr_token,
                )
        yield
        database.dispose()

    application = FastAPI(
        title="M-Journey Backend API",
        version="0.1.0",
        description="M-Journey 해커톤 MVP 백엔드",
        lifespan=lifespan,
    )
    application.state.database = database
    application.state.jwt_secret = jwt_secret or settings.jwt_secret
    application.state.frontend_base_url = (frontend_base_url or settings.frontend_base_url).rstrip("/")
    application.state.access_token_expire_minutes = settings.access_token_expire_minutes
    application.state.refresh_token_expire_days = settings.refresh_token_expire_days
    application.state.password_reset_expire_minutes = settings.password_reset_expire_minutes
    application.state.expose_password_reset_token = (
        expose_password_reset_token
        if expose_password_reset_token is not None
        else settings.expose_password_reset_token
    )
    application.state.password_reset_mailer = password_reset_mailer or build_password_reset_mailer(
        host=settings.smtp_host,
        port=settings.smtp_port,
        sender=settings.smtp_from,
        username=settings.smtp_username,
        password=settings.smtp_password,
        starttls=settings.smtp_starttls,
        use_ssl=settings.smtp_use_ssl,
    )
    configured_ai_provider = ai_provider
    if configured_ai_provider is None:
        configured_ai_provider = (
            OpenAIResponsesProvider(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                base_url=settings.openai_base_url,
                timeout_seconds=ai_timeout_seconds if ai_timeout_seconds is not None else settings.ai_timeout_seconds,
            )
            if settings.ai_provider == "openai"
            else RuleBasedAIProvider()
        )
    application.state.ai_service = AIService(
        configured_ai_provider,
        timeout_seconds=ai_timeout_seconds if ai_timeout_seconds is not None else settings.ai_timeout_seconds,
        max_retries=ai_max_retries if ai_max_retries is not None else settings.ai_max_retries,
    )
    application.state.event_broker = event_broker or InMemoryEventBroker()
    application.state.rate_limiter = InMemoryRateLimiter()
    application.state.rate_limit_window_seconds = settings.rate_limit_window_seconds
    configured_rate_limits = {
        "login": settings.login_rate_limit,
        "password_reset": settings.password_reset_rate_limit,
        "ai": settings.ai_rate_limit,
    }
    if rate_limits:
        configured_rate_limits.update(rate_limits)
    application.state.rate_limits = configured_rate_limits
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Retry-After"],
        max_age=600,
    )

    @application.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        started_at = perf_counter()
        status_code = 500
        request_id = request.headers.get("X-Request-ID", f"req_{uuid4().hex}")
        request.state.request_id = request_id
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            route = request.scope.get("route")
            safe_path = getattr(route, "path", request.url.path)
            request_logger.info(
                json.dumps(
                    {
                        "event": "HTTP_REQUEST",
                        "request_id": request_id,
                        "method": request.method,
                        "path": safe_path,
                        "status_code": status_code,
                        "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                    },
                    separators=(",", ":"),
                )
            )
        response.headers["X-Request-ID"] = request_id
        return response

    @application.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        headers = None
        if exc.status_code == 429 and isinstance(exc.details, dict):
            headers = {"Retry-After": str(exc.details.get("retry_after_seconds", 1))}
        return JSONResponse(
            status_code=exc.status_code,
            headers=headers,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                    "request_id": request.state.request_id,
                }
            },
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "요청 값을 확인해주세요.",
                    "details": exc.errors(),
                    "request_id": request.state.request_id,
                }
            },
        )

    application.include_router(health.router)
    application.include_router(entry.router)
    application.include_router(auth.router)
    application.include_router(catalog.router)
    application.include_router(customer_features.router)
    application.include_router(checkins.router)
    application.include_router(staff.router)
    application.include_router(recommendations.router)
    application.include_router(websockets.router)
    return application


app = create_app()
