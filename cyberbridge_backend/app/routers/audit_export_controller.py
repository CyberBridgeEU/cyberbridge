# routers/audit_export_controller.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import uuid
import os

from app.database.database import get_db
from app.services import audit_export_service
from app.repositories import audit_engagement_repository

router = APIRouter(prefix="/audit-engagements", tags=["Audit Export"])


@router.get("/{engagement_id}/export/review-pack")
def download_review_pack(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Generate and download a comprehensive PDF review pack for an audit engagement.
    Includes engagement summary, controls review, findings, comments, and activity log.
    """
    # Verify engagement exists
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    review_pack = audit_export_service.generate_review_pack(db, engagement_id)
    if not review_pack:
        raise HTTPException(status_code=500, detail="Failed to generate review pack")

    filename = f"review_pack_{engagement.name.replace(' ', '_')}_{engagement_id}.pdf"

    return StreamingResponse(
        review_pack,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{engagement_id}/export/evidence-package")
def download_evidence_package(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Generate and download a ZIP package containing all evidence files for an engagement.
    Includes an index file and integrity manifest.
    """
    # Verify engagement exists
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    if not engagement.assessment_id:
        raise HTTPException(status_code=400, detail="Engagement has no associated assessment")

    # Get upload path from environment
    evidence_base_path = os.environ.get("UPLOAD_PATH", "/app/uploads")

    package = audit_export_service.generate_evidence_package(
        db, engagement_id, evidence_base_path
    )
    if not package:
        raise HTTPException(status_code=500, detail="Failed to generate evidence package")

    filename = f"evidence_package_{engagement.name.replace(' ', '_')}_{engagement_id}.zip"

    return StreamingResponse(
        package,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{engagement_id}/export/pbc-list")
def download_pbc_list(
    engagement_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Generate and download a PBC (Prepared by Client) list as CSV.
    Lists all evidence requests and their current status.
    """
    # Verify engagement exists
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    pbc_list = audit_export_service.generate_pbc_list(db, engagement_id)
    if not pbc_list:
        raise HTTPException(status_code=500, detail="Failed to generate PBC list")

    filename = f"pbc_list_{engagement.name.replace(' ', '_')}_{engagement_id}.csv"

    return StreamingResponse(
        pbc_list,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{engagement_id}/export/activity-log")
def download_activity_log(
    engagement_id: uuid.UUID,
    format: str = Query("csv", description="Export format: csv or json"),
    db: Session = Depends(get_db)
):
    """
    Export the activity log for an engagement.
    Supports CSV and JSON formats.
    """
    # Verify engagement exists
    engagement = audit_engagement_repository.get_engagement(db, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    if format not in ['csv', 'json']:
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")

    activity_log = audit_export_service.export_activity_log(db, engagement_id, format)
    if not activity_log:
        raise HTTPException(status_code=500, detail="Failed to export activity log")

    if format == 'json':
        media_type = "application/json"
        extension = "json"
    else:
        media_type = "text/csv"
        extension = "csv"

    filename = f"activity_log_{engagement.name.replace(' ', '_')}_{engagement_id}.{extension}"

    return StreamingResponse(
        activity_log,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
