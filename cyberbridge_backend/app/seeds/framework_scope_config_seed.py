# app/seeds/framework_scope_config_seed.py
import logging
import json
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class FrameworkScopeConfigSeed(BaseSeed):
    """Configure scope requirements for existing frameworks"""

    def __init__(self, db):
        super().__init__(db)

    def seed(self) -> dict:
        logger.info("Configuring framework scope requirements...")

        # Define scope configurations for each framework
        # Format: {
        #   "framework_name": {
        #     "allowed_scope_types": ["Product", "Organization", ...],
        #     "scope_selection_mode": "required" | "optional"
        #   }
        # }
        framework_configs = {
            "CRA": {
                "allowed_scope_types": ["Product"],
                "scope_selection_mode": "required",
                "reason": "CRA is product-centric - assessments must be tied to a specific product"
            },
            "ISO 27001": {
                "allowed_scope_types": ["Organization", "Other"],
                "scope_selection_mode": "optional",
                "reason": "ISO 27001 is organization-wide but can be scoped to departments/units"
            },
            "GDPR": {
                "allowed_scope_types": ["Organization", "Other"],
                "scope_selection_mode": "required",
                "reason": "GDPR applies to organizations and their data processing activities"
            },
            "PCI DSS v4.0": {
                "allowed_scope_types": ["Organization", "Asset", "Other"],
                "scope_selection_mode": "optional",
                "reason": "PCI DSS can apply to the entire org or specific payment processing systems"
            },
            "SOC 2": {
                "allowed_scope_types": ["Organization", "Product", "Other"],
                "scope_selection_mode": "optional",
                "reason": "SOC 2 typically covers an organization or specific products/services"
            },
            "HIPAA Privacy Rule": {
                "allowed_scope_types": ["Organization", "Other"],
                "scope_selection_mode": "required",
                "reason": "HIPAA applies to covered entities and their business associates"
            },
            "NIS2 Directive": {
                "allowed_scope_types": ["Organization", "Other"],
                "scope_selection_mode": "required",
                "reason": "NIS2 applies to organizations providing essential services"
            },
            "NIST CSF 2.0": {
                "allowed_scope_types": ["Organization", "Asset", "Product", "Other"],
                "scope_selection_mode": "optional",
                "reason": "NIST CSF is flexible and can be applied at various organizational levels"
            },
            "CMMC 2.0": {
                "allowed_scope_types": ["Organization", "Other"],
                "scope_selection_mode": "required",
                "reason": "CMMC applies to organizations in the defense industrial base"
            },
            "CCPA": {
                "allowed_scope_types": ["Organization", "Other"],
                "scope_selection_mode": "required",
                "reason": "CCPA applies to businesses meeting certain thresholds"
            },
            "DORA 2022": {
                "allowed_scope_types": ["Organization", "Asset", "Other"],
                "scope_selection_mode": "required",
                "reason": "DORA applies to financial entities and their ICT systems for operational resilience"
            }
        }

        updated_count = 0
        not_found = []

        for framework_name, config in framework_configs.items():
            # Find framework by name (case-insensitive)
            framework = self.db.query(models.Framework).filter(
                models.Framework.name.ilike(framework_name)
            ).first()

            if framework:
                # Update scope configuration
                framework.allowed_scope_types = json.dumps(config["allowed_scope_types"])
                framework.scope_selection_mode = config["scope_selection_mode"]

                self.db.commit()
                updated_count += 1
                logger.info(
                    f"✓ Configured {framework_name}: "
                    f"allowed_types={config['allowed_scope_types']}, "
                    f"mode={config['scope_selection_mode']}"
                )
            else:
                not_found.append(framework_name)
                logger.warning(f"✗ Framework '{framework_name}' not found in database")

        logger.info(
            f"Scope configuration complete: "
            f"{updated_count} frameworks updated, "
            f"{len(not_found)} not found"
        )

        if not_found:
            logger.info(f"Frameworks not found: {', '.join(not_found)}")

        return {
            "updated_count": updated_count,
            "not_found": not_found,
            "configurations": framework_configs
        }


    def rollback(self):
        """Reset all framework scope configurations to default (optional mode)"""
        logger.info("Rolling back framework scope configurations...")

        frameworks = self.db.query(models.Framework).all()

        for framework in frameworks:
            framework.allowed_scope_types = None
            framework.scope_selection_mode = "optional"

        self.db.commit()
        logger.info(f"Reset {len(frameworks)} frameworks to optional scope mode")
