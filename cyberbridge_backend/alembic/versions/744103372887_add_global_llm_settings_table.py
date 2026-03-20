"""add_global_llm_settings_table

Revision ID: 744103372887
Revises: 3745a5e751fb
Create Date: 2025-10-01 12:10:53.635785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '744103372887'
down_revision: Union[str, None] = '3745a5e751fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if a table exists in the database"""
    conn = op.get_bind()
    inspector = inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    # Create llm_settings table if it doesn't exist
    if not table_exists('llm_settings'):
        op.create_table(
            'llm_settings',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('custom_llm_url', sa.Text(), nullable=True),
            sa.Column('custom_llm_payload', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

        # Insert default settings row
        op.execute("""
            INSERT INTO llm_settings (id, custom_llm_url, custom_llm_payload)
            VALUES (gen_random_uuid(), NULL, NULL)
        """)


def downgrade() -> None:
    op.drop_table('llm_settings')
