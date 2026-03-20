# app/seeds/auditor_roles_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class AuditorRolesSeed(BaseSeed):
    """Seed auditor roles for the Audit Engagement Workspace"""

    def seed(self) -> dict:
        logger.info("Creating auditor roles...")

        roles_data = [
            {
                "role_name": "guest_auditor",
                "can_comment": True,
                "can_request_evidence": True,
                "can_add_findings": False,
                "can_sign_off": False
            },
            {
                "role_name": "auditor_lead",
                "can_comment": True,
                "can_request_evidence": True,
                "can_add_findings": True,
                "can_sign_off": True
            }
        ]

        role_instances = {}

        for role_data in roles_data:
            role, created = self.get_or_create(
                models.AuditorRole,
                {"role_name": role_data["role_name"]},
                role_data
            )
            role_instances[role_data["role_name"]] = role

        return {"auditor_roles": role_instances}
