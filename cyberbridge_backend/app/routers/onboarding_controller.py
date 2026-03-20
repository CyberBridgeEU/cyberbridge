# routers/onboarding_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from ..repositories import user_repository
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"], responses={404: {"description": "Not found"}})


def is_admin_role(role_name: str) -> bool:
    """Check if the role is an admin role that should see the onboarding wizard"""
    admin_roles = ['org_admin', 'super_admin']
    return role_name.lower() in admin_roles


@router.get("/status", response_model=schemas.OnboardingStatusResponse)
def get_onboarding_status(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get the current user's onboarding status"""
    try:
        user = user_repository.get_user_full_profile(db, user_id=uuid.UUID(str(current_user.id)))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user is an admin
        is_admin = is_admin_role(user.get('role_name', ''))

        return schemas.OnboardingStatusResponse(
            onboarding_completed=user.get('onboarding_completed', False),
            onboarding_skipped=user.get('onboarding_skipped', False),
            onboarding_completed_at=user.get('onboarding_completed_at'),
            is_admin=is_admin
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching onboarding status: {str(e)}"
        )


@router.post("/complete", response_model=schemas.OnboardingCompleteResponse)
def complete_onboarding(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Mark the onboarding as completed for the current user"""
    try:
        user_id = uuid.UUID(str(current_user.id))
        completed_at = datetime.utcnow()

        # Update the user's onboarding status
        updated = user_repository.update_onboarding_status(
            db,
            user_id=user_id,
            onboarding_completed=True,
            onboarding_completed_at=completed_at,
            onboarding_skipped=False
        )

        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update onboarding status")

        return schemas.OnboardingCompleteResponse(
            success=True,
            message="Onboarding completed successfully",
            onboarding_completed_at=completed_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while completing onboarding: {str(e)}"
        )


@router.post("/skip", response_model=schemas.OnboardingSkipResponse)
def skip_onboarding(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Skip the onboarding wizard for the current user"""
    try:
        user_id = uuid.UUID(str(current_user.id))

        # Update the user's onboarding status to skipped
        updated = user_repository.update_onboarding_status(
            db,
            user_id=user_id,
            onboarding_completed=True,  # Mark as completed since they've "done" it
            onboarding_completed_at=datetime.utcnow(),
            onboarding_skipped=True
        )

        if not updated:
            raise HTTPException(status_code=500, detail="Failed to update onboarding status")

        return schemas.OnboardingSkipResponse(
            success=True,
            message="Onboarding skipped successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while skipping onboarding: {str(e)}"
        )


@router.post("/reset", response_model=schemas.OnboardingCompleteResponse)
def reset_onboarding(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Reset the onboarding status to allow re-running the wizard (for admin Quick Action)"""
    try:
        user_id = uuid.UUID(str(current_user.id))

        # Reset the user's onboarding status
        updated = user_repository.update_onboarding_status(
            db,
            user_id=user_id,
            onboarding_completed=False,
            onboarding_completed_at=None,
            onboarding_skipped=False
        )

        if not updated:
            raise HTTPException(status_code=500, detail="Failed to reset onboarding status")

        return schemas.OnboardingCompleteResponse(
            success=True,
            message="Onboarding reset successfully - wizard will appear on next page load",
            onboarding_completed_at=None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while resetting onboarding: {str(e)}"
        )
