import { Select, Table, notification, Tag, Modal, Tabs, Card, Progress, Row, Col, Input, Empty, Button, Spin, DatePicker, Segmented, Tooltip, Collapse, Space, InputNumber, Checkbox } from "antd";
import type { FilterDropdownProps } from 'antd/es/table/interface';
import Sidebar from "../components/Sidebar.tsx";
import { PlusOutlined, EditOutlined, DashboardOutlined, WarningOutlined, ExclamationCircleOutlined, InfoCircleOutlined, CheckCircleOutlined, AlertOutlined, SearchOutlined, ThunderboltOutlined, DeleteOutlined, UnorderedListOutlined, AppstoreOutlined, LinkOutlined, SyncOutlined, BugOutlined, GlobalOutlined, ToolOutlined, AuditOutlined, ClockCircleOutlined, SafetyOutlined } from '@ant-design/icons';
import useIncidentStore from "../store/useIncidentStore.ts";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import useRiskStore from "../store/useRiskStore.ts";
import useAssetStore from "../store/useAssetStore.ts";
import useEUVDStore from "../store/useEUVDStore.ts";
import type { EUVDVulnerability } from "../store/useEUVDStore.ts";
import { useEffect, useState, useMemo } from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import { IncidentsInfo } from "../constants/infoContent.tsx";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { StatCard, DashboardSection } from "../components/dashboard";
import dayjs from "dayjs";

const { TextArea } = Input;

// Status color mapping
const getStatusColor = (status: string | null): string => {
    switch ((status || '').toLowerCase()) {
        case 'open': return '#cf1322';
        case 'investigating': return '#d48806';
        case 'contained': return '#1890ff';
        case 'resolved': return '#389e0d';
        case 'closed': return '#8c8c8c';
        default: return '#8c8c8c';
    }
};

const getSeverityColor = (severity: string | null): string => {
    switch ((severity || '').toLowerCase()) {
        case 'critical': return '#cf1322';
        case 'high': return '#fa541c';
        case 'medium': return '#d48806';
        case 'low': return '#389e0d';
        default: return '#8c8c8c';
    }
};

const IncidentRegistrationPage = () => {
    // Menu highlighting
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Tab state
    const [activeTab, setActiveTab] = useState<string>('dashboard');

    // View mode state
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
    const [searchText, setSearchText] = useState('');

    // Store access
    const {
        incidents,
        incidentStatuses,
        riskSeverities,
        linkedFrameworks,
        linkedRisks,
        linkedAssets,
        analyzing,
        error,
        fetchIncidents,
        fetchIncidentStatuses,
        fetchRiskSeverities,
        createIncident,
        updateIncident,
        deleteIncident,
        analyzeIncident,
        fetchLinkedFrameworks,
        linkFramework,
        unlinkFramework,
        fetchLinkedRisks,
        linkRisk,
        unlinkRisk,
        fetchLinkedAssets,
        linkAsset,
        unlinkAsset,
        patches,
        enisaNotification,
        postMarketMetrics,
        metricsLoading,
        fetchPatches,
        createPatch,
        updatePatch,
        deletePatch,
        fetchENISANotification,
        createENISANotification,
        updateENISANotification,
        fetchPostMarketMetrics
    } = useIncidentStore();

    const { frameworks, fetchFrameworks } = useFrameworksStore();
    const { risks, fetchRisks } = useRiskStore();
    const { assets, fetchAssets } = useAssetStore();

    // EUVD store
    const {
        exploitedVulns, exploitedTotal,
        criticalVulns, criticalTotal,
        latestVulns, latestTotal,
        searchResults, searchTotal,
        stats: euvdStats,
        loading: euvdLoading,
        searching: euvdSearching,
        syncing: euvdSyncing,
        fetchExploited, fetchCritical, fetchLatest,
        searchVulns, triggerSync, deleteByDateRange, deleteAll, fetchStats, fetchSyncStatus
    } = useEUVDStore();

    // Notification API
    const [api, contextHolder] = notification.useNotification();

    // Selected incident
    const [selectedIncident, setSelectedIncident] = useState<string | null>(null);
    const [showForm, setShowForm] = useState(false);

    // Form state
    const [incidentCode, setIncidentCode] = useState('');
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [severityId, setSeverityId] = useState<string | undefined>(undefined);
    const [statusId, setStatusId] = useState<string | undefined>(undefined);
    const [reportedBy, setReportedBy] = useState('');
    const [assignedTo, setAssignedTo] = useState('');
    const [discoveredAt, setDiscoveredAt] = useState<dayjs.Dayjs | null>(null);
    const [resolvedAt, setResolvedAt] = useState<dayjs.Dayjs | null>(null);
    const [containmentActions, setContainmentActions] = useState('');
    const [rootCause, setRootCause] = useState('');
    const [remediationSteps, setRemediationSteps] = useState('');

    // Vulnerability triage form state
    const [vulnerabilitySource, setVulnerabilitySource] = useState<string | undefined>(undefined);
    const [cveId, setCveId] = useState('');
    const [cweId, setCweId] = useState('');
    const [cvssScore, setCvssScore] = useState<number | null>(null);
    const [triageStatus, setTriageStatus] = useState<string | undefined>(undefined);
    const [affectedProducts, setAffectedProducts] = useState('');
    const [showTriageFields, setShowTriageFields] = useState(false);

    // Post-market state
    const [selectedPatchIncident, setSelectedPatchIncident] = useState<string | undefined>(undefined);
    const [showPatchModal, setShowPatchModal] = useState(false);
    const [selectedPatch, setSelectedPatch] = useState<string | null>(null);
    const [patchVersion, setPatchVersion] = useState('');
    const [patchDescription, setPatchDescription] = useState('');
    const [patchReleaseDate, setPatchReleaseDate] = useState<dayjs.Dayjs | null>(null);
    const [patchResolutionDate, setPatchResolutionDate] = useState<dayjs.Dayjs | null>(null);

    const [selectedEnisaIncident, setSelectedEnisaIncident] = useState<string | undefined>(undefined);

    // AI Analysis state
    const [selectedAnalysisIncident, setSelectedAnalysisIncident] = useState<string | undefined>(undefined);

    // Connection state
    const [selectedConnectionIncident, setSelectedConnectionIncident] = useState<string | undefined>(undefined);
    const [linkFrameworkId, setLinkFrameworkId] = useState<string | undefined>(undefined);
    const [linkRiskId, setLinkRiskId] = useState<string | undefined>(undefined);
    const [linkAssetId, setLinkAssetId] = useState<string | undefined>(undefined);

    // Severe incidents state
    const [severeSearchText, setSevereSearchText] = useState('');

    // EUVD state
    const [euvdMode, setEuvdMode] = useState<string>('Exploited');
    const [euvdSearchText, setEuvdSearchText] = useState('');
    const [euvdSearchProduct, setEuvdSearchProduct] = useState('');
    const [euvdSearchVendor, setEuvdSearchVendor] = useState('');
    const [lastSyncTime, setLastSyncTime] = useState<string | null>(null);
    const [euvdDateRange, setEuvdDateRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);
    const [euvdDeleting, setEuvdDeleting] = useState(false);
    const [syncProgress, setSyncProgress] = useState<{ active: boolean; percent: number; status: string }>({ active: false, percent: 0, status: '' });

    // Fetch data on mount
    useEffect(() => {
        const fetchData = async () => {
            await fetchIncidentStatuses();
            await fetchRiskSeverities();
            await fetchIncidents();
            await fetchFrameworks();
            await fetchRisks();
            await fetchAssets();
        };
        fetchData();
    }, []);

    // Fetch linked data when connection incident changes
    useEffect(() => {
        if (selectedConnectionIncident) {
            fetchLinkedFrameworks(selectedConnectionIncident);
            fetchLinkedRisks(selectedConnectionIncident);
            fetchLinkedAssets(selectedConnectionIncident);
        }
    }, [selectedConnectionIncident]);

    // Fetch post-market metrics when tab is selected
    useEffect(() => {
        if (activeTab === 'post-market') {
            fetchPostMarketMetrics();
        }
    }, [activeTab]);

    // Dashboard stats
    const stats = useMemo(() => {
        const total = incidents.length;
        const critical = incidents.filter(i => (i.incident_severity || '').toLowerCase() === 'critical').length;
        const high = incidents.filter(i => (i.incident_severity || '').toLowerCase() === 'high').length;
        const open = incidents.filter(i => (i.incident_status || '').toLowerCase() === 'open').length;
        const investigating = incidents.filter(i => (i.incident_status || '').toLowerCase() === 'investigating').length;
        const contained = incidents.filter(i => (i.incident_status || '').toLowerCase() === 'contained').length;
        const resolved = incidents.filter(i => (i.incident_status || '').toLowerCase() === 'resolved').length;
        const closed = incidents.filter(i => (i.incident_status || '').toLowerCase() === 'closed').length;
        return { total, critical, high, open, investigating, contained, resolved, closed };
    }, [incidents]);

    // Fetch EUVD data when Active Exploits tab is selected
    useEffect(() => {
        if (activeTab === 'exploits') {
            fetchStats();
            fetchSyncStatus().then((s: any) => {
                if (s?.completed_at) setLastSyncTime(s.completed_at);
            });
            if (euvdMode === 'Exploited') fetchExploited(0, 50);
            else if (euvdMode === 'Critical') fetchCritical(0, 50);
            else fetchLatest(0, 50);
        }
    }, [activeTab, euvdMode]);

    // Severe incidents (Critical + High only)
    const severeIncidents = useMemo(() => {
        return incidents.filter(i => {
            const sev = (i.incident_severity || '').toLowerCase();
            return sev === 'critical' || sev === 'high';
        });
    }, [incidents]);

    const filteredSevereIncidents = useMemo(() => {
        if (!severeSearchText) return severeIncidents;
        const lower = severeSearchText.toLowerCase();
        return severeIncidents.filter(i =>
            (i.incident_code || '').toLowerCase().includes(lower) ||
            (i.title || '').toLowerCase().includes(lower) ||
            (i.reported_by || '').toLowerCase().includes(lower) ||
            (i.incident_severity || '').toLowerCase().includes(lower) ||
            (i.incident_status || '').toLowerCase().includes(lower)
        );
    }, [severeIncidents, severeSearchText]);

    const severeStats = useMemo(() => {
        const total = severeIncidents.length;
        const critical = severeIncidents.filter(i => (i.incident_severity || '').toLowerCase() === 'critical').length;
        const high = severeIncidents.filter(i => (i.incident_severity || '').toLowerCase() === 'high').length;
        const open = severeIncidents.filter(i => (i.incident_status || '').toLowerCase() === 'open').length;
        return { total, critical, high, open };
    }, [severeIncidents]);

    // EUVD helpers
    const getScoreColor = (score: number | null): string => {
        if (score === null || score === undefined) return '#8c8c8c';
        if (score >= 9.0) return '#cf1322';
        if (score >= 7.0) return '#fa541c';
        if (score >= 4.0) return '#d48806';
        return '#389e0d';
    };

    const currentEuvdVulns = useMemo(() => {
        if (euvdMode === 'Exploited') return exploitedVulns;
        if (euvdMode === 'Critical') return criticalVulns;
        return latestVulns;
    }, [euvdMode, exploitedVulns, criticalVulns, latestVulns]);

    const currentEuvdTotal = useMemo(() => {
        if (euvdMode === 'Exploited') return exploitedTotal;
        if (euvdMode === 'Critical') return criticalTotal;
        return latestTotal;
    }, [euvdMode, exploitedTotal, criticalTotal, latestTotal]);

    const handleEuvdSearch = () => {
        const params: Record<string, any> = { size: 20 };
        if (euvdSearchText) params.text = euvdSearchText;
        if (euvdSearchProduct) params.product = euvdSearchProduct;
        if (euvdSearchVendor) params.vendor = euvdSearchVendor;
        searchVulns(params);
    };

    const reloadEuvdData = async () => {
        await fetchStats();
        const s = await fetchSyncStatus();
        if (s?.completed_at) setLastSyncTime(s.completed_at);
        if (euvdMode === 'Exploited') fetchExploited(0, 50);
        else if (euvdMode === 'Critical') fetchCritical(0, 50);
        else fetchLatest(0, 50);
    };

    const handleRefreshSync = async () => {
        const success = await triggerSync();
        if (!success) return;

        setSyncProgress({ active: true, percent: 5, status: 'Starting sync...' });

        // Poll sync status until completed
        const poll = setInterval(async () => {
            const s = await fetchSyncStatus();
            if (!s) return;

            if (s.status === 'in_progress') {
                const processed = s.vulns_processed || 0;
                // Estimate progress (cap at 90% until complete)
                const pct = Math.min(90, 10 + processed);
                setSyncProgress({ active: true, percent: pct, status: `Processing... ${processed} vulnerabilities` });
            } else if (s.status === 'completed') {
                clearInterval(poll);
                const total = (s.vulns_added || 0) + (s.vulns_updated || 0);
                setSyncProgress({ active: true, percent: 100, status: `Done! ${s.vulns_added || 0} added, ${s.vulns_updated || 0} updated` });
                if (s.completed_at) setLastSyncTime(s.completed_at);
                await reloadEuvdData();
                setTimeout(() => setSyncProgress({ active: false, percent: 0, status: '' }), 3000);
            } else if (s.status === 'failed') {
                clearInterval(poll);
                setSyncProgress({ active: true, percent: 100, status: `Failed: ${s.error_message || 'Unknown error'}` });
                setTimeout(() => setSyncProgress({ active: false, percent: 0, status: '' }), 5000);
            }
        }, 2000);

        // Safety timeout: stop polling after 2 minutes
        setTimeout(() => {
            clearInterval(poll);
            setSyncProgress(prev => prev.active ? { active: false, percent: 0, status: '' } : prev);
        }, 120000);
    };

    const handleClearAll = () => {
        Modal.confirm({
            title: 'Clear All EUVD Data',
            content: 'Are you sure you want to delete ALL cached EUVD vulnerabilities? This cannot be undone. You can re-sync afterwards.',
            okText: 'Clear All',
            okType: 'danger',
            onOk: async () => {
                setEuvdDeleting(true);
                const result = await deleteAll();
                setEuvdDeleting(false);
                if (result) {
                    api.success({ message: 'Cleared', description: `${result.deleted} vulnerabilities removed`, duration: 4 });
                    await reloadEuvdData();
                } else {
                    api.error({ message: 'Clear Failed', description: 'Failed to clear vulnerabilities', duration: 4 });
                }
            }
        });
    };

    const handleDeleteByRange = () => {
        if (!euvdDateRange || !euvdDateRange[0] || !euvdDateRange[1]) {
            api.warning({ message: 'Select Date Range', description: 'Please select a From and To date to delete', duration: 4 });
            return;
        }
        const from = euvdDateRange[0].format('YYYY-MM-DD');
        const to = euvdDateRange[1].format('YYYY-MM-DD');
        Modal.confirm({
            title: 'Delete EUVD Vulnerabilities',
            content: `Are you sure you want to delete all cached vulnerabilities published between ${from} and ${to}? This cannot be undone.`,
            okText: 'Delete',
            okType: 'danger',
            onOk: async () => {
                setEuvdDeleting(true);
                const result = await deleteByDateRange(from, to);
                setEuvdDeleting(false);
                if (result) {
                    api.success({ message: 'Deleted', description: `${result.deleted} vulnerabilities removed`, duration: 4 });
                    setEuvdDateRange(null);
                    await reloadEuvdData();
                } else {
                    api.error({ message: 'Delete Failed', description: 'Failed to delete vulnerabilities', duration: 4 });
                }
            }
        });
    };

    // Unique assigners for filter presets
    const uniqueAssigners = useMemo(() => {
        const assigners = new Set<string>();
        currentEuvdVulns.forEach(v => { if (v.assigner) assigners.add(v.assigner); });
        return Array.from(assigners).sort().map(a => ({ text: a, value: a }));
    }, [currentEuvdVulns]);

    // EUVD table columns
    const euvdColumns = [
        {
            title: 'EUVD ID',
            dataIndex: 'euvd_id',
            key: 'euvd_id',
            width: 160,
            filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: FilterDropdownProps) => (
                <div style={{ padding: 8 }}>
                    <Input
                        placeholder="Search EUVD ID"
                        value={selectedKeys[0]}
                        onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
                        onPressEnter={() => confirm()}
                        style={{ marginBottom: 8, display: 'block' }}
                    />
                    <Space>
                        <Button type="primary" onClick={() => confirm()} icon={<SearchOutlined />} size="small" style={{ width: 90 }}>Search</Button>
                        <Button onClick={() => clearFilters && clearFilters()} size="small" style={{ width: 90 }}>Reset</Button>
                    </Space>
                </div>
            ),
            filterIcon: (filtered: boolean) => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
            onFilter: (value: any, record: EUVDVulnerability) => (record.euvd_id || '').toLowerCase().includes(value.toString().toLowerCase()),
            render: (text: string) => <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{text}</span>,
        },
        {
            title: 'Description',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true,
            filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: FilterDropdownProps) => (
                <div style={{ padding: 8 }}>
                    <Input
                        placeholder="Search description"
                        value={selectedKeys[0]}
                        onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
                        onPressEnter={() => confirm()}
                        style={{ marginBottom: 8, display: 'block' }}
                    />
                    <Space>
                        <Button type="primary" onClick={() => confirm()} icon={<SearchOutlined />} size="small" style={{ width: 90 }}>Search</Button>
                        <Button onClick={() => clearFilters && clearFilters()} size="small" style={{ width: 90 }}>Reset</Button>
                    </Space>
                </div>
            ),
            filterIcon: (filtered: boolean) => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
            onFilter: (value: any, record: EUVDVulnerability) => (record.description || '').toLowerCase().includes(value.toString().toLowerCase()),
            render: (text: string) => <span style={{ fontSize: 12 }}>{text || '-'}</span>,
        },
        {
            title: 'Score',
            dataIndex: 'base_score',
            key: 'base_score',
            width: 90,
            filters: [
                { text: 'Critical (≥9.0)', value: 'critical' },
                { text: 'High (7.0-8.9)', value: 'high' },
                { text: 'Medium (4.0-6.9)', value: 'medium' },
                { text: 'Low (<4.0)', value: 'low' },
            ],
            onFilter: (value: any, record: EUVDVulnerability) => {
                const s = record.base_score;
                if (s === null || s === undefined) return false;
                if (value === 'critical') return s >= 9.0;
                if (value === 'high') return s >= 7.0 && s < 9.0;
                if (value === 'medium') return s >= 4.0 && s < 7.0;
                if (value === 'low') return s < 4.0;
                return false;
            },
            sorter: (a: EUVDVulnerability, b: EUVDVulnerability) => (a.base_score || 0) - (b.base_score || 0),
            render: (score: number | null) => score !== null && score !== undefined
                ? <Tag color={getScoreColor(score)} style={{ fontWeight: 600 }}>{score.toFixed(1)}</Tag>
                : '-',
        },
        {
            title: 'EPSS',
            dataIndex: 'epss',
            key: 'epss',
            width: 80,
            render: (val: number | null) => val !== null && val !== undefined
                ? `${(val * 100).toFixed(1)}%`
                : '-',
        },
        {
            title: 'Assigner',
            dataIndex: 'assigner',
            key: 'assigner',
            width: 140,
            ellipsis: true,
            filters: uniqueAssigners,
            onFilter: (value: any, record: EUVDVulnerability) => record.assigner === value,
        },
        {
            title: 'Published',
            dataIndex: 'date_published',
            key: 'date_published',
            width: 140,
            filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: FilterDropdownProps) => {
                const rangeStr = selectedKeys[0] as string | undefined;
                const parts = rangeStr ? rangeStr.split(',') : [];
                const rangeVal = parts.length === 2 ? [dayjs(parts[0]), dayjs(parts[1])] as [dayjs.Dayjs, dayjs.Dayjs] : null;
                return (
                    <div style={{ padding: 8 }}>
                        <DatePicker.RangePicker
                            value={rangeVal}
                            onChange={(dates) => {
                                if (dates && dates[0] && dates[1]) {
                                    setSelectedKeys([`${dates[0].format('YYYY-MM-DD')},${dates[1].format('YYYY-MM-DD')}`]);
                                } else {
                                    setSelectedKeys([]);
                                }
                            }}
                            style={{ marginBottom: 8, display: 'block' }}
                        />
                        <Space>
                            <Button type="primary" onClick={() => confirm()} icon={<SearchOutlined />} size="small" style={{ width: 90 }}>Filter</Button>
                            <Button onClick={() => { clearFilters && clearFilters(); confirm(); }} size="small" style={{ width: 90 }}>Reset</Button>
                        </Space>
                    </div>
                );
            },
            filterIcon: (filtered: boolean) => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
            onFilter: (value: any, record: EUVDVulnerability) => {
                if (!record.date_published) return false;
                const parts = String(value).split(',');
                if (parts.length !== 2) return true;
                const d = dayjs(record.date_published).format('YYYY-MM-DD');
                return d >= parts[0] && d <= parts[1];
            },
            render: (text: string) => text ? dayjs(text).format('YYYY-MM-DD') : '-',
            sorter: (a: EUVDVulnerability, b: EUVDVulnerability) => (a.date_published || '').localeCompare(b.date_published || ''),
            defaultSortOrder: 'descend' as const,
        },
        {
            title: 'Updated',
            dataIndex: 'date_updated',
            key: 'date_updated',
            width: 140,
            filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: FilterDropdownProps) => {
                const rangeStr = selectedKeys[0] as string | undefined;
                const parts = rangeStr ? rangeStr.split(',') : [];
                const rangeVal = parts.length === 2 ? [dayjs(parts[0]), dayjs(parts[1])] as [dayjs.Dayjs, dayjs.Dayjs] : null;
                return (
                    <div style={{ padding: 8 }}>
                        <DatePicker.RangePicker
                            value={rangeVal}
                            onChange={(dates) => {
                                if (dates && dates[0] && dates[1]) {
                                    setSelectedKeys([`${dates[0].format('YYYY-MM-DD')},${dates[1].format('YYYY-MM-DD')}`]);
                                } else {
                                    setSelectedKeys([]);
                                }
                            }}
                            style={{ marginBottom: 8, display: 'block' }}
                        />
                        <Space>
                            <Button type="primary" onClick={() => confirm()} icon={<SearchOutlined />} size="small" style={{ width: 90 }}>Filter</Button>
                            <Button onClick={() => { clearFilters && clearFilters(); confirm(); }} size="small" style={{ width: 90 }}>Reset</Button>
                        </Space>
                    </div>
                );
            },
            filterIcon: (filtered: boolean) => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
            onFilter: (value: any, record: EUVDVulnerability) => {
                if (!record.date_updated) return false;
                const parts = String(value).split(',');
                if (parts.length !== 2) return true;
                const d = dayjs(record.date_updated).format('YYYY-MM-DD');
                return d >= parts[0] && d <= parts[1];
            },
            render: (text: string) => text ? dayjs(text).format('YYYY-MM-DD') : '-',
            sorter: (a: EUVDVulnerability, b: EUVDVulnerability) => (a.date_updated || '').localeCompare(b.date_updated || ''),
        },
        {
            title: 'Aliases',
            dataIndex: 'aliases',
            key: 'aliases',
            width: 140,
            ellipsis: true,
            filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }: FilterDropdownProps) => (
                <div style={{ padding: 8 }}>
                    <Input
                        placeholder="Search aliases"
                        value={selectedKeys[0]}
                        onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
                        onPressEnter={() => confirm()}
                        style={{ marginBottom: 8, display: 'block' }}
                    />
                    <Space>
                        <Button type="primary" onClick={() => confirm()} icon={<SearchOutlined />} size="small" style={{ width: 90 }}>Search</Button>
                        <Button onClick={() => clearFilters && clearFilters()} size="small" style={{ width: 90 }}>Reset</Button>
                    </Space>
                </div>
            ),
            filterIcon: (filtered: boolean) => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
            onFilter: (value: any, record: EUVDVulnerability) => (record.aliases || '').toLowerCase().includes(value.toString().toLowerCase()),
            render: (text: string) => {
                if (!text) return '-';
                const first = text.split('\n')[0];
                const count = text.split('\n').length;
                return count > 1 ? <Tooltip title={text.split('\n').join(', ')}>{first} +{count - 1}</Tooltip> : first;
            },
        }
    ];

    // Filtered incidents for search
    const filteredIncidents = useMemo(() => {
        if (!searchText) return incidents;
        const lower = searchText.toLowerCase();
        return incidents.filter(i =>
            (i.incident_code || '').toLowerCase().includes(lower) ||
            (i.title || '').toLowerCase().includes(lower) ||
            (i.reported_by || '').toLowerCase().includes(lower) ||
            (i.incident_severity || '').toLowerCase().includes(lower) ||
            (i.incident_status || '').toLowerCase().includes(lower)
        );
    }, [incidents, searchText]);

    // Table columns
    const columns = [
        {
            title: 'Code',
            dataIndex: 'incident_code',
            key: 'incident_code',
            width: 100,
            sorter: (a: any, b: any) => (a.incident_code || '').localeCompare(b.incident_code || ''),
        },
        {
            title: 'Title',
            dataIndex: 'title',
            key: 'title',
            ellipsis: true,
            sorter: (a: any, b: any) => (a.title || '').localeCompare(b.title || ''),
        },
        {
            title: 'Severity',
            dataIndex: 'incident_severity',
            key: 'incident_severity',
            width: 110,
            filters: riskSeverities.map(s => ({ text: s.risk_severity_name, value: s.risk_severity_name })),
            onFilter: (value: any, record: any) => record.incident_severity === value,
            render: (text: string) => text ? <Tag color={getSeverityColor(text)}>{text}</Tag> : '-',
        },
        {
            title: 'Status',
            dataIndex: 'incident_status',
            key: 'incident_status',
            width: 130,
            filters: incidentStatuses.map(s => ({ text: s.incident_status_name, value: s.incident_status_name })),
            onFilter: (value: any, record: any) => record.incident_status === value,
            render: (text: string) => text ? <Tag color={getStatusColor(text)}>{text}</Tag> : '-',
        },
        {
            title: 'Reported By',
            dataIndex: 'reported_by',
            key: 'reported_by',
            width: 150,
            ellipsis: true,
        },
        {
            title: 'Discovered',
            dataIndex: 'discovered_at',
            key: 'discovered_at',
            width: 120,
            render: (text: string) => text ? dayjs(text).format('YYYY-MM-DD') : '-',
            sorter: (a: any, b: any) => (a.discovered_at || '').localeCompare(b.discovered_at || ''),
        },
        {
            title: 'Links',
            key: 'links',
            width: 100,
            render: (_: any, record: any) => {
                const total = (record.linked_frameworks_count || 0) + (record.linked_risks_count || 0) + (record.linked_assets_count || 0);
                return total > 0 ? <Tag icon={<LinkOutlined />}>{total}</Tag> : '-';
            }
        },
        {
            title: 'Updated',
            dataIndex: 'updated_at',
            key: 'updated_at',
            width: 120,
            render: (text: string) => text ? dayjs(text).format('YYYY-MM-DD') : '-',
            sorter: (a: any, b: any) => (a.updated_at || '').localeCompare(b.updated_at || ''),
            defaultSortOrder: 'descend' as const,
        }
    ];

    // Handle row click - open form for editing
    const handleRowClick = (record: any) => {
        setSelectedIncident(record.id);
        setIncidentCode(record.incident_code || '');
        setTitle(record.title || '');
        setDescription(record.description || '');
        setSeverityId(record.incident_severity_id);
        setStatusId(record.incident_status_id);
        setReportedBy(record.reported_by || '');
        setAssignedTo(record.assigned_to || '');
        setDiscoveredAt(record.discovered_at ? dayjs(record.discovered_at) : null);
        setResolvedAt(record.resolved_at ? dayjs(record.resolved_at) : null);
        setContainmentActions(record.containment_actions || '');
        setRootCause(record.root_cause || '');
        setRemediationSteps(record.remediation_steps || '');
        setVulnerabilitySource(record.vulnerability_source || undefined);
        setCveId(record.cve_id || '');
        setCweId(record.cwe_id || '');
        setCvssScore(record.cvss_score ?? null);
        setTriageStatus(record.triage_status || undefined);
        setAffectedProducts(record.affected_products || '');
        setShowTriageFields(!!(record.vulnerability_source || record.cve_id || record.triage_status));
        setShowForm(true);
    };

    // Clear form
    const handleClear = (hideForm = false) => {
        setSelectedIncident(null);
        setIncidentCode('');
        setTitle('');
        setDescription('');
        setSeverityId(undefined);
        setStatusId(undefined);
        setReportedBy('');
        setAssignedTo('');
        setDiscoveredAt(null);
        setResolvedAt(null);
        setContainmentActions('');
        setRootCause('');
        setRemediationSteps('');
        setVulnerabilitySource(undefined);
        setCveId('');
        setCweId('');
        setCvssScore(null);
        setTriageStatus(undefined);
        setAffectedProducts('');
        setShowTriageFields(false);
        if (hideForm) setShowForm(false);
    };

    // Save incident
    const handleSave = async () => {
        if (!title.trim() || !severityId || !statusId) {
            api.error({
                message: 'Validation Error',
                description: 'Please fill in all required fields (Title, Severity, Status)',
                duration: 4,
            });
            return;
        }

        const payload = {
            incident_code: incidentCode || undefined,
            title: title.trim(),
            description: description || undefined,
            incident_severity_id: severityId,
            incident_status_id: statusId,
            reported_by: reportedBy || undefined,
            assigned_to: assignedTo || undefined,
            discovered_at: discoveredAt ? discoveredAt.toISOString() : undefined,
            resolved_at: resolvedAt ? resolvedAt.toISOString() : undefined,
            containment_actions: containmentActions || undefined,
            root_cause: rootCause || undefined,
            remediation_steps: remediationSteps || undefined,
            vulnerability_source: vulnerabilitySource || undefined,
            cve_id: cveId || undefined,
            cwe_id: cweId || undefined,
            cvss_score: cvssScore ?? undefined,
            triage_status: triageStatus || undefined,
            affected_products: affectedProducts || undefined,
        };

        const isUpdate = selectedIncident !== null;
        let success;

        try {
            if (isUpdate && selectedIncident) {
                success = await updateIncident(selectedIncident, { id: selectedIncident, ...payload } as any);
            } else {
                success = await createIncident(payload as any);
            }

            if (success) {
                api.success({
                    message: isUpdate ? 'Incident Updated' : 'Incident Created',
                    description: isUpdate ? 'Incident updated successfully' : 'Incident created successfully',
                    duration: 4,
                });
                handleClear(true);
                await fetchIncidents();
            } else {
                api.error({
                    message: isUpdate ? 'Update Failed' : 'Creation Failed',
                    description: error || 'An error occurred',
                    duration: 4,
                });
            }
        } catch (err) {
            api.error({
                message: 'Error',
                description: 'An unexpected error occurred',
                duration: 4,
            });
        }
    };

    // Delete incident
    const handleDelete = async () => {
        if (!selectedIncident) return;

        Modal.confirm({
            title: 'Delete Incident',
            content: 'Are you sure you want to delete this incident? This action cannot be undone.',
            okText: 'Delete',
            okType: 'danger',
            onOk: async () => {
                const success = await deleteIncident(selectedIncident);
                if (success) {
                    api.success({ message: 'Incident Deleted', description: 'Incident deleted successfully', duration: 4 });
                    handleClear(true);
                    await fetchIncidents();
                } else {
                    api.error({ message: 'Delete Failed', description: error || 'Failed to delete incident', duration: 4 });
                }
            }
        });
    };

    // AI Analysis
    const handleAnalyze = async () => {
        if (!selectedAnalysisIncident) {
            api.warning({ message: 'Select Incident', description: 'Please select an incident to analyze', duration: 4 });
            return;
        }
        const result = await analyzeIncident(selectedAnalysisIncident);
        if (result) {
            api.success({ message: 'Analysis Complete', description: 'AI analysis has been generated', duration: 4 });
        } else {
            api.error({ message: 'Analysis Failed', description: 'Failed to generate AI analysis', duration: 4 });
        }
    };

    const selectedAnalysisData = useMemo(() => {
        return incidents.find(i => i.id === selectedAnalysisIncident);
    }, [incidents, selectedAnalysisIncident]);

    // Parse AI analysis JSON
    const parsedAnalysis = useMemo(() => {
        if (!selectedAnalysisData?.ai_analysis) return null;
        try {
            return JSON.parse(selectedAnalysisData.ai_analysis);
        } catch {
            return { raw: selectedAnalysisData.ai_analysis };
        }
    }, [selectedAnalysisData]);

    // Connection handlers
    const handleLinkFramework = async () => {
        if (!selectedConnectionIncident || !linkFrameworkId) return;
        const success = await linkFramework(selectedConnectionIncident, linkFrameworkId);
        if (success) {
            await fetchLinkedFrameworks(selectedConnectionIncident);
            setLinkFrameworkId(undefined);
            api.success({ message: 'Framework Linked', duration: 3 });
        }
    };

    const handleUnlinkFramework = async (frameworkId: string) => {
        if (!selectedConnectionIncident) return;
        const success = await unlinkFramework(selectedConnectionIncident, frameworkId);
        if (success) {
            await fetchLinkedFrameworks(selectedConnectionIncident);
            api.success({ message: 'Framework Unlinked', duration: 3 });
        }
    };

    const handleLinkRisk = async () => {
        if (!selectedConnectionIncident || !linkRiskId) return;
        const success = await linkRisk(selectedConnectionIncident, linkRiskId);
        if (success) {
            await fetchLinkedRisks(selectedConnectionIncident);
            setLinkRiskId(undefined);
            api.success({ message: 'Risk Linked', duration: 3 });
        }
    };

    const handleUnlinkRisk = async (riskId: string) => {
        if (!selectedConnectionIncident) return;
        const success = await unlinkRisk(selectedConnectionIncident, riskId);
        if (success) {
            await fetchLinkedRisks(selectedConnectionIncident);
            api.success({ message: 'Risk Unlinked', duration: 3 });
        }
    };

    const handleLinkAsset = async () => {
        if (!selectedConnectionIncident || !linkAssetId) return;
        const success = await linkAsset(selectedConnectionIncident, linkAssetId);
        if (success) {
            await fetchLinkedAssets(selectedConnectionIncident);
            setLinkAssetId(undefined);
            api.success({ message: 'Asset Linked', duration: 3 });
        }
    };

    const handleUnlinkAsset = async (assetId: string) => {
        if (!selectedConnectionIncident) return;
        const success = await unlinkAsset(selectedConnectionIncident, assetId);
        if (success) {
            await fetchLinkedAssets(selectedConnectionIncident);
            api.success({ message: 'Asset Unlinked', duration: 3 });
        }
    };

    // Severity/Status options for selects
    const severityOptions = riskSeverities.map(s => ({ label: s.risk_severity_name, value: s.id }));
    const statusOptions = incidentStatuses.map(s => ({ label: s.incident_status_name, value: s.id }));

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--page-background)' }}>
            {contextHolder}
            <Sidebar
                selectedKeys={menuHighlighting.selectedKeys}
                openKeys={menuHighlighting.openKeys}
                onOpenChange={menuHighlighting.onOpenChange}
            />
            <div style={{ flex: 1, padding: '24px', overflow: 'auto' }}>
                <InfoTitle title="Incident Registration" infoContent={IncidentsInfo} />

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
                                            <StatCard title="Total Incidents" value={stats.total} icon={<AlertOutlined />} color="#1890ff" />
                                        </Col>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="Critical" value={stats.critical} icon={<ExclamationCircleOutlined />} color="#cf1322" />
                                        </Col>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="High" value={stats.high} icon={<WarningOutlined />} color="#fa541c" />
                                        </Col>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="Open" value={stats.open} icon={<InfoCircleOutlined />} color="#d48806" />
                                        </Col>
                                    </Row>

                                    <DashboardSection title="Status Distribution" style={{ marginTop: 24 }}>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                            {[
                                                { label: 'Open', count: stats.open, color: '#cf1322' },
                                                { label: 'Investigating', count: stats.investigating, color: '#d48806' },
                                                { label: 'Contained', count: stats.contained, color: '#1890ff' },
                                                { label: 'Resolved', count: stats.resolved, color: '#389e0d' },
                                                { label: 'Closed', count: stats.closed, color: '#8c8c8c' },
                                            ].map(item => (
                                                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                                    <span style={{ width: 100, fontSize: 13 }}>{item.label}</span>
                                                    <Progress
                                                        percent={stats.total > 0 ? Math.round((item.count / stats.total) * 100) : 0}
                                                        strokeColor={item.color}
                                                        format={() => `${item.count}`}
                                                        style={{ flex: 1 }}
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                    </DashboardSection>
                                </div>
                            )
                        },
                        {
                            key: 'registry',
                            label: <span><EditOutlined /> Incident Registry</span>,
                            children: (
                                <div>
                                    {/* Toolbar */}
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                                            <Input
                                                placeholder="Search incidents..."
                                                prefix={<SearchOutlined />}
                                                value={searchText}
                                                onChange={e => setSearchText(e.target.value)}
                                                style={{ width: 280 }}
                                                allowClear
                                            />
                                            <Button
                                                icon={viewMode === 'list' ? <AppstoreOutlined /> : <UnorderedListOutlined />}
                                                onClick={() => setViewMode(viewMode === 'list' ? 'grid' : 'list')}
                                            />
                                        </div>
                                        <Button
                                            type="primary"
                                            icon={<PlusOutlined />}
                                            onClick={() => { handleClear(); setShowForm(true); }}
                                        >
                                            New Incident
                                        </Button>
                                    </div>

                                    {/* Grid or List view */}
                                    {viewMode === 'list' ? (
                                        <Table
                                            dataSource={filteredIncidents}
                                            columns={columns}
                                            rowKey="id"
                                            size="small"
                                            pagination={{ pageSize: 15, showSizeChanger: true }}
                                            onRow={(record) => ({
                                                onClick: () => handleRowClick(record),
                                                style: { cursor: 'pointer' }
                                            })}
                                            style={{ cursor: 'pointer' }}
                                        />
                                    ) : (
                                        <Row gutter={[16, 16]}>
                                            {filteredIncidents.length === 0 ? (
                                                <Col span={24}><Empty description="No incidents found" /></Col>
                                            ) : (
                                                filteredIncidents.map(incident => (
                                                    <Col xs={24} sm={12} md={8} lg={6} key={incident.id}>
                                                        <Card
                                                            hoverable
                                                            size="small"
                                                            onClick={() => handleRowClick(incident)}
                                                            title={<span style={{ fontSize: 13 }}>{incident.incident_code}</span>}
                                                            extra={<Tag color={getSeverityColor(incident.incident_severity)}>{incident.incident_severity}</Tag>}
                                                        >
                                                            <p style={{ fontSize: 13, marginBottom: 8, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{incident.title}</p>
                                                            <Tag color={getStatusColor(incident.incident_status)}>{incident.incident_status}</Tag>
                                                        </Card>
                                                    </Col>
                                                ))
                                            )}
                                        </Row>
                                    )}

                                    {/* Registration Modal */}
                                    <Modal
                                        title={selectedIncident ? 'Edit Incident' : 'New Incident'}
                                        open={showForm}
                                        onCancel={() => handleClear(true)}
                                        width={720}
                                        footer={
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <div>
                                                    {selectedIncident && (
                                                        <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>Delete</Button>
                                                    )}
                                                </div>
                                                <div style={{ display: 'flex', gap: 8 }}>
                                                    {selectedIncident && (
                                                        <Button icon={<PlusOutlined />} onClick={() => handleClear()}>Create New</Button>
                                                    )}
                                                    <Button onClick={() => handleClear(true)}>Cancel</Button>
                                                    <Button type="primary" onClick={handleSave}>
                                                        {selectedIncident ? 'Save Changes' : 'Create Incident'}
                                                    </Button>
                                                </div>
                                            </div>
                                        }
                                    >
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                            <Row gutter={16}>
                                                <Col span={8}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Code (auto-generated)</label>
                                                    <Input value={incidentCode} onChange={e => setIncidentCode(e.target.value)} placeholder="INC-1" />
                                                </Col>
                                                <Col span={16}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Title <span style={{ color: '#cf1322' }}>*</span></label>
                                                    <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="Incident title" />
                                                </Col>
                                            </Row>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Description</label>
                                                <TextArea rows={2} value={description} onChange={e => setDescription(e.target.value)} placeholder="Describe the incident" />
                                            </div>
                                            <Row gutter={16}>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Severity <span style={{ color: '#cf1322' }}>*</span></label>
                                                    <Select
                                                        style={{ width: '100%' }}
                                                        value={severityId}
                                                        onChange={setSeverityId}
                                                        options={severityOptions}
                                                        placeholder="Select severity"
                                                    />
                                                </Col>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Status <span style={{ color: '#cf1322' }}>*</span></label>
                                                    <Select
                                                        style={{ width: '100%' }}
                                                        value={statusId}
                                                        onChange={setStatusId}
                                                        options={statusOptions}
                                                        placeholder="Select status"
                                                    />
                                                </Col>
                                            </Row>
                                            <Row gutter={16}>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Reported By</label>
                                                    <Input value={reportedBy} onChange={e => setReportedBy(e.target.value)} placeholder="Name or email" />
                                                </Col>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Assigned To</label>
                                                    <Input value={assignedTo} onChange={e => setAssignedTo(e.target.value)} placeholder="Name or email" />
                                                </Col>
                                            </Row>
                                            <Row gutter={16}>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Discovered At</label>
                                                    <DatePicker style={{ width: '100%' }} value={discoveredAt} onChange={setDiscoveredAt} showTime />
                                                </Col>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Resolved At</label>
                                                    <DatePicker style={{ width: '100%' }} value={resolvedAt} onChange={setResolvedAt} showTime />
                                                </Col>
                                            </Row>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Containment Actions</label>
                                                <TextArea rows={2} value={containmentActions} onChange={e => setContainmentActions(e.target.value)} placeholder="Actions taken to contain the incident" />
                                            </div>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Root Cause</label>
                                                <TextArea rows={2} value={rootCause} onChange={e => setRootCause(e.target.value)} placeholder="Root cause analysis" />
                                            </div>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Remediation Steps</label>
                                                <TextArea rows={2} value={remediationSteps} onChange={e => setRemediationSteps(e.target.value)} placeholder="Steps to remediate" />
                                            </div>

                                            {/* Vulnerability Triage Section */}
                                            <Collapse
                                                activeKey={showTriageFields ? ['triage'] : []}
                                                onChange={(keys) => setShowTriageFields(keys.includes('triage'))}
                                                size="small"
                                                items={[{
                                                    key: 'triage',
                                                    label: <span><BugOutlined /> Vulnerability Triage</span>,
                                                    children: (
                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                                            <Row gutter={16}>
                                                                <Col span={12}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Vulnerability Source</label>
                                                                    <Select
                                                                        style={{ width: '100%' }}
                                                                        value={vulnerabilitySource}
                                                                        onChange={setVulnerabilitySource}
                                                                        placeholder="Select source"
                                                                        allowClear
                                                                        options={[
                                                                            { value: 'euvd', label: 'EUVD' },
                                                                            { value: 'internal_scan', label: 'Internal Scan' },
                                                                            { value: 'external_report', label: 'External Report' },
                                                                            { value: 'user_report', label: 'User Report' },
                                                                        ]}
                                                                    />
                                                                </Col>
                                                                <Col span={12}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Triage Status</label>
                                                                    <Select
                                                                        style={{ width: '100%' }}
                                                                        value={triageStatus}
                                                                        onChange={setTriageStatus}
                                                                        placeholder="Select triage status"
                                                                        allowClear
                                                                        options={[
                                                                            { value: 'New', label: 'New' },
                                                                            { value: 'Triaged', label: 'Triaged' },
                                                                            { value: 'In Progress', label: 'In Progress' },
                                                                            { value: 'Fixed', label: 'Fixed' },
                                                                            { value: 'Verified', label: 'Verified' },
                                                                            { value: 'Closed', label: 'Closed' },
                                                                        ]}
                                                                    />
                                                                </Col>
                                                            </Row>
                                                            <Row gutter={16}>
                                                                <Col span={8}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>CVE ID</label>
                                                                    <Input value={cveId} onChange={e => setCveId(e.target.value)} placeholder="CVE-2025-12345" />
                                                                </Col>
                                                                <Col span={8}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>CWE ID</label>
                                                                    <Input value={cweId} onChange={e => setCweId(e.target.value)} placeholder="CWE-79" />
                                                                </Col>
                                                                <Col span={8}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>CVSS Score</label>
                                                                    <InputNumber
                                                                        style={{ width: '100%' }}
                                                                        value={cvssScore}
                                                                        onChange={(val) => setCvssScore(val)}
                                                                        min={0} max={10} step={0.1}
                                                                        placeholder="0.0 - 10.0"
                                                                    />
                                                                </Col>
                                                            </Row>
                                                            <div>
                                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Affected Products</label>
                                                                <TextArea rows={2} value={affectedProducts} onChange={e => setAffectedProducts(e.target.value)} placeholder="List affected products, one per line" />
                                                            </div>
                                                        </div>
                                                    )
                                                }]}
                                            />
                                        </div>
                                    </Modal>
                                </div>
                            )
                        },
                        {
                            key: 'analysis',
                            label: <span><ThunderboltOutlined /> AI Analysis</span>,
                            children: (
                                <div>
                                    <Card>
                                        <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
                                            <Select
                                                style={{ flex: 1 }}
                                                placeholder="Select an incident to analyze"
                                                value={selectedAnalysisIncident}
                                                onChange={setSelectedAnalysisIncident}
                                                options={incidents.map(i => ({
                                                    label: `${i.incident_code || 'N/A'} - ${i.title}`,
                                                    value: i.id
                                                }))}
                                                showSearch
                                                filterOption={(input, option) =>
                                                    (option?.label as string || '').toLowerCase().includes(input.toLowerCase())
                                                }
                                            />
                                            <Button
                                                type="primary"
                                                icon={<ThunderboltOutlined />}
                                                onClick={handleAnalyze}
                                                loading={analyzing}
                                                disabled={!selectedAnalysisIncident}
                                            >
                                                Analyze Incident
                                            </Button>
                                        </div>

                                        {analyzing && (
                                            <div style={{ textAlign: 'center', padding: 40 }}>
                                                <Spin size="large" />
                                                <p style={{ marginTop: 16, color: '#8c8c8c' }}>Analyzing incident with AI... This may take a moment.</p>
                                            </div>
                                        )}

                                        {!analyzing && parsedAnalysis && (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                                {parsedAnalysis.raw ? (
                                                    <Card size="small" title="Analysis">
                                                        <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>{parsedAnalysis.raw}</pre>
                                                    </Card>
                                                ) : (
                                                    <>
                                                        {parsedAnalysis.summary && (
                                                            <Card size="small" title="Summary">
                                                                <p style={{ margin: 0, fontSize: 13 }}>{parsedAnalysis.summary}</p>
                                                            </Card>
                                                        )}
                                                        {parsedAnalysis.containment_steps?.length > 0 && (
                                                            <Card size="small" title="Containment Steps">
                                                                <ol style={{ margin: 0, paddingLeft: 20, fontSize: 13 }}>
                                                                    {parsedAnalysis.containment_steps.map((step: string, idx: number) => (
                                                                        <li key={idx} style={{ marginBottom: 4 }}>{step}</li>
                                                                    ))}
                                                                </ol>
                                                            </Card>
                                                        )}
                                                        {parsedAnalysis.root_cause_analysis && (
                                                            <Card size="small" title="Root Cause Analysis">
                                                                <p style={{ margin: 0, fontSize: 13 }}>{parsedAnalysis.root_cause_analysis}</p>
                                                            </Card>
                                                        )}
                                                        {parsedAnalysis.remediation_recommendations?.length > 0 && (
                                                            <Card size="small" title="Remediation Recommendations">
                                                                <ol style={{ margin: 0, paddingLeft: 20, fontSize: 13 }}>
                                                                    {parsedAnalysis.remediation_recommendations.map((rec: string, idx: number) => (
                                                                        <li key={idx} style={{ marginBottom: 4 }}>{rec}</li>
                                                                    ))}
                                                                </ol>
                                                            </Card>
                                                        )}
                                                        {parsedAnalysis.severity_assessment && (
                                                            <Card size="small" title="Severity Assessment">
                                                                <p style={{ margin: 0, fontSize: 13 }}>{parsedAnalysis.severity_assessment}</p>
                                                            </Card>
                                                        )}
                                                        {parsedAnalysis.lessons_learned?.length > 0 && (
                                                            <Card size="small" title="Lessons Learned">
                                                                <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13 }}>
                                                                    {parsedAnalysis.lessons_learned.map((lesson: string, idx: number) => (
                                                                        <li key={idx} style={{ marginBottom: 4 }}>{lesson}</li>
                                                                    ))}
                                                                </ul>
                                                            </Card>
                                                        )}
                                                    </>
                                                )}
                                            </div>
                                        )}

                                        {!analyzing && !parsedAnalysis && selectedAnalysisIncident && (
                                            <Empty description="No analysis available. Click 'Analyze Incident' to generate one." />
                                        )}

                                        {!selectedAnalysisIncident && (
                                            <Empty description="Select an incident above to view or generate AI analysis." />
                                        )}
                                    </Card>
                                </div>
                            )
                        },
                        {
                            key: 'connections',
                            label: <span><LinkOutlined /> Connections</span>,
                            children: (
                                <div>
                                    <Card>
                                        <div style={{ marginBottom: 24 }}>
                                            <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280', marginBottom: 8, display: 'block' }}>Select Incident</label>
                                            <Select
                                                style={{ width: '100%', maxWidth: 500 }}
                                                placeholder="Select an incident to manage connections"
                                                value={selectedConnectionIncident}
                                                onChange={setSelectedConnectionIncident}
                                                options={incidents.map(i => ({
                                                    label: `${i.incident_code || 'N/A'} - ${i.title}`,
                                                    value: i.id
                                                }))}
                                                showSearch
                                                filterOption={(input, option) =>
                                                    (option?.label as string || '').toLowerCase().includes(input.toLowerCase())
                                                }
                                            />
                                        </div>

                                        {selectedConnectionIncident ? (
                                            <Tabs
                                                items={[
                                                    {
                                                        key: 'frameworks',
                                                        label: `Frameworks (${linkedFrameworks.length})`,
                                                        children: (
                                                            <div>
                                                                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                                                                    <Select
                                                                        style={{ flex: 1 }}
                                                                        placeholder="Select framework to link"
                                                                        value={linkFrameworkId}
                                                                        onChange={setLinkFrameworkId}
                                                                        options={frameworks
                                                                            .filter(f => !linkedFrameworks.some(lf => lf.id === f.id))
                                                                            .map(f => ({ label: f.name, value: f.id }))}
                                                                        showSearch
                                                                        filterOption={(input, option) =>
                                                                            (option?.label as string || '').toLowerCase().includes(input.toLowerCase())
                                                                        }
                                                                    />
                                                                    <Button type="primary" onClick={handleLinkFramework} disabled={!linkFrameworkId}>Link</Button>
                                                                </div>
                                                                {linkedFrameworks.length > 0 ? (
                                                                    <Table
                                                                        dataSource={linkedFrameworks}
                                                                        rowKey="id"
                                                                        size="small"
                                                                        pagination={false}
                                                                        columns={[
                                                                            { title: 'Name', dataIndex: 'name', key: 'name' },
                                                                            { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
                                                                            {
                                                                                title: '',
                                                                                key: 'action',
                                                                                width: 80,
                                                                                render: (_: any, record: any) => (
                                                                                    <Button size="small" danger onClick={() => handleUnlinkFramework(record.id)}>Unlink</Button>
                                                                                )
                                                                            }
                                                                        ]}
                                                                    />
                                                                ) : <Empty description="No frameworks linked" />}
                                                            </div>
                                                        )
                                                    },
                                                    {
                                                        key: 'risks',
                                                        label: `Risks (${linkedRisks.length})`,
                                                        children: (
                                                            <div>
                                                                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                                                                    <Select
                                                                        style={{ flex: 1 }}
                                                                        placeholder="Select risk to link"
                                                                        value={linkRiskId}
                                                                        onChange={setLinkRiskId}
                                                                        options={risks
                                                                            .filter(r => !linkedRisks.some(lr => lr.id === r.id))
                                                                            .map(r => ({ label: `${r.risk_code || 'N/A'} - ${r.risk_category_name}`, value: r.id }))}
                                                                        showSearch
                                                                        filterOption={(input, option) =>
                                                                            (option?.label as string || '').toLowerCase().includes(input.toLowerCase())
                                                                        }
                                                                    />
                                                                    <Button type="primary" onClick={handleLinkRisk} disabled={!linkRiskId}>Link</Button>
                                                                </div>
                                                                {linkedRisks.length > 0 ? (
                                                                    <Table
                                                                        dataSource={linkedRisks}
                                                                        rowKey="id"
                                                                        size="small"
                                                                        pagination={false}
                                                                        columns={[
                                                                            { title: 'Code', dataIndex: 'risk_code', key: 'risk_code', width: 100 },
                                                                            { title: 'Category', dataIndex: 'risk_category_name', key: 'risk_category_name' },
                                                                            { title: 'Severity', dataIndex: 'risk_severity', key: 'risk_severity', width: 100,
                                                                                render: (t: string) => t ? <Tag color={getSeverityColor(t)}>{t}</Tag> : '-' },
                                                                            {
                                                                                title: '',
                                                                                key: 'action',
                                                                                width: 80,
                                                                                render: (_: any, record: any) => (
                                                                                    <Button size="small" danger onClick={() => handleUnlinkRisk(record.id)}>Unlink</Button>
                                                                                )
                                                                            }
                                                                        ]}
                                                                    />
                                                                ) : <Empty description="No risks linked" />}
                                                            </div>
                                                        )
                                                    },
                                                    {
                                                        key: 'assets',
                                                        label: `Assets (${linkedAssets.length})`,
                                                        children: (
                                                            <div>
                                                                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                                                                    <Select
                                                                        style={{ flex: 1 }}
                                                                        placeholder="Select asset to link"
                                                                        value={linkAssetId}
                                                                        onChange={setLinkAssetId}
                                                                        options={assets
                                                                            .filter((a: any) => !linkedAssets.some(la => la.id === a.id))
                                                                            .map((a: any) => ({ label: `${a.name}${a.ip_address ? ' (' + a.ip_address + ')' : ''}`, value: a.id }))}
                                                                        showSearch
                                                                        filterOption={(input, option) =>
                                                                            (option?.label as string || '').toLowerCase().includes(input.toLowerCase())
                                                                        }
                                                                    />
                                                                    <Button type="primary" onClick={handleLinkAsset} disabled={!linkAssetId}>Link</Button>
                                                                </div>
                                                                {linkedAssets.length > 0 ? (
                                                                    <Table
                                                                        dataSource={linkedAssets}
                                                                        rowKey="id"
                                                                        size="small"
                                                                        pagination={false}
                                                                        columns={[
                                                                            { title: 'Name', dataIndex: 'name', key: 'name' },
                                                                            { title: 'IP Address', dataIndex: 'ip_address', key: 'ip_address', width: 140 },
                                                                            { title: 'Type', dataIndex: 'asset_type_name', key: 'asset_type_name', width: 120 },
                                                                            {
                                                                                title: '',
                                                                                key: 'action',
                                                                                width: 80,
                                                                                render: (_: any, record: any) => (
                                                                                    <Button size="small" danger onClick={() => handleUnlinkAsset(record.id)}>Unlink</Button>
                                                                                )
                                                                            }
                                                                        ]}
                                                                    />
                                                                ) : <Empty description="No assets linked" />}
                                                            </div>
                                                        )
                                                    }
                                                ]}
                                            />
                                        ) : (
                                            <Empty description="Select an incident above to manage its connections." />
                                        )}
                                    </Card>
                                </div>
                            )
                        },
                        {
                            key: 'severe',
                            label: <span><ExclamationCircleOutlined /> Severe Incidents</span>,
                            children: (
                                <div>
                                    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="Total Severe" value={severeStats.total} icon={<WarningOutlined />} color="#fa541c" />
                                        </Col>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="Critical" value={severeStats.critical} icon={<ExclamationCircleOutlined />} color="#cf1322" />
                                        </Col>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="High" value={severeStats.high} icon={<WarningOutlined />} color="#fa541c" />
                                        </Col>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="Open Severe" value={severeStats.open} icon={<AlertOutlined />} color="#d48806" />
                                        </Col>
                                    </Row>

                                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 16 }}>
                                        <Input
                                            placeholder="Search severe incidents..."
                                            prefix={<SearchOutlined />}
                                            value={severeSearchText}
                                            onChange={e => setSevereSearchText(e.target.value)}
                                            style={{ width: 280 }}
                                            allowClear
                                        />
                                    </div>

                                    <Table
                                        dataSource={filteredSevereIncidents}
                                        columns={columns}
                                        rowKey="id"
                                        size="small"
                                        pagination={{ pageSize: 15, showSizeChanger: true }}
                                        onRow={(record) => ({
                                            onClick: () => handleRowClick(record),
                                            style: { cursor: 'pointer' }
                                        })}
                                    />

                                    {/* Reuse the same edit modal */}
                                    <Modal
                                        title={selectedIncident ? 'Edit Incident' : 'New Incident'}
                                        open={showForm && activeTab === 'severe'}
                                        onCancel={() => handleClear(true)}
                                        width={720}
                                        footer={
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <div>
                                                    {selectedIncident && (
                                                        <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>Delete</Button>
                                                    )}
                                                </div>
                                                <div style={{ display: 'flex', gap: 8 }}>
                                                    <Button onClick={() => handleClear(true)}>Cancel</Button>
                                                    <Button type="primary" onClick={handleSave}>
                                                        {selectedIncident ? 'Save Changes' : 'Create Incident'}
                                                    </Button>
                                                </div>
                                            </div>
                                        }
                                    >
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                            <Row gutter={16}>
                                                <Col span={8}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Code</label>
                                                    <Input value={incidentCode} onChange={e => setIncidentCode(e.target.value)} placeholder="INC-1" />
                                                </Col>
                                                <Col span={16}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Title <span style={{ color: '#cf1322' }}>*</span></label>
                                                    <Input value={title} onChange={e => setTitle(e.target.value)} placeholder="Incident title" />
                                                </Col>
                                            </Row>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Description</label>
                                                <TextArea rows={2} value={description} onChange={e => setDescription(e.target.value)} placeholder="Describe the incident" />
                                            </div>
                                            <Row gutter={16}>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Severity <span style={{ color: '#cf1322' }}>*</span></label>
                                                    <Select style={{ width: '100%' }} value={severityId} onChange={setSeverityId} options={severityOptions} placeholder="Select severity" />
                                                </Col>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Status <span style={{ color: '#cf1322' }}>*</span></label>
                                                    <Select style={{ width: '100%' }} value={statusId} onChange={setStatusId} options={statusOptions} placeholder="Select status" />
                                                </Col>
                                            </Row>
                                            <Row gutter={16}>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Reported By</label>
                                                    <Input value={reportedBy} onChange={e => setReportedBy(e.target.value)} placeholder="Name or email" />
                                                </Col>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Assigned To</label>
                                                    <Input value={assignedTo} onChange={e => setAssignedTo(e.target.value)} placeholder="Name or email" />
                                                </Col>
                                            </Row>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Containment Actions</label>
                                                <TextArea rows={2} value={containmentActions} onChange={e => setContainmentActions(e.target.value)} placeholder="Actions taken to contain the incident" />
                                            </div>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Root Cause</label>
                                                <TextArea rows={2} value={rootCause} onChange={e => setRootCause(e.target.value)} placeholder="Root cause analysis" />
                                            </div>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Remediation Steps</label>
                                                <TextArea rows={2} value={remediationSteps} onChange={e => setRemediationSteps(e.target.value)} placeholder="Steps to remediate" />
                                            </div>

                                            {/* Vulnerability Triage Section */}
                                            <Collapse
                                                activeKey={showTriageFields ? ['triage'] : []}
                                                onChange={(keys) => setShowTriageFields(keys.includes('triage'))}
                                                size="small"
                                                items={[{
                                                    key: 'triage',
                                                    label: <span><BugOutlined /> Vulnerability Triage</span>,
                                                    children: (
                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                                            <Row gutter={16}>
                                                                <Col span={12}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Vulnerability Source</label>
                                                                    <Select style={{ width: '100%' }} value={vulnerabilitySource} onChange={setVulnerabilitySource} placeholder="Select source" allowClear
                                                                        options={[{ value: 'euvd', label: 'EUVD' }, { value: 'internal_scan', label: 'Internal Scan' }, { value: 'external_report', label: 'External Report' }, { value: 'user_report', label: 'User Report' }]} />
                                                                </Col>
                                                                <Col span={12}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Triage Status</label>
                                                                    <Select style={{ width: '100%' }} value={triageStatus} onChange={setTriageStatus} placeholder="Select triage status" allowClear
                                                                        options={[{ value: 'New', label: 'New' }, { value: 'Triaged', label: 'Triaged' }, { value: 'In Progress', label: 'In Progress' }, { value: 'Fixed', label: 'Fixed' }, { value: 'Verified', label: 'Verified' }, { value: 'Closed', label: 'Closed' }]} />
                                                                </Col>
                                                            </Row>
                                                            <Row gutter={16}>
                                                                <Col span={8}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>CVE ID</label>
                                                                    <Input value={cveId} onChange={e => setCveId(e.target.value)} placeholder="CVE-2025-12345" />
                                                                </Col>
                                                                <Col span={8}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>CWE ID</label>
                                                                    <Input value={cweId} onChange={e => setCweId(e.target.value)} placeholder="CWE-79" />
                                                                </Col>
                                                                <Col span={8}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>CVSS Score</label>
                                                                    <InputNumber style={{ width: '100%' }} value={cvssScore} onChange={(val) => setCvssScore(val)} min={0} max={10} step={0.1} placeholder="0.0 - 10.0" />
                                                                </Col>
                                                            </Row>
                                                            <div>
                                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Affected Products</label>
                                                                <TextArea rows={2} value={affectedProducts} onChange={e => setAffectedProducts(e.target.value)} placeholder="List affected products, one per line" />
                                                            </div>
                                                        </div>
                                                    )
                                                }]}
                                            />
                                        </div>
                                    </Modal>
                                </div>
                            )
                        },
                        {
                            key: 'exploits',
                            label: <span><BugOutlined /> Active Exploits</span>,
                            children: (
                                <div>
                                    {/* Segmented control */}
                                    <div style={{ marginBottom: 16 }}>
                                        <Segmented
                                            options={['Exploited', 'Latest', 'Critical']}
                                            value={euvdMode}
                                            onChange={(val) => setEuvdMode(val as string)}
                                        />
                                    </div>

                                    {/* Sync progress bar */}
                                    {syncProgress.active && (
                                        <div style={{ marginBottom: 16 }}>
                                            <Progress
                                                percent={syncProgress.percent}
                                                status={syncProgress.percent >= 100 ? 'success' : 'active'}
                                                strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }}
                                                format={() => syncProgress.status}
                                            />
                                        </div>
                                    )}

                                    {/* Stats cards */}
                                    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="Exploited" value={euvdStats.exploited_count} icon={<BugOutlined />} color="#cf1322" />
                                        </Col>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="Critical" value={euvdStats.critical_count} icon={<ExclamationCircleOutlined />} color="#fa541c" />
                                        </Col>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard title="Total Cached" value={euvdStats.total_cached} icon={<GlobalOutlined />} color="#1890ff" />
                                        </Col>
                                        <Col xs={24} sm={12} md={6}>
                                            <StatCard
                                                title="Highest Score"
                                                value={currentEuvdVulns.length > 0
                                                    ? Math.max(...currentEuvdVulns.map(v => v.base_score || 0)).toFixed(1)
                                                    : '-'}
                                                icon={<AlertOutlined />}
                                                color="#d48806"
                                            />
                                        </Col>
                                    </Row>

                                    {/* Search bar */}
                                    <Collapse
                                        size="small"
                                        style={{ marginBottom: 16 }}
                                        items={[{
                                            key: 'search',
                                            label: <span><SearchOutlined /> Search EUVD</span>,
                                            children: (
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                                    <Row gutter={16}>
                                                        <Col span={8}>
                                                            <Input
                                                                placeholder="Search text..."
                                                                value={euvdSearchText}
                                                                onChange={e => setEuvdSearchText(e.target.value)}
                                                                onPressEnter={handleEuvdSearch}
                                                            />
                                                        </Col>
                                                        <Col span={6}>
                                                            <Input
                                                                placeholder="Product..."
                                                                value={euvdSearchProduct}
                                                                onChange={e => setEuvdSearchProduct(e.target.value)}
                                                                onPressEnter={handleEuvdSearch}
                                                            />
                                                        </Col>
                                                        <Col span={6}>
                                                            <Input
                                                                placeholder="Vendor..."
                                                                value={euvdSearchVendor}
                                                                onChange={e => setEuvdSearchVendor(e.target.value)}
                                                                onPressEnter={handleEuvdSearch}
                                                            />
                                                        </Col>
                                                        <Col span={4}>
                                                            <Button type="primary" icon={<SearchOutlined />} onClick={handleEuvdSearch} loading={euvdSearching} block>
                                                                Search
                                                            </Button>
                                                        </Col>
                                                    </Row>
                                                    {searchResults.length > 0 && (
                                                        <div>
                                                            <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 8 }}>{searchTotal} results found</div>
                                                            <Table
                                                                dataSource={searchResults}
                                                                columns={euvdColumns}
                                                                rowKey={(r: any) => r.euvd_id || r.id || Math.random().toString()}
                                                                size="small"
                                                                pagination={{ pageSize: 10 }}
                                                                expandable={{
                                                                    expandedRowRender: (record: any) => (
                                                                        <div style={{ padding: 8, fontSize: 12 }}>
                                                                            <p><strong>Description:</strong> {record.description || 'N/A'}</p>
                                                                            {record.base_score_vector && <p><strong>CVSS Vector:</strong> <code>{record.base_score_vector}</code></p>}
                                                                            {record.aliases && <p><strong>Aliases:</strong> {record.aliases}</p>}
                                                                            {record.references && (
                                                                                <p><strong>References:</strong><br/>
                                                                                    {record.references.split('\n').map((ref: string, i: number) => (
                                                                                        <span key={i}><a href={ref} target="_blank" rel="noopener noreferrer">{ref}</a><br/></span>
                                                                                    ))}
                                                                                </p>
                                                                            )}
                                                                            {record.vendors && <p><strong>Vendors:</strong> {record.vendors}</p>}
                                                                        </div>
                                                                    )
                                                                }}
                                                            />
                                                        </div>
                                                    )}
                                                </div>
                                            )
                                        }]}
                                    />

                                    {/* Toolbar: delete (left) + sync (right) */}
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
                                        {/* Left: date range & delete controls */}
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                                            <span style={{ fontSize: 13, color: '#595959', fontWeight: 500 }}>Date Range:</span>
                                            <DatePicker.RangePicker
                                                value={euvdDateRange}
                                                onChange={(dates) => setEuvdDateRange(dates as [dayjs.Dayjs | null, dayjs.Dayjs | null] | null)}
                                                style={{ width: 280 }}
                                            />
                                            <Button
                                                danger
                                                icon={<DeleteOutlined />}
                                                onClick={handleDeleteByRange}
                                                loading={euvdDeleting}
                                                disabled={!euvdDateRange || !euvdDateRange[0] || !euvdDateRange[1]}
                                            >
                                                Delete Range
                                            </Button>
                                            <Button
                                                danger
                                                type="primary"
                                                icon={<DeleteOutlined />}
                                                onClick={handleClearAll}
                                            >
                                                Clear All
                                            </Button>
                                        </div>
                                        {/* Right: sync controls */}
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                            {lastSyncTime && (
                                                <span style={{ fontSize: 12, color: '#8c8c8c', whiteSpace: 'nowrap' }}>
                                                    Last sync: {dayjs(lastSyncTime).format('YYYY-MM-DD HH:mm')}
                                                </span>
                                            )}
                                            <Button
                                                type="primary"
                                                size="large"
                                                icon={<SyncOutlined spin={euvdSyncing} />}
                                                onClick={handleRefreshSync}
                                                loading={euvdSyncing}
                                                style={{ fontWeight: 600 }}
                                            >
                                                EUVD Sync
                                            </Button>
                                        </div>
                                    </div>

                                    {/* Main table */}
                                    {euvdLoading ? (
                                        <div style={{ textAlign: 'center', padding: 40 }}>
                                            <Spin size="large" />
                                            <p style={{ marginTop: 16, color: '#8c8c8c' }}>Loading vulnerability data...</p>
                                        </div>
                                    ) : (
                                        <Table
                                            dataSource={currentEuvdVulns}
                                            columns={euvdColumns}
                                            rowKey="id"
                                            size="small"
                                            pagination={{ pageSize: 15, showSizeChanger: true, total: currentEuvdTotal }}
                                            expandable={{
                                                expandedRowRender: (record: EUVDVulnerability) => (
                                                    <div style={{ padding: 8, fontSize: 12 }}>
                                                        <p style={{ marginBottom: 8 }}><strong>Full Description:</strong> {record.description || 'N/A'}</p>
                                                        {record.base_score_vector && <p style={{ marginBottom: 8 }}><strong>CVSS Vector:</strong> <code>{record.base_score_vector}</code></p>}
                                                        {record.aliases && (
                                                            <p style={{ marginBottom: 8 }}><strong>Aliases:</strong> {record.aliases.split('\n').join(', ')}</p>
                                                        )}
                                                        {record.references && (
                                                            <div style={{ marginBottom: 8 }}>
                                                                <strong>References:</strong>
                                                                <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                                                                    {record.references.split('\n').filter(Boolean).map((ref, i) => (
                                                                        <li key={i}><a href={ref} target="_blank" rel="noopener noreferrer">{ref}</a></li>
                                                                    ))}
                                                                </ul>
                                                            </div>
                                                        )}
                                                        {record.vendors && (
                                                            <p style={{ marginBottom: 8 }}><strong>Vendors:</strong> {(() => { try { return JSON.parse(record.vendors).join(', '); } catch { return record.vendors; } })()}</p>
                                                        )}
                                                        {record.products && (
                                                            <p style={{ marginBottom: 8 }}><strong>Products:</strong> {(() => { try { return JSON.parse(record.products).join(', '); } catch { return record.products; } })()}</p>
                                                        )}
                                                        {record.epss !== null && record.epss !== undefined && (
                                                            <p><strong>EPSS Score:</strong> {(record.epss * 100).toFixed(2)}%</p>
                                                        )}
                                                    </div>
                                                )
                                            }}
                                        />
                                    )}
                                </div>
                            )
                        },
                        {
                            key: 'post-market',
                            label: <span><SafetyOutlined /> Post-Market</span>,
                            children: (
                                <div>
                                    {metricsLoading ? (
                                        <div style={{ textAlign: 'center', padding: 40 }}>
                                            <Spin size="large" />
                                            <p style={{ marginTop: 16, color: '#8c8c8c' }}>Loading post-market metrics...</p>
                                        </div>
                                    ) : postMarketMetrics ? (
                                        <div>
                                            <Row gutter={[16, 16]}>
                                                <Col xs={24} sm={12} md={6}>
                                                    <StatCard title="SLA Compliance" value={`${Math.round(postMarketMetrics.sla_compliance_rate ?? 0)}%`} icon={<CheckCircleOutlined />} color="#389e0d" />
                                                </Col>
                                                <Col xs={24} sm={12} md={6}>
                                                    <StatCard title="Overdue" value={postMarketMetrics.overdue_count} icon={<ExclamationCircleOutlined />} color="#cf1322" />
                                                </Col>
                                                <Col xs={24} sm={12} md={6}>
                                                    <StatCard title="At Risk" value={postMarketMetrics.at_risk_count} icon={<WarningOutlined />} color="#d48806" />
                                                </Col>
                                                <Col xs={24} sm={12} md={6}>
                                                    <StatCard title="Avg Resolution" value={postMarketMetrics.avg_resolution_hours != null ? `${Math.round(postMarketMetrics.avg_resolution_hours)}h` : 'N/A'} icon={<ClockCircleOutlined />} color="#1890ff" />
                                                </Col>
                                            </Row>

                                            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                                                <Col xs={24} sm={12} md={6}>
                                                    <StatCard title="Patches Released" value={postMarketMetrics.patches_released} icon={<ToolOutlined />} color="#722ed1" />
                                                </Col>
                                                <Col xs={24} sm={12} md={6}>
                                                    <StatCard title="Advisories Published" value={postMarketMetrics.advisories_published} icon={<AlertOutlined />} color="#13c2c2" />
                                                </Col>
                                                <Col xs={24} sm={12} md={6}>
                                                    <StatCard title="ENISA Pending" value={postMarketMetrics.enisa_pending} icon={<AuditOutlined />} color="#d48806" />
                                                </Col>
                                                <Col xs={24} sm={12} md={6}>
                                                    <StatCard title="ENISA Complete" value={postMarketMetrics.enisa_complete} icon={<AuditOutlined />} color="#389e0d" />
                                                </Col>
                                            </Row>

                                            <Card title="Vulnerability Aging" size="small" style={{ marginTop: 24 }}>
                                                <div style={{ display: 'flex', gap: 16 }}>
                                                    {[
                                                        { label: '0-24h', count: postMarketMetrics.aging_0_24h, color: '#389e0d' },
                                                        { label: '24-72h', count: postMarketMetrics.aging_24_72h, color: '#d48806' },
                                                        { label: '72h-7d', count: postMarketMetrics.aging_72h_7d, color: '#fa541c' },
                                                        { label: '7d+', count: postMarketMetrics.aging_7d_plus, color: '#cf1322' },
                                                    ].map(item => (
                                                        <Card key={item.label} size="small" style={{ flex: 1, textAlign: 'center' }}>
                                                            <div style={{ fontSize: 24, fontWeight: 600, color: item.color }}>{item.count}</div>
                                                            <div style={{ fontSize: 12, color: '#8c8c8c' }}>{item.label}</div>
                                                        </Card>
                                                    ))}
                                                </div>
                                            </Card>

                                            <div style={{ marginTop: 16, textAlign: 'right' }}>
                                                <Button icon={<SyncOutlined />} onClick={fetchPostMarketMetrics} loading={metricsLoading}>Refresh Metrics</Button>
                                            </div>
                                        </div>
                                    ) : (
                                        <Empty description="No post-market data available" />
                                    )}
                                </div>
                            )
                        },
                        {
                            key: 'patches',
                            label: <span><ToolOutlined /> Patch Tracking</span>,
                            children: (
                                <div>
                                    <div style={{ display: 'flex', gap: 16, marginBottom: 16, alignItems: 'center' }}>
                                        <Select
                                            style={{ width: 400 }}
                                            value={selectedPatchIncident}
                                            onChange={(val) => {
                                                setSelectedPatchIncident(val);
                                                if (val) fetchPatches(val);
                                            }}
                                            placeholder="Select an incident to view patches"
                                            showSearch
                                            optionFilterProp="label"
                                            allowClear
                                            options={incidents.map(i => ({ value: i.id, label: `${i.incident_code || 'INC'} - ${i.title}` }))}
                                        />
                                        {selectedPatchIncident && (
                                            <Button type="primary" icon={<PlusOutlined />} onClick={() => {
                                                setSelectedPatch(null);
                                                setPatchVersion('');
                                                setPatchDescription('');
                                                setPatchReleaseDate(null);
                                                setPatchResolutionDate(null);
                                                setShowPatchModal(true);
                                            }}>
                                                Add Patch
                                            </Button>
                                        )}
                                    </div>

                                    {selectedPatchIncident ? (
                                        <Table
                                            dataSource={patches}
                                            rowKey="id"
                                            size="small"
                                            pagination={false}
                                            columns={[
                                                { title: 'Version', dataIndex: 'patch_version', key: 'patch_version', width: 120 },
                                                { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
                                                {
                                                    title: 'Release Date', dataIndex: 'release_date', key: 'release_date', width: 120,
                                                    render: (text: string | null) => text ? dayjs(text).format('YYYY-MM-DD') : '-'
                                                },
                                                {
                                                    title: 'Target SLA', dataIndex: 'target_sla_date', key: 'target_sla_date', width: 120,
                                                    render: (text: string | null) => text ? dayjs(text).format('YYYY-MM-DD') : '-'
                                                },
                                                {
                                                    title: 'Resolution Date', dataIndex: 'actual_resolution_date', key: 'actual_resolution_date', width: 120,
                                                    render: (text: string | null) => text ? dayjs(text).format('YYYY-MM-DD') : '-'
                                                },
                                                {
                                                    title: 'SLA', dataIndex: 'sla_compliance', key: 'sla_compliance', width: 100,
                                                    render: (text: string | null) => {
                                                        if (!text) return '-';
                                                        const color = text === 'on_time' ? '#389e0d' : text === 'at_risk' ? '#d48806' : '#cf1322';
                                                        return <Tag color={color}>{text.replace('_', ' ')}</Tag>;
                                                    }
                                                },
                                                {
                                                    title: 'Actions', key: 'actions', width: 100,
                                                    render: (_: any, record: any) => (
                                                        <Space>
                                                            <Button size="small" icon={<EditOutlined />} onClick={() => {
                                                                setSelectedPatch(record.id);
                                                                setPatchVersion(record.patch_version || '');
                                                                setPatchDescription(record.description || '');
                                                                setPatchReleaseDate(record.release_date ? dayjs(record.release_date) : null);
                                                                setPatchResolutionDate(record.actual_resolution_date ? dayjs(record.actual_resolution_date) : null);
                                                                setShowPatchModal(true);
                                                            }} />
                                                            <Button size="small" danger icon={<DeleteOutlined />} onClick={() => {
                                                                Modal.confirm({
                                                                    title: 'Delete Patch',
                                                                    content: 'Are you sure?',
                                                                    okType: 'danger',
                                                                    onOk: async () => {
                                                                        await deletePatch(record.id);
                                                                        if (selectedPatchIncident) fetchPatches(selectedPatchIncident);
                                                                    }
                                                                });
                                                            }} />
                                                        </Space>
                                                    )
                                                }
                                            ]}
                                        />
                                    ) : (
                                        <Empty description="Select an incident to view its patches" />
                                    )}

                                    <Modal
                                        title={selectedPatch ? 'Edit Patch' : 'Add Patch'}
                                        open={showPatchModal}
                                        onCancel={() => setShowPatchModal(false)}
                                        onOk={async () => {
                                            if (!patchVersion.trim()) {
                                                api.error({ message: 'Validation Error', description: 'Patch version is required', duration: 4 });
                                                return;
                                            }
                                            const payload: any = {
                                                patch_version: patchVersion.trim(),
                                                description: patchDescription || undefined,
                                                release_date: patchReleaseDate ? patchReleaseDate.toISOString() : undefined,
                                                actual_resolution_date: patchResolutionDate ? patchResolutionDate.toISOString() : undefined,
                                            };
                                            let success;
                                            if (selectedPatch) {
                                                success = await updatePatch(selectedPatch, payload);
                                            } else if (selectedPatchIncident) {
                                                success = await createPatch(selectedPatchIncident, payload);
                                            }
                                            if (success) {
                                                api.success({ message: selectedPatch ? 'Patch Updated' : 'Patch Created', duration: 4 });
                                                setShowPatchModal(false);
                                                if (selectedPatchIncident) fetchPatches(selectedPatchIncident);
                                            } else {
                                                api.error({ message: 'Error', description: 'Failed to save patch', duration: 4 });
                                            }
                                        }}
                                    >
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Patch Version <span style={{ color: '#cf1322' }}>*</span></label>
                                                <Input value={patchVersion} onChange={e => setPatchVersion(e.target.value)} placeholder="e.g. 2.1.1" />
                                            </div>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Description</label>
                                                <TextArea rows={2} value={patchDescription} onChange={e => setPatchDescription(e.target.value)} placeholder="Patch description" />
                                            </div>
                                            <Row gutter={16}>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Release Date</label>
                                                    <DatePicker style={{ width: '100%' }} value={patchReleaseDate} onChange={setPatchReleaseDate} />
                                                </Col>
                                                <Col span={12}>
                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Resolution Date</label>
                                                    <DatePicker style={{ width: '100%' }} value={patchResolutionDate} onChange={setPatchResolutionDate} />
                                                </Col>
                                            </Row>
                                        </div>
                                    </Modal>
                                </div>
                            )
                        },
                        {
                            key: 'enisa',
                            label: <span><AuditOutlined /> ENISA Reporting</span>,
                            children: (
                                <div>
                                    <div style={{ display: 'flex', gap: 16, marginBottom: 16, alignItems: 'center' }}>
                                        <Select
                                            style={{ width: 400 }}
                                            value={selectedEnisaIncident}
                                            onChange={(val) => {
                                                setSelectedEnisaIncident(val);
                                                if (val) fetchENISANotification(val);
                                            }}
                                            placeholder="Select an incident for ENISA reporting"
                                            showSearch
                                            optionFilterProp="label"
                                            allowClear
                                            options={incidents.map(i => ({ value: i.id, label: `${i.incident_code || 'INC'} - ${i.title}` }))}
                                        />
                                        {selectedEnisaIncident && !enisaNotification && (
                                            <Button type="primary" onClick={async () => {
                                                const success = await createENISANotification(selectedEnisaIncident);
                                                if (success) {
                                                    api.success({ message: 'ENISA Notification Created', description: 'Deadlines auto-calculated from discovery date', duration: 4 });
                                                }
                                            }}>
                                                Initialize ENISA Reporting
                                            </Button>
                                        )}
                                    </div>

                                    {selectedEnisaIncident && enisaNotification ? (
                                        <div>
                                            <div style={{ marginBottom: 16 }}>
                                                <Tag color={
                                                    enisaNotification.reporting_status === 'complete' ? '#389e0d' :
                                                    enisaNotification.reporting_status === 'overdue' ? '#cf1322' :
                                                    enisaNotification.reporting_status === 'partially_complete' ? '#d48806' :
                                                    enisaNotification.reporting_status === 'in_progress' ? '#1890ff' : '#8c8c8c'
                                                }>
                                                    Reporting Status: {(enisaNotification.reporting_status || 'not_started').replace(/_/g, ' ')}
                                                </Tag>
                                            </div>

                                            <Row gutter={[16, 16]}>
                                                {/* 24h Early Warning */}
                                                <Col xs={24} md={8}>
                                                    <Card
                                                        title="24h Early Warning"
                                                        size="small"
                                                        extra={enisaNotification.early_warning_submitted ? <Tag color="#389e0d">Submitted</Tag> : <Tag color="#d48806">Pending</Tag>}
                                                    >
                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                            <div style={{ fontSize: 12, color: '#8c8c8c' }}>
                                                                Deadline: {enisaNotification.early_warning_deadline ? dayjs(enisaNotification.early_warning_deadline).format('YYYY-MM-DD HH:mm') : 'N/A'}
                                                            </div>
                                                            {enisaNotification.early_warning_deadline && !enisaNotification.early_warning_submitted && (
                                                                <div style={{ fontSize: 12, color: dayjs().isAfter(enisaNotification.early_warning_deadline) ? '#cf1322' : '#d48806' }}>
                                                                    {dayjs().isAfter(enisaNotification.early_warning_deadline) ? 'OVERDUE' : `${dayjs(enisaNotification.early_warning_deadline).diff(dayjs(), 'hour')}h remaining`}
                                                                </div>
                                                            )}
                                                            <TextArea
                                                                rows={4}
                                                                defaultValue={enisaNotification.early_warning_content || ''}
                                                                placeholder="Early warning content..."
                                                                onBlur={(e) => updateENISANotification(enisaNotification.id, { early_warning_content: e.target.value })}
                                                            />
                                                            {!enisaNotification.early_warning_submitted && (
                                                                <Button
                                                                    type="primary" size="small"
                                                                    onClick={async () => {
                                                                        await updateENISANotification(enisaNotification.id, { early_warning_submitted: true });
                                                                        api.success({ message: 'Early Warning Submitted', duration: 4 });
                                                                    }}
                                                                >
                                                                    Mark as Submitted
                                                                </Button>
                                                            )}
                                                        </div>
                                                    </Card>
                                                </Col>

                                                {/* 72h Vulnerability Notification */}
                                                <Col xs={24} md={8}>
                                                    <Card
                                                        title="72h Vulnerability Notification"
                                                        size="small"
                                                        extra={enisaNotification.vuln_notification_submitted ? <Tag color="#389e0d">Submitted</Tag> : <Tag color="#d48806">Pending</Tag>}
                                                    >
                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                            <div style={{ fontSize: 12, color: '#8c8c8c' }}>
                                                                Deadline: {enisaNotification.vuln_notification_deadline ? dayjs(enisaNotification.vuln_notification_deadline).format('YYYY-MM-DD HH:mm') : 'N/A'}
                                                            </div>
                                                            {enisaNotification.vuln_notification_deadline && !enisaNotification.vuln_notification_submitted && (
                                                                <div style={{ fontSize: 12, color: dayjs().isAfter(enisaNotification.vuln_notification_deadline) ? '#cf1322' : '#d48806' }}>
                                                                    {dayjs().isAfter(enisaNotification.vuln_notification_deadline) ? 'OVERDUE' : `${dayjs(enisaNotification.vuln_notification_deadline).diff(dayjs(), 'hour')}h remaining`}
                                                                </div>
                                                            )}
                                                            <TextArea
                                                                rows={4}
                                                                defaultValue={enisaNotification.vuln_notification_content || ''}
                                                                placeholder="Vulnerability notification content..."
                                                                onBlur={(e) => updateENISANotification(enisaNotification.id, { vuln_notification_content: e.target.value })}
                                                            />
                                                            {!enisaNotification.vuln_notification_submitted && (
                                                                <Button
                                                                    type="primary" size="small"
                                                                    onClick={async () => {
                                                                        await updateENISANotification(enisaNotification.id, { vuln_notification_submitted: true });
                                                                        api.success({ message: 'Vulnerability Notification Submitted', duration: 4 });
                                                                    }}
                                                                >
                                                                    Mark as Submitted
                                                                </Button>
                                                            )}
                                                        </div>
                                                    </Card>
                                                </Col>

                                                {/* 14d Final Report */}
                                                <Col xs={24} md={8}>
                                                    <Card
                                                        title="14d Final Report"
                                                        size="small"
                                                        extra={enisaNotification.final_report_submitted ? <Tag color="#389e0d">Submitted</Tag> : <Tag color="#d48806">Pending</Tag>}
                                                    >
                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                            <div style={{ fontSize: 12, color: '#8c8c8c' }}>
                                                                Deadline: {enisaNotification.final_report_deadline ? dayjs(enisaNotification.final_report_deadline).format('YYYY-MM-DD HH:mm') : 'N/A'}
                                                            </div>
                                                            {enisaNotification.final_report_deadline && !enisaNotification.final_report_submitted && (
                                                                <div style={{ fontSize: 12, color: dayjs().isAfter(enisaNotification.final_report_deadline) ? '#cf1322' : '#d48806' }}>
                                                                    {dayjs().isAfter(enisaNotification.final_report_deadline) ? 'OVERDUE' : `${Math.ceil(dayjs(enisaNotification.final_report_deadline).diff(dayjs(), 'day', true))}d remaining`}
                                                                </div>
                                                            )}
                                                            <TextArea
                                                                rows={4}
                                                                defaultValue={enisaNotification.final_report_content || ''}
                                                                placeholder="Final report content..."
                                                                onBlur={(e) => updateENISANotification(enisaNotification.id, { final_report_content: e.target.value })}
                                                            />
                                                            {!enisaNotification.final_report_submitted && (
                                                                <Button
                                                                    type="primary" size="small"
                                                                    onClick={async () => {
                                                                        await updateENISANotification(enisaNotification.id, { final_report_submitted: true });
                                                                        api.success({ message: 'Final Report Submitted', duration: 4 });
                                                                    }}
                                                                >
                                                                    Mark as Submitted
                                                                </Button>
                                                            )}
                                                        </div>
                                                    </Card>
                                                </Col>
                                            </Row>
                                        </div>
                                    ) : selectedEnisaIncident ? (
                                        <Empty description="No ENISA notification exists for this incident. Click 'Initialize ENISA Reporting' to create one." />
                                    ) : (
                                        <Empty description="Select an incident to manage ENISA reporting" />
                                    )}
                                </div>
                            )
                        }
                    ]}
                />
            </div>
        </div>
    );
};

export default IncidentRegistrationPage;
