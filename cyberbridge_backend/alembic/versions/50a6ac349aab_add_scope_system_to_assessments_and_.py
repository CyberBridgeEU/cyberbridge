"""add_scope_system_to_assessments_and_risks

Revision ID: 50a6ac349aab
Revises: c4610c561bc8
Create Date: 2025-11-14 10:32:25.625927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '50a6ac349aab'
down_revision: Union[str, None] = 'c4610c561bc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    # Create scopes table if it doesn't exist
    if 'scopes' not in inspector.get_table_names():
        op.create_table('scopes',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('scope_name', sa.String(length=50), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('scope_name')
        )

    # Add scope configuration columns to frameworks table
    frameworks_columns = [col['name'] for col in inspector.get_columns('frameworks')]
    if 'default_scope_type' not in frameworks_columns:
        op.add_column('frameworks', sa.Column('default_scope_type', sa.String(length=50), nullable=True))
    if 'allowed_scope_types' not in frameworks_columns:
        op.add_column('frameworks', sa.Column('allowed_scope_types', sa.Text(), nullable=True))
    if 'scope_selection_mode' not in frameworks_columns:
        op.add_column('frameworks', sa.Column('scope_selection_mode', sa.String(length=50), server_default='flexible', nullable=True))

    # Add scope columns to assessments table
    assessments_columns = [col['name'] for col in inspector.get_columns('assessments')]
    if 'scope_id' not in assessments_columns:
        op.add_column('assessments', sa.Column('scope_id', sa.UUID(), nullable=True))
    if 'scope_entity_id' not in assessments_columns:
        op.add_column('assessments', sa.Column('scope_entity_id', sa.UUID(), nullable=True))

    # Add foreign key if it doesn't exist
    assessments_fks = [fk['name'] for fk in inspector.get_foreign_keys('assessments')]
    if 'fk_assessments_scope_id' not in assessments_fks:
        op.create_foreign_key('fk_assessments_scope_id', 'assessments', 'scopes', ['scope_id'], ['id'])

    # Add scope columns to risks table
    risks_columns = [col['name'] for col in inspector.get_columns('risks')]
    if 'scope_id' not in risks_columns:
        op.add_column('risks', sa.Column('scope_id', sa.UUID(), nullable=True))
    if 'scope_entity_id' not in risks_columns:
        op.add_column('risks', sa.Column('scope_entity_id', sa.UUID(), nullable=True))

    # Add foreign key if it doesn't exist
    risks_fks = [fk['name'] for fk in inspector.get_foreign_keys('risks')]
    if 'fk_risks_scope_id' not in risks_fks:
        op.create_foreign_key('fk_risks_scope_id', 'risks', 'scopes', ['scope_id'], ['id'])


def downgrade() -> None:
    # Remove scope columns from risks table
    op.drop_constraint('fk_risks_scope_id', 'risks', type_='foreignkey')
    op.drop_column('risks', 'scope_entity_id')
    op.drop_column('risks', 'scope_id')

    # Remove scope columns from assessments table
    op.drop_constraint('fk_assessments_scope_id', 'assessments', type_='foreignkey')
    op.drop_column('assessments', 'scope_entity_id')
    op.drop_column('assessments', 'scope_id')

    # Remove scope configuration columns from frameworks table
    op.drop_column('frameworks', 'scope_selection_mode')
    op.drop_column('frameworks', 'allowed_scope_types')
    op.drop_column('frameworks', 'default_scope_type')

    # Drop scopes table
    op.drop_table('scopes')
