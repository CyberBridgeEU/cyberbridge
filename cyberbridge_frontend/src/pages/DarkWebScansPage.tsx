import { useEffect, useState, useMemo } from 'react';
import { Row, Col, Card, Statistic, Table, Button, Tag, Input, Select, Space, Popconfirm, message, Typography } from 'antd';
import {
    PlusOutlined,
    SearchOutlined,
    CheckCircleOutlined,
    SyncOutlined,
    CloseCircleOutlined,
    EyeOutlined,
    FilePdfOutlined,
    DeleteOutlined,
    ReloadOutlined,
} from '@ant-design/icons';
import Sidebar from '../components/Sidebar';
import { useLocation, Link } from 'wouter';
import { useMenuHighlighting } from '../utils/menuUtils';
import useDarkWebStore from '../store/useDarkWebStore';
import NewScanModal from '../components/NewScanModal';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const statusColorMap: Record<string, string> = {
    queued: 'orange',
    processing: 'blue',
    completed: 'green',
    failed: 'red',
};

const DarkWebScansPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const [showNewScanModal, setShowNewScanModal] = useState(false);
    const [searchText, setSearchText] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('all');

    const {
        scans,
        totalScans,
        scansLoading,
        fetchScans,
        deleteScan,
        downloadPdf,
    } = useDarkWebStore();

    useEffect(() => {
        fetchScans();
        const interval = setInterval(() => fetchScans(), 5000);
        return () => clearInterval(interval);
    }, []);

    const filteredScans = useMemo(() => {
        return scans.filter(scan => {
            const matchesSearch = !searchText || scan.keyword.toLowerCase().includes(searchText.toLowerCase());
            const matchesStatus = statusFilter === 'all' || scan.status === statusFilter;
            return matchesSearch && matchesStatus;
        });
    }, [scans, searchText, statusFilter]);

    const stats = useMemo(() => ({
        total: totalScans,
        completed: scans.filter(s => s.status === 'completed').length,
        processing: scans.filter(s => s.status === 'processing').length,
        failed: scans.filter(s => s.status === 'failed').length,
    }), [scans, totalScans]);

    const handleDelete = async (scanId: string) => {
        try {
            await deleteScan(scanId);
            message.success('Scan deleted successfully');
        } catch {
            message.error('Failed to delete scan');
        }
    };

    const handleDownloadPdf = async (scanId: string, keyword: string) => {
        try {
            await downloadPdf(scanId, keyword);
        } catch {
            message.error('Failed to download PDF');
        }
    };

    const columns: ColumnsType<any> = [
        {
            title: 'Keyword',
            dataIndex: 'keyword',
            key: 'keyword',
            render: (text: string, record: any) => (
                <div>
                    <Link href={`/dark-web/scan/${record.scan_id}`} style={{ fontWeight: 500 }}>
                        {text}
                    </Link>
                    <div>
                        <Text type="secondary" style={{ fontSize: 11, fontFamily: 'monospace' }}>
                            {record.scan_id.substring(0, 8)}...
                        </Text>
                    </div>
                </div>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: 120,
            render: (status: string) => (
                <Tag color={statusColorMap[status] || 'default'} style={{ textTransform: 'capitalize' }}>
                    {status === 'processing' && <SyncOutlined spin style={{ marginRight: 4 }} />}
                    {status}
                </Tag>
            ),
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 160,
            render: (text: string) => text ? dayjs(text.endsWith('Z') ? text : text + 'Z').format('DD/MM/YYYY HH:mm') : '-',
        },
        {
            title: 'Completed',
            dataIndex: 'completed_at',
            key: 'completed_at',
            width: 160,
            render: (text: string) => text ? dayjs(text.endsWith('Z') ? text : text + 'Z').format('DD/MM/YYYY HH:mm') : '-',
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 200,
            render: (_: any, record: any) => (
                <Space size="small">
                    <Link href={`/dark-web/scan/${record.scan_id}`}>
                        <Button size="small" icon={<EyeOutlined />}>View</Button>
                    </Link>
                    {record.status === 'completed' && record.files?.pdf_exists && (
                        <Button
                            size="small"
                            icon={<FilePdfOutlined />}
                            onClick={() => handleDownloadPdf(record.scan_id, record.keyword)}
                        >
                            PDF
                        </Button>
                    )}
                    <Popconfirm
                        title="Delete Scan"
                        description="Are you sure? This cannot be undone."
                        onConfirm={() => handleDelete(record.scan_id)}
                        okText="Delete"
                        okType="danger"
                    >
                        <Button
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                        />
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--page-background)' }}>
            <Sidebar
                selectedKeys={menuHighlighting.selectedKeys}
                openKeys={menuHighlighting.openKeys}
                onOpenChange={menuHighlighting.onOpenChange}
            />
            <div style={{ flex: 1, padding: '24px', overflow: 'auto' }}>
                {/* Header */}
                <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <Title level={3} style={{ margin: 0 }}>Dark Web Scans</Title>
                        <Text type="secondary">Manage and monitor your dark web scans</Text>
                    </div>
                    <Space>
                        <Button icon={<ReloadOutlined />} onClick={() => fetchScans()}>Refresh</Button>
                        <Button type="primary" icon={<PlusOutlined />} onClick={() => setShowNewScanModal(true)}>
                            New Scan
                        </Button>
                    </Space>
                </div>

                {/* Filters */}
                <Card style={{ marginBottom: 16 }} bodyStyle={{ padding: '12px 16px' }}>
                    <Space wrap>
                        <Input
                            placeholder="Search scans by keyword..."
                            prefix={<SearchOutlined />}
                            value={searchText}
                            onChange={e => setSearchText(e.target.value)}
                            style={{ width: 280 }}
                            allowClear
                        />
                        <Select
                            value={statusFilter}
                            onChange={setStatusFilter}
                            style={{ width: 160 }}
                            options={[
                                { value: 'all', label: 'All Statuses' },
                                { value: 'queued', label: 'Queued' },
                                { value: 'processing', label: 'Processing' },
                                { value: 'completed', label: 'Completed' },
                                { value: 'failed', label: 'Failed' },
                            ]}
                        />
                    </Space>
                </Card>

                {/* Stats */}
                <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                    <Col xs={24} sm={12} md={6}>
                        <Card>
                            <Statistic title="Total" value={stats.total} prefix={<SearchOutlined />} />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <Card>
                            <Statistic title="Completed" value={stats.completed} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#389e0d' }} />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <Card>
                            <Statistic title="Processing" value={stats.processing} prefix={<SyncOutlined />} valueStyle={{ color: '#1890ff' }} />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <Card>
                            <Statistic title="Failed" value={stats.failed} prefix={<CloseCircleOutlined />} valueStyle={{ color: '#cf1322' }} />
                        </Card>
                    </Col>
                </Row>

                {/* Table */}
                <Card bordered={false}>
                    <Table
                        dataSource={filteredScans}
                        columns={columns}
                        rowKey="scan_id"
                        loading={scansLoading}
                        pagination={{ pageSize: 15, showSizeChanger: true, showTotal: (total) => `Total ${total} scans` }}
                        locale={{ emptyText: searchText ? 'No scans match your search.' : 'No scans yet. Create your first dark web scan.' }}
                    />
                </Card>

                <NewScanModal
                    open={showNewScanModal}
                    onClose={() => setShowNewScanModal(false)}
                    onSuccess={() => fetchScans()}
                />
            </div>
        </div>
    );
};

export default DarkWebScansPage;
