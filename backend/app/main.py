from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import load_settings
from app.database import Database
from app.errors import DomainError
from app.routers import catalog, checkins, health
from app.seed import seed_database


def create_app(database_url: str | None = None) -> FastAPI:
    settings = load_settings()
    database = Database(database_url or settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        database.create_schema()
        with database.session_factory() as session:
            seed_database(session)
        yield
        database.dispose()

    application = FastAPI(
        title="M-Journey Backend API",
        version="0.1.0",
        description="M-Journey 해커톤 MVP 백엔드",
        lifespan=lifespan,
    )
    application.state.database = database
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
    application.include_router(catalog.router)
    application.include_router(checkins.router)
    return application


app = create_app()
