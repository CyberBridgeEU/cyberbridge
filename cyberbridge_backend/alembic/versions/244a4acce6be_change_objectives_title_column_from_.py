"""Change objectives title column from varchar to text

Revision ID: 244a4acce6be
Revises: c8800f41d9ee
Create Date: 2025-10-16 13:03:20.024262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '244a4acce6be'
down_revision: Union[str, None] = 'c8800f41d9ee'
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
    # Change objectives title column from VARCHAR(255) to TEXT
    if table_exists('objectives') and column_exists('objectives', 'title'):
        op.alter_column('objectives', 'title',
                        existing_type=sa.String(length=255),
                        type_=sa.Text(),
                        existing_nullable=False)


def downgrade() -> None:
    # Revert objectives title column from TEXT back to VARCHAR(255)
    op.alter_column('objectives', 'title',
                    existing_type=sa.Text(),
                    type_=sa.String(length=255),
                    existing_nullable=False)
