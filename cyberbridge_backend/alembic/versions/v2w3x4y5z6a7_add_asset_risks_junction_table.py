"""Add asset_risks junction table for Asset-Risk many-to-many relationship

Revision ID: v2w3x4y5z6a7
Revises: u1v2w3x4y5z6
Create Date: 2026-02-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'v2w3x4y5z6a7'
down_revision: Union[str, None] = 'u1v2w3x4y5z6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not table_exists('asset_risks'):
        op.create_table(
            'asset_risks',
            sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('risk_id', UUID(as_uuid=True), sa.ForeignKey('risks.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )


def downgrade() -> None:
    op.drop_table('asset_risks')
