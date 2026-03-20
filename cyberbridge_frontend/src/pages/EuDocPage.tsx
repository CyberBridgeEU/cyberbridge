import { useState, useEffect } from 'react';
import { DownloadOutlined, FileDoneOutlined, CheckCircleOutlined, CloseCircleOutlined, AimOutlined, FormOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { Progress, Tag, Spin, Tooltip } from 'antd';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { StatCard, DashboardSection } from "../components/dashboard";
import useAuthStore from "../store/useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

interface ReadinessData {
    objectives: {
        total: number;
        compliant: number;
        partially_compliant: number;
        not_compliant: number;
        in_review: number;
        not_assessed: number;
        not_applicable: number;
    };
    assessments: {
        total: number;
        completed: number;
        average_progress: number;
    };
    readiness_score: number;
    is_ready: boolean;
    has_cra_framework: boolean;
}

const sections = [
    {
        number: 1,
        title: 'Product Identification',
        description: 'Unique details that identify the product with digital elements — product name, type/model, batch or serial number, firmware/software version, and any other unique identifier.'
    },
    {
        number: 2,
        title: 'Manufacturer Details',
        description: 'Name, registered trade name or trademark, and postal address of the manufacturer. Where applicable, include the single point of contact as required by Article 13(20) of the CRA.'
    },
    {
        number: 3,
        title: 'Sole Responsibility Statement',
        description: 'A statement confirming that the EU Declaration of Conformity is issued under the sole responsibility of the manufacturer, taking full accountability for the product\'s compliance.'
    },
    {
        number: 4,
        title: 'Object of the Declaration',
        description: 'A clear description of the product with digital elements — its intended purpose, functionality, and classification (Default, Important Class I, Important Class II, or Critical).'
    },
    {
        number: 5,
        title: 'Conformity Assessment Procedure',
        description: 'The conformity assessment procedure followed as set out in Annex VIII — for example, Module A (Internal Control), Module B+C (EU-type Examination), or Module H (Full Quality Assurance).'
    },
    {
        number: 6,
        title: 'Harmonised Standards & Specifications',
        description: 'References to the relevant harmonised standards, common specifications, or European cybersecurity certification schemes used to demonstrate conformity with the essential requirements.'
    },
    {
        number: 7,
        title: 'Notified Body (if applicable)',
        description: 'Where a notified body was involved in the conformity assessment — its name, identification number, the certificate or report reference, and the date of issue.'
    },
    {
        number: 8,
        title: 'Signature',
        description: 'The declaration must be signed by a person authorised to act on behalf of the manufacturer, including their full name, position, date, and place of issue.'
    }
];

const statusRows: { key: string; label: string; color: string }[] = [
    { key: 'compliant', label: 'Compliant', color: '#52c41a' },
    { key: 'partially_compliant', label: 'Partially Compliant', color: '#faad14' },
    { key: 'not_compliant', label: 'Not Compliant', color: '#ff4d4f' },
    { key: 'in_review', label: 'In Review', color: '#1890ff' },
    { key: 'not_assessed', label: 'Not Assessed', color: '#d9d9d9' },
    { key: 'not_applicable', label: 'Not Applicable', color: '#bfbfbf' },
];

const EuDocPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const getAuthHeader = useAuthStore((s) => s.getAuthHeader);

    const [readiness, setReadiness] = useState<ReadinessData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchReadiness = async () => {
            try {
                const headers = getAuthHeader();
                if (!headers) return;
                const res = await fetch(`${cyberbridge_back_end_rest_api}/dashboard/cra-doc-readiness`, { headers });
                if (res.ok) {
                    setReadiness(await res.json());
                }
            } catch (err) {
                console.error('Failed to fetch CRA DoC readiness:', err);
            } finally {
                setLoading(false);
            }
        };
        fetchReadiness();
    }, [getAuthHeader]);

    const gaugeColor = readiness
        ? readiness.readiness_score >= 80 ? '#52c41a'
            : readiness.readiness_score >= 50 ? '#faad14'
                : '#ff4d4f'
        : '#d9d9d9';

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
                            <FileDoneOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>EU Declaration of Conformity</h1>
                        </div>
                    </div>

                    {/* Intro */}
                    <div style={{
                        backgroundColor: '#fff',
                        borderRadius: '8px',
                        border: '1px solid #f0f0f0',
                        padding: '24px',
                        marginTop: '20px'
                    }}>
                        <p style={{ margin: 0, lineHeight: 1.7, color: '#444', fontSize: '14px' }}>
                            The <strong>EU Declaration of Conformity (DoC)</strong> is a mandatory document under the
                            Cyber Resilience Act (Regulation (EU) 2024/2847). Before placing a product with digital
                            elements on the EU market, the manufacturer must draw up a DoC in accordance with
                            Article 28 and Annex V, declaring that the essential cybersecurity requirements have been
                            fulfilled. The DoC must be kept up to date and made available to market surveillance
                            authorities for at least 10 years after the product is placed on the market.
                        </p>
                    </div>

                    {/* CRA DoC Readiness Section */}
                    {loading ? (
                        <div style={{ textAlign: 'center', padding: '40px 0' }}>
                            <Spin size="large" />
                        </div>
                    ) : readiness?.has_cra_framework ? (
                        <DashboardSection
                            title="CRA DoC Readiness"
                            subtitle="Live compliance readiness metrics based on your CRA framework objectives and assessments."
                            style={{ marginTop: '24px' }}
                        >
                            {/* Readiness Gauge + Badge */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '32px', marginBottom: '24px', flexWrap: 'wrap' }}>
                                <Tooltip title={`Readiness score: ${readiness.readiness_score}% (>= 80% required)`}>
                                    <Progress
                                        type="dashboard"
                                        percent={readiness.readiness_score}
                                        strokeColor={gaugeColor}
                                        width={140}
                                        format={(pct) => <span style={{ fontSize: '24px', fontWeight: 700 }}>{pct}%</span>}
                                    />
                                </Tooltip>
                                <div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                                        {readiness.is_ready ? (
                                            <Tag icon={<CheckCircleOutlined />} color="success" style={{ fontSize: '14px', padding: '4px 12px' }}>
                                                Ready to Issue DoC
                                            </Tag>
                                        ) : (
                                            <Tag icon={<CloseCircleOutlined />} color="warning" style={{ fontSize: '14px', padding: '4px 12px' }}>
                                                Not Yet Ready
                                            </Tag>
                                        )}
                                        <a
                                            href="/docs/examples/EU_Declaration_of_Conformity_Template.docx"
                                            download
                                            style={{
                                                display: 'inline-flex',
                                                alignItems: 'center',
                                                gap: '6px',
                                                padding: '4px 14px',
                                                backgroundColor: '#ecfdf5',
                                                color: '#059669',
                                                border: '1px solid #a7f3d0',
                                                borderRadius: '6px',
                                                fontSize: '13px',
                                                fontWeight: 500,
                                                textDecoration: 'none',
                                                transition: 'all 0.2s',
                                                cursor: 'pointer'
                                            }}
                                            onMouseEnter={(e) => {
                                                e.currentTarget.style.backgroundColor = '#d1fae5';
                                                e.currentTarget.style.borderColor = '#6ee7b7';
                                            }}
                                            onMouseLeave={(e) => {
                                                e.currentTarget.style.backgroundColor = '#ecfdf5';
                                                e.currentTarget.style.borderColor = '#a7f3d0';
                                            }}
                                        >
                                            <DownloadOutlined />
                                            Download DoC Template
                                        </a>
                                    </div>
                                    <p style={{ margin: '8px 0 0', color: '#666', fontSize: '13px' }}>
                                        Score = 60% objectives compliance + 40% assessment completion
                                    </p>
                                </div>
                            </div>

                            {/* Stat Cards */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
                                <StatCard
                                    title="CRA Objectives"
                                    value={readiness.objectives.total}
                                    icon={<AimOutlined />}
                                    iconColor="#0f386a"
                                    iconBgColor="#EBF4FC"
                                />
                                <StatCard
                                    title="Objectives Compliant"
                                    value={readiness.objectives.compliant}
                                    icon={<CheckCircleOutlined />}
                                    iconColor="#52c41a"
                                    iconBgColor="#f6ffed"
                                />
                                <StatCard
                                    title="CRA Assessments"
                                    value={readiness.assessments.total}
                                    icon={<FormOutlined />}
                                    iconColor="#722ed1"
                                    iconBgColor="#f9f0ff"
                                />
                                <StatCard
                                    title="Assessments Completed"
                                    value={readiness.assessments.completed}
                                    icon={<SafetyCertificateOutlined />}
                                    iconColor="#13c2c2"
                                    iconBgColor="#e6fffb"
                                />
                            </div>

                            {/* Detail Panels */}
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
                                {/* Objectives Breakdown */}
                                <div style={{
                                    backgroundColor: '#fafafa',
                                    borderRadius: '8px',
                                    border: '1px solid #f0f0f0',
                                    padding: '20px'
                                }}>
                                    <h4 style={{ margin: '0 0 16px', fontSize: '15px', fontWeight: 600, color: '#333' }}>
                                        Objectives Breakdown
                                    </h4>
                                    {statusRows.map((row) => (
                                        <div key={row.key} style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'space-between',
                                            padding: '8px 0',
                                            borderBottom: '1px solid #f0f0f0'
                                        }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <span style={{
                                                    width: '10px',
                                                    height: '10px',
                                                    borderRadius: '50%',
                                                    backgroundColor: row.color,
                                                    display: 'inline-block'
                                                }} />
                                                <span style={{ fontSize: '13px', color: '#555' }}>{row.label}</span>
                                            </div>
                                            <span style={{ fontWeight: 600, fontSize: '14px', color: '#333' }}>
                                                {readiness.objectives[row.key as keyof typeof readiness.objectives]}
                                            </span>
                                        </div>
                                    ))}
                                </div>

                                {/* Assessment Progress */}
                                <div style={{
                                    backgroundColor: '#fafafa',
                                    borderRadius: '8px',
                                    border: '1px solid #f0f0f0',
                                    padding: '20px'
                                }}>
                                    <h4 style={{ margin: '0 0 16px', fontSize: '15px', fontWeight: 600, color: '#333' }}>
                                        Assessment Progress
                                    </h4>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                                        <Progress
                                            type="circle"
                                            percent={readiness.assessments.average_progress}
                                            width={100}
                                            strokeColor="#722ed1"
                                            format={(pct) => <span style={{ fontSize: '16px', fontWeight: 600 }}>{pct}%</span>}
                                        />
                                        <div>
                                            <div style={{ marginBottom: '12px' }}>
                                                <span style={{ fontSize: '13px', color: '#888' }}>Completed</span>
                                                <div style={{ fontSize: '20px', fontWeight: 700, color: '#333' }}>
                                                    {readiness.assessments.completed}
                                                    <span style={{ fontSize: '14px', fontWeight: 400, color: '#888' }}> / {readiness.assessments.total}</span>
                                                </div>
                                            </div>
                                            <div>
                                                <span style={{ fontSize: '13px', color: '#888' }}>In Progress</span>
                                                <div style={{ fontSize: '20px', fontWeight: 700, color: '#333' }}>
                                                    {readiness.assessments.total - readiness.assessments.completed}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </DashboardSection>
                    ) : null}

                    {/* Section Cards */}
                    <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#333', margin: '28px 0 16px' }}>
                        Mandatory Sections of the Declaration
                    </h2>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                        gap: '16px'
                    }}>
                        {sections.map((section) => (
                            <div
                                key={section.number}
                                style={{
                                    backgroundColor: '#fff',
                                    borderRadius: '8px',
                                    border: '1px solid #f0f0f0',
                                    padding: '20px',
                                    display: 'flex',
                                    gap: '14px',
                                    transition: 'border-color 0.2s'
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.borderColor = '#0f386a';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.borderColor = '#f0f0f0';
                                }}
                            >
                                <div style={{
                                    width: '32px',
                                    height: '32px',
                                    borderRadius: '50%',
                                    backgroundColor: '#f0f7ff',
                                    color: '#0f386a',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontWeight: 700,
                                    fontSize: '14px',
                                    flexShrink: 0
                                }}>
                                    {section.number}
                                </div>
                                <div>
                                    <div style={{ fontWeight: 600, fontSize: '14px', color: '#333', marginBottom: '6px' }}>
                                        {section.title}
                                    </div>
                                    <div style={{ fontSize: '13px', color: '#666', lineHeight: 1.6 }}>
                                        {section.description}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* When Must You Issue */}
                    <div style={{
                        backgroundColor: '#f0f7ff',
                        borderRadius: '8px',
                        border: '1px solid #d6e8f7',
                        padding: '24px',
                        marginTop: '28px'
                    }}>
                        <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#1a3c6e', margin: '0 0 12px' }}>
                            When Must You Issue a DoC?
                        </h3>
                        <ul style={{ margin: 0, paddingLeft: '20px', color: '#444', fontSize: '14px', lineHeight: 1.8 }}>
                            <li><strong>Before placing the product on the EU market</strong> — the DoC must exist and be available at the time of market entry.</li>
                            <li><strong>After every substantial modification</strong> — if the product is substantially modified, a new conformity assessment and DoC may be required.</li>
                            <li><strong>Retention period</strong> — the DoC must be kept for at least 10 years after the product is placed on the market, or after the end of the support period, whichever is longer.</li>
                            <li><strong>Language</strong> — it must be translated into the language(s) required by the Member State where the product is placed or made available.</li>
                        </ul>
                    </div>

                    <div style={{ marginBottom: '28px' }} />
                </div>
            </div>
        </div>
    );
};

export default EuDocPage;
