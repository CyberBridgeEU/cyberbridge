"""add assessment_status to risks

Revision ID: w3x4y5z6a7b8
Revises: v2w3x4y5z6a7
Create Date: 2026-02-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'w3x4y5z6a7b8'
down_revision: Union[str, None] = 'v2w3x4y5z6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('risks', sa.Column('assessment_status', sa.String(length=50), nullable=True))
    op.execute("UPDATE risks SET assessment_status = 'Not Assessed' WHERE assessment_status IS NULL")


def downgrade() -> None:
    op.drop_column('risks', 'assessment_status')
