"""add_organisation_id_to_question_correlations

Revision ID: 671d6c3d7243
Revises: bcc2f3b453ed
Create Date: 2025-11-12 14:21:24.303789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '671d6c3d7243'
down_revision: Union[str, None] = 'bcc2f3b453ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add organisation_id column to question_correlations table
    # NULL means global correlation (applies to all organizations)
    # Non-NULL means org-specific correlation
    op.add_column('question_correlations',
                  sa.Column('organisation_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_question_correlations_organisation',
        'question_correlations', 'organisations',
        ['organisation_id'], ['id'],
        ondelete='CASCADE'
    )

    # Create index for faster org-specific queries
    op.create_index(
        'ix_question_correlations_organisation_id',
        'question_correlations',
        ['organisation_id']
    )


def downgrade() -> None:
    # Remove index
    op.drop_index('ix_question_correlations_organisation_id', 'question_correlations')

    # Remove foreign key
    op.drop_constraint('fk_question_correlations_organisation', 'question_correlations', type_='foreignkey')

    # Remove column
    op.drop_column('question_correlations', 'organisation_id')
