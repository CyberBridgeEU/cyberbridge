// src/components/dashboard/DashboardSection.tsx
import React from 'react';

interface DashboardSectionProps {
    title: string;
    subtitle?: string;
    children: React.ReactNode;
    style?: React.CSSProperties;
}

const DashboardSection: React.FC<DashboardSectionProps> = ({
    title,
    subtitle,
    children,
    style
}) => {
    return (
        <div
            className="page-section"
            style={style}
        >
            <h3 className="section-title" style={{
                color: 'var(--primary-navy)',
                fontSize: '20px',
                fontWeight: 700,
                margin: '0 0 18px 0',
                display: 'inline-block',
                letterSpacing: '-0.025em',
                position: 'relative',
                paddingBottom: '12px'
            }}>
                {title}
                <span style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    width: '60px',
                    height: '3px',
                    background: 'linear-gradient(90deg, #0f386a, #1e68a3, #9BCBEF, #0a2d55)',
                    borderRadius: '2px'
                }} />
            </h3>
            {subtitle && (
                <p style={{
                    color: 'var(--text-dark-gray)',
                    fontSize: '15px',
                    margin: '0 0 20px 0',
                    lineHeight: 1.6,
                    fontWeight: 400
                }}>
                    {subtitle}
                </p>
            )}
            {children}
        </div>
    );
};

export default DashboardSection;
