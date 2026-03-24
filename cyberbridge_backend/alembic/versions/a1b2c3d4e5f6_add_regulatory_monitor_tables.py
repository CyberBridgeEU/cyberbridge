"""add_regulatory_monitor_tables

Revision ID: a1b2c3d4e5f6
Revises: jj0kk1ll2mm3
Create Date: 2026-03-24 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'jj0kk1ll2mm3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # 1. Create framework_snapshots table
    if not table_exists('framework_snapshots'):
        op.create_table(
            'framework_snapshots',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('framework_id', UUID(as_uuid=True), sa.ForeignKey('frameworks.id'), nullable=False),
            sa.Column('update_version', sa.Integer, nullable=False),
            sa.Column('snapshot_type', sa.String(20), nullable=False),
            sa.Column('snapshot_data', sa.Text, nullable=False),
            sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        )

    # 2. Add snapshot_id and source columns to framework_updates
    if table_exists('framework_updates'):
        if not column_exists('framework_updates', 'snapshot_id'):
            op.add_column('framework_updates',
                sa.Column('snapshot_id', UUID(as_uuid=True), sa.ForeignKey('framework_snapshots.id'), nullable=True)
            )
        if not column_exists('framework_updates', 'source'):
            op.add_column('framework_updates',
                sa.Column('source', sa.String(50), nullable=False, server_default='manual')
            )

    # 3. Create regulatory_sources table
    if not table_exists('regulatory_sources'):
        op.create_table(
            'regulatory_sources',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('framework_type', sa.String(100), nullable=False),
            sa.Column('source_name', sa.String(255), nullable=False),
            sa.Column('source_type', sa.String(50), nullable=False),
            sa.Column('search_query', sa.Text, nullable=True),
            sa.Column('domain_filter', sa.Text, nullable=True),
            sa.Column('direct_url', sa.Text, nullable=True),
            sa.Column('priority', sa.Integer, default=1),
            sa.Column('enabled', sa.Boolean, default=True, nullable=False),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        )

    # 4. Create regulatory_monitor_settings table
    if not table_exists('regulatory_monitor_settings'):
        op.create_table(
            'regulatory_monitor_settings',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('scan_frequency', sa.String(20), nullable=False, server_default='weekly'),
            sa.Column('scan_day_of_week', sa.String(10), nullable=True, server_default='mon'),
            sa.Column('scan_hour', sa.Integer, default=4),
            sa.Column('searxng_url', sa.String(500), server_default='http://searxng:8080'),
            sa.Column('enabled', sa.Boolean, default=True, nullable=False),
            sa.Column('last_scan_at', sa.DateTime, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        )

    # 5. Create regulatory_scan_runs table
    if not table_exists('regulatory_scan_runs'):
        op.create_table(
            'regulatory_scan_runs',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('status', sa.String(20), nullable=False, server_default='running'),
            sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('completed_at', sa.DateTime, nullable=True),
            sa.Column('frameworks_scanned', sa.Integer, default=0),
            sa.Column('changes_found', sa.Integer, default=0),
            sa.Column('error_message', sa.Text, nullable=True),
            sa.Column('raw_log', sa.Text, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        )

    # 6. Create regulatory_scan_results table
    if not table_exists('regulatory_scan_results'):
        op.create_table(
            'regulatory_scan_results',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('scan_run_id', UUID(as_uuid=True), sa.ForeignKey('regulatory_scan_runs.id'), nullable=False),
            sa.Column('framework_type', sa.String(100), nullable=False),
            sa.Column('source_name', sa.String(255), nullable=False),
            sa.Column('source_url', sa.Text, nullable=True),
            sa.Column('raw_content', sa.Text, nullable=True),
            sa.Column('content_hash', sa.String(64), nullable=True),
            sa.Column('fetched_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        )

    # 7. Create regulatory_changes table
    if not table_exists('regulatory_changes'):
        op.create_table(
            'regulatory_changes',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('scan_run_id', UUID(as_uuid=True), sa.ForeignKey('regulatory_scan_runs.id'), nullable=False),
            sa.Column('framework_type', sa.String(100), nullable=False),
            sa.Column('change_type', sa.String(50), nullable=False),
            sa.Column('entity_identifier', sa.String(255), nullable=True),
            sa.Column('current_value', sa.Text, nullable=True),
            sa.Column('proposed_value', sa.Text, nullable=True),
            sa.Column('source_url', sa.Text, nullable=True),
            sa.Column('source_excerpt', sa.Text, nullable=True),
            sa.Column('confidence', sa.Float, nullable=True),
            sa.Column('llm_reasoning', sa.Text, nullable=True),
            sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
            sa.Column('reviewed_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('reviewed_at', sa.DateTime, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        )


def downgrade() -> None:
    op.drop_table('regulatory_changes')
    op.drop_table('regulatory_scan_results')
    op.drop_table('regulatory_scan_runs')
    op.drop_table('regulatory_monitor_settings')
    op.drop_table('regulatory_sources')

    if column_exists('framework_updates', 'source'):
        op.drop_column('framework_updates', 'source')
    if column_exists('framework_updates', 'snapshot_id'):
        op.drop_column('framework_updates', 'snapshot_id')

    op.drop_table('framework_snapshots')
