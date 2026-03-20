import { useState, useEffect } from 'react';
import { Button, Table, Tag, Space, notification, Collapse, Divider, Typography, Spin } from 'antd';
import { SyncOutlined, EyeOutlined, CheckOutlined, CloseOutlined, DownloadOutlined } from '@ant-design/icons';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import type { TableColumnsType } from 'antd';
import useAuthStore from '../store/useAuthStore';

const { Panel } = Collapse;
const { Title, Text, Paragraph } = Typography;


interface FrameworkUpdate {
    id: string | null;
    version: number;
    description: string;
    status: 'available' | 'applied' | 'failed';
    applied_at: string | null;
    applied_by: string | null;
    error_message: string | null;
}

interface UpdatePreview {
    version: number;
    description: string;
    new_questions: Array<{
        chapter_id: number;
        chapter_name: string;
        title: string;
        question_text: string;
    }>;
    new_chapters: Array<{
        name: string;
        description: string;
        chapter_number: string;
    }>;
    new_objectives: Array<{
        chapter_id: number;
        chapter_name: string;
        subchapter: string;
        title: string;
        requirement_description: string;
        objective_utilities: string;
    }>;
    updated_objectives: Array<{
        subchapter: string;
        chapter_name: string;
        title?: string;
        current_title: string;
        requirement_description?: string;
        current_requirement_description: string;
        objective_utilities?: string;
        current_objective_utilities: string;
    }>;
    updated_questions: Array<{
        question_id: string;
        text?: string;
        current_text: string;
        description?: string;
        current_description: string;
    }>;
}

interface FrameworkUpdatesSectionProps {
    frameworkId: string;
    userRole?: string;
}

const FrameworkUpdatesSection: React.FC<FrameworkUpdatesSectionProps> = ({ frameworkId, userRole }) => {
    const [updates, setUpdates] = useState<FrameworkUpdate[]>([]);
    const [loading, setLoading] = useState(false);
    const [previewData, setPreviewData] = useState<UpdatePreview | null>(null);
    const [previewVersion, setPreviewVersion] = useState<number | null>(null);
    const [applying, setApplying] = useState(false);

    useEffect(() => {
        if (frameworkId) {
            fetchUpdates();
        }
    }, [frameworkId]);

    const fetchUpdates = async () => {
        setLoading(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/frameworks/${frameworkId}/updates`,
                {
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader(),
                    },
                }
            );

            if (!response.ok) {
                throw new Error('Failed to fetch updates');
            }

            const data = await response.json();
            setUpdates(data);
        } catch (error) {
            notification.error({
                message: 'Error',
                description: 'Failed to fetch framework updates',
            });
        } finally {
            setLoading(false);
        }
    };

    const fetchPreview = async (version: number) => {
        setLoading(true);
        setPreviewVersion(version);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/frameworks/${frameworkId}/updates/${version}/preview`,
                {
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader(),
                    },
                }
            );

            if (!response.ok) {
                throw new Error('Failed to fetch preview');
            }

            const data = await response.json();
            setPreviewData(data);
        } catch (error) {
            notification.error({
                message: 'Error',
                description: 'Failed to fetch update preview',
            });
            setPreviewData(null);
        } finally {
            setLoading(false);
        }
    };

    const applyUpdate = async (version: number) => {
        setApplying(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/frameworks/${frameworkId}/updates/${version}/apply`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader(),
                    },
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to apply update');
            }

            const result = await response.json();

            notification.success({
                message: 'Update Applied Successfully',
                description: `Added ${result.changes.new_questions_count} questions, ${result.changes.new_objectives_count} objectives, updated ${result.changes.updated_objectives_count} objectives and ${result.changes.updated_questions_count} questions`,
            });

            // Refresh the updates list
            fetchUpdates();
            setPreviewData(null);
            setPreviewVersion(null);
        } catch (error: any) {
            notification.error({
                message: 'Failed to Apply Update',
                description: error.message || 'An error occurred while applying the update',
            });
        } finally {
            setApplying(false);
        }
    };

    const downloadPromptsGuide = async () => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/frameworks/update-prompts-guide`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader(),
                    },
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to download guide');
            }

            // Get the blob and create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'framework_update_prompts_guide.txt';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            notification.success({
                message: 'Download Started',
                description: 'Framework update prompts guide downloaded successfully',
            });
        } catch (error: any) {
            notification.error({
                message: 'Download Failed',
                description: error.message || 'Failed to download the guide',
            });
        }
    };

    const getStatusTag = (status: string) => {
        switch (status) {
            case 'available':
                return <Tag color="blue">Available</Tag>;
            case 'applied':
                return <Tag color="green" icon={<CheckOutlined />}>Applied</Tag>;
            case 'failed':
                return <Tag color="red" icon={<CloseOutlined />}>Failed</Tag>;
            default:
                return <Tag>{status}</Tag>;
        }
    };

    const columns: TableColumnsType<FrameworkUpdate> = [
        {
            title: 'Version',
            dataIndex: 'version',
            key: 'version',
            width: 100,
            render: (version: number) => <Text strong>Update {version}</Text>,
        },
        {
            title: 'Description',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true,
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: 120,
            render: (status: string) => getStatusTag(status),
        },
        {
            title: 'Applied Date',
            dataIndex: 'applied_at',
            key: 'applied_at',
            width: 180,
            render: (date: string | null) => date ? new Date(date).toLocaleString() : '-',
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 220,
            render: (_: any, record: FrameworkUpdate) => (
                <Space>
                    <Button
                        type="default"
                        icon={<EyeOutlined />}
                        size="small"
                        onClick={() => fetchPreview(record.version)}
                        disabled={previewVersion === record.version && loading}
                    >
                        Preview
                    </Button>
                    {record.status === 'available' && (
                        <Button
                            type="primary"
                            icon={<SyncOutlined />}
                            size="small"
                            onClick={() => applyUpdate(record.version)}
                            loading={applying}
                        >
                            Apply
                        </Button>
                    )}
                </Space>
            ),
        },
    ];

    return (
        <>
            {userRole === 'super_admin' && (
                <div style={{ marginTop: 16, marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                        type="primary"
                        icon={<DownloadOutlined />}
                        onClick={downloadPromptsGuide}
                    >
                        Download Prompts Guide
                    </Button>
                </div>
            )}

            {loading && !previewData ? (
                <div style={{ textAlign: 'center', padding: 40 }}>
                    <Spin size="large" />
                </div>
            ) : (
                <>
                    <Table
                        columns={columns}
                        dataSource={updates}
                        rowKey={(record) => `update-${record.version}`}
                        pagination={false}
                        size="small"
                        locale={{
                            emptyText: 'No updates available for this framework',
                        }}
                    />

                    {previewData && (
                        <div style={{ marginTop: 24, padding: 16, border: '1px solid #d9d9d9', borderRadius: 4 }}>
                            <Title level={5}>
                                Preview: Update {previewData.version} - {previewData.description}
                            </Title>

                            {/* New Chapters */}
                            {previewData.new_chapters.length > 0 && (
                                <>
                                    <Divider orientation="left" plain>
                                        New Chapters ({previewData.new_chapters.length})
                                    </Divider>
                                    {previewData.new_chapters.map((chapter, idx) => (
                                        <div key={idx} style={{ marginBottom: 12, padding: 12, background: '#f0f5ff', borderRadius: 4 }}>
                                            <Text strong>{chapter.chapter_number}. {chapter.name}</Text>
                                            <Paragraph style={{ marginTop: 8, marginBottom: 0 }}>{chapter.description}</Paragraph>
                                        </div>
                                    ))}
                                </>
                            )}

                            {/* New Questions */}
                            {previewData.new_questions.length > 0 && (
                                <>
                                    <Divider orientation="left" plain>
                                        New Questions ({previewData.new_questions.length})
                                    </Divider>
                                    {previewData.new_questions.map((question, idx) => (
                                        <div key={idx} style={{ marginBottom: 12, padding: 12, background: '#f6ffed', borderRadius: 4 }}>
                                            <Tag color="green">Chapter: {question.chapter_name}</Tag>
                                            <Paragraph strong style={{ marginTop: 8 }}>{question.title}</Paragraph>
                                            <Paragraph style={{ marginBottom: 0 }}>{question.question_text}</Paragraph>
                                        </div>
                                    ))}
                                </>
                            )}

                            {/* New Objectives */}
                            {previewData.new_objectives.length > 0 && (
                                <>
                                    <Divider orientation="left" plain>
                                        New Objectives ({previewData.new_objectives.length})
                                    </Divider>
                                    {previewData.new_objectives.map((objective, idx) => (
                                        <div key={idx} style={{ marginBottom: 12, padding: 12, background: '#f6ffed', borderRadius: 4 }}>
                                            <Space>
                                                <Tag color="blue">Chapter: {objective.chapter_name}</Tag>
                                                <Tag color="purple">Subchapter: {objective.subchapter}</Tag>
                                            </Space>
                                            <Paragraph strong style={{ marginTop: 8 }}>{objective.title}</Paragraph>
                                            <Paragraph style={{ marginBottom: 4 }}>
                                                <Text strong>Requirement: </Text>{objective.requirement_description}
                                            </Paragraph>
                                            <Paragraph style={{ marginBottom: 0 }}>
                                                <Text strong>Utilities: </Text>{objective.objective_utilities}
                                            </Paragraph>
                                        </div>
                                    ))}
                                </>
                            )}

                            {/* Updated Objectives */}
                            {previewData.updated_objectives.length > 0 && (
                                <>
                                    <Divider orientation="left" plain>
                                        Updated Objectives ({previewData.updated_objectives.length})
                                    </Divider>
                                    {previewData.updated_objectives.map((objective, idx) => (
                                        <div key={idx} style={{ marginBottom: 12, padding: 12, background: '#fffbe6', borderRadius: 4 }}>
                                            <Space>
                                                <Tag color="orange">Chapter: {objective.chapter_name}</Tag>
                                                <Tag color="purple">Subchapter: {objective.subchapter}</Tag>
                                            </Space>
                                            <Paragraph strong style={{ marginTop: 8 }}>
                                                {objective.title || objective.current_title}
                                            </Paragraph>

                                            {objective.requirement_description && (
                                                <Collapse size="small" style={{ marginBottom: 8 }}>
                                                    <Panel header="Requirement Description (Changed)" key="1">
                                                        <Text type="danger" delete>Old: {objective.current_requirement_description}</Text>
                                                        <br />
                                                        <Text type="success">New: {objective.requirement_description}</Text>
                                                    </Panel>
                                                </Collapse>
                                            )}

                                            {objective.objective_utilities && (
                                                <Collapse size="small">
                                                    <Panel header="Objective Utilities (Changed)" key="2">
                                                        <Text type="danger" delete>Old: {objective.current_objective_utilities}</Text>
                                                        <br />
                                                        <Text type="success">New: {objective.objective_utilities}</Text>
                                                    </Panel>
                                                </Collapse>
                                            )}
                                        </div>
                                    ))}
                                </>
                            )}

                            {/* Updated Questions */}
                            {previewData.updated_questions && previewData.updated_questions.length > 0 && (
                                <>
                                    <Divider orientation="left" plain>
                                        Updated Questions ({previewData.updated_questions.length})
                                    </Divider>
                                    {previewData.updated_questions.map((question, idx) => (
                                        <div key={idx} style={{ marginBottom: 12, padding: 12, background: '#fff7e6', borderRadius: 4 }}>
                                            <Tag color="orange">Question Update</Tag>

                                            {question.text && (
                                                <Collapse size="small" style={{ marginTop: 8 }}>
                                                    <Panel header="Question Text (Changed)" key="1">
                                                        <Text type="danger" delete>Old: {question.current_text}</Text>
                                                        <br />
                                                        <Text type="success">New: {question.text}</Text>
                                                    </Panel>
                                                </Collapse>
                                            )}

                                            {question.description && (
                                                <Collapse size="small" style={{ marginTop: 8 }}>
                                                    <Panel header="Question Description (Changed)" key="2">
                                                        <Text type="danger" delete>Old: {question.current_description}</Text>
                                                        <br />
                                                        <Text type="success">New: {question.description}</Text>
                                                    </Panel>
                                                </Collapse>
                                            )}
                                        </div>
                                    ))}
                                </>
                            )}

                            {previewData.new_chapters.length === 0 &&
                                previewData.new_questions.length === 0 &&
                                previewData.new_objectives.length === 0 &&
                                previewData.updated_objectives.length === 0 &&
                                (!previewData.updated_questions || previewData.updated_questions.length === 0) && (
                                    <Paragraph type="secondary">No changes in this update.</Paragraph>
                                )}
                        </div>
                    )}
                </>
            )}
        </>
    );
};

export default FrameworkUpdatesSection;
