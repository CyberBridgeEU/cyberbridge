import logging
from typing import Optional

import httpx

from ..config import SEMGREP_SERVICE_URL
from .base import BaseConnector

logger = logging.getLogger(__name__)

# OWASP -> MITRE ATT&CK mapping (from original connector)
OWASP_TO_ATTACK = {
    "A01": ("T1068", "Exploitation for Privilege Escalation"),
    "A02": ("T1552", "Unsecured Credentials"),
    "A03": ("T1059", "Command and Scripting Interpreter"),
    "A04": ("T1190", "Exploit Public-Facing Application"),
    "A05": ("T1078", "Valid Accounts"),
    "A06": ("T1195", "Supply Chain Compromise"),
    "A07": ("T1110", "Brute Force"),
    "A09": ("T1565", "Data Manipulation"),
    "A10": ("T1190", "Exploit Public-Facing Application"),
}

SEVERITY_TO_CONFIDENCE = {"ERROR": 80, "WARNING": 60, "INFO": 30}


class SemgrepConnector(BaseConnector):
    source_name = "semgrep"

    def __init__(self):
        self.semgrep_url = SEMGREP_SERVICE_URL.rstrip("/")
        self._seen_check_ids: set = set()

    async def fetch_raw_data(self) -> list[dict]:
        # Semgrep works via push (POST /api/ingest/semgrep) or
        # the backend triggers scans and pushes results.
        # For polling, we'd need the zip upload flow which requires
        # a code path on disk. Return empty for polling; push is preferred.
        return []

    def normalize(self, raw_item: dict) -> Optional[dict]:
        check_id = raw_item.get("check_id", "unknown")

        # Deduplicate by check_id
        if check_id in self._seen_check_ids:
            return None
        self._seen_check_ids.add(check_id)

        file_path = raw_item.get("path", "unknown")
        extra = raw_item.get("extra", {})
        message = extra.get("message", "")
        severity = extra.get("severity", "WARNING").upper()
        metadata = extra.get("metadata", {})

        start_info = raw_item.get("start", {})
        line_num = start_info.get("line", 0) if isinstance(start_info, dict) else 0

        cwe_raw = metadata.get("cwe", "")
        if isinstance(cwe_raw, list):
            cwe_raw = cwe_raw[0] if cwe_raw else ""
        cwe_str = str(cwe_raw).strip()

        owasp_raw = metadata.get("owasp", "")
        if isinstance(owasp_raw, list):
            owasp_raw = owasp_raw[0] if owasp_raw else ""
        owasp_str = str(owasp_raw).strip()

        # Build labels
        short_check = check_id.split(".")[-1][:30]
        labels = [
            f"semgrep-severity-{severity.lower()}",
            f"semgrep-check-{short_check}",
        ]

        cwe_id = None
        if cwe_str:
            cwe_id = cwe_str.upper().replace("CWE-", "").split(":")[0].split(" ")[0].strip()
            labels.append(f"semgrep-cwe-cwe-{cwe_id.lower()}")

        description = message
        if line_num:
            description += f"\nLine: {line_num}"
        if cwe_str:
            description += f"\nCWE: {cwe_str}"
        if owasp_str:
            description += f"\nOWASP: {owasp_str}"

        owasp_category = None
        if owasp_str:
            owasp_category = owasp_str.split(":")[0].strip().upper()

        return {
            "name": f"Semgrep: {check_id}",
            "description": description,
            "confidence": SEVERITY_TO_CONFIDENCE.get(severity, 50),
            "pattern": f"[file:name = '{file_path}']",
            "labels": labels,
            "severity": severity,
            "cwe_id": cwe_id,
            "owasp_category": owasp_category,
            "check_id": check_id,
            "file_path": file_path,
            "_raw": raw_item,
        }

    def dedup_key(self, normalized: dict) -> str:
        return f"semgrep-{normalized.get('check_id', 'unknown')}"

    def get_mitre_mappings(self, raw_item: dict) -> list[tuple[str, str]]:
        extra = raw_item.get("extra", {})
        metadata = extra.get("metadata", {})
        owasp_raw = metadata.get("owasp", "")
        if isinstance(owasp_raw, list):
            owasp_raw = owasp_raw[0] if owasp_raw else ""
        owasp_str = str(owasp_raw).strip()

        if owasp_str:
            owasp_code = owasp_str.split(":")[0].strip().upper()
            if owasp_code in OWASP_TO_ATTACK:
                return [OWASP_TO_ATTACK[owasp_code]]
        return []
