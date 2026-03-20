# routers/assessments_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from ..dtos.schemas import OnlyIdInStringFormat
from ..repositories import assessment_repository, framework_repository, user_repository, answer_repository, assessment_type_repository, history_repository
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user

#protect all routes here by adding dependencies attribute to router APIRouter
# By using `Depends(get_current_active_user)`, you're ensuring that:
# 1. The JWT token is validated
# 2. The user is authenticated
# 3. The user is active
# 4. The route can only be accessed by authenticated users

router = APIRouter(prefix="/assessments",tags=["assessments"],responses={404: {"description": "Not found"}}, dependencies=[Depends(get_current_active_user)])

@router.post("/", response_model=schemas.AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(request: schemas.AssessmentCreateRequest, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Verify framework exists
        db_framework = framework_repository.get_framework(db, framework_id=uuid.UUID(request.framework_id))
        if not db_framework:
            raise HTTPException(status_code=404, detail="Framework not found")

        # Verify user exists
        db_user = user_repository.get_user(db, user_id=uuid.UUID(request.user_id))
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify assessment type exists
        db_assessment_type = assessment_type_repository.get_assessment_type(db, assessment_type_id=uuid.UUID(request.assessment_type_id))
        if not db_assessment_type:
            raise HTTPException(status_code=404, detail="Assessment type not found")

        # Convert request to AssessmentCreate
        assessment_create = schemas.AssessmentCreate(
            name=request.name,
            framework_id=uuid.UUID(request.framework_id),
            user_id=uuid.UUID(request.user_id),
            assessment_type_id=uuid.UUID(request.assessment_type_id)
        )

        # Extract scope parameters
        scope_name = request.scope_name
        # Handle None, empty string, or whitespace as None (for 'Other' scope type)
        scope_entity_id = None
        if request.scope_entity_id and str(request.scope_entity_id).strip():
            try:
                scope_entity_id = uuid.UUID(request.scope_entity_id)
            except (ValueError, AttributeError):
                scope_entity_id = None

        created_assessment = assessment_repository.create_assessment(
            db=db,
            assessment=assessment_create,
            scope_name=scope_name,
            scope_entity_id=scope_entity_id
        )

        # Enrich with scope display information
        from ..services import scope_validation_service
        if created_assessment.scope_id and created_assessment.scope_entity_id:
            scope_info = scope_validation_service.get_scope_info(
                db,
                created_assessment.scope_id,
                created_assessment.scope_entity_id
            )
            if scope_info:
                created_assessment.scope_name = scope_info['scope_name']
                created_assessment.scope_display_name = scope_info['entity_name']

        # Track the creation in history
        history_repository.track_insert(
            db=db,
            table_name="assessments",
            record_id=str(created_assessment.id),
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            new_data={
                "framework_id": str(created_assessment.framework_id),
                "user_id": str(created_assessment.user_id),
                "assessment_type_id": str(created_assessment.assessment_type_id),
                "framework_name": db_framework.name if db_framework else None
            }
        )

        #create all null answers for the questions of this assessment with specific assessment type
        answer_repository.create_answers_for_assessment(db=db, framework_id=uuid.UUID(request.framework_id), assessment_id=created_assessment.id, assessment_type_id=uuid.UUID(request.assessment_type_id))
        return created_assessment
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log the exception if you have logging configured
        # logger.error(f"Error creating assessment: {str(e)}")
        print(f"ERROR creating assessment: {str(e)}")
        import traceback
        traceback.print_exc()

        # Return a generic error message to the client
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"An error occurred while creating the assessment: {str(e)}")


@router.get("/", response_model=List[schemas.AssessmentResponse])
def read_assessments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assessments = assessment_repository.get_assessments(db, skip=skip, limit=limit)
    return assessments

@router.post("/assessments_for_framework_and_user", response_model=List[schemas.AssessmentResponse])
def get_assessments_for_framework(request: schemas.FrameworkAndUser, skip: int = 0, limit: int = 100,db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        assessments = assessment_repository.get_assessments_for_framework_and_user(db, request=request, current_user=current_user,skip=skip, limit=limit)
        return assessments
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {str(e)}")

@router.post("/assessments_for_framework_user_and_assessment_type", response_model=List[schemas.AssessmentResponse])
def get_assessments_for_framework_user_and_assessment_type(request: schemas.FrameworkUserAndAssessmentType, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        assessments = assessment_repository.get_assessments_for_framework_user_and_assessment_type(db, request=request, current_user=current_user, skip=skip, limit=limit)
        return assessments
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {str(e)}")

@router.post("/fetch_assessment_answers", response_model=List[schemas.AssessmentAnswersResponse])
def fetch_assessment_answers(request: schemas.AssessmentAnswersRequest, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        assessments = answer_repository.fetch_answers_for_assessment(db, assessment_id=uuid.UUID(request.assessment_id), current_user=current_user)
        return assessments
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {str(e)}")

@router.post("/delete_assessment_answers", response_model=schemas.AssessmentResponse)
def delete_assessment_answers(request: OnlyIdInStringFormat, db: Session = Depends(get_db)):
    print(f"DEBUG: delete_assessment_answers controller called with request.id={request.id}")
    try:
        db_assessment = answer_repository.delete_answers_for_assessment(db, assessment_id=uuid.UUID(request.id))
        return db_assessment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {str(e)}")


@router.get("/user/{user_id}", response_model=List[schemas.AssessmentWithFrameworkResponse])
def get_assessments_for_user(user_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    """Get all assessments for a specific user with framework and scope information"""
    try:
        # Verify user exists
        db_user = user_repository.get_user(db, user_id=user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        assessments = assessment_repository.get_assessments_for_user(db, user_id=user_id, current_user=current_user, skip=skip, limit=limit)
        return assessments
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {str(e)}")


@router.get("/{assessment_id}", response_model=schemas.AssessmentResponse)
def read_assessment(assessment_id: uuid.UUID, db: Session = Depends(get_db)):
    db_assessment = assessment_repository.get_assessment(db, assessment_id=assessment_id)
    if db_assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return db_assessment


@router.put("/{assessment_id}", response_model=schemas.AssessmentResponse)
def update_assessment(assessment_id: uuid.UUID, assessment: schemas.AssessmentCreate, db: Session = Depends(get_db)):
    try:
        db_assessment = assessment_repository.get_assessment(db, assessment_id=assessment_id)
        if db_assessment is None:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Update assessment attributes
        for key, value in assessment.model_dump().items():
            setattr(db_assessment, key, value)

        db.commit()
        db.refresh(db_assessment)
        return db_assessment
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                           detail=f"An error occurred while updating the assessment: {str(e)}")




@router.patch("/{assessment_id}/complete", response_model=schemas.AssessmentResponse)
def complete_assessment(assessment_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        db_assessment = assessment_repository.get_assessment(db, assessment_id=assessment_id)
        if db_assessment is None:
            raise HTTPException(status_code=404, detail="Assessment not found")

        db_assessment.completed_at = datetime.now()
        db.commit()
        db.refresh(db_assessment)
        return db_assessment
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                           detail=f"An error occurred while completing the assessment: {str(e)}")


@router.get("/{assessment_id}/answers", response_model=List[schemas.AnswerResponse])
def read_assessment_answers(assessment_id: uuid.UUID, db: Session = Depends(get_db)):
    db_assessment = assessment_repository.get_assessment(db, assessment_id=assessment_id)
    if db_assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    answers = assessment_repository.get_assessment_answers(db, assessment_id=assessment_id)
    return answers


@router.get("/{assessment_id}/evidence", response_model=List[schemas.EvidenceResponse])
def read_assessment_evidence(assessment_id: uuid.UUID, db: Session = Depends(get_db)):
    db_assessment = assessment_repository.get_assessment(db, assessment_id=assessment_id)
    if db_assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    evidence = assessment_repository.get_assessment_evidence(db, assessment_id=assessment_id)
    return evidence


# ===========================
# Assessment Reminder Endpoints
# ===========================

from ..services.auth_service import check_user_role
from ..services.notification_service import send_assessment_incomplete_reminder
import logging

logger = logging.getLogger(__name__)


@router.post("/send-incomplete-reminders")
def send_incomplete_assessment_reminders(
    days_threshold: int = 7,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))
):
    """
    Send email reminders to users with incomplete assessments.
    Only org_admin and super_admin can trigger reminders.
    org_admin can only send reminders to users in their organization.
    This endpoint can be called manually or via a scheduled task/cron job.
    """
    try:
        # Determine organisation filter based on role
        organisation_id = None
        if current_user.role_name == "org_admin":
            organisation_id = current_user.organisation_id

        # Get incomplete assessments
        incomplete_assessments = assessment_repository.get_incomplete_assessments_for_reminders(
            db=db,
            days_threshold=days_threshold,
            organisation_id=organisation_id
        )

        if not incomplete_assessments:
            return {
                "success": True,
                "message": "No incomplete assessments found that need reminders",
                "reminders_sent": 0
            }

        # Send reminders
        sent_count = 0
        failed_count = 0
        reminder_details = []

        for assessment in incomplete_assessments:
            try:
                success = send_assessment_incomplete_reminder(
                    db=db,
                    user_id=assessment["user_id"],
                    user_email=assessment["user_email"],
                    assessment_name=assessment["assessment_name"],
                    framework_name=assessment["framework_name"],
                    days_incomplete=assessment["days_incomplete"],
                    progress_percentage=assessment["progress_percentage"]
                )

                if success:
                    sent_count += 1
                    reminder_details.append({
                        "user_email": assessment["user_email"],
                        "assessment_name": assessment["assessment_name"],
                        "status": "sent"
                    })
                else:
                    # User may have disabled notifications
                    reminder_details.append({
                        "user_email": assessment["user_email"],
                        "assessment_name": assessment["assessment_name"],
                        "status": "skipped (notifications disabled)"
                    })

            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send reminder for assessment {assessment['assessment_id']}: {str(e)}")
                reminder_details.append({
                    "user_email": assessment["user_email"],
                    "assessment_name": assessment["assessment_name"],
                    "status": f"failed: {str(e)}"
                })

        return {
            "success": True,
            "message": f"Processed {len(incomplete_assessments)} incomplete assessments",
            "reminders_sent": sent_count,
            "reminders_failed": failed_count,
            "details": reminder_details
        }

    except Exception as e:
        logger.error(f"Error sending assessment reminders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while sending reminders: {str(e)}"
        )


@router.get("/incomplete-assessments")
def get_incomplete_assessments(
    days_threshold: int = 7,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(check_user_role(["super_admin", "org_admin"]))
):
    """
    Get a list of incomplete assessments that would receive reminders.
    Useful for previewing before sending reminders.
    """
    try:
        # Determine organisation filter based on role
        organisation_id = None
        if current_user.role_name == "org_admin":
            organisation_id = current_user.organisation_id

        incomplete_assessments = assessment_repository.get_incomplete_assessments_for_reminders(
            db=db,
            days_threshold=days_threshold,
            organisation_id=organisation_id
        )

        return {
            "success": True,
            "count": len(incomplete_assessments),
            "days_threshold": days_threshold,
            "assessments": incomplete_assessments
        }

    except Exception as e:
        logger.error(f"Error fetching incomplete assessments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching incomplete assessments: {str(e)}"
        )
