"""separate_scanner_settings_from_llm_settings

Revision ID: 6176e58c8a46
Revises: 9987833bf4b3
Create Date: 2025-10-01 12:26:33.521912

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6176e58c8a46'
down_revision: Union[str, None] = '9987833bf4b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if scanner_settings table already exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if 'scanner_settings' not in tables:
        # Create new scanner_settings table
        op.create_table(
            'scanner_settings',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('scanners_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('allowed_scanner_domains', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # Check if scanner columns exist in llm_settings
    llm_settings_columns = [col['name'] for col in inspector.get_columns('llm_settings')]

    if 'scanners_enabled' in llm_settings_columns:
        # Migrate existing scanner settings data from llm_settings to scanner_settings
        # Only insert if scanner_settings is empty
        op.execute("""
            INSERT INTO scanner_settings (id, scanners_enabled, allowed_scanner_domains)
            SELECT gen_random_uuid(), scanners_enabled, allowed_scanner_domains
            FROM llm_settings
            LIMIT 1
            ON CONFLICT DO NOTHING
        """)

        # Drop scanner columns from llm_settings
        op.drop_column('llm_settings', 'allowed_scanner_domains')
        op.drop_column('llm_settings', 'scanners_enabled')


def downgrade() -> None:
    # Add scanner columns back to llm_settings
    op.add_column('llm_settings', sa.Column('scanners_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('llm_settings', sa.Column('allowed_scanner_domains', sa.Text(), nullable=True))

    # Migrate scanner settings data back to llm_settings
    op.execute("""
        UPDATE llm_settings
        SET scanners_enabled = (SELECT scanners_enabled FROM scanner_settings LIMIT 1),
            allowed_scanner_domains = (SELECT allowed_scanner_domains FROM scanner_settings LIMIT 1)
    """)

    # Drop scanner_settings table
    op.drop_table('scanner_settings')
