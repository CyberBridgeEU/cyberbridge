# backup_service.py
"""
Backup and Restore Service for Organization Data

Handles creating encrypted backups and restoring organization data including:
- Users (org-scoped)
- Frameworks, Chapters, Objectives, FrameworkQuestions
- Assessments, Answers, Evidence (metadata + files)
- Policies, PolicyFrameworks, PolicyObjectives
- Products, Criticalities, CriticalityOptions
- Risks, RiskCategories
- QuestionCorrelations
- OrganizationLLMSettings
- History, ScannerHistory
"""
import os
import json
import uuid
import shutil
import zipfile
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import models
from app.repositories import backup_repository
from app.database.database import get_db

logger = logging.getLogger(__name__)

# Base directory for backups
BACKUP_BASE_DIR = Path(__file__).parent.parent / "backups"

# Evidence files directory (relative to app root)
EVIDENCE_DIR = Path(__file__).parent.parent / "evidence_files"

# Encryption key derivation salt (should be stored securely in production)
ENCRYPTION_SALT = b'cyberbridge_backup_salt_2024'


def _get_encryption_key(org_id: str) -> bytes:
    """Derive an encryption key from the organization ID"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=ENCRYPTION_SALT,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(org_id.encode()))
    return key


def _encrypt_data(data: str, org_id: str) -> bytes:
    """Encrypt data using Fernet with org-derived key"""
    key = _get_encryption_key(org_id)
    f = Fernet(key)
    return f.encrypt(data.encode())


def _decrypt_data(encrypted_data: bytes, org_id: str) -> str:
    """Decrypt data using Fernet with org-derived key"""
    key = _get_encryption_key(org_id)
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()


def _serialize_uuid(obj: Any) -> Any:
    """Convert UUID objects to strings for JSON serialization"""
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_uuid(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_uuid(item) for item in obj]
    return obj


def _model_to_dict(model_instance) -> Dict[str, Any]:
    """Convert a SQLAlchemy model instance to a dictionary"""
    if model_instance is None:
        return None

    result = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        result[column.name] = _serialize_uuid(value)
    return result


def _collect_organisation_data(db: Session, organisation_id: uuid.UUID) -> Tuple[Dict[str, Any], int]:
    """
    Collect all data for an organization that needs to be backed up.
    Returns (data_dict, record_count_dict)
    """
    org_id = organisation_id
    data = {}
    counts = {}

    # 1. Users (org-scoped)
    users = db.query(models.User).filter(models.User.organisation_id == org_id).all()
    data['users'] = [_model_to_dict(u) for u in users]
    counts['users'] = len(users)
    user_ids = [u.id for u in users]

    # 2. Frameworks (org-scoped)
    frameworks = db.query(models.Framework).filter(models.Framework.organisation_id == org_id).all()
    data['frameworks'] = [_model_to_dict(f) for f in frameworks]
    counts['frameworks'] = len(frameworks)
    framework_ids = [f.id for f in frameworks]

    # 3. Chapters (linked to frameworks)
    chapters = db.query(models.Chapters).filter(models.Chapters.framework_id.in_(framework_ids)).all() if framework_ids else []
    data['chapters'] = [_model_to_dict(c) for c in chapters]
    counts['chapters'] = len(chapters)
    chapter_ids = [c.id for c in chapters]

    # 4. Objectives (linked to chapters)
    objectives = db.query(models.Objectives).filter(models.Objectives.chapter_id.in_(chapter_ids)).all() if chapter_ids else []
    data['objectives'] = [_model_to_dict(o) for o in objectives]
    counts['objectives'] = len(objectives)
    objective_ids = [o.id for o in objectives]

    # 5. FrameworkQuestions (linked to frameworks)
    framework_questions = db.query(models.FrameworkQuestion).filter(
        models.FrameworkQuestion.framework_id.in_(framework_ids)
    ).all() if framework_ids else []
    data['framework_questions'] = [_model_to_dict(fq) for fq in framework_questions]
    counts['framework_questions'] = len(framework_questions)

    # 6. Assessments (created by org users)
    assessments = db.query(models.Assessment).filter(models.Assessment.user_id.in_(user_ids)).all() if user_ids else []
    data['assessments'] = [_model_to_dict(a) for a in assessments]
    counts['assessments'] = len(assessments)
    assessment_ids = [a.id for a in assessments]

    # 7. Answers (linked to assessments)
    answers = db.query(models.Answer).filter(models.Answer.assessment_id.in_(assessment_ids)).all() if assessment_ids else []
    data['answers'] = [_model_to_dict(a) for a in answers]
    counts['answers'] = len(answers)
    answer_ids = [a.id for a in answers]

    # 8. Evidence (linked to answers)
    evidence = db.query(models.Evidence).filter(models.Evidence.answer_id.in_(answer_ids)).all() if answer_ids else []
    data['evidence'] = [_model_to_dict(e) for e in evidence]
    counts['evidence'] = len(evidence)

    # 9. Policies (org-scoped)
    policies = db.query(models.Policies).filter(models.Policies.organisation_id == org_id).all()
    data['policies'] = [_model_to_dict(p) for p in policies]
    counts['policies'] = len(policies)
    policy_ids = [p.id for p in policies]

    # 10. PolicyFrameworks (linked to policies)
    policy_frameworks = db.query(models.PolicyFrameworks).filter(
        models.PolicyFrameworks.policy_id.in_(policy_ids)
    ).all() if policy_ids else []
    data['policy_frameworks'] = [_model_to_dict(pf) for pf in policy_frameworks]
    counts['policy_frameworks'] = len(policy_frameworks)

    # 11. PolicyObjectives (linked to policies)
    policy_objectives = db.query(models.PolicyObjectives).filter(
        models.PolicyObjectives.policy_id.in_(policy_ids)
    ).all() if policy_ids else []
    data['policy_objectives'] = [_model_to_dict(po) for po in policy_objectives]
    counts['policy_objectives'] = len(policy_objectives)

    # 12. Criticalities (we backup all as they may be referenced)
    criticalities = db.query(models.Criticalities).all()
    data['criticalities'] = [_model_to_dict(c) for c in criticalities]
    counts['criticalities'] = len(criticalities)

    # 14. CriticalityOptions (linked to criticalities)
    criticality_ids = [c.id for c in criticalities]
    criticality_options = db.query(models.CriticalityOptions).filter(
        models.CriticalityOptions.criticality_id.in_(criticality_ids)
    ).all() if criticality_ids else []
    data['criticality_options'] = [_model_to_dict(co) for co in criticality_options]
    counts['criticality_options'] = len(criticality_options)

    # 15. Risks (org-scoped)
    risks = db.query(models.Risks).filter(models.Risks.organisation_id == org_id).all()
    data['risks'] = [_model_to_dict(r) for r in risks]
    counts['risks'] = len(risks)

    # 16. RiskCategories (we backup all as they may be referenced)
    risk_categories = db.query(models.RiskCategories).all()
    data['risk_categories'] = [_model_to_dict(rc) for rc in risk_categories]
    counts['risk_categories'] = len(risk_categories)

    # 17. QuestionCorrelations (org-scoped)
    question_correlations = db.query(models.QuestionCorrelation).filter(
        models.QuestionCorrelation.organisation_id == org_id
    ).all()
    data['question_correlations'] = [_model_to_dict(qc) for qc in question_correlations]
    counts['question_correlations'] = len(question_correlations)

    # 18. OrganizationLLMSettings (org-scoped)
    org_llm_settings = db.query(models.OrganizationLLMSettings).filter(
        models.OrganizationLLMSettings.organisation_id == org_id
    ).first()
    data['organization_llm_settings'] = _model_to_dict(org_llm_settings) if org_llm_settings else None
    counts['organization_llm_settings'] = 1 if org_llm_settings else 0

    # 19. History (org-scoped)
    history = db.query(models.History).filter(models.History.organisation_id == org_id).all()
    data['history'] = [_model_to_dict(h) for h in history]
    counts['history'] = len(history)

    # 20. ScannerHistory (org-scoped)
    scanner_history = db.query(models.ScannerHistory).filter(
        models.ScannerHistory.organisation_id == org_id
    ).all()
    data['scanner_history'] = [_model_to_dict(sh) for sh in scanner_history]
    counts['scanner_history'] = len(scanner_history)

    return data, counts


def _copy_evidence_files(
    evidence_records: List[Dict],
    backup_dir: Path
) -> int:
    """
    Copy evidence files to the backup directory.
    Returns the count of files copied.
    """
    evidence_backup_dir = backup_dir / "evidence"
    evidence_backup_dir.mkdir(parents=True, exist_ok=True)

    files_copied = 0
    for evidence in evidence_records:
        if evidence.get('filepath'):
            source_path = Path(evidence['filepath'])
            if source_path.exists():
                # Create subdirectory for each answer_id
                answer_id = evidence.get('answer_id', 'unknown')
                answer_dir = evidence_backup_dir / str(answer_id)
                answer_dir.mkdir(parents=True, exist_ok=True)

                dest_path = answer_dir / source_path.name
                try:
                    shutil.copy2(source_path, dest_path)
                    files_copied += 1
                except Exception as e:
                    logger.warning(f"Failed to copy evidence file {source_path}: {e}")

    return files_copied


def create_backup_for_organisation(
    db: Session,
    organisation_id: uuid.UUID,
    backup_type: str = 'manual',
    created_by: Optional[uuid.UUID] = None
) -> models.Backup:
    """
    Create a complete backup for an organization.

    Returns the Backup record on success, raises an exception on failure.
    """
    org_id_str = str(organisation_id)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"backup_{timestamp}.zip"

    # Get organization for retention settings
    org = db.query(models.Organisations).filter(models.Organisations.id == organisation_id).first()
    if not org:
        raise ValueError(f"Organisation {organisation_id} not found")

    # Calculate expiration date
    expires_at = datetime.utcnow() + timedelta(days=org.backup_retention_years * 365)

    # Create backup directory
    org_backup_dir = BACKUP_BASE_DIR / org_id_str
    org_backup_dir.mkdir(parents=True, exist_ok=True)

    backup_dir = org_backup_dir / f"backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    filepath = org_backup_dir / filename

    # Create initial backup record with in_progress status
    backup_record = backup_repository.create_backup(
        db=db,
        organisation_id=organisation_id,
        filename=filename,
        filepath=str(filepath),
        file_size=0,
        expires_at=expires_at,
        backup_type=backup_type,
        status='in_progress',
        created_by=created_by
    )

    try:
        # Collect all organization data
        data, counts = _collect_organisation_data(db, organisation_id)

        # Create metadata
        metadata = {
            'organisation_id': org_id_str,
            'organisation_name': org.name,
            'backup_version': '1.0',
            'created_at': datetime.utcnow().isoformat(),
            'backup_type': backup_type,
            'records_count': counts
        }

        # Write metadata file
        metadata_path = backup_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Encrypt and write data
        data_json = json.dumps(data, indent=2)
        encrypted_data = _encrypt_data(data_json, org_id_str)

        encrypted_data_path = backup_dir / "data.json.enc"
        with open(encrypted_data_path, 'wb') as f:
            f.write(encrypted_data)

        # Copy evidence files
        evidence_files_count = _copy_evidence_files(data.get('evidence', []), backup_dir)

        # Create ZIP archive
        with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(backup_dir)
                    zipf.write(file_path, arcname)

        # Get file size
        file_size = filepath.stat().st_size

        # Clean up temporary directory
        shutil.rmtree(backup_dir)

        # Update backup record with success
        backup_repository.update_backup_status(
            db=db,
            backup_id=backup_record.id,
            status='completed',
            records_count=json.dumps(counts),
            evidence_files_count=evidence_files_count,
            file_size=file_size
        )

        # Update organization's last backup info
        backup_repository.update_organisation_last_backup(
            db=db,
            organisation_id=organisation_id,
            last_backup_at=datetime.utcnow(),
            last_backup_status='success'
        )

        logger.info(f"Backup created successfully for organisation {organisation_id}: {filename}")
        return db.query(models.Backup).filter(models.Backup.id == backup_record.id).first()

    except Exception as e:
        logger.error(f"Backup failed for organisation {organisation_id}: {str(e)}")

        # Update backup record with failure
        backup_repository.update_backup_status(
            db=db,
            backup_id=backup_record.id,
            status='failed',
            error_message=str(e)
        )

        # Update organization's last backup info
        backup_repository.update_organisation_last_backup(
            db=db,
            organisation_id=organisation_id,
            last_backup_at=datetime.utcnow(),
            last_backup_status='failed'
        )

        # Clean up temporary directory if it exists
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

        raise


def restore_backup_for_organisation(
    db: Session,
    organisation_id: uuid.UUID,
    backup_id: uuid.UUID
) -> Dict[str, Any]:
    """
    Restore organization data from a backup.

    This operation:
    1. Validates the backup belongs to the organization
    2. Extracts and decrypts the backup data
    3. Clears existing org data (within transaction)
    4. Restores data from backup
    5. Restores evidence files

    Returns a dict with restore results on success, raises exception on failure.
    """
    # Get the backup record
    backup = backup_repository.get_backup_by_id(db, backup_id)
    if not backup:
        raise ValueError(f"Backup {backup_id} not found")

    if backup.organisation_id != organisation_id:
        raise ValueError("Backup does not belong to this organization")

    if backup.status != 'completed':
        raise ValueError("Cannot restore from a non-completed backup")

    org_id_str = str(organisation_id)
    filepath = Path(backup.filepath)

    if not filepath.exists():
        raise ValueError(f"Backup file not found: {filepath}")

    # Create temporary extraction directory
    extract_dir = filepath.parent / f"restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    extract_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Extract ZIP
        with zipfile.ZipFile(filepath, 'r') as zipf:
            zipf.extractall(extract_dir)

        # Read and decrypt data
        encrypted_data_path = extract_dir / "data.json.enc"
        with open(encrypted_data_path, 'rb') as f:
            encrypted_data = f.read()

        data_json = _decrypt_data(encrypted_data, org_id_str)
        data = json.loads(data_json)

        # Read metadata
        metadata_path = extract_dir / "metadata.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        # Restore data within a transaction
        records_restored = _restore_data(db, organisation_id, data)

        # Restore evidence files
        evidence_dir = extract_dir / "evidence"
        evidence_files_restored = 0
        if evidence_dir.exists():
            evidence_files_restored = _restore_evidence_files(evidence_dir, data.get('evidence', []))

        # Clean up
        shutil.rmtree(extract_dir)

        logger.info(f"Restore completed successfully for organisation {organisation_id} from backup {backup_id}")

        return {
            'success': True,
            'message': 'Restore completed successfully',
            'records_restored': records_restored,
            'evidence_files_restored': evidence_files_restored
        }

    except Exception as e:
        logger.error(f"Restore failed for organisation {organisation_id}: {str(e)}")

        # Clean up
        if extract_dir.exists():
            shutil.rmtree(extract_dir)

        raise


def _restore_data(db: Session, organisation_id: uuid.UUID, data: Dict[str, Any]) -> Dict[str, int]:
    """
    Restore all organization data from backup.
    This performs a complete replacement of org-scoped data.
    """
    counts = {}

    # Get user IDs for this org before clearing
    org_users = db.query(models.User).filter(models.User.organisation_id == organisation_id).all()
    user_ids = [u.id for u in org_users]

    # Get framework IDs for this org before clearing
    org_frameworks = db.query(models.Framework).filter(models.Framework.organisation_id == organisation_id).all()
    framework_ids = [f.id for f in org_frameworks]

    # Delete existing org-scoped data in reverse dependency order
    # Note: We're careful to only delete org-scoped data

    # Delete scanner history
    db.query(models.ScannerHistory).filter(
        models.ScannerHistory.organisation_id == organisation_id
    ).delete(synchronize_session=False)

    # Delete history
    db.query(models.History).filter(
        models.History.organisation_id == organisation_id
    ).delete(synchronize_session=False)

    # Delete question correlations
    db.query(models.QuestionCorrelation).filter(
        models.QuestionCorrelation.organisation_id == organisation_id
    ).delete(synchronize_session=False)

    # Delete org LLM settings
    db.query(models.OrganizationLLMSettings).filter(
        models.OrganizationLLMSettings.organisation_id == organisation_id
    ).delete(synchronize_session=False)

    # Delete risks
    db.query(models.Risks).filter(
        models.Risks.organisation_id == organisation_id
    ).delete(synchronize_session=False)

    # Delete policies and related data
    policy_ids = [p.id for p in db.query(models.Policies).filter(
        models.Policies.organisation_id == organisation_id
    ).all()]

    if policy_ids:
        db.query(models.PolicyObjectives).filter(
            models.PolicyObjectives.policy_id.in_(policy_ids)
        ).delete(synchronize_session=False)

        db.query(models.PolicyFrameworks).filter(
            models.PolicyFrameworks.policy_id.in_(policy_ids)
        ).delete(synchronize_session=False)

        db.query(models.Policies).filter(
            models.Policies.id.in_(policy_ids)
        ).delete(synchronize_session=False)

    # Delete assessments, answers, evidence
    if user_ids:
        assessment_ids = [a.id for a in db.query(models.Assessment).filter(
            models.Assessment.user_id.in_(user_ids)
        ).all()]

        if assessment_ids:
            answer_ids = [a.id for a in db.query(models.Answer).filter(
                models.Answer.assessment_id.in_(assessment_ids)
            ).all()]

            if answer_ids:
                db.query(models.Evidence).filter(
                    models.Evidence.answer_id.in_(answer_ids)
                ).delete(synchronize_session=False)

            db.query(models.Answer).filter(
                models.Answer.assessment_id.in_(assessment_ids)
            ).delete(synchronize_session=False)

            db.query(models.Assessment).filter(
                models.Assessment.id.in_(assessment_ids)
            ).delete(synchronize_session=False)

    # Delete frameworks, chapters, objectives, framework_questions
    if framework_ids:
        chapter_ids = [c.id for c in db.query(models.Chapters).filter(
            models.Chapters.framework_id.in_(framework_ids)
        ).all()]

        if chapter_ids:
            db.query(models.Objectives).filter(
                models.Objectives.chapter_id.in_(chapter_ids)
            ).delete(synchronize_session=False)

            db.query(models.Chapters).filter(
                models.Chapters.id.in_(chapter_ids)
            ).delete(synchronize_session=False)

        db.query(models.FrameworkQuestion).filter(
            models.FrameworkQuestion.framework_id.in_(framework_ids)
        ).delete(synchronize_session=False)

        db.query(models.Framework).filter(
            models.Framework.id.in_(framework_ids)
        ).delete(synchronize_session=False)

    db.commit()

    # Now restore data from backup
    # Note: We don't restore users as that would require password handling
    # Users should be managed separately

    # Restore frameworks
    for f_data in data.get('frameworks', []):
        framework = models.Framework(
            id=uuid.UUID(f_data['id']),
            name=f_data['name'],
            description=f_data.get('description'),
            organisation_id=organisation_id,
            _allowed_scope_types=f_data.get('_allowed_scope_types'),
            scope_selection_mode=f_data.get('scope_selection_mode', 'optional')
        )
        db.add(framework)
    counts['frameworks'] = len(data.get('frameworks', []))

    # Restore chapters
    for c_data in data.get('chapters', []):
        chapter = models.Chapters(
            id=uuid.UUID(c_data['id']),
            title=c_data['title'],
            framework_id=uuid.UUID(c_data['framework_id'])
        )
        db.add(chapter)
    counts['chapters'] = len(data.get('chapters', []))

    # Restore objectives
    for o_data in data.get('objectives', []):
        objective = models.Objectives(
            id=uuid.UUID(o_data['id']),
            title=o_data['title'],
            subchapter=o_data.get('subchapter'),
            chapter_id=uuid.UUID(o_data['chapter_id']),
            requirement_description=o_data.get('requirement_description'),
            objective_utilities=o_data.get('objective_utilities'),
            compliance_status_id=uuid.UUID(o_data['compliance_status_id']) if o_data.get('compliance_status_id') else None
        )
        db.add(objective)
    counts['objectives'] = len(data.get('objectives', []))

    # Restore framework questions
    for fq_data in data.get('framework_questions', []):
        fq = models.FrameworkQuestion(
            framework_id=uuid.UUID(fq_data['framework_id']),
            question_id=uuid.UUID(fq_data['question_id']),
            order=fq_data.get('order', 0)
        )
        db.add(fq)
    counts['framework_questions'] = len(data.get('framework_questions', []))

    # Restore policies
    for p_data in data.get('policies', []):
        policy = models.Policies(
            id=uuid.UUID(p_data['id']),
            title=p_data['title'],
            owner=p_data.get('owner'),
            status_id=uuid.UUID(p_data['status_id']),
            body=p_data.get('body'),
            company_name=p_data.get('company_name'),
            organisation_id=organisation_id,
            created_by=uuid.UUID(p_data['created_by']) if p_data.get('created_by') else None,
            last_updated_by=uuid.UUID(p_data['last_updated_by']) if p_data.get('last_updated_by') else None
        )
        db.add(policy)
    counts['policies'] = len(data.get('policies', []))

    # Restore policy frameworks
    for pf_data in data.get('policy_frameworks', []):
        pf = models.PolicyFrameworks(
            policy_id=uuid.UUID(pf_data['policy_id']),
            framework_id=uuid.UUID(pf_data['framework_id'])
        )
        db.add(pf)
    counts['policy_frameworks'] = len(data.get('policy_frameworks', []))

    # Restore policy objectives
    for po_data in data.get('policy_objectives', []):
        po = models.PolicyObjectives(
            policy_id=uuid.UUID(po_data['policy_id']),
            objective_id=uuid.UUID(po_data['objective_id']),
            order=po_data.get('order', 0)
        )
        db.add(po)
    counts['policy_objectives'] = len(data.get('policy_objectives', []))

    # Restore risks (support both new 'asset_category_id' and old 'product_type_id' keys for backward compat)
    for r_data in data.get('risks', []):
        ac_id = r_data.get('asset_category_id') or r_data.get('product_type_id')
        risk = models.Risks(
            id=uuid.UUID(r_data['id']),
            asset_category_id=uuid.UUID(ac_id) if ac_id else None,
            risk_category_name=r_data['risk_category_name'],
            risk_category_description=r_data.get('risk_category_description'),
            risk_potential_impact=r_data.get('risk_potential_impact'),
            risk_control=r_data.get('risk_control'),
            likelihood=uuid.UUID(r_data['likelihood']),
            residual_risk=uuid.UUID(r_data['residual_risk']),
            risk_severity_id=uuid.UUID(r_data['risk_severity_id']),
            risk_status_id=uuid.UUID(r_data['risk_status_id']),
            organisation_id=organisation_id,
            scope_id=uuid.UUID(r_data['scope_id']) if r_data.get('scope_id') else None,
            scope_entity_id=uuid.UUID(r_data['scope_entity_id']) if r_data.get('scope_entity_id') else None,
            created_by=uuid.UUID(r_data['created_by']) if r_data.get('created_by') else None,
            last_updated_by=uuid.UUID(r_data['last_updated_by']) if r_data.get('last_updated_by') else None
        )
        db.add(risk)
    counts['risks'] = len(data.get('risks', []))

    # Restore question correlations
    for qc_data in data.get('question_correlations', []):
        qc = models.QuestionCorrelation(
            id=uuid.UUID(qc_data['id']),
            question_a_id=uuid.UUID(qc_data['question_a_id']),
            question_b_id=uuid.UUID(qc_data['question_b_id']),
            organisation_id=organisation_id,
            scope_id=uuid.UUID(qc_data['scope_id']),
            scope_entity_id=uuid.UUID(qc_data['scope_entity_id']) if qc_data.get('scope_entity_id') else None,
            created_by=uuid.UUID(qc_data['created_by'])
        )
        db.add(qc)
    counts['question_correlations'] = len(data.get('question_correlations', []))

    # Restore org LLM settings
    if data.get('organization_llm_settings'):
        llm_data = data['organization_llm_settings']
        llm_settings = models.OrganizationLLMSettings(
            id=uuid.UUID(llm_data['id']),
            organisation_id=organisation_id,
            llm_provider=llm_data['llm_provider'],
            qlon_url=llm_data.get('qlon_url'),
            qlon_api_key=llm_data.get('qlon_api_key'),
            qlon_use_tools=llm_data.get('qlon_use_tools'),
            openai_api_key=llm_data.get('openai_api_key'),
            openai_model=llm_data.get('openai_model'),
            openai_base_url=llm_data.get('openai_base_url'),
            anthropic_api_key=llm_data.get('anthropic_api_key'),
            anthropic_model=llm_data.get('anthropic_model'),
            xai_api_key=llm_data.get('xai_api_key'),
            xai_model=llm_data.get('xai_model'),
            xai_base_url=llm_data.get('xai_base_url'),
            google_api_key=llm_data.get('google_api_key'),
            google_model=llm_data.get('google_model'),
            is_enabled=llm_data.get('is_enabled', False),
            ai_remediator_enabled=llm_data.get('ai_remediator_enabled', False),
            remediator_prompt_zap=llm_data.get('remediator_prompt_zap'),
            remediator_prompt_nmap=llm_data.get('remediator_prompt_nmap')
        )
        db.add(llm_settings)
        counts['organization_llm_settings'] = 1

    # Note: We don't restore assessments, answers, and evidence as they may have
    # foreign key dependencies on users. These should be handled separately.
    # For now, we skip them to avoid integrity issues.
    counts['assessments'] = 0
    counts['answers'] = 0
    counts['evidence'] = 0

    db.commit()
    return counts


def _restore_evidence_files(evidence_dir: Path, evidence_records: List[Dict]) -> int:
    """Restore evidence files from backup to their original locations"""
    files_restored = 0

    for evidence in evidence_records:
        if evidence.get('filepath') and evidence.get('answer_id'):
            answer_id = evidence['answer_id']
            original_filename = Path(evidence['filepath']).name
            source_path = evidence_dir / str(answer_id) / original_filename

            if source_path.exists():
                dest_path = Path(evidence['filepath'])
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(source_path, dest_path)
                    files_restored += 1
                except Exception as e:
                    logger.warning(f"Failed to restore evidence file {source_path}: {e}")

    return files_restored


async def run_scheduled_backups():
    """
    Check all organizations and run backups for those that are due.
    This function is called by the scheduler.
    """
    logger.info("Running scheduled backup check...")

    db = next(get_db())
    try:
        due_orgs = backup_repository.get_organisations_due_for_backup(db)

        for org in due_orgs:
            try:
                logger.info(f"Creating scheduled backup for organisation {org.id} ({org.name})")
                create_backup_for_organisation(
                    db=db,
                    organisation_id=org.id,
                    backup_type='scheduled'
                )
            except Exception as e:
                logger.error(f"Scheduled backup failed for organisation {org.id}: {str(e)}")

        logger.info(f"Scheduled backup check completed. Processed {len(due_orgs)} organizations.")

    finally:
        db.close()


async def cleanup_expired_backups():
    """
    Delete backups that have passed their expiration date.
    This function is called by the scheduler.
    """
    logger.info("Running expired backup cleanup...")

    db = next(get_db())
    try:
        expired_backups = backup_repository.get_expired_backups(db)

        for backup in expired_backups:
            try:
                # Delete the backup file
                filepath = Path(backup.filepath)
                if filepath.exists():
                    filepath.unlink()
                    logger.info(f"Deleted expired backup file: {filepath}")

                # Delete the backup record
                backup_repository.delete_backup(db, backup.id)
                logger.info(f"Deleted expired backup record: {backup.id}")

            except Exception as e:
                logger.error(f"Failed to cleanup expired backup {backup.id}: {str(e)}")

        logger.info(f"Expired backup cleanup completed. Removed {len(expired_backups)} backups.")

    finally:
        db.close()


def delete_backup_file(db: Session, backup_id: uuid.UUID) -> bool:
    """Delete a backup file and its record"""
    backup = backup_repository.get_backup_by_id(db, backup_id)
    if not backup:
        return False

    # Delete the file
    filepath = Path(backup.filepath)
    if filepath.exists():
        filepath.unlink()

    # Delete the record
    return backup_repository.delete_backup(db, backup_id)
