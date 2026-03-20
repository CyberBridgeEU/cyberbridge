import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..models.kev_entry import CtiKevEntry
from ..models.threat_feed import CtiThreatFeed

logger = logging.getLogger(__name__)

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


async def sync_cisa_kev(db: Session) -> int:
    """Download CISA KEV feed and upsert entries."""
    logger.info("[KEV] Starting CISA KEV sync...")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(KEV_URL)
            resp.raise_for_status()
            data = resp.json()

        vulnerabilities = data.get("vulnerabilities", [])
        count = 0
        now = datetime.now(timezone.utc)

        for vuln in vulnerabilities:
            cve_id = vuln.get("cveID", "")
            if not cve_id:
                continue

            date_added = None
            if vuln.get("dateAdded"):
                try:
                    date_added = datetime.strptime(vuln["dateAdded"], "%Y-%m-%d")
                except ValueError:
                    pass

            due_date = None
            if vuln.get("dueDate"):
                try:
                    due_date = datetime.strptime(vuln["dueDate"], "%Y-%m-%d")
                except ValueError:
                    pass

            stmt = pg_insert(CtiKevEntry).values(
                cve_id=cve_id,
                vendor=vuln.get("vendorProject", ""),
                product=vuln.get("product", ""),
                vulnerability_name=vuln.get("vulnerabilityName", ""),
                date_added=date_added,
                due_date=due_date,
                known_ransomware=vuln.get("knownRansomwareCampaignUse", "").lower() == "known",
                notes=vuln.get("notes", ""),
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["cve_id"],
                set_={
                    "vendor": stmt.excluded.vendor,
                    "product": stmt.excluded.product,
                    "vulnerability_name": stmt.excluded.vulnerability_name,
                    "due_date": stmt.excluded.due_date,
                    "known_ransomware": stmt.excluded.known_ransomware,
                    "notes": stmt.excluded.notes,
                },
            )
            db.execute(stmt)
            count += 1

        feed_stmt = pg_insert(CtiThreatFeed).values(
            feed_name="cisa_kev",
            last_sync_at=now,
            last_sync_status="success",
            record_count=count,
        )
        feed_stmt = feed_stmt.on_conflict_do_update(
            index_elements=["feed_name"],
            set_={
                "last_sync_at": now,
                "last_sync_status": "success",
                "record_count": count,
            },
        )
        db.execute(feed_stmt)
        db.commit()

        logger.info("[KEV] Synced %d KEV entries", count)
        return count

    except Exception as e:
        logger.error("[KEV] Sync failed: %s", e)
        now = datetime.now(timezone.utc)
        try:
            feed_stmt = pg_insert(CtiThreatFeed).values(
                feed_name="cisa_kev",
                last_sync_at=now,
                last_sync_status="error",
                record_count=0,
            )
            feed_stmt = feed_stmt.on_conflict_do_update(
                index_elements=["feed_name"],
                set_={"last_sync_at": now, "last_sync_status": "error"},
            )
            db.execute(feed_stmt)
            db.commit()
        except Exception:
            pass
        return 0
