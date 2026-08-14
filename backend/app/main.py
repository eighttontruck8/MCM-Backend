from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import load_settings
from app.ai import AIProvider, AIService, RuleBasedAIProvider
from app.database import Database
from app.errors import DomainError
from app.events import EventBroker, InMemoryEventBroker
from app.routers import auth, catalog, checkins, customer_features, health, recommendations, staff, websockets
from app.seed import seed_database


def create_app(
    database_url: str | None = None,
    *,
    jwt_secret: str | None = None,
    demo_password: str | None = None,
    ai_provider: AIProvider | None = None,
    ai_timeout_seconds: float | None = None,
    ai_max_retries: int | None = None,
    event_broker: EventBroker | None = None,
) -> FastAPI:
    settings = load_settings()
    database = Database(database_url or settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        database.create_schema()
        with database.session_factory() as session:
            seed_database(session, demo_password if demo_password is not None else settings.demo_password)
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
    application.state.access_token_expire_minutes = settings.access_token_expire_minutes
    application.state.refresh_token_expire_days = settings.refresh_token_expire_days
    application.state.ai_service = AIService(
        ai_provider or RuleBasedAIProvider(),
        timeout_seconds=ai_timeout_seconds if ai_timeout_seconds is not None else settings.ai_timeout_seconds,
        max_retries=ai_max_retries if ai_max_retries is not None else settings.ai_max_retries,
    )
    application.state.event_broker = event_broker or InMemoryEventBroker()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", f"req_{uuid4().hex}")
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @application.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
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
    application.include_router(auth.router)
    application.include_router(catalog.router)
    application.include_router(customer_features.router)
    application.include_router(checkins.router)
    application.include_router(staff.router)
    application.include_router(recommendations.router)
    application.include_router(websockets.router)
    return application


app = create_app()
