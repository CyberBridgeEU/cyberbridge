"""add_scope_fields_to_question_correlations

Revision ID: 6635cb5f9c90
Revises: c6d8e7f8241b
Create Date: 2025-11-17 16:11:15.840296

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6635cb5f9c90'
down_revision: Union[str, None] = 'c6d8e7f8241b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add scope_id column (FK to scopes table)
    op.add_column('question_correlations',
                  sa.Column('scope_id', sa.UUID(), nullable=True))

    # Add scope_entity_id column (UUID, nullable - used for Product/Organization scopes)
    op.add_column('question_correlations',
                  sa.Column('scope_entity_id', sa.UUID(), nullable=True))

    # Get the "Other" scope ID and set it as default for existing correlations
    # This ensures backward compatibility - existing correlations work with "Other" scope
    op.execute("""
        UPDATE question_correlations
        SET scope_id = (SELECT id FROM scopes WHERE scope_name = 'Other')
        WHERE scope_id IS NULL
    """)

    # Make scope_id required after setting defaults
    op.alter_column('question_correlations', 'scope_id',
                    nullable=False)

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_question_correlations_scope_id',
        'question_correlations', 'scopes',
        ['scope_id'], ['id']
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_question_correlations_scope_id',
                      'question_correlations', type_='foreignkey')

    # Drop columns
    op.drop_column('question_correlations', 'scope_entity_id')
    op.drop_column('question_correlations', 'scope_id')
