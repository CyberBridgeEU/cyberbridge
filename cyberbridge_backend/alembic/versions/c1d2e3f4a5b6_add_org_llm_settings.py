"""Add organization LLM settings architecture

Revision ID: c1d2e3f4a5b6
Revises: a8f7e2c3d1b4
Create Date: 2026-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, None] = 'a8f7e2c3d1b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    bind = op.get_bind()
    insp = inspect(bind)
    columns = [col['name'] for col in insp.get_columns(table_name)]
    return column_name in columns


def table_exists(table_name):
    """Check if a table exists."""
    bind = op.get_bind()
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def upgrade() -> None:
    # Add new global settings columns to llm_settings (if they don't exist)
    if not column_exists('llm_settings', 'ai_enabled'):
        op.add_column('llm_settings', sa.Column('ai_enabled', sa.Boolean(), nullable=True))
        op.execute("UPDATE llm_settings SET ai_enabled = true WHERE ai_enabled IS NULL")
        op.alter_column('llm_settings', 'ai_enabled',
                        existing_type=sa.Boolean(),
                        nullable=False,
                        server_default='true')

    if not column_exists('llm_settings', 'default_provider'):
        op.add_column('llm_settings', sa.Column('default_provider', sa.String(50), nullable=True))
        op.execute("UPDATE llm_settings SET default_provider = 'ollama' WHERE default_provider IS NULL")
        op.alter_column('llm_settings', 'default_provider',
                        existing_type=sa.String(50),
                        nullable=False,
                        server_default='ollama')

    # Add QLON configuration columns to llm_settings (if they don't exist)
    if not column_exists('llm_settings', 'llm_provider'):
        op.add_column('llm_settings', sa.Column('llm_provider', sa.String(50), nullable=True))
        op.execute("UPDATE llm_settings SET llm_provider = 'ollama' WHERE llm_provider IS NULL")

    if not column_exists('llm_settings', 'qlon_url'):
        op.add_column('llm_settings', sa.Column('qlon_url', sa.Text(), nullable=True))

    if not column_exists('llm_settings', 'qlon_api_key'):
        op.add_column('llm_settings', sa.Column('qlon_api_key', sa.Text(), nullable=True))

    if not column_exists('llm_settings', 'qlon_use_tools'):
        op.add_column('llm_settings', sa.Column('qlon_use_tools', sa.Boolean(), nullable=True))
        op.execute("UPDATE llm_settings SET qlon_use_tools = true WHERE qlon_use_tools IS NULL")

    # Create organization_llm_settings table (if it doesn't exist)
    if not table_exists('organization_llm_settings'):
        op.create_table(
            'organization_llm_settings',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False, unique=True),
            sa.Column('llm_provider', sa.String(50), nullable=False),
            sa.Column('ollama_url', sa.Text(), nullable=True),
            sa.Column('ollama_model', sa.String(100), nullable=True),
            sa.Column('qlon_url', sa.Text(), nullable=True),
            sa.Column('qlon_api_key', sa.Text(), nullable=True),
            sa.Column('qlon_use_tools', sa.Boolean(), nullable=True),
            sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now())
        )

        # Create index on organisation_id for faster lookups
        op.create_index('ix_organization_llm_settings_org_id', 'organization_llm_settings', ['organisation_id'])


def downgrade() -> None:
    # Drop organization_llm_settings table
    if table_exists('organization_llm_settings'):
        op.drop_index('ix_organization_llm_settings_org_id', table_name='organization_llm_settings')
        op.drop_table('organization_llm_settings')

    # Remove columns from llm_settings
    if column_exists('llm_settings', 'qlon_use_tools'):
        op.drop_column('llm_settings', 'qlon_use_tools')
    if column_exists('llm_settings', 'qlon_api_key'):
        op.drop_column('llm_settings', 'qlon_api_key')
    if column_exists('llm_settings', 'qlon_url'):
        op.drop_column('llm_settings', 'qlon_url')
    if column_exists('llm_settings', 'llm_provider'):
        op.drop_column('llm_settings', 'llm_provider')
    if column_exists('llm_settings', 'default_provider'):
        op.drop_column('llm_settings', 'default_provider')
    if column_exists('llm_settings', 'ai_enabled'):
        op.drop_column('llm_settings', 'ai_enabled')
