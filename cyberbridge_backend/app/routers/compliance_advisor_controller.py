import logging
import time
import json
import uuid as _uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
from urllib.parse import urlparse

from app.database.database import get_db
from ..services.auth_service import get_current_active_user
from ..dtos import schemas
from ..services.compliance_advisor_service import scrape_website, analyze_website_for_frameworks
from ..repositories import scanner_history_repository
from ..models import models
from .scanners_controller import get_effective_llm_settings_for_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/compliance-advisor",
    tags=["compliance-advisor"],
    responses={404: {"description": "Not found"}}
)


class AnalyzeRequest(BaseModel):
    url: str

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        # Add scheme if missing
        url = v.strip()
        if not url:
            raise ValueError('URL cannot be empty')
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        parsed = urlparse(url)
        if not parsed.netloc or '.' not in parsed.netloc:
            raise ValueError('Invalid URL format')
        return url


@router.post("/analyze")
async def analyze_website(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Analyze a company website to recommend relevant compliance frameworks.
    Scrapes the homepage and key internal pages, then uses AI to determine
    which frameworks are most applicable.
    """
    logger.info(f"Compliance advisor analysis requested for URL: {request.url} by user {current_user.email}")

    start_time = time.time()

    # Scrape the website
    scraped_data = await scrape_website(request.url)

    if not scraped_data.get("pages"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not scrape the website. {scraped_data.get('error', 'Please check the URL and try again.')}"
        )

    # Get effective LLM settings for the user's org
    llm_settings = get_effective_llm_settings_for_user(db, current_user)
    if not llm_settings.get("ai_enabled", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="AI analysis is disabled. Please enable AI in Settings."
        )

    # Analyze with LLM
    result = await analyze_website_for_frameworks(db, scraped_data, llm_settings=llm_settings)

    duration = time.time() - start_time

    # Persist to scanner_history
    try:
        org = db.query(models.Organisations).filter(
            models.Organisations.id == _uuid.UUID(str(current_user.organisation_id))
        ).first()
        org_name = org.name if org else ""

        scanner_history_repository.create_scanner_history(
            db=db,
            scanner_type="compliance_advisor",
            scan_target=request.url,
            scan_type="website_analysis",
            scan_config=None,
            results=json.dumps(result),
            summary=result.get("company_summary", ""),
            user_id=_uuid.UUID(str(current_user.id)),
            user_email=current_user.email,
            organisation_id=_uuid.UUID(str(current_user.organisation_id)),
            organisation_name=org_name,
            scan_duration=round(duration, 2),
            status="completed",
        )
    except Exception as e:
        logger.warning(f"Failed to save compliance advisor history: {e}")

    return result


@router.get("/history")
async def get_compliance_advisor_history(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """List compliance advisor analysis history for the user's organisation."""
    org_id = _uuid.UUID(str(current_user.organisation_id))
    rows = scanner_history_repository.get_scanner_history_by_scanner_type(
        db, "compliance_advisor", organisation_id=org_id, limit=20
    )
    return [
        {
            "id": str(r.id),
            "scan_target": r.scan_target,
            "summary": r.summary or "",
            "status": r.status,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "user_email": r.user_email,
            "scan_duration": r.scan_duration,
        }
        for r in rows
    ]


@router.get("/latest")
async def get_compliance_advisor_latest(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get the latest compliance advisor analysis for the user's organisation."""
    org_id = _uuid.UUID(str(current_user.organisation_id))
    rows = scanner_history_repository.get_scanner_history_by_scanner_type(
        db, "compliance_advisor", organisation_id=org_id, limit=1
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "id": str(r.id),
        "scan_target": r.scan_target,
        "summary": r.summary or "",
        "status": r.status,
        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        "user_email": r.user_email,
        "scan_duration": r.scan_duration,
        "results": r.results,
    }


@router.delete("/history/{history_id}")
async def delete_compliance_advisor_history(
    history_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete a compliance advisor history record."""
    record = scanner_history_repository.get_scanner_history_by_id(db, _uuid.UUID(history_id))
    if not record:
        raise HTTPException(status_code=404, detail="History record not found")
    if str(record.organisation_id) != str(current_user.organisation_id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this record")

    success = scanner_history_repository.delete_scanner_history(db, _uuid.UUID(history_id))
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete history record")
    return {"success": True, "message": "History record deleted"}
