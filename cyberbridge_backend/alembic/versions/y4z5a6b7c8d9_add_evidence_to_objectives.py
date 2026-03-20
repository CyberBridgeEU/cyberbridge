"""add evidence to objectives

Revision ID: y4z5a6b7c8d9
Revises: x3y4z5a6b7c8
Create Date: 2026-02-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'y4z5a6b7c8d9'
down_revision: Union[str, None] = 'x3y4z5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('objectives', sa.Column('evidence_filename', sa.String(255), nullable=True))
    op.add_column('objectives', sa.Column('evidence_filepath', sa.String(500), nullable=True))
    op.add_column('objectives', sa.Column('evidence_file_type', sa.String(100), nullable=True))
    op.add_column('objectives', sa.Column('evidence_file_size', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('objectives', 'evidence_file_size')
    op.drop_column('objectives', 'evidence_file_type')
    op.drop_column('objectives', 'evidence_filepath')
    op.drop_column('objectives', 'evidence_filename')
