// src/components/user-onboarding/WelcomeStep.tsx
import React from 'react';
import { Typography, Alert } from 'antd';
import {
    SafetyCertificateOutlined,
    TeamOutlined,
    FileProtectOutlined,
    RocketOutlined
} from '@ant-design/icons';
import useAuthStore from '../../store/useAuthStore';

const { Title, Paragraph } = Typography;

const WelcomeStep: React.FC = () => {
    const { user } = useAuthStore();

    const highlights = [
        {
            icon: <SafetyCertificateOutlined style={{ fontSize: '24px', color: '#0f386a' }} />,
            title: 'Compliance Assessments',
            description: 'Complete security assessments aligned with industry frameworks'
        },
        {
            icon: <FileProtectOutlined style={{ fontSize: '24px', color: '#10b981' }} />,
            title: 'Policy Management',
            description: 'Access and review organizational security policies'
        },
        {
            icon: <TeamOutlined style={{ fontSize: '24px', color: '#f59e0b' }} />,
            title: 'Team Collaboration',
            description: 'Work together with your team on compliance objectives'
        },
        {
            icon: <RocketOutlined style={{ fontSize: '24px', color: '#8b5cf6' }} />,
            title: 'Evidence Collection',
            description: 'Upload and manage compliance evidence documentation'
        }
    ];

    return (
        <div style={{ padding: '0 16px' }}>
            <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                <div style={{
                    width: '80px',
                    height: '80px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #EBF4FC 0%, #d6e8f7 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 20px'
                }}>
                    <SafetyCertificateOutlined style={{ fontSize: '40px', color: '#0f386a' }} />
                </div>
                <Title level={3} style={{ margin: 0, color: '#1a365d' }}>
                    Welcome to CyberBridge{user?.email ? `, ${user.email.split('@')[0]}` : ''}!
                </Title>
                <Paragraph style={{ color: '#8c8c8c', fontSize: '14px', marginTop: '8px' }}>
                    This quick setup will help you get familiar with the platform and its features.
                </Paragraph>
            </div>

            <Alert
                message="What you can do in CyberBridge"
                description="As a team member, you'll have access to key compliance and security features."
                type="info"
                showIcon
                style={{ marginBottom: '24px' }}
            />

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '16px'
            }}>
                {highlights.map((item, index) => (
                    <div
                        key={index}
                        style={{
                            padding: '16px',
                            borderRadius: '8px',
                            border: '1px solid #f0f0f0',
                            background: '#fafafa',
                            display: 'flex',
                            alignItems: 'flex-start',
                            gap: '12px'
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
                            flexShrink: 0
                        }}>
                            {item.icon}
                        </div>
                        <div>
                            <div style={{ fontWeight: 600, color: '#1a365d', marginBottom: '4px' }}>
                                {item.title}
                            </div>
                            <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                                {item.description}
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div style={{
                marginTop: '24px',
                padding: '16px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #EBF4FC 0%, #f0f9ff 100%)',
                textAlign: 'center'
            }}>
                <Paragraph style={{ margin: 0, color: '#1a365d', fontSize: '13px' }}>
                    Click <strong>Next</strong> to explore the key features available to you.
                </Paragraph>
            </div>
        </div>
    );
};

export default WelcomeStep;
