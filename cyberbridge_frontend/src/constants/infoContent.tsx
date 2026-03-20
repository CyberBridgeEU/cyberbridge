import React from 'react';

// Dashboard page info content
export const DashboardInfo = (
    <div>
        <p><strong>Dashboard Overview</strong></p>
        <p>The Dashboard provides a comprehensive view of your cybersecurity compliance status:</p>
        <ul>
            <li><strong>Total Assessments:</strong> Shows the total number of compliance assessments in your organization</li>
            <li><strong>Completed Assessments:</strong> Displays how many assessments have been completed</li>
            <li><strong>Compliance Frameworks:</strong> Number of active compliance frameworks in your organization</li>
            <li><strong>Assessment Status Chart:</strong> Visual pie chart showing the distribution of completed vs in-progress assessments</li>
            <li><strong>Frameworks Section:</strong> Lists all available compliance frameworks with descriptions</li>
            <li><strong>Assessment History:</strong> Table showing all assessments with their current status and progress</li>
        </ul>
        <p><strong>Navigation:</strong> Use the menu on the left to access different sections of the application.</p>
    </div>
);

// Framework Management Page info content
export const AddFrameworkFromTemplateInfo = (
    <div>
        <p><strong>Add Framework from Template</strong></p>
        <p>This section allows you to quickly set up compliance frameworks from pre-defined templates:</p>
        <ul>
            <li><strong>Available Templates:</strong>
                <ul>
                    <li><strong>CRA:</strong> Cyber Resilience Act compliance framework</li>
                    <li><strong>ISO27001:</strong> Information Security Management System framework</li>
                    <li><strong>NIS2:</strong> Network and Information Systems Security framework</li>
                </ul>
            </li>
            <li><strong>How to Use:</strong>
                <ol>
                    <li>Select a template from the dropdown menu</li>
                    <li>Click the "Seed" button to create the framework</li>
                    <li>The system will automatically create the framework with all associated chapters, objectives, and questions</li>
                </ol>
            </li>
        </ul>
        <p><strong>Note:</strong> This creates a complete framework structure for your organization from scratch, independent of other organizations.</p>
    </div>
);

export const ManageSourcesInfo = (
    <div>
        <p><strong>Manage Sources (Create Custom Frameworks)</strong></p>
        <p>This section allows you to create and manage custom compliance frameworks:</p>
        <ul>
            <li><strong>Create New Framework:</strong>
                <ol>
                    <li>Enter a unique framework name</li>
                    <li>Add an optional description</li>
                    <li>Click "Create Framework" to add it to your organization</li>
                </ol>
            </li>
            <li><strong>Delete Framework:</strong>
                <ol>
                    <li>Select the framework(s) you want to delete from the dropdown</li>
                    <li>Click "Delete Selected Frameworks"</li>
                    <li>Confirm the deletion in the popup dialog</li>
                </ol>
            </li>
        </ul>
        <p><strong>Important:</strong> Framework names must be unique within your organization. Deleting a framework will also remove all associated data including assessments, answers, and evidence.</p>
    </div>
);

export const ManageChaptersObjectivesInfo = (
    <div>
        <p><strong>Manage Chapters/Objectives</strong></p>
        <p>Organize your compliance framework by creating chapters and objectives:</p>
        <ul>
            <li><strong>Create Chapter:</strong>
                <ol>
                    <li>Select a framework from the dropdown</li>
                    <li>Enter a chapter name</li>
                    <li>Click "Add New Chapter"</li>
                </ol>
            </li>
            <li><strong>Create Objective:</strong>
                <ol>
                    <li>Select a framework and chapter</li>
                    <li>Enter the objective title and requirement description</li>
                    <li>Add optional utilities information</li>
                    <li>Click "Add New Objective"</li>
                </ol>
            </li>
            <li><strong>Delete Chapter:</strong>
                <ol>
                    <li>Select a framework and chapter</li>
                    <li>Click "Delete Selected Chapter"</li>
                    <li>Confirm the deletion</li>
                </ol>
            </li>
        </ul>
        <p><strong>Note:</strong> Chapters help organize objectives logically. Deleting a chapter will also delete all objectives within it.</p>
    </div>
);

export const EditObjectivesInfo = (
    <div>
        <p><strong>Edit Objectives</strong></p>
        <p>View and manage objectives within selected chapters:</p>
        <ul>
            <li><strong>View Objectives:</strong> The table shows all objectives for the selected chapter including title, description, and compliance status</li>
            <li><strong>Compliance Status:</strong> Each objective can have different compliance statuses:
                <ul>
                    <li>Not Assessed</li>
                    <li>Not Compliant</li>
                    <li>Partially Compliant</li>
                    <li>In Review</li>
                    <li>Compliant</li>
                    <li>Not Applicable</li>
                </ul>
            </li>
            <li><strong>Actions:</strong> Use the action buttons in each row to edit or delete specific objectives</li>
        </ul>
        <p><strong>Tip:</strong> Select a framework and chapter from the dropdowns above to view objectives in this table.</p>
    </div>
);

export const AddQuestionsInfo = (
    <div>
        <p><strong>Add Questions</strong></p>
        <p>Create assessment questions for your compliance frameworks:</p>
        <ul>
            <li><strong>Question Types:</strong>
                <ul>
                    <li><strong>Conformity:</strong> Questions for conformity assessments</li>
                    <li><strong>Audit:</strong> Questions for audit assessments</li>
                </ul>
            </li>
            <li><strong>How to Add:</strong>
                <ol>
                    <li>Select the assessment type (Conformity or Audit)</li>
                    <li>Enter your question text</li>
                    <li>Select one or more frameworks to associate with this question</li>
                    <li>Click "Add Question" to save</li>
                </ol>
            </li>
            <li><strong>Bulk Upload:</strong> You can also upload questions from a CSV file using the upload functionality</li>
        </ul>
        <p><strong>Note:</strong> Questions can be associated with multiple frameworks and will be available for assessments in those frameworks.</p>
    </div>
);

export const EditQuestionsInfo = (
    <div>
        <p><strong>Edit Questions</strong></p>
        <p>View and manage existing questions in your frameworks:</p>
        <ul>
            <li><strong>Question Table:</strong> Shows all questions associated with your frameworks including:
                <ul>
                    <li>Framework name</li>
                    <li>Question text</li>
                    <li>Assessment type</li>
                    <li>Mandatory status</li>
                </ul>
            </li>
            <li><strong>Actions:</strong>
                <ul>
                    <li><strong>Select Row:</strong> Click on a row to view question details in the form above</li>
                    <li><strong>Toggle Mandatory:</strong> Use the toggle button to make questions mandatory or optional</li>
                    <li><strong>Delete Question:</strong> Remove questions that are no longer needed</li>
                </ul>
            </li>
        </ul>
        <p><strong>Tip:</strong> Use the search and filter features in the table to quickly find specific questions.</p>
    </div>
);

// Policy Registration Page info content
export const PoliciesInfo = (
    <div>
        <p><strong>Policy Registration</strong></p>
        <p>Manage cybersecurity policies and link them to compliance objectives:</p>
        <ul>
            <li><strong>Policy Creation:</strong>
                <ol>
                    <li>Enter policy name and description</li>
                    <li>Set policy status (Draft, Review, Ready for Approval, Approved)</li>
                    <li>Associate with relevant frameworks</li>
                    <li>Link to specific objectives</li>
                    <li>Upload policy documents</li>
                </ol>
            </li>
            <li><strong>Policy Statuses:</strong>
                <ul>
                    <li><strong>Draft:</strong> Initial policy creation</li>
                    <li><strong>Review:</strong> Under review process</li>
                    <li><strong>Ready for Approval:</strong> Pending final approval</li>
                    <li><strong>Approved:</strong> Active policy</li>
                </ul>
            </li>
            <li><strong>Linking:</strong> Policies can be linked to specific compliance objectives to track coverage</li>
        </ul>
    </div>
);

// Risk Registration Page info content
export const RisksInfo = (
    <div>
        <p><strong>Risk Registration/Assessment</strong></p>
        <p>Identify, assess, and manage cybersecurity risks:</p>
        <ul>
            <li><strong>Risk Assessment:</strong>
                <ol>
                    <li>Enter risk name and description</li>
                    <li>Select risk category (e.g., Vulnerabilities, Access Control, etc.)</li>
                    <li>Assess likelihood and impact severity</li>
                    <li>Determine residual risk level</li>
                    <li>Set risk treatment status</li>
                </ol>
            </li>
            <li><strong>Severity Levels:</strong>
                <ul>
                    <li><strong>Low:</strong> Minimal impact</li>
                    <li><strong>Medium:</strong> Moderate impact</li>
                    <li><strong>High:</strong> Significant impact</li>
                    <li><strong>Critical:</strong> Severe impact</li>
                </ul>
            </li>
            <li><strong>Treatment Options:</strong> Reduce, Avoid, Transfer, Share, Accept, or Remediated</li>
        </ul>
    </div>
);

export const RiskAssessmentInfo = (
    <div>
        <p><strong>Risk Assessment (5x5 Matrix)</strong></p>
        <p>Perform quantitative risk assessments using the ISO 27001 5x5 risk matrix methodology:</p>
        <ul>
            <li><strong>Tab 1 - Assessment:</strong>
                <ol>
                    <li>Select or create a new assessment for the risk</li>
                    <li>Set Impact (1-5) and Likelihood (1-5) scores for Inherent, Current, and Target risk</li>
                    <li>Scores are automatically computed (Impact x Likelihood = Risk Score 1-25)</li>
                    <li>Complete the Impact Loss Analysis (Health, Financial, Service, Legal, Reputation)</li>
                </ol>
            </li>
            <li><strong>Tab 2 - Controls & Connections:</strong>
                <ul>
                    <li>Link assets, controls, and objectives to the risk</li>
                    <li>Use the connection boards to manage relationships</li>
                </ul>
            </li>
            <li><strong>Tab 3 - Treatment:</strong>
                <ol>
                    <li>Set the Residual Risk score (after treatment actions)</li>
                    <li>Add treatment action items with due dates and owners</li>
                    <li>Mark the assessment as Completed when done</li>
                </ol>
            </li>
        </ul>
        <p><strong>Score Ranges:</strong> 1-4 = Low, 5-10 = Medium, 12-16 = High, 20-25 = Critical</p>
        <p><strong>Note:</strong> Scores auto-sync back to the Risk Register's severity, likelihood, and residual risk fields.</p>
    </div>
);

// Settings Page info content
export const SettingsInfo = (
    <div>
        <p><strong>Settings (Super Admin Only)</strong></p>
        <p>Administrative functions for super administrators:</p>
        <ul>
            <li><strong>Clone Frameworks:</strong>
                <ol>
                    <li>Select frameworks from other organizations</li>
                    <li>Choose target organization</li>
                    <li>Optionally provide custom framework name</li>
                    <li>Click "Clone Selected Frameworks"</li>
                </ol>
            </li>
        </ul>
        <p><strong>Note:</strong> This feature allows super admins to share best practices and standardize frameworks across organizations.</p>
    </div>
);

export const CloneFrameworksInfo = (
    <div>
        <p><strong>Clone Frameworks from Other Organizations</strong></p>
        <p>Copy proven frameworks from other organizations to your target organization:</p>
        <ul>
            <li><strong>How to Clone:</strong>
                <ol>
                    <li>Select the framework(s) you want to clone</li>
                    <li>Choose the target organization</li>
                    <li>Optionally provide a custom name for the cloned framework</li>
                    <li>Click "Clone Selected Frameworks"</li>
                </ol>
            </li>
            <li><strong>What Gets Cloned:</strong>
                <ul>
                    <li>Framework structure and metadata</li>
                    <li>All chapters and objectives</li>
                    <li>Associated questions</li>
                    <li>Compliance requirements</li>
                </ul>
            </li>
            <li><strong>Benefits:</strong>
                <ul>
                    <li>Share best practices across organizations</li>
                    <li>Standardize compliance approaches</li>
                    <li>Save time on framework setup</li>
                </ul>
            </li>
        </ul>
        <p><strong>Note:</strong> Only super administrators can access this feature.</p>
    </div>
);

// Security Tools info content
export const NetworkScannerInfo = (
    <div>
        <p><strong>Network Scanner</strong></p>
        <p>Perform network security assessments and port scanning:</p>
        <ul>
            <li><strong>Target Specification:</strong>
                <ul>
                    <li>Enter IP addresses, ranges, or hostnames</li>
                    <li>Examples: 192.168.1.1, 192.168.1.0/24, example.com</li>
                </ul>
            </li>
            <li><strong>Scan Types:</strong>
                <ul>
                    <li><strong>TCP SYN Scan:</strong> Stealthy port scanning</li>
                    <li><strong>UDP Scan:</strong> Scan UDP ports</li>
                    <li><strong>Service Detection:</strong> Identify services and versions</li>
                    <li><strong>OS Detection:</strong> Determine operating system</li>
                </ul>
            </li>
            <li><strong>Results:</strong> View discovered hosts, open ports, services, and potential vulnerabilities</li>
        </ul>
        <p><strong>Caution:</strong> Only scan networks you own or have explicit permission to test.</p>
    </div>
);

export const WebAppScannerInfo = (
    <div>
        <p><strong>Web Application Scanner</strong></p>
        <p>Automated security testing for web applications:</p>
        <ul>
            <li><strong>Quick Start:</strong>
                <ol>
                    <li>Enter the target URL (e.g., http://example.com)</li>
                    <li>Select scan intensity (Low, Medium, High)</li>
                    <li>Click "Start Quick Scan"</li>
                </ol>
            </li>
            <li><strong>Scan Features:</strong>
                <ul>
                    <li>OWASP Top 10 vulnerability detection</li>
                    <li>SQL injection testing</li>
                    <li>Cross-site scripting (XSS) detection</li>
                    <li>Authentication bypass attempts</li>
                </ul>
            </li>
            <li><strong>Results:</strong> Detailed vulnerability reports with severity ratings and remediation advice</li>
        </ul>
        <p><strong>Important:</strong> Only scan applications you own or have authorization to test.</p>
    </div>
);

export const CodeAnalysisInfo = (
    <div>
        <p><strong>Code Analysis</strong></p>
        <p>Static analysis security testing for source code:</p>
        <ul>
            <li><strong>Language Support:</strong>
                <ul>
                    <li>JavaScript/TypeScript, Python, Java, C/C++</li>
                    <li>Go, Ruby, PHP, and more</li>
                </ul>
            </li>
            <li><strong>Upload Process:</strong>
                <ol>
                    <li>Select a ZIP file containing your source code</li>
                    <li>Choose the primary programming language</li>
                    <li>Click "Upload and Scan Code"</li>
                </ol>
            </li>
            <li><strong>Analysis Types:</strong>
                <ul>
                    <li>Security vulnerability detection</li>
                    <li>Code quality issues</li>
                    <li>Best practice violations</li>
                    <li>Potential bug patterns</li>
                </ul>
            </li>
        </ul>
        <p><strong>Note:</strong> Code is analyzed locally and not shared with external services.</p>
    </div>
);

export const DependencyAnalysisInfo = (
    <div>
        <p><strong>Dependency Vulnerability Analysis</strong></p>
        <p>Scan project dependencies for known security vulnerabilities:</p>
        <ul>
            <li><strong>Supported Formats:</strong>
                <ul>
                    <li>package.json (Node.js)</li>
                    <li>requirements.txt (Python)</li>
                    <li>pom.xml (Maven)</li>
                    <li>go.mod (Go modules)</li>
                    <li>And many more</li>
                </ul>
            </li>
            <li><strong>Scan Process:</strong>
                <ol>
                    <li>Upload your dependency manifest file</li>
                    <li>The system analyzes all dependencies</li>
                    <li>Cross-references with vulnerability databases</li>
                    <li>Generates detailed vulnerability report</li>
                </ol>
            </li>
            <li><strong>Results Include:</strong>
                <ul>
                    <li>CVE numbers and descriptions</li>
                    <li>Severity scores (CVSS)</li>
                    <li>Affected versions</li>
                    <li>Remediation recommendations</li>
                </ul>
            </li>
        </ul>
    </div>
);

export const SbomAnalysisInfo = (
    <div>
        <p><strong>SBOM Generator</strong></p>
        <p>Generate a Software Bill of Materials (SBOM) for your projects:</p>
        <ul>
            <li><strong>Supported Ecosystems:</strong>
                <ul>
                    <li>npm / yarn (Node.js)</li>
                    <li>pip / poetry (Python)</li>
                    <li>Maven / Gradle (Java)</li>
                    <li>Go modules</li>
                    <li>Cargo (Rust)</li>
                    <li>NuGet (.NET)</li>
                    <li>And many more</li>
                </ul>
            </li>
            <li><strong>Output Format:</strong> CycloneDX JSON - an industry-standard SBOM format</li>
            <li><strong>Scan Process:</strong>
                <ol>
                    <li>Upload a ZIP file or provide a GitHub repository URL</li>
                    <li>All files and dependency manifests are analyzed</li>
                    <li>A comprehensive SBOM is generated listing all components</li>
                    <li>Optional AI analysis provides supply chain security insights</li>
                </ol>
            </li>
            <li><strong>Results Include:</strong>
                <ul>
                    <li>Package names, versions, and types</li>
                    <li>Package URLs (PURLs) for precise identification</li>
                    <li>License information for compliance</li>
                    <li>AI-powered supply chain risk assessment (when enabled)</li>
                </ul>
            </li>
        </ul>
    </div>
);

// User Management Page info content
export const ManageOrganisationsInfo = (
    <div>
        <p><strong>Manage Organisations</strong></p>
        <p>Create and manage organizational units:</p>
        <ul>
            <li><strong>Create Organisation:</strong>
                <ol>
                    <li>Enter organization name</li>
                    <li>Provide description</li>
                    <li>Click "Create Organisation"</li>
                </ol>
            </li>
            <li><strong>Organisation Features:</strong>
                <ul>
                    <li>Each organization has isolated data</li>
                    <li>Separate compliance frameworks</li>
                    <li>Independent user management</li>
                    <li>Isolated assessments and policies</li>
                </ul>
            </li>
        </ul>
    </div>
);

export const ManageUsersInfo = (
    <div>
        <p><strong>Manage Users</strong></p>
        <p>User administration and role management:</p>
        <ul>
            <li><strong>User Roles:</strong>
                <ul>
                    <li><strong>Super Admin:</strong> Full system access across all organizations</li>
                    <li><strong>Org Admin:</strong> Administrative access within their organization</li>
                    <li><strong>Org User:</strong> Standard user access within their organization</li>
                </ul>
            </li>
            <li><strong>Create User:</strong>
                <ol>
                    <li>Enter user details (name, email)</li>
                    <li>Select organization</li>
                    <li>Assign appropriate role</li>
                    <li>Click "Create User"</li>
                </ol>
            </li>
            <li><strong>User Management:</strong>
                <ul>
                    <li>View users by organization</li>
                    <li>Edit user roles and details</li>
                    <li>Deactivate or remove users</li>
                </ul>
            </li>
        </ul>
    </div>
);

// Assessments Page info content
export const AssessmentsInfo = (
    <div>
        <p><strong>Assessments</strong></p>
        <p>Conduct compliance assessments and track progress:</p>
        <ul>
            <li><strong>Create Assessment:</strong>
                <ol>
                    <li>Select a framework to assess</li>
                    <li>Choose assessment type (Conformity or Audit)</li>
                    <li>Enter assessment name and description</li>
                    <li>Click "Create Assessment"</li>
                </ol>
            </li>
            <li><strong>Assessment Types:</strong>
                <ul>
                    <li><strong>Conformity:</strong> Self-assessment against compliance requirements</li>
                    <li><strong>Audit:</strong> Formal audit assessment process</li>
                </ul>
            </li>
            <li><strong>Assessment Process:</strong>
                <ul>
                    <li>Answer all framework questions</li>
                    <li>Provide evidence and documentation</li>
                    <li>Track completion progress</li>
                    <li>Review and finalize assessment</li>
                </ul>
            </li>
            <li><strong>Progress Tracking:</strong> View assessment completion status and identify remaining questions</li>
            <li><strong>Export Capabilities:</strong> Generate PDF reports for compliance documentation</li>
        </ul>
    </div>
);

// Objectives Checklist Page info content  
export const ObjectivesChecklistInfo = (
    <div>
        <p><strong>Objectives Checklist</strong></p>
        <p>Track and manage compliance objectives within frameworks:</p>
        <ul>
            <li><strong>Framework Selection:</strong>
                <ol>
                    <li>Select a framework from the dropdown</li>
                    <li>View all objectives organized by chapters</li>
                    <li>Track compliance status for each objective</li>
                </ol>
            </li>
            <li><strong>Compliance Status Options:</strong>
                <ul>
                    <li><strong>Not Assessed:</strong> Objective not yet evaluated</li>
                    <li><strong>Not Compliant:</strong> Requirements not met</li>
                    <li><strong>Partially Compliant:</strong> Some requirements met</li>
                    <li><strong>In Review:</strong> Under assessment review</li>
                    <li><strong>Compliant:</strong> All requirements satisfied</li>
                    <li><strong>Not Applicable:</strong> Objective doesn't apply to organization</li>
                </ul>
            </li>
            <li><strong>Updating Status:</strong>
                <ul>
                    <li>Click on any objective row to edit</li>
                    <li>Select appropriate compliance status</li>
                    <li>Add notes or evidence as needed</li>
                    <li>Save changes to track progress</li>
                </ul>
            </li>
            <li><strong>Progress Overview:</strong> Visual indicators show overall framework compliance progress</li>
            <li><strong>Export Function:</strong> Generate compliance reports and documentation</li>
        </ul>
    </div>
);

// Architecture Page info content
export const ArchitectureInfo = (
    <div>
        <p><strong>Architecture Diagrams</strong></p>
        <p>Manage and document your organization's technical architecture through visual diagrams:</p>
        <ul>
            <li><strong>Diagram Types:</strong>
                <ul>
                    <li><strong>System Architecture:</strong> Overall system design and components</li>
                    <li><strong>Network Diagram:</strong> Network topology and connections</li>
                    <li><strong>Data Flow:</strong> How data moves through systems</li>
                    <li><strong>Infrastructure:</strong> Physical and cloud infrastructure</li>
                    <li><strong>Application:</strong> Application-level architecture</li>
                    <li><strong>Security:</strong> Security controls and boundaries</li>
                </ul>
            </li>
            <li><strong>Features:</strong>
                <ul>
                    <li>Upload diagrams in various formats (PNG, JPG, SVG, PDF, Draw.io, Visio)</li>
                    <li>Link diagrams to compliance frameworks</li>
                    <li>Associate diagrams with identified risks</li>
                    <li>Track version history</li>
                    <li>Assign diagram owners</li>
                </ul>
            </li>
            <li><strong>How to Use:</strong>
                <ol>
                    <li>Click "Add Diagram" to create a new entry</li>
                    <li>Enter diagram name, type, and description</li>
                    <li>Upload the diagram file</li>
                    <li>Link to relevant frameworks and risks</li>
                    <li>Save to add to your architecture registry</li>
                </ol>
            </li>
        </ul>
        <p><strong>Tip:</strong> Keep diagrams up-to-date and linked to risks for comprehensive compliance documentation.</p>
    </div>
);

// Evidence Page info content
export const EvidenceInfo = (
    <div>
        <p><strong>Evidence Management</strong></p>
        <p>Collect, organize, and manage evidence demonstrating control implementation and effectiveness:</p>
        <ul>
            <li><strong>Evidence Types:</strong>
                <ul>
                    <li><strong>Screenshot:</strong> Visual proof of configurations or settings</li>
                    <li><strong>Report:</strong> Generated reports from systems or audits</li>
                    <li><strong>Log:</strong> System or application logs</li>
                    <li><strong>Export:</strong> Data exports from tools or systems</li>
                    <li><strong>AI Generated:</strong> Evidence created using AI tools</li>
                    <li><strong>Document:</strong> Policies, procedures, or other documents</li>
                </ul>
            </li>
            <li><strong>Collection Methods:</strong>
                <ul>
                    <li><strong>Manual:</strong> Manually collected by users</li>
                    <li><strong>Automated:</strong> Automatically collected by systems</li>
                    <li><strong>AI Generated:</strong> Generated using AI assistance</li>
                </ul>
            </li>
            <li><strong>Evidence Status:</strong>
                <ul>
                    <li><strong>Valid:</strong> Evidence is current and acceptable</li>
                    <li><strong>Expiring:</strong> Evidence validity is ending soon</li>
                    <li><strong>Expired:</strong> Evidence needs to be refreshed</li>
                    <li><strong>Pending Review:</strong> Awaiting review by auditor</li>
                </ul>
            </li>
            <li><strong>Features:</strong>
                <ul>
                    <li>Upload evidence files in any format</li>
                    <li>Map evidence to controls and frameworks</li>
                    <li>Track validity periods and expiration dates</li>
                    <li>Add audit notes for reviewers</li>
                    <li>Filter and search evidence by type, framework, or status</li>
                </ul>
            </li>
        </ul>
        <p><strong>Purpose:</strong> Prove that controls are implemented and operating effectively during compliance assessments and audits.</p>
    </div>
);

// Compliance Advisor Page info content
export const ComplianceAdvisorInfo = (
    <div>
        <p><strong>Compliance Advisor</strong></p>
        <p>Get AI-powered recommendations for which compliance frameworks your organization should implement:</p>
        <ul>
            <li><strong>Website Analysis:</strong> Provide your company website URL for automatic analysis</li>
            <li><strong>Framework Recommendations:</strong> Receive prioritized recommendations based on your industry, geography, and products</li>
            <li><strong>One-Click Setup:</strong> Seed recommended frameworks directly into your workspace</li>
        </ul>
    </div>
);

// Scan Findings Page info content
export const ScanFindingsInfo = (
    <div>
        <p><strong>Scan Findings</strong></p>
        <p>A unified view of all security findings extracted from your scanners:</p>
        <ul>
            <li><strong>Stats Overview:</strong> See total findings, how many are linked to risks, breakdown by scanner and severity</li>
            <li><strong>Filters:</strong> Filter by scanner type, severity level, risk linkage status, or search by title/identifier</li>
            <li><strong>CVE Enrichment:</strong> Findings with CVE identifiers are automatically enriched with CVSS scores and descriptions from the NVD database</li>
            <li><strong>Expandable Rows:</strong> Click any row to see the full description, solution, CVE details, and linked risks</li>
            <li><strong>Pagination:</strong> Server-side pagination for efficient browsing of large result sets</li>
        </ul>
        <p><strong>Tip:</strong> Use the "Risk Link" filter to find unlinked findings that may need to be mapped to risks in your risk register.</p>
    </div>
);

// Incident Registration Page info content
export const IncidentsInfo = (
    <div>
        <p><strong>Incident Registration</strong></p>
        <p>Track and manage cybersecurity incidents throughout their lifecycle:</p>
        <ul>
            <li><strong>Dashboard:</strong> Overview of all incidents with status distribution and severity breakdown</li>
            <li><strong>Incident Registry:</strong> Create, edit, and manage incidents with severity levels, status tracking, and vulnerability triage fields</li>
            <li><strong>AI Analysis:</strong> Use AI-powered analysis to get containment steps, root cause analysis, and remediation recommendations</li>
            <li><strong>Connections:</strong> Link incidents to frameworks, risks, and assets for comprehensive tracking</li>
            <li><strong>Severe Incidents:</strong> Focused view of Critical and High severity incidents for priority attention</li>
            <li><strong>Active Exploits:</strong> Real-time feed of actively exploited and critical vulnerabilities from the European Vulnerability Database (EUVD), refreshed hourly</li>
            <li><strong>Post-Market:</strong> Dashboard showing SLA compliance, overdue incidents, patch metrics, ENISA reporting status, and vulnerability aging</li>
            <li><strong>Patch Tracking:</strong> Track patches per incident with version, release date, SLA compliance, and resolution tracking</li>
            <li><strong>ENISA Reporting:</strong> CRA Article 14 notification management with 24h early warning, 72h vulnerability notification, and 14d final report deadlines</li>
        </ul>
        <p><strong>Incident Lifecycle:</strong> Open → Investigating → Contained → Resolved → Closed</p>
    </div>
);

// CE Marking Checklist Page info content
export const CEMarkingChecklistInfo = (
    <div>
        <p><strong>CE Marking Checklist</strong></p>
        <p>Track CE mark readiness for your products and digital devices under the EU Cyber Resilience Act:</p>
        <ul>
            <li><strong>All Checklists:</strong> Overview of all CE marking checklists per asset, with readiness scores and status tracking</li>
            <li><strong>Checklist Items:</strong> Category-based checklist covering Product Classification, CE Placement, Documentation, Notified Body, Traceability, and General Conformity</li>
            <li><strong>Documentation:</strong> Track completion status of required documents (EU DoC, Technical File, User Manual, Risk Assessment, Test Reports, SBOM)</li>
            <li><strong>CE Details:</strong> Configure product type, CE placement, and Notified Body information</li>
            <li><strong>Traceability:</strong> Record version identifiers, build IDs, DoC publication URLs, and product variants</li>
        </ul>
        <p><strong>Readiness Score:</strong> Automatically calculated based on completed mandatory items and documentation status.</p>
    </div>
);

// Security Advisories Page info content
export const AdvisoriesInfo = (
    <div>
        <p><strong>Security Advisories</strong></p>
        <p>Create and manage security advisories for vulnerabilities affecting your products:</p>
        <ul>
            <li><strong>Dashboard:</strong> Overview of advisory counts, severity distribution, and publication status</li>
            <li><strong>Advisory Registry:</strong> Full CRUD management with auto-generated advisory codes (ADV-N)</li>
            <li><strong>Severity Levels:</strong> Critical, High, Medium, Low</li>
            <li><strong>Status Workflow:</strong> Draft → Review → Published → Updated → Archived</li>
            <li><strong>CVE Tracking:</strong> Link advisories to CVE identifiers for vulnerability reference</li>
            <li><strong>Incident Linking:</strong> Associate advisories with incidents for traceability</li>
        </ul>
        <p><strong>CRA Compliance:</strong> Security advisories support the Cyber Resilience Act requirement for coordinated vulnerability disclosure.</p>
    </div>
);

// Security Scanners Page info content
export const SecurityScannersInfo = (
    <div>
        <p><strong>Security Scanners</strong></p>
        <p>Comprehensive security scanning tools for identifying vulnerabilities:</p>
        <ul>
            <li><strong>Web App Scanner:</strong>
                <ul>
                    <li>Spider and active scanning for web vulnerabilities</li>
                    <li>OWASP Top 10 vulnerability detection</li>
                    <li>API security testing</li>
                </ul>
            </li>
            <li><strong>Network Scanner:</strong>
                <ul>
                    <li>Port scanning and service detection</li>
                    <li>Operating system fingerprinting</li>
                    <li>Network reconnaissance</li>
                </ul>
            </li>
            <li><strong>Code Analysis:</strong>
                <ul>
                    <li>Static code analysis for security issues</li>
                    <li>Multi-language support</li>
                    <li>Custom rule configuration</li>
                </ul>
            </li>
            <li><strong>Dependency Check:</strong>
                <ul>
                    <li>Vulnerability scanning for dependencies</li>
                    <li>CVE database cross-referencing</li>
                    <li>Remediation recommendations</li>
                </ul>
            </li>
        </ul>
        <p><strong>Features:</strong></p>
        <ul>
            <li>Current Scan and Scan History tabs for each scanner</li>
            <li>LLM-powered analysis for detailed insights</li>
            <li>Export results to PDF or HTML</li>
        </ul>
        <p><strong>Important:</strong> Only scan systems and applications you own or have explicit authorization to test.</p>
    </div>
);
