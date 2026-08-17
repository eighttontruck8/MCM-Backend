from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def normalize_database_url(url: str) -> str:
    """Render PostgreSQL URL을 psycopg 3 SQLAlchemy URL로 변환한다."""
    # [Backend-10-'Render PostgreSQL 연결'] Render의 connectionString은 드라이버명이 없으므로 명시한다.
    if url.startswith("postgres://"):
        return f"postgresql+psycopg://{url.removeprefix('postgres://')}"
    if url.startswith("postgresql://"):
        return f"postgresql+psycopg://{url.removeprefix('postgresql://')}"
    return url


class Database:
    def __init__(self, url: str) -> None:
        url = normalize_database_url(url)
        engine_options: dict[str, object] = {}
        if url.startswith("sqlite"):
            engine_options["connect_args"] = {"check_same_thread": False}
        else:
            engine_options["pool_pre_ping"] = True
        if url in {"sqlite://", "sqlite:///:memory:", "sqlite+pysqlite:///:memory:"}:
            engine_options["poolclass"] = StaticPool

        self.engine = create_engine(url, **engine_options)
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
            class_=Session,
        )

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def dispose(self) -> None:
        self.engine.dispose()


def get_db(request: Request) -> Generator[Session, None, None]:
    with request.app.state.database.session_factory() as session:
        yield session
