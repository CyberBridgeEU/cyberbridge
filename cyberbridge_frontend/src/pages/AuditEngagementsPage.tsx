import { Table, notification, Tag, Modal, Button, Input, DatePicker, Select, Form, Space, Tooltip, Tabs, Descriptions, Badge, Empty, Popconfirm, Checkbox, List, Card, Row, Col } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { AuditOutlined, PlusOutlined, DeleteOutlined, EyeOutlined, UserAddOutlined, MailOutlined, TeamOutlined, SendOutlined, StopOutlined, CommentOutlined, UserOutlined, BellOutlined, CheckOutlined, AppstoreOutlined, UnorderedListOutlined, SearchOutlined } from '@ant-design/icons';
import useAuditEngagementStore, { AuditEngagement, AuditorInvitation, CreateEngagementRequest, CreateInvitationRequest, EngagementComment } from "../store/useAuditEngagementStore.ts";
import useAuditNotificationStore from "../store/useAuditNotificationStore.ts";
import useAuthStore from "../store/useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import useUserStore from "../store/useUserStore.ts";
import useAssessmentsStore from "../store/useAssessmentsStore.ts";
import { useEffect, useState } from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { TextArea } = Input;
const { RangePicker } = DatePicker;

const AuditEngagementsPage = () => {
    // Menu highlighting
    const [location, setLocation] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // View mode state
    const [engagementViewMode, setEngagementViewMode] = useState<'grid' | 'list'>('list');
    const [engagementSearchText, setEngagementSearchText] = useState('');

    // Store access
    const {
        engagements,
        selectedEngagement,
        invitations,
        auditorRoles,
        comments,
        totalCount,
        loading,
        error,
        loadEngagements,
        loadEngagement,
        createEngagement,
        updateEngagement,
        updateEngagementStatus,
        deleteEngagement,
        setSelectedEngagement,
        loadInvitations,
        createInvitation,
        revokeInvitation,
        resendInvitation,
        loadAuditorRoles,
        loadComments,
        getStatusColor,
        getStatusLabel,
        clearError
    } = useAuditEngagementStore();

    const { current_user } = useUserStore();
    const { assessments, fetchAssessments } = useAssessmentsStore();
    const {
        notifications,
        unreadCount,
        loadNotifications,
        markAsRead,
        deleteNotification,
        getNotificationTypeLabel,
        getNotificationTypeColor
    } = useAuditNotificationStore();

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    // Modal states
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showDetailModal, setShowDetailModal] = useState(false);
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [editMode, setEditMode] = useState(false);

    // Form instances
    const [createForm] = Form.useForm();
    const [inviteForm] = Form.useForm();

    // Filter state
    const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
    const [ownerOnlyFilter, setOwnerOnlyFilter] = useState(false);

    // Reply comment state
    const [showReplyModal, setShowReplyModal] = useState(false);
    const [replyToComment, setReplyToComment] = useState<EngagementComment | null>(null);
    const [replyText, setReplyText] = useState('');

    // Fetch data on mount
    useEffect(() => {
        loadEngagements(statusFilter, ownerOnlyFilter);
        loadAuditorRoles();
        if (current_user?.id) {
            fetchAssessments();
        }
    }, [statusFilter, ownerOnlyFilter, current_user?.id]);

    // Show error notifications
    useEffect(() => {
        if (error) {
            api.error({
                message: 'Error',
                description: error,
                duration: 4,
            });
            clearError();
        }
    }, [error]);

    // Table columns
    const columns: ColumnsType<AuditEngagement> = [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            sorter: (a, b) => a.name.localeCompare(b.name),
            render: (text, record) => (
                <a onClick={() => handleViewEngagement(record)}>{text}</a>
            )
        },
        {
            title: 'Assessment',
            dataIndex: 'assessment_name',
            key: 'assessment_name',
            render: (text) => text || '-'
        },
        {
            title: 'Framework',
            dataIndex: 'framework_name',
            key: 'framework_name',
            render: (text) => text || '-'
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            filters: [
                { text: 'Draft', value: 'draft' },
                { text: 'Planned', value: 'planned' },
                { text: 'In Progress', value: 'in_progress' },
                { text: 'Under Review', value: 'review' },
                { text: 'Completed', value: 'completed' },
                { text: 'Closed', value: 'closed' },
            ],
            onFilter: (value, record) => record.status === value,
            render: (status) => (
                <Tag color={getStatusColor(status)}>{getStatusLabel(status)}</Tag>
            )
        },
        {
            title: 'Owner',
            dataIndex: 'owner_name',
            key: 'owner_name',
            render: (text, record) => (
                <Tooltip title={record.owner_email}>
                    {text || '-'}
                </Tooltip>
            )
        },
        {
            title: 'Auditors',
            key: 'auditors',
            render: (_, record) => (
                <Space>
                    <TeamOutlined />
                    <span>{record.active_invitation_count || 0} active</span>
                </Space>
            )
        },
        {
            title: 'Audit Period',
            key: 'audit_period',
            render: (_, record) => {
                if (!record.audit_period_start && !record.audit_period_end) {
                    return '-';
                }
                const start = record.audit_period_start ? dayjs(record.audit_period_start).format('MMM D, YYYY') : 'TBD';
                const end = record.audit_period_end ? dayjs(record.audit_period_end).format('MMM D, YYYY') : 'TBD';
                return `${start} - ${end}`;
            }
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 150,
            render: (_, record) => (
                <Space>
                    <Tooltip title="View Details">
                        <Button
                            type="text"
                            icon={<EyeOutlined />}
                            onClick={() => handleViewEngagement(record)}
                        />
                    </Tooltip>
                    <Tooltip title="Invite Auditor">
                        <Button
                            type="text"
                            icon={<UserAddOutlined />}
                            onClick={() => handleInviteAuditor(record)}
                            disabled={record.status === 'closed'}
                        />
                    </Tooltip>
                    {(current_user?.role_name === 'super_admin' || current_user?.role_name === 'org_admin') && (
                        <Popconfirm
                            title="Delete this engagement?"
                            description="This action cannot be undone."
                            onConfirm={() => handleDeleteEngagement(record.id)}
                            okText="Delete"
                            cancelText="Cancel"
                            okButtonProps={{ danger: true }}
                        >
                            <Tooltip title="Delete">
                                <Button
                                    type="text"
                                    danger
                                    icon={<DeleteOutlined />}
                                />
                            </Tooltip>
                        </Popconfirm>
                    )}
                </Space>
            )
        }
    ];

    // Invitation table columns
    const invitationColumns: ColumnsType<AuditorInvitation> = [
        {
            title: 'Email',
            dataIndex: 'email',
            key: 'email',
        },
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            render: (text) => text || '-'
        },
        {
            title: 'Company',
            dataIndex: 'company',
            key: 'company',
            render: (text) => text || '-'
        },
        {
            title: 'Role',
            dataIndex: 'role_name',
            key: 'role_name',
            render: (text) => (
                <Tag color={text === 'auditor_lead' ? 'blue' : 'default'}>
                    {text ? text.replace('_', ' ').toUpperCase() : '-'}
                </Tag>
            )
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status, record) => {
                const colors: Record<string, string> = {
                    pending: 'orange',
                    accepted: 'green',
                    expired: 'red',
                    revoked: 'default'
                };
                return (
                    <Space direction="vertical" size={0}>
                        <Tag color={colors[status] || 'default'}>{status.toUpperCase()}</Tag>
                        {record.token_expired && status === 'pending' && (
                            <small style={{ color: '#ff4d4f' }}>Token expired</small>
                        )}
                    </Space>
                );
            }
        },
        {
            title: 'MFA',
            dataIndex: 'mfa_enabled',
            key: 'mfa_enabled',
            render: (enabled) => enabled ? <Tag color="green">Enabled</Tag> : <Tag>Disabled</Tag>
        },
        {
            title: 'Access Window',
            key: 'access_window',
            render: (_, record) => {
                if (!record.access_start && !record.access_end) {
                    return 'No restriction';
                }
                const start = record.access_start ? dayjs(record.access_start).format('MMM D') : 'Now';
                const end = record.access_end ? dayjs(record.access_end).format('MMM D') : 'No end';
                return `${start} - ${end}`;
            }
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 120,
            render: (_, record) => (
                <Space>
                    {record.status === 'pending' && (
                        <Tooltip title="Resend Invitation">
                            <Button
                                type="text"
                                icon={<SendOutlined />}
                                onClick={() => handleResendInvitation(record)}
                            />
                        </Tooltip>
                    )}
                    {(record.status === 'pending' || record.status === 'accepted') && (
                        <Popconfirm
                            title="Revoke this invitation?"
                            onConfirm={() => handleRevokeInvitation(record.id)}
                            okText="Revoke"
                            cancelText="Cancel"
                            okButtonProps={{ danger: true }}
                        >
                            <Tooltip title="Revoke">
                                <Button
                                    type="text"
                                    danger
                                    icon={<StopOutlined />}
                                />
                            </Tooltip>
                        </Popconfirm>
                    )}
                </Space>
            )
        }
    ];

    // Handlers
    const handleCreateEngagement = () => {
        createForm.resetFields();
        setShowCreateModal(true);
    };

    const handleViewEngagement = async (engagement: AuditEngagement) => {
        await loadEngagement(engagement.id);
        await loadInvitations(engagement.id);
        await loadComments(engagement.id);
        await loadNotifications(engagement.id);
        setEditMode(false);
        setShowDetailModal(true);
    };

    const handleInviteAuditor = async (engagement: AuditEngagement) => {
        await loadEngagement(engagement.id);
        inviteForm.resetFields();
        setShowInviteModal(true);
    };

    const handleDeleteEngagement = async (id: string) => {
        try {
            await deleteEngagement(id);
            api.success({
                message: 'Engagement Deleted',
                description: 'The audit engagement has been deleted.',
            });
        } catch (err) {
            // Error handled in store
        }
    };

    const handleRevokeInvitation = async (invitationId: string) => {
        if (!selectedEngagement) return;
        try {
            await revokeInvitation(selectedEngagement.id, invitationId);
            api.success({
                message: 'Invitation Revoked',
                description: 'The auditor invitation has been revoked.',
            });
        } catch (err) {
            // Error handled in store
        }
    };

    const handleResendInvitation = async (invitation: AuditorInvitation) => {
        if (!selectedEngagement) return;
        try {
            await resendInvitation(selectedEngagement.id, invitation.id);
            api.success({
                message: 'Invitation Resent',
                description: `A new invitation email has been sent to ${invitation.email}.`,
            });
        } catch (err) {
            // Error handled in store
        }
    };

    const handleStatusChange = async (newStatus: string) => {
        if (!selectedEngagement) return;
        try {
            await updateEngagementStatus(selectedEngagement.id, newStatus);
            api.success({
                message: 'Status Updated',
                description: `Engagement status changed to ${getStatusLabel(newStatus)}.`,
            });
        } catch (err) {
            // Error handled in store
        }
    };

    // Reply to a comment
    const handleReplyClick = (comment: EngagementComment) => {
        setReplyToComment(comment);
        setReplyText('');
        setShowReplyModal(true);
    };

    const handleReplySubmit = async () => {
        if (!selectedEngagement || !replyToComment || !replyText.trim()) return;

        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${selectedEngagement.id}/comments`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...authHeader
                    },
                    body: JSON.stringify({
                        target_type: replyToComment.targetType,
                        target_id: replyToComment.targetId,
                        content: replyText.trim(),
                        comment_type: 'observation',
                        parent_comment_id: replyToComment.id
                    })
                }
            );

            if (response.ok) {
                api.success({
                    message: 'Reply Sent',
                    description: 'Your reply has been submitted to the auditor.',
                });
                setShowReplyModal(false);
                setReplyToComment(null);
                setReplyText('');

                // Mark any notifications related to this comment as read
                const relatedNotifications = notifications.filter(
                    n => !n.isRead && n.sourceId === replyToComment.id
                );
                if (relatedNotifications.length > 0) {
                    await markAsRead(relatedNotifications.map(n => n.id));
                }

                // Reload comments
                await loadComments(selectedEngagement.id);
            } else {
                const errorData = await response.json();
                api.error({
                    message: 'Failed to Send Reply',
                    description: errorData.detail || 'An error occurred while sending your reply.',
                });
            }
        } catch (error) {
            api.error({
                message: 'Error',
                description: 'An error occurred while sending your reply.',
            });
        }
    };

    // Form submissions
    const onCreateSubmit = async (values: any) => {
        const data: CreateEngagementRequest = {
            name: values.name,
            description: values.description,
            assessment_id: values.assessment_id,
            audit_period_start: values.audit_period?.[0]?.toISOString(),
            audit_period_end: values.audit_period?.[1]?.toISOString(),
            planned_start_date: values.planned_dates?.[0]?.toISOString(),
            planned_end_date: values.planned_dates?.[1]?.toISOString(),
        };

        try {
            await createEngagement(data);
            setShowCreateModal(false);
            api.success({
                message: 'Engagement Created',
                description: 'The audit engagement has been created successfully.',
            });
        } catch (err) {
            // Error handled in store
        }
    };

    const onInviteSubmit = async (values: any) => {
        if (!selectedEngagement) return;

        const data: CreateInvitationRequest = {
            email: values.email,
            name: values.name,
            company: values.company,
            auditor_role_id: values.auditor_role_id,
            access_start: values.access_window?.[0]?.toISOString(),
            access_end: values.access_window?.[1]?.toISOString(),
            mfa_enabled: values.mfa_enabled || false,
            watermark_downloads: values.watermark_downloads !== false,
            download_restricted: values.download_restricted || false,
        };

        try {
            const invitation = await createInvitation(selectedEngagement.id, data);
            setShowInviteModal(false);
            await loadInvitations(selectedEngagement.id);
            api.success({
                message: 'Invitation Sent',
                description: `An invitation has been sent to ${values.email}.`,
            });
        } catch (err) {
            // Error handled in store
        }
    };

    // Status transition options
    const getStatusTransitions = (currentStatus: string) => {
        const transitions: Record<string, string[]> = {
            draft: ['planned', 'in_progress'],
            planned: ['in_progress', 'closed'],
            in_progress: ['review', 'completed'],
            review: ['in_progress', 'completed'],
            completed: ['closed'],
            closed: []
        };
        return transitions[currentStatus] || [];
    };

    // Search filtered engagements
    const searchFilteredEngagements = engagements.filter(engagement =>
        engagement.name?.toLowerCase().includes(engagementSearchText.toLowerCase()) ||
        engagement.assessment_name?.toLowerCase().includes(engagementSearchText.toLowerCase()) ||
        engagement.framework_name?.toLowerCase().includes(engagementSearchText.toLowerCase()) ||
        engagement.owner_name?.toLowerCase().includes(engagementSearchText.toLowerCase()) ||
        engagement.status?.toLowerCase().includes(engagementSearchText.toLowerCase())
    );

    // Engagement Card component
    const EngagementCard = ({ engagement }: { engagement: AuditEngagement }) => {
        return (
            <Card
                hoverable
                style={{ height: '100%' }}
                bodyStyle={{ padding: '16px' }}
                onClick={() => handleViewEngagement(engagement)}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 500, flex: 1, marginRight: '8px' }}>
                        {engagement.name}
                    </h4>
                    <Tag color={getStatusColor(engagement.status)}>{getStatusLabel(engagement.status)}</Tag>
                </div>

                {engagement.framework_name && (
                    <Tag color="blue" style={{ marginBottom: '8px' }}>{engagement.framework_name}</Tag>
                )}

                {engagement.assessment_name && (
                    <p style={{ margin: '4px 0', color: '#595959', fontSize: '13px' }}>
                        Assessment: {engagement.assessment_name}
                    </p>
                )}

                <div style={{ display: 'flex', gap: '12px', marginTop: '8px', color: '#8c8c8c', fontSize: '12px' }}>
                    {engagement.owner_name && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <UserOutlined /> {engagement.owner_name}
                        </span>
                    )}
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <TeamOutlined /> {engagement.active_invitation_count || 0} auditors
                    </span>
                </div>

                {(engagement.audit_period_start || engagement.audit_period_end) && (
                    <div style={{ marginTop: '8px', color: '#8c8c8c', fontSize: '12px' }}>
                        {engagement.audit_period_start ? dayjs(engagement.audit_period_start).format('MMM D, YYYY') : 'TBD'}
                        {' - '}
                        {engagement.audit_period_end ? dayjs(engagement.audit_period_end).format('MMM D, YYYY') : 'TBD'}
                    </div>
                )}
            </Card>
        );
    };

    return (
        <div className="page-parent">
            {contextHolder}
            <Sidebar
                selectedKeys={menuHighlighting.selectedKeys}
                openKeys={menuHighlighting.openKeys}
                onOpenChange={menuHighlighting.onOpenChange}
            />
            <div className="page-content">
                <InfoTitle
                    icon={<AuditOutlined />}
                    title="Audit Engagements"
                    infoContent={{
                        title: "Audit Engagement Workspace",
                        description: "Manage external audit engagements. Invite auditors to review compliance assessments, track findings, and manage sign-offs."
                    }}
                />

                {/* Filters and Actions */}
                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                    <Space wrap>
                        <Input
                            placeholder="Search engagements..."
                            prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                            value={engagementSearchText}
                            onChange={(e) => setEngagementSearchText(e.target.value)}
                            style={{ width: '200px' }}
                        />
                        <div style={{ display: 'flex', border: '1px solid #d9d9d9', borderRadius: '6px', overflow: 'hidden' }}>
                            <button
                                onClick={() => setEngagementViewMode('grid')}
                                style={{
                                    border: 'none',
                                    padding: '6px 12px',
                                    cursor: 'pointer',
                                    backgroundColor: engagementViewMode === 'grid' ? '#1890ff' : 'white',
                                    color: engagementViewMode === 'grid' ? 'white' : '#595959',
                                }}
                            >
                                <AppstoreOutlined />
                            </button>
                            <button
                                onClick={() => setEngagementViewMode('list')}
                                style={{
                                    border: 'none',
                                    borderLeft: '1px solid #d9d9d9',
                                    padding: '6px 12px',
                                    cursor: 'pointer',
                                    backgroundColor: engagementViewMode === 'list' ? '#1890ff' : 'white',
                                    color: engagementViewMode === 'list' ? 'white' : '#595959',
                                }}
                            >
                                <UnorderedListOutlined />
                            </button>
                        </div>
                        <Select
                            placeholder="Filter by status"
                            allowClear
                            style={{ width: 180 }}
                            value={statusFilter}
                            onChange={setStatusFilter}
                            options={[
                                { label: 'Draft', value: 'draft' },
                                { label: 'Planned', value: 'planned' },
                                { label: 'In Progress', value: 'in_progress' },
                                { label: 'Under Review', value: 'review' },
                                { label: 'Completed', value: 'completed' },
                                { label: 'Closed', value: 'closed' },
                            ]}
                        />
                        <Button
                            type={ownerOnlyFilter ? 'primary' : 'default'}
                            onClick={() => setOwnerOnlyFilter(!ownerOnlyFilter)}
                        >
                            My Engagements
                        </Button>
                    </Space>
                    {(current_user?.role_name === 'super_admin' || current_user?.role_name === 'org_admin') && (
                        <Button
                            type="primary"
                            icon={<PlusOutlined />}
                            onClick={handleCreateEngagement}
                        >
                            New Engagement
                        </Button>
                    )}
                </div>

                {/* Engagements Table/Cards */}
                {searchFilteredEngagements.length === 0 ? (
                    <Empty description="No engagements found" />
                ) : engagementViewMode === 'grid' ? (
                    <Row gutter={[16, 16]}>
                        {searchFilteredEngagements.map(engagement => (
                            <Col key={engagement.id} xs={24} sm={12} md={8} lg={6}>
                                <EngagementCard engagement={engagement} />
                            </Col>
                        ))}
                    </Row>
                ) : (
                    <Table
                        columns={columns}
                        dataSource={searchFilteredEngagements}
                        rowKey="id"
                        loading={loading}
                        pagination={{
                            total: totalCount,
                            showSizeChanger: true,
                            showTotal: (total) => `Total ${total} engagements`
                        }}
                    />
                )}

                {/* Create Engagement Modal */}
                <Modal
                    title="Create Audit Engagement"
                    open={showCreateModal}
                    onCancel={() => setShowCreateModal(false)}
                    footer={null}
                    width={600}
                >
                    <Form
                        form={createForm}
                        layout="vertical"
                        onFinish={onCreateSubmit}
                    >
                        <Form.Item
                            name="name"
                            label="Engagement Name"
                            rules={[{ required: true, message: 'Please enter a name' }]}
                        >
                            <Input placeholder="e.g., Q1 2024 ISO 27001 Audit" />
                        </Form.Item>

                        <Form.Item
                            name="assessment_id"
                            label="Assessment"
                            rules={[{ required: true, message: 'Please select an assessment' }]}
                        >
                            <Select
                                placeholder="Select assessment to audit"
                                showSearch
                                optionFilterProp="label"
                                options={assessments.map(a => ({
                                    label: `${a.name} (${a.framework_name || 'Unknown Framework'})`,
                                    value: a.id
                                }))}
                            />
                        </Form.Item>

                        <Form.Item
                            name="description"
                            label="Description"
                        >
                            <TextArea rows={3} placeholder="Brief description of the audit scope and objectives" />
                        </Form.Item>

                        <Form.Item
                            name="audit_period"
                            label="Audit Period"
                        >
                            <RangePicker style={{ width: '100%' }} />
                        </Form.Item>

                        <Form.Item
                            name="planned_dates"
                            label="Planned Dates"
                        >
                            <RangePicker style={{ width: '100%' }} />
                        </Form.Item>

                        <Form.Item>
                            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                                <Button onClick={() => setShowCreateModal(false)}>Cancel</Button>
                                <Button type="primary" htmlType="submit" loading={loading}>
                                    Create Engagement
                                </Button>
                            </Space>
                        </Form.Item>
                    </Form>
                </Modal>

                {/* Engagement Detail Modal */}
                <Modal
                    title={
                        <Space>
                            <AuditOutlined />
                            {selectedEngagement?.name}
                            <Tag color={getStatusColor(selectedEngagement?.status || 'draft')}>
                                {getStatusLabel(selectedEngagement?.status || 'draft')}
                            </Tag>
                        </Space>
                    }
                    open={showDetailModal}
                    onCancel={() => {
                        setShowDetailModal(false);
                        setSelectedEngagement(null);
                    }}
                    width={900}
                    footer={
                        <Space>
                            {selectedEngagement && getStatusTransitions(selectedEngagement.status).length > 0 && (
                                <Select
                                    placeholder="Change status"
                                    style={{ width: 180 }}
                                    onChange={handleStatusChange}
                                    options={getStatusTransitions(selectedEngagement.status).map(s => ({
                                        label: getStatusLabel(s),
                                        value: s
                                    }))}
                                />
                            )}
                            <Button onClick={() => setShowDetailModal(false)}>Close</Button>
                        </Space>
                    }
                >
                    {selectedEngagement && (
                        <Tabs
                            defaultActiveKey="details"
                            items={[
                                {
                                    key: 'details',
                                    label: 'Details',
                                    children: (
                                        <Descriptions column={2} bordered size="small">
                                            <Descriptions.Item label="Assessment">{selectedEngagement.assessment_name}</Descriptions.Item>
                                            <Descriptions.Item label="Framework">{selectedEngagement.framework_name}</Descriptions.Item>
                                            <Descriptions.Item label="Owner">{selectedEngagement.owner_name} ({selectedEngagement.owner_email})</Descriptions.Item>
                                            <Descriptions.Item label="Organization">{selectedEngagement.organisation_name}</Descriptions.Item>
                                            <Descriptions.Item label="Audit Period">
                                                {selectedEngagement.audit_period_start && selectedEngagement.audit_period_end
                                                    ? `${dayjs(selectedEngagement.audit_period_start).format('MMM D, YYYY')} - ${dayjs(selectedEngagement.audit_period_end).format('MMM D, YYYY')}`
                                                    : 'Not set'}
                                            </Descriptions.Item>
                                            <Descriptions.Item label="Planned Dates">
                                                {selectedEngagement.planned_start_date && selectedEngagement.planned_end_date
                                                    ? `${dayjs(selectedEngagement.planned_start_date).format('MMM D, YYYY')} - ${dayjs(selectedEngagement.planned_end_date).format('MMM D, YYYY')}`
                                                    : 'Not set'}
                                            </Descriptions.Item>
                                            <Descriptions.Item label="Actual Start">
                                                {selectedEngagement.actual_start_date
                                                    ? dayjs(selectedEngagement.actual_start_date).format('MMM D, YYYY')
                                                    : 'Not started'}
                                            </Descriptions.Item>
                                            <Descriptions.Item label="Actual End">
                                                {selectedEngagement.actual_end_date
                                                    ? dayjs(selectedEngagement.actual_end_date).format('MMM D, YYYY')
                                                    : 'Ongoing'}
                                            </Descriptions.Item>
                                            <Descriptions.Item label="Description" span={2}>
                                                {selectedEngagement.description || 'No description provided'}
                                            </Descriptions.Item>
                                        </Descriptions>
                                    )
                                },
                                {
                                    key: 'auditors',
                                    label: (
                                        <Space size={4}>
                                            <TeamOutlined />
                                            <span>Auditors</span>
                                            {invitations.filter(i => i.status === 'accepted').length > 0 && (
                                                <Tag color="green" style={{ marginLeft: 4 }}>
                                                    {invitations.filter(i => i.status === 'accepted').length} Active
                                                </Tag>
                                            )}
                                            {invitations.filter(i => i.status === 'pending').length > 0 && (
                                                <Tag color="orange" style={{ marginLeft: 4 }}>
                                                    {invitations.filter(i => i.status === 'pending').length} Pending
                                                </Tag>
                                            )}
                                        </Space>
                                    ),
                                    children: (
                                        <>
                                            <div style={{ marginBottom: 16 }}>
                                                <Button
                                                    type="primary"
                                                    icon={<UserAddOutlined />}
                                                    onClick={() => {
                                                        inviteForm.resetFields();
                                                        setShowInviteModal(true);
                                                    }}
                                                    disabled={selectedEngagement.status === 'closed'}
                                                >
                                                    Invite Auditor
                                                </Button>
                                            </div>
                                            {invitations.length > 0 ? (
                                                <Table
                                                    columns={invitationColumns}
                                                    dataSource={invitations}
                                                    rowKey="id"
                                                    pagination={false}
                                                    size="small"
                                                />
                                            ) : (
                                                <Empty description="No auditors invited yet" />
                                            )}
                                        </>
                                    )
                                },
                                {
                                    key: 'comments',
                                    label: (
                                        <Badge count={comments.length} size="small" offset={[8, 0]}>
                                            <span><CommentOutlined /> Comments</span>
                                        </Badge>
                                    ),
                                    children: (
                                        <>
                                            {comments.length > 0 ? (
                                                <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                                                    {comments.map((comment) => (
                                                        <div
                                                            key={comment.id}
                                                            style={{
                                                                padding: 12,
                                                                marginBottom: 12,
                                                                border: '1px solid #f0f0f0',
                                                                borderRadius: 8,
                                                                backgroundColor: '#fafafa'
                                                            }}
                                                        >
                                                            <Space style={{ justifyContent: 'space-between', width: '100%', marginBottom: 8 }}>
                                                                <Space>
                                                                    <span style={{
                                                                        width: 32,
                                                                        height: 32,
                                                                        borderRadius: '50%',
                                                                        backgroundColor: comment.authorType === 'auditor' ? '#0f386a' : '#52c41a',
                                                                        display: 'flex',
                                                                        alignItems: 'center',
                                                                        justifyContent: 'center',
                                                                        color: 'white'
                                                                    }}>
                                                                        <UserOutlined />
                                                                    </span>
                                                                    <div>
                                                                        <strong>{comment.authorName}</strong>
                                                                        <br />
                                                                        <span style={{ fontSize: 12, color: '#888' }}>
                                                                            {new Date(comment.createdAt).toLocaleString()}
                                                                        </span>
                                                                    </div>
                                                                </Space>
                                                                <Space>
                                                                    <Tag color={comment.authorType === 'auditor' ? 'blue' : 'green'}>
                                                                        {comment.authorType}
                                                                    </Tag>
                                                                    <Tag>{comment.commentType.replace('_', ' ')}</Tag>
                                                                    <Tag color={comment.status === 'open' ? 'orange' : 'green'}>
                                                                        {comment.status}
                                                                    </Tag>
                                                                </Space>
                                                            </Space>
                                                            <div style={{ padding: '8px 0 8px 40px', background: 'white', borderRadius: 4, marginTop: 8 }}>
                                                                {comment.content}
                                                            </div>
                                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8, paddingLeft: 40 }}>
                                                                <span style={{ fontSize: 12, color: '#888' }}>
                                                                    Target: {comment.targetType} ({comment.targetId.substring(0, 8)}...)
                                                                </span>
                                                                <Button
                                                                    type="primary"
                                                                    size="small"
                                                                    icon={<SendOutlined />}
                                                                    onClick={() => handleReplyClick(comment)}
                                                                >
                                                                    Reply
                                                                </Button>
                                                            </div>
                                                            {/* Show replies */}
                                                            {comment.replies && comment.replies.length > 0 && (
                                                                <div style={{ marginTop: 12, marginLeft: 40, borderLeft: '2px solid #e8e8e8', paddingLeft: 16 }}>
                                                                    {comment.replies.map((reply) => (
                                                                        <div
                                                                            key={reply.id}
                                                                            style={{
                                                                                padding: 10,
                                                                                marginBottom: 8,
                                                                                backgroundColor: 'white',
                                                                                borderRadius: 6,
                                                                                border: '1px solid #f0f0f0'
                                                                            }}
                                                                        >
                                                                            <Space style={{ marginBottom: 6 }}>
                                                                                <span style={{
                                                                                    width: 24,
                                                                                    height: 24,
                                                                                    borderRadius: '50%',
                                                                                    backgroundColor: reply.authorType === 'auditor' ? '#0f386a' : '#52c41a',
                                                                                    display: 'flex',
                                                                                    alignItems: 'center',
                                                                                    justifyContent: 'center',
                                                                                    color: 'white',
                                                                                    fontSize: 12
                                                                                }}>
                                                                                    <UserOutlined />
                                                                                </span>
                                                                                <strong style={{ fontSize: 13 }}>{reply.authorName}</strong>
                                                                                <Tag color={reply.authorType === 'auditor' ? 'blue' : 'green'} style={{ fontSize: 11 }}>
                                                                                    {reply.authorType}
                                                                                </Tag>
                                                                                <span style={{ fontSize: 11, color: '#888' }}>
                                                                                    {new Date(reply.createdAt).toLocaleString()}
                                                                                </span>
                                                                            </Space>
                                                                            <div style={{ fontSize: 13, color: '#333', paddingLeft: 32 }}>
                                                                                {reply.content}
                                                                            </div>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <Empty description="No comments yet" />
                                            )}
                                        </>
                                    )
                                },
                                {
                                    key: 'notifications',
                                    label: (
                                        <Badge count={notifications.filter(n => !n.isRead).length} size="small" offset={[8, 0]}>
                                            <span><BellOutlined /> Notifications</span>
                                        </Badge>
                                    ),
                                    children: (
                                        <>
                                            {notifications.length > 0 && (
                                                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
                                                    <Button
                                                        type="link"
                                                        icon={<CheckOutlined />}
                                                        onClick={() => markAsRead()}
                                                        disabled={notifications.filter(n => !n.isRead).length === 0}
                                                    >
                                                        Mark all as read
                                                    </Button>
                                                </div>
                                            )}
                                            {notifications.length > 0 ? (
                                                <List
                                                    dataSource={notifications}
                                                    renderItem={(item: any) => (
                                                        <List.Item
                                                            style={{
                                                                padding: '12px 16px',
                                                                marginBottom: 8,
                                                                backgroundColor: item.isRead ? '#fafafa' : 'rgba(24, 144, 255, 0.05)',
                                                                borderLeft: item.isRead ? '3px solid transparent' : '3px solid #1890ff',
                                                                borderRadius: 4,
                                                                border: '1px solid #f0f0f0'
                                                            }}
                                                            actions={[
                                                                !item.isRead && (
                                                                    <Button
                                                                        type="link"
                                                                        size="small"
                                                                        onClick={() => markAsRead([item.id])}
                                                                    >
                                                                        Mark read
                                                                    </Button>
                                                                ),
                                                                <Popconfirm
                                                                    title="Delete this notification?"
                                                                    onConfirm={() => deleteNotification(item.id)}
                                                                    okText="Delete"
                                                                    cancelText="Cancel"
                                                                    okButtonProps={{ danger: true }}
                                                                >
                                                                    <Button type="link" size="small" danger>
                                                                        Delete
                                                                    </Button>
                                                                </Popconfirm>
                                                            ].filter(Boolean)}
                                                        >
                                                            <List.Item.Meta
                                                                title={
                                                                    <Space>
                                                                        <span style={{ fontWeight: item.isRead ? 400 : 600 }}>
                                                                            {item.title}
                                                                        </span>
                                                                        <Tag color={getNotificationTypeColor(item.notificationType)}>
                                                                            {getNotificationTypeLabel(item.notificationType)}
                                                                        </Tag>
                                                                    </Space>
                                                                }
                                                                description={
                                                                    <div>
                                                                        <div style={{ marginBottom: 4 }}>
                                                                            {item.message}
                                                                        </div>
                                                                        <div style={{ fontSize: 12, color: '#888' }}>
                                                                            {item.senderName && (
                                                                                <span style={{ marginRight: 12 }}>
                                                                                    From: {item.senderName}
                                                                                </span>
                                                                            )}
                                                                            {new Date(item.createdAt).toLocaleString()}
                                                                        </div>
                                                                    </div>
                                                                }
                                                            />
                                                        </List.Item>
                                                    )}
                                                />
                                            ) : (
                                                <Empty description="No notifications for this engagement" />
                                            )}
                                        </>
                                    )
                                }
                            ]}
                        />
                    )}
                </Modal>

                {/* Invite Auditor Modal */}
                <Modal
                    title={
                        <Space>
                            <UserAddOutlined />
                            Invite Auditor
                        </Space>
                    }
                    open={showInviteModal}
                    onCancel={() => setShowInviteModal(false)}
                    footer={null}
                    width={600}
                >
                    <Form
                        form={inviteForm}
                        layout="vertical"
                        onFinish={onInviteSubmit}
                        initialValues={{
                            mfa_enabled: false,
                            watermark_downloads: true,
                            download_restricted: false
                        }}
                    >
                        <Form.Item
                            name="email"
                            label="Email Address"
                            rules={[
                                { required: true, message: 'Please enter email' },
                                { type: 'email', message: 'Please enter a valid email' }
                            ]}
                        >
                            <Input placeholder="auditor@example.com" />
                        </Form.Item>

                        <Form.Item
                            name="name"
                            label="Auditor Name"
                        >
                            <Input placeholder="Full name" />
                        </Form.Item>

                        <Form.Item
                            name="company"
                            label="Company"
                        >
                            <Input placeholder="Audit firm name" />
                        </Form.Item>

                        <Form.Item
                            name="auditor_role_id"
                            label="Role"
                            rules={[{ required: true, message: 'Please select a role' }]}
                        >
                            <Select
                                placeholder="Select auditor role"
                                options={auditorRoles.map(role => ({
                                    label: (
                                        <Space>
                                            <span>{role.role_name.replace('_', ' ').toUpperCase()}</span>
                                            {role.can_sign_off && <Tag color="blue" style={{ marginLeft: 8 }}>Can Sign Off</Tag>}
                                        </Space>
                                    ),
                                    value: role.id
                                }))}
                            />
                        </Form.Item>

                        <Form.Item
                            name="access_window"
                            label="Access Window"
                            help="Optional: Restrict when the auditor can access the engagement"
                        >
                            <RangePicker style={{ width: '100%' }} />
                        </Form.Item>

                        <Form.Item
                            name="mfa_enabled"
                            valuePropName="checked"
                            label="Security Settings"
                        >
                            <Checkbox>Require Multi-Factor Authentication (MFA)</Checkbox>
                        </Form.Item>

                        <Form.Item
                            name="watermark_downloads"
                            valuePropName="checked"
                        >
                            <Checkbox>Watermark downloaded files</Checkbox>
                        </Form.Item>

                        <Form.Item>
                            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                                <Button onClick={() => setShowInviteModal(false)}>Cancel</Button>
                                <Button type="primary" htmlType="submit" loading={loading} icon={<MailOutlined />}>
                                    Send Invitation
                                </Button>
                            </Space>
                        </Form.Item>
                    </Form>
                </Modal>

                {/* Reply to Comment Modal */}
                <Modal
                    title={
                        <Space>
                            <SendOutlined />
                            Reply to Comment
                        </Space>
                    }
                    open={showReplyModal}
                    onCancel={() => {
                        setShowReplyModal(false);
                        setReplyToComment(null);
                        setReplyText('');
                    }}
                    onOk={handleReplySubmit}
                    okText="Send Reply"
                    okButtonProps={{ disabled: !replyText.trim(), icon: <SendOutlined /> }}
                    width={600}
                >
                    {replyToComment && (
                        <div>
                            <div style={{
                                background: '#f5f5f5',
                                padding: 12,
                                borderRadius: 8,
                                marginBottom: 16,
                                borderLeft: '3px solid #0f386a'
                            }}>
                                <Space style={{ marginBottom: 8 }}>
                                    <Tag color={replyToComment.authorType === 'auditor' ? 'blue' : 'green'}>
                                        {replyToComment.authorType}
                                    </Tag>
                                    <strong>{replyToComment.authorName}</strong>
                                    <span style={{ color: '#888', fontSize: 12 }}>
                                        {new Date(replyToComment.createdAt).toLocaleString()}
                                    </span>
                                </Space>
                                <p style={{ margin: 0, color: '#555' }}>{replyToComment.content}</p>
                            </div>
                            <Input.TextArea
                                rows={4}
                                placeholder="Type your reply..."
                                value={replyText}
                                onChange={(e) => setReplyText(e.target.value)}
                            />
                        </div>
                    )}
                </Modal>
            </div>
        </div>
    );
};

export default AuditEngagementsPage;
