import { Table, notification, Tag, Modal, Tabs, Card, Progress, Row, Col, Input, Button, Select, Checkbox, Collapse, Space, Form, InputNumber } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { PlusOutlined, EditOutlined, DeleteOutlined, CheckSquareOutlined, FileTextOutlined, SafetyCertificateOutlined, InfoCircleOutlined, SearchOutlined } from '@ant-design/icons';
import useCEMarkingStore from "../store/useCEMarkingStore.ts";
import useAssetStore from "../store/useAssetStore.ts";
import type { CEChecklist, CEChecklistItem, CEDocumentStatus } from "../store/useCEMarkingStore.ts";
import { useEffect, useState, useMemo } from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import { CEMarkingChecklistInfo } from "../constants/infoContent.tsx";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const { TextArea } = Input;

const getStatusColor = (status: string): string => {
    switch (status) {
        case 'not_started': return '#8c8c8c';
        case 'in_progress': return '#1890ff';
        case 'ready': return '#389e0d';
        case 'approved': return '#722ed1';
        default: return '#8c8c8c';
    }
};

const getStatusLabel = (status: string): string => {
    switch (status) {
        case 'not_started': return 'Not Started';
        case 'in_progress': return 'In Progress';
        case 'ready': return 'Ready';
        case 'approved': return 'Approved';
        default: return status;
    }
};

const getDocStatusColor = (status: string): string => {
    switch (status) {
        case 'not_started': return '#8c8c8c';
        case 'in_progress': return '#1890ff';
        case 'review': return '#d48806';
        case 'complete': return '#389e0d';
        default: return '#8c8c8c';
    }
};

const CEMarkingChecklistPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const [api, contextHolder] = notification.useNotification();

    const [activeTab, setActiveTab] = useState<string>('all');
    const [selectedChecklist, setSelectedChecklist] = useState<string | null>(null);
    const [detailTab, setDetailTab] = useState<string>('items');
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [createAssetId, setCreateAssetId] = useState<string | undefined>(undefined);
    const [createProductTypeId, setCreateProductTypeId] = useState<string | undefined>(undefined);
    const [searchText, setSearchText] = useState('');

    // Custom item form
    const [showCustomItemModal, setShowCustomItemModal] = useState(false);
    const [customCategory, setCustomCategory] = useState('');
    const [customTitle, setCustomTitle] = useState('');
    const [customDescription, setCustomDescription] = useState('');

    const {
        checklists, currentChecklist, productTypes, documentTypes, loading, error,
        fetchChecklists, fetchChecklist, fetchProductTypes, fetchDocumentTypes,
        createChecklist, updateChecklist, deleteChecklist,
        toggleChecklistItem, addCustomItem, deleteCustomItem, updateDocumentStatus
    } = useCEMarkingStore();

    const { assets, fetchAssets } = useAssetStore();

    useEffect(() => {
        fetchChecklists();
        fetchProductTypes();
        fetchDocumentTypes();
        fetchAssets();
    }, []);

    useEffect(() => {
        if (selectedChecklist) {
            fetchChecklist(selectedChecklist);
            setActiveTab('detail');
        }
    }, [selectedChecklist]);

    const filteredChecklists = useMemo(() => {
        if (!searchText) return checklists;
        const lower = searchText.toLowerCase();
        return checklists.filter(c =>
            (c.asset_name || '').toLowerCase().includes(lower) ||
            (c.ce_product_type_name || '').toLowerCase().includes(lower) ||
            (c.status || '').toLowerCase().includes(lower)
        );
    }, [checklists, searchText]);

    const handleCreate = async () => {
        if (!createAssetId) {
            api.error({ message: 'Validation Error', description: 'Please select an asset', duration: 4 });
            return;
        }
        try {
            const result = await createChecklist(createAssetId, createProductTypeId);
            if (result) {
                api.success({ message: 'Checklist Created', description: 'CE Marking checklist created successfully', duration: 4 });
                setShowCreateModal(false);
                setCreateAssetId(undefined);
                setCreateProductTypeId(undefined);
                setSelectedChecklist(result.id);
            }
        } catch (e: any) {
            api.error({ message: 'Creation Failed', description: e.message || 'Failed to create checklist', duration: 4 });
        }
    };

    const handleDelete = (id: string) => {
        Modal.confirm({
            title: 'Delete Checklist',
            content: 'Are you sure you want to delete this checklist? All items and document statuses will be removed.',
            okText: 'Delete',
            okType: 'danger',
            onOk: async () => {
                try {
                    await deleteChecklist(id);
                    api.success({ message: 'Deleted', description: 'Checklist deleted successfully', duration: 4 });
                    if (selectedChecklist === id) {
                        setSelectedChecklist(null);
                        setActiveTab('all');
                    }
                } catch {
                    api.error({ message: 'Delete Failed', description: 'Failed to delete checklist', duration: 4 });
                }
            }
        });
    };

    const handleToggleItem = async (item: CEChecklistItem) => {
        try {
            await toggleChecklistItem(item.id, !item.is_completed);
        } catch {
            api.error({ message: 'Error', description: 'Failed to update item', duration: 4 });
        }
    };

    const handleAddCustomItem = async () => {
        if (!currentChecklist || !customTitle.trim() || !customCategory.trim()) return;
        try {
            await addCustomItem(currentChecklist.id, {
                category: customCategory,
                title: customTitle.trim(),
                description: customDescription || undefined,
            });
            api.success({ message: 'Item Added', description: 'Custom item added successfully', duration: 4 });
            setShowCustomItemModal(false);
            setCustomCategory('');
            setCustomTitle('');
            setCustomDescription('');
        } catch {
            api.error({ message: 'Error', description: 'Failed to add custom item', duration: 4 });
        }
    };

    const handleDeleteCustomItem = (itemId: string) => {
        Modal.confirm({
            title: 'Delete Custom Item',
            content: 'Are you sure you want to remove this custom item?',
            okText: 'Delete',
            okType: 'danger',
            onOk: async () => {
                try {
                    await deleteCustomItem(itemId);
                    api.success({ message: 'Deleted', description: 'Custom item deleted', duration: 4 });
                } catch {
                    api.error({ message: 'Error', description: 'Failed to delete item', duration: 4 });
                }
            }
        });
    };

    const handleDocStatusChange = async (statusId: string, newStatus: string) => {
        try {
            await updateDocumentStatus(statusId, { status: newStatus });
        } catch {
            api.error({ message: 'Error', description: 'Failed to update document status', duration: 4 });
        }
    };

    const handleUpdateChecklist = async (data: any) => {
        if (!currentChecklist) return;
        try {
            await updateChecklist(currentChecklist.id, data);
            api.success({ message: 'Updated', description: 'Checklist updated successfully', duration: 4 });
        } catch {
            api.error({ message: 'Error', description: 'Failed to update checklist', duration: 4 });
        }
    };

    // Group items by category
    const groupedItems = useMemo(() => {
        if (!currentChecklist?.items) return {};
        const groups: Record<string, CEChecklistItem[]> = {};
        currentChecklist.items.forEach(item => {
            const cat = item.category || 'Other';
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(item);
        });
        return groups;
    }, [currentChecklist?.items]);

    const checklistColumns = [
        {
            title: 'Asset',
            dataIndex: 'asset_name',
            key: 'asset_name',
            sorter: (a: CEChecklist, b: CEChecklist) => (a.asset_name || '').localeCompare(b.asset_name || ''),
        },
        {
            title: 'Product Type',
            dataIndex: 'ce_product_type_name',
            key: 'ce_product_type_name',
            render: (text: string | null) => text || '-',
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => <Tag color={getStatusColor(status)}>{getStatusLabel(status)}</Tag>,
            filters: [
                { text: 'Not Started', value: 'not_started' },
                { text: 'In Progress', value: 'in_progress' },
                { text: 'Ready', value: 'ready' },
                { text: 'Approved', value: 'approved' },
            ],
            onFilter: (value: any, record: CEChecklist) => record.status === value,
        },
        {
            title: 'Readiness',
            dataIndex: 'readiness_score',
            key: 'readiness_score',
            width: 160,
            render: (score: number) => <Progress percent={Math.round(score)} size="small" strokeColor={score >= 80 ? '#389e0d' : score >= 50 ? '#d48806' : '#cf1322'} />,
            sorter: (a: CEChecklist, b: CEChecklist) => a.readiness_score - b.readiness_score,
        },
        {
            title: 'Items',
            key: 'items',
            width: 80,
            render: (_: any, record: CEChecklist) => `${record.items_completed}/${record.items_total}`,
        },
        {
            title: 'Docs',
            key: 'docs',
            width: 80,
            render: (_: any, record: CEChecklist) => `${record.docs_completed}/${record.docs_total}`,
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 100,
            render: (_: any, record: CEChecklist) => (
                <Space>
                    <Button size="small" icon={<EditOutlined />} onClick={(e) => { e.stopPropagation(); setSelectedChecklist(record.id); }} />
                    <Button size="small" danger icon={<DeleteOutlined />} onClick={(e) => { e.stopPropagation(); handleDelete(record.id); }} />
                </Space>
            ),
        },
    ];

    const docColumns = [
        {
            title: 'Document Type',
            dataIndex: 'document_type_name',
            key: 'document_type_name',
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string, record: CEDocumentStatus) => (
                <Select
                    value={status}
                    onChange={(val) => handleDocStatusChange(record.id, val)}
                    style={{ width: 140 }}
                    size="small"
                    options={[
                        { value: 'not_started', label: 'Not Started' },
                        { value: 'in_progress', label: 'In Progress' },
                        { value: 'review', label: 'Review' },
                        { value: 'complete', label: 'Complete' },
                    ]}
                />
            ),
        },
        {
            title: 'Reference',
            dataIndex: 'document_reference',
            key: 'document_reference',
            render: (text: string | null, record: CEDocumentStatus) => (
                <Input
                    size="small"
                    defaultValue={text || ''}
                    placeholder="Document reference"
                    onBlur={(e) => {
                        if (e.target.value !== (text || '')) {
                            updateDocumentStatus(record.id, { document_reference: e.target.value });
                        }
                    }}
                />
            ),
        },
        {
            title: 'Notes',
            dataIndex: 'notes',
            key: 'notes',
            render: (text: string | null, record: CEDocumentStatus) => (
                <Input
                    size="small"
                    defaultValue={text || ''}
                    placeholder="Notes"
                    onBlur={(e) => {
                        if (e.target.value !== (text || '')) {
                            updateDocumentStatus(record.id, { notes: e.target.value });
                        }
                    }}
                />
            ),
        },
    ];

    // Assets not yet having a checklist
    const availableAssets = useMemo(() => {
        const checklistAssetIds = new Set(checklists.map(c => c.asset_id));
        return assets.filter(a => !checklistAssetIds.has(a.id));
    }, [assets, checklists]);

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--page-background)' }}>
            {contextHolder}
            <Sidebar
                selectedKeys={menuHighlighting.selectedKeys}
                openKeys={menuHighlighting.openKeys}
                onOpenChange={menuHighlighting.onOpenChange}
            />
            <div style={{ flex: 1, padding: '24px', overflow: 'auto' }}>
                <InfoTitle title="CE Marking Checklist" infoContent={CEMarkingChecklistInfo} />

                <Tabs
                    activeKey={activeTab}
                    onChange={(key) => {
                        setActiveTab(key);
                        if (key === 'all') setSelectedChecklist(null);
                    }}
                    items={[
                        {
                            key: 'all',
                            label: <span><SafetyCertificateOutlined /> All Checklists</span>,
                            children: (
                                <div>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                                        <Input
                                            placeholder="Search checklists..."
                                            prefix={<SearchOutlined />}
                                            value={searchText}
                                            onChange={e => setSearchText(e.target.value)}
                                            style={{ width: 280 }}
                                            allowClear
                                        />
                                        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowCreateModal(true)}>
                                            Create Checklist
                                        </Button>
                                    </div>

                                    <Table
                                        dataSource={filteredChecklists}
                                        columns={checklistColumns}
                                        rowKey="id"
                                        size="small"
                                        loading={loading}
                                        pagination={{ pageSize: 15, showSizeChanger: true }}
                                        onRow={(record) => ({
                                            onClick: () => setSelectedChecklist(record.id),
                                            style: { cursor: 'pointer' }
                                        })}
                                    />

                                    <Modal
                                        title="Create CE Marking Checklist"
                                        open={showCreateModal}
                                        onCancel={() => setShowCreateModal(false)}
                                        onOk={handleCreate}
                                        okText="Create"
                                    >
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Asset <span style={{ color: '#cf1322' }}>*</span></label>
                                                <Select
                                                    style={{ width: '100%' }}
                                                    value={createAssetId}
                                                    onChange={setCreateAssetId}
                                                    placeholder="Select an asset"
                                                    showSearch
                                                    optionFilterProp="label"
                                                    options={availableAssets.map(a => ({ value: a.id, label: a.name }))}
                                                />
                                            </div>
                                            <div>
                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Product Type</label>
                                                <Select
                                                    style={{ width: '100%' }}
                                                    value={createProductTypeId}
                                                    onChange={setCreateProductTypeId}
                                                    placeholder="Select product type (optional)"
                                                    allowClear
                                                    options={productTypes.map(pt => ({ value: pt.id, label: pt.name }))}
                                                />
                                            </div>
                                        </div>
                                    </Modal>
                                </div>
                            )
                        },
                        ...(selectedChecklist && currentChecklist ? [{
                            key: 'detail',
                            label: <span><CheckSquareOutlined /> {currentChecklist.asset_name || 'Checklist Detail'}</span>,
                            children: (
                                <div>
                                    {/* Summary bar */}
                                    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                                        <Col xs={24} sm={6}>
                                            <Card size="small">
                                                <div style={{ fontSize: 12, color: '#8c8c8c' }}>Status</div>
                                                <Tag color={getStatusColor(currentChecklist.status)}>{getStatusLabel(currentChecklist.status)}</Tag>
                                            </Card>
                                        </Col>
                                        <Col xs={24} sm={6}>
                                            <Card size="small">
                                                <div style={{ fontSize: 12, color: '#8c8c8c' }}>Readiness</div>
                                                <Progress percent={Math.round(currentChecklist.readiness_score)} size="small" />
                                            </Card>
                                        </Col>
                                        <Col xs={24} sm={6}>
                                            <Card size="small">
                                                <div style={{ fontSize: 12, color: '#8c8c8c' }}>Items</div>
                                                <span style={{ fontSize: 18, fontWeight: 600 }}>{currentChecklist.items_completed}/{currentChecklist.items_total}</span>
                                            </Card>
                                        </Col>
                                        <Col xs={24} sm={6}>
                                            <Card size="small">
                                                <div style={{ fontSize: 12, color: '#8c8c8c' }}>Documents</div>
                                                <span style={{ fontSize: 18, fontWeight: 600 }}>{currentChecklist.docs_completed}/{currentChecklist.docs_total}</span>
                                            </Card>
                                        </Col>
                                    </Row>

                                    <Tabs
                                        activeKey={detailTab}
                                        onChange={setDetailTab}
                                        size="small"
                                        items={[
                                            {
                                                key: 'items',
                                                label: <span><CheckSquareOutlined /> Checklist Items</span>,
                                                children: (
                                                    <div>
                                                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
                                                            <Button icon={<PlusOutlined />} onClick={() => setShowCustomItemModal(true)}>Add Custom Item</Button>
                                                        </div>
                                                        <Collapse
                                                            defaultActiveKey={Object.keys(groupedItems)}
                                                            items={Object.entries(groupedItems).map(([category, items]) => ({
                                                                key: category,
                                                                label: (
                                                                    <span>
                                                                        {category}
                                                                        <Tag style={{ marginLeft: 8 }}>{items.filter(i => i.is_completed).length}/{items.length}</Tag>
                                                                    </span>
                                                                ),
                                                                children: (
                                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                                        {items.sort((a, b) => a.sort_order - b.sort_order).map(item => (
                                                                            <div key={item.id} style={{
                                                                                display: 'flex', alignItems: 'flex-start', gap: 8, padding: '8px 12px',
                                                                                background: item.is_completed ? 'rgba(56, 158, 13, 0.04)' : 'transparent',
                                                                                borderRadius: 6, border: '1px solid #f0f0f0'
                                                                            }}>
                                                                                <Checkbox
                                                                                    checked={item.is_completed}
                                                                                    onChange={() => handleToggleItem(item)}
                                                                                    style={{ marginTop: 2 }}
                                                                                />
                                                                                <div style={{ flex: 1 }}>
                                                                                    <div style={{
                                                                                        fontWeight: 500, fontSize: 13,
                                                                                        textDecoration: item.is_completed ? 'line-through' : 'none',
                                                                                        color: item.is_completed ? '#8c8c8c' : 'inherit'
                                                                                    }}>
                                                                                        {item.title}
                                                                                        {item.is_mandatory && <Tag color="red" style={{ marginLeft: 6, fontSize: 10 }}>Required</Tag>}
                                                                                    </div>
                                                                                    {item.description && (
                                                                                        <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 2 }}>{item.description}</div>
                                                                                    )}
                                                                                </div>
                                                                                {!item.template_item_id && (
                                                                                    <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteCustomItem(item.id)} />
                                                                                )}
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                )
                                                            }))}
                                                        />

                                                        <Modal
                                                            title="Add Custom Item"
                                                            open={showCustomItemModal}
                                                            onCancel={() => setShowCustomItemModal(false)}
                                                            onOk={handleAddCustomItem}
                                                            okText="Add"
                                                        >
                                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                                                <div>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Category <span style={{ color: '#cf1322' }}>*</span></label>
                                                                    <Select
                                                                        style={{ width: '100%' }}
                                                                        value={customCategory || undefined}
                                                                        onChange={setCustomCategory}
                                                                        placeholder="Select or enter category"
                                                                        options={Object.keys(groupedItems).map(c => ({ value: c, label: c }))}
                                                                    />
                                                                </div>
                                                                <div>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Title <span style={{ color: '#cf1322' }}>*</span></label>
                                                                    <Input value={customTitle} onChange={e => setCustomTitle(e.target.value)} placeholder="Item title" />
                                                                </div>
                                                                <div>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Description</label>
                                                                    <TextArea rows={2} value={customDescription} onChange={e => setCustomDescription(e.target.value)} placeholder="Optional description" />
                                                                </div>
                                                            </div>
                                                        </Modal>
                                                    </div>
                                                )
                                            },
                                            {
                                                key: 'documentation',
                                                label: <span><FileTextOutlined /> Documentation</span>,
                                                children: (
                                                    <Table
                                                        dataSource={currentChecklist.document_statuses || []}
                                                        columns={docColumns}
                                                        rowKey="id"
                                                        size="small"
                                                        pagination={false}
                                                    />
                                                )
                                            },
                                            {
                                                key: 'ce_details',
                                                label: <span><SafetyCertificateOutlined /> CE Details</span>,
                                                children: (
                                                    <Card>
                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                                            <Row gutter={16}>
                                                                <Col span={12}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Product Type</label>
                                                                    <Select
                                                                        style={{ width: '100%' }}
                                                                        value={currentChecklist.ce_product_type_id || undefined}
                                                                        onChange={(val) => handleUpdateChecklist({ ce_product_type_id: val })}
                                                                        placeholder="Select product type"
                                                                        allowClear
                                                                        options={productTypes.map(pt => ({ value: pt.id, label: pt.name }))}
                                                                    />
                                                                </Col>
                                                                <Col span={12}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Status</label>
                                                                    <Select
                                                                        style={{ width: '100%' }}
                                                                        value={currentChecklist.status}
                                                                        onChange={(val) => handleUpdateChecklist({ status: val })}
                                                                        options={[
                                                                            { value: 'not_started', label: 'Not Started' },
                                                                            { value: 'in_progress', label: 'In Progress' },
                                                                            { value: 'ready', label: 'Ready' },
                                                                            { value: 'approved', label: 'Approved' },
                                                                        ]}
                                                                    />
                                                                </Col>
                                                            </Row>
                                                            <Row gutter={16}>
                                                                <Col span={12}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>CE Placement</label>
                                                                    <Input
                                                                        defaultValue={currentChecklist.ce_placement || ''}
                                                                        placeholder="e.g. On product label, packaging"
                                                                        onBlur={(e) => handleUpdateChecklist({ ce_placement: e.target.value })}
                                                                    />
                                                                </Col>
                                                                <Col span={12}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Placement Notes</label>
                                                                    <Input
                                                                        defaultValue={currentChecklist.ce_placement_notes || ''}
                                                                        placeholder="Additional placement notes"
                                                                        onBlur={(e) => handleUpdateChecklist({ ce_placement_notes: e.target.value })}
                                                                    />
                                                                </Col>
                                                            </Row>
                                                            <Row gutter={16}>
                                                                <Col span={6}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Notified Body Required</label>
                                                                    <div>
                                                                        <Checkbox
                                                                            checked={currentChecklist.notified_body_required}
                                                                            onChange={(e) => handleUpdateChecklist({ notified_body_required: e.target.checked })}
                                                                        >Yes</Checkbox>
                                                                    </div>
                                                                </Col>
                                                                <Col span={6}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>NB Name</label>
                                                                    <Input
                                                                        defaultValue={currentChecklist.notified_body_name || ''}
                                                                        placeholder="Name"
                                                                        onBlur={(e) => handleUpdateChecklist({ notified_body_name: e.target.value })}
                                                                    />
                                                                </Col>
                                                                <Col span={6}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>NB Number</label>
                                                                    <Input
                                                                        defaultValue={currentChecklist.notified_body_number || ''}
                                                                        placeholder="Number"
                                                                        onBlur={(e) => handleUpdateChecklist({ notified_body_number: e.target.value })}
                                                                    />
                                                                </Col>
                                                                <Col span={6}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>NB Certificate Ref</label>
                                                                    <Input
                                                                        defaultValue={currentChecklist.notified_body_certificate_ref || ''}
                                                                        placeholder="Reference"
                                                                        onBlur={(e) => handleUpdateChecklist({ notified_body_certificate_ref: e.target.value })}
                                                                    />
                                                                </Col>
                                                            </Row>
                                                        </div>
                                                    </Card>
                                                )
                                            },
                                            {
                                                key: 'traceability',
                                                label: <span><InfoCircleOutlined /> Traceability</span>,
                                                children: (
                                                    <Card>
                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                                            <Row gutter={16}>
                                                                <Col span={12}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Version Identifier</label>
                                                                    <Input
                                                                        defaultValue={currentChecklist.version_identifier || ''}
                                                                        placeholder="e.g. v2.1.0"
                                                                        onBlur={(e) => handleUpdateChecklist({ version_identifier: e.target.value })}
                                                                    />
                                                                </Col>
                                                                <Col span={12}>
                                                                    <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Build Identifier</label>
                                                                    <Input
                                                                        defaultValue={currentChecklist.build_identifier || ''}
                                                                        placeholder="e.g. build-2025-001"
                                                                        onBlur={(e) => handleUpdateChecklist({ build_identifier: e.target.value })}
                                                                    />
                                                                </Col>
                                                            </Row>
                                                            <div>
                                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>DoC Publication URL</label>
                                                                <Input
                                                                    defaultValue={currentChecklist.doc_publication_url || ''}
                                                                    placeholder="https://example.com/doc"
                                                                    onBlur={(e) => handleUpdateChecklist({ doc_publication_url: e.target.value })}
                                                                />
                                                            </div>
                                                            <div>
                                                                <label style={{ fontSize: 12, fontWeight: 500, color: '#6b7280' }}>Product Variants</label>
                                                                <TextArea
                                                                    rows={3}
                                                                    defaultValue={currentChecklist.product_variants || ''}
                                                                    placeholder="List product variants, models, or SKUs"
                                                                    onBlur={(e) => handleUpdateChecklist({ product_variants: e.target.value })}
                                                                />
                                                            </div>
                                                        </div>
                                                    </Card>
                                                )
                                            },
                                        ]}
                                    />
                                </div>
                            )
                        }] : [])
                    ]}
                />
            </div>
        </div>
    );
};

export default CEMarkingChecklistPage;
