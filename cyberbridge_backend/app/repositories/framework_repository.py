# crud.py
from sqlalchemy.orm import Session
import uuid
from app.services.security_service import get_password_hash
from app.models import models
from app.dtos import schemas

# Framework CRUD operations
def get_framework(db: Session, framework_id: uuid.UUID):
    return db.query(models.Framework).filter(models.Framework.id == framework_id).first()


def get_frameworks(db: Session, current_user: schemas.UserBase ,skip: int = 0, limit: int = 100):
    # Join with Organizations table to get domain information
    query = db.query(
        models.Framework,
        models.Organisations.domain
    ).join(
        models.Organisations,
        models.Framework.organisation_id == models.Organisations.id
    )

    if current_user.role_name != "super_admin":
        query = query.filter(models.Framework.organisation_id == current_user.organisation_id)

    results = query.offset(skip).limit(limit).all()

    # Convert to list of FrameworkResponse objects with conditional domain information
    frameworks_with_domain = []
    for framework, org_domain in results:
        # Only include organisation_domain for super_admin users
        organisation_domain = None
        if current_user.role_name == "super_admin":
            organisation_domain = org_domain or "no-domain"

        # allowed_scope_types is already a list thanks to the hybrid property
        # No need to parse JSON - just use it directly
        allowed_scope_types = framework.allowed_scope_types

        # Create FrameworkResponse object
        framework_response = schemas.FrameworkResponse(
            id=framework.id,
            name=framework.name,
            description=framework.description,
            created_at=framework.created_at,
            updated_at=framework.updated_at,
            organisation_domain=organisation_domain,
            allowed_scope_types=allowed_scope_types,
            scope_selection_mode=framework.scope_selection_mode
        )
        frameworks_with_domain.append(framework_response)

    return frameworks_with_domain


def check_framework_name_exists(db: Session, name: str, organisation_id: str) -> bool:
    """Check if a framework name already exists within an organization"""
    existing_framework = db.query(models.Framework).filter(
        models.Framework.name == name,
        models.Framework.organisation_id == organisation_id
    ).first()
    return existing_framework is not None


def create_framework(db: Session, framework: schemas.FrameworkCreate, current_user: schemas.UserBase, force_create: bool = False):
    # Check if framework name already exists in the organization
    if check_framework_name_exists(db, framework.name, current_user.organisation_id):
        if not force_create:
            raise ValueError(f"Framework name '{framework.name}' already exists in your organization")
        else:
            # Find a unique name by appending a number
            base_name = framework.name
            counter = 1
            new_name = f"{base_name} ({counter})"
            while check_framework_name_exists(db, new_name, current_user.organisation_id):
                counter += 1
                new_name = f"{base_name} ({counter})"
            framework.name = new_name
    
    # db_framework = models.Framework(**framework.model_dump())
    # db_framework.organisation_id = current_user.organisation_id
    import json

    # Ensure 'Other' scope type is always included in allowed_scope_types
    # This guarantees that any two frameworks will have at least one common scope type
    allowed_scope_types_list = framework.allowed_scope_types if framework.allowed_scope_types else []
    if 'Other' not in allowed_scope_types_list:
        allowed_scope_types_list.append('Other')

    db_framework = models.Framework(
        name=framework.name,
        description=framework.description,
        organisation_id=current_user.organisation_id,
        allowed_scope_types=json.dumps(allowed_scope_types_list),
        scope_selection_mode=framework.scope_selection_mode or "optional"
    )
    db.add(db_framework)
    db.commit()
    db.refresh(db_framework)
    return db_framework


def create_framework_question(db, framework_id, question_id, order=None):
    # If order is not provided, get the max order for this framework and add 1
    if order is None:
        max_order = db.query(models.FrameworkQuestion).filter(
            models.FrameworkQuestion.framework_id == framework_id
        ).count()
        order = max_order + 1

    db_question = models.FrameworkQuestion(framework_id=framework_id, question_id=question_id, order=order)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def get_framework_assessments(db, framework_id):
    return db.query(models.Assessment).filter(models.Assessment.framework_id == framework_id).all()

def get_all_frameworks_for_cloning(db: Session, current_user: schemas.UserBase, skip: int = 0, limit: int = 100):
    """Get all frameworks from all organizations for cloning purposes"""
    query = db.query(models.Framework, models.Organisations.name.label("organisation_name")).join(
        models.Organisations, models.Framework.organisation_id == models.Organisations.id
    )
    
    # Exclude frameworks from the current user's organization to avoid self-cloning
    if current_user.role_name != "super_admin":
        query = query.filter(models.Framework.organisation_id != current_user.organisation_id)
    
    frameworks = query.offset(skip).limit(limit).all()
    
    # Convert to response format with organization info
    result = []
    for framework, org_name in frameworks:
        framework_response = schemas.FrameworkResponse(
            id=framework.id,
            name=f"{framework.name} (from {org_name})",
            description=framework.description,
            created_at=framework.created_at,
            updated_at=framework.updated_at
        )
        result.append(framework_response)
    
    return result

def clone_frameworks(db: Session, framework_ids: list[str], current_user: schemas.UserBase, custom_name: str = None, target_organization_id: str = None):
    """Clone frameworks with their questions to the specified organization (or current user's organization if not specified)"""
    cloned_frameworks = []
    
    # Determine target organization - for super_admin, use provided target_organization_id or fallback to current user's org
    if current_user.role_name == "super_admin" and target_organization_id:
        target_org_id = target_organization_id
    else:
        target_org_id = current_user.organisation_id
    
    for framework_id in framework_ids:
        # Get the original framework
        original_framework = get_framework(db, uuid.UUID(framework_id))
        if not original_framework:
            continue
            
        # Get the organization name for proper naming
        org = db.query(models.Organisations).filter(models.Organisations.id == original_framework.organisation_id).first()
        org_name = org.name if org else "Unknown"
        
        # Create a new framework for the current user's organization
        if custom_name and custom_name.strip():
            # Use custom name if provided, but only for single framework cloning
            if len(framework_ids) == 1:
                new_framework_name = custom_name.strip()
            else:
                new_framework_name = f"{custom_name.strip()} - {original_framework.name} (from {org_name})"
        else:
            new_framework_name = f"{original_framework.name} (cloned from {org_name})"
        
        # Check if the name already exists and make it unique if necessary
        base_name = new_framework_name
        counter = 1
        while check_framework_name_exists(db, new_framework_name, target_org_id):
            new_framework_name = f"{base_name} ({counter})"
            counter += 1
        # Get allowed scope types (hybrid property already returns a list)
        import json
        original_allowed_scopes = original_framework.allowed_scope_types or []
        # Make a copy to avoid modifying the original
        original_allowed_scopes = list(original_allowed_scopes)

        # Always include 'Other' scope type
        if 'Other' not in original_allowed_scopes:
            original_allowed_scopes.append('Other')

        cloned_framework = models.Framework(
            name=new_framework_name,
            description=original_framework.description,
            organisation_id=target_org_id,
            allowed_scope_types=json.dumps(original_allowed_scopes),
            scope_selection_mode=original_framework.scope_selection_mode or "optional"
        )
        db.add(cloned_framework)
        db.commit()
        db.refresh(cloned_framework)
        
        # Get all questions associated with the original framework
        framework_questions = db.query(models.FrameworkQuestion).filter(
            models.FrameworkQuestion.framework_id == original_framework.id
        ).all()
        
        # Clone each question and associate it with the new framework
        for fq in framework_questions:
            original_question = db.query(models.Question).filter(models.Question.id == fq.question_id).first()
            if original_question:
                # Create a new question (clone)
                new_question = models.Question(
                    text=original_question.text,
                    description=original_question.description,
                    mandatory=original_question.mandatory,
                    assessment_type_id=original_question.assessment_type_id
                )
                db.add(new_question)
                db.commit()
                db.refresh(new_question)
                
                # Associate the new question with the new framework
                new_framework_question = models.FrameworkQuestion(
                    framework_id=cloned_framework.id,
                    question_id=new_question.id,
                    order=fq.order
                )
                db.add(new_framework_question)
        
        # Clone chapters and objectives
        original_chapters = db.query(models.Chapters).filter(
            models.Chapters.framework_id == original_framework.id
        ).all()
        
        for original_chapter in original_chapters:
            # Clone chapter
            new_chapter = models.Chapters(
                title=original_chapter.title,
                framework_id=cloned_framework.id
            )
            db.add(new_chapter)
            db.commit()
            db.refresh(new_chapter)
            
            # Clone objectives for this chapter
            original_objectives = db.query(models.Objectives).filter(
                models.Objectives.chapter_id == original_chapter.id
            ).all()
            
            for original_objective in original_objectives:
                new_objective = models.Objectives(
                    title=original_objective.title,
                    body=original_objective.body,
                    chapter_id=new_chapter.id,
                    requirement_description=original_objective.requirement_description,
                    objective_utilities=original_objective.objective_utilities,
                    compliance_status_id=None  # Reset compliance status for new organization
                )
                db.add(new_objective)
        
        db.commit()
        cloned_frameworks.append(cloned_framework)
    
    return cloned_frameworks


def delete_framework_with_relations(db: Session, framework_id: uuid.UUID):
    """Delete a framework and all its related data"""
    # Get the framework first to check if it exists
    framework = get_framework(db, framework_id)
    if not framework:
        return False

    try:
        print(f"Starting cascading deletion of framework: {framework.name} (ID: {framework_id})")

        # Delete related data in correct dependency order

        # 1. First delete PolicyFramework associations - this must come before deleting policies
        policy_frameworks_deleted = db.query(models.PolicyFrameworks).filter(
            models.PolicyFrameworks.framework_id == framework_id
        ).delete(synchronize_session=False)
        if policy_frameworks_deleted > 0:
            print(f"Deleted {policy_frameworks_deleted} policy framework associations")

        # 2. Get policy IDs that were associated with this framework (before we deleted the associations)
        # We need to get these separately since we can't rely on the associations anymore
        # Let's get all policies that were linked to objectives in this framework
        policies_to_delete = db.query(models.Policies.id).join(
            models.PolicyObjectives, models.Policies.id == models.PolicyObjectives.policy_id
        ).join(
            models.Objectives, models.PolicyObjectives.objective_id == models.Objectives.id
        ).join(
            models.Chapters, models.Objectives.chapter_id == models.Chapters.id
        ).filter(models.Chapters.framework_id == framework_id).distinct().all()

        if policies_to_delete:
            policy_ids = [policy.id for policy in policies_to_delete]

            # MUST delete PolicyObjectives before deleting Policies due to foreign key constraints
            policy_objectives_deleted = db.query(models.PolicyObjectives).filter(
                models.PolicyObjectives.policy_id.in_(policy_ids)
            ).delete(synchronize_session=False)
            if policy_objectives_deleted > 0:
                print(f"Deleted {policy_objectives_deleted} policy objective associations for policies")

            # Before deleting policies, we need to handle answers that reference these policies
            # Set policy_id to NULL for answers that reference these policies
            answers_updated = db.query(models.Answer).filter(
                models.Answer.policy_id.in_(policy_ids)
            ).update({models.Answer.policy_id: None}, synchronize_session=False)
            if answers_updated > 0:
                print(f"Unlinked {answers_updated} answers from policies being deleted")

            # Now delete the actual Policy records (safe since policy objectives and answer references are gone)
            policies_deleted = db.query(models.Policies).filter(
                models.Policies.id.in_(policy_ids)
            ).delete(synchronize_session=False)
            if policies_deleted > 0:
                print(f"Deleted {policies_deleted} policy records")

        # 3. Get question IDs associated with this framework before deleting relationships
        question_ids_for_framework = db.query(models.FrameworkQuestion.question_id).filter(
            models.FrameworkQuestion.framework_id == framework_id
        ).distinct().all()

        if question_ids_for_framework:
            question_ids = [q.question_id for q in question_ids_for_framework]

            # Delete question correlations for these questions
            correlations_deleted = db.query(models.QuestionCorrelation).filter(
                (models.QuestionCorrelation.question_a_id.in_(question_ids)) |
                (models.QuestionCorrelation.question_b_id.in_(question_ids))
            ).delete(synchronize_session=False)
            if correlations_deleted > 0:
                print(f"Deleted {correlations_deleted} question correlations")

        # Delete FrameworkQuestion relationships
        framework_questions_deleted = db.query(models.FrameworkQuestion).filter(
            models.FrameworkQuestion.framework_id == framework_id
        ).delete(synchronize_session=False)
        if framework_questions_deleted > 0:
            print(f"Deleted {framework_questions_deleted} framework question relationships")

        # 4. Delete Objectives for this framework (PolicyObjectives already deleted in step 2)
        objectives_to_delete = db.query(models.Objectives.id).join(
            models.Chapters, models.Objectives.chapter_id == models.Chapters.id
        ).filter(models.Chapters.framework_id == framework_id).all()

        if objectives_to_delete:
            objective_ids = [obj.id for obj in objectives_to_delete]
            objectives_count = len(objective_ids)

            # 5. Delete objectives by their IDs (now safe since policy associations are gone)
            db.query(models.Objectives).filter(
                models.Objectives.id.in_(objective_ids)
            ).delete(synchronize_session=False)
            print(f"Deleted {objectives_count} objective records")
        
        # 5. Delete Chapters for this framework (now safe since objectives are gone)
        chapters_query = db.query(models.Chapters).filter(
            models.Chapters.framework_id == framework_id
        )
        chapters_count = chapters_query.count()
        if chapters_count > 0:
            chapters_query.delete(synchronize_session=False)
            print(f"Deleted {chapters_count} chapter records")
        
        # 6. Delete Answers and Evidence for assessments related to this framework
        # First get assessment IDs for this framework
        assessment_ids_to_delete = db.query(models.Assessment.id).filter(
            models.Assessment.framework_id == framework_id
        ).all()
        
        if assessment_ids_to_delete:
            assessment_ids = [assessment.id for assessment in assessment_ids_to_delete]
            
            # Delete Evidence files for answers related to these assessments
            # First get answer IDs for these assessments
            answer_ids_to_delete = db.query(models.Answer.id).filter(
                models.Answer.assessment_id.in_(assessment_ids)
            ).all()
            
            if answer_ids_to_delete:
                answer_ids = [answer.id for answer in answer_ids_to_delete]
                
                # Delete evidence files for these answers
                evidence_deleted = db.query(models.Evidence).filter(
                    models.Evidence.answer_id.in_(answer_ids)
                ).delete(synchronize_session=False)
                if evidence_deleted > 0:
                    print(f"Deleted {evidence_deleted} evidence records")
            
            # Delete Answers for these assessments
            answers_deleted = db.query(models.Answer).filter(
                models.Answer.assessment_id.in_(assessment_ids)
            ).delete(synchronize_session=False)
            if answers_deleted > 0:
                print(f"Deleted {answers_deleted} answer records")
            
            # Now delete the assessments (should be safe now)
            assessments_deleted = db.query(models.Assessment).filter(
                models.Assessment.framework_id == framework_id
            ).delete(synchronize_session=False)
            if assessments_deleted > 0:
                print(f"Deleted {assessments_deleted} assessment records")
        
        # 7. Questions are NOT deleted because they might be shared with other frameworks
        # Only the FrameworkQuestion relationships were deleted in step 3

        # 8. Delete OrganizationFrameworkPermissions for this framework
        org_permissions_deleted = db.query(models.OrganizationFrameworkPermissions).filter(
            models.OrganizationFrameworkPermissions.framework_id == framework_id
        ).delete(synchronize_session=False)
        if org_permissions_deleted > 0:
            print(f"Deleted {org_permissions_deleted} organization framework permission records")

        # 9. Finally, delete the framework itself
        db.delete(framework)
        print(f"Deleted framework: {framework.name}")
        
        # Commit all changes
        db.commit()
        print("Framework cascading deletion completed successfully")
        return True
        
    except Exception as e:
        print(f"Error during framework deletion: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise e