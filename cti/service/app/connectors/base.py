import json
import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from ..models.indicator import CtiIndicator
from ..models.attack_pattern import CtiAttackPattern
from ..models.indicator_attack_pattern import CtiIndicatorAttackPattern

logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    source_name: str

    @abstractmethod
    async def fetch_raw_data(self) -> list[dict]:
        """Pull raw data from the scanner API."""

    @abstractmethod
    def normalize(self, raw_item: dict) -> dict:
        """Transform a raw scanner item into indicator column values."""

    @abstractmethod
    def dedup_key(self, normalized: dict) -> str:
        """Return a string key for deterministic UUID5 generation."""

    def get_mitre_mappings(self, raw_item: dict) -> list[tuple[str, str]]:
        """Return list of (mitre_id, technique_name) for the item. Override in subclasses."""
        return []

    def _make_id(self, key: str) -> uuid.UUID:
        return uuid.uuid5(uuid.NAMESPACE_DNS, key)

    async def run(self, db: Session) -> int:
        """Full pipeline: fetch -> normalize -> upsert. Returns count of upserted rows."""
        try:
            raw_items = await self.fetch_raw_data()
        except Exception as e:
            logger.error("[%s] Failed to fetch data: %s", self.source_name, e)
            return 0

        if not raw_items:
            logger.info("[%s] No data returned", self.source_name)
            return 0

        count = 0
        for raw_item in raw_items:
            try:
                normalized = self.normalize(raw_item)
                if not normalized:
                    continue

                key = self.dedup_key(normalized)
                indicator_id = self._make_id(key)
                # Remove internal fields not in the DB model
                normalized.pop("_raw", None)
                # Serialize labels list to JSON string for Text column
                if isinstance(normalized.get("labels"), list):
                    normalized["labels"] = json.dumps(normalized["labels"])
                normalized["id"] = indicator_id
                normalized["source"] = self.source_name
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
                mitre_mappings = self.get_mitre_mappings(raw_item)
                for mitre_id, technique_name in mitre_mappings:
                    ap_id = self._make_id(f"mitre-{mitre_id}")
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
                        source=self.source_name,
                        created_at=now,
                    )
                    junction_stmt = junction_stmt.on_conflict_do_nothing(
                        index_elements=["indicator_id", "attack_pattern_id"]
                    )
                    db.execute(junction_stmt)

            except Exception as e:
                logger.warning("[%s] Failed to process item: %s", self.source_name, e)
                continue

        db.commit()
        logger.info("[%s] Upserted %d indicators", self.source_name, count)
        return count
