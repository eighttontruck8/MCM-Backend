from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.database import Base


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations").replace("%", "%%"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def test_initial_migration_matches_models_and_downgrades(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv("M_JOURNEY_DATABASE_URL", raising=False)
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'migration.db').as_posix()}"
    config = alembic_config(database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert set(Base.metadata.tables).issubset(set(inspector.get_table_names()))
    assert "alembic_version" in inspector.get_table_names()
    customer_columns = {column["name"] for column in inspector.get_columns("customers")}
    assert "phone" in customer_columns
    customer_indexes = {index["name"]: index for index in inspector.get_indexes("customers")}
    assert customer_indexes["ix_customers_phone"]["unique"] == 1
    inventory_constraints = {
        constraint["name"] for constraint in inspector.get_check_constraints("inventories")
    }
    assert "ck_inventories_quantity_nonnegative" in inventory_constraints
    engine.dispose()

    command.check(config)
    command.downgrade(config, "base")

    engine = create_engine(database_url)
    assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
    engine.dispose()
