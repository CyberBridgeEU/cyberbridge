"""add scope to objectives

Revision ID: t8u9v0w1x2y3
Revises: s7t8u9v0w1x2
Create Date: 2025-01-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 't8u9v0w1x2y3'
down_revision: Union[str, None] = 's7t8u9v0w1x2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add scope_id and scope_entity_id columns to objectives table
    op.add_column('objectives', sa.Column('scope_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('scopes.id'), nullable=True))
    op.add_column('objectives', sa.Column('scope_entity_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Create index for faster scope-based queries
    op.create_index('ix_objectives_scope_id', 'objectives', ['scope_id'])
    op.create_index('ix_objectives_scope_entity_id', 'objectives', ['scope_entity_id'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_objectives_scope_entity_id', table_name='objectives')
    op.drop_index('ix_objectives_scope_id', table_name='objectives')

    # Remove columns
    op.drop_column('objectives', 'scope_entity_id')
    op.drop_column('objectives', 'scope_id')
