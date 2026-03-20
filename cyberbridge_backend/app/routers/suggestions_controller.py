# routers/suggestions_controller.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
import logging

from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user
from ..services.suggestion_service import SuggestionService
from ..repositories import assets_repository, risks_repository, control_repository, policy_repository, assessment_repository, answer_repository, scan_finding_repository
from ..models import models
from ..utils.cancellation import run_with_disconnect_check, register_task, unregister_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/suggestions", tags=["suggestions"], responses={404: {"description": "Not found"}})


def _build_response(suggestions: list, engine: str, entity_id: str) -> schemas.SuggestionResponse:
    return schemas.SuggestionResponse(
        suggestions=[schemas.SuggestionItem(**s) for s in suggestions],
        engine=engine,
        entity_id=entity_id,
        total_suggestions=len(suggestions),
    )


@router.post("/risks-for-asset", response_model=schemas.SuggestionResponse)
async def suggest_risks_for_asset(
    raw_request: Request,
    request: schemas.SuggestionRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Suggest risks for a given asset."""
    asset = assets_repository.get_asset(db, request.entity_id, current_user)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset_type = db.query(models.AssetTypes).filter(models.AssetTypes.id == asset.asset_type_id).first()
    asset_type_name = asset_type.name if asset_type else ""

    all_risks = risks_repository.get_risks(db, current_user, skip=0, limit=5000)
    available = [
        {
            "id": str(r.id),
            "risk_code": r.risk_code,
            "risk_category_name": r.risk_category_name,
            "risk_category_description": r.risk_category_description,
            "risk_potential_impact": r.risk_potential_impact,
            "risk_control": r.risk_control,
        }
        for r in all_risks
    ]

    if request.available_item_ids:
        id_set = set(request.available_item_ids)
        available = [r for r in available if r["id"] in id_set]

    svc = SuggestionService(db, current_user)
    try:
        if request.engine == "llm":
            suggestions = await run_with_disconnect_check(
                raw_request,
                svc.suggest_risks_for_asset_llm(
                    asset_name=asset.name,
                    asset_type_name=asset_type_name,
                    confidentiality=asset.confidentiality,
                    integrity=asset.integrity,
                    availability=asset.availability,
                    description=asset.description,
                    available_risks=available,
                ),
            )
        else:
            suggestions = svc.suggest_risks_for_asset_rules(
                asset_name=asset.name,
                asset_type_name=asset_type_name,
                confidentiality=asset.confidentiality,
                integrity=asset.integrity,
                availability=asset.availability,
                description=asset.description,
                available_risks=available,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Suggestion engine failed: {str(e)}")
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")

    return _build_response(suggestions, request.engine, request.entity_id)


@router.post("/controls-for-risk", response_model=schemas.SuggestionResponse)
async def suggest_controls_for_risk(
    raw_request: Request,
    request: schemas.SuggestionRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Suggest controls for a given risk."""
    risk = risks_repository.get_risk(db, request.entity_id, current_user)
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    all_controls = control_repository.get_controls(db, control_set_id=None, current_user=current_user, skip=0, limit=5000)
    available = [
        {
            "id": str(c.id),
            "code": c.code,
            "name": c.name,
            "description": c.description,
        }
        for c in all_controls
    ]

    if request.available_item_ids:
        id_set = set(request.available_item_ids)
        available = [c for c in available if c["id"] in id_set]

    svc = SuggestionService(db, current_user)
    try:
        if request.engine == "llm":
            suggestions = await run_with_disconnect_check(
                raw_request,
                svc.suggest_controls_for_risk_llm(
                    risk_name=risk.risk_category_name,
                    risk_description=risk.risk_category_description,
                    risk_impact=risk.risk_potential_impact,
                    risk_control=risk.risk_control,
                    available_controls=available,
                ),
            )
        else:
            suggestions = svc.suggest_controls_for_risk_rules(
                risk_name=risk.risk_category_name,
                risk_description=risk.risk_category_description,
                risk_impact=risk.risk_potential_impact,
                risk_control=risk.risk_control,
                available_controls=available,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Suggestion engine failed: {str(e)}")
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")

    return _build_response(suggestions, request.engine, request.entity_id)


@router.post("/policies-for-control", response_model=schemas.SuggestionResponse)
async def suggest_policies_for_control(
    raw_request: Request,
    request: schemas.SuggestionRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Suggest policies for a given control."""
    control = control_repository.get_control(db, request.entity_id, current_user)
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")

    all_policies = policy_repository.get_policies(db, current_user, skip=0, limit=5000)
    available = [
        {
            "id": str(p.id),
            "title": p.title,
            "policy_code": p.policy_code,
            "body": p.body,
        }
        for p in all_policies
    ]

    if request.available_item_ids:
        id_set = set(request.available_item_ids)
        available = [p for p in available if p["id"] in id_set]

    svc = SuggestionService(db, current_user)
    try:
        if request.engine == "llm":
            suggestions = await run_with_disconnect_check(
                raw_request,
                svc.suggest_policies_for_control_llm(
                    control_code=control.code,
                    control_name=control.name,
                    control_description=control.description,
                    available_policies=available,
                ),
            )
        else:
            suggestions = svc.suggest_policies_for_control_rules(
                control_code=control.code,
                control_name=control.name,
                control_description=control.description,
                available_policies=available,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Suggestion engine failed: {str(e)}")
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")

    return _build_response(suggestions, request.engine, request.entity_id)


@router.post("/objectives-for-policy", response_model=schemas.SuggestionResponse)
async def suggest_objectives_for_policy(
    raw_request: Request,
    request: schemas.SuggestionRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Suggest objectives for a given policy."""
    policy = policy_repository.get_policy(db, request.entity_id, current_user)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    if request.framework_id:
        chapters = db.query(models.Chapters).filter(models.Chapters.framework_id == request.framework_id).all()
        chapter_ids = [c.id for c in chapters]
        if chapter_ids:
            all_objectives = db.query(models.Objectives).filter(models.Objectives.chapter_id.in_(chapter_ids)).all()
        else:
            all_objectives = []
    else:
        all_objectives = db.query(models.Objectives).limit(5000).all()

    available = [
        {
            "id": str(o.id),
            "title": o.title,
            "requirement_description": o.requirement_description,
        }
        for o in all_objectives
    ]

    if request.available_item_ids:
        id_set = set(request.available_item_ids)
        available = [o for o in available if o["id"] in id_set]

    svc = SuggestionService(db, current_user)
    try:
        if request.engine == "llm":
            suggestions = await run_with_disconnect_check(
                raw_request,
                svc.suggest_objectives_for_policy_llm(
                    policy_title=policy.title,
                    policy_body=policy.body,
                    available_objectives=available,
                ),
            )
        else:
            suggestions = svc.suggest_objectives_for_policy_rules(
                policy_title=policy.title,
                policy_body=policy.body,
                available_objectives=available,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Suggestion engine failed: {str(e)}")
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")

    return _build_response(suggestions, request.engine, request.entity_id)


@router.post("/gather-platform-data")
async def gather_platform_data(
    request: schemas.AssessmentAnswerSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Gather all platform data for the data preview wizard without running the LLM."""
    import uuid as _uuid

    assessment = assessment_repository.get_assessment(db, _uuid.UUID(request.assessment_id))
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Count unanswered questions
    all_answers = answer_repository.fetch_answers_for_assessment(db, _uuid.UUID(request.assessment_id), current_user)
    all_unanswered = [
        a for a in all_answers
        if not a.get("answer_value") or a.get("answer_value", "").strip() == ""
    ]

    # If specific question IDs provided (page-based), count only those
    if request.question_ids:
        id_set = set(request.question_ids)
        unanswered_count = sum(1 for a in all_unanswered if str(a.get("question_id")) in id_set)
    else:
        unanswered_count = len(all_unanswered)

    org_id = current_user.organisation_id
    framework_id = assessment.framework_id
    user_id = current_user.id

    svc = SuggestionService(db, current_user)
    platform_data = svc._gather_all_platform_data(framework_id, org_id, user_id)

    return {
        "platform_data": platform_data,
        "unanswered_count": unanswered_count,
        "question_ids": request.question_ids,
        "assessment_id": request.assessment_id,
    }


@router.post("/answers-from-all-sources", response_model=schemas.AssessmentAnswerSuggestionResponse)
async def suggest_answers_from_all_sources(
    raw_request: Request,
    request: schemas.AssessmentAnswerSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Suggest assessment answers based on all platform data (scans, policies, objectives, evidence)."""
    import uuid as _uuid

    # 1. Fetch assessment
    assessment = assessment_repository.get_assessment(db, _uuid.UUID(request.assessment_id))
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # 2. Get answers and filter to unanswered
    all_answers = answer_repository.fetch_answers_for_assessment(db, _uuid.UUID(request.assessment_id), current_user)
    unanswered = [
        a for a in all_answers
        if not a.get("answer_value") or a.get("answer_value", "").strip() == ""
    ]

    # If specific question IDs provided (page-based), filter to only those
    if request.question_ids:
        id_set = set(request.question_ids)
        unanswered = [a for a in unanswered if str(a.get("question_id")) in id_set]

    if not unanswered:
        return schemas.AssessmentAnswerSuggestionResponse(
            suggestions=[],
            engine="llm",
            assessment_id=request.assessment_id,
            total_questions=0,
            total_suggestions=0,
        )

    # 3. Use pre-gathered platform data if provided, otherwise gather fresh
    svc = SuggestionService(db, current_user)
    if request.platform_data:
        platform_data = request.platform_data
    else:
        org_id = current_user.organisation_id
        framework_id = assessment.framework_id
        user_id = current_user.id
        platform_data = svc._gather_all_platform_data(framework_id, org_id, user_id)

    # 4. Call LLM engine with cancellation support
    import asyncio
    user_id = str(current_user.id)
    llm_coro = svc.suggest_answers_from_all_sources_llm(
        unanswered_questions=unanswered,
        platform_data=platform_data,
    )
    llm_task = asyncio.ensure_future(llm_coro)
    register_task(user_id, llm_task)
    try:
        suggestion_dicts = await llm_task
    except asyncio.CancelledError:
        return schemas.AssessmentAnswerSuggestionResponse(
            suggestions=[],
            engine="llm",
            assessment_id=request.assessment_id,
            total_questions=len(unanswered),
            total_suggestions=0,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI answer suggestion engine failed: {str(e)}")
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")
    finally:
        unregister_task(user_id)

    return schemas.AssessmentAnswerSuggestionResponse(
        suggestions=[schemas.AnswerSuggestionItem(**s) for s in suggestion_dicts],
        engine="llm",
        assessment_id=request.assessment_id,
        total_questions=len(unanswered),
        total_suggestions=len(suggestion_dicts),
    )


@router.post("/answers-from-scans", response_model=schemas.AssessmentAnswerSuggestionResponse)
async def suggest_answers_from_scans(
    raw_request: Request,
    request: schemas.AssessmentAnswerSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user),
):
    """Suggest assessment answers based on scan findings."""
    import uuid as _uuid

    # 1. Fetch assessment
    assessment = assessment_repository.get_assessment(db, _uuid.UUID(request.assessment_id))
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # 2. Get answers and filter to unanswered
    all_answers = answer_repository.fetch_answers_for_assessment(db, _uuid.UUID(request.assessment_id), current_user)
    unanswered = [
        a for a in all_answers
        if not a.get("answer_value") or a.get("answer_value", "").strip() == ""
    ]

    if not unanswered:
        return schemas.AssessmentAnswerSuggestionResponse(
            suggestions=[],
            engine=request.engine,
            assessment_id=request.assessment_id,
            total_questions=0,
            total_suggestions=0,
        )

    # 3. Get findings + stats for user's org
    org_id = current_user.organisation_id
    findings, stats = scan_finding_repository.get_findings_for_suggestion(db, org_id)

    if not findings:
        return schemas.AssessmentAnswerSuggestionResponse(
            suggestions=[],
            engine=request.engine,
            assessment_id=request.assessment_id,
            total_questions=len(unanswered),
            total_suggestions=0,
        )

    # 4. Call rule or LLM engine
    svc = SuggestionService(db, current_user)
    try:
        if request.engine == "llm":
            suggestion_dicts = await run_with_disconnect_check(
                raw_request,
                svc.suggest_answers_from_scans_llm(
                    unanswered_questions=unanswered,
                    findings_summary=stats,
                    all_findings=findings,
                ),
            )
        else:
            suggestion_dicts = svc.suggest_answers_from_scans_rules(
                unanswered_questions=unanswered,
                findings_summary=stats,
                all_findings=findings,
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Answer suggestion engine failed: {str(e)}")
        raise HTTPException(status_code=502, detail=f"LLM service error: {str(e)}")

    return schemas.AssessmentAnswerSuggestionResponse(
        suggestions=[schemas.AnswerSuggestionItem(**s) for s in suggestion_dicts],
        engine=request.engine,
        assessment_id=request.assessment_id,
        total_questions=len(unanswered),
        total_suggestions=len(suggestion_dicts),
    )
