"""Add AI Policy Aligner feature

Revision ID: n2o3p4q5r6s7
Revises: m1b2c3d4e5f6
Create Date: 2026-01-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'n2o3p4q5r6s7'
down_revision: Union[str, None] = 'm1b2c3d4e5f6'
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
    # Add AI Policy Aligner column to global llm_settings table
    if table_exists('llm_settings'):
        if not column_exists('llm_settings', 'ai_policy_aligner_enabled'):
            op.add_column('llm_settings',
                          sa.Column('ai_policy_aligner_enabled', sa.Boolean(), nullable=True))
            op.execute("UPDATE llm_settings SET ai_policy_aligner_enabled = false WHERE ai_policy_aligner_enabled IS NULL")
            op.alter_column('llm_settings', 'ai_policy_aligner_enabled',
                            existing_type=sa.Boolean(),
                            nullable=False,
                            server_default='false')

    # Add AI Policy Aligner columns to organization_llm_settings table
    if table_exists('organization_llm_settings'):
        if not column_exists('organization_llm_settings', 'ai_policy_aligner_enabled'):
            op.add_column('organization_llm_settings',
                          sa.Column('ai_policy_aligner_enabled', sa.Boolean(), nullable=True))
            op.execute("UPDATE organization_llm_settings SET ai_policy_aligner_enabled = false WHERE ai_policy_aligner_enabled IS NULL")
            op.alter_column('organization_llm_settings', 'ai_policy_aligner_enabled',
                            existing_type=sa.Boolean(),
                            nullable=False,
                            server_default='false')

        if not column_exists('organization_llm_settings', 'policy_aligner_prompt'):
            op.add_column('organization_llm_settings',
                          sa.Column('policy_aligner_prompt', sa.Text(), nullable=True))

    # Create policy_question_alignments table
    if not table_exists('policy_question_alignments'):
        op.create_table(
            'policy_question_alignments',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
            sa.Column('framework_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('frameworks.id'), nullable=False),
            sa.Column('question_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('questions.id'), nullable=False),
            sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('policies.id'), nullable=False),
            sa.Column('confidence_score', sa.Integer(), nullable=False),
            sa.Column('reasoning', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.UniqueConstraint('framework_id', 'question_id', name='uix_framework_question_alignment')
        )

        # Create indexes for faster lookups
        op.create_index('ix_policy_question_alignments_framework_id', 'policy_question_alignments', ['framework_id'])
        op.create_index('ix_policy_question_alignments_organisation_id', 'policy_question_alignments', ['organisation_id'])


def downgrade() -> None:
    # Drop policy_question_alignments table
    if table_exists('policy_question_alignments'):
        op.drop_index('ix_policy_question_alignments_organisation_id', table_name='policy_question_alignments')
        op.drop_index('ix_policy_question_alignments_framework_id', table_name='policy_question_alignments')
        op.drop_table('policy_question_alignments')

    # Remove AI Policy Aligner columns from organization_llm_settings
    if table_exists('organization_llm_settings'):
        if column_exists('organization_llm_settings', 'policy_aligner_prompt'):
            op.drop_column('organization_llm_settings', 'policy_aligner_prompt')
        if column_exists('organization_llm_settings', 'ai_policy_aligner_enabled'):
            op.drop_column('organization_llm_settings', 'ai_policy_aligner_enabled')

    # Remove AI Policy Aligner column from global llm_settings
    if table_exists('llm_settings'):
        if column_exists('llm_settings', 'ai_policy_aligner_enabled'):
            op.drop_column('llm_settings', 'ai_policy_aligner_enabled')
