import logging
import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .database import SessionLocal
from .config import SCANNER_POLL_INTERVAL, MITRE_SYNC_INTERVAL, KEV_SYNC_INTERVAL
from .routers import health, stats, indicators, scanner_results, alerts, malware, ingest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_connector_run():
    """Periodic task: run all scanner connectors."""
    from .services.ingestion_service import run_all_connectors
    db = SessionLocal()
    try:
        results = await run_all_connectors(db)
        logger.info("[Scheduler] Connector run complete: %s", results)
    except Exception as e:
        logger.error("[Scheduler] Connector run failed: %s", e)
    finally:
        db.close()


async def scheduled_mitre_sync():
    """Periodic task: sync MITRE ATT&CK feed."""
    from .feeds.mitre_attack import sync_mitre_attack
    db = SessionLocal()
    try:
        count = await sync_mitre_attack(db)
        logger.info("[Scheduler] MITRE sync complete: %d patterns", count)
    except Exception as e:
        logger.error("[Scheduler] MITRE sync failed: %s", e)
    finally:
        db.close()


async def scheduled_kev_sync():
    """Periodic task: sync CISA KEV feed."""
    from .feeds.cisa_kev import sync_cisa_kev
    db = SessionLocal()
    try:
        count = await sync_cisa_kev(db)
        logger.info("[Scheduler] KEV sync complete: %d entries", count)
    except Exception as e:
        logger.error("[Scheduler] KEV sync failed: %s", e)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tables are created by cyberbridge_backend (Alembic migrations)
    logger.info("CTI service starting (tables managed by backend)")

    # Schedule periodic jobs
    scheduler.add_job(
        scheduled_connector_run,
        IntervalTrigger(seconds=SCANNER_POLL_INTERVAL),
        id="connector_run",
        name="Scanner connector polling",
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_mitre_sync,
        IntervalTrigger(seconds=MITRE_SYNC_INTERVAL),
        id="mitre_sync",
        name="MITRE ATT&CK sync",
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_kev_sync,
        IntervalTrigger(seconds=KEV_SYNC_INTERVAL),
        id="kev_sync",
        name="CISA KEV sync",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started")

    # Run initial sync in the background after a short delay
    async def initial_sync():
        await asyncio.sleep(10)
        await scheduled_mitre_sync()
        await scheduled_kev_sync()
        await scheduled_connector_run()

    asyncio.create_task(initial_sync())

    yield

    scheduler.shutdown()
    logger.info("Scheduler shut down")


app = FastAPI(title="CyberGuard CTI Service", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(stats.router)
app.include_router(indicators.router)
app.include_router(scanner_results.router)
app.include_router(alerts.router)
app.include_router(malware.router)
app.include_router(ingest.router)
