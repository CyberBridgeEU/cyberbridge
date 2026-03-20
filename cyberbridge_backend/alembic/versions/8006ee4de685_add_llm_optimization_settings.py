"""add_llm_optimization_settings

Revision ID: 8006ee4de685
Revises: 9e2e5aff846d
Create Date: 2025-10-02 12:12:05.438113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '8006ee4de685'
down_revision: Union[str, None] = '9e2e5aff846d'
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
    # Add LLM optimization settings to llm_settings table
    if table_exists('llm_settings'):
        if not column_exists('llm_settings', 'max_questions_per_framework'):
            op.add_column('llm_settings', sa.Column('max_questions_per_framework', sa.Integer(), nullable=False, server_default='10'))
        if not column_exists('llm_settings', 'llm_timeout_seconds'):
            op.add_column('llm_settings', sa.Column('llm_timeout_seconds', sa.Integer(), nullable=False, server_default='300'))
        if not column_exists('llm_settings', 'min_confidence_threshold'):
            op.add_column('llm_settings', sa.Column('min_confidence_threshold', sa.Integer(), nullable=False, server_default='75'))
        if not column_exists('llm_settings', 'max_correlations'):
            op.add_column('llm_settings', sa.Column('max_correlations', sa.Integer(), nullable=False, server_default='10'))


def downgrade() -> None:
    # Remove LLM optimization settings from llm_settings table
    op.drop_column('llm_settings', 'max_correlations')
    op.drop_column('llm_settings', 'min_confidence_threshold')
    op.drop_column('llm_settings', 'llm_timeout_seconds')
    op.drop_column('llm_settings', 'max_questions_per_framework')
