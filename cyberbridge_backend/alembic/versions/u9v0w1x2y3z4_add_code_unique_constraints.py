"""Add unique constraints for policy_code and control code per organisation

Revision ID: u9v0w1x2y3z4
Revises: t8u9v0w1x2y3
Create Date: 2026-02-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'u9v0w1x2y3z4'
down_revision: Union[str, None] = 't9u0v1w2x3y4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def constraint_exists(constraint_name: str) -> bool:
    """Check if a constraint exists in the database"""
    conn = op.get_bind()
    inspector = inspect(conn)
    for table_name in inspector.get_table_names():
        for constraint in inspector.get_unique_constraints(table_name):
            if constraint['name'] == constraint_name:
                return True
    return False


def upgrade() -> None:
    # Add unique constraint to policies (organisation_id, policy_code)
    if not constraint_exists('uq_policies_org_policy_code'):
        op.create_unique_constraint(
            'uq_policies_org_policy_code',
            'policies',
            ['organisation_id', 'policy_code']
        )

    # Add unique constraint to controls (organisation_id, code)
    if not constraint_exists('uq_controls_org_code'):
        op.create_unique_constraint(
            'uq_controls_org_code',
            'controls',
            ['organisation_id', 'code']
        )


def downgrade() -> None:
    # Remove unique constraint from controls
    if constraint_exists('uq_controls_org_code'):
        op.drop_constraint('uq_controls_org_code', 'controls', type_='unique')

    # Remove unique constraint from policies
    if constraint_exists('uq_policies_org_policy_code'):
        op.drop_constraint('uq_policies_org_policy_code', 'policies', type_='unique')
