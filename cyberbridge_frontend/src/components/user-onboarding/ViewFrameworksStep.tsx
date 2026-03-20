// src/components/user-onboarding/ViewFrameworksStep.tsx
import React, { useEffect } from 'react';
import { Typography, Alert, Spin, Empty } from 'antd';
import {
    AppstoreOutlined,
    SafetyCertificateOutlined,
    CheckCircleFilled
} from '@ant-design/icons';
import useFrameworksStore from '../../store/useFrameworksStore';
import useUserOnboardingStore from '../../store/useUserOnboardingStore';

const { Title, Paragraph } = Typography;

const ViewFrameworksStep: React.FC = () => {
    const { frameworks, loading, fetchFrameworks } = useFrameworksStore();
    const { viewedFrameworks, addViewedFramework } = useUserOnboardingStore();

    useEffect(() => {
        fetchFrameworks();
    }, [fetchFrameworks]);

    const handleFrameworkClick = (frameworkId: string) => {
        addViewedFramework(frameworkId);
    };

    // Framework color mapping for visual variety
    const getFrameworkColor = (index: number) => {
        const colors = [
            { color: '#0f386a', bgColor: '#EBF4FC' },
            { color: '#10b981', bgColor: '#f0fdfa' },
            { color: '#f59e0b', bgColor: '#fffbeb' },
            { color: '#8b5cf6', bgColor: '#f5f3ff' },
            { color: '#ec4899', bgColor: '#fdf2f8' },
            { color: '#06b6d4', bgColor: '#ecfeff' }
        ];
        return colors[index % colors.length];
    };

    return (
        <div style={{ padding: '0 16px' }}>
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                <Title level={4} style={{ margin: 0, color: '#1a365d' }}>
                    Your Compliance Frameworks
                </Title>
                <Paragraph style={{ color: '#8c8c8c', fontSize: '14px', marginTop: '8px' }}>
                    These are the compliance frameworks your organization is working with.
                </Paragraph>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: '60px 0' }}>
                    <Spin size="large" />
                    <Paragraph style={{ marginTop: '16px', color: '#8c8c8c' }}>
                        Loading frameworks...
                    </Paragraph>
                </div>
            ) : frameworks.length === 0 ? (
                <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={
                        <span style={{ color: '#8c8c8c' }}>
                            No frameworks have been set up yet.
                            <br />
                            Your administrator will configure compliance frameworks.
                        </span>
                    }
                />
            ) : (
                <>
                    <Alert
                        message={`${frameworks.length} framework${frameworks.length !== 1 ? 's' : ''} available`}
                        description="Click on each framework to learn more about it."
                        type="info"
                        showIcon
                        icon={<AppstoreOutlined />}
                        style={{ marginBottom: '20px' }}
                    />

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, 1fr)',
                        gap: '12px',
                        maxHeight: '250px',
                        overflowY: 'auto',
                        padding: '4px'
                    }}>
                        {frameworks.map((framework, index) => {
                            const colors = getFrameworkColor(index);
                            const isViewed = viewedFrameworks.includes(framework.id);

                            return (
                                <div
                                    key={framework.id}
                                    onClick={() => handleFrameworkClick(framework.id)}
                                    style={{
                                        padding: '16px',
                                        borderRadius: '10px',
                                        border: `2px solid ${isViewed ? colors.color : '#f0f0f0'}`,
                                        background: isViewed ? colors.bgColor : 'white',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s ease',
                                        position: 'relative'
                                    }}
                                >
                                    {isViewed && (
                                        <CheckCircleFilled
                                            style={{
                                                position: 'absolute',
                                                top: '8px',
                                                right: '8px',
                                                color: colors.color,
                                                fontSize: '16px'
                                            }}
                                        />
                                    )}
                                    <div style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '10px',
                                        marginBottom: '8px'
                                    }}>
                                        <div style={{
                                            width: '36px',
                                            height: '36px',
                                            borderRadius: '8px',
                                            background: isViewed ? 'white' : colors.bgColor,
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center'
                                        }}>
                                            <SafetyCertificateOutlined
                                                style={{ fontSize: '20px', color: colors.color }}
                                            />
                                        </div>
                                        <div style={{
                                            fontWeight: 600,
                                            fontSize: '14px',
                                            color: '#1a365d',
                                            flex: 1,
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            whiteSpace: 'nowrap'
                                        }}>
                                            {framework.name}
                                        </div>
                                    </div>
                                    {framework.description && (
                                        <div style={{
                                            fontSize: '12px',
                                            color: '#64748b',
                                            lineHeight: '1.4',
                                            display: '-webkit-box',
                                            WebkitLineClamp: 2,
                                            WebkitBoxOrient: 'vertical',
                                            overflow: 'hidden'
                                        }}>
                                            {framework.description}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </>
            )}

            <div style={{
                marginTop: '20px',
                padding: '12px 16px',
                borderRadius: '8px',
                background: '#f9fafb',
                textAlign: 'center'
            }}>
                <Paragraph style={{ margin: 0, color: '#64748b', fontSize: '12px' }}>
                    Frameworks define the compliance standards and controls your organization follows.
                    You'll answer assessment questions based on these frameworks.
                </Paragraph>
            </div>
        </div>
    );
};

export default ViewFrameworksStep;
