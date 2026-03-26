import { useState, useEffect, useRef } from 'react';
import {
    BarChartOutlined, AimOutlined, CheckCircleOutlined, FormOutlined,
    SafetyCertificateOutlined, DownloadOutlined, ExclamationCircleOutlined,
    FileSearchOutlined, CloseCircleOutlined, LinkOutlined, HistoryOutlined,
    DeleteOutlined, CompassOutlined, LoadingOutlined, ThunderboltOutlined,
    ClockCircleOutlined, WarningOutlined, ToolOutlined, CodeOutlined,
    FileTextOutlined, ReadOutlined
} from '@ant-design/icons';
import { Progress, Spin, Select, Collapse, Table, Modal, Tag, Tooltip, message, Button, Steps, Alert, Divider, Typography } from 'antd';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { StatCard, DashboardSection } from "../components/dashboard";
import useAuthStore from "../store/useAuthStore.ts";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import useCRAFilteredFrameworks from "../hooks/useCRAFilteredFrameworks.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import { exportToPdf } from "../utils/pdfUtils.ts";
import useRoadmapStore from "../store/useRoadmapStore.ts";
import type { RoadmapData, RoadmapActionStep } from "../store/useRoadmapStore.ts";

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

interface Certificate {
    id: string;
    certificate_number: string;
    framework_name: string;
    organisation_name: string;
    overall_score: number;
    objectives_compliant_pct: number;
    assessments_completed_pct: number;
    policies_approved_pct: number;
    issued_at: string;
    expires_at: string;
    revoked: boolean;
    revoked_at: string | null;
    revoked_reason: string | null;
    verification_hash: string;
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
    const getUserRole = useAuthStore((s) => s.getUserRole);
    const { fetchFrameworks } = useFrameworksStore();
    const { filteredFrameworks } = useCRAFilteredFrameworks();

    const [data, setData] = useState<GapAnalysisData | null>(null);
    const [loading, setLoading] = useState(true);
    const [selectedFrameworkId, setSelectedFrameworkId] = useState<string | undefined>(undefined);
    const [exporting, setExporting] = useState(false);
    const contentRef = useRef<HTMLDivElement>(null);

    // Certificate state
    const [generatingCert, setGeneratingCert] = useState(false);
    const [certificates, setCertificates] = useState<Certificate[]>([]);
    const [showCertHistory, setShowCertHistory] = useState(false);
    const [revokingId, setRevokingId] = useState<string | null>(null);

    // Bulk roadmap state
    const [showBulkRoadmap, setShowBulkRoadmap] = useState(false);
    const { bulkRoadmaps, bulkLoading, error: roadmapError, generateBulkRoadmap, clearBulkRoadmaps } = useRoadmapStore();

    const userRole = getUserRole();
    const isAdmin = userRole === 'org_admin' || userRole === 'super_admin';

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

    // Fetch certificates when framework changes
    useEffect(() => {
        const fetchCertificates = async () => {
            const headers = getAuthHeader();
            if (!headers) return;
            try {
                const params = selectedFrameworkId ? `?framework_id=${selectedFrameworkId}` : '';
                const res = await fetch(`${cyberbridge_back_end_rest_api}/certificates${params}`, { headers });
                if (res.ok) {
                    setCertificates(await res.json());
                }
            } catch (err) {
                console.error('Failed to fetch certificates:', err);
            }
        };
        fetchCertificates();
    }, [getAuthHeader, selectedFrameworkId]);

    const handleExportPdf = async () => {
        setExporting(true);
        try {
            await exportToPdf(contentRef.current, 'gap_analysis_report');
        } finally {
            setExporting(false);
        }
    };

    const handleGenerateCertificate = async () => {
        if (!selectedFrameworkId) return;
        setGeneratingCert(true);
        try {
            const headers = getAuthHeader();
            if (!headers) return;
            const res = await fetch(`${cyberbridge_back_end_rest_api}/certificates/generate`, {
                method: 'POST',
                headers: { ...headers, 'Content-Type': 'application/json' },
                body: JSON.stringify({ framework_id: selectedFrameworkId }),
            });
            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                const disposition = res.headers.get('Content-Disposition');
                const filename = disposition?.match(/filename="(.+)"/)?.[1] || 'certificate.pdf';
                a.href = url;
                a.download = filename;
                a.click();
                window.URL.revokeObjectURL(url);
                message.success('Certificate generated successfully!');
                // Refresh certificates list
                const certsRes = await fetch(
                    `${cyberbridge_back_end_rest_api}/certificates?framework_id=${selectedFrameworkId}`,
                    { headers }
                );
                if (certsRes.ok) setCertificates(await certsRes.json());
            } else {
                const err = await res.json();
                message.error(err.detail || 'Failed to generate certificate');
            }
        } catch (err) {
            console.error('Certificate generation failed:', err);
            message.error('Failed to generate certificate');
        } finally {
            setGeneratingCert(false);
        }
    };

    const handleDownloadCertificate = async (certId: string) => {
        const headers = getAuthHeader();
        if (!headers) return;
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/certificates/${certId}/download`, { headers });
            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                const disposition = res.headers.get('Content-Disposition');
                const filename = disposition?.match(/filename="(.+)"/)?.[1] || 'certificate.pdf';
                a.href = url;
                a.download = filename;
                a.click();
                window.URL.revokeObjectURL(url);
            }
        } catch (err) {
            console.error('Download failed:', err);
        }
    };

    const handleRevokeCertificate = async (certId: string) => {
        const headers = getAuthHeader();
        if (!headers) return;
        const reason = window.prompt('Enter revocation reason:');
        if (!reason) return;
        setRevokingId(certId);
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/certificates/${certId}/revoke`, {
                method: 'POST',
                headers: { ...headers, 'Content-Type': 'application/json' },
                body: JSON.stringify({ reason }),
            });
            if (res.ok) {
                message.success('Certificate revoked');
                // Refresh
                const params = selectedFrameworkId ? `?framework_id=${selectedFrameworkId}` : '';
                const certsRes = await fetch(`${cyberbridge_back_end_rest_api}/certificates${params}`, { headers });
                if (certsRes.ok) setCertificates(await certsRes.json());
            } else {
                const err = await res.json();
                message.error(err.detail || 'Failed to revoke certificate');
            }
        } catch (err) {
            console.error('Revoke failed:', err);
        } finally {
            setRevokingId(null);
        }
    };

    const canGenerateCertificate = selectedFrameworkId && data && data.summary.overall_compliance_score === 100 && isAdmin;

    const certColumns = [
        {
            title: 'Certificate #',
            dataIndex: 'certificate_number',
            key: 'certificate_number',
            width: 180,
        },
        {
            title: 'Framework',
            dataIndex: 'framework_name',
            key: 'framework_name',
        },
        {
            title: 'Score',
            dataIndex: 'overall_score',
            key: 'overall_score',
            width: 80,
            align: 'center' as const,
            render: (val: number) => <span style={{ fontWeight: 600, color: '#52c41a' }}>{val}%</span>,
        },
        {
            title: 'Issued',
            dataIndex: 'issued_at',
            key: 'issued_at',
            width: 120,
            render: (val: string) => new Date(val).toLocaleDateString(),
        },
        {
            title: 'Expires',
            dataIndex: 'expires_at',
            key: 'expires_at',
            width: 120,
            render: (val: string) => new Date(val).toLocaleDateString(),
        },
        {
            title: 'Status',
            key: 'status',
            width: 100,
            render: (_: unknown, record: Certificate) => record.revoked
                ? <Tag color="red">Revoked</Tag>
                : new Date(record.expires_at) < new Date()
                    ? <Tag color="orange">Expired</Tag>
                    : <Tag color="green">Valid</Tag>,
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 140,
            render: (_: unknown, record: Certificate) => (
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        onClick={() => handleDownloadCertificate(record.id)}
                        style={{
                            padding: '2px 8px', fontSize: '12px', cursor: 'pointer',
                            backgroundColor: '#1a365d', color: '#fff', border: 'none',
                            borderRadius: '4px',
                        }}
                    >
                        <DownloadOutlined /> PDF
                    </button>
                    {isAdmin && !record.revoked && (
                        <button
                            onClick={() => handleRevokeCertificate(record.id)}
                            disabled={revokingId === record.id}
                            style={{
                                padding: '2px 8px', fontSize: '12px', cursor: 'pointer',
                                backgroundColor: '#ff4d4f', color: '#fff', border: 'none',
                                borderRadius: '4px', opacity: revokingId === record.id ? 0.6 : 1,
                            }}
                        >
                            <DeleteOutlined /> Revoke
                        </button>
                    )}
                </div>
            ),
        },
    ];

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
                            <Tooltip title={
                                !isAdmin ? 'Only admins can generate certificates'
                                : !selectedFrameworkId ? 'Select a framework first'
                                : !data || data.summary.overall_compliance_score < 100 ? `Score must be 100% (currently ${data?.summary.overall_compliance_score ?? 0}%)`
                                : ''
                            }>
                                <span>
                                    <button
                                        onClick={handleGenerateCertificate}
                                        disabled={!canGenerateCertificate || generatingCert}
                                        style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            gap: '6px',
                                            padding: '6px 16px',
                                            backgroundColor: canGenerateCertificate ? '#52c41a' : '#a0d911',
                                            color: '#fff',
                                            border: 'none',
                                            borderRadius: '6px',
                                            fontSize: '13px',
                                            fontWeight: 500,
                                            cursor: !canGenerateCertificate || generatingCert ? 'not-allowed' : 'pointer',
                                            opacity: !canGenerateCertificate || generatingCert ? 0.45 : 1,
                                            transition: 'all 0.2s',
                                        }}
                                    >
                                        <SafetyCertificateOutlined />
                                        {generatingCert ? 'Generating...' : 'Generate Certificate'}
                                    </button>
                                </span>
                            </Tooltip>
                            <Tooltip title={certificates.length === 0 ? 'No certificates generated yet' : ''}>
                                <span>
                                    <button
                                        onClick={() => setShowCertHistory(true)}
                                        disabled={certificates.length === 0}
                                        style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            gap: '6px',
                                            padding: '6px 16px',
                                            backgroundColor: '#0f386a',
                                            color: '#fff',
                                            border: 'none',
                                            borderRadius: '6px',
                                            fontSize: '13px',
                                            fontWeight: 500,
                                            cursor: certificates.length === 0 ? 'not-allowed' : 'pointer',
                                            opacity: certificates.length === 0 ? 0.45 : 1,
                                            transition: 'all 0.2s',
                                        }}
                                    >
                                        <HistoryOutlined />
                                        Certificates ({certificates.length})
                                    </button>
                                </span>
                            </Tooltip>
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
                                {data.gaps.objectives_not_compliant.length > 0 && (
                                    <div style={{ marginBottom: '16px' }}>
                                        <Button
                                            type="primary"
                                            icon={bulkLoading ? <LoadingOutlined spin /> : <CompassOutlined />}
                                            loading={bulkLoading}
                                            onClick={async () => {
                                                if (!selectedFrameworkId) return;
                                                const ids = data.gaps.objectives_not_compliant.map(g => g.id);
                                                setShowBulkRoadmap(true);
                                                await generateBulkRoadmap(selectedFrameworkId, ids.slice(0, 10));
                                            }}
                                            style={{ backgroundColor: '#0f386a', borderColor: '#0f386a' }}
                                        >
                                            Generate Roadmaps for Non-Compliant Objectives
                                        </Button>
                                        <span style={{ marginLeft: 12, fontSize: '12px', color: '#8c8c8c' }}>
                                            (up to 10 objectives)
                                        </span>
                                    </div>
                                )}
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

            {/* Bulk Roadmap Modal */}
            <Modal
                title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <CompassOutlined style={{ color: '#0f386a' }} />
                        <span>Compliance Roadmaps</span>
                    </div>
                }
                open={showBulkRoadmap}
                onCancel={() => { setShowBulkRoadmap(false); clearBulkRoadmaps(); }}
                footer={null}
                width={800}
                styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
            >
                {bulkLoading && (
                    <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                        <Spin indicator={<LoadingOutlined style={{ fontSize: 36 }} spin />} />
                        <div style={{ marginTop: 20, color: '#8c8c8c', fontSize: '15px' }}>
                            Generating compliance roadmaps...
                        </div>
                        <div style={{ marginTop: 8, color: '#bfbfbf', fontSize: '13px' }}>
                            This may take a few minutes depending on the number of objectives
                        </div>
                    </div>
                )}
                {roadmapError && !bulkLoading && (
                    <Alert message="Error" description={roadmapError} type="error" showIcon style={{ marginBottom: 16 }} />
                )}
                {!bulkLoading && bulkRoadmaps.length > 0 && (
                    <Collapse
                        accordion
                        style={{ backgroundColor: '#fafafa' }}
                        items={bulkRoadmaps.map((rm, idx) => ({
                            key: rm.objective_id,
                            label: (
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontWeight: 600 }}>{idx + 1}. {rm.objective_title}</span>
                                    <div style={{ display: 'flex', gap: 6 }}>
                                        <Tag color="red">{rm.current_status}</Tag>
                                        <Tag color="default">{rm.action_steps.length} steps</Tag>
                                        <Tag icon={<ClockCircleOutlined />}>{rm.estimated_total_effort}</Tag>
                                    </div>
                                </div>
                            ),
                            children: (
                                <div>
                                    <div style={{
                                        padding: '10px 14px', backgroundColor: '#fff7e6',
                                        border: '1px solid #ffd591', borderRadius: '6px', marginBottom: 14
                                    }}>
                                        <Typography.Text strong style={{ color: '#d46b08' }}>
                                            <WarningOutlined style={{ marginRight: 6 }} />Gap Summary
                                        </Typography.Text>
                                        <Typography.Paragraph style={{ margin: '6px 0 0 0', fontSize: '13px' }}>
                                            {rm.gap_summary}
                                        </Typography.Paragraph>
                                    </div>
                                    {rm.quick_wins && rm.quick_wins.length > 0 && (
                                        <div style={{ marginBottom: 14 }}>
                                            <Typography.Text strong style={{ fontSize: '13px' }}>
                                                <ThunderboltOutlined style={{ color: '#52c41a', marginRight: 6 }} />Quick Wins
                                            </Typography.Text>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
                                                {rm.quick_wins.map((w, i) => (
                                                    <Tag key={i} color="green" style={{ fontSize: '12px' }}>{w}</Tag>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    <Typography.Text strong style={{ display: 'block', marginBottom: 8, fontSize: '13px' }}>
                                        Action Steps
                                    </Typography.Text>
                                    {rm.action_steps.map((step) => (
                                        <div key={step.step_number} style={{
                                            padding: '10px 12px', marginBottom: 8,
                                            backgroundColor: '#fff', borderRadius: '6px', border: '1px solid #f0f0f0'
                                        }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                                                <span style={{
                                                    width: 22, height: 22, borderRadius: '50%', backgroundColor: '#0f386a',
                                                    color: '#fff', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                                                    fontSize: '11px', fontWeight: 700, flexShrink: 0
                                                }}>{step.step_number}</span>
                                                <Typography.Text strong style={{ fontSize: '13px' }}>{step.title}</Typography.Text>
                                            </div>
                                            <Typography.Paragraph style={{ margin: '0 0 8px 30px', fontSize: '13px', color: '#595959' }}>
                                                {step.description}
                                            </Typography.Paragraph>
                                            <div style={{ marginLeft: 30, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                                                <Tag color={step.priority === 'critical' ? 'red' : step.priority === 'high' ? 'volcano' : step.priority === 'medium' ? 'orange' : 'blue'}>
                                                    {step.priority}
                                                </Tag>
                                                <Tag>{step.estimated_effort}</Tag>
                                                <Tag color={step.category === 'technical' ? 'geekblue' : step.category === 'policy' ? 'purple' : step.category === 'evidence' ? 'cyan' : 'gold'}>
                                                    {step.category}
                                                </Tag>
                                            </div>
                                            {step.platform_action && (
                                                <div style={{
                                                    marginTop: 8, marginLeft: 30, padding: '6px 10px',
                                                    backgroundColor: '#f0f5ff', borderRadius: '4px', fontSize: '12px',
                                                    borderLeft: '2px solid #1890ff'
                                                }}>
                                                    <ToolOutlined style={{ marginRight: 4, color: '#1890ff' }} />
                                                    {step.platform_action}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                    {rm.risk_if_unaddressed && (
                                        <Alert message="Risk if Unaddressed" description={rm.risk_if_unaddressed} type="warning" showIcon style={{ marginTop: 12 }} />
                                    )}
                                </div>
                            ),
                        }))}
                    />
                )}
                {!bulkLoading && bulkRoadmaps.length === 0 && !roadmapError && (
                    <div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>
                        No roadmaps generated yet.
                    </div>
                )}
            </Modal>

            {/* Certificate History Modal */}
            <Modal
                title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <SafetyCertificateOutlined style={{ color: '#0f386a' }} />
                        <span>Certificate History</span>
                    </div>
                }
                open={showCertHistory}
                onCancel={() => setShowCertHistory(false)}
                footer={null}
                width={900}
            >
                <Table
                    dataSource={certificates}
                    columns={certColumns}
                    rowKey="id"
                    pagination={false}
                    size="small"
                    style={{ marginTop: '16px' }}
                />
            </Modal>
        </div>
    );
};

export default GapAnalysisPage;
