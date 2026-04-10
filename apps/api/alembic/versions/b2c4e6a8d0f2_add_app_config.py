"""add app_config table

Revision ID: b2c4e6a8d0f2
Revises: 5adddc8afc34
Create Date: 2026-04-10 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b2c4e6a8d0f2'
down_revision: Union[str, Sequence[str], None] = '5adddc8afc34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'app_config',
        sa.Column('key',        sa.String(),  nullable=False),
        sa.Column('value',      sa.Text(),    nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('key'),
    )


def downgrade() -> None:
    op.drop_table('app_config')
