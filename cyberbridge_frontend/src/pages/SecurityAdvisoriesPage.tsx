import { Table, notification, Tag, Modal, Tabs, Card, Row, Col, Input, Button, Select, Space } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { PlusOutlined, EditOutlined, DeleteOutlined, DashboardOutlined, FileTextOutlined, SearchOutlined, NotificationOutlined } from '@ant-design/icons';
import useAdvisoryStore from "../store/useAdvisoryStore.ts";
import useIncidentStore from "../store/useIncidentStore.ts";
import type { SecurityAdvisory } from "../store/useAdvisoryStore.ts";
import { useEffect, useState, useMemo } from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import { AdvisoriesInfo } from "../constants/infoContent.tsx";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { StatCard, DashboardSection } from "../components/dashboard";
import dayjs from "dayjs";

const { TextArea } = Input;

const getSeverityColor = (severity: string | null): string => {
    switch ((severity || '').toLowerCase()) {
        case 'critical': return '#cf1322';
        case 'high': return '#fa541c';
        case 'medium': return '#d48806';
        case 'low': return '#389e0d';
        default: return '#8c8c8c';
    }
};

const getAdvisoryStatusColor = (status: string | null): string => {
    switch ((status || '').toLowerCase()) {
        case 'draft': return '#8c8c8c';
        case 'review': return '#d48806';
        case 'published': return '#389e0d';
        case 'updated': return '#1890ff';
        case 'archived': return '#595959';
        default: return '#8c8c8c';
    }
};

const SecurityAdvisoriesPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const [api, contextHolder] = notification.useNotification();

    const [activeTab, setActiveTab] = useState<string>('dashboard');
    const [searchText, setSearchText] = useState('');
    const [showForm, setShowForm] = useState(false);
    const [selectedAdvisory, setSelectedAdvisory] = useState<string | null>(null);

    // Form state
    const [formTitle, setFormTitle] = useState('');
    const [formDescription, setFormDescription] = useState('');
    const [formAffectedVersions, setFormAffectedVersions] = useState('');
    const [formFixedVersion, setFormFixedVersion] = useState('');
    const [formSeverity, setFormSeverity] = useState<string | undefined>(undefined);
    const [formCveIds, setFormCveIds] = useState('');
    const [formWorkaround, setFormWorkaround] = useState('');
    const [formStatusId, setFormStatusId] = useState<string | undefined>(undefined);
    const [formIncidentId, setFormIncidentId] = useState<string | undefined>(undefined);

    const {
        advisories, advisoryStatuses, loading, error,
        fetchAdvisories, fetchAdvisoryStatuses, createAdvisory, updateAdvisory, deleteAdvisory
    } = useAdvisoryStore();

    const { incidents, fetchIncidents } = useIncidentStore();

    useEffect(() => {
        fetchAdvisories();
        fetchAdvisoryStatuses();
        fetchIncidents();
    }, []);

    const filteredAdvisories = useMemo(() => {
        if (!searchText) return advisories;
        const lower = searchText.toLowerCase();
        return advisories.filter(a =>
            (a.advisory_code || '').toLowerCase().includes(lower) ||
            (a.title || '').toLowerCase().includes(lower) ||
            (a.severity || '').toLowerCase().includes(lower) ||
            (a.cve_ids || '').toLowerCase().includes(lower)
        );
    }, [advisories, searchText]);

    const stats = useMemo(() => {
        const total = advisories.length;
        const published = advisories.filter(a => (a.advisory_status_name || '').toLowerCase() === 'published').length;
        const draft = advisories.filter(a => (a.advisory_status_name || '').toLowerCase() === 'draft').length;
        const critical = advisories.filter(a => (a.severity || '').toLowerCase() === 'critical').length;
        const high = advisories.filter(a => (a.severity || '').toLowerCase() === 'high').length;
        return { total, published, draft, critical, high };
    }, [advisories]);

    const handleClear = (hideForm = false) => {
        setSelectedAdvisory(null);
        setFormTitle('');
        setFormDescription('');
        setFormAffectedVersions('');
        setFormFixedVersion('');
        setFormSeverity(undefined);
        setFormCveIds('');
        setFormWorkaround('');
        setFormStatusId(undefined);
        setFormIncidentId(undefined);
        if (hideForm) setShowForm(false);
    };

    const handleRowClick = (record: SecurityAdvisory) => {
        setSelectedAdvisory(record.id);
        setFormTitle(record.title || '');
        setFormDescription(record.description || '');
        setFormAffectedVersions(record.affected_versions || '');
        setFormFixedVersion(record.fixed_version || '');
        setFormSeverity(record.severity || undefined);
        setFormCveIds(record.cve_ids || '');
        setFormWorkaround(record.workaround || '');
        setFormStatusId(record.advisory_status_id || undefined);
        setFormIncidentId(record.incident_id || undefined);
        setShowForm(true);
    };

    const handleSave = async () => {
        if (!formTitle.trim() || !formStatusId) {
            api.error({ message: 'Validation Error', description: 'Title and Status are required', duration: 4 });
            return;
        }

        const payload: any = {
            title: formTitle.trim(),
            description: formDescription || undefined,
            affected_versions: formAffectedVersions || undefined,
            fixed_version: formFixedVersion || undefined,
            severity: formSeverity || undefined,
            cve_ids: formCveIds || undefined,
            workaround: formWorkaround || undefined,
            advisory_status_id: formStatusId,
            incident_id: formIncidentId || undefined,
        };

        try {
            if (selectedAdvisory) {
                await updateAdvisory(selectedAdvisory, payload);
                api.success({ message: 'Advisory Updated', description: 'Security advisory updated successfully', duration: 4 });
            } else {
                await createAdvisory(payload);
                api.success({ message: 'Advisory Created', description: 'Security advisory created successfully', duration: 4 });
            }
            handleClear(true);
        } catch (e: any) {
            api.error({ message: 'Error', description: e.message || 'An error occurred', duration: 4 });
        }
    };

    const handleDelete = () => {
        if (!selectedAdvisory) return;
        Modal.confirm({
            title: 'Delete Advisory',
            content: 'Are you sure you want to delete this security advisory?',
            okText: 'Delete',
            okType: 'danger',
            onOk: async () => {
                try {
                    await deleteAdvisory(selectedAdvisory);
                    api.success({ message: 'Deleted', description: 'Advisory deleted successfully', duration: 4 });
                    handleClear(true);
                } catch {
                    api.error({ message: 'Delete Failed', description: 'Failed to delete advisory', duration: 4 });
                }
            }
        });
    };

    const columns = [
        {
            title: 'Code',
            dataIndex: 'advisory_code',
            key: 'advisory_code',
            width: 100,
            render: (text: string | null) => text || '-',
        },
        {
            title: 'Title',
            dataIndex: 'title',
            key: 'title',
            ellipsis: true,
        },
        {
            title: 'Severity',
            dataIndex: 'severity',
            key: 'severity',
            width: 100,
            render: (text: string | null) => text ? <Tag color={getSeverityColor(text)}>{text}</Tag> : '-',
            filters: [
                { text: 'Critical', value: 'Critical' },
                { text: 'High', value: 'High' },
                { text: 'Medium', value: 'Medium' },
                { text: 'Low', value: 'Low' },
            ],
            onFilter: (value: any, record: SecurityAdvisory) => record.severity === value,
        },
        {
            title: 'Status',
            dataIndex: 'advisory_status_name',
            key: 'advisory_status_name',
            width: 110,
            render: (text: string | null) => text ? <Tag color={getAdvisoryStatusColor(text)}>{text}</Tag> : '-',
        },
        {
            title: 'CVEs',
            dataIndex: 'cve_ids',
            key: 'cve_ids',
            width: 140,
            ellipsis: true,
            render: (text: string | null) => text || '-',
        },
        {
            title: 'Incident',
            dataIndex: 'incident_code',
            key: 'incident_code',
            width: 100,
            render: (text: string | null) => text || '-',
        },
        {
            title: 'Published',
            dataIndex: 'published_at',
            key: 'published_at',
            width: 120,
            render: (text: string | null) => text ? dayjs(text).format('YYYY-MM-DD') : '-',
            sorter: (a: SecurityAdvisory, b: SecurityAdvisory) => (a.published_at || '').localeCompare(b.published_at || ''),
        },
        {
            title: 'Updated',
            dataIndex: 'updated_at',
            key: 'updated_at',
            width: 120,
            render: (text: string) => dayjs(text).format('YYYY-MM-DD'),
            sorter: (a: SecurityAdvisory, b: SecurityAdvisory) => a.updated_at.localeCompare(b.updated_at),
            defaultSortOrder: 'descend' as const,
        },
    ];

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--page-background)' }}>
            {contextHolder}
            <Sidebar
                selectedKeys={menuHighlighting.selectedKeys}
                openKeys={menuHighlighting.openKeys}
                onOpenChange={menuHighlighting.onOpenChange}
            />
            <div style={{ flex: 1, padding: '24px', overflow: 'auto' }}>
                <InfoTitle title="Security Advisories" infoContent={AdvisoriesInfo} />

                <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    items={[
                        {
                            key: 'dashboard',
                            label: <span><DashboardOutlined /> Dashboard</span>,
                            children: (
                                <div>
                                    <Row gutter={[16, 16]}>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="Total Advisories" value={stats.total} icon={<NotificationOutlined />} color="#1890ff" />
                                        </Col>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="Published" value={stats.published} icon={<FileTextOutlined />} color="#389e0d" />
                                        </Col>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="Critical" value={stats.critical} icon={<NotificationOutlined />} color="#cf1322" />
                                        </Col>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="Draft" value={stats.draft} icon={<EditOutlined />} color="#8c8c8c" />
                                        </Col>
                                    </Row>

                                    <DashboardSection title="Severity Distribution" style={{ marginTop: 24 }}>
                                        <div style={{ display: 'flex', gap: 16 }}>
                                            {[
                                                { label: 'Critical', count: stats.critical, color: '#cf1322' },
                                                { label: 'High', count: stats.high, color: '#fa541c' },
                                                { label: 'Medium', count: advisories.filter(a => (a.severity || '').toLowerCase() === 'medium').length, color: '#d48806' },
                                                { label: 'Low', count: advisories.filter(a => (a.severity || '').toLowerCase() === 'low').length, color: '#389e0d' },
                                            ].map(item => (
                                                <Card key={item.label} size="small" style={{ flex: 1, textAlign: 'center' }}>
                                                    <div style={{ fontSize: 24, fontWeight: 600, color: item.color }}>{item.count}</div>
                                                    <div style={{ fontSize: 12, color: '#8c8c8c' }}>{item.label}</div>
                                                </Card>
                                            ))}
                                        </div>
                                    </DashboardSection>
                                </div>
                            )
                        },
                        {
                            key: 'registry',
                            label: <span><FileTextOutlined /> Advisory Registry</span>,
                            children: (
                                <div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                                        <Input
                                            placeholder="Search advisories..."
                                            prefix={<SearchOutlined />}
                                            value={searchText}
                                            onChange={e => setSearchText(e.target.value)}
                                            style={{ width: 280 }}
                                            allowClear
                                        />
                                        <Button type="primary" icon={<PlusOutlined />} onClick={() => { handleClear(); setShowForm(true); }}>
                                            New Advisory
                                        </Button>
                                    </div>

                                    <Table
                                        dataSource={filteredAdvisories}
                                        columns={columns}
                                        rowKey="id"
                                        size="small"
                                        loading={loading}
                                        pagination={{ pageSize: 15, showSizeChanger: true }}
                                        onRow={(record) => ({
                                            onClick: () => handleRowClick(record),
                                            style: { cursor: 'pointer' }
                                        })}
                                    />

                                    <Modal
                                        title={selectedAdvisory ? 'Edit Advisory' : 'New Advisory'}
                                        open={showForm}
                                        onCancel={() => handleClear(true)}
                                        width={720}
                                        footer={
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <div>
                                                    {selectedAdvisory && (
                                                        <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>Delete</Button>
                                                    )}
                                                </div>
                                                <div style={{ display: 'flex', gap: 8 }}>
                                                    {selectedAdvisory && (
                                                        <Button icon={<PlusOutlined />} onClick={() => handleClear()}>Create New</Button>
                                                    )}
                                                    <Button onClick={() => handleClear(true)}>Cancel</Button>
                                                    <Button type="primary" onClick={handleSave}>
                                                        {selectedAdvisory ? 'Save Changes' : 'Create Advisory'}
                                                    </Button>
                                                </div>
                                            </div>
                                        }
                                    >
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Title <span style={{ color: '#cf1322' }}>*</span></label>
                                                <Input value={formTitle} onChange={e => setFormTitle(e.target.value)} placeholder="Advisory title" />
                                            </div>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Description</label>
                                                <TextArea rows={3} value={formDescription} onChange={e => setFormDescription(e.target.value)} placeholder="Detailed description of the vulnerability" />
                                            </div>
                                            <Row gutter={16}>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Severity</label>
                                                    <Select
                                                        style={{ width: '100%' }}
                                                        value={formSeverity}
                                                        onChange={setFormSeverity}
                                                        placeholder="Select severity"
                                                        allowClear
                                                        options={[
                                                            { value: 'Critical', label: 'Critical' },
                                                            { value: 'High', label: 'High' },
                                                            { value: 'Medium', label: 'Medium' },
                                                            { value: 'Low', label: 'Low' },
                                                        ]}
                                                    />
                                                </Col>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Status <span style={{ color: '#cf1322' }}>*</span></label>
                                                    <Select
                                                        style={{ width: '100%' }}
                                                        value={formStatusId}
                                                        onChange={setFormStatusId}
                                                        placeholder="Select status"
                                                        options={advisoryStatuses.map(s => ({ value: s.id, label: s.status_name }))}
                                                    />
                                                </Col>
                                            </Row>
                                            <Row gutter={16}>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Affected Versions</label>
                                                    <Input value={formAffectedVersions} onChange={e => setFormAffectedVersions(e.target.value)} placeholder="e.g. < 2.1.0" />
                                                </Col>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Fixed Version</label>
                                                    <Input value={formFixedVersion} onChange={e => setFormFixedVersion(e.target.value)} placeholder="e.g. 2.1.0" />
                                                </Col>
                                            </Row>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>CVE IDs</label>
                                                <Input value={formCveIds} onChange={e => setFormCveIds(e.target.value)} placeholder="e.g. CVE-2025-12345, CVE-2025-12346" />
                                            </div>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Workaround</label>
                                                <TextArea rows={2} value={formWorkaround} onChange={e => setFormWorkaround(e.target.value)} placeholder="Temporary workaround until fix is applied" />
                                            </div>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Linked Incident</label>
                                                <Select
                                                    style={{ width: '100%' }}
                                                    value={formIncidentId}
                                                    onChange={setFormIncidentId}
                                                    placeholder="Link to an incident (optional)"
                                                    allowClear
                                                    showSearch
                                                    optionFilterProp="label"
                                                    options={incidents.map(i => ({ value: i.id, label: `${i.incident_code || ''} - ${i.title}` }))}
                                                />
                                            </div>
                                        </div>
                                    </Modal>
                                </div>
                            )
                        }
                    ]}
                />
            </div>
        </div>
    );
};

export default SecurityAdvisoriesPage;
