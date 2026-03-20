// src/components/superadmin-onboarding/SuperAdminOnboardingComplete.tsx
import React from 'react';
import { Typography, Alert } from 'antd';
import {
    CheckCircleFilled,
    CrownOutlined,
    UserAddOutlined,
    BankOutlined,
    SettingOutlined,
    NodeIndexOutlined,
    ArrowRightOutlined
} from '@ant-design/icons';
import useSuperAdminOnboardingStore from '../../store/useSuperAdminOnboardingStore';
import { useAdminAreaStore } from '../../store/adminAreaStore';

const { Title, Paragraph } = Typography;

const SuperAdminOnboardingComplete: React.FC = () => {
    const { viewedSections } = useSuperAdminOnboardingStore();
    const { pendingUsers } = useAdminAreaStore();

    const quickStartItems = [
        {
            icon: <UserAddOutlined style={{ color: '#0f386a' }} />,
            text: 'Approve pending user registrations',
            path: '/admin',
            badge: pendingUsers.length > 0 ? pendingUsers.length : null
        },
        {
            icon: <BankOutlined style={{ color: '#8b5cf6' }} />,
            text: 'Manage organizations',
            path: '/user_management'
        },
        {
            icon: <SettingOutlined style={{ color: '#f59e0b' }} />,
            text: 'Configure system settings',
            path: '/settings'
        },
        {
            icon: <NodeIndexOutlined style={{ color: '#10b981' }} />,
            text: 'View compliance correlations',
            path: '/correlations'
        }
    ];

    return (
        <div style={{ padding: '0 16px', textAlign: 'center' }}>
            <div style={{
                width: '100px',
                height: '100px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #dc2626 0%, #991b1b 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 24px',
                boxShadow: '0 8px 24px rgba(220, 38, 38, 0.25)'
            }}>
                <CrownOutlined style={{ fontSize: '50px', color: 'white' }} />
            </div>

            <Title level={3} style={{ margin: 0, color: '#1a365d' }}>
                You're Ready to Manage CyberBridge!
            </Title>
            <Paragraph style={{ color: '#8c8c8c', fontSize: '14px', marginTop: '8px', marginBottom: '24px' }}>
                You've completed the Super Admin setup and are ready to manage the platform.
            </Paragraph>

            <Alert
                message="Setup Summary"
                description={
                    <div style={{ textAlign: 'left' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                            <CheckCircleFilled style={{ color: '#10b981' }} />
                            <span>{viewedSections.length} configuration areas reviewed</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                            <CheckCircleFilled style={{ color: '#10b981' }} />
                            <span>Organization management overview completed</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                            <CheckCircleFilled style={{ color: '#10b981' }} />
                            <span>User management overview completed</span>
                        </div>
                        {pendingUsers.length > 0 && (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    width: '14px',
                                    height: '14px',
                                    borderRadius: '50%',
                                    background: '#f59e0b',
                                    color: 'white',
                                    fontSize: '10px',
                                    fontWeight: 'bold'
                                }}>!</span>
                                <span style={{ color: '#f59e0b' }}>
                                    {pendingUsers.length} user{pendingUsers.length !== 1 ? 's' : ''} awaiting approval
                                </span>
                            </div>
                        )}
                    </div>
                }
                type="success"
                showIcon={false}
                style={{ marginBottom: '24px', textAlign: 'left' }}
            />

            <div style={{
                background: '#f9fafb',
                borderRadius: '10px',
                padding: '20px',
                marginBottom: '16px'
            }}>
                <Title level={5} style={{ margin: '0 0 16px 0', color: '#1a365d' }}>
                    Recommended Next Steps
                </Title>
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px'
                }}>
                    {quickStartItems.map((item, index) => (
                        <div
                            key={index}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                padding: '12px 16px',
                                borderRadius: '8px',
                                background: 'white',
                                border: '1px solid #e5e7eb'
                            }}
                        >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {item.icon}
                                <span style={{ fontSize: '13px', color: '#374151' }}>{item.text}</span>
                                {item.badge && (
                                    <span style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        minWidth: '20px',
                                        height: '20px',
                                        borderRadius: '10px',
                                        background: '#f59e0b',
                                        color: 'white',
                                        fontSize: '11px',
                                        fontWeight: 600,
                                        padding: '0 6px'
                                    }}>
                                        {item.badge}
                                    </span>
                                )}
                            </div>
                            <ArrowRightOutlined style={{ color: '#9ca3af', fontSize: '12px' }} />
                        </div>
                    ))}
                </div>
            </div>

            <div style={{
                padding: '12px 16px',
                borderRadius: '8px',
                background: '#fef2f2',
                border: '1px solid #fecaca'
            }}>
                <Paragraph style={{ margin: 0, color: '#991b1b', fontSize: '12px' }}>
                    <strong>Remember:</strong> As a Super Admin, your actions affect all organizations.
                    Always verify before making system-wide changes.
                </Paragraph>
            </div>
        </div>
    );
};

export default SuperAdminOnboardingComplete;
