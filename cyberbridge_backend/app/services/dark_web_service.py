# dark_web_service.py
import httpx
import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Dark Web Scanner microservice base URL
DARK_WEB_SCANNER_BASE_URL = os.getenv(
    "DARK_WEB_SCANNER_URL", "http://dark-web-scanner:8001"
)

# HTTP client timeout in seconds
DARK_WEB_TIMEOUT = float(os.getenv("DARK_WEB_TIMEOUT", "120"))


class DarkWebService:
    """
    Service that proxies requests from CyberBridge to the Dark Web Scanner
    microservice. No auth headers needed — trusted Docker network.
    """

    def __init__(self):
        self.base_url = DARK_WEB_SCANNER_BASE_URL.rstrip("/")

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=DARK_WEB_TIMEOUT,
        )

    @staticmethod
    def _handle_response(response: httpx.Response) -> Any:
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.content

    # ------------------------------------------------------------------
    # Scan operations
    # ------------------------------------------------------------------

    async def create_scan(
        self,
        keyword: str,
        user_id: str,
        organisation_id: str,
        engines: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        mp_units: int = 2,
        proxy: str = "localhost:9050",
        limit: int = 3,
        continuous_write: bool = False,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "keyword": keyword,
            "mp_units": mp_units,
            "proxy": proxy,
            "limit": limit,
            "continuous_write": continuous_write,
            "user_id": user_id,
            "organisation_id": organisation_id,
        }
        if engines:
            params["engines"] = engines
        if exclude:
            params["exclude"] = exclude

        logger.info("Creating dark-web scan for keyword=%s engines=%s", keyword, engines)
        async with self._client() as client:
            response = await client.post("/scan", params=params)
            return self._handle_response(response)

    async def get_scans(
        self,
        limit: int = 100,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {"limit": limit}
        if status:
            params["status"] = status
        if user_id:
            params["user_id"] = user_id

        logger.info("Fetching dark-web scans list")
        async with self._client() as client:
            response = await client.get("/scans", params=params)
            return self._handle_response(response)

    async def get_scan_result(self, scan_id: str) -> Dict[str, Any]:
        logger.info("Fetching dark-web scan result for scan_id=%s", scan_id)
        async with self._client() as client:
            response = await client.get(f"/scan/json/{scan_id}")
            return self._handle_response(response)

    async def download_pdf(self, scan_id: str) -> bytes:
        logger.info("Downloading dark-web PDF for scan_id=%s", scan_id)
        async with self._client() as client:
            response = await client.get(f"/download/pdf/{scan_id}")
            response.raise_for_status()
            return response.content

    async def delete_scan(self, scan_id: str) -> Dict[str, Any]:
        logger.info("Deleting dark-web scan scan_id=%s", scan_id)
        async with self._client() as client:
            response = await client.delete(f"/scan/{scan_id}")
            return self._handle_response(response)

    # ------------------------------------------------------------------
    # Queue
    # ------------------------------------------------------------------

    async def get_queue_overview(self) -> Dict[str, Any]:
        logger.info("Fetching dark-web queue overview")
        async with self._client() as client:
            response = await client.get("/queue/overview")
            return self._handle_response(response)

    # ------------------------------------------------------------------
    # Settings – workers
    # ------------------------------------------------------------------

    async def get_workers_settings(self) -> Dict[str, Any]:
        logger.info("Fetching dark-web worker settings")
        async with self._client() as client:
            response = await client.get("/settings/workers")
            return self._handle_response(response)

    async def update_workers_settings(self, max_workers: int) -> Dict[str, Any]:
        logger.info("Updating dark-web max_workers to %d", max_workers)
        async with self._client() as client:
            response = await client.put(
                "/settings/workers", params={"max_workers": max_workers}
            )
            return self._handle_response(response)

    # ------------------------------------------------------------------
    # Settings – engines
    # ------------------------------------------------------------------

    async def get_engines(self) -> Dict[str, Any]:
        logger.info("Fetching dark-web engine settings")
        async with self._client() as client:
            response = await client.get("/settings/engines")
            return self._handle_response(response)

    async def update_engines(self, enabled_engines: List[str]) -> Dict[str, Any]:
        logger.info("Updating dark-web enabled engines: %s", enabled_engines)
        async with self._client() as client:
            response = await client.put(
                "/settings/engines",
                json={"enabled_engines": enabled_engines},
            )
            return self._handle_response(response)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def check_health(self) -> Dict[str, Any]:
        logger.info("Checking dark-web scanner health")
        async with self._client() as client:
            response = await client.get("/health")
            return self._handle_response(response)
