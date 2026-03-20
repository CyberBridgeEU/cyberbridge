"""Add architecture diagrams and evidence library tables

Revision ID: u1v2w3x4y5z6
Revises: t8u9v0w1x2y3
Create Date: 2026-02-05 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'u1v2w3x4y5z6'
down_revision: Union[str, None] = 't9u0v1w2x3y4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not table_exists('architecture_diagrams'):
        op.create_table(
            'architecture_diagrams',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text, nullable=True),
            sa.Column('diagram_type', sa.String(50), nullable=False),
            sa.Column('file_name', sa.String(255), nullable=True),
            sa.Column('file_path', sa.String(1024), nullable=True),
            sa.Column('file_size', sa.Integer, nullable=True),
            sa.Column('owner', sa.String(255), nullable=True),
            sa.Column('version', sa.String(50), nullable=True),
            sa.Column('organisation_id', UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
        )

    if not table_exists('architecture_diagram_frameworks'):
        op.create_table(
            'architecture_diagram_frameworks',
            sa.Column('diagram_id', UUID(as_uuid=True), sa.ForeignKey('architecture_diagrams.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('framework_id', UUID(as_uuid=True), sa.ForeignKey('frameworks.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )

    if not table_exists('architecture_diagram_risks'):
        op.create_table(
            'architecture_diagram_risks',
            sa.Column('diagram_id', UUID(as_uuid=True), sa.ForeignKey('architecture_diagrams.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('risk_id', UUID(as_uuid=True), sa.ForeignKey('risks.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )

    if not table_exists('evidence_library_items'):
        op.create_table(
            'evidence_library_items',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text, nullable=True),
            sa.Column('evidence_type', sa.String(50), nullable=False),
            sa.Column('file_name', sa.String(255), nullable=True),
            sa.Column('file_path', sa.String(1024), nullable=True),
            sa.Column('file_size', sa.Integer, nullable=True),
            sa.Column('owner', sa.String(255), nullable=True),
            sa.Column('collected_date', sa.DateTime, nullable=True),
            sa.Column('valid_until', sa.DateTime, nullable=True),
            sa.Column('status', sa.String(50), nullable=False),
            sa.Column('collection_method', sa.String(50), nullable=False),
            sa.Column('audit_notes', sa.Text, nullable=True),
            sa.Column('organisation_id', UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
        )

    if not table_exists('evidence_library_frameworks'):
        op.create_table(
            'evidence_library_frameworks',
            sa.Column('evidence_id', UUID(as_uuid=True), sa.ForeignKey('evidence_library_items.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('framework_id', UUID(as_uuid=True), sa.ForeignKey('frameworks.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )

    if not table_exists('evidence_library_controls'):
        op.create_table(
            'evidence_library_controls',
            sa.Column('evidence_id', UUID(as_uuid=True), sa.ForeignKey('evidence_library_items.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('control_id', UUID(as_uuid=True), sa.ForeignKey('controls.id', ondelete='CASCADE'), primary_key=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )


def downgrade() -> None:
    if table_exists('evidence_library_controls'):
        op.drop_table('evidence_library_controls')
    if table_exists('evidence_library_frameworks'):
        op.drop_table('evidence_library_frameworks')
    if table_exists('evidence_library_items'):
        op.drop_table('evidence_library_items')
    if table_exists('architecture_diagram_risks'):
        op.drop_table('architecture_diagram_risks')
    if table_exists('architecture_diagram_frameworks'):
        op.drop_table('architecture_diagram_frameworks')
    if table_exists('architecture_diagrams'):
        op.drop_table('architecture_diagrams')
