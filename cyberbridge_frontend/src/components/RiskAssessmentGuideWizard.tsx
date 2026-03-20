// src/components/RiskAssessmentGuideWizard.tsx
import React, { useState } from 'react';
import { Modal, Steps } from 'antd';
import {
    ScheduleOutlined,
    AlertOutlined,
    DashboardOutlined,
    LinkOutlined,
    ToolOutlined,
    TableOutlined,
    BulbOutlined,
    SyncOutlined,
    LeftOutlined,
    RightOutlined,
    BookOutlined,
    ArrowRightOutlined,
    CheckCircleOutlined
} from '@ant-design/icons';

const steps = [
    {
        title: 'Overview',
        icon: <ScheduleOutlined />,
        description: 'What is Risk Assessment?',
        content: {
            heading: 'ISO 27001 Risk Assessment',
            body: 'Risk Assessment adds quantitative scoring to your risks using the ISO 27001 5x5 risk matrix. Each risk is scored by Impact (1-5) x Likelihood (1-5), producing a score from 1 to 25. This provides a standardised, repeatable way to measure and compare risks across your organisation.',
            tip: 'You can create multiple assessments per risk over time to track how risk scores evolve as you implement controls and treatments.'
        }
    },
    {
        title: 'Registry Link',
        icon: <SyncOutlined />,
        description: 'How assessments update the Risk Register',
        content: {
            heading: 'Connection to the Risk Register',
            body: 'Risk Assessment is directly linked to the Risk Register. When you create or update an assessment, the system automatically syncs the scores back to the corresponding risk entry in the Risk Register.',
            syncInfo: true,
            tip: 'If a risk has multiple assessments (e.g. #1, #2, #3), only the latest assessment (#3) is synced to the Risk Register. Earlier assessments are kept as history.'
        }
    },
    {
        title: 'Assessment',
        icon: <DashboardOutlined />,
        description: 'Tab 1: Score your risks',
        content: {
            heading: 'Tab 1 - Assessment',
            body: 'This is where you score the risk. Set Impact and Likelihood values (1-5) for each risk perspective:',
            scoreTypes: true,
            tip: 'Start by setting the Inherent Risk (before any controls). Then set Current Risk to reflect existing mitigations. Target Risk is your goal state.'
        }
    },
    {
        title: 'Connections',
        icon: <LinkOutlined />,
        description: 'Tab 2: Link assets, controls & objectives',
        content: {
            heading: 'Tab 2 - Controls & Connections',
            body: 'Connect your risk to the broader compliance ecosystem. Use the connection boards to link:',
            connections: true,
            tip: 'These connections build your compliance chain - showing how assets are protected by controls, governed by policies, and aligned to framework objectives.'
        }
    },
    {
        title: 'Treatment',
        icon: <ToolOutlined />,
        description: 'Tab 3: Plan risk treatment',
        content: {
            heading: 'Tab 3 - Treatment',
            body: 'After linking controls, assess the Residual Risk (what remains after treatment). Then create action items to track the work needed to reach your target risk level.',
            treatment: true,
            tip: 'When all actions are complete and the residual score meets your target, click "Complete Assessment" to mark it done. This updates the Risk Register status to "Assessed".'
        }
    },
    {
        title: 'Score Matrix',
        icon: <TableOutlined />,
        description: 'Understanding the 5x5 matrix',
        content: {
            heading: 'The 5x5 Risk Matrix',
            body: 'Scores map to severity levels as follows:',
            matrix: true
        }
    },
    {
        title: 'Tips',
        icon: <BulbOutlined />,
        description: 'Best practices',
        content: {
            heading: 'Best Practices',
            body: '',
            tips: [
                'Start from the Risk Register - click the "Assess" button on any risk to jump directly to its assessment.',
                'Always set Inherent Risk first (before controls), then Current Risk (with controls in place).',
                'Use the Impact Loss Analysis fields to document potential consequences across Health, Financial, Service, Legal, and Reputation dimensions.',
                'Create a new assessment periodically (e.g. quarterly) to track how your risk profile evolves over time.',
                'Link controls and assets in Tab 2 to build a complete picture of how the risk is mitigated.',
                'The latest assessment always syncs to the Risk Register - earlier assessments are preserved as audit history.'
            ]
        }
    }
];

const modalStyles = `
    .risk-assessment-guide-modal .ant-modal-content {
        border-radius: 16px;
        overflow: hidden;
    }
    .risk-assessment-guide-modal .ant-modal-header {
        border-bottom: none;
        padding: 24px 24px 0;
    }
    .risk-assessment-guide-modal .ant-modal-body {
        padding: 16px 24px 24px;
    }
    .risk-assessment-guide-modal .ant-steps-item-title {
        font-size: 12px !important;
    }
    .risk-assessment-guide-modal .ant-steps-item-icon {
        font-size: 14px;
    }
    .ra-guide-step-content {
        min-height: 280px;
        display: flex;
        flex-direction: column;
        padding: 24px;
        background: linear-gradient(135deg, #f8faff 0%, #f0f7ff 100%);
        border-radius: 12px;
        margin-top: 20px;
    }
    .ra-guide-step-heading {
        font-size: 20px;
        font-weight: 700;
        color: var(--primary-navy, #1e293b);
        margin: 0 0 16px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .ra-guide-step-body {
        font-size: 15px;
        line-height: 1.7;
        color: #475569;
        margin: 0 0 16px 0;
    }
    .ra-guide-tip {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 12px 16px;
        background: #fffbeb;
        border-radius: 8px;
        border-left: 3px solid #f59e0b;
        margin-top: auto;
    }
    .ra-guide-tip-icon {
        color: #f59e0b;
        font-size: 16px;
        margin-top: 2px;
        flex-shrink: 0;
    }
    .ra-guide-tip-text {
        font-size: 13px;
        color: #92400e;
        margin: 0;
        line-height: 1.5;
    }
    .ra-guide-info-rows {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 16px;
    }
    .ra-guide-info-row {
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
    .ra-guide-info-row-icon {
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
    .ra-guide-score-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 6px;
        color: white;
        font-weight: 700;
        font-size: 12px;
        margin-right: 6px;
    }
    .ra-guide-matrix-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 16px;
        font-size: 13px;
    }
    .ra-guide-matrix-table th,
    .ra-guide-matrix-table td {
        border: 1px solid #e2e8f0;
        padding: 8px 12px;
        text-align: center;
    }
    .ra-guide-matrix-table th {
        background: #f8fafc;
        font-weight: 600;
        color: #334155;
    }
    .ra-guide-tips-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .ra-guide-tips-list li {
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
    .ra-guide-tips-list li .tip-bullet {
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
    .ra-guide-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 20px;
    }
    .ra-guide-nav-btn {
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
    .ra-guide-nav-btn:hover {
        transform: translateY(-1px);
    }
    .ra-guide-nav-btn.prev {
        background: #f1f5f9;
        color: #475569;
    }
    .ra-guide-nav-btn.prev:hover {
        background: #e2e8f0;
    }
    .ra-guide-nav-btn.next {
        background: linear-gradient(135deg, #0f386a, #1e68a3);
        color: white;
        box-shadow: 0 4px 12px rgba(15, 56, 106, 0.3);
    }
    .ra-guide-nav-btn.next:hover {
        box-shadow: 0 6px 20px rgba(15, 56, 106, 0.4);
    }
    .ra-guide-nav-btn.finish {
        background: linear-gradient(135deg, #10b981, #34d399);
        color: white;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    .ra-guide-nav-btn.finish:hover {
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
    }
    .ra-guide-progress {
        font-size: 13px;
        color: #94a3b8;
        font-weight: 500;
    }
    .ra-guide-sync-flow {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-bottom: 16px;
        flex-wrap: wrap;
    }
    .ra-guide-sync-box {
        padding: 10px 18px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 13px;
        color: white;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .ra-guide-sync-arrow {
        font-size: 18px;
        color: #94a3b8;
    }
`;

const RiskAssessmentGuideWizard: React.FC = () => {
    const [open, setOpen] = useState(false);
    const [current, setCurrent] = useState(0);

    const handleOpen = () => {
        setCurrent(0);
        setOpen(true);
    };

    const handleClose = () => {
        setOpen(false);
    };

    const next = () => setCurrent(prev => Math.min(prev + 1, steps.length - 1));
    const prev = () => setCurrent(prev => Math.max(prev - 1, 0));

    const step = steps[current];
    const isLast = current === steps.length - 1;
    const isFirst = current === 0;

    return (
        <>
            <style>{modalStyles}</style>
            <button
                onClick={handleOpen}
                style={{
                    background: 'linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa)',
                    color: '#ffffff',
                    border: '2px solid rgba(255,255,255,0.2)',
                    borderRadius: '10px',
                    padding: '10px 18px',
                    fontSize: '13px',
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
                <span style={{ display: 'flex', alignItems: 'center', fontSize: '15px' }}>
                    <BookOutlined />
                </span>
                Assessment Guide
            </button>

            <Modal
                open={open}
                onCancel={handleClose}
                footer={null}
                width={920}
                centered
                destroyOnClose
                className="risk-assessment-guide-modal"
                title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <ScheduleOutlined style={{ fontSize: '22px', color: '#0f386a' }} />
                        <span style={{ fontSize: '18px', fontWeight: 700, color: 'var(--primary-navy, #1e293b)' }}>
                            Risk Assessment Guide
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

                <div className="ra-guide-step-content">
                    <h3 className="ra-guide-step-heading">
                        {step.icon}
                        {step.content.heading}
                    </h3>

                    {step.content.body && (
                        <p className="ra-guide-step-body">{step.content.body}</p>
                    )}

                    {/* Sync Info (Registry Link step) */}
                    {'syncInfo' in step.content && step.content.syncInfo && (
                        <>
                            <div className="ra-guide-sync-flow">
                                <div className="ra-guide-sync-box" style={{ background: 'linear-gradient(135deg, #0f386a, #1e68a3)' }}>
                                    Latest Assessment
                                </div>
                                <span className="ra-guide-sync-arrow"><ArrowRightOutlined /></span>
                                <div className="ra-guide-sync-box" style={{ background: 'linear-gradient(135deg, #f59e0b, #fbbf24)' }}>
                                    Auto-Sync
                                </div>
                                <span className="ra-guide-sync-arrow"><ArrowRightOutlined /></span>
                                <div className="ra-guide-sync-box" style={{ background: 'linear-gradient(135deg, #dc2626, #ef4444)' }}>
                                    Risk Register
                                </div>
                            </div>
                            <div className="ra-guide-info-rows">
                                <div className="ra-guide-info-row">
                                    <span className="ra-guide-info-row-icon" style={{ background: '#dc2626' }}><AlertOutlined /></span>
                                    <span><strong>Inherent Risk Score</strong>{' -> '}maps to the risk's <strong>Severity</strong> in the Risk Register</span>
                                </div>
                                <div className="ra-guide-info-row">
                                    <span className="ra-guide-info-row-icon" style={{ background: '#f59e0b' }}><DashboardOutlined /></span>
                                    <span><strong>Inherent Likelihood</strong>{' -> '}maps to the risk's <strong>Likelihood</strong> field in the Risk Register</span>
                                </div>
                                <div className="ra-guide-info-row">
                                    <span className="ra-guide-info-row-icon" style={{ background: '#10b981' }}><CheckCircleOutlined /></span>
                                    <span><strong>Residual Risk Score</strong>{' -> '}maps to the risk's <strong>Residual Risk</strong> in the Risk Register</span>
                                </div>
                                <div className="ra-guide-info-row">
                                    <span className="ra-guide-info-row-icon" style={{ background: '#8b5cf6' }}><SyncOutlined /></span>
                                    <span><strong>Assessment Status</strong> (Draft/In Progress/Completed){' -> '}updates the risk's <strong>Assessment Status</strong></span>
                                </div>
                            </div>
                        </>
                    )}

                    {/* Score Types (Assessment tab step) */}
                    {'scoreTypes' in step.content && step.content.scoreTypes && (
                        <div className="ra-guide-info-rows">
                            <div className="ra-guide-info-row">
                                <span className="ra-guide-info-row-icon" style={{ background: '#dc2626' }}><AlertOutlined /></span>
                                <span><strong>Inherent Risk</strong> - The raw risk before any controls are applied. This is your worst-case scenario.</span>
                            </div>
                            <div className="ra-guide-info-row">
                                <span className="ra-guide-info-row-icon" style={{ background: '#f59e0b' }}><DashboardOutlined /></span>
                                <span><strong>Current Risk</strong> - The risk level with your existing controls in place. This reflects reality today.</span>
                            </div>
                            <div className="ra-guide-info-row">
                                <span className="ra-guide-info-row-icon" style={{ background: '#0f386a' }}><ScheduleOutlined /></span>
                                <span><strong>Target Risk</strong> - The risk level you aim to achieve after planned improvements. This is your goal.</span>
                            </div>
                        </div>
                    )}

                    {/* Connections (Controls & Connections step) */}
                    {'connections' in step.content && step.content.connections && (
                        <div className="ra-guide-info-rows">
                            <div className="ra-guide-info-row">
                                <span className="ra-guide-info-row-icon" style={{ background: '#0f386a' }}>
                                    <span style={{ fontSize: 11 }}>A</span>
                                </span>
                                <span><strong>Assets</strong> - The products, systems, or data that are exposed to this risk.</span>
                            </div>
                            <div className="ra-guide-info-row">
                                <span className="ra-guide-info-row-icon" style={{ background: '#8b5cf6' }}>
                                    <span style={{ fontSize: 11 }}>C</span>
                                </span>
                                <span><strong>Controls</strong> - The security measures that mitigate this risk (e.g. encryption, access control).</span>
                            </div>
                            <div className="ra-guide-info-row">
                                <span className="ra-guide-info-row-icon" style={{ background: '#10b981' }}>
                                    <span style={{ fontSize: 11 }}>O</span>
                                </span>
                                <span><strong>Objectives</strong> - The framework objectives that this risk relates to.</span>
                            </div>
                        </div>
                    )}

                    {/* Treatment (Treatment step) */}
                    {'treatment' in step.content && step.content.treatment && (
                        <div className="ra-guide-info-rows">
                            <div className="ra-guide-info-row">
                                <span className="ra-guide-info-row-icon" style={{ background: '#10b981' }}><CheckCircleOutlined /></span>
                                <span><strong>Residual Risk</strong> - Set the Impact and Likelihood that remain after all treatments. This score syncs to the Risk Register's Residual Risk field.</span>
                            </div>
                            <div className="ra-guide-info-row">
                                <span className="ra-guide-info-row-icon" style={{ background: '#0f386a' }}><ToolOutlined /></span>
                                <span><strong>Action Items</strong> - Create tasks with descriptions, due dates, owners, and statuses to track risk treatment work.</span>
                            </div>
                            <div className="ra-guide-info-row">
                                <span className="ra-guide-info-row-icon" style={{ background: '#8b5cf6' }}><CheckCircleOutlined /></span>
                                <span><strong>Complete Assessment</strong> - When done, mark the assessment as "Completed". This changes the Risk Register status from "Assessment in progress" to "Assessed".</span>
                            </div>
                        </div>
                    )}

                    {/* Score Matrix */}
                    {'matrix' in step.content && step.content.matrix && (
                        <>
                            <table className="ra-guide-matrix-table">
                                <thead>
                                    <tr>
                                        <th>Score Range</th>
                                        <th>Severity</th>
                                        <th>Colour</th>
                                        <th>Example</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td><strong>1 - 4</strong></td>
                                        <td>Low</td>
                                        <td><span className="ra-guide-score-badge" style={{ background: '#52c41a' }}>Low</span></td>
                                        <td>1x1=1, 2x2=4</td>
                                    </tr>
                                    <tr>
                                        <td><strong>5 - 10</strong></td>
                                        <td>Medium</td>
                                        <td><span className="ra-guide-score-badge" style={{ background: '#faad14' }}>Medium</span></td>
                                        <td>2x3=6, 2x5=10</td>
                                    </tr>
                                    <tr>
                                        <td><strong>12 - 16</strong></td>
                                        <td>High</td>
                                        <td><span className="ra-guide-score-badge" style={{ background: '#fa8c16' }}>High</span></td>
                                        <td>3x4=12, 4x4=16</td>
                                    </tr>
                                    <tr>
                                        <td><strong>20 - 25</strong></td>
                                        <td>Critical</td>
                                        <td><span className="ra-guide-score-badge" style={{ background: '#f5222d' }}>Critical</span></td>
                                        <td>4x5=20, 5x5=25</td>
                                    </tr>
                                </tbody>
                            </table>
                            <div className="ra-guide-info-row" style={{ background: '#f0f7ff' }}>
                                <span className="ra-guide-info-row-icon" style={{ background: '#0f386a' }}><BulbOutlined /></span>
                                <span><strong>Likelihood mapping:</strong> 1-2 = Low, 3 = Medium, 4 = High, 5 = Critical. This is used when syncing to the Risk Register's categorical Likelihood field.</span>
                            </div>
                        </>
                    )}

                    {/* Tips */}
                    {'tips' in step.content && step.content.tips && (
                        <ul className="ra-guide-tips-list">
                            {step.content.tips.map((tip, i) => (
                                <li key={i}>
                                    <span className="tip-bullet">{i + 1}</span>
                                    <span>{tip}</span>
                                </li>
                            ))}
                        </ul>
                    )}

                    {step.content.tip && (
                        <div className="ra-guide-tip">
                            <BulbOutlined className="ra-guide-tip-icon" />
                            <p className="ra-guide-tip-text">{step.content.tip}</p>
                        </div>
                    )}
                </div>

                <div className="ra-guide-nav">
                    <button
                        className="ra-guide-nav-btn prev"
                        onClick={prev}
                        style={{ visibility: isFirst ? 'hidden' : 'visible' }}
                    >
                        <LeftOutlined /> Previous
                    </button>
                    <span className="ra-guide-progress">
                        {current + 1} of {steps.length}
                    </span>
                    {isLast ? (
                        <button className="ra-guide-nav-btn finish" onClick={handleClose}>
                            Got it!
                        </button>
                    ) : (
                        <button className="ra-guide-nav-btn next" onClick={next}>
                            Next <RightOutlined />
                        </button>
                    )}
                </div>
            </Modal>
        </>
    );
};

export default RiskAssessmentGuideWizard;
