from app.database import normalize_database_url


def test_normalize_render_postgres_url_for_psycopg() -> None:
    assert normalize_database_url("postgresql://user:password@host/database") == (
        "postgresql+psycopg://user:password@host/database"
    )
    assert normalize_database_url("postgres://user:password@host/database") == (
        "postgresql+psycopg://user:password@host/database"
    )


def test_normalize_database_url_preserves_explicit_driver_and_sqlite() -> None:
    postgres_url = "postgresql+psycopg://user:password@host/database"
    sqlite_url = "sqlite:///./mjourney.db"

    assert normalize_database_url(postgres_url) == postgres_url
    assert normalize_database_url(sqlite_url) == sqlite_url
