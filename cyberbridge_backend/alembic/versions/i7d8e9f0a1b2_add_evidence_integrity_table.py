"""Add evidence integrity table

Revision ID: i7d8e9f0a1b2
Revises: h6c7d8e9f0a1
Create Date: 2025-01-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'i7d8e9f0a1b2'
down_revision = 'h6c7d8e9f0a1'
branch_labels = None
depends_on = None


def upgrade():
    # Create evidence_integrity table
    op.create_table(
        'evidence_integrity',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sha256_hash', sa.String(64), nullable=False),
        sa.Column('md5_hash', sa.String(32), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('uploaded_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('previous_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_verified_at', sa.DateTime(), nullable=True),
        sa.Column('verification_status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['evidence_id'], ['evidence.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['previous_version_id'], ['evidence_integrity.id'])
    )

    # Create indexes for common queries
    op.create_index('ix_evidence_integrity_evidence_id', 'evidence_integrity', ['evidence_id'])
    op.create_index('ix_evidence_integrity_sha256_hash', 'evidence_integrity', ['sha256_hash'])
    op.create_index('ix_evidence_integrity_version', 'evidence_integrity', ['evidence_id', 'version'])


def downgrade():
    op.drop_index('ix_evidence_integrity_version')
    op.drop_index('ix_evidence_integrity_sha256_hash')
    op.drop_index('ix_evidence_integrity_evidence_id')
    op.drop_table('evidence_integrity')
