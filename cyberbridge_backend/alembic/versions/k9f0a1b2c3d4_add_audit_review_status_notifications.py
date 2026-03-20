"""Add control review status and audit notifications tables

Revision ID: k9f0a1b2c3d4
Revises: j8e9f0a1b2c3
Create Date: 2026-01-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'k9f0a1b2c3d4'
down_revision: Union[str, None] = 'j8e9f0a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    bind = op.get_bind()
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def upgrade() -> None:
    # Create control_review_statuses table
    if not table_exists('control_review_statuses'):
        op.create_table(
            'control_review_statuses',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audit_engagements.id', ondelete='CASCADE'), nullable=False),
            sa.Column('answer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('answers.id', ondelete='CASCADE'), nullable=False),
            # Review status
            sa.Column('status', sa.String(50), nullable=False, server_default='not_started'),
            # Track who last updated
            sa.Column('last_updated_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('last_updated_by_auditor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auditor_invitations.id'), nullable=True),
            # Notes
            sa.Column('status_note', sa.Text(), nullable=True),
            # Timestamps
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
            # Constraints
            sa.CheckConstraint(
                "status IN ('not_started', 'pending_review', 'information_requested', 'response_provided', 'in_review', 'approved', 'approved_with_exceptions', 'needs_remediation')",
                name='valid_review_status'
            ),
        )
        # Create indexes
        op.create_index('ix_control_review_statuses_engagement_id', 'control_review_statuses', ['engagement_id'])
        op.create_index('ix_control_review_statuses_answer_id', 'control_review_statuses', ['answer_id'])
        op.create_index('ix_control_review_statuses_status', 'control_review_statuses', ['status'])
        # Create unique constraint for one status per control per engagement
        op.create_unique_constraint('uq_control_review_engagement_answer', 'control_review_statuses', ['engagement_id', 'answer_id'])

    # Create audit_notifications table
    if not table_exists('audit_notifications'):
        op.create_table(
            'audit_notifications',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('engagement_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('audit_engagements.id', ondelete='CASCADE'), nullable=False),
            # Recipient
            sa.Column('recipient_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('recipient_auditor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auditor_invitations.id'), nullable=True),
            # Notification type
            sa.Column('notification_type', sa.String(50), nullable=False),
            # Source reference
            sa.Column('source_type', sa.String(50), nullable=False),
            sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
            # Related answer
            sa.Column('related_answer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('answers.id'), nullable=True),
            # Content
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('message', sa.Text(), nullable=True),
            # Sender
            sa.Column('sender_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('sender_auditor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('auditor_invitations.id'), nullable=True),
            # Read status
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            # Timestamp
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        )
        # Create indexes
        op.create_index('ix_audit_notifications_engagement_id', 'audit_notifications', ['engagement_id'])
        op.create_index('ix_audit_notifications_recipient_user', 'audit_notifications', ['recipient_user_id'])
        op.create_index('ix_audit_notifications_recipient_auditor', 'audit_notifications', ['recipient_auditor_id'])
        op.create_index('ix_audit_notifications_is_read', 'audit_notifications', ['is_read'])
        op.create_index('ix_audit_notifications_created_at', 'audit_notifications', ['created_at'])


def downgrade() -> None:
    # Drop audit_notifications table
    if table_exists('audit_notifications'):
        op.drop_index('ix_audit_notifications_created_at', table_name='audit_notifications')
        op.drop_index('ix_audit_notifications_is_read', table_name='audit_notifications')
        op.drop_index('ix_audit_notifications_recipient_auditor', table_name='audit_notifications')
        op.drop_index('ix_audit_notifications_recipient_user', table_name='audit_notifications')
        op.drop_index('ix_audit_notifications_engagement_id', table_name='audit_notifications')
        op.drop_table('audit_notifications')

    # Drop control_review_statuses table
    if table_exists('control_review_statuses'):
        op.drop_constraint('uq_control_review_engagement_answer', 'control_review_statuses', type_='unique')
        op.drop_index('ix_control_review_statuses_status', table_name='control_review_statuses')
        op.drop_index('ix_control_review_statuses_answer_id', table_name='control_review_statuses')
        op.drop_index('ix_control_review_statuses_engagement_id', table_name='control_review_statuses')
        op.drop_table('control_review_statuses')
