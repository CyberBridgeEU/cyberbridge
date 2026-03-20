# routers/answers_controller.py
import os
import shutil
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from fastapi.responses import StreamingResponse
from starlette.responses import FileResponse

from ..dtos.schemas import OnlyIdInStringFormat, OnlyIdsInStringFormat
from ..repositories import answer_repository, policy_repository
from ..dtos import schemas
from .. import models
from ..database.database import get_db
from ..services.auth_service import get_current_active_user
from ..services.question_correlation_service import synchronize_correlated_answers

router = APIRouter(prefix="/answers",tags=["answers"],responses={404: {"description": "Not found"}},)

@router.post("/", response_model=schemas.AnswerResponse, status_code=status.HTTP_201_CREATED)
def create_answer(answer: schemas.AnswerCreate, db: Session = Depends(get_db)):
    try:
        # Verify assessment exists
        db_assessment = answer_repository.get_assessment(db, assessment_id=answer.assessment_id)
        if not db_assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Verify question exists
        db_question = answer_repository.get_question(db, question_id=answer.question_id)
        if not db_question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Check if answer already exists (to update instead of create)
        existing_answer = db.query(models.Answer).filter(
            models.Answer.assessment_id == answer.assessment_id,
            models.Answer.question_id == answer.question_id
        ).first()

        if existing_answer:
            # Update existing answer
            for key, value in answer.model_dump().items():
                setattr(existing_answer, key, value)
            db.commit()
            db.refresh(existing_answer)

            # Trigger synchronization for correlated questions
            try:
                synchronize_correlated_answers(db, existing_answer)
            except Exception as sync_error:
                logger.error(f"Error synchronizing correlated answers: {str(sync_error)}")
                # Don't fail the main operation if synchronization fails

            return existing_answer

        # Create new answer
        new_answer = answer_repository.create_answer(db=db, answer=answer)

        # Trigger synchronization for correlated questions
        try:
            synchronize_correlated_answers(db, new_answer)
        except Exception as sync_error:
            logger.error(f"Error synchronizing correlated answers: {str(sync_error)}")
            # Don't fail the main operation if synchronization fails

        return new_answer
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                           detail=f"An error occurred while creating the answer: {str(e)}")

@router.post("/update_answer", response_model=schemas.AnswerResponse)
def update_answer(answer_id: str = Form(...), answer_value: Optional[str] = Form(None), evidence_description: Optional[str] = Form(None), policy_id: Optional[str] = Form(None), files: List[UploadFile] = File(None), db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Validate policy_id belongs to user's organization if provided
        if policy_id and policy_id.strip() != "":
            policy = policy_repository.get_policy(db, uuid.UUID(policy_id), current_user)
            if not policy:
                raise HTTPException(status_code=403, detail="Policy not found or does not belong to your organization")

        request = schemas.UpdateAnswerRequest(answer_id=answer_id, answer_value=answer_value, evidence_description=evidence_description, policy_id=policy_id)
        db_answer = answer_repository.update_answer(answer=request, db=db)
        if files and any(file.filename for file in files):
            answer_repository.delete_existing_evidences(db=db, answer_id=db_answer.id)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            evidence_directory = os.path.join(project_root, "uploads", str(db_answer.id))
            os.makedirs(evidence_directory, exist_ok=True)
            for file in files:
                if file.filename:
                    file_path = os.path.join(evidence_directory, file.filename)
                    with open(file_path, "wb") as buffer:
                        buffer.write(file.file.read())
                        #alternative: shutil.copyfileobj(file.file, buffer)

                    # Save file metadata to the database
                    file_size = os.path.getsize(file_path)
                    file_type = file.content_type or "application/octet-stream"

                    evidence = schemas.EvidenceCreate(filename=file.filename, file_size=file_size, file_type=file_type, filepath=file_path, answer_id=db_answer.id)
                    answer_repository.update_evidence(evidence=evidence, db=db)

        # Trigger synchronization for correlated questions
        try:
            synchronize_correlated_answers(db, db_answer)
        except Exception as sync_error:
            logger.error(f"Error synchronizing correlated answers: {str(sync_error)}")
            # Don't fail the main operation if synchronization fails

        return db_answer
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Error updating answer: {str(e)}")

@router.post("/delete_answer")
def delete_answer(request: OnlyIdInStringFormat, db: Session = Depends(get_db)):
    try:
        request = schemas.UpdateAnswerRequest(answer_id=request.id, answer_value=None, policy_id=None)
        db_answer = answer_repository.update_answer(answer=request, db=db)
        if db_answer:
            answer_repository.delete_existing_evidences(db=db, answer_id=db_answer.id)
        return db_answer
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Error deleting answer: {str(e)}")


@router.post("/download_zip")
def download_zip(request: OnlyIdsInStringFormat, db: Session = Depends(get_db)):
    if not request.ids or len(request.ids) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file IDs provided")
    try:
        zip_buffer = answer_repository.create_zip_file(db, evidence_ids=request.ids)
        return StreamingResponse(zip_buffer,media_type="application/zip",headers={"Content-Disposition": "attachment; filename=evidence.zip"})
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Error downloading ZIP file: {str(e)}")


@router.post("/update_assessment_answers")
def update_assessment_answers(request: List[schemas.UpdateAnswerRequest], db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Validate all policy_ids belong to user's organization if provided
        for answer_request in request:
            if hasattr(answer_request, 'policy_id') and answer_request.policy_id and answer_request.policy_id.strip() != "":
                policy = policy_repository.get_policy(db, uuid.UUID(answer_request.policy_id), current_user)
                if not policy:
                    raise HTTPException(status_code=403, detail=f"Policy {answer_request.policy_id} not found or does not belong to your organization")

        # Update answers and collect updated answer objects for synchronization
        updated_answers = []
        for answer_request in request:
            db_answer = answer_repository.update_answer(answer=answer_request, db=db)
            if db_answer:
                updated_answers.append(db_answer)

        # Trigger synchronization for each updated answer
        for db_answer in updated_answers:
            try:
                synchronize_correlated_answers(db, db_answer)
            except Exception as sync_error:
                logger.error(f"Error synchronizing correlated answers for answer {db_answer.id}: {str(sync_error)}")
                # Don't fail the main operation if synchronization fails
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Error updating assessment answers: {str(e)}")

@router.get("/{answer_id}", response_model=schemas.AnswerResponse)
def read_answer(answer_id: uuid.UUID, db: Session = Depends(get_db)):
    db_answer = answer_repository.get_answer(db, answer_id=answer_id)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="Answer not found")
    return db_answer


@router.put("/{answer_id}", response_model=schemas.AnswerResponse)
def update_answer(answer_id: uuid.UUID, answer: schemas.AnswerCreate, db: Session = Depends(get_db)):
    db_answer = answer_repository.get_answer(db, answer_id=answer_id)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="Answer not found")

    # Update answer
    return answer_repository.update_answer(db=db, answer_id=answer_id, answer=answer)


@router.delete("/{answer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_answer(answer_id: uuid.UUID, db: Session = Depends(get_db)):
    db_answer = answer_repository.get_answer(db, answer_id=answer_id)
    if db_answer is None:
        raise HTTPException(status_code=404, detail="Answer not found")

    db.delete(db_answer)
    db.commit()
    return None


@router.get("/assessment/{assessment_id}", response_model=List[schemas.AnswerResponse])
def read_answers_by_assessment(assessment_id: uuid.UUID, db: Session = Depends(get_db)):
    # Verify assessment exists
    db_assessment = answer_repository.get_assessment(db, assessment_id=assessment_id)
    if not db_assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    answers = answer_repository.get_assessment_answers(db, assessment_id=assessment_id)
    return answers
