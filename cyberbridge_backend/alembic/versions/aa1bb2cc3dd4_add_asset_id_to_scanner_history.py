"""Add asset_id to scanner_history

Revision ID: aa1bb2cc3dd4
Revises: y4z5a6b7c8d9
Create Date: 2026-02-19 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'aa1bb2cc3dd4'
down_revision: Union[str, None] = 'y4z5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scanner_history', sa.Column('asset_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_scanner_history_asset_id',
        'scanner_history', 'assets',
        ['asset_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_scanner_history_asset_id', 'scanner_history', type_='foreignkey')
    op.drop_column('scanner_history', 'asset_id')
