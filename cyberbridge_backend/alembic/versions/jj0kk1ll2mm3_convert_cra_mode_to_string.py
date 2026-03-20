"""Convert cra_mode_enabled boolean to cra_mode string column

Replace the boolean cra_mode_enabled with a string cra_mode column
that supports 'focused', 'extended', or NULL (off).

Revision ID: jj0kk1ll2mm3
Revises: ii9jj0kk1ll2
Create Date: 2026-03-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'jj0kk1ll2mm3'
down_revision: Union[str, None] = 'ii9jj0kk1ll2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new cra_mode column
    op.add_column('organisations', sa.Column('cra_mode', sa.String(20), nullable=True))

    # Migrate data: true -> 'focused', false/null -> NULL
    op.execute("UPDATE organisations SET cra_mode = 'focused' WHERE cra_mode_enabled = true")

    # Drop old column
    op.drop_column('organisations', 'cra_mode_enabled')


def downgrade() -> None:
    # Add back boolean column
    op.add_column('organisations', sa.Column('cra_mode_enabled', sa.Boolean(), nullable=False, server_default='false'))

    # Migrate data back: 'focused' or 'extended' -> true, NULL -> false
    op.execute("UPDATE organisations SET cra_mode_enabled = true WHERE cra_mode IS NOT NULL")

    # Drop string column
    op.drop_column('organisations', 'cra_mode')
