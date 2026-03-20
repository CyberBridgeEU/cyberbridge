"""Add framework_id to control_risks and control_policies junction tables

Revision ID: dd4ee5ff6gg7
Revises: cc3dd4ee5ff6
Create Date: 2026-02-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'dd4ee5ff6gg7'
down_revision: Union[str, None] = 'cc3dd4ee5ff6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # =========================================================================
    # CONTROL_RISKS: Add framework_id
    # =========================================================================

    # 1. Add nullable framework_id column
    op.add_column('control_risks', sa.Column('framework_id', UUID(as_uuid=True), nullable=True))

    # 2. Drop the old composite primary key
    op.drop_constraint('control_risks_pkey', 'control_risks', type_='primary')

    # 3. Backfill framework_id from the objective chain:
    #    control_risks.control_id → objective_controls.control_id
    #    control_risks.risk_id → objective_risks.risk_id
    #    Both point to the same objective → chapter → framework
    #
    #    A control-risk pair may belong to MULTIPLE frameworks (e.g., GDPR and SOC2).
    #    We first UPDATE existing rows with the first matching framework_id,
    #    then INSERT additional rows for pairs that belong to more frameworks.

    # Build a mapping of (control_id, risk_id) → [framework_id, ...] via the objective chain
    # For control_risks: find objectives that link to BOTH the control AND the risk
    mapping_query = sa.text("""
        SELECT DISTINCT cr.control_id, cr.risk_id, ch.framework_id
        FROM control_risks cr
        JOIN objective_controls oc ON oc.control_id = cr.control_id
        JOIN objective_risks orr ON orr.risk_id = cr.risk_id
            AND orr.objective_id = oc.objective_id
        JOIN objectives o ON o.id = oc.objective_id
        JOIN chapters ch ON ch.id = o.chapter_id
        ORDER BY cr.control_id, cr.risk_id, ch.framework_id
    """)
    rows = conn.execute(mapping_query).fetchall()

    # Group by (control_id, risk_id) to find which frameworks each pair belongs to
    from collections import defaultdict
    cr_frameworks = defaultdict(list)
    for control_id, risk_id, framework_id in rows:
        cr_frameworks[(control_id, risk_id)].append(framework_id)

    # Update existing rows with the first framework_id
    for (control_id, risk_id), framework_ids in cr_frameworks.items():
        conn.execute(sa.text("""
            UPDATE control_risks
            SET framework_id = :fw_id
            WHERE control_id = :c_id AND risk_id = :r_id AND framework_id IS NULL
        """), {"fw_id": framework_ids[0], "c_id": control_id, "r_id": risk_id})

        # Insert additional rows for extra frameworks
        for fw_id in framework_ids[1:]:
            conn.execute(sa.text("""
                INSERT INTO control_risks (control_id, risk_id, framework_id, created_at)
                SELECT :c_id, :r_id, :fw_id, created_at
                FROM control_risks
                WHERE control_id = :c_id AND risk_id = :r_id AND framework_id = :first_fw_id
                LIMIT 1
            """), {"c_id": control_id, "r_id": risk_id, "fw_id": fw_id, "first_fw_id": framework_ids[0]})

    # Fallback: assign remaining NULLs to the org's first framework
    # These are manual user-created links without an objective chain connection
    conn.execute(sa.text("""
        UPDATE control_risks
        SET framework_id = sub.framework_id
        FROM (
            SELECT DISTINCT ON (c2.organisation_id) c2.organisation_id, f.id AS framework_id
            FROM controls c2
            JOIN frameworks f ON f.organisation_id = c2.organisation_id
            ORDER BY c2.organisation_id, f.created_at ASC
        ) sub
        WHERE control_risks.framework_id IS NULL
          AND control_risks.control_id IN (
              SELECT c3.id FROM controls c3 WHERE c3.organisation_id = sub.organisation_id
          )
    """))

    # Make NOT NULL and add FK
    op.alter_column('control_risks', 'framework_id', nullable=False)
    op.create_foreign_key(
        'fk_control_risks_framework_id',
        'control_risks', 'frameworks',
        ['framework_id'], ['id'],
        ondelete='CASCADE'
    )

    # Create new composite PK
    op.create_primary_key('control_risks_pkey', 'control_risks', ['control_id', 'risk_id', 'framework_id'])

    # =========================================================================
    # CONTROL_POLICIES: Add framework_id
    # =========================================================================

    # 1. Add nullable framework_id column
    op.add_column('control_policies', sa.Column('framework_id', UUID(as_uuid=True), nullable=True))

    # 2. Drop the old composite primary key
    op.drop_constraint('control_policies_pkey', 'control_policies', type_='primary')

    # 3. Backfill framework_id from the objective chain:
    #    control_policies.control_id → objective_controls.control_id
    #    control_policies.policy_id → policy_objectives.policy_id
    #    Both point to the same objective → chapter → framework
    cp_mapping_query = sa.text("""
        SELECT DISTINCT cp.control_id, cp.policy_id, ch.framework_id
        FROM control_policies cp
        JOIN objective_controls oc ON oc.control_id = cp.control_id
        JOIN policy_objectives po ON po.policy_id = cp.policy_id
            AND po.objective_id = oc.objective_id
        JOIN objectives o ON o.id = oc.objective_id
        JOIN chapters ch ON ch.id = o.chapter_id
        ORDER BY cp.control_id, cp.policy_id, ch.framework_id
    """)
    cp_rows = conn.execute(cp_mapping_query).fetchall()

    cp_frameworks = defaultdict(list)
    for control_id, policy_id, framework_id in cp_rows:
        cp_frameworks[(control_id, policy_id)].append(framework_id)

    # Update existing rows with the first framework_id
    for (control_id, policy_id), framework_ids in cp_frameworks.items():
        conn.execute(sa.text("""
            UPDATE control_policies
            SET framework_id = :fw_id
            WHERE control_id = :c_id AND policy_id = :p_id AND framework_id IS NULL
        """), {"fw_id": framework_ids[0], "c_id": control_id, "p_id": policy_id})

        # Insert additional rows for extra frameworks
        for fw_id in framework_ids[1:]:
            conn.execute(sa.text("""
                INSERT INTO control_policies (control_id, policy_id, framework_id, created_at)
                SELECT :c_id, :p_id, :fw_id, created_at
                FROM control_policies
                WHERE control_id = :c_id AND policy_id = :p_id AND framework_id = :first_fw_id
                LIMIT 1
            """), {"c_id": control_id, "p_id": policy_id, "fw_id": fw_id, "first_fw_id": framework_ids[0]})

    # Fallback: assign remaining NULLs to the org's first framework
    conn.execute(sa.text("""
        UPDATE control_policies
        SET framework_id = sub.framework_id
        FROM (
            SELECT DISTINCT ON (c2.organisation_id) c2.organisation_id, f.id AS framework_id
            FROM controls c2
            JOIN frameworks f ON f.organisation_id = c2.organisation_id
            ORDER BY c2.organisation_id, f.created_at ASC
        ) sub
        WHERE control_policies.framework_id IS NULL
          AND control_policies.control_id IN (
              SELECT c3.id FROM controls c3 WHERE c3.organisation_id = sub.organisation_id
          )
    """))

    # Make NOT NULL and add FK
    op.alter_column('control_policies', 'framework_id', nullable=False)
    op.create_foreign_key(
        'fk_control_policies_framework_id',
        'control_policies', 'frameworks',
        ['framework_id'], ['id'],
        ondelete='CASCADE'
    )

    # Create new composite PK
    op.create_primary_key('control_policies_pkey', 'control_policies', ['control_id', 'policy_id', 'framework_id'])


def downgrade() -> None:
    # CONTROL_POLICIES: Remove framework_id
    op.drop_constraint('control_policies_pkey', 'control_policies', type_='primary')
    op.drop_constraint('fk_control_policies_framework_id', 'control_policies', type_='foreignkey')

    # Remove duplicate rows (keep one per control_id, policy_id)
    conn = op.get_bind()
    conn.execute(sa.text("""
        DELETE FROM control_policies cp1
        USING control_policies cp2
        WHERE cp1.control_id = cp2.control_id
          AND cp1.policy_id = cp2.policy_id
          AND cp1.framework_id > cp2.framework_id
    """))

    op.drop_column('control_policies', 'framework_id')
    op.create_primary_key('control_policies_pkey', 'control_policies', ['control_id', 'policy_id'])

    # CONTROL_RISKS: Remove framework_id
    op.drop_constraint('control_risks_pkey', 'control_risks', type_='primary')
    op.drop_constraint('fk_control_risks_framework_id', 'control_risks', type_='foreignkey')

    # Remove duplicate rows (keep one per control_id, risk_id)
    conn.execute(sa.text("""
        DELETE FROM control_risks cr1
        USING control_risks cr2
        WHERE cr1.control_id = cr2.control_id
          AND cr1.risk_id = cr2.risk_id
          AND cr1.framework_id > cr2.framework_id
    """))

    op.drop_column('control_risks', 'framework_id')
    op.create_primary_key('control_risks_pkey', 'control_risks', ['control_id', 'risk_id'])
