# app/seeds/ce_marking_seed.py
import logging
from .base_seed import BaseSeed
from app.models import models

logger = logging.getLogger(__name__)


class CEMarkingSeed(BaseSeed):
    """Seed CE marking lookup tables"""

    def seed(self) -> dict:
        logger.info("Creating CE marking lookup data...")

        # CE Product Types
        product_types_data = [
            {"name": "Hardware Device", "recommended_placement": "On product label and packaging"},
            {"name": "Small Hardware", "recommended_placement": "On packaging or accompanying documentation"},
            {"name": "Software-Only", "recommended_placement": "In digital interface (About/Settings screen)"},
            {"name": "SaaS", "recommended_placement": "In application footer or legal/compliance page"},
            {"name": "Library-Component", "recommended_placement": "In documentation and package metadata"},
        ]

        product_types = {}
        for pt_data in product_types_data:
            pt, created = self.get_or_create(
                models.CEProductTypes,
                {"name": pt_data["name"]},
                pt_data
            )
            product_types[pt_data["name"]] = pt

        # CE Document Types
        document_types_data = [
            {"name": "EU Declaration of Conformity", "description": "Formal declaration that the product meets all applicable EU requirements", "is_mandatory": True, "sort_order": 1},
            {"name": "Technical File", "description": "Complete technical documentation demonstrating conformity", "is_mandatory": True, "sort_order": 2},
            {"name": "User Manual", "description": "Instructions for safe and proper use of the product", "is_mandatory": True, "sort_order": 3},
            {"name": "Risk Assessment", "description": "Cybersecurity risk assessment documentation", "is_mandatory": True, "sort_order": 4},
            {"name": "Test Reports", "description": "Testing and validation reports for conformity assessment", "is_mandatory": True, "sort_order": 5},
            {"name": "SBOM", "description": "Software Bill of Materials listing all components", "is_mandatory": True, "sort_order": 6},
        ]

        document_types = {}
        for dt_data in document_types_data:
            dt, created = self.get_or_create(
                models.CEDocumentTypes,
                {"name": dt_data["name"]},
                dt_data
            )
            document_types[dt_data["name"]] = dt

        # CE Checklist Template Items
        template_items_data = [
            # Product Classification
            {"category": "Product Classification", "title": "Product category determined (default/important/critical)", "description": "Determine if the product falls under default, important (Class I/II), or critical category per CRA Annexes III/IV", "sort_order": 1, "is_mandatory": True},
            {"category": "Product Classification", "title": "CE product type assigned", "description": "Assign the appropriate CE product type (Hardware Device, Software-Only, SaaS, etc.)", "sort_order": 2, "is_mandatory": True},
            {"category": "Product Classification", "title": "Conformity assessment procedure selected", "description": "Select the appropriate conformity assessment procedure based on product classification", "sort_order": 3, "is_mandatory": True},
            {"category": "Product Classification", "title": "Applicable harmonised standards identified", "description": "Identify relevant harmonised standards that apply to the product", "sort_order": 4, "is_mandatory": True},
            # CE Placement
            {"category": "CE Placement", "title": "CE marking placement location determined", "description": "Determine where the CE mark will be physically or digitally placed", "sort_order": 5, "is_mandatory": True},
            {"category": "CE Placement", "title": "CE marking visibility and legibility verified", "description": "Ensure the CE mark is visible, legible, and indelible as required by EU regulations", "sort_order": 6, "is_mandatory": True},
            {"category": "CE Placement", "title": "CE marking dimensions meet minimum requirements (5mm height)", "description": "Verify the CE mark meets the minimum height of 5mm and maintains correct proportions", "sort_order": 7, "is_mandatory": True},
            # Documentation
            {"category": "Documentation", "title": "EU Declaration of Conformity drafted", "description": "Draft the EU DoC with all required elements per CRA Article 28", "sort_order": 8, "is_mandatory": True},
            {"category": "Documentation", "title": "Technical file compiled", "description": "Compile the complete technical file per CRA Annex VII", "sort_order": 9, "is_mandatory": True},
            {"category": "Documentation", "title": "User instructions prepared", "description": "Prepare user instructions including security information per CRA Annex II", "sort_order": 10, "is_mandatory": True},
            {"category": "Documentation", "title": "Risk assessment completed and documented", "description": "Complete cybersecurity risk assessment and document findings", "sort_order": 11, "is_mandatory": True},
            {"category": "Documentation", "title": "SBOM generated and maintained", "description": "Generate Software Bill of Materials and establish maintenance process", "sort_order": 12, "is_mandatory": True},
            {"category": "Documentation", "title": "Test reports compiled", "description": "Compile all testing and validation reports", "sort_order": 13, "is_mandatory": True},
            # Notified Body
            {"category": "Notified Body", "title": "Notified Body requirement assessed", "description": "Determine if third-party conformity assessment by a Notified Body is required", "sort_order": 14, "is_mandatory": True},
            {"category": "Notified Body", "title": "Notified Body selected (if required)", "description": "Select an appropriate EU Notified Body for conformity assessment", "sort_order": 15, "is_mandatory": False},
            {"category": "Notified Body", "title": "Notified Body certificate obtained (if required)", "description": "Obtain the certificate from the Notified Body confirming conformity", "sort_order": 16, "is_mandatory": False},
            # Traceability
            {"category": "Traceability", "title": "Unique product identification established", "description": "Establish version identifiers, build identifiers, or serial numbers for traceability", "sort_order": 17, "is_mandatory": True},
            {"category": "Traceability", "title": "Manufacturer contact information on product/packaging", "description": "Ensure manufacturer name and contact details are on the product or packaging", "sort_order": 18, "is_mandatory": True},
            {"category": "Traceability", "title": "Economic operator information documented", "description": "Document all economic operators in the supply chain", "sort_order": 19, "is_mandatory": True},
            {"category": "Traceability", "title": "Product variants documented", "description": "Document all product variants covered by the CE marking", "sort_order": 20, "is_mandatory": True},
            # General Conformity
            {"category": "General Conformity", "title": "Essential cybersecurity requirements met (CRA Annex I)", "description": "Verify all essential cybersecurity requirements from CRA Annex I are satisfied", "sort_order": 21, "is_mandatory": True},
            {"category": "General Conformity", "title": "Vulnerability handling process established", "description": "Establish and document the vulnerability handling and disclosure process", "sort_order": 22, "is_mandatory": True},
            {"category": "General Conformity", "title": "Support period defined and communicated", "description": "Define the support period for security updates and communicate to users", "sort_order": 23, "is_mandatory": True},
        ]

        template_items = {}
        for ti_data in template_items_data:
            ti, created = self.get_or_create(
                models.CEChecklistTemplateItems,
                {"category": ti_data["category"], "title": ti_data["title"]},
                ti_data
            )
            template_items[ti_data["title"]] = ti

        return {
            "ce_product_types": product_types,
            "ce_document_types": document_types,
            "ce_template_items": template_items,
        }
