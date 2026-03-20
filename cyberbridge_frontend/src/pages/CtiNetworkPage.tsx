import { Card, Row, Col, Statistic, Spin, Empty, Table, Tag, Typography } from "antd";
import type { ColumnsType } from 'antd/es/table';
import {
    GlobalOutlined,
    ApiOutlined,
    ClusterOutlined,
} from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useEffect } from "react";
import useCtiStore from "../store/useCtiStore.ts";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { Bar, Pie } from '@ant-design/plots';

const { Title } = Typography;

const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    try {
        return new Date(dateStr).toLocaleString();
    } catch {
        return dateStr;
    }
};

const CtiNetworkPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    const {
        nmap,
        nmapLoading,
        fetchNmapResults,
    } = useCtiStore();

    useEffect(() => {
        fetchNmapResults();
    }, []);

    const total = nmap?.total ?? 0;
    const openPorts = nmap?.open_ports ?? [];
    const byService = nmap?.by_service ?? [];
    const hosts = nmap?.hosts ?? [];
    const recent = nmap?.recent ?? [];

    const portBarConfig = {
        data: openPorts.slice(0, 10),
        xField: 'port',
        yField: 'count',
        height: 280,
        colorField: 'port',
        label: { position: 'top' as const },
    };

    const servicePieConfig = {
        data: byService.map((s: any) => ({ type: s.service, value: s.count })),
        angleField: 'value',
        colorField: 'type',
        innerRadius: 0.6,
        height: 280,
        label: { text: 'type', position: 'outside' as const },
        legend: { position: 'bottom' as const },
    };

    const hostColumns: ColumnsType<any> = [
        {
            title: 'IP Address',
            dataIndex: 'ip',
            key: 'ip',
            width: 150,
            render: (v: string) => (
                <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#1890ff' }}>{v || '-'}</span>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: 100,
            render: (v: string) => (
                <Tag color={v === 'up' ? 'green' : 'default'}>{v || 'unknown'}</Tag>
            ),
        },
        {
            title: 'Ports',
            dataIndex: 'ports',
            key: 'ports',
            render: (ports: string[]) => (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {(ports || []).slice(0, 8).map((p: string) => (
                        <Tag key={p} color="blue" style={{ fontSize: 11, fontFamily: 'monospace' }}>{p}</Tag>
                    ))}
                    {(ports || []).length > 8 && (
                        <Tag color="default">+{ports.length - 8}</Tag>
                    )}
                </div>
            ),
        },
        {
            title: 'Services',
            dataIndex: 'services',
            key: 'services',
            render: (services: string[]) => (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {(services || []).slice(0, 5).map((s: string) => (
                        <Tag key={s} color="cyan" style={{ fontSize: 11 }}>{s}</Tag>
                    ))}
                    {(services || []).length > 5 && (
                        <Tag color="default">+{services.length - 5}</Tag>
                    )}
                </div>
            ),
        },
    ];

    const recentColumns: ColumnsType<any> = [
        {
            title: 'Indicator',
            dataIndex: 'name',
            key: 'name',
            ellipsis: true,
        },
        {
            title: 'Port',
            dataIndex: 'port',
            key: 'port',
            width: 80,
            render: (v: string) => (
                <Tag color="blue" style={{ fontFamily: 'monospace', fontWeight: 600 }}>{v || '-'}</Tag>
            ),
        },
        {
            title: 'Protocol',
            dataIndex: 'protocol',
            key: 'protocol',
            width: 90,
            render: (v: string) => <Tag color="default">{v || '-'}</Tag>,
        },
        {
            title: 'Service',
            dataIndex: 'service',
            key: 'service',
            width: 110,
            render: (v: string) => <Tag color="cyan">{v || 'unknown'}</Tag>,
        },
        {
            title: 'First Seen',
            dataIndex: 'created',
            key: 'created',
            width: 170,
            render: (v: string) => <span style={{ fontSize: 12, color: '#8c8c8c' }}>{formatDate(v)}</span>,
        },
    ];

    return (
        <div>
            <div className={'page-parent'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys} onOpenChange={menuHighlighting.onOpenChange} />
                <div className={'page-content'}>
                    <Title level={3}>CTI Network Scan</Title>

                    {/* Stat Cards */}
                    <Spin spinning={nmapLoading}>
                        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Total Hosts"
                                        value={hosts.length}
                                        prefix={<ClusterOutlined style={{ color: '#52c41a' }} />}
                                        valueStyle={{ color: '#52c41a' }}
                                    />
                                </Card>
                            </Col>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Open Ports"
                                        value={openPorts.length}
                                        prefix={<ApiOutlined style={{ color: '#13c2c2' }} />}
                                        valueStyle={{ color: '#13c2c2' }}
                                    />
                                </Card>
                            </Col>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Unique Services"
                                        value={byService.length}
                                        prefix={<GlobalOutlined style={{ color: '#1890ff' }} />}
                                        valueStyle={{ color: '#1890ff' }}
                                    />
                                </Card>
                            </Col>
                        </Row>
                    </Spin>

                    {total === 0 ? (
                        <Card>
                            <Empty description="No network scan data yet - configure targets and start the connector" />
                        </Card>
                    ) : (
                        <>
                            {/* Charts Row */}
                            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                                <Col xs={24} md={12}>
                                    <Card title="Top 10 Open Ports">
                                        {openPorts.length === 0 ? (
                                            <Empty description="No port data" />
                                        ) : (
                                            <Bar {...portBarConfig} />
                                        )}
                                    </Card>
                                </Col>
                                <Col xs={24} md={12}>
                                    <Card title="Services Detected">
                                        {byService.length === 0 ? (
                                            <Empty description="No service data" />
                                        ) : (
                                            <Pie {...servicePieConfig} />
                                        )}
                                    </Card>
                                </Col>
                            </Row>

                            {/* Host Inventory Table */}
                            {hosts.length > 0 && (
                                <Card title="Host Inventory" style={{ marginBottom: 24 }}>
                                    <Table
                                        dataSource={hosts}
                                        columns={hostColumns}
                                        rowKey="ip"
                                        pagination={{ pageSize: 10, size: 'small' }}
                                        size="small"
                                        scroll={{ x: 700 }}
                                        locale={{ emptyText: <Empty description="No hosts discovered" /> }}
                                    />
                                </Card>
                            )}

                            {/* Recent Findings Table */}
                            <Card title="Open Ports Discovered" style={{ marginBottom: 24 }}>
                                <Table
                                    dataSource={recent.slice(0, 50)}
                                    columns={recentColumns}
                                    rowKey="id"
                                    pagination={{ pageSize: 20, size: 'small' }}
                                    size="small"
                                    scroll={{ x: 600 }}
                                    locale={{ emptyText: <Empty description="No open ports discovered yet" /> }}
                                />
                            </Card>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CtiNetworkPage;
