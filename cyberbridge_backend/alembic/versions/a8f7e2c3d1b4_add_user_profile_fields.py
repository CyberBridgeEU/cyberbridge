"""Add user profile fields

Revision ID: a8f7e2c3d1b4
Revises: 6635cb5f9c90
Create Date: 2026-01-19 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'a8f7e2c3d1b4'
down_revision: Union[str, None] = '6635cb5f9c90'
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
    # Add profile fields to users table
    if table_exists('users'):
        if not column_exists('users', 'first_name'):
            op.add_column('users', sa.Column('first_name', sa.String(100), nullable=True))

        if not column_exists('users', 'last_name'):
            op.add_column('users', sa.Column('last_name', sa.String(100), nullable=True))

        if not column_exists('users', 'phone'):
            op.add_column('users', sa.Column('phone', sa.String(50), nullable=True))

        if not column_exists('users', 'job_title'):
            op.add_column('users', sa.Column('job_title', sa.String(100), nullable=True))

        if not column_exists('users', 'department'):
            op.add_column('users', sa.Column('department', sa.String(100), nullable=True))

        if not column_exists('users', 'profile_picture'):
            op.add_column('users', sa.Column('profile_picture', sa.Text(), nullable=True))

        if not column_exists('users', 'timezone'):
            op.add_column('users', sa.Column('timezone', sa.String(100), nullable=True, server_default='UTC'))

        if not column_exists('users', 'notification_preferences'):
            op.add_column('users', sa.Column('notification_preferences', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove profile fields from users table
    if table_exists('users'):
        if column_exists('users', 'first_name'):
            op.drop_column('users', 'first_name')

        if column_exists('users', 'last_name'):
            op.drop_column('users', 'last_name')

        if column_exists('users', 'phone'):
            op.drop_column('users', 'phone')

        if column_exists('users', 'job_title'):
            op.drop_column('users', 'job_title')

        if column_exists('users', 'department'):
            op.drop_column('users', 'department')

        if column_exists('users', 'profile_picture'):
            op.drop_column('users', 'profile_picture')

        if column_exists('users', 'timezone'):
            op.drop_column('users', 'timezone')

        if column_exists('users', 'notification_preferences'):
            op.drop_column('users', 'notification_preferences')
