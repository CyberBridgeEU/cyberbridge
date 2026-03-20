import logging

import httpx

from ..config import ZAP_SERVICE_URL, ZAP_TARGETS
from .base import BaseConnector

logger = logging.getLogger(__name__)

# CWE -> MITRE ATT&CK mapping (from original connector)
CWE_TO_ATTACK = {
    "79": ("T1059.007", "JavaScript"),
    "89": ("T1190", "Exploit Public-Facing Application"),
    "22": ("T1083", "File and Directory Discovery"),
    "352": ("T1185", "Browser Session Hijacking"),
    "601": ("T1204", "User Execution"),
    "200": ("T1213", "Data from Information Repositories"),
}

RISK_TO_CONFIDENCE = {"High": 85, "Medium": 60, "Low": 35, "Info": 10}


class ZapConnector(BaseConnector):
    source_name = "zap"

    def __init__(self):
        self.zap_url = ZAP_SERVICE_URL.rstrip("/")
        self.targets = [t.strip() for t in ZAP_TARGETS.split(",") if t.strip()]

    async def fetch_raw_data(self) -> list[dict]:
        results = []
        async with httpx.AsyncClient(timeout=60) as client:
            for target_url in self.targets:
                try:
                    resp = await client.get(
                        f"{self.zap_url}/get-alerts/",
                        params={"target_url": target_url},
                    )
                    resp.raise_for_status()
                    alerts = resp.json().get("alerts", [])
                    for alert in alerts:
                        alert["_target_url"] = target_url
                        results.append(alert)
                except httpx.ConnectError:
                    logger.warning("[ZAP] Cannot reach ZAP API at %s", self.zap_url)
                except Exception as e:
                    logger.error("[ZAP] Error fetching alerts for %s: %s", target_url, e)
        return results

    def normalize(self, raw_item: dict) -> dict:
        risk = raw_item.get("risk", "Info")
        alert_name = raw_item.get("alert", "Unknown Finding")
        description = raw_item.get("description", "")
        solution = raw_item.get("solution", "")
        url_value = raw_item.get("url", "")
        cwe_id = str(raw_item.get("cweId", "")).strip()
        confidence = RISK_TO_CONFIDENCE.get(risk, 50)

        labels = [f"zap-risk-{risk.lower()}"]
        if cwe_id:
            labels.append(f"zap-cwe-{cwe_id}")

        full_description = description
        if solution:
            full_description += f"\n\nSolution: {solution}"

        return {
            "name": f"ZAP: {alert_name}",
            "description": full_description,
            "confidence": confidence,
            "pattern": f"[url:value = '{url_value}']",
            "labels": labels,
            "severity": risk,
            "cwe_id": cwe_id if cwe_id else None,
            "url": url_value,
            "_raw": raw_item,
        }

    def dedup_key(self, normalized: dict) -> str:
        raw = normalized.get("_raw", {})
        alert_name = raw.get("alert", "")
        url_value = raw.get("url", "")
        cwe_id = str(raw.get("cweId", "")).strip()
        return f"zap-{alert_name}-{url_value}-{cwe_id}"

    def get_mitre_mappings(self, raw_item: dict) -> list[tuple[str, str]]:
        cwe_id = str(raw_item.get("cweId", "")).strip()
        if cwe_id and cwe_id in CWE_TO_ATTACK:
            return [CWE_TO_ATTACK[cwe_id]]
        return []
