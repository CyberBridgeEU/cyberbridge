import { useEffect, useState, useRef } from 'react';
import { Row, Col, Card, Statistic, Table, Button, Alert, Spin, Space, Typography } from 'antd';
import {
    ClockCircleOutlined,
    SyncOutlined,
    TeamOutlined,
    SearchOutlined,
    PlusOutlined,
    EyeOutlined,
    FileTextOutlined,
} from '@ant-design/icons';
import Sidebar from '../components/Sidebar';
import { useLocation } from 'wouter';
import { useMenuHighlighting } from '../utils/menuUtils';
import useDarkWebStore from '../store/useDarkWebStore';
import NewScanModal from '../components/NewScanModal';
import { Link } from 'wouter';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const DarkWebDashboardPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const [showNewScanModal, setShowNewScanModal] = useState(false);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const {
        queueOverview,
        scans,
        totalScans,
        scansLoading,
        fetchQueueOverview,
        fetchScans,
    } = useDarkWebStore();

    useEffect(() => {
        fetchQueueOverview();
        fetchScans(undefined, 10);
    }, []);

    // Auto-refresh every 5 seconds when queue is active
    useEffect(() => {
        const isActive = (queueOverview?.processing_count ?? 0) > 0 || (queueOverview?.queue_length ?? 0) > 0;
        if (isActive) {
            intervalRef.current = setInterval(() => {
                fetchQueueOverview();
                fetchScans(undefined, 10);
            }, 5000);
        }
        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, [queueOverview?.processing_count, queueOverview?.queue_length]);

    const recentScans = scans.slice(0, 5);

    const columns: ColumnsType<any> = [
        {
            title: 'Keyword',
            dataIndex: 'keyword',
            key: 'keyword',
            render: (text: string, record: any) => (
                <Link href={`/dark-web/scan/${record.scan_id}`}>
                    {text}
                </Link>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => {
                const colorMap: Record<string, string> = {
                    queued: 'orange',
                    processing: 'blue',
                    completed: 'green',
                    failed: 'red',
                };
                return (
                    <span style={{ color: colorMap[status] || '#8c8c8c', fontWeight: 600, textTransform: 'capitalize' }}>
                        {status}
                    </span>
                );
            },
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (text: string) => text ? dayjs(text.endsWith('Z') ? text : text + 'Z').format('DD/MM/YYYY HH:mm') : '-',
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
                <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <Title level={3} style={{ margin: 0 }}>Dark Web Intelligence Dashboard</Title>
                        <Text type="secondary">Real-time dark web monitoring and analysis</Text>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            backgroundColor: '#52c41a',
                            display: 'inline-block',
                        }} />
                        <Text type="secondary" strong>System Operational</Text>
                    </div>
                </div>

                {/* KPI Stat Cards */}
                <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                    <Col xs={24} sm={12} md={6}>
                        <Card>
                            <Statistic
                                title="Queue Length"
                                value={queueOverview?.queue_length ?? 0}
                                prefix={<ClockCircleOutlined />}
                                valueStyle={{ color: '#1890ff' }}
                            />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <Card>
                            <Statistic
                                title="Currently Processing"
                                value={queueOverview?.processing_count ?? 0}
                                prefix={<SyncOutlined spin={!!(queueOverview?.processing_count)} />}
                                valueStyle={{ color: '#722ed1' }}
                            />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <Card>
                            <Statistic
                                title="Active Workers"
                                value={`${(queueOverview?.max_workers ?? 0) - (queueOverview?.processing_count ?? 0)}/${queueOverview?.max_workers ?? 0}`}
                                prefix={<TeamOutlined />}
                                valueStyle={{ color: '#389e0d' }}
                            />
                        </Card>
                    </Col>
                    <Col xs={24} sm={12} md={6}>
                        <Card>
                            <Statistic
                                title="Total Scans"
                                value={totalScans}
                                prefix={<SearchOutlined />}
                                valueStyle={{ color: '#1890ff' }}
                            />
                        </Card>
                    </Col>
                </Row>

                {/* Processing Banner */}
                {(queueOverview?.processing_count ?? 0) > 0 && (
                    <Alert
                        type="info"
                        showIcon
                        icon={<SyncOutlined spin />}
                        message={`${queueOverview!.processing_count} Scan${queueOverview!.processing_count !== 1 ? 's' : ''} In Progress`}
                        description={
                            <div>
                                {queueOverview?.currently_processing && queueOverview.currently_processing.length > 0 && (
                                    <Text type="secondary">
                                        Processing: {queueOverview.currently_processing.map(id => id.substring(0, 8) + '...').join(', ')}
                                    </Text>
                                )}
                                <div style={{ marginTop: 4 }}>
                                    <Text type="secondary">
                                        {queueOverview?.queue_length ?? 0} pending in queue | {queueOverview?.active_workers ?? 0}/{queueOverview?.max_workers ?? 0} workers running
                                    </Text>
                                </div>
                            </div>
                        }
                        style={{ marginBottom: 24 }}
                    />
                )}

                {/* Recent Scans & Quick Actions */}
                <Row gutter={[16, 16]}>
                    <Col xs={24} lg={16}>
                        <Card title="Recent Activity" bordered={false}>
                            <Table
                                dataSource={recentScans}
                                columns={columns}
                                rowKey="scan_id"
                                pagination={false}
                                loading={scansLoading}
                                size="small"
                                locale={{ emptyText: 'No recent scans' }}
                            />
                        </Card>
                    </Col>
                    <Col xs={24} lg={8}>
                        <Card title="Quick Actions" bordered={false}>
                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                <Button
                                    type="primary"
                                    icon={<PlusOutlined />}
                                    block
                                    onClick={() => setShowNewScanModal(true)}
                                >
                                    New Scan
                                </Button>
                                <Link href="/dark-web/scans">
                                    <Button icon={<EyeOutlined />} block>View All Scans</Button>
                                </Link>
                                <Link href="/dark-web/reports">
                                    <Button icon={<FileTextOutlined />} block>Reports</Button>
                                </Link>
                            </Space>
                        </Card>
                    </Col>
                </Row>

                <NewScanModal
                    open={showNewScanModal}
                    onClose={() => setShowNewScanModal(false)}
                    onSuccess={() => {
                        fetchScans(undefined, 10);
                        fetchQueueOverview();
                    }}
                />
            </div>
        </div>
    );
};

export default DarkWebDashboardPage;
