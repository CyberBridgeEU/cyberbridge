# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid

# User schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role_id: str
    organisation_id: str
    status: str = "pending_approval"

class UserCreate(UserBase):
    password: str

class SimpleUserResponse(UserBase):
    id: uuid.UUID

class UserEmail(BaseModel):
    email: EmailStr

class UserStatusUpdate(BaseModel):
    status: str

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    role_id: str
    organisation_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class FullUserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role_id: uuid.UUID
    organisation_id: uuid.UUID
    status: str
    role_name: str
    organisation_name: str
    organisation_logo: Optional[str] = None
    organisation_domain: Optional[str] = None
    auth_provider: str = "local"
    # Profile fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    profile_picture: Optional[str] = None
    timezone: Optional[str] = "UTC"
    notification_preferences: Optional[dict] = None
    # Onboarding fields
    onboarding_completed: bool = False
    onboarding_skipped: bool = False


class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    timezone: Optional[str] = None
    notification_preferences: Optional[dict] = None


class ProfilePictureResponse(BaseModel):
    profile_picture: str
    message: str


class UserCreateInOrganisation(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    role_id: str
    organisation_id: str
    auth_provider: str = "local"

class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    role_id: str
    organisation_id: str

class UserVerificationRegistration(BaseModel):
    email: EmailStr
    password: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class SendInvitationRequest(BaseModel):
    email: EmailStr
    temporary_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForceChangePasswordRequest(BaseModel):
    new_password: str

class UserUpdateInOrganisation(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role_id: Optional[str] = None
    user_id: str

class OrganisationRequest(BaseModel):
    id: Optional[str] = None
    name: str
    domain: str
    logo: Optional[str] = None

class OrganisationResponse(BaseModel):
    id: uuid.UUID
    name: str
    domain: str
    logo: Optional[str] = None


class RoleResponse(BaseModel):
    id: uuid.UUID
    role_name: str


# Framework schemas
class FrameworkBase(BaseModel):
    name: str
    description: Optional[str] = None

class FrameworkCreate(FrameworkBase):
    force_create: Optional[bool] = False
    allowed_scope_types: Optional[List[str]] = None
    scope_selection_mode: Optional[str] = "optional"  # 'required', 'optional'

class FrameworkAndUser(BaseModel):
    framework_id: str
    user_id: str

class FrameworkUserAndAssessmentType(BaseModel):
    framework_id: str
    user_id: str
    assessment_type_id: str

class FrameworkResponse(FrameworkBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    organisation_domain: Optional[str] = None
    allowed_scope_types: Optional[List[str]] = None
    scope_selection_mode: Optional[str] = None

    class Config:
        orm_mode = True

# Question schemas
class QuestionBase(BaseModel):
    text: str
    description: Optional[str] = None
    mandatory: bool = False
    assessment_type_id: uuid.UUID

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class FrameworkIdsRequest(BaseModel):
    framework_ids: List[str]

class CloneFrameworksRequest(BaseModel):
    framework_ids: List[str]
    custom_name: Optional[str] = None
    target_organization_id: Optional[str] = None


class FrameworksQuestionsResponse(BaseModel):
    key: str
    framework_id: str
    question_id: str
    framework_name: str
    framework_description: str
    question_text: str
    is_question_mandatory: bool
    assessment_type: str


# Assessment schemas
class OnlyIdInStringFormat(BaseModel):
    id: str

class OnlyIdsInStringFormat(BaseModel):
    ids: List[str]

# Assessment Type schemas
class AssessmentTypeResponse(BaseModel):
    id: uuid.UUID
    type_name: str
    created_at: datetime

    class Config:
        orm_mode = True

class AssessmentBase(BaseModel):
    name: str
    framework_id: uuid.UUID
    user_id: uuid.UUID
    assessment_type_id: uuid.UUID

class AssessmentCreateRequest(BaseModel):
    name: str
    framework_id: str
    user_id: str
    assessment_type_id: str
    scope_name: Optional[str] = None  # 'Product', 'Organization', 'Other'
    scope_entity_id: Optional[str] = None  # UUID of the entity (optional for 'Other')

class AssessmentCreate(AssessmentBase):
    scope_id: Optional[uuid.UUID] = None
    scope_entity_id: Optional[uuid.UUID] = None

class AssessmentResponse(AssessmentBase):
    id: uuid.UUID
    name: str
    framework_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    scope_id: Optional[uuid.UUID] = None
    scope_entity_id: Optional[uuid.UUID] = None
    scope_name: Optional[str] = None  # Added dynamically in repository
    scope_display_name: Optional[str] = None  # Added dynamically in repository

    class Config:
        orm_mode = True


class AssessmentWithFrameworkResponse(AssessmentBase):
    """Assessment response with framework and assessment type information for overview"""
    id: uuid.UUID
    name: str
    framework_id: uuid.UUID
    user_id: uuid.UUID
    assessment_type_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    scope_id: Optional[uuid.UUID] = None
    scope_entity_id: Optional[uuid.UUID] = None
    scope_name: Optional[str] = None
    scope_display_name: Optional[str] = None
    framework_name: Optional[str] = None
    assessment_type_name: Optional[str] = None
    progress: Optional[int] = 0

    class Config:
        orm_mode = True


# Answer schemas
class AnswerBase(BaseModel):
    assessment_id: uuid.UUID
    question_id: uuid.UUID
    value: Optional[str] = None
    evidence_description: Optional[str] = None
    policy_id: Optional[uuid.UUID] = None

class AnswerCreate(AnswerBase):
    pass

class AnswerResponse(AnswerBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class UpdateAnswerRequest(BaseModel):
    answer_id: str
    answer_value: Optional[str] = None
    evidence_description: Optional[str] = None
    policy_id: Optional[str] = None

class AssessmentAnswersRequest(BaseModel):
    assessment_id: str

class EvidenceFileResponse(BaseModel):
    id: str
    name: str
    type: str
    size: int
    path: str


class AssessmentAnswersResponse(BaseModel):
    answer_id: uuid.UUID
    assessment_id: uuid.UUID
    question_id: uuid.UUID
    answer_value: Optional[str]
    evidence_description: Optional[str] = None
    question_text: str
    question_description: Optional[str]
    is_question_mandatory: bool
    framework_names: str
    files: List[EvidenceFileResponse] = []
    assessment_type: str
    policy_id: Optional[uuid.UUID] = None
    policy_title: Optional[str] = None
    is_correlated: bool = False

# Evidence schemas
class EvidenceBase(BaseModel):
    filename: str
    file_type: str
    file_size: int
    answer_id: uuid.UUID

class EvidenceCreate(EvidenceBase):
    filepath: str

class EvidenceResponse(EvidenceBase):
    id: uuid.UUID
    filepath: str
    uploaded_at: datetime

    class Config:
        orm_mode = True

# Architecture Diagram schemas
class ArchitectureDiagramResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    diagram_type: str
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    framework_ids: List[str] = []
    framework_names: List[str] = []
    risk_ids: List[str] = []
    owner: Optional[str] = None
    version: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    organisation_id: Optional[str] = None

# Evidence Library schemas
class EvidenceLibraryItemResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    evidence_type: str
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    framework_ids: List[str] = []
    framework_names: List[str] = []
    control_ids: List[str] = []
    control_names: List[str] = []
    owner: Optional[str] = None
    collected_date: Optional[str] = None
    valid_until: Optional[str] = None
    status: str
    collection_method: str
    audit_notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    organisation_id: Optional[str] = None

# Notification schemas
class NotificationBase(BaseModel):
    user_id: uuid.UUID
    message: str
    type: str
    related_id: Optional[str] = None

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: uuid.UUID
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True

class FrameworkQuestionsCreate(BaseModel):
    framework_ids: List[str]
    questions: List[QuestionBase]


# Chapter schemas
class ChapterBase(BaseModel):
    title: str
    framework_id: str

class ChapterCreate(ChapterBase):
    pass

class ChapterUpdate(ChapterBase):
    id: str

class ChapterResponse(BaseModel):
    id: uuid.UUID
    title: str
    framework_id: uuid.UUID  # Changed from str to uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Compliance Status schemas
class ComplianceStatusBase(BaseModel):
    status_name: str

class ComplianceStatusCreate(ComplianceStatusBase):
    pass

class ComplianceStatusResponse(BaseModel):
    id: uuid.UUID
    status_name: str

    class Config:
        orm_mode = True

# Objective schemas
class ObjectiveBase(BaseModel):
    title: str
    subchapter: Optional[str] = None
    chapter_id: str
    requirement_description: Optional[str] = None
    objective_utilities: Optional[str] = None
    compliance_status_id: Optional[str] = None

class ObjectiveCreate(ObjectiveBase):
    pass

class ObjectiveUpdate(ObjectiveBase):
    id: str

class ObjectiveResponse(BaseModel):
    id: uuid.UUID
    title: str
    subchapter: Optional[str] = None
    chapter_id: uuid.UUID  # Changed from str to uuid.UUID
    requirement_description: Optional[str] = None
    objective_utilities: Optional[str] = None
    compliance_status_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    # Additional fields for UI display
    compliance_status: Optional[str] = None
    chapter_name: Optional[str] = None
    # Scope fields
    scope_id: Optional[uuid.UUID] = None
    scope_entity_id: Optional[uuid.UUID] = None
    scope_name: Optional[str] = None  # Added dynamically (e.g., 'Product', 'Organization')
    scope_display_name: Optional[str] = None  # Added dynamically (e.g., product name, org name)
    # Evidence file fields
    evidence_filename: Optional[str] = None
    evidence_file_type: Optional[str] = None
    evidence_file_size: Optional[int] = None

    class Config:
        orm_mode = True

class ChecklistPolicyItem(BaseModel):
    id: str
    title: str
    status_id: str
    status: str

# Objectives Checklist schemas
class ObjectiveChecklistItem(BaseModel):
    id: uuid.UUID
    title: str
    subchapter: Optional[str] = None
    chapter_id: uuid.UUID
    requirement_description: Optional[str] = None
    objective_utilities: Optional[str] = None
    compliance_status_id: Optional[uuid.UUID] = None
    compliance_status: Optional[str] = None
    policies: Optional[List[ChecklistPolicyItem]] = None
    # Scope fields
    scope_id: Optional[uuid.UUID] = None
    scope_entity_id: Optional[uuid.UUID] = None
    scope_name: Optional[str] = None  # Added dynamically (e.g., 'Product', 'Organization')
    scope_display_name: Optional[str] = None  # Added dynamically (e.g., product name, org name)
    applicable_operators: Optional[str] = None  # JSON array e.g. '["Manufacturer"]'
    # Evidence file fields
    evidence_filename: Optional[str] = None
    evidence_file_type: Optional[str] = None
    evidence_file_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime

class ChapterWithObjectives(BaseModel):
    id: uuid.UUID
    title: str
    framework_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    objectives: List[ObjectiveChecklistItem]

# Economic Operator schemas
class EconomicOperatorBase(BaseModel):
    name: str

class EconomicOperatorCreate(EconomicOperatorBase):
    pass

class EconomicOperatorResponse(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        orm_mode = True

# Asset Category schemas (formerly Product Type)
class AssetCategoryBase(BaseModel):
    name: str

class AssetCategoryCreate(AssetCategoryBase):
    pass

class AssetCategoryResponse(BaseModel):
    id: uuid.UUID
    name: str

    class Config:
        orm_mode = True

# Criticality Option schemas
class CriticalityOptionBase(BaseModel):
    value: str

class CriticalityOptionCreate(CriticalityOptionBase):
    criticality_id: str

class CriticalityOptionResponse(BaseModel):
    id: uuid.UUID
    criticality_id: uuid.UUID
    value: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Criticality schemas
class CriticalityBase(BaseModel):
    label: str

class CriticalityCreate(CriticalityBase):
    pass

class CriticalityResponse(BaseModel):
    id: uuid.UUID
    label: str
    options: List[CriticalityOptionResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Risk schemas
class RiskBase(BaseModel):
    asset_category_id: str
    risk_code: Optional[str] = None
    risk_category_name: str
    risk_category_description: Optional[str] = None
    risk_potential_impact: Optional[str] = None
    risk_control: Optional[str] = None
    likelihood: str
    residual_risk: str
    risk_severity_id: str
    risk_status_id: str
    assessment_status: Optional[str] = None

class RiskCreate(RiskBase):
    scope_name: Optional[str] = None  # 'Product', 'Organization', 'Other'
    scope_entity_id: Optional[str] = None  # UUID of the entity (optional for 'Other')

class RiskUpdate(RiskBase):
    id: str
    scope_name: Optional[str] = None
    scope_entity_id: Optional[str] = None

class RiskResponse(BaseModel):
    id: uuid.UUID
    asset_category_id: Optional[uuid.UUID] = None
    risk_code: Optional[str] = None
    risk_category_name: str
    risk_category_description: Optional[str] = None
    risk_potential_impact: Optional[str] = None
    risk_control: Optional[str] = None
    likelihood: uuid.UUID
    residual_risk: uuid.UUID
    risk_severity_id: uuid.UUID
    risk_status_id: uuid.UUID
    assessment_status: Optional[str] = None
    organisation_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    # Scope fields
    scope_id: Optional[uuid.UUID] = None
    scope_entity_id: Optional[uuid.UUID] = None
    scope_name: Optional[str] = None  # Added dynamically in repository
    scope_display_name: Optional[str] = None  # Added dynamically in repository
    # Additional fields for UI display
    asset_category: Optional[str] = None
    risk_severity: Optional[str] = None
    risk_status: Optional[str] = None
    organisation_name: Optional[str] = None
    last_updated_by_email: Optional[str] = None
    linked_findings_count: Optional[int] = 0

    class Config:
        orm_mode = True


# Scan Finding schemas
class ScanFindingResponse(BaseModel):
    id: str
    scan_history_id: str
    scanner_type: str
    title: str
    severity: Optional[str] = None
    normalized_severity: Optional[str] = None
    identifier: Optional[str] = None
    description: Optional[str] = None
    solution: Optional[str] = None
    url_or_target: Optional[str] = None
    is_auto_mapped: Optional[bool] = None
    scan_target: Optional[str] = None
    scan_timestamp: Optional[str] = None
    created_at: Optional[str] = None


class ScanFindingRiskResponse(BaseModel):
    id: str
    risk_code: Optional[str] = None
    risk_category_name: str


class ScanFindingWithCVE(BaseModel):
    id: str
    scan_history_id: str
    scanner_type: str
    title: str
    severity: Optional[str] = None
    normalized_severity: Optional[str] = None
    identifier: Optional[str] = None
    description: Optional[str] = None
    solution: Optional[str] = None
    url_or_target: Optional[str] = None
    extra_data: Optional[str] = None
    cve_description: Optional[str] = None
    cvss_v31_score: Optional[float] = None
    cvss_v31_severity: Optional[str] = None
    cve_published: Optional[str] = None
    linked_risks_count: int = 0
    scan_target: Optional[str] = None
    scan_timestamp: Optional[str] = None
    created_at: Optional[str] = None


class ScanFindingsListResponse(BaseModel):
    findings: list[ScanFindingWithCVE]
    total: int
    offset: int
    limit: int


class ScanFindingsStatsResponse(BaseModel):
    total: int
    by_scanner: dict
    by_severity: dict
    linked_to_risks: int


# Risk Category schemas
class RiskCategoryBase(BaseModel):
    asset_category_id: str
    risk_category_name: str
    risk_category_description: Optional[str] = None
    risk_potential_impact: Optional[str] = None
    risk_control: Optional[str] = None

class RiskCategoryCreate(RiskCategoryBase):
    pass

class RiskCategoryResponse(BaseModel):
    id: uuid.UUID
    asset_category_id: uuid.UUID
    risk_category_name: str
    risk_category_description: Optional[str] = None
    risk_potential_impact: Optional[str] = None
    risk_control: Optional[str] = None

    class Config:
        orm_mode = True

# Risk Severity schemas
class RiskSeverityBase(BaseModel):
    risk_severity_name: str

class RiskSeverityCreate(RiskSeverityBase):
    pass

class RiskSeverityResponse(BaseModel):
    id: uuid.UUID
    risk_severity_name: str

    class Config:
        orm_mode = True

# Risk Status schemas
class RiskStatusBase(BaseModel):
    risk_status_name: str

class RiskStatusCreate(RiskStatusBase):
    pass

class RiskStatusResponse(BaseModel):
    id: uuid.UUID
    risk_status_name: str

    class Config:
        orm_mode = True

# Control schemas
class ControlSetBase(BaseModel):
    name: str
    description: Optional[str] = None

class ControlSetCreate(ControlSetBase):
    pass

class ControlSetResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    organisation_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class ControlStatusBase(BaseModel):
    status_name: str

class ControlStatusCreate(ControlStatusBase):
    pass

class ControlStatusResponse(BaseModel):
    id: uuid.UUID
    status_name: str

    class Config:
        orm_mode = True

class ControlBase(BaseModel):
    code: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    owner: Optional[str] = None
    control_set_id: str
    control_status_id: str

class ControlCreate(ControlBase):
    pass

class ControlUpdate(ControlBase):
    id: str

class ControlResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    owner: Optional[str] = None
    control_set_id: uuid.UUID
    control_status_id: uuid.UUID
    organisation_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    # Additional fields for UI display
    control_set_name: Optional[str] = None
    control_status_name: Optional[str] = None
    organisation_name: Optional[str] = None
    last_updated_by_email: Optional[str] = None
    linked_risks_count: Optional[int] = 0
    linked_policies_count: Optional[int] = 0

    class Config:
        orm_mode = True

class ControlImportItem(BaseModel):
    """Individual control to import from Excel"""
    code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None

class ControlImportRequest(BaseModel):
    """Request to import controls from Excel"""
    control_set_name: str
    controls: List[ControlImportItem]
    default_status: str  # UUID of control status

class ControlImportResponse(BaseModel):
    """Response after importing controls"""
    success: bool
    imported_count: int
    failed_count: int
    message: str
    imported_control_ids: List[str] = []
    errors: List[str] = []

# Control Template schemas
class ControlSetTemplateInfo(BaseModel):
    """Summary information about a control set template"""
    name: str
    description: str
    control_count: int

class ControlTemplateItem(BaseModel):
    """A single control in a template"""
    code: str
    name: str
    description: Optional[str] = None

class ControlSetTemplateDetail(BaseModel):
    """Detailed control set template with all controls"""
    name: str
    description: str
    controls: List[ControlTemplateItem]

class ControlTemplateImportRequest(BaseModel):
    """Request to import controls from a pre-loaded template"""
    template_name: str

# Policy schemas
class PolicyBase(BaseModel):
    title: str
    policy_code: Optional[str] = None
    owner: Optional[str] = None
    status_id: str
    body: Optional[str] = None

class PolicyCreate(PolicyBase):
    framework_ids: Optional[List[str]] = None
    objective_ids: Optional[List[dict]] = None
    company_name: Optional[str] = None

class PolicyUpdate(PolicyBase):
    id: str
    framework_ids: Optional[List[str]] = None
    objective_ids: Optional[List[dict]] = None
    company_name: Optional[str] = None

class PolicyResponse(BaseModel):
    id: uuid.UUID
    title: str
    policy_code: Optional[str] = None
    owner: Optional[str] = None
    status_id: uuid.UUID
    body: Optional[str] = None
    company_name: Optional[str] = None
    organisation_id: Optional[uuid.UUID] = None
    created_at: datetime
    # Additional fields for UI display
    status: Optional[str] = None
    organisation_name: Optional[str] = None
    frameworks: Optional[List[str]] = None
    objectives: Optional[List[str]] = None
    chapters: Optional[List[str]] = None
    last_updated_by_email: Optional[str] = None

    class Config:
        orm_mode = True

# Policy Template schemas
class PolicyTemplateResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    policy_code: Optional[str] = None
    filename: str
    file_size: Optional[int] = None
    source: Optional[str] = None

    class Config:
        orm_mode = True


class PolicyTemplateImportRequest(BaseModel):
    template_ids: List[str]


class PolicyTemplateImportResponse(BaseModel):
    success: bool
    imported_count: int
    skipped_count: int
    message: str
    imported_policy_codes: List[str] = []
    errors: List[str] = []


# Policy Status schemas
class PolicyStatusBase(BaseModel):
    status: str

class PolicyStatusCreate(PolicyStatusBase):
    pass

class PolicyStatusResponse(BaseModel):
    id: uuid.UUID
    status: str

    class Config:
        orm_mode = True

class PolicyStatusPatch(BaseModel):
    status_id: str

# Policy Framework relationship schemas
class PolicyFrameworkBase(BaseModel):
    policy_id: str
    framework_id: str

class PolicyFrameworkCreate(PolicyFrameworkBase):
    pass

class PolicyFrameworkResponse(BaseModel):
    policy_id: uuid.UUID
    framework_id: uuid.UUID

    class Config:
        orm_mode = True

# Policy Objective relationship schemas
class PolicyObjectiveBase(BaseModel):
    policy_id: str
    objective_id: str
    order: int

class PolicyObjectiveCreate(PolicyObjectiveBase):
    pass

class PolicyObjectiveResponse(BaseModel):
    policy_id: uuid.UUID
    objective_id: uuid.UUID
    order: int

    class Config:
        orm_mode = True


# Scanner History schemas
class ScannerHistoryBase(BaseModel):
    scanner_type: str  # 'zap', 'nmap', 'semgrep', 'osv'
    scan_target: str
    scan_type: Optional[str] = None
    scan_config: Optional[str] = None
    results: str  # JSON string
    summary: Optional[str] = None
    status: str = "completed"
    error_message: Optional[str] = None
    scan_duration: Optional[float] = None


class ScannerHistoryCreate(ScannerHistoryBase):
    user_id: str
    user_email: str
    organisation_id: Optional[str] = None
    organisation_name: Optional[str] = None


class ScannerHistoryResponse(BaseModel):
    id: uuid.UUID
    scanner_type: str
    user_id: uuid.UUID
    user_email: str
    organisation_id: Optional[uuid.UUID] = None
    organisation_name: Optional[str] = None
    scan_target: str
    scan_type: Optional[str] = None
    scan_config: Optional[str] = None
    results: str  # JSON string
    summary: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    scan_duration: Optional[float] = None
    timestamp: datetime
    created_at: datetime
    updated_at: datetime
    asset_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class ScannerHistoryListResponse(BaseModel):
    """Lightweight response for listing scanner history (excludes full results)"""
    id: uuid.UUID
    scanner_type: str
    user_id: uuid.UUID
    user_email: str
    organisation_id: Optional[uuid.UUID] = None
    organisation_name: Optional[str] = None
    scan_target: str
    scan_type: Optional[str] = None
    scan_config: Optional[str] = None
    summary: Optional[str] = None
    max_severity: Optional[str] = None  # Computed from results: High, Medium, Low, Info, or N/A
    status: str
    error_message: Optional[str] = None
    scan_duration: Optional[float] = None
    timestamp: datetime
    asset_id: Optional[uuid.UUID] = None
    asset_name: Optional[str] = None

    class Config:
        from_attributes = True


class ScannerHistoryAssetAssign(BaseModel):
    asset_id: Optional[uuid.UUID] = None


# Scope schemas
class ScopeInfo(BaseModel):
    """Information about assessment/risk scope"""
    scope_name: str  # 'Product', 'Organization', 'Other'
    scope_id: uuid.UUID
    scope_entity_id: Optional[uuid.UUID]
    entity_name: Optional[str]  # Display name


class FrameworkScopeConfig(BaseModel):
    """Framework scope configuration"""
    allowed_scope_types: List[str]
    scope_selection_mode: str  # 'required', 'optional'
    supported_scope_types: List[str]  # Currently available in system


class ScopeTypeResponse(BaseModel):
    """Available scope type"""
    id: uuid.UUID
    scope_name: str
    created_at: datetime

    class Config:
        orm_mode = True


# AI Feature Settings schemas
class AIFeatureSettingsRequest(BaseModel):
    """Request to update AI feature settings for an organization"""
    ai_remediator_enabled: Optional[bool] = None
    remediator_prompt_zap: Optional[str] = None  # Custom ZAP remediation prompt (null for default)
    remediator_prompt_nmap: Optional[str] = None  # Custom Nmap remediation prompt (null for default)
    # AI Policy Aligner settings
    ai_policy_aligner_enabled: Optional[bool] = None
    policy_aligner_prompt: Optional[str] = None  # Custom policy alignment prompt (null for default)


class AIFeatureSettingsResponse(BaseModel):
    """Response containing AI feature settings"""
    ai_remediator_enabled: bool
    remediator_prompt_zap: Optional[str] = None
    remediator_prompt_nmap: Optional[str] = None
    default_prompt_zap: str  # Always include default prompts for reference
    default_prompt_nmap: str
    # AI Policy Aligner settings
    ai_policy_aligner_enabled: bool = False
    policy_aligner_prompt: Optional[str] = None
    default_policy_aligner_prompt: str = ""  # Default prompt for policy alignment


# AI Policy Aligner schemas
class PolicyAlignmentRequest(BaseModel):
    """Request to trigger AI policy alignment for a framework"""
    framework_id: uuid.UUID


class PolicyAlignmentResponse(BaseModel):
    """Response containing a single policy-question alignment"""
    question_id: uuid.UUID
    question_text: str
    policy_id: uuid.UUID
    policy_title: str
    confidence_score: int
    reasoning: Optional[str] = None


class AlignmentStatusResponse(BaseModel):
    """Response containing the status of policy alignments for a framework"""
    has_alignments: bool
    alignment_count: int
    last_updated: Optional[datetime] = None


class AlignmentGenerationResponse(BaseModel):
    """Response from triggering AI alignment generation"""
    success: bool
    alignments_created: int
    error: Optional[str] = None


# AI Remediation schemas
class RemediationRequest(BaseModel):
    """Request for AI remediation guidance"""
    scanner_type: str  # 'zap' or 'nmap'
    history_id: str  # UUID of scanner history record


class RemediationResponse(BaseModel):
    """Response with AI remediation guidance"""
    success: bool
    scanner_type: str
    history_id: str
    remediation: Optional[str] = None  # The AI-generated remediation guidance
    error: Optional[str] = None  # Error message if failed
    scan_target: Optional[str] = None  # Original scan target for context


# Backup Configuration schemas
class BackupConfigBase(BaseModel):
    """Backup configuration for an organization"""
    backup_enabled: bool = True
    backup_frequency: str = "monthly"  # daily, weekly, monthly
    backup_retention_years: int = 10


class BackupConfigResponse(BackupConfigBase):
    """Response with backup configuration and status"""
    last_backup_at: Optional[datetime] = None
    last_backup_status: Optional[str] = None


class BackupConfigUpdate(BaseModel):
    """Request to update backup configuration"""
    backup_enabled: Optional[bool] = None
    backup_frequency: Optional[str] = None  # daily, weekly, monthly
    backup_retention_years: Optional[int] = None


# Backup Record schemas
class BackupBase(BaseModel):
    """Base backup record information"""
    filename: str
    file_size: int
    backup_type: str  # scheduled, manual
    status: str  # completed, failed, in_progress
    is_encrypted: bool = True


class BackupResponse(BackupBase):
    """Response for a backup record"""
    id: uuid.UUID
    organisation_id: uuid.UUID
    filepath: str
    error_message: Optional[str] = None
    records_count: Optional[str] = None  # JSON string
    evidence_files_count: Optional[int] = None
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class BackupListResponse(BaseModel):
    """Response for list of backups"""
    backups: List[BackupResponse]
    total_count: int


class BackupCreateRequest(BaseModel):
    """Request to create a manual backup"""
    pass  # No additional fields needed - org_id comes from path


class BackupRestoreRequest(BaseModel):
    """Request to restore from a backup"""
    backup_id: str
    confirm: bool = False  # Must be True to proceed with restore


class BackupRestoreResponse(BaseModel):
    """Response from a backup restore operation"""
    success: bool
    message: str
    records_restored: Optional[dict] = None
    evidence_files_restored: Optional[int] = None
    error: Optional[str] = None


# ===========================
# Audit Engagement Workspace Schemas
# ===========================

# Auditor Role schemas
class AuditorRoleBase(BaseModel):
    role_name: str
    can_comment: bool = True
    can_request_evidence: bool = True
    can_add_findings: bool = False
    can_sign_off: bool = False


class AuditorRoleResponse(AuditorRoleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Audit Engagement schemas
class AuditEngagementBase(BaseModel):
    name: str
    description: Optional[str] = None
    audit_period_start: Optional[datetime] = None
    audit_period_end: Optional[datetime] = None
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    in_scope_controls: Optional[List[str]] = None
    in_scope_policies: Optional[List[str]] = None
    in_scope_chapters: Optional[List[str]] = None


class AuditEngagementCreateRequest(AuditEngagementBase):
    assessment_id: str
    prior_engagement_id: Optional[str] = None


class AuditEngagementUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    audit_period_start: Optional[datetime] = None
    audit_period_end: Optional[datetime] = None
    planned_start_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    in_scope_controls: Optional[List[str]] = None
    in_scope_policies: Optional[List[str]] = None
    in_scope_chapters: Optional[List[str]] = None
    prior_engagement_id: Optional[str] = None


class AuditEngagementStatusUpdate(BaseModel):
    status: str  # draft, planned, in_progress, review, completed, closed


class AuditEngagementResponse(AuditEngagementBase):
    id: uuid.UUID
    assessment_id: uuid.UUID
    status: str
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    owner_id: uuid.UUID
    organisation_id: uuid.UUID
    prior_engagement_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    # Enriched fields
    assessment_name: Optional[str] = None
    framework_name: Optional[str] = None
    framework_id: Optional[uuid.UUID] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    organisation_name: Optional[str] = None
    invitation_count: Optional[int] = 0
    active_invitation_count: Optional[int] = 0

    class Config:
        from_attributes = True


class AuditEngagementListResponse(BaseModel):
    engagements: List[AuditEngagementResponse]
    total_count: int


# Auditor Invitation schemas
class AuditorInvitationBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    company: Optional[str] = None
    access_start: Optional[datetime] = None
    access_end: Optional[datetime] = None
    mfa_enabled: bool = False
    ip_allowlist: Optional[List[str]] = None
    download_restricted: bool = False
    watermark_downloads: bool = True


class AuditorInvitationCreateRequest(AuditorInvitationBase):
    auditor_role_id: str


class AuditorInvitationUpdateRequest(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    auditor_role_id: Optional[str] = None
    access_start: Optional[datetime] = None
    access_end: Optional[datetime] = None
    mfa_enabled: Optional[bool] = None
    ip_allowlist: Optional[List[str]] = None
    download_restricted: Optional[bool] = None
    watermark_downloads: Optional[bool] = None


class AuditorInvitationResponse(AuditorInvitationBase):
    id: uuid.UUID
    engagement_id: uuid.UUID
    auditor_role_id: uuid.UUID
    status: str
    invited_by: uuid.UUID
    accepted_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    token_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # Enriched fields
    role_name: Optional[str] = None
    can_comment: Optional[bool] = None
    can_request_evidence: Optional[bool] = None
    can_add_findings: Optional[bool] = None
    can_sign_off: Optional[bool] = None
    engagement_name: Optional[str] = None
    engagement_status: Optional[str] = None
    invited_by_name: Optional[str] = None
    invited_by_email: Optional[str] = None
    token_expired: Optional[bool] = False
    within_access_window: Optional[bool] = True

    class Config:
        from_attributes = True


class AuditorInvitationWithTokenResponse(AuditorInvitationResponse):
    """Response that includes the access token (only for creation/regeneration)"""
    access_token: str


class AuditorInvitationListResponse(BaseModel):
    invitations: List[AuditorInvitationResponse]
    total_count: int


# ===========================
# Audit Comment schemas
# ===========================

class AuditCommentBase(BaseModel):
    target_type: str  # answer, evidence, objective, policy
    target_id: uuid.UUID
    content: str
    comment_type: str = "observation"  # question, evidence_request, observation, potential_exception


class AuditCommentCreateRequest(AuditCommentBase):
    parent_comment_id: Optional[uuid.UUID] = None
    assigned_to_id: Optional[uuid.UUID] = None
    assigned_to_auditor_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None


class AuditCommentUpdateRequest(BaseModel):
    content: Optional[str] = None
    comment_type: Optional[str] = None
    assigned_to_id: Optional[uuid.UUID] = None
    assigned_to_auditor_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None


class AuditCommentResolveRequest(BaseModel):
    resolution_note: Optional[str] = None


class AuditCommentResponse(BaseModel):
    id: uuid.UUID
    engagement_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    content: str
    comment_type: str
    status: str
    parent_comment_id: Optional[uuid.UUID] = None
    assigned_to_id: Optional[uuid.UUID] = None
    assigned_to_auditor_id: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by_id: Optional[uuid.UUID] = None
    resolved_by_auditor_id: Optional[uuid.UUID] = None
    resolution_note: Optional[str] = None
    author_user_id: Optional[uuid.UUID] = None
    author_auditor_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    # Enriched fields
    author_name: Optional[str] = None
    author_type: Optional[str] = None  # user, auditor
    assigned_to_name: Optional[str] = None
    resolved_by_name: Optional[str] = None
    reply_count: int = 0
    attachment_count: int = 0

    class Config:
        from_attributes = True


class AuditCommentWithRepliesResponse(AuditCommentResponse):
    replies: List[AuditCommentResponse] = []


class AuditCommentListResponse(BaseModel):
    comments: List[AuditCommentWithRepliesResponse]
    total_count: int


# Audit Comment Attachment schemas
class AuditCommentAttachmentResponse(BaseModel):
    id: uuid.UUID
    comment_id: uuid.UUID
    filename: str
    filepath: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_by_user_id: Optional[uuid.UUID] = None
    uploaded_by_auditor_id: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ===========================
# Audit Finding schemas
# ===========================

class AuditFindingBase(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "medium"  # low, medium, high, critical
    category: str  # control_deficiency, documentation_gap, compliance_issue, process_weakness


class AuditFindingCreateRequest(AuditFindingBase):
    related_controls: Optional[List[str]] = None
    related_evidence: Optional[List[str]] = None
    remediation_plan: Optional[str] = None
    remediation_owner_id: Optional[uuid.UUID] = None
    remediation_due_date: Optional[datetime] = None


class AuditFindingUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    related_controls: Optional[List[str]] = None
    related_evidence: Optional[List[str]] = None
    remediation_plan: Optional[str] = None
    remediation_owner_id: Optional[uuid.UUID] = None
    remediation_due_date: Optional[datetime] = None


class AuditFindingStatusUpdate(BaseModel):
    status: str  # draft, confirmed, remediation_in_progress, remediated, accepted, closed


class AuditFindingResponse(BaseModel):
    id: uuid.UUID
    engagement_id: uuid.UUID
    title: str
    description: Optional[str] = None
    severity: str
    category: str
    related_controls: Optional[List[str]] = None
    related_evidence: Optional[List[str]] = None
    remediation_plan: Optional[str] = None
    remediation_owner_id: Optional[uuid.UUID] = None
    remediation_due_date: Optional[datetime] = None
    status: str
    author_user_id: Optional[uuid.UUID] = None
    author_auditor_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    # Enriched fields
    author_name: Optional[str] = None
    remediation_owner_name: Optional[str] = None

    class Config:
        from_attributes = True


class AuditFindingListResponse(BaseModel):
    findings: List[AuditFindingResponse]
    total_count: int


# ===========================
# Audit Sign-Off schemas
# ===========================

class AuditSignOffCreateRequest(BaseModel):
    sign_off_type: str  # control, section, engagement
    target_id: Optional[uuid.UUID] = None  # NULL for engagement-level
    status: str  # approved, approved_with_exceptions, rejected
    comments: Optional[str] = None


class AuditSignOffResponse(BaseModel):
    id: uuid.UUID
    engagement_id: uuid.UUID
    sign_off_type: str
    target_id: Optional[uuid.UUID] = None
    status: str
    comments: Optional[str] = None
    signer_auditor_id: uuid.UUID
    signed_at: datetime
    ip_address: Optional[str] = None
    created_at: datetime
    # Enriched fields
    signer_name: Optional[str] = None
    signer_email: Optional[str] = None

    class Config:
        from_attributes = True


class AuditSignOffListResponse(BaseModel):
    sign_offs: List[AuditSignOffResponse]
    total_count: int


# ===========================
# Audit Activity Log schemas
# ===========================

class AuditActivityLogResponse(BaseModel):
    id: uuid.UUID
    engagement_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    auditor_id: Optional[uuid.UUID] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[uuid.UUID] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime
    # Enriched fields
    actor_name: Optional[str] = None
    actor_type: Optional[str] = None  # user, auditor

    class Config:
        from_attributes = True


class AuditActivityLogListResponse(BaseModel):
    logs: List[AuditActivityLogResponse]
    total_count: int


# ===========================
# Evidence Integrity schemas
# ===========================

class EvidenceIntegrityResponse(BaseModel):
    id: uuid.UUID
    evidence_id: uuid.UUID
    version: int
    sha256_hash: str
    md5_hash: Optional[str] = None
    file_size: int
    original_filename: str
    uploaded_by_id: Optional[uuid.UUID] = None
    uploaded_by_name: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    last_verified_at: Optional[datetime] = None
    verification_status: Optional[str] = None
    previous_version_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class EvidenceIntegrityVerificationResponse(BaseModel):
    status: str
    message: str
    verified: bool
    sha256_hash: Optional[str] = None
    file_size: Optional[int] = None
    expected_sha256: Optional[str] = None
    actual_sha256: Optional[str] = None
    expected_size: Optional[int] = None
    actual_size: Optional[int] = None


class EvidenceVersionHistoryResponse(BaseModel):
    versions: List[EvidenceIntegrityResponse]
    current_version: int
    total_versions: int


# ===========================
# NVD Vulnerability Sync Schemas
# ===========================

class NVDSettingsBase(BaseModel):
    """Base NVD settings"""
    api_key: Optional[str] = None
    sync_enabled: bool = True
    sync_hour: int = 3  # Hour of day (0-23)
    sync_minute: int = 0


class NVDSettingsUpdate(BaseModel):
    """Request to update NVD settings"""
    api_key: Optional[str] = None
    sync_enabled: Optional[bool] = None
    sync_hour: Optional[int] = None
    sync_minute: Optional[int] = None


class NVDSettingsResponse(NVDSettingsBase):
    """Response containing NVD settings"""
    id: uuid.UUID
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    # Mask API key for security
    has_api_key: bool = False

    class Config:
        from_attributes = True


class NVDSyncTriggerRequest(BaseModel):
    """Request to trigger a manual sync"""
    full_sync: bool = False  # If True, fetch all CVEs; otherwise incremental


class NVDSyncStatusResponse(BaseModel):
    """Response for sync status"""
    id: uuid.UUID
    status: str  # pending, in_progress, completed, failed
    sync_type: str  # full, incremental
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cves_processed: int = 0
    cves_added: int = 0
    cves_updated: int = 0
    error_message: Optional[str] = None
    triggered_by: Optional[uuid.UUID] = None
    triggered_by_email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NVDSyncHistoryResponse(BaseModel):
    """Response for sync history"""
    syncs: List[NVDSyncStatusResponse]
    total_count: int


class CVEBase(BaseModel):
    """Base CVE information"""
    cve_id: str
    description: Optional[str] = None
    cvss_v3_score: Optional[float] = None
    cvss_v3_severity: Optional[str] = None
    cvss_v3_vector: Optional[str] = None
    cvss_v2_score: Optional[float] = None
    cvss_v2_severity: Optional[str] = None
    published_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    vuln_status: Optional[str] = None


class CVEResponse(CVEBase):
    """Full CVE response"""
    id: uuid.UUID
    references: Optional[List[dict]] = None
    cwe_ids: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CVEListResponse(BaseModel):
    """Response for CVE list"""
    cves: List[CVEResponse]
    total_count: int


class CVESearchRequest(BaseModel):
    """Request for CVE search"""
    search: Optional[str] = None
    severity: Optional[str] = None  # CRITICAL, HIGH, MEDIUM, LOW
    skip: int = 0
    limit: int = 100


class NVDStatisticsResponse(BaseModel):
    """Response for NVD database statistics"""
    total_cves: int
    severity_breakdown: dict  # {"CRITICAL": 100, "HIGH": 500, ...}
    latest_cve_date: Optional[datetime] = None
    oldest_cve_date: Optional[datetime] = None
    cpe_match_count: int
    last_sync_at: Optional[datetime] = None
    sync_enabled: bool = True


class ServiceVulnerabilityResponse(BaseModel):
    """Response for a single vulnerability correlation"""
    id: str
    host: str
    port: int
    protocol: Optional[str] = None
    service_name: Optional[str] = None
    service_product: Optional[str] = None
    service_version: Optional[str] = None
    generated_cpe: Optional[str] = None
    confidence: int
    match_type: Optional[str] = None
    # CVE details
    cve_id: str
    cve_description: Optional[str] = None
    cvss_v3_score: Optional[float] = None
    cvss_v3_severity: Optional[str] = None
    cvss_v3_vector: Optional[str] = None
    published_date: Optional[str] = None
    references: Optional[List[dict]] = None
    cwe_ids: Optional[List[str]] = None


class ScanVulnerabilitiesResponse(BaseModel):
    """Response for scan vulnerabilities"""
    scan_id: str
    scan_target: str
    scan_timestamp: Optional[datetime] = None
    vulnerabilities: List[ServiceVulnerabilityResponse]
    summary: dict  # total_vulnerabilities, severity_breakdown, unique_hosts_affected


class CorrelateRequest(BaseModel):
    """Request to correlate a scan (empty body, scan_id comes from path)"""
    pass


class CorrelateResponse(BaseModel):
    """Response from correlation"""
    success: bool
    scan_id: str
    vulnerabilities_found: int
    message: str


# ===========================
# Control Review Status schemas
# ===========================

class ControlReviewStatusResponse(BaseModel):
    """Response for control review status"""
    id: uuid.UUID
    engagement_id: uuid.UUID
    answer_id: uuid.UUID
    status: str
    status_note: Optional[str] = None
    last_updated_by_user_id: Optional[uuid.UUID] = None
    last_updated_by_auditor_id: Optional[uuid.UUID] = None
    last_updated_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ControlReviewStatusUpdateRequest(BaseModel):
    """Request to update control review status"""
    status: str
    status_note: Optional[str] = None


class ReviewStatusCountsResponse(BaseModel):
    """Response for review status counts"""
    not_started: int = 0
    pending_review: int = 0
    information_requested: int = 0
    response_provided: int = 0
    in_review: int = 0
    approved: int = 0
    approved_with_exceptions: int = 0
    needs_remediation: int = 0


# ===========================
# Audit Notification schemas
# ===========================

class AuditNotificationResponse(BaseModel):
    """Response for a single notification"""
    id: uuid.UUID
    engagement_id: uuid.UUID
    notification_type: str
    source_type: str
    source_id: uuid.UUID
    related_answer_id: Optional[uuid.UUID] = None
    title: str
    message: Optional[str] = None
    sender_user_id: Optional[uuid.UUID] = None
    sender_auditor_id: Optional[uuid.UUID] = None
    sender_name: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditNotificationListResponse(BaseModel):
    """Response for notification list"""
    notifications: List[AuditNotificationResponse]
    unread_count: int
    total_count: int


class MarkNotificationsReadRequest(BaseModel):
    """Request to mark notifications as read"""
    notification_ids: Optional[List[uuid.UUID]] = None  # If None, mark all as read
    engagement_id: Optional[uuid.UUID] = None  # Optional filter by engagement


# ===========================
# Onboarding Wizard Schemas
# ===========================

class OnboardingStatusResponse(BaseModel):
    """Response for onboarding status check"""
    onboarding_completed: bool
    onboarding_skipped: bool
    onboarding_completed_at: Optional[datetime] = None
    is_admin: bool  # Whether the user is an admin who should see the wizard


class OnboardingCompleteRequest(BaseModel):
    """Request to mark onboarding as completed"""
    pass  # No additional fields needed


class OnboardingCompleteResponse(BaseModel):
    """Response after completing onboarding"""
    success: bool
    message: str
    onboarding_completed_at: Optional[datetime] = None


class OnboardingSkipRequest(BaseModel):
    """Request to skip onboarding"""
    pass  # No additional fields needed


class OnboardingSkipResponse(BaseModel):
    """Response after skipping onboarding"""
    success: bool
    message: str


# ===========================
# Nmap Vulnerability Schemas
# ===========================

class NmapVulnerability(BaseModel):
    """Individual vulnerability from Nmap scan"""
    id: str
    severity: str  # High, Medium, Low, Info
    title: str
    description: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    service_name: Optional[str] = None
    service_version: Optional[str] = None
    cpe: Optional[str] = None
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None
    references: Optional[List[dict]] = None
    cwe_ids: Optional[List[str]] = None


class NmapScanSummary(BaseModel):
    """Summary counts by severity level"""
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    total: int = 0


class NmapScanResponse(BaseModel):
    """Complete Nmap scan response with vulnerabilities"""
    success: bool
    vulnerabilities: List[NmapVulnerability]
    summary: NmapScanSummary
    raw_data: Optional[dict] = None
    analysis: Optional[str] = None  # For backward compatibility with history display


# ===========================
# Asset Management Schemas
# ===========================

# Asset Type schemas
class AssetTypeBase(BaseModel):
    name: str
    icon_name: Optional[str] = None
    description: Optional[str] = None
    default_confidentiality: Optional[str] = None
    default_integrity: Optional[str] = None
    default_availability: Optional[str] = None
    default_asset_value: Optional[str] = None


class AssetTypeCreate(AssetTypeBase):
    pass


class AssetTypeUpdate(AssetTypeBase):
    pass


class AssetTypeResponse(BaseModel):
    id: uuid.UUID
    name: str
    icon_name: Optional[str] = None
    description: Optional[str] = None
    default_confidentiality: Optional[str] = None
    default_integrity: Optional[str] = None
    default_availability: Optional[str] = None
    default_asset_value: Optional[str] = None
    organisation_id: uuid.UUID
    asset_count: int = 0
    risk_count: int = 0
    risk_level: str = "Low"  # Low, Medium, Severe
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssetTypeListResponse(BaseModel):
    asset_types: List[AssetTypeResponse]
    total_count: int


# Asset Status schemas
class AssetStatusResponse(BaseModel):
    id: uuid.UUID
    status: str

    class Config:
        from_attributes = True


# Asset schemas
class AssetBase(BaseModel):
    name: str
    version: Optional[str] = None
    justification: Optional[str] = None
    license_model: Optional[str] = None
    description: Optional[str] = None
    sbom: Optional[str] = None
    ip_address: Optional[str] = None  # IP address, IP range, or URL
    asset_type_id: str
    asset_status_id: Optional[str] = None
    economic_operator_id: Optional[str] = None
    criticality_id: Optional[str] = None
    criticality_option: Optional[str] = None
    confidentiality: Optional[str] = None
    integrity: Optional[str] = None
    availability: Optional[str] = None
    asset_value: Optional[str] = None
    inherit_cia: bool = True


class AssetCreate(AssetBase):
    pass


class AssetUpdate(AssetBase):
    pass


class AssetResponse(BaseModel):
    id: uuid.UUID
    name: str
    version: Optional[str] = None
    justification: Optional[str] = None
    license_model: Optional[str] = None
    description: Optional[str] = None
    sbom: Optional[str] = None
    ip_address: Optional[str] = None  # IP address, IP range, or URL
    asset_type_id: uuid.UUID
    asset_type_name: Optional[str] = None
    asset_type_icon: Optional[str] = None
    asset_status_id: Optional[uuid.UUID] = None
    status_name: Optional[str] = None
    economic_operator_id: Optional[uuid.UUID] = None
    economic_operator_name: Optional[str] = None
    criticality_id: Optional[uuid.UUID] = None
    criticality_label: Optional[str] = None
    criticality_option: Optional[str] = None
    # CIA fields
    confidentiality: Optional[str] = None
    integrity: Optional[str] = None
    availability: Optional[str] = None
    asset_value: Optional[str] = None
    inherit_cia: bool = True
    overall_asset_value: Optional[str] = None  # Computed server-side
    organisation_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    last_updated_by_email: Optional[str] = None
    # Scan status fields
    has_scan: Optional[bool] = False
    last_scan_date: Optional[datetime] = None
    last_scan_status: Optional[str] = None  # 'completed', 'failed', 'in_progress'
    last_scan_type: Optional[str] = None  # e.g., 'basic', 'aggressive', 'spider', 'active'
    last_scan_scanner: Optional[str] = None  # 'nmap', 'zap', etc.
    # Separate status for Network and Application scans
    network_scan_status: Optional[str] = None  # 'completed', 'failed', 'in_progress'
    network_scan_date: Optional[datetime] = None
    application_scan_status: Optional[str] = None  # 'completed', 'failed', 'in_progress'
    application_scan_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    assets: List[AssetResponse]
    total_count: int


# ===========================
# Risk Template Schemas
# ===========================

# ===========================
# Incident Registration Schemas
# ===========================

class IncidentCreate(BaseModel):
    incident_code: Optional[str] = None
    title: str
    description: Optional[str] = None
    incident_severity_id: str
    incident_status_id: str
    reported_by: Optional[str] = None
    assigned_to: Optional[str] = None
    discovered_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    containment_actions: Optional[str] = None
    root_cause: Optional[str] = None
    remediation_steps: Optional[str] = None
    # Post-market triage fields
    vulnerability_source: Optional[str] = None
    cvss_score: Optional[float] = None
    cve_id: Optional[str] = None
    cwe_id: Optional[str] = None
    triage_status: Optional[str] = None
    affected_products: Optional[str] = None


class IncidentUpdate(IncidentCreate):
    id: str


class IncidentResponse(BaseModel):
    id: uuid.UUID
    incident_code: Optional[str] = None
    title: str
    description: Optional[str] = None
    incident_severity_id: uuid.UUID
    incident_status_id: uuid.UUID
    reported_by: Optional[str] = None
    assigned_to: Optional[str] = None
    discovered_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    containment_actions: Optional[str] = None
    root_cause: Optional[str] = None
    remediation_steps: Optional[str] = None
    ai_analysis: Optional[str] = None
    # Post-market triage fields
    vulnerability_source: Optional[str] = None
    cvss_score: Optional[float] = None
    cve_id: Optional[str] = None
    cwe_id: Optional[str] = None
    euvd_vulnerability_id: Optional[uuid.UUID] = None
    triage_status: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    sla_status: Optional[str] = None
    affected_products: Optional[str] = None
    organisation_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    # Denormalized display fields
    incident_severity: Optional[str] = None
    incident_status: Optional[str] = None
    last_updated_by_email: Optional[str] = None
    linked_frameworks_count: Optional[int] = 0
    linked_risks_count: Optional[int] = 0
    linked_assets_count: Optional[int] = 0

    class Config:
        orm_mode = True


class IncidentStatusResponse(BaseModel):
    id: uuid.UUID
    incident_status_name: str

    class Config:
        orm_mode = True


class RiskTemplateItem(BaseModel):
    """Individual risk template item"""
    risk_code: str
    risk_category_name: str
    risk_category_description: str
    risk_potential_impact: str
    risk_control: str


class RiskTemplateCategoryResponse(BaseModel):
    """Response for a risk template category"""
    id: str
    name: str
    description: str
    risk_count: int


class RiskTemplatesListResponse(BaseModel):
    """Response for list of template categories"""
    categories: List[RiskTemplateCategoryResponse]


class RiskTemplateRisksResponse(BaseModel):
    """Response for risks in a category"""
    category_id: str
    category_name: str
    risks: List[RiskTemplateItem]


class RiskTemplateImportItem(BaseModel):
    """Individual risk to import"""
    risk_code: Optional[str] = None
    risk_category_name: str
    risk_category_description: str
    risk_potential_impact: str
    risk_control: str


class RiskTemplateImportRequest(BaseModel):
    """Request to import selected risk templates"""
    category_id: str
    selected_risks: List[RiskTemplateImportItem]
    asset_category_id: str
    default_likelihood: str  # UUID of severity
    default_severity: str  # UUID of severity
    default_residual_risk: str  # UUID of severity
    default_status: str  # UUID of status
    scope_name: Optional[str] = None
    scope_entity_id: Optional[str] = None


class RiskTemplateImportResponse(BaseModel):
    """Response after importing risk templates"""
    success: bool
    imported_count: int
    failed_count: int
    message: str
    imported_risk_ids: List[str] = []
    errors: List[str] = []


# ===========================
# Risk Assessment Schemas
# ===========================

class RiskTreatmentActionCreate(BaseModel):
    description: str
    due_date: Optional[datetime] = None
    owner: Optional[str] = None
    status: Optional[str] = "Open"

class RiskTreatmentActionUpdate(BaseModel):
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    owner: Optional[str] = None
    status: Optional[str] = None
    completion_notes: Optional[str] = None

class RiskTreatmentActionResponse(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    description: str
    due_date: Optional[datetime] = None
    owner: Optional[str] = None
    status: str
    completion_notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class RiskAssessmentCreate(BaseModel):
    description: Optional[str] = None
    inherent_impact: int
    inherent_likelihood: int
    current_impact: int
    current_likelihood: int
    target_impact: Optional[int] = None
    target_likelihood: Optional[int] = None
    residual_impact: Optional[int] = None
    residual_likelihood: Optional[int] = None
    impact_health: Optional[str] = None
    impact_financial: Optional[str] = None
    impact_service: Optional[str] = None
    impact_legal: Optional[str] = None
    impact_reputation: Optional[str] = None
    status: Optional[str] = "Draft"

class RiskAssessmentUpdate(BaseModel):
    description: Optional[str] = None
    inherent_impact: Optional[int] = None
    inherent_likelihood: Optional[int] = None
    current_impact: Optional[int] = None
    current_likelihood: Optional[int] = None
    target_impact: Optional[int] = None
    target_likelihood: Optional[int] = None
    residual_impact: Optional[int] = None
    residual_likelihood: Optional[int] = None
    impact_health: Optional[str] = None
    impact_financial: Optional[str] = None
    impact_service: Optional[str] = None
    impact_legal: Optional[str] = None
    impact_reputation: Optional[str] = None
    status: Optional[str] = None

class RiskAssessmentResponse(BaseModel):
    id: uuid.UUID
    risk_id: uuid.UUID
    assessment_number: int
    description: Optional[str] = None
    inherent_impact: int
    inherent_likelihood: int
    inherent_risk_score: int
    current_impact: int
    current_likelihood: int
    current_risk_score: int
    target_impact: Optional[int] = None
    target_likelihood: Optional[int] = None
    target_risk_score: Optional[int] = None
    residual_impact: Optional[int] = None
    residual_likelihood: Optional[int] = None
    residual_risk_score: Optional[int] = None
    impact_health: Optional[str] = None
    impact_financial: Optional[str] = None
    impact_service: Optional[str] = None
    impact_legal: Optional[str] = None
    impact_reputation: Optional[str] = None
    status: str
    organisation_id: uuid.UUID
    assessed_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # Computed/enriched fields
    inherent_severity: Optional[str] = None
    current_severity: Optional[str] = None
    target_severity: Optional[str] = None
    residual_severity: Optional[str] = None
    assessed_by_email: Optional[str] = None
    risk_code: Optional[str] = None
    risk_category_name: Optional[str] = None

    class Config:
        orm_mode = True

class RiskAssessmentDetailResponse(RiskAssessmentResponse):
    treatment_actions: List[RiskTreatmentActionResponse] = []

class RiskWithAssessmentResponse(BaseModel):
    id: uuid.UUID
    risk_code: Optional[str] = None
    risk_category_name: str
    risk_category_description: Optional[str] = None
    assessment_status: Optional[str] = None
    organisation_id: Optional[uuid.UUID] = None
    risk_severity: Optional[str] = None
    # Latest assessment scores
    inherent_risk_score: Optional[int] = None
    current_risk_score: Optional[int] = None
    target_risk_score: Optional[int] = None
    residual_risk_score: Optional[int] = None
    inherent_severity: Optional[str] = None
    current_severity: Optional[str] = None
    target_severity: Optional[str] = None
    residual_severity: Optional[str] = None
    last_assessed_at: Optional[datetime] = None
    assessment_count: Optional[int] = 0

    class Config:
        orm_mode = True


# ===========================
# EUVD Schemas
# ===========================

class EUVDVulnerabilityResponse(BaseModel):
    id: str
    euvd_id: str
    description: Optional[str] = None
    date_published: Optional[str] = None
    date_updated: Optional[str] = None
    base_score: Optional[float] = None
    base_score_version: Optional[str] = None
    base_score_vector: Optional[str] = None
    epss: Optional[float] = None
    assigner: Optional[str] = None
    references: Optional[str] = None
    aliases: Optional[str] = None
    products: Optional[str] = None
    vendors: Optional[str] = None
    is_exploited: bool = False
    is_critical: bool = False
    category: str


class EUVDListResponse(BaseModel):
    items: List[EUVDVulnerabilityResponse]
    total: int
    skip: int
    limit: int


class EUVDSyncStatusResponse(BaseModel):
    id: Optional[str] = None
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    vulns_processed: Optional[int] = 0
    vulns_added: Optional[int] = 0
    vulns_updated: Optional[int] = 0
    error_message: Optional[str] = None
    created_at: Optional[str] = None


class EUVDStatsResponse(BaseModel):
    total_cached: int = 0
    exploited_count: int = 0
    critical_count: int = 0
    last_sync_at: Optional[str] = None
    sync_status: Optional[str] = None


class EUVDSettingsUpdate(BaseModel):
    sync_enabled: Optional[bool] = None
    sync_interval_hours: Optional[int] = None
    sync_interval_seconds: Optional[int] = None


class EUVDSettingsResponse(BaseModel):
    id: uuid.UUID
    sync_enabled: bool
    sync_interval_hours: int
    sync_interval_seconds: int
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===========================
# CE Marking Checklist Schemas
# ===========================

class CEProductTypeResponse(BaseModel):
    id: uuid.UUID
    name: str
    recommended_placement: Optional[str] = None

    class Config:
        orm_mode = True


class CEDocumentTypeResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_mandatory: bool
    sort_order: int

    class Config:
        orm_mode = True


class CEChecklistCreate(BaseModel):
    asset_id: str
    ce_product_type_id: Optional[str] = None


class CEChecklistUpdate(BaseModel):
    ce_product_type_id: Optional[str] = None
    ce_placement: Optional[str] = None
    ce_placement_notes: Optional[str] = None
    notified_body_required: Optional[bool] = None
    notified_body_name: Optional[str] = None
    notified_body_number: Optional[str] = None
    notified_body_certificate_ref: Optional[str] = None
    version_identifier: Optional[str] = None
    build_identifier: Optional[str] = None
    doc_publication_url: Optional[str] = None
    product_variants: Optional[str] = None
    status: Optional[str] = None


class CEChecklistItemResponse(BaseModel):
    id: uuid.UUID
    checklist_id: uuid.UUID
    template_item_id: Optional[uuid.UUID] = None
    category: str
    title: str
    description: Optional[str] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    sort_order: int
    is_mandatory: bool

    class Config:
        orm_mode = True


class CEDocumentStatusResponse(BaseModel):
    id: uuid.UUID
    checklist_id: uuid.UUID
    document_type_id: uuid.UUID
    document_type_name: Optional[str] = None
    status: str
    document_reference: Optional[str] = None
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class CEChecklistResponse(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    asset_name: Optional[str] = None
    ce_product_type_id: Optional[uuid.UUID] = None
    ce_product_type_name: Optional[str] = None
    ce_placement: Optional[str] = None
    ce_placement_notes: Optional[str] = None
    notified_body_required: bool
    notified_body_name: Optional[str] = None
    notified_body_number: Optional[str] = None
    notified_body_certificate_ref: Optional[str] = None
    version_identifier: Optional[str] = None
    build_identifier: Optional[str] = None
    doc_publication_url: Optional[str] = None
    product_variants: Optional[str] = None
    status: str
    readiness_score: float
    organisation_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    # Enriched counts
    items_completed: Optional[int] = 0
    items_total: Optional[int] = 0
    docs_completed: Optional[int] = 0
    docs_total: Optional[int] = 0

    class Config:
        orm_mode = True


class CEChecklistDetailResponse(CEChecklistResponse):
    items: List[CEChecklistItemResponse] = []
    document_statuses: List[CEDocumentStatusResponse] = []


class CEChecklistItemUpdate(BaseModel):
    is_completed: Optional[bool] = None
    notes: Optional[str] = None


class CEChecklistItemCreate(BaseModel):
    category: str
    title: str
    description: Optional[str] = None
    is_mandatory: bool = False


class CEDocumentStatusUpdate(BaseModel):
    status: Optional[str] = None
    document_reference: Optional[str] = None
    notes: Optional[str] = None


# ===========================
# Post-Market Surveillance Schemas
# ===========================

class IncidentPatchCreate(BaseModel):
    patch_version: str
    description: Optional[str] = None
    release_date: Optional[datetime] = None
    target_sla_date: Optional[datetime] = None
    actual_resolution_date: Optional[datetime] = None


class IncidentPatchUpdate(BaseModel):
    patch_version: Optional[str] = None
    description: Optional[str] = None
    release_date: Optional[datetime] = None
    target_sla_date: Optional[datetime] = None
    actual_resolution_date: Optional[datetime] = None


class IncidentPatchResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    patch_version: str
    description: Optional[str] = None
    release_date: Optional[datetime] = None
    target_sla_date: Optional[datetime] = None
    actual_resolution_date: Optional[datetime] = None
    sla_compliance: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class AdvisoryStatusResponse(BaseModel):
    id: uuid.UUID
    status_name: str

    class Config:
        orm_mode = True


class SecurityAdvisoryCreate(BaseModel):
    title: str
    description: Optional[str] = None
    affected_versions: Optional[str] = None
    fixed_version: Optional[str] = None
    severity: Optional[str] = None
    cve_ids: Optional[str] = None
    workaround: Optional[str] = None
    advisory_status_id: str
    incident_id: Optional[str] = None


class SecurityAdvisoryUpdate(SecurityAdvisoryCreate):
    id: str


class SecurityAdvisoryResponse(BaseModel):
    id: uuid.UUID
    advisory_code: Optional[str] = None
    title: str
    description: Optional[str] = None
    affected_versions: Optional[str] = None
    fixed_version: Optional[str] = None
    severity: Optional[str] = None
    cve_ids: Optional[str] = None
    workaround: Optional[str] = None
    advisory_status_id: uuid.UUID
    advisory_status_name: Optional[str] = None
    incident_id: Optional[uuid.UUID] = None
    incident_code: Optional[str] = None
    published_at: Optional[datetime] = None
    organisation_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ENISANotificationCreate(BaseModel):
    early_warning_content: Optional[str] = None
    vuln_notification_content: Optional[str] = None
    final_report_content: Optional[str] = None


class ENISANotificationUpdate(BaseModel):
    early_warning_submitted: Optional[bool] = None
    early_warning_content: Optional[str] = None
    vuln_notification_submitted: Optional[bool] = None
    vuln_notification_content: Optional[str] = None
    final_report_submitted: Optional[bool] = None
    final_report_content: Optional[str] = None


class ENISANotificationResponse(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    early_warning_required: bool
    early_warning_deadline: Optional[datetime] = None
    early_warning_submitted: bool
    early_warning_submitted_at: Optional[datetime] = None
    early_warning_content: Optional[str] = None
    vuln_notification_required: bool
    vuln_notification_deadline: Optional[datetime] = None
    vuln_notification_submitted: bool
    vuln_notification_submitted_at: Optional[datetime] = None
    vuln_notification_content: Optional[str] = None
    final_report_required: bool
    final_report_deadline: Optional[datetime] = None
    final_report_submitted: bool
    final_report_submitted_at: Optional[datetime] = None
    final_report_content: Optional[str] = None
    reporting_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ChainLinksStatus(BaseModel):
    has_mapping: bool
    already_imported: bool
    framework_name: str

class ChainLinksImportResult(BaseModel):
    success: bool
    framework_name: str
    message: str
    risks_created: int = 0
    controls_created: int = 0
    policies_created: int = 0
    links_created: dict = {}
    warnings: list[str] = []

class ObjectiveFieldChange(BaseModel):
    objective_title: str
    objective_key: str
    changes: dict  # { field_name: { "old": ..., "new": ... } }

class ChainLinksUpdateCheck(BaseModel):
    has_updates: bool
    new_risks: int = 0
    new_controls: int = 0
    new_policies: int = 0
    new_links: dict = {}
    objective_field_changes: list[ObjectiveFieldChange] = []
    framework_name: str

class ChainLinksUpdateResult(BaseModel):
    success: bool
    framework_name: str
    message: str
    risks_created: int = 0
    controls_created: int = 0
    policies_created: int = 0
    links_created: dict = {}
    objectives_updated: int = 0
    warnings: list[str] = []


class PostMarketMetricsResponse(BaseModel):
    total_incidents: int = 0
    open_vulnerabilities: int = 0
    overdue_count: int = 0
    at_risk_count: int = 0
    avg_resolution_hours: Optional[float] = None
    sla_compliance_rate: Optional[float] = None
    patches_released: int = 0
    advisories_published: int = 0
    enisa_pending: int = 0
    enisa_complete: int = 0


# ===========================
# AI Suggestion Assistant Schemas
# ===========================

class SuggestionRequest(BaseModel):
    entity_id: str
    engine: str = "rule"  # "rule" or "llm"
    framework_id: Optional[str] = None
    available_item_ids: Optional[List[str]] = None


class SuggestionItem(BaseModel):
    item_id: str
    display_name: str
    confidence: int  # 0-100
    reasoning: str


class SuggestionResponse(BaseModel):
    suggestions: List[SuggestionItem]
    engine: str
    entity_id: str
    total_suggestions: int


# Assessment Answer Suggestions from Scan Results

class AssessmentAnswerSuggestionRequest(BaseModel):
    assessment_id: str
    engine: str = "llm"  # "rule" or "llm"
    platform_data: Optional[dict] = None  # Pre-gathered platform data from wizard
    question_ids: Optional[List[str]] = None  # Limit to specific questions (e.g. current page)

class AnswerSuggestionItem(BaseModel):
    question_id: str
    question_text: str
    question_number: int        # Display order from framework
    suggested_answer: str       # "yes", "no", "partially", "n/a"
    evidence_description: str   # Scan-derived evidence text
    confidence: int             # 0-100
    reasoning: str

class AssessmentAnswerSuggestionResponse(BaseModel):
    suggestions: List[AnswerSuggestionItem]
    engine: str
    assessment_id: str
    total_questions: int        # Total unanswered questions examined
    total_suggestions: int


# ===========================
# Compliance Certificate Schemas
# ===========================

class CertificateGenerateRequest(BaseModel):
    framework_id: uuid.UUID

class CertificateRevokeRequest(BaseModel):
    reason: str

class CertificateResponse(BaseModel):
    id: uuid.UUID
    certificate_number: str
    framework_name: str
    organisation_name: str
    overall_score: float
    objectives_compliant_pct: float
    assessments_completed_pct: float
    policies_approved_pct: float
    issued_at: datetime
    expires_at: datetime
    revoked: bool
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None
    verification_hash: str

class CertificateVerifyResponse(BaseModel):
    certificate_number: str
    organisation_name: str
    framework_name: str
    issued_at: datetime
    expires_at: datetime
    is_valid: bool


# ===========================
# Regulatory Submission Schemas
# ===========================

class SubmissionCreateRequest(BaseModel):
    certificate_id: uuid.UUID
    authority_name: str
    recipient_emails: List[str]
    subject: Optional[str] = None
    body: Optional[str] = None

class SubmissionUpdateFeedbackRequest(BaseModel):
    feedback: str

class SubmissionResponse(BaseModel):
    id: uuid.UUID
    certificate_id: uuid.UUID
    certificate_number: str
    framework_name: str
    authority_name: str
    recipient_emails: List[str]
    submission_method: str
    status: str
    subject: Optional[str] = None
    body: Optional[str] = None
    feedback: Optional[str] = None
    feedback_received_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    submitted_by_name: Optional[str] = None
    created_at: datetime

class EmailConfigCreateRequest(BaseModel):
    authority_name: str
    email: str

class EmailConfigResponse(BaseModel):
    id: uuid.UUID
    authority_name: str
    email: str
    is_default: bool
