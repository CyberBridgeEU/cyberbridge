# cti_service.py
import os
import httpx
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Base URL for the CTI microservice
CTI_SERVICE_BASE_URL = os.environ.get(
    "CTI_DASHBOARD_BASE_URL", "http://cti-service:8000"
)

# Default timeout for HTTP requests (seconds)
CTI_REQUEST_TIMEOUT = float(os.environ.get("CTI_REQUEST_TIMEOUT", "30"))


class CTIService:
    """
    Service that proxies requests to the CTI microservice.

    The CTI service is a lightweight FastAPI application that stores scanner
    results in PostgreSQL and exposes aggregated cyber-threat-intelligence
    data (alerts, indicators, scan results, etc.).
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None):
        self.base_url = (base_url or CTI_SERVICE_BASE_URL).rstrip("/")
        self.timeout = timeout or CTI_REQUEST_TIMEOUT

    # ------------------------------------------------------------------
    # Internal HTTP helper
    # ------------------------------------------------------------------

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform an async GET request against the CTI service API.

        Returns the parsed JSON response body or raises an exception.
        """
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException:
            logger.error("CTI service request timed out: GET %s", path)
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(
                "CTI service returned HTTP %s for GET %s: %s",
                exc.response.status_code,
                path,
                exc.response.text[:500],
            )
            raise
        except httpx.RequestError as exc:
            logger.error("CTI service connection error for GET %s: %s", path, exc)
            raise

    # ------------------------------------------------------------------
    # Public methods – one per CTI service endpoint
    # ------------------------------------------------------------------

    async def check_health(self) -> Dict[str, Any]:
        """Check CTI service health / connectivity."""
        return await self._get("/api/health")

    async def get_stats(self) -> Dict[str, Any]:
        """Fetch aggregated CTI statistics (counts by source)."""
        return await self._get("/api/stats")

    async def get_timeline(self, days: int = 7) -> Any:
        """Fetch CTI event timeline for the given number of days."""
        return await self._get("/api/timeline", params={"days": days})

    async def get_suricata_alerts(self) -> Dict[str, Any]:
        """Fetch Suricata IDS alerts summary."""
        return await self._get("/api/suricata/alerts")

    async def get_wazuh_alerts(self) -> Dict[str, Any]:
        """Fetch Wazuh SIEM alerts summary."""
        return await self._get("/api/wazuh/alerts")

    async def get_malware(self) -> Dict[str, Any]:
        """Fetch CAPE malware sandbox results."""
        return await self._get("/api/malware")

    async def get_attack_patterns(self) -> Dict[str, Any]:
        """Fetch MITRE ATT&CK patterns across all sources."""
        return await self._get("/api/attack-patterns")

    async def get_indicators(self) -> Dict[str, Any]:
        """Fetch all indicators across sources (recent 100)."""
        return await self._get("/api/indicators")

    async def get_nmap_results(self) -> Dict[str, Any]:
        """Fetch Nmap port scan results summary."""
        return await self._get("/api/nmap/results")

    async def get_zap_results(self) -> Dict[str, Any]:
        """Fetch ZAP web application scan results summary."""
        return await self._get("/api/zap/results")

    async def get_semgrep_results(self) -> Dict[str, Any]:
        """Fetch Semgrep SAST code analysis results summary."""
        return await self._get("/api/semgrep/results")

    async def get_osv_results(self) -> Dict[str, Any]:
        """Fetch OSV dependency vulnerability scan results summary."""
        return await self._get("/api/osv/results")
