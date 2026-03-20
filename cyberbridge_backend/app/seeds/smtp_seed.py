# app/seeds/smtp_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models
from app.repositories import smtp_repository

logger = logging.getLogger(__name__)


class SmtpSeed(BaseSeed):
    """Seed default SMTP configurations"""

    def seed(self) -> dict:
        logger.info("Creating default SMTP configurations...")

        existing_configs = smtp_repository.get_all_smtp_configs(self.db)
        existing_servers = {c.smtp_server for c in existing_configs}
        results = {}

        # 1. Gmail (Dev) - active by default
        if "smtp.gmail.com" not in existing_servers:
            gmail_data = {
                "label": "Gmail (Dev)",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": None,
                "username": "miaritisnestor@gmail.com",
                "password": "gyve dotr eyap nzdj",
                "use_tls": True,
                "is_active": True
            }
            results["smtp_gmail"] = smtp_repository.create_smtp_config(self.db, gmail_data)
            logger.info("Created Gmail (Dev) SMTP configuration")
        else:
            logger.info("Gmail SMTP configuration already exists, skipping")

        # 2. Clone Systems (Prod) - inactive by default
        if "mail.clone-systems.com" not in existing_servers:
            clone_data = {
                "label": "Clone Systems (Prod)",
                "smtp_server": "mail.clone-systems.com",
                "smtp_port": 25,
                "sender_email": "no-reply@clone-systems.com",
                "username": None,
                "password": None,
                "use_tls": False,
                "is_active": False
            }
            results["smtp_clone"] = smtp_repository.create_smtp_config(self.db, clone_data)
            logger.info("Created Clone Systems (Prod) SMTP configuration")
        else:
            logger.info("Clone Systems SMTP configuration already exists, skipping")

        return results
