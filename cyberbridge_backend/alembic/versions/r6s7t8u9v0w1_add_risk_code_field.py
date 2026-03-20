"""Add risk_code field to risks and risk_categories tables

Revision ID: r6s7t8u9v0w1
Revises: q5r6s7t8u9v0
Create Date: 2026-02-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'r6s7t8u9v0w1'
down_revision: Union[str, None] = 'q5r6s7t8u9v0'
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
    # Add risk_code column to risks table
    if table_exists('risks') and not column_exists('risks', 'risk_code'):
        op.add_column('risks', sa.Column('risk_code', sa.String(50), nullable=True))

    # Add risk_code column to risk_categories table
    if table_exists('risk_categories') and not column_exists('risk_categories', 'risk_code'):
        op.add_column('risk_categories', sa.Column('risk_code', sa.String(50), nullable=True))


def downgrade() -> None:
    # Remove risk_code column from risks table
    if table_exists('risks') and column_exists('risks', 'risk_code'):
        op.drop_column('risks', 'risk_code')

    # Remove risk_code column from risk_categories table
    if table_exists('risk_categories') and column_exists('risk_categories', 'risk_code'):
        op.drop_column('risk_categories', 'risk_code')
