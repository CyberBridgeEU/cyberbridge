# crud.py
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
import uuid
import logging
from app.services.security_service import get_password_hash
from app.services import risk_seeding_service
from app.seeds.asset_types_seed import AssetTypesSeed
from app.models import models
from app.dtos import schemas

logger = logging.getLogger(__name__)

# User CRUD operations
def get_user(db: Session, user_id: uuid.UUID):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    result = db.query(models.User.id,models.User.email,models.User.hashed_password,models.User.auth_provider,models.User.role_id,models.User.organisation_id,models.User.status,models.User.must_change_password,models.Role.role_name,models.Organisations.name.label("organisation_name"),models.Organisations.logo.label("organisation_logo"),models.Organisations.domain.label("organisation_domain")
    ).join(
        models.Role, models.User.role_id == models.Role.id
    ).join(
        models.Organisations, models.User.organisation_id == models.Organisations.id, isouter=True
    ).filter(models.User.email == email).first()

    if not result:
        return None

    user = models.User()
    user.id = result.id
    user.email = result.email
    user.hashed_password = result.hashed_password
    user.auth_provider = result.auth_provider
    user.role_id = result.role_id
    user.organisation_id = result.organisation_id
    user.status = result.status
    user.must_change_password = result.must_change_password
    user.role_name = result.role_name
    user.organisation_name = result.organisation_name
    user.organisation_logo = result.organisation_logo
    user.organisation_domain = result.organisation_domain

    return user

def get_current_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email, models.User.status == "active").first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(
        models.User.id,
        models.User.email,
        models.User.role_id,
        models.User.status,
        models.User.auth_provider,
                models.Role.role_name,
        models.Organisations.id.label("organisation_id"),
        models.Organisations.name.label("organisation_name"),
        models.Organisations.logo.label("organisation_logo")
    ).join(
        models.Organisations,
        models.User.organisation_id == models.Organisations.id,
        isouter=True
    ).join(
        models.Role,
        models.User.role_id == models.Role.id,
        isouter=True  # Using outer join in case some users don't have a role assigned
    ).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):

    # Hash the password securely
    hashed_password = get_password_hash(user.password)
    
    # Determine status based on role - super_admin and org_admin get active, org_user gets pending_approval
    role = db.query(models.Role).filter(models.Role.id == user.role_id).first()
    user_status = "active" if role and role.role_name in ["super_admin", "org_admin"] else "pending_approval"

    db_user = models.User(name=user.name,email=str(user.email),hashed_password=hashed_password,role_id=user.role_id, organisation_id=user.organisation_id,status=user_status)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_user_in_organisation(db, user):
    auth_provider = getattr(user, 'auth_provider', 'local')

    # Hash password for local users, None for SSO users
    if auth_provider == 'local':
        if not user.password:
            raise HTTPException(status_code=400, detail="Password required for local accounts")
        hashed_password = get_password_hash(user.password)
    else:
        hashed_password = None

    # Get the role and organisation for names
    role = db.query(models.Role).filter(models.Role.id == uuid.UUID(user.role_id)).first()
    organisation = db.query(models.Organisations).filter(models.Organisations.id == uuid.UUID(user.organisation_id)).first()

    #check if user email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # Determine status based on role
    role = db.query(models.Role).filter(models.Role.id == uuid.UUID(user.role_id)).first()
    user_status = "active" if role and role.role_name in ["super_admin", "org_admin"] else "pending_approval"

    db_user = models.User(name=user.email.split('@')[0], email=str(user.email), hashed_password=hashed_password, auth_provider=auth_provider, role_id=user.role_id, organisation_id=user.organisation_id, status=user_status)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)


    # Add the additional fields to the user object
    db_user.role_name = role.role_name
    db_user.organisation_name = organisation.name
    db_user.organisation_logo = organisation.logo
    db_user.organisation_domain = organisation.domain

    return db_user


def update_user_in_organisation(db, user):
    try:
        # Find the user with user.user_id first
        user_uuid = uuid.UUID(user.user_id) if isinstance(user.user_id, str) else user.user_id
        db_user = db.query(models.User).filter(models.User.id == user_uuid).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get the current role of the user (will be used if role_id is not being updated)
        role = db.query(models.Role).filter(models.Role.id == db_user.role_id).first()

        # Update the user attributes
        if user.email is not None:
            db_user.email = str(user.email)
        if user.password is not None and user.password != "":
            # Hash the password securely
            hashed_password = get_password_hash(user.password)
            db_user.hashed_password = hashed_password
        if user.role_id is not None:
            db_user.role_id = user.role_id
            # If role_id is being updated, get the new role for the response
            role = db.query(models.Role).filter(models.Role.id == uuid.UUID(user.role_id)).first()

        # Get the organisation based on the user's organisation_id (which comes from user_id lookup)
        organisation = db.query(models.Organisations).filter(models.Organisations.id == db_user.organisation_id).first()

        # Commit the changes to the database
        db.commit()
        db.refresh(db_user)

        # Add the additional fields to the user object for the response
        db_user.role_name = role.role_name if role else None
        db_user.organisation_name = organisation.name if organisation else None
        db_user.organisation_logo = organisation.logo if organisation else None
        db_user.organisation_domain = organisation.domain if organisation else None

        # Return the updated user object with all required fields
        return db_user
    except Exception as e:
        print(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Error updating user")


def update_user(db: Session, user_id: uuid.UUID, user: schemas.UserCreate):

    db_user = db.query(models.User).filter(models.User.id == user_id).first()

    if db_user:
        # Update user attributes
        if user.name is not None:
            db_user.name = user.name
        if user.email is not None:
            db_user.email = str(user.email)
        if user.password is not None:
            # Hash the new password securely
            db_user.hashed_password = get_password_hash(user.password)
        if user.role is not None:
            db_user.role = user.role
        if hasattr(user, 'status') and user.status is not None:
            db_user.status = user.status

        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: uuid.UUID):
    from app.repositories.answer_repository import delete_existing_evidences

    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return False

    try:
        # Step 1: Handle History table foreign key constraints
        # Update history records where this user is referenced as initial_user_id (set to NULL - it's nullable)
        db.query(models.History).filter(models.History.initial_user_id == user_id).update(
            {models.History.initial_user_id: None}
        )

        # For history records where this user is last_user_id, preserve email but set user_id to NULL
        # The email is already stored in last_user_email, so we just need to set the FK to NULL
        db.query(models.History).filter(models.History.last_user_id == user_id).update(
            {models.History.last_user_id: None}
        )

        # Step 2: Delete assessments and their related data (answers, evidence)
        user_assessments = db.query(models.Assessment).filter(models.Assessment.user_id == user_id).all()
        for assessment in user_assessments:
            # Get all answers for this assessment
            answers = db.query(models.Answer).filter(models.Answer.assessment_id == assessment.id).all()

            # Delete evidence files and database records for each answer using the existing utility
            for answer in answers:
                delete_existing_evidences(answer_id=answer.id, db=db)

            # Delete all answers for this assessment
            db.query(models.Answer).filter(models.Answer.assessment_id == assessment.id).delete()

        # Step 3: Delete all assessments created by this user
        db.query(models.Assessment).filter(models.Assessment.user_id == user_id).delete()

        # Step 4: Delete user's policies, risks, and products
        # Delete policies created by this user and their related data
        user_policies = db.query(models.Policies).filter(models.Policies.created_by == user_id).all()
        for policy in user_policies:
            # Delete policy framework relationships
            db.query(models.PolicyFrameworks).filter(models.PolicyFrameworks.policy_id == policy.id).delete()
            # Delete policy objective relationships
            db.query(models.PolicyObjectives).filter(models.PolicyObjectives.policy_id == policy.id).delete()
            # Set answer policy references to NULL to avoid FK violations
            db.query(models.Answer).filter(models.Answer.policy_id == policy.id).update({models.Answer.policy_id: None})
        # Delete the policies themselves
        db.query(models.Policies).filter(models.Policies.created_by == user_id).delete()

        # Null out last_updated_by on policies updated (but not created) by this user
        db.query(models.Policies).filter(models.Policies.last_updated_by == user_id).update(
            {models.Policies.last_updated_by: None})

        # Delete risks created by this user
        db.query(models.Risks).filter(models.Risks.created_by == user_id).delete()

        # Step 5: Delete user sessions and PDF download records
        db.query(models.UserSessions).filter(models.UserSessions.user_id == user_id).delete()
        db.query(models.PdfDownloads).filter(models.PdfDownloads.user_id == user_id).delete()

        # Step 6: Handle remaining foreign key references to this user

        # NOT NULL FK columns - must delete or reassign these records
        db.query(models.DomainBlacklist).filter(models.DomainBlacklist.blacklisted_by == user_id).delete()
        db.query(models.QuestionCorrelation).filter(models.QuestionCorrelation.created_by == user_id).delete()
        db.query(models.ScannerHistory).filter(models.ScannerHistory.user_id == user_id).delete()
        db.query(models.ScanSchedule).filter(models.ScanSchedule.user_id == user_id).delete()
        db.query(models.RiskAssessment).filter(models.RiskAssessment.assessed_by == user_id).delete()

        # Audit engagements owned by this user - delete with all related audit data
        user_engagements = db.query(models.AuditEngagement).filter(models.AuditEngagement.owner_id == user_id).all()
        for engagement in user_engagements:
            eid = engagement.id
            db.query(models.AuditNotification).filter(models.AuditNotification.engagement_id == eid).delete()
            db.query(models.AuditActivityLog).filter(models.AuditActivityLog.engagement_id == eid).delete()
            db.query(models.ControlReviewStatus).filter(models.ControlReviewStatus.engagement_id == eid).delete()
            db.query(models.AuditSignOff).filter(models.AuditSignOff.engagement_id == eid).delete()
            # Delete audit comments (attachments cascade via ondelete="CASCADE" on comment_id)
            db.query(models.AuditComment).filter(models.AuditComment.engagement_id == eid).delete()
            # Delete audit findings
            db.query(models.AuditFinding).filter(models.AuditFinding.engagement_id == eid).delete()
            # Delete auditor invitations for this engagement
            db.query(models.AuditorInvitation).filter(models.AuditorInvitation.engagement_id == eid).delete()
        db.query(models.AuditEngagement).filter(models.AuditEngagement.owner_id == user_id).delete()

        # Auditor invitations created by this user (for engagements they don't own)
        db.query(models.AuditorInvitation).filter(models.AuditorInvitation.invited_by == user_id).delete()

        # Nullable FK columns - set to NULL to preserve the records
        db.query(models.Risks).filter(models.Risks.last_updated_by == user_id).update(
            {models.Risks.last_updated_by: None})
        db.query(models.FrameworkUpdates).filter(models.FrameworkUpdates.applied_by == user_id).update(
            {models.FrameworkUpdates.applied_by: None})
        db.query(models.ScanFinding).filter(models.ScanFinding.remediated_by == user_id).update(
            {models.ScanFinding.remediated_by: None})
        db.query(models.Backup).filter(models.Backup.created_by == user_id).update(
            {models.Backup.created_by: None})
        db.query(models.AuditComment).filter(models.AuditComment.author_user_id == user_id).update(
            {models.AuditComment.author_user_id: None})
        db.query(models.AuditComment).filter(models.AuditComment.assigned_to_id == user_id).update(
            {models.AuditComment.assigned_to_id: None})
        db.query(models.AuditComment).filter(models.AuditComment.resolved_by_id == user_id).update(
            {models.AuditComment.resolved_by_id: None})
        db.query(models.AuditCommentAttachment).filter(models.AuditCommentAttachment.uploaded_by_user_id == user_id).update(
            {models.AuditCommentAttachment.uploaded_by_user_id: None})
        db.query(models.AuditFinding).filter(models.AuditFinding.remediation_owner_id == user_id).update(
            {models.AuditFinding.remediation_owner_id: None})
        db.query(models.AuditFinding).filter(models.AuditFinding.author_user_id == user_id).update(
            {models.AuditFinding.author_user_id: None})
        db.query(models.AuditActivityLog).filter(models.AuditActivityLog.user_id == user_id).update(
            {models.AuditActivityLog.user_id: None})
        db.query(models.ControlReviewStatus).filter(models.ControlReviewStatus.last_updated_by_user_id == user_id).update(
            {models.ControlReviewStatus.last_updated_by_user_id: None})
        db.query(models.AuditNotification).filter(models.AuditNotification.recipient_user_id == user_id).update(
            {models.AuditNotification.recipient_user_id: None})
        db.query(models.AuditNotification).filter(models.AuditNotification.sender_user_id == user_id).update(
            {models.AuditNotification.sender_user_id: None})
        db.query(models.EvidenceIntegrity).filter(models.EvidenceIntegrity.uploaded_by_id == user_id).update(
            {models.EvidenceIntegrity.uploaded_by_id: None})
        db.query(models.NVDSyncStatus).filter(models.NVDSyncStatus.triggered_by == user_id).update(
            {models.NVDSyncStatus.triggered_by: None})
        db.query(models.EUVDSyncStatus).filter(models.EUVDSyncStatus.triggered_by == user_id).update(
            {models.EUVDSyncStatus.triggered_by: None})

        # Nullable created_by/last_updated_by on various tables
        for model_cls in [models.Assets, models.ControlSet, models.Control, models.Incidents]:
            if hasattr(model_cls, 'created_by'):
                db.query(model_cls).filter(model_cls.created_by == user_id).update(
                    {model_cls.created_by: None})
            if hasattr(model_cls, 'last_updated_by'):
                db.query(model_cls).filter(model_cls.last_updated_by == user_id).update(
                    {model_cls.last_updated_by: None})

        # Step 7: Check if this is the last user in the organization
        remaining_users_count = db.query(models.User).filter(
            models.User.organisation_id == db_user.organisation_id,
            models.User.id != user_id
        ).count()

        # Step 8: Delete the user
        user_organisation_id = db_user.organisation_id
        db.delete(db_user)

        # Step 9: If this was the last user, delete the organization and its frameworks
        if remaining_users_count == 0:
            # Delete organization frameworks and their related data using existing function
            from app.repositories.framework_repository import delete_framework_with_relations

            # Get all frameworks for this organization
            org_frameworks = db.query(models.Framework).filter(
                models.Framework.organisation_id == user_organisation_id
            ).all()

            # Delete each framework with its relations
            for framework in org_frameworks:
                delete_framework_with_relations(db, framework.id)

            # Delete the organization itself
            db.query(models.Organisations).filter(models.Organisations.id == user_organisation_id).delete()

        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print(f"Error deleting user {user_id}: {str(e)}")
        raise e


def truncate_all_database_tables(db: Session):
    try:
        # First, truncate dependent tables
        db.execute(text("TRUNCATE TABLE compliance_assessments.answers RESTART IDENTITY CASCADE;"))
        db.execute(text("TRUNCATE TABLE compliance_assessments.evidence RESTART IDENTITY CASCADE;"))
        db.execute(text("TRUNCATE TABLE compliance_assessments.framework_questions RESTART IDENTITY CASCADE;"))

        # Then truncate the main tables
        db.execute(text("TRUNCATE TABLE compliance_assessments.questions RESTART IDENTITY CASCADE;"))
        db.execute(text("TRUNCATE TABLE compliance_assessments.frameworks RESTART IDENTITY CASCADE;"))
        db.execute(text("TRUNCATE TABLE compliance_assessments.assessments RESTART IDENTITY CASCADE;"))

        db.commit()
        print("All tables truncated successfully with identity sequences reset.")
    except Exception as e:
        db.rollback()
        print(f"Error truncating tables: {e}")
        raise

def drop_all_database_tables(db: Session):
    try:
        # Drop tables in the specified order
        db.execute(text("DROP TABLE IF EXISTS compliance_assessments.framework_questions ;"))
        db.execute(text("DROP TABLE IF EXISTS compliance_assessments.notifications ;"))
        db.execute(text("DROP TABLE IF EXISTS compliance_assessments.evidence ;"))
        db.execute(text("DROP TABLE IF EXISTS compliance_assessments.answers ;"))
        db.execute(text("DROP TABLE IF EXISTS compliance_assessments.questions ;"))
        db.execute(text("DROP TABLE IF EXISTS compliance_assessments.assessments ;"))
        db.execute(text("DROP TABLE IF EXISTS compliance_assessments.users ;"))
        db.execute(text("DROP TABLE IF EXISTS compliance_assessments.frameworks ;"))

        db.commit()
        print("All tables dropped successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error dropping tables: {e}")
        raise


def check_organization_name_exists(db: Session, org_name: str) -> bool:
    return db.query(models.Organisations).filter(models.Organisations.name == org_name).first() is not None

def check_organization_domain_exists(db: Session, domain: str) -> bool:
    return db.query(models.Organisations).filter(models.Organisations.domain == domain).first() is not None

def check_organization_domain_exists_excluding_id(db: Session, domain: str, exclude_id: uuid.UUID) -> bool:
    return db.query(models.Organisations).filter(
        models.Organisations.domain == domain,
        models.Organisations.id != exclude_id
    ).first() is not None

def user_belongs_to_clone_systems_domain(db: Session, user_id: uuid.UUID) -> bool:
    """Check if a user belongs to the clone-systems.com domain organization"""
    user = db.query(models.User).join(
        models.Organisations,
        models.User.organisation_id == models.Organisations.id
    ).filter(
        models.User.id == user_id,
        models.Organisations.domain == "clone-systems.com"
    ).first()
    return user is not None


def create_organisation(db: Session, request: schemas.OrganisationRequest):
    # Validate domain format (must be a valid email domain)
    if not request.domain or '.' not in request.domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organisation domain must be a valid email domain (e.g., 'company.com')"
        )

    # Check for existing organization with this domain
    if check_organization_domain_exists(db, request.domain):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Organisation with this domain already exists")

    # Note: We removed name uniqueness check since organization names can be duplicated
    # The domain is the unique identifier, not the name

    db_organisation = models.Organisations(
        name=request.name,
        domain=request.domain.lower(),  # Ensure domain is lowercase
        logo=request.logo,
    )
    db.add(db_organisation)
    db.commit()
    db.refresh(db_organisation)

    # Auto-seed Common Risks for the new organisation
    try:
        seed_result = risk_seeding_service.seed_common_risks_for_organisation(
            db=db,
            organisation_id=db_organisation.id,
            created_by_user_id=None  # No user yet when org is first created
        )
        logger.info(f"Seeded {seed_result['created_count']} common risks for new organisation '{db_organisation.name}'")
    except Exception as e:
        # Log but don't fail the org creation if risk seeding fails
        logger.error(f"Failed to seed common risks for organisation '{db_organisation.name}': {str(e)}")

    # Auto-seed default asset types for the new organisation
    try:
        asset_types = AssetTypesSeed.seed_for_organization(db, db_organisation)
        db.commit()
        logger.info(f"Seeded {len(asset_types)} default asset types for new organisation '{db_organisation.name}'")
    except Exception as e:
        logger.error(f"Failed to seed asset types for organisation '{db_organisation.name}': {str(e)}")

    return db_organisation


def get_all_organisations(db, current_user):
    user_with_role = db.query(models.User, models.Role.role_name).join(
        models.Role, models.User.role_id == models.Role.id
    ).filter(models.User.id == current_user.id).first()

    if user_with_role.role_name == "super_admin":
        return db.query(models.Organisations).all()
    else:
        return db.query(models.Organisations).filter(
            models.Organisations.id == current_user.organisation_id
        ).all()


def update_organisation(db: Session, organisation_id: uuid.UUID, request: schemas.OrganisationRequest):
    # Get the organisation by id
    db_organisation = db.query(models.Organisations).filter(models.Organisations.id == organisation_id).first()
    if db_organisation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"Organisation with id {organisation_id} not found")

    # DOMAIN IMMUTABILITY: Domains cannot be changed after organization creation
    # The domain is derived from user email domains and changing it would break user associations
    if request.domain != db_organisation.domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization domain cannot be changed. The domain '{db_organisation.domain}' is derived from user email domains and cannot be modified."
        )

    # Update only the organization name and logo (domain remains immutable)
    db_organisation.name = request.name
    # Handle logo update: if logo is explicitly set to None, delete it; if non-empty string, update it
    if request.logo is None:
        db_organisation.logo = None
    elif request.logo.strip() != "":
        db_organisation.logo = request.logo

    # Commit the changes
    db.commit()
    db.refresh(db_organisation)
    return db_organisation


def get_all_roles(db):
    return db.query(models.Role).all()


def get_organisation_users(db, organisation_id):
    return db.query(
        models.User.id,
        models.User.email,
        models.User.role_id,
        models.User.status,
        models.User.auth_provider,
                models.Role.role_name,
        models.Organisations.id.label("organisation_id"),
        models.Organisations.name.label("organisation_name"),
        models.Organisations.logo.label("organisation_logo"),
        models.Organisations.domain.label("organisation_domain")
    ).join(
        models.Organisations,
        models.User.organisation_id == models.Organisations.id,
        isouter=True
    ).join(
        models.Role,
        models.User.role_id == models.Role.id,
        isouter=True
    ).filter(models.User.organisation_id == organisation_id).all()


def get_role_by_id(db: Session, role_id: str):
    return db.query(models.Role).filter(models.Role.id == uuid.UUID(role_id)).first()


def get_organisation_by_id(db: Session, organisation_id: str):
    return db.query(models.Organisations).filter(models.Organisations.id == uuid.UUID(organisation_id)).first()


def get_org_admin(db: Session, organisation_id: str):
    """Get the org_admin user for a specific organisation"""
    return db.query(models.User).join(
        models.Role, models.User.role_id == models.Role.id
    ).filter(
        models.User.organisation_id == uuid.UUID(organisation_id),
        models.Role.role_name == 'org_admin'
    ).first()


def get_organisation_admins(db: Session, organisation_id: str):
    """Get all org_admin and super_admin users for a specific organisation for notifications"""
    return db.query(models.User).join(
        models.Role, models.User.role_id == models.Role.id
    ).filter(
        models.User.organisation_id == uuid.UUID(organisation_id),
        models.User.status == 'active',
        models.Role.role_name.in_(['org_admin', 'super_admin'])
    ).all()


def get_all_organisations_public(db: Session):
    """Public endpoint to get all organisations for registration"""
    return db.query(models.Organisations).all()


def get_registration_roles(db: Session):
    """Get only org_admin and org_user roles for registration"""
    return db.query(models.Role).filter(
        models.Role.role_name.in_(['org_admin', 'org_user'])
    ).all()


def delete_organisation(db: Session, organisation_id: uuid.UUID):
    """Delete organization with complete cascading deletes"""
    from app.repositories.answer_repository import delete_existing_evidences

    db_organisation = db.query(models.Organisations).filter(models.Organisations.id == organisation_id).first()
    if not db_organisation:
        return False

    try:
        print(f"Starting deletion of organization: {db_organisation.name} ({organisation_id})")

        # STEP 1: Delete all users and their associated data (using the same logic as single user deletion)
        org_users = db.query(models.User).filter(models.User.organisation_id == organisation_id).all()
        print(f"Found {len(org_users)} users to delete")

        for user in org_users:
            print(f"Deleting user: {user.email}")

            # 1a. Handle History table foreign key constraints for this user
            # Update history records where this user is referenced as initial_user_id (set to NULL - it's nullable)
            updated_initial = db.query(models.History).filter(models.History.initial_user_id == user.id).update(
                {models.History.initial_user_id: None}
            )
            print(f"Updated {updated_initial} history records with initial_user_id")

            # For history records where this user is last_user_id (not nullable), delete the records
            deleted_history = db.query(models.History).filter(models.History.last_user_id == user.id).delete()
            print(f"Deleted {deleted_history} history records with last_user_id")

            # 1b. Delete assessments and their related data (answers, evidence)
            user_assessments = db.query(models.Assessment).filter(models.Assessment.user_id == user.id).all()
            print(f"Found {len(user_assessments)} assessments for user {user.email}")

            for assessment in user_assessments:
                # Get all answers for this assessment
                answers = db.query(models.Answer).filter(models.Answer.assessment_id == assessment.id).all()
                print(f"Found {len(answers)} answers for assessment {assessment.name}")

                # Delete evidence files and database records for each answer
                for answer in answers:
                    delete_existing_evidences(answer_id=answer.id, db=db)

                # Delete all answers for this assessment
                deleted_answers = db.query(models.Answer).filter(models.Answer.assessment_id == assessment.id).delete()
                print(f"Deleted {deleted_answers} answers")

            # Delete all assessments created by this user
            deleted_assessments = db.query(models.Assessment).filter(models.Assessment.user_id == user.id).delete()
            print(f"Deleted {deleted_assessments} assessments for user {user.email}")

        # STEP 2: Handle Policies and their relationships BEFORE deleting users
        org_policies = db.query(models.Policies).filter(models.Policies.organisation_id == organisation_id).all()
        print(f"Found {len(org_policies)} policies to delete")

        for policy in org_policies:
            # First, handle answers that reference this policy (set policy_id to NULL)
            # The policy_id field in answers is nullable, so we can set it to NULL
            updated_answer_policies = db.query(models.Answer).filter(models.Answer.policy_id == policy.id).update(
                {models.Answer.policy_id: None}
            )
            print(f"Updated {updated_answer_policies} answers to remove policy reference for policy {policy.title}")

            # Delete policy objectives relationships
            deleted_policy_objectives = db.query(models.PolicyObjectives).filter(models.PolicyObjectives.policy_id == policy.id).delete()
            print(f"Deleted {deleted_policy_objectives} policy-objective relationships for policy {policy.title}")

        # Handle user foreign key constraints in policies before deleting users
        user_ids_in_org = [user.id for user in db.query(models.User).filter(models.User.organisation_id == organisation_id).all()]
        print(f"Found {len(user_ids_in_org)} users in organization to remove from policy references")

        if user_ids_in_org:
            # Set created_by and last_updated_by to NULL in all policies that reference users from this organization
            updated_created_by = db.query(models.Policies).filter(models.Policies.created_by.in_(user_ids_in_org)).update(
                {models.Policies.created_by: None}, synchronize_session=False
            )
            print(f"Updated {updated_created_by} policies to remove created_by references")

            updated_last_updated_by = db.query(models.Policies).filter(models.Policies.last_updated_by.in_(user_ids_in_org)).update(
                {models.Policies.last_updated_by: None}, synchronize_session=False
            )
            print(f"Updated {updated_last_updated_by} policies to remove last_updated_by references")

            # Update Products table user references (nullable fields)
            updated_products_created = db.query(models.Products).filter(models.Products.created_by.in_(user_ids_in_org)).update(
                {models.Products.created_by: None}, synchronize_session=False
            )
            print(f"Updated {updated_products_created} products to remove created_by references")

            updated_products_updated = db.query(models.Products).filter(models.Products.last_updated_by.in_(user_ids_in_org)).update(
                {models.Products.last_updated_by: None}, synchronize_session=False
            )
            print(f"Updated {updated_products_updated} products to remove last_updated_by references")

            # Update Risks table user references (nullable fields)
            updated_risks_created = db.query(models.Risks).filter(models.Risks.created_by.in_(user_ids_in_org)).update(
                {models.Risks.created_by: None}, synchronize_session=False
            )
            print(f"Updated {updated_risks_created} risks to remove created_by references")

            updated_risks_updated = db.query(models.Risks).filter(models.Risks.last_updated_by.in_(user_ids_in_org)).update(
                {models.Risks.last_updated_by: None}, synchronize_session=False
            )
            print(f"Updated {updated_risks_updated} risks to remove last_updated_by references")

        # Handle user foreign key constraints in other tables that might reference organization users
        if user_ids_in_org:
            # Delete domain blacklist entries created by users from this organization
            # (since blacklisted_by is NOT nullable, we must delete these entries)
            deleted_blacklist = db.query(models.DomainBlacklist).filter(models.DomainBlacklist.blacklisted_by.in_(user_ids_in_org)).delete()
            print(f"Deleted {deleted_blacklist} domain blacklist entries created by organization users")

            # Update organization framework permissions
            deleted_permissions = db.query(models.OrganizationFrameworkPermissions).filter(
                models.OrganizationFrameworkPermissions.organization_id == organisation_id
            ).delete()
            print(f"Deleted {deleted_permissions} organization framework permissions")

        # Delete user sessions and PDF download records for all org users
        if user_ids_in_org:
            db.query(models.UserSessions).filter(models.UserSessions.user_id.in_(user_ids_in_org)).delete()
            db.query(models.PdfDownloads).filter(models.PdfDownloads.user_id.in_(user_ids_in_org)).delete()

        # Now safe to delete all users in this organization
        deleted_users = db.query(models.User).filter(models.User.organisation_id == organisation_id).delete()
        print(f"Deleted {deleted_users} users")

        # STEP 3: Handle Frameworks and their complex relationships
        org_frameworks = db.query(models.Framework).filter(models.Framework.organisation_id == organisation_id).all()
        print(f"Found {len(org_frameworks)} frameworks to delete")

        for framework in org_frameworks:
            print(f"Deleting framework: {framework.name}")

            # 3a. Delete policy frameworks relationships FIRST
            deleted_policy_frameworks = db.query(models.PolicyFrameworks).filter(models.PolicyFrameworks.framework_id == framework.id).delete()
            print(f"Deleted {deleted_policy_frameworks} policy-framework relationships")

            # 3b. Delete any remaining assessments using this framework (safety check)
            deleted_remaining_assessments = db.query(models.Assessment).filter(models.Assessment.framework_id == framework.id).delete()
            if deleted_remaining_assessments > 0:
                print(f"WARNING: Deleted {deleted_remaining_assessments} remaining assessments for framework {framework.name}")

            # 3c. Handle Chapters and Objectives
            framework_chapters = db.query(models.Chapters).filter(models.Chapters.framework_id == framework.id).all()
            print(f"Found {len(framework_chapters)} chapters for framework {framework.name}")

            for chapter in framework_chapters:
                chapter_objectives = db.query(models.Objectives).filter(models.Objectives.chapter_id == chapter.id).all()
                print(f"Found {len(chapter_objectives)} objectives for chapter {chapter.title}")

                for objective in chapter_objectives:
                    # Delete policy objectives relationships (safety check - should already be done above)
                    deleted_obj_policies = db.query(models.PolicyObjectives).filter(models.PolicyObjectives.objective_id == objective.id).delete()
                    if deleted_obj_policies > 0:
                        print(f"WARNING: Deleted {deleted_obj_policies} remaining policy-objective relationships")

                # Delete all objectives in this chapter
                deleted_objectives = db.query(models.Objectives).filter(models.Objectives.chapter_id == chapter.id).delete()
                print(f"Deleted {deleted_objectives} objectives for chapter {chapter.title}")

            # Delete all chapters in this framework
            deleted_chapters = db.query(models.Chapters).filter(models.Chapters.framework_id == framework.id).delete()
            print(f"Deleted {deleted_chapters} chapters for framework {framework.name}")

            # 3d. Delete framework questions relationships (keep questions as they're shared)
            deleted_framework_questions = db.query(models.FrameworkQuestion).filter(models.FrameworkQuestion.framework_id == framework.id).delete()
            print(f"Deleted {deleted_framework_questions} framework-question relationships")

        # Delete all frameworks in this organization
        deleted_frameworks = db.query(models.Framework).filter(models.Framework.organisation_id == organisation_id).delete()
        print(f"Deleted {deleted_frameworks} frameworks")

        # STEP 4: Delete all policies for this organization
        deleted_policies = db.query(models.Policies).filter(models.Policies.organisation_id == organisation_id).delete()
        print(f"Deleted {deleted_policies} policies")

        # STEP 5: Delete all products for this organization
        deleted_products = db.query(models.Products).filter(models.Products.organisation_id == organisation_id).delete()
        print(f"Deleted {deleted_products} products")

        # STEP 6: Delete all risks for this organization
        deleted_risks = db.query(models.Risks).filter(models.Risks.organisation_id == organisation_id).delete()
        print(f"Deleted {deleted_risks} risks")

        # STEP 7: Clean up any remaining history records that reference this organization's entities
        # This is a safety cleanup - delete any remaining history records for this organization
        remaining_history = db.query(models.History).filter(
            models.History.table_name_changed.in_(['products', 'policies', 'risks', 'objectives', 'frameworks', 'users'])
        ).all()

        # Filter history records that might reference deleted entities
        for history_record in remaining_history:
            try:
                # Check if the referenced record still exists
                if history_record.table_name_changed == 'users':
                    exists = db.query(models.User).filter(models.User.id == uuid.UUID(history_record.record_id)).first()
                elif history_record.table_name_changed == 'policies':
                    exists = db.query(models.Policies).filter(models.Policies.id == uuid.UUID(history_record.record_id)).first()
                elif history_record.table_name_changed == 'products':
                    exists = db.query(models.Products).filter(models.Products.id == uuid.UUID(history_record.record_id)).first()
                elif history_record.table_name_changed == 'risks':
                    exists = db.query(models.Risks).filter(models.Risks.id == uuid.UUID(history_record.record_id)).first()
                elif history_record.table_name_changed == 'objectives':
                    exists = db.query(models.Objectives).filter(models.Objectives.id == uuid.UUID(history_record.record_id)).first()
                elif history_record.table_name_changed == 'frameworks':
                    exists = db.query(models.Framework).filter(models.Framework.id == uuid.UUID(history_record.record_id)).first()
                else:
                    exists = True  # Skip unknown table types

                # If the referenced entity no longer exists, delete the history record
                if not exists:
                    db.delete(history_record)

            except (ValueError, Exception):
                # If there's any error parsing the record_id or checking existence, delete the record
                db.delete(history_record)

        # STEP 8: Finally delete the organization itself
        print(f"Deleting organization: {db_organisation.name}")
        db.delete(db_organisation)

        db.commit()
        print(f"Successfully deleted organization {db_organisation.name} and all associated data")
        return True

    except Exception as e:
        db.rollback()
        print(f"Error deleting organisation: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise e  # Re-raise to see the full error in API response

def get_organisation_by_domain(db: Session, domain: str):
    """Get organization by domain"""
    return db.query(models.Organisations).filter(models.Organisations.domain == domain).first()

def get_role_by_name(db: Session, role_name: str):
    """Get role by role name"""
    return db.query(models.Role).filter(models.Role.role_name == role_name).first()

def create_organisation_from_dict(db: Session, org_data: dict):
    """Create a new organization from dict data - used by seeding and registration"""
    organisation = models.Organisations(**org_data)
    db.add(organisation)
    db.commit()
    db.refresh(organisation)

    # Auto-seed default asset types for the new organisation
    try:
        asset_types = AssetTypesSeed.seed_for_organization(db, organisation)
        db.commit()
        logger.info(f"Seeded {len(asset_types)} default asset types for new organisation '{organisation.name}'")
    except Exception as e:
        logger.error(f"Failed to seed asset types for organisation '{organisation.name}': {str(e)}")

    return organisation

def update_user_password_hash(db: Session, user_id: uuid.UUID, hashed_password: str):
    """Update user's password hash directly"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.hashed_password = hashed_password
        db.commit()
        db.refresh(user)
    return user

def create_user_with_hashed_password(db: Session, email: str, hashed_password: str, role_id: str, organisation_id: str, status: str = None):
    """Create user with already hashed password"""
    # Check if user email already exists
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # All self-registered users start as pending_approval and require admin approval
    user_status = "pending_approval"
    
    # Create user with pre-hashed password
    db_user = models.User(
        name=email.split('@')[0], 
        email=email, 
        hashed_password=hashed_password,
        role_id=role_id, 
        organisation_id=organisation_id,
        status=user_status if status is None else status
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_status(db: Session, user_id: uuid.UUID, new_status: str):
    """Update user status (pending_approval, active, inactive)"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.status = new_status
    db.commit()
    db.refresh(user)
    return user


def get_pending_users_for_approval(db: Session, current_user):
    """Get pending users for approval based on current user's role and organization"""
    # Get current user's role
    user_role = db.query(models.Role).filter(models.Role.id == current_user.role_id).first()

    if user_role.role_name == "super_admin":
        # Super admin can see all pending users
        return db.query(
            models.User.id,
            models.User.email,
            models.User.role_id,
            models.User.status,
            models.User.created_at,
            models.Role.role_name,
            models.Organisations.name.label("organisation_name")
        ).join(
            models.Role, models.User.role_id == models.Role.id
        ).join(
            models.Organisations, models.User.organisation_id == models.Organisations.id
        ).filter(models.User.status == "pending_approval").all()

    elif user_role.role_name == "org_admin":
        # Org admin can only see pending users from same organization
        return db.query(
            models.User.id,
            models.User.email,
            models.User.role_id,
            models.User.status,
            models.User.created_at,
            models.Role.role_name,
            models.Organisations.name.label("organisation_name")
        ).join(
            models.Role, models.User.role_id == models.Role.id
        ).join(
            models.Organisations, models.User.organisation_id == models.Organisations.id
        ).filter(
            models.User.status == "pending_approval",
            models.User.organisation_id == current_user.organisation_id
        ).all()

    else:
        # org_user cannot see any pending users
        return []


def get_user_full_profile(db: Session, user_id: uuid.UUID):
    """Get user's full profile with all details"""
    import json

    result = db.query(
        models.User.id,
        models.User.email,
        models.User.role_id,
        models.User.organisation_id,
        models.User.status,
        models.User.auth_provider,
        models.User.first_name,
        models.User.last_name,
        models.User.phone,
        models.User.job_title,
        models.User.department,
        models.User.profile_picture,
        models.User.timezone,
        models.User.notification_preferences,
        models.User.onboarding_completed,
        models.User.onboarding_completed_at,
        models.User.onboarding_skipped,
        models.Role.role_name,
        models.Organisations.name.label("organisation_name"),
        models.Organisations.logo.label("organisation_logo"),
        models.Organisations.domain.label("organisation_domain")
    ).join(
        models.Role, models.User.role_id == models.Role.id
    ).join(
        models.Organisations, models.User.organisation_id == models.Organisations.id, isouter=True
    ).filter(models.User.id == user_id).first()

    if not result:
        return None

    # Parse notification_preferences from JSON string
    notification_prefs = None
    if result.notification_preferences:
        try:
            notification_prefs = json.loads(result.notification_preferences)
        except (json.JSONDecodeError, TypeError):
            notification_prefs = None

    return {
        "id": result.id,
        "email": result.email,
        "role_id": result.role_id,
        "organisation_id": result.organisation_id,
        "status": result.status,
        "auth_provider": result.auth_provider or "local",
        "role_name": result.role_name,
        "organisation_name": result.organisation_name,
        "organisation_logo": result.organisation_logo,
        "organisation_domain": result.organisation_domain,
        "first_name": result.first_name,
        "last_name": result.last_name,
        "phone": result.phone,
        "job_title": result.job_title,
        "department": result.department,
        "profile_picture": result.profile_picture,
        "timezone": result.timezone or "UTC",
        "notification_preferences": notification_prefs,
        "onboarding_completed": result.onboarding_completed or False,
        "onboarding_completed_at": result.onboarding_completed_at,
        "onboarding_skipped": result.onboarding_skipped or False
    }


def update_user_profile(db: Session, user_id: uuid.UUID, first_name=None, last_name=None, phone=None, job_title=None, department=None, timezone=None, notification_preferences=None):
    """Update user's profile fields"""
    import json

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None

    # Update fields if provided
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if phone is not None:
        user.phone = phone
    if job_title is not None:
        user.job_title = job_title
    if department is not None:
        user.department = department
    if timezone is not None:
        user.timezone = timezone
    if notification_preferences is not None:
        user.notification_preferences = json.dumps(notification_preferences)

    db.commit()
    db.refresh(user)

    # Return full profile
    return get_user_full_profile(db, user_id)


def update_user_profile_picture(db: Session, user_id: uuid.UUID, profile_picture: str):
    """Update user's profile picture"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None

    user.profile_picture = profile_picture
    db.commit()
    db.refresh(user)
    return user


def update_onboarding_status(db: Session, user_id: uuid.UUID, onboarding_completed: bool, onboarding_completed_at=None, onboarding_skipped: bool = False):
    """Update user's onboarding status"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None

    user.onboarding_completed = onboarding_completed
    user.onboarding_completed_at = onboarding_completed_at
    user.onboarding_skipped = onboarding_skipped

    db.commit()
    db.refresh(user)
    return user

