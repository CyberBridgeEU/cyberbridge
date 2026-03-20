import logging
from typing import Optional

import httpx

from ..config import OSV_SERVICE_URL
from .base import BaseConnector

logger = logging.getLogger(__name__)


def _parse_cvss_score(severity_list: list) -> float:
    for entry in severity_list:
        if isinstance(entry, dict) and entry.get("type") == "CVSS_V3":
            try:
                return float(entry.get("score", 0.0))
            except (ValueError, TypeError):
                pass
    return 0.0


def _cvss_to_severity(cvss: float) -> str:
    if cvss >= 9.0:
        return "Critical"
    if cvss >= 7.0:
        return "High"
    if cvss >= 4.0:
        return "Medium"
    return "Low"


class OsvConnector(BaseConnector):
    source_name = "osv"

    def __init__(self):
        self.osv_url = OSV_SERVICE_URL.rstrip("/")
        self._seen_keys: set = set()

    async def fetch_raw_data(self) -> list[dict]:
        # OSV works via push (POST /api/ingest/osv) or
        # requires zip upload of project files. Return empty for polling.
        return []

    def normalize(self, raw_item: dict) -> Optional[dict]:
        pkg_name = raw_item.get("package_name", "unknown")
        pkg_version = raw_item.get("package_version", "unknown")
        ecosystem = raw_item.get("ecosystem", "unknown")
        vuln = raw_item.get("vulnerability", {})
        vuln_id = vuln.get("id", "UNKNOWN")
        summary = vuln.get("summary", "")

        dedup = f"{vuln_id}-{pkg_name}"
        if dedup in self._seen_keys:
            return None
        self._seen_keys.add(dedup)

        severity_list = vuln.get("severity", [])
        cvss = _parse_cvss_score(severity_list)
        severity = _cvss_to_severity(cvss)

        # Extract fixed version
        fixed_version = ""
        for affected in vuln.get("affected", []):
            if isinstance(affected, dict):
                for r in affected.get("ranges", []):
                    for event in r.get("events", []):
                        if "fixed" in event:
                            fixed_version = event["fixed"]
                            break
                if not fixed_version:
                    fixed_version = affected.get("fixed", "")

        description = summary or f"Vulnerable dependency: {pkg_name}@{pkg_version}"
        if fixed_version:
            description += f" (Fixed in: {fixed_version})"
        description += f" | Ecosystem: {ecosystem} | CVSS: {cvss:.1f} ({severity})"

        labels = [
            f"osv-ecosystem-{ecosystem.lower()}",
            f"osv-severity-{severity.lower()}",
            f"osv-id-{vuln_id[:30]}",
        ]

        confidence = int(min(cvss * 10, 100)) if cvss > 0 else 50

        return {
            "name": f"Vulnerable dependency: {pkg_name}@{pkg_version} ({vuln_id})",
            "description": description,
            "confidence": confidence,
            "pattern": f"[software:name = '{pkg_name}' AND software:version = '{pkg_version}']",
            "labels": labels,
            "severity": severity,
            "ecosystem": ecosystem,
            "package_name": pkg_name,
            "package_version": pkg_version,
            "vuln_id": vuln_id if vuln_id.startswith("CVE-") else None,
            "cvss_score": cvss if cvss > 0 else None,
            "_raw": raw_item,
        }

    def dedup_key(self, normalized: dict) -> str:
        raw = normalized.get("_raw", {})
        vuln = raw.get("vulnerability", {})
        return f"osv-{vuln.get('id', 'UNKNOWN')}-{raw.get('package_name', '')}-{raw.get('package_version', '')}"
