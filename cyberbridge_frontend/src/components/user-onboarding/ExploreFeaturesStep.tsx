// src/components/user-onboarding/ExploreFeaturesStep.tsx
import React from 'react';
import { Typography, Alert, Badge } from 'antd';
import {
    FormOutlined,
    FileProtectOutlined,
    CheckSquareOutlined,
    CloudUploadOutlined,
    CheckCircleFilled
} from '@ant-design/icons';
import useUserOnboardingStore from '../../store/useUserOnboardingStore';

const { Title, Paragraph } = Typography;

const ExploreFeaturesStep: React.FC = () => {
    const { viewedFeatures, addViewedFeature } = useUserOnboardingStore();

    const features = [
        {
            id: 'assessments',
            icon: <FormOutlined style={{ fontSize: '28px', color: '#0f386a' }} />,
            title: 'Assessments',
            description: 'Complete compliance assessments by answering questions aligned with security frameworks. Track your progress and see how your organization measures up.',
            color: '#0f386a',
            bgColor: '#EBF4FC'
        },
        {
            id: 'policies',
            icon: <FileProtectOutlined style={{ fontSize: '28px', color: '#10b981' }} />,
            title: 'Policies',
            description: 'View and manage security policies that define how your organization handles data, access control, and compliance requirements.',
            color: '#10b981',
            bgColor: '#f0fdfa'
        },
        {
            id: 'objectives',
            icon: <CheckSquareOutlined style={{ fontSize: '28px', color: '#f59e0b' }} />,
            title: 'Objectives Checklist',
            description: 'Track compliance objectives and their completion status. See which objectives need attention and monitor overall compliance progress.',
            color: '#f59e0b',
            bgColor: '#fffbeb'
        },
        {
            id: 'evidence',
            icon: <CloudUploadOutlined style={{ fontSize: '28px', color: '#8b5cf6' }} />,
            title: 'Evidence Management',
            description: 'Upload and organize compliance evidence including documents, screenshots, and audit artifacts. Link evidence to specific assessment questions.',
            color: '#8b5cf6',
            bgColor: '#f5f3ff'
        }
    ];

    const handleFeatureClick = (featureId: string) => {
        addViewedFeature(featureId);
    };

    return (
        <div style={{ padding: '0 16px' }}>
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                <Title level={4} style={{ margin: 0, color: '#1a365d' }}>
                    Explore Key Features
                </Title>
                <Paragraph style={{ color: '#8c8c8c', fontSize: '14px', marginTop: '8px' }}>
                    Click on each feature to learn more about what you can do.
                </Paragraph>
            </div>

            <Alert
                message={`${viewedFeatures.length} of ${features.length} features explored`}
                type={viewedFeatures.length === features.length ? 'success' : 'info'}
                showIcon
                style={{ marginBottom: '20px' }}
            />

            <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '12px'
            }}>
                {features.map((feature) => {
                    const isViewed = viewedFeatures.includes(feature.id);

                    return (
                        <div
                            key={feature.id}
                            onClick={() => handleFeatureClick(feature.id)}
                            style={{
                                padding: '16px',
                                borderRadius: '10px',
                                border: `2px solid ${isViewed ? feature.color : '#f0f0f0'}`,
                                background: isViewed ? feature.bgColor : 'white',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                display: 'flex',
                                alignItems: 'flex-start',
                                gap: '16px',
                                position: 'relative'
                            }}
                        >
                            {isViewed && (
                                <Badge
                                    count={<CheckCircleFilled style={{ color: feature.color }} />}
                                    style={{
                                        position: 'absolute',
                                        top: '8px',
                                        right: '8px'
                                    }}
                                />
                            )}
                            <div style={{
                                width: '50px',
                                height: '50px',
                                borderRadius: '10px',
                                background: isViewed ? 'white' : feature.bgColor,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                flexShrink: 0
                            }}>
                                {feature.icon}
                            </div>
                            <div style={{ flex: 1 }}>
                                <div style={{
                                    fontWeight: 600,
                                    fontSize: '15px',
                                    color: '#1a365d',
                                    marginBottom: '6px'
                                }}>
                                    {feature.title}
                                </div>
                                <div style={{
                                    fontSize: '13px',
                                    color: '#64748b',
                                    lineHeight: '1.5'
                                }}>
                                    {feature.description}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            <div style={{
                marginTop: '20px',
                padding: '12px 16px',
                borderRadius: '8px',
                background: '#f9fafb',
                textAlign: 'center'
            }}>
                <Paragraph style={{ margin: 0, color: '#64748b', fontSize: '12px' }}>
                    Tip: You can access all these features from the sidebar menu after completing setup.
                </Paragraph>
            </div>
        </div>
    );
};

export default ExploreFeaturesStep;
