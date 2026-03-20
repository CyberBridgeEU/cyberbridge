// src/components/superadmin-onboarding/OrganizationOverviewStep.tsx
import React, { useEffect } from 'react';
import { Typography, Alert, Spin, Empty, Tag } from 'antd';
import {
    BankOutlined,
    TeamOutlined,
    CheckCircleFilled,
    PlusOutlined
} from '@ant-design/icons';
import useSuperAdminOnboardingStore from '../../store/useSuperAdminOnboardingStore';
import useDashboardStore from '../../store/useDashboardStore';

const { Title, Paragraph } = Typography;

const OrganizationOverviewStep: React.FC = () => {
    const { viewedSections, addViewedSection } = useSuperAdminOnboardingStore();
    const { metrics, userAnalytics, loading, fetchDashboardMetrics, fetchUserAnalytics } = useDashboardStore();

    useEffect(() => {
        fetchDashboardMetrics();
        fetchUserAnalytics();
    }, [fetchDashboardMetrics, fetchUserAnalytics]);

    const handleSectionClick = (sectionId: string) => {
        addViewedSection(sectionId);
    };

    const managementTasks = [
        {
            id: 'create-org',
            icon: <PlusOutlined style={{ fontSize: '20px', color: '#10b981' }} />,
            title: 'Create New Organization',
            description: 'Add a new organization to the platform with its own users and frameworks.',
            path: '/organizations',
            color: '#10b981',
            bgColor: '#f0fdfa'
        },
        {
            id: 'manage-orgs',
            icon: <BankOutlined style={{ fontSize: '20px', color: '#0f386a' }} />,
            title: 'Manage Organizations',
            description: 'View and edit existing organizations, their settings, and assigned frameworks.',
            path: '/user_management',
            color: '#0f386a',
            bgColor: '#EBF4FC'
        },
        {
            id: 'org-users',
            icon: <TeamOutlined style={{ fontSize: '20px', color: '#8b5cf6' }} />,
            title: 'Organization Users',
            description: 'View all users across organizations and manage their access.',
            path: '/admin',
            color: '#8b5cf6',
            bgColor: '#f5f3ff'
        }
    ];

    return (
        <div style={{ padding: '0 16px' }}>
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                <Title level={4} style={{ margin: 0, color: '#1a365d' }}>
                    Organization Management
                </Title>
                <Paragraph style={{ color: '#8c8c8c', fontSize: '14px', marginTop: '8px' }}>
                    Manage organizations and their resources across the platform.
                </Paragraph>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <Spin size="large" />
                    <Paragraph style={{ marginTop: '16px', color: '#8c8c8c' }}>
                        Loading organization data...
                    </Paragraph>
                </div>
            ) : (
                <>
                    {/* Stats Overview */}
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '12px',
                        marginBottom: '20px'
                    }}>
                        <div style={{
                            padding: '16px',
                            borderRadius: '10px',
                            background: 'linear-gradient(135deg, #EBF4FC 0%, #d6e8f7 100%)',
                            textAlign: 'center'
                        }}>
                            <div style={{ fontSize: '28px', fontWeight: 700, color: '#0f386a' }}>
                                {metrics.totalOrganizations || 0}
                            </div>
                            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                                Organizations
                            </div>
                        </div>
                        <div style={{
                            padding: '16px',
                            borderRadius: '10px',
                            background: 'linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%)',
                            textAlign: 'center'
                        }}>
                            <div style={{ fontSize: '28px', fontWeight: 700, color: '#8b5cf6' }}>
                                {metrics.totalUsers || 0}
                            </div>
                            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                                Total Users
                            </div>
                        </div>
                        <div style={{
                            padding: '16px',
                            borderRadius: '10px',
                            background: 'linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%)',
                            textAlign: 'center'
                        }}>
                            <div style={{ fontSize: '28px', fontWeight: 700, color: '#10b981' }}>
                                {metrics.complianceFrameworks || 0}
                            </div>
                            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                                Frameworks
                            </div>
                        </div>
                    </div>

                    <Alert
                        message="Organization Management Tasks"
                        description="Click on each task to learn more about organization management capabilities."
                        type="info"
                        showIcon
                        icon={<BankOutlined />}
                        style={{ marginBottom: '16px' }}
                    />

                    <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '10px'
                    }}>
                        {managementTasks.map((task) => {
                            const isViewed = viewedSections.includes(task.id);

                            return (
                                <div
                                    key={task.id}
                                    onClick={() => handleSectionClick(task.id)}
                                    style={{
                                        padding: '14px 16px',
                                        borderRadius: '10px',
                                        border: `2px solid ${isViewed ? task.color : '#f0f0f0'}`,
                                        background: isViewed ? task.bgColor : 'white',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s ease',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '14px',
                                        position: 'relative'
                                    }}
                                >
                                    {isViewed && (
                                        <CheckCircleFilled
                                            style={{
                                                position: 'absolute',
                                                top: '10px',
                                                right: '10px',
                                                color: task.color,
                                                fontSize: '16px'
                                            }}
                                        />
                                    )}
                                    <div style={{
                                        width: '42px',
                                        height: '42px',
                                        borderRadius: '10px',
                                        background: isViewed ? 'white' : task.bgColor,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        flexShrink: 0
                                    }}>
                                        {task.icon}
                                    </div>
                                    <div style={{ flex: 1 }}>
                                        <div style={{
                                            fontWeight: 600,
                                            fontSize: '14px',
                                            color: '#1a365d',
                                            marginBottom: '4px'
                                        }}>
                                            {task.title}
                                        </div>
                                        <div style={{
                                            fontSize: '12px',
                                            color: '#64748b',
                                            lineHeight: '1.4'
                                        }}>
                                            {task.description}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </>
            )}

            <div style={{
                marginTop: '16px',
                padding: '12px 16px',
                borderRadius: '8px',
                background: '#f9fafb',
                textAlign: 'center'
            }}>
                <Paragraph style={{ margin: 0, color: '#64748b', fontSize: '12px' }}>
                    Access organization management from <strong>Manage Organizations</strong> in Quick Actions.
                </Paragraph>
            </div>
        </div>
    );
};

export default OrganizationOverviewStep;
