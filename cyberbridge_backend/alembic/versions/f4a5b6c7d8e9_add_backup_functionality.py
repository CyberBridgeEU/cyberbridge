"""Add backup functionality

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-01-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'f4a5b6c7d8e9'
down_revision: Union[str, None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    bind = op.get_bind()
    insp = inspect(bind)
    columns = [col['name'] for col in insp.get_columns(table_name)]
    return column_name in columns


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def upgrade() -> None:
    # Add backup configuration fields to organisations table
    if table_exists('organisations'):
        if not column_exists('organisations', 'backup_enabled'):
            op.add_column('organisations', sa.Column('backup_enabled', sa.Boolean(), nullable=False, server_default='true'))
        if not column_exists('organisations', 'backup_frequency'):
            op.add_column('organisations', sa.Column('backup_frequency', sa.String(20), nullable=False, server_default='monthly'))
        if not column_exists('organisations', 'backup_retention_years'):
            op.add_column('organisations', sa.Column('backup_retention_years', sa.Integer(), nullable=False, server_default='10'))
        if not column_exists('organisations', 'last_backup_at'):
            op.add_column('organisations', sa.Column('last_backup_at', sa.DateTime(), nullable=True))
        if not column_exists('organisations', 'last_backup_status'):
            op.add_column('organisations', sa.Column('last_backup_status', sa.String(50), nullable=True))

    # Create backups table
    if not table_exists('backups'):
        op.create_table(
            'backups',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('filename', sa.String(255), nullable=False),
            sa.Column('filepath', sa.String(500), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('backup_type', sa.String(20), nullable=False, server_default='scheduled'),
            sa.Column('status', sa.String(50), nullable=False, server_default='completed'),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('records_count', sa.Text(), nullable=True),
            sa.Column('evidence_files_count', sa.Integer(), nullable=True),
            sa.Column('is_encrypted', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
        )
        # Create index on organisation_id for faster lookups
        op.create_index('ix_backups_organisation_id', 'backups', ['organisation_id'])
        # Create index on expires_at for cleanup queries
        op.create_index('ix_backups_expires_at', 'backups', ['expires_at'])


def downgrade() -> None:
    # Drop backups table
    if table_exists('backups'):
        op.drop_index('ix_backups_expires_at', table_name='backups')
        op.drop_index('ix_backups_organisation_id', table_name='backups')
        op.drop_table('backups')

    # Remove backup configuration fields from organisations table
    if table_exists('organisations'):
        if column_exists('organisations', 'last_backup_status'):
            op.drop_column('organisations', 'last_backup_status')
        if column_exists('organisations', 'last_backup_at'):
            op.drop_column('organisations', 'last_backup_at')
        if column_exists('organisations', 'backup_retention_years'):
            op.drop_column('organisations', 'backup_retention_years')
        if column_exists('organisations', 'backup_frequency'):
            op.drop_column('organisations', 'backup_frequency')
        if column_exists('organisations', 'backup_enabled'):
            op.drop_column('organisations', 'backup_enabled')
