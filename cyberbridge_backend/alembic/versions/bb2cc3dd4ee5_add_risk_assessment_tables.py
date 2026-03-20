"""Add risk assessment tables

Revision ID: bb2cc3dd4ee5
Revises: aa1bb2cc3dd4
Create Date: 2026-02-19 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'bb2cc3dd4ee5'
down_revision: Union[str, None] = 'aa1bb2cc3dd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create risk_assessments table
    op.create_table(
        'risk_assessments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('risk_id', UUID(as_uuid=True), sa.ForeignKey('risks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assessment_number', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Inherent risk
        sa.Column('inherent_impact', sa.Integer(), nullable=False),
        sa.Column('inherent_likelihood', sa.Integer(), nullable=False),
        sa.Column('inherent_risk_score', sa.Integer(), nullable=False),

        # Current risk
        sa.Column('current_impact', sa.Integer(), nullable=False),
        sa.Column('current_likelihood', sa.Integer(), nullable=False),
        sa.Column('current_risk_score', sa.Integer(), nullable=False),

        # Target risk
        sa.Column('target_impact', sa.Integer(), nullable=True),
        sa.Column('target_likelihood', sa.Integer(), nullable=True),
        sa.Column('target_risk_score', sa.Integer(), nullable=True),

        # Residual risk
        sa.Column('residual_impact', sa.Integer(), nullable=True),
        sa.Column('residual_likelihood', sa.Integer(), nullable=True),
        sa.Column('residual_risk_score', sa.Integer(), nullable=True),

        # Impact Loss Analysis
        sa.Column('impact_health', sa.Text(), nullable=True),
        sa.Column('impact_financial', sa.Text(), nullable=True),
        sa.Column('impact_service', sa.Text(), nullable=True),
        sa.Column('impact_legal', sa.Text(), nullable=True),
        sa.Column('impact_reputation', sa.Text(), nullable=True),

        sa.Column('status', sa.String(50), nullable=False, server_default='Draft'),

        sa.Column('organisation_id', UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
        sa.Column('assessed_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),

        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),

        # Check constraints for score ranges
        sa.CheckConstraint('inherent_impact >= 1 AND inherent_impact <= 5', name='ck_inherent_impact_range'),
        sa.CheckConstraint('inherent_likelihood >= 1 AND inherent_likelihood <= 5', name='ck_inherent_likelihood_range'),
        sa.CheckConstraint('current_impact >= 1 AND current_impact <= 5', name='ck_current_impact_range'),
        sa.CheckConstraint('current_likelihood >= 1 AND current_likelihood <= 5', name='ck_current_likelihood_range'),
        sa.CheckConstraint('target_impact IS NULL OR (target_impact >= 1 AND target_impact <= 5)', name='ck_target_impact_range'),
        sa.CheckConstraint('target_likelihood IS NULL OR (target_likelihood >= 1 AND target_likelihood <= 5)', name='ck_target_likelihood_range'),
        sa.CheckConstraint('residual_impact IS NULL OR (residual_impact >= 1 AND residual_impact <= 5)', name='ck_residual_impact_range'),
        sa.CheckConstraint('residual_likelihood IS NULL OR (residual_likelihood >= 1 AND residual_likelihood <= 5)', name='ck_residual_likelihood_range'),
    )

    # Create risk_treatment_actions table
    op.create_table(
        'risk_treatment_actions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('assessment_id', UUID(as_uuid=True), sa.ForeignKey('risk_assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('owner', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='Open'),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('risk_treatment_actions')
    op.drop_table('risk_assessments')
