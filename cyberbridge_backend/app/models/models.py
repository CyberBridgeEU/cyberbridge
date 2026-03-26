# models.py
from sqlalchemy import Column, String, Boolean, Float, ForeignKey, Integer, DateTime, Text, LargeBinary, func, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from ..database.database import Base
import uuid
import json


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # NULL for SSO users
    auth_provider = Column(String(20), nullable=False, default="local")  # local/google/microsoft
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"))
    status = Column(String(50), nullable=False, default="pending_approval")  # pending_approval, active, inactive
    last_activity = Column(DateTime, nullable=True)  # Track user activity for online status

    # Profile fields
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    job_title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    profile_picture = Column(Text, nullable=True)  # URL or base64 encoded image
    timezone = Column(String(100), nullable=True, default="UTC")
    notification_preferences = Column(Text, nullable=True)  # JSON string for preferences

    # Force password change on first login
    must_change_password = Column(Boolean, default=False, nullable=False)

    # Onboarding tracking
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    onboarding_completed_at = Column(DateTime, nullable=True)
    onboarding_skipped = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class UserSessions(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False)
    login_timestamp = Column(DateTime, nullable=False, default=func.now())
    logout_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())


class PdfDownloads(Base):
    __tablename__ = "pdf_downloads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False)
    pdf_type = Column(String(100), nullable=False)  # assessment, policy, risk, product, objectives, zap, nmap, semgrep, osv
    download_timestamp = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, default=func.now())


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())

class Scopes(Base):
    __tablename__ = "scopes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope_name = Column(String(50), unique=True, nullable=False)  # 'Product', 'Organization', 'Asset', 'Project', 'Process'
    created_at = Column(DateTime, default=func.now())


class Framework(Base):
    __tablename__ = "frameworks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"))

    # Scope configuration fields
    _allowed_scope_types = Column('allowed_scope_types', Text, nullable=True)  # JSON array: ['Product', 'Organization']
    scope_selection_mode = Column(String(50), default='optional')  # 'required', 'optional'

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship to Organisation
    organisation = relationship("Organisations", foreign_keys=[organisation_id])

    @property
    def organisation_domain(self):
        """Property to access the organisation's domain"""
        return self.organisation.domain if self.organisation else None

    @hybrid_property
    def allowed_scope_types(self):
        """Property to deserialize JSON string to list"""
        if self._allowed_scope_types:
            try:
                return json.loads(self._allowed_scope_types)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @allowed_scope_types.setter
    def allowed_scope_types(self, value):
        """Setter to serialize list to JSON string"""
        if value is not None:
            if isinstance(value, list):
                self._allowed_scope_types = json.dumps(value)
            elif isinstance(value, str):
                # If it's already a string, store it as-is
                self._allowed_scope_types = value
            else:
                self._allowed_scope_types = None
        else:
            self._allowed_scope_types = None


class AssessmentType(Base):
    __tablename__ = "assessment_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type_name = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=func.now())


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    description = Column(Text)
    mandatory = Column(Boolean, default=False)
    assessment_type_id = Column(UUID(as_uuid=True), ForeignKey("assessment_types.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class FrameworkQuestion(Base):
    __tablename__ = "framework_questions"

    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id"), primary_key=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), primary_key=True)
    order = Column(Integer, default=0)


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assessment_type_id = Column(UUID(as_uuid=True), ForeignKey("assessment_types.id"), nullable=False)

    # Scope fields
    scope_id = Column(UUID(as_uuid=True), ForeignKey("scopes.id"), nullable=True)  # Which type of scope
    scope_entity_id = Column(UUID(as_uuid=True), nullable=True)  # The actual entity UUID (product_id, org_id, etc.)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)


class Answer(Base):
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    value = Column(String(50), nullable=True)
    evidence_description = Column(Text)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=func.now())

class ArchitectureDiagram(Base):
    __tablename__ = "architecture_diagrams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    diagram_type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(1024), nullable=True)
    file_size = Column(Integer, nullable=True)
    owner = Column(String(255), nullable=True)
    version = Column(String(50), nullable=True)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    organisation = relationship("Organisations", foreign_keys=[organisation_id])


class ArchitectureDiagramFramework(Base):
    __tablename__ = "architecture_diagram_frameworks"

    diagram_id = Column(UUID(as_uuid=True), ForeignKey("architecture_diagrams.id", ondelete="CASCADE"), primary_key=True)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())


class ArchitectureDiagramRisk(Base):
    __tablename__ = "architecture_diagram_risks"

    diagram_id = Column(UUID(as_uuid=True), ForeignKey("architecture_diagrams.id", ondelete="CASCADE"), primary_key=True)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())


class EvidenceLibraryItem(Base):
    __tablename__ = "evidence_library_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    evidence_type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(1024), nullable=True)
    file_size = Column(Integer, nullable=True)
    owner = Column(String(255), nullable=True)
    collected_date = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False)
    collection_method = Column(String(50), nullable=False)
    audit_notes = Column(Text, nullable=True)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    organisation = relationship("Organisations", foreign_keys=[organisation_id])


class EvidenceLibraryFramework(Base):
    __tablename__ = "evidence_library_frameworks"

    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence_library_items.id", ondelete="CASCADE"), primary_key=True)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())


class EvidenceLibraryControl(Base):
    __tablename__ = "evidence_library_controls"

    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence_library_items.id", ondelete="CASCADE"), primary_key=True)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())

class Organisations(Base):
    __tablename__ = "organisations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True)
    logo = Column(Text, nullable=True)

    # History cleanup configuration
    history_cleanup_enabled = Column(Boolean, nullable=False, default=False)
    history_retention_days = Column(Integer, nullable=False, default=30)  # Keep records for X days
    history_cleanup_interval_hours = Column(Integer, nullable=False, default=24)  # Check every X hours

    # Backup configuration
    backup_enabled = Column(Boolean, nullable=False, default=True)
    backup_frequency = Column(String(20), nullable=False, default='monthly')  # daily, weekly, monthly
    backup_retention_years = Column(Integer, nullable=False, default=10)
    last_backup_at = Column(DateTime, nullable=True)
    last_backup_status = Column(String(50), nullable=True)  # success, failed, in_progress

    # CRA Mode configuration: None (off), 'focused', 'extended'
    cra_mode = Column(String(20), nullable=True)
    cra_operator_role = Column(String(50), nullable=True)  # 'Manufacturer', 'Importer', 'Distributor', or null

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Policies(Base):
    __tablename__ = "policies"
    __table_args__ = (
        UniqueConstraint('organisation_id', 'policy_code', name='uq_policies_org_policy_code'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    policy_code = Column(String(50), nullable=True)
    owner = Column(String(255), nullable=True)
    status_id = Column(UUID(as_uuid=True), ForeignKey("policy_statuses.id"), nullable=False)
    body = Column(Text, nullable=True)
    company_name = Column(String(255), nullable=True)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class PolicyStatuses(Base):
    __tablename__ = "policy_statuses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(50), nullable=False) #Draft, Review, Ready for Approval, Approved

class PolicyFrameworks(Base):
    __tablename__ = "policy_frameworks"

    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), primary_key=True)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id"), primary_key=True)

class Chapters(Base):
    __tablename__ = "chapters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Objectives(Base):
    __tablename__ = "objectives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    subchapter = Column(Text, nullable=True)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id"), nullable=False)
    requirement_description = Column(Text, nullable=True)
    objective_utilities = Column(Text, nullable=True)
    compliance_status_id = Column(UUID(as_uuid=True), ForeignKey("compliance_statuses.id"), nullable=True)
    # Scope fields for scope-based objectives checklist
    scope_id = Column(UUID(as_uuid=True), ForeignKey("scopes.id"), nullable=True)
    scope_entity_id = Column(UUID(as_uuid=True), nullable=True)  # The actual entity UUID (product_id, org_id, etc.)
    applicable_operators = Column(String(500), nullable=True)  # JSON array e.g. '["Manufacturer"]'
    # Evidence file fields
    evidence_filename = Column(String(255), nullable=True)
    evidence_filepath = Column(String(500), nullable=True)
    evidence_file_type = Column(String(100), nullable=True)
    evidence_file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class PolicyObjectives(Base):
    __tablename__ = "policy_objectives"

    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), primary_key=True)
    objective_id = Column(UUID(as_uuid=True), ForeignKey("objectives.id"), primary_key=True)
    order = Column(Integer, default=0)

class EconomicOperators(Base):
    __tablename__ = "economic_operators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False) #Manufacturer, Importer, Distributor

class Criticalities(Base):
    __tablename__ = "criticalities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label = Column(String(500), nullable=False)  # Full title content
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class CriticalityOptions(Base):
    __tablename__ = "criticality_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    criticality_id = Column(UUID(as_uuid=True), ForeignKey("criticalities.id"), nullable=False)
    value = Column(String(500), nullable=False)  # The option value
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AssetCategories(Base):
    __tablename__ = "asset_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False) #Hardware, Software

#Risks
class Risks(Base):
    __tablename__ = "risks"
    __table_args__ = (
        UniqueConstraint('organisation_id', 'risk_code', name='uq_risks_org_risk_code'),
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_category_id = Column(UUID(as_uuid=True), ForeignKey("asset_categories.id"), nullable=True)
    risk_code = Column(String(50), nullable=True)  # Risk code identifier (e.g., RSK-1, RSK-2)
    risk_category_name = Column(String(255), nullable=False)
    risk_category_description = Column(Text, nullable=True)
    risk_potential_impact = Column(Text, nullable=True)
    risk_control = Column(Text, nullable=True)
    likelihood = Column(UUID(as_uuid=True), ForeignKey("risk_severity.id"), nullable=False)
    residual_risk = Column(UUID(as_uuid=True), ForeignKey("risk_severity.id"), nullable=False)
    risk_severity_id = Column(UUID(as_uuid=True), ForeignKey("risk_severity.id"), nullable=False)
    risk_status_id = Column(UUID(as_uuid=True), ForeignKey("risk_status.id"), nullable=False)
    assessment_status = Column(String(50), nullable=True)  # Not Assessed, Assessment in progress, Assessed, Needs Remediation, Remediated, Closed
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)

    # Scope fields
    scope_id = Column(UUID(as_uuid=True), ForeignKey("scopes.id"), nullable=True)  # Which type of scope
    scope_entity_id = Column(UUID(as_uuid=True), nullable=True)  # The actual entity UUID (product_id, org_id, etc.)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class RiskCategories(Base):
    __tablename__ = "risk_categories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_category_id = Column(UUID(as_uuid=True), ForeignKey("asset_categories.id"), nullable=True)
    risk_code = Column(String(50), nullable=True)  # Risk code identifier (e.g., RSK-1, RSK-2)
    risk_category_name = Column(String(255), nullable=False)
    risk_category_description = Column(Text, nullable=True)
    risk_potential_impact = Column(Text, nullable=True)
    risk_control = Column(Text, nullable=True)

class RiskSeverity(Base):
    __tablename__ = "risk_severity"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_severity_name = Column(String(255), nullable=False) #Low, Medium, High, Critical

class RiskStatuses(Base):
    __tablename__ = "risk_status"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_status_name = Column(String(255), nullable=False) #Reduce, Avoid, Transfer, Share, Accept, Remediated

class ComplianceStatuses(Base):
    __tablename__ = "compliance_statuses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status_name = Column(String(255), nullable=False) #not assessed, not compliant, partially compliant, in review, compliant, not applicable

class SMTPConfiguration(Base):
    __tablename__ = "smtp_configurations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label = Column(String(255), nullable=True)
    smtp_server = Column(String(255), nullable=False)
    smtp_port = Column(Integer, nullable=False)
    sender_email = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    password = Column(String(500), nullable=True)
    use_tls = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)  # To support multiple configs but only one active
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class UserVerification(Base):
    __tablename__ = "user_verifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    verification_key = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())


class OrganizationFrameworkPermissions(Base):
    __tablename__ = "organization_framework_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id"), nullable=False)
    can_seed = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class DomainBlacklist(Base):
    __tablename__ = "domain_blacklist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String(255), unique=True, nullable=False)
    is_blacklisted = Column(Boolean, default=True, nullable=False)
    reason = Column(Text, nullable=True)
    blacklisted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class History(Base):
    __tablename__ = "history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_name_changed = Column(String(100), nullable=False)  # products, policies, risks, objectives
    record_id = Column(String(255), nullable=False)  # ID of the record that was changed
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=True)  # Organization for cleanup
    initial_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # User who created the record
    initial_user_email = Column(String(255), nullable=True)  # Store email for reference
    last_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # User who made the change
    last_user_email = Column(String(255), nullable=False)  # Store email for reference
    last_timestamp = Column(DateTime, default=func.now(), nullable=False)
    column_name = Column(String(100), nullable=True)  # Column that was changed (null for insert/delete)
    old_data = Column(Text, nullable=True)  # JSON string of old data
    new_data = Column(Text, nullable=True)  # JSON string of new data
    action = Column(String(20), nullable=False)  # insert, update, delete
    created_at = Column(DateTime, default=func.now())


class QuestionCorrelation(Base):
    __tablename__ = "question_correlations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_a_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    question_b_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False)  # All correlations are org-specific
    scope_id = Column(UUID(as_uuid=True), ForeignKey("scopes.id"), nullable=False)  # Scope type (Product, Organization, Other, etc.)
    scope_entity_id = Column(UUID(as_uuid=True), nullable=True)  # Specific product/organization/etc. (NULL for "Other" scope)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Ensure we don't have duplicate correlations in either direction
    __table_args__ = (
        # This prevents correlating the same question with itself
        CheckConstraint("question_a_id != question_b_id", name="different_questions_check"),
    )


class LLMSettings(Base):
    """Global LLM settings managed by super admin."""
    __tablename__ = "llm_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Global AI toggle
    ai_enabled = Column(Boolean, default=True, nullable=False)
    # Default provider for orgs that don't configure their own
    default_provider = Column(String(50), default='llamacpp', nullable=False)
    # Super Admin Focused Mode - shows simplified menu for super admin
    super_admin_focused_mode = Column(Boolean, default=False, nullable=False)
    # AI Policy Aligner - global toggle to enable/disable the feature
    ai_policy_aligner_enabled = Column(Boolean, default=False, nullable=False)
    # Legacy fields (kept for backward compatibility with correlations feature)
    custom_llm_url = Column(Text, nullable=True)
    custom_llm_payload = Column(Text, nullable=True)
    max_questions_per_framework = Column(Integer, default=10, nullable=False)
    llm_timeout_seconds = Column(Integer, default=300, nullable=False)
    min_confidence_threshold = Column(Integer, default=75, nullable=False)
    max_correlations = Column(Integer, default=10, nullable=False)
    # Legacy QLON fields (kept for migration, will be moved to org settings)
    llm_provider = Column(String(50), default='llamacpp', nullable=True)
    qlon_url = Column(Text, nullable=True)
    qlon_api_key = Column(Text, nullable=True)
    qlon_use_tools = Column(Boolean, default=True, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class OrganizationLLMSettings(Base):
    """Organization-specific LLM settings. Each org can configure their own AI provider."""
    __tablename__ = "organization_llm_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False, unique=True)
    # Provider selection: 'llamacpp', 'qlon', 'openai', 'anthropic', 'xai', 'google'
    llm_provider = Column(String(50), nullable=False)
    # QLON Ai configuration
    qlon_url = Column(Text, nullable=True)
    qlon_api_key = Column(Text, nullable=True)
    qlon_use_tools = Column(Boolean, default=True, nullable=True)
    # OpenAI (ChatGPT) configuration
    openai_api_key = Column(Text, nullable=True)
    openai_model = Column(String(100), default='gpt-4o', nullable=True)
    openai_base_url = Column(Text, nullable=True)  # Optional for custom endpoints
    # Anthropic (Claude) configuration
    anthropic_api_key = Column(Text, nullable=True)
    anthropic_model = Column(String(100), default='claude-sonnet-4-20250514', nullable=True)
    # X AI (Grok) configuration
    xai_api_key = Column(Text, nullable=True)
    xai_model = Column(String(100), default='grok-3', nullable=True)
    xai_base_url = Column(Text, nullable=True)  # Default: https://api.x.ai/v1
    # Google (Gemini) configuration
    google_api_key = Column(Text, nullable=True)
    google_model = Column(String(100), default='gemini-2.0-flash', nullable=True)
    # Common settings
    is_enabled = Column(Boolean, default=False, nullable=False)  # Org can enable AI for themselves (disabled by default)
    # AI Remediator settings
    ai_remediator_enabled = Column(Boolean, default=False, nullable=False)  # Enable AI Remediator feature
    remediator_prompt_zap = Column(Text, nullable=True)  # Custom prompt for ZAP remediation (null for default)
    remediator_prompt_nmap = Column(Text, nullable=True)  # Custom prompt for Nmap remediation (null for default)
    # AI Policy Aligner settings
    ai_policy_aligner_enabled = Column(Boolean, default=False, nullable=False)  # Enable AI Policy Aligner feature
    policy_aligner_prompt = Column(Text, nullable=True)  # Custom prompt for policy alignment (null for default)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship - using string reference to avoid circular import issues
    organisation = relationship("Organisations", backref="llm_settings")


class PolicyQuestionAlignment(Base):
    """Stores AI-generated alignments between policies and framework questions."""
    __tablename__ = "policy_question_alignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    confidence_score = Column(Integer, nullable=False)  # 0-100
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Unique constraint: one policy per question per framework
    __table_args__ = (
        UniqueConstraint('framework_id', 'question_id', name='uix_framework_question_alignment'),
    )

    # Relationships
    organisation = relationship("Organisations", backref="policy_alignments")
    framework = relationship("Framework", backref="policy_alignments")
    question = relationship("Question", backref="policy_alignments")
    policy = relationship("Policies", backref="question_alignments")


class ScannerSettings(Base):
    __tablename__ = "scanner_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scanners_enabled = Column(Boolean, default=True, nullable=False)
    allowed_scanner_domains = Column(Text, nullable=True)  # JSON array stored as text
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SSOSettings(Base):
    """SSO settings supporting multiple configurations (multi-record)."""
    __tablename__ = "sso_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    label = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
    # Google OAuth2
    google_client_id = Column(Text, nullable=True)
    google_client_secret = Column(Text, nullable=True)
    # Microsoft OAuth2
    microsoft_client_id = Column(Text, nullable=True)
    microsoft_client_secret = Column(Text, nullable=True)
    microsoft_tenant_id = Column(String(255), default="common", nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class FrameworkUpdates(Base):
    __tablename__ = "framework_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id"), nullable=False)
    version = Column(Integer, nullable=False)  # Update version number (1, 2, 3, etc.)
    framework_name = Column(String(50), nullable=False)  # 'cra', 'iso27001', or 'nis2'
    description = Column(Text, nullable=False)  # What this update contains
    status = Column(String(50), nullable=False, default="available")  # available, applied, failed
    applied_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # User who applied the update
    error_message = Column(Text, nullable=True)  # Error details if status=failed
    applied_at = Column(DateTime, nullable=True)  # When the update was applied
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("framework_snapshots.id"), nullable=True)  # Pre-update snapshot
    source = Column(String(50), nullable=False, default="manual")  # manual, regulatory_monitor
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ScannerHistory(Base):
    __tablename__ = "scanner_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scanner_type = Column(String(50), nullable=False)  # 'zap', 'nmap', 'semgrep', 'osv'
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_email = Column(String(255), nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=True)
    organisation_name = Column(String(255), nullable=True)
    scan_target = Column(String(500), nullable=False)  # Target URL or filename
    scan_type = Column(String(100), nullable=True)  # For ZAP: spider/active/full/api, for Nmap: basic/ports/aggressive, etc.
    scan_config = Column(Text, nullable=True)  # JSON string of scan configuration
    results = Column(Text, nullable=False)  # JSON string of results (for ZAP: all alerts array, for others: raw_data)
    summary = Column(Text, nullable=True)  # LLM analysis or summary
    status = Column(String(50), nullable=False, default="completed")  # 'completed', 'failed', 'in_progress'
    error_message = Column(Text, nullable=True)  # Error details if status=failed
    scan_duration = Column(Float, nullable=True)  # Duration in seconds
    timestamp = Column(DateTime, nullable=False, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True)

    asset = relationship("Assets", foreign_keys=[asset_id])


class ScanFinding(Base):
    """Individual finding extracted from a scanner history result"""
    __tablename__ = "scan_findings"
    __table_args__ = (
        UniqueConstraint('scan_history_id', 'finding_hash', name='uq_scan_finding_hash'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_history_id = Column(UUID(as_uuid=True), ForeignKey("scanner_history.id", ondelete="CASCADE"), nullable=False)
    scanner_type = Column(String(50), nullable=False)  # zap, nmap, semgrep, osv
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    finding_hash = Column(String(64), nullable=False)  # SHA256 for dedup
    title = Column(String(500), nullable=False)
    severity = Column(String(50), nullable=True)  # Original severity from scanner
    normalized_severity = Column(String(20), nullable=True)  # high, medium, low, info
    identifier = Column(String(255), nullable=True)  # CWE-ID, CVE-ID, check_id
    description = Column(Text, nullable=True)
    solution = Column(Text, nullable=True)
    url_or_target = Column(String(500), nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON for scanner-specific fields
    is_remediated = Column(Boolean, default=False, nullable=False)
    remediated_at = Column(DateTime, nullable=True)
    remediated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    scan_history = relationship("ScannerHistory", foreign_keys=[scan_history_id])
    organisation = relationship("Organisations", foreign_keys=[organisation_id])
    remediated_by_user = relationship("User", foreign_keys=[remediated_by])


class RiskScanFinding(Base):
    """Junction table linking risks to scan findings"""
    __tablename__ = "risk_scan_findings"

    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), primary_key=True)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("scan_findings.id", ondelete="CASCADE"), primary_key=True)
    is_auto_mapped = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    risk = relationship("Risks", foreign_keys=[risk_id], backref="risk_scan_findings")
    finding = relationship("ScanFinding", foreign_keys=[finding_id], backref="finding_risks")


class Backup(Base):
    """Backup records for organization data"""
    __tablename__ = "backups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    backup_type = Column(String(20), nullable=False, default='scheduled')  # scheduled, manual
    status = Column(String(50), nullable=False, default='completed')  # completed, failed, in_progress
    error_message = Column(Text, nullable=True)
    records_count = Column(Text, nullable=True)  # JSON: {"assessments": 50, "policies": 10, ...}
    evidence_files_count = Column(Integer, nullable=True)
    is_encrypted = Column(Boolean, nullable=False, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    organisation = relationship("Organisations", foreign_keys=[organisation_id])


# ===========================
# Audit Engagement Workspace Models
# ===========================

class AuditorRole(Base):
    """Permissions lookup table for auditor roles"""
    __tablename__ = "auditor_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_name = Column(String(50), unique=True, nullable=False)  # guest_auditor, auditor_lead
    can_comment = Column(Boolean, default=True, nullable=False)
    can_request_evidence = Column(Boolean, default=True, nullable=False)
    can_add_findings = Column(Boolean, default=False, nullable=False)
    can_sign_off = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class AuditEngagement(Base):
    """Core entity wrapping an assessment for external auditor review"""
    __tablename__ = "audit_engagements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)

    # Audit period
    audit_period_start = Column(DateTime, nullable=True)
    audit_period_end = Column(DateTime, nullable=True)

    # Status: draft, planned, in_progress, review, completed, closed
    status = Column(String(50), nullable=False, default="draft")

    # Scope configuration (JSON arrays of IDs)
    _in_scope_controls = Column('in_scope_controls', Text, nullable=True)  # Question IDs
    _in_scope_policies = Column('in_scope_policies', Text, nullable=True)  # Policy IDs
    _in_scope_chapters = Column('in_scope_chapters', Text, nullable=True)  # Chapter IDs

    # Timeline
    planned_start_date = Column(DateTime, nullable=True)
    actual_start_date = Column(DateTime, nullable=True)
    planned_end_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)

    # Ownership
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)

    # For change comparison with prior engagements
    prior_engagement_id = Column(UUID(as_uuid=True), ForeignKey("audit_engagements.id"), nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    assessment = relationship("Assessment", foreign_keys=[assessment_id])
    owner = relationship("User", foreign_keys=[owner_id])
    organisation = relationship("Organisations", foreign_keys=[organisation_id])
    prior_engagement = relationship("AuditEngagement", remote_side=[id], foreign_keys=[prior_engagement_id])

    @hybrid_property
    def in_scope_controls(self):
        if self._in_scope_controls:
            try:
                return json.loads(self._in_scope_controls)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @in_scope_controls.setter
    def in_scope_controls(self, value):
        if value is not None:
            if isinstance(value, list):
                self._in_scope_controls = json.dumps(value)
            elif isinstance(value, str):
                self._in_scope_controls = value
            else:
                self._in_scope_controls = None
        else:
            self._in_scope_controls = None

    @hybrid_property
    def in_scope_policies(self):
        if self._in_scope_policies:
            try:
                return json.loads(self._in_scope_policies)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @in_scope_policies.setter
    def in_scope_policies(self, value):
        if value is not None:
            if isinstance(value, list):
                self._in_scope_policies = json.dumps(value)
            elif isinstance(value, str):
                self._in_scope_policies = value
            else:
                self._in_scope_policies = None
        else:
            self._in_scope_policies = None

    @hybrid_property
    def in_scope_chapters(self):
        if self._in_scope_chapters:
            try:
                return json.loads(self._in_scope_chapters)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @in_scope_chapters.setter
    def in_scope_chapters(self, value):
        if value is not None:
            if isinstance(value, list):
                self._in_scope_chapters = json.dumps(value)
            elif isinstance(value, str):
                self._in_scope_chapters = value
            else:
                self._in_scope_chapters = None
        else:
            self._in_scope_chapters = None


class AuditorInvitation(Base):
    """External auditor access invitation"""
    __tablename__ = "auditor_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("audit_engagements.id", ondelete="CASCADE"), nullable=False)

    # Auditor details
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)

    # Role assignment
    auditor_role_id = Column(UUID(as_uuid=True), ForeignKey("auditor_roles.id"), nullable=False)

    # Access token for magic link auth
    access_token = Column(String(500), nullable=True)
    token_expires_at = Column(DateTime, nullable=True)

    # Time-bound access
    access_start = Column(DateTime, nullable=True)
    access_end = Column(DateTime, nullable=True)

    # Security settings
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)  # TOTP secret
    _ip_allowlist = Column('ip_allowlist', Text, nullable=True)  # JSON array of IPs

    # Download restrictions
    download_restricted = Column(Boolean, default=False, nullable=False)
    watermark_downloads = Column(Boolean, default=True, nullable=False)

    # Status: pending, accepted, expired, revoked
    status = Column(String(50), nullable=False, default="pending")

    # Tracking
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    engagement = relationship("AuditEngagement", foreign_keys=[engagement_id])
    auditor_role = relationship("AuditorRole", foreign_keys=[auditor_role_id])
    inviter = relationship("User", foreign_keys=[invited_by])

    @hybrid_property
    def ip_allowlist(self):
        if self._ip_allowlist:
            try:
                return json.loads(self._ip_allowlist)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @ip_allowlist.setter
    def ip_allowlist(self, value):
        if value is not None:
            if isinstance(value, list):
                self._ip_allowlist = json.dumps(value)
            elif isinstance(value, str):
                self._ip_allowlist = value
            else:
                self._ip_allowlist = None
        else:
            self._ip_allowlist = None


class AuditComment(Base):
    """Comments on audit items (answers, evidence, objectives, policies)"""
    __tablename__ = "audit_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("audit_engagements.id", ondelete="CASCADE"), nullable=False)

    # Target reference - polymorphic design
    target_type = Column(String(50), nullable=False)  # answer, evidence, objective, policy
    target_id = Column(UUID(as_uuid=True), nullable=False)

    # Comment type
    comment_type = Column(String(50), nullable=False, default="observation")  # question, evidence_request, observation, potential_exception

    # Content
    content = Column(Text, nullable=False)

    # Threading support
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("audit_comments.id"), nullable=True)

    # Assignment
    assigned_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Assigned to internal user
    assigned_to_auditor_id = Column(UUID(as_uuid=True), ForeignKey("auditor_invitations.id"), nullable=True)  # Assigned to external auditor
    due_date = Column(DateTime, nullable=True)

    # Status tracking
    status = Column(String(50), nullable=False, default="open")  # open, in_progress, resolved, closed

    # Resolution
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolved_by_auditor_id = Column(UUID(as_uuid=True), ForeignKey("auditor_invitations.id"), nullable=True)
    resolution_note = Column(Text, nullable=True)

    # Author - can be internal user OR external auditor
    author_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    author_auditor_id = Column(UUID(as_uuid=True), ForeignKey("auditor_invitations.id"), nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    engagement = relationship("AuditEngagement", foreign_keys=[engagement_id])
    parent_comment = relationship("AuditComment", remote_side=[id], foreign_keys=[parent_comment_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    assigned_to_auditor = relationship("AuditorInvitation", foreign_keys=[assigned_to_auditor_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    resolved_by_auditor = relationship("AuditorInvitation", foreign_keys=[resolved_by_auditor_id])
    author_user = relationship("User", foreign_keys=[author_user_id])
    author_auditor = relationship("AuditorInvitation", foreign_keys=[author_auditor_id])


class AuditCommentAttachment(Base):
    """Attachments on audit comments"""
    __tablename__ = "audit_comment_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comment_id = Column(UUID(as_uuid=True), ForeignKey("audit_comments.id", ondelete="CASCADE"), nullable=False)

    filename = Column(String(500), nullable=False)
    filepath = Column(Text, nullable=False)
    file_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)

    uploaded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    uploaded_by_auditor_id = Column(UUID(as_uuid=True), ForeignKey("auditor_invitations.id"), nullable=True)

    created_at = Column(DateTime, default=func.now())

    # Relationships
    comment = relationship("AuditComment", foreign_keys=[comment_id])
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by_user_id])
    uploaded_by_auditor = relationship("AuditorInvitation", foreign_keys=[uploaded_by_auditor_id])


class AuditFinding(Base):
    """Audit findings from the review process"""
    __tablename__ = "audit_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("audit_engagements.id", ondelete="CASCADE"), nullable=False)

    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    # Severity classification
    severity = Column(String(50), nullable=False, default="medium")  # low, medium, high, critical

    # Category of finding
    category = Column(String(100), nullable=False)  # control_deficiency, documentation_gap, compliance_issue, process_weakness

    # Related items (JSON arrays of IDs)
    _related_controls = Column('related_controls', Text, nullable=True)
    _related_evidence = Column('related_evidence', Text, nullable=True)

    # Remediation tracking
    remediation_plan = Column(Text, nullable=True)
    remediation_owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    remediation_due_date = Column(DateTime, nullable=True)

    # Status: draft, confirmed, remediation_in_progress, remediated, accepted, closed
    status = Column(String(50), nullable=False, default="draft")

    # Author - can be internal user OR external auditor
    author_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    author_auditor_id = Column(UUID(as_uuid=True), ForeignKey("auditor_invitations.id"), nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    engagement = relationship("AuditEngagement", foreign_keys=[engagement_id])
    remediation_owner = relationship("User", foreign_keys=[remediation_owner_id])
    author_user = relationship("User", foreign_keys=[author_user_id])
    author_auditor = relationship("AuditorInvitation", foreign_keys=[author_auditor_id])

    @hybrid_property
    def related_controls(self):
        if self._related_controls:
            try:
                return json.loads(self._related_controls)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @related_controls.setter
    def related_controls(self, value):
        if value is not None:
            if isinstance(value, list):
                self._related_controls = json.dumps(value)
            elif isinstance(value, str):
                self._related_controls = value
            else:
                self._related_controls = None
        else:
            self._related_controls = None

    @hybrid_property
    def related_evidence(self):
        if self._related_evidence:
            try:
                return json.loads(self._related_evidence)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @related_evidence.setter
    def related_evidence(self, value):
        if value is not None:
            if isinstance(value, list):
                self._related_evidence = json.dumps(value)
            elif isinstance(value, str):
                self._related_evidence = value
            else:
                self._related_evidence = None
        else:
            self._related_evidence = None


class AuditSignOff(Base):
    """Sign-off records for audit items"""
    __tablename__ = "audit_sign_offs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("audit_engagements.id", ondelete="CASCADE"), nullable=False)

    # Sign-off scope
    sign_off_type = Column(String(50), nullable=False)  # control, section, engagement
    target_id = Column(UUID(as_uuid=True), nullable=True)  # NULL for engagement-level sign-off

    # Sign-off status
    status = Column(String(50), nullable=False)  # approved, approved_with_exceptions, rejected

    # Comments/notes
    comments = Column(Text, nullable=True)

    # Signer details
    signer_auditor_id = Column(UUID(as_uuid=True), ForeignKey("auditor_invitations.id"), nullable=False)
    signed_at = Column(DateTime, nullable=False, default=func.now())

    # Audit trail for sign-off
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now())

    # Relationships
    engagement = relationship("AuditEngagement", foreign_keys=[engagement_id])
    signer = relationship("AuditorInvitation", foreign_keys=[signer_auditor_id])


class AuditActivityLog(Base):
    """Activity log for audit engagements"""
    __tablename__ = "audit_activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("audit_engagements.id", ondelete="CASCADE"), nullable=False)

    # Actor - can be internal user OR external auditor
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    auditor_id = Column(UUID(as_uuid=True), ForeignKey("auditor_invitations.id"), nullable=True)

    # Action details
    action = Column(String(100), nullable=False)  # viewed, commented, signed_off, downloaded, etc.
    target_type = Column(String(50), nullable=True)  # control, evidence, policy, etc.
    target_id = Column(UUID(as_uuid=True), nullable=True)

    # Additional details (JSON)
    _details = Column('details', Text, nullable=True)

    # Request metadata
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now())

    # Relationships
    engagement = relationship("AuditEngagement", foreign_keys=[engagement_id])
    user = relationship("User", foreign_keys=[user_id])
    auditor = relationship("AuditorInvitation", foreign_keys=[auditor_id])

    @hybrid_property
    def details(self):
        if self._details:
            try:
                return json.loads(self._details)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @details.setter
    def details(self, value):
        if value is not None:
            if isinstance(value, dict):
                self._details = json.dumps(value)
            elif isinstance(value, str):
                self._details = value
            else:
                self._details = None
        else:
            self._details = None


class EvidenceIntegrity(Base):
    """Track file integrity and version history for evidence files"""
    __tablename__ = "evidence_integrity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False)

    # Version tracking
    version = Column(Integer, nullable=False, default=1)

    # File integrity hashes
    sha256_hash = Column(String(64), nullable=False)
    md5_hash = Column(String(32), nullable=True)

    # File metadata at time of hash
    file_size = Column(Integer, nullable=False)
    original_filename = Column(String(255), nullable=False)

    # Upload tracking
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=func.now())

    # Version chain
    previous_version_id = Column(UUID(as_uuid=True), ForeignKey("evidence_integrity.id"), nullable=True)

    # Integrity verification status
    last_verified_at = Column(DateTime, nullable=True)
    verification_status = Column(String(20), nullable=True)  # valid, corrupted, missing

    created_at = Column(DateTime, default=func.now())

    # Relationships
    evidence = relationship("Evidence", foreign_keys=[evidence_id])
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
    previous_version = relationship("EvidenceIntegrity", remote_side=[id], foreign_keys=[previous_version_id])


# ===========================
# NVD Vulnerability Sync Models
# ===========================

class NVDSettings(Base):
    """Global NVD settings for vulnerability sync"""
    __tablename__ = "nvd_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key = Column(Text, nullable=True)  # Optional NVD API key for higher rate limits
    sync_enabled = Column(Boolean, default=True, nullable=False)
    sync_hour = Column(Integer, default=3, nullable=False)  # Hour of day for daily sync (0-23)
    sync_minute = Column(Integer, default=0, nullable=False)  # Minute of hour for sync
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class NVDSyncStatus(Base):
    """Track NVD sync history and status"""
    __tablename__ = "nvd_sync_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(50), nullable=False, default="pending")  # pending, in_progress, completed, failed
    sync_type = Column(String(50), nullable=False, default="incremental")  # full, incremental
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cves_processed = Column(Integer, default=0, nullable=False)
    cves_added = Column(Integer, default=0, nullable=False)
    cves_updated = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # NULL for scheduled syncs
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    triggered_by_user = relationship("User", foreign_keys=[triggered_by])


class CVE(Base):
    """Store CVE vulnerability data from NVD"""
    __tablename__ = "cves"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cve_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., CVE-2021-44228
    description = Column(Text, nullable=True)

    # CVSS v3.x scores
    cvss_v3_score = Column(Float, nullable=True)
    cvss_v3_severity = Column(String(20), nullable=True)  # NONE, LOW, MEDIUM, HIGH, CRITICAL
    cvss_v3_vector = Column(String(200), nullable=True)

    # CVSS v2 scores (for older CVEs)
    cvss_v2_score = Column(Float, nullable=True)
    cvss_v2_severity = Column(String(20), nullable=True)

    # Dates
    published_date = Column(DateTime, nullable=True)
    last_modified_date = Column(DateTime, nullable=True)

    # Vulnerability status
    vuln_status = Column(String(50), nullable=True)  # Analyzed, Modified, Rejected, etc.

    # References (stored as JSON array)
    _references = Column('references', Text, nullable=True)

    # CWE IDs (stored as JSON array)
    _cwe_ids = Column('cwe_ids', Text, nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    @hybrid_property
    def references(self):
        if self._references:
            try:
                return json.loads(self._references)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @references.setter
    def references(self, value):
        if value is not None:
            if isinstance(value, list):
                self._references = json.dumps(value)
            elif isinstance(value, str):
                self._references = value
            else:
                self._references = None
        else:
            self._references = None

    @hybrid_property
    def cwe_ids(self):
        if self._cwe_ids:
            try:
                return json.loads(self._cwe_ids)
            except (json.JSONDecodeError, TypeError):
                return None
        return None

    @cwe_ids.setter
    def cwe_ids(self, value):
        if value is not None:
            if isinstance(value, list):
                self._cwe_ids = json.dumps(value)
            elif isinstance(value, str):
                self._cwe_ids = value
            else:
                self._cwe_ids = None
        else:
            self._cwe_ids = None


class CPEMatch(Base):
    """CPE configurations linked to CVEs with version ranges"""
    __tablename__ = "cpe_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cve_id = Column(UUID(as_uuid=True), ForeignKey("cves.id", ondelete="CASCADE"), nullable=False)

    # CPE URI (e.g., cpe:2.3:a:openbsd:openssh:7.4:*:*:*:*:*:*:*)
    cpe_uri = Column(String(500), nullable=False, index=True)

    # Parsed CPE components for faster matching
    cpe_vendor = Column(String(200), nullable=True, index=True)
    cpe_product = Column(String(200), nullable=True, index=True)
    cpe_version = Column(String(100), nullable=True)

    # Version range for matching
    version_start_including = Column(String(100), nullable=True)
    version_start_excluding = Column(String(100), nullable=True)
    version_end_including = Column(String(100), nullable=True)
    version_end_excluding = Column(String(100), nullable=True)

    # Whether this is a vulnerable configuration
    vulnerable = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    cve = relationship("CVE", foreign_keys=[cve_id], backref="cpe_matches")


class AssetTypes(Base):
    """Asset type categories for organizing assets"""
    __tablename__ = "asset_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    icon_name = Column(String(100), nullable=True)  # Ant Design icon name
    description = Column(Text, nullable=True)
    # CIA default ratings for assets of this type
    default_confidentiality = Column(String(10), nullable=True)  # 'low', 'medium', 'high'
    default_integrity = Column(String(10), nullable=True)
    default_availability = Column(String(10), nullable=True)
    default_asset_value = Column(String(10), nullable=True)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    organisation = relationship("Organisations", foreign_keys=[organisation_id])


class AssetStatuses(Base):
    """Asset status lookup table"""
    __tablename__ = "asset_statuses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.now())


class Assets(Base):
    """Individual assets belonging to asset types"""
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    version = Column(String(100), nullable=True)  # Asset version
    justification = Column(Text, nullable=True)  # Justification for the asset
    license_model = Column(String(255), nullable=True)  # License information
    description = Column(Text, nullable=True)
    sbom = Column(Text, nullable=True)  # Software Bill of Materials
    ip_address = Column(String(500), nullable=True)  # IP address, IP range, or URL
    asset_type_id = Column(UUID(as_uuid=True), ForeignKey("asset_types.id"), nullable=False)
    asset_status_id = Column(UUID(as_uuid=True), ForeignKey("asset_statuses.id"), nullable=True)
    economic_operator_id = Column(UUID(as_uuid=True), ForeignKey("economic_operators.id"), nullable=True)
    criticality_id = Column(UUID(as_uuid=True), ForeignKey("criticalities.id"), nullable=True)
    criticality_option = Column(Text, nullable=True)  # Selected criticality option value
    # CIA ratings
    confidentiality = Column(String(10), nullable=True)  # 'low', 'medium', 'high'
    integrity = Column(String(10), nullable=True)
    availability = Column(String(10), nullable=True)
    asset_value = Column(String(10), nullable=True)
    inherit_cia = Column(Boolean, nullable=False, default=True)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    asset_type = relationship("AssetTypes", foreign_keys=[asset_type_id])
    asset_status = relationship("AssetStatuses", foreign_keys=[asset_status_id])
    economic_operator = relationship("EconomicOperators", foreign_keys=[economic_operator_id])
    criticality = relationship("Criticalities", foreign_keys=[criticality_id])
    organisation = relationship("Organisations", foreign_keys=[organisation_id])


class AssetRisk(Base):
    """Junction table linking assets to risks (many-to-many)"""
    __tablename__ = "asset_risks"

    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    asset = relationship("Assets", foreign_keys=[asset_id], backref="asset_risks")
    risk = relationship("Risks", foreign_keys=[risk_id], backref="risk_assets")


class NmapServiceVulnerability(Base):
    """Correlation results linking Nmap scans to CVEs"""
    __tablename__ = "nmap_service_vulnerabilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_history_id = Column(UUID(as_uuid=True), ForeignKey("scanner_history.id", ondelete="CASCADE"), nullable=False)
    cve_id = Column(UUID(as_uuid=True), ForeignKey("cves.id", ondelete="CASCADE"), nullable=False)

    # Service details from Nmap scan
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    protocol = Column(String(10), nullable=True)  # tcp, udp
    service_name = Column(String(100), nullable=True)
    service_product = Column(String(200), nullable=True)
    service_version = Column(String(100), nullable=True)

    # Generated CPE used for matching
    generated_cpe = Column(String(500), nullable=True)

    # Match confidence (0-100)
    confidence = Column(Integer, default=100, nullable=False)

    # Match details
    match_type = Column(String(50), nullable=True)  # exact, version_range, product_only

    created_at = Column(DateTime, default=func.now())

    # Relationships
    scan_history = relationship("ScannerHistory", foreign_keys=[scan_history_id])
    cve = relationship("CVE", foreign_keys=[cve_id])


# ===========================
# Audit Review Status & Notifications
# ===========================

class ControlReviewStatus(Base):
    """Track the review status of each control (answer) within an audit engagement"""
    __tablename__ = "control_review_statuses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("audit_engagements.id", ondelete="CASCADE"), nullable=False)
    answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id", ondelete="CASCADE"), nullable=False)

    # Review status workflow:
    # not_started -> pending_review (auditor needs to review)
    # pending_review -> information_requested (auditor asked a question)
    # information_requested -> response_provided (employee responded)
    # response_provided -> pending_review (back to auditor for review)
    # pending_review -> approved / approved_with_exceptions / needs_remediation
    status = Column(String(50), nullable=False, default="not_started")
    # Statuses: not_started, pending_review, information_requested, response_provided,
    #           in_review, approved, approved_with_exceptions, needs_remediation

    # Track who last updated the status
    last_updated_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_updated_by_auditor_id = Column(UUID(as_uuid=True), ForeignKey("auditor_invitations.id"), nullable=True)

    # Notes about the current status
    status_note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    engagement = relationship("AuditEngagement", foreign_keys=[engagement_id])
    answer = relationship("Answer", foreign_keys=[answer_id])
    last_updated_by_user = relationship("User", foreign_keys=[last_updated_by_user_id])
    last_updated_by_auditor = relationship("AuditorInvitation", foreign_keys=[last_updated_by_auditor_id])

    # Unique constraint - one status per control per engagement
    __table_args__ = (
        CheckConstraint(
            "status IN ('not_started', 'pending_review', 'information_requested', 'response_provided', 'in_review', 'approved', 'approved_with_exceptions', 'needs_remediation')",
            name='valid_review_status'
        ),
    )


class AuditNotification(Base):
    """Track notifications for audit-related activities"""
    __tablename__ = "audit_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey("audit_engagements.id", ondelete="CASCADE"), nullable=False)

    # Recipient - either a user or an auditor
    recipient_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    recipient_auditor_id = Column(UUID(as_uuid=True), ForeignKey("auditor_invitations.id"), nullable=True)

    # Notification type
    notification_type = Column(String(50), nullable=False)
    # Types: new_comment, comment_reply, status_change, information_requested,
    #        response_provided, finding_added, sign_off_requested

    # Reference to the source of the notification
    source_type = Column(String(50), nullable=False)  # comment, control, finding, sign_off
    source_id = Column(UUID(as_uuid=True), nullable=False)

    # Related control/answer for quick reference
    related_answer_id = Column(UUID(as_uuid=True), ForeignKey("answers.id"), nullable=True)

    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)

    # Sender info
    sender_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    sender_auditor_id = Column(UUID(as_uuid=True), ForeignKey("auditor_invitations.id"), nullable=True)

    # Read status
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=func.now())

    # Relationships
    engagement = relationship("AuditEngagement", foreign_keys=[engagement_id])
    recipient_user = relationship("User", foreign_keys=[recipient_user_id])
    recipient_auditor = relationship("AuditorInvitation", foreign_keys=[recipient_auditor_id])
    sender_user = relationship("User", foreign_keys=[sender_user_id])
    sender_auditor = relationship("AuditorInvitation", foreign_keys=[sender_auditor_id])
    related_answer = relationship("Answer", foreign_keys=[related_answer_id])


# ===========================
# Controls Management Models
# ===========================

class ControlSet(Base):
    """Control sets (categories/groups) - like tabs in Excel"""
    __tablename__ = "control_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    organisation = relationship("Organisations", foreign_keys=[organisation_id])


class ControlStatus(Base):
    """Control status lookup table"""
    __tablename__ = "control_statuses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status_name = Column(String(100), nullable=False, unique=True)  # Not Implemented, Partially Implemented, Implemented, N/A
    created_at = Column(DateTime, default=func.now())


class Control(Base):
    """Individual controls"""
    __tablename__ = "controls"
    __table_args__ = (
        UniqueConstraint('organisation_id', 'code', name='uq_controls_org_code'),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), nullable=False)  # e.g., HRM-1, HRM-2
    name = Column(Text, nullable=False)  # Control name/description
    description = Column(Text, nullable=True)  # Additional details
    category = Column(String(255), nullable=True)  # e.g., Human Resources Management
    owner = Column(String(255), nullable=True)  # Owner of the control
    control_set_id = Column(UUID(as_uuid=True), ForeignKey("control_sets.id"), nullable=False)
    control_status_id = Column(UUID(as_uuid=True), ForeignKey("control_statuses.id"), nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    control_set = relationship("ControlSet", foreign_keys=[control_set_id])
    control_status = relationship("ControlStatus", foreign_keys=[control_status_id])
    organisation = relationship("Organisations", foreign_keys=[organisation_id])


class ControlRisk(Base):
    """Junction table linking controls to risks (many-to-many), scoped by framework"""
    __tablename__ = "control_risks"

    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), primary_key=True)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    control = relationship("Control", foreign_keys=[control_id], backref="control_risks")
    risk = relationship("Risks", foreign_keys=[risk_id], backref="risk_controls")
    framework = relationship("Framework", foreign_keys=[framework_id])


class ControlPolicy(Base):
    """Junction table linking controls to policies (many-to-many), scoped by framework"""
    __tablename__ = "control_policies"

    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id", ondelete="CASCADE"), primary_key=True)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    control = relationship("Control", foreign_keys=[control_id], backref="control_policies")
    policy = relationship("Policies", foreign_keys=[policy_id], backref="policy_controls")
    framework = relationship("Framework", foreign_keys=[framework_id])


class ObjectiveRisk(Base):
    """Junction table linking objectives to risks (many-to-many)"""
    __tablename__ = "objective_risks"

    objective_id = Column(UUID(as_uuid=True), ForeignKey("objectives.id", ondelete="CASCADE"), primary_key=True)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    objective = relationship("Objectives", foreign_keys=[objective_id], backref="objective_risks")
    risk = relationship("Risks", foreign_keys=[risk_id], backref="risk_objectives")


class ObjectiveControl(Base):
    """Junction table linking objectives to controls (many-to-many)"""
    __tablename__ = "objective_controls"

    objective_id = Column(UUID(as_uuid=True), ForeignKey("objectives.id", ondelete="CASCADE"), primary_key=True)
    control_id = Column(UUID(as_uuid=True), ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    objective = relationship("Objectives", foreign_keys=[objective_id], backref="objective_controls")
    control = relationship("Control", foreign_keys=[control_id], backref="control_objectives")


# ===========================
# Template Catalog Models
# ===========================

class FrameworkTemplate(Base):
    """Framework templates available for seeding"""
    __tablename__ = "framework_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(String(100), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    seed_filename = Column(String(255), nullable=True)
    source = Column(String(50), nullable=True, default="seed_file")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class PolicyTemplate(Base):
    """Policy templates sourced from .docx files"""
    __tablename__ = "policy_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=True)
    policy_code = Column(String(50), nullable=True)
    content_docx = Column(LargeBinary, nullable=True)
    content_sha256 = Column(String(64), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_modified_at = Column(DateTime, nullable=True)
    source = Column(String(50), nullable=True, default="file")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ControlSetTemplate(Base):
    """Control set templates (catalog)"""
    __tablename__ = "control_set_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=True, default="builtin")
    control_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ControlTemplate(Base):
    """Individual control templates belonging to a control set template"""
    __tablename__ = "control_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    control_set_template_id = Column(UUID(as_uuid=True), ForeignKey("control_set_templates.id"), nullable=False)
    code = Column(String(100), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint("control_set_template_id", "code", name="uq_control_template_set_code"),
    )


# ===========================
# Incident Registration Models
# ===========================

class IncidentStatuses(Base):
    __tablename__ = "incident_statuses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_status_name = Column(String(50), nullable=False, unique=True)


class Incidents(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        UniqueConstraint('organisation_id', 'incident_code', name='uq_incidents_org_incident_code'),
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_code = Column(String(50), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    incident_severity_id = Column(UUID(as_uuid=True), ForeignKey("risk_severity.id"), nullable=False)
    incident_status_id = Column(UUID(as_uuid=True), ForeignKey("incident_statuses.id"), nullable=False)
    reported_by = Column(String(255), nullable=True)
    assigned_to = Column(String(255), nullable=True)
    discovered_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    containment_actions = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    remediation_steps = Column(Text, nullable=True)
    ai_analysis = Column(Text, nullable=True)
    # Post-market surveillance fields
    vulnerability_source = Column(String(50), nullable=True)
    cvss_score = Column(Float, nullable=True)
    cve_id = Column(String(50), nullable=True)
    cwe_id = Column(String(50), nullable=True)
    euvd_vulnerability_id = Column(UUID(as_uuid=True), ForeignKey("euvd_vulnerabilities.id", ondelete="SET NULL"), nullable=True)
    triage_status = Column(String(50), nullable=True)
    sla_deadline = Column(DateTime, nullable=True)
    sla_status = Column(String(20), nullable=True)
    affected_products = Column(Text, nullable=True)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class IncidentFramework(Base):
    __tablename__ = "incident_frameworks"
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())


class IncidentRisk(Base):
    __tablename__ = "incident_risks"
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())


class IncidentAsset(Base):
    __tablename__ = "incident_assets"
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())


class RiskTemplateCategory(Base):
    """Risk template categories"""
    __tablename__ = "risk_template_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_key = Column(String(100), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    risk_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=func.now())


class RiskTemplate(Base):
    """Individual risk templates"""
    __tablename__ = "risk_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("risk_template_categories.id"), nullable=False)
    risk_code = Column(String(50), nullable=False, unique=True)
    risk_category_name = Column(String(255), nullable=False)
    risk_category_description = Column(Text, nullable=True)
    risk_potential_impact = Column(Text, nullable=True)
    risk_control = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())


# ===========================
# EUVD (EU Vulnerability Database) Models
# ===========================

class EUVDVulnerability(Base):
    __tablename__ = "euvd_vulnerabilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    euvd_id = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    date_published = Column(DateTime, nullable=True)
    date_updated = Column(DateTime, nullable=True)
    base_score = Column(Float, nullable=True)
    base_score_version = Column(String(10), nullable=True)
    base_score_vector = Column(String(200), nullable=True)
    epss = Column(Float, nullable=True)
    assigner = Column(String(255), nullable=True)
    references = Column(Text, nullable=True)
    aliases = Column(Text, nullable=True)
    products = Column(Text, nullable=True)
    vendors = Column(Text, nullable=True)
    is_exploited = Column(Boolean, default=False, index=True)
    is_critical = Column(Boolean, default=False, index=True)
    category = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class EUVDSyncStatus(Base):
    __tablename__ = "euvd_sync_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), nullable=False, default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    vulns_processed = Column(Integer, default=0)
    vulns_added = Column(Integer, default=0)
    vulns_updated = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ScanSchedule(Base):
    """Scheduled scan jobs for recurring security scans"""
    __tablename__ = "scan_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scanner_type = Column(String(50), nullable=False)  # 'zap', 'nmap', 'semgrep', 'osv', 'syft'
    scan_target = Column(String(500), nullable=False)  # Target URL, IP, or filename
    scan_type = Column(String(100), nullable=True)  # e.g., 'basic', 'spider', 'active', 'full', 'auto'
    scan_config = Column(Text, nullable=True)  # JSON string of extra config (github_token, ports, config, use_llm etc.)

    # Schedule configuration - interval-based
    schedule_type = Column(String(20), nullable=False, default='interval')  # 'interval' or 'cron'
    interval_months = Column(Integer, nullable=False, default=0)
    interval_days = Column(Integer, nullable=False, default=0)
    interval_hours = Column(Integer, nullable=False, default=0)
    interval_minutes = Column(Integer, nullable=False, default=0)
    interval_seconds = Column(Integer, nullable=False, default=0)

    # Schedule configuration - cron-based (day of week at specific time)
    cron_day_of_week = Column(String(20), nullable=True)  # 'mon','tue','wed','thu','fri','sat','sun' or '*' or comma-separated
    cron_hour = Column(Integer, nullable=True)  # 0-23
    cron_minute = Column(Integer, nullable=True)  # 0-59

    # State
    is_enabled = Column(Boolean, nullable=False, default=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_status = Column(String(50), nullable=True)  # 'completed', 'failed', 'running'
    last_error = Column(Text, nullable=True)
    run_count = Column(Integer, nullable=False, default=0)

    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user_email = Column(String(255), nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=True)
    organisation_name = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    organisation = relationship("Organisations", foreign_keys=[organisation_id])


# ===========================
# Risk Assessment Models
# ===========================

class RiskAssessment(Base):
    """Quantitative risk assessment using 5x5 matrix methodology"""
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(UUID(as_uuid=True), ForeignKey("risks.id", ondelete="CASCADE"), nullable=False)
    assessment_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)

    # Inherent risk (before controls)
    inherent_impact = Column(Integer, nullable=False)
    inherent_likelihood = Column(Integer, nullable=False)
    inherent_risk_score = Column(Integer, nullable=False)

    # Current risk (with existing controls)
    current_impact = Column(Integer, nullable=False)
    current_likelihood = Column(Integer, nullable=False)
    current_risk_score = Column(Integer, nullable=False)

    # Target risk (desired state)
    target_impact = Column(Integer, nullable=True)
    target_likelihood = Column(Integer, nullable=True)
    target_risk_score = Column(Integer, nullable=True)

    # Residual risk (after treatment)
    residual_impact = Column(Integer, nullable=True)
    residual_likelihood = Column(Integer, nullable=True)
    residual_risk_score = Column(Integer, nullable=True)

    # Impact Loss Analysis
    impact_health = Column(Text, nullable=True)
    impact_financial = Column(Text, nullable=True)
    impact_service = Column(Text, nullable=True)
    impact_legal = Column(Text, nullable=True)
    impact_reputation = Column(Text, nullable=True)

    status = Column(String(50), nullable=False, default="Draft")  # Draft, In Progress, Completed

    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("inherent_impact >= 1 AND inherent_impact <= 5", name="ck_inherent_impact_range"),
        CheckConstraint("inherent_likelihood >= 1 AND inherent_likelihood <= 5", name="ck_inherent_likelihood_range"),
        CheckConstraint("current_impact >= 1 AND current_impact <= 5", name="ck_current_impact_range"),
        CheckConstraint("current_likelihood >= 1 AND current_likelihood <= 5", name="ck_current_likelihood_range"),
        CheckConstraint("target_impact IS NULL OR (target_impact >= 1 AND target_impact <= 5)", name="ck_target_impact_range"),
        CheckConstraint("target_likelihood IS NULL OR (target_likelihood >= 1 AND target_likelihood <= 5)", name="ck_target_likelihood_range"),
        CheckConstraint("residual_impact IS NULL OR (residual_impact >= 1 AND residual_impact <= 5)", name="ck_residual_impact_range"),
        CheckConstraint("residual_likelihood IS NULL OR (residual_likelihood >= 1 AND residual_likelihood <= 5)", name="ck_residual_likelihood_range"),
    )

    # Relationships
    risk = relationship("Risks", foreign_keys=[risk_id], backref="risk_assessments")
    assessed_by_user = relationship("User", foreign_keys=[assessed_by])
    organisation = relationship("Organisations", foreign_keys=[organisation_id])
    treatment_actions = relationship("RiskTreatmentAction", back_populates="assessment", cascade="all, delete-orphan")


class RiskTreatmentAction(Base):
    """Treatment action items for risk assessments"""
    __tablename__ = "risk_treatment_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("risk_assessments.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(DateTime, nullable=True)
    owner = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="Open")  # Open, In Progress, Completed, Cancelled
    completion_notes = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    assessment = relationship("RiskAssessment", back_populates="treatment_actions")


class EUVDSettings(Base):
    __tablename__ = "euvd_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_enabled = Column(Boolean, default=True, nullable=False)
    sync_interval_hours = Column(Integer, default=1, nullable=False)
    sync_interval_seconds = Column(Integer, default=0, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# ===========================
# CE Marking Checklist Models
# ===========================

class CEProductTypes(Base):
    __tablename__ = "ce_product_types"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    recommended_placement = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())


class CEDocumentTypes(Base):
    __tablename__ = "ce_document_types"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_mandatory = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now())


class CEChecklistTemplateItems(Base):
    __tablename__ = "ce_checklist_template_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_mandatory = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())


class CEMarkingChecklists(Base):
    __tablename__ = "ce_marking_checklists"
    __table_args__ = (
        UniqueConstraint('asset_id', name='uq_ce_checklist_asset'),
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    ce_product_type_id = Column(UUID(as_uuid=True), ForeignKey("ce_product_types.id"), nullable=True)
    ce_placement = Column(String(100), nullable=True)
    ce_placement_notes = Column(Text, nullable=True)
    notified_body_required = Column(Boolean, default=False, nullable=False)
    notified_body_name = Column(String(255), nullable=True)
    notified_body_number = Column(String(100), nullable=True)
    notified_body_certificate_ref = Column(String(255), nullable=True)
    version_identifier = Column(String(255), nullable=True)
    build_identifier = Column(String(255), nullable=True)
    doc_publication_url = Column(String(500), nullable=True)
    product_variants = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="not_started")
    readiness_score = Column(Float, default=0.0, nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    asset = relationship("Assets", foreign_keys=[asset_id])
    ce_product_type = relationship("CEProductTypes", foreign_keys=[ce_product_type_id])
    organisation = relationship("Organisations", foreign_keys=[organisation_id])


class CEChecklistItems(Base):
    __tablename__ = "ce_checklist_items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checklist_id = Column(UUID(as_uuid=True), ForeignKey("ce_marking_checklists.id", ondelete="CASCADE"), nullable=False)
    template_item_id = Column(UUID(as_uuid=True), ForeignKey("ce_checklist_template_items.id"), nullable=True)
    category = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_mandatory = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    checklist = relationship("CEMarkingChecklists", foreign_keys=[checklist_id])


class CEDocumentStatuses(Base):
    __tablename__ = "ce_document_statuses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checklist_id = Column(UUID(as_uuid=True), ForeignKey("ce_marking_checklists.id", ondelete="CASCADE"), nullable=False)
    document_type_id = Column(UUID(as_uuid=True), ForeignKey("ce_document_types.id"), nullable=False)
    status = Column(String(50), nullable=False, default="not_started")
    document_reference = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    completed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    checklist = relationship("CEMarkingChecklists", foreign_keys=[checklist_id])
    document_type = relationship("CEDocumentTypes", foreign_keys=[document_type_id])


# ===========================
# Post-Market Surveillance Models
# ===========================

class IncidentPatches(Base):
    __tablename__ = "incident_patches"
    __table_args__ = (
        UniqueConstraint('incident_id', 'patch_version', name='uq_incident_patch_version'),
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    patch_version = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    release_date = Column(DateTime, nullable=True)
    target_sla_date = Column(DateTime, nullable=True)
    actual_resolution_date = Column(DateTime, nullable=True)
    sla_compliance = Column(String(20), nullable=True)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    incident = relationship("Incidents", foreign_keys=[incident_id])
    organisation = relationship("Organisations", foreign_keys=[organisation_id])


class AdvisoryStatuses(Base):
    __tablename__ = "advisory_statuses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status_name = Column(String(50), nullable=False, unique=True)


class SecurityAdvisories(Base):
    __tablename__ = "security_advisories"
    __table_args__ = (
        UniqueConstraint('organisation_id', 'advisory_code', name='uq_advisories_org_code'),
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    advisory_code = Column(String(50), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    affected_versions = Column(Text, nullable=True)
    fixed_version = Column(String(255), nullable=True)
    severity = Column(String(50), nullable=True)
    cve_ids = Column(Text, nullable=True)
    workaround = Column(Text, nullable=True)
    advisory_status_id = Column(UUID(as_uuid=True), ForeignKey("advisory_statuses.id"), nullable=False)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    published_at = Column(DateTime, nullable=True)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    advisory_status = relationship("AdvisoryStatuses", foreign_keys=[advisory_status_id])
    incident = relationship("Incidents", foreign_keys=[incident_id])
    organisation = relationship("Organisations", foreign_keys=[organisation_id])


class ENISANotifications(Base):
    __tablename__ = "enisa_notifications"
    __table_args__ = (
        UniqueConstraint('incident_id', name='uq_enisa_incident'),
    )
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    # 24h early warning
    early_warning_required = Column(Boolean, default=True, nullable=False)
    early_warning_deadline = Column(DateTime, nullable=True)
    early_warning_submitted = Column(Boolean, default=False, nullable=False)
    early_warning_submitted_at = Column(DateTime, nullable=True)
    early_warning_content = Column(Text, nullable=True)
    # 72h vulnerability notification
    vuln_notification_required = Column(Boolean, default=True, nullable=False)
    vuln_notification_deadline = Column(DateTime, nullable=True)
    vuln_notification_submitted = Column(Boolean, default=False, nullable=False)
    vuln_notification_submitted_at = Column(DateTime, nullable=True)
    vuln_notification_content = Column(Text, nullable=True)
    # 14d final report
    final_report_required = Column(Boolean, default=True, nullable=False)
    final_report_deadline = Column(DateTime, nullable=True)
    final_report_submitted = Column(Boolean, default=False, nullable=False)
    final_report_submitted_at = Column(DateTime, nullable=True)
    final_report_content = Column(Text, nullable=True)
    # Overall status
    reporting_status = Column(String(50), nullable=False, default="not_started")
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    last_updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    incident = relationship("Incidents", foreign_keys=[incident_id])
    organisation = relationship("Organisations", foreign_keys=[organisation_id])


class LoginLogo(Base):
    __tablename__ = "login_logos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    logo = Column(Text, nullable=False)  # base64 data URL
    is_global = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    organisations = relationship("LoginLogoOrganisation", back_populates="logo", cascade="all, delete-orphan")


class LoginLogoOrganisation(Base):
    __tablename__ = "login_logo_organisations"

    logo_id = Column(UUID(as_uuid=True), ForeignKey("login_logos.id", ondelete="CASCADE"), primary_key=True)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=func.now())

    logo = relationship("LoginLogo", back_populates="organisations")
    organisation = relationship("Organisations")


# ═══════════════════════════════════════════════════════════════════════════════
# CTI (Cyber Threat Intelligence) Models
# Used by the cti-service microservice for storing scanner results and threat feeds
# ═══════════════════════════════════════════════════════════════════════════════

class CtiIndicator(Base):
    __tablename__ = "cti_indicators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(50), nullable=False, index=True)
    confidence = Column(Integer, default=0)
    pattern = Column(Text, nullable=True)
    labels = Column(Text, nullable=True)  # JSON array stored as text
    metadata_json = Column("metadata", Text, nullable=True)  # JSON object stored as text
    severity = Column(String(20), nullable=True, index=True)
    cwe_id = Column(String(20), nullable=True, index=True)
    owasp_category = Column(String(20), nullable=True)
    port = Column(Integer, nullable=True)
    protocol = Column(String(10), nullable=True)
    service_name = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)
    url = Column(Text, nullable=True)
    ecosystem = Column(String(50), nullable=True)
    package_name = Column(String(256), nullable=True)
    package_version = Column(String(100), nullable=True)
    vuln_id = Column(String(50), nullable=True)
    cvss_score = Column(Float, nullable=True)
    check_id = Column(String(256), nullable=True)
    file_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CtiAttackPattern(Base):
    __tablename__ = "cti_attack_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mitre_id = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(256), nullable=False)
    tactic = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CtiIndicatorAttackPattern(Base):
    __tablename__ = "cti_indicator_attack_patterns"

    indicator_id = Column(UUID(as_uuid=True), ForeignKey("cti_indicators.id", ondelete="CASCADE"), primary_key=True)
    attack_pattern_id = Column(UUID(as_uuid=True), ForeignKey("cti_attack_patterns.id", ondelete="CASCADE"), primary_key=True)
    source = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now())


class CtiSighting(Base):
    __tablename__ = "cti_sightings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    indicator_id = Column(UUID(as_uuid=True), ForeignKey("cti_indicators.id", ondelete="CASCADE"), nullable=True)
    source = Column(String(50), nullable=False, index=True)
    count = Column(Integer, default=1)
    severity = Column(String(20), nullable=True)
    category = Column(String(100), nullable=True)
    metadata_json = Column("metadata", Text, nullable=True)
    observed_at = Column(DateTime, default=func.now(), index=True)


class CtiMalware(Base):
    __tablename__ = "cti_malware"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(256), nullable=False)
    malware_type = Column(String(50), nullable=True)
    source = Column(String(50), nullable=True)
    metadata_json = Column("metadata", Text, nullable=True)
    created_at = Column(DateTime, default=func.now())


class CtiThreatFeed(Base):
    __tablename__ = "cti_threat_feeds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feed_name = Column(String(50), unique=True, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(String(20), nullable=True)
    record_count = Column(Integer, default=0)


class CtiKevEntry(Base):
    __tablename__ = "cti_kev_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cve_id = Column(String(20), unique=True, index=True, nullable=False)
    vendor = Column(String(256), nullable=True)
    product = Column(String(256), nullable=True)
    vulnerability_name = Column(String(512), nullable=True)
    date_added = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    known_ransomware = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)


# ==============================================================================
# API Key Management
# ==============================================================================

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    key_hash = Column(String(64), unique=True, index=True, nullable=False)
    key_prefix = Column(String(10), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scopes = Column(Text, nullable=True)  # JSON string
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    revoker = relationship("User", foreign_keys=[revoked_by])


# ==============================================================================
# Dark Web Scanning
# ==============================================================================

class DarkwebScan(Base):
    __tablename__ = "darkweb_scans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    keyword = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="queued", index=True)  # queued/processing/completed/failed
    engines = Column(Text, nullable=True)  # JSON list
    params = Column(Text, nullable=True)  # JSON dict
    result = Column(Text, nullable=True)  # JSON dict (full results including base64 PDF)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])


class DarkwebSettings(Base):
    __tablename__ = "darkweb_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    max_workers = Column(Integer, default=3, nullable=False)
    enabled_engines = Column(Text, nullable=True)  # JSON list
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# ==============================================================================
# Regulatory Change Monitor
# ==============================================================================

class FrameworkSnapshot(Base):
    __tablename__ = "framework_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id"), nullable=False)
    update_version = Column(Integer, nullable=False)
    snapshot_type = Column(String(20), nullable=False)  # pre_update, pre_revert
    snapshot_data = Column(Text, nullable=False)  # JSON: chapters, objectives, questions, framework_questions
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())


class RegulatorySource(Base):
    __tablename__ = "regulatory_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_type = Column(String(100), nullable=False)  # cra, nis2_directive, iso_27001_2022, etc.
    source_name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)  # searxng, eurlex_api, nist_api, direct_scrape, rss
    search_query = Column(Text, nullable=True)  # Search query template
    domain_filter = Column(Text, nullable=True)  # JSON array of allowed domains
    direct_url = Column(Text, nullable=True)  # Direct URL for scraping/API
    priority = Column(Integer, default=1)  # Lower = higher priority
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class RegulatoryMonitorSettings(Base):
    __tablename__ = "regulatory_monitor_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_frequency = Column(String(20), nullable=False, default="weekly")  # daily, weekly, biweekly
    scan_day_of_week = Column(String(10), nullable=True, default="mon")  # mon, tue, etc.
    scan_hour = Column(Integer, default=4)
    searxng_url = Column(String(500), default="http://searxng:8080")
    enabled = Column(Boolean, default=True, nullable=False)
    last_scan_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class RegulatoryScanRun(Base):
    __tablename__ = "regulatory_scan_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), nullable=False, default="running")  # running, completed, failed
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime, nullable=True)
    frameworks_scanned = Column(Integer, default=0)
    changes_found = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    raw_log = Column(Text, nullable=True)  # JSON log entries
    created_at = Column(DateTime, default=func.now())


class RegulatoryScanResult(Base):
    __tablename__ = "regulatory_scan_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id = Column(UUID(as_uuid=True), ForeignKey("regulatory_scan_runs.id"), nullable=False)
    framework_type = Column(String(100), nullable=False)
    source_name = Column(String(255), nullable=False)
    source_url = Column(Text, nullable=True)
    raw_content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True)  # SHA256 for dedup across runs
    fetched_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())


class RegulatoryChange(Base):
    __tablename__ = "regulatory_changes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id = Column(UUID(as_uuid=True), ForeignKey("regulatory_scan_runs.id"), nullable=False)
    framework_type = Column(String(100), nullable=False)
    change_type = Column(String(50), nullable=False)  # new_chapter, new_objective, update_objective, new_question, update_question, remove_objective
    entity_identifier = Column(String(255), nullable=True)  # e.g. subchapter "3.2.7"
    current_value = Column(Text, nullable=True)  # JSON of current state
    proposed_value = Column(Text, nullable=True)  # JSON of proposed state
    source_url = Column(Text, nullable=True)
    source_excerpt = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)  # 0.0 - 1.0
    llm_reasoning = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected, applied
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ComplianceCertificate(Base):
    __tablename__ = "compliance_certificates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    certificate_number = Column(String(50), unique=True, nullable=False)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("frameworks.id"), nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    issued_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    overall_score = Column(Float, nullable=False)
    objectives_compliant_pct = Column(Float, nullable=False)
    assessments_completed_pct = Column(Float, nullable=False)
    policies_approved_pct = Column(Float, nullable=False)
    issued_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(Text, nullable=True)
    verification_hash = Column(String(64), unique=True, nullable=False)
    pdf_data = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class CertificateSubmission(Base):
    __tablename__ = "certificate_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    certificate_id = Column(UUID(as_uuid=True), ForeignKey("compliance_certificates.id"), nullable=False)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    submitted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    authority_name = Column(String(255), nullable=False)  # e.g. "ENISA", "National CSIRT", custom
    recipient_emails = Column(Text, nullable=False)  # JSON array of email addresses
    submission_method = Column(String(50), nullable=False, default="email")  # email, portal
    status = Column(String(50), nullable=False, default="draft")  # draft, sent, acknowledged, feedback_received
    subject = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    feedback_received_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SubmissionEmailConfig(Base):
    __tablename__ = "submission_email_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"), nullable=False)
    authority_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    is_default = Column(Boolean, default=False)  # True = system default, False = user-added
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
