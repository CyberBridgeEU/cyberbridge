"""
PostgreSQL Queue Manager for handling concurrent dark web scan requests.
Drop-in replacement for redis_queue_manager — uses the shared CyberBridge
database via sync SQLAlchemy (psycopg2).
"""

import json
import uuid
import os
import base64
import threading
import time
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# ---------------------------------------------------------------------------
# Scan status enum (unchanged from Redis version)
# ---------------------------------------------------------------------------

class ScanStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# PostgreSQL Queue Manager
# ---------------------------------------------------------------------------

class PostgresQueueManager:
    def __init__(self, database_url: str, max_workers: int = 3):
        self.engine = create_engine(
            database_url,
            pool_size=max_workers + 2,
            max_overflow=5,
            pool_pre_ping=True,
        )
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Data directory for saving files
        self.DATA_DIR = Path("/data")
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

        # Worker configuration
        self.max_workers = max_workers
        self.enabled_engines: Optional[list] = None
        self.worker_threads: List[threading.Thread] = []
        self.stop_worker = False

        # Re-queue orphaned scans (processing → queued) on startup
        self._recover_orphans()

        # Load persisted max_workers from settings if available
        self._load_settings()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_session(self) -> Session:
        return self.SessionLocal()

    def _recover_orphans(self):
        """Re-queue scans stuck in 'processing' (crashed workers)."""
        session = self._get_session()
        try:
            session.execute(
                text(
                    "UPDATE darkweb_scans SET status = 'queued' "
                    "WHERE status = 'processing'"
                )
            )
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Warning: orphan recovery failed: {e}")
        finally:
            session.close()

    def _load_settings(self):
        """Load max_workers and enabled_engines from darkweb_settings if a record exists."""
        session = self._get_session()
        try:
            row = session.execute(
                text("SELECT max_workers, enabled_engines FROM darkweb_settings LIMIT 1")
            ).fetchone()
            if row:
                self.max_workers = row[0]
                if row[1]:
                    self.enabled_engines = json.loads(row[1])
        except Exception:
            pass  # table may not exist yet on first run
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Queue operations
    # ------------------------------------------------------------------

    def add_to_queue(self, **scan_params) -> str:
        scan_id = str(uuid.uuid4())
        session = self._get_session()
        try:
            session.execute(
                text(
                    "INSERT INTO darkweb_scans "
                    "(id, user_id, organisation_id, keyword, status, engines, params, created_at) "
                    "VALUES (:id, :user_id, :org_id, :keyword, 'queued', :engines, :params, :created_at)"
                ),
                {
                    "id": scan_id,
                    "user_id": scan_params.get("user_id", ""),
                    "org_id": scan_params.get("organisation_id", ""),
                    "keyword": scan_params.get("keyword", ""),
                    "engines": json.dumps(scan_params.get("engines", [])),
                    "params": json.dumps(scan_params),
                    "created_at": datetime.utcnow(),
                },
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

        print(f"Added scan {scan_id} to queue")
        return scan_id

    def get_status(self, scan_id: str) -> Optional[Dict[str, Any]]:
        session = self._get_session()
        try:
            row = session.execute(
                text(
                    "SELECT id, keyword, status, engines, params, result, error, "
                    "created_at, started_at, completed_at "
                    "FROM darkweb_scans WHERE id = :id"
                ),
                {"id": scan_id},
            ).fetchone()
            if not row:
                return None

            result_dict: Dict[str, Any] = {
                "scan_id": str(row[0]),
                "keyword": row[1],
                "status": row[2],
                "created_at": row[7].isoformat() if row[7] else "",
                "started_at": row[8].isoformat() if row[8] else None,
                "completed_at": row[9].isoformat() if row[9] else None,
                "error": row[6] if row[6] else None,
            }

            if row[2] == ScanStatus.QUEUED.value:
                position = self._get_queue_position(session, scan_id)
                result_dict["position"] = position
                result_dict["estimated_wait_minutes"] = position * 2

            if row[2] == ScanStatus.COMPLETED.value and row[5]:
                try:
                    result_dict["result"] = json.loads(row[5])
                except (json.JSONDecodeError, TypeError):
                    result_dict["result"] = None

            return result_dict
        finally:
            session.close()

    def _get_queue_position(self, session: Session, scan_id: str) -> int:
        row = session.execute(
            text(
                "SELECT COUNT(*) FROM darkweb_scans "
                "WHERE status = 'queued' AND created_at <= "
                "(SELECT created_at FROM darkweb_scans WHERE id = :id)"
            ),
            {"id": scan_id},
        ).fetchone()
        return row[0] if row else 0

    def get_queue_overview(self) -> Dict[str, Any]:
        session = self._get_session()
        try:
            counts = {}
            for s in ["queued", "processing", "completed", "failed"]:
                row = session.execute(
                    text("SELECT COUNT(*) FROM darkweb_scans WHERE status = :s"),
                    {"s": s},
                ).fetchone()
                counts[s] = row[0] if row else 0

            total = session.execute(text("SELECT COUNT(*) FROM darkweb_scans")).fetchone()

            processing_ids = [
                str(r[0])
                for r in session.execute(
                    text("SELECT id FROM darkweb_scans WHERE status = 'processing'")
                ).fetchall()
            ]

            active_workers = sum(
                1 for t in self.worker_threads if t and t.is_alive()
            )

            return {
                "queue_length": counts["queued"],
                "processing_count": counts["processing"],
                "completed_count": counts["completed"],
                "total_scans": total[0] if total else 0,
                "workers_busy": counts["processing"],
                "max_workers": self.max_workers,
                "currently_processing": processing_ids,
                "recent_completed": [],
                "worker_active": active_workers > 0,
                "active_workers": active_workers,
                "estimated_total_wait_minutes": max(
                    0,
                    (counts["queued"] - (self.max_workers - counts["processing"])) * 2 / self.max_workers
                )
                if self.max_workers > 0
                else counts["queued"] * 2,
                "avg_processing_time_minutes": 2.0,
                "next_items": [],
            }
        finally:
            session.close()

    def get_scan_result(self, scan_id: str) -> Optional[Dict[str, Any]]:
        session = self._get_session()
        try:
            row = session.execute(
                text("SELECT result FROM darkweb_scans WHERE id = :id"),
                {"id": scan_id},
            ).fetchone()
            if row and row[0]:
                try:
                    return json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    return None
            return None
        finally:
            session.close()

    def list_all_scans(
        self,
        limit: Optional[int] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            query = "SELECT id, keyword, status, user_id, created_at, started_at, completed_at FROM darkweb_scans WHERE 1=1"
            params: Dict[str, Any] = {}

            if status:
                query += " AND status = :status"
                params["status"] = status
            if user_id:
                query += " AND user_id = :user_id"
                params["user_id"] = user_id

            query += " ORDER BY created_at DESC"
            if limit:
                query += " LIMIT :limit"
                params["limit"] = limit

            rows = session.execute(text(query), params).fetchall()
            scans = []
            for r in rows:
                scan_id = str(r[0])
                scan_dir = self.DATA_DIR / scan_id
                json_path = scan_dir / "result.json"
                pdf_paths = list(scan_dir.glob("*.pdf")) if scan_dir.exists() else []

                scans.append(
                    {
                        "scan_id": scan_id,
                        "keyword": r[1],
                        "status": r[2],
                        "user_id": str(r[3]) if r[3] else "",
                        "created_at": r[4].isoformat() if r[4] else "",
                        "started_at": r[5].isoformat() if r[5] else None,
                        "completed_at": r[6].isoformat() if r[6] else None,
                        "files": {
                            "json_exists": json_path.exists(),
                            "pdf_exists": len(pdf_paths) > 0,
                            "pdf_files": [str(p.name) for p in pdf_paths],
                        },
                    }
                )
            return scans
        finally:
            session.close()

    def delete_scan(self, scan_id: str) -> bool:
        import shutil

        session = self._get_session()
        try:
            result = session.execute(
                text("DELETE FROM darkweb_scans WHERE id = :id"), {"id": scan_id}
            )
            session.commit()
            deleted = result.rowcount > 0
        except Exception:
            session.rollback()
            deleted = False
        finally:
            session.close()

        scan_dir = self.DATA_DIR / scan_id
        if scan_dir.exists():
            shutil.rmtree(scan_dir, ignore_errors=True)

        return deleted

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def save_max_workers(self, max_workers: int):
        session = self._get_session()
        try:
            row = session.execute(text("SELECT id FROM darkweb_settings LIMIT 1")).fetchone()
            if row:
                session.execute(
                    text("UPDATE darkweb_settings SET max_workers = :mw, updated_at = :now WHERE id = :id"),
                    {"mw": max_workers, "now": datetime.utcnow(), "id": str(row[0])},
                )
            else:
                # Get a real organisation_id to satisfy the foreign key
                org_row = session.execute(
                    text("SELECT id FROM organisations LIMIT 1")
                ).fetchone()
                org_id = str(org_row[0]) if org_row else str(uuid.uuid4())
                session.execute(
                    text(
                        "INSERT INTO darkweb_settings (id, organisation_id, max_workers, created_at, updated_at) "
                        "VALUES (:id, :org_id, :mw, :now, :now)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "org_id": org_id,
                        "mw": max_workers,
                        "now": datetime.utcnow(),
                    },
                )
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Warning: Failed to save max_workers to DB: {e}")
        finally:
            session.close()

    def get_enabled_engines(self) -> Optional[list]:
        if self.enabled_engines is not None:
            return self.enabled_engines
        session = self._get_session()
        try:
            row = session.execute(
                text("SELECT enabled_engines FROM darkweb_settings LIMIT 1")
            ).fetchone()
            if row and row[0]:
                self.enabled_engines = json.loads(row[0])
                return self.enabled_engines
            return None
        except Exception:
            return None
        finally:
            session.close()

    def save_enabled_engines(self, engines: list):
        self.enabled_engines = engines
        session = self._get_session()
        try:
            row = session.execute(text("SELECT id FROM darkweb_settings LIMIT 1")).fetchone()
            if row:
                session.execute(
                    text(
                        "UPDATE darkweb_settings SET enabled_engines = :eng, updated_at = :now WHERE id = :id"
                    ),
                    {"eng": json.dumps(engines), "now": datetime.utcnow(), "id": str(row[0])},
                )
            else:
                # Get a real organisation_id to satisfy the foreign key
                org_row = session.execute(
                    text("SELECT id FROM organisations LIMIT 1")
                ).fetchone()
                org_id = str(org_row[0]) if org_row else str(uuid.uuid4())
                session.execute(
                    text(
                        "INSERT INTO darkweb_settings (id, organisation_id, max_workers, enabled_engines, created_at, updated_at) "
                        "VALUES (:id, :org_id, 3, :eng, :now, :now)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "org_id": org_id,
                        "eng": json.dumps(engines),
                        "now": datetime.utcnow(),
                    },
                )
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Warning: Failed to save enabled engines to DB: {e}")
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Worker management
    # ------------------------------------------------------------------

    def start_worker(self):
        if not self.worker_threads or not any(t.is_alive() for t in self.worker_threads):
            self.stop_worker = False
            self.worker_threads = []

            for i in range(self.max_workers):
                worker_thread = threading.Thread(
                    target=self._worker_loop,
                    args=(i,),
                    daemon=False,
                    name=f"ScanWorker-{i}",
                )
                worker_thread.start()
                self.worker_threads.append(worker_thread)
                print(f"PostgreSQL queue worker {i+1}/{self.max_workers} started")

            print(f"All {self.max_workers} workers started")

    def stop_worker_thread(self):
        self.stop_worker = True
        for i, worker_thread in enumerate(self.worker_threads):
            if worker_thread:
                worker_thread.join(timeout=5)
                print(f"Worker {i+1} stopped")
        self.worker_threads = []
        print("All workers stopped")

    def _worker_loop(self, worker_id: int):
        worker_name = f"Worker-{worker_id}"
        while not self.stop_worker:
            try:
                scan_id = self._pick_next_scan()
                if scan_id is None:
                    time.sleep(1)
                    continue

                print(f"[{worker_name}] Processing scan: {scan_id}")
                self._process_scan(scan_id, worker_name)

            except Exception as e:
                print(f"Worker loop error: {str(e)}")
                traceback.print_exc()
                time.sleep(1)

    def _pick_next_scan(self) -> Optional[str]:
        """Atomically pick the next queued scan using FOR UPDATE SKIP LOCKED."""
        session = self._get_session()
        try:
            row = session.execute(
                text(
                    "UPDATE darkweb_scans SET status = 'processing', started_at = :now "
                    "WHERE id = ("
                    "  SELECT id FROM darkweb_scans "
                    "  WHERE status = 'queued' "
                    "  ORDER BY created_at "
                    "  FOR UPDATE SKIP LOCKED "
                    "  LIMIT 1"
                    ") RETURNING id"
                ),
                {"now": datetime.utcnow()},
            ).fetchone()
            session.commit()
            return str(row[0]) if row else None
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()

    def _process_scan(self, scan_id: str, worker_name: str):
        session = self._get_session()
        try:
            # Get scan params
            row = session.execute(
                text("SELECT params, keyword FROM darkweb_scans WHERE id = :id"),
                {"id": scan_id},
            ).fetchone()
            if not row:
                return

            params = json.loads(row[0]) if row[0] else {}
            keyword = row[1]
            session.close()

            # Execute the search
            from app.darkweb_search_service import search_keyword

            result = search_keyword(
                keyword=params.get("keyword", keyword),
                engines=params.get("engines"),
                exclude=params.get("exclude"),
                mp_units=params.get("mp_units", 2),
                proxy=params.get("proxy", "localhost:9050"),
                limit=params.get("limit", 3),
                continuous_write=params.get("continuous_write", False),
                use_categorized=True,
            )

            # Save result to database
            pdf_report = result.get("pdf_report")
            result_json = json.dumps(result)

            session = self._get_session()
            session.execute(
                text(
                    "UPDATE darkweb_scans SET status = 'completed', "
                    "completed_at = :now, result = :result WHERE id = :id"
                ),
                {"now": datetime.utcnow(), "result": result_json, "id": scan_id},
            )
            session.commit()
            session.close()

            # Save files to disk
            result_for_file = result.copy()
            result_for_file.pop("pdf_report", None)
            self._save_scan_files(scan_id, result_for_file, keyword, pdf_report)

            print(f"[{worker_name}] Scan {scan_id} completed successfully")

        except Exception as e:
            error_msg = f"Scan failed: {str(e)}\n{traceback.format_exc()}"
            print(f"[{worker_name}] Scan {scan_id} failed: {error_msg}")

            session = self._get_session()
            try:
                session.execute(
                    text(
                        "UPDATE darkweb_scans SET status = 'failed', "
                        "completed_at = :now, error = :error WHERE id = :id"
                    ),
                    {"now": datetime.utcnow(), "error": error_msg, "id": scan_id},
                )
                session.commit()
            except Exception:
                session.rollback()
            finally:
                session.close()

    def _save_scan_files(
        self,
        scan_id: str,
        result: Dict[str, Any],
        keyword: str,
        pdf_report: Optional[str] = None,
    ):
        try:
            scan_dir = self.DATA_DIR / scan_id
            scan_dir.mkdir(parents=True, exist_ok=True)

            # Save result.json
            json_path = scan_dir / "result.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)

            # Save PDF
            if pdf_report:
                pdf_path = scan_dir / f"report_{keyword}_{scan_id[:8]}.pdf"
                pdf_content = base64.b64decode(pdf_report)
                with open(pdf_path, "wb") as f:
                    f.write(pdf_content)

        except Exception as e:
            print(f"Warning: Failed to save scan files for {scan_id}: {str(e)}")

    # ------------------------------------------------------------------
    # Convenience (not used internally but matches Redis interface)
    # ------------------------------------------------------------------

    def clear_queue(self):
        session = self._get_session()
        try:
            session.execute(text("DELETE FROM darkweb_scans WHERE status = 'queued'"))
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Singleton instance
# ---------------------------------------------------------------------------

_database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/postgres")
# Ensure sync driver (strip +asyncpg if present)
_database_url = _database_url.replace("+asyncpg", "")
_max_workers = int(os.getenv("MAX_SCAN_WORKERS", "3"))

print(f"PostgreSQL Queue Configuration:")
print(f"   Database: {_database_url}")
print(f"   Max Workers: {_max_workers}")

postgres_queue_manager = PostgresQueueManager(
    database_url=_database_url,
    max_workers=_max_workers,
)
