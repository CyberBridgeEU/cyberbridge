import { useLocation } from 'wouter';
import { Select, Tooltip, Collapse } from 'antd';
import { InfoCircleOutlined, CheckCircleFilled, PlusOutlined } from '@ant-design/icons';
import useCraScopeStore from '../store/useCraScopeStore';
import cyberbridgeLogo from '../assets/cyberbridge_logo.svg';
import Sidebar from '../components/Sidebar';
import { useMenuHighlighting } from '../utils/menuUtils';

const steps = [
    { label: 'STEP 01', name: 'Company Details' },
    { label: 'STEP 02', name: 'Product Details' },
    { label: 'STEP 03', name: 'Market Information' },
];

function NoYesToggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
    return (
        <div className="cra-toggle">
            <button
                type="button"
                className={`cra-toggle-btn ${!value ? 'active no' : ''}`}
                onClick={() => onChange(false)}
            >
                No
            </button>
            <button
                type="button"
                className={`cra-toggle-btn ${value ? 'active yes' : ''}`}
                onClick={() => onChange(true)}
            >
                Yes
            </button>
        </div>
    );
}

export default function CraScopeAssessmentPage() {
    const [location, setLocation] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const {
        currentStep, nextStep, prevStep,
        companyDetails, setCompanyField,
        productDetails, setProductField,
        marketInfo, setMarketField,
        calculateScope,
    } = useCraScopeStore();

    const handleContinue = () => {
        if (currentStep === 3) {
            calculateScope();
            setLocation('/cra-scope-report');
        } else {
            nextStep();
        }
    };

    const handleBack = () => {
        if (currentStep === 0) {
            setLocation('/assessments');
        } else {
            prevStep();
        }
    };

    const renderStepper = () => (
        <div className="cra-stepper">
            <img src={cyberbridgeLogo} alt="CyberBridge" style={{ width: '160px', marginBottom: '20px' }} />
            <button
                type="button"
                className="cra-btn-login"
                onClick={() => setLocation('/assessments')}
            >
                Back to Assessments
            </button>
            {steps.map((step, idx) => (
                <div key={idx} className="cra-stepper-step">
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <div className={`cra-stepper-circle ${idx === currentStep ? 'active' : ''} ${idx < currentStep ? 'completed' : ''}`}>
                                {idx < currentStep ? <CheckCircleFilled style={{ fontSize: '24px' }} /> : idx + 1}
                            </div>
                            {idx < steps.length - 1 && (
                                <div className={`cra-stepper-line ${idx < currentStep ? 'completed' : ''}`} />
                            )}
                        </div>
                        <div className="cra-stepper-label">
                            <span className="cra-stepper-step-label">{step.label}</span>
                            <span className={`cra-stepper-step-name ${idx === currentStep ? 'active' : ''}`}>{step.name}</span>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );

    const renderCompanyStep = () => (
        <div>
            <h3 className="cra-section-heading">1.1 Company Information</h3>
            <table className="cra-question-table">
                <thead>
                    <tr>
                        <th style={{ width: '50px' }}>No.</th>
                        <th>Question</th>
                        <th style={{ width: '280px' }}>Answer</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td className="cra-question-number">01</td>
                        <td className="cra-question-text">What is your company name?</td>
                        <td className="cra-question-answer">
                            <input
                                type="text"
                                className="cra-input"
                                value={companyDetails.companyName}
                                onChange={(e) => setCompanyField('companyName', e.target.value)}
                                placeholder="Enter company name"
                            />
                        </td>
                    </tr>
                    <tr>
                        <td className="cra-question-number">02</td>
                        <td className="cra-question-text">What is your contact name?</td>
                        <td className="cra-question-answer">
                            <input
                                type="text"
                                className="cra-input"
                                value={companyDetails.contactName}
                                onChange={(e) => setCompanyField('contactName', e.target.value)}
                                placeholder="Enter contact name"
                            />
                        </td>
                    </tr>
                    <tr>
                        <td className="cra-question-number">03</td>
                        <td className="cra-question-text">
                            What is the size of your company in terms of the number of employees?
                        </td>
                        <td className="cra-question-answer">
                            <Select
                                className="cra-select"
                                value={companyDetails.companySize || undefined}
                                onChange={(val) => setCompanyField('companySize', val)}
                                placeholder="Select size"
                                style={{ width: '100%' }}
                                options={[
                                    { value: 'Micro: 0-9', label: 'Micro: 0-9' },
                                    { value: 'Small: 10-49', label: 'Small: 10-49' },
                                    { value: 'Medium: 50-249', label: 'Medium: 50-249' },
                                    { value: 'Large: 250+', label: 'Large: 250+' },
                                ]}
                            />
                        </td>
                    </tr>
                    <tr>
                        <td className="cra-question-number">04</td>
                        <td className="cra-question-text">What is the name of your product?</td>
                        <td className="cra-question-answer">
                            <input
                                type="text"
                                className="cra-input"
                                value={companyDetails.productName}
                                onChange={(e) => setCompanyField('productName', e.target.value)}
                                placeholder="Enter product name"
                            />
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    );

    const renderProductStep = () => (
        <div>
            <h3 className="cra-section-heading">2.1 Product Summary</h3>
            <table className="cra-question-table">
                <thead>
                    <tr>
                        <th style={{ width: '50px' }}>No.</th>
                        <th>Question</th>
                        <th style={{ width: '200px' }}>Answer</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td className="cra-question-number">01</td>
                        <td className="cra-question-text">
                            Is your product a digital product? i.e. does it contain hardware and/or software components{' '}
                            <Tooltip title="The CRA defines products in scope as 'product with digital elements' meaning any software or hardware product and its remote data processing solutions. Examples: bluetooth headphones, smart home devices, phone applications, computer operating systems, microprocessors.">
                                <InfoCircleOutlined className="cra-question-info" />
                            </Tooltip>
                        </td>
                        <td className="cra-question-answer">
                            <NoYesToggle value={productDetails.isDigitalProduct} onChange={(v) => setProductField('isDigitalProduct', v)} />
                        </td>
                    </tr>
                    <tr>
                        <td className="cra-question-number">02</td>
                        <td className="cra-question-text">
                            Does your product connect to a network or other devices directly or indirectly?{' '}
                            <Tooltip title="A direct connection is a link between your product and another device without any intermediary (e.g., USB to PC or WiFi). An indirect connection uses intermediaries, such as connection via a WiFi access point.">
                                <InfoCircleOutlined className="cra-question-info" />
                            </Tooltip>
                        </td>
                        <td className="cra-question-answer">
                            <NoYesToggle value={productDetails.connectsToNetwork} onChange={(v) => setProductField('connectsToNetwork', v)} />
                        </td>
                    </tr>
                    <tr>
                        <td className="cra-question-number">03</td>
                        <td className="cra-question-text">
                            Is your product standalone software as a service (SaaS)?{' '}
                            <Tooltip title="Standalone SaaS examples: a pure cloud productivity suite, Dropbox, Office 365, or a CRM not tied to a device.">
                                <InfoCircleOutlined className="cra-question-info" />
                            </Tooltip>
                        </td>
                        <td className="cra-question-answer">
                            <NoYesToggle value={productDetails.isSaaS} onChange={(v) => setProductField('isSaaS', v)} />
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    );

    const renderMarketStep = () => (
        <div>
            <h3 className="cra-section-heading">3.1 Market Summary</h3>
            <table className="cra-question-table">
                <thead>
                    <tr>
                        <th style={{ width: '50px' }}>No.</th>
                        <th>Question</th>
                        <th style={{ width: '200px' }}>Answer</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td className="cra-question-number">01</td>
                        <td className="cra-question-text">
                            Will you be "placing" or "making available" products on the EU internal single market?{' '}
                            <Tooltip title="The CRA distinguishes between 'placing on the market' (first making available in the EU market) and 'making available on the market' (any supply of a product for distribution, consumption, or use in the EU market, for payment or free).">
                                <InfoCircleOutlined className="cra-question-info" />
                            </Tooltip>
                        </td>
                        <td className="cra-question-answer">
                            <NoYesToggle value={marketInfo.euMarket} onChange={(v) => setMarketField('euMarket', v)} />
                        </td>
                    </tr>
                    <tr>
                        <td className="cra-question-number">02</td>
                        <td className="cra-question-text">
                            Does your product already comply with one or more of the following EU regulations?
                            <ul style={{ margin: '8px 0 0 16px', fontSize: '13px', color: '#64748b' }}>
                                <li>Medical Devices Regulation (MDR)</li>
                                <li>In Vitro Diagnostic Regulation (IVDR)</li>
                                <li>General Safety Regulation (GSR)</li>
                                <li>European Aviation Safety Agency (EASA)</li>
                                <li>Defence Products Directive</li>
                            </ul>
                            <Tooltip title="Check 'Yes' if your product complies with any of the listed regulations. Products for exclusive military use are out of scope.">
                                <InfoCircleOutlined className="cra-question-info" />
                            </Tooltip>
                        </td>
                        <td className="cra-question-answer">
                            <NoYesToggle value={marketInfo.compliesWithRegulations} onChange={(v) => setMarketField('compliesWithRegulations', v)} />
                        </td>
                    </tr>
                    <tr>
                        <td className="cra-question-number">03</td>
                        <td className="cra-question-text">
                            Are you a product manufacturer including software development, importer, or distributor?{' '}
                            <Tooltip title="Manufacturer: Designs or manufactures and markets the product under its own name or trademark. Importer: Brings a product from outside the EU/EEA. Distributor: Makes an EU product available as a reseller or wholesaler.">
                                <InfoCircleOutlined className="cra-question-info" />
                            </Tooltip>
                        </td>
                        <td className="cra-question-answer">
                            <Select
                                className="cra-select"
                                value={marketInfo.operatorRole || undefined}
                                onChange={(val) => setMarketField('operatorRole', val)}
                                placeholder="Select role"
                                style={{ width: '100%' }}
                                options={[
                                    { value: 'Manufacturer', label: 'Manufacturer' },
                                    { value: 'Importer', label: 'Importer' },
                                    { value: 'Distributor', label: 'Distributor' },
                                ]}
                            />
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    );

    const renderReviewStep = () => {
        const collapseItems = [
            {
                key: '1',
                label: 'Section 1 - Company Details',
                children: (
                    <table className="cra-question-table review">
                        <tbody>
                            <tr><td className="cra-question-number">01</td><td>Company Name</td><td><strong>{companyDetails.companyName || '—'}</strong></td></tr>
                            <tr><td className="cra-question-number">02</td><td>Contact Name</td><td><strong>{companyDetails.contactName || '—'}</strong></td></tr>
                            <tr><td className="cra-question-number">03</td><td>Company Size</td><td><strong>{companyDetails.companySize || '—'}</strong></td></tr>
                            <tr><td className="cra-question-number">04</td><td>Product Name</td><td><strong>{companyDetails.productName || '—'}</strong></td></tr>
                        </tbody>
                    </table>
                ),
            },
            {
                key: '2',
                label: 'Section 2 - Product Details',
                children: (
                    <table className="cra-question-table review">
                        <tbody>
                            <tr><td className="cra-question-number">01</td><td>Is your product a digital product?</td><td><strong>{productDetails.isDigitalProduct ? 'Yes' : 'No'}</strong></td></tr>
                            <tr><td className="cra-question-number">02</td><td>Does your product connect to a network?</td><td><strong>{productDetails.connectsToNetwork ? 'Yes' : 'No'}</strong></td></tr>
                            <tr><td className="cra-question-number">03</td><td>Is your product standalone SaaS?</td><td><strong>{productDetails.isSaaS ? 'Yes' : 'No'}</strong></td></tr>
                        </tbody>
                    </table>
                ),
            },
            {
                key: '3',
                label: 'Section 3 - Market Information',
                children: (
                    <table className="cra-question-table review">
                        <tbody>
                            <tr><td className="cra-question-number">01</td><td>Placing/making available on EU market?</td><td><strong>{marketInfo.euMarket ? 'Yes' : 'No'}</strong></td></tr>
                            <tr><td className="cra-question-number">02</td><td>Complies with listed EU regulations?</td><td><strong>{marketInfo.compliesWithRegulations ? 'Yes' : 'No'}</strong></td></tr>
                            <tr><td className="cra-question-number">03</td><td>Operator role</td><td><strong>{marketInfo.operatorRole || '—'}</strong></td></tr>
                        </tbody>
                    </table>
                ),
            },
        ];

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

    const stepContent = [renderCompanyStep, renderProductStep, renderMarketStep, renderReviewStep];

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
                            <div className="cra-content-card">
                                {stepContent[currentStep]()}
                            </div>
                            <div className="cra-footer">
                                <button className="cra-btn-back" onClick={handleBack}>
                                    Go Back
                                </button>
                                <button className="cra-btn-continue" onClick={handleContinue}>
                                    {currentStep === 3 ? 'Submit' : 'Continue'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
