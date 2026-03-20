"""Add login logo tables

Revision ID: hh8ii9jj0kk1
Revises: gg7hh8ii9jj0
Create Date: 2026-03-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'hh8ii9jj0kk1'
down_revision: Union[str, None] = 'gg7hh8ii9jj0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(bind, table_name):
    """Check if a table exists in the database"""
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()

    if not table_exists(bind, 'login_logos'):
        op.create_table(
            'login_logos',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('logo', sa.Text(), nullable=False),
            sa.Column('is_global', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        )

    if not table_exists(bind, 'login_logo_organisations'):
        op.create_table(
            'login_logo_organisations',
            sa.Column('logo_id', UUID(as_uuid=True), sa.ForeignKey('login_logos.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('organisation_id', UUID(as_uuid=True), sa.ForeignKey('organisations.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        )


def downgrade() -> None:
    bind = op.get_bind()

    if table_exists(bind, 'login_logo_organisations'):
        op.drop_table('login_logo_organisations')
    if table_exists(bind, 'login_logos'):
        op.drop_table('login_logos')
