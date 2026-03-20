import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..database import get_db
from ..models.indicator import CtiIndicator
from ..models.attack_pattern import CtiAttackPattern
from ..models.indicator_attack_pattern import CtiIndicatorAttackPattern
from ..connectors.nmap_connector import NmapConnector
from ..connectors.zap_connector import ZapConnector
from ..connectors.semgrep_connector import SemgrepConnector
from ..connectors.osv_connector import OsvConnector

logger = logging.getLogger(__name__)
router = APIRouter()

CONNECTOR_MAP = {
    "nmap": NmapConnector,
    "zap": ZapConnector,
    "semgrep": SemgrepConnector,
    "osv": OsvConnector,
}


@router.post("/api/ingest/{source}")
async def ingest(source: str, payload: list[dict[str, Any]], db: Session = Depends(get_db)):
    """Accept pre-fetched scanner results via push. Backend sends data here after user-triggered scans."""
    if source not in CONNECTOR_MAP:
        return {"error": f"Unknown source: {source}", "ingested": 0}

    connector = CONNECTOR_MAP[source]()
    count = 0

    for raw_item in payload:
        try:
            normalized = connector.normalize(raw_item)
            if not normalized:
                continue

            key = connector.dedup_key(normalized)
            indicator_id = connector._make_id(key)
            # Remove internal fields
            normalized.pop("_raw", None)
            # Serialize labels list to JSON string for Text column
            if isinstance(normalized.get("labels"), list):
                normalized["labels"] = json.dumps(normalized["labels"])
            normalized["id"] = indicator_id
            normalized["source"] = connector.source_name
            now = datetime.now(timezone.utc)
            normalized.setdefault("created_at", now)
            normalized["updated_at"] = now

            stmt = pg_insert(CtiIndicator).values(**normalized)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": stmt.excluded.name,
                    "description": stmt.excluded.description,
                    "confidence": stmt.excluded.confidence,
                    "labels": stmt.excluded.labels,
                    "severity": stmt.excluded.severity,
                    "updated_at": now,
                },
            )
            db.execute(stmt)
            count += 1

            # Handle MITRE mappings
            mitre_mappings = connector.get_mitre_mappings(raw_item)
            for mitre_id, technique_name in mitre_mappings:
                ap_id = connector._make_id(f"mitre-{mitre_id}")
                ap_stmt = pg_insert(CtiAttackPattern).values(
                    id=ap_id,
                    mitre_id=mitre_id,
                    name=technique_name,
                    url=f"https://attack.mitre.org/techniques/{mitre_id.replace('.', '/')}",
                    created_at=now,
                    updated_at=now,
                )
                ap_stmt = ap_stmt.on_conflict_do_nothing(index_elements=["mitre_id"])
                db.execute(ap_stmt)

                junction_stmt = pg_insert(CtiIndicatorAttackPattern).values(
                    indicator_id=indicator_id,
                    attack_pattern_id=ap_id,
                    source=connector.source_name,
                    created_at=now,
                )
                junction_stmt = junction_stmt.on_conflict_do_nothing(
                    index_elements=["indicator_id", "attack_pattern_id"]
                )
                db.execute(junction_stmt)

        except Exception as e:
            logger.warning("[Ingest/%s] Failed to process item: %s", source, e)
            continue

    db.commit()
    logger.info("[Ingest/%s] Ingested %d indicators", source, count)
    return {"ingested": count}
