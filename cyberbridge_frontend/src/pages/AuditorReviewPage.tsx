// src/pages/AuditorReviewPage.tsx
import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import {
    Layout,
    Card,
    Tabs,
    Table,
    Tag,
    Button,
    Space,
    Typography,
    Descriptions,
    Progress,
    Statistic,
    Row,
    Col,
    Badge,
    Empty,
    Spin,
    Alert,
    Modal,
    Input,
    Tooltip,
    Divider,
    Avatar
} from 'antd';
import {
    FileTextOutlined,
    SafetyOutlined,
    FolderOpenOutlined,
    CheckSquareOutlined,
    LogoutOutlined,
    EyeOutlined,
    CommentOutlined,
    FileSearchOutlined,
    UserOutlined,
    CalendarOutlined,
    BankOutlined,
    ReloadOutlined,
    DownloadOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import useAuditorStore, {
    ReviewControl,
    ReviewEvidence,
    ReviewPolicy,
    ReviewObjective,
    ReviewQueueItem,
    AuditComment
} from '../store/useAuditorStore';
import cyberbridgeLogo from '../assets/cyberbridge_logo.svg';

const { Header, Content, Sider } = Layout;
const { Title, Text, Paragraph } = Typography;
const { Search } = Input;

export default function AuditorReviewPage() {
    const [, setLocation] = useLocation();
    const {
        isAuthenticated,
        session,
        engagement,
        controls,
        evidence,
        policies,
        objectives,
        reviewQueue,
        comments,
        isLoading,
        error,
        loadEngagement,
        loadControls,
        loadEvidence,
        loadPolicies,
        loadObjectives,
        loadReviewQueue,
        loadComments,
        createComment,
        getEvidencePreviewUrl,
        logout,
        clearError
    } = useAuditorStore();

    const [activeTab, setActiveTab] = useState('overview');
    const [previewModalVisible, setPreviewModalVisible] = useState(false);
    const [previewEvidence, setPreviewEvidence] = useState<ReviewEvidence | null>(null);
    const [searchText, setSearchText] = useState('');
    const [collapsed, setCollapsed] = useState(false);
    const [controlDetailModal, setControlDetailModal] = useState(false);
    const [selectedControl, setSelectedControl] = useState<ReviewControl | null>(null);
    const [commentModal, setCommentModal] = useState(false);
    const [commentText, setCommentText] = useState('');
    const [viewCommentsModal, setViewCommentsModal] = useState(false);

    // Redirect if not authenticated
    useEffect(() => {
        if (!isAuthenticated) {
            setLocation('/auditor/login');
        }
    }, [isAuthenticated, setLocation]);

    // Load data on mount
    useEffect(() => {
        if (isAuthenticated) {
            loadEngagement();
            loadControls();
            loadEvidence();
            loadPolicies();
            loadObjectives();
            loadReviewQueue();
            loadComments();
        }
    }, [isAuthenticated]);

    const handleLogout = () => {
        Modal.confirm({
            title: 'Confirm Logout',
            content: 'Are you sure you want to log out of the audit portal?',
            okText: 'Logout',
            okType: 'danger',
            onOk: () => {
                logout();
                setLocation('/auditor/login');
            }
        });
    };

    const handleRefresh = () => {
        loadEngagement();
        loadControls();
        loadEvidence();
        loadPolicies();
        loadObjectives();
        loadReviewQueue();
        loadComments();
    };

    const handlePreviewEvidence = (ev: ReviewEvidence) => {
        setPreviewEvidence(ev);
        setPreviewModalVisible(true);
    };

    const handleViewControlDetails = (control: ReviewControl) => {
        setSelectedControl(control);
        // Load comments for this specific control
        loadComments('answer', control.answerId || control.id);
        setControlDetailModal(true);
    };

    const handleViewAllComments = () => {
        loadComments();
        setViewCommentsModal(true);
    };

    // Get comments for the selected control
    const controlComments = selectedControl
        ? comments.filter(c => c.targetId === (selectedControl.answerId || selectedControl.id))
        : [];

    const handleAddComment = (control: ReviewControl) => {
        setSelectedControl(control);
        setCommentText('');
        setCommentModal(true);
    };

    const handleSubmitComment = async () => {
        if (!selectedControl || !commentText.trim()) return;

        const result = await createComment(
            'answer',
            selectedControl.answerId || selectedControl.id,
            commentText.trim(),
            'observation'
        );

        if (result.success) {
            Modal.success({
                title: 'Comment Submitted',
                content: 'Your comment has been submitted successfully.',
            });
            setCommentModal(false);
            setCommentText('');
            setSelectedControl(null);
            // Reload controls to update comment counts
            loadControls();
        } else {
            Modal.error({
                title: 'Failed to Submit Comment',
                content: result.error || 'An error occurred while submitting your comment.',
            });
        }
    };

    const getStatusColor = (status: string) => {
        const colors: Record<string, string> = {
            'not_reviewed': 'default',
            'in_progress': 'processing',
            'reviewed': 'success',
            'signed_off': 'green',
            'compliant': 'green',
            'non_compliant': 'red',
            'partial': 'orange',
            'pending': 'gold',
            'approved': 'green',
            'active': 'green',
            'draft': 'default'
        };
        return colors[status?.toLowerCase()] || 'default';
    };

    const getReviewStatusColor = (status: string) => {
        const colors: Record<string, string> = {
            'not_reviewed': '#d9d9d9',
            'in_progress': '#1890ff',
            'reviewed': '#52c41a',
            'signed_off': '#389e0d'
        };
        return colors[status] || '#d9d9d9';
    };

    // Calculate review progress
    const reviewedCount = controls.filter(c => c.reviewStatus === 'reviewed' || c.reviewStatus === 'signed_off').length;
    const totalControls = controls.length;
    const progressPercent = totalControls > 0 ? Math.round((reviewedCount / totalControls) * 100) : 0;

    // Control columns
    const controlColumns: ColumnsType<ReviewControl> = [
        {
            title: 'Control',
            dataIndex: 'questionText',
            key: 'questionText',
            width: '40%',
            render: (text, record) => (
                <Space direction="vertical" size={0}>
                    <Text strong>{text}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>{record.chapterName}</Text>
                </Space>
            ),
            filteredValue: searchText ? [searchText] : null,
            onFilter: (value, record) =>
                record.questionText.toLowerCase().includes(String(value).toLowerCase()) ||
                record.chapterName.toLowerCase().includes(String(value).toLowerCase())
        },
        {
            title: 'Status',
            dataIndex: 'answerStatus',
            key: 'answerStatus',
            width: '15%',
            render: (status) => status ? <Tag color={getStatusColor(status)}>{status}</Tag> : <Tag>No Answer</Tag>
        },
        {
            title: 'Evidence',
            dataIndex: 'evidenceCount',
            key: 'evidenceCount',
            width: '10%',
            align: 'center',
            render: (count) => (
                <Badge count={count} showZero style={{ backgroundColor: count > 0 ? '#52c41a' : '#d9d9d9' }} />
            )
        },
        {
            title: 'Comments',
            dataIndex: 'commentCount',
            key: 'commentCount',
            width: '10%',
            align: 'center',
            render: (count) => (
                <Badge count={count} showZero style={{ backgroundColor: count > 0 ? '#1890ff' : '#d9d9d9' }} />
            )
        },
        {
            title: 'Review Status',
            dataIndex: 'reviewStatus',
            key: 'reviewStatus',
            width: '15%',
            render: (status) => (
                <Tag color={getStatusColor(status)} style={{ textTransform: 'capitalize' }}>
                    {status?.replace('_', ' ') || 'Not Reviewed'}
                </Tag>
            )
        },
        {
            title: 'Actions',
            key: 'actions',
            width: '10%',
            render: (_, record) => (
                <Space>
                    <Tooltip title="View Details">
                        <Button
                            type="text"
                            icon={<EyeOutlined />}
                            size="small"
                            onClick={() => handleViewControlDetails(record)}
                        />
                    </Tooltip>
                    {session?.canComment && (
                        <Tooltip title="Add Comment">
                            <Button
                                type="text"
                                icon={<CommentOutlined />}
                                size="small"
                                onClick={() => handleAddComment(record)}
                            />
                        </Tooltip>
                    )}
                </Space>
            )
        }
    ];

    // Evidence columns
    const evidenceColumns: ColumnsType<ReviewEvidence> = [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            render: (text, record) => (
                <Space>
                    <FileTextOutlined style={{ color: '#0f386a' }} />
                    <Space direction="vertical" size={0}>
                        <Text strong>{text}</Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>{record.fileType}</Text>
                    </Space>
                </Space>
            )
        },
        {
            title: 'Related Control',
            dataIndex: 'questionText',
            key: 'questionText',
            width: '30%',
            ellipsis: true
        },
        {
            title: 'Size',
            dataIndex: 'fileSize',
            key: 'fileSize',
            width: '10%',
            render: (size) => {
                if (size < 1024) return `${size} B`;
                if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
                return `${(size / (1024 * 1024)).toFixed(1)} MB`;
            }
        },
        {
            title: 'Uploaded',
            dataIndex: 'uploadedAt',
            key: 'uploadedAt',
            width: '15%',
            render: (date) => date ? new Date(date).toLocaleDateString() : '-'
        },
        {
            title: 'Actions',
            key: 'actions',
            width: '15%',
            render: (_, record) => (
                <Space>
                    <Button
                        type="primary"
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => handlePreviewEvidence(record)}
                    >
                        Preview
                    </Button>
                    {!session?.downloadRestricted && (
                        <Button
                            size="small"
                            icon={<DownloadOutlined />}
                        >
                            Download
                        </Button>
                    )}
                </Space>
            )
        }
    ];

    // Policy columns
    const policyColumns: ColumnsType<ReviewPolicy> = [
        {
            title: 'Policy Name',
            dataIndex: 'name',
            key: 'name',
            render: (text) => <Text strong>{text}</Text>
        },
        {
            title: 'Version',
            dataIndex: 'version',
            key: 'version',
            width: '10%'
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: '15%',
            render: (status) => <Tag color={getStatusColor(status)}>{status}</Tag>
        },
        {
            title: 'Last Review',
            dataIndex: 'reviewDate',
            key: 'reviewDate',
            width: '15%',
            render: (date) => date ? new Date(date).toLocaleDateString() : '-'
        },
        {
            title: 'Actions',
            key: 'actions',
            width: '15%',
            render: (_, record) => (
                <Space>
                    {record.filePath && (
                        <Button type="primary" size="small" icon={<EyeOutlined />}>View</Button>
                    )}
                </Space>
            )
        }
    ];

    // Objective columns
    const objectiveColumns: ColumnsType<ReviewObjective> = [
        {
            title: 'Objective',
            dataIndex: 'name',
            key: 'name',
            render: (text, record) => (
                <Space direction="vertical" size={0}>
                    <Text strong>{text}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>{record.chapterName}</Text>
                </Space>
            )
        },
        {
            title: 'Compliance Status',
            dataIndex: 'complianceStatus',
            key: 'complianceStatus',
            width: '20%',
            render: (status) => status ? <Tag color={getStatusColor(status)}>{status}</Tag> : <Tag>Not Assessed</Tag>
        },
        {
            title: 'Linked Policies',
            dataIndex: 'linkedPoliciesCount',
            key: 'linkedPoliciesCount',
            width: '15%',
            align: 'center',
            render: (count) => <Badge count={count} showZero style={{ backgroundColor: '#0f386a' }} />
        }
    ];

    // Review queue columns
    const queueColumns: ColumnsType<ReviewQueueItem> = [
        {
            title: 'Item',
            dataIndex: 'name',
            key: 'name',
            render: (text, record) => (
                <Space>
                    {record.type === 'control' && <SafetyOutlined style={{ color: '#0f386a' }} />}
                    {record.type === 'evidence' && <FileTextOutlined style={{ color: '#52c41a' }} />}
                    {record.type === 'policy' && <FolderOpenOutlined style={{ color: '#fa8c16' }} />}
                    {record.type === 'objective' && <CheckSquareOutlined style={{ color: '#722ed1' }} />}
                    <Text>{text}</Text>
                </Space>
            )
        },
        {
            title: 'Type',
            dataIndex: 'type',
            key: 'type',
            width: '15%',
            render: (type) => <Tag style={{ textTransform: 'capitalize' }}>{type}</Tag>
        },
        {
            title: 'Priority',
            dataIndex: 'priority',
            key: 'priority',
            width: '10%',
            render: (priority) => {
                const colors: Record<string, string> = { high: 'red', medium: 'orange', low: 'green' };
                return <Tag color={colors[priority]}>{priority}</Tag>;
            }
        },
        {
            title: 'Due Date',
            dataIndex: 'dueDate',
            key: 'dueDate',
            width: '15%',
            render: (date) => date ? new Date(date).toLocaleDateString() : '-'
        }
    ];

    if (!isAuthenticated) {
        return null;
    }

    return (
        <Layout style={{ minHeight: '100vh' }}>
            {/* Header */}
            <Header style={{
                background: 'linear-gradient(135deg, #1a365d 0%, #2d4a6f 100%)',
                padding: '0 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <img src={cyberbridgeLogo} alt="CyberBridge" style={{ height: 28, filter: 'brightness(0) invert(1)', verticalAlign: 'middle' }} />
                    <Divider type="vertical" style={{ backgroundColor: 'rgba(255,255,255,0.3)', height: 24, margin: 0 }} />
                    <Text style={{ color: 'white', fontSize: 16, lineHeight: '28px', fontWeight: 500 }}>Audit Review Portal</Text>
                </div>
                <Space>
                    <Space style={{ color: 'white', marginRight: 24 }}>
                        <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#0f386a' }} />
                        <Space direction="vertical" size={0}>
                            <Text style={{ color: 'white', fontWeight: 500 }}>{session?.roleName || 'Auditor'}</Text>
                            <Text style={{ color: 'rgba(255,255,255,0.7)', fontSize: 12 }}>{engagement?.engagementName}</Text>
                        </Space>
                    </Space>
                    <Button type="text" icon={<ReloadOutlined />} onClick={handleRefresh} style={{ color: 'white' }}>
                        Refresh
                    </Button>
                    <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout} style={{ color: 'white' }}>
                        Logout
                    </Button>
                </Space>
            </Header>

            <Layout>
                {/* Sidebar with quick stats */}
                <Sider
                    width={280}
                    collapsible
                    collapsed={collapsed}
                    onCollapse={setCollapsed}
                    style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}
                >
                    {!collapsed && (
                        <div style={{ padding: 16 }}>
                            <Title level={5} style={{ marginBottom: 16 }}>Review Progress</Title>
                            <Progress
                                percent={progressPercent}
                                strokeColor="#0f386a"
                                format={(percent) => `${reviewedCount}/${totalControls}`}
                            />

                            <Divider />

                            <Row gutter={[16, 16]}>
                                <Col span={12}>
                                    <Statistic
                                        title="Controls"
                                        value={controls.length}
                                        prefix={<SafetyOutlined />}
                                        valueStyle={{ color: '#0f386a', fontSize: 20 }}
                                    />
                                </Col>
                                <Col span={12}>
                                    <Statistic
                                        title="Evidence"
                                        value={evidence.length}
                                        prefix={<FileTextOutlined />}
                                        valueStyle={{ color: '#52c41a', fontSize: 20 }}
                                    />
                                </Col>
                                <Col span={12}>
                                    <Statistic
                                        title="Policies"
                                        value={policies.length}
                                        prefix={<FolderOpenOutlined />}
                                        valueStyle={{ color: '#fa8c16', fontSize: 20 }}
                                    />
                                </Col>
                                <Col span={12}>
                                    <Statistic
                                        title="Objectives"
                                        value={objectives.length}
                                        prefix={<CheckSquareOutlined />}
                                        valueStyle={{ color: '#722ed1', fontSize: 20 }}
                                    />
                                </Col>
                            </Row>

                            <Divider />

                            <Title level={5} style={{ marginBottom: 16 }}>Comments</Title>
                            <Button
                                type="default"
                                icon={<CommentOutlined />}
                                onClick={handleViewAllComments}
                                style={{ width: '100%', marginBottom: 8 }}
                            >
                                View All Comments
                                <Badge count={comments.length} style={{ marginLeft: 8 }} />
                            </Button>

                            <Divider />

                            <Title level={5} style={{ marginBottom: 16 }}>Your Permissions</Title>
                            <Space direction="vertical" size={8} style={{ width: '100%' }}>
                                <Tag color={session?.canComment ? 'green' : 'default'}>
                                    {session?.canComment ? '✓' : '✗'} Add Comments
                                </Tag>
                                <Tag color={session?.canRequestEvidence ? 'green' : 'default'}>
                                    {session?.canRequestEvidence ? '✓' : '✗'} Request Evidence
                                </Tag>
                                <Tag color={session?.canAddFindings ? 'green' : 'default'}>
                                    {session?.canAddFindings ? '✓' : '✗'} Add Findings
                                </Tag>
                                <Tag color={session?.canSignOff ? 'green' : 'default'}>
                                    {session?.canSignOff ? '✓' : '✗'} Sign Off
                                </Tag>
                            </Space>
                        </div>
                    )}
                </Sider>

                {/* Main content */}
                <Content style={{ padding: 24, background: '#f5f5f5' }}>
                    {error && (
                        <Alert
                            message="Error"
                            description={error}
                            type="error"
                            showIcon
                            closable
                            onClose={clearError}
                            style={{ marginBottom: 16 }}
                        />
                    )}

                    <Tabs
                        activeKey={activeTab}
                        onChange={setActiveTab}
                        size="large"
                        items={[
                            {
                                key: 'overview',
                                label: <span><FileSearchOutlined /> Overview</span>,
                                children: engagement ? (
                                    <Row gutter={[16, 16]}>
                                        <Col span={24}>
                                            <Card title="Engagement Details">
                                                <Descriptions column={{ xs: 1, sm: 2, md: 3 }}>
                                                    <Descriptions.Item label="Engagement Name">
                                                        <Text strong>{engagement.name}</Text>
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Organisation">
                                                        <Space>
                                                            <BankOutlined />
                                                            {engagement.organisationName || '-'}
                                                        </Space>
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Status">
                                                        <Tag color={getStatusColor(engagement.status)}>
                                                            {engagement.status?.replace('_', ' ').toUpperCase()}
                                                        </Tag>
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Framework">
                                                        {engagement.frameworkName || '-'}
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Assessment">
                                                        {engagement.assessmentName || '-'}
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Audit Period">
                                                        <Space>
                                                            <CalendarOutlined />
                                                            {engagement.auditPeriodStart && engagement.auditPeriodEnd ? (
                                                                `${new Date(engagement.auditPeriodStart).toLocaleDateString()} - ${new Date(engagement.auditPeriodEnd).toLocaleDateString()}`
                                                            ) : '-'}
                                                        </Space>
                                                    </Descriptions.Item>
                                                </Descriptions>
                                                {engagement.description && (
                                                    <>
                                                        <Divider />
                                                        <Paragraph>{engagement.description}</Paragraph>
                                                    </>
                                                )}
                                            </Card>
                                        </Col>

                                        <Col xs={24} lg={12}>
                                            <Card title="In-Scope Summary" style={{ height: '100%' }}>
                                                <Row gutter={16}>
                                                    <Col span={8}>
                                                        <Statistic
                                                            title="Controls"
                                                            value={engagement.inScopeControls?.length || 0}
                                                            prefix={<SafetyOutlined />}
                                                        />
                                                    </Col>
                                                    <Col span={8}>
                                                        <Statistic
                                                            title="Policies"
                                                            value={engagement.inScopePolicies?.length || 0}
                                                            prefix={<FolderOpenOutlined />}
                                                        />
                                                    </Col>
                                                    <Col span={8}>
                                                        <Statistic
                                                            title="Chapters"
                                                            value={engagement.inScopeChapters?.length || 0}
                                                            prefix={<FileTextOutlined />}
                                                        />
                                                    </Col>
                                                </Row>
                                            </Card>
                                        </Col>

                                        <Col xs={24} lg={12}>
                                            <Card title="Review Queue" style={{ height: '100%' }}>
                                                {reviewQueue.length > 0 ? (
                                                    <Table
                                                        dataSource={reviewQueue.slice(0, 5)}
                                                        columns={queueColumns}
                                                        rowKey="id"
                                                        pagination={false}
                                                        size="small"
                                                    />
                                                ) : (
                                                    <Empty description="No items in review queue" />
                                                )}
                                            </Card>
                                        </Col>
                                    </Row>
                                ) : (
                                    <Spin size="large" />
                                )
                            },
                            {
                                key: 'controls',
                                label: <span><SafetyOutlined /> Controls ({controls.length})</span>,
                                children: (
                                    <Card>
                                        <Space style={{ marginBottom: 16 }}>
                                            <Search
                                                placeholder="Search controls..."
                                                allowClear
                                                style={{ width: 300 }}
                                                onChange={(e) => setSearchText(e.target.value)}
                                            />
                                        </Space>
                                        <Table
                                            dataSource={controls}
                                            columns={controlColumns}
                                            rowKey="id"
                                            loading={isLoading}
                                            pagination={{ pageSize: 20, showSizeChanger: true }}
                                        />
                                    </Card>
                                )
                            },
                            {
                                key: 'evidence',
                                label: <span><FileTextOutlined /> Evidence ({evidence.length})</span>,
                                children: (
                                    <Card>
                                        <Table
                                            dataSource={evidence}
                                            columns={evidenceColumns}
                                            rowKey="id"
                                            loading={isLoading}
                                            pagination={{ pageSize: 20, showSizeChanger: true }}
                                        />
                                    </Card>
                                )
                            },
                            {
                                key: 'policies',
                                label: <span><FolderOpenOutlined /> Policies ({policies.length})</span>,
                                children: (
                                    <Card>
                                        <Table
                                            dataSource={policies}
                                            columns={policyColumns}
                                            rowKey="id"
                                            loading={isLoading}
                                            pagination={{ pageSize: 20, showSizeChanger: true }}
                                        />
                                    </Card>
                                )
                            },
                            {
                                key: 'objectives',
                                label: <span><CheckSquareOutlined /> Objectives ({objectives.length})</span>,
                                children: (
                                    <Card>
                                        <Table
                                            dataSource={objectives}
                                            columns={objectiveColumns}
                                            rowKey="id"
                                            loading={isLoading}
                                            pagination={{ pageSize: 20, showSizeChanger: true }}
                                        />
                                    </Card>
                                )
                            }
                        ]}
                    />
                </Content>
            </Layout>

            {/* Evidence Preview Modal */}
            <Modal
                title={previewEvidence?.name || 'Evidence Preview'}
                open={previewModalVisible}
                onCancel={() => setPreviewModalVisible(false)}
                footer={[
                    <Button key="close" onClick={() => setPreviewModalVisible(false)}>
                        Close
                    </Button>,
                    !session?.downloadRestricted && (
                        <Button key="download" type="primary" icon={<DownloadOutlined />}>
                            Download
                        </Button>
                    )
                ]}
                width={800}
            >
                {previewEvidence && (
                    <div style={{ textAlign: 'center' }}>
                        <Descriptions column={2} style={{ marginBottom: 16 }}>
                            <Descriptions.Item label="File Type">{previewEvidence.fileType}</Descriptions.Item>
                            <Descriptions.Item label="Size">
                                {previewEvidence.fileSize < 1024 * 1024
                                    ? `${(previewEvidence.fileSize / 1024).toFixed(1)} KB`
                                    : `${(previewEvidence.fileSize / (1024 * 1024)).toFixed(1)} MB`
                                }
                            </Descriptions.Item>
                            <Descriptions.Item label="Related Control" span={2}>
                                {previewEvidence.questionText}
                            </Descriptions.Item>
                        </Descriptions>
                        {previewEvidence.fileType?.includes('image') ? (
                            <img
                                src={getEvidencePreviewUrl(previewEvidence.id)}
                                alt={previewEvidence.name}
                                style={{ maxWidth: '100%', maxHeight: 500 }}
                            />
                        ) : previewEvidence.fileType?.includes('pdf') ? (
                            <iframe
                                src={getEvidencePreviewUrl(previewEvidence.id)}
                                style={{ width: '100%', height: 500, border: 'none' }}
                                title="PDF Preview"
                            />
                        ) : (
                            <Empty description="Preview not available for this file type" />
                        )}
                    </div>
                )}
            </Modal>

            {/* Control Detail Modal */}
            <Modal
                title="Control Details"
                open={controlDetailModal}
                onCancel={() => {
                    setControlDetailModal(false);
                    setSelectedControl(null);
                }}
                footer={[
                    session?.canComment && (
                        <Button key="add-comment" type="primary" icon={<CommentOutlined />} onClick={() => {
                            setControlDetailModal(false);
                            if (selectedControl) handleAddComment(selectedControl);
                        }}>
                            Add Comment
                        </Button>
                    ),
                    <Button key="close" onClick={() => {
                        setControlDetailModal(false);
                        setSelectedControl(null);
                    }}>
                        Close
                    </Button>
                ]}
                width={800}
            >
                {selectedControl && (
                    <div>
                        <Descriptions column={1} bordered size="small">
                            <Descriptions.Item label="Control Question">
                                <Text strong>{selectedControl.questionText}</Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="Chapter">
                                {selectedControl.chapterName}
                            </Descriptions.Item>
                            <Descriptions.Item label="Answer Status">
                                <Tag color={getStatusColor(selectedControl.answerStatus || '')}>
                                    {selectedControl.answerStatus || 'Not Answered'}
                                </Tag>
                            </Descriptions.Item>
                            <Descriptions.Item label="Review Status">
                                <Tag color={getStatusColor(selectedControl.reviewStatus)}>
                                    {selectedControl.reviewStatus?.replace('_', ' ') || 'Not Reviewed'}
                                </Tag>
                            </Descriptions.Item>
                            <Descriptions.Item label="Evidence Count">
                                <Badge count={selectedControl.evidenceCount} showZero style={{ backgroundColor: selectedControl.evidenceCount > 0 ? '#52c41a' : '#d9d9d9' }} />
                            </Descriptions.Item>
                            {selectedControl.answerNotes && (
                                <Descriptions.Item label="Notes">
                                    <Paragraph>{selectedControl.answerNotes}</Paragraph>
                                </Descriptions.Item>
                            )}
                        </Descriptions>

                        {/* Comments Section */}
                        <Divider orientation="left">
                            <Space>
                                <CommentOutlined />
                                Comments ({controlComments.length})
                            </Space>
                        </Divider>
                        {controlComments.length > 0 ? (
                            <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                                {controlComments.map((comment) => (
                                    <div key={comment.id}>
                                        <Card
                                            size="small"
                                            style={{ marginBottom: 8 }}
                                            styles={{ body: { padding: 12 } }}
                                        >
                                            <Space direction="vertical" size={4} style={{ width: '100%' }}>
                                                <Space>
                                                    <Avatar
                                                        size="small"
                                                        icon={<UserOutlined />}
                                                        style={{ backgroundColor: comment.authorType === 'auditor' ? '#0f386a' : '#52c41a' }}
                                                    />
                                                    <Text strong>{comment.authorName}</Text>
                                                    <Tag color={comment.authorType === 'auditor' ? 'blue' : 'green'} style={{ fontSize: 10 }}>
                                                        {comment.authorType}
                                                    </Tag>
                                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                                        {new Date(comment.createdAt).toLocaleString()}
                                                    </Text>
                                                </Space>
                                                <Paragraph style={{ margin: 0, marginLeft: 32 }}>
                                                    {comment.content}
                                                </Paragraph>
                                                <Space style={{ marginLeft: 32 }}>
                                                    <Tag>{comment.commentType.replace('_', ' ')}</Tag>
                                                    <Tag color={comment.status === 'open' ? 'orange' : 'green'}>{comment.status}</Tag>
                                                </Space>
                                            </Space>
                                        </Card>
                                        {/* Show replies */}
                                        {comment.replies && comment.replies.length > 0 && (
                                            <div style={{ marginLeft: 24, marginBottom: 12, borderLeft: '2px solid #e8e8e8', paddingLeft: 12 }}>
                                                {comment.replies.map((reply) => (
                                                    <Card
                                                        key={reply.id}
                                                        size="small"
                                                        style={{ marginBottom: 6, backgroundColor: '#fafafa' }}
                                                        styles={{ body: { padding: 10 } }}
                                                    >
                                                        <Space direction="vertical" size={2} style={{ width: '100%' }}>
                                                            <Space>
                                                                <Avatar
                                                                    size={20}
                                                                    icon={<UserOutlined />}
                                                                    style={{ backgroundColor: reply.authorType === 'auditor' ? '#0f386a' : '#52c41a' }}
                                                                />
                                                                <Text strong style={{ fontSize: 12 }}>{reply.authorName}</Text>
                                                                <Tag color={reply.authorType === 'auditor' ? 'blue' : 'green'} style={{ fontSize: 9 }}>
                                                                    {reply.authorType}
                                                                </Tag>
                                                                <Text type="secondary" style={{ fontSize: 11 }}>
                                                                    {new Date(reply.createdAt).toLocaleString()}
                                                                </Text>
                                                            </Space>
                                                            <Paragraph style={{ margin: 0, marginLeft: 28, fontSize: 13 }}>
                                                                {reply.content}
                                                            </Paragraph>
                                                        </Space>
                                                    </Card>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <Empty description="No comments yet" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                        )}
                    </div>
                )}
            </Modal>

            {/* Add Comment Modal */}
            <Modal
                title="Add Comment"
                open={commentModal}
                onCancel={() => {
                    setCommentModal(false);
                    setSelectedControl(null);
                    setCommentText('');
                }}
                onOk={handleSubmitComment}
                okText="Submit Comment"
                okButtonProps={{ disabled: !commentText.trim() }}
                width={600}
            >
                {selectedControl && (
                    <div>
                        <Alert
                            message={`Adding comment for: ${selectedControl.questionText.substring(0, 100)}${selectedControl.questionText.length > 100 ? '...' : ''}`}
                            type="info"
                            showIcon
                            style={{ marginBottom: 16 }}
                        />
                        <Input.TextArea
                            rows={4}
                            placeholder="Enter your comment..."
                            value={commentText}
                            onChange={(e) => setCommentText(e.target.value)}
                        />
                    </div>
                )}
            </Modal>

            {/* View All Comments Modal */}
            <Modal
                title={<Space><CommentOutlined /> All Comments ({comments.length})</Space>}
                open={viewCommentsModal}
                onCancel={() => setViewCommentsModal(false)}
                footer={[
                    <Button key="close" onClick={() => setViewCommentsModal(false)}>
                        Close
                    </Button>
                ]}
                width={800}
            >
                {comments.length > 0 ? (
                    <div style={{ maxHeight: 500, overflowY: 'auto' }}>
                        {comments.map((comment) => (
                            <Card
                                key={comment.id}
                                size="small"
                                style={{ marginBottom: 12 }}
                                styles={{ body: { padding: 16 } }}
                            >
                                <Space direction="vertical" size={8} style={{ width: '100%' }}>
                                    <Space style={{ justifyContent: 'space-between', width: '100%' }}>
                                        <Space>
                                            <Avatar
                                                icon={<UserOutlined />}
                                                style={{ backgroundColor: comment.authorType === 'auditor' ? '#0f386a' : '#52c41a' }}
                                            />
                                            <div>
                                                <Text strong>{comment.authorName}</Text>
                                                <br />
                                                <Text type="secondary" style={{ fontSize: 12 }}>
                                                    {new Date(comment.createdAt).toLocaleString()}
                                                </Text>
                                            </div>
                                        </Space>
                                        <Space>
                                            <Tag color={comment.authorType === 'auditor' ? 'blue' : 'green'}>
                                                {comment.authorType}
                                            </Tag>
                                            <Tag>{comment.commentType.replace('_', ' ')}</Tag>
                                            <Tag color={comment.status === 'open' ? 'orange' : 'green'}>{comment.status}</Tag>
                                        </Space>
                                    </Space>
                                    <Paragraph style={{ margin: 0, padding: '8px 0', background: '#f5f5f5', borderRadius: 4, paddingLeft: 12 }}>
                                        {comment.content}
                                    </Paragraph>
                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                        Target: {comment.targetType} ({comment.targetId.substring(0, 8)}...)
                                    </Text>
                                </Space>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <Empty description="No comments yet" />
                )}
            </Modal>
        </Layout>
    );
}
