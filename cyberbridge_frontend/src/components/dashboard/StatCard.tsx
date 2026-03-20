// src/components/dashboard/StatCard.tsx
import React from 'react';
import { Spin } from 'antd';

interface StatCardProps {
    title: string;
    value: number | string;
    icon: React.ReactNode;
    iconColor?: string;
    iconBgColor?: string;
    onClick?: () => void;
    loading?: boolean;
    suffix?: string;
}

const StatCard: React.FC<StatCardProps> = ({
    title,
    value,
    icon,
    iconColor = '#0f386a',
    iconBgColor = '#EBF4FC',
    onClick,
    loading = false,
    suffix = ''
}) => {
    return (
        <div
            className="stat-card"
            onClick={onClick}
            style={{
                cursor: onClick ? 'pointer' : 'default',
                ...(!onClick && { boxShadow: 'none', border: '1px solid var(--border-light-gray)' })
            }}
            onMouseEnter={(e) => {
                if (onClick) {
                    e.currentTarget.style.transform = 'translateY(-4px)';
                }
            }}
            onMouseLeave={(e) => {
                if (onClick) {
                    e.currentTarget.style.transform = 'translateY(0)';
                }
            }}
        >
            <div
                style={{
                    width: '56px',
                    height: '56px',
                    borderRadius: '12px',
                    backgroundColor: iconBgColor,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0
                }}
            >
                <span style={{ fontSize: '24px', color: iconColor, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {icon}
                </span>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
                {loading ? (
                    <Spin size="small" />
                ) : (
                    <>
                        <p style={{
                            fontWeight: '700',
                            fontSize: '28px',
                            color: 'var(--text-charcoal)',
                            margin: '0 0 4px 0',
                            lineHeight: 1.2
                        }}>
                            {value}{suffix}
                        </p>
                        <p style={{
                            color: 'var(--text-dark-gray)',
                            fontSize: '14px',
                            margin: 0,
                            fontWeight: 500,
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis'
                        }}>
                            {title}
                        </p>
                    </>
                )}
            </div>
        </div>
    );
};

export default StatCard;
