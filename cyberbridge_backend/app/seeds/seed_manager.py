# app/seeds/seed_manager.py
import logging
from sqlalchemy.orm import Session

from .roles_seed import RolesSeed
from .organizations_seed import OrganizationsSeed
from .users_seed import UsersSeed
from .lookup_tables_seed import LookupTablesSeed
from .smtp_seed import SmtpSeed
from .settings_seed import SettingsSeed
from .scopes_seed import ScopesSeed
from .auditor_roles_seed import AuditorRolesSeed
from .asset_types_seed import AssetTypesSeed
from .template_catalog_seed import TemplateCatalogSeed
from .ce_marking_seed import CEMarkingSeed

logger = logging.getLogger(__name__)


class SeedManager:
    """Manages the execution of all seeds in the correct order"""

    def __init__(self, db: Session):
        self.db = db

    def run_all_seeds(self):
        """Run all seeds in the correct order"""
        logger.info("Starting database seeding...")

        try:
            # Seed roles first (they're referenced by users)
            roles_seed = RolesSeed(self.db)
            roles_result = roles_seed.seed()

            # Seed organizations
            organizations_seed = OrganizationsSeed(self.db)
            organizations_result = organizations_seed.seed()

            # Seed users (requires roles and organizations)
            users_seed = UsersSeed(
                self.db,
                roles_result["roles"],
                organizations_result["organizations"]
            )
            users_result = users_seed.seed()

            # Seed scopes (referenced by assessments and risks)
            scopes_seed = ScopesSeed(self.db)
            scopes_result = scopes_seed.seed()

            # Seed lookup tables
            lookup_seed = LookupTablesSeed(self.db)
            lookup_result = lookup_seed.seed()

            # Seed CE marking lookup tables
            ce_marking_seed = CEMarkingSeed(self.db)
            ce_marking_result = ce_marking_seed.seed()

            # FRAMEWORKS SEEDING DISABLED
            # Frameworks are no longer automatically seeded for the initial organization.
            # Super admins and org admins can manually seed frameworks as needed using the
            # POST /frameworks/seed-template endpoint with template IDs: "CRA", "ISO_27001_2022", or "NIS2_DIRECTIVE"
            logger.info("Framework seeding skipped - organizations can manually seed frameworks via API")

            # Seed SMTP configuration (independent)
            smtp_seed = SmtpSeed(self.db)
            smtp_result = smtp_seed.seed()

            # Seed LLM and Scanner settings (independent)
            settings_seed = SettingsSeed(self.db)
            settings_result = settings_seed.seed()

            # Seed auditor roles for Audit Engagement Workspace
            auditor_roles_seed = AuditorRolesSeed(self.db)
            auditor_roles_result = auditor_roles_seed.seed()

            # Seed default asset types for organizations
            asset_types_seed = AssetTypesSeed(self.db, organizations_result["organizations"])
            asset_types_result = asset_types_seed.seed()

            # Seed template catalogs (controls, risks, policies, frameworks)
            template_catalog_seed = TemplateCatalogSeed(self.db)
            template_catalog_result = template_catalog_seed.seed()

            # Commit all changes
            self.db.commit()
            logger.info("Database seeding completed successfully!")

            return {
                "roles": roles_result,
                "organizations": organizations_result,
                "users": users_result,
                "scopes": scopes_result,
                "lookup_tables": lookup_result,
                "smtp": smtp_result,
                "settings": settings_result,
                "auditor_roles": auditor_roles_result,
                "asset_types": asset_types_result,
                "template_catalog": template_catalog_result,
                "ce_marking": ce_marking_result
            }

        except Exception as e:
            logger.error(f"Error during database seeding: {str(e)}")
            self.db.rollback()
            raise
        finally:
            self.db.close()
