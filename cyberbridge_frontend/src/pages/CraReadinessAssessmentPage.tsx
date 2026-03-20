import { useLocation } from 'wouter';
import { Select, Tooltip, Collapse, Radio } from 'antd';
import { InfoCircleOutlined, CheckCircleFilled, PlusOutlined } from '@ant-design/icons';
import useCraReadinessStore, { SectionKey } from '../store/useCraReadinessStore';
import cyberbridgeLogo from '../assets/cyberbridge_logo.svg';
import Sidebar from '../components/Sidebar';
import { useMenuHighlighting } from '../utils/menuUtils';

// ─── Shared option lists ──────────────────────────────────────────

const EU_COUNTRIES = [
    'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic',
    'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary',
    'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta',
    'Netherlands', 'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia',
    'Spain', 'Sweden',
];

const EU_LANGUAGES = [
    'Bulgarian', 'Croatian', 'Czech', 'Danish', 'Dutch', 'English', 'Estonian',
    'Finnish', 'French', 'German', 'Greek', 'Hungarian', 'Irish', 'Italian',
    'Latvian', 'Lithuanian', 'Maltese', 'Polish', 'Portuguese', 'Romanian',
    'Slovak', 'Slovenian', 'Spanish', 'Swedish',
];

const SECTORS = [
    'Aerospace', 'Agriculture', 'Automotive', 'Banking & Finance',
    'Construction', 'Consumer Electronics', 'Defence', 'Education',
    'Energy', 'Healthcare', 'Hospitality', 'Information Technology',
    'Insurance', 'Legal', 'Manufacturing', 'Media & Entertainment',
    'Pharmaceuticals', 'Public Sector', 'Retail', 'Telecommunications',
    'Transportation & Logistics',
];

const PERCENTAGE_OPTIONS = [
    '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%',
];

const PRODUCT_COUNT_OPTIONS = [
    'Only 1', '2-4', '5-6', '7-9', 'More than 10',
];

const CRA_CATEGORIES = [
    'Default (Self Assessment)',
    'Important Class I (Harmonised Standards)',
    'Important Product Class II (3rd Party Assessment)',
    'Critical Products (EUCC by default)',
    'Not sure',
];

const PRODUCT_TYPES = ['Hardware Only', 'Software Only', 'Hardware & Software'];
const MARKET_CHANNELS = ['Direct to Market', 'Distributor', 'Both'];
const LIFECYCLE_OPTIONS = ['Less than a year', '1 year', '2 years', '3 years', 'More than 3 years'];

const HARMONISED_STANDARDS = [
    'None',
    'EN 303 645 (IoT Cybersecurity)',
    'IEC 62443 (Industrial Automation)',
    'ISO/IEC 27001 (Information Security)',
    'ISO/IEC 27002 (Security Controls)',
    'ISO/IEC 15408 (Common Criteria)',
    'ISO/IEC 27005 (Risk Management)',
    'ETSI EN 303 645 (Consumer IoT)',
    'IEC 61508 (Functional Safety)',
    'ISO 21434 (Automotive Cybersecurity)',
    'ISO/SAE 21434 (Road Vehicles)',
    'EN 18031 (Radio Equipment)',
    'IEC 62351 (Power Systems)',
    'ISO 22301 (Business Continuity)',
    'ISO/IEC 29147 (Vulnerability Disclosure)',
    'ISO/IEC 30111 (Vulnerability Handling)',
    'NIST Cybersecurity Framework',
    'CIS Controls',
    'OWASP ASVS',
    'SOC 2 Type II',
    'PCI DSS',
];

const RISK_METHODOLOGIES = [
    'ISO 27005', 'NIST SP 800-30', 'OCTAVE', 'FAIR', 'CRAMM',
    'STRIDE', 'DREAD', 'PASTA', 'Attack Trees', 'Bow-Tie Analysis', 'Custom/Other',
];

const LIKERT_OPTIONS = [
    'Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree',
];

// ─── Question type definitions ────────────────────────────────────

type QuestionType = 'text' | 'select' | 'toggle' | 'likert' | 'toggleCustom';

interface QuestionDef {
    field: string;
    question: string;
    type: QuestionType;
    tooltip?: string;
    options?: string[];
    customLabels?: [string, string]; // for toggleCustom
    placeholder?: string;
}

// ─── Question data per section ────────────────────────────────────

const companyInfoQuestions: QuestionDef[] = [
    { field: 'companyName', question: 'What is your company name?', type: 'text', tooltip: 'Enter the registered legal name of your company.', placeholder: 'Enter company name' },
    { field: 'contactName', question: 'What is your contact name?', type: 'text', tooltip: 'Enter the name of the primary contact person for this assessment.', placeholder: 'Enter contact name' },
    { field: 'companySize', question: 'What is the size of your company in terms of the number of employees?', type: 'select', tooltip: 'Select the employee range that best describes your company.', options: ['Micro: 0-9', 'Small: 10-49', 'Medium: 50-249', 'Large: 250+'] },
    { field: 'country', question: 'What country is your company headquartered in?', type: 'select', tooltip: 'Select the EU member state where your company is headquartered.', options: EU_COUNTRIES },
    { field: 'sectors', question: 'What sectors does your company operate in?', type: 'select', tooltip: 'Select the primary sector your company operates in.', options: SECTORS },
    { field: 'languages', question: 'What languages does your company use for product documentation?', type: 'select', tooltip: 'Select the primary language used for product documentation and support.', options: EU_LANGUAGES },
    { field: 'craImpact', question: 'How well do you understand the impact of the Cyber Resilience Act on your organisation?', type: 'select', tooltip: 'Rate your understanding of CRA requirements and their impact on your business operations.', options: PERCENTAGE_OPTIONS },
    { field: 'staffTraining', question: 'What percentage of your staff require specialised cybersecurity training?', type: 'select', tooltip: 'Estimate the percentage of staff who need training to meet CRA compliance requirements.', options: PERCENTAGE_OPTIONS },
    { field: 'productsOnMarket', question: 'How many products do you have on the EU single market?', type: 'select', tooltip: 'Count all products with digital elements currently available on the EU market.', options: PRODUCT_COUNT_OPTIONS },
    { field: 'newProducts', question: 'How many new products do you plan to launch in the next 3 years?', type: 'select', tooltip: 'Estimate new product launches to plan for CRA compliance timelines.', options: PRODUCT_COUNT_OPTIONS },
];

const productInfoQuestions: QuestionDef[] = [
    { field: 'craCategory', question: 'What CRA category does your product fall under?', type: 'select', tooltip: 'Default products require self-assessment. Important Class I can use harmonised standards. Important Class II requires third-party assessment. Critical products require EUCC certification.', options: CRA_CATEGORIES },
    { field: 'productType', question: 'Is your product hardware, software, or both?', type: 'select', tooltip: 'The CRA applies to all products with digital elements, including hardware devices with embedded software, standalone software, and combined hardware/software products.', options: PRODUCT_TYPES },
    { field: 'marketChannel', question: 'Do you sell your product direct to market, through a distributor, or both?', type: 'select', options: MARKET_CHANNELS },
    { field: 'importsComponents', question: 'Does your product import components with digital elements from other suppliers?', type: 'toggle' },
    { field: 'lifecycleLength', question: 'What is your product development lifecycle length?', type: 'select', options: LIFECYCLE_OPTIONS },
    { field: 'containsOpenSource', question: 'Does your product contain open source software?', type: 'toggle' },
    { field: 'intendedUse', question: 'What is the overall intended use of your product?', type: 'text', tooltip: 'Describe the primary function and purpose of your product in the market.', placeholder: 'Describe intended use' },
    { field: 'keyFeatures', question: 'What are the key features of your product?', type: 'text', tooltip: 'List the main features and functionalities of your product.', placeholder: 'Describe key features' },
    { field: 'marketsForSale', question: 'What EU markets do you sell your product in?', type: 'select', tooltip: 'Select the primary EU country where your product is sold.', options: EU_COUNTRIES },
    { field: 'harmonisedStandards', question: 'Is your product compliant with any harmonised standards?', type: 'select', tooltip: 'Harmonised standards provide a presumption of conformity with corresponding CRA essential requirements. Using these standards simplifies the conformity assessment process.', options: HARMONISED_STANDARDS },
    { field: 'usesAI', question: 'Does your product use Artificial Intelligence?', type: 'toggle', tooltip: 'Products using AI may have additional requirements under the EU AI Act in conjunction with the CRA.' },
    { field: 'processesGDPR', question: 'Does your product process personal data under GDPR?', type: 'toggle', tooltip: 'Products processing personal data must comply with both GDPR and CRA data protection requirements.' },
];

const riskManagementQuestions: QuestionDef[] = [
    { field: 'riskInLifecycle', question: 'Do you conduct a risk assessment as part of your product development lifecycle?', type: 'toggle', tooltip: 'A risk assessment identifies, analyses, and evaluates cybersecurity risks throughout the product development process.' },
    { field: 'formalMethodology', question: 'Do you use a formal methodology for your risk assessment?', type: 'toggle', tooltip: 'Formal methodologies provide structured approaches to identifying and managing cybersecurity risks consistently.' },
    { field: 'methodologies', question: 'Which risk assessment methodologies do you use?', type: 'select', tooltip: 'Select the primary risk assessment methodology used by your organisation.', options: RISK_METHODOLOGIES },
    { field: 'internalOrExternal', question: 'Is your risk assessment conducted internally or externally?', type: 'select', tooltip: 'Internal assessments are conducted by your own team. External assessments are performed by third-party specialists.', options: ['Internal', 'External'] },
    { field: 'formalReport', question: 'Does your risk assessment produce a formal report?', type: 'toggle', tooltip: 'A formal report documents the risk assessment findings, risk treatment decisions, and residual risks.' },
    { field: 'allPhasesAssessed', question: 'Cybersecurity risks are assessed in all phases of the product lifecycle.', type: 'likert', tooltip: 'Rate your agreement that cybersecurity risk assessment occurs at every phase: design, development, testing, deployment, and maintenance.' },
    { field: 'minimisingPriority', question: 'Minimising cybersecurity risk is a priority in product development.', type: 'likert', tooltip: 'Rate your agreement that reducing cybersecurity risk is a key priority throughout development.' },
];

const testingQuestions: QuestionDef[] = [
    { field: 'testForVulnerabilities', question: 'Do you test for known vulnerabilities as part of your product development lifecycle?', type: 'toggle', tooltip: 'Product testing occurs throughout development to identify and address known vulnerabilities before release.' },
    { field: 'vulnerabilityScanning', question: 'Do you use vulnerability scanning products?', type: 'toggle', tooltip: 'Vulnerability scanning uses automated tools to detect known vulnerabilities in your product components and dependencies.' },
    { field: 'penetrationTesting', question: 'Do you conduct penetration testing?', type: 'toggle', tooltip: 'Penetration testing simulates cyber attacks against your product to identify exploitable vulnerabilities.' },
    { field: 'codeReviews', question: 'Do you conduct secure source code reviews?', type: 'toggle', tooltip: 'Reviewing source code identifies vulnerabilities such as injection flaws, authentication weaknesses, and insecure data handling.' },
    { field: 'riskBasedTesting', question: 'Do you use risk assessment to determine testing criteria?', type: 'toggle', tooltip: 'Risk assessment identifies high-risk areas to prioritise testing efforts where they have the most impact.' },
    { field: 'standardisedDB', question: 'Do you use a standardised vulnerability database such as MITRE CVE?', type: 'toggle', tooltip: 'MITRE CVE is a standard method to classify and reference known vulnerabilities. Using it helps ensure comprehensive coverage.' },
    { field: 'confidentNoVulnerabilities', question: 'You are confident that your product has no known exploitable vulnerabilities.', type: 'likert', tooltip: 'Rate your confidence from Strongly Disagree (low) to Strongly Agree (high).' },
    { field: 'systematicDocumenting', question: 'Do you have a systematic method for documenting vulnerabilities?', type: 'toggle', tooltip: 'Includes issue tracking systems such as Jira, vulnerability management tools like Qualys, or structured reporting processes.' },
];

const secureConfigQuestions: QuestionDef[] = [
    { field: 'secureByDefault', question: 'Is your product delivered "secure by default"?', type: 'toggle', tooltip: 'Secure by default means security is embedded in every step of the product — security controls are enabled out of the box without requiring user configuration.' },
    { field: 'secureConfigDocs', question: 'Does your product documentation contain secure configuration details?', type: 'toggle', tooltip: 'Documentation should describe security controls enabled by default, recommended security settings, and configuration hardening guidance.' },
    { field: 'resetInstructions', question: 'Does your documentation include instructions to reset to a secure default configuration?', type: 'toggle', tooltip: 'Users should be able to reset the product to its initial secure configuration state if needed.' },
];

const securityControlsQuestions: QuestionDef[] = [
    { field: 'unauthorisedAccess', question: 'Does your product protect from unauthorised access (e.g., password, MFA)?', type: 'toggle', tooltip: 'Authentication mechanisms such as passwords, multi-factor authentication, and access controls prevent unauthorised users from accessing the product.' },
    { field: 'dataConfidentiality', question: 'Is the confidentiality of data protected (e.g., encryption)?', type: 'toggle', tooltip: 'Data confidentiality measures such as encryption at rest and in transit prevent unauthorised access to sensitive information.' },
    { field: 'dataIntegrity', question: 'Is the integrity of data protected?', type: 'toggle', tooltip: 'Data integrity controls ensure that data is not modified, corrupted, or tampered with during storage or transmission.' },
    { field: 'dataAvailability', question: 'Is the availability of data protected?', type: 'toggle', tooltip: 'Availability measures ensure data and services remain accessible and operational when needed by authorised users.' },
    { field: 'dosResilience', question: 'Are essential functions available during denial of service attacks?', type: 'toggle', tooltip: 'The product should maintain core functionality even under denial of service conditions through resilience measures.' },
    { field: 'dataMinimised', question: 'Is data minimised to what is adequate, relevant, and necessary?', type: 'toggle', tooltip: 'Data minimisation ensures only the minimum amount of data required for the product to function is collected and processed.' },
    { field: 'noNegativeImpact', question: 'Does your product avoid negatively impacting other connected services?', type: 'toggle', tooltip: 'The product should not compromise the security or availability of other devices, networks, or services it connects to.' },
    { field: 'limitAttackSurfaces', question: 'Your product is designed to limit attack surfaces.', type: 'likert', tooltip: 'Rate your agreement that the product minimises entry points through measures like disabling unused ports, services, and interfaces.' },
    { field: 'reduceIncidentImpact', question: 'Your product is designed to reduce the impact of cyber incidents (e.g., through segmentation).', type: 'likert', tooltip: 'Rate your agreement that the product uses techniques like network segmentation, sandboxing, or compartmentalisation to contain incidents.' },
    { field: 'monitorActivity', question: 'Does your product monitor relevant internal activity?', type: 'toggle', tooltip: 'Monitoring capabilities such as logging, auditing, and alerting help detect and respond to security incidents.' },
];

const vulnManagementQuestions: QuestionDef[] = [
    { field: 'routineTestPostMarket', question: 'Do you routinely test for vulnerabilities after product release (post-market)?', type: 'toggle', tooltip: 'Ongoing vulnerability testing after release helps identify new threats and maintain product security throughout its lifecycle.' },
    { field: 'vulnScanningLifecycle', question: 'Do you conduct vulnerability scanning throughout the product lifecycle?', type: 'toggle', tooltip: 'Continuous vulnerability scanning ensures new vulnerabilities are detected across all phases of the product lifecycle.' },
    { field: 'penTestLifecycle', question: 'Do you conduct penetration testing throughout the product lifecycle?', type: 'toggle', tooltip: 'Regular penetration testing validates security controls and identifies exploitable vulnerabilities beyond automated scanning.' },
    { field: 'codeReviewLifecycle', question: 'Do you conduct secure code reviews throughout the product lifecycle?', type: 'toggle', tooltip: 'Ongoing code reviews catch vulnerabilities introduced through updates, patches, and feature additions.' },
    { field: 'vulnTestOnUpdates', question: 'Do you conduct vulnerability testing on product updates?', type: 'toggle', tooltip: 'Testing updates before release ensures patches and new features do not introduce new vulnerabilities.' },
    { field: 'addressPromptly', question: 'You address and remediate identified vulnerabilities promptly.', type: 'likert', tooltip: 'Rate your agreement that your organisation has processes to quickly fix discovered vulnerabilities.' },
];

const vulnDisclosureQuestions: QuestionDef[] = [
    { field: 'publiclyDisclose', question: 'Do you publicly disclose information about fixed vulnerabilities?', type: 'toggle', tooltip: 'Public disclosure of fixed vulnerabilities helps users understand risks and apply patches. The CRA requires timely disclosure.' },
    { field: 'disclosureMethod', question: 'How do you publicly disclose vulnerability information?', type: 'text', tooltip: 'Describe your disclosure channels such as security advisories, CVE publications, website notices, or mailing lists.', placeholder: 'Describe disclosure method' },
    { field: 'coordinatedPolicy', question: 'Do you have a policy for coordinated vulnerability disclosure?', type: 'toggle', tooltip: 'A coordinated disclosure policy defines how vulnerabilities reported by external researchers are handled, verified, and disclosed.' },
    { field: 'contactAddress', question: 'Do you provide a contact address for reporting vulnerabilities?', type: 'toggle', tooltip: 'A dedicated security contact (e.g., security@company.com) enables responsible disclosure from external researchers.' },
    { field: 'otherMeasures', question: 'Do you have other measures in place to facilitate information sharing about vulnerabilities?', type: 'toggle', tooltip: 'Additional measures may include bug bounty programs, security response teams, or participation in industry sharing groups.' },
    { field: 'measuresDetails', question: 'Please provide details on your information sharing measures.', type: 'text', tooltip: 'Describe any additional measures such as bug bounty programs, ISACs, or threat intelligence sharing arrangements.', placeholder: 'Describe measures' },
    { field: 'secureDistribution', question: 'Do you have a mechanism to securely distribute security updates?', type: 'toggle', tooltip: 'Secure distribution ensures updates are authentic, untampered, and delivered through trusted channels.' },
    { field: 'patchesNoDelay', question: 'Are security patches made available without delay?', type: 'toggle', tooltip: 'The CRA requires that security patches are provided promptly after vulnerability identification.' },
    { field: 'patchesFreeOfCharge', question: 'Are security patches available free of charge?', type: 'toggle', tooltip: 'The CRA requires that security updates are provided free of charge for the expected product lifetime.' },
    { field: 'patchesWithInfo', question: 'Are patches accompanied with relevant information for users?', type: 'toggle', tooltip: 'Patch information should include details about the vulnerability addressed, impact, and any required user actions.' },
];

const sbomQuestions: QuestionDef[] = [
    { field: 'hasSBOM', question: 'Do you have a Software Bill of Materials (SBOM) for your product?', type: 'toggle', tooltip: 'An SBOM is a formal inventory of all software components, libraries, and dependencies used in your product. The CRA requires manufacturers to produce an SBOM.' },
    { field: 'sbomProcess', question: 'Is your SBOM created through an automated or manual process?', type: 'toggleCustom', tooltip: 'Automated SBOM generation tools provide more consistent and comprehensive results than manual processes.', customLabels: ['Manual', 'Automatic'] },
    { field: 'sbomFormat', question: 'Is your SBOM in a commonly used machine-readable format (e.g., SPDX, CycloneDX, CPE)?', type: 'toggle', tooltip: 'Machine-readable formats like SPDX and CycloneDX enable automated processing, compliance checking, and vulnerability matching.' },
];

const productDocsQuestions: QuestionDef[] = [
    { field: 'manufacturerDetails', question: 'Does your product documentation detail the manufacturer name, address, and email?', type: 'toggle' },
    { field: 'vulnReportingContact', question: 'Does your documentation detail a vulnerability reporting contact point?', type: 'toggle', tooltip: 'CRA requires manufacturers to provide a single point of contact for vulnerability reporting in product documentation.' },
    { field: 'productIdentification', question: 'Does your documentation detail product identification (type, batch, version)?', type: 'toggle', tooltip: 'Product identification enables traceability and helps users verify they have the correct and latest version.' },
    { field: 'intendedUseDocs', question: 'Does your documentation detail intended use, security environment, and functionalities?', type: 'toggle', tooltip: 'Comprehensive documentation helps users understand the security context and properly deploy and configure the product.' },
];

// ─── Map sub-steps to sections and questions ──────────────────────

interface SubStepConfig {
    mainStep: number;
    heading: string;
    section: SectionKey;
    questions: QuestionDef[];
}

const subStepConfigs: SubStepConfig[] = [
    { mainStep: 0, heading: '1.1 Company Information', section: 'companyInfo', questions: companyInfoQuestions },
    { mainStep: 0, heading: '1.2 Product Information', section: 'productInfo', questions: productInfoQuestions },
    { mainStep: 1, heading: '2.1 Risk Management', section: 'riskManagement', questions: riskManagementQuestions },
    { mainStep: 1, heading: '2.2 Testing', section: 'testing', questions: testingQuestions },
    { mainStep: 1, heading: '2.3 Secure Configuration', section: 'secureConfig', questions: secureConfigQuestions },
    { mainStep: 1, heading: '2.4 Security Controls', section: 'securityControls', questions: securityControlsQuestions },
    { mainStep: 2, heading: '3.1 Vulnerability Management', section: 'vulnManagement', questions: vulnManagementQuestions },
    { mainStep: 2, heading: '3.2 Vulnerabilities Disclosure', section: 'vulnDisclosure', questions: vulnDisclosureQuestions },
    { mainStep: 3, heading: '4.1 Software Bill of Materials', section: 'sbom', questions: sbomQuestions },
    { mainStep: 3, heading: '4.2 Product Documentation', section: 'productDocs', questions: productDocsQuestions },
];

const mainSteps = [
    { label: 'STEP 01', name: 'General Information' },
    { label: 'STEP 02', name: 'Risk Assessment' },
    { label: 'STEP 03', name: 'Vulnerabilities' },
    { label: 'STEP 04', name: 'Documentation' },
];

// ─── Reusable components ──────────────────────────────────────────

function NoYesToggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
    return (
        <div className="cra-toggle">
            <button type="button" className={`cra-toggle-btn ${!value ? 'active no' : ''}`} onClick={() => onChange(false)}>No</button>
            <button type="button" className={`cra-toggle-btn ${value ? 'active yes' : ''}`} onClick={() => onChange(true)}>Yes</button>
        </div>
    );
}

function CustomToggle({ value, onChange, labels }: { value: string; onChange: (v: string) => void; labels: [string, string] }) {
    return (
        <div className="cra-toggle">
            <button type="button" className={`cra-toggle-btn ${value === labels[0] ? 'active no' : ''}`} onClick={() => onChange(labels[0])}>{labels[0]}</button>
            <button type="button" className={`cra-toggle-btn ${value === labels[1] ? 'active yes' : ''}`} onClick={() => onChange(labels[1])}>{labels[1]}</button>
        </div>
    );
}

function LikertScale({ value, onChange }: { value: string; onChange: (v: string) => void }) {
    return (
        <Radio.Group className="cra-likert" value={value || undefined} onChange={(e) => onChange(e.target.value)}>
            {LIKERT_OPTIONS.map((opt) => (
                <Radio.Button key={opt} value={opt} className="cra-likert-option">
                    {opt}
                </Radio.Button>
            ))}
        </Radio.Group>
    );
}

// ─── Main component ───────────────────────────────────────────────

export default function CraReadinessAssessmentPage() {
    const [location, setLocation] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const { currentSubStep, nextStep, prevStep, data, setField, calculateReadiness } = useCraReadinessStore();

    const handleContinue = () => {
        if (currentSubStep === 10) {
            calculateReadiness();
            setLocation('/cra-readiness-report');
        } else {
            nextStep();
        }
    };

    const handleBack = () => {
        if (currentSubStep === 0) {
            setLocation('/assessments');
        } else {
            prevStep();
        }
    };

    // ─── Stepper ──────────────────────────────────────────────────

    const renderStepper = () => {
        // Determine completed main steps based on current sub-step
        const getMainStepStatus = (idx: number) => {
            if (currentSubStep >= 10) return 'completed'; // review step means all steps are done
            const currentMain = subStepConfigs[currentSubStep].mainStep;
            if (idx < currentMain) return 'completed';
            if (idx === currentMain) return 'active';
            return '';
        };

        return (
            <div className="cra-stepper">
                <img src={cyberbridgeLogo} alt="CyberBridge" style={{ width: '160px', marginBottom: '20px' }} />
                <button
                    type="button"
                    className="cra-btn-login"
                    onClick={() => setLocation('/assessments')}
                >
                    Back to Assessments
                </button>
                {mainSteps.map((step, idx) => (
                    <div key={idx} className="cra-stepper-step">
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                <div className={`cra-stepper-circle ${getMainStepStatus(idx)}`}>
                                    {getMainStepStatus(idx) === 'completed' ? <CheckCircleFilled style={{ fontSize: '24px' }} /> : idx + 1}
                                </div>
                                {idx < mainSteps.length - 1 && (
                                    <div className={`cra-stepper-line ${getMainStepStatus(idx) === 'completed' ? 'completed' : ''}`} />
                                )}
                            </div>
                            <div className="cra-stepper-label">
                                <span className="cra-stepper-step-label">{step.label}</span>
                                <span className={`cra-stepper-step-name ${getMainStepStatus(idx) === 'active' ? 'active' : ''}`}>{step.name}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        );
    };

    // ─── Generic question renderer ────────────────────────────────

    const renderQuestionTable = (config: SubStepConfig) => {
        const { heading, section, questions } = config;
        const answerWidth = questions.some(q => q.type === 'likert') ? '380px' : '280px';

        return (
            <div>
                <h3 className="cra-section-heading">{heading}</h3>
                <table className="cra-question-table">
                    <thead>
                        <tr>
                            <th style={{ width: '50px' }}>No.</th>
                            <th>Question</th>
                            <th style={{ width: answerWidth }}>Answer</th>
                        </tr>
                    </thead>
                    <tbody>
                        {questions.map((q, idx) => (
                            <tr key={q.field}>
                                <td className="cra-question-number">{String(idx + 1).padStart(2, '0')}</td>
                                <td className="cra-question-text">
                                    {q.question}
                                    {q.tooltip && (
                                        <>
                                            {' '}
                                            <Tooltip title={q.tooltip}>
                                                <InfoCircleOutlined className="cra-question-info" />
                                            </Tooltip>
                                        </>
                                    )}
                                </td>
                                <td className="cra-question-answer">
                                    {q.type === 'text' && (
                                        <input
                                            type="text"
                                            className="cra-input"
                                            value={(data[section][q.field] as string) || ''}
                                            onChange={(e) => setField(section, q.field, e.target.value)}
                                            placeholder={q.placeholder || ''}
                                        />
                                    )}
                                    {q.type === 'select' && (
                                        <Select
                                            className="cra-select"
                                            value={(data[section][q.field] as string) || undefined}
                                            onChange={(val) => setField(section, q.field, val)}
                                            placeholder="Select"
                                            style={{ width: '100%' }}
                                            options={(q.options || []).map(o => ({ value: o, label: o }))}
                                        />
                                    )}
                                    {q.type === 'toggle' && (
                                        <NoYesToggle
                                            value={data[section][q.field] as boolean}
                                            onChange={(v) => setField(section, q.field, v)}
                                        />
                                    )}
                                    {q.type === 'likert' && (
                                        <LikertScale
                                            value={(data[section][q.field] as string) || ''}
                                            onChange={(v) => setField(section, q.field, v)}
                                        />
                                    )}
                                    {q.type === 'toggleCustom' && (
                                        <CustomToggle
                                            value={(data[section][q.field] as string) || ''}
                                            onChange={(v) => setField(section, q.field, v)}
                                            labels={q.customLabels || ['No', 'Yes']}
                                        />
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    };

    // ─── Review step ──────────────────────────────────────────────

    const renderReviewStep = () => {
        const formatAnswer = (val: string | boolean, q: QuestionDef): string => {
            if (q.type === 'toggle') return val ? 'Yes' : 'No';
            if (q.type === 'toggleCustom') return (val as string) || '—';
            if (typeof val === 'string') return val || '—';
            return String(val);
        };

        const sectionGroups = [
            { key: '1', label: 'Section 1 - General Information', configs: subStepConfigs.filter(c => c.mainStep === 0) },
            { key: '2', label: 'Section 2 - Risk Assessment', configs: subStepConfigs.filter(c => c.mainStep === 1) },
            { key: '3', label: 'Section 3 - Vulnerabilities', configs: subStepConfigs.filter(c => c.mainStep === 2) },
            { key: '4', label: 'Section 4 - Documentation', configs: subStepConfigs.filter(c => c.mainStep === 3) },
        ];

        const collapseItems = sectionGroups.map(group => ({
            key: group.key,
            label: group.label,
            children: (
                <div>
                    {group.configs.map(config => (
                        <div key={config.section} style={{ marginBottom: '16px' }}>
                            <h4 style={{ color: '#0f386a', fontSize: '14px', fontWeight: 600, margin: '0 0 8px 0' }}>{config.heading}</h4>
                            <table className="cra-question-table review">
                                <tbody>
                                    {config.questions.map((q, idx) => (
                                        <tr key={q.field}>
                                            <td className="cra-question-number">{String(idx + 1).padStart(2, '0')}</td>
                                            <td>{q.question}</td>
                                            <td><strong>{formatAnswer(data[config.section][q.field], q)}</strong></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ))}
                </div>
            ),
        }));

        return (
            <div>
                <h3 className="cra-section-heading">Submission of Form</h3>
                <p style={{ color: '#64748b', marginBottom: '24px', fontSize: '14px' }}>
                    Please review your answers. If you are happy with all your answers, please submit your form below.
                </p>
                <Collapse
                    className="cra-review-section"
                    expandIcon={({ isActive }) => (
                        <PlusOutlined style={{ color: '#0f386a', fontSize: '14px', transform: isActive ? 'rotate(45deg)' : 'none', transition: 'transform 0.2s' }} />
                    )}
                    items={collapseItems}
                />
            </div>
        );
    };

    // ─── Render ───────────────────────────────────────────────────

    const renderContent = () => {
        if (currentSubStep === 10) return renderReviewStep();
        return renderQuestionTable(subStepConfigs[currentSubStep]);
    };

    return (
        <div className={'page-parent'}>
            <Sidebar
                selectedKeys={menuHighlighting.selectedKeys}
                openKeys={menuHighlighting.openKeys}
                onOpenChange={menuHighlighting.onOpenChange}
            />
            <div className={'page-content'}>
                <div className="cra-scope-page">
                    <div className="cra-layout">
                        <div className="cra-sidebar">
                            {renderStepper()}
                        </div>
                        <div className="cra-content">
                            <div className="cra-content-card" style={{ overflowY: 'auto', maxHeight: 'calc(100vh - 140px)' }}>
                                {renderContent()}
                            </div>
                            <div className="cra-footer">
                                <button className="cra-btn-back" onClick={handleBack}>
                                    Go Back
                                </button>
                                <button className="cra-btn-continue" onClick={handleContinue}>
                                    {currentSubStep === 10 ? 'Submit' : 'Continue'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
