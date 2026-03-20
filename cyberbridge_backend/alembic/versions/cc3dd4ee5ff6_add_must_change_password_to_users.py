"""Add must_change_password to users

Revision ID: cc3dd4ee5ff6
Revises: bb2cc3dd4ee5
Create Date: 2026-02-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc3dd4ee5ff6'
down_revision: Union[str, None] = 'bb2cc3dd4ee5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
    op.drop_column('users', 'must_change_password')
