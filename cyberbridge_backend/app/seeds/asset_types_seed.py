# app/seeds/asset_types_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class AssetTypesSeed(BaseSeed):
    """Seed default asset types for organizations"""

    # Default asset types with icons
    DEFAULT_ASSET_TYPES = [
        {"name": "Cloud Infrastructure", "icon_name": "CloudOutlined", "description": "Cloud-based infrastructure including AWS, Azure, GCP resources"},
        {"name": "Customer Data", "icon_name": "UserOutlined", "description": "Customer personal and business data"},
        {"name": "Data Storage", "icon_name": "DatabaseOutlined", "description": "Data storage systems and repositories"},
        {"name": "Database", "icon_name": "TableOutlined", "description": "Database servers and instances"},
        {"name": "Email", "icon_name": "MailOutlined", "description": "Email systems and communication platforms"},
        {"name": "Employees", "icon_name": "TeamOutlined", "description": "Employee-related assets and workstations"},
        {"name": "Laptops", "icon_name": "LaptopOutlined", "description": "Laptop computers and portable workstations"},
        {"name": "Mobiles & Cellphones", "icon_name": "MobileOutlined", "description": "Mobile devices and smartphones"},
        {"name": "Network", "icon_name": "GlobalOutlined", "description": "Network infrastructure and connectivity"},
        {"name": "Operating Systems", "icon_name": "DesktopOutlined", "description": "Operating system installations and licenses"},
        {"name": "Physical File Drawers", "icon_name": "FolderOutlined", "description": "Physical document storage and filing systems"},
        {"name": "Physical Facilities", "icon_name": "BankOutlined", "description": "Buildings, data centers, and physical locations"},
        {"name": "Process Management", "icon_name": "SettingOutlined", "description": "Business process management systems"},
        {"name": "SAAS Product / Application", "icon_name": "CloudServerOutlined", "description": "Software as a Service applications"},
        {"name": "Servers", "icon_name": "HddOutlined", "description": "Physical and virtual server infrastructure"},
        {"name": "Source Code", "icon_name": "CodeOutlined", "description": "Application source code and intellectual property"},
        {"name": "Source Code Repository", "icon_name": "GithubOutlined", "description": "Code repositories and version control systems"},
        {"name": "Third Party SaaS / Hosted", "icon_name": "CloudUploadOutlined", "description": "Third-party hosted services and SaaS platforms"},
        {"name": "Uncategorized", "icon_name": "QuestionCircleOutlined", "description": "Assets that do not fit other categories"},
        {"name": "Website", "icon_name": "GlobalOutlined", "description": "Web applications and public-facing sites"},
        {"name": "WiFi Network", "icon_name": "WifiOutlined", "description": "Wireless network infrastructure"},
    ]

    def __init__(self, db, organizations: dict):
        super().__init__(db)
        self.organizations = organizations

    def seed(self) -> dict:
        """Seed default asset types for each organization"""
        logger.info("Creating default asset types for organizations...")

        created_asset_types = {}

        for org_name, org in self.organizations.items():
            org_asset_types = {}

            for asset_type_data in self.DEFAULT_ASSET_TYPES:
                # Create filter and create kwargs with organisation_id
                filter_kwargs = {
                    "name": asset_type_data["name"],
                    "organisation_id": org.id
                }
                create_kwargs = {
                    **asset_type_data,
                    "organisation_id": org.id
                }

                asset_type, created = self.get_or_create(
                    models.AssetTypes,
                    filter_kwargs,
                    create_kwargs
                )
                org_asset_types[asset_type_data["name"]] = asset_type

            created_asset_types[org_name] = org_asset_types

        total_count = sum(len(types) for types in created_asset_types.values())
        logger.info(f"Created/verified {total_count} asset types across {len(self.organizations)} organizations")

        return created_asset_types

    @classmethod
    def seed_for_organization(cls, db, organization):
        """
        Seed default asset types for a single organization.
        Can be called when a new organization is created.
        """
        logger.info(f"Creating default asset types for organization: {organization.name}")

        created_asset_types = {}

        for asset_type_data in cls.DEFAULT_ASSET_TYPES:
            # Check if asset type already exists for this org
            existing = db.query(models.AssetTypes).filter(
                models.AssetTypes.name == asset_type_data["name"],
                models.AssetTypes.organisation_id == organization.id
            ).first()

            if existing:
                created_asset_types[asset_type_data["name"]] = existing
                continue

            # Create new asset type
            asset_type = models.AssetTypes(
                name=asset_type_data["name"],
                icon_name=asset_type_data["icon_name"],
                description=asset_type_data["description"],
                organisation_id=organization.id
            )
            db.add(asset_type)
            db.flush()
            created_asset_types[asset_type_data["name"]] = asset_type

        logger.info(f"Created/verified {len(created_asset_types)} asset types for {organization.name}")

        return created_asset_types
