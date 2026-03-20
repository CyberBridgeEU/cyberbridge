import json
from typing import Optional, Union


def parse_labels(raw: Optional[Union[str, list]]) -> list[str]:
    """Parse labels from Text column (JSON string) or list."""
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, list) else []
    except (json.JSONDecodeError, TypeError):
        return []
