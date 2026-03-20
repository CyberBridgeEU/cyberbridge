"""Add CE marking tables

Revision ID: ff6gg7hh8ii9
Revises: ee5ff6gg7hh8
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = 'ff6gg7hh8ii9'
down_revision = 'ee5ff6gg7hh8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CE Product Types (lookup)
    op.create_table(
        'ce_product_types',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('recommended_placement', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # CE Document Types (lookup)
    op.create_table(
        'ce_document_types',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_mandatory', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # CE Checklist Template Items (lookup)
    op.create_table(
        'ce_checklist_template_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default=sa.text('0')),
        sa.Column('is_mandatory', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # CE Marking Checklists (org-scoped)
    op.create_table(
        'ce_marking_checklists',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('asset_id', UUID(as_uuid=True), sa.ForeignKey('assets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ce_product_type_id', UUID(as_uuid=True), sa.ForeignKey('ce_product_types.id'), nullable=True),
        sa.Column('ce_placement', sa.String(100), nullable=True),
        sa.Column('ce_placement_notes', sa.Text, nullable=True),
        sa.Column('notified_body_required', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('notified_body_name', sa.String(255), nullable=True),
        sa.Column('notified_body_number', sa.String(100), nullable=True),
        sa.Column('notified_body_certificate_ref', sa.String(255), nullable=True),
        sa.Column('version_identifier', sa.String(255), nullable=True),
        sa.Column('build_identifier', sa.String(255), nullable=True),
        sa.Column('doc_publication_url', sa.String(500), nullable=True),
        sa.Column('product_variants', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='not_started'),
        sa.Column('readiness_score', sa.Float, nullable=False, server_default=sa.text('0.0')),
        sa.Column('organisation_id', UUID(as_uuid=True), sa.ForeignKey('organisations.id'), nullable=False),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('last_updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('asset_id', name='uq_ce_checklist_asset'),
    )

    # CE Checklist Items (org-scoped)
    op.create_table(
        'ce_checklist_items',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('checklist_id', UUID(as_uuid=True), sa.ForeignKey('ce_marking_checklists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('template_item_id', UUID(as_uuid=True), sa.ForeignKey('ce_checklist_template_items.id'), nullable=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('is_completed', sa.Boolean, nullable=False, server_default=sa.text('false')),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('completed_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default=sa.text('0')),
        sa.Column('is_mandatory', sa.Boolean, nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # CE Document Statuses (org-scoped)
    op.create_table(
        'ce_document_statuses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('checklist_id', UUID(as_uuid=True), sa.ForeignKey('ce_marking_checklists.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_type_id', UUID(as_uuid=True), sa.ForeignKey('ce_document_types.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='not_started'),
        sa.Column('document_reference', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('completed_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('ce_document_statuses')
    op.drop_table('ce_checklist_items')
    op.drop_table('ce_marking_checklists')
    op.drop_table('ce_checklist_template_items')
    op.drop_table('ce_document_types')
    op.drop_table('ce_product_types')
