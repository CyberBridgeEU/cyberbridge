import {Select, Table, notification, Tag, Modal, Tabs, Card, Progress, Row, Col, Breadcrumb, Input, Empty, Tooltip, Button, Collapse} from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { SafetyCertificateOutlined, PlusOutlined, EditOutlined, DatabaseOutlined, UnorderedListOutlined, DashboardOutlined, CheckCircleOutlined, ClockCircleOutlined, ExclamationCircleOutlined, MinusCircleOutlined, AppstoreOutlined, SearchOutlined, LinkOutlined, AlertOutlined, AuditOutlined, BulbOutlined } from '@ant-design/icons';
import useControlStore from "../store/useControlStore.ts";
import useRiskStore from "../store/useRiskStore.ts";
import usePolicyStore from "../store/usePolicyStore.ts";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import useCRAFilteredFrameworks from "../hooks/useCRAFilteredFrameworks.ts";
import {useEffect, useState, useMemo} from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import useUserStore from "../store/useUserStore.ts";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { StatCard, QuickActionsPanel, QuickActionButton, DashboardSection } from "../components/dashboard";
import ConnectionBoard from "../components/ConnectionBoard.tsx";
import { filterByRelevance } from "../utils/recommendationUtils.ts";

const ControlsInfo = {
    title: "Controls Management",
    description: "Manage controls that help mitigate risks and ensure policy compliance. Controls are organized into Control Sets for better categorization.",
    features: [
        "Create and manage individual controls with codes and descriptions",
        "Organize controls into Control Sets",
        "Track control implementation status",
        "Link controls to risks and policies",
        "Import controls from Excel files via Controls Library"
    ]
};

const ControlRegistrationPage = () => {
    // Menu highlighting
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Tab state
    const [activeTab, setActiveTab] = useState<string>('dashboard');

    // View mode state for Control Registry
    const [controlViewMode, setControlViewMode] = useState<'grid' | 'list'>('list');
    const [controlSearchText, setControlSearchText] = useState('');

    // Store access
    const {
        controls,
        controlSets,
        controlStatuses,
        fetchControls,
        fetchControlSets,
        fetchControlStatuses,
        createControl,
        updateControl,
        deleteControl,
        error
    } = useControlStore();

    const {organisations, fetchOrganisations} = useUserStore();
    const {risks, fetchRisks} = useRiskStore();
    const {policies, fetchPolicies, policyTemplates, fetchPolicyTemplates, importPolicyTemplates} = usePolicyStore();

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    // Selected control state
    const [selectedControl, setSelectedControl] = useState<string | null>(null);

    // Form visibility state
    const [showForm, setShowForm] = useState<boolean>(false);

    // Form state
    const [code, setCode] = useState<string>('');
    const [name, setName] = useState<string>('');
    const [description, setDescription] = useState<string>('');
    const [category, setCategory] = useState<string>('');
    const [owner, setOwner] = useState<string>('');
    const [controlSetId, setControlSetId] = useState<string | undefined>(undefined);
    const [controlStatusId, setControlStatusId] = useState<string | undefined>(undefined);

    // Filter state for breadcrumb navigation
    const [selectedControlSetFilter, setSelectedControlSetFilter] = useState<string | null>(null);
    const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string | null>(null);

    // Connection tab state
    const [selectedConnectionControl, setSelectedConnectionControl] = useState<string | undefined>(undefined);
    const [connectionFrameworkId, setConnectionFrameworkId] = useState<string | undefined>(undefined);
    const [controlRecommendationLoading, setControlRecommendationLoading] = useState<Record<string, boolean>>({});

    // Framework store
    const { fetchFrameworks } = useFrameworksStore();
    const { filteredFrameworks, craFrameworkId, isCRAModeActive } = useCRAFilteredFrameworks();

    // Fetch data on component mount
    useEffect(() => {
        const fetchData = async () => {
            try {
                await fetchControlStatuses();
                await fetchControlSets();
                await fetchOrganisations();
                await fetchControls();
                await fetchRisks();
                await fetchPolicies();
                await fetchFrameworks();
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        };
        fetchData();
    }, [fetchControlStatuses, fetchControlSets, fetchOrganisations, fetchControls, fetchRisks, fetchPolicies, fetchFrameworks]);

    // Auto-select CRA framework when CRA mode is active
    useEffect(() => {
        if (isCRAModeActive && craFrameworkId && !connectionFrameworkId) {
            setConnectionFrameworkId(craFrameworkId);
        }
    }, [isCRAModeActive, craFrameworkId]);

    // Fetch linked data when connection control or framework changes
    const { fetchLinkedRisks, fetchLinkedPolicies, linkedRisks, linkedPolicies, linkControlToRisk, unlinkControlFromRisk, linkControlToPolicy, unlinkControlFromPolicy } = useControlStore();
    useEffect(() => {
        if (selectedConnectionControl && connectionFrameworkId) {
            fetchLinkedRisks(selectedConnectionControl, connectionFrameworkId);
            fetchLinkedPolicies(selectedConnectionControl, connectionFrameworkId);
        }
    }, [selectedConnectionControl, connectionFrameworkId, fetchLinkedRisks, fetchLinkedPolicies]);

    useEffect(() => {
        if (policyTemplates.length === 0) {
            fetchPolicyTemplates();
        }
    }, [policyTemplates.length, fetchPolicyTemplates]);

    // Handle form submission
    const handleSave = async () => {
        if (!code || !name || !controlSetId || !controlStatusId) {
            api.error({
                message: 'Control Operation Failed',
                description: 'Please fill in all required fields (Code, Name, Control Set, Status)',
                duration: 4,
            });
            return;
        }

        let success;
        const isUpdate = selectedControl !== null;

        try {
            if (isUpdate && selectedControl) {
                success = await updateControl(
                    selectedControl,
                    code,
                    name,
                    description,
                    category,
                    owner,
                    controlSetId,
                    controlStatusId
                );
            } else {
                success = await createControl(
                    code,
                    name,
                    description,
                    category,
                    owner,
                    controlSetId,
                    controlStatusId
                );
            }

            if (success) {
                api.success({
                    message: isUpdate ? 'Control Update Success' : 'Control Creation Success',
                    description: isUpdate ? 'Control updated successfully' : 'Control created successfully',
                    duration: 4,
                });
                handleClear(true);
                await fetchControls();
            } else {
                api.error({
                    message: isUpdate ? 'Control Update Failed' : 'Control Creation Failed',
                    description: isUpdate ? 'Failed to update control' : 'Failed to create control',
                    duration: 4,
                });
            }
        } catch (error) {
            console.error('Error saving control:', error);
            api.error({
                message: isUpdate ? 'Control Update Failed' : 'Control Creation Failed',
                description: 'An unexpected error occurred',
                duration: 4,
            });
        }
    };

    // Clear form
    const handleClear = (hideForm: boolean = false) => {
        setCode('');
        setName('');
        setDescription('');
        setCategory('');
        setOwner('');
        setControlSetId(undefined);
        setControlStatusId(undefined);
        setSelectedControl(null);
        if (hideForm) {
            setShowForm(false);
        }
    };

    // Handle control deletion
    const handleDelete = async () => {
        if (!selectedControl) {
            api.error({
                message: 'Control Deletion Failed',
                description: 'Please select a control to delete',
                duration: 4,
            });
            return;
        }

        try {
            const success = await deleteControl(selectedControl);

            if (success) {
                api.success({
                    message: 'Control Deletion Success',
                    description: 'Control deleted successfully',
                    duration: 4,
                });
                handleClear(true);
                await fetchControls();
            } else {
                api.error({
                    message: 'Control Deletion Failed',
                    description: error || 'Failed to delete control',
                    duration: 4,
                });
            }
        } catch (error) {
            console.error('Error deleting control:', error);
            api.error({
                message: 'Control Deletion Failed',
                description: 'An unexpected error occurred',
                duration: 4,
            });
        }
    };

    const handleImportAndLinkPolicyRecommendation = async (templateId: string) => {
        if (!selectedConnectionControl || !connectionFrameworkId) {
            api.warning({
                message: !selectedConnectionControl ? 'No Control Selected' : 'No Framework Selected',
                description: !selectedConnectionControl
                    ? 'Select a control in the Connections tab before importing policies.'
                    : 'Select a framework in the Connections tab before importing policies.',
                duration: 4,
            });
            return;
        }

        setControlRecommendationLoading((prev) => ({ ...prev, [templateId]: true }));
        try {
            const result = await importPolicyTemplates([templateId]);
            if (result && result.success && result.imported_policy_codes.length > 0) {
                await fetchPolicies();
                const latestPolicies = usePolicyStore.getState().policies;
                const importedPolicies = latestPolicies.filter((policy) =>
                    result.imported_policy_codes.includes(policy.policy_code || '')
                );
                for (const policy of importedPolicies) {
                    await linkControlToPolicy(selectedConnectionControl, policy.id, connectionFrameworkId!);
                }
                await fetchLinkedPolicies(selectedConnectionControl, connectionFrameworkId);
                api.success({
                    message: 'Policy Imported & Linked',
                    description: `Imported ${result.imported_policy_codes.length} policy(ies) and linked to control`,
                    duration: 4,
                });
            } else if (result && result.success && result.imported_count === 0) {
                api.info({
                    message: 'Already Imported',
                    description: result.message || 'This policy template has already been imported.',
                    duration: 4,
                });
            } else {
                api.error({
                    message: 'Import Failed',
                    description: result?.message || 'Failed to import policy template',
                    duration: 4,
                });
            }
        } catch {
            api.error({
                message: 'Import Failed',
                description: 'An unexpected error occurred',
                duration: 4,
            });
        } finally {
            setControlRecommendationLoading((prev) => ({ ...prev, [templateId]: false }));
        }
    };

    // Convert data for Select components
    const controlSetOptions = controlSets.map(set => ({
        label: set.name,
        value: set.id
    }));

    const statusOptions = controlStatuses.map(status => ({
        label: status.status_name,
        value: status.id
    }));

    // Get unique categories from controls
    const categories = useMemo(() => {
        const uniqueCategories = [...new Set(controls.filter(c => c.category).map(c => c.category))];
        return uniqueCategories.sort();
    }, [controls]);

    // Filter controls based on breadcrumb selection
    const filteredControls = useMemo(() => {
        let filtered = controls;

        if (selectedControlSetFilter) {
            filtered = filtered.filter(c => c.control_set_id === selectedControlSetFilter);
        }

        if (selectedCategoryFilter) {
            filtered = filtered.filter(c => c.category === selectedCategoryFilter);
        }

        return filtered;
    }, [controls, selectedControlSetFilter, selectedCategoryFilter]);

    // Dashboard statistics
    const dashboardStats = useMemo(() => {
        const totalControls = controls.length;
        const statusCounts: Record<string, number> = {};
        const controlSetCounts: Record<string, number> = {};

        controls.forEach(control => {
            const statusName = control.control_status_name || 'Unknown';
            statusCounts[statusName] = (statusCounts[statusName] || 0) + 1;

            const setName = control.control_set_name || 'Unknown';
            controlSetCounts[setName] = (controlSetCounts[setName] || 0) + 1;
        });

        const implementedCount = statusCounts['Implemented'] || 0;
        const notImplementedCount = statusCounts['Not Implemented'] || 0;
        const partiallyImplementedCount = statusCounts['Partially Implemented'] || 0;

        return {
            totalControls,
            implementedCount,
            notImplementedCount,
            partiallyImplementedCount,
            statusCounts,
            controlSetCounts
        };
    }, [controls]);

    // Status color mapping
    const getStatusColor = (status: string): string => {
        switch (status?.toLowerCase()) {
            case 'implemented': return '#52c41a';
            case 'partially implemented': return '#faad14';
            case 'not implemented': return '#ff4d4f';
            case 'n/a': return '#8c8c8c';
            default: return '#8c8c8c';
        }
    };

    // Status icon mapping
    const getStatusIcon = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'implemented': return <CheckCircleOutlined />;
            case 'partially implemented': return <ClockCircleOutlined />;
            case 'not implemented': return <ExclamationCircleOutlined />;
            case 'n/a': return <MinusCircleOutlined />;
            default: return <MinusCircleOutlined />;
        }
    };

    // Search filtered controls
    const searchFilteredControls = filteredControls.filter(control =>
        control.code?.toLowerCase().includes(controlSearchText.toLowerCase()) ||
        control.name?.toLowerCase().includes(controlSearchText.toLowerCase()) ||
        control.category?.toLowerCase().includes(controlSearchText.toLowerCase()) ||
        control.control_set_name?.toLowerCase().includes(controlSearchText.toLowerCase()) ||
        control.control_status_name?.toLowerCase().includes(controlSearchText.toLowerCase())
    );

    // Control Card component
    const ControlCard = ({ control }: { control: any }) => {
        const handleCardClick = () => {
            setSelectedControl(control.id);
            setCode(control.code);
            setName(control.name);
            setDescription(control.description || '');
            setCategory(control.category || '');
            setOwner(control.owner || '');
            setControlSetId(control.control_set_id);
            setControlStatusId(control.control_status_id);
            setShowForm(true);
        };

        return (
            <Card
                hoverable
                style={{ height: '100%' }}
                bodyStyle={{ padding: '16px' }}
                onClick={handleCardClick}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <Tag color="blue">{control.code}</Tag>
                    <span style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '12px',
                        color: getStatusColor(control.control_status_name)
                    }}>
                        {getStatusIcon(control.control_status_name)}
                        {control.control_status_name}
                    </span>
                </div>

                <h4 style={{ margin: '8px 0', fontSize: '15px', fontWeight: 500 }}>
                    {control.name}
                </h4>

                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '8px' }}>
                    {control.control_set_name && (
                        <Tag color="purple">{control.control_set_name}</Tag>
                    )}
                    {control.category && (
                        <Tag color="default">{control.category}</Tag>
                    )}
                </div>

                {control.owner && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
                        <div style={{
                            width: 24,
                            height: 24,
                            borderRadius: '50%',
                            backgroundColor: '#fce4ec',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: '#c2185b',
                            fontSize: '12px',
                            fontWeight: 500
                        }}>
                            {control.owner.charAt(0).toUpperCase()}
                        </div>
                        <span style={{ color: '#8c8c8c', fontSize: '13px' }}>{control.owner}</span>
                    </div>
                )}

                {control.description && (
                    <p style={{
                        margin: '8px 0 0 0',
                        color: '#8c8c8c',
                        fontSize: '13px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                    }}>
                        {control.description}
                    </p>
                )}
            </Card>
        );
    };

    // Grid columns
    const columns = [
        {
            title: 'Code',
            dataIndex: 'code',
            key: 'code',
            sorter: (a: any, b: any) => a.code.localeCompare(b.code),
            width: 120
        },
        {
            title: 'Control Name',
            dataIndex: 'name',
            key: 'name',
            sorter: (a: any, b: any) => a.name.localeCompare(b.name),
            render: (text: string) => (
                <span style={{ color: '#1890ff', cursor: 'pointer' }}>{text}</span>
            )
        },
        {
            title: 'Category',
            dataIndex: 'category',
            key: 'category',
            filters: categories.map(cat => ({ text: cat, value: cat })),
            onFilter: (value: any, record: any) => record.category === value,
            width: 180
        },
        {
            title: 'Owner',
            dataIndex: 'owner',
            key: 'owner',
            width: 120,
            render: (text: string) => text ? (
                <div style={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    backgroundColor: '#fce4ec',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#c2185b',
                    fontWeight: 500
                }}>
                    {text.charAt(0).toUpperCase()}
                </div>
            ) : '-'
        },
        {
            title: 'Status',
            dataIndex: 'control_status_name',
            key: 'control_status_name',
            filters: controlStatuses.map(s => ({ text: s.status_name, value: s.status_name })),
            onFilter: (value: any, record: any) => record.control_status_name === value,
            width: 160,
            render: (text: string) => (
                <span style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    color: getStatusColor(text)
                }}>
                    <span style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        backgroundColor: getStatusColor(text)
                    }} />
                    {text}
                </span>
            )
        },
        {
            title: 'Control Set',
            dataIndex: 'control_set_name',
            key: 'control_set_name',
            filters: controlSets.map(s => ({ text: s.name, value: s.name })),
            onFilter: (value: any, record: any) => record.control_set_name === value,
            width: 180
        }
    ];

    // Tab items
    const tabItems = [
        {
            key: 'dashboard',
            label: (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <DashboardOutlined />
                    Dashboard
                </span>
            ),
            children: (
                <div>
                    {/* Summary Statistics Cards */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', marginBottom: '24px' }}>
                        <StatCard
                            title="Total Controls"
                            value={dashboardStats.totalControls}
                            icon={<SafetyCertificateOutlined />}
                            iconColor="#0f386a"
                            iconBgColor="#EBF4FC"
                            onClick={() => setActiveTab('registry')}
                        />
                        <StatCard
                            title="Implemented"
                            value={dashboardStats.implementedCount}
                            icon={<CheckCircleOutlined />}
                            iconColor="#10b981"
                            iconBgColor="#f0fdfa"
                            onClick={() => setActiveTab('registry')}
                        />
                        <StatCard
                            title="Partially Implemented"
                            value={dashboardStats.partiallyImplementedCount}
                            icon={<ClockCircleOutlined />}
                            iconColor="#f59e0b"
                            iconBgColor="#fffbeb"
                            onClick={() => setActiveTab('registry')}
                        />
                        <StatCard
                            title="Not Implemented"
                            value={dashboardStats.notImplementedCount}
                            icon={<ExclamationCircleOutlined />}
                            iconColor="#dc2626"
                            iconBgColor="#fef2f2"
                            onClick={() => setActiveTab('registry')}
                        />
                    </div>

                    {/* Quick Actions */}
                    <QuickActionsPanel title="Quick Actions">
                        <QuickActionButton
                            label="Add New Control"
                            icon={<PlusOutlined />}
                            onClick={() => {
                                handleClear(false);
                                setShowForm(true);
                                setActiveTab('registry');
                            }}
                            variant="primary"
                        />
                        <QuickActionButton
                            label="View Control List"
                            icon={<UnorderedListOutlined />}
                            onClick={() => setActiveTab('registry')}
                            variant="secondary"
                        />
                        <QuickActionButton
                            label="Import from Excel"
                            icon={<DatabaseOutlined />}
                            onClick={() => window.location.href = '/controls_library'}
                            variant="success"
                        />
                    </QuickActionsPanel>

                    {/* Status Distribution */}
                    <Row gutter={[24, 24]} style={{ marginTop: '24px' }}>
                        <Col xs={24} lg={12}>
                            <DashboardSection title="Implementation Status">
                                {dashboardStats.totalControls === 0 ? (
                                    <div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>
                                        No controls registered yet
                                    </div>
                                ) : (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                        {['Implemented', 'Partially Implemented', 'Not Implemented', 'N/A'].map(status => {
                                            const count = dashboardStats.statusCounts[status] || 0;
                                            const percent = dashboardStats.totalControls > 0
                                                ? Math.round((count / dashboardStats.totalControls) * 100)
                                                : 0;
                                            return (
                                                <div key={status}>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                        <span style={{ fontWeight: 500, color: getStatusColor(status), display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                            {getStatusIcon(status)} {status}
                                                        </span>
                                                        <span style={{ color: '#8c8c8c' }}>
                                                            {count} control{count !== 1 ? 's' : ''} ({percent}%)
                                                        </span>
                                                    </div>
                                                    <Progress
                                                        percent={percent}
                                                        strokeColor={getStatusColor(status)}
                                                        showInfo={false}
                                                        size="small"
                                                    />
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </DashboardSection>
                        </Col>

                        <Col xs={24} lg={12}>
                            <DashboardSection title="Control Sets">
                                {Object.keys(dashboardStats.controlSetCounts).length === 0 ? (
                                    <div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>
                                        No control sets yet
                                    </div>
                                ) : (
                                    <Row gutter={[12, 12]}>
                                        {Object.entries(dashboardStats.controlSetCounts).map(([setName, count]) => {
                                            const percent = dashboardStats.totalControls > 0
                                                ? Math.round((count / dashboardStats.totalControls) * 100)
                                                : 0;
                                            return (
                                                <Col xs={12} key={setName}>
                                                    <Card
                                                        size="small"
                                                        style={{
                                                            borderRadius: '8px',
                                                            borderLeft: '4px solid #1890ff',
                                                            background: '#fafafa'
                                                        }}
                                                    >
                                                        <div style={{ fontWeight: 500, fontSize: '13px', marginBottom: '4px' }}>{setName}</div>
                                                        <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#262626' }}>
                                                            {count}
                                                        </div>
                                                        <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                                                            {percent}% of total
                                                        </div>
                                                    </Card>
                                                </Col>
                                            );
                                        })}
                                    </Row>
                                )}
                            </DashboardSection>
                        </Col>
                    </Row>
                </div>
            )
        },
        {
            key: 'registry',
            label: (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <UnorderedListOutlined />
                    Control Registry
                    <Tag color="blue">{controls.length}</Tag>
                </span>
            ),
            children: (
                <div>
                    {/* Breadcrumb Navigation */}
                    <Breadcrumb style={{ marginBottom: '16px' }}>
                        <Breadcrumb.Item>
                            <a onClick={() => {
                                setSelectedControlSetFilter(null);
                                setSelectedCategoryFilter(null);
                            }}>
                                All Control Sets
                            </a>
                        </Breadcrumb.Item>
                        {selectedControlSetFilter && (
                            <Breadcrumb.Item>
                                <a onClick={() => setSelectedCategoryFilter(null)}>
                                    {controlSets.find(s => s.id === selectedControlSetFilter)?.name || 'Unknown Set'}
                                </a>
                            </Breadcrumb.Item>
                        )}
                        {selectedCategoryFilter && (
                            <Breadcrumb.Item>{selectedCategoryFilter}</Breadcrumb.Item>
                        )}
                    </Breadcrumb>

                    {/* Control Data Table Section */}
                    <div className="page-section">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <Input
                                    placeholder="Search controls..."
                                    prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                    value={controlSearchText}
                                    onChange={(e) => setControlSearchText(e.target.value)}
                                    style={{ width: '250px' }}
                                />
                                <div style={{ display: 'flex', border: '1px solid #d9d9d9', borderRadius: '6px', overflow: 'hidden' }}>
                                    <button
                                        onClick={() => setControlViewMode('grid')}
                                        style={{
                                            border: 'none',
                                            padding: '6px 12px',
                                            cursor: 'pointer',
                                            backgroundColor: controlViewMode === 'grid' ? '#1890ff' : 'white',
                                            color: controlViewMode === 'grid' ? 'white' : '#595959',
                                        }}
                                    >
                                        <AppstoreOutlined />
                                    </button>
                                    <button
                                        onClick={() => setControlViewMode('list')}
                                        style={{
                                            border: 'none',
                                            borderLeft: '1px solid #d9d9d9',
                                            padding: '6px 12px',
                                            cursor: 'pointer',
                                            backgroundColor: controlViewMode === 'list' ? '#1890ff' : 'white',
                                            color: controlViewMode === 'list' ? 'white' : '#595959',
                                        }}
                                    >
                                        <UnorderedListOutlined />
                                    </button>
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <button
                                    className="add-button"
                                    data-tour-id="qs-control-add-button"
                                    onClick={() => {
                                        handleClear(false);
                                        setShowForm(true);
                                    }}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    <PlusOutlined /> Add New Control
                                </button>
                            </div>
                        </div>

                        {searchFilteredControls.length === 0 ? (
                            <Empty description="No controls found" />
                        ) : controlViewMode === 'grid' ? (
                            <Row gutter={[16, 16]}>
                                {searchFilteredControls.map(control => (
                                    <Col key={control.id} xs={24} sm={12} md={8} lg={6}>
                                        <ControlCard control={control} />
                                    </Col>
                                ))}
                            </Row>
                        ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <Table
                                columns={columns}
                                dataSource={searchFilteredControls}
                                showSorterTooltip={{ target: 'sorter-icon' }}
                                onRow={(record) => {
                                    return {
                                        onClick: () => {
                                            setSelectedControl(record.id);
                                            setCode(record.code);
                                            setName(record.name);
                                            setDescription(record.description || '');
                                            setCategory(record.category || '');
                                            setOwner(record.owner || '');
                                            setControlSetId(record.control_set_id);
                                            setControlStatusId(record.control_status_id);
                                            setShowForm(true);
                                        },
                                        style: {
                                            cursor: 'pointer',
                                            backgroundColor: selectedControl === record.id ? '#e6f7ff' : undefined
                                        }
                                    };
                                }}
                                rowKey="id"
                                pagination={{
                                    showSizeChanger: true,
                                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} controls`,
                                }}
                                scroll={{ x: 900 }}
                            />
                        </div>
                        )}
                    </div>
                </div>
            )
        },
        {
            key: 'connections',
            label: (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <LinkOutlined />
                    Connections
                </span>
            ),
            children: (() => {
                const selectedControlObj = controls.find(c => c.id === selectedConnectionControl);
                const connRiskStats = (() => {
                    const stats = { total: 0, severe: 0, high: 0, medium: 0, low: 0 };
                    linkedRisks.forEach((r: any) => {
                        stats.total++;
                        const sev = (r.risk_severity || '').toLowerCase();
                        if (sev === 'severe' || sev === 'critical') stats.severe++;
                        else if (sev === 'high') stats.high++;
                        else if (sev === 'medium') stats.medium++;
                        else stats.low++;
                    });
                    return stats;
                })();

                return (
                <div className="page-section">
                    {/* Control Selector */}
                    <div style={{ marginBottom: 24 }}>
                        <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                            Select Control to Manage Connections
                        </label>
                        <Select
                            showSearch
                            placeholder="Select a control..."
                            options={controls.map(control => ({
                                label: `${control.code}: ${control.name}${control.control_set_name ? ` (${control.control_set_name})` : ''}`,
                                value: control.id,
                            }))}
                            value={selectedConnectionControl}
                            onChange={(value) => setSelectedConnectionControl(value)}
                            filterOption={(input, option) =>
                                (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                            }
                            style={{ width: '100%', maxWidth: 500 }}
                            allowClear
                        />
                    </div>

                    {selectedConnectionControl && selectedControlObj ? (
                        <>
                            {/* Control Context Banner */}
                            <div style={{
                                background: 'linear-gradient(135deg, #1a365d 0%, #0f386a 100%)',
                                borderRadius: '10px',
                                padding: '16px 24px',
                                marginBottom: 24,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                flexWrap: 'wrap',
                                gap: '12px',
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <SafetyCertificateOutlined style={{ fontSize: 22, color: '#fff' }} />
                                    <div>
                                        <div style={{ color: '#fff', fontWeight: 600, fontSize: '15px' }}>
                                            {selectedControlObj.code}: {selectedControlObj.name}
                                        </div>
                                        {selectedControlObj.control_set_name && (
                                            <Tag color="rgba(255,255,255,0.2)" style={{ color: '#fff', border: '1px solid rgba(255,255,255,0.3)', marginTop: 4 }}>
                                                {selectedControlObj.control_set_name}
                                            </Tag>
                                        )}
                                    </div>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                    {selectedControlObj.control_status_name && (
                                        <Tag color={getStatusColor(selectedControlObj.control_status_name)} style={{ fontWeight: 600 }}>
                                            {getStatusIcon(selectedControlObj.control_status_name)} {selectedControlObj.control_status_name}
                                        </Tag>
                                    )}
                                    {selectedControlObj.category && (
                                        <Tag color="default" style={{ background: 'rgba(255,255,255,0.15)', color: '#fff', border: '1px solid rgba(255,255,255,0.3)' }}>
                                            {selectedControlObj.category}
                                        </Tag>
                                    )}
                                </div>
                            </div>

                            {/* Framework Selector */}
                            <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
                                <label style={{ fontWeight: 500, whiteSpace: 'nowrap' }}>Framework:</label>
                                <Select
                                    showSearch
                                    placeholder="Select a framework to scope connections..."
                                    options={filteredFrameworks.map(fw => ({ label: fw.name, value: fw.id }))}
                                    value={connectionFrameworkId}
                                    onChange={(value) => setConnectionFrameworkId(value)}
                                    filterOption={(input, option) =>
                                        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                    }
                                    style={{ width: '100%', maxWidth: 400 }}
                                    allowClear
                                />
                            </div>

                            {connectionFrameworkId ? (
                            <Row gutter={[24, 24]} align="top">
                                {/* Left Column: Stacked Connection Boards */}
                                <Col xs={24} lg={12}>
                                    <div style={{ marginBottom: 16 }}>
                                        <ConnectionBoard
                                            title="Risks Mitigated by Control"
                                            sourceLabel="Control"
                                            targetLabel="Risk"
                                            relationshipLabel="mitigates"
                                            availableItems={risks.map(risk => ({
                                                id: risk.id,
                                                risk_code: risk.risk_code,
                                                risk_category_name: risk.risk_category_name,
                                                risk_category_description: risk.risk_category_description,
                                                risk_severity: risk.risk_severity,
                                                risk_status: risk.risk_status,
                                            }))}
                                            linkedItems={linkedRisks.map(risk => ({
                                                id: risk.id,
                                                risk_code: risk.risk_code,
                                                risk_category_name: risk.risk_category_name,
                                                risk_category_description: risk.risk_category_description,
                                                risk_severity: risk.risk_severity,
                                                risk_status: risk.risk_status,
                                            }))}
                                            loading={false}
                                            getItemDisplayName={(item) => {
                                                const risk = item as { risk_code?: string | null; risk_category_name?: string };
                                                return risk.risk_code
                                                    ? `${risk.risk_code}: ${risk.risk_category_name || 'Unknown'}`
                                                    : risk.risk_category_name || 'Unknown Risk';
                                            }}
                                            getItemDescription={(item) => {
                                                const risk = item as { risk_category_description?: string };
                                                return risk.risk_category_description || null;
                                            }}
                                            getItemTags={(item) => {
                                                const risk = item as { risk_severity?: string | null; risk_status?: string | null };
                                                const tags: { label: string; color: string }[] = [];
                                                if (risk.risk_severity) {
                                                    const severityColors: Record<string, string> = {
                                                        'Severe': 'red', 'High': 'orange', 'Medium': 'gold', 'Low': 'green',
                                                    };
                                                    tags.push({ label: risk.risk_severity, color: severityColors[risk.risk_severity] || 'default' });
                                                }
                                                if (risk.risk_status) {
                                                    tags.push({ label: risk.risk_status, color: 'blue' });
                                                }
                                                return tags;
                                            }}
                                            onLink={async (riskIds) => {
                                                if (!connectionFrameworkId) return;
                                                for (const riskId of riskIds) {
                                                    const success = await linkControlToRisk(selectedConnectionControl, riskId, connectionFrameworkId);
                                                    if (!success) { api.error({ message: 'Link Failed', description: 'Failed to link control to risk', duration: 4 }); return; }
                                                }
                                                api.success({ message: 'Risks Linked', description: `Successfully linked ${riskIds.length} risk(s) to the control`, duration: 4 });
                                                fetchLinkedRisks(selectedConnectionControl, connectionFrameworkId);
                                            }}
                                            onUnlink={async (riskIds) => {
                                                if (!connectionFrameworkId) return;
                                                for (const riskId of riskIds) {
                                                    const success = await unlinkControlFromRisk(selectedConnectionControl, riskId, connectionFrameworkId);
                                                    if (!success) { api.error({ message: 'Unlink Failed', description: 'Failed to unlink control from risk', duration: 4 }); return; }
                                                }
                                                api.success({ message: 'Risks Unlinked', description: `Successfully unlinked ${riskIds.length} risk(s) from the control`, duration: 4 });
                                                fetchLinkedRisks(selectedConnectionControl, connectionFrameworkId);
                                            }}
                                            height={250}
                                        />
                                    </div>
                                    <ConnectionBoard
                                        title="Policies Governing Control"
                                        sourceLabel="Policy"
                                        targetLabel="Control"
                                        relationshipLabel="governs"
                                        itemLabel="Policy"
                                        availableItems={policies.map(policy => ({ id: policy.id, title: policy.title, owner: policy.owner, status: policy.status }))}
                                        linkedItems={linkedPolicies.map(policy => ({ id: policy.id, title: policy.title, owner: policy.owner, status: policy.status }))}
                                        loading={false}
                                        getItemDisplayName={(item) => { const policy = item as { title: string }; return policy.title; }}
                                        getItemDescription={(item) => { const policy = item as { owner?: string | null }; return policy.owner ? `Owner: ${policy.owner}` : null; }}
                                        getItemTags={(item) => {
                                            const policy = item as { status?: string | null };
                                            const tags: { label: string; color: string }[] = [];
                                            if (policy.status) {
                                                const statusColors: Record<string, string> = { 'Draft': 'default', 'Review': 'orange', 'Approved': 'green', 'Active': 'blue', 'Retired': 'red' };
                                                tags.push({ label: policy.status, color: statusColors[policy.status] || 'default' });
                                            }
                                            return tags;
                                        }}
                                        onLink={async (policyIds) => {
                                            if (!connectionFrameworkId) return;
                                            for (const policyId of policyIds) {
                                                const success = await linkControlToPolicy(selectedConnectionControl, policyId, connectionFrameworkId);
                                                if (!success) { api.error({ message: 'Link Failed', description: 'Failed to link control to policy', duration: 4 }); return; }
                                            }
                                            api.success({ message: 'Policies Linked', description: `Successfully linked ${policyIds.length} policy(ies) to the control`, duration: 4 });
                                            fetchLinkedPolicies(selectedConnectionControl, connectionFrameworkId);
                                        }}
                                        onUnlink={async (policyIds) => {
                                            if (!connectionFrameworkId) return;
                                            for (const policyId of policyIds) {
                                                const success = await unlinkControlFromPolicy(selectedConnectionControl, policyId, connectionFrameworkId);
                                                if (!success) { api.error({ message: 'Unlink Failed', description: 'Failed to unlink control from policy', duration: 4 }); return; }
                                            }
                                            api.success({ message: 'Policies Unlinked', description: `Successfully unlinked ${policyIds.length} policy(ies) from the control`, duration: 4 });
                                            fetchLinkedPolicies(selectedConnectionControl, connectionFrameworkId);
                                        }}
                                        height={250}
                                    />
                                </Col>

                                {/* Right Column: Intelligence Panel */}
                                <Col xs={24} lg={12}>
                                    <Card style={{ borderRadius: '10px', height: '100%' }} bodyStyle={{ padding: 0 }}>
                                        <Tabs
                                            defaultActiveKey="riskCoverage"
                                            style={{ padding: '0 16px' }}
                                            items={[
                                                {
                                                    key: 'riskCoverage',
                                                    label: (
                                                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                            <AlertOutlined />
                                                            Risk Coverage
                                                            {connRiskStats.total > 0 && <Tag color="red" style={{ marginLeft: 4 }}>{connRiskStats.total}</Tag>}
                                                        </span>
                                                    ),
                                                    children: (
                                                        <div style={{ paddingBottom: 16 }}>
                                                            <div style={{ display: 'flex', gap: '8px', marginBottom: 16, flexWrap: 'wrap' }}>
                                                                <div style={{ flex: 1, minWidth: 70, textAlign: 'center', background: '#f0f5ff', borderRadius: 8, padding: '8px 4px' }}>
                                                                    <div style={{ fontSize: 20, fontWeight: 700, color: '#1890ff' }}>{connRiskStats.total}</div>
                                                                    <div style={{ fontSize: 11, color: '#8c8c8c' }}>Total</div>
                                                                </div>
                                                                <div style={{ flex: 1, minWidth: 70, textAlign: 'center', background: '#fff1f0', borderRadius: 8, padding: '8px 4px' }}>
                                                                    <div style={{ fontSize: 20, fontWeight: 700, color: '#ff4d4f' }}>{connRiskStats.severe}</div>
                                                                    <div style={{ fontSize: 11, color: '#8c8c8c' }}>Critical</div>
                                                                </div>
                                                                <div style={{ flex: 1, minWidth: 70, textAlign: 'center', background: '#fff7e6', borderRadius: 8, padding: '8px 4px' }}>
                                                                    <div style={{ fontSize: 20, fontWeight: 700, color: '#fa8c16' }}>{connRiskStats.high}</div>
                                                                    <div style={{ fontSize: 11, color: '#8c8c8c' }}>High</div>
                                                                </div>
                                                                <div style={{ flex: 1, minWidth: 70, textAlign: 'center', background: '#f6ffed', borderRadius: 8, padding: '8px 4px' }}>
                                                                    <div style={{ fontSize: 20, fontWeight: 700, color: '#52c41a' }}>{connRiskStats.medium + connRiskStats.low}</div>
                                                                    <div style={{ fontSize: 11, color: '#8c8c8c' }}>Med/Low</div>
                                                                </div>
                                                            </div>
                                                            {linkedRisks.length > 0 ? (
                                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                                    {linkedRisks.map((risk: any) => {
                                                                        const severityColors: Record<string, string> = { 'Severe': 'red', 'Critical': 'red', 'High': 'orange', 'Medium': 'gold', 'Low': 'green' };
                                                                        return (
                                                                            <div key={risk.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: '#fafafa', borderRadius: 6, border: '1px solid #f0f0f0' }}>
                                                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                                                    <div style={{ fontWeight: 500, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                                        {risk.risk_code ? `${risk.risk_code}: ` : ''}{risk.risk_category_name}
                                                                                    </div>
                                                                                    {risk.risk_category_description && (
                                                                                        <div style={{ fontSize: 11, color: '#8c8c8c', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{risk.risk_category_description}</div>
                                                                                    )}
                                                                                </div>
                                                                                <div style={{ display: 'flex', gap: 4, marginLeft: 8, flexShrink: 0 }}>
                                                                                    {risk.risk_severity && <Tag color={severityColors[risk.risk_severity] || 'default'}>{risk.risk_severity}</Tag>}
                                                                                    {risk.risk_status && <Tag color="blue">{risk.risk_status}</Tag>}
                                                                                </div>
                                                                            </div>
                                                                        );
                                                                    })}
                                                                </div>
                                                            ) : (
                                                                <Empty description="No risks linked. Use the board on the left to link risks." image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ margin: '24px 0' }} />
                                                            )}
                                                        </div>
                                                    ),
                                                },
                                                {
                                                    key: 'policyAlignment',
                                                    label: (
                                                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                            <AuditOutlined />
                                                            Policy Alignment
                                                            {linkedPolicies.length > 0 && <Tag color="purple" style={{ marginLeft: 4 }}>{linkedPolicies.length}</Tag>}
                                                        </span>
                                                    ),
                                                    children: (
                                                        <div style={{ paddingBottom: 16 }}>
                                                            {linkedPolicies.length > 0 ? (
                                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                                    {linkedPolicies.map((policy: any) => {
                                                                        const statusColors: Record<string, string> = { 'Draft': 'default', 'Review': 'orange', 'Approved': 'green', 'Active': 'blue', 'Retired': 'red' };
                                                                        return (
                                                                            <div key={policy.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: '#fafafa', borderRadius: 6, border: '1px solid #f0f0f0' }}>
                                                                                <div style={{ flex: 1, minWidth: 0 }}>
                                                                                    <div style={{ fontWeight: 500, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{policy.title}</div>
                                                                                    {policy.owner && <div style={{ fontSize: 11, color: '#8c8c8c' }}>Owner: {policy.owner}</div>}
                                                                                </div>
                                                                                {policy.status && <Tag color={statusColors[policy.status] || 'default'} style={{ marginLeft: 8, flexShrink: 0 }}>{policy.status}</Tag>}
                                                                            </div>
                                                                        );
                                                                    })}
                                                                </div>
                                                            ) : (
                                                                <Empty description="No policies linked. Use the board on the left to link policies." image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ margin: '24px 0' }} />
                                                            )}
                                                        </div>
                                                    ),
                                                },
                                                {
                                                    key: 'profile',
                                                    label: (
                                                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                            <SafetyCertificateOutlined />
                                                            Control Profile
                                                        </span>
                                                    ),
                                                    children: (
                                                        <div style={{ paddingBottom: 16 }}>
                                                            <div style={{ display: 'flex', gap: '8px', marginBottom: 16, flexWrap: 'wrap' }}>
                                                                <Tag color="red">{linkedRisks.length} Risk{linkedRisks.length !== 1 ? 's' : ''}</Tag>
                                                                <Tag color="purple">{linkedPolicies.length} Polic{linkedPolicies.length !== 1 ? 'ies' : 'y'}</Tag>
                                                            </div>

                                                            {selectedControlObj.control_set_name && (
                                                                <div style={{ marginBottom: 16 }}>
                                                                    <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Control Set</div>
                                                                    <div style={{ fontSize: 13, color: '#262626' }}>{selectedControlObj.control_set_name}</div>
                                                                </div>
                                                            )}

                                                            {selectedControlObj.category && (
                                                                <div style={{ marginBottom: 16 }}>
                                                                    <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Category</div>
                                                                    <div style={{ fontSize: 13, color: '#262626' }}>{selectedControlObj.category}</div>
                                                                </div>
                                                            )}

                                                            <div style={{ marginBottom: 16 }}>
                                                                <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Status</div>
                                                                <Tag color={getStatusColor(selectedControlObj.control_status_name || '')}>{selectedControlObj.control_status_name || 'Unknown'}</Tag>
                                                            </div>

                                                            {selectedControlObj.owner && (
                                                                <div style={{ marginBottom: 16 }}>
                                                                    <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Owner</div>
                                                                    <div style={{ fontSize: 13, color: '#262626' }}>{selectedControlObj.owner}</div>
                                                                </div>
                                                            )}

                                                            {selectedControlObj.description && (
                                                                <div style={{ marginBottom: 16 }}>
                                                                    <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Description</div>
                                                                    <div style={{ fontSize: 13, color: '#262626', lineHeight: 1.6 }}>{selectedControlObj.description}</div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    ),
                                                },
                                                {
                                                    key: 'recommendations',
                                                    label: (
                                                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                            <BulbOutlined />
                                                            Recommendations
                                                        </span>
                                                    ),
                                                    children: (
                                                        <div style={{ paddingBottom: 16 }}>
                                                            {/* Guidance Card */}
                                                            <div style={{
                                                                background: '#f0f7ff',
                                                                borderRadius: 8,
                                                                padding: 12,
                                                                marginBottom: 16,
                                                                display: 'flex',
                                                                gap: '10px',
                                                                alignItems: 'flex-start',
                                                            }}>
                                                                <BulbOutlined style={{ fontSize: 18, color: '#1890ff', marginTop: 2 }} />
                                                                <div style={{ fontSize: 13, color: '#262626' }}>
                                                                    Import policy templates and automatically link them to this control for governance alignment.
                                                                </div>
                                                            </div>

                                                            {/* Policy Templates — filtered by keyword relevance */}
                                                            {(() => {
                                                                const { relevant, other } = filterByRelevance(
                                                                    policyTemplates,
                                                                    [selectedControlObj.name, selectedControlObj.description, selectedControlObj.category, selectedControlObj.control_set_name],
                                                                    (t) => [t.title, t.filename, t.policy_code]
                                                                );
                                                                const renderTemplateCard = (template: typeof policyTemplates[0]) => (
                                                                    <div key={template.id} style={{
                                                                        border: '1px solid #f0f0f0',
                                                                        borderRadius: 8,
                                                                        padding: '12px 16px',
                                                                        display: 'flex',
                                                                        alignItems: 'center',
                                                                        justifyContent: 'space-between',
                                                                        gap: 12,
                                                                    }}>
                                                                        <div style={{ flex: 1, minWidth: 0 }}>
                                                                            <div style={{ fontWeight: 500, fontSize: 13 }}>
                                                                                {template.title || template.filename}
                                                                            </div>
                                                                            <div style={{ display: 'flex', gap: 4, marginTop: 4, flexWrap: 'wrap' }}>
                                                                                {template.policy_code && <Tag color="blue">{template.policy_code}</Tag>}
                                                                                {template.source && <Tag color="default">{template.source}</Tag>}
                                                                            </div>
                                                                        </div>
                                                                        <Button
                                                                            type="primary"
                                                                            ghost
                                                                            size="small"
                                                                            loading={controlRecommendationLoading[template.id]}
                                                                            onClick={() => handleImportAndLinkPolicyRecommendation(template.id)}
                                                                            style={{ flexShrink: 0 }}
                                                                        >
                                                                            Import & Link
                                                                        </Button>
                                                                    </div>
                                                                );

                                                                if (policyTemplates.length === 0) {
                                                                    return <Empty description="No policy templates available" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ margin: '24px 0' }} />;
                                                                }

                                                                return (
                                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                                        {relevant.length > 0 ? (
                                                                            <>
                                                                                {relevant.map(renderTemplateCard)}
                                                                                {other.length > 0 && (
                                                                                    <Collapse size="small" style={{ marginTop: 8 }} items={[{
                                                                                        key: 'other',
                                                                                        label: <span style={{ fontSize: 12, color: '#8c8c8c' }}>Other policies ({other.length})</span>,
                                                                                        children: <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>{other.map(renderTemplateCard)}</div>,
                                                                                    }]} />
                                                                                )}
                                                                            </>
                                                                        ) : (
                                                                            policyTemplates.map(renderTemplateCard)
                                                                        )}
                                                                    </div>
                                                                );
                                                            })()}
                                                        </div>
                                                    ),
                                                },
                                            ]}
                                        />
                                    </Card>
                                </Col>
                            </Row>
                            ) : (
                                <Empty description="Select a framework above to manage connections" style={{ marginTop: 40 }} />
                            )}
                        </>
                    ) : (
                        <Empty
                            description="Select a control to manage its connections"
                            style={{ marginTop: 60 }}
                        />
                    )}
                </div>
                );
            })()
        }
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
                            <SafetyCertificateOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Controls Management"
                                infoContent={ControlsInfo}
                                className="page-title"
                            />
                        </div>
                    </div>

                    {/* Tabbed Content */}
                    <Tabs
                        activeKey={activeTab}
                        onChange={setActiveTab}
                        items={tabItems}
                        size="large"
                        style={{ marginTop: '-8px' }}
                    />

                    {/* Control Registration Modal */}
                    <Modal
                        title={
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {selectedControl ? (
                                    <EditOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                                ) : (
                                    <PlusOutlined style={{ fontSize: '20px', color: '#52c41a' }} />
                                )}
                                <span>{selectedControl ? 'Edit Control' : 'Add New Control'}</span>
                                {selectedControl && <Tag color="blue">Editing</Tag>}
                            </div>
                        }
                        open={showForm}
                        onCancel={() => handleClear(true)}
                        width={800}
                        footer={
                            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                {selectedControl && (
                                    <button
                                        className="delete-button"
                                        onClick={handleDelete}
                                        style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f', color: 'white' }}
                                    >
                                        Delete Control
                                    </button>
                                )}
                                {selectedControl && (
                                    <button
                                        className="secondary-button"
                                        onClick={() => handleClear(false)}
                                    >
                                        Create New Instead
                                    </button>
                                )}
                                <button
                                    className="secondary-button"
                                    onClick={() => handleClear(true)}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="add-button"
                                    onClick={handleSave}
                                    style={{
                                        backgroundColor: selectedControl ? '#1890ff' : '#52c41a',
                                        borderColor: selectedControl ? '#1890ff' : '#52c41a'
                                    }}
                                >
                                    {selectedControl ? 'Update Control' : 'Save Control'}
                                </button>
                            </div>
                        }
                    >
                        <p style={{ color: '#8c8c8c', fontSize: '14px', marginBottom: '24px' }}>
                            {selectedControl
                                ? 'Update the control details below and click "Update Control" to save changes.'
                                : 'Fill out the form below to register a new control.'}
                        </p>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label required">Code</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="e.g., HRM-1"
                                    value={code}
                                    onChange={(e) => setCode(e.target.value)}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label required">Control Set</label>
                                <Select
                                    showSearch
                                    placeholder="Select control set"
                                    onChange={(value) => setControlSetId(value)}
                                    options={controlSetOptions}
                                    filterOption={(input, option) => (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())}
                                    value={controlSetId}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label required">Status</label>
                                <Select
                                    showSearch
                                    placeholder="Select status"
                                    onChange={(value) => setControlStatusId(value)}
                                    options={statusOptions}
                                    filterOption={(input, option) => (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())}
                                    value={controlStatusId}
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group" style={{ flex: 2 }}>
                                <label className="form-label required">Control Name</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="Enter control name/description"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Owner</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="Control owner"
                                    value={owner}
                                    onChange={(e) => setOwner(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Category</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="e.g., Human Resources Management"
                                    value={category}
                                    onChange={(e) => setCategory(e.target.value)}
                                />
                            </div>
                            <div className="form-group" style={{ flex: 2 }}>
                                <label className="form-label">Description</label>
                                <textarea
                                    className="form-input"
                                    placeholder="Additional details about the control"
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    rows={3}
                                />
                            </div>
                        </div>
                    </Modal>
                </div>
            </div>
        </div>
    );
};

export default ControlRegistrationPage;
