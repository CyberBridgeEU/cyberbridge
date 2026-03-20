"""Add onboarding fields to users table

Revision ID: l0a1b2c3d4e5
Revises: k9f0a1b2c3d4
Create Date: 2026-01-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision: str = 'l0a1b2c3d4e5'
down_revision: Union[str, None] = 'k9f0a1b2c3d4'
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
    # Add onboarding fields to users table
    if table_exists('users'):
        if not column_exists('users', 'onboarding_completed'):
            op.add_column('users', sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false'))

        if not column_exists('users', 'onboarding_completed_at'):
            op.add_column('users', sa.Column('onboarding_completed_at', sa.DateTime(), nullable=True))

        if not column_exists('users', 'onboarding_skipped'):
            op.add_column('users', sa.Column('onboarding_skipped', sa.Boolean(), nullable=False, server_default='false'))

        # Mark all existing admin users as having completed onboarding
        # This prevents existing admins from seeing the wizard on next login
        conn = op.get_bind()
        conn.execute(text("""
            UPDATE users
            SET onboarding_completed = true, onboarding_completed_at = NOW()
            WHERE role_id IN (
                SELECT id FROM roles WHERE role_name IN ('org_admin', 'super_admin')
            )
        """))


def downgrade() -> None:
    # Remove onboarding fields from users table
    if table_exists('users'):
        if column_exists('users', 'onboarding_completed'):
            op.drop_column('users', 'onboarding_completed')

        if column_exists('users', 'onboarding_completed_at'):
            op.drop_column('users', 'onboarding_completed_at')

        if column_exists('users', 'onboarding_skipped'):
            op.drop_column('users', 'onboarding_skipped')
