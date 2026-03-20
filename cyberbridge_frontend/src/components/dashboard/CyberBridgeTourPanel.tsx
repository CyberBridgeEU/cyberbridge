// src/components/dashboard/CyberBridgeTourPanel.tsx
import React, { useState } from 'react';
import { CompassOutlined, BookOutlined, ThunderboltOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { useLocation } from 'wouter';
import useGuidedTourStore from '../../store/useGuidedTourStore';
import UserGuideWizard from './UserGuideWizard';

interface TourCardProps {
    icon: React.ReactNode;
    title: string;
    description: string;
    gradient: string;
    hoverGradient: string;
    shadowColor: string;
    onClick: () => void;
    badge?: string;
}

const TourCard: React.FC<TourCardProps> = ({
    icon,
    title,
    description,
    gradient,
    hoverGradient,
    shadowColor,
    onClick,
    badge
}) => {
    const [hovered, setHovered] = useState(false);

    return (
        <div
            role="button"
            tabIndex={0}
            onClick={onClick}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onClick(); }}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            style={{
                background: hovered ? hoverGradient : gradient,
                border: '2px solid rgba(255,255,255,0.15)',
                borderRadius: '16px',
                padding: '32px 24px 28px',
                cursor: 'pointer',
                transition: 'all 0.35s cubic-bezier(0.4, 0, 0.2, 1)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '16px',
                flex: '1 1 0',
                minWidth: '200px',
                minHeight: '180px',
                position: 'relative',
                transform: hovered ? 'translateY(-6px) scale(1.02)' : 'translateY(0) scale(1)',
                boxShadow: hovered
                    ? `0 20px 40px ${shadowColor}60, 0 8px 16px ${shadowColor}40, inset 0 1px 0 rgba(255,255,255,0.2)`
                    : `0 8px 24px ${shadowColor}35, 0 4px 8px ${shadowColor}20, inset 0 1px 0 rgba(255,255,255,0.15)`,
                color: '#ffffff',
                textAlign: 'center',
                outline: 'none'
            }}
        >
            {/* Decorative glow */}
            <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: 'radial-gradient(circle at 30% 20%, rgba(255,255,255,0.15) 0%, transparent 60%)',
                pointerEvents: 'none',
                borderRadius: '14px'
            }} />

            {badge && (
                <span style={{
                    position: 'absolute',
                    top: '12px',
                    right: '12px',
                    fontSize: '10px',
                    fontWeight: 700,
                    backgroundColor: 'rgba(255,255,255,0.25)',
                    backdropFilter: 'blur(4px)',
                    padding: '3px 8px',
                    borderRadius: '8px',
                    lineHeight: 1,
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    color: '#fff',
                    zIndex: 2
                }}>
                    {badge}
                </span>
            )}

            {/* Icon container */}
            <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '16px',
                background: 'rgba(255,255,255,0.2)',
                backdropFilter: 'blur(8px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '28px',
                color: '#fff',
                flexShrink: 0,
                transition: 'transform 0.35s ease',
                transform: hovered ? 'scale(1.1)' : 'scale(1)',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
            }}>
                {icon}
            </div>

            {/* Text */}
            <div style={{ position: 'relative', zIndex: 1 }}>
                <p style={{
                    margin: '0 0 4px 0',
                    fontSize: '16px',
                    fontWeight: 700,
                    letterSpacing: '-0.2px',
                    lineHeight: 1.3
                }}>
                    {title}
                </p>
                <p style={{
                    margin: 0,
                    fontSize: '12.5px',
                    fontWeight: 500,
                    opacity: 0.85,
                    lineHeight: 1.4
                }}>
                    {description}
                </p>
            </div>
        </div>
    );
};

const CyberBridgeTourPanel: React.FC = () => {
    const [, setLocation] = useLocation();
    const { startQuickStartTour } = useGuidedTourStore();
    const [guideOpen, setGuideOpen] = useState(false);

    return (
        <>
            <div className="cyberbridge-tour-panel">
                <h4 className="cyberbridge-tour-panel-title" style={{
                    margin: '0 0 18px 0',
                    color: 'var(--primary-navy)',
                    fontSize: '16px',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}>
                    CyberBridge Tour
                </h4>
                <div style={{
                    display: 'flex',
                    gap: '16px',
                    flexWrap: 'wrap'
                }}>
                    <TourCard
                        icon={<CompassOutlined />}
                        title="Interactive Tour"
                        description="Guided walkthrough of the platform"
                        gradient="linear-gradient(145deg, #1a3d5c, #162d4d, #0f2240)"
                        hoverGradient="linear-gradient(145deg, #1f4a6e, #1a3d5c, #162d4d)"
                        shadowColor="rgba(26, 61, 92,"
                        onClick={startQuickStartTour}
                        badge="New"
                    />
                    <TourCard
                        icon={<BookOutlined />}
                        title="User Guide"
                        description="Step-by-step compliance workflow"
                        gradient="linear-gradient(145deg, #2a2d52, #1f2145, #161838)"
                        hoverGradient="linear-gradient(145deg, #333664, #2a2d52, #1f2145)"
                        shadowColor="rgba(42, 45, 82,"
                        onClick={() => setGuideOpen(true)}
                        badge="New"
                    />
                    <TourCard
                        icon={<ThunderboltOutlined />}
                        title="Quick Start Example"
                        description="See a full compliance flow in action"
                        gradient="linear-gradient(145deg, #3d2c1a, #2e2015, #221810)"
                        hoverGradient="linear-gradient(145deg, #4a3520, #3d2c1a, #2e2015)"
                        shadowColor="rgba(61, 44, 26,"
                        onClick={() => setLocation('/documentation?doc=quick_start_example')}
                    />
                    <TourCard
                        icon={<SafetyCertificateOutlined />}
                        title="CRA Start Example"
                        description="CRA compliance for a SIEM with AI"
                        gradient="linear-gradient(145deg, #1a3d3a, #152e2c, #0f2220)"
                        hoverGradient="linear-gradient(145deg, #1f4a46, #1a3d3a, #152e2c)"
                        shadowColor="rgba(26, 61, 58,"
                        onClick={() => setLocation('/documentation?doc=cra_start_example')}
                        badge="New"
                    />
                </div>
            </div>

            <UserGuideWizard externalOpen={guideOpen} onExternalClose={() => setGuideOpen(false)} />
        </>
    );
};

export default CyberBridgeTourPanel;
