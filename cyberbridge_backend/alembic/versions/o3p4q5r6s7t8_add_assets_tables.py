"""Add assets tables (asset_types and assets)

Revision ID: o3p4q5r6s7t8
Revises: n2o3p4q5r6s7
Create Date: 2026-01-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision: str = 'o3p4q5r6s7t8'
down_revision: Union[str, None] = 'n2o3p4q5r6s7'
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
    # Create asset_types table
    if not table_exists('asset_types'):
        op.create_table(
            'asset_types',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('icon_name', sa.String(100), nullable=True),
            sa.Column('description', sa.Text, nullable=True),
            sa.Column('organisation_id', UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
            sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('last_updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
        )

    # Create assets table
    if not table_exists('assets'):
        op.create_table(
            'assets',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text, nullable=True),
            sa.Column('ip_address', sa.String(500), nullable=True),  # IP address, IP range, or URL
            sa.Column('asset_type_id', UUID(as_uuid=True), sa.ForeignKey('asset_types.id'), nullable=False),
            sa.Column('organisation_id', UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
            sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('last_updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
        )
    else:
        # If assets table already exists, add ip_address column if it doesn't exist
        if not column_exists('assets', 'ip_address'):
            op.add_column('assets', sa.Column('ip_address', sa.String(500), nullable=True))


def downgrade() -> None:
    # Drop assets table first (has FK to asset_types)
    if table_exists('assets'):
        op.drop_table('assets')

    # Drop asset_types table
    if table_exists('asset_types'):
        op.drop_table('asset_types')
