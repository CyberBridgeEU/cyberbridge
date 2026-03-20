// src/components/dashboard/QuickStartButton.tsx
import { ThunderboltOutlined } from '@ant-design/icons';
import { useLocation } from 'wouter';

const QuickStartButton: React.FC = () => {
    const [, setLocation] = useLocation();

    const handleClick = () => {
        setLocation('/documentation?doc=quick_start_example');
    };

    return (
        <button
            onClick={handleClick}
            style={{
                background: 'linear-gradient(135deg, #f59e0b, #f97316, #ef4444)',
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
                boxShadow: '0 4px 15px rgba(245, 158, 11, 0.4), inset 0 1px 0 rgba(255,255,255,0.2)',
                whiteSpace: 'nowrap',
                position: 'relative',
                overflow: 'hidden'
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.background = 'linear-gradient(135deg, #d97706, #ea580c, #dc2626)';
                e.currentTarget.style.transform = 'translateY(-2px) scale(1.02)';
                e.currentTarget.style.boxShadow = '0 8px 25px rgba(245, 158, 11, 0.5), inset 0 1px 0 rgba(255,255,255,0.2)';
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.background = 'linear-gradient(135deg, #f59e0b, #f97316, #ef4444)';
                e.currentTarget.style.transform = 'translateY(0) scale(1)';
                e.currentTarget.style.boxShadow = '0 4px 15px rgba(245, 158, 11, 0.4), inset 0 1px 0 rgba(255,255,255,0.2)';
            }}
        >
            <span style={{ display: 'flex', alignItems: 'center', fontSize: '16px' }}>
                <ThunderboltOutlined />
            </span>
            Quick Start Example
        </button>
    );
};

export default QuickStartButton;
