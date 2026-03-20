import { Select, Table, notification, Modal, Tag, Upload, DatePicker, Card, Row, Col, Input, Empty } from "antd";
import type { TableColumnsType } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { FileSearchOutlined, PlusOutlined, CloseOutlined, EditOutlined, UploadOutlined, RobotOutlined, EyeOutlined, AppstoreOutlined, UnorderedListOutlined, SearchOutlined, LinkOutlined } from '@ant-design/icons';
import useEvidenceStore, { Evidence, EvidenceType, EvidenceStatus, CollectionMethod } from "../store/useEvidenceStore.ts";
import usePolicyStore from "../store/usePolicyStore.ts";
import useControlStore from "../store/useControlStore.ts";
import useUserStore from "../store/useUserStore.ts";
import { useEffect, useState } from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import { EvidenceInfo } from "../constants/infoContent.tsx";
import dayjs from 'dayjs';
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const EvidencePage = () => {
    // Menu highlighting
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // View mode state
    const [evidenceViewMode, setEvidenceViewMode] = useState<'grid' | 'list'>('list');
    const [evidenceSearchText, setEvidenceSearchText] = useState('');

    // Store access
    const {
        evidence,
        fetchEvidence,
        addEvidenceLocal,
        updateEvidenceLocal,
        deleteEvidenceLocal,
        loading,
    } = useEvidenceStore();

    const { frameworks, fetchFrameworks } = usePolicyStore();
    const { controls, fetchControls } = useControlStore();
    const { current_user } = useUserStore();

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    // Selected evidence state
    const [selectedEvidence, setSelectedEvidence] = useState<string | null>(null);

    // Form visibility state
    const [showForm, setShowForm] = useState<boolean>(false);

    // Preview modal state
    const [showPreview, setShowPreview] = useState<boolean>(false);
    const [previewEvidence, setPreviewEvidence] = useState<Evidence | null>(null);

    // Form state
    const [evidenceName, setEvidenceName] = useState('');
    const [evidenceDescription, setEvidenceDescription] = useState('');
    const [evidenceType, setEvidenceType] = useState<EvidenceType | undefined>(undefined);
    const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([]);
    const [selectedControls, setSelectedControls] = useState<string[]>([]);
    const [owner, setOwner] = useState('');
    const [collectedDate, setCollectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
    const [validUntil, setValidUntil] = useState<string | null>(null);
    const [status, setStatus] = useState<EvidenceStatus>('Valid');
    const [collectionMethod, setCollectionMethod] = useState<CollectionMethod>('Manual');
    const [auditNotes, setAuditNotes] = useState('');
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [fileName, setFileName] = useState<string>('');

    // Evidence type options
    const evidenceTypeOptions: { label: string; value: EvidenceType }[] = [
        { label: 'Screenshot', value: 'Screenshot' },
        { label: 'Report', value: 'Report' },
        { label: 'Log File', value: 'Log' },
        { label: 'Export', value: 'Export' },
        { label: 'AI Generated', value: 'AI Generated' },
        { label: 'Document', value: 'Document' },
        { label: 'Other', value: 'Other' },
    ];

    // Evidence status options
    const evidenceStatusOptions: { label: string; value: EvidenceStatus }[] = [
        { label: 'Valid', value: 'Valid' },
        { label: 'Expiring Soon', value: 'Expiring' },
        { label: 'Expired', value: 'Expired' },
        { label: 'Pending Review', value: 'Pending Review' },
    ];

    // Collection method options
    const collectionMethodOptions: { label: string; value: CollectionMethod }[] = [
        { label: 'Manual', value: 'Manual' },
        { label: 'Automated', value: 'Automated' },
        { label: 'AI Generated', value: 'AI Generated' },
    ];

    // Fetch data on component mount
    useEffect(() => {
        const fetchData = async () => {
            await fetchEvidence();
            await fetchFrameworks();
            await fetchControls();
        };
        fetchData();
    }, [fetchEvidence, fetchFrameworks, fetchControls]);

    // Handle form submission
    const handleSave = async () => {
        if (!evidenceName || !evidenceType) {
            api.error({
                message: 'Evidence Operation Failed',
                description: 'Please fill in all required fields (Name and Type)',
                duration: 4,
            });
            return;
        }

        const isUpdate = selectedEvidence !== null;
        const now = new Date().toISOString();

        // Get framework names and control names for display
        const frameworkNames = selectedFrameworks.map(id => {
            const framework = frameworks.find(f => f.id === id);
            return framework?.name || '';
        }).filter(Boolean);

        const controlNames = selectedControls.map(id => {
            const control = controls.find(c => c.id === id);
            if (!control) return '';
            return control.code ? `${control.code} - ${control.name}` : control.name;
        }).filter(Boolean);

        if (isUpdate && selectedEvidence) {
            // Update existing evidence
            updateEvidenceLocal(selectedEvidence, {
                name: evidenceName,
                description: evidenceDescription || null,
                evidence_type: evidenceType,
                framework_ids: selectedFrameworks,
                framework_names: frameworkNames,
                control_ids: selectedControls,
                control_names: controlNames,
                owner: owner || null,
                collected_date: collectedDate,
                valid_until: validUntil,
                status: status,
                collection_method: collectionMethod,
                audit_notes: auditNotes || null,
                file_name: uploadedFile?.name || fileName || null,
                updated_at: now,
            });

            api.success({
                message: 'Evidence Update Success',
                description: 'Evidence updated successfully',
                duration: 4,
            });
        } else {
            // Create new evidence
            const newEvidence: Evidence = {
                id: crypto.randomUUID(),
                name: evidenceName,
                description: evidenceDescription || null,
                evidence_type: evidenceType,
                file_name: uploadedFile?.name || null,
                file_url: null,
                file_size: uploadedFile?.size || null,
                framework_ids: selectedFrameworks,
                framework_names: frameworkNames,
                control_ids: selectedControls,
                control_names: controlNames,
                owner: owner || current_user?.name || null,
                collected_date: collectedDate,
                valid_until: validUntil,
                status: status,
                collection_method: collectionMethod,
                audit_notes: auditNotes || null,
                created_at: now,
                updated_at: now,
            };

            addEvidenceLocal(newEvidence);

            api.success({
                message: 'Evidence Creation Success',
                description: 'Evidence added successfully',
                duration: 4,
            });
        }

        handleClear(true);
    };

    // Clear form
    const handleClear = (hideForm: boolean = false) => {
        setEvidenceName('');
        setEvidenceDescription('');
        setEvidenceType(undefined);
        setSelectedFrameworks([]);
        setSelectedControls([]);
        setOwner('');
        setCollectedDate(new Date().toISOString().split('T')[0]);
        setValidUntil(null);
        setStatus('Valid');
        setCollectionMethod('Manual');
        setAuditNotes('');
        setUploadedFile(null);
        setFileName('');
        setSelectedEvidence(null);
        if (hideForm) {
            setShowForm(false);
        }
    };

    // Handle evidence deletion
    const handleDelete = async () => {
        if (!selectedEvidence) {
            api.error({
                message: 'Evidence Deletion Failed',
                description: 'Please select evidence to delete',
                duration: 4,
            });
            return;
        }

        deleteEvidenceLocal(selectedEvidence);

        api.success({
            message: 'Evidence Deletion Success',
            description: 'Evidence deleted successfully',
            duration: 4,
        });

        handleClear(true);
    };

    // Handle file upload
    const handleFileUpload = (file: File) => {
        setUploadedFile(file);
        setFileName(file.name);
        return false; // Prevent automatic upload
    };

    // Handle preview
    const handlePreview = (record: Evidence) => {
        setPreviewEvidence(record);
        setShowPreview(true);
    };

    // Filter option for Select components
    const filterOption = (input: string, option?: { label: string; value: string }) =>
        (option?.label ?? '').toLowerCase().includes(input.toLowerCase());

    // Convert data for Select components
    const frameworkOptions = frameworks.map(framework => ({
        label: framework.name,
        value: framework.id
    }));

    const controlOptions = controls.map(control => ({
        label: control.code ? `${control.code} - ${control.name}` : control.name,
        value: control.id
    }));

    // Get status color
    const getStatusColor = (status: EvidenceStatus): string => {
        switch (status) {
            case 'Valid': return 'green';
            case 'Expiring': return 'orange';
            case 'Expired': return 'red';
            case 'Pending Review': return 'blue';
            default: return 'default';
        }
    };

    // Get type color
    const getTypeColor = (type: EvidenceType): string => {
        switch (type) {
            case 'Screenshot': return 'cyan';
            case 'Report': return 'blue';
            case 'Log': return 'purple';
            case 'Export': return 'green';
            case 'AI Generated': return 'magenta';
            case 'Document': return 'orange';
            default: return 'default';
        }
    };

    // Table columns
    const columns: TableColumnsType<Evidence> = [
        {
            title: 'Evidence Name',
            dataIndex: 'name',
            key: 'name',
            width: 200,
            sorter: (a, b) => a.name.localeCompare(b.name),
        },
        {
            title: 'Type',
            dataIndex: 'evidence_type',
            key: 'evidence_type',
            width: 120,
            filters: evidenceTypeOptions.map(opt => ({ text: opt.label, value: opt.value })),
            onFilter: (value, record) => record.evidence_type === value,
            render: (type: EvidenceType) => <Tag color={getTypeColor(type)}>{type}</Tag>,
        },
        {
            title: 'Related Control(s)',
            dataIndex: 'control_names',
            key: 'control_names',
            width: 200,
            render: (names: string[]) => {
                if (!names || names.length === 0) return '-';
                const displayNames = names.slice(0, 2);
                const remaining = names.length - 2;
                return (
                    <span>
                        {displayNames.join(', ')}
                        {remaining > 0 && <span style={{ color: '#8c8c8c' }}> +{remaining} more</span>}
                    </span>
                );
            },
        },
        {
            title: 'Framework(s)',
            dataIndex: 'framework_names',
            key: 'framework_names',
            width: 150,
            filters: frameworks.map(f => ({ text: f.name, value: f.name })),
            onFilter: (value, record) => record.framework_names?.includes(value as string) || false,
            render: (names: string[]) => names?.length > 0 ? names.join(', ') : '-',
        },
        {
            title: 'Owner',
            dataIndex: 'owner',
            key: 'owner',
            width: 120,
            render: (owner: string) => owner || '-',
        },
        {
            title: 'Collected Date',
            dataIndex: 'collected_date',
            key: 'collected_date',
            width: 120,
            sorter: (a, b) => new Date(a.collected_date).getTime() - new Date(b.collected_date).getTime(),
            render: (date: string) => date ? new Date(date).toLocaleDateString() : '-',
        },
        {
            title: 'Valid Until',
            dataIndex: 'valid_until',
            key: 'valid_until',
            width: 120,
            render: (date: string | null) => date ? new Date(date).toLocaleDateString() : 'No Expiry',
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: 120,
            filters: evidenceStatusOptions.map(opt => ({ text: opt.label, value: opt.value })),
            onFilter: (value, record) => record.status === value,
            render: (status: EvidenceStatus) => <Tag color={getStatusColor(status)}>{status}</Tag>,
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 80,
            render: (_, record) => (
                <button
                    className="secondary-button"
                    onClick={(e) => {
                        e.stopPropagation();
                        handlePreview(record);
                    }}
                    style={{ padding: '4px 8px', fontSize: '12px' }}
                >
                    <EyeOutlined /> View
                </button>
            ),
        },
    ];

    // Search filtered evidence
    const searchFilteredEvidence = evidence.filter(item =>
        item.name?.toLowerCase().includes(evidenceSearchText.toLowerCase()) ||
        item.description?.toLowerCase().includes(evidenceSearchText.toLowerCase()) ||
        item.evidence_type?.toLowerCase().includes(evidenceSearchText.toLowerCase()) ||
        item.owner?.toLowerCase().includes(evidenceSearchText.toLowerCase()) ||
        item.status?.toLowerCase().includes(evidenceSearchText.toLowerCase())
    );

    // Evidence Card component
    const EvidenceCard = ({ item }: { item: Evidence }) => {
        const handleCardClick = () => {
            setSelectedEvidence(item.id);
            setEvidenceName(item.name);
            setEvidenceDescription(item.description || '');
            setEvidenceType(item.evidence_type);
            setSelectedFrameworks(item.framework_ids || []);
            setSelectedControls(item.control_ids || []);
            setOwner(item.owner || '');
            setCollectedDate(item.collected_date);
            setValidUntil(item.valid_until);
            setStatus(item.status);
            setCollectionMethod(item.collection_method);
            setAuditNotes(item.audit_notes || '');
            setFileName(item.file_name || '');
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
                    <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 500, flex: 1, marginRight: '8px' }}>
                        {item.name}
                    </h4>
                    <Tag color={getStatusColor(item.status)}>{item.status}</Tag>
                </div>

                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '8px' }}>
                    <Tag color={getTypeColor(item.evidence_type)}>{item.evidence_type}</Tag>
                    {item.collection_method && <Tag>{item.collection_method}</Tag>}
                </div>

                {item.framework_names && item.framework_names.length > 0 && (
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '8px' }}>
                        {item.framework_names.slice(0, 2).map((fw: string, idx: number) => (
                            <Tag key={idx} color="blue">{fw}</Tag>
                        ))}
                        {item.framework_names.length > 2 && (
                            <Tag color="default">+{item.framework_names.length - 2} more</Tag>
                        )}
                    </div>
                )}

                <div style={{ display: 'flex', gap: '12px', color: '#8c8c8c', fontSize: '12px', marginBottom: '8px' }}>
                    {item.owner && <span>Owner: {item.owner}</span>}
                    {item.collected_date && <span>Collected: {new Date(item.collected_date).toLocaleDateString()}</span>}
                </div>

                {item.description && (
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
                        {item.description}
                    </p>
                )}

                {item.file_name && (
                    <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px', color: '#1890ff', fontSize: '12px' }}>
                        <LinkOutlined />
                        <span>{item.file_name}</span>
                    </div>
                )}
            </Card>
        );
    };

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
                            <FileSearchOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Evidence"
                                infoContent={EvidenceInfo}
                                className="page-title"
                            />
                        </div>
                        <div className="page-header-right">
                            {!showForm && (
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <button
                                        className="add-button"
                                        onClick={() => {
                                            handleClear(false);
                                            setShowForm(true);
                                        }}
                                        style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                    >
                                        <PlusOutlined /> Add Evidence
                                    </button>
                                    <button
                                        className="secondary-button"
                                        onClick={() => {
                                            handleClear(false);
                                            setShowForm(true);
                                        }}
                                        style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                    >
                                        <UploadOutlined /> Upload Evidence
                                    </button>
                                    <button
                                        className="secondary-button"
                                        disabled
                                        style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: 0.5 }}
                                        title="Coming soon"
                                    >
                                        <RobotOutlined /> Generate via AI
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Description */}
                    <div style={{ marginBottom: '24px', color: '#6b7280' }}>
                        <p style={{ margin: 0 }}>
                            Documents, reports, and artifacts demonstrating control implementation and effectiveness.
                        </p>
                    </div>

                    {/* Evidence Table Section */}
                    <div className="page-section">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <Input
                                    placeholder="Search evidence..."
                                    prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                    value={evidenceSearchText}
                                    onChange={(e) => setEvidenceSearchText(e.target.value)}
                                    style={{ width: '250px' }}
                                />
                                <div style={{ display: 'flex', border: '1px solid #d9d9d9', borderRadius: '6px', overflow: 'hidden' }}>
                                    <button
                                        onClick={() => setEvidenceViewMode('grid')}
                                        style={{
                                            border: 'none',
                                            padding: '6px 12px',
                                            cursor: 'pointer',
                                            backgroundColor: evidenceViewMode === 'grid' ? '#1890ff' : 'white',
                                            color: evidenceViewMode === 'grid' ? 'white' : '#595959',
                                        }}
                                    >
                                        <AppstoreOutlined />
                                    </button>
                                    <button
                                        onClick={() => setEvidenceViewMode('list')}
                                        style={{
                                            border: 'none',
                                            borderLeft: '1px solid #d9d9d9',
                                            padding: '6px 12px',
                                            cursor: 'pointer',
                                            backgroundColor: evidenceViewMode === 'list' ? '#1890ff' : 'white',
                                            color: evidenceViewMode === 'list' ? 'white' : '#595959',
                                        }}
                                    >
                                        <UnorderedListOutlined />
                                    </button>
                                </div>
                            </div>
                        </div>

                        {searchFilteredEvidence.length === 0 ? (
                            <Empty description="No evidence found" />
                        ) : evidenceViewMode === 'grid' ? (
                            <Row gutter={[16, 16]}>
                                {searchFilteredEvidence.map(item => (
                                    <Col key={item.id} xs={24} sm={12} md={8} lg={6}>
                                        <EvidenceCard item={item} />
                                    </Col>
                                ))}
                            </Row>
                        ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <Table
                                columns={columns}
                                dataSource={searchFilteredEvidence}
                                showSorterTooltip={{ target: 'sorter-icon' }}
                                onRow={(record) => {
                                    return {
                                        onClick: () => {
                                            setSelectedEvidence(record.id);
                                            setEvidenceName(record.name);
                                            setEvidenceDescription(record.description || '');
                                            setEvidenceType(record.evidence_type);
                                            setSelectedFrameworks(record.framework_ids || []);
                                            setSelectedControls(record.control_ids || []);
                                            setOwner(record.owner || '');
                                            setCollectedDate(record.collected_date);
                                            setValidUntil(record.valid_until);
                                            setStatus(record.status);
                                            setCollectionMethod(record.collection_method);
                                            setAuditNotes(record.audit_notes || '');
                                            setFileName(record.file_name || '');
                                            setShowForm(true);
                                        },
                                        style: {
                                            cursor: 'pointer',
                                            backgroundColor: selectedEvidence === record.id ? '#e6f7ff' : undefined
                                        }
                                    };
                                }}
                                rowKey="id"
                                pagination={{
                                    showSizeChanger: true,
                                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} evidence items`,
                                }}
                            />
                        </div>
                        )}
                    </div>

                    {/* Evidence Form Modal */}
                    <Modal
                        title={
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {selectedEvidence ? (
                                    <EditOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                                ) : (
                                    <PlusOutlined style={{ fontSize: '20px', color: '#52c41a' }} />
                                )}
                                <span>{selectedEvidence ? 'Edit Evidence' : 'Add New Evidence'}</span>
                                {selectedEvidence && <Tag color="blue">Editing</Tag>}
                            </div>
                        }
                        open={showForm}
                        onCancel={() => handleClear(true)}
                        width={1000}
                        footer={
                            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                {selectedEvidence && (
                                    <button
                                        className="delete-button"
                                        onClick={handleDelete}
                                        disabled={loading}
                                        style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f', color: 'white' }}
                                    >
                                        Delete Evidence
                                    </button>
                                )}
                                {selectedEvidence && (
                                    <button
                                        className="secondary-button"
                                        onClick={() => handleClear(false)}
                                        disabled={loading}
                                    >
                                        Create New Instead
                                    </button>
                                )}
                                <button
                                    className="secondary-button"
                                    onClick={() => handleClear(true)}
                                    disabled={loading}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="add-button"
                                    onClick={handleSave}
                                    disabled={loading}
                                    style={{
                                        backgroundColor: selectedEvidence ? '#1890ff' : '#52c41a',
                                        borderColor: selectedEvidence ? '#1890ff' : '#52c41a',
                                    }}
                                >
                                    {loading ? 'Saving...' : selectedEvidence ? 'Update Evidence' : 'Save Evidence'}
                                </button>
                            </div>
                        }
                    >
                        <p style={{ color: '#8c8c8c', fontSize: '14px', marginBottom: '24px' }}>
                            {selectedEvidence
                                ? 'Update the evidence details below and click "Update Evidence" to save changes.'
                                : 'Fill out the form below to add new evidence.'}
                        </p>

                        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
                            {/* Left Column - Basic Info */}
                            <div style={{ flex: '1 1 500px', minWidth: '0' }}>
                                <div className="form-row">
                                    <div className="form-group" style={{ width: '100%' }}>
                                        <label className="form-label required">Evidence Name</label>
                                        <input
                                            type="text"
                                            className="form-input"
                                            placeholder="Enter evidence name"
                                            value={evidenceName}
                                            onChange={(e) => setEvidenceName(e.target.value)}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label required">Evidence Type</label>
                                        <Select
                                            showSearch
                                            placeholder="Select evidence type"
                                            onChange={(value) => setEvidenceType(value)}
                                            options={evidenceTypeOptions}
                                            filterOption={filterOption}
                                            value={evidenceType}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Collection Method</label>
                                        <Select
                                            placeholder="Select collection method"
                                            onChange={(value) => setCollectionMethod(value)}
                                            options={collectionMethodOptions}
                                            value={collectionMethod}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group" style={{ width: '100%' }}>
                                        <label className="form-label">Description</label>
                                        <textarea
                                            className="large-textarea"
                                            placeholder="Describe what this evidence proves"
                                            value={evidenceDescription}
                                            onChange={(e) => setEvidenceDescription(e.target.value)}
                                            style={{ minHeight: '80px' }}
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Related Control(s)</label>
                                        <Select
                                            mode="multiple"
                                            showSearch
                                            placeholder="Select controls this evidence supports"
                                            onChange={(values) => setSelectedControls(values)}
                                            options={controlOptions}
                                            filterOption={filterOption}
                                            value={selectedControls}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Framework(s)</label>
                                        <Select
                                            mode="multiple"
                                            showSearch
                                            placeholder="Select frameworks"
                                            onChange={(values) => setSelectedFrameworks(values)}
                                            options={frameworkOptions}
                                            filterOption={filterOption}
                                            value={selectedFrameworks}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group" style={{ width: '100%' }}>
                                        <label className="form-label">Upload Evidence File</label>
                                        <Upload
                                            beforeUpload={handleFileUpload}
                                            maxCount={1}
                                            showUploadList={false}
                                        >
                                            <button className="secondary-button" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <UploadOutlined /> Upload File
                                            </button>
                                        </Upload>
                                        {(uploadedFile || fileName) && (
                                            <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <Tag color="blue">{uploadedFile?.name || fileName}</Tag>
                                                <CloseOutlined
                                                    style={{ cursor: 'pointer', color: '#ff4d4f' }}
                                                    onClick={() => {
                                                        setUploadedFile(null);
                                                        setFileName('');
                                                    }}
                                                />
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Right Column - Metadata & Validity */}
                            <div style={{ flex: '0 0 320px', minWidth: '0' }}>
                                <div style={{ border: '1px solid #e8e8e8', borderRadius: '8px', padding: '20px', backgroundColor: '#fafafa', marginBottom: '16px' }}>
                                    <h4 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#262626' }}>
                                        Validity & Status
                                    </h4>

                                    <div className="form-group" style={{ marginBottom: '16px' }}>
                                        <label className="form-label">Owner</label>
                                        <input
                                            type="text"
                                            className="form-input"
                                            placeholder="Evidence owner"
                                            value={owner}
                                            onChange={(e) => setOwner(e.target.value)}
                                            style={{ width: '100%' }}
                                        />
                                    </div>

                                    <div className="form-group" style={{ marginBottom: '16px' }}>
                                        <label className="form-label">Collected Date</label>
                                        <DatePicker
                                            value={collectedDate ? dayjs(collectedDate) : null}
                                            onChange={(date) => setCollectedDate(date ? date.format('YYYY-MM-DD') : '')}
                                            style={{ width: '100%' }}
                                        />
                                    </div>

                                    <div className="form-group" style={{ marginBottom: '16px' }}>
                                        <label className="form-label">Valid Until (Expiry)</label>
                                        <DatePicker
                                            value={validUntil ? dayjs(validUntil) : null}
                                            onChange={(date) => setValidUntil(date ? date.format('YYYY-MM-DD') : null)}
                                            style={{ width: '100%' }}
                                            placeholder="No expiry date"
                                        />
                                        <p style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '4px' }}>
                                            Leave empty if evidence doesn't expire
                                        </p>
                                    </div>

                                    <div className="form-group">
                                        <label className="form-label">Status</label>
                                        <Select
                                            placeholder="Select status"
                                            onChange={(value) => setStatus(value)}
                                            options={evidenceStatusOptions}
                                            value={status}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                </div>

                                <div style={{ border: '1px solid #e8e8e8', borderRadius: '8px', padding: '20px', backgroundColor: '#fafafa' }}>
                                    <h4 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#262626' }}>
                                        Audit Notes
                                    </h4>
                                    <div className="form-group">
                                        <textarea
                                            className="large-textarea"
                                            placeholder="Optional notes for auditors"
                                            value={auditNotes}
                                            onChange={(e) => setAuditNotes(e.target.value)}
                                            style={{ minHeight: '80px' }}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Modal>

                    {/* Evidence Preview Modal */}
                    <Modal
                        title={
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <EyeOutlined style={{ fontSize: '20px', color: '#0f386a' }} />
                                <span>Evidence Details</span>
                            </div>
                        }
                        open={showPreview}
                        onCancel={() => {
                            setShowPreview(false);
                            setPreviewEvidence(null);
                        }}
                        width={800}
                        footer={
                            <button
                                className="secondary-button"
                                onClick={() => {
                                    setShowPreview(false);
                                    setPreviewEvidence(null);
                                }}
                            >
                                Close
                            </button>
                        }
                    >
                        {previewEvidence && (
                            <div>
                                <div style={{ marginBottom: '24px' }}>
                                    <h3 style={{ margin: '0 0 8px 0' }}>{previewEvidence.name}</h3>
                                    <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                                        <Tag color={getTypeColor(previewEvidence.evidence_type)}>{previewEvidence.evidence_type}</Tag>
                                        <Tag color={getStatusColor(previewEvidence.status)}>{previewEvidence.status}</Tag>
                                        <Tag>{previewEvidence.collection_method}</Tag>
                                    </div>
                                </div>

                                {previewEvidence.description && (
                                    <div style={{ marginBottom: '24px' }}>
                                        <h4 style={{ margin: '0 0 8px 0', color: '#262626' }}>Description</h4>
                                        <p style={{ margin: 0, color: '#595959' }}>{previewEvidence.description}</p>
                                    </div>
                                )}

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
                                    <div>
                                        <h4 style={{ margin: '0 0 8px 0', color: '#262626' }}>Related Controls</h4>
                                        <p style={{ margin: 0, color: '#595959' }}>
                                            {previewEvidence.control_names?.length > 0 ? previewEvidence.control_names.join(', ') : 'None'}
                                        </p>
                                    </div>
                                    <div>
                                        <h4 style={{ margin: '0 0 8px 0', color: '#262626' }}>Frameworks</h4>
                                        <p style={{ margin: 0, color: '#595959' }}>
                                            {previewEvidence.framework_names?.length > 0 ? previewEvidence.framework_names.join(', ') : 'None'}
                                        </p>
                                    </div>
                                    <div>
                                        <h4 style={{ margin: '0 0 8px 0', color: '#262626' }}>Owner</h4>
                                        <p style={{ margin: 0, color: '#595959' }}>{previewEvidence.owner || 'Not specified'}</p>
                                    </div>
                                    <div>
                                        <h4 style={{ margin: '0 0 8px 0', color: '#262626' }}>Collected Date</h4>
                                        <p style={{ margin: 0, color: '#595959' }}>
                                            {new Date(previewEvidence.collected_date).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <div>
                                        <h4 style={{ margin: '0 0 8px 0', color: '#262626' }}>Valid Until</h4>
                                        <p style={{ margin: 0, color: '#595959' }}>
                                            {previewEvidence.valid_until ? new Date(previewEvidence.valid_until).toLocaleDateString() : 'No expiry'}
                                        </p>
                                    </div>
                                    <div>
                                        <h4 style={{ margin: '0 0 8px 0', color: '#262626' }}>File</h4>
                                        <p style={{ margin: 0, color: '#595959' }}>{previewEvidence.file_name || 'No file attached'}</p>
                                    </div>
                                </div>

                                {previewEvidence.audit_notes && (
                                    <div style={{ backgroundColor: '#f5f5f5', padding: '16px', borderRadius: '8px' }}>
                                        <h4 style={{ margin: '0 0 8px 0', color: '#262626' }}>Audit Notes</h4>
                                        <p style={{ margin: 0, color: '#595959' }}>{previewEvidence.audit_notes}</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </Modal>
                </div>
            </div>
        </div>
    );
};

export default EvidencePage;
