// src/components/dashboard/UserGuideWizard.tsx
import React, { useState } from 'react';
import { Modal, Steps } from 'antd';
import {
    AppstoreOutlined,
    ShoppingOutlined,
    AlertOutlined,
    FileProtectOutlined,
    FormOutlined,
    CheckSquareOutlined,
    BulbOutlined,
    SafetyCertificateOutlined,
    LeftOutlined,
    RightOutlined,
    BookOutlined,
    ControlOutlined,
    ApartmentOutlined,
    ArrowRightOutlined
} from '@ant-design/icons';

const chainNodes = [
    { label: 'Assets', color: '#0f386a', icon: <ShoppingOutlined /> },
    { label: 'Risks', color: '#dc2626', icon: <AlertOutlined /> },
    { label: 'Controls', color: '#8b5cf6', icon: <ControlOutlined /> },
    { label: 'Policies', color: '#06b6d4', icon: <FileProtectOutlined /> },
    { label: 'Objectives', color: '#10b981', icon: <CheckSquareOutlined /> },
];

const steps = [
    {
        title: 'Framework',
        icon: <AppstoreOutlined />,
        description: 'Start by selecting a compliance framework',
        content: {
            heading: 'Step 1: Seed a Framework',
            body: 'Navigate to Framework Management and seed a compliance framework (e.g. ISO 27001, NIST CSF, CRA). This populates the system with the relevant chapters, objectives, and assessment questions for your chosen standard.',
            tip: 'You can seed multiple frameworks and manage them independently.'
        }
    },
    {
        title: 'Assets',
        icon: <ShoppingOutlined />,
        description: 'Add your products and assets',
        content: {
            heading: 'Step 2: Register Your Assets',
            body: 'Go to Product Registration to add the assets, products, or systems that fall under your compliance scope. Fill in the product details, type, economic operator, and criticality level.',
            tip: "Assets are the starting point of the compliance chain - risks, controls, and policies all trace back to what you're protecting."
        }
    },
    {
        title: 'Risks',
        icon: <AlertOutlined />,
        description: 'Document and assess your risks',
        content: {
            heading: 'Step 3: Identify & Assess Risks',
            body: 'Navigate to Risk Registration to document potential risks. For each risk, define its severity, likelihood, status, and associate it with relevant assets. This forms your risk register - the threats and vulnerabilities that your assets face.',
            tip: 'Each risk should be tied to an asset. This connection drives which controls and policies you need.'
        }
    },
    {
        title: 'Controls',
        icon: <ControlOutlined />,
        description: 'Implement security controls',
        content: {
            heading: 'Step 4: Register Controls',
            body: 'Go to Control Register to document the technical and organisational measures that mitigate your identified risks. Controls are the concrete actions or safeguards you put in place - for example, encryption, access control, or backup procedures. You can also browse the Controls Library for pre-built control suggestions.',
            tip: 'Controls are the bridge between your risks and your policies - they define what you actually do to address each risk.'
        }
    },
    {
        title: 'Policies',
        icon: <FileProtectOutlined />,
        description: 'Define your security policies',
        content: {
            heading: 'Step 5: Create Policies',
            body: 'Go to Policy Registration to create security and compliance policies. Link each policy to the relevant frameworks, objectives, and controls. Policies are the formal rules that govern how controls are applied and maintained across your organisation.',
            tip: 'Policies formalise your controls into documented rules. Map them to framework objectives to close the compliance loop.'
        }
    },
    {
        title: 'Assessments',
        icon: <FormOutlined />,
        description: 'Evaluate your compliance',
        content: {
            heading: 'Step 6: Run Assessments',
            body: 'Navigate to Assessments to start a new compliance assessment. Select a framework, answer the assessment questions, and track your progress. Completed assessments contribute to your overall compliance score.',
            tip: 'You can pause and resume assessments at any time.'
        }
    },
    {
        title: 'Objectives',
        icon: <CheckSquareOutlined />,
        description: 'Track and fulfil framework objectives',
        content: {
            heading: 'Step 7: Complete the Objectives Checklist',
            body: 'Go to the Objectives Checklist to review the specific objectives from your framework chapters. Mark objectives as compliant, upload evidence files, and link policies. This is where you track real progress against the standard.',
            tip: 'Upload evidence files directly to each objective for audit readiness.'
        }
    },
    {
        title: 'Chain',
        icon: <ApartmentOutlined />,
        description: 'How everything connects',
        content: {
            heading: 'The Compliance Chain',
            body: '',
            chain: true
        }
    },
    {
        title: 'Tips',
        icon: <BulbOutlined />,
        description: 'Get the most out of CyberBridge',
        content: {
            heading: 'Helpful Tips',
            body: '',
            tips: [
                'Use the Security Scanners to automate vulnerability detection on your assets.',
                'The AI Analysis feature provides intelligent remediation suggestions for scan results.',
                'Export assessment results and reports as PDF for sharing with stakeholders.',
                'Check the Correlations page to see how risks, policies, and objectives connect across frameworks.',
                'Use the dashboard statistics to monitor your overall compliance health at a glance.',
                'The Setup Wizard on the home page can walk you through initial configuration if needed.'
            ]
        }
    }
];

const modalStyles = `
    .user-guide-modal .ant-modal-content {
        border-radius: 16px;
        overflow: hidden;
    }
    .user-guide-modal .ant-modal-header {
        border-bottom: none;
        padding: 24px 24px 0;
    }
    .user-guide-modal .ant-modal-body {
        padding: 16px 24px 24px;
    }
    .user-guide-modal .ant-steps-item-title {
        font-size: 12px !important;
    }
    .user-guide-modal .ant-steps-item-icon {
        font-size: 14px;
    }
    .user-guide-step-content {
        min-height: 260px;
        display: flex;
        flex-direction: column;
        padding: 24px;
        background: linear-gradient(135deg, #f8faff 0%, #f0f7ff 100%);
        border-radius: 12px;
        margin-top: 20px;
    }
    .user-guide-step-heading {
        font-size: 20px;
        font-weight: 700;
        color: var(--primary-navy, #1e293b);
        margin: 0 0 16px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .user-guide-step-body {
        font-size: 15px;
        line-height: 1.7;
        color: #475569;
        margin: 0 0 16px 0;
    }
    .user-guide-tip {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 12px 16px;
        background: #fffbeb;
        border-radius: 8px;
        border-left: 3px solid #f59e0b;
        margin-top: auto;
    }
    .user-guide-tip-icon {
        color: #f59e0b;
        font-size: 16px;
        margin-top: 2px;
        flex-shrink: 0;
    }
    .user-guide-tip-text {
        font-size: 13px;
        color: #92400e;
        margin: 0;
        line-height: 1.5;
    }
    .user-guide-tips-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .user-guide-tips-list li {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 10px 14px;
        background: white;
        border-radius: 8px;
        font-size: 14px;
        line-height: 1.5;
        color: #475569;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .user-guide-tips-list li .tip-bullet {
        flex-shrink: 0;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: linear-gradient(135deg, #0f386a, #1e68a3);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
        font-weight: 700;
        margin-top: 1px;
    }
    .user-guide-chain {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        margin: 4px 0 18px 0;
        flex-wrap: wrap;
    }
    .user-guide-chain-node {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
    }
    .user-guide-chain-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        color: white;
        box-shadow: 0 3px 10px rgba(0,0,0,0.12);
    }
    .user-guide-chain-label {
        font-size: 12px;
        font-weight: 700;
        text-align: center;
    }
    .user-guide-chain-arrow {
        font-size: 18px;
        color: #cbd5e1;
        margin: 0 10px;
        margin-bottom: 20px;
    }
    .user-guide-chain-desc {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 2px;
    }
    .user-guide-chain-row {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 8px 12px;
        background: white;
        border-radius: 8px;
        font-size: 13.5px;
        line-height: 1.5;
        color: #475569;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .user-guide-chain-row-icon {
        flex-shrink: 0;
        width: 24px;
        height: 24px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        color: white;
        margin-top: 1px;
    }
    .user-guide-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 20px;
    }
    .user-guide-nav-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 10px 24px;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .user-guide-nav-btn:hover {
        transform: translateY(-1px);
    }
    .user-guide-nav-btn.prev {
        background: #f1f5f9;
        color: #475569;
    }
    .user-guide-nav-btn.prev:hover {
        background: #e2e8f0;
    }
    .user-guide-nav-btn.next {
        background: linear-gradient(135deg, #0f386a, #1e68a3);
        color: white;
        box-shadow: 0 4px 12px rgba(15, 56, 106, 0.3);
    }
    .user-guide-nav-btn.next:hover {
        box-shadow: 0 6px 20px rgba(15, 56, 106, 0.4);
    }
    .user-guide-nav-btn.finish {
        background: linear-gradient(135deg, #10b981, #34d399);
        color: white;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    .user-guide-nav-btn.finish:hover {
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
    }
    .user-guide-progress {
        font-size: 13px;
        color: #94a3b8;
        font-weight: 500;
    }
`;

interface UserGuideWizardProps {
    externalOpen?: boolean;
    onExternalClose?: () => void;
}

const UserGuideWizard: React.FC<UserGuideWizardProps> = ({ externalOpen, onExternalClose }) => {
    const [internalOpen, setInternalOpen] = useState(false);
    const [current, setCurrent] = useState(0);

    const isControlled = externalOpen !== undefined;
    const open = isControlled ? externalOpen : internalOpen;

    const handleOpen = () => {
        setCurrent(0);
        if (!isControlled) setInternalOpen(true);
    };

    const handleClose = () => {
        if (isControlled && onExternalClose) {
            onExternalClose();
        } else {
            setInternalOpen(false);
        }
    };

    // Reset step when opening externally
    React.useEffect(() => {
        if (externalOpen) setCurrent(0);
    }, [externalOpen]);

    const next = () => setCurrent(prev => Math.min(prev + 1, steps.length - 1));
    const prev = () => setCurrent(prev => Math.max(prev - 1, 0));

    const step = steps[current];
    const isLast = current === steps.length - 1;
    const isFirst = current === 0;

    return (
        <>
            <style>{modalStyles}</style>
            {!isControlled && (
                <button
                    onClick={handleOpen}
                    style={{
                        background: 'linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa)',
                        color: '#ffffff',
                        border: '2px solid rgba(255,255,255,0.2)',
                        borderRadius: '10px',
                        padding: '12px 22px',
                        fontSize: '14px',
                        fontWeight: 700,
                        cursor: 'pointer',
                        transition: 'all 0.3s ease',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '8px',
                        boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4), inset 0 1px 0 rgba(255,255,255,0.2)',
                        whiteSpace: 'nowrap',
                        position: 'relative',
                        overflow: 'hidden'
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'linear-gradient(135deg, #4f46e5, #7c3aed, #8b5cf6)';
                        e.currentTarget.style.transform = 'translateY(-2px) scale(1.02)';
                        e.currentTarget.style.boxShadow = '0 8px 25px rgba(99, 102, 241, 0.5), inset 0 1px 0 rgba(255,255,255,0.2)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa)';
                        e.currentTarget.style.transform = 'translateY(0) scale(1)';
                        e.currentTarget.style.boxShadow = '0 4px 15px rgba(99, 102, 241, 0.4), inset 0 1px 0 rgba(255,255,255,0.2)';
                    }}
                >
                    <span style={{ display: 'flex', alignItems: 'center', fontSize: '16px' }}>
                        <BookOutlined />
                    </span>
                    User Guide
                    <span style={{
                        background: 'rgba(255,255,255,0.25)',
                        padding: '1px 8px',
                        borderRadius: '6px',
                        fontSize: '11px',
                        fontWeight: 600,
                        letterSpacing: '0.5px'
                    }}>
                        NEW
                    </span>
                </button>
            )}

            <Modal
                open={open}
                onCancel={handleClose}
                footer={null}
                width={900}
                centered
                destroyOnClose
                className="user-guide-modal"
                title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <SafetyCertificateOutlined style={{ fontSize: '22px', color: '#0f386a' }} />
                        <span style={{ fontSize: '18px', fontWeight: 700, color: 'var(--primary-navy, #1e293b)' }}>
                            CyberBridge User Guide
                        </span>
                    </div>
                }
            >
                <Steps
                    current={current}
                    size="small"
                    onChange={(value) => setCurrent(value)}
                    items={steps.map(s => ({
                        title: s.title,
                        icon: s.icon
                    }))}
                    style={{ marginTop: 8 }}
                />

                <div className="user-guide-step-content">
                    <h3 className="user-guide-step-heading">
                        {step.icon}
                        {step.content.heading}
                    </h3>

                    {step.content.body && (
                        <p className="user-guide-step-body">{step.content.body}</p>
                    )}

                    {step.content.tip && (
                        <div className="user-guide-tip">
                            <BulbOutlined className="user-guide-tip-icon" />
                            <p className="user-guide-tip-text">{step.content.tip}</p>
                        </div>
                    )}

                    {'chain' in step.content && step.content.chain && (
                        <>
                            <div className="user-guide-chain">
                                {chainNodes.map((node, i) => (
                                    <React.Fragment key={node.label}>
                                        <div className="user-guide-chain-node">
                                            <div className="user-guide-chain-icon" style={{ background: node.color }}>
                                                {node.icon}
                                            </div>
                                            <span className="user-guide-chain-label" style={{ color: node.color }}>{node.label}</span>
                                        </div>
                                        {i < chainNodes.length - 1 && (
                                            <span className="user-guide-chain-arrow"><ArrowRightOutlined /></span>
                                        )}
                                    </React.Fragment>
                                ))}
                            </div>
                            <div className="user-guide-chain-desc">
                                <div className="user-guide-chain-row">
                                    <span className="user-guide-chain-row-icon" style={{ background: '#0f386a' }}><ShoppingOutlined /></span>
                                    <span><strong>Assets</strong> are the products and systems you need to protect. They are the starting point.</span>
                                </div>
                                <div className="user-guide-chain-row">
                                    <span className="user-guide-chain-row-icon" style={{ background: '#dc2626' }}><AlertOutlined /></span>
                                    <span><strong>Risks</strong> are the threats and vulnerabilities that each asset faces.</span>
                                </div>
                                <div className="user-guide-chain-row">
                                    <span className="user-guide-chain-row-icon" style={{ background: '#8b5cf6' }}><ControlOutlined /></span>
                                    <span><strong>Controls</strong> are the safeguards you implement to mitigate those risks.</span>
                                </div>
                                <div className="user-guide-chain-row">
                                    <span className="user-guide-chain-row-icon" style={{ background: '#06b6d4' }}><FileProtectOutlined /></span>
                                    <span><strong>Policies</strong> formalise controls into documented rules for your organisation.</span>
                                </div>
                                <div className="user-guide-chain-row">
                                    <span className="user-guide-chain-row-icon" style={{ background: '#10b981' }}><CheckSquareOutlined /></span>
                                    <span><strong>Objectives</strong> are the framework goals that your policies and controls fulfil, proving compliance.</span>
                                </div>
                            </div>
                        </>
                    )}

                    {'tips' in step.content && step.content.tips && (
                        <ul className="user-guide-tips-list">
                            {step.content.tips.map((tip, i) => (
                                <li key={i}>
                                    <span className="tip-bullet">{i + 1}</span>
                                    <span>{tip}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                <div className="user-guide-nav">
                    <button
                        className="user-guide-nav-btn prev"
                        onClick={prev}
                        style={{ visibility: isFirst ? 'hidden' : 'visible' }}
                    >
                        <LeftOutlined /> Previous
                    </button>
                    <span className="user-guide-progress">
                        {current + 1} of {steps.length}
                    </span>
                    {isLast ? (
                        <button className="user-guide-nav-btn finish" onClick={handleClose}>
                            Got it!
                        </button>
                    ) : (
                        <button className="user-guide-nav-btn next" onClick={next}>
                            Next <RightOutlined />
                        </button>
                    )}
                </div>
            </Modal>
        </>
    );
};

export default UserGuideWizard;
