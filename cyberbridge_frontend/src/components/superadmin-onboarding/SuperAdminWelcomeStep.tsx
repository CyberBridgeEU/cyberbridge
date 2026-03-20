// src/components/superadmin-onboarding/SuperAdminWelcomeStep.tsx
import React from 'react';
import { Typography, Alert } from 'antd';
import {
    CrownOutlined,
    BankOutlined,
    TeamOutlined,
    SettingOutlined,
    SafetyCertificateOutlined,
    DatabaseOutlined
} from '@ant-design/icons';
import useAuthStore from '../../store/useAuthStore';

const { Title, Paragraph } = Typography;

const SuperAdminWelcomeStep: React.FC = () => {
    const { user } = useAuthStore();

    const capabilities = [
        {
            icon: <BankOutlined style={{ fontSize: '22px', color: '#dc2626' }} />,
            title: 'Organization Management',
            description: 'Create and manage multiple organizations'
        },
        {
            icon: <TeamOutlined style={{ fontSize: '22px', color: '#8b5cf6' }} />,
            title: 'User Administration',
            description: 'Approve users and manage access across all organizations'
        },
        {
            icon: <SettingOutlined style={{ fontSize: '22px', color: '#f59e0b' }} />,
            title: 'System Configuration',
            description: 'Configure AI providers, integrations, and global settings'
        },
        {
            icon: <SafetyCertificateOutlined style={{ fontSize: '22px', color: '#0f386a' }} />,
            title: 'Framework Templates',
            description: 'Manage compliance framework templates available to organizations'
        },
        {
            icon: <DatabaseOutlined style={{ fontSize: '22px', color: '#10b981' }} />,
            title: 'System Backups',
            description: 'Manage system backups and data integrity'
        }
    ];

    return (
        <div style={{ padding: '0 16px' }}>
            <div style={{ textAlign: 'center', marginBottom: '28px' }}>
                <div style={{
                    width: '80px',
                    height: '80px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 20px'
                }}>
                    <CrownOutlined style={{ fontSize: '40px', color: '#dc2626' }} />
                </div>
                <Title level={3} style={{ margin: 0, color: '#1a365d' }}>
                    Welcome, Super Administrator{user?.email ? ` (${user.email.split('@')[0]})` : ''}!
                </Title>
                <Paragraph style={{ color: '#8c8c8c', fontSize: '14px', marginTop: '8px' }}>
                    You have full administrative access to the CyberBridge platform.
                </Paragraph>
            </div>

            <Alert
                message="Elevated Privileges"
                description="As a Super Admin, you have access to all system features and can manage organizations, users, and platform settings."
                type="warning"
                showIcon
                icon={<CrownOutlined />}
                style={{ marginBottom: '24px' }}
            />

            <div style={{ marginBottom: '16px' }}>
                <Title level={5} style={{ margin: '0 0 12px 0', color: '#1a365d' }}>
                    Your Administrative Capabilities
                </Title>
            </div>

            <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '10px'
            }}>
                {capabilities.map((item, index) => (
                    <div
                        key={index}
                        style={{
                            padding: '12px 16px',
                            borderRadius: '8px',
                            border: '1px solid #f0f0f0',
                            background: '#fafafa',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '14px'
                        }}
                    >
                        <div style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '8px',
                            background: 'white',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                            border: '1px solid #f0f0f0'
                        }}>
                            {item.icon}
                        </div>
                        <div>
                            <div style={{ fontWeight: 600, color: '#1a365d', fontSize: '14px' }}>
                                {item.title}
                            </div>
                            <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                                {item.description}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SuperAdminWelcomeStep;
