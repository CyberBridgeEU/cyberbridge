# app/seeds/scopes_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class ScopesSeed(BaseSeed):
    """Seed scope types"""

    def __init__(self, db):
        super().__init__(db)

    def seed(self) -> dict:
        logger.info("Creating scope types...")

        scopes_data = [
            {"scope_name": "Product"},
            {"scope_name": "Organization"},
            {"scope_name": "Other"},      # For flexible/undefined scope
            {"scope_name": "Asset"},      # Reserved for future use
            {"scope_name": "Project"},    # Reserved for future use
            {"scope_name": "Process"},    # Reserved for future use
        ]

        created_scopes = {}

        for scope_data in scopes_data:
            scope, created = self.get_or_create(
                models.Scopes,
                {"scope_name": scope_data["scope_name"]},
                scope_data
            )
            created_scopes[scope_data["scope_name"]] = scope

        logger.info(f"Created/verified {len(created_scopes)} scope types")

        return created_scopes
