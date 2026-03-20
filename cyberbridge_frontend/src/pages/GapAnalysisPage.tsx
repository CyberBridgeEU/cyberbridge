import { useState, useEffect, useRef } from 'react';
import {
    BarChartOutlined, AimOutlined, CheckCircleOutlined, FormOutlined,
    SafetyCertificateOutlined, DownloadOutlined, ExclamationCircleOutlined,
    FileSearchOutlined, CloseCircleOutlined, LinkOutlined
} from '@ant-design/icons';
import { Progress, Spin, Select, Collapse, Table } from 'antd';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { StatCard, DashboardSection } from "../components/dashboard";
import useAuthStore from "../store/useAuthStore.ts";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import useCRAFilteredFrameworks from "../hooks/useCRAFilteredFrameworks.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import { exportToPdf } from "../utils/pdfUtils.ts";

interface GapAnalysisData {
    summary: {
        total_frameworks: number;
        total_objectives: number;
        total_assessments: number;
        total_policies: number;
        overall_compliance_score: number;
    };
    objectives_analysis: {
        total: number;
        compliant: number;
        partially_compliant: number;
        not_compliant: number;
        in_review: number;
        not_assessed: number;
        not_applicable: number;
        with_evidence: number;
        without_evidence: number;
        compliance_rate: number;
    };
    assessment_analysis: {
        total: number;
        completed: number;
        in_progress: number;
        average_progress: number;
        unanswered_questions: number;
        total_questions: number;
        completion_rate: number;
    };
    policy_analysis: {
        total: number;
        by_status: { status: string; count: number }[];
        approved_count: number;
        approved_percentage: number;
        objectives_with_policies: number;
        objectives_without_policies: number;
        policy_coverage_percentage: number;
    };
    gaps: {
        objectives_without_evidence: { id: string; title: string; chapter_title: string; compliance_status: string }[];
        objectives_not_compliant: { id: string; title: string; chapter_title: string; compliance_status: string }[];
        objectives_without_policies: { id: string; title: string; chapter_title: string }[];
    };
    chapter_breakdown: {
        chapter_title: string;
        total_objectives: number;
        compliant: number;
        not_compliant: number;
        not_assessed: number;
        compliance_rate: number;
    }[];
}

const statusRows: { key: string; label: string; color: string }[] = [
    { key: 'compliant', label: 'Compliant', color: '#52c41a' },
    { key: 'partially_compliant', label: 'Partially Compliant', color: '#faad14' },
    { key: 'not_compliant', label: 'Not Compliant', color: '#ff4d4f' },
    { key: 'in_review', label: 'In Review', color: '#1890ff' },
    { key: 'not_assessed', label: 'Not Assessed', color: '#d9d9d9' },
    { key: 'not_applicable', label: 'Not Applicable', color: '#bfbfbf' },
];

const policyStatusColors: Record<string, string> = {
    'Approved': '#52c41a',
    'Review': '#1890ff',
    'Ready for Approval': '#faad14',
    'Draft': '#bfbfbf',
};

const getScoreColor = (score: number) => {
    if (score >= 70) return '#52c41a';
    if (score >= 40) return '#faad14';
    return '#ff4d4f';
};

const GapAnalysisPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const getAuthHeader = useAuthStore((s) => s.getAuthHeader);
    const { fetchFrameworks } = useFrameworksStore();
    const { filteredFrameworks } = useCRAFilteredFrameworks();

    const [data, setData] = useState<GapAnalysisData | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedFrameworkId, setSelectedFrameworkId] = useState<string | undefined>(undefined);
    const [exporting, setExporting] = useState(false);
    const contentRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchFrameworks();
    }, [fetchFrameworks]);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const headers = getAuthHeader();
                if (!headers) return;
                const params = selectedFrameworkId ? `?framework_id=${selectedFrameworkId}` : '';
                const res = await fetch(`${cyberbridge_back_end_rest_api}/gap-analysis${params}`, { headers });
                if (res.ok) {
                    setData(await res.json());
                }
            } catch (err) {
                console.error('Failed to fetch gap analysis:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [getAuthHeader, selectedFrameworkId]);

    const handleExportPdf = async () => {
        setExporting(true);
        try {
            await exportToPdf(contentRef.current, 'gap_analysis_report');
        } finally {
            setExporting(false);
        }
    };

    const chapterColumns = [
        {
            title: 'Chapter',
            dataIndex: 'chapter_title',
            key: 'chapter_title',
            ellipsis: true,
        },
        {
            title: 'Total',
            dataIndex: 'total_objectives',
            key: 'total_objectives',
            width: 80,
            align: 'center' as const,
        },
        {
            title: 'Compliant',
            dataIndex: 'compliant',
            key: 'compliant',
            width: 100,
            align: 'center' as const,
            render: (val: number) => <span style={{ color: '#52c41a', fontWeight: 600 }}>{val}</span>,
        },
        {
            title: 'Not Compliant',
            dataIndex: 'not_compliant',
            key: 'not_compliant',
            width: 120,
            align: 'center' as const,
            render: (val: number) => <span style={{ color: val > 0 ? '#ff4d4f' : '#999', fontWeight: 600 }}>{val}</span>,
        },
        {
            title: 'Not Assessed',
            dataIndex: 'not_assessed',
            key: 'not_assessed',
            width: 120,
            align: 'center' as const,
            render: (val: number) => <span style={{ color: val > 0 ? '#999' : '#999', fontWeight: 600 }}>{val}</span>,
        },
        {
            title: 'Rate',
            dataIndex: 'compliance_rate',
            key: 'compliance_rate',
            width: 100,
            align: 'center' as const,
            render: (val: number) => (
                <span style={{ color: getScoreColor(val), fontWeight: 700 }}>{val}%</span>
            ),
        },
    ];

    return (
        <div>
            <div className={'page-parent'}>
                <Sidebar
                    selectedKeys={menuHighlighting.selectedKeys}
                    openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange}
                />
                <div className={'page-content'}>
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <BarChartOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Gap Analysis</h1>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <Select
                                placeholder="All Frameworks"
                                allowClear
                                style={{ minWidth: 220 }}
                                value={selectedFrameworkId}
                                onChange={(val) => setSelectedFrameworkId(val)}
                                options={filteredFrameworks.map((f) => ({
                                    label: f.name,
                                    value: f.id,
                                }))}
                            />
                            <button
                                onClick={handleExportPdf}
                                disabled={exporting || loading}
                                style={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: '6px',
                                    padding: '6px 16px',
                                    backgroundColor: '#1a365d',
                                    color: '#fff',
                                    border: 'none',
                                    borderRadius: '6px',
                                    fontSize: '13px',
                                    fontWeight: 500,
                                    cursor: exporting || loading ? 'not-allowed' : 'pointer',
                                    opacity: exporting || loading ? 0.6 : 1,
                                    transition: 'all 0.2s',
                                }}
                            >
                                <DownloadOutlined />
                                {exporting ? 'Exporting...' : 'Export PDF'}
                            </button>
                        </div>
                    </div>

                    {loading ? (
                        <div style={{ textAlign: 'center', padding: '60px 0' }}>
                            <Spin size="large" />
                        </div>
                    ) : data ? (
                        <div ref={contentRef}>
                            {/* Section 1: Compliance Overview */}
                            <DashboardSection title="Compliance Overview" style={{ marginTop: '24px' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
                                    <StatCard
                                        title="Total Objectives"
                                        value={data.summary.total_objectives}
                                        icon={<AimOutlined />}
                                        iconColor="#0f386a"
                                        iconBgColor="#EBF4FC"
                                    />
                                    <StatCard
                                        title="Compliant Objectives"
                                        value={data.objectives_analysis.compliant}
                                        icon={<CheckCircleOutlined />}
                                        iconColor="#52c41a"
                                        iconBgColor="#f6ffed"
                                    />
                                    <StatCard
                                        title="Assessments Completed"
                                        value={`${data.assessment_analysis.completed} / ${data.assessment_analysis.total}`}
                                        icon={<FormOutlined />}
                                        iconColor="#722ed1"
                                        iconBgColor="#f9f0ff"
                                    />
                                    <StatCard
                                        title="Approved Policies"
                                        value={data.policy_analysis.approved_count}
                                        icon={<SafetyCertificateOutlined />}
                                        iconColor="#13c2c2"
                                        iconBgColor="#e6fffb"
                                    />
                                    <StatCard
                                        title="Overall Score"
                                        value={data.summary.overall_compliance_score}
                                        suffix="%"
                                        icon={<BarChartOutlined />}
                                        iconColor={getScoreColor(data.summary.overall_compliance_score)}
                                        iconBgColor={data.summary.overall_compliance_score >= 70 ? '#f6ffed' : data.summary.overall_compliance_score >= 40 ? '#fffbe6' : '#fff2f0'}
                                    />
                                </div>
                            </DashboardSection>

                            {/* Section 2: Objectives Compliance */}
                            <DashboardSection title="Objectives Compliance" style={{ marginTop: '24px' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
                                    {/* Status breakdown */}
                                    <div style={{ backgroundColor: '#fafafa', borderRadius: '8px', border: '1px solid #f0f0f0', padding: '20px' }}>
                                        <h4 style={{ margin: '0 0 16px', fontSize: '15px', fontWeight: 600, color: '#333' }}>
                                            Status Breakdown
                                        </h4>
                                        {statusRows.map((row) => (
                                            <div key={row.key} style={{
                                                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                                padding: '8px 0', borderBottom: '1px solid #f0f0f0'
                                            }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    <span style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: row.color, display: 'inline-block' }} />
                                                    <span style={{ fontSize: '13px', color: '#555' }}>{row.label}</span>
                                                </div>
                                                <span style={{ fontWeight: 600, fontSize: '14px', color: '#333' }}>
                                                    {data.objectives_analysis[row.key as keyof typeof data.objectives_analysis]}
                                                </span>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Evidence coverage */}
                                    <div style={{ backgroundColor: '#fafafa', borderRadius: '8px', border: '1px solid #f0f0f0', padding: '20px' }}>
                                        <h4 style={{ margin: '0 0 16px', fontSize: '15px', fontWeight: 600, color: '#333' }}>
                                            Evidence Coverage
                                        </h4>
                                        <p style={{ fontSize: '14px', color: '#555', margin: '0 0 16px' }}>
                                            <strong>{data.objectives_analysis.with_evidence}</strong> of{' '}
                                            <strong>{data.objectives_analysis.total}</strong> objectives have evidence attached
                                        </p>
                                        <Progress
                                            percent={data.objectives_analysis.total > 0
                                                ? Math.round((data.objectives_analysis.with_evidence / data.objectives_analysis.total) * 100)
                                                : 0}
                                            strokeColor="#0f386a"
                                            size="default"
                                        />
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', fontSize: '13px', color: '#888' }}>
                                            <span>With evidence: {data.objectives_analysis.with_evidence}</span>
                                            <span>Without evidence: {data.objectives_analysis.without_evidence}</span>
                                        </div>
                                    </div>
                                </div>
                            </DashboardSection>

                            {/* Section 3: Policy Coverage */}
                            <DashboardSection title="Policy Coverage" style={{ marginTop: '24px' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
                                    {/* Policy status breakdown */}
                                    <div style={{ backgroundColor: '#fafafa', borderRadius: '8px', border: '1px solid #f0f0f0', padding: '20px' }}>
                                        <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                                            <div style={{ fontSize: '40px', fontWeight: 700, color: '#13c2c2' }}>
                                                {data.policy_analysis.approved_count}
                                            </div>
                                            <div style={{ fontSize: '14px', color: '#888' }}>
                                                Approved Policies ({data.policy_analysis.approved_percentage}%)
                                            </div>
                                        </div>
                                        {data.policy_analysis.by_status.map((item) => (
                                            <div key={item.status} style={{
                                                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                                padding: '8px 0', borderBottom: '1px solid #f0f0f0'
                                            }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    <span style={{
                                                        width: 10, height: 10, borderRadius: '50%',
                                                        backgroundColor: policyStatusColors[item.status] || '#bfbfbf',
                                                        display: 'inline-block'
                                                    }} />
                                                    <span style={{ fontSize: '13px', color: '#555' }}>{item.status}</span>
                                                </div>
                                                <span style={{ fontWeight: 600, fontSize: '14px', color: '#333' }}>{item.count}</span>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Objective-policy coverage */}
                                    <div style={{ backgroundColor: '#fafafa', borderRadius: '8px', border: '1px solid #f0f0f0', padding: '20px' }}>
                                        <h4 style={{ margin: '0 0 16px', fontSize: '15px', fontWeight: 600, color: '#333' }}>
                                            Objective-Policy Linkage
                                        </h4>
                                        <p style={{ fontSize: '14px', color: '#555', margin: '0 0 16px' }}>
                                            <strong>{data.policy_analysis.objectives_with_policies}</strong> of{' '}
                                            <strong>{data.summary.total_objectives}</strong> objectives linked to policies
                                        </p>
                                        <Progress
                                            percent={data.policy_analysis.policy_coverage_percentage}
                                            strokeColor="#13c2c2"
                                            size="default"
                                        />
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', fontSize: '13px', color: '#888' }}>
                                            <span>Linked: {data.policy_analysis.objectives_with_policies}</span>
                                            <span>Unlinked: {data.policy_analysis.objectives_without_policies}</span>
                                        </div>
                                    </div>
                                </div>
                            </DashboardSection>

                            {/* Section 4: Assessment Progress */}
                            <DashboardSection title="Assessment Progress" style={{ marginTop: '24px' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
                                    {/* Circular progress */}
                                    <div style={{ backgroundColor: '#fafafa', borderRadius: '8px', border: '1px solid #f0f0f0', padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                        <Progress
                                            type="circle"
                                            percent={data.assessment_analysis.completion_rate}
                                            width={140}
                                            strokeColor="#722ed1"
                                            format={(pct) => <span style={{ fontSize: '24px', fontWeight: 700 }}>{pct}%</span>}
                                        />
                                    </div>

                                    {/* Assessment stats */}
                                    <div style={{ backgroundColor: '#fafafa', borderRadius: '8px', border: '1px solid #f0f0f0', padding: '20px' }}>
                                        <h4 style={{ margin: '0 0 16px', fontSize: '15px', fontWeight: 600, color: '#333' }}>
                                            Assessment Details
                                        </h4>
                                        {[
                                            { label: 'Total Assessments', value: data.assessment_analysis.total },
                                            { label: 'Completed', value: data.assessment_analysis.completed, color: '#52c41a' },
                                            { label: 'In Progress', value: data.assessment_analysis.in_progress, color: '#faad14' },
                                            { label: 'Average Progress', value: `${data.assessment_analysis.average_progress}%` },
                                            { label: 'Unanswered Questions', value: data.assessment_analysis.unanswered_questions, color: data.assessment_analysis.unanswered_questions > 0 ? '#ff4d4f' : undefined },
                                            { label: 'Total Questions', value: data.assessment_analysis.total_questions },
                                        ].map((item) => (
                                            <div key={item.label} style={{
                                                display: 'flex', justifyContent: 'space-between',
                                                padding: '8px 0', borderBottom: '1px solid #f0f0f0'
                                            }}>
                                                <span style={{ fontSize: '13px', color: '#555' }}>{item.label}</span>
                                                <span style={{ fontWeight: 600, fontSize: '14px', color: item.color || '#333' }}>{item.value}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </DashboardSection>

                            {/* Section 5: Chapter Breakdown */}
                            {data.chapter_breakdown.length > 0 && (
                                <DashboardSection title="Chapter Breakdown" style={{ marginTop: '24px' }}>
                                    <Table
                                        dataSource={data.chapter_breakdown}
                                        columns={chapterColumns}
                                        rowKey="chapter_title"
                                        pagination={false}
                                        size="small"
                                        style={{ backgroundColor: '#fff', borderRadius: '8px' }}
                                    />
                                </DashboardSection>
                            )}

                            {/* Section 6: Identified Gaps */}
                            <DashboardSection title="Identified Gaps" style={{ marginTop: '24px' }}>
                                <Collapse
                                    bordered={false}
                                    style={{ backgroundColor: '#fafafa', borderRadius: '8px' }}
                                    items={[
                                        {
                                            key: 'without_evidence',
                                            label: (
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    <FileSearchOutlined style={{ color: '#faad14' }} />
                                                    <span>Objectives Without Evidence</span>
                                                    <span style={{
                                                        backgroundColor: '#fff7e6', color: '#d48806', fontSize: '12px',
                                                        fontWeight: 600, padding: '1px 8px', borderRadius: '10px', border: '1px solid #ffe58f'
                                                    }}>
                                                        {data.gaps.objectives_without_evidence.length}
                                                    </span>
                                                </div>
                                            ),
                                            children: data.gaps.objectives_without_evidence.length > 0 ? (
                                                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                                                    {data.gaps.objectives_without_evidence.map((gap) => (
                                                        <div key={gap.id} style={{
                                                            padding: '8px 12px', borderBottom: '1px solid #f0f0f0',
                                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                                                        }}>
                                                            <div>
                                                                <div style={{ fontSize: '13px', color: '#333' }}>{gap.title}</div>
                                                                <div style={{ fontSize: '12px', color: '#999' }}>{gap.chapter_title}</div>
                                                            </div>
                                                            <span style={{ fontSize: '12px', color: '#888', whiteSpace: 'nowrap', marginLeft: '12px' }}>{gap.compliance_status}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : <p style={{ color: '#999', margin: 0 }}>All objectives have evidence attached.</p>,
                                        },
                                        {
                                            key: 'not_compliant',
                                            label: (
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
                                                    <span>Non-Compliant Objectives</span>
                                                    <span style={{
                                                        backgroundColor: '#fff2f0', color: '#cf1322', fontSize: '12px',
                                                        fontWeight: 600, padding: '1px 8px', borderRadius: '10px', border: '1px solid #ffccc7'
                                                    }}>
                                                        {data.gaps.objectives_not_compliant.length}
                                                    </span>
                                                </div>
                                            ),
                                            children: data.gaps.objectives_not_compliant.length > 0 ? (
                                                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                                                    {data.gaps.objectives_not_compliant.map((gap) => (
                                                        <div key={gap.id} style={{
                                                            padding: '8px 12px', borderBottom: '1px solid #f0f0f0',
                                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                                                        }}>
                                                            <div>
                                                                <div style={{ fontSize: '13px', color: '#333' }}>{gap.title}</div>
                                                                <div style={{ fontSize: '12px', color: '#999' }}>{gap.chapter_title}</div>
                                                            </div>
                                                            <span style={{ fontSize: '12px', color: '#ff4d4f', fontWeight: 600, whiteSpace: 'nowrap', marginLeft: '12px' }}>{gap.compliance_status}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : <p style={{ color: '#999', margin: 0 }}>No non-compliant objectives found.</p>,
                                        },
                                        {
                                            key: 'without_policies',
                                            label: (
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    <LinkOutlined style={{ color: '#1890ff' }} />
                                                    <span>Objectives Without Policy Coverage</span>
                                                    <span style={{
                                                        backgroundColor: '#e6f7ff', color: '#096dd9', fontSize: '12px',
                                                        fontWeight: 600, padding: '1px 8px', borderRadius: '10px', border: '1px solid #91d5ff'
                                                    }}>
                                                        {data.gaps.objectives_without_policies.length}
                                                    </span>
                                                </div>
                                            ),
                                            children: data.gaps.objectives_without_policies.length > 0 ? (
                                                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                                                    {data.gaps.objectives_without_policies.map((gap) => (
                                                        <div key={gap.id} style={{
                                                            padding: '8px 12px', borderBottom: '1px solid #f0f0f0'
                                                        }}>
                                                            <div style={{ fontSize: '13px', color: '#333' }}>{gap.title}</div>
                                                            <div style={{ fontSize: '12px', color: '#999' }}>{gap.chapter_title}</div>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : <p style={{ color: '#999', margin: 0 }}>All objectives are linked to policies.</p>,
                                        },
                                    ]}
                                />
                            </DashboardSection>

                            <div style={{ marginBottom: '28px' }} />
                        </div>
                    ) : null}
                </div>
            </div>
        </div>
    );
};

export default GapAnalysisPage;
