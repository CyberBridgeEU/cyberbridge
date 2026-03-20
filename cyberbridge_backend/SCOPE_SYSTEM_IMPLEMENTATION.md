# Scope System Implementation - Complete

## Overview

The scope system has been fully implemented in the backend to support framework-agnostic compliance assessments and risk management. This system allows assessments and risks to be scoped to different entities (Products, Organizations, Assets, etc.) based on the framework's requirements.

## What Was Implemented

### 1. Database Models (`app/models/models.py`)

#### New Model: `Scopes`
- Lookup table for scope types (Product, Organization, Other, Asset, Project, Process)
- Only Product, Organization, and Other are currently active

#### Updated Models:
- **Framework**: Added scope configuration fields
  - `default_scope_type`: Default scope for the framework
  - `allowed_scope_types`: JSON array of allowed scope types
  - `scope_selection_mode`: 'required', 'optional', or 'flexible'

- **Assessment**: Added scope tracking fields
  - `scope_id`: Foreign key to scopes table
  - `scope_entity_id`: UUID of the scoped entity

- **Risks**: Added scope tracking fields
  - `scope_id`: Foreign key to scopes table
  - `scope_entity_id`: UUID of the scoped entity

### 2. Database Migration

**File**: `alembic/versions/50a6ac349aab_add_scope_system_to_assessments_and_.py`

Creates:
- `scopes` table with predefined scope types
- Scope configuration columns in `frameworks` table
- Scope tracking columns in `assessments` and `risks` tables

The migration is idempotent and can be safely re-run.

### 3. Scope Validation Service

**File**: `app/services/scope_validation_service.py`

Key Functions:
- `validate_scope()`: Validates that a scoped entity exists
- `get_scope_display_name()`: Returns human-readable name for scoped entities
- `get_scope_info()`: Retrieves complete scope information
- `validate_framework_scope()`: Validates scope against framework requirements
- `get_framework_scope_config()`: Returns framework's scope configuration

Special Features:
- 'Other' scope type doesn't require entity validation
- Polymorphic entity resolution (Product, Organization, etc.)
- Framework-specific scope requirement enforcement

### 4. Pydantic Schemas (`app/dtos/schemas.py`)

#### Updated Schemas:
- `AssessmentCreateRequest`: Added `scope_name` and `scope_entity_id`
- `AssessmentResponse`: Added scope fields with dynamic enrichment
- `RiskCreate`, `RiskUpdate`, `RiskResponse`: Added scope fields

#### New Schemas:
- `ScopeInfo`: Detailed scope information
- `FrameworkScopeConfig`: Framework scope configuration
- `ScopeTypeResponse`: Available scope types

### 5. Repository Updates

#### Assessment Repository (`app/repositories/assessment_repository.py`)
- `create_assessment()`: Validates and adds scope to new assessments
- `get_assessments_by_scope()`: Retrieves assessments for a specific scope
- `_enrich_assessment_with_scope()`: Adds scope display names

#### Risk Repository (`app/repositories/risks_repository.py`)
- `create_risk()`: Validates and adds scope to new risks
- `update_risk()`: Updates risk scope
- `_enrich_risk_with_info()`: Adds scope information to risk objects

### 6. Seeding System

#### Scopes Seed (`app/seeds/scopes_seed.py`)
- Creates all scope types on application startup
- Integrated into `seed_manager.py`

#### Framework Scope Configuration (`app/seeds/framework_scope_config_seed.py`)
- Configures scope requirements for existing frameworks
- Run via standalone script

### 7. Configuration Script

**File**: `scripts/configure_framework_scopes.py`

Standalone script to configure scope settings for existing frameworks.

**Usage**:
```bash
python scripts/configure_framework_scopes.py
```

## Framework Scope Configurations

The following frameworks have been configured:

| Framework | Default Scope | Allowed Scopes | Selection Mode | Rationale |
|-----------|--------------|----------------|----------------|-----------|
| **CRA** | Product | Product | Required | Product-centric framework |
| **GDPR** | Organization | Organization, Other | Required | Applies to organizations |
| **PCI DSS v4.0** | Organization | Organization, Asset, Other | Optional | Can scope to payment systems |
| **HIPAA Privacy Rule** | Organization | Organization, Other | Required | Applies to covered entities |
| **NIS2 Directive** | Organization | Organization, Other | Required | Essential service providers |
| **CMMC 2.0** | Organization | Organization, Other | Required | Defense industrial base |

Frameworks not yet in database: ISO 27001, SOC 2, NIST CSF 2.0, CCPA

## Scope Types

### Currently Active:
1. **Product**: For product-centric frameworks (e.g., CRA)
   - Links to `products` table
   - Requires valid product UUID

2. **Organization**: For organization-wide frameworks (e.g., ISO 27001, GDPR)
   - Links to `organisations` table
   - Requires valid organization UUID

3. **Other**: Flexible/undefined scope
   - No entity validation required
   - For frameworks that don't fit standard categories

### Reserved for Future:
- **Asset**: For asset-specific assessments (e.g., PCI DSS)
- **Project**: For project-based assessments
- **Process**: For process-specific assessments

## How It Works

### Creating a Scoped Assessment

```python
# With scope
assessment = {
    "framework_id": "...",
    "user_id": "...",
    "assessment_type_id": "...",
    "scope_name": "Product",  # or "Organization", "Other"
    "scope_entity_id": "product-uuid-here"
}

# Framework validation occurs automatically:
# - Checks if framework requires/allows this scope type
# - Validates that the entity exists
# - Returns error if requirements aren't met
```

### Creating a Scoped Risk

```python
# With scope
risk = {
    "product_type_id": "...",
    "risk_category_name": "...",
    "scope_name": "Product",
    "scope_entity_id": "product-uuid-here"
    # ... other fields
}

# Validation occurs:
# - Checks scope type is supported
# - Validates entity exists (unless 'Other')
# - Returns enriched risk with scope display name
```

### Querying by Scope

```python
# Get all assessments for a specific product
assessments = get_assessments_by_scope(
    db,
    scope_name="Product",
    scope_entity_id=product_id
)

# All returned assessments include:
# - scope_name: "Product"
# - scope_display_name: "MyProduct v1.0"
```

## Validation Rules

### Framework Scope Modes

1. **Required**: Assessment/risk MUST have a scope
   - Framework specifies which scope types are allowed
   - API rejects requests without valid scope

2. **Optional**: Assessment/risk MAY have a scope
   - If provided, must be from allowed types
   - Can be created without scope

3. **Flexible**: Any scope or no scope accepted
   - Maximum flexibility
   - No validation of scope types

### Entity Validation

- **Product**: Must exist in `products` table
- **Organization**: Must exist in `organisations` table
- **Other**: No validation (special case)
- **Future types**: Will validate against respective tables

## API Changes Needed (Frontend Integration)

The following API endpoints need to be created or updated:

### New Endpoints Needed:
1. `GET /frameworks/{id}/scope-config` - Get framework's scope requirements
2. `GET /scopes` - List available scope types
3. `POST /assessments` - Updated to accept scope parameters
4. `PUT /assessments/{id}` - Updated to accept scope updates
5. `POST /risks` - Updated to accept scope parameters
6. `PUT /risks/{id}` - Updated to accept scope updates

### Response Format:
All assessment and risk responses now include:
```json
{
  "id": "...",
  "scope_id": "uuid",
  "scope_entity_id": "uuid",
  "scope_name": "Product",
  "scope_display_name": "MyProduct v1.0"
}
```

## Testing the Implementation

### 1. Check Migration Status
```bash
cd cyberbridge_backend
alembic current
# Should show: 50a6ac349aab
```

### 2. Verify Scopes Exist
```sql
SELECT * FROM scopes;
-- Should show: Product, Organization, Other, Asset, Project, Process
```

### 3. Check Framework Configurations
```sql
SELECT name, default_scope_type, scope_selection_mode
FROM frameworks;
```

### 4. Test Scope Validation
```python
from app.services import scope_validation_service

# Test valid product scope
result = scope_validation_service.validate_scope(
    db, "Product", product_uuid
)
# Returns: {'scope_id': uuid, 'scope_entity': <Product>}

# Test 'Other' scope
result = scope_validation_service.validate_scope(
    db, "Other", None
)
# Returns: {'scope_id': uuid, 'scope_entity': None}
```

## Future Enhancements

1. **Asset Scope**: Implement asset table and enable Asset scope
2. **Project Scope**: Add project tracking and enable Project scope
3. **Process Scope**: Add process management and enable Process scope
4. **Scope Hierarchies**: Support parent-child scope relationships
5. **Scope Templates**: Pre-defined scope configurations for common scenarios
6. **Scope Analytics**: Dashboard showing assessments/risks by scope
7. **Scope Permissions**: Fine-grained access control based on scope

## Migration Notes

### For Existing Data:
- All existing assessments and risks have `scope_id` and `scope_entity_id` as NULL
- This is valid for frameworks with 'optional' or 'flexible' scope modes
- New assessments/risks will require scope based on framework configuration

### Running the Configuration Script:
```bash
# From cyberbridge_backend directory
python scripts/configure_framework_scopes.py

# Output shows:
# - Frameworks successfully configured
# - Frameworks not found (not yet seeded)
# - Detailed configuration for each framework
```

## Files Modified/Created

### Created:
1. `app/services/scope_validation_service.py`
2. `app/seeds/scopes_seed.py`
3. `app/seeds/framework_scope_config_seed.py`
4. `scripts/configure_framework_scopes.py`
5. `alembic/versions/50a6ac349aab_add_scope_system_to_assessments_and_.py`

### Modified:
1. `app/models/models.py` - Added Scopes model, updated Framework/Assessment/Risks
2. `app/dtos/schemas.py` - Added scope fields to relevant schemas
3. `app/repositories/assessment_repository.py` - Added scope support
4. `app/repositories/risks_repository.py` - Added scope support
5. `app/seeds/seed_manager.py` - Integrated scopes seed

## Summary

The scope system is now fully functional in the backend and ready for frontend integration. It provides:

✅ Flexible scope types (Product, Organization, Other)
✅ Framework-specific scope requirements
✅ Entity validation and display names
✅ Backward compatibility (existing data unaffected)
✅ Extensibility (reserved scope types for future)
✅ Configuration management (standalone script)

The next phase is frontend development to:
- Add scope selectors to assessment/risk forms
- Display scope information in lists and details
- Filter assessments/risks by scope
- Show framework scope requirements dynamically
