# app/seeds/template_catalog_seed.py
import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path

from .base_seed import BaseSeed
from app.models import models
from app.constants.control_templates import get_control_set_templates
from app.constants import risk_templates

logger = logging.getLogger(__name__)


class TemplateCatalogSeed(BaseSeed):
    """Seed template catalogs (frameworks, policies, controls, risks) into the database."""

    # Maps normalized policy filename (stem, uppercased, underscores→spaces) → (POL code, clean title).
    # POL-1 to POL-35 come from the reference mapping; POL-36 to POL-48 are seed-only files.
    POLICY_CODE_MAP = {
        "PASSWORD POLICY":                                      ("POL-1",  "Password Policy"),
        "ACCEPTABLE USE POLICY":                                ("POL-2",  "Acceptable Use Policy"),
        "ACCESS MANAGEMENT POLICY":                             ("POL-4",  "Access Management Policy"),
        "ANTIVIRUS POLICY":                                     ("POL-5",  "Antivirus Policy"),
        "APPLICATION SECURITY POLICY":                          ("POL-6",  "Application Security Policy"),
        "ASSET MANAGEMENT POLICY":                              ("POL-7",  "Asset Management Policy"),
        "AVAILABILITY POLICY":                                  ("POL-8",  "Availability Policy"),
        "BACKUP POLICY":                                        ("POL-9",  "Backup Policy"),
        "BUSINESS CONTINUITY POLICY":                           ("POL-10", "Business Continuity Policy"),
        "CHANGE MANAGEMENT POLICY":                             ("POL-11", "Change Management Policy"),
        "CLEAN DESK POLICY":                                    ("POL-12", "Clean Desk Policy"),
        "CODE OF CONDUCT POLICY":                               ("POL-13", "Code Of Conduct Policy"),
        "CONFIDENTIALITY POLICY":                               ("POL-14", "Confidentiality Policy"),
        "CONFIGURATION MANAGEMENT POLICY":                      ("POL-15", "Configuration Management Policy"),
        "DATA CLASSIFICATION POLICY":                           ("POL-16", "Data Classification Policy"),
        "DATA RETENTION POLICY":                                ("POL-17", "Data Retention Policy"),
        "DISASTER RECOVERY POLICY":                             ("POL-18", "Disaster Recovery Policy"),
        "ENCRYPTION POLICY":                                    ("POL-19", "Encryption Policy"),
        "INCIDENT MANAGEMENT POLICY":                           ("POL-20", "Incident Management Policy"),
        "INFORMATION SECURITY POLICY":                          ("POL-21", "Information Security Policy"),
        "LOGGING AND MONITORING POLICY":                        ("POL-22", "Logging And Monitoring Policy"),
        "MOBILE DEVICE POLICY":                                 ("POL-23", "Mobile Device Policy"),
        "NETWORK MANAGEMENT POLICY":                            ("POL-24", "Network Management Policy"),
        "PATCH MANAGEMENT POLICY":                              ("POL-26", "Patch Management Policy"),
        "PERSONNEL SECURITY POLICY":                            ("POL-27", "Personnel Security Policy"),
        "PHYSICAL SECURITY POLICY":                             ("POL-28", "Physical Security Policy"),
        "REMOTE ACCESS POLICY":                                 ("POL-29", "Remote Access Policy"),
        "RISK MANAGEMENT POLICY":                               ("POL-30", "Risk Management Policy"),
        "SANCTIONS POLICY":                                     ("POL-31", "Sanctions Policy"),
        "SOCIAL MEDIA POLICY":                                  ("POL-32", "Social Media Policy"),
        "SOFTWARE DEVELOPMENT LIFECYCLE POLICY V1.0":           ("POL-33", "Software Development Lifecycle Policy"),
        "VENDOR MANAGEMENT POLICY":                             ("POL-34", "Vendor Management Policy"),
        "VULNERABILITY MANAGEMENT POLICY":                      ("POL-35", "Vulnerability Management Policy"),
        # Seed-only policies (procedures, strategies, standards)
        "BUSINESS CONTINUITY AND DISASTER RECOVERY PROCEDURES": ("POL-36", "Business Continuity And Disaster Recovery Procedures"),
        "CONTACT PROCEDURE WITH LOCAL AUTHORITIES":             ("POL-37", "Contact Procedure With Local Authorities"),
        "CORRECTIVE ACTION PROCEDURES":                         ("POL-38", "Corrective Action Procedures"),
        "DATA BACKUP PROCEDURES":                               ("POL-39", "Data Backup Procedures"),
        "DIGITAL OPERATIONAL RESILIENCE STRATEGY V1":           ("POL-40", "Digital Operational Resilience Strategy"),
        "DIGITAL OPERATIONAL RESILIENCE TESTING PROGRAM V1":    ("POL-41", "Digital Operational Resilience Testing Program"),
        "EMPLOYEE ONBOARDING PROCEDURES":                       ("POL-42", "Employee Onboarding Procedures"),
        "ICT 3RD PARTY SECURITY STANDARDS V1":                  ("POL-43", "ICT 3rd Party Security Standards"),
        "INTERNAL AUDIT PROCEDURE":                             ("POL-44", "Internal Audit Procedure"),
        "MANAGEMENT REVIEW PROCEDURE":                          ("POL-45", "Management Review Procedure"),
        "MULTI VENDOR STRATEGY V1.0":                           ("POL-46", "Multi Vendor Strategy"),
        "PATCH MANAGEMENT PROCEDURE":                           ("POL-47", "Patch Management Procedure"),
        "PROCEDURE FOR CONTROL OF DOCUMENTED INFORMATION":      ("POL-48", "Procedure For Control Of Documented Information"),
        # CRA-specific policies, procedures, and documents (POL-49 to POL-91)
        "CRA STRATEGY POLICY AND SCOPE":                        ("POL-49", "CRA Strategy Policy And Scope"),
        "PRODUCT REGISTRY FORM":                                ("POL-50", "Product Registry Form"),
        "PRODUCT CYBERSECURITY POLICY":                         ("POL-51", "Product Cybersecurity Policy"),
        "ORGANIZATIONAL ROLES RESPONSIBILITIES AND AUTHORITIES": ("POL-52", "Organizational Roles Responsibilities And Authorities"),
        "PRODUCT LIFECYCLE MANAGEMENT POLICY":                  ("POL-53", "Product Lifecycle Management Policy"),
        "EXTERNAL COMMUNICATIONS POLICY":                       ("POL-54", "External Communications Policy"),
        "INFORMATION SECURITY OBJECTIVES AND PLAN":             ("POL-55", "Information Security Objectives And Plan"),
        "INFORMATION SECURITY COMMUNICATION PLAN":              ("POL-56", "Information Security Communication Plan"),
        "PERFORMANCE MEASUREMENT POLICY":                       ("POL-57", "Performance Measurement Policy"),
        "RISK ASSESSMENT METHODOLOGY":                          ("POL-58", "Risk Assessment Methodology"),
        "AWARENESS POLICY":                                     ("POL-59", "Awareness Policy"),
        "THIRD-PARTY DATA PROCESSING POLICY":                   ("POL-60", "Third-Party Data Processing Policy"),
        "SYSTEM HARDENING STANDARDS":                           ("POL-61", "System Hardening Standards"),
        "THREAT INTELLIGENCE AND MONITORING PROCEDURE":         ("POL-62", "Threat Intelligence And Monitoring Procedure"),
        "SECURITY COMMUNICATIONS PLAN":                         ("POL-63", "Security Communications Plan"),
        "SECURE SOFTWARE DELIVERY PROCEDURE":                   ("POL-64", "Secure Software Delivery Procedure"),
        "PRODUCT LIFECYCLE AND SUPPORT POLICY":                 ("POL-65", "Product Lifecycle And Support Policy"),
        "SECURITY ADVISORY COMMUNICATION PROCEDURE":            ("POL-66", "Security Advisory Communication Procedure"),
        "VULNERABILITY REPORTING PROCEDURE":                    ("POL-67", "Vulnerability Reporting Procedure"),
        "MANUFACTURER COMMUNICATION PROTOCOL":                  ("POL-68", "Manufacturer Communication Protocol"),
        "RELEASE MANAGEMENT PROCEDURE":                         ("POL-69", "Release Management Procedure"),
        "IMPORTER DUE DILIGENCE PROCEDURE":                     ("POL-70", "Importer Due Diligence Procedure"),
        "PRODUCT COMPLIANCE CHECKLIST":                         ("POL-71", "Product Compliance Checklist"),
        "CONFORMITY ASSESSMENT VERIFICATION PROCEDURE":         ("POL-72", "Conformity Assessment Verification Procedure"),
        "TECHNICAL DOCUMENTATION REVIEW CHECKLIST":             ("POL-73", "Technical Documentation Review Checklist"),
        "CE MARKING VERIFICATION PROCEDURE":                    ("POL-74", "CE Marking Verification Procedure"),
        "PRODUCT DOCUMENTATION CHECKLIST":                      ("POL-75", "Product Documentation Checklist"),
        "IMPORTER IDENTIFICATION PROCEDURE":                    ("POL-76", "Importer Identification Procedure"),
        "PRODUCT LABELLING POLICY":                             ("POL-77", "Product Labelling Policy"),
        "NON-CONFORMITY HANDLING PROCEDURE":                    ("POL-78", "Non-Conformity Handling Procedure"),
        "MARKET SURVEILLANCE COMMUNICATION PLAN":               ("POL-79", "Market Surveillance Communication Plan"),
        "DISTRIBUTOR DUE CARE POLICY":                          ("POL-80", "Distributor Due Care Policy"),
        "PRODUCT HANDLING PROCEDURES":                          ("POL-81", "Product Handling Procedures"),
        "PRE-DISTRIBUTION VERIFICATION CHECKLIST":              ("POL-82", "Pre-Distribution Verification Checklist"),
        "DOCUMENTATION REVIEW PROCEDURE":                       ("POL-83", "Documentation Review Procedure"),
        "PRODUCT QUARANTINE POLICY":                            ("POL-84", "Product Quarantine Policy"),
        "MARKET SURVEILLANCE NOTIFICATION PROCEDURE":           ("POL-85", "Market Surveillance Notification Procedure"),
        "RISK ASSESSMENT POLICY":                               ("POL-86", "Risk Assessment Policy"),
        "RECORD KEEPING POLICY":                                ("POL-87", "Record Keeping Policy"),
        "PRODUCT TRACEABILITY PROCEDURE":                       ("POL-88", "Product Traceability Procedure"),
        "EU DECLARATION OF CONFORMITY TEMPLATE":                ("POL-89", "EU Declaration Of Conformity Template"),
        "CRA COMPLIANCE CHECKLIST":                             ("POL-90", "CRA Compliance Checklist"),
        "MANAGEMENT REVIEW MINUTES":                            ("POL-91", "Management Review Minutes"),
    }

    NON_FRAMEWORK_SEEDS = {
        '__init__.py',
        'base_seed.py',
        'asset_types_seed.py',
        'auditor_roles_seed.py',
        'seed_manager.py',
        'roles_seed.py',
        'organizations_seed.py',
        'users_seed.py',
        'lookup_tables_seed.py',
        'smtp_seed.py',
        'settings_seed.py',
        'scopes_seed.py',
        'framework_scope_config_seed.py'
    }

    def seed(self) -> dict:
        logger.info("Seeding template catalogs...")

        results = {
            "framework_templates": self._seed_framework_templates(),
            "policy_templates": self._seed_policy_templates(),
            "control_templates": self._seed_control_templates(),
            "risk_templates": self._seed_risk_templates()
        }

        logger.info("Template catalog seeding completed.")
        return results

    def _seed_framework_templates(self) -> dict:
        if self.db.query(models.FrameworkTemplate).count() > 0:
            logger.info("Framework templates already seeded; skipping.")
            return {"skipped": True}

        seeds_dir = Path(__file__).resolve().parent.parent / "seeds"
        if not seeds_dir.exists():
            logger.warning("Seeds directory not found; skipping framework templates.")
            return {"skipped": True}

        created = 0
        for filename in os.listdir(seeds_dir):
            if not filename.endswith('_seed.py') or filename in self.NON_FRAMEWORK_SEEDS:
                continue
            template_id = filename.replace('_seed.py', '').upper()
            template_name = template_id
            self.db.add(models.FrameworkTemplate(
                template_id=template_id,
                name=template_name,
                description=f"{template_name} compliance framework",
                seed_filename=filename,
                source="seed_file"
            ))
            created += 1

        logger.info(f"Seeded {created} framework templates.")
        return {"created": created}

    def _seed_policy_templates(self) -> dict:
        policies_dir = Path(__file__).resolve().parent.parent / "policies_files"
        if not policies_dir.exists():
            logger.warning("policies_files directory not found; skipping policy templates.")
            return {"skipped": True}

        existing_count = self.db.query(models.PolicyTemplate).count()

        created = 0
        updated = 0
        for file_path in sorted(policies_dir.glob("*.docx")):
            # Look up policy code and clean title from the map
            normalized_stem = file_path.stem.replace("_", " ").upper().strip()
            mapping = self.POLICY_CODE_MAP.get(normalized_stem)
            policy_code = mapping[0] if mapping else None
            clean_title = mapping[1] if mapping else file_path.stem.replace("_", " ").title()

            # Check if template already exists by filename
            existing = self.db.query(models.PolicyTemplate).filter(
                models.PolicyTemplate.filename == file_path.name
            ).first()

            if existing:
                # Update code and title if missing or changed
                changed = False
                if existing.policy_code != policy_code:
                    existing.policy_code = policy_code
                    changed = True
                if existing.title != clean_title:
                    existing.title = clean_title
                    changed = True
                if changed:
                    updated += 1
            else:
                content = file_path.read_bytes()
                sha256 = hashlib.sha256(content).hexdigest()
                stat = file_path.stat()
                modified_at = datetime.utcfromtimestamp(stat.st_mtime)

                self.db.add(models.PolicyTemplate(
                    filename=file_path.name,
                    title=clean_title,
                    policy_code=policy_code,
                    content_docx=content,
                    content_sha256=sha256,
                    file_size=stat.st_size,
                    file_modified_at=modified_at,
                    source="file"
                ))
                created += 1

        logger.info(f"Policy templates: {created} created, {updated} updated.")
        return {"created": created, "updated": updated}

    def _seed_control_templates(self) -> dict:
        if self.db.query(models.ControlSetTemplate).count() > 0:
            logger.info("Control templates already seeded; skipping.")
            return {"skipped": True}

        templates = get_control_set_templates()
        created_sets = 0
        created_controls = 0

        for template in templates:
            control_set = models.ControlSetTemplate(
                name=template["name"],
                description=template.get("description"),
                source="builtin",
                control_count=len(template.get("controls", []))
            )
            self.db.add(control_set)
            self.db.flush()
            created_sets += 1

            controls = []
            for idx, control in enumerate(template.get("controls", [])):
                controls.append(models.ControlTemplate(
                    control_set_template_id=control_set.id,
                    code=control.get("code"),
                    name=control.get("name"),
                    description=control.get("description"),
                    sort_order=idx
                ))
            if controls:
                self.db.bulk_save_objects(controls)
                created_controls += len(controls)

        logger.info(f"Seeded {created_sets} control set templates and {created_controls} controls.")
        return {"control_sets": created_sets, "controls": created_controls}

    def _seed_risk_templates(self) -> dict:
        created_categories = 0
        updated_categories = 0
        created_risks = 0
        updated_risks = 0

        # Upsert categories
        category_map = {}
        for category in risk_templates.RISK_TEMPLATE_CATEGORIES:
            existing = self.db.query(models.RiskTemplateCategory).filter(
                models.RiskTemplateCategory.category_key == category["id"]
            ).first()

            if existing:
                changed = False
                if existing.name != category["name"]:
                    existing.name = category["name"]
                    changed = True
                if existing.risk_count != category.get("risk_count"):
                    existing.risk_count = category.get("risk_count")
                    changed = True
                if changed:
                    updated_categories += 1
                category_map[category["id"]] = existing.id
            else:
                category_model = models.RiskTemplateCategory(
                    category_key=category["id"],
                    name=category["name"],
                    description=category.get("description"),
                    risk_count=category.get("risk_count")
                )
                self.db.add(category_model)
                self.db.flush()
                category_map[category["id"]] = category_model.id
                created_categories += 1

        # Upsert risk templates — match by risk_category_name to update codes
        seen_names = set()
        for category in risk_templates.RISK_TEMPLATE_CATEGORIES:
            category_id = category_map.get(category["id"])
            if not category_id:
                continue
            for risk in risk_templates.RISK_TEMPLATES.get(category["id"], []):
                risk_code = risk.get("risk_code")
                risk_name = risk.get("risk_category_name")
                if not risk_code or not risk_name or risk_name in seen_names:
                    continue

                # Try to find existing by name (stable identifier)
                existing = self.db.query(models.RiskTemplate).filter(
                    models.RiskTemplate.risk_category_name == risk_name
                ).first()

                if existing:
                    changed = False
                    if existing.risk_code != risk_code:
                        existing.risk_code = risk_code
                        changed = True
                    if existing.category_id != category_id:
                        existing.category_id = category_id
                        changed = True
                    if changed:
                        updated_risks += 1
                else:
                    self.db.add(models.RiskTemplate(
                        category_id=category_id,
                        risk_code=risk_code,
                        risk_category_name=risk_name,
                        risk_category_description=risk.get("risk_category_description"),
                        risk_potential_impact=risk.get("risk_potential_impact"),
                        risk_control=risk.get("risk_control")
                    ))
                    created_risks += 1

                seen_names.add(risk_name)

        logger.info(f"Risk templates: {created_categories} categories created, {updated_categories} updated; "
                     f"{created_risks} risks created, {updated_risks} updated.")
        return {"categories_created": created_categories, "categories_updated": updated_categories,
                "risks_created": created_risks, "risks_updated": updated_risks}
