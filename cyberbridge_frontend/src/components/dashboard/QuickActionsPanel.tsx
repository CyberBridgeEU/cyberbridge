// src/components/dashboard/QuickActionsPanel.tsx
import React from 'react';

interface QuickActionsPanelProps {
    title?: string;
    children: React.ReactNode;
}

const QuickActionsPanel: React.FC<QuickActionsPanelProps> = ({
    title = 'Quick Actions',
    children
}) => {
    return (
        <div
            className="dashboard-quick-actions-panel"
        >
            <h4 className="dashboard-quick-actions-title" style={{
                margin: '0 0 16px 0',
                color: 'var(--primary-navy)',
                fontSize: '16px',
                fontWeight: 600
            }}>
                {title}
            </h4>
            <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '12px'
            }}>
                {children}
            </div>
        </div>
    );
};

export default QuickActionsPanel;
