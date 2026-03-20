"""add_scanner_settings_to_llm_settings

Revision ID: 9987833bf4b3
Revises: 744103372887
Create Date: 2025-10-01 12:20:14.314249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '9987833bf4b3'
down_revision: Union[str, None] = '744103372887'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database"""
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    conn = op.get_bind()
    inspector = inspect(conn)
    if not table_exists(table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # Add scanner settings columns to llm_settings table
    if table_exists('llm_settings'):
        if not column_exists('llm_settings', 'scanners_enabled'):
            op.add_column('llm_settings', sa.Column('scanners_enabled', sa.Boolean(), nullable=False, server_default='true'))
        if not column_exists('llm_settings', 'allowed_scanner_domains'):
            op.add_column('llm_settings', sa.Column('allowed_scanner_domains', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('llm_settings', 'allowed_scanner_domains')
    op.drop_column('llm_settings', 'scanners_enabled')
