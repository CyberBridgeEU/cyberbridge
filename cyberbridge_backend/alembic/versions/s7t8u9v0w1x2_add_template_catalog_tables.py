"""Add template catalog tables for frameworks, policies, controls, and risks

Revision ID: s7t8u9v0w1x2
Revises: r6s7t8u9v0w1
Create Date: 2026-02-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 's7t8u9v0w1x2'
down_revision: Union[str, None] = 'r6s7t8u9v0w1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database"""
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not table_exists('framework_templates'):
        op.create_table(
            'framework_templates',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('template_id', sa.String(100), nullable=False, unique=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text, nullable=True),
            sa.Column('seed_filename', sa.String(255), nullable=True),
            sa.Column('source', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
        )

    if not table_exists('policy_templates'):
        op.create_table(
            'policy_templates',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('filename', sa.String(255), nullable=False, unique=True),
            sa.Column('title', sa.String(255), nullable=True),
            sa.Column('content_docx', sa.LargeBinary, nullable=True),
            sa.Column('content_sha256', sa.String(64), nullable=True),
            sa.Column('file_size', sa.Integer, nullable=True),
            sa.Column('file_modified_at', sa.DateTime, nullable=True),
            sa.Column('source', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
        )

    if not table_exists('control_set_templates'):
        op.create_table(
            'control_set_templates',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('name', sa.String(255), nullable=False, unique=True),
            sa.Column('description', sa.Text, nullable=True),
            sa.Column('source', sa.String(50), nullable=True),
            sa.Column('control_count', sa.Integer, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now())
        )

    if not table_exists('control_templates'):
        op.create_table(
            'control_templates',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('control_set_template_id', UUID(as_uuid=True), sa.ForeignKey('control_set_templates.id'), nullable=False),
            sa.Column('code', sa.String(100), nullable=False),
            sa.Column('name', sa.Text, nullable=False),
            sa.Column('description', sa.Text, nullable=True),
            sa.Column('sort_order', sa.Integer, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
            sa.UniqueConstraint('control_set_template_id', 'code', name='uq_control_template_set_code')
        )

    if not table_exists('risk_template_categories'):
        op.create_table(
            'risk_template_categories',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('category_key', sa.String(100), nullable=False, unique=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text, nullable=True),
            sa.Column('risk_count', sa.Integer, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )

    if not table_exists('risk_templates'):
        op.create_table(
            'risk_templates',
            sa.Column('id', UUID(as_uuid=True), primary_key=True),
            sa.Column('category_id', UUID(as_uuid=True), sa.ForeignKey('risk_template_categories.id'), nullable=False),
            sa.Column('risk_code', sa.String(50), nullable=False, unique=True),
            sa.Column('risk_category_name', sa.String(255), nullable=False),
            sa.Column('risk_category_description', sa.Text, nullable=True),
            sa.Column('risk_potential_impact', sa.Text, nullable=True),
            sa.Column('risk_control', sa.Text, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now())
        )


def downgrade() -> None:
    if table_exists('risk_templates'):
        op.drop_table('risk_templates')
    if table_exists('risk_template_categories'):
        op.drop_table('risk_template_categories')
    if table_exists('control_templates'):
        op.drop_table('control_templates')
    if table_exists('control_set_templates'):
        op.drop_table('control_set_templates')
    if table_exists('policy_templates'):
        op.drop_table('policy_templates')
    if table_exists('framework_templates'):
        op.drop_table('framework_templates')
