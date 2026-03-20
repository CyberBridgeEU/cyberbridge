# routers/admin_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from ..database.database import get_db
from ..services.auth_service import get_current_user, check_user_role
from ..services import history_cleanup_service, notification_service
from ..repositories import user_repository, user_sessions_repository, pdf_downloads_repository
from ..dtos import schemas
from ..models import models

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/all-users")
def get_all_users(
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Get all users (super_admin sees all, org_admin sees only their org)"""
    try:
        if current_user.role_name == "super_admin":
            # Super admin sees all users
            users = db.query(user_repository.models.User).all()
        else:
            # Org admin sees only users from their organization
            users = db.query(user_repository.models.User).filter(
                user_repository.models.User.organisation_id == current_user.organisation_id
            ).all()

        # Format response with role and organization names
        result = []
        for user in users:
            # Get role name
            role = db.query(user_repository.models.Role).filter(
                user_repository.models.Role.id == user.role_id
            ).first()

            # Filter out superadmin users if current user is org_admin
            if current_user.role_name == "org_admin" and role and role.role_name == "super_admin":
                continue

            # Get organization name
            org = db.query(user_repository.models.Organisations).filter(
                user_repository.models.Organisations.id == user.organisation_id
            ).first()

            result.append({
                "id": str(user.id),
                "email": user.email,
                "role_name": role.role_name if role else None,
                "organisation_name": org.name if org else None,
                "status": user.status,
                "created_at": user.created_at.isoformat() if user.created_at else None
            })

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching users: {str(e)}"
        )

@router.get("/pending-users")
def get_pending_users(
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Get all pending users for approval (super_admin sees all, org_admin sees only their org)"""
    try:
        pending_users = user_repository.get_pending_users_for_approval(db, current_user)
        
        # Format response
        result = []
        for user in pending_users:
            result.append({
                "id": str(user.id),
                "email": user.email,
                "role_name": user.role_name,
                "organisation_name": user.organisation_name,
                "status": user.status,
                "created_at": user.created_at.isoformat() if user.created_at else None
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching pending users: {str(e)}"
        )

@router.post("/approve-user/{user_id}")
def approve_user(
    user_id: str,
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Approve a user (change status from pending_approval to active)"""
    try:
        # Convert string to UUID
        user_uuid = uuid.UUID(user_id)
        
        # Get the user to be approved
        user_to_approve = user_repository.get_user(db, user_uuid)
        if not user_to_approve:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if current user has permission to approve this user
        current_user_role = db.query(user_repository.models.Role).filter(
            user_repository.models.Role.id == current_user.role_id
        ).first()
        
        if current_user_role.role_name == "org_admin":
            # Org admin can only approve users from same organization
            if user_to_approve.organisation_id != current_user.organisation_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only approve users from your organization"
                )

        # Only super_admin can approve org_admin users
        user_role = db.query(models.Role).filter(models.Role.id == user_to_approve.role_id).first()
        if user_role and user_role.role_name == "org_admin" and current_user_role.role_name != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super administrators can approve organization admin accounts"
            )

        # Update user status to active
        updated_user = user_repository.update_user_status(db, user_uuid, "active")

        # Send email notification (non-blocking)
        try:
            notification_service.send_account_status_change_notification(
                db=db,
                user_id=str(updated_user.id),
                user_email=user_to_approve.email,
                new_status="active",
                changed_by_email=current_user.email,
            )
        except Exception as notif_err:
            logger.warning(f"Failed to send approval notification to {user_to_approve.email}: {notif_err}")

        return {
            "message": f"User {user_to_approve.email} has been approved",
            "user_id": str(updated_user.id),
            "status": updated_user.status
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while approving user: {str(e)}"
        )

@router.post("/reject-user/{user_id}")
def reject_user(
    user_id: str,
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Reject a user (change status from pending_approval to inactive)"""
    try:
        # Convert string to UUID
        user_uuid = uuid.UUID(user_id)

        # Get the user to be rejected
        user_to_reject = user_repository.get_user(db, user_uuid)
        if not user_to_reject:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if current user has permission to reject this user
        current_user_role = db.query(user_repository.models.Role).filter(
            user_repository.models.Role.id == current_user.role_id
        ).first()

        if current_user_role.role_name == "org_admin":
            # Org admin can only reject users from same organization
            if user_to_reject.organisation_id != current_user.organisation_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only reject users from your organization"
                )

        # Only super_admin can reject org_admin users
        user_role = db.query(models.Role).filter(models.Role.id == user_to_reject.role_id).first()
        if user_role and user_role.role_name == "org_admin" and current_user_role.role_name != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super administrators can reject organization admin accounts"
            )

        # Update user status to inactive
        updated_user = user_repository.update_user_status(db, user_uuid, "inactive")

        # Send email notification (non-blocking)
        try:
            notification_service.send_account_status_change_notification(
                db=db,
                user_id=str(updated_user.id),
                user_email=user_to_reject.email,
                new_status="inactive",
                changed_by_email=current_user.email,
            )
        except Exception as notif_err:
            logger.warning(f"Failed to send rejection notification to {user_to_reject.email}: {notif_err}")

        return {
            "message": f"User {user_to_reject.email} has been rejected",
            "user_id": str(updated_user.id),
            "status": updated_user.status
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while rejecting user: {str(e)}"
        )

@router.put("/update-user-status/{user_id}")
def update_user_status(
    user_id: str,
    status_update: schemas.UserStatusUpdate,
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Update a user's status (pending_approval, active, or inactive)"""
    try:
        # Convert string to UUID
        user_uuid = uuid.UUID(user_id)

        # Get the user to be updated
        user_to_update = user_repository.get_user(db, user_uuid)
        if not user_to_update:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if current user has permission to update this user
        current_user_role = db.query(user_repository.models.Role).filter(
            user_repository.models.Role.id == current_user.role_id
        ).first()

        if current_user_role.role_name == "org_admin":
            # Org admin can only update users from same organization
            if user_to_update.organisation_id != current_user.organisation_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only update users from your organization"
                )

        # Only super_admin can change org_admin user status
        user_role = db.query(models.Role).filter(models.Role.id == user_to_update.role_id).first()
        if user_role and user_role.role_name == "org_admin" and current_user_role.role_name != "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super administrators can change organization admin account status"
            )

        # Validate status value
        valid_statuses = ["pending_approval", "active", "inactive"]
        if status_update.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        # Update user status
        updated_user = user_repository.update_user_status(db, user_uuid, status_update.status)

        # Send email notification (non-blocking)
        try:
            notification_service.send_account_status_change_notification(
                db=db,
                user_id=str(updated_user.id),
                user_email=user_to_update.email,
                new_status=status_update.status,
                changed_by_email=current_user.email,
            )
        except Exception as notif_err:
            logger.warning(f"Failed to send status change notification to {user_to_update.email}: {notif_err}")

        return {
            "message": f"User {user_to_update.email} status updated to {status_update.status}",
            "user_id": str(updated_user.id),
            "status": updated_user.status
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating user status: {str(e)}"
        )


@router.get("/online-users")
def get_online_users(
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Get list of currently online users (active within last 3 minutes)"""
    from datetime import datetime, timedelta

    try:
        # Calculate threshold (3 minutes ago)
        threshold = datetime.utcnow() - timedelta(minutes=3)

        # Query users with recent activity
        query = db.query(models.User).filter(
            models.User.last_activity >= threshold,
            models.User.status == "active"
        )

        # Filter by organization for org_admin
        if current_user.role_name == "org_admin":
            query = query.filter(models.User.organisation_id == current_user.organisation_id)

        online_users = query.all()

        # Format response with role and org names
        result = []
        for user in online_users:
            # Get role name
            role = db.query(models.Role).filter(
                models.Role.id == user.role_id
            ).first()

            # Get organization name
            org = db.query(models.Organisations).filter(
                models.Organisations.id == user.organisation_id
            ).first()

            result.append({
                "id": str(user.id),
                "email": user.email,
                "role_name": role.role_name if role else None,
                "organisation_name": org.name if org else None,
                "last_activity": user.last_activity.isoformat() if user.last_activity else None
            })

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching online users: {str(e)}"
        )


# ============ User Sessions Endpoints ============

@router.get("/user-sessions")
def get_user_sessions(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Get all user sessions with optional date filtering"""
    from datetime import datetime

    try:
        # Parse date strings if provided
        from_datetime = None
        to_datetime = None

        if from_date:
            try:
                from_datetime = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from_date format. Use ISO format.")

        if to_date:
            try:
                to_datetime = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_date format. Use ISO format.")

        # Get sessions from repository
        sessions = user_sessions_repository.get_all_user_sessions(db, from_datetime, to_datetime)

        # Format response
        result = []
        for session in sessions:
            result.append({
                "id": str(session.id),
                "user_id": str(session.user_id),
                "email": session.email,
                "login_timestamp": session.login_timestamp.isoformat() if session.login_timestamp else None,
                "logout_timestamp": session.logout_timestamp.isoformat() if session.logout_timestamp else None,
                "created_at": session.created_at.isoformat() if session.created_at else None
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching user sessions: {str(e)}"
        )


@router.get("/visits-per-email")
def get_visits_per_email(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Get total visits per email with optional date filtering"""
    from datetime import datetime

    try:
        # Parse date strings if provided
        from_datetime = None
        to_datetime = None

        if from_date:
            try:
                from_datetime = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from_date format. Use ISO format.")

        if to_date:
            try:
                to_datetime = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_date format. Use ISO format.")

        # Get visits per email from repository
        visits = user_sessions_repository.get_visits_per_email(db, from_datetime, to_datetime)

        # Format response
        result = []
        for visit in visits:
            result.append({
                "email": visit.email,
                "visit_count": visit.visit_count
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching visits per email: {str(e)}"
        )


@router.get("/total-visits")
def get_total_visits(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Get total number of visits with optional date filtering"""
    from datetime import datetime

    try:
        # Parse date strings if provided
        from_datetime = None
        to_datetime = None

        if from_date:
            try:
                from_datetime = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from_date format. Use ISO format.")

        if to_date:
            try:
                to_datetime = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_date format. Use ISO format.")

        # Get total visits from repository
        total = user_sessions_repository.get_total_visits(db, from_datetime, to_datetime)

        return {
            "total_visits": total or 0
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching total visits: {str(e)}"
        )


@router.delete("/user-sessions")
def delete_all_user_sessions(
    current_user=Depends(check_user_role(["super_admin"])),
    db: Session = Depends(get_db)
):
    """Delete all user sessions from the database (super_admin only)"""
    try:
        # Delete all sessions
        deleted_count = user_sessions_repository.delete_all_user_sessions(db)

        return {
            "message": "All user sessions have been deleted successfully",
            "deleted_count": deleted_count
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting user sessions: {str(e)}"
        )


# ============ History Cleanup Configuration Endpoints ============

class HistoryCleanupConfigUpdate(BaseModel):
    history_cleanup_enabled: Optional[bool] = None
    history_retention_days: Optional[int] = None
    history_cleanup_interval_hours: Optional[int] = None


@router.get("/organizations/{org_id}/history-cleanup-config")
def get_history_cleanup_config(
    org_id: str,
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Get history cleanup configuration for an organization"""
    try:
        org_uuid = uuid.UUID(org_id)

        # Check permissions: org_admin can only access their own org
        if current_user.role_name == "org_admin" and str(current_user.organisation_id) != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own organization's settings"
            )

        org = db.query(models.Organisations).filter(
            models.Organisations.id == org_uuid
        ).first()

        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        return {
            "organisation_id": str(org.id),
            "organisation_name": org.name,
            "history_cleanup_enabled": org.history_cleanup_enabled,
            "history_retention_days": org.history_retention_days,
            "history_cleanup_interval_hours": org.history_cleanup_interval_hours
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid organization ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching history cleanup configuration: {str(e)}"
        )


@router.put("/organizations/{org_id}/history-cleanup-config")
def update_history_cleanup_config(
    org_id: str,
    config: HistoryCleanupConfigUpdate,
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Update history cleanup configuration for an organization"""
    try:
        org_uuid = uuid.UUID(org_id)

        # Check permissions
        if current_user.role_name == "org_admin" and str(current_user.organisation_id) != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own organization's settings"
            )

        org = db.query(models.Organisations).filter(
            models.Organisations.id == org_uuid
        ).first()

        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        # Update fields if provided
        if config.history_cleanup_enabled is not None:
            org.history_cleanup_enabled = config.history_cleanup_enabled

        if config.history_retention_days is not None:
            if config.history_retention_days < 1:
                raise HTTPException(status_code=400, detail="Retention days must be at least 1")
            org.history_retention_days = config.history_retention_days

        if config.history_cleanup_interval_hours is not None:
            if config.history_cleanup_interval_hours < 1:
                raise HTTPException(status_code=400, detail="Cleanup interval must be at least 1 hour")
            org.history_cleanup_interval_hours = config.history_cleanup_interval_hours

        db.commit()
        db.refresh(org)

        return {
            "message": "History cleanup configuration updated successfully",
            "organisation_id": str(org.id),
            "history_cleanup_enabled": org.history_cleanup_enabled,
            "history_retention_days": org.history_retention_days,
            "history_cleanup_interval_hours": org.history_cleanup_interval_hours
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid organization ID format")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating history cleanup configuration: {str(e)}"
        )


@router.post("/organizations/{org_id}/cleanup-history-now")
def cleanup_history_now(
    org_id: str,
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Manually trigger history cleanup for an organization"""
    try:
        org_uuid = uuid.UUID(org_id)

        # Check permissions
        if current_user.role_name == "org_admin" and str(current_user.organisation_id) != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cleanup your own organization's history"
            )

        # Run cleanup
        result = history_cleanup_service.manual_cleanup_organization(org_id, db)

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])

        return result

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid organization ID format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while cleaning up history: {str(e)}"
        )


# ============ PDF Downloads Tracking Endpoints ============

class PdfDownloadTrack(BaseModel):
    pdf_type: str  # assessment, policy, risk, product, objectives, zap, nmap, semgrep, osv


@router.post("/track-pdf-download")
def track_pdf_download(
    download: PdfDownloadTrack,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track a PDF download"""
    try:
        # Validate current_user
        if not current_user or not hasattr(current_user, 'id') or not current_user.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated or invalid user session"
            )

        # Create PDF download record
        pdf_downloads_repository.create_pdf_download(
            db=db,
            user_id=current_user.id,
            email=current_user.email,
            pdf_type=download.pdf_type
        )

        return {
            "message": "PDF download tracked successfully",
            "pdf_type": download.pdf_type
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"PDF Download Tracking Error: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while tracking PDF download: {str(e)}"
        )


@router.get("/total-pdf-downloads")
def get_total_pdf_downloads(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Get total number of PDF downloads with optional date filtering"""
    from datetime import datetime

    try:
        # Parse date strings if provided
        from_datetime = None
        to_datetime = None

        if from_date:
            try:
                from_datetime = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from_date format. Use ISO format.")

        if to_date:
            try:
                to_datetime = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_date format. Use ISO format.")

        # Get total PDF downloads from repository
        total = pdf_downloads_repository.get_total_pdf_downloads(db, from_datetime, to_datetime)

        return {
            "total_pdf_downloads": total or 0
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching total PDF downloads: {str(e)}"
        )


@router.get("/pdf-downloads-per-type")
def get_pdf_downloads_per_type(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    current_user=Depends(check_user_role(["super_admin", "org_admin"])),
    db: Session = Depends(get_db)
):
    """Get PDF downloads grouped by type with optional date filtering"""
    from datetime import datetime

    try:
        # Parse date strings if provided
        from_datetime = None
        to_datetime = None

        if from_date:
            try:
                from_datetime = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid from_date format. Use ISO format.")

        if to_date:
            try:
                to_datetime = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_date format. Use ISO format.")

        # Get downloads per type from repository
        downloads = pdf_downloads_repository.get_downloads_per_type(db, from_datetime, to_datetime)

        # Format response
        result = []
        for download in downloads:
            result.append({
                "pdf_type": download.pdf_type,
                "download_count": download.download_count
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching PDF downloads per type: {str(e)}"
        )