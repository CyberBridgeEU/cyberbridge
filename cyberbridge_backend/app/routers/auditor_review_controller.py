# routers/auditor_review_controller.py
"""
Auditor review endpoints for the Audit Engagement Workspace.
Provides read-only and limited write access for authenticated auditors.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import logging

from ..dtos import schemas
from ..database.database import get_db
from ..services import auditor_auth_service
from ..models import models
from ..repositories import audit_notification_repository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auditor/review",
    tags=["auditor-review"],
    responses={404: {"description": "Not found"}}
)


# Dependency to get current auditor from token
async def get_current_auditor(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
) -> dict:
    """Extract and verify auditor from JWT token."""
    try:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization

        success, payload, error_message = auditor_auth_service.verify_auditor_token(token)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message,
                headers={"WWW-Authenticate": "Bearer"}
            )

        return payload

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying auditor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication",
            headers={"WWW-Authenticate": "Bearer"}
        )


# Response Models
class EngagementOverview(schemas.BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    assessment_name: str
    framework_name: str
    audit_period_start: Optional[str]
    audit_period_end: Optional[str]
    organisation_name: str
    total_controls: int
    answered_controls: int
    completion_percentage: int


class ControlItem(schemas.BaseModel):
    id: str
    question_text: str
    question_description: Optional[str]
    answer_value: Optional[str]
    evidence_description: Optional[str]
    is_mandatory: bool
    has_evidence: bool
    evidence_count: int
    comment_count: int
    policy_title: Optional[str]


class EvidenceItem(schemas.BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    uploaded_at: str
    answer_id: str
    question_text: str


class ReviewQueueItem(schemas.BaseModel):
    id: str
    item_type: str  # control, policy, evidence
    item_id: str
    title: str
    description: Optional[str]
    status: str
    priority: str


# Endpoints

@router.get("/engagement", response_model=EngagementOverview)
def get_engagement_overview(
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Get overview of the engagement the auditor has access to."""
    try:
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))

        engagement = db.query(models.AuditEngagement).filter(
            models.AuditEngagement.id == engagement_id
        ).first()

        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")

        # Get assessment details
        assessment = db.query(models.Assessment).filter(
            models.Assessment.id == engagement.assessment_id
        ).first()

        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Get framework name
        framework = db.query(models.Framework).filter(
            models.Framework.id == assessment.framework_id
        ).first()

        # Get organisation name
        organisation = db.query(models.Organisations).filter(
            models.Organisations.id == engagement.organisation_id
        ).first()

        # Calculate control completion
        total_answers = db.query(models.Answer).filter(
            models.Answer.assessment_id == assessment.id
        ).count()

        answered_count = db.query(models.Answer).filter(
            models.Answer.assessment_id == assessment.id,
            models.Answer.value.isnot(None),
            models.Answer.value != ''
        ).count()

        completion_pct = int((answered_count / total_answers * 100)) if total_answers > 0 else 0

        return EngagementOverview(
            id=str(engagement.id),
            name=engagement.name,
            description=engagement.description,
            status=engagement.status,
            assessment_name=assessment.name,
            framework_name=framework.name if framework else "Unknown",
            audit_period_start=engagement.audit_period_start.isoformat() if engagement.audit_period_start else None,
            audit_period_end=engagement.audit_period_end.isoformat() if engagement.audit_period_end else None,
            organisation_name=organisation.name if organisation else "Unknown",
            total_controls=total_answers,
            answered_controls=answered_count,
            completion_percentage=completion_pct
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting engagement overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching engagement overview"
        )


@router.get("/controls", response_model=List[ControlItem])
def get_in_scope_controls(
    filter_answered: Optional[bool] = None,
    filter_mandatory: Optional[bool] = None,
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Get all controls (questions/answers) in scope for the engagement."""
    try:
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))

        engagement = db.query(models.AuditEngagement).filter(
            models.AuditEngagement.id == engagement_id
        ).first()

        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")

        # Get answers for the assessment
        answers_query = db.query(
            models.Answer,
            models.Question
        ).join(
            models.Question, models.Answer.question_id == models.Question.id
        ).filter(
            models.Answer.assessment_id == engagement.assessment_id
        )

        # Apply filters
        if filter_answered is not None:
            if filter_answered:
                answers_query = answers_query.filter(
                    models.Answer.value.isnot(None),
                    models.Answer.value != ''
                )
            else:
                answers_query = answers_query.filter(
                    (models.Answer.value.is_(None)) | (models.Answer.value == '')
                )

        if filter_mandatory is not None:
            answers_query = answers_query.filter(
                models.Question.mandatory == filter_mandatory
            )

        results = answers_query.all()

        controls = []
        for answer, question in results:
            # Count evidence for this answer
            evidence_count = db.query(models.Evidence).filter(
                models.Evidence.answer_id == answer.id
            ).count()

            # Count comments for this answer
            comment_count = db.query(models.AuditComment).filter(
                models.AuditComment.engagement_id == engagement_id,
                models.AuditComment.target_type == 'answer',
                models.AuditComment.target_id == answer.id
            ).count()

            # Get policy title if linked
            policy_title = None
            if answer.policy_id:
                policy = db.query(models.Policies).filter(
                    models.Policies.id == answer.policy_id
                ).first()
                policy_title = policy.title if policy else None

            controls.append(ControlItem(
                id=str(answer.id),
                question_text=question.text,
                question_description=question.description,
                answer_value=answer.value,
                evidence_description=answer.evidence_description,
                is_mandatory=question.mandatory,
                has_evidence=evidence_count > 0,
                evidence_count=evidence_count,
                comment_count=comment_count,
                policy_title=policy_title
            ))

        return controls

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting controls: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching controls"
        )


@router.get("/evidence", response_model=List[EvidenceItem])
def get_evidence_list(
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Get all evidence files for the engagement."""
    try:
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))

        engagement = db.query(models.AuditEngagement).filter(
            models.AuditEngagement.id == engagement_id
        ).first()

        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")

        # Get all evidence for answers in this assessment
        evidence_list = db.query(
            models.Evidence,
            models.Answer,
            models.Question
        ).join(
            models.Answer, models.Evidence.answer_id == models.Answer.id
        ).join(
            models.Question, models.Answer.question_id == models.Question.id
        ).filter(
            models.Answer.assessment_id == engagement.assessment_id
        ).all()

        items = []
        for evidence, answer, question in evidence_list:
            items.append(EvidenceItem(
                id=str(evidence.id),
                filename=evidence.filename,
                file_type=evidence.file_type,
                file_size=evidence.file_size,
                uploaded_at=evidence.uploaded_at.isoformat() if evidence.uploaded_at else "",
                answer_id=str(answer.id),
                question_text=question.text
            ))

        return items

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evidence: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching evidence"
        )


@router.get("/evidence/{evidence_id}/preview")
def preview_evidence(
    evidence_id: uuid.UUID,
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """
    Get evidence file for in-browser preview.
    Returns file path and metadata. Actual file serving handled separately.
    """
    try:
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))

        # Verify evidence belongs to this engagement
        evidence = db.query(models.Evidence).filter(
            models.Evidence.id == evidence_id
        ).first()

        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")

        # Verify the evidence is linked to this engagement's assessment
        answer = db.query(models.Answer).filter(
            models.Answer.id == evidence.answer_id
        ).first()

        if not answer:
            raise HTTPException(status_code=404, detail="Answer not found")

        engagement = db.query(models.AuditEngagement).filter(
            models.AuditEngagement.id == engagement_id
        ).first()

        if not engagement or answer.assessment_id != engagement.assessment_id:
            raise HTTPException(status_code=403, detail="Access denied to this evidence")

        return {
            "id": str(evidence.id),
            "filename": evidence.filename,
            "file_type": evidence.file_type,
            "file_size": evidence.file_size,
            "filepath": evidence.filepath,
            "can_preview": evidence.file_type.lower() in ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'txt'],
            "watermark_required": current_auditor.get("watermark_downloads", True)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing evidence: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while accessing evidence"
        )


@router.get("/policies")
def get_policies(
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Get policies linked to the engagement's framework."""
    try:
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))
        organisation_id = uuid.UUID(current_auditor.get("organisation_id"))

        engagement = db.query(models.AuditEngagement).filter(
            models.AuditEngagement.id == engagement_id
        ).first()

        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")

        # Get assessment to find framework
        assessment = db.query(models.Assessment).filter(
            models.Assessment.id == engagement.assessment_id
        ).first()

        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Get policies linked to this framework
        policies = db.query(models.Policies).join(
            models.PolicyFrameworks, models.Policies.id == models.PolicyFrameworks.policy_id
        ).filter(
            models.PolicyFrameworks.framework_id == assessment.framework_id,
            models.Policies.organisation_id == organisation_id
        ).all()

        result = []
        for policy in policies:
            # Get status name
            status_obj = db.query(models.PolicyStatuses).filter(
                models.PolicyStatuses.id == policy.status_id
            ).first()

            result.append({
                "id": str(policy.id),
                "title": policy.title,
                "owner": policy.owner,
                "status": status_obj.status if status_obj else "Unknown",
                "body_preview": policy.body[:200] + "..." if policy.body and len(policy.body) > 200 else policy.body,
                "created_at": policy.created_at.isoformat() if policy.created_at else None,
                "updated_at": policy.updated_at.isoformat() if policy.updated_at else None
            })

        return {"policies": result, "total_count": len(result)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching policies"
        )


@router.get("/objectives")
def get_objectives(
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Get objectives/chapters for the engagement's framework."""
    try:
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))

        engagement = db.query(models.AuditEngagement).filter(
            models.AuditEngagement.id == engagement_id
        ).first()

        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")

        # Get assessment to find framework
        assessment = db.query(models.Assessment).filter(
            models.Assessment.id == engagement.assessment_id
        ).first()

        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Get chapters and objectives for this framework
        chapters = db.query(models.Chapters).filter(
            models.Chapters.framework_id == assessment.framework_id
        ).order_by(models.Chapters.title).all()

        result = []
        for chapter in chapters:
            objectives = db.query(models.Objectives).filter(
                models.Objectives.chapter_id == chapter.id
            ).all()

            chapter_data = {
                "id": str(chapter.id),
                "title": chapter.title,
                "objectives": []
            }

            for obj in objectives:
                # Get compliance status
                status_name = None
                if obj.compliance_status_id:
                    status_obj = db.query(models.ComplianceStatuses).filter(
                        models.ComplianceStatuses.id == obj.compliance_status_id
                    ).first()
                    status_name = status_obj.status_name if status_obj else None

                chapter_data["objectives"].append({
                    "id": str(obj.id),
                    "title": obj.title,
                    "subchapter": obj.subchapter,
                    "requirement_description": obj.requirement_description,
                    "compliance_status": status_name
                })

            result.append(chapter_data)

        return {"chapters": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting objectives: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching objectives"
        )


@router.get("/queue", response_model=List[ReviewQueueItem])
def get_review_queue(
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """
    Get a prioritized review queue for the auditor.
    Returns items that need attention (unanswered controls, missing evidence, etc.)
    """
    try:
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))

        engagement = db.query(models.AuditEngagement).filter(
            models.AuditEngagement.id == engagement_id
        ).first()

        if not engagement:
            raise HTTPException(status_code=404, detail="Engagement not found")

        queue_items = []

        # Add unanswered mandatory controls
        unanswered_mandatory = db.query(
            models.Answer, models.Question
        ).join(
            models.Question, models.Answer.question_id == models.Question.id
        ).filter(
            models.Answer.assessment_id == engagement.assessment_id,
            models.Question.mandatory == True,
            (models.Answer.value.is_(None)) | (models.Answer.value == '')
        ).all()

        for answer, question in unanswered_mandatory:
            queue_items.append(ReviewQueueItem(
                id=str(uuid.uuid4()),
                item_type="control",
                item_id=str(answer.id),
                title=question.text[:100] + "..." if len(question.text) > 100 else question.text,
                description="Mandatory control not answered",
                status="pending",
                priority="high"
            ))

        # Add controls without evidence
        answers_without_evidence = db.query(
            models.Answer, models.Question
        ).join(
            models.Question, models.Answer.question_id == models.Question.id
        ).outerjoin(
            models.Evidence, models.Answer.id == models.Evidence.answer_id
        ).filter(
            models.Answer.assessment_id == engagement.assessment_id,
            models.Answer.value.isnot(None),
            models.Answer.value != '',
            models.Evidence.id.is_(None)
        ).limit(20).all()

        for answer, question in answers_without_evidence:
            queue_items.append(ReviewQueueItem(
                id=str(uuid.uuid4()),
                item_type="control",
                item_id=str(answer.id),
                title=question.text[:100] + "..." if len(question.text) > 100 else question.text,
                description="Control answered but no evidence attached",
                status="needs_evidence",
                priority="medium"
            ))

        return queue_items

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review queue: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while building review queue"
        )


# ===========================
# Comment Endpoints for Auditors
# ===========================

class AuditorCommentCreate(schemas.BaseModel):
    target_type: str  # answer, evidence, objective, policy
    target_id: str
    content: str
    comment_type: str = "observation"  # question, evidence_request, observation, potential_exception


class AuditorCommentResponse(schemas.BaseModel):
    id: str
    target_type: str
    target_id: str
    content: str
    comment_type: str
    status: str
    author_name: str
    author_type: str
    created_at: str
    reply_count: int


@router.get("/comments")
def get_auditor_comments(
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Get comments for the engagement, optionally filtered by target."""
    try:
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))
        # The invitation_id is stored in 'sub' field of the JWT
        invitation_id = uuid.UUID(current_auditor.get("sub"))

        # Build query for comments
        query = db.query(models.AuditComment).filter(
            models.AuditComment.engagement_id == engagement_id
        )

        if target_type:
            query = query.filter(models.AuditComment.target_type == target_type)

        if target_id:
            query = query.filter(models.AuditComment.target_id == uuid.UUID(target_id))

        # Only get root comments (not replies)
        query = query.filter(models.AuditComment.parent_comment_id.is_(None))
        query = query.order_by(models.AuditComment.created_at.desc())

        comments = query.all()

        result = []
        for comment in comments:
            # Get author name
            author_name = "Unknown"
            author_type = "user"

            if comment.author_auditor_id:
                invitation = db.query(models.AuditorInvitation).filter(
                    models.AuditorInvitation.id == comment.author_auditor_id
                ).first()
                if invitation:
                    author_name = invitation.name or invitation.email
                    author_type = "auditor"
            elif comment.author_user_id:
                user = db.query(models.User).filter(
                    models.User.id == comment.author_user_id
                ).first()
                if user:
                    author_name = user.name or user.email
                    author_type = "user"

            # Get replies for this comment
            replies_query = db.query(models.AuditComment).filter(
                models.AuditComment.parent_comment_id == comment.id
            ).order_by(models.AuditComment.created_at.asc())
            replies = replies_query.all()

            reply_list = []
            for reply in replies:
                reply_author_name = "Unknown"
                reply_author_type = "user"

                if reply.author_auditor_id:
                    reply_inv = db.query(models.AuditorInvitation).filter(
                        models.AuditorInvitation.id == reply.author_auditor_id
                    ).first()
                    if reply_inv:
                        reply_author_name = reply_inv.name or reply_inv.email
                        reply_author_type = "auditor"
                elif reply.author_user_id:
                    reply_user = db.query(models.User).filter(
                        models.User.id == reply.author_user_id
                    ).first()
                    if reply_user:
                        reply_author_name = reply_user.name or reply_user.email
                        reply_author_type = "user"

                reply_list.append({
                    "id": str(reply.id),
                    "target_type": reply.target_type,
                    "target_id": str(reply.target_id),
                    "content": reply.content,
                    "comment_type": reply.comment_type,
                    "status": reply.status,
                    "author_name": reply_author_name,
                    "author_type": reply_author_type,
                    "created_at": reply.created_at.isoformat() if reply.created_at else None,
                    "reply_count": 0
                })

            result.append({
                "id": str(comment.id),
                "target_type": comment.target_type,
                "target_id": str(comment.target_id),
                "content": comment.content,
                "comment_type": comment.comment_type,
                "status": comment.status,
                "author_name": author_name,
                "author_type": author_type,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
                "reply_count": len(replies),
                "replies": reply_list
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting auditor comments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching comments"
        )


@router.post("/comments", status_code=status.HTTP_201_CREATED)
def create_auditor_comment(
    request: AuditorCommentCreate,
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Create a new comment as an auditor."""
    try:
        # Check if auditor has permission to comment
        can_comment = current_auditor.get("can_comment", False)
        if not can_comment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to add comments"
            )

        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))
        # The invitation_id is stored in 'sub' field of the JWT
        invitation_id = uuid.UUID(current_auditor.get("sub"))

        # Validate target_type
        valid_target_types = ["answer", "evidence", "objective", "policy"]
        if request.target_type not in valid_target_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target_type. Must be one of: {valid_target_types}"
            )

        # Validate comment_type
        valid_comment_types = ["question", "evidence_request", "observation", "potential_exception"]
        if request.comment_type not in valid_comment_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid comment_type. Must be one of: {valid_comment_types}"
            )

        # Create the comment
        comment = models.AuditComment(
            id=uuid.uuid4(),
            engagement_id=engagement_id,
            target_type=request.target_type,
            target_id=uuid.UUID(request.target_id),
            content=request.content,
            comment_type=request.comment_type,
            status="open",
            author_auditor_id=invitation_id
        )

        db.add(comment)
        db.commit()
        db.refresh(comment)

        # Get auditor name for response
        invitation = db.query(models.AuditorInvitation).filter(
            models.AuditorInvitation.id == invitation_id
        ).first()
        author_name = invitation.name or invitation.email if invitation else "Unknown"

        # Get the engagement for notifications
        engagement = db.query(models.AuditEngagement).filter(
            models.AuditEngagement.id == engagement_id
        ).first()

        # Create notifications for org users
        if engagement:
            try:
                audit_notification_repository.notify_users_of_new_comment(
                    db=db,
                    comment=comment,
                    engagement=engagement,
                    sender_name=author_name
                )
            except Exception as e:
                logger.error(f"Failed to create notifications: {e}")

        # Update review status if this is a comment on an answer (control)
        if request.target_type == "answer":
            try:
                target_id = uuid.UUID(request.target_id)
                # If auditor is asking a question or requesting evidence, set to "information_requested"
                if request.comment_type in ["question", "evidence_request"]:
                    audit_notification_repository.update_review_status(
                        db=db,
                        engagement_id=engagement_id,
                        answer_id=target_id,
                        new_status="information_requested",
                        updated_by_auditor_id=invitation_id,
                        status_note=f"Information requested by {author_name}"
                    )
                else:
                    # Just update to pending_review if not already in a more advanced state
                    current_status = audit_notification_repository.get_review_status(
                        db, engagement_id, target_id
                    )
                    if not current_status or current_status.status == "not_started":
                        audit_notification_repository.update_review_status(
                            db=db,
                            engagement_id=engagement_id,
                            answer_id=target_id,
                            new_status="pending_review",
                            updated_by_auditor_id=invitation_id,
                            status_note=f"Review started by {author_name}"
                        )
            except Exception as e:
                logger.error(f"Failed to update review status: {e}")

        return {
            "id": str(comment.id),
            "target_type": comment.target_type,
            "target_id": str(comment.target_id),
            "content": comment.content,
            "comment_type": comment.comment_type,
            "status": comment.status,
            "author_name": author_name,
            "author_type": "auditor",
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
            "reply_count": 0
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating auditor comment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating comment"
        )


# ===========================
# Auditor Notification Endpoints
# ===========================

@router.get("/notifications")
def get_auditor_notifications(
    unread_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Get notifications for the current auditor."""
    try:
        invitation_id = uuid.UUID(current_auditor.get("sub"))
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))

        notifications = audit_notification_repository.get_notifications_for_auditor(
            db=db,
            auditor_id=invitation_id,
            engagement_id=engagement_id,
            unread_only=unread_only,
            skip=skip,
            limit=limit
        )

        unread_count = audit_notification_repository.get_unread_count_for_auditor(
            db=db,
            auditor_id=invitation_id,
            engagement_id=engagement_id
        )

        # Enrich notifications with sender names
        notification_responses = []
        for n in notifications:
            sender_name = None
            if n.sender_user_id:
                sender = db.query(models.User).filter(models.User.id == n.sender_user_id).first()
                sender_name = sender.name if sender else None
            elif n.sender_auditor_id:
                auditor = db.query(models.AuditorInvitation).filter(models.AuditorInvitation.id == n.sender_auditor_id).first()
                sender_name = auditor.name if auditor else "Auditor"

            notification_responses.append({
                "id": str(n.id),
                "engagement_id": str(n.engagement_id),
                "notification_type": n.notification_type,
                "source_type": n.source_type,
                "source_id": str(n.source_id),
                "related_answer_id": str(n.related_answer_id) if n.related_answer_id else None,
                "title": n.title,
                "message": n.message,
                "sender_name": sender_name,
                "is_read": n.is_read,
                "read_at": n.read_at.isoformat() if n.read_at else None,
                "created_at": n.created_at.isoformat() if n.created_at else None
            })

        return {
            "notifications": notification_responses,
            "unread_count": unread_count,
            "total_count": len(notification_responses)
        }

    except Exception as e:
        logger.error(f"Error fetching auditor notifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching notifications"
        )


@router.get("/notifications/count")
def get_auditor_unread_count(
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Get unread notification count for the current auditor."""
    try:
        invitation_id = uuid.UUID(current_auditor.get("sub"))
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))

        count = audit_notification_repository.get_unread_count_for_auditor(
            db=db,
            auditor_id=invitation_id,
            engagement_id=engagement_id
        )
        return {"unread_count": count}

    except Exception as e:
        logger.error(f"Error fetching notification count: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching notification count"
        )


@router.post("/notifications/mark-read")
def mark_auditor_notifications_read(
    notification_ids: Optional[List[str]] = None,
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Mark notifications as read for the auditor."""
    try:
        invitation_id = uuid.UUID(current_auditor.get("sub"))
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))

        if notification_ids:
            count = 0
            for nid in notification_ids:
                notification = audit_notification_repository.mark_notification_as_read(db, uuid.UUID(nid))
                if notification and notification.recipient_auditor_id == invitation_id:
                    count += 1
            return {"success": True, "marked_read": count}
        else:
            count = audit_notification_repository.mark_all_notifications_as_read_for_auditor(
                db=db,
                auditor_id=invitation_id,
                engagement_id=engagement_id
            )
            return {"success": True, "marked_read": count}

    except Exception as e:
        logger.error(f"Error marking notifications as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while marking notifications as read"
        )


# ===========================
# Auditor Review Status Endpoints
# ===========================

@router.get("/controls/{answer_id}/review-status")
def get_control_review_status_for_auditor(
    answer_id: uuid.UUID,
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Get the review status for a specific control."""
    try:
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))

        status_record = audit_notification_repository.get_or_create_review_status(
            db, engagement_id, answer_id
        )

        # Get last updated by name
        last_updated_by_name = None
        if status_record.last_updated_by_user_id:
            user = db.query(models.User).filter(models.User.id == status_record.last_updated_by_user_id).first()
            last_updated_by_name = user.name if user else None
        elif status_record.last_updated_by_auditor_id:
            auditor = db.query(models.AuditorInvitation).filter(models.AuditorInvitation.id == status_record.last_updated_by_auditor_id).first()
            last_updated_by_name = auditor.name if auditor else "Auditor"

        return {
            "id": str(status_record.id),
            "engagement_id": str(status_record.engagement_id),
            "answer_id": str(status_record.answer_id),
            "status": status_record.status,
            "status_note": status_record.status_note,
            "last_updated_by_name": last_updated_by_name,
            "created_at": status_record.created_at.isoformat() if status_record.created_at else None,
            "updated_at": status_record.updated_at.isoformat() if status_record.updated_at else None
        }

    except Exception as e:
        logger.error(f"Error fetching review status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching review status"
        )


class ReviewStatusUpdate(schemas.BaseModel):
    status: str
    status_note: Optional[str] = None


@router.put("/controls/{answer_id}/review-status")
def update_control_review_status_for_auditor(
    answer_id: uuid.UUID,
    request: ReviewStatusUpdate,
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Update the review status for a control as an auditor."""
    try:
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))
        invitation_id = uuid.UUID(current_auditor.get("sub"))

        # Validate status
        valid_statuses = [
            "not_started", "pending_review", "information_requested", "response_provided",
            "in_review", "approved", "approved_with_exceptions", "needs_remediation"
        ]
        if request.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {valid_statuses}"
            )

        # Get auditor name
        invitation = db.query(models.AuditorInvitation).filter(
            models.AuditorInvitation.id == invitation_id
        ).first()
        auditor_name = invitation.name or invitation.email if invitation else "Auditor"

        # Get old status for notification
        old_status_record = audit_notification_repository.get_review_status(db, engagement_id, answer_id)
        old_status = old_status_record.status if old_status_record else "not_started"

        # Update status
        status_record = audit_notification_repository.update_review_status(
            db=db,
            engagement_id=engagement_id,
            answer_id=answer_id,
            new_status=request.status,
            updated_by_auditor_id=invitation_id,
            status_note=request.status_note
        )

        # Create notification for status change
        if old_status != request.status:
            engagement = db.query(models.AuditEngagement).filter(
                models.AuditEngagement.id == engagement_id
            ).first()
            if engagement:
                audit_notification_repository.notify_status_change(
                    db=db,
                    engagement=engagement,
                    answer_id=answer_id,
                    old_status=old_status,
                    new_status=request.status,
                    changed_by_auditor_id=invitation_id,
                    changer_name=auditor_name
                )

        return {
            "id": str(status_record.id),
            "engagement_id": str(status_record.engagement_id),
            "answer_id": str(status_record.answer_id),
            "status": status_record.status,
            "status_note": status_record.status_note,
            "last_updated_by_name": auditor_name,
            "created_at": status_record.created_at.isoformat() if status_record.created_at else None,
            "updated_at": status_record.updated_at.isoformat() if status_record.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating review status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating review status"
        )


@router.get("/review-status/summary")
def get_review_status_summary_for_auditor(
    current_auditor: dict = Depends(get_current_auditor),
    db: Session = Depends(get_db)
):
    """Get summary of review statuses for the engagement."""
    try:
        engagement_id = uuid.UUID(current_auditor.get("engagement_id"))

        counts = audit_notification_repository.get_review_status_counts(db, engagement_id)
        return counts

    except Exception as e:
        logger.error(f"Error fetching review status summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching review status summary"
        )
