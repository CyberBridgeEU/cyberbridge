"""rename_objectives_body_to_subchapter

Revision ID: 9442915730d2
Revises: 2a1e7f77c4a5
Create Date: 2025-10-14 15:51:02.015001

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '9442915730d2'
down_revision: Union[str, None] = '2a1e7f77c4a5'
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
    # Rename column 'body' to 'subchapter' in objectives table
    if table_exists('objectives') and column_exists('objectives', 'body') and not column_exists('objectives', 'subchapter'):
        op.alter_column('objectives', 'body', new_column_name='subchapter')


def downgrade() -> None:
    # Rename column 'subchapter' back to 'body' in objectives table
    op.alter_column('objectives', 'subchapter', new_column_name='body')
