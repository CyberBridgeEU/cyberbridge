import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.models import (
    FrameworkSnapshot, Framework, Chapters, Objectives,
    Question, FrameworkQuestion
)

logger = logging.getLogger(__name__)


class FrameworkSnapshotService:
    """Service for creating and reverting framework snapshots."""

    @staticmethod
    def create_snapshot(
        db: Session,
        framework_id: uuid.UUID,
        version: int,
        snapshot_type: str,
        user_id: uuid.UUID = None
    ) -> FrameworkSnapshot:
        """
        Create a snapshot of the current framework state.
        Serializes all chapters, objectives, questions, and framework_questions to JSON.
        """
        framework = db.query(Framework).filter(Framework.id == framework_id).first()
        if not framework:
            raise ValueError(f"Framework with ID {framework_id} not found")

        # Get all chapters for this framework
        chapters = db.query(Chapters).filter(Chapters.framework_id == framework_id).all()

        # Get all objectives for those chapters
        chapter_ids = [c.id for c in chapters]
        objectives = db.query(Objectives).filter(Objectives.chapter_id.in_(chapter_ids)).all() if chapter_ids else []

        # Get all framework_questions for this framework
        fqs = db.query(FrameworkQuestion).filter(FrameworkQuestion.framework_id == framework_id).all()

        # Get all questions linked to this framework
        question_ids = [fq.question_id for fq in fqs]
        questions = db.query(Question).filter(Question.id.in_(question_ids)).all() if question_ids else []

        # Serialize everything
        snapshot_data = {
            "framework": {
                "id": str(framework.id),
                "name": framework.name,
                "description": framework.description
            },
            "chapters": [
                {
                    "id": str(c.id),
                    "title": c.title,
                    "framework_id": str(c.framework_id),
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None
                }
                for c in chapters
            ],
            "objectives": [
                {
                    "id": str(o.id),
                    "title": o.title,
                    "subchapter": o.subchapter,
                    "chapter_id": str(o.chapter_id),
                    "requirement_description": o.requirement_description,
                    "objective_utilities": o.objective_utilities,
                    "compliance_status_id": str(o.compliance_status_id) if o.compliance_status_id else None,
                    "scope_id": str(o.scope_id) if o.scope_id else None,
                    "scope_entity_id": str(o.scope_entity_id) if o.scope_entity_id else None,
                    "applicable_operators": o.applicable_operators,
                    "evidence_filename": o.evidence_filename,
                    "evidence_filepath": o.evidence_filepath,
                    "evidence_file_type": o.evidence_file_type,
                    "evidence_file_size": o.evidence_file_size,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                    "updated_at": o.updated_at.isoformat() if o.updated_at else None
                }
                for o in objectives
            ],
            "questions": [
                {
                    "id": str(q.id),
                    "text": q.text,
                    "description": q.description,
                    "mandatory": q.mandatory,
                    "assessment_type_id": str(q.assessment_type_id) if q.assessment_type_id else None,
                    "created_at": q.created_at.isoformat() if q.created_at else None,
                    "updated_at": q.updated_at.isoformat() if q.updated_at else None
                }
                for q in questions
            ],
            "framework_questions": [
                {
                    "framework_id": str(fq.framework_id),
                    "question_id": str(fq.question_id),
                    "order": fq.order
                }
                for fq in fqs
            ]
        }

        snapshot = FrameworkSnapshot(
            id=uuid.uuid4(),
            framework_id=framework_id,
            update_version=version,
            snapshot_type=snapshot_type,
            snapshot_data=json.dumps(snapshot_data),
            created_by=user_id,
            created_at=datetime.utcnow()
        )
        db.add(snapshot)
        db.flush()

        logger.info(
            f"Created {snapshot_type} snapshot for framework {framework_id}, "
            f"version {version}: {len(chapters)} chapters, "
            f"{len(objectives)} objectives, {len(questions)} questions"
        )

        return snapshot

    @staticmethod
    def revert_to_snapshot(
        db: Session,
        framework_id: uuid.UUID,
        snapshot_id: uuid.UUID,
        user_id: uuid.UUID = None
    ) -> Dict:
        """
        Revert a framework to a previous snapshot state.
        Creates a safety snapshot first, then replaces entities preserving original UUIDs.
        """
        snapshot = db.query(FrameworkSnapshot).filter(FrameworkSnapshot.id == snapshot_id).first()
        if not snapshot:
            raise ValueError(f"Snapshot with ID {snapshot_id} not found")

        if snapshot.framework_id != framework_id:
            raise ValueError("Snapshot does not belong to this framework")

        # Parse snapshot data
        data = json.loads(snapshot.snapshot_data)

        # Create a safety snapshot before reverting
        current_max_version = snapshot.update_version
        safety_snapshot = FrameworkSnapshotService.create_snapshot(
            db, framework_id, current_max_version, "pre_revert", user_id
        )

        # Step 1: Delete current objectives for this framework's chapters
        current_chapters = db.query(Chapters).filter(Chapters.framework_id == framework_id).all()
        current_chapter_ids = [c.id for c in current_chapters]

        if current_chapter_ids:
            db.query(Objectives).filter(Objectives.chapter_id.in_(current_chapter_ids)).delete(
                synchronize_session='fetch'
            )

        # Step 2: Delete current framework_questions
        db.query(FrameworkQuestion).filter(FrameworkQuestion.framework_id == framework_id).delete(
            synchronize_session='fetch'
        )

        # Step 3: Delete current chapters
        db.query(Chapters).filter(Chapters.framework_id == framework_id).delete(
            synchronize_session='fetch'
        )

        db.flush()

        # Step 4: Restore chapters from snapshot (preserving original UUIDs)
        for ch_data in data["chapters"]:
            chapter = Chapters(
                id=uuid.UUID(ch_data["id"]),
                title=ch_data["title"],
                framework_id=framework_id,
                created_at=datetime.fromisoformat(ch_data["created_at"]) if ch_data.get("created_at") else datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(chapter)

        db.flush()

        # Step 5: Restore objectives from snapshot
        for obj_data in data["objectives"]:
            objective = Objectives(
                id=uuid.UUID(obj_data["id"]),
                title=obj_data["title"],
                subchapter=obj_data.get("subchapter"),
                chapter_id=uuid.UUID(obj_data["chapter_id"]),
                requirement_description=obj_data.get("requirement_description"),
                objective_utilities=obj_data.get("objective_utilities"),
                compliance_status_id=uuid.UUID(obj_data["compliance_status_id"]) if obj_data.get("compliance_status_id") else None,
                scope_id=uuid.UUID(obj_data["scope_id"]) if obj_data.get("scope_id") else None,
                scope_entity_id=uuid.UUID(obj_data["scope_entity_id"]) if obj_data.get("scope_entity_id") else None,
                applicable_operators=obj_data.get("applicable_operators"),
                evidence_filename=obj_data.get("evidence_filename"),
                evidence_filepath=obj_data.get("evidence_filepath"),
                evidence_file_type=obj_data.get("evidence_file_type"),
                evidence_file_size=obj_data.get("evidence_file_size"),
                created_at=datetime.fromisoformat(obj_data["created_at"]) if obj_data.get("created_at") else datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(objective)

        # Step 6: Restore framework_questions from snapshot
        for fq_data in data["framework_questions"]:
            fq = FrameworkQuestion(
                framework_id=uuid.UUID(fq_data["framework_id"]),
                question_id=uuid.UUID(fq_data["question_id"]),
                order=fq_data.get("order", 0)
            )
            db.add(fq)

        # Step 7: Restore questions (update existing or create missing)
        for q_data in data["questions"]:
            q_id = uuid.UUID(q_data["id"])
            existing_q = db.query(Question).filter(Question.id == q_id).first()
            if existing_q:
                existing_q.text = q_data["text"]
                existing_q.description = q_data.get("description")
                existing_q.mandatory = q_data.get("mandatory", False)
                existing_q.updated_at = datetime.utcnow()
            else:
                question = Question(
                    id=q_id,
                    text=q_data["text"],
                    description=q_data.get("description"),
                    mandatory=q_data.get("mandatory", False),
                    assessment_type_id=uuid.UUID(q_data["assessment_type_id"]) if q_data.get("assessment_type_id") else None,
                    created_at=datetime.fromisoformat(q_data["created_at"]) if q_data.get("created_at") else datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(question)

        db.flush()

        logger.info(
            f"Reverted framework {framework_id} to snapshot {snapshot_id}: "
            f"restored {len(data['chapters'])} chapters, "
            f"{len(data['objectives'])} objectives, "
            f"{len(data['questions'])} questions"
        )

        return {
            "success": True,
            "message": f"Framework reverted to snapshot from version {snapshot.update_version}",
            "safety_snapshot_id": str(safety_snapshot.id),
            "restored": {
                "chapters": len(data["chapters"]),
                "objectives": len(data["objectives"]),
                "questions": len(data["questions"]),
                "framework_questions": len(data["framework_questions"])
            }
        }

    @staticmethod
    def list_snapshots(db: Session, framework_id: uuid.UUID) -> List[Dict]:
        """List all snapshots for a framework, ordered by creation time."""
        snapshots = db.query(FrameworkSnapshot).filter(
            FrameworkSnapshot.framework_id == framework_id
        ).order_by(FrameworkSnapshot.created_at.desc()).all()

        return [
            {
                "id": str(s.id),
                "framework_id": str(s.framework_id),
                "update_version": s.update_version,
                "snapshot_type": s.snapshot_type,
                "created_by": str(s.created_by) if s.created_by else None,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in snapshots
        ]
