import { useEffect, useRef, useState } from 'react';
import { Card, Row, Col, Statistic, Tag, Table, Tabs, Button, Descriptions, Spin, Alert, Typography, Space, Empty, Progress, Tooltip } from 'antd';
import {
    ArrowLeftOutlined,
    ReloadOutlined,
    DownloadOutlined,
    GlobalOutlined,
    KeyOutlined,
    WarningOutlined,
    CheckCircleOutlined,
    SyncOutlined,
    ClockCircleOutlined,
    CloseCircleOutlined,
    SearchOutlined,
    LockOutlined,
    DatabaseOutlined,
    SafetyOutlined,
    MailOutlined,
    AlertOutlined,
    UserOutlined,
    RightOutlined,
} from '@ant-design/icons';
import Sidebar from '../components/Sidebar';
import { useLocation, useRoute } from 'wouter';
import { useMenuHighlighting } from '../utils/menuUtils';
import useDarkWebStore from '../store/useDarkWebStore';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const statusTagMap: Record<string, { color: string; icon: React.ReactNode }> = {
    queued: { color: 'orange', icon: <ClockCircleOutlined /> },
    processing: { color: 'blue', icon: <SyncOutlined spin /> },
    completed: { color: 'green', icon: <CheckCircleOutlined /> },
    failed: { color: 'red', icon: <CloseCircleOutlined /> },
};

const categoryIcons: Record<string, React.ReactNode> = {
    search_term: <SearchOutlined />,
    password: <LockOutlined />,
    database: <DatabaseOutlined />,
    credentials: <SafetyOutlined />,
    email: <MailOutlined />,
    leak: <AlertOutlined />,
};

// Severity weights per category — higher = more dangerous
const CATEGORY_WEIGHTS: Record<string, number> = {
    credentials: 30,
    password: 25,
    leak: 25,
    database: 20,
    email: 15,
    search_term: 10,
};

const computeSeverityScore = (record: any, searchTerm?: string): number => {
    const categories: string[] = record.categories_detected || [];
    const kwDetails: Record<string, any> = record.keyword_details || {};
    const catFindings: Record<string, any> = record.categorized_findings || {};

    // 1. Category severity (max 40 points) — sum weights of detected categories, capped
    let categoryScore = 0;
    categories.forEach((cat) => {
        categoryScore += CATEGORY_WEIGHTS[cat] || 5;
    });
    categoryScore = Math.min(categoryScore, 40);

    // 2. Keyword occurrence density (max 25 points)
    let totalOccurrences = 0;
    Object.values(kwDetails).forEach((d: any) => {
        totalOccurrences += d.count || 0;
    });
    // logarithmic scale: 1→5, 5→15, 20→22, 50+→25
    const occurrenceScore = totalOccurrences > 0
        ? Math.min(25, Math.round(5 * Math.log2(totalOccurrences + 1)))
        : 0;

    // 3. Distinct keyword breadth (max 15 points)
    const distinctKeywords = Object.keys(kwDetails).length;
    const breadthScore = Math.min(15, distinctKeywords * 5);

    // 4. Search term found bonus (max 10 points)
    const searchLower = searchTerm?.toLowerCase();
    const searchTermFound = searchLower && Object.keys(kwDetails).some(
        (kw) => kw.toLowerCase() === searchLower
    );
    const searchTermScore = searchTermFound ? 10 : 0;

    // 5. Context richness bonus (max 10 points) — more context snippets = more evidence
    let totalContexts = 0;
    Object.values(kwDetails).forEach((d: any) => {
        totalContexts += (d.contexts?.length || 0);
    });
    const contextScore = Math.min(10, Math.round(2 * Math.log2(totalContexts + 1)));

    return Math.min(100, categoryScore + occurrenceScore + breadthScore + searchTermScore + contextScore);
};

const getSeverityLabel = (score: number): { text: string; color: string } => {
    if (score >= 75) return { text: 'Critical', color: '#f5222d' };
    if (score >= 50) return { text: 'High', color: '#fa8c16' };
    if (score >= 25) return { text: 'Medium', color: '#faad14' };
    return { text: 'Low', color: '#52c41a' };
};

const KEYWORD_HIGHLIGHT_STYLE: React.CSSProperties = {
    background: '#fff3b0',
    fontWeight: 'bold',
    padding: '1px 3px',
    borderRadius: 2,
};

const MAX_CONTEXT_LENGTH = 300;

const truncateText = (text: string, maxLen: number) => {
    if (text.length <= maxLen) return text;
    return text.slice(0, maxLen) + '…';
};

const FindingContexts = ({ record, searchTerm }: { record: any; searchTerm?: string }) => {
    const [expandedKeywords, setExpandedKeywords] = useState<Record<string, boolean>>({});
    const kwDetails: Record<string, any> = record.keyword_details || {};
    const catFindings: Record<string, any> = record.categorized_findings || {};

    // Sort entries: search term first, then alphabetical
    const entries = Object.entries(kwDetails).sort(([a], [b]) => {
        const searchLower = searchTerm?.toLowerCase();
        const aIsSearch = a.toLowerCase() === searchLower;
        const bIsSearch = b.toLowerCase() === searchLower;
        if (aIsSearch && !bIsSearch) return -1;
        if (!aIsSearch && bIsSearch) return 1;
        return a.localeCompare(b);
    });

    // Derive category for a keyword
    const getCategoryForKeyword = (kw: string): string | null => {
        for (const [catKey, catData] of Object.entries(catFindings) as [string, any][]) {
            if (catData.found_subcategories?.includes(kw)) return catKey;
        }
        return null;
    };

    const toggleExpand = (kw: string) => {
        setExpandedKeywords((prev) => ({ ...prev, [kw]: !prev[kw] }));
    };

    const renderSnippet = (ctx: any, kw: string, idx: number) => {
        const before = ctx.before || '';
        const after = ctx.after || '';
        const keyword = ctx.keyword || kw;

        // Fallback to full_context if before/after are missing
        if (!before && !after && ctx.full_context) {
            const full = truncateText(ctx.full_context, MAX_CONTEXT_LENGTH);
            const kwIndex = full.toLowerCase().indexOf(kw.toLowerCase());
            if (kwIndex >= 0) {
                return (
                    <div
                        key={idx}
                        style={{
                            padding: '8px 12px',
                            borderBottom: '1px solid #f0f0f0',
                            fontFamily: 'monospace',
                            fontSize: 12,
                            lineHeight: 1.6,
                            color: '#595959',
                        }}
                    >
                        {full.slice(0, kwIndex)}
                        <span style={KEYWORD_HIGHLIGHT_STYLE}>{full.slice(kwIndex, kwIndex + kw.length)}</span>
                        {full.slice(kwIndex + kw.length)}
                    </div>
                );
            }
            return (
                <div
                    key={idx}
                    style={{
                        padding: '8px 12px',
                        borderBottom: '1px solid #f0f0f0',
                        fontFamily: 'monospace',
                        fontSize: 12,
                        lineHeight: 1.6,
                        color: '#595959',
                    }}
                >
                    {full}
                </div>
            );
        }

        const displayBefore = truncateText(before, 150);
        const displayAfter = truncateText(after, 150);

        return (
            <div
                key={idx}
                style={{
                    padding: '8px 12px',
                    borderBottom: '1px solid #f0f0f0',
                    fontFamily: 'monospace',
                    fontSize: 12,
                    lineHeight: 1.6,
                    color: '#595959',
                }}
            >
                ...{displayBefore}
                <span style={KEYWORD_HIGHLIGHT_STYLE}>{keyword}</span>
                {displayAfter}...
            </div>
        );
    };

    return (
        <div style={{ background: '#fafafa', padding: '16px 24px' }}>
            {entries.map(([kw, detail]) => {
                const contexts: any[] = detail.contexts || [];
                const count = detail.count || contexts.length;
                const isSearch = kw.toLowerCase() === searchTerm?.toLowerCase();
                const category = getCategoryForKeyword(kw);
                const isExpanded = expandedKeywords[kw];
                const displayContexts = isExpanded ? contexts : contexts.slice(0, 3);

                return (
                    <div key={kw} style={{ marginBottom: 16 }}>
                        <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontSize: 14 }}>
                                {isSearch ? <SearchOutlined /> : categoryIcons[category || ''] || <KeyOutlined />}
                            </span>
                            <Text strong style={{ fontSize: 13 }}>
                                "{kw}"
                                {isSearch && <Text type="secondary" style={{ fontWeight: 'normal', marginLeft: 4 }}>(search term)</Text>}
                            </Text>
                            <Text type="secondary" style={{ fontSize: 12 }}>
                                — found {count} time{count !== 1 ? 's' : ''}
                                {!isExpanded && contexts.length > 3 && ` (showing 3)`}
                            </Text>
                            {category && (
                                <Tag style={{ textTransform: 'capitalize', marginLeft: 4 }}>
                                    {category.replace('_', ' ')}
                                </Tag>
                            )}
                        </div>
                        {contexts.length > 0 ? (
                            <div style={{ border: '1px solid #e8e8e8', borderRadius: 4, overflow: 'hidden', background: '#fff' }}>
                                {displayContexts.map((ctx, idx) => renderSnippet(ctx, kw, idx))}
                            </div>
                        ) : (
                            <Text type="secondary" style={{ fontSize: 12, fontStyle: 'italic' }}>No context snippets available</Text>
                        )}
                        {contexts.length > 3 && (
                            <Button
                                type="link"
                                size="small"
                                style={{ paddingLeft: 0, marginTop: 4 }}
                                onClick={() => toggleExpand(kw)}
                            >
                                {isExpanded ? 'Show fewer' : `Show all ${contexts.length} occurrences`}
                            </Button>
                        )}
                    </div>
                );
            })}
        </div>
    );
};

const expandableConfig = (searchTerm?: string) => ({
    expandedRowRender: (record: any) => <FindingContexts record={record} searchTerm={searchTerm} />,
    rowExpandable: (record: any) => {
        const kd = record.keyword_details || {};
        return Object.values(kd).some((d: any) => d.contexts?.length > 0);
    },
    expandIcon: ({ expanded, onExpand, record }: { expanded: boolean; onExpand: (record: any, e: React.MouseEvent) => void; record: any }) => (
        <RightOutlined
            onClick={(e) => onExpand(record, e)}
            style={{
                cursor: 'pointer',
                transition: 'transform 0.2s',
                transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
                fontSize: 12,
            }}
        />
    ),
});

const DarkWebScanDetailPage = () => {
    const [location, navigate] = useLocation();
    const [, params] = useRoute('/dark-web/scan/:scanId');
    const scanId = params?.scanId;
    const menuHighlighting = useMenuHighlighting(location);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const { currentScan, scanDetailLoading, fetchScanResult, downloadPdf } = useDarkWebStore();

    useEffect(() => {
        if (scanId) {
            fetchScanResult(scanId);
        }
    }, [scanId]);

    // Auto-refresh every 3 seconds if queued/processing
    useEffect(() => {
        const status = currentScan?.status;
        if (status === 'queued' || status === 'processing') {
            intervalRef.current = setInterval(() => {
                if (scanId) fetchScanResult(scanId);
            }, 3000);
        }
        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, [currentScan?.status, scanId]);

    const formatDate = (ts?: string) => {
        if (!ts) return '-';
        return dayjs(ts.endsWith('Z') ? ts : ts + 'Z').format('DD/MM/YYYY HH:mm:ss');
    };

    const getDuration = () => {
        if (!currentScan?.started_at || !currentScan?.completed_at) return '-';
        const start = new Date(currentScan.started_at.endsWith('Z') ? currentScan.started_at : currentScan.started_at + 'Z');
        const end = new Date(currentScan.completed_at.endsWith('Z') ? currentScan.completed_at : currentScan.completed_at + 'Z');
        const diffSec = Math.round((end.getTime() - start.getTime()) / 1000);
        if (diffSec < 60) return `${diffSec}s`;
        return `${Math.floor(diffSec / 60)}m ${diffSec % 60}s`;
    };

    if (scanDetailLoading || !currentScan) {
        return (
            <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--page-background)' }}>
                <Sidebar
                    selectedKeys={menuHighlighting.selectedKeys}
                    openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange}
                />
                <div style={{ flex: 1, padding: '24px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    {scanDetailLoading ? <Spin size="large" tip="Loading scan details..." /> : (
                        <Empty description="Scan not found">
                            <Button type="primary" onClick={() => navigate('/dark-web/scans')}>Back to Scans</Button>
                        </Empty>
                    )}
                </div>
            </div>
        );
    }

    const results = currentScan.results || {};
    const findings = results.findings || [];
    const summary = results.summary || {};
    const categorizedFindings = results.categorized_findings || {};
    const statusInfo = statusTagMap[currentScan.status] || statusTagMap.queued;
    const hasFindings = findings.length > 0;

    // Build tab items for categorized findings
    const categoryTabs = Object.entries(categorizedFindings).map(([key, catData]) => ({
        key,
        label: (
            <span>
                {categoryIcons[key] || <GlobalOutlined />}
                <span style={{ marginLeft: 6 }}>{catData.main_category}</span>
                <Tag style={{ marginLeft: 6 }} color="blue">{catData.found_subcategories?.length || 0}</Tag>
            </span>
        ),
        children: (
            <div>
                <div style={{ marginBottom: 16 }}>
                    <Text type="secondary">Keywords found:</Text>
                    <div style={{ marginTop: 8 }}>
                        {catData.found_subcategories?.map((kw: string, idx: number) => (
                            <Tag key={idx} style={{ marginBottom: 4 }}>{kw}</Tag>
                        ))}
                    </div>
                </div>
                {/* Findings that match this category */}
                <Table
                    dataSource={findings.filter((f: any) =>
                        f.categories_detected?.includes(key)
                    )}
                    columns={findingColumns}
                    rowKey={(_, idx) => String(idx)}
                    size="small"
                    pagination={{ pageSize: 10 }}
                    locale={{ emptyText: 'No findings in this category' }}
                    expandable={expandableConfig(currentScan?.keyword)}
                />
            </div>
        ),
    }));

    const findingColumns: ColumnsType<any> = [
        {
            title: 'URL',
            dataIndex: 'url',
            key: 'url',
            ellipsis: true,
            render: (url: string, record: any) => (
                <a href={url || record.link || '#'} target="_blank" rel="noopener noreferrer" style={{ fontFamily: 'monospace', fontSize: 12 }}>
                    {url || record.link || 'N/A'}
                </a>
            ),
        },
        {
            title: 'Categories',
            dataIndex: 'categories_detected',
            key: 'categories',
            width: 200,
            render: (cats: string[]) => (
                <span>
                    {(cats || []).map((cat, i) => (
                        <Tag key={i} style={{ textTransform: 'capitalize' }}>{cat.replace('_', ' ')}</Tag>
                    ))}
                </span>
            ),
        },
        {
            title: 'Keywords',
            key: 'keywords',
            width: 280,
            render: (_: any, record: any) => {
                const catFindings = record.categorized_findings || {};
                const kwDetails = record.keyword_details || {};
                const keywords: string[] = [];
                Object.values(catFindings).forEach((cd: any) => {
                    if (cd.found_subcategories) keywords.push(...cd.found_subcategories);
                });
                return (
                    <span>
                        {keywords.map((kw, i) => {
                            const count = kwDetails[kw]?.count || 1;
                            return (
                                <Tag
                                    key={i}
                                    color="blue"
                                    style={{ marginBottom: 2, cursor: 'help' }}
                                    title={`Found ${count} time${count !== 1 ? 's' : ''} on this page`}
                                >
                                    {kw}
                                </Tag>
                            );
                        })}
                        {keywords.length === 0 && <Text type="secondary">-</Text>}
                    </span>
                );
            },
        },
        {
            title: 'Count',
            key: 'count',
            width: 80,
            align: 'center' as const,
            render: (_: any, record: any) => {
                const catFindings = record.categorized_findings || {};
                const kwDetails = record.keyword_details || {};
                const keywords: string[] = [];
                Object.values(catFindings).forEach((cd: any) => {
                    if (cd.found_subcategories) keywords.push(...cd.found_subcategories);
                });
                let totalCount = 0;
                keywords.forEach((kw) => {
                    totalCount += kwDetails[kw]?.count || 1;
                });
                if (totalCount === 0) {
                    totalCount = record.total_keywords_found || keywords.length || 0;
                }
                return (
                    <Tag
                        color="orange"
                        style={{
                            borderRadius: '50%',
                            width: 36,
                            height: 36,
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 'bold',
                            fontSize: 14,
                        }}
                    >
                        {totalCount}
                    </Tag>
                );
            },
        },
        {
            title: 'Severity',
            key: 'severity',
            width: 140,
            sorter: (a: any, b: any) =>
                computeSeverityScore(a, currentScan?.keyword) - computeSeverityScore(b, currentScan?.keyword),
            defaultSortOrder: 'descend' as const,
            render: (_: any, record: any) => {
                const score = computeSeverityScore(record, currentScan?.keyword);
                const { text, color } = getSeverityLabel(score);
                return (
                    <Tooltip title={`Score: ${score}/100`}>
                        <div style={{ minWidth: 100 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                                <Text strong style={{ fontSize: 11, color }}>{text}</Text>
                                <Text type="secondary" style={{ fontSize: 11 }}>{score}</Text>
                            </div>
                            <Progress
                                percent={score}
                                size="small"
                                showInfo={false}
                                strokeColor={color}
                                trailColor="#f0f0f0"
                            />
                        </div>
                    </Tooltip>
                );
            },
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
                <div style={{ marginBottom: 24 }}>
                    <Space style={{ marginBottom: 16 }}>
                        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/dark-web/scans')}>
                            Back to Scans
                        </Button>
                        <Button icon={<ReloadOutlined />} onClick={() => scanId && fetchScanResult(scanId)}>
                            Refresh
                        </Button>
                        {currentScan.status === 'completed' && currentScan.files?.pdf_exists && (
                            <Button
                                type="primary"
                                icon={<DownloadOutlined />}
                                onClick={() => downloadPdf(currentScan.scan_id, currentScan.keyword)}
                            >
                                Download Report
                            </Button>
                        )}
                    </Space>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <Title level={3} style={{ margin: 0 }}>{currentScan.keyword}</Title>
                        <Tag icon={statusInfo.icon} color={statusInfo.color} style={{ textTransform: 'capitalize' }}>
                            {currentScan.status}
                        </Tag>
                        {currentScan.status === 'completed' && (
                            hasFindings
                                ? <Tag color="red" icon={<WarningOutlined />}>Breached / Leaked</Tag>
                                : <Tag color="green" icon={<CheckCircleOutlined />}>Secure</Tag>
                        )}
                    </div>
                    <Text type="secondary" style={{ fontFamily: 'monospace', fontSize: 12 }}>
                        Scan ID: {currentScan.scan_id}
                    </Text>
                    {currentScan.is_admin_view && currentScan.owner && (
                        <div style={{ marginTop: 8 }}>
                            <Tag icon={<UserOutlined />} color="geekblue">
                                Owned by: {currentScan.owner.username} ({currentScan.owner.email})
                            </Tag>
                        </div>
                    )}
                </div>

                {/* Info Row */}
                <Card style={{ marginBottom: 24 }}>
                    <Descriptions bordered size="small" column={{ xs: 1, sm: 2, md: 4 }}>
                        <Descriptions.Item label="Created">{formatDate(currentScan.created_at)}</Descriptions.Item>
                        <Descriptions.Item label="Started">{formatDate(currentScan.started_at)}</Descriptions.Item>
                        <Descriptions.Item label="Completed">{formatDate(currentScan.completed_at)}</Descriptions.Item>
                        <Descriptions.Item label="Duration">{getDuration()}</Descriptions.Item>
                    </Descriptions>
                </Card>

                {/* Queued / Processing states */}
                {currentScan.status === 'processing' && (
                    <Alert
                        type="info"
                        showIcon
                        icon={<SyncOutlined spin />}
                        message="Scan in Progress"
                        description="This scan is currently being processed. Results will appear here when complete. Auto-refreshing every 3 seconds..."
                        style={{ marginBottom: 24 }}
                    />
                )}

                {currentScan.status === 'queued' && (
                    <Alert
                        type="warning"
                        showIcon
                        icon={<ClockCircleOutlined />}
                        message="Scan Queued"
                        description={
                            <span>
                                This scan is waiting in the queue.
                                {currentScan.position !== undefined && (
                                    <span> Position: {currentScan.position} | Estimated wait: {currentScan.estimated_wait_minutes || 0} minutes</span>
                                )}
                            </span>
                        }
                        style={{ marginBottom: 24 }}
                    />
                )}

                {currentScan.status === 'failed' && currentScan.error && (
                    <Alert
                        type="error"
                        showIcon
                        message="Scan Failed"
                        description={currentScan.error}
                        style={{ marginBottom: 24 }}
                    />
                )}

                {/* Stats Cards - Only for completed scans */}
                {currentScan.status === 'completed' && (
                    <>
                        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Sites Found"
                                        value={summary.total_sites || 0}
                                        prefix={<GlobalOutlined />}
                                        valueStyle={{ color: '#1890ff' }}
                                    />
                                </Card>
                            </Col>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Keywords Matched"
                                        value={summary.total_keywords || 0}
                                        prefix={<KeyOutlined />}
                                        valueStyle={{ color: '#722ed1' }}
                                    />
                                </Card>
                            </Col>
                            <Col xs={24} sm={8}>
                                <Card>
                                    <Statistic
                                        title="Critical Threats"
                                        value={hasFindings ? '100%' : '0%'}
                                        prefix={<WarningOutlined />}
                                        valueStyle={{ color: hasFindings ? '#f5222d' : '#52c41a' }}
                                    />
                                </Card>
                            </Col>
                        </Row>

                        {/* Categorized Findings Tabs */}
                        {categoryTabs.length > 0 && (
                            <Card title="Categorized Findings" bordered={false} style={{ marginBottom: 24 }}>
                                <Tabs items={categoryTabs} />
                            </Card>
                        )}

                        {/* All Findings Table */}
                        {findings.length > 0 && (
                            <Card title={`All Findings (${findings.length})`} bordered={false}>
                                <Table
                                    dataSource={findings}
                                    columns={findingColumns}
                                    rowKey={(_, idx) => String(idx)}
                                    pagination={{ pageSize: 15 }}
                                    expandable={expandableConfig(currentScan.keyword)}
                                />
                            </Card>
                        )}

                        {findings.length === 0 && (
                            <Card bordered={false}>
                                <Empty
                                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                                    description="No findings detected. The searched keyword was not found on the dark web."
                                />
                            </Card>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

export default DarkWebScanDetailPage;
