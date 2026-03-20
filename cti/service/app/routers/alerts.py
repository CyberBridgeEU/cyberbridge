from fastapi import APIRouter

router = APIRouter()


@router.get("/api/suricata/alerts")
def suricata_alerts():
    """Stub endpoint — Suricata not yet integrated."""
    return {
        "total": 0,
        "by_category": {},
        "by_severity": {"High": 0, "Medium": 0, "Low": 0, "Unknown": 0},
        "top_src_ips": [],
        "recent": [],
    }


@router.get("/api/wazuh/alerts")
def wazuh_alerts():
    """Stub endpoint — Wazuh not yet integrated."""
    return {
        "total": 0,
        "by_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Unknown": 0},
        "by_rule_group": {},
        "recent": [],
    }
