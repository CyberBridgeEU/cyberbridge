// src/components/onboarding/OnboardingComplete.tsx
import React from 'react';
import { Result, Typography, List, Space } from 'antd';
import {
    CheckCircleOutlined,
    AppstoreOutlined,
    TeamOutlined,
    RobotOutlined,
    RocketOutlined
} from '@ant-design/icons';
import useOnboardingStore from '../../store/useOnboardingStore';

const { Text } = Typography;

const OnboardingComplete: React.FC = () => {
    const { selectedFrameworks, invitedUsers, aiConfig } = useOnboardingStore();

    const summaryItems = [
        {
            icon: <AppstoreOutlined style={{ color: '#0f386a' }} />,
            title: 'Compliance Frameworks',
            description: selectedFrameworks.length > 0
                ? `${selectedFrameworks.length} framework${selectedFrameworks.length > 1 ? 's' : ''} added to your organization`
                : 'No frameworks selected - you can add them later'
        },
        {
            icon: <TeamOutlined style={{ color: '#8b5cf6' }} />,
            title: 'Team Members',
            description: invitedUsers.length > 0
                ? `${invitedUsers.length} team member${invitedUsers.length > 1 ? 's' : ''} invited`
                : 'No team members invited - you can add them later'
        },
        {
            icon: <RobotOutlined style={{ color: '#10b981' }} />,
            title: 'AI Provider',
            description: aiConfig.provider
                ? `Configured with ${aiConfig.provider.charAt(0).toUpperCase() + aiConfig.provider.slice(1)}`
                : 'Using default llama.cpp configuration'
        }
    ];

    return (
        <div style={{ textAlign: 'center' }}>
            <Result
                icon={
                    <div style={{
                        width: '80px',
                        height: '80px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        margin: '0 auto',
                        boxShadow: '0 8px 24px rgba(16, 185, 129, 0.3)'
                    }}>
                        <CheckCircleOutlined style={{ fontSize: '40px', color: 'white' }} />
                    </div>
                }
                title={
                    <span style={{ color: '#1a365d', fontSize: '24px' }}>
                        You're All Set!
                    </span>
                }
                subTitle={
                    <span style={{ color: '#8c8c8c' }}>
                        Your organization is ready to start managing compliance
                    </span>
                }
            />

            <div style={{
                maxWidth: '400px',
                margin: '0 auto',
                textAlign: 'left',
                backgroundColor: '#fafafa',
                borderRadius: '12px',
                padding: '20px'
            }}>
                <Text strong style={{ display: 'block', marginBottom: '16px', color: '#1a365d' }}>
                    Setup Summary
                </Text>
                <List
                    dataSource={summaryItems}
                    renderItem={item => (
                        <List.Item style={{ padding: '12px 0', borderBottom: '1px solid #f0f0f0' }}>
                            <Space align="start">
                                <div style={{
                                    width: '32px',
                                    height: '32px',
                                    borderRadius: '8px',
                                    backgroundColor: 'white',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '16px'
                                }}>
                                    {item.icon}
                                </div>
                                <div>
                                    <Text strong style={{ display: 'block', fontSize: '13px' }}>
                                        {item.title}
                                    </Text>
                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                        {item.description}
                                    </Text>
                                </div>
                            </Space>
                        </List.Item>
                    )}
                />
            </div>

            <div style={{
                marginTop: '24px',
                padding: '16px',
                backgroundColor: '#f0f7ff',
                borderRadius: '8px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '12px'
            }}>
                <RocketOutlined style={{ fontSize: '20px', color: '#0f386a' }} />
                <Text style={{ color: '#1a365d' }}>
                    Click <strong>"Start Using CyberBridge"</strong> below to begin
                </Text>
            </div>
        </div>
    );
};

export default OnboardingComplete;
