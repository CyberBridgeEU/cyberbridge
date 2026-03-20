# app/seeds/users_seed.py
import os
import logging
from pathlib import Path
from pydantic import EmailStr, ValidationError
from dotenv import load_dotenv

from .base_seed import BaseSeed
from app.models import models
from app.dtos import schemas
from app.repositories import user_repository

logger = logging.getLogger(__name__)


class UsersSeed(BaseSeed):
    """Seed initial users"""

    def __init__(self, db, role_instances, organization_instances):
        super().__init__(db)
        self.role_instances = role_instances
        self.organization_instances = organization_instances
        self._load_env_variables()

    def _load_env_variables(self):
        """Load environment variables"""
        # Get the directory of the current file
        current_dir = Path(__file__).parent.parent
        env_path = current_dir / ".env"
        load_dotenv(dotenv_path=env_path)

        # Get admin credentials from environment
        email_str = os.getenv("ADMIN_EMAIL", "superadmin@clone-systems.com")
        self.super_admin_password = os.getenv("ADMIN_PASSWORD", "clone")

        # Convert string to EmailStr - let Pydantic handle validation
        from pydantic import BaseModel
        class EmailValidator(BaseModel):
            email: EmailStr

        try:
            validated = EmailValidator(email=email_str)
            self.super_admin_email = validated.email
            logger.info(f"Email validation successful: {self.super_admin_email}")
        except ValidationError as e:
            logger.error(f"Invalid email format: {email_str}, Error: {e}")
            raise ValueError(f"Invalid email format in environment variable: {email_str}")

        # Check if admin password is set
        if not self.super_admin_password:
            logger.warning(
                "ADMIN_PASSWORD environment variable is not set. "
                "Using DEFAULT password. Consider setting a secure password in production."
            )

    def seed(self) -> dict:
        logger.info("Creating initial users...")

        # Check if super admin already exists
        db_user = user_repository.get_user_by_email(
            self.db,
            email="superadmin@clone-systems.com"
        )

        if not db_user:
            try:
                super_admin = schemas.UserCreate(
                    name="Super Admin",
                    email=self.super_admin_email,
                    password=self.super_admin_password,
                    role_id=str(self.role_instances["super_admin"].id),
                    organisation_id=str(self.organization_instances["clone_systems"].id),
                    status="active"
                )
                db_user = user_repository.create_user(self.db, user=super_admin)
                # Force superadmin to change password on first login
                db_user.must_change_password = True
                self.db.commit()
                self.db.refresh(db_user)
                logger.info(f"Super Admin user created with email: {self.super_admin_email}")
            except ValidationError as e:
                logger.error(f"Validation error creating user: {e}")
                raise
            except Exception as e:
                logger.error(f"Error creating user: {e}")
                raise
        else:
            logger.info("Super Admin user already exists, skipping creation")

        return {"users": {"super_admin": db_user}}