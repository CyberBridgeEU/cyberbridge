// src/pages/dashboards/OrgAdminDashboard.tsx
import React, { useEffect } from 'react';
import { useLocation } from 'wouter';
import { Table, Progress, Empty, Badge, List, Avatar } from 'antd';
import { Chart } from 'react-google-charts';
import {
    TeamOutlined,
    FormOutlined,
    ClockCircleOutlined,
    CheckCircleOutlined,
    FileProtectOutlined,
    AlertOutlined,
    PlusOutlined,
    UserAddOutlined,
    AppstoreOutlined,
    CheckSquareOutlined,
    UserOutlined,
    RocketOutlined
} from '@ant-design/icons';
import { StatCard, QuickActionButton, QuickActionsPanel, DashboardSection, CyberBridgeTourPanel } from '../../components/dashboard';
import useDashboardStore from '../../store/useDashboardStore';
import { useAdminAreaStore, PendingUser } from '../../store/adminAreaStore';
import useOnboardingStore from '../../store/useOnboardingStore';

// Import framework logos
import craLogo from '../../assets/cra_logo.svg';
import iso27001Logo from '../../assets/iso27001_logo.png';
import nis2Logo from '../../assets/nis2_logo.png';
import nistCsfLogo from '../../assets/nist_csf_logo.webp';
import pciDssLogo from '../../assets/pci_dss_logo.png';
import soc2Logo from '../../assets/soc_2_logo.png';
import hipaaLogo from '../../assets/hippa_logo.png';
import ccpaLogo from '../../assets/ccpa_logo.webp';
import gdprLogo from '../../assets/gdpr_logo.jpg';
import cmmc20Logo from '../../assets/cmmc_2_0_logo.jpeg';
import doraLogo from '../../assets/dora_logo.webp';
import aescsfLogo from '../../assets/australia_energy_aescsf_logo.svg';
import ftcSafeguardsLogo from '../../assets/ftc_safeguards_logo.png';
import cobit2019Logo from '../../assets/cobit_2019_logo.webp';

// Helper function to get framework logo
const getFrameworkLogo = (frameworkName: string): string | null => {
    const name = frameworkName.toLowerCase();
    if (name.includes('cra') || name.includes('cyber resilience act')) return craLogo;
    if (name.includes('iso27001') || name.includes('iso 27001')) return iso27001Logo;
    if (name.includes('nis2') || name.includes('nis 2')) return nis2Logo;
    if (name.includes('aescsf') || name.includes('australia energy')) return aescsfLogo;
    if (name.includes('nist') || name.includes('csf')) return nistCsfLogo;
    if (name.includes('pci') || name.includes('dss')) return pciDssLogo;
    if (name.includes('soc') || name.includes('soc 2') || name.includes('soc2')) return soc2Logo;
    if (name.includes('hipaa') || name.includes('hippa') || name.includes('privacy rule')) return hipaaLogo;
    if (name.includes('ccpa') || name.includes('california consumer privacy act')) return ccpaLogo;
    if (name.includes('gdpr') || name.includes('general data protection regulation')) return gdprLogo;
    if (name.includes('cmmc') || name.includes('cybersecurity maturity model certification')) return cmmc20Logo;
    if (name.includes('dora') || name.includes('digital operational resilience act')) return doraLogo;
    if (name.includes('ftc') || name.includes('safeguards') || name.includes('federal trade commission')) return ftcSafeguardsLogo;
    if (name.includes('cobit')) return cobit2019Logo;
    return null;
};

const OrgAdminDashboard: React.FC = () => {
    const [, setLocation] = useLocation();
    const {
        metrics,
        pieChartData,
        frameworks,
        assessments,
        policyRiskAnalytics,
        loading,
        fetchDashboardMetrics,
        fetchPieChartData,
        fetchFrameworks,
        fetchAssessments,
        fetchPolicyRiskAnalytics
    } = useDashboardStore();

    const { pendingUsers, fetchPendingUsers } = useAdminAreaStore();
    const { openWizard, resetOnboarding } = useOnboardingStore();

    const handleRunSetupWizard = async () => {
        await resetOnboarding();
        openWizard();
    };

    useEffect(() => {
        fetchDashboardMetrics();
        fetchPieChartData();
        fetchFrameworks();
        fetchAssessments();
        fetchPolicyRiskAnalytics();
        fetchPendingUsers();
    }, [fetchDashboardMetrics, fetchPieChartData, fetchFrameworks, fetchAssessments, fetchPolicyRiskAnalytics, fetchPendingUsers]);

    // Calculate metrics
    const activeAssessments = assessments.filter(a => !a.completed);
    const completedAssessments = assessments.filter(a => a.completed);
    const openRisks = policyRiskAnalytics.riskStatusDistribution?.find(r => r.status.toLowerCase() === 'open')?.count || 0;

    // Calculate framework progress
    const frameworkProgress = frameworks.map(framework => {
        const frameworkAssessments = assessments.filter(a => a.framework_id === framework.id);
        const avgProgress = frameworkAssessments.length > 0
            ? frameworkAssessments.reduce((sum, a) => sum + a.progress, 0) / frameworkAssessments.length
            : 0;
        return {
            ...framework,
            progress: avgProgress,
            assessmentCount: frameworkAssessments.length
        };
    });

    const pendingUserColumns = [
        {
            title: 'User',
            dataIndex: 'email',
            key: 'email',
            render: (email: string) => (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Avatar size="small" icon={<UserOutlined />} style={{ backgroundColor: '#0f386a' }} />
                    {email}
                </div>
            )
        },
        {
            title: 'Role',
            dataIndex: 'role_name',
            key: 'role_name',
            render: (role: string) => (
                <span style={{
                    padding: '4px 12px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 500,
                    backgroundColor: '#f5f3ff',
                    color: '#8b5cf6'
                }}>
                    {role?.replace('_', ' ')}
                </span>
            )
        },
        {
            title: 'Requested',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => new Date(date).toLocaleDateString()
        },
        {
            title: 'Action',
            key: 'action',
            render: () => (
                <button
                    className="view-button"
                    onClick={() => setLocation('/admin')}
                    style={{ padding: '4px 12px', fontSize: '12px', height: 'auto' }}
                >
                    Review
                </button>
            )
        }
    ];

    return (
        <>
            {/* CyberBridge Tour */}
            <div style={{ marginBottom: '24px' }}>
                <CyberBridgeTourPanel />
            </div>

            {/* Stat Cards */}
            <div data-tour-id="stat-cards" className="stat-cards-grid" style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', marginBottom: '24px' }}>
                <StatCard
                    title="Team Members"
                    value={metrics.totalUsers}
                    icon={<TeamOutlined />}
                    iconColor="#0f386a"
                    iconBgColor="#EBF4FC"
                    onClick={() => setLocation('/user_management')}
                    loading={loading}
                />
                <StatCard
                    title="Active Assessments"
                    value={activeAssessments.length}
                    icon={<FormOutlined />}
                    iconColor="#8b5cf6"
                    iconBgColor="#f5f3ff"
                    onClick={() => setLocation('/assessments')}
                    loading={loading}
                />
                <StatCard
                    title="Pending Approvals"
                    value={pendingUsers.length}
                    icon={<ClockCircleOutlined />}
                    iconColor="#f59e0b"
                    iconBgColor="#fffbeb"
                    onClick={() => setLocation('/admin')}
                    loading={loading}
                />
                <StatCard
                    title="Completed Assessments"
                    value={completedAssessments.length}
                    icon={<CheckCircleOutlined />}
                    iconColor="#10b981"
                    iconBgColor="#f0fdfa"
                    onClick={() => setLocation('/assessments')}
                    loading={loading}
                />
                <StatCard
                    title="Total Policies"
                    value={metrics.totalPolicies}
                    icon={<FileProtectOutlined />}
                    iconColor="#06b6d4"
                    iconBgColor="#ecfeff"
                    onClick={() => setLocation('/policies_registration')}
                    loading={loading}
                />
                <StatCard
                    title="Open Risks"
                    value={openRisks}
                    icon={<AlertOutlined />}
                    iconColor="#dc2626"
                    iconBgColor="#fef2f2"
                    onClick={() => setLocation('/risk_registration')}
                    loading={loading}
                />
            </div>

            {/* Quick Actions */}
            <div data-tour-id="quick-actions">
            <QuickActionsPanel title="Quick Actions">
                <QuickActionButton
                    label="Start Assessment"
                    icon={<PlusOutlined />}
                    onClick={() => setLocation('/assessments')}
                    variant="primary"
                />
                <QuickActionButton
                    label="Approve Users"
                    icon={<UserAddOutlined />}
                    onClick={() => setLocation('/admin')}
                    variant="warning"
                />
                <QuickActionButton
                    label="Manage Frameworks"
                    icon={<AppstoreOutlined />}
                    onClick={() => setLocation('/framework_management')}
                    variant="secondary"
                />
                <QuickActionButton
                    label="View Objectives"
                    icon={<CheckSquareOutlined />}
                    onClick={() => setLocation('/objectives_checklist')}
                    variant="success"
                />
                <QuickActionButton
                    label="Run Setup Wizard"
                    icon={<RocketOutlined />}
                    onClick={handleRunSetupWizard}
                    variant="secondary"
                />
            </QuickActionsPanel>
            </div>

            {/* Pending Approvals */}
            {pendingUsers.length > 0 && (
                <DashboardSection title="Pending User Approvals" style={{ marginTop: '24px' }}>
                    <Table
                        columns={pendingUserColumns}
                        dataSource={pendingUsers.slice(0, 5).map((u: PendingUser) => ({ ...u, key: u.id }))}
                        pagination={false}
                        size="small"
                    />
                    {pendingUsers.length > 5 && (
                        <div style={{ textAlign: 'center', marginTop: '12px' }}>
                            <button
                                className="view-button"
                                onClick={() => setLocation('/admin')}
                            >
                                View All ({pendingUsers.length})
                            </button>
                        </div>
                    )}
                </DashboardSection>
            )}

            {/* Framework Progress */}
            <DashboardSection title="Framework Progress" style={{ marginTop: '24px' }}>
                <div style={{ overflowX: 'auto', paddingBottom: '16px' }}>
                    <div style={{ display: 'flex', gap: '20px', minWidth: `${frameworks.length * 250}px` }}>
                        {frameworkProgress.length > 0 ? (
                            frameworkProgress.map((framework, index) => {
                                const logo = getFrameworkLogo(framework.name);
                                const colors = [
                                    ['#0f386a', '#EBF4FC'],
                                    ['#10b981', '#f0fdfa'],
                                    ['#f59e0b', '#fffbeb'],
                                    ['#8b5cf6', '#f5f3ff'],
                                    ['#06b6d4', '#ecfeff'],
                                    ['#dc2626', '#fef2f2']
                                ];
                                const colorIndex = index % colors.length;

                                return (
                                    <div
                                        key={framework.id}
                                        className="ant-card"
                                        onClick={() => setLocation('/assessments')}
                                        style={{
                                            minWidth: '240px',
                                            flex: '0 0 240px',
                                            padding: '20px',
                                            cursor: 'pointer',
                                            transition: 'all 0.3s ease'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.currentTarget.style.transform = 'translateY(-4px)';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.currentTarget.style.transform = 'translateY(0)';
                                        }}
                                    >
                                        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                                            {logo && (
                                                <img
                                                    src={logo}
                                                    alt={`${framework.name} logo`}
                                                    style={{
                                                        width: '32px',
                                                        height: '32px',
                                                        objectFit: 'contain',
                                                        marginRight: '12px'
                                                    }}
                                                />
                                            )}
                                            <div style={{ flex: 1, minWidth: 0 }}>
                                                <h5 style={{
                                                    margin: '0',
                                                    fontSize: '14px',
                                                    fontWeight: '600',
                                                    color: '#262626',
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    whiteSpace: 'nowrap'
                                                }}>
                                                    {framework.name}
                                                </h5>
                                                <p style={{
                                                    margin: '2px 0 0 0',
                                                    fontSize: '12px',
                                                    color: '#8c8c8c'
                                                }}>
                                                    {framework.assessmentCount} assessments
                                                </p>
                                            </div>
                                        </div>
                                        <Chart
                                            chartType="PieChart"
                                            data={[
                                                ["Status", "Percentage"],
                                                ["Progress", parseFloat(framework.progress.toFixed(1))],
                                                ["Remaining", parseFloat((100 - framework.progress).toFixed(1))]
                                            ]}
                                            options={{
                                                legend: { position: 'none' },
                                                colors: colors[colorIndex],
                                                backgroundColor: 'transparent',
                                                pieHole: 0.6,
                                                chartArea: { width: '100%', height: '80%' },
                                                pieSliceText: 'none',
                                                tooltip: { trigger: 'none' }
                                            }}
                                            width="200px"
                                            height="120px"
                                        />
                                        <div style={{ textAlign: 'center', marginTop: '8px' }}>
                                            <p style={{
                                                margin: '0',
                                                fontSize: '20px',
                                                fontWeight: '700',
                                                color: colors[colorIndex][0]
                                            }}>
                                                {framework.progress.toFixed(1)}%
                                            </p>
                                        </div>
                                    </div>
                                );
                            })
                        ) : (
                            <Empty
                                description="No frameworks available"
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                            />
                        )}
                    </div>
                </div>
            </DashboardSection>

            {/* Charts Section */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '24px' }}>
                <DashboardSection title="Assessment Status" style={{ flex: '1 1 400px' }}>
                    <Chart
                        chartType="PieChart"
                        data={[
                            ["Status", "Count"],
                            ["Completed", pieChartData.completed || 0],
                            ["In Progress", pieChartData.inProgress || 0]
                        ]}
                        options={{
                            legend: { position: 'bottom', textStyle: { fontSize: 12 } },
                            colors: ['#10b981', '#0f386a'],
                            backgroundColor: 'transparent',
                            pieHole: 0.5,
                            chartArea: { width: '85%', height: '70%' },
                            pieSliceTextStyle: { color: '#ffffff' },
                            pieSliceBorderColor: 'transparent'
                        }}
                        width="100%"
                        height="280px"
                        loader={<div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>Loading...</div>}
                    />
                </DashboardSection>

                <DashboardSection title="Risk Severity Distribution" style={{ flex: '1 1 400px' }}>
                    {policyRiskAnalytics.riskSeverityDistribution?.length > 0 ? (
                        <Chart
                            chartType="PieChart"
                            data={[
                                ["Severity", "Count"],
                                ...policyRiskAnalytics.riskSeverityDistribution.map(item => [item.severity, item.count])
                            ]}
                            options={{
                                legend: { position: 'bottom', textStyle: { fontSize: 12 } },
                                colors: ['#dc2626', '#f59e0b', '#fde68a', '#10b981'],
                                backgroundColor: 'transparent',
                                chartArea: { width: '85%', height: '70%' },
                                pieSliceTextStyle: { color: '#ffffff' },
                                pieSliceBorderColor: 'transparent'
                            }}
                            width="100%"
                            height="280px"
                            loader={<div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>Loading...</div>}
                        />
                    ) : (
                        <Empty
                            description="No risk data available"
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                        />
                    )}
                </DashboardSection>
            </div>
        </>
    );
};

export default OrgAdminDashboard;
