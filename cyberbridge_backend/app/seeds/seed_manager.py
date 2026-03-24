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
from ..models.models import RegulatorySource, RegulatoryMonitorSettings

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

            # Seed Regulatory Monitor defaults
            reg_result = self._seed_regulatory_monitor_defaults()

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
                "ce_marking": ce_marking_result,
                "regulatory_monitor": reg_result
            }

        except Exception as e:
            logger.error(f"Error during database seeding: {str(e)}")
            self.db.rollback()
            raise
        finally:
            self.db.close()

    def _seed_regulatory_monitor_defaults(self):
        """Seed default regulatory monitor settings and sources."""
        import uuid
        import json

        # Seed default settings if not exists
        existing_settings = self.db.query(RegulatoryMonitorSettings).first()
        if not existing_settings:
            settings = RegulatoryMonitorSettings(
                id=uuid.uuid4(),
                scan_frequency="weekly",
                scan_day_of_week="mon",
                scan_hour=4,
                searxng_url="http://searxng:8080",
                enabled=False  # Disabled by default until admin enables
            )
            self.db.add(settings)
            logger.info("Seeded regulatory monitor default settings")

        # Seed default sources if none exist
        existing_sources = self.db.query(RegulatorySource).count()
        if existing_sources == 0:
            default_sources = [
                # EU Frameworks - EUR-Lex API (primary)
                {"framework_type": "cra", "source_name": "EUR-Lex CRA", "source_type": "eurlex_api", "direct_url": "32024R2847", "priority": 1},
                {"framework_type": "nis2_directive", "source_name": "EUR-Lex NIS2", "source_type": "eurlex_api", "direct_url": "32022L2555", "priority": 1},
                {"framework_type": "gdpr", "source_name": "EUR-Lex GDPR", "source_type": "eurlex_api", "direct_url": "32016R0679", "priority": 1},
                {"framework_type": "dora_2022", "source_name": "EUR-Lex DORA", "source_type": "eurlex_api", "direct_url": "32022R2554", "priority": 1},
                # EU Frameworks - SearXNG (secondary)
                {"framework_type": "cra", "source_name": "SearXNG CRA", "source_type": "searxng", "search_query": "EU Cyber Resilience Act amendment update 2024 2025 2026", "priority": 2},
                {"framework_type": "nis2_directive", "source_name": "SearXNG NIS2", "source_type": "searxng", "search_query": "NIS2 Directive amendment update implementation", "priority": 2},
                {"framework_type": "gdpr", "source_name": "SearXNG GDPR", "source_type": "searxng", "search_query": "GDPR amendment update regulatory change", "priority": 2},
                {"framework_type": "dora_2022", "source_name": "SearXNG DORA", "source_type": "searxng", "search_query": "DORA Digital Operational Resilience Act update", "priority": 2},
                # US Frameworks - NIST API + SearXNG
                {"framework_type": "nist_csf_2_0", "source_name": "NIST CSRC", "source_type": "nist_api", "direct_url": "sp800-53", "priority": 1},
                {"framework_type": "nist_csf_2_0", "source_name": "SearXNG NIST CSF", "source_type": "searxng", "search_query": "NIST Cybersecurity Framework update revision", "priority": 2},
                {"framework_type": "cmmc_2_0", "source_name": "SearXNG CMMC", "source_type": "searxng", "search_query": "CMMC 2.0 Cybersecurity Maturity Model update", "priority": 1},
                {"framework_type": "hipaa_privacy_rule", "source_name": "SearXNG HIPAA", "source_type": "searxng", "search_query": "HIPAA Privacy Rule amendment update HHS", "priority": 1},
                {"framework_type": "ftc_safeguards", "source_name": "SearXNG FTC", "source_type": "searxng", "search_query": "FTC Safeguards Rule update amendment", "priority": 1},
                {"framework_type": "ccpa_california_consumer_privacy_act", "source_name": "SearXNG CCPA", "source_type": "searxng", "search_query": "CCPA CPRA California Privacy Rights Act update", "priority": 1},
                # Industry Frameworks - SearXNG only
                {"framework_type": "iso_27001_2022", "source_name": "SearXNG ISO 27001", "source_type": "searxng", "search_query": "ISO 27001 2022 amendment update revision", "priority": 1},
                {"framework_type": "pci_dss_v4_0", "source_name": "SearXNG PCI DSS", "source_type": "searxng", "search_query": "PCI DSS v4.0 update supplement bulletin", "priority": 1},
                {"framework_type": "soc_2", "source_name": "SearXNG SOC 2", "source_type": "searxng", "search_query": "SOC 2 Trust Services Criteria update AICPA", "priority": 1},
                {"framework_type": "cobit_2019", "source_name": "SearXNG COBIT", "source_type": "searxng", "search_query": "COBIT 2019 update ISACA governance", "priority": 1},
                # Regional
                {"framework_type": "australia_energy_aescsf", "source_name": "SearXNG AESCSF", "source_type": "searxng", "search_query": "Australian Energy Sector Cyber Security Framework update", "priority": 1},
            ]

            for src_data in default_sources:
                source = RegulatorySource(id=uuid.uuid4(), enabled=True, **src_data)
                self.db.add(source)

            logger.info(f"Seeded {len(default_sources)} default regulatory sources")

        return {"regulatory_monitor": "seeded"}
