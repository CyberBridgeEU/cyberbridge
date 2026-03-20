import uuid
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..models.attack_pattern import CtiAttackPattern
from ..models.threat_feed import CtiThreatFeed

logger = logging.getLogger(__name__)

MITRE_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"


async def sync_mitre_attack(db: Session) -> int:
    """Download MITRE ATT&CK enterprise JSON and upsert attack patterns."""
    logger.info("[MITRE] Starting ATT&CK sync...")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(MITRE_URL)
            resp.raise_for_status()
            data = resp.json()

        objects = data.get("objects", [])
        count = 0
        now = datetime.now(timezone.utc)

        for obj in objects:
            if obj.get("type") != "attack-pattern":
                continue
            if obj.get("revoked") or obj.get("x_mitre_deprecated"):
                continue

            mitre_id = None
            url = None
            for ref in obj.get("external_references", []):
                if ref.get("source_name") == "mitre-attack":
                    mitre_id = ref.get("external_id")
                    url = ref.get("url")
                    break

            if not mitre_id:
                continue

            # Extract tactic from kill_chain_phases
            tactic = None
            phases = obj.get("kill_chain_phases", [])
            if phases:
                tactic = phases[0].get("phase_name", "").replace("-", " ").title()

            ap_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"mitre-{mitre_id}")

            stmt = pg_insert(CtiAttackPattern).values(
                id=ap_id,
                mitre_id=mitre_id,
                name=obj.get("name", ""),
                tactic=tactic,
                description=(obj.get("description", "") or "")[:2000],
                url=url,
                created_at=now,
                updated_at=now,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["mitre_id"],
                set_={
                    "name": stmt.excluded.name,
                    "tactic": stmt.excluded.tactic,
                    "description": stmt.excluded.description,
                    "url": stmt.excluded.url,
                    "updated_at": now,
                },
            )
            db.execute(stmt)
            count += 1

        # Update sync state
        feed_stmt = pg_insert(CtiThreatFeed).values(
            feed_name="mitre_attack",
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

        logger.info("[MITRE] Synced %d attack patterns", count)
        return count

    except Exception as e:
        logger.error("[MITRE] Sync failed: %s", e)
        now = datetime.now(timezone.utc)
        try:
            feed_stmt = pg_insert(CtiThreatFeed).values(
                feed_name="mitre_attack",
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
