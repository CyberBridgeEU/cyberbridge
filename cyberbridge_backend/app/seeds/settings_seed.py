# app/seeds/settings_seed.py
import os
import logging
import json
from .base_seed import BaseSeed
from app.models import models
from app.repositories import sso_repository

logger = logging.getLogger(__name__)


class SettingsSeed(BaseSeed):
    """Seed default LLM and Scanner settings"""

    def seed(self) -> dict:
        logger.info("Creating default LLM and Scanner settings...")

        # Check if LLM settings already exist
        existing_llm = self.db.query(models.LLMSettings).first()

        if not existing_llm:
            # Create default LLM settings
            llm_settings = models.LLMSettings(
                custom_llm_url=None,
                custom_llm_payload=None,
                max_questions_per_framework=10,
                llm_timeout_seconds=300,
                min_confidence_threshold=75,
                max_correlations=10,
                default_provider='llamacpp',
                llm_provider='llamacpp'
            )
            self.db.add(llm_settings)
            self.db.commit()
            logger.info("Created default LLM settings")
        else:
            # Ensure default provider is llamacpp
            if existing_llm.default_provider != 'llamacpp':
                existing_llm.default_provider = 'llamacpp'
                self.db.commit()
                logger.info("Updated default LLM provider to llamacpp")
            else:
                logger.info("LLM settings already exist")
            llm_settings = existing_llm

        # Check if Scanner settings already exist
        existing_scanner = self.db.query(models.ScannerSettings).first()

        if not existing_scanner:
            # Create default Scanner settings with empty allowed domains
            scanner_settings = models.ScannerSettings(
                scanners_enabled=True,
                allowed_scanner_domains=json.dumps([])  # Empty array as JSON string
            )
            self.db.add(scanner_settings)
            self.db.commit()
            logger.info("Created default Scanner settings")
        else:
            logger.info("Scanner settings already exist")
            scanner_settings = existing_scanner

        # Seed default SSO config (by label to avoid duplicates)
        default_label = "Clone Systems (Default)"
        existing_sso = self.db.query(models.SSOSettings).filter(
            models.SSOSettings.label == default_label
        ).first()

        if not existing_sso:
            # Read SSO credentials from environment variables
            google_client_id = os.getenv("SSO_GOOGLE_CLIENT_ID", "")
            google_client_secret = os.getenv("SSO_GOOGLE_CLIENT_SECRET", "")
            microsoft_client_id = os.getenv("SSO_MICROSOFT_CLIENT_ID", "")
            microsoft_client_secret = os.getenv("SSO_MICROSOFT_CLIENT_SECRET", "")
            microsoft_tenant_id = os.getenv("SSO_MICROSOFT_TENANT_ID", "common")

            # Treat placeholder values as empty
            placeholders = {"your-google-client-id", "your-google-client-secret",
                            "your-microsoft-client-id", "your-microsoft-client-secret"}

            google_id = google_client_id if google_client_id not in placeholders else None
            google_secret = google_client_secret if google_client_secret not in placeholders else None
            ms_id = microsoft_client_id if microsoft_client_id not in placeholders else None
            ms_secret = microsoft_client_secret if microsoft_client_secret not in placeholders else None

            # Auto-activate if at least one provider has valid credentials
            google_configured = bool(google_id and google_secret)
            microsoft_configured = bool(ms_id and ms_secret)
            is_active = google_configured or microsoft_configured

            sso_config_data = {
                "label": default_label,
                "is_active": is_active,
                "google_client_id": google_id,
                "google_client_secret": google_secret,
                "microsoft_client_id": ms_id,
                "microsoft_client_secret": ms_secret,
                "microsoft_tenant_id": microsoft_tenant_id,
            }
            sso_settings = sso_repository.create_sso_config(self.db, sso_config_data)

            if is_active:
                providers = []
                if google_configured:
                    providers.append("Google")
                if microsoft_configured:
                    providers.append("Microsoft")
                logger.info(f"Created SSO config '{default_label}' with providers: {', '.join(providers)}")
            else:
                logger.info(f"Created SSO config '{default_label}' (no valid credentials in env)")
        else:
            logger.info(f"SSO config '{default_label}' already exists")
            sso_settings = existing_sso

        return {
            "llm_settings": llm_settings,
            "scanner_settings": scanner_settings,
            "sso_settings": sso_settings
        }
