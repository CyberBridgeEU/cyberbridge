"""Add cra_mode_enabled and cra_operator_role to organisations

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2026-02-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, None] = 'f6g7h8i9j0k1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    bind = op.get_bind()
    insp = inspect(bind)
    columns = [col['name'] for col in insp.get_columns(table_name)]
    return column_name in columns


def table_exists(table_name):
    """Check if a table exists."""
    bind = op.get_bind()
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def upgrade() -> None:
    if table_exists('organisations'):
        if not column_exists('organisations', 'cra_mode_enabled'):
            op.add_column('organisations',
                          sa.Column('cra_mode_enabled', sa.Boolean(), nullable=True))
            op.execute("UPDATE organisations SET cra_mode_enabled = false WHERE cra_mode_enabled IS NULL")
            op.alter_column('organisations', 'cra_mode_enabled',
                            existing_type=sa.Boolean(),
                            nullable=False,
                            server_default='false')

        if not column_exists('organisations', 'cra_operator_role'):
            op.add_column('organisations',
                          sa.Column('cra_operator_role', sa.String(50), nullable=True))


def downgrade() -> None:
    if table_exists('organisations'):
        if column_exists('organisations', 'cra_operator_role'):
            op.drop_column('organisations', 'cra_operator_role')
        if column_exists('organisations', 'cra_mode_enabled'):
            op.drop_column('organisations', 'cra_mode_enabled')
