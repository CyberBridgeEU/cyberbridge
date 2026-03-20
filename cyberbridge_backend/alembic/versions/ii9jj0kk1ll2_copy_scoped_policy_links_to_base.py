"""Copy policy-objective links from scoped clones to base objectives

One-time data migration: on production, policies were linked to scoped clone
objectives instead of base objectives. This copies those links to the base
objectives so that all scopes can inherit them correctly.

Revision ID: ii9jj0kk1ll2
Revises: hh8ii9jj0kk1
Create Date: 2026-03-11 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'ii9jj0kk1ll2'
down_revision: Union[str, None] = 'hh8ii9jj0kk1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Find all policy-objective links on scoped clones that are missing from
    # the corresponding base objectives.
    # Match scoped → base by chapter_id + title + subchapter where base has
    # scope_id IS NULL and scope_entity_id IS NULL.
    result = conn.execute(text("""
        SELECT DISTINCT po.policy_id, base.id AS base_objective_id
        FROM policy_objectives po
        JOIN objectives scoped ON scoped.id = po.objective_id
            AND scoped.scope_id IS NOT NULL
        JOIN objectives base ON base.chapter_id = scoped.chapter_id
            AND base.title = scoped.title
            AND COALESCE(base.subchapter, '') = COALESCE(scoped.subchapter, '')
            AND base.scope_id IS NULL
            AND base.scope_entity_id IS NULL
        WHERE NOT EXISTS (
            SELECT 1 FROM policy_objectives existing
            WHERE existing.policy_id = po.policy_id
              AND existing.objective_id = base.id
        )
    """))

    rows = result.fetchall()
    if rows:
        for policy_id, base_objective_id in rows:
            conn.execute(text(
                "INSERT INTO policy_objectives (policy_id, objective_id) VALUES (:pid, :oid)"
            ), {"pid": policy_id, "oid": base_objective_id})


def downgrade() -> None:
    # This is a data migration; downgrade would require tracking which rows
    # were inserted, which is not practical. No-op.
    pass
