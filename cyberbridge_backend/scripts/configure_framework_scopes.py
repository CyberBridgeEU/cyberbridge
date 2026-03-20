#!/usr/bin/env python3
"""
Script to configure scope requirements for existing frameworks.

This script updates all frameworks in the database with their appropriate
scope configurations (Product, Organization, etc.) based on their compliance nature.

Usage:
    python scripts/configure_framework_scopes.py
"""

import sys
import os

# Add the parent directory to Python path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.seeds.framework_scope_config_seed import FrameworkScopeConfigSeed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run the framework scope configuration"""
    db: Session = SessionLocal()

    try:
        logger.info("=" * 80)
        logger.info("FRAMEWORK SCOPE CONFIGURATION SCRIPT")
        logger.info("=" * 80)
        logger.info("")

        # Run the scope configuration seed
        scope_config_seed = FrameworkScopeConfigSeed(db)
        result = scope_config_seed.seed()

        logger.info("")
        logger.info("=" * 80)
        logger.info("CONFIGURATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total frameworks updated: {result['updated_count']}")
        logger.info(f"Frameworks not found: {len(result['not_found'])}")

        if result['not_found']:
            logger.info("")
            logger.info("The following frameworks were not found in the database:")
            for fw_name in result['not_found']:
                logger.info(f"  - {fw_name}")

        logger.info("")
        logger.info("Configuration details:")
        logger.info("")

        for fw_name, config in result['configurations'].items():
            status = "✓" if fw_name not in result['not_found'] else "✗"
            logger.info(f"{status} {fw_name}:")
            logger.info(f"    Default Scope: {config['default_scope_type']}")
            logger.info(f"    Allowed Scopes: {', '.join(config['allowed_scope_types'])}")
            logger.info(f"    Selection Mode: {config['scope_selection_mode']}")
            logger.info(f"    Reason: {config['reason']}")
            logger.info("")

        logger.info("=" * 80)
        logger.info("SCRIPT COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        return 0

    except Exception as e:
        logger.error("=" * 80)
        logger.error("ERROR OCCURRED")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}", exc_info=True)
        db.rollback()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
