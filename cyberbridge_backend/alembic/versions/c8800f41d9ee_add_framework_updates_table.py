"""add_framework_updates_table

Revision ID: c8800f41d9ee
Revises: 9442915730d2
Create Date: 2025-10-15 15:34:27.782304

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'c8800f41d9ee'
down_revision: Union[str, None] = '9442915730d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database"""
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    # Only create table if it doesn't exist and required tables exist
    if not table_exists('framework_updates') and table_exists('frameworks') and table_exists('users'):
        op.create_table(
            'framework_updates',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('framework_id', UUID(as_uuid=True), sa.ForeignKey('frameworks.id'), nullable=False),
            sa.Column('version', sa.Integer, nullable=False),
            sa.Column('framework_name', sa.String(50), nullable=False),
            sa.Column('description', sa.Text, nullable=False),
            sa.Column('status', sa.String(50), nullable=False, server_default='available'),
            sa.Column('applied_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('error_message', sa.Text, nullable=True),
            sa.Column('applied_at', sa.DateTime, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
        )


def downgrade() -> None:
    op.drop_table('framework_updates')
