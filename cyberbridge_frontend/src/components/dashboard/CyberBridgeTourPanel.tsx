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
                        gradient="linear-gradient(145deg, #06b6d4, #0891b2, #0e7490)"
                        hoverGradient="linear-gradient(145deg, #0891b2, #0e7490, #155e75)"
                        shadowColor="rgba(6, 182, 212,"
                        onClick={startQuickStartTour}
                        badge="New"
                    />
                    <TourCard
                        icon={<BookOutlined />}
                        title="User Guide"
                        description="Step-by-step compliance workflow"
                        gradient="linear-gradient(145deg, #6366f1, #8b5cf6, #a78bfa)"
                        hoverGradient="linear-gradient(145deg, #4f46e5, #7c3aed, #8b5cf6)"
                        shadowColor="rgba(99, 102, 241,"
                        onClick={() => setGuideOpen(true)}
                        badge="New"
                    />
                    <TourCard
                        icon={<ThunderboltOutlined />}
                        title="Quick Start Example"
                        description="See a full compliance flow in action"
                        gradient="linear-gradient(145deg, #f59e0b, #f97316, #ef4444)"
                        hoverGradient="linear-gradient(145deg, #d97706, #ea580c, #dc2626)"
                        shadowColor="rgba(245, 158, 11,"
                        onClick={() => setLocation('/documentation?doc=quick_start_example')}
                    />
                    <TourCard
                        icon={<SafetyCertificateOutlined />}
                        title="CRA Start Example"
                        description="CRA compliance for a SIEM with AI"
                        gradient="linear-gradient(145deg, #10b981, #059669, #047857)"
                        hoverGradient="linear-gradient(145deg, #059669, #047857, #065f46)"
                        shadowColor="rgba(16, 185, 129,"
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
