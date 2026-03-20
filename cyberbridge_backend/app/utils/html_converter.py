import re
from bs4 import BeautifulSoup


def convert_html_to_plain_text(html: str) -> str:
    """Convert HTML (e.g. from mammoth DOCX conversion) to formatted plain text
    with markdown-style indicators for bold/italic."""
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # Replace bold/strong with markdown-style indicators
    for tag in soup.find_all(["strong", "b"]):
        tag.replace_with(f"**{tag.get_text()}**")

    # Replace italic/em with markdown-style indicators
    for tag in soup.find_all(["em", "i"]):
        tag.replace_with(f"*{tag.get_text()}*")

    # Replace list items with bullet points
    for tag in soup.find_all("li"):
        tag.replace_with(f"\n• {tag.get_text()}")

    # Get plain text
    text = soup.get_text(separator="\n")

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n ", "\n", text)
    text = re.sub(r" \n", "\n", text)

    return text.strip()
