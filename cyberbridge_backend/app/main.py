# main.py
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database.database import Base, engine, get_db
from app.routers import users_controller, frameworks_controller, questions_controller, assessments_controller, answers_controller, auth_controller, objectives_controller, risks_controller, policies_controller, home_controller, assessment_types_controller, settings_controller, admin_controller, history_controller, ai_tools_controller, scanners_controller, scopes_controller, backups_controller, audit_engagements_controller, auditor_auth_controller, auditor_review_controller, audit_comments_controller, audit_findings_controller, evidence_integrity_controller, audit_export_controller, audit_dashboard_controller, nvd_controller, audit_notifications_controller, onboarding_controller, policy_aligner_controller, assets_controller, controls_controller, architecture_controller, evidence_controller, compliance_advisor_controller, incidents_controller, euvd_controller, risk_assessments_controller, ce_marking_controller, advisories_controller, gap_analysis_controller, chain_map_controller, suggestions_controller, chatbot_controller, cti_controller, dark_web_controller, api_keys_controller
from app.seeds import SeedManager
from app.config.environment import get_api_base_url, get_environment_name
from app.services import history_cleanup_service, backup_service, nvd_service, euvd_service, scan_scheduler_service
from app.repositories import euvd_repository
from app.middleware import ActivityTrackerMiddleware
import logging
from sqlalchemy import inspect

logger = logging.getLogger(__name__)

# Log the tables that will be created
metadata = Base.metadata
logger.info(f"Attempting to create the following tables: {', '.join(metadata.tables.keys())}")

# Create tables
Base.metadata.create_all(bind=engine)

# Verify which tables were created
inspector = inspect(engine)
tables = inspector.get_table_names()
logger.info(f"Tables in database: {', '.join(tables)}")

# Run database seeds
db = next(get_db())
try:
    seed_manager = SeedManager(db)
    seed_manager.run_all_seeds()
except Exception as e:
    logger.error(f"Error during database seeding: {str(e)}")
finally:
    db.close()

# Start FastAPI, middleware, routers
app = FastAPI(
    title="Compliance Assessment API",
    description="API for managing assessments, frameworks, and questions",
    version="1.0.0"
)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Activity tracking middleware
app.add_middleware(ActivityTrackerMiddleware)

# Add routers to the application
app.include_router(users_controller.router)
app.include_router(auth_controller.router)
app.include_router(admin_controller.router)
app.include_router(frameworks_controller.router)
app.include_router(questions_controller.router)
app.include_router(assessments_controller.router)
app.include_router(answers_controller.router)
app.include_router(objectives_controller.router)
app.include_router(risks_controller.router)
app.include_router(policies_controller.router)
app.include_router(home_controller.router)
app.include_router(assessment_types_controller.router)
app.include_router(settings_controller.router)
app.include_router(history_controller.router)
app.include_router(ai_tools_controller.router)
app.include_router(scanners_controller.router)
app.include_router(scopes_controller.router)
app.include_router(backups_controller.router)
app.include_router(audit_engagements_controller.router)
app.include_router(auditor_auth_controller.router)
app.include_router(auditor_review_controller.router)
app.include_router(audit_comments_controller.router)
app.include_router(audit_findings_controller.router)
app.include_router(evidence_integrity_controller.router)
app.include_router(audit_export_controller.router)
app.include_router(audit_dashboard_controller.router)
app.include_router(nvd_controller.router)
app.include_router(audit_notifications_controller.router)
app.include_router(onboarding_controller.router)
app.include_router(policy_aligner_controller.router)
app.include_router(assets_controller.router)
app.include_router(controls_controller.router)
app.include_router(architecture_controller.router)
app.include_router(evidence_controller.router)
app.include_router(compliance_advisor_controller.router)
app.include_router(incidents_controller.router)
app.include_router(euvd_controller.router)
app.include_router(risk_assessments_controller.router)
app.include_router(ce_marking_controller.router)
app.include_router(advisories_controller.router)
app.include_router(gap_analysis_controller.router)
app.include_router(chain_map_controller.router)
app.include_router(suggestions_controller.router)
app.include_router(chatbot_controller.router)
app.include_router(cti_controller.router)
app.include_router(dark_web_controller.router)
app.include_router(api_keys_controller.router)

# Initialize scheduler
scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def startup_event():
    """
    Start the scheduled jobs on application startup.
    - History cleanup: runs hourly, checks each org's configuration
    - Backup scheduler: runs daily at 2 AM, creates backups for orgs due
    - Backup cleanup: runs weekly on Sunday at 3 AM, removes expired backups
    - NVD sync: runs daily at 3 AM, syncs CVE data from NVD
    """
    from apscheduler.triggers.cron import CronTrigger

    # Schedule the history cleanup job to run every hour
    # Each organization's specific interval is checked within the cleanup function
    scheduler.add_job(
        history_cleanup_service.cleanup_all_organizations,
        trigger=IntervalTrigger(hours=1),
        id='history_cleanup_job',
        name='History Cleanup Job',
        replace_existing=True
    )

    # Schedule the backup job to run daily at 2 AM
    # This checks each organization's backup frequency settings
    scheduler.add_job(
        backup_service.run_scheduled_backups,
        trigger=CronTrigger(hour=2, minute=0),
        id='backup_scheduler_job',
        name='Backup Scheduler Job',
        replace_existing=True
    )

    # Schedule the backup cleanup job to run weekly on Sunday at 3 AM
    # This removes backups that have passed their retention period
    scheduler.add_job(
        backup_service.cleanup_expired_backups,
        trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
        id='backup_cleanup_job',
        name='Backup Cleanup Job',
        replace_existing=True
    )

    # Schedule the NVD sync job to run daily at 3 AM
    # Downloads and updates CVE data from the National Vulnerability Database
    scheduler.add_job(
        nvd_service.run_nvd_sync,
        trigger=CronTrigger(hour=3, minute=0),
        id='nvd_sync_job',
        name='NVD CVE Sync Job',
        replace_existing=True
    )

    # Schedule EUVD sync based on DB settings
    # Fetches exploited, critical, and latest vulnerabilities from the EU Vulnerability Database
    euvd_db = next(get_db())
    try:
        euvd_settings = euvd_repository.get_euvd_settings(euvd_db)
        if not euvd_settings:
            euvd_settings = euvd_repository.create_euvd_settings(euvd_db)

        if euvd_settings.sync_enabled:
            scheduler.add_job(
                euvd_service.run_euvd_sync,
                trigger=IntervalTrigger(
                    hours=euvd_settings.sync_interval_hours,
                    seconds=euvd_settings.sync_interval_seconds
                ),
                id='euvd_sync_job',
                name='EUVD Sync',
                replace_existing=True
            )
            logger.info(f"EUVD sync scheduled: every {euvd_settings.sync_interval_hours}h {euvd_settings.sync_interval_seconds}s")
        else:
            logger.info("EUVD sync disabled in settings")
    except Exception as e:
        logger.error(f"Error loading EUVD settings, using default hourly schedule: {e}")
        scheduler.add_job(
            euvd_service.run_euvd_sync,
            trigger=IntervalTrigger(hours=1),
            id='euvd_sync_job',
            name='EUVD Sync',
            replace_existing=True
        )
    finally:
        euvd_db.close()

    # Initialize scan scheduler service and load all enabled scan schedules
    scan_scheduler_service.init_scheduler(scheduler)

    scheduler.start()

    # Load scan schedules after scheduler has started
    try:
        scan_scheduler_service.load_all_scan_schedules()
    except Exception as e:
        logger.error(f"Error loading scan schedules: {e}")

    logger.info("Scheduler started - History cleanup (hourly), Backup scheduler (daily 2 AM), Backup cleanup (weekly Sunday 3 AM), NVD sync (daily 3 AM), EUVD sync (DB settings), Scan schedules (from DB)")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown the scheduler gracefully when the application stops."""
    scheduler.shutdown()
    logger.info("History cleanup scheduler shut down")


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Compliance Assessment API",
        "docs": "/docs",
        "version": "1.0.0",
        "environment": get_environment_name(),
        "api_base_url": get_api_base_url()
    }
