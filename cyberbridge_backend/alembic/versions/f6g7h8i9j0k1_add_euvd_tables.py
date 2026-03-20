"""add euvd_vulnerabilities, euvd_sync_status and euvd_settings tables

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2026-02-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'f6g7h8i9j0k1'
down_revision = 'e5f6g7h8i9j0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'euvd_vulnerabilities',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('euvd_id', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('date_published', sa.DateTime, nullable=True),
        sa.Column('date_updated', sa.DateTime, nullable=True),
        sa.Column('base_score', sa.Float, nullable=True),
        sa.Column('base_score_version', sa.String(10), nullable=True),
        sa.Column('base_score_vector', sa.String(200), nullable=True),
        sa.Column('epss', sa.Float, nullable=True),
        sa.Column('assigner', sa.String(255), nullable=True),
        sa.Column('references', sa.Text, nullable=True),
        sa.Column('aliases', sa.Text, nullable=True),
        sa.Column('products', sa.Text, nullable=True),
        sa.Column('vendors', sa.Text, nullable=True),
        sa.Column('is_exploited', sa.Boolean, default=False),
        sa.Column('is_critical', sa.Boolean, default=False),
        sa.Column('category', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_euvd_vulnerabilities_euvd_id', 'euvd_vulnerabilities', ['euvd_id'])
    op.create_index('ix_euvd_vulnerabilities_is_exploited', 'euvd_vulnerabilities', ['is_exploited'])
    op.create_index('ix_euvd_vulnerabilities_is_critical', 'euvd_vulnerabilities', ['is_critical'])
    op.create_index('ix_euvd_vulnerabilities_category', 'euvd_vulnerabilities', ['category'])

    op.create_table(
        'euvd_sync_status',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('vulns_processed', sa.Integer, default=0),
        sa.Column('vulns_added', sa.Integer, default=0),
        sa.Column('vulns_updated', sa.Integer, default=0),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('triggered_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'euvd_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('sync_enabled', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('sync_interval_hours', sa.Integer, nullable=False, server_default=sa.text('1')),
        sa.Column('sync_interval_seconds', sa.Integer, nullable=False, server_default=sa.text('0')),
        sa.Column('last_sync_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('euvd_settings')
    op.drop_table('euvd_sync_status')
    op.drop_index('ix_euvd_vulnerabilities_category', table_name='euvd_vulnerabilities')
    op.drop_index('ix_euvd_vulnerabilities_is_critical', table_name='euvd_vulnerabilities')
    op.drop_index('ix_euvd_vulnerabilities_is_exploited', table_name='euvd_vulnerabilities')
    op.drop_index('ix_euvd_vulnerabilities_euvd_id', table_name='euvd_vulnerabilities')
    op.drop_table('euvd_vulnerabilities')
