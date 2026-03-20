"""Add additional AI providers (OpenAI, Anthropic, X AI, Google)

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-01-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'e3f4a5b6c7d8'
down_revision: Union[str, None] = 'd2e3f4a5b6c7'
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
    # Add OpenAI (ChatGPT) columns to organization_llm_settings
    if table_exists('organization_llm_settings'):
        if not column_exists('organization_llm_settings', 'openai_api_key'):
            op.add_column('organization_llm_settings',
                          sa.Column('openai_api_key', sa.Text(), nullable=True))

        if not column_exists('organization_llm_settings', 'openai_model'):
            op.add_column('organization_llm_settings',
                          sa.Column('openai_model', sa.String(100), nullable=True))

        if not column_exists('organization_llm_settings', 'openai_base_url'):
            op.add_column('organization_llm_settings',
                          sa.Column('openai_base_url', sa.Text(), nullable=True))

        # Add Anthropic (Claude) columns
        if not column_exists('organization_llm_settings', 'anthropic_api_key'):
            op.add_column('organization_llm_settings',
                          sa.Column('anthropic_api_key', sa.Text(), nullable=True))

        if not column_exists('organization_llm_settings', 'anthropic_model'):
            op.add_column('organization_llm_settings',
                          sa.Column('anthropic_model', sa.String(100), nullable=True))

        # Add X AI (Grok) columns
        if not column_exists('organization_llm_settings', 'xai_api_key'):
            op.add_column('organization_llm_settings',
                          sa.Column('xai_api_key', sa.Text(), nullable=True))

        if not column_exists('organization_llm_settings', 'xai_model'):
            op.add_column('organization_llm_settings',
                          sa.Column('xai_model', sa.String(100), nullable=True))

        if not column_exists('organization_llm_settings', 'xai_base_url'):
            op.add_column('organization_llm_settings',
                          sa.Column('xai_base_url', sa.Text(), nullable=True))

        # Add Google (Gemini) columns
        if not column_exists('organization_llm_settings', 'google_api_key'):
            op.add_column('organization_llm_settings',
                          sa.Column('google_api_key', sa.Text(), nullable=True))

        if not column_exists('organization_llm_settings', 'google_model'):
            op.add_column('organization_llm_settings',
                          sa.Column('google_model', sa.String(100), nullable=True))


def downgrade() -> None:
    # Remove additional AI provider columns from organization_llm_settings
    if table_exists('organization_llm_settings'):
        # Remove Google (Gemini) columns
        if column_exists('organization_llm_settings', 'google_model'):
            op.drop_column('organization_llm_settings', 'google_model')
        if column_exists('organization_llm_settings', 'google_api_key'):
            op.drop_column('organization_llm_settings', 'google_api_key')

        # Remove X AI (Grok) columns
        if column_exists('organization_llm_settings', 'xai_base_url'):
            op.drop_column('organization_llm_settings', 'xai_base_url')
        if column_exists('organization_llm_settings', 'xai_model'):
            op.drop_column('organization_llm_settings', 'xai_model')
        if column_exists('organization_llm_settings', 'xai_api_key'):
            op.drop_column('organization_llm_settings', 'xai_api_key')

        # Remove Anthropic (Claude) columns
        if column_exists('organization_llm_settings', 'anthropic_model'):
            op.drop_column('organization_llm_settings', 'anthropic_model')
        if column_exists('organization_llm_settings', 'anthropic_api_key'):
            op.drop_column('organization_llm_settings', 'anthropic_api_key')

        # Remove OpenAI (ChatGPT) columns
        if column_exists('organization_llm_settings', 'openai_base_url'):
            op.drop_column('organization_llm_settings', 'openai_base_url')
        if column_exists('organization_llm_settings', 'openai_model'):
            op.drop_column('organization_llm_settings', 'openai_model')
        if column_exists('organization_llm_settings', 'openai_api_key'):
            op.drop_column('organization_llm_settings', 'openai_api_key')
