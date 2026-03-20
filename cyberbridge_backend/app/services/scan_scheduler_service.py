# scan_scheduler_service.py
"""
Background scheduler service for executing scheduled scans.
Uses the main APScheduler instance from main.py to register/update/remove scan jobs.
"""
import logging
import json
import requests
import uuid
import time
from datetime import datetime, timedelta
from typing import Optional

from app.database.database import get_db
from app.repositories import scan_schedule_repository, scanner_history_repository
from app.models import models

logger = logging.getLogger(__name__)

# Reference to the scheduler instance (set by main.py)
_scheduler = None


def init_scheduler(scheduler_instance):
    """Initialize with the APScheduler instance from main.py."""
    global _scheduler
    _scheduler = scheduler_instance


def load_all_scan_schedules():
    """Load all enabled scan schedules from DB and register them with the scheduler."""
    db = next(get_db())
    try:
        schedules = scan_schedule_repository.get_all_enabled_schedules(db)
        for schedule in schedules:
            try:
                register_schedule(schedule)
            except Exception as e:
                logger.error(f"Error registering scan schedule {schedule.id}: {e}")
        logger.info(f"Loaded {len(schedules)} scan schedule(s)")
    except Exception as e:
        logger.error(f"Error loading scan schedules: {e}")
    finally:
        db.close()


def _get_job_id(schedule_id: str) -> str:
    """Generate a unique APScheduler job ID for a scan schedule."""
    return f"scan_schedule_{schedule_id}"


def register_schedule(schedule):
    """Register a scan schedule with APScheduler."""
    if not _scheduler:
        logger.warning("Scheduler not initialized, cannot register scan schedule")
        return

    job_id = _get_job_id(str(schedule.id))

    # Remove existing job if any
    existing = _scheduler.get_job(job_id)
    if existing:
        _scheduler.remove_job(job_id)

    if not schedule.is_enabled:
        logger.info(f"Scan schedule {schedule.id} is disabled, skipping registration")
        return

    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger

    if schedule.schedule_type == "cron":
        trigger = CronTrigger(
            day_of_week=schedule.cron_day_of_week or '*',
            hour=schedule.cron_hour or 0,
            minute=schedule.cron_minute or 0
        )
    else:
        # Interval-based — convert months to days approximately
        total_days = (schedule.interval_months or 0) * 30 + (schedule.interval_days or 0)
        total_hours = schedule.interval_hours or 0
        total_minutes = schedule.interval_minutes or 0
        total_seconds = schedule.interval_seconds or 0

        # Ensure at least some interval
        total_secs = total_days * 86400 + total_hours * 3600 + total_minutes * 60 + total_seconds
        if total_secs <= 0:
            total_secs = 3600  # default 1 hour

        trigger = IntervalTrigger(seconds=total_secs)

    _scheduler.add_job(
        execute_scheduled_scan,
        trigger=trigger,
        id=job_id,
        name=f"Scan: {schedule.scanner_type} -> {schedule.scan_target[:50]}",
        replace_existing=True,
        kwargs={"schedule_id": str(schedule.id)},
        misfire_grace_time=300  # 5 minute grace period
    )
    logger.info(f"Registered scan schedule {schedule.id}: {schedule.scanner_type} -> {schedule.scan_target}")


def update_scheduled_job(schedule):
    """Update an existing scheduled job (re-register it)."""
    register_schedule(schedule)


def remove_scheduled_job(schedule_id: str):
    """Remove a scheduled job from APScheduler."""
    if not _scheduler:
        return
    job_id = _get_job_id(schedule_id)
    existing = _scheduler.get_job(job_id)
    if existing:
        _scheduler.remove_job(job_id)
        logger.info(f"Removed scan schedule job: {schedule_id}")


def _get_scanner_service_url(scanner_type: str) -> str:
    """Get the scanner microservice URL."""
    import os
    urls = {
        "nmap": os.getenv("NMAP_SERVICE_URL", "http://localhost:8011"),
        "semgrep": os.getenv("SEMGREP_SERVICE_URL", "http://localhost:8013"),
        "osv": os.getenv("OSV_SERVICE_URL", "http://localhost:8012"),
        "zap": os.getenv("ZAP_SERVICE_URL", "http://localhost:8010"),
        "syft": os.getenv("SYFT_SERVICE_URL", "http://localhost:8014"),
    }
    return urls.get(scanner_type, "")


def execute_scheduled_scan(schedule_id: str):
    """
    Execute a scheduled scan. Called by APScheduler.
    This runs in a thread so we use synchronous DB/HTTP calls.
    """
    db = next(get_db())
    try:
        schedule = scan_schedule_repository.get_schedule_by_id(db, uuid.UUID(schedule_id))
        if not schedule:
            logger.error(f"Scan schedule {schedule_id} not found")
            return

        if not schedule.is_enabled:
            logger.info(f"Scan schedule {schedule_id} is disabled, skipping execution")
            return

        logger.info(f"Executing scheduled scan: {schedule.scanner_type} -> {schedule.scan_target}")

        start_time = time.time()
        scan_config = json.loads(schedule.scan_config) if schedule.scan_config else {}
        service_url = _get_scanner_service_url(schedule.scanner_type)
        scanner_type = schedule.scanner_type.lower()
        scan_type = schedule.scan_type or "basic"
        results = None
        error_msg = None
        status = "completed"

        try:
            if scanner_type == "nmap":
                # Nmap scans are GET requests
                from urllib.parse import urlparse
                target = schedule.scan_target
                if "://" in target:
                    parsed = urlparse(target)
                    target = parsed.netloc if parsed.netloc else parsed.path

                endpoint_map = {
                    "basic": "/scan/basic",
                    "fast": "/scan/fast",
                    "aggressive": "/scan/aggressive",
                    "all_ports": "/scan/all_ports",
                    "os": "/scan/os",
                    "stealth": "/scan/stealth",
                    "no_ping": "/scan/no_ping",
                    "service_version": "/scan/service_version",
                }
                endpoint = endpoint_map.get(scan_type, "/scan/basic")
                params = {"target": target}
                if scan_type == "ports" and scan_config.get("ports"):
                    params["ports"] = scan_config["ports"]
                    endpoint = "/scan/ports"

                resp = requests.get(f"{service_url}{endpoint}", params=params, timeout=600)
                resp.raise_for_status()
                results = resp.json()

            elif scanner_type == "zap":
                # ZAP scans are GET requests with target
                endpoint_map = {
                    "spider": "/scan/spider",
                    "active": "/scan/active",
                    "full": "/scan/full",
                    "api": "/scan/api",
                }
                endpoint = endpoint_map.get(scan_type, "/scan/spider")
                resp = requests.get(
                    f"{service_url}{endpoint}",
                    params={"target": schedule.scan_target},
                    timeout=1800  # ZAP can take a long time
                )
                resp.raise_for_status()
                results = resp.json()

            elif scanner_type in ["semgrep", "osv", "syft"]:
                # These need a GitHub URL or file upload
                # For scheduled scans, we support GitHub URLs
                github_url = schedule.scan_target
                github_token = scan_config.get("github_token")

                if scanner_type == "semgrep":
                    endpoint = "/scan-github" if "github.com" in github_url else "/scan-zip"
                elif scanner_type == "osv":
                    endpoint = "/scan-github" if "github.com" in github_url else "/scan/zip"
                else:  # syft
                    endpoint = "/scan-github" if "github.com" in github_url else "/scan/zip"

                if "github.com" in github_url:
                    # GitHub URL scan via the main backend (not direct to microservice)
                    # We call the microservice directly by cloning and sending
                    import tempfile, subprocess, shutil, zipfile, io

                    normalized_url = github_url.strip()
                    if not normalized_url.startswith('http'):
                        normalized_url = f"https://{normalized_url}"
                    if normalized_url.endswith('.git'):
                        normalized_url = normalized_url[:-4]

                    from urllib.parse import urlparse
                    parsed = urlparse(normalized_url)
                    path_parts = [p for p in parsed.path.split('/') if p]
                    if len(path_parts) >= 2:
                        owner = path_parts[0]
                        repo = path_parts[1]

                        temp_dir = tempfile.mkdtemp()
                        repo_dir = import_os_path_join(temp_dir, repo)

                        try:
                            clone_url = f"https://{github_token}@github.com/{owner}/{repo}.git" if github_token else f"https://github.com/{owner}/{repo}.git"
                            env = import_os_environ_copy()
                            env["GIT_TERMINAL_PROMPT"] = "0"

                            result = subprocess.run(
                                ["git", "clone", "--depth", "1", clone_url, repo_dir],
                                capture_output=True, text=True, timeout=120, env=env
                            )

                            if result.returncode != 0:
                                raise Exception(f"Git clone failed: {result.stderr}")

                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                                for root, dirs, files_list in import_os_walk(repo_dir):
                                    dirs[:] = [d for d in dirs if d != '.git']
                                    for f in files_list:
                                        file_path = import_os_path_join(root, f)
                                        arcname = import_os_path_relpath(file_path, repo_dir)
                                        zipf.write(file_path, arcname)

                            zip_buffer.seek(0)

                            scan_endpoint = "/scan-zip" if scanner_type in ["semgrep", "syft"] else "/scan/zip"
                            files_payload = {"file": (f"{repo}.zip", zip_buffer, "application/zip")}
                            data_payload = {}
                            if scanner_type == "semgrep":
                                data_payload["config"] = scan_config.get("config", "auto")

                            resp = requests.post(
                                f"{service_url}{scan_endpoint}",
                                files=files_payload,
                                data=data_payload,
                                timeout=600
                            )
                            resp.raise_for_status()
                            results = resp.json()
                        finally:
                            shutil.rmtree(temp_dir, ignore_errors=True)
                    else:
                        raise Exception("Invalid GitHub URL format")
                else:
                    raise Exception(f"Scheduled scans for {scanner_type} require a GitHub URL target")

        except Exception as e:
            logger.error(f"Scheduled scan failed for {schedule_id}: {str(e)}")
            status = "failed"
            error_msg = str(e)

        scan_duration = time.time() - start_time

        # Save to scanner history
        try:
            results_json = json.dumps(results) if results else json.dumps({"error": error_msg})
            scanner_history_repository.create_scanner_history(
                db=db,
                scanner_type=schedule.scanner_type,
                user_id=schedule.user_id,
                user_email=schedule.user_email,
                organisation_id=schedule.organisation_id,
                organisation_name=schedule.organisation_name,
                scan_target=schedule.scan_target,
                scan_type=scan_type,
                scan_config=json.dumps({"scheduled": True, "schedule_id": str(schedule.id), **scan_config}),
                results=results_json,
                summary=None,
                status=status,
                error_message=error_msg,
                scan_duration=scan_duration
            )
        except Exception as e:
            logger.error(f"Error saving scheduled scan history: {e}")

        # Update schedule last_run info
        next_run = _compute_next_run_from_schedule(schedule)
        scan_schedule_repository.update_last_run(
            db=db,
            schedule_id=uuid.UUID(schedule_id),
            status=status,
            error=error_msg,
            next_run_at=next_run
        )

        logger.info(f"Scheduled scan completed: {schedule.scanner_type} -> {schedule.scan_target} [{status}] in {scan_duration:.1f}s")

    except Exception as e:
        logger.error(f"Critical error in scheduled scan execution: {e}")
    finally:
        db.close()


def _compute_next_run_from_schedule(schedule) -> datetime:
    """Compute next run from a ScanSchedule model."""
    now = datetime.now()
    if schedule.schedule_type == "cron":
        day_str = schedule.cron_day_of_week or "*"
        hour = schedule.cron_hour or 0
        minute = schedule.cron_minute or 0
        if day_str == "*":
            candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate <= now:
                candidate += timedelta(days=1)
            return candidate
        else:
            day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
            target_days = [day_map.get(d.strip().lower(), 0) for d in day_str.split(",")]
            for offset in range(8):
                candidate = now + timedelta(days=offset)
                candidate = candidate.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if candidate > now and candidate.weekday() in target_days:
                    return candidate
            return now + timedelta(days=7)
    else:
        total_seconds = (
            (schedule.interval_months or 0) * 30 * 86400 +
            (schedule.interval_days or 0) * 86400 +
            (schedule.interval_hours or 0) * 3600 +
            (schedule.interval_minutes or 0) * 60 +
            (schedule.interval_seconds or 0)
        )
        if total_seconds <= 0:
            total_seconds = 3600
        return now + timedelta(seconds=total_seconds)


# os helpers to avoid top-level import issues in threaded context
import os as _os

def import_os_path_join(*args):
    return _os.path.join(*args)

def import_os_path_relpath(*args):
    return _os.path.relpath(*args)

def import_os_environ_copy():
    return _os.environ.copy()

def import_os_walk(path):
    return _os.walk(path)
