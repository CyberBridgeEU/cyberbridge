// src/components/superadmin-onboarding/UserManagementStep.tsx
import React, { useEffect } from 'react';
import { Typography, Alert, Spin, Empty, Avatar, Tag } from 'antd';
import {
    TeamOutlined,
    UserOutlined,
    ClockCircleOutlined,
    CheckCircleOutlined,
    ExclamationCircleOutlined
} from '@ant-design/icons';
import { useAdminAreaStore, PendingUser } from '../../store/adminAreaStore';
import useSuperAdminOnboardingStore from '../../store/useSuperAdminOnboardingStore';

const { Title, Paragraph } = Typography;

const UserManagementStep: React.FC = () => {
    const { pendingUsers, fetchPendingUsers, loading } = useAdminAreaStore();
    const { addViewedSection } = useSuperAdminOnboardingStore();

    useEffect(() => {
        fetchPendingUsers();
        addViewedSection('user-management');
    }, [fetchPendingUsers, addViewedSection]);

    const getRoleColor = (role: string) => {
        const colorMap: Record<string, string> = {
            'super_admin': '#dc2626',
            'org_admin': '#8b5cf6',
            'org_user': '#10b981'
        };
        return colorMap[role] || '#0f386a';
    };

    return (
        <div style={{ padding: '0 16px' }}>
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                <Title level={4} style={{ margin: 0, color: '#1a365d' }}>
                    User Management
                </Title>
                <Paragraph style={{ color: '#8c8c8c', fontSize: '14px', marginTop: '8px' }}>
                    Review and approve user registrations across all organizations.
                </Paragraph>
            </div>

            {/* User Management Features */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '12px',
                marginBottom: '20px'
            }}>
                <div style={{
                    padding: '14px',
                    borderRadius: '10px',
                    background: '#fffbeb',
                    border: '1px solid #fde68a',
                    textAlign: 'center'
                }}>
                    <ClockCircleOutlined style={{ fontSize: '24px', color: '#f59e0b', marginBottom: '8px' }} />
                    <div style={{ fontSize: '20px', fontWeight: 700, color: '#f59e0b' }}>
                        {pendingUsers.length}
                    </div>
                    <div style={{ fontSize: '11px', color: '#92400e' }}>
                        Pending Approvals
                    </div>
                </div>
                <div style={{
                    padding: '14px',
                    borderRadius: '10px',
                    background: '#f0fdfa',
                    border: '1px solid #99f6e4',
                    textAlign: 'center'
                }}>
                    <CheckCircleOutlined style={{ fontSize: '24px', color: '#10b981', marginBottom: '8px' }} />
                    <div style={{ fontSize: '11px', color: '#065f46', marginTop: '24px' }}>
                        Approve Users
                    </div>
                </div>
                <div style={{
                    padding: '14px',
                    borderRadius: '10px',
                    background: '#fef2f2',
                    border: '1px solid #fecaca',
                    textAlign: 'center'
                }}>
                    <ExclamationCircleOutlined style={{ fontSize: '24px', color: '#dc2626', marginBottom: '8px' }} />
                    <div style={{ fontSize: '11px', color: '#991b1b', marginTop: '24px' }}>
                        Reject/Deactivate
                    </div>
                </div>
            </div>

            {loading ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <Spin size="large" />
                    <Paragraph style={{ marginTop: '16px', color: '#8c8c8c' }}>
                        Loading pending users...
                    </Paragraph>
                </div>
            ) : pendingUsers.length > 0 ? (
                <>
                    <Alert
                        message={`${pendingUsers.length} user${pendingUsers.length !== 1 ? 's' : ''} awaiting approval`}
                        description="Review user requests from the Admin Area after completing setup."
                        type="warning"
                        showIcon
                        icon={<ClockCircleOutlined />}
                        style={{ marginBottom: '16px' }}
                    />

                    <div style={{
                        maxHeight: '200px',
                        overflowY: 'auto',
                        border: '1px solid #f0f0f0',
                        borderRadius: '10px'
                    }}>
                        {pendingUsers.slice(0, 5).map((user: PendingUser, index: number) => (
                            <div
                                key={user.id}
                                style={{
                                    padding: '12px 16px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'space-between',
                                    borderBottom: index < Math.min(pendingUsers.length, 5) - 1 ? '1px solid #f0f0f0' : 'none',
                                    background: index % 2 === 0 ? '#fafafa' : 'white'
                                }}
                            >
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                    <Avatar
                                        size="small"
                                        icon={<UserOutlined />}
                                        style={{ backgroundColor: getRoleColor(user.role_name) }}
                                    />
                                    <div>
                                        <div style={{ fontSize: '13px', fontWeight: 500, color: '#1a365d' }}>
                                            {user.email}
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#8c8c8c' }}>
                                            {user.organisation_name || 'No Organization'}
                                        </div>
                                    </div>
                                </div>
                                <Tag
                                    color={getRoleColor(user.role_name)}
                                    style={{ margin: 0, fontSize: '11px' }}
                                >
                                    {user.role_name?.replace('_', ' ')}
                                </Tag>
                            </div>
                        ))}
                        {pendingUsers.length > 5 && (
                            <div style={{
                                padding: '10px',
                                textAlign: 'center',
                                background: '#f9fafb',
                                fontSize: '12px',
                                color: '#64748b'
                            }}>
                                +{pendingUsers.length - 5} more pending users
                            </div>
                        )}
                    </div>
                </>
            ) : (
                <Alert
                    message="No Pending Users"
                    description="All user registration requests have been processed. New requests will appear here."
                    type="success"
                    showIcon
                    icon={<CheckCircleOutlined />}
                    style={{ marginBottom: '16px' }}
                />
            )}

            <div style={{
                marginTop: '16px',
                padding: '14px 16px',
                borderRadius: '8px',
                background: '#f9fafb',
                border: '1px solid #e5e7eb'
            }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                    <TeamOutlined style={{ fontSize: '18px', color: '#0f386a', marginTop: '2px' }} />
                    <div>
                        <div style={{ fontWeight: 600, fontSize: '13px', color: '#1a365d', marginBottom: '4px' }}>
                            User Administration
                        </div>
                        <Paragraph style={{ margin: 0, color: '#64748b', fontSize: '12px' }}>
                            Access the Admin Area from Quick Actions to approve, reject, or deactivate users.
                            You can also manage user roles and organization assignments.
                        </Paragraph>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UserManagementStep;
