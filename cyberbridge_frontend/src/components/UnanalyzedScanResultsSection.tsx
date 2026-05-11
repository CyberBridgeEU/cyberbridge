import React, { useEffect, useState } from 'react';
import { Table, Tag, Button, Space, Typography, Empty, notification } from 'antd';
import { ExperimentOutlined, ReloadOutlined, RightOutlined, DownOutlined } from '@ant-design/icons';
import type { TableColumnsType } from 'antd';
import useRegulatoryMonitorStore from '../store/useRegulatoryMonitorStore';
import InfoTitle from './InfoTitle';

const { Text } = Typography;

const UnanalyzedScanResultsSection: React.FC = () => {
    const {
        unanalyzedGroups,
        fetchUnanalyzedResults,
        fetchNotifications,
        triggerLLMAnalysis,
        analyzing,
    } = useRegulatoryMonitorStore();

    const [api, contextHolder] = notification.useNotification();
    const [analyzingKey, setAnalyzingKey] = useState<string | null>(null);

    useEffect(() => {
        fetchUnanalyzedResults();
    }, []);

    const handleAnalyze = async (scanRunId: string, frameworkType: string) => {
        const key = `${scanRunId}:${frameworkType}`;
        setAnalyzingKey(key);
        api.info({
            message: 'LLM Analysis Started',
            description: `Analyzing ${frameworkType.toUpperCase().replace(/_/g, ' ')} findings. This may take a minute…`,
            duration: 5,
        });
        const result = await triggerLLMAnalysis(scanRunId, frameworkType);
        setAnalyzingKey(null);
        if (result) {
            if (result.status === 'completed') {
                api.success({
                    message: 'LLM Analysis Complete',
                    description: `Found ${result.changes_count ?? 0} regulatory changes for ${frameworkType.toUpperCase().replace(/_/g, ' ')}`,
                });
            } else if (result.status === 'llm_error') {
                api.warning({
                    message: 'LLM Analysis Failed',
                    description: 'Automatic analysis failed. Check the LLM service and retry.',
                    duration: 10,
                });
            }
            fetchUnanalyzedResults();
            fetchNotifications();
        } else {
            api.error({ message: 'Analysis Failed', description: 'Failed to run LLM analysis' });
        }
    };

    const columns: TableColumnsType<any> = [
        {
            title: 'Scan Date',
            dataIndex: 'scan_started_at',
            key: 'scan_started_at',
            width: 180,
            render: (d: string | null) => d ? new Date(d).toLocaleString() : '—',
        },
        {
            title: 'Framework',
            dataIndex: 'framework_type',
            key: 'framework_type',
            width: 220,
            render: (ft: string) => <Tag color="geekblue">{ft.toUpperCase().replace(/_/g, ' ')}</Tag>,
        },
        {
            title: 'Findings',
            dataIndex: 'finding_count',
            key: 'finding_count',
            width: 100,
            render: (n: number) => <Text strong>{n}</Text>,
        },
        {
            title: 'Status',
            key: 'status',
            width: 140,
            render: () => <Tag color="orange">Not analyzed</Tag>,
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_: any, record: any) => {
                const key = `${record.scan_run_id}:${record.framework_type}`;
                const isThisAnalyzing = analyzingKey === key;
                return (
                    <Button
                        type="primary"
                        size="small"
                        icon={<ExperimentOutlined />}
                        onClick={() => handleAnalyze(record.scan_run_id, record.framework_type)}
                        loading={isThisAnalyzing}
                        disabled={analyzing && !isThisAnalyzing}
                        style={{ background: '#1a365d', borderColor: '#1a365d' }}
                    >
                        Run LLM Analysis
                    </Button>
                );
            },
        },
    ];

    return (
        <>
            {contextHolder}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <InfoTitle
                    title="Unanalyzed Scan Findings"
                    infoContent="Raw findings collected by the scheduled regulatory web scan that have not yet been processed by the LLM. Click 'Run LLM Analysis' on a row to turn its findings into reviewable change proposals."
                    className="section-title"
                />
                <Button
                    icon={<ReloadOutlined />}
                    onClick={fetchUnanalyzedResults}
                    size="small"
                >
                    Refresh
                </Button>
            </div>
            <p className="section-subtitle">
                {unanalyzedGroups.length > 0
                    ? `${unanalyzedGroups.length} framework/scan pair${unanalyzedGroups.length === 1 ? '' : 's'} awaiting LLM analysis`
                    : 'All scan findings have been analyzed'}
            </p>

            {unanalyzedGroups.length === 0 ? (
                <Empty description="No unanalyzed scan findings" />
            ) : (
                <Table
                    columns={columns}
                    dataSource={unanalyzedGroups}
                    rowKey={(record: any) => `${record.scan_run_id}:${record.framework_type}`}
                    size="small"
                    pagination={false}
                    expandable={{
                        expandIcon: ({ expanded, onExpand, record }: any) => (
                            expanded
                                ? <DownOutlined onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#1a365d' }} />
                                : <RightOutlined onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#1a365d' }} />
                        ),
                        expandedRowRender: (record: any) => (
                            <div style={{ padding: '8px 0' }}>
                                {record.findings.map((f: any) => (
                                    <div key={f.id} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: '1px solid #f0f0f0' }}>
                                        <Space direction="vertical" size={2} style={{ width: '100%' }}>
                                            <Space>
                                                <Text strong>{f.source_name}</Text>
                                                {f.fetched_at && (
                                                    <Text type="secondary" style={{ fontSize: 12 }}>
                                                        fetched {new Date(f.fetched_at).toLocaleString()}
                                                    </Text>
                                                )}
                                            </Space>
                                            {f.source_url && (
                                                <a href={f.source_url} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>
                                                    {f.source_url}
                                                </a>
                                            )}
                                            {f.content_preview && (
                                                <Text type="secondary" style={{ fontSize: 12, whiteSpace: 'pre-wrap' }}>
                                                    {f.content_preview}
                                                </Text>
                                            )}
                                        </Space>
                                    </div>
                                ))}
                            </div>
                        ),
                    }}
                />
            )}
        </>
    );
};

export default UnanalyzedScanResultsSection;
