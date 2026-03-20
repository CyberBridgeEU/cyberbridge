# Scope System Implementation Status

## ✅ Completed (Phase 1)

### 1. Database Models ✅
**Location**: `cyberbridge_backend/app/models/models.py`

**Created:**
- `Scopes` model - Lookup table for scope types (Product, Organization, Asset, Project, Process)
- Updated `Framework` model - Added scope configuration fields
- Updated `Assessment` model - Added `scope_id` and `scope_entity_id` fields
- Updated `Risks` model - Added `scope_id` and `scope_entity_id` fields

### 2. Database Migration ✅
**Location**: `cyberbridge_backend/alembic/versions/50a6ac349aab_add_scope_system_to_assessments_and_.py`

**Applied:**
- Created `scopes` table
- Added scope configuration columns to `frameworks` table
- Added scope columns to `assessments` table
- Added scope columns to `risks` table
- Foreign key constraints created
- Migration is idempotent (safe to run multiple times)

### 3. Scope Validation Service ✅
**Location**: `cyberbridge_backend/app/services/scope_validation_service.py`

**Functions:**
- `get_supported_scope_types()` - Returns list of currently enabled scope types
- `validate_scope()` - Validates that a scope entity exists
- `get_scope_display_name()` - Gets human-readable name for scoped entity
- `get_scope_info()` - Gets complete scope information
- `validate_framework_scope()` - Validates scope against framework requirements
- `get_framework_scope_config()` - Gets framework's scope configuration

**Currently Supported Scopes:**
- ✅ Product
- ✅ Organization
- ⏸️ Asset (reserved, not yet implemented)
- ⏸️ Project (reserved, not yet implemented)
- ⏸️ Process (reserved, not yet implemented)

### 4. Scopes Seed ✅
**Location**: `cyberbridge_backend/app/seeds/scopes_seed.py`

Seeds scope types on application startup. Integrated into seed_manager.py.

---

## 🚧 Remaining Work (Phase 2)

### 5. Update DTOs/Schemas
**Location**: `cyberbridge_backend/app/dtos/schemas.py`

**Need to add:**

#### Assessment Schemas
```python
class AssessmentCreate(AssessmentBase):
    scope_name: Optional[str] = None  # 'Product', 'Organization'
    scope_entity_id: Optional[uuid.UUID] = None

class AssessmentResponse(AssessmentBase):
    id: uuid.UUID
    # ... existing fields ...
    scope_id: Optional[uuid.UUID] = None
    scope_entity_id: Optional[uuid.UUID] = None
    scope_display_name: Optional[str] = None  # e.g., "Product A v1.0"

    class Config:
        orm_mode = True
```

#### Risk Schemas
```python
class RiskCreate(RiskBase):
    # ... existing fields ...
    scope_name: Optional[str] = None
    scope_entity_id: Optional[uuid.UUID] = None

class RiskResponse(BaseModel):
    id: uuid.UUID
    # ... existing fields ...
    scope_id: Optional[uuid.UUID] = None
    scope_entity_id: Optional[uuid.UUID] = None
    scope_display_name: Optional[str] = None

    class Config:
        orm_mode = True
```

#### Framework Schemas
```python
class FrameworkResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    # ... existing fields ...

    # NEW: Scope configuration
    default_scope_type: Optional[str] = None
    allowed_scope_types: Optional[List[str]] = None
    scope_selection_mode: Optional[str] = 'flexible'

    class Config:
        orm_mode = True
```

#### New Scope Schemas
```python
class ScopeInfo(BaseModel):
    """Information about assessment/risk scope"""
    scope_name: str  # 'Product', 'Organization'
    scope_id: uuid.UUID
    scope_entity_id: uuid.UUID
    entity_name: str  # Display name

class FrameworkScopeConfig(BaseModel):
    """Framework scope configuration"""
    default_scope_type: Optional[str]
    allowed_scope_types: List[str]
    scope_selection_mode: str  # 'required', 'optional', 'flexible'
    supported_scope_types: List[str]  # Currently available in system
```

---

### 6. Update Repositories

#### Assessment Repository
**Location**: `cyberbridge_backend/app/repositories/assessment_repository.py`

**Updates needed:**

```python
from app.services import scope_validation_service

def create_assessment(
    db: Session,
    assessment: schemas.AssessmentCreate,
    scope_name: Optional[str] = None,
    scope_entity_id: Optional[uuid.UUID] = None
):
    """Create assessment with optional scope"""

    assessment_data = assessment.model_dump()

    # Validate and add scope if provided
    if scope_name and scope_entity_id:
        # Validate framework scope requirements
        scope_validation_service.validate_framework_scope(
            db,
            assessment.framework_id,
            scope_name,
            scope_entity_id
        )

        # Validate scope entity exists
        scope_result = scope_validation_service.validate_scope(
            db,
            scope_name,
            scope_entity_id
        )

        assessment_data['scope_id'] = scope_result['scope_id']
        assessment_data['scope_entity_id'] = scope_entity_id

    # Create assessment
    db_assessment = models.Assessment(**assessment_data)
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)

    return db_assessment

def get_assessments_with_scope(db: Session, skip: int = 0, limit: int = 100):
    """Get assessments with scope information"""
    assessments = db.query(models.Assessment).offset(skip).limit(limit).all()

    # Enrich with scope display names
    for assessment in assessments:
        if assessment.scope_id and assessment.scope_entity_id:
            scope_info = scope_validation_service.get_scope_info(
                db,
                assessment.scope_id,
                assessment.scope_entity_id
            )
            if scope_info:
                assessment.scope_display_name = scope_info['entity_name']

    return assessments

def get_assessments_by_scope(
    db: Session,
    scope_name: str,
    scope_entity_id: uuid.UUID
):
    """Get all assessments for a specific scoped entity"""

    # Get scope_id from scope name
    scope = db.query(models.Scopes).filter(
        models.Scopes.scope_name == scope_name
    ).first()

    if not scope:
        return []

    return db.query(models.Assessment).filter(
        models.Assessment.scope_id == scope.id,
        models.Assessment.scope_entity_id == scope_entity_id
    ).all()
```

#### Risk Repository
**Location**: `cyberbridge_backend/app/repositories/risks_repository.py`

**Similar updates needed:**

```python
def create_risk(db: Session, risk: dict, current_user: schemas.UserBase = None):
    """Create risk with optional scope"""

    # Extract scope information if provided
    scope_name = risk.pop('scope_name', None)
    scope_entity_id = risk.pop('scope_entity_id', None)

    # Validate and add scope if provided
    scope_id = None
    if scope_name and scope_entity_id:
        scope_result = scope_validation_service.validate_scope(
            db,
            scope_name,
            scope_entity_id
        )
        scope_id = scope_result['scope_id']

    db_risk = models.Risks(
        # ... existing fields ...
        scope_id=scope_id,
        scope_entity_id=scope_entity_id,
        organisation_id=current_user.organisation_id if current_user else None,
        created_by=current_user.id if current_user else None,
        last_updated_by=current_user.id if current_user else None
    )

    db.add(db_risk)
    db.commit()
    db.refresh(db_risk)

    return db_risk

def get_risks_by_scope(
    db: Session,
    scope_name: str,
    scope_entity_id: uuid.UUID,
    current_user: schemas.UserBase = None
):
    """Get all risks for a specific scoped entity"""

    scope = db.query(models.Scopes).filter(
        models.Scopes.scope_name == scope_name
    ).first()

    if not scope:
        return []

    query = db.query(models.Risks).filter(
        models.Risks.scope_id == scope.id,
        models.Risks.scope_entity_id == scope_entity_id
    )

    # Apply org filtering
    if current_user and current_user.role_name != "super_admin":
        query = query.filter(models.Risks.organisation_id == current_user.organisation_id)

    return query.all()
```

---

### 7. Configure Existing Frameworks

**Need to update framework seeds or create a migration script to set scope requirements:**

#### Update Framework Seeds

**CRA Framework** (`cyberbridge_backend/app/seeds/cra_seed.py`):
```python
# In the seed() method, after creating the framework:

import json

# Update CRA framework with scope configuration
if created:
    cra_framework.default_scope_type = 'Product'
    cra_framework.allowed_scope_types = json.dumps(['Product'])
    cra_framework.scope_selection_mode = 'required'
    db.commit()
```

**ISO 27001 Framework** (`cyberbridge_backend/app/seeds/iso_27001_2022_seed.py`):
```python
if created:
    iso_27001_2022_framework.default_scope_type = 'Organization'
    iso_27001_2022_framework.allowed_scope_types = json.dumps(['Organization', 'Subsidiary'])
    iso_27001_2022_framework.scope_selection_mode = 'optional'
    db.commit()
```

**Alternative: Create a Data Migration Script**

**Location**: `cyberbridge_backend/scripts/configure_framework_scopes.py`

```python
import json
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models import models

def configure_framework_scopes():
    """Configure scope requirements for existing frameworks"""
    db = next(get_db())

    framework_configs = {
        'CRA': {
            'default_scope_type': 'Product',
            'allowed_scope_types': ['Product'],
            'scope_selection_mode': 'required'
        },
        'ISO 27001 2022': {
            'default_scope_type': 'Organization',
            'allowed_scope_types': ['Organization'],
            'scope_selection_mode': 'optional'
        },
        'NIS2': {
            'default_scope_type': 'Organization',
            'allowed_scope_types': ['Organization'],
            'scope_selection_mode': 'optional'
        },
        'GDPR': {
            'default_scope_type': 'Organization',
            'allowed_scope_types': ['Organization'],
            'scope_selection_mode': 'required'
        },
        'PCI DSS v4.0': {
            'default_scope_type': 'Asset',
            'allowed_scope_types': ['Asset', 'System', 'Organization'],
            'scope_selection_mode': 'required'
        },
        # Add more frameworks...
    }

    for framework_name, config in framework_configs.items():
        framework = db.query(models.Framework).filter(
            models.Framework.name == framework_name
        ).first()

        if framework:
            framework.default_scope_type = config['default_scope_type']
            framework.allowed_scope_types = json.dumps(config['allowed_scope_types'])
            framework.scope_selection_mode = config['scope_selection_mode']
            print(f"✅ Configured {framework_name}")
        else:
            print(f"⏭️  {framework_name} not found in database")

    db.commit()
    print("Framework scope configuration complete!")

if __name__ == "__main__":
    configure_framework_scopes()
```

**Run with:**
```bash
cd cyberbridge_backend
python -m scripts.configure_framework_scopes
```

---

## 📊 Framework Scope Configuration Reference

| Framework | Default Scope | Allowed Scopes | Mode | Reasoning |
|-----------|--------------|----------------|------|-----------|
| CRA | Product | Product | required | Per-product compliance mandatory |
| ISO 27001 | Organization | Organization | optional | ISMS is org-wide |
| NIS2 | Organization | Organization | optional | Essential entity compliance |
| GDPR | Organization | Organization | required | Data protection is org-level |
| CCPA | Organization | Organization | required | Business-level privacy |
| HIPAA | Organization | Organization | required | Healthcare entity compliance |
| SOC 2 | Organization | Organization, Service | optional | Can be org or service-level |
| CMMC 2.0 | Organization | Organization | required | DoD contractor certification |
| NIST CSF 2.0 | Organization | Organization | optional | Enterprise cybersecurity |
| PCI-DSS v4.0 | Asset | Asset, System, Organization | required | Payment processing systems |

---

## 🎯 Next Steps for Full Implementation

### Immediate (Required for basic functionality):

1. ✅ **Update DTOs** - Add scope fields to request/response schemas
2. ✅ **Update Assessment Repository** - Handle scope on create/read
3. ✅ **Update Risk Repository** - Handle scope on create/read
4. ✅ **Configure Frameworks** - Run script or update seeds

### Short-term (Enhanced functionality):

5. **Update Assessment Controller** - Accept scope parameters in API endpoints
6. **Update Risk Controller** - Accept scope parameters in API endpoints
7. **Add API Endpoint** - `GET /frameworks/{id}/scope-config` to return scope requirements
8. **Add API Endpoint** - `GET /scopes` to list available scope types

### Medium-term (Full UI support):

9. **Frontend: Assessment Creation Form** - Dynamic scope selector based on framework
10. **Frontend: Risk Creation Form** - Optional scope selector
11. **Frontend: Filtering** - Filter assessments/risks by scope
12. **Frontend: Dashboard** - Show scope information in lists/cards

---

## 🧪 Testing the Implementation

### 1. Verify Database Schema
```bash
cd cyberbridge_backend
alembic current
# Should show: 50a6ac349aab (head)
```

### 2. Check Scopes Table
```sql
SELECT * FROM scopes;
```
Expected output:
```
id | scope_name    | created_at
---|--------------|-----------
... | Product      | ...
... | Organization | ...
... | Asset        | ...
... | Project      | ...
... | Process      | ...
```

### 3. Verify Models Loaded
```python
# In Python shell or test:
from app.models import models
from app.database.database import get_db

db = next(get_db())

# Check if scopes exist
scopes = db.query(models.Scopes).all()
print(f"Scopes count: {len(scopes)}")

# Check if assessment has scope fields
from sqlalchemy import inspect
insp = inspect(models.Assessment)
columns = [c.name for c in insp.columns]
print("scope_id" in columns)  # Should be True
print("scope_entity_id" in columns)  # Should be True
```

### 4. Test Scope Validation Service
```python
from app.services import scope_validation_service

# Get supported types
types = scope_validation_service.get_supported_scope_types()
print(types)  # ['Product', 'Organization']

# Test validation (replace UUIDs with actual ones)
result = scope_validation_service.validate_scope(
    db,
    'Product',
    'actual-product-uuid-here'
)
print(result)
```

---

## 📝 Summary

**Completed:**
- ✅ Database schema with scope support
- ✅ Migration applied successfully
- ✅ Scope validation service created
- ✅ Scopes seed file created and integrated

**Ready to Implement:**
- 🚧 DTOs/Schemas updates (code examples provided above)
- 🚧 Repository updates (code examples provided above)
- 🚧 Framework configuration (script provided above)

**Time Estimate for Remaining Work:**
- DTOs: ~30 minutes
- Repositories: ~1 hour
- Framework Configuration: ~15 minutes
- API Controllers: ~1 hour
- Frontend UI: ~3-4 hours

**Total remaining:** ~6 hours for complete backend + frontend implementation

The foundation is solid! The remaining work is straightforward CRUD updates and UI enhancements.
