"""Add AI remediator settings to organization LLM settings

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-01-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
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
    # Add AI remediator columns to organization_llm_settings table
    if table_exists('organization_llm_settings'):
        if not column_exists('organization_llm_settings', 'ai_remediator_enabled'):
            op.add_column('organization_llm_settings',
                          sa.Column('ai_remediator_enabled', sa.Boolean(), nullable=True))
            op.execute("UPDATE organization_llm_settings SET ai_remediator_enabled = false WHERE ai_remediator_enabled IS NULL")
            op.alter_column('organization_llm_settings', 'ai_remediator_enabled',
                            existing_type=sa.Boolean(),
                            nullable=False,
                            server_default='false')

        if not column_exists('organization_llm_settings', 'remediator_prompt_zap'):
            op.add_column('organization_llm_settings',
                          sa.Column('remediator_prompt_zap', sa.Text(), nullable=True))

        if not column_exists('organization_llm_settings', 'remediator_prompt_nmap'):
            op.add_column('organization_llm_settings',
                          sa.Column('remediator_prompt_nmap', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove AI remediator columns from organization_llm_settings
    if table_exists('organization_llm_settings'):
        if column_exists('organization_llm_settings', 'remediator_prompt_nmap'):
            op.drop_column('organization_llm_settings', 'remediator_prompt_nmap')
        if column_exists('organization_llm_settings', 'remediator_prompt_zap'):
            op.drop_column('organization_llm_settings', 'remediator_prompt_zap')
        if column_exists('organization_llm_settings', 'ai_remediator_enabled'):
            op.drop_column('organization_llm_settings', 'ai_remediator_enabled')
