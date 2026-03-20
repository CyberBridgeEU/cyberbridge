"""add remediation columns to scan_findings

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-02-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6g7h8'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('scan_findings', sa.Column('is_remediated', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('scan_findings', sa.Column('remediated_at', sa.DateTime(), nullable=True))
    op.add_column('scan_findings', sa.Column('remediated_by', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_scan_findings_remediated_by_users',
        'scan_findings',
        'users',
        ['remediated_by'],
        ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_scan_findings_remediated_by_users', 'scan_findings', type_='foreignkey')
    op.drop_column('scan_findings', 'remediated_by')
    op.drop_column('scan_findings', 'remediated_at')
    op.drop_column('scan_findings', 'is_remediated')
