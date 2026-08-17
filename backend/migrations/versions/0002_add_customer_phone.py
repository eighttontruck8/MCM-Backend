"""add customer phone

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("phone", sa.String(length=20), nullable=True))
    op.create_index(op.f("ix_customers_phone"), "customers", ["phone"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_customers_phone"), table_name="customers")
    op.drop_column("customers", "phone")
