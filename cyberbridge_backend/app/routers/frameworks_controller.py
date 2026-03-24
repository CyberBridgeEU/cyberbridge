# routers/frameworks_controller.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging
import os
import tempfile
import shutil

logger = logging.getLogger(__name__)

from ..repositories import framework_repository, question_repository, answer_repository, history_repository
from ..dtos import schemas
from ..database.database import get_db
from ..services.auth_service import get_current_active_user
from ..services.framework_update_service import FrameworkUpdateService
from ..seeds.cra_seed import CraSeed
from ..seeds.iso_27001_2022_seed import ISO270012022Seed
from ..seeds.nis2_directive_seed import NIS2DirectiveSeed
from ..models import models
from ..utils.excel_framework_parser import ExcelFrameworkParser

router = APIRouter(prefix="/frameworks",tags=["frameworks"],responses={404: {"description": "Not found"}},)

# Template IDs that have chain links (connections mappings) available
TEMPLATES_WITH_CHAIN_LINKS = {
    "CRA", "GDPR", "SOC_2", "ISO_27001_2022", "NIS2_DIRECTIVE",
    "NIST_CSF_2_0", "CMMC_2_0", "DORA_2022", "PCI_DSS_V4_0", "FTC_SAFEGUARDS"
}

def seed_cra_framework_for_organization(db: Session, organization, assessment_types, wire_connections=True):
    """Seed CRA framework for a specific organization"""
    organizations = {organization.name: organization}
    seed_instance = CraSeed(db, organizations, assessment_types)
    seed_instance.skip_wire_connections = not wire_connections

    try:
        result = seed_instance.seed()
        db.commit()  # Single commit for entire operation
        return result["frameworks"]["CRA"]
    except Exception as e:
        db.rollback()
        raise

def seed_iso_27001_2022_framework_for_organization(db: Session, organization, assessment_types, wire_connections=True):
    """Seed ISO 27001 2022 framework for a specific organization"""
    organizations = {organization.name: organization}
    seed_instance = ISO270012022Seed(db, organizations, assessment_types)
    seed_instance.skip_wire_connections = not wire_connections

    try:
        result = seed_instance.seed()
        db.commit()  # Single commit for entire operation
        return result["frameworks"]["ISO 27001 2022"]
    except Exception as e:
        db.rollback()
        raise

def seed_nis2_directive_framework_for_organization(db: Session, organization, assessment_types, wire_connections=True):
    """Seed NIS2 Directive framework for a specific organization"""
    organizations = {organization.name: organization}
    seed_instance = NIS2DirectiveSeed(db, organizations, assessment_types)
    seed_instance.skip_wire_connections = not wire_connections

    try:
        result = seed_instance.seed()
        db.commit()  # Single commit for entire operation
        return result["frameworks"]["NIS2 Directive"]
    except Exception as e:
        db.rollback()
        raise

@router.post("/", response_model=schemas.FrameworkResponse, status_code=status.HTTP_201_CREATED)
def create_framework(framework: schemas.FrameworkCreate, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Create the framework
        new_framework = framework_repository.create_framework(db=db, framework=framework, current_user=current_user, force_create=framework.force_create)

        # Track the creation in history
        history_repository.track_insert(
            db=db,
            table_name="frameworks",
            record_id=str(new_framework.id),
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            new_data={
                "name": new_framework.name,
                "description": new_framework.description
            }
        )

        return new_framework
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[schemas.FrameworkResponse])
def read_frameworks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    frameworks = framework_repository.get_frameworks(db, current_user=current_user ,skip=skip, limit=limit)
    return frameworks

@router.get("/all-for-cloning", response_model=List[schemas.FrameworkResponse])
def read_all_frameworks_for_cloning(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    frameworks = framework_repository.get_all_frameworks_for_cloning(db, current_user=current_user, skip=skip, limit=limit)
    return frameworks

@router.get("/templates", response_model=List[dict])
def get_framework_templates(db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    """Get available framework templates for seeding based on organization permissions"""

    # Scan all framework seed files from the seeds directory
    all_templates = []
    seeds_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "seeds")

    # Non-framework seed files to skip (infrastructure/utility seeds)
    non_framework_seeds = {
        '__init__.py',
        'base_seed.py',
        'asset_types_seed.py',
        'auditor_roles_seed.py',
        'seed_manager.py',
        'roles_seed.py',
        'organizations_seed.py',
        'users_seed.py',
        'lookup_tables_seed.py',
        'smtp_seed.py',
        'settings_seed.py',
        'scopes_seed.py',
        'framework_scope_config_seed.py'
    }

    try:
        for filename in os.listdir(seeds_dir):
            if filename.endswith('_seed.py') and filename not in non_framework_seeds:
                # Extract framework name from filename
                # e.g., "gdpr_seed.py" -> "GDPR", "iso_27001_2022_seed.py" -> "ISO_27001_2022"
                framework_id = filename.replace('_seed.py', '').upper()
                # Use framework_id directly as name to preserve case
                framework_name = framework_id

                all_templates.append({
                    "id": framework_id,
                    "name": framework_name,
                    "description": f"{framework_name} compliance framework",
                    "is_custom": False,  # All are treated equally
                    "has_chain_links": framework_id in TEMPLATES_WITH_CHAIN_LINKS
                })
    except Exception as e:
        logger.error(f"Error scanning framework seed files: {e}")

    # Super admin and org admin see all templates
    if current_user.role_name in ['super_admin', 'org_admin']:
        return sorted(all_templates, key=lambda x: x['name'])

    # For org_user, check if there are specific permissions set for this organization
    existing_permissions = db.query(models.OrganizationFrameworkPermissions).filter(
        models.OrganizationFrameworkPermissions.organization_id == current_user.organisation_id
    ).first()

    if not existing_permissions:
        # No permissions set - show all templates (default behavior)
        return sorted(all_templates, key=lambda x: x['name'])

    # Get framework IDs that are allowed for seeding
    allowed_framework_ids = db.query(models.OrganizationFrameworkPermissions.framework_id).filter(
        models.OrganizationFrameworkPermissions.organization_id == current_user.organisation_id,
        models.OrganizationFrameworkPermissions.can_seed == True
    ).all()

    if not allowed_framework_ids:
        # No frameworks allowed
        return []

    # Get the actual frameworks to map template names to framework names
    allowed_framework_ids_list = [str(row.framework_id) for row in allowed_framework_ids]
    allowed_frameworks = db.query(models.Framework).filter(
        models.Framework.id.in_(allowed_framework_ids_list)
    ).all()

    # Map framework names to their templates
    allowed_framework_names = [fw.name for fw in allowed_frameworks]

    # Filter templates based on allowed framework names
    filtered_templates = []
    for template in builtin_templates:
        # Check if this template corresponds to any allowed framework
        if template["name"] in allowed_framework_names or template["id"] in allowed_framework_names:
            filtered_templates.append(template)

    return filtered_templates

@router.post("/seed-template", response_model=schemas.FrameworkResponse)
def seed_framework_template(template_id: str, wire_connections: bool = True, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    """Seed a framework template for the current user's organization"""
    try:
        logger.info(f"=== SEED FRAMEWORK TEMPLATE CALLED: template_id={template_id} ===")
        # Get user's organization
        user_org = db.query(models.Organisations).filter(models.Organisations.id == current_user.organisation_id).first()
        if not user_org:
            raise HTTPException(status_code=404, detail="User organization not found")

        logger.info(f"User organization found: {user_org.id}")
        # Check if the framework template already exists for this organization
        # Use case-insensitive LIKE matching with both underscore and space versions
        # E.g., template_id "CMMC_2_0" should match "CMMC 2.0", "cmmc 2.0", etc.
        template_search_pattern = template_id.replace('_', '%').upper()

        # Get all frameworks for this organization
        org_frameworks = db.query(models.Framework).filter(
            models.Framework.organisation_id == current_user.organisation_id
        ).all()

        # Check if any existing framework name matches the template (case-insensitive, flexible with separators)
        existing_framework = None
        logger.info(f"Checking {len(org_frameworks)} frameworks for duplicates")
        for framework in org_frameworks:
            # Normalize both names by removing spaces, underscores, periods for comparison
            normalized_existing = framework.name.upper().replace('_', '').replace(' ', '').replace('.', '').replace('-', '')
            normalized_template = template_id.upper().replace('_', '').replace(' ', '').replace('.', '').replace('-', '')

            logger.info(f"Comparing: '{normalized_existing}' vs '{normalized_template}'")
            if normalized_existing == normalized_template:
                existing_framework = framework
                logger.info(f"MATCH FOUND! Framework '{framework.name}' matches template '{template_id}'")
                break

        if existing_framework:
            logger.warning(f"Duplicate framework detected: {existing_framework.name}")
            raise HTTPException(
                status_code=400,
                detail="This framework template already exists in your organization and cannot be seeded again."
            )

        logger.info("No duplicate found, proceeding with seeding")

        # Get assessment types
        assessment_types = {}
        for assessment_type in db.query(models.AssessmentType).all():
            assessment_types[assessment_type.type_name] = assessment_type

        if not assessment_types:
            raise HTTPException(status_code=500, detail="Assessment types not found")

        # Seed the appropriate framework based on template_id
        template_name_upper = template_id.upper()
        if template_name_upper == "CRA":
            framework = seed_cra_framework_for_organization(db, user_org, assessment_types, wire_connections)
        elif template_name_upper == "ISO_27001_2022":
            framework = seed_iso_27001_2022_framework_for_organization(db, user_org, assessment_types, wire_connections)
        elif template_name_upper == "NIS2_DIRECTIVE":
            framework = seed_nis2_directive_framework_for_organization(db, user_org, assessment_types, wire_connections)
        else:
            # Try to load custom seed file dynamically
            seed_filename = f"{template_id.lower()}_seed"
            seed_module_path = f"app.seeds.{seed_filename}"

            try:
                import importlib
                seed_module = importlib.import_module(seed_module_path)

                # Find the seed class (should end with 'Seed')
                seed_class = None
                for attr_name in dir(seed_module):
                    attr = getattr(seed_module, attr_name)
                    if isinstance(attr, type) and attr_name.endswith('Seed') and attr_name != 'BaseSeed':
                        seed_class = attr
                        break

                if not seed_class:
                    raise HTTPException(status_code=500, detail=f"Could not find seed class in {seed_filename}.py")

                # Instantiate and run the seed
                organizations = {user_org.name: user_org}
                seed_instance = seed_class(db, organizations, assessment_types)
                seed_instance.skip_wire_connections = not wire_connections
                result = seed_instance.seed()

                # Extract framework from result BEFORE commit
                # The result structure can be: {"framework": framework_obj} or {"frameworks": {"NAME": framework_obj}}
                framework = None
                if "framework" in result:
                    framework = result["framework"]
                elif "frameworks" in result:
                    # Handle the case where result has "frameworks" dictionary
                    frameworks_dict = result["frameworks"]
                    if isinstance(frameworks_dict, dict) and len(frameworks_dict) > 0:
                        # Get the first (and usually only) framework from the dict
                        framework = next(iter(frameworks_dict.values()))

                if not framework:
                    # Fallback: try to find framework by name
                    framework = db.query(models.Framework).filter(
                        models.Framework.organisation_id == user_org.id
                    ).order_by(models.Framework.created_at.desc()).first()

                    if not framework:
                        raise HTTPException(status_code=500, detail="Framework was created but could not be retrieved")

                # Now commit the transaction
                db.commit()

            except ImportError as e:
                logger.error(f"Could not import seed module {seed_module_path}: {e}")
                raise HTTPException(status_code=400, detail=f"Unknown template: {template_id}")
            except HTTPException:
                # Re-raise HTTP exceptions (like duplicate framework check)
                db.rollback()
                raise
            except Exception as e:
                logger.error(f"Error loading custom seed {template_id}: {e}")
                db.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=f"Error loading custom framework template: {str(e)}"
                )

        return schemas.FrameworkResponse(
            id=framework.id,
            name=framework.name,
            description=framework.description,
            created_at=framework.created_at,
            updated_at=framework.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        # Log the full error details for debugging
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error seeding framework template {template_id}: {str(e)}")
        logger.error(f"Full traceback: {error_details}")

        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                           detail=f"An error occurred while seeding framework template {template_id}: {str(e)}")

@router.get("/update-prompts-guide", response_class=FileResponse)
def download_update_prompts_guide(
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Download the Framework Update Prompts Guide.
    Only accessible by super_admin users.
    """
    # Check if user is super_admin
    if current_user.role_name != 'super_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This resource is only available to super administrators."
        )

    # Get the file path
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "static",
        "framework_update_prompts.txt"
    )

    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Framework update prompts guide not found"
        )

    # Return the file
    return FileResponse(
        path=file_path,
        filename="framework_update_prompts_guide.txt",
        media_type="text/plain"
    )

@router.get("/{framework_id}/entity-counts")
def get_framework_entity_counts(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get framework-scoped entity counts (risks, controls, policies, objectives linked to this framework)."""
    from ..services import chain_links_service

    framework = framework_repository.get_framework(db, framework_id=framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")

    return chain_links_service.get_framework_entity_counts(db, str(framework_id))


@router.get("/{framework_id}/chain-links-status", response_model=schemas.ChainLinksStatus)
def get_chain_links_status(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Check if a framework has a chain links mapping and whether it's already imported."""
    from ..services import chain_links_service

    framework = framework_repository.get_framework(db, framework_id=framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")

    return schemas.ChainLinksStatus(
        has_mapping=chain_links_service.has_mapping(framework.name),
        already_imported=chain_links_service.is_already_imported(db, str(framework_id)),
        framework_name=framework.name,
    )


@router.post("/{framework_id}/import-chain-links", response_model=schemas.ChainLinksImportResult)
def import_chain_links(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Import chain links (risks, controls, policies, junction tables) for a framework."""
    from ..services import chain_links_service

    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organisation admins and super admins can import chain links"
        )

    framework = framework_repository.get_framework(db, framework_id=framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")

    if not chain_links_service.has_mapping(framework.name):
        raise HTTPException(
            status_code=400,
            detail=f"No chain links mapping available for framework '{framework.name}'"
        )

    try:
        result = chain_links_service.import_chain_links(
            db, str(framework_id), str(current_user.organisation_id)
        )
        db.commit()
        return schemas.ChainLinksImportResult(**result)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing chain links for framework {framework_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while importing chain links: {str(e)}"
        )


@router.get("/{framework_id}/check-chain-links-updates", response_model=schemas.ChainLinksUpdateCheck)
def check_chain_links_updates(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Check if there are pending chain link updates (new entities, links, or field changes)."""
    from ..services import chain_links_service

    framework = framework_repository.get_framework(db, framework_id=framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")

    if not chain_links_service.has_mapping(framework.name):
        raise HTTPException(
            status_code=400,
            detail=f"No chain links mapping available for framework '{framework.name}'"
        )

    try:
        result = chain_links_service.check_chain_links_updates(
            db, str(framework_id), str(current_user.organisation_id)
        )
        return schemas.ChainLinksUpdateCheck(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error checking chain links updates for framework {framework_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while checking for updates: {str(e)}"
        )


@router.post("/{framework_id}/apply-chain-links-updates", response_model=schemas.ChainLinksUpdateResult)
def apply_chain_links_updates(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Apply pending chain link updates (create missing entities/links and update objective fields)."""
    from ..services import chain_links_service

    if current_user.role_name not in ['super_admin', 'org_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organisation admins and super admins can apply chain link updates"
        )

    framework = framework_repository.get_framework(db, framework_id=framework_id)
    if not framework:
        raise HTTPException(status_code=404, detail="Framework not found")

    if not chain_links_service.has_mapping(framework.name):
        raise HTTPException(
            status_code=400,
            detail=f"No chain links mapping available for framework '{framework.name}'"
        )

    try:
        result = chain_links_service.apply_chain_links_updates(
            db, str(framework_id), str(current_user.organisation_id)
        )
        db.commit()
        return schemas.ChainLinksUpdateResult(**result)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error applying chain links updates for framework {framework_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while applying updates: {str(e)}"
        )


@router.get("/{framework_id}", response_model=schemas.FrameworkResponse)
def read_framework(framework_id: uuid.UUID, db: Session = Depends(get_db)):
    db_framework = framework_repository.get_framework(db, framework_id=framework_id)
    if db_framework is None:
        raise HTTPException(status_code=404, detail="Framework not found")
    return db_framework


@router.post("/questions", status_code=status.HTTP_201_CREATED)
def add_framework_questions(payload: schemas.FrameworkQuestionsCreate, db: Session = Depends(get_db)):
    # First, create all questions once and collect their IDs
    created_question_ids = []
    for question_data in payload.questions:
        if not question_data or not any(question_data.model_dump().values()) or not payload.questions:
            raise HTTPException(status_code=400, detail="Question data cannot be empty or null")
        created_question = question_repository.create_question(db=db, question=schemas.QuestionCreate(**question_data.model_dump()))
        created_question_ids.append(created_question.id)

    # Then, verify all frameworks exist
    for framework_id in payload.framework_ids:
        if not framework_id or not payload.framework_ids:
            raise HTTPException(status_code=400, detail="Framework ID cannot be empty or null")
        framework = framework_repository.get_framework(db, framework_id=framework_id)
        if not framework:
            raise HTTPException(status_code=404,detail=f"Framework with ID {framework_id} not found")

    # Finally, associate each question with each framework
    for framework_id in payload.framework_ids:
        for question_id in created_question_ids:
            framework_repository.create_framework_question(db=db,framework_id=framework_id,question_id=question_id)

    #for all framework_ids collect all assessment_ids. If found then for all assessment_ids and question id create answers_ids
    for framework_id in payload.framework_ids:
        framework_assessments = framework_repository.get_framework_assessments(db, framework_id=framework_id)
        if framework_assessments:
            for assessment in framework_assessments:
                for question_id in created_question_ids:
                    answer_data = schemas.AnswerCreate(question_id=question_id,assessment_id=assessment.id)
                    answer_repository.create_answer(db=db, answer=answer_data)

    return {"message": "Question(s) successfully added to framework(s)"}

@router.post("/clone", response_model=List[schemas.FrameworkResponse])
def clone_frameworks(payload: schemas.CloneFrameworksRequest, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    cloned_frameworks = framework_repository.clone_frameworks(
        db=db, 
        framework_ids=payload.framework_ids, 
        current_user=current_user, 
        custom_name=payload.custom_name,
        target_organization_id=payload.target_organization_id
    )
    return cloned_frameworks

@router.delete("/{framework_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_framework(framework_id: uuid.UUID, db: Session = Depends(get_db), current_user: schemas.UserBase = Depends(get_current_active_user)):
    try:
        # Only super_admin and org_admin can delete frameworks
        if current_user.role_name not in ['super_admin', 'org_admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only organisation admins and super admins can delete frameworks"
            )

        # Check if framework exists
        db_framework = framework_repository.get_framework(db, framework_id=framework_id)
        if db_framework is None:
            raise HTTPException(status_code=404, detail="Framework not found")

        # Ensure the framework belongs to the user's organisation (super_admin can delete any)
        if current_user.role_name != 'super_admin' and db_framework.organisation_id != current_user.organisation_id:
            raise HTTPException(status_code=404, detail="Framework not found")

        # Track the deletion in history
        history_repository.track_delete(
            db=db,
            table_name="frameworks",
            record_id=str(framework_id),
            user_id=current_user.id,
            user_email=current_user.email,
            organisation_id=current_user.organisation_id,
            old_data={
                "name": db_framework.name,
                "description": db_framework.description
            }
        )

        # Use the new cascading delete function
        success = framework_repository.delete_framework_with_relations(db, framework_id)
        if not success:
            raise HTTPException(status_code=404, detail="Framework not found")

        return None
    except HTTPException:
        raise
    except ValueError as e:
        # Handle validation errors (like policy dependencies) as 400 Bad Request
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                           detail=f"An error occurred while deleting the framework: {str(e)}")


# ==================== Excel Framework Seed Generation Endpoints ====================

@router.post("/analyze-excel", response_model=dict)
def analyze_excel_framework(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Analyze an Excel file for framework seed generation.
    Returns column mapping and deduplication metrics.
    Only accessible by super_admin users.
    """
    # Check if user is super_admin
    if current_user.role_name != 'super_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This feature is only available to super administrators."
        )

    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an Excel file (.xlsx or .xls)"
        )

    # Create temporary file
    temp_file = None
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name

        # Parse and analyze Excel file
        parser = ExcelFrameworkParser(temp_file_path)
        parser.parse_excel()

        # Detect columns
        column_mapping = parser.detect_columns()
        logger.info(f"Column mapping detected: {column_mapping}")

        # Parse framework data
        framework_data = parser.parse_framework_data()
        logger.info(f"Parsed {len(framework_data)} rows of data")

        # Analyze data for deduplication metrics
        metrics = parser.analyze_data(framework_data)
        logger.info(f"Analysis metrics: {metrics}")

        result = {
            "success": True,
            "filename": file.filename,
            "column_mapping": column_mapping,
            "metrics": metrics,
            "total_rows": len(framework_data)
        }
        logger.info(f"Returning result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error analyzing Excel file: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while analyzing the Excel file: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@router.post("/generate-seed-file", response_model=dict)
def generate_framework_seed_file(
    file: UploadFile = File(...),
    framework_name: str = Form(...),
    framework_description: str = Form(""),
    allowed_scope_types: Optional[str] = Form(None),  # JSON string: '["Product", "Organization"]'
    scope_selection_mode: Optional[str] = Form("optional"),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Generate a Python seed file from an Excel framework file.
    Creates a new seed file with deduplicated questions and objectives.
    Only accessible by super_admin users.
    """
    # Check if user is super_admin
    if current_user.role_name != 'super_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This feature is only available to super administrators."
        )

    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an Excel file (.xlsx or .xls)"
        )

    # Validate framework name
    if not framework_name or not framework_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Framework name is required"
        )

    # Create temporary file
    temp_file = None
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name

        # Parse Excel file
        parser = ExcelFrameworkParser(temp_file_path)
        parser.parse_excel()
        parser.detect_columns()
        framework_data = parser.parse_framework_data()

        # Parse allowed_scope_types from JSON string if provided
        import json
        parsed_allowed_scope_types = None
        if allowed_scope_types:
            try:
                parsed_allowed_scope_types = json.loads(allowed_scope_types)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON format for allowed_scope_types"
                )

        # Generate seed file content
        seed_content = parser.generate_seed_file_content(
            framework_name=framework_name,
            framework_description=framework_description,
            framework_data=framework_data,
            allowed_scope_types=parsed_allowed_scope_types,
            scope_selection_mode=scope_selection_mode
        )

        # Generate filename from framework name (sanitize for Python module naming)
        # Remove parentheses and other special characters that are invalid in Python module names
        sanitized_name = framework_name.lower()
        sanitized_name = sanitized_name.replace('(', '').replace(')', '').replace('[', '').replace(']', '')
        sanitized_name = sanitized_name.replace(' ', '_').replace('-', '_').replace('.', '_').replace(',', '_')
        # Remove multiple consecutive underscores
        while '__' in sanitized_name:
            sanitized_name = sanitized_name.replace('__', '_')
        # Remove leading/trailing underscores
        sanitized_name = sanitized_name.strip('_')
        seed_filename = f"{sanitized_name}_seed.py"

        # Save seed file to app/seeds directory
        seeds_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "seeds"
        )
        seed_file_path = os.path.join(seeds_dir, seed_filename)

        # Check if file already exists
        if os.path.exists(seed_file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Seed file already exists: {seed_filename}. Please use a different framework name or delete the existing file."
            )

        # Write seed file
        with open(seed_file_path, 'w', encoding='utf-8') as f:
            f.write(seed_content)

        logger.info(f"Generated seed file: {seed_file_path}")

        # Handle logo file if provided
        logo_saved = False
        logo_filename = None
        if logo and logo.filename:
            # Validate logo file type
            allowed_extensions = ('.png', '.jpg', '.jpeg', '.svg', '.webp', '.gif')
            if not logo.filename.lower().endswith(allowed_extensions):
                logger.warning(f"Invalid logo file type: {logo.filename}")
            else:
                # Get file extension
                file_ext = os.path.splitext(logo.filename)[1]

                # Generate logo filename using sanitized framework name
                logo_filename = f"{sanitized_name}_logo{file_ext}"

                # Determine frontend assets directory path
                # Navigate from current file to project root, then to frontend assets
                # __file__ is in cyberbridge_backend/app/routers/frameworks_controller.py
                # Go up 4 levels to project root: routers -> app -> cyberbridge_backend -> project_root
                frontend_assets_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                    "cyberbridge_frontend",
                    "src",
                    "assets"
                )

                # Create assets directory if it doesn't exist
                os.makedirs(frontend_assets_dir, exist_ok=True)

                logo_path = os.path.join(frontend_assets_dir, logo_filename)

                # Save logo file
                try:
                    with open(logo_path, 'wb') as logo_file:
                        shutil.copyfileobj(logo.file, logo_file)
                    logger.info(f"Saved framework logo: {logo_path}")
                    logo_saved = True
                except Exception as logo_error:
                    logger.error(f"Failed to save logo: {str(logo_error)}")

        # Get metrics for response
        metrics = parser.analyze_data(framework_data)

        message = f"Seed file generated successfully: {seed_filename}"
        if logo_saved:
            message += f". Logo saved as: {logo_filename}"

        return {
            "success": True,
            "message": message,
            "filename": seed_filename,
            "file_path": seed_file_path,
            "metrics": metrics,
            "logo_saved": logo_saved,
            "logo_filename": logo_filename if logo_saved else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating seed file: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating the seed file: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


# ==================== Framework Updates Endpoints ====================

@router.get("/{framework_id}/updates", response_model=List[dict])
def get_framework_updates(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Get all available updates for a framework.
    Returns both applied and unapplied updates.
    """
    try:
        updates = FrameworkUpdateService.get_available_updates(db, framework_id)
        return updates
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching framework updates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching updates: {str(e)}"
        )


@router.get("/{framework_id}/updates/{version}/preview", response_model=dict)
def preview_framework_update(
    framework_id: uuid.UUID,
    version: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Get a preview of what will change when applying an update.
    Shows new questions, chapters, objectives, and updated objectives.
    """
    try:
        preview = FrameworkUpdateService.get_update_preview(db, framework_id, version)
        return preview
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error previewing framework update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while previewing update: {str(e)}"
        )


@router.post("/{framework_id}/updates/{version}/apply", response_model=dict)
def apply_framework_update(
    framework_id: uuid.UUID,
    version: int,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """
    Apply an update to a framework.
    Creates new questions, chapters, objectives and updates existing objectives.
    """
    try:
        result = FrameworkUpdateService.apply_update(db, framework_id, version, current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error applying framework update: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while applying update: {str(e)}"
        )


@router.get("/{framework_id}/snapshots")
def list_framework_snapshots(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """List all snapshots for a framework."""
    if current_user.role_name not in ["super_admin", "org_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        from app.services.framework_snapshot_service import FrameworkSnapshotService
        return FrameworkSnapshotService.list_snapshots(db, framework_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{framework_id}/snapshots/{snapshot_id}/revert")
def revert_framework_snapshot(
    framework_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Revert a framework to a previous snapshot state."""
    if current_user.role_name not in ["super_admin", "org_admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        from app.services.framework_snapshot_service import FrameworkSnapshotService
        result = FrameworkSnapshotService.revert_to_snapshot(db, framework_id, snapshot_id, current_user.id)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{framework_id}/scope-config", response_model=schemas.FrameworkScopeConfig)
def get_framework_scope_config(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: schemas.UserBase = Depends(get_current_active_user)
):
    """Get scope configuration for a framework"""
    try:
        from app.services import scope_validation_service
        config = scope_validation_service.get_framework_scope_config(db, framework_id)
        return config
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting framework scope config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred: {str(e)}"
        )
