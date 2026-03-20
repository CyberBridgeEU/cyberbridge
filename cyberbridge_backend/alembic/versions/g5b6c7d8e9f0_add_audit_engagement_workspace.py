"""Add audit engagement workspace tables

Revision ID: g5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-01-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'g5b6c7d8e9f0'
down_revision: Union[str, None] = 'f4a5b6c7d8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def upgrade() -> None:
    # Create auditor_roles table (permissions lookup)
    if not table_exists('auditor_roles'):
        op.create_table(
            'auditor_roles',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('role_name', sa.String(50), unique=True, nullable=False),
            sa.Column('can_comment', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('can_request_evidence', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('can_add_findings', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('can_sign_off', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )

    # Create audit_engagements table (core entity)
    if not table_exists('audit_engagements'):
        op.create_table(
            'audit_engagements',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('assessment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False),
            # Audit period
            sa.Column('audit_period_start', sa.DateTime(), nullable=True),
            sa.Column('audit_period_end', sa.DateTime(), nullable=True),
            # Status
            sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
            # Scope configuration (JSON arrays)
            sa.Column('in_scope_controls', sa.Text(), nullable=True),
            sa.Column('in_scope_policies', sa.Text(), nullable=True),
            sa.Column('in_scope_chapters', sa.Text(), nullable=True),
            # Timeline
            sa.Column('planned_start_date', sa.DateTime(), nullable=True),
            sa.Column('actual_start_date', sa.DateTime(), nullable=True),
            sa.Column('planned_end_date', sa.DateTime(), nullable=True),
            sa.Column('actual_end_date', sa.DateTime(), nullable=True),
            # Ownership
            sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
            # Change comparison
            sa.Column('prior_engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audit_engagements.id'), nullable=True),
            # Timestamps
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        # Create indexes
        op.create_index('ix_audit_engagements_organisation_id', 'audit_engagements', ['organisation_id'])
        op.create_index('ix_audit_engagements_assessment_id', 'audit_engagements', ['assessment_id'])
        op.create_index('ix_audit_engagements_status', 'audit_engagements', ['status'])
        op.create_index('ix_audit_engagements_owner_id', 'audit_engagements', ['owner_id'])

    # Create auditor_invitations table (external auditor access)
    if not table_exists('auditor_invitations'):
        op.create_table(
            'auditor_invitations',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audit_engagements.id', ondelete='CASCADE'), nullable=False),
            # Auditor details
            sa.Column('email', sa.String(255), nullable=False),
            sa.Column('name', sa.String(255), nullable=True),
            sa.Column('company', sa.String(255), nullable=True),
            # Role assignment
            sa.Column('auditor_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auditor_roles.id'), nullable=False),
            # Access token for magic link auth
            sa.Column('access_token', sa.String(500), nullable=True),
            sa.Column('token_expires_at', sa.DateTime(), nullable=True),
            # Time-bound access
            sa.Column('access_start', sa.DateTime(), nullable=True),
            sa.Column('access_end', sa.DateTime(), nullable=True),
            # Security settings
            sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('mfa_secret', sa.String(255), nullable=True),
            sa.Column('ip_allowlist', sa.Text(), nullable=True),
            # Download restrictions
            sa.Column('download_restricted', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('watermark_downloads', sa.Boolean(), nullable=False, server_default='true'),
            # Status
            sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
            # Tracking
            sa.Column('invited_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('accepted_at', sa.DateTime(), nullable=True),
            sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
            # Timestamps
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        # Create indexes
        op.create_index('ix_auditor_invitations_engagement_id', 'auditor_invitations', ['engagement_id'])
        op.create_index('ix_auditor_invitations_email', 'auditor_invitations', ['email'])
        op.create_index('ix_auditor_invitations_status', 'auditor_invitations', ['status'])
        op.create_index('ix_auditor_invitations_access_token', 'auditor_invitations', ['access_token'])


def downgrade() -> None:
    # Drop auditor_invitations table
    if table_exists('auditor_invitations'):
        op.drop_index('ix_auditor_invitations_access_token', table_name='auditor_invitations')
        op.drop_index('ix_auditor_invitations_status', table_name='auditor_invitations')
        op.drop_index('ix_auditor_invitations_email', table_name='auditor_invitations')
        op.drop_index('ix_auditor_invitations_engagement_id', table_name='auditor_invitations')
        op.drop_table('auditor_invitations')

    # Drop audit_engagements table
    if table_exists('audit_engagements'):
        op.drop_index('ix_audit_engagements_owner_id', table_name='audit_engagements')
        op.drop_index('ix_audit_engagements_status', table_name='audit_engagements')
        op.drop_index('ix_audit_engagements_assessment_id', table_name='audit_engagements')
        op.drop_index('ix_audit_engagements_organisation_id', table_name='audit_engagements')
        op.drop_table('audit_engagements')

    # Drop auditor_roles table
    if table_exists('auditor_roles'):
        op.drop_table('auditor_roles')
