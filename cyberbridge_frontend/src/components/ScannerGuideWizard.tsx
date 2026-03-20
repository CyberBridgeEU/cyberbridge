// src/components/ScannerGuideWizard.tsx
import React, { useState } from 'react';
import { Modal, Steps } from 'antd';
import {
    BulbOutlined,
    LeftOutlined,
    RightOutlined,
    BookOutlined
} from '@ant-design/icons';

export interface GuideInfoRow {
    icon: React.ReactNode;
    iconBg: string;
    text: React.ReactNode;
}

export interface GuideTableRow {
    cells: React.ReactNode[];
}

export interface GuideStepContent {
    heading: string;
    body?: string;
    infoRows?: GuideInfoRow[];
    tip?: string;
    tips?: string[];
    table?: {
        headers: string[];
        rows: GuideTableRow[];
    };
}

export interface GuideStep {
    title: string;
    icon: React.ReactNode;
    description: string;
    content: GuideStepContent;
}

interface ScannerGuideWizardProps {
    steps: GuideStep[];
    title: string;
    icon: React.ReactNode;
    buttonLabel?: string;
}

const modalStyles = `
    .scanner-guide-modal .ant-modal-content {
        border-radius: 16px;
        overflow: hidden;
    }
    .scanner-guide-modal .ant-modal-header {
        border-bottom: none;
        padding: 24px 24px 0;
    }
    .scanner-guide-modal .ant-modal-body {
        padding: 16px 24px 24px;
    }
    .scanner-guide-modal .ant-steps-item-title {
        font-size: 12px !important;
    }
    .scanner-guide-modal .ant-steps-item-icon {
        font-size: 14px;
    }
    .scanner-guide-step-content {
        min-height: 280px;
        display: flex;
        flex-direction: column;
        padding: 24px;
        background: linear-gradient(135deg, #f8faff 0%, #f0f7ff 100%);
        border-radius: 12px;
        margin-top: 20px;
    }
    .scanner-guide-step-heading {
        font-size: 20px;
        font-weight: 700;
        color: var(--primary-navy, #1e293b);
        margin: 0 0 16px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .scanner-guide-step-body {
        font-size: 15px;
        line-height: 1.7;
        color: #475569;
        margin: 0 0 16px 0;
    }
    .scanner-guide-tip {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 12px 16px;
        background: #fffbeb;
        border-radius: 8px;
        border-left: 3px solid #f59e0b;
        margin-top: auto;
    }
    .scanner-guide-tip-icon {
        color: #f59e0b;
        font-size: 16px;
        margin-top: 2px;
        flex-shrink: 0;
    }
    .scanner-guide-tip-text {
        font-size: 13px;
        color: #92400e;
        margin: 0;
        line-height: 1.5;
    }
    .scanner-guide-info-rows {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-bottom: 16px;
    }
    .scanner-guide-info-row {
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
    .scanner-guide-info-row-icon {
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
    .scanner-guide-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 16px;
        font-size: 13px;
    }
    .scanner-guide-table th,
    .scanner-guide-table td {
        border: 1px solid #e2e8f0;
        padding: 8px 12px;
        text-align: center;
    }
    .scanner-guide-table th {
        background: #f8fafc;
        font-weight: 600;
        color: #334155;
    }
    .scanner-guide-tips-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .scanner-guide-tips-list li {
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
    .scanner-guide-tips-list li .tip-bullet {
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
    .scanner-guide-nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 20px;
    }
    .scanner-guide-nav-btn {
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
    .scanner-guide-nav-btn:hover {
        transform: translateY(-1px);
    }
    .scanner-guide-nav-btn.prev {
        background: #f1f5f9;
        color: #475569;
    }
    .scanner-guide-nav-btn.prev:hover {
        background: #e2e8f0;
    }
    .scanner-guide-nav-btn.next {
        background: linear-gradient(135deg, #0f386a, #1e68a3);
        color: white;
        box-shadow: 0 4px 12px rgba(15, 56, 106, 0.3);
    }
    .scanner-guide-nav-btn.next:hover {
        box-shadow: 0 6px 20px rgba(15, 56, 106, 0.4);
    }
    .scanner-guide-nav-btn.finish {
        background: linear-gradient(135deg, #10b981, #34d399);
        color: white;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    .scanner-guide-nav-btn.finish:hover {
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
    }
    .scanner-guide-progress {
        font-size: 13px;
        color: #94a3b8;
        font-weight: 500;
    }
`;

const ScannerGuideWizard: React.FC<ScannerGuideWizardProps> = ({
    steps,
    title,
    icon,
    buttonLabel = 'Scanner Guide'
}) => {
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
                {buttonLabel}
            </button>

            <Modal
                open={open}
                onCancel={handleClose}
                footer={null}
                width={920}
                centered
                destroyOnClose
                className="scanner-guide-modal"
                title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontSize: '22px', color: '#0f386a', display: 'flex', alignItems: 'center' }}>{icon}</span>
                        <span style={{ fontSize: '18px', fontWeight: 700, color: 'var(--primary-navy, #1e293b)' }}>
                            {title}
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

                <div className="scanner-guide-step-content">
                    <h3 className="scanner-guide-step-heading">
                        {step.icon}
                        {step.content.heading}
                    </h3>

                    {step.content.body && (
                        <p className="scanner-guide-step-body">{step.content.body}</p>
                    )}

                    {/* Info Rows */}
                    {step.content.infoRows && step.content.infoRows.length > 0 && (
                        <div className="scanner-guide-info-rows">
                            {step.content.infoRows.map((row, i) => (
                                <div className="scanner-guide-info-row" key={i}>
                                    <span className="scanner-guide-info-row-icon" style={{ background: row.iconBg }}>
                                        {row.icon}
                                    </span>
                                    <span>{row.text}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Table */}
                    {step.content.table && (
                        <table className="scanner-guide-table">
                            <thead>
                                <tr>
                                    {step.content.table.headers.map((h, i) => (
                                        <th key={i}>{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {step.content.table.rows.map((row, i) => (
                                    <tr key={i}>
                                        {row.cells.map((cell, j) => (
                                            <td key={j}>{cell}</td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}

                    {/* Numbered Tips List */}
                    {step.content.tips && step.content.tips.length > 0 && (
                        <ul className="scanner-guide-tips-list">
                            {step.content.tips.map((tip, i) => (
                                <li key={i}>
                                    <span className="tip-bullet">{i + 1}</span>
                                    <span>{tip}</span>
                                </li>
                            ))}
                        </ul>
                    )}

                    {/* Yellow Callout Tip */}
                    {step.content.tip && (
                        <div className="scanner-guide-tip">
                            <BulbOutlined className="scanner-guide-tip-icon" />
                            <p className="scanner-guide-tip-text">{step.content.tip}</p>
                        </div>
                    )}
                </div>

                <div className="scanner-guide-nav">
                    <button
                        className="scanner-guide-nav-btn prev"
                        onClick={prev}
                        style={{ visibility: isFirst ? 'hidden' : 'visible' }}
                    >
                        <LeftOutlined /> Previous
                    </button>
                    <span className="scanner-guide-progress">
                        {current + 1} of {steps.length}
                    </span>
                    {isLast ? (
                        <button className="scanner-guide-nav-btn finish" onClick={handleClose}>
                            Got it!
                        </button>
                    ) : (
                        <button className="scanner-guide-nav-btn next" onClick={next}>
                            Next <RightOutlined />
                        </button>
                    )}
                </div>
            </Modal>
        </>
    );
};

export default ScannerGuideWizard;
