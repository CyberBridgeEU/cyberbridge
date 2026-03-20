"""add scan_findings and risk_scan_findings tables

Revision ID: y5z6a7b8c9d0
Revises: x4y5z6a7b8c9
Create Date: 2026-02-11 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'y5z6a7b8c9d0'
down_revision: Union[str, None] = 'x4y5z6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scan_findings table
    op.create_table(
        'scan_findings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('scan_history_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scanner_history.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scanner_type', sa.String(50), nullable=False),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
        sa.Column('finding_hash', sa.String(64), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('severity', sa.String(50), nullable=True),
        sa.Column('normalized_severity', sa.String(20), nullable=True),
        sa.Column('identifier', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('solution', sa.Text(), nullable=True),
        sa.Column('url_or_target', sa.String(500), nullable=True),
        sa.Column('extra_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('scan_history_id', 'finding_hash', name='uq_scan_finding_hash'),
    )

    # Add indexes on scan_findings
    op.create_index('ix_scan_findings_organisation_id', 'scan_findings', ['organisation_id'])
    op.create_index('ix_scan_findings_scanner_type', 'scan_findings', ['scanner_type'])

    # Create risk_scan_findings junction table
    op.create_table(
        'risk_scan_findings',
        sa.Column('risk_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('risks.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('finding_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scan_findings.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('is_auto_mapped', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('risk_scan_findings')
    op.drop_index('ix_scan_findings_scanner_type', table_name='scan_findings')
    op.drop_index('ix_scan_findings_organisation_id', table_name='scan_findings')
    op.drop_table('scan_findings')
