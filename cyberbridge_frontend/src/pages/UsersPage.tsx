import { Table, notification, Modal, Tag, Select, Input, Button, Typography, Space, Dropdown } from "antd";
import type { MenuProps } from 'antd';
import type { ColumnsType, ColumnType } from 'antd/es/table';
import type { FilterDropdownProps } from 'antd/es/table/interface';
import Sidebar from "../components/Sidebar.tsx";
import { UserOutlined, PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, ReloadOutlined, TeamOutlined, DownOutlined, CheckCircleOutlined, ClockCircleOutlined, StopOutlined, LockOutlined } from '@ant-design/icons';
import useUserStore from "../store/useUserStore.ts";
import { useAdminAreaStore } from '../store/adminAreaStore';
import useAuthStore from "../store/useAuthStore.ts";
import { useEffect, useState, useMemo } from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import { ManageUsersInfo } from "../constants/infoContent.tsx";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const { Text } = Typography;

const UsersPage = () => {
    // Menu highlighting
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Store access
    const {
        organisations,
        roles,
        fetchOrganisations,
        fetchRoles,
        createUser,
        updateUser,
        deleteUser,
        current_user,
        error
    } = useUserStore();

    // Admin area store for user management with status control
    const {
        users: adminUsers,
        loading: adminLoading,
        fetchAllUsers,
        updateUserStatus,
        clearError
    } = useAdminAreaStore();

    const { getAuthHeader } = useAuthStore();

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    // Selected user state
    const [selectedUser, setSelectedUser] = useState<string | null>(null);

    // Form visibility state
    const [showForm, setShowForm] = useState<boolean>(false);

    // Form state
    const [userEmail, setUserEmail] = useState('');
    const [userPassword, setUserPassword] = useState('');
    const [roleSelectedId, setRoleSelectedId] = useState<string | undefined>(undefined);
    const [orgSelectedId, setOrgSelectedId] = useState<string | undefined>(undefined);
    const [authProvider, setAuthProvider] = useState<string>('local');

    // Determine user role
    const isSuperAdmin = current_user?.role_name === 'super_admin';
    const isOrgAdmin = current_user?.role_name === 'org_admin';

    // Fetch data on component mount
    useEffect(() => {
        const fetchData = async () => {
            await fetchOrganisations();
            await fetchRoles();
            await fetchAllUsers();
        };
        fetchData();
    }, [fetchOrganisations, fetchRoles, fetchAllUsers]);

    // Handle status change
    const handleStatusChange = async (userId: string, newStatus: string) => {
        try {
            await updateUserStatus(userId, newStatus);
            api.success({
                message: 'Status Updated',
                description: `User status updated to ${newStatus}`,
                duration: 4,
            });
        } catch (err) {
            api.error({
                message: 'Status Update Failed',
                description: 'Failed to update user status',
                duration: 4,
            });
        }
    };

    // Filter roles based on user type
    const availableRoles = isSuperAdmin
        ? roles
        : roles.filter(role => role.role_name === 'org_admin' || role.role_name === 'org_user');

    // Get unique organizations for filter
    const organizationNames = useMemo(() => {
        const orgs = [...new Set(adminUsers.map(u => u.organisation_name))];
        return orgs.sort();
    }, [adminUsers]);

    // Filter users based on role permissions (org_admin can only see their org's users)
    const displayedUsers = useMemo(() => {
        if (isOrgAdmin && current_user?.organisation_name) {
            return adminUsers.filter(u => u.organisation_name === current_user.organisation_name);
        }
        return adminUsers;
    }, [adminUsers, isOrgAdmin, current_user]);

    const handleRefresh = () => {
        fetchAllUsers();
        api.info({
            message: 'Refreshing',
            description: 'Refreshing user list...',
            duration: 2,
        });
    };

    // Handle form submission
    const handleSave = async () => {
        if (!userEmail) {
            api.error({
                message: 'User Operation Failed',
                description: 'Please enter an email address',
                duration: 4,
            });
            return;
        }

        if (!selectedUser && authProvider === 'local' && !userPassword) {
            api.error({
                message: 'User Operation Failed',
                description: 'Please enter a password for the new user',
                duration: 4,
            });
            return;
        }

        if (!roleSelectedId) {
            api.error({
                message: 'User Operation Failed',
                description: 'Please select a role',
                duration: 4,
            });
            return;
        }

        const isUpdate = selectedUser !== null;
        let success;

        if (isUpdate) {
            success = await updateUser(
                userEmail,
                userPassword || null,
                roleSelectedId,
                selectedUser
            );
        } else {
            const organisationId = isSuperAdmin ? orgSelectedId : current_user?.organisation_id;
            if (!organisationId) {
                api.error({
                    message: 'User Creation Failed',
                    description: 'Please select an organization',
                    duration: 4,
                });
                return;
            }
            success = await createUser(
                userEmail,
                userPassword,
                roleSelectedId,
                organisationId,
                authProvider
            );
        }

        if (success) {
            api.success({
                message: isUpdate ? 'User Update Success' : 'User Creation Success',
                description: isUpdate ? 'User updated successfully' : 'User created successfully',
                duration: 4,
            });
            handleClear(true);
            await fetchAllUsers();
        } else {
            api.error({
                message: isUpdate ? 'User Update Failed' : 'User Creation Failed',
                description: error || (isUpdate ? 'Failed to update user' : 'Failed to create user'),
                duration: 4,
            });
        }
    };

    // Clear form
    const handleClear = (hideForm: boolean = false) => {
        setUserEmail('');
        setUserPassword('');
        setRoleSelectedId(undefined);
        setOrgSelectedId(undefined);
        setAuthProvider('local');
        setSelectedUser(null);
        if (hideForm) {
            setShowForm(false);
        }
    };

    // Handle user deletion
    const handleDelete = async () => {
        if (!selectedUser) {
            api.error({
                message: 'User Deletion Failed',
                description: 'Please select a user to delete',
                duration: 4,
            });
            return;
        }

        if (selectedUser === current_user?.id) {
            api.error({
                message: 'User Deletion Failed',
                description: 'You cannot delete your own account',
                duration: 4,
            });
            return;
        }

        const success = await deleteUser(selectedUser);

        if (success) {
            api.success({
                message: 'User Deletion Success',
                description: 'User deleted successfully',
                duration: 4,
            });
            handleClear(true);
            await fetchAllUsers();
        } else {
            api.error({
                message: 'User Deletion Failed',
                description: error || 'Failed to delete user',
                duration: 4,
            });
        }
    };

    // Role options for select
    const roleOptions = availableRoles.map(role => ({
        label: role.role_name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: role.id
    }));

    // Organization options for select
    const orgOptions = organisations.map(org => ({
        label: org.name + (org.domain ? ` (${org.domain})` : ''),
        value: org.id
    }));

    // Get organization name by ID
    const getOrgName = (orgId: string) => {
        const org = organisations.find(o => o.id === orgId);
        return org ? org.name : 'Unknown';
    };

    // Role tag color
    const getRoleColor = (roleName: string) => {
        switch (roleName) {
            case 'super_admin': return 'red';
            case 'org_admin': return 'orange';
            case 'org_user': return 'blue';
            default: return 'default';
        }
    };

    // Email search filter for table
    const getEmailSearchProps = (): ColumnType<any> => ({
        filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: FilterDropdownProps) => (
            <div style={{ padding: 8 }}>
                <Input
                    placeholder="Search email"
                    value={selectedKeys[0]}
                    onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
                    onPressEnter={() => confirm()}
                    style={{ marginBottom: 8, display: 'block' }}
                />
                <Space>
                    <Button
                        type="primary"
                        onClick={() => confirm()}
                        icon={<SearchOutlined />}
                        size="small"
                        style={{ width: 90 }}
                    >
                        Search
                    </Button>
                    <Button onClick={() => clearFilters && clearFilters()} size="small" style={{ width: 90 }}>
                        Reset
                    </Button>
                </Space>
            </div>
        ),
        filterIcon: (filtered: boolean) => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
        onFilter: (value, record) => record.email.toLowerCase().includes(value.toString().toLowerCase()),
    });

    // Table columns with built-in filters
    const columns: ColumnsType<any> = [
        {
            title: 'Email',
            dataIndex: 'email',
            key: 'email',
            sorter: (a: any, b: any) => a.email.localeCompare(b.email),
            ...getEmailSearchProps(),
            render: (email: string) => (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <UserOutlined />
                    <strong>{email}</strong>
                </span>
            ),
        },
        {
            title: 'Role',
            dataIndex: 'role_name',
            key: 'role_name',
            filters: [
                { text: 'Super Admin', value: 'super_admin' },
                { text: 'Organization Admin', value: 'org_admin' },
                { text: 'Organization User', value: 'org_user' },
            ],
            onFilter: (value, record) => record.role_name === value,
            render: (roleName: string) => {
                const displayText = roleName === 'super_admin' ? 'Super Admin' :
                    roleName === 'org_admin' ? 'Organization Admin' :
                    roleName === 'org_user' ? 'Organization User' : roleName;
                return <Tag color={getRoleColor(roleName)}>{displayText}</Tag>;
            },
        },
        ...(isSuperAdmin ? [{
            title: 'Organization',
            dataIndex: 'organisation_name',
            key: 'organisation_name',
            sorter: (a: any, b: any) => (a.organisation_name || '').localeCompare(b.organisation_name || ''),
            filters: organizationNames.map(org => ({ text: org, value: org })),
            onFilter: (value: any, record: any) => record.organisation_name === value,
            render: (org: string) => (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <TeamOutlined />
                    {org}
                </span>
            ),
        }] : [{
            title: 'Organization',
            dataIndex: 'organisation_name',
            key: 'organisation_name',
            render: (org: string) => (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <TeamOutlined />
                    {org}
                </span>
            ),
        }]),
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: 180,
            filters: [
                { text: 'Pending Approval', value: 'pending_approval' },
                { text: 'Active', value: 'active' },
                { text: 'Inactive', value: 'inactive' },
            ],
            onFilter: (value, record) => record.status === value,
            render: (status: string, record: any) => {
                const statusConfig: Record<string, { color: string; icon: React.ReactNode; label: string; bgColor: string }> = {
                    'pending_approval': {
                        color: '#faad14',
                        icon: <ClockCircleOutlined />,
                        label: 'Pending',
                        bgColor: '#fffbe6'
                    },
                    'active': {
                        color: '#52c41a',
                        icon: <CheckCircleOutlined />,
                        label: 'Active',
                        bgColor: '#f6ffed'
                    },
                    'inactive': {
                        color: '#8c8c8c',
                        icon: <StopOutlined />,
                        label: 'Inactive',
                        bgColor: '#f5f5f5'
                    },
                };

                const config = statusConfig[status] || statusConfig['inactive'];

                // Protected super_admin accounts
                if (record.role_name === 'super_admin') {
                    return (
                        <div style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '4px 12px',
                            borderRadius: '6px',
                            backgroundColor: '#f0f0f0',
                            color: '#8c8c8c',
                            fontSize: '13px'
                        }}>
                            <LockOutlined style={{ fontSize: '12px' }} />
                            <span>Protected</span>
                        </div>
                    );
                }

                // No permission for org_admin on other orgs
                if (isOrgAdmin && record.organisation_name !== current_user?.organisation_name) {
                    return (
                        <div style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '4px 12px',
                            borderRadius: '6px',
                            backgroundColor: config.bgColor,
                            border: `1px solid ${config.color}`,
                            color: config.color,
                            fontSize: '13px'
                        }}>
                            {config.icon}
                            <span>{config.label}</span>
                        </div>
                    );
                }

                // Dropdown menu items
                const menuItems: MenuProps['items'] = [
                    {
                        key: 'pending_approval',
                        label: (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 0' }}>
                                <ClockCircleOutlined style={{ color: '#faad14' }} />
                                <span>Pending Approval</span>
                                {status === 'pending_approval' && <CheckCircleOutlined style={{ color: '#1890ff', marginLeft: 'auto' }} />}
                            </div>
                        ),
                        disabled: status === 'pending_approval',
                    },
                    {
                        key: 'active',
                        label: (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 0' }}>
                                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                                <span>Active</span>
                                {status === 'active' && <CheckCircleOutlined style={{ color: '#1890ff', marginLeft: 'auto' }} />}
                            </div>
                        ),
                        disabled: status === 'active',
                    },
                    {
                        key: 'inactive',
                        label: (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 0' }}>
                                <StopOutlined style={{ color: '#8c8c8c' }} />
                                <span>Inactive</span>
                                {status === 'inactive' && <CheckCircleOutlined style={{ color: '#1890ff', marginLeft: 'auto' }} />}
                            </div>
                        ),
                        disabled: status === 'inactive',
                    },
                ];

                return (
                    <Dropdown
                        menu={{
                            items: menuItems,
                            onClick: ({ key }) => handleStatusChange(record.id, key),
                        }}
                        trigger={['click']}
                        disabled={adminLoading}
                    >
                        <div
                            onClick={(e) => e.stopPropagation()}
                            style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '6px',
                                padding: '4px 12px',
                                borderRadius: '6px',
                                backgroundColor: config.bgColor,
                                border: `1px solid ${config.color}`,
                                color: config.color,
                                fontSize: '13px',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.boxShadow = `0 2px 8px ${config.color}40`;
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.boxShadow = 'none';
                            }}
                        >
                            {config.icon}
                            <span style={{ fontWeight: 500 }}>{config.label}</span>
                            <DownOutlined style={{ fontSize: '10px', marginLeft: '4px' }} />
                        </div>
                    </Dropdown>
                );
            },
        },
        {
            title: 'Registration Date',
            dataIndex: 'created_at',
            key: 'created_at',
            sorter: (a: any, b: any) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
            render: (date: string) => {
                if (!date) return '-';
                const formattedDate = new Date(date).toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                });
                return <Text type="secondary">{formattedDate}</Text>;
            },
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 80,
            render: (_: any, record: any) => (
                <button
                    className="secondary-button"
                    onClick={(e) => {
                        e.stopPropagation();
                        const role = roles.find(r => r.role_name === record.role_name);
                        const org = organisations.find(o => o.name === record.organisation_name);
                        setSelectedUser(record.id);
                        setUserEmail(record.email);
                        setUserPassword('');
                        setRoleSelectedId(role?.id);
                        setOrgSelectedId(org?.id || undefined);
                        setAuthProvider(record.auth_provider || 'local');
                        setShowForm(true);
                    }}
                    style={{ padding: '4px 8px', fontSize: '12px' }}
                >
                    <EditOutlined />
                </button>
            ),
        },
    ];

    return (
        <div>
            {contextHolder}
            <div className={'page-parent'}>
                <Sidebar
                    selectedKeys={menuHighlighting.selectedKeys}
                    openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange}
                />
                <div className={'page-content'}>
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <UserOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Users"
                                infoContent={ManageUsersInfo}
                                className="page-title"
                            />
                        </div>
                        <div className="page-header-right">
                            {!showForm && (
                                <button
                                    className="add-button"
                                    onClick={() => {
                                        handleClear(false);
                                        setShowForm(true);
                                    }}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    <PlusOutlined /> Add User
                                </button>
                            )}
                        </div>
                    </div>

                    {/* User Management Section */}
                    <div className="page-section">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                            <h3 className="section-title" style={{ margin: 0 }}>User Account Management</h3>
                            <button className="secondary-button" onClick={handleRefresh} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <ReloadOutlined /> Refresh
                            </button>
                        </div>

                        {/* User Table */}
                        <div style={{ overflowX: 'auto' }}>
                            <Table
                                columns={columns}
                                dataSource={displayedUsers}
                                showSorterTooltip={{ target: 'sorter-icon' }}
                                loading={adminLoading}
                                onRow={(record) => {
                                    return {
                                        onClick: () => {
                                            const role = roles.find(r => r.role_name === record.role_name);
                                            const org = organisations.find(o => o.name === record.organisation_name);
                                            setSelectedUser(record.id);
                                            setUserEmail(record.email);
                                            setUserPassword('');
                                            setRoleSelectedId(role?.id);
                                            setOrgSelectedId(org?.id || undefined);
                                            setAuthProvider(record.auth_provider || 'local');
                                            setShowForm(true);
                                        },
                                        style: {
                                            cursor: 'pointer',
                                            backgroundColor: selectedUser === record.id ? '#e6f7ff' : undefined
                                        }
                                    };
                                }}
                                rowKey="id"
                                pagination={{
                                    showSizeChanger: true,
                                    pageSizeOptions: ['10', '20', '50'],
                                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} users`,
                                }}
                                scroll={{ x: 1200 }}
                            />
                        </div>
                    </div>

                    {/* User Modal */}
                    <Modal
                        title={
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {selectedUser ? (
                                    <EditOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                                ) : (
                                    <PlusOutlined style={{ fontSize: '20px', color: '#52c41a' }} />
                                )}
                                <span>{selectedUser ? 'Edit User' : 'Add New User'}</span>
                                {selectedUser && <Tag color="blue">Editing</Tag>}
                            </div>
                        }
                        open={showForm}
                        onCancel={() => handleClear(true)}
                        width={600}
                        footer={
                            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                {selectedUser && selectedUser !== current_user?.id && (
                                    <button
                                        className="delete-button"
                                        onClick={handleDelete}
                                        disabled={adminLoading}
                                        style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f', color: 'white' }}
                                    >
                                        <DeleteOutlined /> Delete User
                                    </button>
                                )}
                                <button
                                    className="secondary-button"
                                    onClick={() => handleClear(true)}
                                    disabled={adminLoading}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="add-button"
                                    onClick={handleSave}
                                    disabled={adminLoading}
                                    style={{
                                        backgroundColor: selectedUser ? '#1890ff' : '#52c41a',
                                        borderColor: selectedUser ? '#1890ff' : '#52c41a',
                                    }}
                                >
                                    {adminLoading ? 'Saving...' : selectedUser ? 'Update User' : 'Save User'}
                                </button>
                            </div>
                        }
                    >
                        <p style={{ color: '#8c8c8c', fontSize: '14px', marginBottom: '24px' }}>
                            {selectedUser
                                ? 'Update the user details below and click "Update User" to save changes.'
                                : 'Fill out the form below to create a new user.'}
                        </p>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div className="form-group">
                                <label className="form-label required">Email</label>
                                <input
                                    type="email"
                                    className="form-input"
                                    placeholder="Enter user email"
                                    value={userEmail}
                                    onChange={(e) => setUserEmail(e.target.value)}
                                    style={{ width: '100%' }}
                                />
                            </div>

                            {!selectedUser && (
                                <div className="form-group">
                                    <label className="form-label">Authentication Method</label>
                                    <Select
                                        value={authProvider}
                                        onChange={(value) => { setAuthProvider(value); if (value !== 'local') setUserPassword(''); }}
                                        options={[
                                            { label: 'Password (Local)', value: 'local' },
                                            { label: 'Google SSO', value: 'google' },
                                            { label: 'Microsoft SSO', value: 'microsoft' },
                                        ]}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                            )}

                            {(authProvider === 'local') && (
                                <div className="form-group">
                                    <label className="form-label">{selectedUser ? 'New Password (leave blank to keep current)' : 'Password'}</label>
                                    <input
                                        type="password"
                                        className="form-input"
                                        placeholder={selectedUser ? 'Enter new password (optional)' : 'Enter password'}
                                        value={userPassword}
                                        onChange={(e) => setUserPassword(e.target.value)}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                            )}

                            <div className="form-group">
                                <label className="form-label required">Role</label>
                                <Select
                                    showSearch
                                    placeholder="Select role"
                                    onChange={(value) => setRoleSelectedId(value)}
                                    options={roleOptions}
                                    filterOption={(input, option) =>
                                        (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                                    }
                                    value={roleSelectedId}
                                    style={{ width: '100%' }}
                                />
                            </div>

                            {isSuperAdmin && !selectedUser && (
                                <div className="form-group">
                                    <label className="form-label required">Organization</label>
                                    <Select
                                        showSearch
                                        placeholder="Select organization"
                                        onChange={(value) => setOrgSelectedId(value)}
                                        options={orgOptions}
                                        filterOption={(input, option) =>
                                            (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                                        }
                                        value={orgSelectedId}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                            )}

                            {selectedUser && (
                                <div className="form-group">
                                    <label className="form-label">Organization</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        value={getOrgName(orgSelectedId || '')}
                                        disabled
                                        style={{ width: '100%', backgroundColor: '#f5f5f5' }}
                                    />
                                    <p style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '4px' }}>
                                        Organization cannot be changed after user creation.
                                    </p>
                                </div>
                            )}
                        </div>
                    </Modal>
                </div>
            </div>
        </div>
    );
};

export default UsersPage;
