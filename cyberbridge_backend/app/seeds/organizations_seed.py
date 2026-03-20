# app/seeds/organizations_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models
from app.dtos import schemas
from app.repositories import user_repository

logger = logging.getLogger(__name__)


class OrganizationsSeed(BaseSeed):
    """Seed initial organizations"""

    def seed(self) -> dict:
        logger.info("Creating initial organizations...")

        # Check if organization with clone-systems.com domain exists
        db_org = self.db.query(models.Organisations).filter(
            models.Organisations.domain == "clone-systems.com"
        ).first()

        if not db_org:
            org_data = {
                "name": "Clone Systems",
                "domain": "clone-systems.com"
            }
            db_org = user_repository.create_organisation_from_dict(self.db, org_data)
            logger.info(f"Created organization: {org_data['name']} with ID: {db_org.id}")
        else:
            logger.info(f"Organization with domain clone-systems.com already exists with ID: {db_org.id}")

        return {"organizations": {"clone_systems": db_org}}
