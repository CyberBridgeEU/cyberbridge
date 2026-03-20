import { Card, Row, Col, Statistic, Spin, Empty, Table, Tag, Progress, Typography } from "antd";
import type { ColumnsType } from 'antd/es/table';
import {
    ThunderboltOutlined,
    AimOutlined,
    RadarChartOutlined,
} from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useEffect } from "react";
import useCtiStore from "../store/useCtiStore.ts";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { Bar, Pie } from '@ant-design/plots';

const { Title } = Typography;

const SOURCE_COLORS: Record<string, string> = {
    'Suricata IDS': '#1890ff',
    'Wazuh/SEUXDR Alerts': '#52c41a',
    'CAPE Malware Sandbox': '#ff4d4f',
    'Unknown': '#8c8c8c',
};

const getSourceColor = (source: string): string => {
    return SOURCE_COLORS[source] || '#1890ff';
};

const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    try {
        return new Date(dateStr).toLocaleString();
    } catch {
        return dateStr;
    }
};

const CtiThreatIntelPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    const {
        attackPatterns,
        indicators,
        attackPatternsLoading,
        indicatorsLoading,
        fetchAttackPatterns,
        fetchIndicators,
    } = useCtiStore();

    useEffect(() => {
        fetchAttackPatterns();
        fetchIndicators();
    }, []);

    const apTotal = attackPatterns?.total ?? 0;
    const topTechniques = (attackPatterns?.top_techniques ?? []).slice(0, 15);
    const bySource = attackPatterns?.by_source ?? [];
    const recentAP = attackPatterns?.recent ?? [];

    const indTotal = indicators?.total ?? 0;
    const recentIndicators = (indicators?.recent ?? []).slice(0, 20);

    const techniqueBarData = topTechniques.map((t) => ({
        name: t.mitre_id ? t.mitre_id : (t.name.length > 16 ? t.name.substring(0, 16) + '...' : t.name),
        fullName: t.name,
        count: t.count,
        source: t.source,
    }));

    const techniqueBarConfig = {
        data: techniqueBarData,
        xField: 'count',
        yField: 'name',
        height: Math.max(300, techniqueBarData.length * 36),
        colorField: 'name',
        label: { position: 'right' as const },
    };

    const sourcePieConfig = {
        data: bySource.map((s: any) => ({ type: s.source, value: s.count })),
        angleField: 'value',
        colorField: 'type',
        innerRadius: 0.6,
        height: 300,
        label: { text: 'type', position: 'outside' as const },
        legend: { position: 'bottom' as const },
    };

    const indicatorColumns: ColumnsType<any> = [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            ellipsis: true,
        },
        {
            title: 'Confidence',
            dataIndex: 'confidence',
            key: 'confidence',
            width: 140,
            render: (v: number) => (
                <Progress
                    percent={v ?? 0}
                    size="small"
                    strokeColor={v >= 75 ? '#52c41a' : v >= 50 ? '#faad14' : '#ff4d4f'}
                />
            ),
        },
        {
            title: 'Source',
            dataIndex: 'source',
            key: 'source',
            width: 160,
            render: (v: string) => (
                <Tag color={getSourceColor(v)}>{v}</Tag>
            ),
        },
        {
            title: 'Labels',
            dataIndex: 'labels',
            key: 'labels',
            width: 200,
            render: (labels: string[]) => (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                    {(labels || []).slice(0, 3).map((lbl: string) => (
                        <Tag key={lbl} color="default" style={{ fontSize: 10 }}>
                            {lbl.length > 16 ? lbl.substring(0, 16) + '...' : lbl}
                        </Tag>
                    ))}
                    {(labels || []).length > 3 && (
                        <Tag color="default" style={{ fontSize: 10 }}>+{labels.length - 3}</Tag>
                    )}
                </div>
            ),
        },
        {
            title: 'Created',
            dataIndex: 'created',
            key: 'created',
            width: 170,
            render: (v: string) => <span style={{ fontSize: 12, color: '#8c8c8c' }}>{formatDate(v)}</span>,
        },
    ];

    const apColumns: ColumnsType<any> = [
        {
            title: 'MITRE ID',
            dataIndex: 'mitre_id',
            key: 'mitre_id',
            width: 110,
            render: (v: string) => (
                <Tag color="blue" style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                    {v || '-'}
                </Tag>
            ),
        },
        {
            title: 'Technique',
            dataIndex: 'name',
            key: 'name',
            ellipsis: true,
        },
        {
            title: 'Source',
            dataIndex: 'source',
            key: 'source',
            width: 160,
            render: (v: string) => (
                <Tag color={getSourceColor(v)}>{v}</Tag>
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
                    <Title level={3}>MITRE ATT&CK / Threat Intel</Title>

                    {/* Stat Cards */}
                    <Spin spinning={attackPatternsLoading || indicatorsLoading}>
                        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Total Indicators"
                                        value={indTotal}
                                        prefix={<ThunderboltOutlined style={{ color: '#1890ff' }} />}
                                        valueStyle={{ color: '#1890ff' }}
                                    />
                                </Card>
                            </Col>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Total Techniques"
                                        value={apTotal}
                                        prefix={<AimOutlined style={{ color: '#722ed1' }} />}
                                        valueStyle={{ color: '#722ed1' }}
                                    />
                                </Card>
                            </Col>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Active Sources"
                                        value={bySource.length}
                                        prefix={<RadarChartOutlined style={{ color: '#52c41a' }} />}
                                        valueStyle={{ color: '#52c41a' }}
                                    />
                                </Card>
                            </Col>
                        </Row>
                    </Spin>

                    {/* Charts Row */}
                    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                        <Col xs={24} md={16}>
                            <Card title="Top MITRE ATT&CK Techniques">
                                {techniqueBarData.length === 0 ? (
                                    <Empty description="No attack pattern data" />
                                ) : (
                                    <Bar {...techniqueBarConfig} />
                                )}
                            </Card>
                        </Col>
                        <Col xs={24} md={8}>
                            <Card title="Patterns by Source">
                                {bySource.length === 0 ? (
                                    <Empty description="No source data" />
                                ) : (
                                    <Pie {...sourcePieConfig} />
                                )}
                            </Card>
                        </Col>
                    </Row>

                    {/* Recent Indicators Table */}
                    <Card title="Recent Indicators" style={{ marginBottom: 24 }}>
                        <Table
                            dataSource={recentIndicators}
                            columns={indicatorColumns}
                            rowKey="id"
                            pagination={{ pageSize: 10, size: 'small' }}
                            size="small"
                            scroll={{ x: 800 }}
                            locale={{ emptyText: <Empty description="No indicators found" /> }}
                        />
                    </Card>

                    {/* Recent Attack Patterns Table */}
                    <Card title="Recent Attack Patterns" style={{ marginBottom: 24 }}>
                        <Table
                            dataSource={recentAP}
                            columns={apColumns}
                            rowKey="id"
                            pagination={{ pageSize: 10, size: 'small' }}
                            size="small"
                            scroll={{ x: 600 }}
                            locale={{ emptyText: <Empty description="No attack patterns found" /> }}
                        />
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default CtiThreatIntelPage;
