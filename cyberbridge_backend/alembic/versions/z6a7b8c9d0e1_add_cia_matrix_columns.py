"""Add CIA matrix columns to asset_types and assets

Revision ID: z6a7b8c9d0e1
Revises: y5z6a7b8c9d0, u9v0w1x2y3z4
Create Date: 2026-02-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'z6a7b8c9d0e1'
down_revision: Union[str, None] = ('y5z6a7b8c9d0', 'u9v0w1x2y3z4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(bind, table_name):
    """Check if a table exists in the database"""
    insp = inspect(bind)
    return table_name in insp.get_table_names()


def column_exists(bind, table_name, column_name):
    """Check if a column exists in a table"""
    insp = inspect(bind)
    if table_name not in insp.get_table_names():
        return False
    columns = [c['name'] for c in insp.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    bind = op.get_bind()

    # Add CIA default columns to asset_types
    if table_exists(bind, 'asset_types'):
        if not column_exists(bind, 'asset_types', 'default_confidentiality'):
            op.add_column('asset_types', sa.Column('default_confidentiality', sa.String(10), nullable=True))
        if not column_exists(bind, 'asset_types', 'default_integrity'):
            op.add_column('asset_types', sa.Column('default_integrity', sa.String(10), nullable=True))
        if not column_exists(bind, 'asset_types', 'default_availability'):
            op.add_column('asset_types', sa.Column('default_availability', sa.String(10), nullable=True))
        if not column_exists(bind, 'asset_types', 'default_asset_value'):
            op.add_column('asset_types', sa.Column('default_asset_value', sa.String(10), nullable=True))

    # Add CIA columns to assets
    if table_exists(bind, 'assets'):
        if not column_exists(bind, 'assets', 'confidentiality'):
            op.add_column('assets', sa.Column('confidentiality', sa.String(10), nullable=True))
        if not column_exists(bind, 'assets', 'integrity'):
            op.add_column('assets', sa.Column('integrity', sa.String(10), nullable=True))
        if not column_exists(bind, 'assets', 'availability'):
            op.add_column('assets', sa.Column('availability', sa.String(10), nullable=True))
        if not column_exists(bind, 'assets', 'asset_value'):
            op.add_column('assets', sa.Column('asset_value', sa.String(10), nullable=True))
        if not column_exists(bind, 'assets', 'inherit_cia'):
            op.add_column('assets', sa.Column('inherit_cia', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    bind = op.get_bind()

    # Remove CIA columns from assets
    if table_exists(bind, 'assets'):
        if column_exists(bind, 'assets', 'inherit_cia'):
            op.drop_column('assets', 'inherit_cia')
        if column_exists(bind, 'assets', 'asset_value'):
            op.drop_column('assets', 'asset_value')
        if column_exists(bind, 'assets', 'availability'):
            op.drop_column('assets', 'availability')
        if column_exists(bind, 'assets', 'integrity'):
            op.drop_column('assets', 'integrity')
        if column_exists(bind, 'assets', 'confidentiality'):
            op.drop_column('assets', 'confidentiality')

    # Remove CIA default columns from asset_types
    if table_exists(bind, 'asset_types'):
        if column_exists(bind, 'asset_types', 'default_asset_value'):
            op.drop_column('asset_types', 'default_asset_value')
        if column_exists(bind, 'asset_types', 'default_availability'):
            op.drop_column('asset_types', 'default_availability')
        if column_exists(bind, 'asset_types', 'default_integrity'):
            op.drop_column('asset_types', 'default_integrity')
        if column_exists(bind, 'asset_types', 'default_confidentiality'):
            op.drop_column('asset_types', 'default_confidentiality')
