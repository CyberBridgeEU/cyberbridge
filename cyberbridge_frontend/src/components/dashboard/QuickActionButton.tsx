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
        background: 'linear-gradient(135deg, #0a2444, #0f386a)',
        hoverBackground: 'linear-gradient(135deg, #071b33, #0a2444)',
        shadowColor: 'rgba(10, 36, 68, 0.5)'
    },
    secondary: {
        background: 'linear-gradient(135deg, #334155, #475569)',
        hoverBackground: 'linear-gradient(135deg, #1e293b, #334155)',
        shadowColor: 'rgba(51, 65, 85, 0.5)'
    },
    success: {
        background: 'linear-gradient(135deg, #047857, #059669)',
        hoverBackground: 'linear-gradient(135deg, #064e3b, #047857)',
        shadowColor: 'rgba(4, 120, 87, 0.5)'
    },
    warning: {
        background: 'linear-gradient(135deg, #b45309, #d97706)',
        hoverBackground: 'linear-gradient(135deg, #92400e, #b45309)',
        shadowColor: 'rgba(180, 83, 9, 0.5)'
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
