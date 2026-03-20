# euvd_service.py
import httpx
import json
import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from app.database.database import get_db
from app.repositories import euvd_repository

logger = logging.getLogger(__name__)

EUVD_BASE_URL = "https://euvdservices.enisa.europa.eu"


class EUVDService:
    """Service for fetching and caching vulnerability data from the EU Vulnerability Database."""

    def __init__(self, db: Session):
        self.db = db

    async def fetch_exploited(self) -> List[Dict[str, Any]]:
        """Fetch actively exploited vulnerabilities."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{EUVD_BASE_URL}/api/exploitedvulnerabilities")
            response.raise_for_status()
            return response.json()

    async def fetch_latest(self) -> List[Dict[str, Any]]:
        """Fetch latest vulnerabilities."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{EUVD_BASE_URL}/api/lastvulnerabilities")
            response.raise_for_status()
            return response.json()

    async def fetch_critical(self) -> List[Dict[str, Any]]:
        """Fetch critical vulnerabilities."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{EUVD_BASE_URL}/api/criticalvulnerabilities")
            response.raise_for_status()
            return response.json()

    async def search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Proxy search to EUVD search API."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{EUVD_BASE_URL}/api/search", params=params)
            response.raise_for_status()
            return response.json()

    def parse_item(self, item: Dict[str, Any], category: str) -> Dict[str, Any]:
        """Normalize an EUVD API response item into a DB-ready dict."""
        # Parse dates - EUVD uses formats like "Apr 15, 2025, 8:30:58 PM"
        date_published = None
        date_updated = None
        try:
            if item.get("datePublished"):
                from dateutil import parser as dateutil_parser
                date_published = dateutil_parser.parse(item["datePublished"])
        except Exception:
            pass
        try:
            if item.get("dateUpdated"):
                from dateutil import parser as dateutil_parser
                date_updated = dateutil_parser.parse(item["dateUpdated"])
        except Exception:
            pass

        # Extract products and vendors from nested structures
        products_list = []
        vendors_list = []
        enisa_products = item.get("enisaIdProduct") or []
        if isinstance(enisa_products, list):
            for p in enisa_products:
                if isinstance(p, dict):
                    prod = p.get("product")
                    if isinstance(prod, dict):
                        products_list.append(prod.get("name", ""))
                    elif isinstance(prod, str):
                        products_list.append(prod)
                    vendor = p.get("vendor")
                    if isinstance(vendor, dict):
                        vendors_list.append(vendor.get("name", ""))
                    elif isinstance(vendor, str):
                        vendors_list.append(vendor)
                elif isinstance(p, str):
                    products_list.append(p)

        # Also check direct vendor field
        enisa_vendors = item.get("enisaIdVendor") or []
        if isinstance(enisa_vendors, list):
            for v in enisa_vendors:
                if isinstance(v, dict):
                    vendor = v.get("vendor")
                    if isinstance(vendor, dict):
                        vendors_list.append(vendor.get("name", ""))
                    elif isinstance(vendor, str):
                        vendors_list.append(vendor)
                elif isinstance(v, str):
                    vendors_list.append(v)

        # Extract aliases (CVE IDs) - API returns newline-separated string or list
        aliases = item.get("aliases") or ""
        if isinstance(aliases, list):
            aliases_str = "\n".join(str(a) for a in aliases)
        else:
            aliases_str = str(aliases).strip() if aliases else None

        # Extract references - API returns newline-separated string or list
        refs = item.get("references") or ""
        if isinstance(refs, list):
            refs_str = "\n".join(str(r) for r in refs)
        else:
            refs_str = str(refs).strip() if refs else None

        return {
            "euvd_id": item.get("id") or item.get("euvdId") or "",
            "description": item.get("description"),
            "date_published": date_published,
            "date_updated": date_updated,
            "base_score": item.get("baseScore"),
            "base_score_version": item.get("baseScoreVersion"),
            "base_score_vector": item.get("baseScoreVector"),
            "epss": item.get("epss"),
            "assigner": item.get("assigner"),
            "references": refs_str,
            "aliases": aliases_str,
            "products": json.dumps(products_list) if products_list else None,
            "vendors": json.dumps(list(set(vendors_list))) if vendors_list else None,
            "is_exploited": category == "exploited",
            "is_critical": category == "critical",
            "category": category,
        }

    async def sync_all(self, sync_id) -> Dict[str, int]:
        """Fetch all 3 endpoints concurrently and upsert into DB."""
        stats = {"processed": 0, "added": 0, "updated": 0}

        try:
            euvd_repository.update_sync_status(self.db, sync_id, "in_progress")

            # Fetch all 3 endpoints concurrently
            exploited_data, latest_data, critical_data = await asyncio.gather(
                self.fetch_exploited(),
                self.fetch_latest(),
                self.fetch_critical(),
                return_exceptions=True
            )

            # Process exploited
            if isinstance(exploited_data, list):
                for item in exploited_data:
                    try:
                        data = self.parse_item(item, "exploited")
                        if data["euvd_id"]:
                            _, is_new = euvd_repository.upsert_vulnerability(self.db, data)
                            stats["added" if is_new else "updated"] += 1
                            stats["processed"] += 1
                    except Exception as e:
                        logger.error(f"Error processing exploited vuln: {e}")
            elif isinstance(exploited_data, Exception):
                logger.error(f"Failed to fetch exploited: {exploited_data}")

            # Process critical
            if isinstance(critical_data, list):
                for item in critical_data:
                    try:
                        data = self.parse_item(item, "critical")
                        if data["euvd_id"]:
                            _, is_new = euvd_repository.upsert_vulnerability(self.db, data)
                            stats["added" if is_new else "updated"] += 1
                            stats["processed"] += 1
                    except Exception as e:
                        logger.error(f"Error processing critical vuln: {e}")
            elif isinstance(critical_data, Exception):
                logger.error(f"Failed to fetch critical: {critical_data}")

            # Process latest
            if isinstance(latest_data, list):
                for item in latest_data:
                    try:
                        data = self.parse_item(item, "latest")
                        if data["euvd_id"]:
                            _, is_new = euvd_repository.upsert_vulnerability(self.db, data)
                            stats["added" if is_new else "updated"] += 1
                            stats["processed"] += 1
                    except Exception as e:
                        logger.error(f"Error processing latest vuln: {e}")
            elif isinstance(latest_data, Exception):
                logger.error(f"Failed to fetch latest: {latest_data}")

            # Mark sync as completed
            euvd_repository.update_sync_status(
                self.db, sync_id, "completed",
                stats["processed"], stats["added"], stats["updated"]
            )
            logger.info(f"EUVD sync completed: {stats}")

        except Exception as e:
            logger.error(f"EUVD sync failed: {e}")
            euvd_repository.update_sync_status(
                self.db, sync_id, "failed",
                stats["processed"], stats["added"], stats["updated"],
                str(e)
            )
            raise

        return stats


# Scheduled job entry point
async def run_euvd_sync():
    """Entry point for scheduled EUVD sync job."""
    logger.info("Starting scheduled EUVD sync")

    db = next(get_db())
    try:
        # Check if another sync is already running
        if euvd_repository.is_sync_in_progress(db):
            logger.info("Another EUVD sync is already in progress")
            return

        # Create sync status
        sync_status = euvd_repository.create_sync_status(db)

        # Run sync
        service = EUVDService(db)
        await service.sync_all(sync_status.id)

        logger.info("Scheduled EUVD sync completed")

    except Exception as e:
        logger.error(f"Scheduled EUVD sync failed: {e}")
    finally:
        db.close()
