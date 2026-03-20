import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Query, HTTPException
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import List, Optional
import uvicorn
import base64
import json
from pathlib import Path
from app.postgres_queue_manager import postgres_queue_manager, ScanStatus
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the PostgreSQL queue worker on application startup
    print("Starting PostgreSQL queue worker...")
    postgres_queue_manager.start_worker()
    try:
        yield
    finally:
        # Stop the queue worker on application shutdown
        print("Stopping PostgreSQL queue worker...")
        postgres_queue_manager.stop_worker_thread()


app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# No auth middleware — trusted Docker network (like nmap/zap/semgrep)


@app.post("/scan")
def scan_and_report(
    keyword: str = Query(description="Enter the keyword to search"),
    engines: Optional[List[str]] = Query(default=None, description="Search engines to include"),
    exclude: Optional[List[str]] = Query(default=None, description="Search engines to exclude"),
    mp_units: int = Query(default=2, ge=1, le=10, description="Number of multiprocessing units"),
    proxy: str = Query(default="localhost:9050", description="Tor proxy address"),
    limit: int = Query(default=3, ge=1, le=50, description="Max pages per engine"),
    continuous_write: bool = Query(default=False, description="Write progressively to output file"),
    user_id: Optional[str] = Query(default=None, description="User ID (passed by backend proxy)"),
    organisation_id: Optional[str] = Query(default=None, description="Organisation ID (passed by backend proxy)"),
):
    """
    Queue a new dark-web scan. Returns a scan_id for progress tracking.
    No auth required — called from the CyberBridge backend over Docker network.
    """
    try:
        # Load enabled engines
        engines_data, enabled_engines, error = _load_engines_from_files()

        if error:
            print(f"Warning: Error loading engines: {error}")
            enabled_engines = ["clone_systems_engine"]
            all_available_engines = []
        else:
            all_available_engines = list(engines_data.keys()) if engines_data else []

        # Validate keyword
        if not keyword or keyword.strip() == "":
            raise HTTPException(status_code=400, detail="Keyword cannot be empty")
        if len(keyword) > 200:
            raise HTTPException(status_code=400, detail="Keyword too long (max 200 characters)")

        # Use enabled engines if none specified
        if not engines or len(engines) == 0:
            engines = enabled_engines

        # Validate requested engines
        if all_available_engines:
            invalid_engines = [e for e in engines if e not in all_available_engines]
            if invalid_engines:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid engines: {', '.join(invalid_engines)}. Available: {', '.join(all_available_engines)}",
                )

        # Validate proxy format
        if proxy and not proxy.startswith("localhost:"):
            raise HTTPException(status_code=400, detail="Proxy must be in format 'localhost:PORT'")

        # Add to queue
        scan_id = postgres_queue_manager.add_to_queue(
            keyword=keyword,
            engines=engines,
            exclude=exclude,
            mp_units=mp_units,
            proxy=proxy,
            limit=limit,
            continuous_write=continuous_write,
            user_id=user_id or "",
            organisation_id=organisation_id or "",
        )

        status = postgres_queue_manager.get_status(scan_id)
        return {
            "scan_id": scan_id,
            "status": "queued",
            "message": "Scan queued for processing.",
            "queue_position": status.get("position", 0) if status else 0,
            "estimated_wait_minutes": status.get("estimated_wait_minutes", 0) if status else 0,
            "status_url": f"/scan/json/{scan_id}",
            "pdf_url": f"/download/pdf/{scan_id}",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan error: {str(e)}")


@app.get("/scan/json/{scan_id}")
def get_scan_status(scan_id: str):
    """Get the status of a scan as JSON."""
    try:
        status = postgres_queue_manager.get_status(scan_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Scan not found")

        response = {
            "scan_id": scan_id,
            "status": status["status"],
            "keyword": status["keyword"],
            "created_at": status["created_at"],
            "message": f"Scan {status['status']}",
        }

        if status["status"] == ScanStatus.QUEUED.value:
            response.update(
                {
                    "queue_position": status.get("position", 0),
                    "estimated_wait_minutes": status.get("estimated_wait_minutes", 0),
                }
            )

        if status.get("started_at"):
            response["started_at"] = status["started_at"]
        if status.get("completed_at"):
            response["completed_at"] = status["completed_at"]

        if status["status"] == ScanStatus.COMPLETED.value:
            result = status.get("result")
            if result and isinstance(result, dict) and "pdf_report" in result:
                result = result.copy()
                result.pop("pdf_report", None)
            response["results"] = result
            response["pdf_url"] = f"/download/pdf/{scan_id}"

        if status["status"] == ScanStatus.FAILED.value:
            response["error"] = status.get("error")

        # Save status.json to disk (backup)
        try:
            scan_dir = Path("/data") / scan_id
            scan_dir.mkdir(parents=True, exist_ok=True)
            json_path = scan_dir / "status.json"
            response_clean = json.loads(json.dumps(response, default=str))

            def remove_pdf_report(obj):
                if isinstance(obj, dict):
                    obj.pop("pdf_report", None)
                    for value in obj.values():
                        remove_pdf_report(value)
                elif isinstance(obj, list):
                    for item in obj:
                        remove_pdf_report(item)

            remove_pdf_report(response_clean)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(response_clean, f, indent=2, ensure_ascii=False, default=str)
        except Exception as save_error:
            print(f"Warning: Failed to save status.json: {str(save_error)}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting scan status: {str(e)}")


@app.get("/download/pdf/{scan_id}")
def download_pdf(scan_id: str):
    """Download PDF report for a completed scan."""
    try:
        result = postgres_queue_manager.get_scan_result(scan_id)
        if result and "pdf_report" in result and result["pdf_report"]:
            pdf_content = base64.b64decode(result["pdf_report"])
            keyword = result.get("keyword", scan_id)
            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=security_report_{keyword}_{scan_id[:8]}.pdf"
                },
            )

        status = postgres_queue_manager.get_status(scan_id)
        if status:
            if status["status"] == ScanStatus.QUEUED.value:
                raise HTTPException(
                    status_code=202,
                    detail=f"Scan is still queued. Position: {status.get('position', 'unknown')}",
                )
            elif status["status"] == ScanStatus.PROCESSING.value:
                raise HTTPException(status_code=202, detail="Scan is currently processing.")
            elif status["status"] == ScanStatus.FAILED.value:
                raise HTTPException(
                    status_code=500,
                    detail=f"Scan failed: {status.get('error', 'Unknown error')}",
                )
            elif status["status"] == ScanStatus.COMPLETED.value:
                raise HTTPException(status_code=404, detail="PDF report not found")
        else:
            raise HTTPException(status_code=404, detail="Scan not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading PDF: {str(e)}")


@app.get("/queue/overview")
def get_queue_overview():
    """Get overview of the queue system."""
    try:
        overview = postgres_queue_manager.get_queue_overview()
        return {
            **overview,
            "message": "Queue system operational",
            "processing_mode": "parallel",
            "max_concurrent": overview.get("max_workers", 1),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting queue overview: {str(e)}")


@app.delete("/queue/clear")
def clear_queue(confirm: bool = Query(default=False, description="Confirm queue clearing")):
    """Clear all queued scans."""
    if not confirm:
        raise HTTPException(status_code=400, detail="Please confirm by setting confirm=true")
    try:
        postgres_queue_manager.clear_queue()
        return {"message": "Queue cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing queue: {str(e)}")


@app.get("/settings/workers")
def get_max_workers():
    """Get current max_workers setting."""
    try:
        return {
            "max_workers": postgres_queue_manager.max_workers,
            "active_workers": sum(
                1 for t in postgres_queue_manager.worker_threads if t and t.is_alive()
            ),
            "message": f"Currently configured for {postgres_queue_manager.max_workers} concurrent scans",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting max workers: {str(e)}")


@app.put("/settings/workers")
def update_max_workers(max_workers: int = Query(description="New max_workers value (1-10)", ge=1, le=10)):
    """Update max_workers setting and restart worker threads."""
    try:
        print(f"Updating max_workers from {postgres_queue_manager.max_workers} to {max_workers}")
        postgres_queue_manager.stop_worker_thread()
        postgres_queue_manager.max_workers = max_workers
        postgres_queue_manager.save_max_workers(max_workers)
        postgres_queue_manager.start_worker()
        return {
            "max_workers": max_workers,
            "active_workers": sum(
                1 for t in postgres_queue_manager.worker_threads if t and t.is_alive()
            ),
            "message": f"Successfully updated to {max_workers} concurrent scan workers",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating max workers: {str(e)}")


def _load_engines_from_files():
    """Load engines from JSON files."""
    base_path = Path(__file__).parent / "app" / "utils"
    if not base_path.exists():
        base_path = Path.cwd() / "app" / "utils"

    engines_file = base_path / "engines.json"
    if not engines_file.exists():
        return None, None, f"engines.json not found at {engines_file}"

    try:
        with open(engines_file, "r", encoding="utf-8") as f:
            engines_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return None, None, f"Error reading engines.json: {str(e)}"

    # Load from PostgreSQL first, then file fallback
    pg_engines = postgres_queue_manager.get_enabled_engines()
    if pg_engines:
        return engines_data, pg_engines, None

    config_file = base_path / "enabled_engines.json"
    enabled_engines = ["clone_systems_engine"]
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                enabled_data = json.load(f)
                enabled_engines = enabled_data.get("enabled_engines", ["clone_systems_engine"])
        except (json.JSONDecodeError, IOError):
            pass

    return engines_data, enabled_engines, None


@app.get("/settings/engines")
def get_available_engines():
    """Get list of available search engines."""
    try:
        engines_data, enabled_engines, error = _load_engines_from_files()
        if error:
            raise HTTPException(status_code=404, detail=error)

        engines = []
        for name, url in engines_data.items():
            engine_type = "ONION" if ".onion" in url else "CLEARNET"
            engines.append(
                {
                    "name": name,
                    "display_name": name.replace("_", " ").title(),
                    "url": url,
                    "type": engine_type,
                    "enabled": name in enabled_engines,
                }
            )

        return {"engines": engines, "total": len(engines), "enabled_count": len(enabled_engines)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading engines: {str(e)}")


@app.put("/settings/engines")
def update_enabled_engines(request_body: dict):
    """Update which search engines are enabled."""
    try:
        enabled_engines = request_body.get("enabled_engines", [])
        if not enabled_engines:
            raise HTTPException(status_code=400, detail="At least one engine must be enabled")

        engines_data, _, error = _load_engines_from_files()
        if engines_data:
            available_engines = list(engines_data.keys())
            invalid_engines = [e for e in enabled_engines if e not in available_engines]
            if invalid_engines:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid engines: {', '.join(invalid_engines)}. Available: {', '.join(available_engines)}",
                )

        postgres_queue_manager.save_enabled_engines(enabled_engines)
        return {
            "message": "Engines configuration updated successfully.",
            "enabled_engines": enabled_engines,
            "count": len(enabled_engines),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving engines: {str(e)}")


@app.get("/scans")
def list_scans(
    limit: Optional[int] = Query(default=100, ge=1, description="Maximum scans to return"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    user_id: Optional[str] = Query(default=None, description="Filter by user ID (passed by backend)"),
):
    """List scans with optional filtering. No auth — backend handles access control."""
    try:
        scans = postgres_queue_manager.list_all_scans(limit=limit, status=status, user_id=user_id)
        return {"total": len(scans), "scans": scans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing scans: {str(e)}")


@app.delete("/scan/{scan_id}")
def delete_scan(scan_id: str):
    """Delete a scan and all its associated data."""
    try:
        deleted = postgres_queue_manager.delete_scan(scan_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Scan not found")
        return {"message": f"Scan {scan_id} deleted successfully", "scan_id": scan_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting scan: {str(e)}")


@app.get("/health")
def health_check():
    """Health check — verifies PostgreSQL connectivity."""
    try:
        overview = postgres_queue_manager.get_queue_overview()
        return {
            "status": "healthy",
            "database": "connected",
            "worker": "active" if overview["worker_active"] else "inactive",
            "queue_length": overview["queue_length"],
            "currently_processing": len(overview["currently_processing"]) > 0,
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
