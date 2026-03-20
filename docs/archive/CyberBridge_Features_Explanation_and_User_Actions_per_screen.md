# CyberBridge - Features Explanation and User Actions per Screen

This document provides a comprehensive guide to all features and user actions available in the CyberBridge Cybersecurity Compliance Assessment Platform, organized by screen/page.

---

## Table of Contents

1. [Authentication Screens](#1-authentication-screens)
   - [Login Page](#11-login-page)
   - [Register Page](#12-register-page)
2. [Dashboard](#2-dashboard-home-page)
3. [Assessments](#3-assessments)
4. [Product Registration](#4-product-registration)
5. [Policies Registration](#5-policies-registration)
6. [Risk Registration](#6-risk-registration)
7. [Framework Management](#7-framework-management)
8. [Objectives Checklist](#8-objectives-checklist)
9. [Update Password](#9-update-password)
10. [Admin Area](#10-admin-area)
    - [Settings](#101-settings)
    - [Correlations](#102-correlations)
    - [Organizations (User Management)](#103-organizations-user-management)
    - [Approvals](#104-approvals)
    - [History](#105-history)
11. [Scanners](#11-scanners)
    - [Web App Scanner (ZAP)](#111-web-app-scanner-zap)
    - [Network Scanner (Nmap)](#112-network-scanner-nmap)
    - [Code Analysis (Semgrep)](#113-code-analysis-semgrep)
    - [Dependency Analysis (OSV)](#114-dependency-analysis-osv)

---

## 1. Authentication Screens

### 1.1 Login Page

**Route:** `/login`
**Access:** Public (no authentication required)
**Purpose:** Allow users to authenticate and access the platform

#### Features

| Feature | Description |
|---------|-------------|
| Email Input | Text field for entering registered email address |
| Password Input | Secure password field with masked characters |
| Login Button | Submits credentials for authentication with loading state indicator |
| Forgot Password | Link to trigger password reset flow via email |
| Register Link | Navigation to registration page for new users |
| Partner Logos | Displays CyberBridge, EU, and ECCC logos |
| Background Branding | Styled background image for brand identity |

#### User Actions

1. **Login to Account**
   - Enter email address in the email field
   - Enter password in the password field
   - Click "Login" button
   - On success: Redirects to **Dashboard (Home Page)**
   - On failure: Displays error notification

2. **Reset Forgotten Password**
   - Click "Forgot your password?" link
   - Enter registered email address in the prompt
   - Receive password reset email
   - Follow email instructions to reset password
   - Return to Login Page to sign in with new password

3. **Navigate to Registration**
   - Click "Register here" link
   - Redirects to **Register Page**

#### Connections to Other Screens

- **On successful login** → Dashboard (Home Page)
- **Register link** → Register Page
- **Password reset email** → External email client, then back to Login

---

### 1.2 Register Page

**Route:** `/register`
**Access:** Public (no authentication required)
**Purpose:** Allow new users to create an account

#### Features

| Feature | Description |
|---------|-------------|
| Email Input | Text field for new account email |
| Password Input | Secure field for creating password |
| Confirm Password | Verification field to ensure password accuracy |
| Form Validation | Real-time validation for email format and password matching |
| Register Button | Submits registration with loading state |
| Verification Email | Automated email sent upon successful registration |
| Resend Verification | Option to resend verification email if not received |
| Login Link | Navigation back to login page |

#### Validation Rules

- Email must be in valid email format
- Password must be at least 6 characters
- Password and Confirm Password must match

#### User Actions

1. **Create New Account**
   - Enter email address
   - Enter password (minimum 6 characters)
   - Re-enter password in confirm field
   - Click "Register" button
   - On success: Receive verification email, see confirmation message
   - On validation error: See inline validation messages

2. **Verify Account via Email**
   - Open verification email in email client
   - Click verification link
   - Account becomes active
   - Return to **Login Page** to sign in

3. **Resend Verification Email**
   - If verification email not received
   - Click "Resend verification email" button
   - Check email inbox again

4. **Navigate to Login**
   - Click "Login" link
   - Redirects to **Login Page**

#### Connections to Other Screens

- **After registration** → Email verification, then Login Page
- **Login link** → Login Page

---

## 2. Dashboard (Home Page)

**Route:** `/home`
**Access:** Protected (requires authentication)
**Purpose:** Central dashboard displaying compliance overview, key metrics, and analytics

#### Features

##### Key Metrics Section
| Metric | Description |
|--------|-------------|
| Total Assessments | Count of all assessments in the system |
| Completed Assessments | Count of assessments marked as complete |
| Compliance Frameworks | Number of active frameworks |
| Total Users | Count of registered users |
| Total Policies | Number of policies in the system |
| Total Risks | Count of registered risks |

##### Active Frameworks Section
- Displays all active compliance frameworks with official logos
- Supported frameworks: CRA, ISO 27001, NIS2, NIST CSF, PCI DSS, SOC 2, HIPAA, CCPA, GDPR, CMMC 2.0, DORA, AESCSF, FTC Safeguards, COBIT 2019
- Shows framework name and description

##### Recent Assessment Activity Overview
- Horizontally scrollable carousel of donut charts
- Each chart displays:
  - Assessment name
  - Associated framework
  - Progress percentage (color-coded)

##### Framework Progress Section
- Horizontally scrollable donut charts per framework
- Displays:
  - Framework logo
  - Framework name
  - Number of associated assessments
  - Overall progress percentage
  - Count of completed assessments

##### Assessment Analytics
| Chart | Type | Description |
|-------|------|-------------|
| Assessment Types | Pie Chart | Distribution of assessments by type |
| Assessment Trends | Line Chart | Completed vs in-progress assessments over time |

##### Policy & Risk Analytics
| Chart | Type | Description |
|-------|------|-------------|
| Policy Status | Pie Chart | Distribution by policy status |
| Risk Severity | Pie Chart | Distribution by risk severity level |
| Product Types | Pie Chart | Distribution by product type |

##### User Analytics
| Chart | Type | Description |
|-------|------|-------------|
| User Role Distribution | Pie Chart | Users by role (super_admin, org_admin, org_user) |
| User Status Distribution | Column Chart | Users by status (active, pending, etc.) |

##### Recent Assessment Activity Table
- Paginated table of latest assessments
- Columns: Name, Framework, User, Assessment Type, Progress, Status, Organisation
- Pagination controls with size changer and quick jumper

#### User Actions

1. **View Key Metrics**
   - Observe total counts across all main entities
   - Metrics update in real-time based on system data

2. **Browse Active Frameworks**
   - Scroll through framework cards
   - View framework logos and descriptions

3. **Monitor Assessment Progress**
   - Scroll through assessment progress donut charts
   - Identify assessments needing attention
   - Click on assessment to navigate to **Assessments Page**

4. **Analyze Framework Progress**
   - Scroll through framework progress charts
   - Compare completion rates across frameworks

5. **Review Analytics Charts**
   - Analyze assessment, policy, risk, and user distribution
   - Identify trends in assessment completion

6. **Browse Recent Assessments Table**
   - Page through assessment records
   - Change page size (10, 20, 50, 100)
   - Use quick jumper to navigate to specific page

#### Connections to Other Screens

- **Sidebar Navigation** → All main screens
- **Assessment click** → Assessments Page (with pre-selected assessment)
- **Framework click** → Framework-specific assessments

---

## 3. Assessments

**Route:** `/assessments`
**Access:** Protected (requires authentication)
**Purpose:** Create, manage, and complete compliance assessments with question answering

#### Features

##### Assessment Configuration Section
| Feature | Description |
|---------|-------------|
| Framework Selector | Dropdown to select compliance framework |
| Assessment Type Selector | Dropdown filtered by selected framework |
| Scope Type Selector | Choose between Product or Organization scope |
| Scope Entity Selector | Select specific product or organization |
| Assessment Selector | Dropdown to load existing assessment |
| Assessment Name Input | Text field for naming new assessments |
| Create Assessment Button | Creates new assessment with current configuration |
| Delete Assessment Button | Removes selected assessment (with confirmation) |

##### Question & Answer Interface
| Feature | Description |
|---------|-------------|
| Question Display | Shows questions based on framework and assessment type |
| Answer Input | Text area for entering responses |
| File Upload | Attach evidence files to answers |
| Policy Assignment | Multi-select to link policies to answers |
| Notes Field | Additional comments for each answer |
| Save Answer | Save individual answer (local or to backend) |
| Delete Answer | Remove answer from assessment |

##### Import/Export Features
| Feature | Description |
|---------|-------------|
| CSV Import | Upload answers from CSV file |
| CSV Export | Download answers to CSV format |
| PDF Export | Generate comprehensive assessment report |
| ZIP Download | Download all evidence files |

##### Progress Tracking
- Progress percentage display
- Visual progress bar
- Status indicator (in-progress, completed)
- Framework and assessment type labels

#### User Actions

1. **Create New Assessment**
   - Select framework from dropdown → Assessment types populate
   - Select assessment type
   - (If required) Select scope type → Select scope entity
   - Enter assessment name
   - Click "Create Assessment" button
   - New assessment loads with all questions

2. **Load Existing Assessment**
   - Select framework
   - Select assessment type
   - Use "Load Assessment" dropdown to select existing
   - Assessment questions and answers populate

3. **Answer Questions**
   - Navigate through questions (previous/next or list view)
   - Enter text response in answer field
   - Upload evidence files (drag-and-drop or browse)
   - Assign related policies from multi-select
   - Add notes if needed
   - Click "Save" to persist answer

4. **Manage Evidence Files**
   - Click upload zone or drag files
   - View uploaded files in list
   - Download individual files
   - Delete files from answer

5. **Import Answers from CSV**
   - Click "Import CSV" button
   - Select CSV file with question IDs and answers
   - Review imported data
   - Confirm import

6. **Export Assessment Data**
   - **CSV Export**: Click "Export CSV" → Downloads answer data
   - **PDF Export**: Click "Export PDF" → Opens **PDF generation modal**, generates report
   - **ZIP Download**: Click "Download Files" → Downloads all evidence

7. **Delete Assessment**
   - Select assessment to delete
   - Click "Delete Assessment" button
   - Confirm deletion in modal
   - Assessment and all answers removed

8. **Track Progress**
   - View progress percentage at top
   - Monitor answered vs total questions
   - Status updates automatically as answers are saved

#### Connections to Other Screens

- **Policy Assignment** → Uses policies from **Policies Registration**
- **Scope Selection (Product)** → Uses products from **Product Registration**
- **Framework Selection** → Uses frameworks from **Framework Management**
- **PDF Export** → Generates downloadable report

---

## 4. Product Registration

**Route:** `/product_registration`
**Access:** Protected (requires authentication)
**Purpose:** Manage product catalog and register new products for compliance tracking

#### Features

##### Product Registration Form
| Field | Type | Description |
|-------|------|-------------|
| Product Name | Text Input | Name of the product |
| Product Version | Text Input | Version identifier |
| Justification | Text Area | Reason for product registration |
| License | Text Input | Licensing information |
| Description | Text Area | Detailed product description |
| SBOM | Text Area | Software Bill of Materials (optional) |
| Product Status | Dropdown | Select from predefined statuses |
| Economic Operator | Dropdown | Select organization/vendor |
| Product Type | Dropdown | Category (software, hardware, service) |
| Criticality Level | Dropdown | Importance level with options |

##### Product Management Actions
| Action | Description |
|--------|-------------|
| Save Product | Create new or update existing product |
| Delete Product | Remove product from registry |
| Clear Form | Reset all form fields |

##### Product Display Table
- Paginated table of all products
- Columns: Product Name, Version, Type, Status, Economic Operator, Criticality
- Click row to edit
- Search and filter capabilities
- Sortable columns

##### Export
- PDF Export: Generate products report document

#### User Actions

1. **Register New Product**
   - Fill in product name and version
   - Enter justification and description
   - Add license information
   - Optionally add SBOM details
   - Select product status from dropdown
   - Select economic operator
   - Select product type
   - Select criticality level (if applicable)
   - Click "Save" button
   - Product appears in table

2. **Edit Existing Product**
   - Click on product row in table
   - Form populates with product data
   - Modify desired fields
   - Click "Save" to update
   - Changes reflected in table

3. **Delete Product**
   - Select product from table
   - Click "Delete" button
   - Confirm deletion in modal
   - Product removed from registry

4. **Clear Form**
   - Click "Clear" button
   - All form fields reset
   - Ready to enter new product

5. **Search and Filter Products**
   - Use search box to find products by name
   - Filter by status, type, or criticality
   - Sort columns by clicking headers

6. **Export Products to PDF**
   - Click "Export PDF" button
   - Report generates with all product data
   - PDF downloads automatically

#### Connections to Other Screens

- **Products used in** → Assessments (as scope entities)
- **Economic Operators** → Organizations from User Management
- **Product Types** → Used in Risk Registration

---

## 5. Policies Registration

**Route:** `/policies_registration`
**Access:** Protected (requires authentication)
**Purpose:** Create and manage organizational policies, map them to framework objectives

#### Features

##### Policy Registration Form
| Field | Type | Description |
|-------|------|-------------|
| Policy Title | Text Input | Name of the policy |
| Policy Body | Rich Text Area | Full policy content |
| Policy Status | Dropdown | Active, Draft, Approved, Archived |
| Framework Assignment | Multi-select | Select one or more frameworks |
| Chapter Selection | Dropdown | Chapters within selected framework |
| Subchapter Selection | Dropdown | Subchapters within chapter |
| Objective Assignment | Multi-select | Map policy to framework objectives |
| Company Parameter | Text Input | Organization name |
| Policy File | File Picker | Upload policy documents |

##### Policy Management Actions
| Action | Description |
|--------|-------------|
| Save Policy | Create new or update existing policy |
| Delete Policy | Remove policy |
| Clear Form | Reset all form fields |

##### Policy Display Table
- Paginated table of all policies
- Columns: Title, Status, Frameworks, Chapter, Objectives
- Click row to edit
- Cross-organization warning for super_admin

##### File Management
- Upload policy document files
- Preview uploaded files
- Delete file associations

##### Export
- PDF Export: Generate policies report

#### User Actions

1. **Create New Policy**
   - Enter policy title
   - Write policy body content
   - Select status (Active, Draft, Approved, Archived)
   - Select framework(s) to associate
   - Select chapter from framework
   - Select subchapter if applicable
   - Select objectives to map
   - Enter company parameter
   - Upload policy document file (optional)
   - Click "Save" button

2. **Map Policy to Objectives**
   - Select framework → Chapters populate
   - Select chapter → Subchapters populate
   - Select subchapter → Objectives populate
   - Select one or more objectives
   - Policy becomes linked to compliance objectives

3. **Edit Existing Policy**
   - Click on policy row in table
   - Form populates with policy data
   - Modify desired fields
   - Update objective mappings if needed
   - Click "Save" to update

4. **Delete Policy**
   - Select policy from table
   - Click "Delete" button
   - Confirm deletion
   - Policy removed (note: may affect assessment answers)

5. **Upload Policy Document**
   - Click file picker in form
   - Select document file
   - File uploads and associates with policy
   - Preview file before saving

6. **Export Policies to PDF**
   - Click "Export PDF" button
   - Report generates with all policy data
   - PDF downloads automatically

#### Connections to Other Screens

- **Policies used in** → Assessments (assigned to answers)
- **Frameworks from** → Framework Management
- **Objectives from** → Framework Management (Chapters/Objectives)
- **Visible in** → Objectives Checklist (via Policy Objectives)

---

## 6. Risk Registration

**Route:** `/risk_registration`
**Access:** Protected (requires authentication)
**Purpose:** Register, track, and manage organizational risks

#### Features

##### Risk Registration Form
| Field | Type | Description |
|-------|------|-------------|
| Product Type | Dropdown | Category of affected product |
| Risk Category | AutoComplete | Predefined or custom categories |
| Risk Description | Text Area | Detailed risk description |
| Potential Impact | Text Area | Impact if risk materializes |
| Controls | Text Area | Mitigation controls in place |
| Status | Dropdown | Open, Mitigated, Accepted, Closed |
| Likelihood | Dropdown | Low, Medium, High probability |
| Risk Severity | Dropdown | Critical, High, Medium, Low impact |
| Residual Risk | Dropdown | Risk level after mitigation |
| Scope Type | Selector | Product or Organization |
| Scope Entity | Selector | Specific product or organization |

##### Risk Management Actions
| Action | Description |
|--------|-------------|
| Save Risk | Create new or update existing risk |
| Delete Risk | Remove risk from registry |
| Clear Form | Reset all form fields |

##### Risk Display Table
- Paginated table of all risks
- Columns: Category, Description, Status, Likelihood, Severity, Residual Risk
- Color-coded severity indicators
- Click row to edit
- Sortable and filterable

##### Export
- PDF Export: Generate risks report

#### User Actions

1. **Register New Risk**
   - Select product type from dropdown
   - Enter or select risk category
   - Write detailed risk description
   - Describe potential impact
   - Document existing controls
   - Set status (Open, Mitigated, Accepted, Closed)
   - Set likelihood level
   - Set severity level
   - Set residual risk (after mitigation)
   - Select scope type and entity
   - Click "Save" button

2. **Assess Risk Levels**
   - Evaluate likelihood (Low, Medium, High)
   - Evaluate severity (Critical, High, Medium, Low)
   - Document controls
   - Determine residual risk
   - System may calculate risk score

3. **Update Risk Status**
   - Select risk from table
   - Change status to reflect current state
   - Update controls if new mitigations added
   - Adjust residual risk accordingly
   - Save changes

4. **Delete Risk**
   - Select risk from table
   - Click "Delete" button
   - Confirm deletion
   - Risk removed from registry

5. **Filter and Search Risks**
   - Filter by status, severity, or likelihood
   - Search by category or description
   - Sort by any column

6. **Export Risks to PDF**
   - Click "Export PDF" button
   - Report generates with all risk data
   - PDF downloads automatically

#### Connections to Other Screens

- **Product Types from** → Product Registration
- **Scope Entities** → Products or Organizations
- **Risk analytics visible in** → Dashboard

---

## 7. Framework Management

**Route:** `/framework_management`
**Access:** Protected (super_admin and org_admin only)
**Purpose:** Create, configure, and manage compliance frameworks, questions, and objectives

#### Features

##### Framework Management Section
| Feature | Description |
|---------|-------------|
| Create Framework | Name, description, and scope configuration |
| Framework List | All frameworks with delete option |
| Framework Template Seeding | Pre-populate from standard templates |
| Scope Configuration | Allowed scope types and selection mode |

##### Question Management Section
| Feature | Description |
|---------|-------------|
| Add Question | Text, framework assignment, assessment type, mandatory flag |
| Edit Question | Modify existing question properties |
| Delete Question | Remove question from framework |
| CSV Upload | Batch import questions from CSV file |
| Questions Table | Display all questions with search and filter |

##### Chapter & Objective Management Section
| Feature | Description |
|---------|-------------|
| Create Chapter | Add chapter to framework |
| Create Objective | Title, description, utilities, subchapter, requirements |
| Edit Objective | Modify objective details |
| Delete Objective | Remove objective from chapter |
| Hierarchical View | Chapters and subchapters organization |

#### User Actions

1. **Create New Framework**
   - Enter framework name
   - Enter framework description
   - Configure allowed scope types (Product, Organization, Both)
   - Set scope selection mode
   - Click "Create Framework" button
   - Framework appears in list

2. **Seed Framework from Template**
   - Select framework to populate
   - Select template from dropdown (ISO 27001, NIST, etc.)
   - Click "Seed Template" button
   - Questions and objectives populate automatically

3. **Add Questions to Framework**
   - Enter question text
   - Select target framework(s) using multi-select
   - Select assessment type
   - Toggle mandatory flag if required
   - Click "Add Question" button
   - Question appears in table

4. **Bulk Upload Questions via CSV**
   - Click "Upload CSV" button
   - Select CSV file with question data
   - Format: question_text, framework_id, assessment_type, mandatory
   - Review imported questions
   - Confirm import

5. **Edit Existing Question**
   - Click on question in table
   - Modify question text
   - Change framework associations
   - Update assessment type
   - Toggle mandatory flag
   - Save changes

6. **Create Chapter**
   - Select target framework
   - Enter chapter name
   - Click "Create Chapter" button
   - Chapter appears under framework

7. **Create Objective**
   - Select framework and chapter
   - Enter objective title
   - Enter objective description
   - Add utilities information
   - Select subchapter (if applicable)
   - Enter requirement description
   - Click "Create Objective" button

8. **Manage Objectives**
   - View hierarchical structure by chapter
   - Edit objective details
   - Delete objectives as needed
   - Reorganize by subchapter

9. **Delete Framework**
   - Select framework from list
   - Click delete icon
   - Confirm deletion (warning: deletes all associated data)

#### Connections to Other Screens

- **Frameworks used in** → Assessments, Policies Registration, Objectives Checklist
- **Questions used in** → Assessments
- **Objectives used in** → Policies Registration, Objectives Checklist
- **Templates from** → Settings (template permissions)

---

## 8. Objectives Checklist

**Route:** `/objectives_checklist`
**Access:** Protected (requires authentication)
**Purpose:** Track compliance status of framework objectives with AI-powered suggestions

#### Features

##### Framework Selection
| Feature | Description |
|---------|-------------|
| Framework Selector | Dropdown to select compliance framework |
| Dynamic Loading | Objectives load based on selected framework |

##### Objectives Display
| Column | Description |
|--------|-------------|
| Subchapter | Grouping within chapter |
| Title | Objective name |
| Requirement Description | What is required for compliance |
| Objective Utilities | Supporting information |
| Compliance Status | Current status with selector |
| Evidence/Actions | Related actions and evidence |

##### Compliance Status Options
- Compliant
- Partially Compliant
- Non-Compliant
- Not Applicable

##### AI-Powered Suggestions
| Feature | Description |
|---------|-------------|
| Generate AI Suggestions | Request LLM-powered recommendations |
| Suggestion Display | Shows suggestion text and confidence score |
| Apply Suggestion | Accept and apply AI recommendation |
| Remove Suggestion | Discard suggestion |
| Loading State | Progress indicator during generation |
| Page Leave Warning | Alert when leaving during AI processing |

##### Export
- PDF Export: Generate checklist report with all statuses

#### User Actions

1. **Select Framework**
   - Choose framework from dropdown
   - Objectives load organized by chapter/subchapter
   - Previous statuses retained if previously set

2. **Review Objectives**
   - Scroll through objectives list
   - View requirement descriptions
   - Check utilities for guidance
   - Understand what compliance requires

3. **Update Compliance Status**
   - For each objective, select status from dropdown
   - Choose: Compliant, Partially Compliant, Non-Compliant, Not Applicable
   - Status saves automatically
   - Progress updates in real-time

4. **Generate AI Improvement Suggestions**
   - Click "Generate AI Suggestions" button
   - Wait for LLM processing (loading indicator)
   - View suggestions with confidence scores
   - Note: Do not leave page during processing

5. **Apply AI Suggestion**
   - Review suggestion text
   - Check confidence score
   - Click "Apply" to implement suggestion
   - Objective updates accordingly

6. **Remove AI Suggestion**
   - If suggestion not appropriate
   - Click "Remove" button
   - Suggestion dismissed

7. **Export Checklist to PDF**
   - Click "Export PDF" button
   - Report includes all objectives and current statuses
   - PDF downloads automatically

#### Connections to Other Screens

- **Framework from** → Framework Management
- **Objectives from** → Framework Management
- **Policies linked via** → Policies Registration (Policy Objectives)
- **AI powered by** → llama.cpp (configured in Settings)

---

## 9. Update Password

**Route:** `/update_password`
**Access:** Protected (requires authentication)
**Purpose:** Allow users to change their account password

#### Features

##### Password Update Form
| Field | Description |
|-------|-------------|
| Current User | Read-only display of logged-in user email |
| New Password | Password input field for new password |
| Password Requirements | Guidelines for strong password |

##### Password Requirements Display
- Use strong, unique password
- Mix of letters, numbers, and symbols
- Avoid personal information
- Different from previous passwords

##### Actions
| Action | Description |
|--------|-------------|
| Update Password | Submit button (disabled when empty) |
| Loading State | Progress indicator during update |

#### User Actions

1. **Change Password**
   - View current user email (confirmation of account)
   - Enter new password in input field
   - Review password requirements
   - Click "Update Password" button
   - On success: See success notification
   - On failure: See error message

2. **Password Requirements**
   - Ensure password meets strength requirements
   - Use combination of characters
   - Avoid easily guessable information

#### Connections to Other Screens

- **User authentication** → Login Page (new password used on next login)
- **User data from** → User store (current session)

---

## 10. Admin Area

The Admin Area contains multiple sub-screens accessible only to super_admin and org_admin users.

### 10.1 Settings

**Route:** `/settings`
**Access:** Protected (super_admin only)
**Purpose:** Configure system-wide settings, scanners, integrations, and permissions

#### Features

##### Framework Cloning
| Feature | Description |
|---------|-------------|
| Clonable Frameworks | Multi-select frameworks to clone |
| Target Organization | Destination organization dropdown |
| Custom Framework Name | Name for cloned framework |
| Clone Button | Execute framework cloning |

##### Scanner Access Control
| Feature | Description |
|---------|-------------|
| Scanner Toggle | Enable/disable scanner availability |
| Allowed Domains | Multi-select organizations with scanner access |
| Scanner List | ZAP, Nmap, Semgrep, OSV |

##### SMTP Configuration
| Field | Description |
|-------|-------------|
| SMTP Host | Mail server address |
| SMTP Port | Mail server port |
| SMTP Username | Authentication username |
| SMTP Password | Authentication password |
| From Email | Sender email address |
| Save Settings | Persist SMTP configuration |
| Test Email | Send test email to verify |

##### Framework Template Permissions
| Feature | Description |
|---------|-------------|
| Organization Selector | Select target organization |
| Allowed Templates | Multi-select templates to permit |
| Update Permissions | Save template permissions |

##### Domain Blacklist Management
| Feature | Description |
|---------|-------------|
| Add Domain | Input field for domain name |
| Add Reason | Input field for blacklist reason |
| Add Button | Add domain to blacklist |
| Blacklist Table | View all blacklisted domains |
| Remove Domain | Delete from blacklist |
| CSV Upload | Bulk import blacklisted domains |

##### LLM Configuration
| Feature | Description |
|---------|-------------|
| LLM URL | Custom llama.cpp/LLM endpoint |
| Payload Template | llama.cpp, Mistral, or Custom |
| Custom Payload Editor | JSON configuration for custom LLM |
| Save LLM Settings | Persist LLM configuration |

#### User Actions

1. **Clone Frameworks to Organizations**
   - Select frameworks to clone (multi-select)
   - Select target organization
   - Enter custom name for cloned framework
   - Click "Clone Frameworks"
   - Frameworks replicate to target organization

2. **Configure Scanner Access**
   - Toggle scanner availability on/off
   - Select organizations allowed to use scanners
   - Scanner access applies to: ZAP, Nmap, Semgrep, OSV

3. **Setup SMTP Email**
   - Enter SMTP server details
   - Configure authentication credentials
   - Set sender email address
   - Save settings
   - Test configuration by sending test email

4. **Manage Template Permissions**
   - Select organization
   - Choose which framework templates they can access
   - Update permissions

5. **Manage Domain Blacklist**
   - Add domains to blacklist with reasons
   - View all blacklisted domains in table
   - Remove domains as needed
   - Bulk upload via CSV file

6. **Configure LLM Integration**
   - Enter custom LLM endpoint URL
   - Select payload template or create custom
   - Save LLM settings
   - Used by: Objectives Checklist AI, Correlations AI, Scanner analysis

#### Connections to Other Screens

- **Scanner access affects** → ZAP, Nmap, Semgrep, OSV scanner pages
- **Framework templates used in** → Framework Management
- **SMTP used for** → Password reset, verification emails
- **LLM used by** → Objectives Checklist, Correlations, Scanner analysis

---

### 10.2 Correlations

**Route:** `/correlations`
**Access:** Protected (super_admin and org_admin only)
**Purpose:** Correlate questions across different frameworks using AI

#### Features

##### Framework & Assessment Selection
| Feature | Description |
|---------|-------------|
| Framework A Selector | First framework dropdown |
| Assessment Type A | Assessment type for Framework A |
| Questions A List | Questions from Framework A |
| Framework B Selector | Second framework dropdown |
| Assessment Type B | Assessment type for Framework B |
| Questions B List | Questions from Framework B |
| Scope Selection | Product or Organization scope |

##### Correlation Operations
| Action | Description |
|--------|-------------|
| Correlate Questions | Create correlation between selected questions |
| Check Correlation | Verify if correlation exists |
| Remove Correlation | Delete existing correlation |
| Correlation Status | Display if already correlated |

##### AI-Powered Suggestions
| Feature | Description |
|---------|-------------|
| Generate AI Suggestions | LLM-powered correlation recommendations |
| Apply Suggestion | Accept AI recommendation |
| Remove Suggestion | Discard suggestion |
| Confidence Score | AI confidence level display |

##### All Correlations View
| Feature | Description |
|---------|-------------|
| Correlations Table | All correlations with search |
| Bulk Remove | Remove all correlations |
| Search | Find specific correlations |

##### LLM Optimization Settings
| Setting | Description |
|---------|-------------|
| Max Questions Per Framework | Limit for AI processing |
| LLM Timeout Seconds | AI request timeout |
| Min Confidence Threshold | Minimum score to show suggestions |
| Max Correlations | Limit total correlations |

##### Correlation Audit
| Feature | Description |
|---------|-------------|
| Run Audit | Check correlation integrity |
| Audit Results | Display findings |
| Auto-Fix | Fix issues found |

#### User Actions

1. **Create Manual Correlation**
   - Select Framework A → Select assessment type → Select question
   - Select Framework B → Select assessment type → Select question
   - Click "Correlate Questions"
   - Correlation created between questions

2. **Generate AI Correlation Suggestions**
   - Select frameworks and assessment types
   - Click "Generate AI Suggestions"
   - Review suggestions with confidence scores
   - Apply useful suggestions
   - Remove irrelevant suggestions

3. **View All Correlations**
   - Open correlations table
   - Search for specific correlations
   - Review Framework A ↔ Framework B mappings

4. **Remove Correlations**
   - Select correlation from table
   - Click remove action
   - Or use bulk remove for all correlations

5. **Configure LLM Optimization**
   - Set maximum questions per framework
   - Configure timeout duration
   - Set minimum confidence threshold
   - Set maximum correlations limit
   - Save optimization settings

6. **Run Correlation Audit**
   - Click "Run Audit" button
   - Review audit results
   - Use "Auto-Fix" to resolve issues
   - Verify data integrity

#### Connections to Other Screens

- **Questions from** → Framework Management
- **Frameworks from** → Framework Management
- **AI powered by** → LLM configured in Settings
- **Correlations used in** → Assessments (answer correlation suggestions)

---

### 10.3 Organizations (User Management)

**Route:** `/user_management`
**Access:** Protected (super_admin and org_admin only)
**Purpose:** Manage organizations, users, logos, and history cleanup

#### Features

##### Organization Management (super_admin only)
| Feature | Description |
|---------|-------------|
| Create Organization | Name and domain inputs |
| Organization List | All organizations with delete option |
| Logo Upload | Upload organization logo |
| Logo Delete | Remove organization logo |
| Default Logo | Fallback when no logo set |

##### User Management
| Feature | Description |
|---------|-------------|
| Create User | Email, password, role, organization |
| Edit User | Modify user details |
| Delete User | Remove user from organization |
| User List Table | All users with role and organization |

##### User Form Fields
| Field | Description |
|-------|-------------|
| Email | User email address |
| Password | Initial password (required for creation) |
| Role | super_admin, org_admin, org_user |
| Organization | Assigned organization |

##### History Cleanup Configuration
| Setting | Description |
|---------|-------------|
| Enable/Disable | Toggle history cleanup |
| Retention Days | Days to keep history (default 30) |
| Cleanup Interval Hours | Hours between cleanup runs (default 24) |
| Manual Cleanup | Run cleanup immediately |
| Organization Selector | Select organization for cleanup |

#### User Actions

1. **Create Organization** (super_admin)
   - Enter organization name
   - Enter organization domain
   - Click "Create Organization"
   - Organization appears in list

2. **Upload Organization Logo**
   - Select organization
   - Click upload button
   - Select logo image file
   - Logo displays in header for organization users

3. **Create New User**
   - Enter user email
   - Enter initial password
   - Select role (super_admin, org_admin, org_user)
   - Select organization
   - Click "Create User"
   - User added with pending status (requires approval)

4. **Edit Existing User**
   - Select user from table
   - Modify email, role, or organization
   - Save changes

5. **Delete User**
   - Select user from table
   - Click "Delete" button
   - Confirm deletion
   - User removed from system

6. **Configure History Cleanup**
   - Enable history cleanup toggle
   - Set retention period in days
   - Set cleanup interval in hours
   - Save configuration

7. **Run Manual History Cleanup**
   - Select target organization
   - Click "Run Cleanup" button
   - Old history entries deleted per retention policy

#### Connections to Other Screens

- **Organizations used in** → All entity screens (filtering)
- **Users appear in** → Approvals, Admin statistics
- **Logo displays in** → Header bar across all screens
- **Cleanup affects** → History page data

---

### 10.4 Approvals

**Route:** `/admin`
**Access:** Protected (super_admin and org_admin only)
**Purpose:** Manage user approvals, monitor activity, and view analytics

#### Features

##### User Management Section
| Feature | Description |
|---------|-------------|
| User List Table | All users with status and role |
| Status Filter | All, Pending, Approved, Rejected, Active, Inactive |
| Role Filter | Filter by user role |
| Organization Filter | Filter by organization |
| Email Search | Search users by email |
| Status Update | Dropdown to change user status |

##### Online Users Monitoring
| Feature | Description |
|---------|-------------|
| Online Users List | Currently active users |
| Polling Interval | Updates every 20 seconds |
| User Count | Total active user count |

##### User Sessions & Activity
| Feature | Description |
|---------|-------------|
| Sessions Table | Active user sessions |
| Last Activity | Timestamp of last action |
| Session Duration | How long user has been active |

##### Analytics & Statistics
| Chart/Feature | Description |
|---------------|-------------|
| Visits Per Email | Chart showing user visit frequency |
| Total Visits | Aggregate visit count |
| PDF Downloads Per Type | Chart of report downloads |
| Date Range Filter | Filter analytics by date |
| Download Analytics | Export analytics data |

#### User Actions

1. **Filter Users**
   - Select status filter (Pending, Approved, etc.)
   - Select role filter
   - Select organization filter
   - Search by email
   - Table updates with filtered results

2. **Approve/Reject Users**
   - Find user in list
   - Use status dropdown to change status
   - Approve → User can access system
   - Reject → User denied access

3. **Monitor Online Users**
   - View list of currently active users
   - List auto-refreshes every 20 seconds
   - See total count of online users

4. **View User Sessions**
   - Review active sessions
   - See last activity timestamps
   - Monitor session durations

5. **Analyze User Activity**
   - View visits per user chart
   - Check total visit counts
   - Review PDF download statistics
   - Filter by date range

6. **Export Analytics**
   - Click "Download Analytics"
   - Export data for further analysis

#### Connections to Other Screens

- **Users from** → Organizations (User Management)
- **Analytics include data from** → All main screens (assessments, policies, etc.)
- **User status affects** → Login access throughout system

---

### 10.5 History

**Route:** `/history`
**Access:** Protected (super_admin and org_admin only)
**Purpose:** Track and audit system activity history

#### Features

##### History Entry Display
| Column | Description |
|--------|-------------|
| User | User who performed action |
| Action | Type of action (Create, Update, Delete, Export) |
| Entity Type | Type of entity affected |
| Timestamp | When action occurred |
| Details | Additional action details |

##### Filtering Options
| Filter | Description |
|--------|-------------|
| Entity Type | All, User, Assessment, Policy, Risk, Product |
| Action | All, Create, Update, Delete, Export |
| Date Range | RangePicker for date filtering |
| Search | Search by user email or details |

##### History Management
| Action | Description |
|--------|-------------|
| Delete Entry | Remove individual history entry |
| Clear All | Clear all history for organization |
| Organization Selector | Select organization for management |
| Refresh | Reload history with latest entries |

#### User Actions

1. **View System History**
   - Browse paginated history table
   - See who performed what actions and when
   - Review action details

2. **Filter History**
   - Select entity type (Assessment, Policy, Risk, etc.)
   - Select action type (Create, Update, Delete, Export)
   - Set date range using picker
   - Search by user email or details
   - Results update based on filters

3. **Delete Individual Entry**
   - Find entry in table
   - Click delete action
   - Confirm deletion
   - Entry removed from history

4. **Clear All History**
   - Select organization
   - Click "Clear All" button
   - Confirm action
   - All history for organization deleted

5. **Export History Report**
   - Click export button
   - History data downloaded
   - Use for audit purposes

6. **Refresh History**
   - Click "Refresh" button
   - Latest entries load
   - See most recent activity

#### Connections to Other Screens

- **Tracks activity from** → All main screens
- **Affected by** → History cleanup configuration in Organizations
- **User actions across** → Assessments, Policies, Risks, Products, Users

---

## 11. Scanners

Scanner pages are available to users from organizations with scanner access enabled (configured in Settings).

### 11.1 Web App Scanner (ZAP)

**Route:** `/zap`
**Access:** Protected (requires scanner domain access)
**Purpose:** Perform OWASP ZAP web application security scanning

#### Features

##### Scan Configuration
| Field | Description |
|-------|-------------|
| Target URL | Website URL to scan |
| Scan Type | Spider, Active, Full, or API scan |
| Start Scan | Launch scan with loading state |

##### Scan Types Explained
| Type | Description |
|------|-------------|
| Spider Scan | Discovers content and URLs |
| Active Scan | Tests for vulnerabilities |
| Full Scan | Spider + Active combined |
| API Scan | API-specific security testing |

##### Scan Control
| Action | Description |
|--------|-------------|
| Emergency Stop | Halt ongoing scan |
| Clear Results | Reset scan results |
| Polling Status | Real-time progress updates |

##### Results Display
| Feature | Description |
|---------|-------------|
| Alerts Table | Findings with risk level, confidence |
| Severity Coding | Red (High), Orange (Medium), Yellow (Low) |
| Expandable Details | Evidence and solutions per finding |
| Summary Statistics | Total, High, Medium, Low counts |

##### Progress Visualization
- Progress bar showing scan completion
- Status display (Scanning, Completed, etc.)
- Real-time updates

##### Export & History
| Feature | Description |
|---------|-------------|
| Export PDF | Generate scan report |
| History Modal | View previous scans |

#### User Actions

1. **Configure and Start Scan**
   - Enter target URL (full URL with protocol)
   - Select scan type based on needs
   - Click "Start Scan" button
   - Wait for scan to begin

2. **Monitor Scan Progress**
   - Watch progress bar update
   - View status indicator
   - See real-time alert count updates

3. **Review Scan Results**
   - View alerts in table format
   - Check severity levels (color-coded)
   - Expand alerts for details
   - Review evidence and solutions

4. **Stop Scan** (if needed)
   - Click "Emergency Stop" button
   - Scan halts immediately
   - Partial results available

5. **Export Scan Report**
   - Click "Export PDF" button
   - Report generates with all findings
   - PDF downloads automatically

6. **View Scan History**
   - Open history modal
   - Browse previous scans
   - View date, target, type
   - Load historical results

7. **Clear Results**
   - Click "Clear Results" button
   - Results reset
   - Ready for new scan

#### Connections to Other Screens

- **Scanner access from** → Settings (scanner domain configuration)
- **LLM analysis from** → LLM configured in Settings
- **Results can inform** → Risk Registration, Assessments

---

### 11.2 Network Scanner (Nmap)

**Route:** `/nmap`
**Access:** Protected (requires scanner domain access)
**Purpose:** Perform network reconnaissance and port scanning

#### Features

##### Scan Configuration
| Field | Description |
|-------|-------------|
| Target | Hostname, IP, or IP range |
| Ports | Specific ports (for port scan) |
| Scan Type | Various scan types |
| LLM Analysis | Toggle AI analysis of results |

##### Scan Types Explained
| Type | Description |
|------|-------------|
| Basic Scan | Standard host discovery |
| Port Scan | Scan specific ports |
| All Ports | Scan all 65535 ports |
| Aggressive | OS detection, version, scripts |
| OS Scan | Operating system detection |
| Network Scan | Network segment discovery |
| Stealth Scan | SYN scan (less detectable) |
| No Ping | Skip ping, scan directly |
| Fast Scan | Top 100 ports only |

##### Scan Execution
| Action | Description |
|--------|-------------|
| Start Scan | Launch network scan |
| Clear Results | Reset scan output |

##### Results Display
| Format | Description |
|--------|-------------|
| Raw Results | Terminal-style output |
| Structured Data | Parsed table format |
| Host Information | Discovered hosts |
| Port Status | Open, closed, filtered |
| Service Detection | Services and versions |

##### Export & History
| Feature | Description |
|---------|-------------|
| Export PDF | Generate network report |
| History Modal | Previous network scans |

#### User Actions

1. **Configure Network Scan**
   - Enter target (hostname, IP, or range)
   - Enter specific ports if needed
   - Select appropriate scan type
   - Enable LLM analysis for insights (optional)

2. **Execute Scan**
   - Click "Start Scan" button
   - Wait for scan completion
   - View progress indicator

3. **Review Results**
   - View raw terminal output
   - Review structured data in table
   - Check discovered hosts
   - Review open ports and services

4. **Analyze with AI** (if enabled)
   - LLM processes scan results
   - View AI-generated insights
   - Understand security implications

5. **Export Network Report**
   - Click "Export PDF" button
   - Report with all findings generates
   - PDF downloads

6. **View Scan History**
   - Open history modal
   - Browse previous network scans
   - Compare historical results

#### Connections to Other Screens

- **Scanner access from** → Settings
- **LLM analysis from** → LLM configuration in Settings
- **Results can inform** → Risk Registration, Assessments

---

### 11.3 Code Analysis (Semgrep)

**Route:** `/semgrep`
**Access:** Protected (requires scanner domain access)
**Purpose:** Perform static code analysis and vulnerability detection

#### Features

##### Scan Configuration
| Feature | Description |
|---------|-------------|
| File Upload | Drag-drop or browse for code archive |
| Configuration | Auto or Custom rule selection |
| LLM Analysis | Toggle AI insights |

##### Supported Uploads
- ZIP archives
- TAR archives
- Code directories (compressed)

##### Scan Execution
| Action | Description |
|--------|-------------|
| Start Scan | Launch code analysis |
| Clear Results | Reset scan output |
| Loading State | Progress indicator |

##### Results Display
| Column | Description |
|--------|-------------|
| Rule ID | Semgrep rule that triggered |
| Severity | Issue severity level |
| File | Affected file path |
| Line | Line number of issue |
| Issue Description | What the problem is |
| Code Snippet | Preview of affected code |
| Remediation | How to fix the issue |

##### Summary Statistics
- Total findings count
- By severity level breakdown
- By rule category grouping

##### Export & History
| Feature | Description |
|---------|-------------|
| Export PDF | Generate code analysis report |
| History Modal | Previous code scans |

#### User Actions

1. **Upload Code for Analysis**
   - Drag and drop code archive to upload zone
   - Or click to browse and select file
   - Supported: ZIP, TAR, compressed directories

2. **Configure Scan**
   - Select configuration (Auto or Custom)
   - Enable LLM analysis for deeper insights (optional)

3. **Execute Code Scan**
   - Click "Start Scan" button
   - Wait for analysis completion
   - View progress indicator

4. **Review Findings**
   - Browse findings table
   - Check severity levels
   - Expand for code snippets
   - Read remediation suggestions

5. **Analyze with AI** (if enabled)
   - LLM processes code findings
   - Get contextual recommendations
   - Understand security implications

6. **Export Code Report**
   - Click "Export PDF" button
   - Comprehensive report generates
   - PDF downloads

7. **View Scan History**
   - Open history modal
   - Review previous code scans
   - Compare findings over time

#### Connections to Other Screens

- **Scanner access from** → Settings
- **LLM analysis from** → LLM configuration in Settings
- **Results can inform** → Risk Registration, Assessments

---

### 11.4 Dependency Analysis (OSV)

**Route:** `/osv`
**Access:** Protected (requires scanner domain access)
**Purpose:** Detect vulnerable dependencies and supply chain risks

#### Features

##### Scan Configuration
| Feature | Description |
|---------|-------------|
| File Upload | Upload dependency lock file |
| LLM Analysis | Toggle AI vulnerability insights |

##### Supported Lock Files
- package-lock.json (npm)
- requirements.txt (Python)
- go.mod (Go)
- Gemfile.lock (Ruby)
- Cargo.lock (Rust)
- pom.xml (Maven)
- And more...

##### Scan Execution
| Action | Description |
|--------|-------------|
| Start Scan | Launch dependency analysis |
| Clear Results | Reset results |
| Loading State | Progress during scan |

##### Results Display
| Column | Description |
|--------|-------------|
| Package | Affected package name |
| Version | Installed version |
| Vulnerability ID | CVE or OSV identifier |
| Severity | Vulnerability severity |
| Status | Fixed/Unfixed status |
| Affected Versions | Version range affected |
| Fix Recommendation | How to remediate |
| References | CVE links, advisories |

##### Summary Statistics
- Total vulnerabilities
- By severity breakdown
- Packages affected count

##### Export & History
| Feature | Description |
|---------|-------------|
| Export PDF | Generate dependency report |
| History Modal | Previous dependency scans |

#### User Actions

1. **Upload Dependency File**
   - Select lock file from project
   - Upload package-lock.json, requirements.txt, etc.
   - File processes and prepares for scan

2. **Enable AI Analysis** (optional)
   - Toggle LLM analysis switch
   - Get contextual vulnerability insights

3. **Execute Dependency Scan**
   - Click "Start Scan" button
   - Wait for OSV database check
   - View progress indicator

4. **Review Vulnerabilities**
   - Browse vulnerabilities table
   - Check severity levels
   - Review affected versions
   - Read fix recommendations
   - Follow reference links for details

5. **Analyze with AI** (if enabled)
   - LLM provides context on vulnerabilities
   - Understand real-world impact
   - Get prioritization suggestions

6. **Export Dependency Report**
   - Click "Export PDF" button
   - Report with all vulnerabilities generates
   - PDF downloads

7. **View Scan History**
   - Open history modal
   - Review previous dependency scans
   - Track vulnerability trends

#### Connections to Other Screens

- **Scanner access from** → Settings
- **LLM analysis from** → LLM configuration in Settings
- **Results can inform** → Risk Registration, Product Registration (SBOM)
- **Related to** → Product Registration (dependencies are part of products)

---

## Navigation Summary

### Main Menu Structure

```
Dashboard (Home)
├── Frameworks* (admin only)
├── Product Registration
├── Policies Registration
├── Risk Registration
├── Assessments
├── Objectives Checklist
├── Update Password
│
├── Admin Area* (admin only)
│   ├── Settings* (super_admin only)
│   ├── Correlations
│   ├── Organizations
│   ├── Approvals
│   └── History
│
└── Scanners* (if scanner access enabled)
    ├── Web App Scanner (ZAP)
    ├── Network Scanner (Nmap)
    ├── Code Analysis (Semgrep)
    └── Dependency Analysis (OSV)
```

*Items marked with asterisk have restricted access based on user role or organization configuration.

### Role-Based Access Summary

| Screen | org_user | org_admin | super_admin |
|--------|----------|-----------|-------------|
| Dashboard | Yes | Yes | Yes |
| Assessments | Yes | Yes | Yes |
| Product Registration | Yes | Yes | Yes |
| Policies Registration | Yes | Yes | Yes |
| Risk Registration | Yes | Yes | Yes |
| Objectives Checklist | Yes | Yes | Yes |
| Update Password | Yes | Yes | Yes |
| Framework Management | No | Yes | Yes |
| Correlations | No | Yes | Yes |
| Organizations | No | Yes | Yes |
| Approvals | No | Yes | Yes |
| History | No | Yes | Yes |
| Settings | No | No | Yes |
| Scanners | Domain-based | Domain-based | Domain-based |

---

## Document Version

**Version:** 1.0
**Last Updated:** December 2024
**Application:** CyberBridge Cybersecurity Compliance Assessment Platform
