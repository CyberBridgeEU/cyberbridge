"""Drop products tables and rename product_types to asset_categories

Revision ID: w2x3y4z5a6b7
Revises: v1w2x3y4z5a6
Create Date: 2026-02-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'w2x3y4z5a6b7'
down_revision: Union[str, None] = 'v1w2x3y4z5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop products table (FK to product_statuses, product_types, etc.)
    op.drop_table('products')

    # 2. Drop product_statuses table (no longer referenced)
    op.drop_table('product_statuses')

    # 3. Rename risks.product_type_id -> risks.asset_category_id
    #    Drop old FK, rename column, create new FK
    op.drop_constraint('risks_product_type_id_fkey', 'risks', type_='foreignkey')
    op.alter_column('risks', 'product_type_id', new_column_name='asset_category_id')
    op.create_foreign_key(
        'risks_asset_category_id_fkey', 'risks',
        'product_types', ['asset_category_id'], ['id']
    )

    # 4. Rename risk_categories.product_type_id -> risk_categories.asset_category_id
    op.drop_constraint('risk_categories_product_type_id_fkey', 'risk_categories', type_='foreignkey')
    op.alter_column('risk_categories', 'product_type_id', new_column_name='asset_category_id')
    op.create_foreign_key(
        'risk_categories_asset_category_id_fkey', 'risk_categories',
        'product_types', ['asset_category_id'], ['id']
    )

    # 5. Rename table product_types -> asset_categories
    op.rename_table('product_types', 'asset_categories')

    # 6. Update FK constraints to point to renamed table
    op.drop_constraint('risks_asset_category_id_fkey', 'risks', type_='foreignkey')
    op.create_foreign_key(
        'risks_asset_category_id_fkey', 'risks',
        'asset_categories', ['asset_category_id'], ['id']
    )
    op.drop_constraint('risk_categories_asset_category_id_fkey', 'risk_categories', type_='foreignkey')
    op.create_foreign_key(
        'risk_categories_asset_category_id_fkey', 'risk_categories',
        'asset_categories', ['asset_category_id'], ['id']
    )


def downgrade() -> None:
    # Reverse: rename asset_categories back to product_types
    op.rename_table('asset_categories', 'product_types')

    # Rename columns back
    op.drop_constraint('risks_asset_category_id_fkey', 'risks', type_='foreignkey')
    op.alter_column('risks', 'asset_category_id', new_column_name='product_type_id')
    op.create_foreign_key(
        'risks_product_type_id_fkey', 'risks',
        'product_types', ['product_type_id'], ['id']
    )

    op.drop_constraint('risk_categories_asset_category_id_fkey', 'risk_categories', type_='foreignkey')
    op.alter_column('risk_categories', 'asset_category_id', new_column_name='product_type_id')
    op.create_foreign_key(
        'risk_categories_product_type_id_fkey', 'risk_categories',
        'product_types', ['product_type_id'], ['id']
    )

    # Recreate product_statuses table
    op.create_table(
        'product_statuses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('status', sa.String(50), nullable=False),
    )

    # Recreate products table
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('product_version', sa.String(255), nullable=False),
        sa.Column('justification', sa.String(255), nullable=False),
        sa.Column('license_model', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('sbom', sa.Text(), nullable=True),
        sa.Column('product_status_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_statuses.id'), nullable=False),
        sa.Column('economic_operator_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('economic_operators.id'), nullable=False),
        sa.Column('product_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('product_types.id'), nullable=False),
        sa.Column('criticality_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('criticalities.id'), nullable=True),
        sa.Column('organisation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('last_updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
    )
