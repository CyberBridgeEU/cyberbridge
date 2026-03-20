// src/components/dashboard/QuickActionButton.tsx
import React from 'react';

interface QuickActionButtonProps {
    label: string;
    icon: React.ReactNode;
    onClick: () => void;
    variant?: 'primary' | 'secondary' | 'success' | 'warning';
}

const variantStyles = {
    primary: {
        background: 'linear-gradient(135deg, #0f386a, #1e68a3)',
        hoverBackground: 'linear-gradient(135deg, #0a2d55, #0f386a)',
        shadowColor: 'rgba(15, 56, 106, 0.4)'
    },
    secondary: {
        background: 'linear-gradient(135deg, #64748b, #94a3b8)',
        hoverBackground: 'linear-gradient(135deg, #475569, #64748b)',
        shadowColor: 'rgba(100, 116, 139, 0.4)'
    },
    success: {
        background: 'linear-gradient(135deg, #10b981, #34d399)',
        hoverBackground: 'linear-gradient(135deg, #059669, #10b981)',
        shadowColor: 'rgba(16, 185, 129, 0.4)'
    },
    warning: {
        background: 'linear-gradient(135deg, #f59e0b, #fbbf24)',
        hoverBackground: 'linear-gradient(135deg, #d97706, #f59e0b)',
        shadowColor: 'rgba(245, 158, 11, 0.4)'
    }
};

const QuickActionButton: React.FC<QuickActionButtonProps> = ({
    label,
    icon,
    onClick,
    variant = 'primary'
}) => {
    const styles = variantStyles[variant];

    return (
        <button
            onClick={onClick}
            style={{
                background: styles.background,
                color: '#ffffff',
                border: 'none',
                borderRadius: '10px',
                padding: '12px 20px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: `0 4px 15px ${styles.shadowColor}`,
                whiteSpace: 'nowrap'
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.background = styles.hoverBackground;
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = `0 8px 25px ${styles.shadowColor}`;
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.background = styles.background;
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = `0 4px 15px ${styles.shadowColor}`;
            }}
        >
            <span style={{ display: 'flex', alignItems: 'center', fontSize: '16px' }}>
                {icon}
            </span>
            {label}
        </button>
    );
};

export default QuickActionButton;
