import { Card, Row, Col, Statistic, Spin, Empty, Radio, Typography } from "antd";
import {
    ThunderboltOutlined,
    EyeOutlined,
    BugOutlined,
    AimOutlined,
    RadarChartOutlined,
    SafetyOutlined,
} from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useEffect, useState, useRef } from "react";
import useCtiStore from "../store/useCtiStore.ts";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { Line, Bar } from '@ant-design/plots';

const { Title } = Typography;

const CtiOverviewPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const [timelineDays, setTimelineDays] = useState<number>(7);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const {
        stats,
        timeline,
        attackPatterns,
        statsLoading,
        timelineLoading,
        attackPatternsLoading,
        fetchStats,
        fetchTimeline,
        fetchAttackPatterns,
    } = useCtiStore();

    useEffect(() => {
        fetchStats();
        fetchTimeline(timelineDays);
        fetchAttackPatterns();

        intervalRef.current = setInterval(() => {
            fetchStats();
            fetchTimeline(timelineDays);
            fetchAttackPatterns();
        }, 60000);

        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, []);

    const handleDaysChange = (days: number) => {
        setTimelineDays(days);
        fetchTimeline(days);
    };

    const totals = stats?.totals || { indicators: 0, sightings: 0, malware_families: 0, attack_patterns: 0 };
    const suricata = stats?.suricata || { indicators: 0, sightings: 0 };
    const wazuh = stats?.wazuh || { indicators: 0, sightings: 0 };
    const cape = stats?.cape || { malware_families: 0, indicators: 0 };

    const hasTimelineData = timeline.some(d => d.suricata > 0 || d.wazuh > 0 || d.malware > 0);
    const topTechniques = (attackPatterns?.top_techniques || []).slice(0, 10).map((t) => ({
        name: t.mitre_id ? t.mitre_id : t.name.substring(0, 20),
        fullName: t.name,
        count: t.count,
    }));

    // Transform timeline data for @ant-design/plots Line chart
    const timelineChartData = timeline.flatMap(entry => [
        { date: entry.date, value: entry.suricata, category: 'Suricata' },
        { date: entry.date, value: entry.wazuh, category: 'Wazuh' },
        { date: entry.date, value: entry.malware, category: 'CAPE Malware' },
    ]);

    const timelineConfig = {
        data: timelineChartData,
        xField: 'date',
        yField: 'value',
        colorField: 'category',
        height: 300,
        smooth: true,
        axis: {
            x: {
                labelFormatter: (v: string) => {
                    try {
                        return new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
                    } catch {
                        return v;
                    }
                },
            },
        },
        point: { shapeField: 'point', sizeField: 2 },
    };

    const techniqueBarConfig = {
        data: topTechniques,
        xField: 'count',
        yField: 'name',
        height: Math.max(200, topTechniques.length * 36),
        colorField: 'name',
        label: { position: 'right' as const },
        axis: {
            y: { labelFormatter: (v: string) => v },
        },
        tooltip: {
            items: [
                { channel: 'x', name: 'Count' },
                { channel: 'y', name: 'Technique' },
            ],
        },
    };

    return (
        <div>
            <div className={'page-parent'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys} onOpenChange={menuHighlighting.onOpenChange} />
                <div className={'page-content'}>
                    <Title level={3}>CTI Overview</Title>

                    {/* KPI Stat Cards */}
                    <Spin spinning={statsLoading}>
                        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                            <Col xs={24} sm={12} md={6}>
                                <Card>
                                    <Statistic
                                        title="Total Indicators"
                                        value={totals.indicators}
                                        prefix={<ThunderboltOutlined style={{ color: '#1890ff' }} />}
                                        valueStyle={{ color: '#1890ff' }}
                                    />
                                    <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>Across all sources</div>
                                </Card>
                            </Col>
                            <Col xs={24} sm={12} md={6}>
                                <Card>
                                    <Statistic
                                        title="Total Sightings"
                                        value={totals.sightings}
                                        prefix={<EyeOutlined style={{ color: '#faad14' }} />}
                                        valueStyle={{ color: '#faad14' }}
                                    />
                                    <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>Network & endpoint</div>
                                </Card>
                            </Col>
                            <Col xs={24} sm={12} md={6}>
                                <Card>
                                    <Statistic
                                        title="Malware Families"
                                        value={totals.malware_families}
                                        prefix={<BugOutlined style={{ color: '#ff4d4f' }} />}
                                        valueStyle={{ color: '#ff4d4f' }}
                                    />
                                    <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>CAPE sandbox results</div>
                                </Card>
                            </Col>
                            <Col xs={24} sm={12} md={6}>
                                <Card>
                                    <Statistic
                                        title="Attack Patterns"
                                        value={totals.attack_patterns}
                                        prefix={<AimOutlined style={{ color: '#722ed1' }} />}
                                        valueStyle={{ color: '#722ed1' }}
                                    />
                                    <div style={{ fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>MITRE ATT&CK</div>
                                </Card>
                            </Col>
                        </Row>
                    </Spin>

                    {/* Source Breakdown Cards */}
                    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                        <Col xs={24} sm={8}>
                            <Card>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <RadarChartOutlined style={{ fontSize: 28, color: '#1890ff' }} />
                                    <div>
                                        <div style={{ fontSize: 12, color: '#8c8c8c' }}>Suricata IDS</div>
                                        <div style={{ fontSize: 22, fontWeight: 700 }}>{(suricata.indicators ?? 0).toLocaleString()}</div>
                                        <div style={{ fontSize: 11, color: '#8c8c8c' }}>{(suricata.sightings ?? 0).toLocaleString()} sightings</div>
                                    </div>
                                </div>
                            </Card>
                        </Col>
                        <Col xs={24} sm={8}>
                            <Card>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <SafetyOutlined style={{ fontSize: 28, color: '#52c41a' }} />
                                    <div>
                                        <div style={{ fontSize: 12, color: '#8c8c8c' }}>Wazuh SIEM</div>
                                        <div style={{ fontSize: 22, fontWeight: 700 }}>{(wazuh.indicators ?? 0).toLocaleString()}</div>
                                        <div style={{ fontSize: 11, color: '#8c8c8c' }}>{(wazuh.sightings ?? 0).toLocaleString()} sightings</div>
                                    </div>
                                </div>
                            </Card>
                        </Col>
                        <Col xs={24} sm={8}>
                            <Card>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <BugOutlined style={{ fontSize: 28, color: '#ff4d4f' }} />
                                    <div>
                                        <div style={{ fontSize: 12, color: '#8c8c8c' }}>CAPE Sandbox</div>
                                        <div style={{ fontSize: 22, fontWeight: 700 }}>{(cape.malware_families ?? 0).toLocaleString()}</div>
                                        <div style={{ fontSize: 11, color: '#8c8c8c' }}>{(cape.indicators ?? 0).toLocaleString()} indicators</div>
                                    </div>
                                </div>
                            </Card>
                        </Col>
                    </Row>

                    {/* Threat Timeline */}
                    <Card
                        title="Threat Timeline"
                        extra={
                            <Radio.Group
                                value={timelineDays}
                                onChange={(e) => handleDaysChange(e.target.value)}
                                size="small"
                            >
                                <Radio.Button value={7}>7d</Radio.Button>
                                <Radio.Button value={14}>14d</Radio.Button>
                                <Radio.Button value={30}>30d</Radio.Button>
                            </Radio.Group>
                        }
                        style={{ marginBottom: 24 }}
                    >
                        <Spin spinning={timelineLoading}>
                            {!hasTimelineData ? (
                                <Empty description="No timeline data yet - waiting for connector data" />
                            ) : (
                                <Line {...timelineConfig} />
                            )}
                        </Spin>
                    </Card>

                    {/* Top MITRE ATT&CK Techniques */}
                    <Card title="Top MITRE ATT&CK Techniques" style={{ marginBottom: 24 }}>
                        <Spin spinning={attackPatternsLoading}>
                            {topTechniques.length === 0 ? (
                                <Empty description="No attack patterns yet - waiting for connector data" />
                            ) : (
                                <Bar {...techniqueBarConfig} />
                            )}
                        </Spin>
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default CtiOverviewPage;
