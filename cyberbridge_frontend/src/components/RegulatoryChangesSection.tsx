import React, { useEffect, useState } from 'react';
import { Table, Tag, Button, Space, notification, Typography, Collapse, Spin, Modal, Input } from 'antd';
import { CheckOutlined, CloseOutlined, SendOutlined, FileTextOutlined, RightOutlined, DownOutlined } from '@ant-design/icons';
import type { TableColumnsType } from 'antd';
import useRegulatoryMonitorStore from '../store/useRegulatoryMonitorStore';
import useFrameworksStore from '../store/useFrameworksStore';
import InfoTitle from './InfoTitle';

const { Text, Paragraph } = Typography;
const { TextArea } = Input;

interface RegulatoryChangesSectionProps {
    frameworkId: string;
    userRole?: string;
}

const RegulatoryChangesSection: React.FC<RegulatoryChangesSectionProps> = ({ frameworkId, userRole }) => {
    const {
        changes,
        fetchChanges,
        reviewChange,
        applyChanges,
        applyToSeed,
        loading
    } = useRegulatoryMonitorStore();

    const { frameworks } = useFrameworksStore();
    const [applying, setApplying] = useState(false);
    const [seedModalVisible, setSeedModalVisible] = useState(false);
    const [seedDescription, setSeedDescription] = useState('');

    // Detect framework type from selected framework
    const selectedFramework = frameworks.find(f => f.id === frameworkId);
    const frameworkType = selectedFramework ? detectFrameworkType(selectedFramework.name) : null;

    useEffect(() => {
        if (frameworkType) {
            fetchChanges(frameworkType);
        }
    }, [frameworkId, frameworkType]);

    const handleReview = async (changeId: string, status: 'approved' | 'rejected') => {
        const success = await reviewChange(changeId, status);
        if (success) {
            notification.success({ message: `Change ${status}` });
        } else {
            notification.error({ message: 'Review failed' });
        }
    };

    const handleApplyToOrg = async () => {
        const approvedIds = changes.filter(c => c.status === 'approved').map(c => c.id);
        if (approvedIds.length === 0) {
            notification.warning({ message: 'No approved changes to apply' });
            return;
        }
        setApplying(true);
        const success = await applyChanges(approvedIds, frameworkId);
        setApplying(false);
        if (success) {
            notification.success({
                message: 'Changes Applied',
                description: `Applied ${approvedIds.length} changes to your organization's framework`
            });
            if (frameworkType) fetchChanges(frameworkType);
        } else {
            notification.error({ message: 'Failed to apply changes' });
        }
    };

    const handleApplyToSeed = async () => {
        if (!frameworkType) return;
        const approvedIds = changes.filter(c => c.status === 'approved').map(c => c.id);
        if (approvedIds.length === 0) {
            notification.warning({ message: 'No approved changes to apply' });
            return;
        }
        setApplying(true);
        const result = await applyToSeed(approvedIds, frameworkType, seedDescription);
        setApplying(false);
        setSeedModalVisible(false);
        setSeedDescription('');
        if (result) {
            notification.success({
                message: 'Seed File Written',
                description: `Update file written to ${result.file_path} (version ${result.version})`
            });
            if (frameworkType) fetchChanges(frameworkType);
        } else {
            notification.error({ message: 'Failed to write seed file' });
        }
    };

    const getChangeTypeTag = (type: string) => {
        const colors: Record<string, string> = {
            new_chapter: 'blue',
            new_objective: 'green',
            update_objective: 'orange',
            new_question: 'cyan',
            update_question: 'gold',
            remove_objective: 'red',
        };
        return <Tag color={colors[type] || 'default'}>{type.replace(/_/g, ' ')}</Tag>;
    };

    const getStatusTag = (status: string) => {
        const map: Record<string, { color: string; icon?: React.ReactNode }> = {
            pending: { color: 'blue' },
            approved: { color: 'green', icon: <CheckOutlined /> },
            rejected: { color: 'red', icon: <CloseOutlined /> },
            applied: { color: 'purple' },
        };
        const info = map[status] || { color: 'default' };
        return <Tag color={info.color} icon={info.icon}>{status}</Tag>;
    };

    const columns: TableColumnsType<any> = [
        {
            title: 'Type',
            dataIndex: 'change_type',
            key: 'change_type',
            width: 150,
            render: (type: string) => getChangeTypeTag(type),
        },
        {
            title: 'Identifier',
            dataIndex: 'entity_identifier',
            key: 'entity_identifier',
            width: 120,
            render: (id: string) => <Text code>{id || 'N/A'}</Text>,
        },
        {
            title: 'Confidence',
            dataIndex: 'confidence',
            key: 'confidence',
            width: 100,
            render: (c: number | null) => c !== null ? (
                <Text type={c >= 0.8 ? 'success' : c >= 0.5 ? 'warning' : 'danger'}>
                    {Math.round(c * 100)}%
                </Text>
            ) : '-',
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: 100,
            render: (status: string) => getStatusTag(status),
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 180,
            render: (_: any, record: any) => record.status === 'pending' ? (
                <Space>
                    <Button
                        type="primary"
                        size="small"
                        icon={<CheckOutlined />}
                        onClick={() => handleReview(record.id, 'approved')}
                        style={{ background: '#52c41a', borderColor: '#52c41a' }}
                    >
                        Approve
                    </Button>
                    <Button
                        size="small"
                        danger
                        icon={<CloseOutlined />}
                        onClick={() => handleReview(record.id, 'rejected')}
                    >
                        Reject
                    </Button>
                </Space>
            ) : null,
        },
    ];

    const approvedCount = changes.filter(c => c.status === 'approved').length;
    const pendingCount = changes.filter(c => c.status === 'pending').length;

    if (!frameworkType || changes.length === 0) {
        return null;
    }

    return (
        <>
            <InfoTitle
                title="Regulatory Changes"
                infoContent="Changes discovered by the Regulatory Change Monitor. Review and approve changes, then apply them to your organization's framework or write them to seed template files."
                className="section-title"
            />
            <p className="section-subtitle">
                {pendingCount > 0 && `${pendingCount} pending review. `}
                {approvedCount > 0 && `${approvedCount} approved and ready to apply.`}
            </p>

            {loading ? (
                <div style={{ textAlign: 'center', padding: 40 }}><Spin size="large" /></div>
            ) : (
                <>
                    <Table
                        columns={columns}
                        dataSource={changes}
                        rowKey="id"
                        size="small"
                        pagination={false}
                        expandable={{
                            expandIcon: ({ expanded, onExpand, record }: any) => (
                                expanded
                                    ? <DownOutlined onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#1a365d' }} />
                                    : <RightOutlined onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#1a365d' }} />
                            ),
                            expandedRowRender: (record: any) => (
                                <div style={{ padding: '8px 0' }}>
                                    {record.source_excerpt && (
                                        <Paragraph>
                                            <Text strong>Source: </Text>
                                            {record.source_url ? (
                                                <a href={record.source_url} target="_blank" rel="noreferrer">{record.source_url}</a>
                                            ) : 'N/A'}
                                            <br />
                                            <Text type="secondary">{record.source_excerpt}</Text>
                                        </Paragraph>
                                    )}
                                    {record.llm_reasoning && (
                                        <Paragraph>
                                            <Text strong>Reasoning: </Text>{record.llm_reasoning}
                                        </Paragraph>
                                    )}
                                    {record.current_value && (
                                        <Collapse size="small" style={{ marginBottom: 8 }}>
                                            <Collapse.Panel header="Current Value" key="current">
                                                <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap' }}>
                                                    {JSON.stringify(JSON.parse(record.current_value), null, 2)}
                                                </pre>
                                            </Collapse.Panel>
                                        </Collapse>
                                    )}
                                    {record.proposed_value && (
                                        <Collapse size="small">
                                            <Collapse.Panel header="Proposed Value" key="proposed">
                                                <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap' }}>
                                                    {JSON.stringify(JSON.parse(record.proposed_value), null, 2)}
                                                </pre>
                                            </Collapse.Panel>
                                        </Collapse>
                                    )}
                                </div>
                            ),
                        }}
                    />

                    {approvedCount > 0 && (
                        <div style={{ marginTop: 16, display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
                            <Button
                                type="primary"
                                icon={<SendOutlined />}
                                onClick={handleApplyToOrg}
                                loading={applying}
                                style={{ background: '#1a365d', borderColor: '#1a365d' }}
                            >
                                Apply Approved to My Org ({approvedCount})
                            </Button>
                            {userRole === 'super_admin' && (
                                <Button
                                    type="primary"
                                    icon={<FileTextOutlined />}
                                    onClick={() => setSeedModalVisible(true)}
                                    loading={applying}
                                    style={{ background: '#722ed1', borderColor: '#722ed1' }}
                                >
                                    Apply to Seed Templates ({approvedCount})
                                </Button>
                            )}
                        </div>
                    )}
                </>
            )}

            <Modal
                title="Write Seed Update File"
                open={seedModalVisible}
                onOk={handleApplyToSeed}
                onCancel={() => setSeedModalVisible(false)}
                confirmLoading={applying}
                okText="Write to Disk"
            >
                <p>This will generate a Python update file from the {approvedCount} approved changes and write it to the seeds directory.</p>
                <TextArea
                    placeholder="Optional description for this update"
                    value={seedDescription}
                    onChange={e => setSeedDescription(e.target.value)}
                    rows={3}
                />
            </Modal>
        </>
    );
};

// Helper to detect framework type from name
function detectFrameworkType(name: string): string | null {
    const lower = name.toLowerCase();
    const map: Record<string, string[]> = {
        cra: ['cra', 'cyber resilience act'],
        nis2_directive: ['nis', 'nis2'],
        iso_27001_2022: ['iso', '27001'],
        gdpr: ['gdpr'],
        dora_2022: ['dora'],
        nist_csf_2_0: ['nist', 'cybersecurity framework'],
        cmmc_2_0: ['cmmc'],
        pci_dss_v4_0: ['pci', 'payment card'],
        soc_2: ['soc 2', 'soc2'],
        hipaa_privacy_rule: ['hipaa'],
        cobit_2019: ['cobit'],
        ccpa_california_consumer_privacy_act: ['ccpa'],
        ftc_safeguards: ['ftc', 'safeguards'],
        australia_energy_aescsf: ['aescsf'],
    };
    for (const [type, keywords] of Object.entries(map)) {
        if (keywords.some(kw => lower.includes(kw))) return type;
    }
    return null;
}

export default RegulatoryChangesSection;
