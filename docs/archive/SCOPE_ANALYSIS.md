# Framework Scope Analysis & Architecture Decisions

## 1. Framework Natural Scopes

### Product-Centric Frameworks (Must Track Per-Product)
- **CRA (Cyber Resilience Act)**: Product compliance, SBOM, vulnerability tracking
  - Natural scope: `product` (mandatory)
  - Each product needs separate compliance declaration

### Organization-Centric Frameworks (Org-Wide)
- **ISO 27001:2022**: Information Security Management System (ISMS)
  - Natural scope: `organization`
  - Single ISMS covers entire organization

- **GDPR**: Data protection regulation
  - Natural scope: `organization`
  - Org-wide compliance, not per-product

- **NIS2 Directive**: Network and Information Security
  - Natural scope: `organization` (with optional service/system breakdown)
  - Essential entities compliance

- **CCPA (California Consumer Privacy Act)**: Privacy regulation
  - Natural scope: `organization`
  - Business-level compliance

- **HIPAA Privacy Rule**: Healthcare privacy
  - Natural scope: `organization`
  - Healthcare entity compliance

- **SOC 2**: Service Organization Control
  - Natural scope: `organization` or `service`
  - Could be org-wide or per-service offering

- **CMMC 2.0**: Cybersecurity Maturity Model Certification
  - Natural scope: `organization`
  - DoD contractor certification (org-level)

- **NIST CSF 2.0**: Cybersecurity Framework
  - Natural scope: `organization`
  - Enterprise cybersecurity program

### Asset/System-Centric Frameworks
- **PCI-DSS v4.0**: Payment Card Industry Data Security Standard
  - Natural scope: `asset` or `system`
  - Applies to payment processing systems (cardholder data environment)
  - Could also be `organization` if org-wide payment processing

---

## 2. Question Correlations Strategy

### Current Implementation
- Question correlations are **organization-scoped** (`organisation_id` in `question_correlations` table)
- Correlations form transitive groups (if A↔B and B↔C, then A↔C automatically)
- Purpose: Identify similar/overlapping requirements across frameworks

### Correlation Scope Decision: Framework-Level (Not Assessment-Level)

**Key Insight**: Correlations should be between **Questions** (framework requirements), NOT between **Answers** (assessment instances).

#### Why Framework-Level Correlations?

```
❌ WRONG: Assessment-Level Correlations
Assessment 1 (CRA for Product A) → Question 123 → Answer "Yes"
Assessment 2 (CRA for Product B) → Question 123 → Answer "No"
❌ Don't correlate these answers - they're different products!

✅ CORRECT: Framework-Level Correlations
Framework CRA → Question 123: "Do you maintain SBOM?"
Framework ISO 27001 → Question 456: "Do you track software inventory?"
✅ These questions are conceptually similar (both about software tracking)
   → Create correlation: Question 123 ↔ Question 456
```

#### Correlation Use Cases

**Scenario 1: Cross-Framework Answer Reuse**
```
User answers CRA Question: "Do you have vulnerability disclosure policy?"
  Answer: "Yes" + Evidence: policy.pdf

System suggests for ISO 27001 Question: "Is there a vulnerability management policy?"
  → Pre-fill answer: "Yes" + Reuse evidence: policy.pdf
  → User can modify if needed
```

**Scenario 2: Gap Analysis**
```
User completed ISO 27001 assessment
System shows: "You've answered 70% of CRA questions through ISO 27001 correlations"
                "30% unique CRA questions remaining"
```

**Scenario 3: Workload Reduction**
```
Org has 3 products (A, B, C) all needing CRA compliance
Product A: Full CRA assessment (100 questions)
Product B: Only answer non-correlated questions with ISO 27001
Product C: Same efficiency as Product B
```

### Scope Impact on Correlations

**Question**: Does it make sense to correlate questions between frameworks with different scopes?

**Answer**: **YES - Absolutely!** Scope is irrelevant for correlations.

#### Example: CRA (Product) ↔ ISO 27001 (Organization)

```
CRA Product Assessment for "IoT Sensor v3.2"
  ├─ Question: "Does the product use secure boot?"
  └─ Correlated with ISO 27001 Organizational Control:
      └─ "Does the organization enforce secure boot on all devices?"

Assessment instances:
  ├─ CRA Assessment → Scope: Product "IoT Sensor v3.2" → Answer: "Yes, using TPM"
  └─ ISO 27001 Assessment → Scope: Organization "Acme Corp" → Answer: "Yes, company policy"

The QUESTIONS are correlated (similar control concepts)
The ANSWERS are different contexts (product vs org)
```

**When to suggest correlated answers**:
- ✅ If answering Product A's CRA and user has ISO 27001 org assessment
  → Suggest ISO 27001 answer as a starting point
- ✅ If answering Product B's CRA and Product A's CRA is complete
  → Suggest Product A's answers for product-specific questions
- ⚠️ Smart filtering: Only suggest if context makes sense

---

## 3. Risk Scope Strategy

### Current State
- Risks have `organisation_id` (org-scoped)
- Risks have `product_type_id` (Hardware/Software - generic type)

### Proposed: Flexible Risk Scoping

**Why risks need flexible scoping:**

```
Risk Type 1: Product-Specific Vulnerability
  Risk: "CVE-2024-1234 in IoT Sensor v3.2 firmware"
  Scope: product (specific product instance)
  Impact: Only affects this product

Risk Type 2: Organizational Risk
  Risk: "No disaster recovery plan"
  Scope: organization
  Impact: Affects entire organization

Risk Type 3: Asset-Specific Risk
  Risk: "Unpatched payment gateway server"
  Scope: asset (specific server)
  Impact: Affects payment processing system

Risk Type 4: Process Risk
  Risk: "Software development lacks secure coding review"
  Scope: process (SDLC process)
  Impact: Affects all products developed
```

**Recommendation**: Use `risk_scope` junction table (same pattern as `assessment_scope`)

```sql
risk_scope:
  - risk_id
  - scope_type ('product', 'organization', 'asset', 'process', 'project')
  - scope_id
```

**Benefits**:
- ✅ Track product vulnerabilities per product
- ✅ Track organizational risks org-wide
- ✅ Link risks to specific assets when needed
- ✅ One risk can affect multiple scopes (e.g., supply chain risk affects all products)

---

## 4. User-Controlled Scope Selection

### Question: Should users choose scope type freely or framework-dictated?

**Answer**: **Hybrid Approach** (Framework suggests, user can override)

### Recommended Implementation

#### Framework Metadata (New Fields in `frameworks` table)

```python
class Framework(Base):
    __tablename__ = "frameworks"

    # Existing fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organisations.id"))

    # NEW FIELDS for scope control
    default_scope_type = Column(String(50), nullable=True)  # 'product', 'organization', 'flexible'
    allowed_scope_types = Column(Text, nullable=True)  # JSON: ['product', 'organization']
    scope_selection_mode = Column(String(50), default='flexible')  # 'required', 'optional', 'flexible'

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

#### Scope Selection Modes

**Mode 1: `required` - Framework Enforces Scope**
```
Framework: CRA
  default_scope_type: 'product'
  allowed_scope_types: ['product']
  scope_selection_mode: 'required'

UI Behavior:
  ├─ User must select product(s)
  ├─ No option to skip or choose different scope
  └─ Validation fails without product selection
```

**Mode 2: `optional` - Framework Suggests Scope**
```
Framework: ISO 27001
  default_scope_type: 'organization'
  allowed_scope_types: ['organization', 'department', 'subsidiary']
  scope_selection_mode: 'optional'

UI Behavior:
  ├─ Defaults to organization scope
  ├─ User can choose different scope from allowed list
  └─ User can skip scope selection (framwork-only assessment)
```

**Mode 3: `flexible` - User Chooses Freely**
```
Framework: Custom Framework
  default_scope_type: null
  allowed_scope_types: ['product', 'organization', 'asset', 'project']
  scope_selection_mode: 'flexible'

UI Behavior:
  ├─ Dropdown: "What is this assessment for?"
  ├─ Options: Product | Organization | Asset | Project | None
  └─ Complete freedom for user
```

### UI Flow Example

```typescript
// Step 1: User selects framework
const framework = getSelectedFramework(); // e.g., CRA

// Step 2: Backend returns framework metadata
const scopeConfig = {
  default_scope_type: 'product',
  allowed_scope_types: ['product'],
  scope_selection_mode: 'required'
};

// Step 3: UI adapts
if (scopeConfig.scope_selection_mode === 'required') {
  // Show required scope selector
  <FormItem required>
    <Select placeholder="Select Product(s)">
      {products.map(p => <Option key={p.id}>{p.name}</Option>)}
    </Select>
  </FormItem>

} else if (scopeConfig.scope_selection_mode === 'optional') {
  // Show optional scope selector with default
  <FormItem>
    <Select defaultValue="organization" allowClear>
      <Option value="organization">Organization: {orgName}</Option>
      <Option value="none">No specific scope</Option>
    </Select>
  </FormItem>

} else if (scopeConfig.scope_selection_mode === 'flexible') {
  // Show full flexibility
  <FormItem>
    <Select placeholder="Assessment applies to... (optional)">
      <Option value="product">Product</Option>
      <Option value="organization">Organization</Option>
      <Option value="asset">Asset</Option>
      <Option value="none">No specific scope</Option>
    </Select>
  </FormItem>

  // Second dropdown appears based on first selection
  {scopeType === 'product' && (
    <Select placeholder="Select product">
      {products.map(p => <Option key={p.id}>{p.name}</Option>)}
    </Select>
  )}
}
```

### Benefits of Hybrid Approach

✅ **Framework Correctness**: CRA always requires product scope
✅ **Flexibility**: Custom frameworks can be scope-agnostic
✅ **User Experience**: Guided by defaults, empowered by choice
✅ **Validation**: Enforce rules where needed, relax where appropriate
✅ **Future-Proof**: Add new scope types without breaking existing frameworks

---

## 5. Recommended Implementation Plan

### Phase 1: Core Scope Infrastructure
1. Add scope tables (`assessment_scope`, `risk_scope`)
2. Add framework metadata columns (`default_scope_type`, `allowed_scope_types`, `scope_selection_mode`)
3. Create scope validation service
4. Migrate existing data (assessments via user→org, risks via organisation_id)

### Phase 2: Framework Configuration
Configure each framework's scope requirements:

```python
# CRA - Product Required
update_framework(
    name="CRA",
    default_scope_type='product',
    allowed_scope_types=['product'],
    scope_selection_mode='required'
)

# ISO 27001 - Organization Default
update_framework(
    name="ISO 27001 2022",
    default_scope_type='organization',
    allowed_scope_types=['organization', 'subsidiary'],
    scope_selection_mode='optional'
)

# PCI-DSS - Asset/System Focus
update_framework(
    name="PCI DSS v4.0",
    default_scope_type='asset',
    allowed_scope_types=['asset', 'system', 'organization'],
    scope_selection_mode='required'
)

# Custom Frameworks - Full Flexibility
update_framework(
    name="Custom Framework",
    default_scope_type=null,
    allowed_scope_types=['product', 'organization', 'asset', 'project', 'process'],
    scope_selection_mode='flexible'
)
```

### Phase 3: UI Updates
1. Assessment creation wizard adapts to framework scope config
2. Risk creation form allows scope selection
3. Reporting/dashboards filter by scope
4. Search: "Show all assessments for Product X"

### Phase 4: Correlation Intelligence
1. Smart correlation suggestions based on scope context
2. Answer pre-filling with scope awareness
3. Gap analysis across scoped assessments

---

## Summary: Key Decisions

| Topic | Decision | Reasoning |
|-------|----------|-----------|
| **Framework Scopes** | Each framework has natural scope, configured in DB | Different regulations apply to different entities |
| **Question Correlations** | Framework-level (not assessment-level) | Questions are conceptually similar, regardless of scope |
| **Scope Impact on Correlations** | No impact - correlate freely across scopes | A "vulnerability policy" question is similar whether product or org |
| **Risk Scoping** | Use `risk_scope` table (flexible) | Risks can be product, org, asset, or process-specific |
| **User Scope Control** | Hybrid: Framework suggests, user can choose (within allowed types) | Balance compliance correctness with flexibility |
| **Scope Enforcement** | Three modes: required, optional, flexible | CRA enforces product, ISO suggests org, custom is free |

---

## Next Steps

**Option A: Implement Full Flexible Architecture**
- ✅ Future-proof for any framework type
- ✅ Supports CRA, ISO, PCI-DSS, custom frameworks
- ⚠️ More complex initial implementation

**Option B: Start with CRA Product Scope Only**
- ✅ Solve immediate CRA need
- ✅ Simpler initial implementation
- ⚠️ Need refactoring later for full flexibility

**Recommendation**: **Option A** - The scope infrastructure is not significantly more complex than solving just CRA, and it provides a solid foundation for your GRC platform's future.

Would you like to proceed with implementation?
