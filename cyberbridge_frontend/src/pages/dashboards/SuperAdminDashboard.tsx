// src/pages/dashboards/SuperAdminDashboard.tsx
import React, { useEffect } from 'react';
import { useLocation } from 'wouter';
import { Table, Empty, Avatar, Tag } from 'antd';
import { Chart } from 'react-google-charts';
import {
    TeamOutlined,
    UserOutlined,
    ClockCircleOutlined,
    AppstoreOutlined,
    FileProtectOutlined,
    AlertOutlined,
    UserAddOutlined,
    BankOutlined,
    SettingOutlined,
    NodeIndexOutlined,
    RocketOutlined
} from '@ant-design/icons';
import { StatCard, QuickActionButton, QuickActionsPanel, DashboardSection, CyberBridgeTourPanel } from '../../components/dashboard';
import { SuperAdminOnboardingWizard } from '../../components/superadmin-onboarding';
import useDashboardStore from '../../store/useDashboardStore';
import { useAdminAreaStore, PendingUser } from '../../store/adminAreaStore';
import useSuperAdminOnboardingStore from '../../store/useSuperAdminOnboardingStore';

const SuperAdminDashboard: React.FC = () => {
    const [, setLocation] = useLocation();
    const {
        metrics,
        userAnalytics,
        policyRiskAnalytics,
        assessmentAnalytics,
        loading,
        fetchDashboardMetrics,
        fetchUserAnalytics,
        fetchPolicyRiskAnalytics,
        fetchAssessmentAnalytics
    } = useDashboardStore();

    const { pendingUsers, fetchPendingUsers } = useAdminAreaStore();
    const {
        onboardingStatus,
        checkOnboardingStatus,
        openWizard,
        resetOnboarding
    } = useSuperAdminOnboardingStore();

    const handleRunSetupWizard = () => {
        resetOnboarding();
        openWizard();
    };

    useEffect(() => {
        fetchDashboardMetrics();
        fetchUserAnalytics();
        fetchPolicyRiskAnalytics();
        fetchAssessmentAnalytics();
        fetchPendingUsers();
    }, [fetchDashboardMetrics, fetchUserAnalytics, fetchPolicyRiskAnalytics, fetchAssessmentAnalytics, fetchPendingUsers]);

    // Check superadmin onboarding status on mount
    useEffect(() => {
        const checkStatus = async () => {
            const status = await checkOnboardingStatus();
            // Auto-open wizard for superadmins who haven't completed onboarding
            if (status && !status.superadmin_onboarding_completed && !status.superadmin_onboarding_skipped) {
                openWizard();
            }
        };
        checkStatus();
    }, [checkOnboardingStatus, openWizard]);

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
            title: 'Organization',
            dataIndex: 'organisation_name',
            key: 'organisation_name',
            render: (org: string) => (
                <Tag color="blue">{org || 'N/A'}</Tag>
            )
        },
        {
            title: 'Role',
            dataIndex: 'role_name',
            key: 'role_name',
            render: (role: string) => {
                const colorMap: Record<string, string> = {
                    'super_admin': '#dc2626',
                    'org_admin': '#8b5cf6',
                    'org_user': '#10b981'
                };
                return (
                    <span style={{
                        padding: '4px 12px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: 500,
                        backgroundColor: `${colorMap[role] || '#0f386a'}15`,
                        color: colorMap[role] || '#0f386a'
                    }}>
                        {role?.replace('_', ' ')}
                    </span>
                );
            }
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
            {/* Super Admin Onboarding Wizard */}
            <SuperAdminOnboardingWizard />

            {/* CyberBridge Tour */}
            <div style={{ marginBottom: '24px' }}>
                <CyberBridgeTourPanel />
            </div>

            {/* Stat Cards */}
            <div data-tour-id="stat-cards" className="stat-cards-grid" style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', marginBottom: '24px' }}>
                <StatCard
                    title="Total Organizations"
                    value={metrics.totalOrganizations}
                    icon={<TeamOutlined />}
                    iconColor="#0f386a"
                    iconBgColor="#EBF4FC"
                    onClick={() => setLocation('/user_management')}
                    loading={loading}
                />
                <StatCard
                    title="Total Users"
                    value={metrics.totalUsers}
                    icon={<UserOutlined />}
                    iconColor="#8b5cf6"
                    iconBgColor="#f5f3ff"
                    onClick={() => setLocation('/admin')}
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
                    title="Total Frameworks"
                    value={metrics.complianceFrameworks}
                    icon={<AppstoreOutlined />}
                    iconColor="#06b6d4"
                    iconBgColor="#ecfeff"
                    onClick={() => setLocation('/framework_management')}
                    loading={loading}
                />
                <StatCard
                    title="Total Policies"
                    value={metrics.totalPolicies}
                    icon={<FileProtectOutlined />}
                    iconColor="#10b981"
                    iconBgColor="#f0fdfa"
                    onClick={() => setLocation('/policies_registration')}
                    loading={loading}
                />
                <StatCard
                    title="Total Risks"
                    value={metrics.totalRisks}
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
                    label="Approve Users"
                    icon={<UserAddOutlined />}
                    onClick={() => setLocation('/admin')}
                    variant="primary"
                />
                <QuickActionButton
                    label="Manage Organizations"
                    icon={<BankOutlined />}
                    onClick={() => setLocation('/user_management')}
                    variant="secondary"
                />
                <QuickActionButton
                    label="Configuration"
                    icon={<SettingOutlined />}
                    onClick={() => setLocation('/settings')}
                    variant="warning"
                />
                <QuickActionButton
                    label="View Correlations"
                    icon={<NodeIndexOutlined />}
                    onClick={() => setLocation('/correlations')}
                    variant="success"
                />
                <QuickActionButton
                    label="Admin Setup Wizard"
                    icon={<RocketOutlined />}
                    onClick={handleRunSetupWizard}
                    variant="secondary"
                />
            </QuickActionsPanel>
            </div>

            {/* Pending Approvals Across All Organizations */}
            <DashboardSection title="Pending User Approvals (All Organizations)" style={{ marginTop: '24px' }}>
                {pendingUsers.length > 0 ? (
                    <>
                        <Table
                            columns={pendingUserColumns}
                            dataSource={pendingUsers.slice(0, 10).map((u: PendingUser) => ({ ...u, key: u.id }))}
                            pagination={false}
                            size="small"
                        />
                        {pendingUsers.length > 10 && (
                            <div style={{ textAlign: 'center', marginTop: '12px' }}>
                                <button
                                    className="view-button"
                                    onClick={() => setLocation('/admin')}
                                >
                                    View All ({pendingUsers.length})
                                </button>
                            </div>
                        )}
                    </>
                ) : (
                    <Empty
                        description="No pending user approvals"
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                    />
                )}
            </DashboardSection>

            {/* Analytics Charts */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '24px' }}>
                <DashboardSection title="User Role Distribution" style={{ flex: '1 1 400px' }}>
                    {userAnalytics.userRoleDistribution?.length > 0 ? (
                        <Chart
                            chartType="PieChart"
                            data={[
                                ["Role", "Count"],
                                ...userAnalytics.userRoleDistribution.map(item => [item.role.replace('_', ' '), item.count])
                            ]}
                            options={{
                                legend: { position: 'bottom', textStyle: { fontSize: 12 } },
                                colors: ['#0f386a', '#8b5cf6', '#10b981'],
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
                            description="No user role data available"
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                        />
                    )}
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

            {/* Additional Analytics */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '24px' }}>
                <DashboardSection title="User Status Distribution" style={{ flex: '1 1 400px' }}>
                    {userAnalytics.userStatusDistribution?.length > 0 ? (
                        <Chart
                            chartType="ColumnChart"
                            data={[
                                ["Status", "Count", { role: "style" }],
                                ...userAnalytics.userStatusDistribution.map((item, index) => {
                                    const colors = ['#10b981', '#f59e0b', '#dc2626', '#0f386a'];
                                    return [item.status.replace('_', ' '), item.count, colors[index % colors.length]];
                                })
                            ]}
                            options={{
                                legend: { position: 'none' },
                                backgroundColor: 'transparent',
                                chartArea: { width: '80%', height: '70%' },
                                hAxis: { textStyle: { fontSize: 12 } },
                                vAxis: { textStyle: { fontSize: 12 }, minValue: 0 }
                            }}
                            width="100%"
                            height="280px"
                            loader={<div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>Loading...</div>}
                        />
                    ) : (
                        <Empty
                            description="No user status data available"
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                        />
                    )}
                </DashboardSection>

                <DashboardSection title="Policy Status Distribution" style={{ flex: '1 1 400px' }}>
                    {policyRiskAnalytics.policyStatusDistribution?.length > 0 ? (
                        <Chart
                            chartType="PieChart"
                            data={[
                                ["Status", "Count"],
                                ...policyRiskAnalytics.policyStatusDistribution.map(item => [item.status, item.count])
                            ]}
                            options={{
                                legend: { position: 'bottom', textStyle: { fontSize: 12 } },
                                colors: ['#10b981', '#0f386a', '#f59e0b', '#dc2626'],
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
                            description="No policy status data available"
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                        />
                    )}
                </DashboardSection>
            </div>

            {/* Assessment Trends */}
            <DashboardSection title="Assessment Trends">
                {assessmentAnalytics.assessmentTrend?.length > 0 ? (
                    <Chart
                        chartType="LineChart"
                        data={[
                            ["Month", "Completed", "In Progress"],
                            ...assessmentAnalytics.assessmentTrend.map(item => [item.month, item.completed, item.inProgress])
                        ]}
                        options={{
                            legend: { position: 'bottom', textStyle: { fontSize: 12 } },
                            colors: ['#10b981', '#0f386a'],
                            backgroundColor: 'transparent',
                            chartArea: { width: '90%', height: '70%' },
                            hAxis: { textStyle: { fontSize: 11 } },
                            vAxis: { textStyle: { fontSize: 11 }, minValue: 0 },
                            curveType: 'function',
                            pointSize: 6,
                            lineWidth: 3
                        }}
                        width="100%"
                        height="350px"
                        loader={<div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>Loading...</div>}
                    />
                ) : (
                    <Empty
                        description="No assessment trend data available"
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                    />
                )}
            </DashboardSection>
        </>
    );
};

export default SuperAdminDashboard;
