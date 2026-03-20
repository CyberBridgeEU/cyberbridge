import { Select, Table, notification, Modal, Tag, Upload, DatePicker, Card, Row, Col, Input, Empty } from "antd";
import type { TableColumnsType } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { DeploymentUnitOutlined, PlusOutlined, CloseOutlined, EditOutlined, UploadOutlined, LinkOutlined, AppstoreOutlined, UnorderedListOutlined, SearchOutlined } from '@ant-design/icons';
import useArchitectureStore, { ArchitectureDiagram, DiagramType } from "../store/useArchitectureStore.ts";
import usePolicyStore from "../store/usePolicyStore.ts";
import useRiskStore from "../store/useRiskStore.ts";
import useUserStore from "../store/useUserStore.ts";
import { useEffect, useState } from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import { ArchitectureInfo } from "../constants/infoContent.tsx";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const ArchitecturePage = () => {
    // Menu highlighting
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // View mode state
    const [diagramViewMode, setDiagramViewMode] = useState<'grid' | 'list'>('list');
    const [diagramSearchText, setDiagramSearchText] = useState('');

    // Store access
    const {
        diagrams,
        fetchDiagrams,
        addDiagramLocal,
        updateDiagramLocal,
        deleteDiagramLocal,
        loading,
    } = useArchitectureStore();

    const { frameworks, fetchFrameworks } = usePolicyStore();
    const { risks, fetchRisks } = useRiskStore();
    const { current_user } = useUserStore();

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    // Selected diagram state
    const [selectedDiagram, setSelectedDiagram] = useState<string | null>(null);

    // Form visibility state
    const [showForm, setShowForm] = useState<boolean>(false);

    // Form state
    const [diagramName, setDiagramName] = useState('');
    const [diagramDescription, setDiagramDescription] = useState('');
    const [diagramType, setDiagramType] = useState<DiagramType | undefined>(undefined);
    const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([]);
    const [selectedRisks, setSelectedRisks] = useState<string[]>([]);
    const [owner, setOwner] = useState('');
    const [version, setVersion] = useState('');
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [fileName, setFileName] = useState<string>('');

    // Diagram type options
    const diagramTypeOptions: { label: string; value: DiagramType }[] = [
        { label: 'System Architecture', value: 'System' },
        { label: 'Network Diagram', value: 'Network' },
        { label: 'Data Flow Diagram', value: 'Data Flow' },
        { label: 'Infrastructure', value: 'Infrastructure' },
        { label: 'Application Architecture', value: 'Application' },
        { label: 'Security Architecture', value: 'Security' },
        { label: 'Other', value: 'Other' },
    ];

    // Fetch data on component mount
    useEffect(() => {
        const fetchData = async () => {
            await fetchDiagrams();
            await fetchFrameworks();
            await fetchRisks();
        };
        fetchData();
    }, [fetchDiagrams, fetchFrameworks, fetchRisks]);

    // Handle form submission
    const handleSave = async () => {
        if (!diagramName || !diagramType) {
            api.error({
                message: 'Diagram Operation Failed',
                description: 'Please fill in all required fields (Name and Type)',
                duration: 4,
            });
            return;
        }

        const isUpdate = selectedDiagram !== null;
        const now = new Date().toISOString();

        // Get framework names for display
        const frameworkNames = selectedFrameworks.map(id => {
            const framework = frameworks.find(f => f.id === id);
            return framework?.name || '';
        }).filter(Boolean);

        if (isUpdate && selectedDiagram) {
            // Update existing diagram
            updateDiagramLocal(selectedDiagram, {
                name: diagramName,
                description: diagramDescription || null,
                diagram_type: diagramType,
                framework_ids: selectedFrameworks,
                framework_names: frameworkNames,
                risk_ids: selectedRisks,
                owner: owner || null,
                version: version || null,
                file_name: uploadedFile?.name || fileName || null,
                updated_at: now,
            });

            api.success({
                message: 'Diagram Update Success',
                description: 'Architecture diagram updated successfully',
                duration: 4,
            });
        } else {
            // Create new diagram
            const newDiagram: ArchitectureDiagram = {
                id: crypto.randomUUID(),
                name: diagramName,
                description: diagramDescription || null,
                diagram_type: diagramType,
                file_name: uploadedFile?.name || null,
                file_url: null,
                file_size: uploadedFile?.size || null,
                framework_ids: selectedFrameworks,
                framework_names: frameworkNames,
                risk_ids: selectedRisks,
                owner: owner || current_user?.name || null,
                version: version || '1.0',
                created_at: now,
                updated_at: now,
            };

            addDiagramLocal(newDiagram);

            api.success({
                message: 'Diagram Creation Success',
                description: 'Architecture diagram created successfully',
                duration: 4,
            });
        }

        handleClear(true);
    };

    // Clear form
    const handleClear = (hideForm: boolean = false) => {
        setDiagramName('');
        setDiagramDescription('');
        setDiagramType(undefined);
        setSelectedFrameworks([]);
        setSelectedRisks([]);
        setOwner('');
        setVersion('');
        setUploadedFile(null);
        setFileName('');
        setSelectedDiagram(null);
        if (hideForm) {
            setShowForm(false);
        }
    };

    // Handle diagram deletion
    const handleDelete = async () => {
        if (!selectedDiagram) {
            api.error({
                message: 'Diagram Deletion Failed',
                description: 'Please select a diagram to delete',
                duration: 4,
            });
            return;
        }

        deleteDiagramLocal(selectedDiagram);

        api.success({
            message: 'Diagram Deletion Success',
            description: 'Architecture diagram deleted successfully',
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

    // Filter option for Select components
    const filterOption = (input: string, option?: { label: string; value: string }) =>
        (option?.label ?? '').toLowerCase().includes(input.toLowerCase());

    // Convert data for Select components
    const frameworkOptions = frameworks.map(framework => ({
        label: framework.name,
        value: framework.id
    }));

    const riskOptions = risks.map(risk => ({
        label: risk.name,
        value: risk.id
    }));

    // Table columns
    const columns: TableColumnsType<ArchitectureDiagram> = [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            width: 200,
            sorter: (a, b) => a.name.localeCompare(b.name),
        },
        {
            title: 'Type',
            dataIndex: 'diagram_type',
            key: 'diagram_type',
            width: 150,
            filters: diagramTypeOptions.map(opt => ({ text: opt.label, value: opt.value })),
            onFilter: (value, record) => record.diagram_type === value,
            render: (type: DiagramType) => {
                const colorMap: Record<DiagramType, string> = {
                    'System': 'blue',
                    'Network': 'cyan',
                    'Data Flow': 'green',
                    'Infrastructure': 'orange',
                    'Application': 'purple',
                    'Security': 'red',
                    'Other': 'default'
                };
                return <Tag color={colorMap[type]}>{type}</Tag>;
            }
        },
        {
            title: 'Framework(s)',
            dataIndex: 'framework_names',
            key: 'framework_names',
            width: 200,
            render: (names: string[]) => names?.length > 0 ? names.join(', ') : '-',
        },
        {
            title: 'Version',
            dataIndex: 'version',
            key: 'version',
            width: 100,
            render: (version: string) => version || '-',
        },
        {
            title: 'Owner',
            dataIndex: 'owner',
            key: 'owner',
            width: 150,
            render: (owner: string) => owner || '-',
        },
        {
            title: 'File',
            dataIndex: 'file_name',
            key: 'file_name',
            width: 150,
            render: (fileName: string) => fileName || '-',
        },
        {
            title: 'Updated',
            dataIndex: 'updated_at',
            key: 'updated_at',
            width: 120,
            sorter: (a, b) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime(),
            render: (date: string) => new Date(date).toLocaleDateString(),
        },
    ];

    // Search filtered diagrams
    const searchFilteredDiagrams = diagrams.filter(diagram =>
        diagram.name?.toLowerCase().includes(diagramSearchText.toLowerCase()) ||
        diagram.description?.toLowerCase().includes(diagramSearchText.toLowerCase()) ||
        diagram.diagram_type?.toLowerCase().includes(diagramSearchText.toLowerCase()) ||
        diagram.owner?.toLowerCase().includes(diagramSearchText.toLowerCase())
    );

    // Diagram type color mapping
    const getDiagramTypeColor = (type: string): string => {
        const colorMap: Record<string, string> = {
            'System': 'blue',
            'Network': 'cyan',
            'Data Flow': 'green',
            'Infrastructure': 'orange',
            'Application': 'purple',
            'Security': 'red',
            'Other': 'default'
        };
        return colorMap[type] || 'default';
    };

    // Diagram Card component
    const DiagramCard = ({ diagram }: { diagram: ArchitectureDiagram }) => {
        const handleCardClick = () => {
            setSelectedDiagram(diagram.id);
            setDiagramName(diagram.name);
            setDiagramDescription(diagram.description || '');
            setDiagramType(diagram.diagram_type);
            setSelectedFrameworks(diagram.framework_ids || []);
            setSelectedRisks(diagram.risk_ids || []);
            setOwner(diagram.owner || '');
            setVersion(diagram.version || '');
            setFileName(diagram.file_name || '');
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
                        {diagram.name}
                    </h4>
                    <Tag color={getDiagramTypeColor(diagram.diagram_type)}>{diagram.diagram_type}</Tag>
                </div>

                {diagram.framework_names && diagram.framework_names.length > 0 && (
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '8px' }}>
                        {diagram.framework_names.map((fw: string, idx: number) => (
                            <Tag key={idx} color="blue">{fw}</Tag>
                        ))}
                    </div>
                )}

                <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', color: '#8c8c8c', fontSize: '13px' }}>
                    {diagram.version && <span>v{diagram.version}</span>}
                    {diagram.owner && <span>• {diagram.owner}</span>}
                </div>

                {diagram.description && (
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
                        {diagram.description}
                    </p>
                )}

                {diagram.file_name && (
                    <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '4px', color: '#1890ff', fontSize: '12px' }}>
                        <LinkOutlined />
                        <span>{diagram.file_name}</span>
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
                            <DeploymentUnitOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Architecture"
                                infoContent={ArchitectureInfo}
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
                                        <PlusOutlined /> Add Diagram
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Description */}
                    <div style={{ marginBottom: '24px', color: '#6b7280' }}>
                        <p style={{ margin: 0 }}>
                            System, network, and data flow diagrams describing the organization's technical architecture.
                        </p>
                    </div>

                    {/* Architecture Diagrams Table Section */}
                    <div className="page-section">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <Input
                                    placeholder="Search diagrams..."
                                    prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                    value={diagramSearchText}
                                    onChange={(e) => setDiagramSearchText(e.target.value)}
                                    style={{ width: '250px' }}
                                />
                                <div style={{ display: 'flex', border: '1px solid #d9d9d9', borderRadius: '6px', overflow: 'hidden' }}>
                                    <button
                                        onClick={() => setDiagramViewMode('grid')}
                                        style={{
                                            border: 'none',
                                            padding: '6px 12px',
                                            cursor: 'pointer',
                                            backgroundColor: diagramViewMode === 'grid' ? '#1890ff' : 'white',
                                            color: diagramViewMode === 'grid' ? 'white' : '#595959',
                                        }}
                                    >
                                        <AppstoreOutlined />
                                    </button>
                                    <button
                                        onClick={() => setDiagramViewMode('list')}
                                        style={{
                                            border: 'none',
                                            borderLeft: '1px solid #d9d9d9',
                                            padding: '6px 12px',
                                            cursor: 'pointer',
                                            backgroundColor: diagramViewMode === 'list' ? '#1890ff' : 'white',
                                            color: diagramViewMode === 'list' ? 'white' : '#595959',
                                        }}
                                    >
                                        <UnorderedListOutlined />
                                    </button>
                                </div>
                            </div>
                        </div>

                        {searchFilteredDiagrams.length === 0 ? (
                            <Empty description="No diagrams found" />
                        ) : diagramViewMode === 'grid' ? (
                            <Row gutter={[16, 16]}>
                                {searchFilteredDiagrams.map(diagram => (
                                    <Col key={diagram.id} xs={24} sm={12} md={8} lg={6}>
                                        <DiagramCard diagram={diagram} />
                                    </Col>
                                ))}
                            </Row>
                        ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <Table
                                columns={columns}
                                dataSource={searchFilteredDiagrams}
                                showSorterTooltip={{ target: 'sorter-icon' }}
                                onRow={(record) => {
                                    return {
                                        onClick: () => {
                                            setSelectedDiagram(record.id);
                                            setDiagramName(record.name);
                                            setDiagramDescription(record.description || '');
                                            setDiagramType(record.diagram_type);
                                            setSelectedFrameworks(record.framework_ids || []);
                                            setSelectedRisks(record.risk_ids || []);
                                            setOwner(record.owner || '');
                                            setVersion(record.version || '');
                                            setFileName(record.file_name || '');
                                            setShowForm(true);
                                        },
                                        style: {
                                            cursor: 'pointer',
                                            backgroundColor: selectedDiagram === record.id ? '#e6f7ff' : undefined
                                        }
                                    };
                                }}
                                rowKey="id"
                                pagination={{
                                    showSizeChanger: true,
                                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} diagrams`,
                                }}
                            />
                        </div>
                        )}
                    </div>

                    {/* Architecture Diagram Modal */}
                    <Modal
                        title={
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {selectedDiagram ? (
                                    <EditOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                                ) : (
                                    <PlusOutlined style={{ fontSize: '20px', color: '#52c41a' }} />
                                )}
                                <span>{selectedDiagram ? 'Edit Diagram' : 'Add New Diagram'}</span>
                                {selectedDiagram && <Tag color="blue">Editing</Tag>}
                            </div>
                        }
                        open={showForm}
                        onCancel={() => handleClear(true)}
                        width={900}
                        footer={
                            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                {selectedDiagram && (
                                    <button
                                        className="delete-button"
                                        onClick={handleDelete}
                                        disabled={loading}
                                        style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f', color: 'white' }}
                                    >
                                        Delete Diagram
                                    </button>
                                )}
                                {selectedDiagram && (
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
                                        backgroundColor: selectedDiagram ? '#1890ff' : '#52c41a',
                                        borderColor: selectedDiagram ? '#1890ff' : '#52c41a',
                                    }}
                                >
                                    {loading ? 'Saving...' : selectedDiagram ? 'Update Diagram' : 'Save Diagram'}
                                </button>
                            </div>
                        }
                    >
                        <p style={{ color: '#8c8c8c', fontSize: '14px', marginBottom: '24px' }}>
                            {selectedDiagram
                                ? 'Update the diagram details below and click "Update Diagram" to save changes.'
                                : 'Fill out the form below to add a new architecture diagram.'}
                        </p>

                        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
                            {/* Left Column - Basic Info */}
                            <div style={{ flex: '1 1 400px', minWidth: '0' }}>
                                <div className="form-row">
                                    <div className="form-group" style={{ width: '100%' }}>
                                        <label className="form-label required">Diagram Name</label>
                                        <input
                                            type="text"
                                            className="form-input"
                                            placeholder="Enter diagram name"
                                            value={diagramName}
                                            onChange={(e) => setDiagramName(e.target.value)}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label required">Diagram Type</label>
                                        <Select
                                            showSearch
                                            placeholder="Select diagram type"
                                            onChange={(value) => setDiagramType(value)}
                                            options={diagramTypeOptions}
                                            filterOption={filterOption}
                                            value={diagramType}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Version</label>
                                        <input
                                            type="text"
                                            className="form-input"
                                            placeholder="e.g., 1.0"
                                            value={version}
                                            onChange={(e) => setVersion(e.target.value)}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group" style={{ width: '100%' }}>
                                        <label className="form-label">Description</label>
                                        <textarea
                                            className="large-textarea"
                                            placeholder="Describe what this diagram represents"
                                            value={diagramDescription}
                                            onChange={(e) => setDiagramDescription(e.target.value)}
                                            style={{ minHeight: '100px' }}
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group" style={{ width: '100%' }}>
                                        <label className="form-label">Upload Diagram File</label>
                                        <Upload
                                            beforeUpload={handleFileUpload}
                                            maxCount={1}
                                            accept=".png,.jpg,.jpeg,.gif,.svg,.pdf,.drawio,.vsdx"
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
                                        <p style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '4px' }}>
                                            Supported formats: PNG, JPG, SVG, PDF, Draw.io, Visio
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* Right Column - Associations */}
                            <div style={{ flex: '0 0 320px', minWidth: '0' }}>
                                <div style={{ border: '1px solid #e8e8e8', borderRadius: '8px', padding: '20px', backgroundColor: '#fafafa' }}>
                                    <h4 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: '#262626' }}>
                                        Associations
                                    </h4>

                                    <div className="form-group" style={{ marginBottom: '16px' }}>
                                        <label className="form-label">Owner</label>
                                        <input
                                            type="text"
                                            className="form-input"
                                            placeholder="Diagram owner"
                                            value={owner}
                                            onChange={(e) => setOwner(e.target.value)}
                                            style={{ width: '100%' }}
                                        />
                                    </div>

                                    <div className="form-group" style={{ marginBottom: '16px' }}>
                                        <label className="form-label">Link to Framework(s)</label>
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

                                    <div className="form-group">
                                        <label className="form-label">
                                            <LinkOutlined style={{ marginRight: '4px' }} />
                                            Link to Risk(s)
                                        </label>
                                        <Select
                                            mode="multiple"
                                            showSearch
                                            placeholder="Select related risks"
                                            onChange={(values) => setSelectedRisks(values)}
                                            options={riskOptions}
                                            filterOption={filterOption}
                                            value={selectedRisks}
                                            style={{ width: '100%' }}
                                        />
                                        <p style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '4px' }}>
                                            Link this diagram to risks for context
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Modal>
                </div>
            </div>
        </div>
    );
};

export default ArchitecturePage;
