"""add_regulatory_analysis_runs_table

Revision ID: r1a2b3c4d5e6
Revises: y4z5a6b7c8d9
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'r1a2b3c4d5e6'
down_revision: Union[str, None] = 'y4z5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not table_exists('regulatory_analysis_runs'):
        op.create_table(
            'regulatory_analysis_runs',
            sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
            sa.Column('scan_run_id', UUID(as_uuid=True), sa.ForeignKey('regulatory_scan_runs.id'), nullable=False),
            sa.Column('framework_type', sa.String(100), nullable=False),
            sa.Column('changes_found', sa.Integer, nullable=False, server_default='0'),
            sa.Column('triggered_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('analyzed_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        )
        op.create_index(
            'ix_regulatory_analysis_runs_pair',
            'regulatory_analysis_runs',
            ['scan_run_id', 'framework_type'],
        )


def downgrade() -> None:
    if table_exists('regulatory_analysis_runs'):
        op.drop_index('ix_regulatory_analysis_runs_pair', table_name='regulatory_analysis_runs')
        op.drop_table('regulatory_analysis_runs')
