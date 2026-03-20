"""Add audit comments, findings, sign-offs, and activity logs tables

Revision ID: h6c7d8e9f0a1
Revises: g5b6c7d8e9f0
Create Date: 2026-01-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'h6c7d8e9f0a1'
down_revision: Union[str, None] = 'g5b6c7d8e9f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def upgrade() -> None:
    # Create audit_comments table
    if not table_exists('audit_comments'):
        op.create_table(
            'audit_comments',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audit_engagements.id', ondelete='CASCADE'), nullable=False),
            # Target reference
            sa.Column('target_type', sa.String(50), nullable=False),  # answer, evidence, objective, policy
            sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
            # Comment type
            sa.Column('comment_type', sa.String(50), nullable=False, server_default='observation'),
            # Content
            sa.Column('content', sa.Text(), nullable=False),
            # Threading
            sa.Column('parent_comment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audit_comments.id'), nullable=True),
            # Assignment
            sa.Column('assigned_to_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('assigned_to_auditor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auditor_invitations.id'), nullable=True),
            sa.Column('due_date', sa.DateTime(), nullable=True),
            # Status
            sa.Column('status', sa.String(50), nullable=False, server_default='open'),
            # Resolution
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('resolved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('resolved_by_auditor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auditor_invitations.id'), nullable=True),
            sa.Column('resolution_note', sa.Text(), nullable=True),
            # Author
            sa.Column('author_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('author_auditor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auditor_invitations.id'), nullable=True),
            # Timestamps
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        # Create indexes
        op.create_index('ix_audit_comments_engagement_id', 'audit_comments', ['engagement_id'])
        op.create_index('ix_audit_comments_target', 'audit_comments', ['target_type', 'target_id'])
        op.create_index('ix_audit_comments_status', 'audit_comments', ['status'])
        op.create_index('ix_audit_comments_parent_id', 'audit_comments', ['parent_comment_id'])

    # Create audit_comment_attachments table
    if not table_exists('audit_comment_attachments'):
        op.create_table(
            'audit_comment_attachments',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('comment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audit_comments.id', ondelete='CASCADE'), nullable=False),
            sa.Column('filename', sa.String(500), nullable=False),
            sa.Column('filepath', sa.Text(), nullable=False),
            sa.Column('file_type', sa.String(100), nullable=True),
            sa.Column('file_size', sa.Integer(), nullable=True),
            sa.Column('uploaded_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('uploaded_by_auditor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auditor_invitations.id'), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        )
        op.create_index('ix_audit_comment_attachments_comment_id', 'audit_comment_attachments', ['comment_id'])

    # Create audit_findings table
    if not table_exists('audit_findings'):
        op.create_table(
            'audit_findings',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audit_engagements.id', ondelete='CASCADE'), nullable=False),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            # Classification
            sa.Column('severity', sa.String(50), nullable=False, server_default='medium'),
            sa.Column('category', sa.String(100), nullable=False),
            # Related items (JSON arrays)
            sa.Column('related_controls', sa.Text(), nullable=True),
            sa.Column('related_evidence', sa.Text(), nullable=True),
            # Remediation
            sa.Column('remediation_plan', sa.Text(), nullable=True),
            sa.Column('remediation_owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('remediation_due_date', sa.DateTime(), nullable=True),
            # Status
            sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
            # Author
            sa.Column('author_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('author_auditor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auditor_invitations.id'), nullable=True),
            # Timestamps
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        )
        op.create_index('ix_audit_findings_engagement_id', 'audit_findings', ['engagement_id'])
        op.create_index('ix_audit_findings_severity', 'audit_findings', ['severity'])
        op.create_index('ix_audit_findings_status', 'audit_findings', ['status'])

    # Create audit_sign_offs table
    if not table_exists('audit_sign_offs'):
        op.create_table(
            'audit_sign_offs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audit_engagements.id', ondelete='CASCADE'), nullable=False),
            # Sign-off scope
            sa.Column('sign_off_type', sa.String(50), nullable=False),  # control, section, engagement
            sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
            # Status
            sa.Column('status', sa.String(50), nullable=False),  # approved, approved_with_exceptions, rejected
            sa.Column('comments', sa.Text(), nullable=True),
            # Signer
            sa.Column('signer_auditor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auditor_invitations.id'), nullable=False),
            sa.Column('signed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            # Audit trail
            sa.Column('ip_address', sa.String(50), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            # Timestamps
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        )
        op.create_index('ix_audit_sign_offs_engagement_id', 'audit_sign_offs', ['engagement_id'])
        op.create_index('ix_audit_sign_offs_type_target', 'audit_sign_offs', ['sign_off_type', 'target_id'])

    # Create audit_activity_logs table
    if not table_exists('audit_activity_logs'):
        op.create_table(
            'audit_activity_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audit_engagements.id', ondelete='CASCADE'), nullable=False),
            # Actor
            sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('auditor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auditor_invitations.id'), nullable=True),
            # Action
            sa.Column('action', sa.String(100), nullable=False),
            sa.Column('target_type', sa.String(50), nullable=True),
            sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('details', sa.Text(), nullable=True),  # JSON
            # Request metadata
            sa.Column('ip_address', sa.String(50), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            # Timestamps
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        )
        op.create_index('ix_audit_activity_logs_engagement_id', 'audit_activity_logs', ['engagement_id'])
        op.create_index('ix_audit_activity_logs_action', 'audit_activity_logs', ['action'])
        op.create_index('ix_audit_activity_logs_created_at', 'audit_activity_logs', ['created_at'])


def downgrade() -> None:
    # Drop audit_activity_logs
    if table_exists('audit_activity_logs'):
        op.drop_index('ix_audit_activity_logs_created_at', table_name='audit_activity_logs')
        op.drop_index('ix_audit_activity_logs_action', table_name='audit_activity_logs')
        op.drop_index('ix_audit_activity_logs_engagement_id', table_name='audit_activity_logs')
        op.drop_table('audit_activity_logs')

    # Drop audit_sign_offs
    if table_exists('audit_sign_offs'):
        op.drop_index('ix_audit_sign_offs_type_target', table_name='audit_sign_offs')
        op.drop_index('ix_audit_sign_offs_engagement_id', table_name='audit_sign_offs')
        op.drop_table('audit_sign_offs')

    # Drop audit_findings
    if table_exists('audit_findings'):
        op.drop_index('ix_audit_findings_status', table_name='audit_findings')
        op.drop_index('ix_audit_findings_severity', table_name='audit_findings')
        op.drop_index('ix_audit_findings_engagement_id', table_name='audit_findings')
        op.drop_table('audit_findings')

    # Drop audit_comment_attachments
    if table_exists('audit_comment_attachments'):
        op.drop_index('ix_audit_comment_attachments_comment_id', table_name='audit_comment_attachments')
        op.drop_table('audit_comment_attachments')

    # Drop audit_comments
    if table_exists('audit_comments'):
        op.drop_index('ix_audit_comments_parent_id', table_name='audit_comments')
        op.drop_index('ix_audit_comments_status', table_name='audit_comments')
        op.drop_index('ix_audit_comments_target', table_name='audit_comments')
        op.drop_index('ix_audit_comments_engagement_id', table_name='audit_comments')
        op.drop_table('audit_comments')
