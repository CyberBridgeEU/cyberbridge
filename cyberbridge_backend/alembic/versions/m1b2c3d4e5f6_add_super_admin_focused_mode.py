"""Add super_admin_focused_mode to llm_settings

Revision ID: m1b2c3d4e5f6
Revises: l0a1b2c3d4e5
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'm1b2c3d4e5f6'
down_revision: Union[str, None] = 'l0a1b2c3d4e5'
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
    # Add super_admin_focused_mode column to llm_settings table
    if table_exists('llm_settings'):
        if not column_exists('llm_settings', 'super_admin_focused_mode'):
            op.add_column('llm_settings',
                          sa.Column('super_admin_focused_mode', sa.Boolean(), nullable=True))
            op.execute("UPDATE llm_settings SET super_admin_focused_mode = false WHERE super_admin_focused_mode IS NULL")
            op.alter_column('llm_settings', 'super_admin_focused_mode',
                            existing_type=sa.Boolean(),
                            nullable=False,
                            server_default='false')


def downgrade() -> None:
    # Remove super_admin_focused_mode column from llm_settings
    if table_exists('llm_settings'):
        if column_exists('llm_settings', 'super_admin_focused_mode'):
            op.drop_column('llm_settings', 'super_admin_focused_mode')
