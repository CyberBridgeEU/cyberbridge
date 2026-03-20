"""Add controls tables, objective/control junction tables, and policy_code columns

Revision ID: t9u0v1w2x3y4
Revises: t8u9v0w1x2y3
Create Date: 2026-02-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 't9u0v1w2x3y4'
down_revision: Union[str, None] = 't8u9v0w1x2y3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    conn = op.get_bind()
    inspector = inspect(conn)
    if table_name not in inspector.get_table_names():
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # --- Add policy_code column to policies table ---
    if not column_exists('policies', 'policy_code'):
        op.add_column('policies', sa.Column('policy_code', sa.String(50), nullable=True))

    # --- Add policy_code column to policy_templates table ---
    if table_exists('policy_templates') and not column_exists('policy_templates', 'policy_code'):
        op.add_column('policy_templates', sa.Column('policy_code', sa.String(50), nullable=True))

    # --- Populate policy_code for existing policies (POL-N per organisation) ---
    op.execute("""
        WITH numbered_policies AS (
            SELECT id, organisation_id,
                   ROW_NUMBER() OVER (PARTITION BY organisation_id ORDER BY created_at, id) AS rn
            FROM policies
            WHERE policy_code IS NULL
        )
        UPDATE policies
        SET policy_code = 'POL-' || numbered_policies.rn
        FROM numbered_policies
        WHERE policies.id = numbered_policies.id
    """)

    # --- Populate risk_code for existing risks (RSK-N per organisation) ---
    # risk_code column was added by earlier migration r6s7t8u9v0w1
    if column_exists('risks', 'risk_code'):
        op.execute("""
            WITH numbered_risks AS (
                SELECT id, organisation_id,
                       ROW_NUMBER() OVER (PARTITION BY organisation_id ORDER BY created_at, id) AS rn
                FROM risks
                WHERE risk_code IS NULL
            )
            UPDATE risks
            SET risk_code = 'RSK-' || numbered_risks.rn
            FROM numbered_risks
            WHERE risks.id = numbered_risks.id
        """)

    # --- Create control_statuses lookup table ---
    if not table_exists('control_statuses'):
        op.create_table(
            'control_statuses',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('status_name', sa.String(100), nullable=False, unique=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )

    # --- Create control_sets table ---
    if not table_exists('control_sets'):
        op.create_table(
            'control_sets',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text, nullable=True),
            sa.Column('organisation_id', UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
            sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('last_updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
        )

    # --- Create controls table ---
    if not table_exists('controls'):
        op.create_table(
            'controls',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('code', sa.String(100), nullable=False),
            sa.Column('name', sa.Text, nullable=False),
            sa.Column('description', sa.Text, nullable=True),
            sa.Column('category', sa.String(255), nullable=True),
            sa.Column('owner', sa.String(255), nullable=True),
            sa.Column('control_set_id', UUID(as_uuid=True), sa.ForeignKey('control_sets.id'), nullable=False),
            sa.Column('control_status_id', UUID(as_uuid=True), sa.ForeignKey('control_statuses.id'), nullable=False),
            sa.Column('organisation_id', UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
            sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('last_updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.UniqueConstraint('organisation_id', 'code', name='uq_controls_org_code')
        )

    # --- Create control_risks junction table ---
    if not table_exists('control_risks'):
        op.create_table(
            'control_risks',
            sa.Column('control_id', UUID(as_uuid=True), sa.ForeignKey('controls.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('risk_id', UUID(as_uuid=True), sa.ForeignKey('risks.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )

    # --- Create control_policies junction table ---
    if not table_exists('control_policies'):
        op.create_table(
            'control_policies',
            sa.Column('control_id', UUID(as_uuid=True), sa.ForeignKey('controls.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('policy_id', UUID(as_uuid=True), sa.ForeignKey('policies.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )

    # --- Create objective_risks junction table ---
    if not table_exists('objective_risks'):
        op.create_table(
            'objective_risks',
            sa.Column('objective_id', UUID(as_uuid=True), sa.ForeignKey('objectives.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('risk_id', UUID(as_uuid=True), sa.ForeignKey('risks.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )

    # --- Create objective_controls junction table ---
    if not table_exists('objective_controls'):
        op.create_table(
            'objective_controls',
            sa.Column('objective_id', UUID(as_uuid=True), sa.ForeignKey('objectives.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('control_id', UUID(as_uuid=True), sa.ForeignKey('controls.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )


def downgrade() -> None:
    if table_exists('objective_controls'):
        op.drop_table('objective_controls')
    if table_exists('objective_risks'):
        op.drop_table('objective_risks')
    if table_exists('control_policies'):
        op.drop_table('control_policies')
    if table_exists('control_risks'):
        op.drop_table('control_risks')
    if table_exists('controls'):
        op.drop_table('controls')
    if table_exists('control_sets'):
        op.drop_table('control_sets')
    if table_exists('control_statuses'):
        op.drop_table('control_statuses')
    if column_exists('policy_templates', 'policy_code'):
        op.drop_column('policy_templates', 'policy_code')
    if column_exists('policies', 'policy_code'):
        op.drop_column('policies', 'policy_code')
