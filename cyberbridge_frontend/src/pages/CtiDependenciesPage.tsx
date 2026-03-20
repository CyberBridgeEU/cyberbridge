import { Card, Row, Col, Statistic, Spin, Empty, Table, Tag, Typography } from "antd";
import type { ColumnsType } from 'antd/es/table';
import {
    NodeIndexOutlined,
    FireOutlined,
    ClusterOutlined,
} from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useEffect } from "react";
import useCtiStore from "../store/useCtiStore.ts";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { Bar, Pie } from '@ant-design/plots';

const { Title } = Typography;

const SEVERITY_TAG_COLORS: Record<string, string> = {
    Critical: 'magenta',
    High: 'red',
    Medium: 'orange',
    Low: 'green',
};

const SEVERITY_ORDER: Record<string, number> = {
    Critical: 0,
    High: 1,
    Medium: 2,
    Low: 3,
};

const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    try {
        return new Date(dateStr).toLocaleString();
    } catch {
        return dateStr;
    }
};

const CtiDependenciesPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    const {
        osv,
        osvLoading,
        fetchOsvResults,
    } = useCtiStore();

    useEffect(() => {
        fetchOsvResults();
    }, []);

    const total = osv?.total ?? 0;
    const bySeverity = osv?.by_severity ?? { Critical: 0, High: 0, Medium: 0, Low: 0 };
    const byEcosystem = osv?.by_ecosystem ?? [];
    const topPackages = osv?.top_packages ?? [];
    const recent = osv?.recent ?? [];

    const criticalCount = bySeverity['Critical'] ?? 0;
    const uniqueEcosystems = byEcosystem.length;

    const pieData = Object.entries(bySeverity)
        .filter(([, v]) => (v as number) > 0)
        .map(([name, value]) => ({ type: name, value: value as number }));

    const severityPieConfig = {
        data: pieData,
        angleField: 'value',
        colorField: 'type',
        innerRadius: 0.6,
        height: 280,
        color: ['#eb2f96', '#ff4d4f', '#faad14', '#52c41a'],
        label: { text: 'type', position: 'outside' as const },
        legend: { position: 'bottom' as const },
    };

    const ecosystemBarConfig = {
        data: byEcosystem,
        xField: 'ecosystem',
        yField: 'count',
        height: 280,
        colorField: 'ecosystem',
        label: { position: 'top' as const },
    };

    // Sort recent by severity
    const sortedRecent = [...recent].sort(
        (a, b) => (SEVERITY_ORDER[a.severity] ?? 4) - (SEVERITY_ORDER[b.severity] ?? 4)
    );

    const recentColumns: ColumnsType<any> = [
        {
            title: 'Package',
            key: 'package',
            ellipsis: true,
            render: (_: any, record: any) => {
                const name = record.name || '';
                const match = name.match(/Vulnerable dependency: ([^\s]+) \(/);
                const pkg = match ? match[1] : name;
                return (
                    <span style={{ fontSize: 12, fontFamily: 'monospace' }}>{pkg || '-'}</span>
                );
            },
        },
        {
            title: 'Vulnerability ID',
            dataIndex: 'cve_id',
            key: 'cve_id',
            width: 180,
            render: (v: string) => v ? (
                <span style={{ fontSize: 12, fontFamily: 'monospace', fontWeight: v.startsWith('CVE-') ? 600 : 400 }}>
                    {v}
                </span>
            ) : <span style={{ color: '#8c8c8c', fontSize: 11 }}>-</span>,
        },
        {
            title: 'Severity',
            dataIndex: 'severity',
            key: 'severity',
            width: 100,
            render: (v: string) => (
                <Tag color={SEVERITY_TAG_COLORS[v] || 'default'}>{v || 'Unknown'}</Tag>
            ),
            sorter: (a: any, b: any) =>
                (SEVERITY_ORDER[a.severity] ?? 4) - (SEVERITY_ORDER[b.severity] ?? 4),
            defaultSortOrder: 'ascend' as const,
        },
        {
            title: 'Ecosystem',
            dataIndex: 'ecosystem',
            key: 'ecosystem',
            width: 110,
            render: (v: string) => v ? (
                <Tag color="blue" style={{ fontSize: 11, textTransform: 'uppercase' }}>{v}</Tag>
            ) : <span style={{ color: '#8c8c8c', fontSize: 11 }}>-</span>,
        },
        {
            title: 'Detected',
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
                    <Title level={3}>CTI Dependencies</Title>

                    {/* Stat Cards */}
                    <Spin spinning={osvLoading}>
                        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Total CVEs"
                                        value={total}
                                        prefix={<NodeIndexOutlined style={{ color: '#1890ff' }} />}
                                        valueStyle={{ color: '#1890ff' }}
                                    />
                                </Card>
                            </Col>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Critical CVEs"
                                        value={criticalCount}
                                        prefix={<FireOutlined style={{ color: '#eb2f96' }} />}
                                        valueStyle={{ color: '#eb2f96' }}
                                    />
                                    {total > 0 && (
                                        <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
                                            {Math.round((criticalCount / total) * 100)}% of total
                                        </div>
                                    )}
                                </Card>
                            </Col>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Ecosystems"
                                        value={uniqueEcosystems}
                                        prefix={<ClusterOutlined style={{ color: '#13c2c2' }} />}
                                        valueStyle={{ color: '#13c2c2' }}
                                    />
                                </Card>
                            </Col>
                        </Row>
                    </Spin>

                    {total === 0 ? (
                        <Card>
                            <Empty description="No dependency scan data yet - configure scan path and start the connector" />
                        </Card>
                    ) : (
                        <>
                            {/* Charts Row */}
                            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                                <Col xs={24} md={12}>
                                    <Card title="CVE Severity Distribution">
                                        {pieData.length === 0 ? (
                                            <Empty description="No severity data" />
                                        ) : (
                                            <Pie {...severityPieConfig} />
                                        )}
                                    </Card>
                                </Col>
                                <Col xs={24} md={12}>
                                    <Card title="Ecosystem Breakdown">
                                        {byEcosystem.length === 0 ? (
                                            <Empty description="No ecosystem data" />
                                        ) : (
                                            <Bar {...ecosystemBarConfig} />
                                        )}
                                    </Card>
                                </Col>
                            </Row>

                            {/* Top Vulnerable Packages */}
                            {topPackages.length > 0 && (
                                <Card title="Top Vulnerable Packages" style={{ marginBottom: 24 }}>
                                    <Bar
                                        data={topPackages.slice(0, 10)}
                                        xField="count"
                                        yField="package"
                                        height={Math.max(200, topPackages.slice(0, 10).length * 32)}
                                        colorField="package"
                                        label={{ position: 'right' as const }}
                                    />
                                </Card>
                            )}

                            {/* Vulnerable Dependencies Table */}
                            <Card title="Vulnerable Dependencies" style={{ marginBottom: 24 }}>
                                <Table
                                    dataSource={sortedRecent}
                                    columns={recentColumns}
                                    rowKey="id"
                                    pagination={{ pageSize: 20, size: 'small' }}
                                    size="small"
                                    scroll={{ x: 700 }}
                                    locale={{ emptyText: <Empty description="No vulnerable dependencies found yet" /> }}
                                />
                            </Card>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CtiDependenciesPage;
