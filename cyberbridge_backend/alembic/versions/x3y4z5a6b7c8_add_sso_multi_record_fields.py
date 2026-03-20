"""Add label and is_active to sso_settings, drop sso_enabled

Revision ID: x3y4z5a6b7c8
Revises: w2x3y4z5a6b7
Create Date: 2026-02-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'x3y4z5a6b7c8'
down_revision: Union[str, None] = 'w2x3y4z5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column('sso_settings', sa.Column('label', sa.String(255), nullable=True))
    op.add_column('sso_settings', sa.Column('is_active', sa.Boolean(), server_default='false', nullable=False))

    # Migrate data: set is_active = sso_enabled for existing rows
    op.execute("UPDATE sso_settings SET is_active = sso_enabled")

    # Drop the old sso_enabled column
    op.drop_column('sso_settings', 'sso_enabled')


def downgrade() -> None:
    # Re-add sso_enabled column
    op.add_column('sso_settings', sa.Column('sso_enabled', sa.Boolean(), server_default='false', nullable=False))

    # Migrate data back: set sso_enabled = is_active
    op.execute("UPDATE sso_settings SET sso_enabled = is_active")

    # Drop the new columns
    op.drop_column('sso_settings', 'is_active')
    op.drop_column('sso_settings', 'label')
