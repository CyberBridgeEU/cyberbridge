import React, { useEffect, useState } from 'react';
import {
    Timeline, Tag, Typography, Empty, Spin, Select, Button, Tooltip, notification, Card, Row, Col, Table
} from 'antd';
import {
    PlusOutlined, DeleteOutlined, ReloadOutlined,
    BugOutlined, EditOutlined, ToolOutlined, GlobalOutlined, AuditOutlined, SafetyOutlined
} from '@ant-design/icons';
import useIncidentStore, { type ForensicTimelineEvent, type LinkedEvidence } from '../store/useIncidentStore';
import InfoTitle from './InfoTitle';

const { Text } = Typography;

interface ForensicTimelineProps {
    incidentId: string | null;
    availableEvidence: LinkedEvidence[];
}

const EVENT_CONFIG: Record<string, { color: string; icon: React.ReactNode; tagColor: string; label: string }> = {
    incident_created: { color: '#cf1322', icon: <BugOutlined />, tagColor: 'red', label: 'Created' },
    field_updated: { color: '#1890ff', icon: <EditOutlined />, tagColor: 'blue', label: 'Updated' },
    patch_released: { color: '#52c41a', icon: <ToolOutlined />, tagColor: 'green', label: 'Patch' },
    enisa_notification: { color: '#722ed1', icon: <GlobalOutlined />, tagColor: 'purple', label: 'ENISA' },
    advisory_published: { color: '#fa8c16', icon: <AuditOutlined />, tagColor: 'orange', label: 'Advisory' },
    evidence_linked: { color: '#13c2c2', icon: <SafetyOutlined />, tagColor: 'cyan', label: 'Evidence' },
};

const EVENT_TYPE_OPTIONS = [
    { label: 'All', value: 'all' },
    { label: 'Created', value: 'incident_created' },
    { label: 'Field Updates', value: 'field_updated' },
    { label: 'Patches', value: 'patch_released' },
    { label: 'ENISA', value: 'enisa_notification' },
    { label: 'Advisories', value: 'advisory_published' },
    { label: 'Evidence', value: 'evidence_linked' },
];

const ForensicTimeline: React.FC<ForensicTimelineProps> = ({ incidentId, availableEvidence }) => {
    const {
        forensicTimeline, timelineLoading, linkedEvidence,
        fetchForensicTimeline, fetchLinkedEvidence, linkEvidence, unlinkEvidence
    } = useIncidentStore();

    const [filterType, setFilterType] = useState<string>('all');
    const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
    const [linking, setLinking] = useState(false);

    useEffect(() => {
        if (incidentId) {
            fetchForensicTimeline(incidentId);
            fetchLinkedEvidence(incidentId);
        }
    }, [incidentId]);

    const handleRefresh = () => {
        if (incidentId) {
            fetchForensicTimeline(incidentId);
            fetchLinkedEvidence(incidentId);
        }
    };

    const handleLinkEvidence = async () => {
        if (!incidentId || !selectedEvidenceId) return;
        setLinking(true);
        const ok = await linkEvidence(incidentId, selectedEvidenceId);
        setLinking(false);
        if (ok) {
            notification.success({ message: 'Evidence linked to incident' });
            setSelectedEvidenceId(null);
            fetchLinkedEvidence(incidentId);
            fetchForensicTimeline(incidentId);
        } else {
            notification.error({ message: 'Failed to link evidence (may already be linked)' });
        }
    };

    const handleUnlinkEvidence = async (evidenceId: string) => {
        if (!incidentId) return;
        const ok = await unlinkEvidence(incidentId, evidenceId);
        if (ok) {
            notification.success({ message: 'Evidence unlinked' });
            fetchLinkedEvidence(incidentId);
            fetchForensicTimeline(incidentId);
        } else {
            notification.error({ message: 'Failed to unlink evidence' });
        }
    };

    const filtered = filterType === 'all'
        ? forensicTimeline
        : forensicTimeline.filter(e => e.event_type === filterType);

    const linkedIds = new Set(linkedEvidence.map(e => e.id));
    const evidenceOptions = availableEvidence
        .filter(e => !linkedIds.has(e.id))
        .map(e => ({ label: `${e.name} (${e.evidence_type})`, value: e.id }));

    const evidenceColumns = [
        { title: 'Name', dataIndex: 'name', key: 'name' },
        { title: 'Type', dataIndex: 'evidence_type', key: 'evidence_type' },
        { title: 'Custody', dataIndex: 'custody_status', key: 'custody_status', render: (v: string) => v ? <Tag>{v}</Tag> : '-' },
        { title: 'Linked', dataIndex: 'linked_at', key: 'linked_at', render: (v: string) => v ? new Date(v).toLocaleString() : '-' },
        {
            title: '',
            key: 'actions',
            render: (_: any, record: LinkedEvidence) => (
                <Tooltip title="Unlink evidence">
                    <Button
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => handleUnlinkEvidence(record.id)}
                    />
                </Tooltip>
            )
        }
    ];

    if (!incidentId) {
        return <Empty description="Select an incident to view its forensic timeline" />;
    }

    return (
        <div>
            <InfoTitle
                title="Forensic Timeline"
                infoContent="Chronological record of all forensic events related to this incident: lifecycle changes, patches, ENISA notifications, security advisories, and linked evidence."
                className="section-title"
            />

            {/* Evidence management panel */}
            <Card size="small" style={{ marginBottom: 16 }}>
                <Text strong>Linked Evidence</Text>
                <div style={{ display: 'flex', gap: 8, marginTop: 8, marginBottom: 12 }}>
                    <Select
                        placeholder="Attach evidence item..."
                        options={evidenceOptions}
                        value={selectedEvidenceId}
                        onChange={setSelectedEvidenceId}
                        style={{ flex: 1 }}
                        showSearch
                        filterOption={(input, option) =>
                            (option?.label as string || '').toLowerCase().includes(input.toLowerCase())
                        }
                    />
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={handleLinkEvidence}
                        disabled={!selectedEvidenceId}
                        loading={linking}
                    >
                        Attach
                    </Button>
                </div>
                {linkedEvidence.length > 0 ? (
                    <Table
                        dataSource={linkedEvidence}
                        columns={evidenceColumns}
                        rowKey="id"
                        size="small"
                        pagination={false}
                    />
                ) : (
                    <Text type="secondary">No evidence attached yet</Text>
                )}
            </Card>

            {/* Timeline controls */}
            <Row justify="space-between" align="middle" style={{ marginBottom: 12 }}>
                <Col>
                    <Select
                        value={filterType}
                        onChange={setFilterType}
                        options={EVENT_TYPE_OPTIONS}
                        style={{ width: 160 }}
                        size="small"
                    />
                </Col>
                <Col>
                    <Tooltip title="Refresh timeline">
                        <Button size="small" icon={<ReloadOutlined />} onClick={handleRefresh} loading={timelineLoading} />
                    </Tooltip>
                </Col>
            </Row>

            {timelineLoading ? (
                <Spin style={{ display: 'block', marginTop: 32, textAlign: 'center' }} />
            ) : filtered.length === 0 ? (
                <Empty description="No timeline events yet" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            ) : (
                <Timeline
                    style={{ marginTop: 8, paddingLeft: 4 }}
                    items={filtered.map((event: ForensicTimelineEvent, idx: number) => {
                        const cfg = EVENT_CONFIG[event.event_type] || { color: '#8c8c8c', tagColor: 'default', label: event.event_type };
                        return {
                            key: idx,
                            color: cfg.color,
                            children: (
                                <div style={{ paddingBottom: 4 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                        <Tag color={cfg.tagColor}>{cfg.label}</Tag>
                                        <Text strong>{event.title}</Text>
                                        <Text type="secondary" style={{ fontSize: 12 }}>
                                            {event.timestamp ? new Date(event.timestamp).toLocaleString() : '—'}
                                        </Text>
                                        {event.actor && (
                                            <Text type="secondary" style={{ fontSize: 12 }}>· {event.actor}</Text>
                                        )}
                                    </div>
                                    <div style={{ marginTop: 2 }}>
                                        <Text type="secondary">{event.description}</Text>
                                    </div>
                                </div>
                            )
                        };
                    })}
                />
            )}
        </div>
    );
};

export default ForensicTimeline;
