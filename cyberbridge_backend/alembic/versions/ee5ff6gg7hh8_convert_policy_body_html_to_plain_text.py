"""Convert policy body HTML to plain text

Revision ID: ee5ff6gg7hh8
Revises: dd4ee5ff6gg7
Create Date: 2026-02-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import re
from bs4 import BeautifulSoup


# revision identifiers, used by Alembic.
revision: str = 'ee5ff6gg7hh8'
down_revision: Union[str, None] = 'dd4ee5ff6gg7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _convert_html_to_plain_text(html: str) -> str:
    """Convert HTML to formatted plain text with markdown-style indicators."""
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(["strong", "b"]):
        tag.replace_with(f"**{tag.get_text()}**")

    for tag in soup.find_all(["em", "i"]):
        tag.replace_with(f"*{tag.get_text()}*")

    for tag in soup.find_all("li"):
        tag.replace_with(f"\n• {tag.get_text()}")

    text = soup.get_text(separator="\n")

    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n ", "\n", text)
    text = re.sub(r" \n", "\n", text)

    return text.strip()


def _looks_like_html(text: str) -> bool:
    """Check if text contains HTML tags (to avoid re-processing plain text bodies)."""
    if not text:
        return False
    return bool(re.search(r"<(p|div|br|strong|em|ul|ol|li|h[1-6]|table|span)\b[^>]*>", text, re.IGNORECASE))


def upgrade() -> None:
    conn = op.get_bind()
    results = conn.execute(
        sa.text("SELECT id, body FROM policies WHERE body IS NOT NULL AND body != ''")
    ).fetchall()

    for row in results:
        policy_id, body = row
        if _looks_like_html(body):
            plain_text = _convert_html_to_plain_text(body)
            conn.execute(
                sa.text("UPDATE policies SET body = :body WHERE id = :id"),
                {"body": plain_text, "id": policy_id}
            )


def downgrade() -> None:
    # Cannot restore original HTML from plain text — this is a one-way data migration
    pass
