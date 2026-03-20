"""remove_default_scope_type_and_simplify_scope_selection_mode

Revision ID: c6d8e7f8241b
Revises: 50a6ac349aab
Create Date: 2025-11-14 16:11:18.514438

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6d8e7f8241b'
down_revision: Union[str, None] = '50a6ac349aab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop default_scope_type column from frameworks table
    op.drop_column('frameworks', 'default_scope_type')

    # Update existing 'flexible' values to 'optional' in scope_selection_mode
    op.execute("""
        UPDATE frameworks
        SET scope_selection_mode = 'optional'
        WHERE scope_selection_mode = 'flexible'
    """)

    # Update the default value of scope_selection_mode from 'flexible' to 'optional'
    op.alter_column('frameworks', 'scope_selection_mode',
                    server_default='optional')


def downgrade() -> None:
    # Restore default_scope_type column
    op.add_column('frameworks',
                  sa.Column('default_scope_type', sa.String(length=50), nullable=True))

    # Restore the original default value
    op.alter_column('frameworks', 'scope_selection_mode',
                    server_default='flexible')
