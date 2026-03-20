from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging
import uuid

from app.database.database import get_db
from app.models import models
from app.services.auth_service import get_current_active_user
from app.services.llm_service import LLMService
from app.repositories import policy_aligner_repository
from app.dtos import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policy-aligner", tags=["Policy Aligner"])


@router.post("/align")
async def trigger_alignment(
    request: schemas.PolicyAlignmentRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Trigger AI policy alignment for a framework.
    This will analyze all policies and framework questions and create alignments.
    """
    try:
        framework_id = request.framework_id

        # Get the framework
        framework = db.query(models.Framework).filter(
            models.Framework.id == framework_id
        ).first()

        if not framework:
            raise HTTPException(status_code=404, detail="Framework not found")

        # Check permission - user must be super_admin, org_admin, or belong to the framework's org
        organisation_id = framework.organisation_id
        if current_user.role_name not in ['super_admin', 'org_admin']:
            if str(current_user.organisation_id) != str(organisation_id):
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to generate alignments for this framework"
                )

        # Check if global AI is enabled and AI Policy Aligner is enabled
        global_settings = db.query(models.LLMSettings).first()
        if not global_settings or not global_settings.ai_enabled:
            raise HTTPException(
                status_code=400,
                detail="AI features are globally disabled. Contact your administrator."
            )

        if not global_settings.ai_policy_aligner_enabled:
            raise HTTPException(
                status_code=400,
                detail="AI Policy Aligner is not enabled. Contact your administrator to enable it in System Settings."
            )

        # Get org settings for custom prompt (optional)
        org_settings = db.query(models.OrganizationLLMSettings).filter(
            models.OrganizationLLMSettings.organisation_id == organisation_id
        ).first()

        # Get policies for the organization
        policies = policy_aligner_repository.get_policies_for_organisation(db, organisation_id)
        if not policies:
            raise HTTPException(
                status_code=400,
                detail="No policies found for this organization. Create policies first."
            )

        # Get questions for the framework
        questions = policy_aligner_repository.get_framework_questions(db, framework_id)
        if not questions:
            raise HTTPException(
                status_code=400,
                detail="No questions found for this framework."
            )

        # Delete existing alignments for this framework (re-run)
        policy_aligner_repository.delete_alignments_for_framework(db, framework_id)

        # Generate alignments using LLM
        llm_service = LLMService(db)
        # Use org's provider if set (e.g. "llamacpp")
        if org_settings and getattr(org_settings, 'llm_provider', None) == 'llamacpp':
            llm_service.llm_backend = "llamacpp"
        custom_prompt = org_settings.policy_aligner_prompt

        logger.info(f"Generating policy alignments for framework {framework_id}")
        logger.info(f"Policies: {len(policies)}, Questions: {len(questions)}")

        alignments = await llm_service.generate_policy_alignments(
            policies=policies,
            questions=questions,
            custom_prompt=custom_prompt
        )

        if not alignments:
            return {
                "success": True,
                "alignments_created": 0,
                "message": "No alignments were generated. The AI could not find confident matches between policies and questions."
            }

        # Save alignments to database
        created_count = policy_aligner_repository.create_alignments_bulk(
            db=db,
            organisation_id=organisation_id,
            framework_id=framework_id,
            alignments=alignments
        )

        logger.info(f"Created {created_count} policy alignments for framework {framework_id}")

        return {
            "success": True,
            "alignments_created": created_count,
            "message": f"Successfully created {created_count} policy alignments"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating policy alignments: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate policy alignments: {str(e)}"
        )


@router.get("/alignments/{framework_id}")
async def get_alignments(
    framework_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get all policy-question alignments for a framework."""
    try:
        # Get the framework to verify it exists
        framework = db.query(models.Framework).filter(
            models.Framework.id == framework_id
        ).first()

        if not framework:
            raise HTTPException(status_code=404, detail="Framework not found")

        # Check permission
        if current_user.role_name != 'super_admin':
            if str(current_user.organisation_id) != str(framework.organisation_id):
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to view alignments for this framework"
                )

        alignments = policy_aligner_repository.get_alignments_for_framework_with_details(
            db, uuid.UUID(framework_id)
        )

        return alignments

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy alignments: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get policy alignments: {str(e)}"
        )


@router.delete("/alignments/{framework_id}")
async def delete_alignments(
    framework_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Delete all policy-question alignments for a framework."""
    try:
        # Get the framework to verify it exists
        framework = db.query(models.Framework).filter(
            models.Framework.id == framework_id
        ).first()

        if not framework:
            raise HTTPException(status_code=404, detail="Framework not found")

        # Check permission - only org_admin and super_admin can delete alignments
        if current_user.role_name not in ['super_admin', 'org_admin']:
            raise HTTPException(
                status_code=403,
                detail="Only administrators can delete alignments"
            )

        if current_user.role_name == 'org_admin':
            if str(current_user.organisation_id) != str(framework.organisation_id):
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to delete alignments for this framework"
                )

        deleted_count = policy_aligner_repository.delete_alignments_for_framework(
            db, uuid.UUID(framework_id)
        )

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Successfully deleted {deleted_count} alignments"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting policy alignments: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete policy alignments: {str(e)}"
        )


@router.get("/status/{framework_id}")
async def get_alignment_status(
    framework_id: str,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get the alignment status for a framework."""
    try:
        # Get the framework to verify it exists
        framework = db.query(models.Framework).filter(
            models.Framework.id == framework_id
        ).first()

        if not framework:
            raise HTTPException(status_code=404, detail="Framework not found")

        # Check permission
        if current_user.role_name != 'super_admin':
            if str(current_user.organisation_id) != str(framework.organisation_id):
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to view alignment status for this framework"
                )

        status = policy_aligner_repository.get_alignment_status(db, uuid.UUID(framework_id))

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alignment status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get alignment status: {str(e)}"
        )
