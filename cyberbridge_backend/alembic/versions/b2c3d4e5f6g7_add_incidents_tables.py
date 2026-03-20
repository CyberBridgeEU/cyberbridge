"""add incidents tables

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-13 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create incident_statuses lookup table
    op.create_table('incident_statuses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_status_name', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('incident_status_name')
    )

    # Create incidents table
    op.create_table('incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_code', sa.String(length=50), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('incident_severity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_status_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reported_by', sa.String(length=255), nullable=True),
        sa.Column('assigned_to', sa.String(length=255), nullable=True),
        sa.Column('discovered_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('containment_actions', sa.Text(), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('remediation_steps', sa.Text(), nullable=True),
        sa.Column('ai_analysis', sa.Text(), nullable=True),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('last_updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['incident_severity_id'], ['risk_severity.id'], ),
        sa.ForeignKeyConstraint(['incident_status_id'], ['incident_statuses.id'], ),
        sa.ForeignKeyConstraint(['organisation_id'], ['organisations.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['last_updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organisation_id', 'incident_code', name='uq_incidents_org_incident_code')
    )

    # Create incident_frameworks junction table
    op.create_table('incident_frameworks',
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('framework_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['framework_id'], ['frameworks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('incident_id', 'framework_id')
    )

    # Create incident_risks junction table
    op.create_table('incident_risks',
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['risk_id'], ['risks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('incident_id', 'risk_id')
    )

    # Create incident_assets junction table
    op.create_table('incident_assets',
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['incidents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('incident_id', 'asset_id')
    )


def downgrade() -> None:
    op.drop_table('incident_assets')
    op.drop_table('incident_risks')
    op.drop_table('incident_frameworks')
    op.drop_table('incidents')
    op.drop_table('incident_statuses')
