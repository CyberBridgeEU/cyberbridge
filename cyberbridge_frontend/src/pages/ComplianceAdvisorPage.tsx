import React, { useState, useEffect } from 'react';
import { Input, Button, Card, Tag, Spin, Alert, notification, Empty, Table, Popconfirm } from 'antd';
import { GlobalOutlined, BulbOutlined, CheckCircleOutlined, LoadingOutlined, RocketOutlined, InfoCircleOutlined, EyeOutlined, DeleteOutlined, HistoryOutlined } from '@ant-design/icons';
import Sidebar from '../components/Sidebar.tsx';
import InfoTitle from '../components/InfoTitle.tsx';
import { ComplianceAdvisorInfo } from '../constants/infoContent.tsx';
import useComplianceAdvisorStore from '../store/useComplianceAdvisorStore.ts';
import type { ComplianceAdvisorHistoryItem } from '../store/useComplianceAdvisorStore.ts';
import useFrameworksStore from '../store/useFrameworksStore.ts';
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const ComplianceAdvisorPage: React.FC = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Store state
    const {
        result, loading, error, seedingTemplateId,
        analyzeWebsite, seedFramework,
        history, historyLoading, fetchHistory, loadHistoryResult, deleteHistory
    } = useComplianceAdvisorStore();
    const { frameworks, fetchFrameworks } = useFrameworksStore();

    // Local state
    const [url, setUrl] = useState('');
    const [seededIds, setSeededIds] = useState<Set<string>>(new Set());
    const [api, contextHolder] = notification.useNotification();

    useEffect(() => {
        fetchFrameworks();
        fetchHistory();
    }, []);

    // Check which frameworks already exist in the org
    const isFrameworkSeeded = (templateId: string): boolean => {
        if (seededIds.has(templateId)) return true;

        // Match against existing framework names (case-insensitive, normalized)
        const templateLower = templateId.toLowerCase().replace(/_/g, ' ');
        return frameworks.some(f => {
            const fwName = f.name.toLowerCase().replace(/_/g, ' ');
            return fwName === templateLower ||
                fwName.includes(templateLower) ||
                templateLower.includes(fwName);
        });
    };

    const handleAnalyze = async () => {
        if (!url.trim()) {
            api.warning({ message: 'Please enter a website URL' });
            return;
        }
        const success = await analyzeWebsite(url.trim());
        if (success) {
            api.success({ message: 'Analysis Complete', description: 'Website analyzed successfully.' });
        } else {
            api.error({ message: 'Analysis Failed', description: error || 'Could not analyze the website.' });
        }
    };

    const handleSeed = async (templateId: string, frameworkName: string) => {
        const success = await seedFramework(templateId);
        if (success) {
            setSeededIds(prev => new Set(prev).add(templateId));
            await fetchFrameworks();
            api.success({ message: 'Framework Seeded', description: `${frameworkName} has been added to your organization.` });
        } else {
            api.error({ message: 'Seeding Failed', description: `Could not seed ${frameworkName}. It may already exist.` });
        }
    };

    const handleViewHistory = (id: string) => {
        loadHistoryResult(id);
    };

    const handleDeleteHistory = async (id: string) => {
        const success = await deleteHistory(id);
        if (success) {
            api.success({ message: 'Deleted', description: 'History record deleted.' });
        } else {
            api.error({ message: 'Delete Failed', description: 'Could not delete history record.' });
        }
    };

    const getRelevanceColor = (relevance: string) => {
        switch (relevance) {
            case 'high': return 'green';
            case 'medium': return 'gold';
            case 'low': return 'blue';
            default: return 'default';
        }
    };

    const historyColumns = [
        {
            title: 'Date',
            dataIndex: 'timestamp',
            key: 'timestamp',
            width: 160,
            render: (ts: string | null) => ts ? new Date(ts).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' }) : '—',
        },
        {
            title: 'URL',
            dataIndex: 'scan_target',
            key: 'scan_target',
            ellipsis: true,
        },
        {
            title: 'Summary',
            dataIndex: 'summary',
            key: 'summary',
            ellipsis: true,
            render: (text: string) => text ? (text.length > 80 ? text.slice(0, 80) + '...' : text) : '—',
        },
        {
            title: 'Duration',
            dataIndex: 'scan_duration',
            key: 'scan_duration',
            width: 90,
            render: (d: number | null) => d != null ? `${d}s` : '—',
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 120,
            render: (_: unknown, record: ComplianceAdvisorHistoryItem) => (
                <div style={{ display: 'flex', gap: '4px' }}>
                    <Button
                        size="small"
                        type="link"
                        icon={<EyeOutlined />}
                        onClick={() => handleViewHistory(record.id)}
                    >
                        View
                    </Button>
                    <Popconfirm
                        title="Delete this record?"
                        onConfirm={() => handleDeleteHistory(record.id)}
                        okText="Yes"
                        cancelText="No"
                    >
                        <Button size="small" type="link" danger icon={<DeleteOutlined />} />
                    </Popconfirm>
                </div>
            ),
        },
    ];

    return (
        <div>
            {contextHolder}
            <div className={'page-parent'}>
                <Sidebar
                    selectedKeys={menuHighlighting.selectedKeys}
                    openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange}
                />
                <div className="page-content">

                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <BulbOutlined style={{ fontSize: 22, color: '#1a365d' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Compliance Advisor</h1>
                        </div>
                    </div>

                    {/* Disclaimer */}
                    <div className="page-section">
                        <Alert
                            message="AI-Generated Recommendations"
                            description="The compliance framework recommendations provided by this tool are generated by an AI model based on publicly available website content. They are intended as a starting point and should not be considered legal or regulatory advice. Always consult with a qualified compliance professional before making decisions based on these recommendations."
                            type="info"
                            showIcon
                            icon={<InfoCircleOutlined />}
                        />
                    </div>

                    {/* URL Input Section */}
                    <div className="page-section">
                        <InfoTitle
                            title="Website Analysis"
                            infoContent={ComplianceAdvisorInfo}
                            className="section-title"
                        />
                        <p className="section-subtitle">
                            Enter your company website URL to receive AI-powered compliance framework recommendations
                        </p>

                        <div style={{ display: 'flex', gap: '12px', maxWidth: '700px', marginTop: '16px' }}>
                            <Input
                                size="large"
                                placeholder="https://example.com"
                                prefix={<GlobalOutlined style={{ color: '#8c8c8c' }} />}
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                onPressEnter={handleAnalyze}
                                disabled={loading}
                                style={{ flex: 1 }}
                            />
                            <Button
                                type="primary"
                                size="large"
                                onClick={handleAnalyze}
                                loading={loading}
                                icon={<RocketOutlined />}
                            >
                                Analyze
                            </Button>
                        </div>

                        {loading && (
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '12px',
                                marginTop: '20px',
                                padding: '16px',
                                background: '#f0f5ff',
                                borderRadius: '8px',
                                border: '1px solid #d6e4ff'
                            }}>
                                <Spin indicator={<LoadingOutlined spin />} />
                                <span style={{ color: '#1a365d' }}>
                                    Analyzing website and generating recommendations... This may take 30-60 seconds.
                                </span>
                            </div>
                        )}
                    </div>

                    {/* Analysis History */}
                    {history.length > 0 && (
                        <div className="page-section">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                                <HistoryOutlined style={{ color: '#1a365d' }} />
                                <h3 className="section-title" style={{ margin: 0 }}>Analysis History</h3>
                            </div>
                            <Table
                                dataSource={history}
                                columns={historyColumns}
                                rowKey="id"
                                size="small"
                                loading={historyLoading}
                                pagination={{ pageSize: 5, size: 'small', showSizeChanger: false }}
                            />
                        </div>
                    )}

                    {/* Error State */}
                    {error && !loading && (
                        <div className="page-section">
                            <Alert
                                message="Analysis Error"
                                description={error}
                                type="error"
                                showIcon
                                closable
                            />
                        </div>
                    )}

                    {/* Results Section */}
                    {result && !loading && (
                        <>
                            {/* Company Summary */}
                            <div className="page-section">
                                <Card
                                    size="small"
                                    style={{ background: '#fafafa', borderColor: '#e8e8e8' }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                                        <GlobalOutlined style={{ fontSize: '20px', color: '#0f386a', marginTop: '2px' }} />
                                        <div>
                                            <div style={{ fontWeight: 600, fontSize: '15px', marginBottom: '4px', color: '#1a365d' }}>
                                                Company Summary
                                            </div>
                                            <div style={{ color: '#595959', lineHeight: 1.6 }}>
                                                {result.company_summary}
                                            </div>
                                            <Tag style={{ marginTop: '8px' }} color="blue">
                                                {result.scraped_pages} page{result.scraped_pages !== 1 ? 's' : ''} analyzed
                                            </Tag>
                                        </div>
                                    </div>
                                </Card>
                            </div>

                            {/* Framework Recommendations */}
                            <div className="page-section">
                                <h3 className="section-title" style={{ marginBottom: '16px' }}>
                                    Recommended Frameworks ({result.recommendations.length})
                                </h3>

                                {result.recommendations.length === 0 ? (
                                    <Empty
                                        description="No specific framework recommendations could be determined from the website content."
                                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                                    />
                                ) : (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                        {result.recommendations
                                            .sort((a, b) => a.priority - b.priority)
                                            .map((rec) => {
                                                const alreadySeeded = isFrameworkSeeded(rec.template_id);
                                                const isSeeding = seedingTemplateId === rec.template_id;

                                                return (
                                                    <Card
                                                        key={rec.template_id}
                                                        size="small"
                                                        style={{
                                                            borderLeft: `4px solid ${rec.relevance === 'high' ? '#52c41a' : rec.relevance === 'medium' ? '#faad14' : '#1890ff'}`,
                                                        }}
                                                    >
                                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                                            <div style={{ flex: 1 }}>
                                                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
                                                                    <span style={{ fontWeight: 600, fontSize: '15px', color: '#1a365d' }}>
                                                                        {rec.framework_name}
                                                                    </span>
                                                                    <Tag color={getRelevanceColor(rec.relevance)}>
                                                                        {rec.relevance.toUpperCase()}
                                                                    </Tag>
                                                                    <Tag color="default">Priority #{rec.priority}</Tag>
                                                                </div>
                                                                <div style={{ color: '#595959', lineHeight: 1.6 }}>
                                                                    {rec.reasoning}
                                                                </div>
                                                            </div>
                                                            <div style={{ marginLeft: '16px', flexShrink: 0 }}>
                                                                {alreadySeeded ? (
                                                                    <Button
                                                                        disabled
                                                                        icon={<CheckCircleOutlined />}
                                                                        style={{ color: '#52c41a', borderColor: '#b7eb8f' }}
                                                                    >
                                                                        Already Seeded
                                                                    </Button>
                                                                ) : (
                                                                    <Button
                                                                        type={rec.relevance === 'high' ? 'primary' : 'default'}
                                                                        onClick={() => handleSeed(rec.template_id, rec.framework_name)}
                                                                        loading={isSeeding}
                                                                        icon={<RocketOutlined />}
                                                                    >
                                                                        Seed Framework
                                                                    </Button>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </Card>
                                                );
                                            })}
                                    </div>
                                )}
                            </div>
                        </>
                    )}

                    {/* Empty State */}
                    {!result && !loading && !error && (
                        <div className="page-section">
                            <div style={{
                                padding: '60px 20px',
                                textAlign: 'center',
                                background: '#fafafa',
                                borderRadius: '8px',
                                border: '1px dashed #d9d9d9'
                            }}>
                                <BulbOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
                                <p style={{ color: '#8c8c8c', fontSize: '16px', marginBottom: '8px', fontWeight: 500 }}>
                                    Get AI-Powered Framework Recommendations
                                </p>
                                <p style={{ color: '#bfbfbf', fontSize: '14px', maxWidth: '500px', margin: '0 auto' }}>
                                    Enter your company's website URL above and click "Analyze" to receive
                                    personalized compliance framework recommendations based on your industry,
                                    geography, and products.
                                </p>
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
};

export default ComplianceAdvisorPage;
