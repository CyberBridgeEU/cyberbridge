import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..repositories.indicator_repository import IndicatorRepository
from ..utils import parse_labels as _parse_labels

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/indicators")
def get_indicators(db: Session = Depends(get_db)):
    try:
        total = IndicatorRepository.count_all_indicators(db)
        indicators = IndicatorRepository.get_recent_indicators(db, limit=100)
        recent = []
        for ind in indicators:
            labels = _parse_labels(ind.labels)
            # Determine source display name
            source_map = {
                "nmap": "Nmap Scanner",
                "zap": "ZAP Web Scanner",
                "semgrep": "Semgrep SAST",
                "osv": "OSV Scanner",
                "suricata": "Suricata IDS",
                "wazuh": "Wazuh/SEUXDR Alerts",
                "cape": "CAPE Malware Sandbox",
            }
            source_display = source_map.get(ind.source, ind.source or "Unknown")
            recent.append({
                "id": str(ind.id),
                "name": ind.name or "",
                "created": ind.created_at.isoformat() if ind.created_at else "",
                "confidence": ind.confidence or 0,
                "pattern_type": "stix",
                "source": source_display,
                "labels": labels,
            })
        return {"total": total, "recent": recent}
    except Exception as exc:
        logger.error("get_indicators error: %s", exc)
        return {"total": 0, "recent": []}


@router.get("/api/attack-patterns")
def get_attack_patterns(db: Session = Depends(get_db)):
    try:
        return IndicatorRepository.get_attack_patterns_with_counts(db)
    except Exception as exc:
        logger.error("get_attack_patterns error: %s", exc)
        return {"total": 0, "top_techniques": [], "by_source": [], "recent": []}
