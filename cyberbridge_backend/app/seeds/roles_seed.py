# app/seeds/roles_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class RolesSeed(BaseSeed):
    """Seed initial roles"""

    def seed(self) -> dict:
        logger.info("Creating initial roles...")

        roles_data = [
            {"role_name": "super_admin"},
            {"role_name": "org_admin"},
            {"role_name": "org_user"}
        ]

        role_instances = {}

        for role_data in roles_data:
            role, created = self.get_or_create(
                models.Role,
                {"role_name": role_data["role_name"]},
                role_data
            )
            role_instances[role_data["role_name"]] = role

        return {"roles": role_instances}
