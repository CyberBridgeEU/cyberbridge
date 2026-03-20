"""add_history_cleanup_configuration

Revision ID: e79f3cb4599b
Revises: 6176e58c8a46
Create Date: 2025-10-01 14:09:40.284246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'e79f3cb4599b'
down_revision: Union[str, None] = '6176e58c8a46'
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
    # Add history cleanup configuration fields to organisations table
    if table_exists('organisations'):
        if not column_exists('organisations', 'history_cleanup_enabled'):
            op.add_column('organisations', sa.Column('history_cleanup_enabled', sa.Boolean(), nullable=False, server_default='false'))
        if not column_exists('organisations', 'history_retention_days'):
            op.add_column('organisations', sa.Column('history_retention_days', sa.Integer(), nullable=False, server_default='30'))
        if not column_exists('organisations', 'history_cleanup_interval_hours'):
            op.add_column('organisations', sa.Column('history_cleanup_interval_hours', sa.Integer(), nullable=False, server_default='24'))

    # Add organisation_id to history table for efficient per-org cleanup queries
    if table_exists('history') and table_exists('organisations'):
        if not column_exists('history', 'organisation_id'):
            op.add_column('history', sa.Column('organisation_id', sa.UUID(), nullable=True))
            op.create_foreign_key('fk_history_organisation', 'history', 'organisations', ['organisation_id'], ['id'])

            # Backfill organisation_id in history table from user's organisation
            if table_exists('users'):
                op.execute("""
                    UPDATE history
                    SET organisation_id = u.organisation_id
                    FROM users u
                    WHERE history.last_user_id = u.id
                """)


def downgrade() -> None:
    # Remove organisation_id from history table
    op.drop_constraint('fk_history_organisation', 'history', type_='foreignkey')
    op.drop_column('history', 'organisation_id')

    # Remove history cleanup configuration fields from organisations table
    op.drop_column('organisations', 'history_cleanup_interval_hours')
    op.drop_column('organisations', 'history_retention_days')
    op.drop_column('organisations', 'history_cleanup_enabled')
