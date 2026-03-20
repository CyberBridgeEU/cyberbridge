"""add SSO auth_provider column and make hashed_password nullable

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-02-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6g7h8i9'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('users', 'hashed_password', nullable=True)
    op.add_column('users', sa.Column('auth_provider', sa.String(20), nullable=False, server_default='local'))


def downgrade():
    op.drop_column('users', 'auth_provider')
    op.alter_column('users', 'hashed_password', nullable=False)
