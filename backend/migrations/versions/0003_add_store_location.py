"""add store location

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("stores", sa.Column("address", sa.String(length=255), nullable=True))
    op.add_column("stores", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("stores", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("stores", "longitude")
    op.drop_column("stores", "latitude")
    op.drop_column("stores", "address")
