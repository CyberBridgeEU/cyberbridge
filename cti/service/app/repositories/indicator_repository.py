from datetime import datetime, timedelta, timezone
from collections import defaultdict

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from ..models.indicator import CtiIndicator
from ..models.sighting import CtiSighting
from ..models.malware import CtiMalware
from ..models.attack_pattern import CtiAttackPattern
from ..models.indicator_attack_pattern import CtiIndicatorAttackPattern


class IndicatorRepository:

    @staticmethod
    def count_by_source(db: Session, source: str) -> int:
        return db.query(func.count(CtiIndicator.id)).filter(CtiIndicator.source == source).scalar() or 0

    @staticmethod
    def count_sightings_by_source(db: Session, source: str) -> int:
        return db.query(func.count(CtiSighting.id)).filter(CtiSighting.source == source).scalar() or 0

    @staticmethod
    def count_malware(db: Session) -> int:
        return db.query(func.count(CtiMalware.id)).scalar() or 0

    @staticmethod
    def count_attack_patterns(db: Session) -> int:
        return db.query(func.count(CtiAttackPattern.id)).scalar() or 0

    @staticmethod
    def count_all_indicators(db: Session) -> int:
        return db.query(func.count(CtiIndicator.id)).scalar() or 0

    @staticmethod
    def count_all_sightings(db: Session) -> int:
        return db.query(func.count(CtiSighting.id)).scalar() or 0

    @staticmethod
    def get_recent_indicators(db: Session, limit: int = 100) -> list:
        return (
            db.query(CtiIndicator)
            .order_by(CtiIndicator.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_indicators_by_source(db: Session, source: str) -> list:
        return (
            db.query(CtiIndicator)
            .filter(CtiIndicator.source == source)
            .order_by(CtiIndicator.created_at.desc())
            .all()
        )

    @staticmethod
    def get_timeline_data(db: Session, days: int = 7) -> list[dict]:
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Build date buckets
        date_buckets = {}
        for i in range(days):
            d = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            date_buckets[d] = {"date": d, "suricata": 0, "wazuh": 0, "malware": 0}

        # Count suricata indicators by date
        suricata_rows = (
            db.query(
                func.date(CtiIndicator.created_at).label("d"),
                func.count(CtiIndicator.id),
            )
            .filter(CtiIndicator.source == "suricata", CtiIndicator.created_at >= start_date)
            .group_by(text("d"))
            .all()
        )
        for row in suricata_rows:
            d_str = str(row[0])
            if d_str in date_buckets:
                date_buckets[d_str]["suricata"] = row[1]

        # Count wazuh indicators by date
        wazuh_rows = (
            db.query(
                func.date(CtiIndicator.created_at).label("d"),
                func.count(CtiIndicator.id),
            )
            .filter(CtiIndicator.source == "wazuh", CtiIndicator.created_at >= start_date)
            .group_by(text("d"))
            .all()
        )
        for row in wazuh_rows:
            d_str = str(row[0])
            if d_str in date_buckets:
                date_buckets[d_str]["wazuh"] = row[1]

        # Count malware by date
        malware_rows = (
            db.query(
                func.date(CtiMalware.created_at).label("d"),
                func.count(CtiMalware.id),
            )
            .filter(CtiMalware.created_at >= start_date)
            .group_by(text("d"))
            .all()
        )
        for row in malware_rows:
            d_str = str(row[0])
            if d_str in date_buckets:
                date_buckets[d_str]["malware"] = row[1]

        return sorted(date_buckets.values(), key=lambda x: x["date"])

    @staticmethod
    def get_attack_patterns_with_counts(db: Session) -> dict:
        """Get attack patterns with indicator counts and source attribution."""
        results = (
            db.query(
                CtiAttackPattern.id,
                CtiAttackPattern.mitre_id,
                CtiAttackPattern.name,
                CtiAttackPattern.created_at,
                CtiIndicatorAttackPattern.source,
                func.count(CtiIndicatorAttackPattern.indicator_id).label("count"),
            )
            .outerjoin(
                CtiIndicatorAttackPattern,
                CtiAttackPattern.id == CtiIndicatorAttackPattern.attack_pattern_id,
            )
            .group_by(
                CtiAttackPattern.id,
                CtiAttackPattern.mitre_id,
                CtiAttackPattern.name,
                CtiAttackPattern.created_at,
                CtiIndicatorAttackPattern.source,
            )
            .order_by(CtiAttackPattern.created_at.desc())
            .all()
        )

        source_counts = defaultdict(int)
        technique_counts = {}
        recent = []

        for row in results:
            ap_id, mitre_id, name, created_at, source, count = row
            source_name = source or "Unknown"
            source_counts[source_name] += count

            key = mitre_id or name
            if key not in technique_counts:
                technique_counts[key] = {
                    "mitre_id": mitre_id,
                    "name": name,
                    "count": 0,
                    "source": source_name,
                }
            technique_counts[key]["count"] += count

            if len(recent) < 20:
                recent.append({
                    "id": str(ap_id),
                    "mitre_id": mitre_id,
                    "name": name,
                    "source": source_name,
                    "created": created_at.isoformat() if created_at else "",
                })

        top_techniques = sorted(
            technique_counts.values(),
            key=lambda x: x["count"],
            reverse=True,
        )[:15]

        by_source = [
            {"source": src, "count": cnt}
            for src, cnt in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        total = sum(t["count"] for t in technique_counts.values())

        return {
            "total": total,
            "top_techniques": top_techniques,
            "by_source": by_source,
            "recent": recent,
        }
