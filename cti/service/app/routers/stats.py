import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.stats_service import get_stats
from ..services.timeline_service import get_timeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    try:
        return get_stats(db)
    except Exception as exc:
        logger.error("get_stats error: %s", exc)
        return {
            "suricata": {"indicators": 0, "sightings": 0},
            "wazuh": {"indicators": 0, "sightings": 0},
            "cape": {"indicators": 0, "malware_families": 0},
            "totals": {"indicators": 0, "sightings": 0, "malware_families": 0, "attack_patterns": 0},
        }


@router.get("/api/timeline")
def timeline(days: int = 7, db: Session = Depends(get_db)):
    try:
        return get_timeline(db, days)
    except Exception as exc:
        logger.error("get_timeline error: %s", exc)
        return []
