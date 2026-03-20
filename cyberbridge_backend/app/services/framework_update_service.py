from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Dict, Optional
import uuid
from datetime import datetime
import importlib
import os

from ..models.models import FrameworkUpdates, Framework, Chapters, Objectives, Question, FrameworkQuestion
from ..seeds.updates.base_framework_update import BaseFrameworkUpdate


class FrameworkUpdateService:
    """
    Service for managing framework updates.
    Handles discovering, previewing, and applying updates to frameworks.
    """

    @staticmethod
    def get_available_updates(db: Session, framework_id: uuid.UUID) -> List[Dict]:
        """
        Get all available updates for a framework.
        Returns both applied and unapplied updates with their status.
        """
        # Get the framework
        framework = db.query(Framework).filter(Framework.id == framework_id).first()
        if not framework:
            raise ValueError(f"Framework with ID {framework_id} not found")

        # Determine framework type from framework name
        framework_name_lower = framework.name.lower()
        if "cra" in framework_name_lower:
            framework_type = "cra"
        elif "iso" in framework_name_lower or "27001" in framework_name_lower:
            framework_type = "iso_27001_2022"
        elif "nis" in framework_name_lower or "nis2" in framework_name_lower:
            framework_type = "nis2_directive"
        else:
            return []  # Unknown framework type

        # Discover all update files for this framework
        update_files = FrameworkUpdateService._discover_update_files(framework_type)

        # Get all applied updates from database
        applied_updates = db.query(FrameworkUpdates).filter(
            FrameworkUpdates.framework_id == framework_id
        ).all()

        # Create a map of version -> status
        applied_map = {u.version: u for u in applied_updates}

        # Build result list
        results = []
        for update_class in update_files:
            update_instance = update_class()
            version = update_instance.version

            if version in applied_map:
                # Already applied
                applied_update = applied_map[version]
                results.append({
                    "id": str(applied_update.id),
                    "version": version,
                    "description": update_instance.description,
                    "status": applied_update.status,
                    "applied_at": applied_update.applied_at.isoformat() if applied_update.applied_at else None,
                    "applied_by": str(applied_update.applied_by) if applied_update.applied_by else None,
                    "error_message": applied_update.error_message
                })
            else:
                # Not yet applied
                results.append({
                    "id": None,
                    "version": version,
                    "description": update_instance.description,
                    "status": "available",
                    "applied_at": None,
                    "applied_by": None,
                    "error_message": None
                })

        # Sort by version
        results.sort(key=lambda x: x["version"])
        return results

    @staticmethod
    def _discover_update_files(framework_type: str) -> List:
        """
        Dynamically discover all update classes for a given framework type.
        Returns a list of update classes sorted by version.
        """
        updates = []
        update_dir = f"app.seeds.updates.{framework_type}"

        try:
            # Import the framework's update package
            package = importlib.import_module(update_dir)

            # Get all classes exported from __all__
            if hasattr(package, '__all__'):
                for class_name in package.__all__:
                    update_class = getattr(package, class_name)
                    if issubclass(update_class, BaseFrameworkUpdate) and update_class != BaseFrameworkUpdate:
                        updates.append(update_class)
        except (ImportError, AttributeError):
            # No updates found for this framework
            pass

        # Sort by version
        updates.sort(key=lambda cls: cls.version if hasattr(cls, 'version') else 0)
        return updates

    @staticmethod
    def get_update_preview(db: Session, framework_id: uuid.UUID, version: int) -> Dict:
        """
        Get a preview of what will be changed by applying an update.
        Returns detailed information about new/updated items.
        """
        # Get the framework
        framework = db.query(Framework).filter(Framework.id == framework_id).first()
        if not framework:
            raise ValueError(f"Framework with ID {framework_id} not found")

        # Determine framework type
        framework_name_lower = framework.name.lower()
        if "cra" in framework_name_lower:
            framework_type = "cra"
        elif "iso" in framework_name_lower or "27001" in framework_name_lower:
            framework_type = "iso_27001_2022"
        elif "nis" in framework_name_lower or "nis2" in framework_name_lower:
            framework_type = "nis2_directive"
        else:
            raise ValueError("Unknown framework type")

        # Load the update class
        update_class = FrameworkUpdateService._load_update_class(framework_type, version)
        if not update_class:
            raise ValueError(f"Update version {version} not found for {framework_type}")

        update_instance = update_class()

        # Get all the changes
        new_questions = update_instance.get_new_questions()
        new_chapters = update_instance.get_new_chapters()
        new_objectives = update_instance.get_new_objectives()
        updated_objectives = update_instance.get_updated_objectives()
        updated_questions = update_instance.get_updated_questions()

        # Enrich the data with chapter names for questions and objectives
        for question in new_questions:
            chapter = db.query(Chapters).filter(Chapters.id == question["chapter_id"]).first()
            question["chapter_name"] = chapter.title if chapter else "Unknown Chapter"

        for objective in new_objectives:
            chapter = db.query(Chapters).filter(Chapters.id == objective["chapter_id"]).first()
            objective["chapter_name"] = chapter.title if chapter else "Unknown Chapter"

        # For updated objectives, get the current values
        for obj_update in updated_objectives:
            subchapter = obj_update["subchapter"]
            current_obj = db.query(Objectives).join(Chapters).filter(
                and_(
                    Objectives.subchapter == subchapter,
                    Chapters.framework_id == framework_id
                )
            ).first()

            if current_obj:
                obj_update["current_title"] = current_obj.title
                obj_update["current_requirement_description"] = current_obj.requirement_description
                obj_update["current_objective_utilities"] = current_obj.objective_utilities

                chapter = db.query(Chapters).filter(Chapters.id == current_obj.chapter_id).first()
                obj_update["chapter_name"] = chapter.title if chapter else "Unknown Chapter"
            else:
                obj_update["current_title"] = None
                obj_update["current_requirement_description"] = None
                obj_update["current_objective_utilities"] = None
                obj_update["chapter_name"] = "Not Found"

        # For updated questions, get the current values
        for question_update in updated_questions:
            question_id = question_update["question_id"]
            current_question = db.query(Question).filter(Question.id == question_id).first()

            if current_question:
                question_update["current_text"] = current_question.text
                question_update["current_description"] = current_question.description
            else:
                question_update["current_text"] = None
                question_update["current_description"] = None

        return {
            "version": update_instance.version,
            "description": update_instance.description,
            "new_questions": new_questions,
            "new_chapters": new_chapters,
            "new_objectives": new_objectives,
            "updated_objectives": updated_objectives,
            "updated_questions": updated_questions
        }

    @staticmethod
    def _load_update_class(framework_type: str, version: int):
        """
        Load a specific update class by framework type and version.
        """
        updates = FrameworkUpdateService._discover_update_files(framework_type)
        for update_class in updates:
            if hasattr(update_class, 'version') and update_class.version == version:
                return update_class
        return None

    @staticmethod
    def apply_update(db: Session, framework_id: uuid.UUID, version: int, user_id: uuid.UUID) -> Dict:
        """
        Apply an update to a framework.
        Creates new questions, chapters, objectives, and updates existing objectives.
        """
        try:
            # Get the framework
            framework = db.query(Framework).filter(Framework.id == framework_id).first()
            if not framework:
                raise ValueError(f"Framework with ID {framework_id} not found")

            # Check if already applied
            existing_update = db.query(FrameworkUpdates).filter(
                and_(
                    FrameworkUpdates.framework_id == framework_id,
                    FrameworkUpdates.version == version
                )
            ).first()

            if existing_update and existing_update.status == "applied":
                raise ValueError(f"Update version {version} has already been applied to this framework")

            # Determine framework type
            framework_name_lower = framework.name.lower()
            if "cra" in framework_name_lower:
                framework_type = "cra"
            elif "iso" in framework_name_lower or "27001" in framework_name_lower:
                framework_type = "iso_27001_2022"
            elif "nis" in framework_name_lower or "nis2" in framework_name_lower:
                framework_type = "nis2_directive"
            else:
                raise ValueError("Unknown framework type")

            # Load the update class
            update_class = FrameworkUpdateService._load_update_class(framework_type, version)
            if not update_class:
                raise ValueError(f"Update version {version} not found for {framework_type}")

            update_instance = update_class()

            # Track changes
            changes = {
                "new_questions_count": 0,
                "new_chapters_count": 0,
                "new_objectives_count": 0,
                "updated_objectives_count": 0,
                "updated_questions_count": 0
            }

            # 1. Add new chapters
            for chapter_data in update_instance.get_new_chapters():
                new_chapter = Chapters(
                    id=uuid.uuid4(),
                    title=chapter_data["name"],
                    framework_id=framework_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_chapter)
                changes["new_chapters_count"] += 1

            db.flush()  # Flush to get chapter IDs

            # 2. Add new questions
            for question_data in update_instance.get_new_questions():
                new_question = Question(
                    id=uuid.uuid4(),
                    text=question_data["question_text"],
                    description=question_data.get("title", ""),
                    mandatory=False,
                    assessment_type_id=question_data["assessment_type_id"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_question)
                db.flush()

                # Link question to framework
                framework_question = FrameworkQuestion(
                    framework_id=framework_id,
                    question_id=new_question.id,
                    order=question_data.get("order", 0)
                )
                db.add(framework_question)
                changes["new_questions_count"] += 1

            # 3. Add new objectives
            for objective_data in update_instance.get_new_objectives():
                new_objective = Objectives(
                    id=uuid.uuid4(),
                    title=objective_data["title"],
                    subchapter=objective_data["subchapter"],
                    chapter_id=objective_data["chapter_id"],
                    requirement_description=objective_data.get("requirement_description"),
                    objective_utilities=objective_data.get("objective_utilities"),
                    compliance_status_id=objective_data.get("compliance_status_id"),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_objective)
                changes["new_objectives_count"] += 1

            # 4. Update existing objectives
            for obj_update in update_instance.get_updated_objectives():
                subchapter = obj_update["subchapter"]
                existing_obj = db.query(Objectives).join(Chapters).filter(
                    and_(
                        Objectives.subchapter == subchapter,
                        Chapters.framework_id == framework_id
                    )
                ).first()

                if existing_obj:
                    # Update only the fields provided
                    if "title" in obj_update:
                        existing_obj.title = obj_update["title"]
                    if "requirement_description" in obj_update:
                        existing_obj.requirement_description = obj_update["requirement_description"]
                    if "objective_utilities" in obj_update:
                        existing_obj.objective_utilities = obj_update["objective_utilities"]
                    if "compliance_status_id" in obj_update:
                        existing_obj.compliance_status_id = obj_update["compliance_status_id"]

                    existing_obj.updated_at = datetime.utcnow()
                    changes["updated_objectives_count"] += 1

            # 5. Update existing questions
            for question_update in update_instance.get_updated_questions():
                question_id = question_update["question_id"]
                existing_question = db.query(Question).filter(Question.id == question_id).first()

                if existing_question:
                    # Update only the fields provided
                    if "text" in question_update:
                        existing_question.text = question_update["text"]
                    if "description" in question_update:
                        existing_question.description = question_update["description"]
                    if "mandatory" in question_update:
                        existing_question.mandatory = question_update["mandatory"]

                    existing_question.updated_at = datetime.utcnow()
                    changes["updated_questions_count"] += 1

            # 6. Record the update in framework_updates table
            if existing_update:
                # Update existing record
                existing_update.status = "applied"
                existing_update.applied_by = user_id
                existing_update.applied_at = datetime.utcnow()
                existing_update.error_message = None
                existing_update.updated_at = datetime.utcnow()
                update_record = existing_update
            else:
                # Create new record
                update_record = FrameworkUpdates(
                    id=uuid.uuid4(),
                    framework_id=framework_id,
                    version=version,
                    framework_name=framework_type,
                    description=update_instance.description,
                    status="applied",
                    applied_by=user_id,
                    applied_at=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(update_record)

            # Commit all changes
            db.commit()

            return {
                "success": True,
                "message": f"Update version {version} applied successfully",
                "changes": changes,
                "update_id": str(update_record.id)
            }

        except Exception as e:
            db.rollback()

            # Record the failure
            if existing_update:
                existing_update.status = "failed"
                existing_update.error_message = str(e)
                existing_update.updated_at = datetime.utcnow()
            else:
                failure_record = FrameworkUpdates(
                    id=uuid.uuid4(),
                    framework_id=framework_id,
                    version=version,
                    framework_name=framework_type,
                    description=update_instance.description if update_instance else "Unknown",
                    status="failed",
                    applied_by=user_id,
                    error_message=str(e),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(failure_record)

            db.commit()

            raise Exception(f"Failed to apply update: {str(e)}")
