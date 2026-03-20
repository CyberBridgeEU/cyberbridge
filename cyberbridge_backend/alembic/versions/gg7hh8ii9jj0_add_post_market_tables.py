"""Add post-market surveillance tables and incident triage columns

Revision ID: gg7hh8ii9jj0
Revises: ff6gg7hh8ii9
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'gg7hh8ii9jj0'
down_revision = 'ff6gg7hh8ii9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add triage columns to incidents table
    op.add_column('incidents', sa.Column('vulnerability_source', sa.String(50), nullable=True))
    op.add_column('incidents', sa.Column('cvss_score', sa.Float, nullable=True))
    op.add_column('incidents', sa.Column('cve_id', sa.String(50), nullable=True))
    op.add_column('incidents', sa.Column('cwe_id', sa.String(50), nullable=True))
    op.add_column('incidents', sa.Column('euvd_vulnerability_id', UUID(as_uuid=True), nullable=True))
    op.add_column('incidents', sa.Column('triage_status', sa.String(50), nullable=True))
    op.add_column('incidents', sa.Column('sla_deadline', sa.DateTime, nullable=True))
    op.add_column('incidents', sa.Column('sla_status', sa.String(20), nullable=True))
    op.add_column('incidents', sa.Column('affected_products', sa.Text, nullable=True))

    op.create_foreign_key(
        'fk_incidents_euvd_vulnerability',
        'incidents', 'euvd_vulnerabilities',
        ['euvd_vulnerability_id'], ['id'],
        ondelete='SET NULL'
    )

    # Incident Patches
    op.create_table(
        'incident_patches',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('incident_id', UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('patch_version', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('release_date', sa.DateTime, nullable=True),
        sa.Column('target_sla_date', sa.DateTime, nullable=True),
        sa.Column('actual_resolution_date', sa.DateTime, nullable=True),
        sa.Column('sla_compliance', sa.String(20), nullable=True),
        sa.Column('organisation_id', UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('incident_id', 'patch_version', name='uq_incident_patch_version'),
    )

    # Advisory Statuses (lookup)
    op.create_table(
        'advisory_statuses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('status_name', sa.String(50), nullable=False, unique=True),
    )

    # Security Advisories
    op.create_table(
        'security_advisories',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('advisory_code', sa.String(50), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('affected_versions', sa.Text, nullable=True),
        sa.Column('fixed_version', sa.String(255), nullable=True),
        sa.Column('severity', sa.String(50), nullable=True),
        sa.Column('cve_ids', sa.Text, nullable=True),
        sa.Column('workaround', sa.Text, nullable=True),
        sa.Column('advisory_status_id', UUID(as_uuid=True), sa.ForeignKey('advisory_statuses.id'), nullable=False),
        sa.Column('incident_id', UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('published_at', sa.DateTime, nullable=True),
        sa.Column('organisation_id', UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('last_updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('organisation_id', 'advisory_code', name='uq_advisories_org_code'),
    )

    # ENISA Notifications
    op.create_table(
        'enisa_notifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('incident_id', UUID(as_uuid=True), sa.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('early_warning_required', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('early_warning_deadline', sa.DateTime, nullable=True),
        sa.Column('early_warning_submitted', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('early_warning_submitted_at', sa.DateTime, nullable=True),
        sa.Column('early_warning_content', sa.Text, nullable=True),
        sa.Column('vuln_notification_required', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('vuln_notification_deadline', sa.DateTime, nullable=True),
        sa.Column('vuln_notification_submitted', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('vuln_notification_submitted_at', sa.DateTime, nullable=True),
        sa.Column('vuln_notification_content', sa.Text, nullable=True),
        sa.Column('final_report_required', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('final_report_deadline', sa.DateTime, nullable=True),
        sa.Column('final_report_submitted', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('final_report_submitted_at', sa.DateTime, nullable=True),
        sa.Column('final_report_content', sa.Text, nullable=True),
        sa.Column('reporting_status', sa.String(50), nullable=False, server_default='not_started'),
        sa.Column('organisation_id', UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('last_updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('incident_id', name='uq_enisa_incident'),
    )


def downgrade() -> None:
    op.drop_table('enisa_notifications')
    op.drop_table('security_advisories')
    op.drop_table('advisory_statuses')
    op.drop_table('incident_patches')
    op.drop_constraint('fk_incidents_euvd_vulnerability', 'incidents', type_='foreignkey')
    op.drop_column('incidents', 'affected_products')
    op.drop_column('incidents', 'sla_status')
    op.drop_column('incidents', 'sla_deadline')
    op.drop_column('incidents', 'triage_status')
    op.drop_column('incidents', 'euvd_vulnerability_id')
    op.drop_column('incidents', 'cwe_id')
    op.drop_column('incidents', 'cve_id')
    op.drop_column('incidents', 'cvss_score')
    op.drop_column('incidents', 'vulnerability_source')
