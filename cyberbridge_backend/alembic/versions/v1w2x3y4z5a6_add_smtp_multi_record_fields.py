"""Add sender_email and label to smtp_configurations, make username and password nullable

Revision ID: v1w2x3y4z5a6
Revises: g7h8i9j0k1l2
Create Date: 2026-02-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'v1w2x3y4z5a6'
down_revision: Union[str, None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column('smtp_configurations', sa.Column('sender_email', sa.String(255), nullable=True))
    op.add_column('smtp_configurations', sa.Column('label', sa.String(255), nullable=True))

    # Make username and password nullable
    op.alter_column('smtp_configurations', 'username',
                     existing_type=sa.String(255),
                     nullable=True)
    op.alter_column('smtp_configurations', 'password',
                     existing_type=sa.String(500),
                     nullable=True)


def downgrade() -> None:
    # Make username and password non-nullable again
    op.alter_column('smtp_configurations', 'password',
                     existing_type=sa.String(500),
                     nullable=False)
    op.alter_column('smtp_configurations', 'username',
                     existing_type=sa.String(255),
                     nullable=False)

    # Remove new columns
    op.drop_column('smtp_configurations', 'label')
    op.drop_column('smtp_configurations', 'sender_email')
