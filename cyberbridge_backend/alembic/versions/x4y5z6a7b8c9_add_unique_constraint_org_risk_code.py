"""add unique constraint on organisation_id and risk_code

Revision ID: x4y5z6a7b8c9
Revises: w3x4y5z6a7b8
Create Date: 2026-02-11 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'x4y5z6a7b8c9'
down_revision: Union[str, None] = 'w3x4y5z6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('uq_risks_org_risk_code', 'risks', ['organisation_id', 'risk_code'])


def downgrade() -> None:
    op.drop_constraint('uq_risks_org_risk_code', 'risks', type_='unique')
