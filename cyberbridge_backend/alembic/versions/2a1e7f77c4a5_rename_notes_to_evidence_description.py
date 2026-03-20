"""rename_notes_to_evidence_description

Revision ID: 2a1e7f77c4a5
Revises: 8006ee4de685
Create Date: 2025-10-03 12:06:28.608576

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '2a1e7f77c4a5'
down_revision: Union[str, None] = '8006ee4de685'
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
    # Rename 'notes' column to 'evidence_description' in answers table
    if table_exists('answers') and column_exists('answers', 'notes') and not column_exists('answers', 'evidence_description'):
        op.alter_column('answers', 'notes', new_column_name='evidence_description')


def downgrade() -> None:
    # Revert 'evidence_description' column back to 'notes' in answers table
    op.alter_column('answers', 'evidence_description', new_column_name='notes')
