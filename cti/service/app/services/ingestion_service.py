import logging

from sqlalchemy.orm import Session

from ..connectors.nmap_connector import NmapConnector
from ..connectors.zap_connector import ZapConnector
from ..connectors.semgrep_connector import SemgrepConnector
from ..connectors.osv_connector import OsvConnector

logger = logging.getLogger(__name__)


async def run_all_connectors(db: Session) -> dict[str, int]:
    """Run all scanner connectors and return counts per source."""
    results = {}
    connectors = [
        NmapConnector(),
        ZapConnector(),
        SemgrepConnector(),
        OsvConnector(),
    ]
    for connector in connectors:
        try:
            count = await connector.run(db)
            results[connector.source_name] = count
            logger.info("[Ingestion] %s: %d indicators", connector.source_name, count)
        except Exception as e:
            logger.error("[Ingestion] %s failed: %s", connector.source_name, e)
            results[connector.source_name] = 0
    return results
