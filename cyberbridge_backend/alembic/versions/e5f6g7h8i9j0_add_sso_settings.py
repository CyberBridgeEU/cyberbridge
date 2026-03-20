"""add sso_settings table

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-02-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'e5f6g7h8i9j0'
down_revision = 'd4e5f6g7h8i9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sso_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('sso_enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('google_client_id', sa.Text(), nullable=True),
        sa.Column('google_client_secret', sa.Text(), nullable=True),
        sa.Column('microsoft_client_id', sa.Text(), nullable=True),
        sa.Column('microsoft_client_secret', sa.Text(), nullable=True),
        sa.Column('microsoft_tenant_id', sa.String(255), nullable=True, server_default='common'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('sso_settings')
