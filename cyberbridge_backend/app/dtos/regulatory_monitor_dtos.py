from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid


# ==================== Settings ====================

class RegulatoryMonitorSettingsResponse(BaseModel):
    id: uuid.UUID
    scan_frequency: str
    scan_day_of_week: Optional[str] = None
    scan_hour: int
    searxng_url: str
    enabled: bool
    last_scan_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class RegulatoryMonitorSettingsUpdate(BaseModel):
    scan_frequency: Optional[str] = None
    scan_day_of_week: Optional[str] = None
    scan_hour: Optional[int] = None
    searxng_url: Optional[str] = None
    enabled: Optional[bool] = None


# ==================== Sources ====================

class RegulatorySourceCreate(BaseModel):
    framework_type: str
    source_name: str
    source_type: str  # searxng, eurlex_api, nist_api, direct_scrape, rss
    search_query: Optional[str] = None
    domain_filter: Optional[str] = None  # JSON array
    direct_url: Optional[str] = None
    priority: int = 1
    enabled: bool = True


class RegulatorySourceUpdate(BaseModel):
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    search_query: Optional[str] = None
    domain_filter: Optional[str] = None
    direct_url: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None


class RegulatorySourceResponse(BaseModel):
    id: uuid.UUID
    framework_type: str
    source_name: str
    source_type: str
    search_query: Optional[str] = None
    domain_filter: Optional[str] = None
    direct_url: Optional[str] = None
    priority: int
    enabled: bool

    class Config:
        orm_mode = True


# ==================== Scan Runs ====================

class ScanRunResponse(BaseModel):
    id: uuid.UUID
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    frameworks_scanned: int
    changes_found: int
    error_message: Optional[str] = None

    class Config:
        orm_mode = True


class ScanResultResponse(BaseModel):
    id: uuid.UUID
    scan_run_id: uuid.UUID
    framework_type: str
    source_name: str
    source_url: Optional[str] = None
    content_hash: Optional[str] = None
    fetched_at: Optional[datetime] = None

    class Config:
        orm_mode = True


# ==================== Changes ====================

class RegulatoryChangeResponse(BaseModel):
    id: uuid.UUID
    scan_run_id: uuid.UUID
    framework_type: str
    change_type: str
    entity_identifier: Optional[str] = None
    current_value: Optional[str] = None  # JSON string
    proposed_value: Optional[str] = None  # JSON string
    source_url: Optional[str] = None
    source_excerpt: Optional[str] = None
    confidence: Optional[float] = None
    llm_reasoning: Optional[str] = None
    status: str
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ChangeReviewRequest(BaseModel):
    status: str  # approved or rejected


class ApplyChangesRequest(BaseModel):
    change_ids: List[uuid.UUID]
    framework_id: uuid.UUID


class ApplyToSeedRequest(BaseModel):
    change_ids: List[uuid.UUID]
    framework_type: str
    description: Optional[str] = None


class LLMAnalysisRequest(BaseModel):
    llm_response: Optional[str] = None  # If providing pre-computed LLM response


# ==================== Notifications ====================

class NotificationResponse(BaseModel):
    has_findings: bool
    scan_run_id: Optional[str] = None
    scan_date: Optional[str] = None
    frameworks: List[str] = []
    pending_changes: dict = {}


# ==================== Snapshots ====================

class SnapshotResponse(BaseModel):
    id: str
    framework_id: str
    update_version: int
    snapshot_type: str
    created_by: Optional[str] = None
    created_at: Optional[str] = None
