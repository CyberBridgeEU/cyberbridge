"""make_organisation_id_required_in_correlations

Revision ID: c4610c561bc8
Revises: 671d6c3d7243
Create Date: 2025-11-12 14:28:25.796204

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4610c561bc8'
down_revision: Union[str, None] = '671d6c3d7243'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Delete any existing correlations with NULL organisation_id (global correlations)
    # Since we're removing the concept of global correlations
    op.execute("DELETE FROM question_correlations WHERE organisation_id IS NULL")

    # Make organisation_id NOT NULL - all correlations must belong to an organization
    op.alter_column('question_correlations', 'organisation_id',
                    existing_type=sa.UUID(),
                    nullable=False)


def downgrade() -> None:
    # Make organisation_id nullable again
    op.alter_column('question_correlations', 'organisation_id',
                    existing_type=sa.UUID(),
                    nullable=True)
