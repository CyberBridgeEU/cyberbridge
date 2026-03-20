// src/components/user-onboarding/UserOnboardingComplete.tsx
import React from 'react';
import { Typography, Alert } from 'antd';
import {
    CheckCircleFilled,
    FormOutlined,
    FileProtectOutlined,
    CheckSquareOutlined,
    CloudUploadOutlined,
    ArrowRightOutlined
} from '@ant-design/icons';
import useUserOnboardingStore from '../../store/useUserOnboardingStore';
import useFrameworksStore from '../../store/useFrameworksStore';

const { Title, Paragraph } = Typography;

const UserOnboardingComplete: React.FC = () => {
    const { viewedFeatures, viewedFrameworks } = useUserOnboardingStore();
    const { frameworks } = useFrameworksStore();

    const quickStartItems = [
        {
            icon: <FormOutlined style={{ color: '#0f386a' }} />,
            text: 'Start your first assessment',
            path: '/assessments'
        },
        {
            icon: <FileProtectOutlined style={{ color: '#10b981' }} />,
            text: 'Review organizational policies',
            path: '/policies_registration'
        },
        {
            icon: <CheckSquareOutlined style={{ color: '#f59e0b' }} />,
            text: 'Check compliance objectives',
            path: '/objectives_checklist'
        },
        {
            icon: <CloudUploadOutlined style={{ color: '#8b5cf6' }} />,
            text: 'Upload compliance evidence',
            path: '/evidence'
        }
    ];

    return (
        <div style={{ padding: '0 16px', textAlign: 'center' }}>
            <div style={{
                width: '100px',
                height: '100px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 24px',
                boxShadow: '0 8px 24px rgba(16, 185, 129, 0.25)'
            }}>
                <CheckCircleFilled style={{ fontSize: '50px', color: 'white' }} />
            </div>

            <Title level={3} style={{ margin: 0, color: '#1a365d' }}>
                You're All Set!
            </Title>
            <Paragraph style={{ color: '#8c8c8c', fontSize: '14px', marginTop: '8px', marginBottom: '24px' }}>
                You've completed the setup and are ready to start using CyberBridge.
            </Paragraph>

            <Alert
                message="Setup Summary"
                description={
                    <div style={{ textAlign: 'left' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                            <CheckCircleFilled style={{ color: '#10b981' }} />
                            <span>{viewedFeatures.length} features explored</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                            <CheckCircleFilled style={{ color: '#10b981' }} />
                            <span>{viewedFrameworks.length} of {frameworks.length} frameworks reviewed</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <CheckCircleFilled style={{ color: '#10b981' }} />
                            <span>Account ready for compliance work</span>
                        </div>
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
                    Quick Start Suggestions
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
                            </div>
                            <ArrowRightOutlined style={{ color: '#9ca3af', fontSize: '12px' }} />
                        </div>
                    ))}
                </div>
            </div>

            <Paragraph style={{ color: '#64748b', fontSize: '12px', margin: 0 }}>
                Click <strong>"Start Using CyberBridge"</strong> below to begin working on your compliance tasks.
            </Paragraph>
        </div>
    );
};

export default UserOnboardingComplete;
