import { Card, Row, Col, Statistic, Spin, Empty, Table, Tag, Typography } from "antd";
import type { ColumnsType } from 'antd/es/table';
import {
    CodeOutlined,
    BugOutlined,
    WarningOutlined,
} from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useEffect } from "react";
import useCtiStore from "../store/useCtiStore.ts";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { Bar, Pie } from '@ant-design/plots';

const { Title } = Typography;

const SEVERITY_TAG_COLORS: Record<string, string> = {
    ERROR: 'red',
    WARNING: 'orange',
    INFO: 'blue',
};

const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    try {
        return new Date(dateStr).toLocaleString();
    } catch {
        return dateStr;
    }
};

const CtiCodeAnalysisPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    const {
        semgrep,
        semgrepLoading,
        fetchSemgrepResults,
    } = useCtiStore();

    useEffect(() => {
        fetchSemgrepResults();
    }, []);

    const total = semgrep?.total ?? 0;
    const bySeverity = semgrep?.by_severity ?? { ERROR: 0, WARNING: 0, INFO: 0 };
    const byOwasp = semgrep?.by_owasp ?? [];
    const byCheck = semgrep?.by_check ?? [];
    const recent = semgrep?.recent ?? [];

    const errorCount = bySeverity['ERROR'] ?? 0;
    const warningCount = bySeverity['WARNING'] ?? 0;
    const uniqueCategories = byOwasp.length;

    const pieData = Object.entries(bySeverity)
        .filter(([, v]) => (v as number) > 0)
        .map(([name, value]) => ({ type: name, value: value as number }));

    const severityPieConfig = {
        data: pieData,
        angleField: 'value',
        colorField: 'type',
        innerRadius: 0.6,
        height: 280,
        color: ['#ff4d4f', '#faad14', '#1890ff'],
        label: { text: 'type', position: 'outside' as const },
        legend: { position: 'bottom' as const },
    };

    const owaspBarConfig = {
        data: byOwasp.slice(0, 10),
        xField: 'count',
        yField: 'category',
        height: Math.max(250, byOwasp.slice(0, 10).length * 36),
        colorField: 'category',
        label: { position: 'right' as const },
    };

    const recentColumns: ColumnsType<any> = [
        {
            title: 'Rule ID',
            dataIndex: 'name',
            key: 'name',
            ellipsis: true,
            render: (v: string) => (
                <span style={{ fontSize: 12, fontFamily: 'monospace' }}>
                    {v?.replace('Semgrep: ', '') || '-'}
                </span>
            ),
        },
        {
            title: 'Severity',
            dataIndex: 'severity',
            key: 'severity',
            width: 100,
            render: (v: string) => (
                <Tag color={SEVERITY_TAG_COLORS[v?.toUpperCase()] || 'default'}>
                    {v || 'UNKNOWN'}
                </Tag>
            ),
            sorter: (a: any, b: any) => {
                const order: Record<string, number> = { ERROR: 0, WARNING: 1, INFO: 2 };
                return (order[a.severity] ?? 3) - (order[b.severity] ?? 3);
            },
        },
        {
            title: 'CWE',
            dataIndex: 'cwe',
            key: 'cwe',
            width: 110,
            render: (v: string) => v ? (
                <Tag color="warning" style={{ fontFamily: 'monospace', fontSize: 10 }}>{v}</Tag>
            ) : <span style={{ color: '#8c8c8c', fontSize: 11 }}>-</span>,
        },
        {
            title: 'File',
            dataIndex: 'file',
            key: 'file',
            ellipsis: true,
            render: (v: string) => (
                <span style={{ fontSize: 11, fontFamily: 'monospace', color: '#8c8c8c' }} title={v}>
                    {v ? (v.length > 50 ? '...' + v.slice(-50) : v) : '-'}
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
                    <Title level={3}>CTI Code Analysis</Title>

                    {/* Stat Cards */}
                    <Spin spinning={semgrepLoading}>
                        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Total Findings"
                                        value={total}
                                        prefix={<CodeOutlined style={{ color: '#1890ff' }} />}
                                        valueStyle={{ color: '#1890ff' }}
                                    />
                                </Card>
                            </Col>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Critical / High"
                                        value={errorCount + warningCount}
                                        prefix={<BugOutlined style={{ color: '#ff4d4f' }} />}
                                        valueStyle={{ color: '#ff4d4f' }}
                                    />
                                    {total > 0 && (
                                        <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
                                            {Math.round(((errorCount + warningCount) / total) * 100)}% of total
                                        </div>
                                    )}
                                </Card>
                            </Col>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="OWASP Categories"
                                        value={uniqueCategories}
                                        prefix={<WarningOutlined style={{ color: '#faad14' }} />}
                                        valueStyle={{ color: '#faad14' }}
                                    />
                                </Card>
                            </Col>
                        </Row>
                    </Spin>

                    {total === 0 ? (
                        <Card>
                            <Empty description="No code analysis data yet - configure scan path and start the connector" />
                        </Card>
                    ) : (
                        <>
                            {/* Charts Row */}
                            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                                <Col xs={24} md={12}>
                                    <Card title="Severity Distribution">
                                        {pieData.length === 0 ? (
                                            <Empty description="No severity data" />
                                        ) : (
                                            <Pie {...severityPieConfig} />
                                        )}
                                    </Card>
                                </Col>
                                <Col xs={24} md={12}>
                                    <Card title="OWASP Categories">
                                        {byOwasp.length === 0 ? (
                                            <Empty description="No OWASP data" />
                                        ) : (
                                            <Bar {...owaspBarConfig} />
                                        )}
                                    </Card>
                                </Col>
                            </Row>

                            {/* Code Findings Table */}
                            <Card title="Code Findings" style={{ marginBottom: 24 }}>
                                <Table
                                    dataSource={recent}
                                    columns={recentColumns}
                                    rowKey="id"
                                    pagination={{ pageSize: 20, size: 'small' }}
                                    size="small"
                                    scroll={{ x: 700 }}
                                    locale={{ emptyText: <Empty description="No code findings yet" /> }}
                                />
                            </Card>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default CtiCodeAnalysisPage;
