"""Add applicable_operators column to objectives

Revision ID: a1b2c3d4e5f6
Revises: z6a7b8c9d0e1
Create Date: 2026-02-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'z6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(bind, table_name):
    """Check if a table exists in the database"""
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def column_exists(bind, table_name, column_name):
    """Check if a column exists in a table"""
    insp = inspect(bind)
    if table_name not in insp.get_table_names():
        return False
    columns = [c['name'] for c in insp.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    bind = op.get_bind()

    if table_exists(bind, 'objectives'):
        if not column_exists(bind, 'objectives', 'applicable_operators'):
            op.add_column('objectives', sa.Column('applicable_operators', sa.String(500), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()

    if table_exists(bind, 'objectives'):
        if column_exists(bind, 'objectives', 'applicable_operators'):
            op.drop_column('objectives', 'applicable_operators')
