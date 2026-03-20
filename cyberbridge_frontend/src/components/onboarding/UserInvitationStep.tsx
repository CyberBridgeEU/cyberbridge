// src/components/onboarding/UserInvitationStep.tsx
import React, { useEffect, useState } from 'react';
import { Form, Input, Select, Button, Table, Space, Typography, Empty, notification, Card, Tag } from 'antd';
import { UserAddOutlined, DeleteOutlined, MailOutlined } from '@ant-design/icons';
import useOnboardingStore, { InvitedUser } from '../../store/useOnboardingStore';
import useUserStore from '../../store/useUserStore';
import useAuthStore from '../../store/useAuthStore';
import { cyberbridge_back_end_rest_api } from '../../constants/urls';

const { Title, Text } = Typography;

interface Role {
    id: string;
    role_name: string;
}

const UserInvitationStep: React.FC = () => {
    const [form] = Form.useForm();
    const [api, contextHolder] = notification.useNotification();
    const [roles, setRoles] = useState<Role[]>([]);
    const [loadingRoles, setLoadingRoles] = useState(false);
    const [creating, setCreating] = useState(false);

    const { invitedUsers, addInvitedUser, removeInvitedUser } = useOnboardingStore();
    const { createUser, current_user } = useUserStore();
    const authStore = useAuthStore();

    useEffect(() => {
        fetchRoles();
    }, []);

    const fetchRoles = async () => {
        setLoadingRoles(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/get_all_roles`, {
                headers: {
                    ...authStore.getAuthHeader()
                }
            });

            if (response.ok) {
                const data = await response.json();
                // Filter to only show org_admin and org_user roles for invitation
                const filteredRoles = data.filter((role: Role) =>
                    ['org_admin', 'org_user'].includes(role.role_name)
                );
                setRoles(filteredRoles);
            }
        } catch (error) {
            console.error('Error fetching roles:', error);
        } finally {
            setLoadingRoles(false);
        }
    };

    const generatePassword = () => {
        // Generate a secure random password
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%';
        let password = '';
        for (let i = 0; i < 12; i++) {
            password += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return password;
    };

    const handleAddUser = async (values: { email: string; roleId: string }) => {
        // Check if email already exists in invited users
        if (invitedUsers.find(u => u.email === values.email)) {
            api.warning({
                message: 'Duplicate Email',
                description: 'This email has already been added.'
            });
            return;
        }

        setCreating(true);
        try {
            // Get the current user's organization ID
            const orgId = current_user?.organisation_id;
            if (!orgId) {
                throw new Error('Organization ID not found');
            }

            // Generate a temporary password
            const tempPassword = generatePassword();

            // Create the user
            const success = await createUser(values.email, tempPassword, values.roleId, orgId);

            if (success) {
                addInvitedUser({ email: values.email, roleId: values.roleId });
                form.resetFields();

                // Send invitation email with temporary password
                try {
                    await fetch(`${cyberbridge_back_end_rest_api}/auth/send-invitation`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            ...authStore.getAuthHeader()
                        },
                        body: JSON.stringify({ email: values.email, temporary_password: tempPassword })
                    });
                    api.success({
                        message: 'User Added',
                        description: `${values.email} has been added and an invitation email has been sent.`
                    });
                } catch {
                    api.success({
                        message: 'User Added',
                        description: `${values.email} has been added, but the invitation email could not be sent. Please share credentials manually.`
                    });
                }
            } else {
                api.error({
                    message: 'Error',
                    description: 'Failed to create user. The email may already be registered.'
                });
            }
        } catch (error) {
            api.error({
                message: 'Error',
                description: error instanceof Error ? error.message : 'Failed to add user.'
            });
        } finally {
            setCreating(false);
        }
    };

    const getRoleName = (roleId: string) => {
        const role = roles.find(r => r.id === roleId);
        return role?.role_name?.replace('_', ' ') || 'Unknown';
    };

    const getRoleColor = (roleId: string) => {
        const role = roles.find(r => r.id === roleId);
        if (role?.role_name === 'org_admin') return 'purple';
        return 'blue';
    };

    const columns = [
        {
            title: 'Email',
            dataIndex: 'email',
            key: 'email',
            render: (email: string) => (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <MailOutlined style={{ color: '#0f386a' }} />
                    {email}
                </div>
            )
        },
        {
            title: 'Role',
            dataIndex: 'roleId',
            key: 'roleId',
            render: (roleId: string) => (
                <Tag color={getRoleColor(roleId)}>
                    {getRoleName(roleId)}
                </Tag>
            )
        },
        {
            title: 'Action',
            key: 'action',
            width: 80,
            render: (_: unknown, record: InvitedUser) => (
                <Button
                    type="text"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={() => removeInvitedUser(record.email)}
                    size="small"
                />
            )
        }
    ];

    return (
        <div>
            {contextHolder}
            <div style={{ marginBottom: '24px' }}>
                <Title level={4} style={{ marginBottom: '8px', color: '#1a365d' }}>
                    Invite Team Members
                </Title>
                <Text type="secondary">
                    Add team members to your organization. They'll be able to access CyberBridge and collaborate on compliance.
                </Text>
            </div>

            <Card style={{ marginBottom: '24px', backgroundColor: '#fafafa' }}>
                <Form
                    form={form}
                    layout="inline"
                    onFinish={handleAddUser}
                    style={{ width: '100%' }}
                >
                    <Form.Item
                        name="email"
                        rules={[
                            { required: true, message: 'Enter email' },
                            { type: 'email', message: 'Enter a valid email' }
                        ]}
                        style={{ flex: 1, minWidth: '200px', marginBottom: '8px' }}
                    >
                        <Input
                            placeholder="Enter email address"
                            prefix={<MailOutlined style={{ color: '#8c8c8c' }} />}
                        />
                    </Form.Item>
                    <Form.Item
                        name="roleId"
                        rules={[{ required: true, message: 'Select role' }]}
                        style={{ width: '160px', marginBottom: '8px' }}
                    >
                        <Select
                            placeholder="Select role"
                            loading={loadingRoles}
                        >
                            {roles.map(role => (
                                <Select.Option key={role.id} value={role.id}>
                                    {role.role_name.replace('_', ' ')}
                                </Select.Option>
                            ))}
                        </Select>
                    </Form.Item>
                    <Form.Item style={{ marginBottom: '8px' }}>
                        <Button
                            type="primary"
                            htmlType="submit"
                            icon={<UserAddOutlined />}
                            loading={creating}
                            style={{
                                backgroundColor: '#0f386a',
                                borderColor: '#0f386a'
                            }}
                        >
                            Add User
                        </Button>
                    </Form.Item>
                </Form>
            </Card>

            {invitedUsers.length > 0 ? (
                <Table
                    columns={columns}
                    dataSource={invitedUsers.map((u, i) => ({ ...u, key: i }))}
                    pagination={false}
                    size="small"
                    style={{ backgroundColor: 'white', borderRadius: '8px' }}
                />
            ) : (
                <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={
                        <span style={{ color: '#8c8c8c' }}>
                            No team members added yet. You can add them now or later.
                        </span>
                    }
                />
            )}

            <div style={{ marginTop: '16px', textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                    New users will need to set their password when they first log in. You can also add more users later from User Management.
                </Text>
            </div>
        </div>
    );
};

export default UserInvitationStep;
