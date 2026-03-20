"""Add product registration fields to assets table

Revision ID: q5r6s7t8u9v0
Revises: p4q5r6s7t8u9
Create Date: 2026-02-04 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect, text


# revision identifiers, used by Alembic.
revision: str = 'q5r6s7t8u9v0'
down_revision: Union[str, None] = 'p4q5r6s7t8u9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database"""
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    conn = op.get_bind()
    inspector = inspect(conn)
    if not table_exists(table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # Create asset_statuses lookup table
    if not table_exists('asset_statuses'):
        op.create_table(
            'asset_statuses',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('status', sa.String(100), nullable=False, unique=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )

        # Seed default asset statuses
        conn = op.get_bind()
        conn.execute(text("""
            INSERT INTO asset_statuses (id, status) VALUES
            (gen_random_uuid(), 'Active'),
            (gen_random_uuid(), 'Inactive'),
            (gen_random_uuid(), 'Maintenance'),
            (gen_random_uuid(), 'Deprecated'),
            (gen_random_uuid(), 'Testing'),
            (gen_random_uuid(), 'Retired')
        """))

    # Add new columns to assets table
    if table_exists('assets'):
        # Add version column
        if not column_exists('assets', 'version'):
            op.add_column('assets', sa.Column('version', sa.String(100), nullable=True))

        # Add justification column
        if not column_exists('assets', 'justification'):
            op.add_column('assets', sa.Column('justification', sa.Text, nullable=True))

        # Add license_model column
        if not column_exists('assets', 'license_model'):
            op.add_column('assets', sa.Column('license_model', sa.String(255), nullable=True))

        # Add sbom column
        if not column_exists('assets', 'sbom'):
            op.add_column('assets', sa.Column('sbom', sa.Text, nullable=True))

        # Add asset_status_id foreign key
        if not column_exists('assets', 'asset_status_id'):
            op.add_column('assets', sa.Column('asset_status_id', UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(
                'fk_assets_asset_status_id',
                'assets', 'asset_statuses',
                ['asset_status_id'], ['id']
            )

        # Add economic_operator_id foreign key (reuses existing economic_operators table)
        if not column_exists('assets', 'economic_operator_id'):
            op.add_column('assets', sa.Column('economic_operator_id', UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(
                'fk_assets_economic_operator_id',
                'assets', 'economic_operators',
                ['economic_operator_id'], ['id']
            )

        # Add criticality_id foreign key (reuses existing criticalities table)
        if not column_exists('assets', 'criticality_id'):
            op.add_column('assets', sa.Column('criticality_id', UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(
                'fk_assets_criticality_id',
                'assets', 'criticalities',
                ['criticality_id'], ['id']
            )

        # Add criticality_option column (stores the selected option value)
        if not column_exists('assets', 'criticality_option'):
            op.add_column('assets', sa.Column('criticality_option', sa.Text, nullable=True))


def downgrade() -> None:
    # Remove columns from assets table
    if table_exists('assets'):
        if column_exists('assets', 'criticality_option'):
            op.drop_column('assets', 'criticality_option')

        if column_exists('assets', 'criticality_id'):
            op.drop_constraint('fk_assets_criticality_id', 'assets', type_='foreignkey')
            op.drop_column('assets', 'criticality_id')

        if column_exists('assets', 'economic_operator_id'):
            op.drop_constraint('fk_assets_economic_operator_id', 'assets', type_='foreignkey')
            op.drop_column('assets', 'economic_operator_id')

        if column_exists('assets', 'asset_status_id'):
            op.drop_constraint('fk_assets_asset_status_id', 'assets', type_='foreignkey')
            op.drop_column('assets', 'asset_status_id')

        if column_exists('assets', 'sbom'):
            op.drop_column('assets', 'sbom')

        if column_exists('assets', 'license_model'):
            op.drop_column('assets', 'license_model')

        if column_exists('assets', 'justification'):
            op.drop_column('assets', 'justification')

        if column_exists('assets', 'version'):
            op.drop_column('assets', 'version')

    # Drop asset_statuses table
    if table_exists('asset_statuses'):
        op.drop_table('asset_statuses')
