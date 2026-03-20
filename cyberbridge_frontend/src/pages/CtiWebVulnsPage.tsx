import { Card, Row, Col, Statistic, Spin, Empty, Table, Tag, Typography } from "antd";
import type { ColumnsType } from 'antd/es/table';
import {
    BugOutlined,
    FireOutlined,
    WarningOutlined,
    InfoCircleOutlined,
} from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useEffect } from "react";
import useCtiStore from "../store/useCtiStore.ts";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { Bar, Pie } from '@ant-design/plots';

const { Title } = Typography;

const RISK_TAG_COLORS: Record<string, string> = {
    High: 'red',
    Medium: 'orange',
    Low: 'green',
    Info: 'default',
};

const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    try {
        return new Date(dateStr).toLocaleString();
    } catch {
        return dateStr;
    }
};

const CtiWebVulnsPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    const {
        zap,
        zapLoading,
        fetchZapResults,
    } = useCtiStore();

    useEffect(() => {
        fetchZapResults();
    }, []);

    const total = zap?.total ?? 0;
    const byRisk = zap?.by_risk ?? { High: 0, Medium: 0, Low: 0, Info: 0 };
    const byCwe = zap?.by_cwe ?? [];
    const recent = zap?.recent ?? [];

    const highCount = byRisk['High'] ?? 0;
    const mediumCount = byRisk['Medium'] ?? 0;
    const lowCount = byRisk['Low'] ?? 0;

    const pieData = Object.entries(byRisk)
        .filter(([, v]) => (v as number) > 0)
        .map(([name, value]) => ({ type: name, value: value as number }));

    const riskPieConfig = {
        data: pieData,
        angleField: 'value',
        colorField: 'type',
        innerRadius: 0.6,
        height: 280,
        color: ['#ff4d4f', '#faad14', '#52c41a', '#8c8c8c'],
        label: { text: 'type', position: 'outside' as const },
        legend: { position: 'bottom' as const },
    };

    const cweBarConfig = {
        data: byCwe.slice(0, 10),
        xField: 'count',
        yField: 'cwe',
        height: Math.max(250, byCwe.slice(0, 10).length * 32),
        colorField: 'cwe',
        label: { position: 'right' as const },
    };

    const recentColumns: ColumnsType<any> = [
        {
            title: 'Vulnerability',
            dataIndex: 'name',
            key: 'name',
            ellipsis: true,
        },
        {
            title: 'Risk',
            dataIndex: 'risk',
            key: 'risk',
            width: 100,
            render: (v: string) => (
                <Tag color={RISK_TAG_COLORS[v] || 'default'}>{v || 'Unknown'}</Tag>
            ),
            sorter: (a: any, b: any) => {
                const order: Record<string, number> = { High: 0, Medium: 1, Low: 2, Info: 3 };
                return (order[a.risk] ?? 4) - (order[b.risk] ?? 4);
            },
            defaultSortOrder: 'ascend' as const,
        },
        {
            title: 'CWE ID',
            dataIndex: 'cwe',
            key: 'cwe',
            width: 110,
            render: (v: string) => v ? (
                <Tag color="warning" style={{ fontFamily: 'monospace', fontSize: 11 }}>CWE-{v}</Tag>
            ) : <span style={{ color: '#8c8c8c', fontSize: 11 }}>-</span>,
        },
        {
            title: 'URL',
            dataIndex: 'url',
            key: 'url',
            ellipsis: true,
            render: (v: string) => (
                <span style={{ fontSize: 11, fontFamily: 'monospace', color: '#8c8c8c' }} title={v}>
                    {v ? (v.length > 60 ? v.substring(0, 60) + '...' : v) : '-'}
                </span>
            ),
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
                    <Title level={3}>CTI Web Vulnerabilities</Title>

                    {/* Stat Cards */}
                    <Spin spinning={zapLoading}>
                        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                            <Col xs={24} sm={12} md={6}>
                                <Card>
                                    <Statistic
                                        title="Total Vulns"
                                        value={total}
                                        prefix={<BugOutlined style={{ color: '#1890ff' }} />}
                                        valueStyle={{ color: '#1890ff' }}
                                    />
                                </Card>
                            </Col>
                            <Col xs={24} sm={12} md={6}>
                                <Card>
                                    <Statistic
                                        title="High Risk"
                                        value={highCount}
                                        prefix={<FireOutlined style={{ color: '#ff4d4f' }} />}
                                        valueStyle={{ color: '#ff4d4f' }}
                                    />
                                    {total > 0 && (
                                        <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
                                            {Math.round((highCount / total) * 100)}% of total
                                        </div>
                                    )}
                                </Card>
                            </Col>
                            <Col xs={24} sm={12} md={6}>
                                <Card>
                                    <Statistic
                                        title="Medium Risk"
                                        value={mediumCount}
                                        prefix={<WarningOutlined style={{ color: '#faad14' }} />}
                                        valueStyle={{ color: '#faad14' }}
                                    />
                                </Card>
                            </Col>
                            <Col xs={24} sm={12} md={6}>
                                <Card>
                                    <Statistic
                                        title="Low Risk"
                                        value={lowCount}
                                        prefix={<InfoCircleOutlined style={{ color: '#52c41a' }} />}
                                        valueStyle={{ color: '#52c41a' }}
                                    />
                                </Card>
                            </Col>
                        </Row>
                    </Spin>

                    {total === 0 ? (
                        <Card>
                            <Empty description="No web vulnerability scan data yet - configure targets and start the connector" />
                        </Card>
                    ) : (
                        <>
                            {/* Charts Row */}
                            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                                <Col xs={24} md={12}>
                                    <Card title="Risk Distribution">
                                        {pieData.length === 0 ? (
                                            <Empty description="No risk data" />
                                        ) : (
                                            <Pie {...riskPieConfig} />
                                        )}
                                    </Card>
                                </Col>
                                <Col xs={24} md={12}>
                                    <Card title="Top CWE IDs">
                                        {byCwe.length === 0 ? (
                                            <Empty description="No CWE data" />
                                        ) : (
                                            <Bar {...cweBarConfig} />
                                        )}
                                    </Card>
                                </Col>
                            </Row>

                            {/* Findings Table */}
                            <Card title="Vulnerability Findings" style={{ marginBottom: 24 }}>
                                <Table
                                    dataSource={recent}
                                    columns={recentColumns}
                                    rowKey="id"
                                    pagination={{ pageSize: 20, size: 'small' }}
                                    size="small"
                                    scroll={{ x: 800 }}
                                    locale={{ emptyText: <Empty description="No web application findings yet" /> }}
                                />
                            </Card>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CtiWebVulnsPage;
