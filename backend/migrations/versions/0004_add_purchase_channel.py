"""add purchase channel

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # [Backend-Staff-01-'온오프라인 구매 채널'] 기존 이력은 안전하게 ONLINE으로 보강한다.
    with op.batch_alter_table("purchase_history") as batch_op:
        batch_op.add_column(sa.Column("channel", sa.String(length=20), nullable=False, server_default="ONLINE"))
        batch_op.create_check_constraint("ck_purchase_history_channel", "channel IN ('ONLINE', 'OFFLINE')")


def downgrade() -> None:
    with op.batch_alter_table("purchase_history") as batch_op:
        batch_op.drop_constraint("ck_purchase_history_channel", type_="check")
        batch_op.drop_column("channel")
