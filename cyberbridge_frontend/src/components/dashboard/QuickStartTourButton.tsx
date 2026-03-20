// src/components/dashboard/QuickStartTourButton.tsx
import { CompassOutlined } from '@ant-design/icons';
import useGuidedTourStore from '../../store/useGuidedTourStore';

const QuickStartTourButton: React.FC = () => {
    const { startQuickStartTour } = useGuidedTourStore();

    return (
        <button
            onClick={startQuickStartTour}
            style={{
                background: 'linear-gradient(135deg, #06b6d4, #0891b2, #0e7490)',
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
                boxShadow: '0 4px 15px rgba(6, 182, 212, 0.4), inset 0 1px 0 rgba(255,255,255,0.2)',
                whiteSpace: 'nowrap',
                position: 'relative',
                overflow: 'hidden'
            }}
            onMouseEnter={(e) => {
                e.currentTarget.style.background = 'linear-gradient(135deg, #0891b2, #0e7490, #155e75)';
                e.currentTarget.style.transform = 'translateY(-2px) scale(1.02)';
                e.currentTarget.style.boxShadow = '0 8px 25px rgba(6, 182, 212, 0.5), inset 0 1px 0 rgba(255,255,255,0.2)';
            }}
            onMouseLeave={(e) => {
                e.currentTarget.style.background = 'linear-gradient(135deg, #06b6d4, #0891b2, #0e7490)';
                e.currentTarget.style.transform = 'translateY(0) scale(1)';
                e.currentTarget.style.boxShadow = '0 4px 15px rgba(6, 182, 212, 0.4), inset 0 1px 0 rgba(255,255,255,0.2)';
            }}
        >
            <span style={{ display: 'flex', alignItems: 'center', fontSize: '16px' }}>
                <CompassOutlined />
            </span>
            Interactive Tour
            <span style={{
                fontSize: '10px',
                fontWeight: 700,
                backgroundColor: 'rgba(255,255,255,0.25)',
                padding: '2px 6px',
                borderRadius: '6px',
                lineHeight: 1,
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
            }}>
                New
            </span>
        </button>
    );
};

export default QuickStartTourButton;
