// src/pages/dashboards/OrgUserDashboard.tsx
import React, { useEffect } from 'react';
import { useLocation } from 'wouter';
import { Table, Progress, Empty } from 'antd';
import { Chart } from 'react-google-charts';
import {
    FormOutlined,
    CheckCircleOutlined,
    FileProtectOutlined,
    FileSearchOutlined,
    PlusOutlined,
    EyeOutlined,
    CheckSquareOutlined,
    UploadOutlined,
    PlayCircleOutlined,
    RocketOutlined
} from '@ant-design/icons';
import { StatCard, QuickActionButton, QuickActionsPanel, DashboardSection, CyberBridgeTourPanel } from '../../components/dashboard';
import { UserOnboardingWizard } from '../../components/user-onboarding';
import useDashboardStore from '../../store/useDashboardStore';
import useUserOnboardingStore from '../../store/useUserOnboardingStore';

const OrgUserDashboard: React.FC = () => {
    const [, setLocation] = useLocation();
    const {
        metrics,
        pieChartData,
        assessments,
        policyRiskAnalytics,
        loading,
        fetchDashboardMetrics,
        fetchPieChartData,
        fetchAssessments,
        fetchPolicyRiskAnalytics
    } = useDashboardStore();

    const {
        onboardingStatus,
        checkOnboardingStatus,
        openWizard,
        resetOnboarding
    } = useUserOnboardingStore();

    useEffect(() => {
        fetchDashboardMetrics();
        fetchPieChartData();
        fetchAssessments();
        fetchPolicyRiskAnalytics();
    }, [fetchDashboardMetrics, fetchPieChartData, fetchAssessments, fetchPolicyRiskAnalytics]);

    // Check user onboarding status on mount
    useEffect(() => {
        const checkStatus = async () => {
            const status = await checkOnboardingStatus();
            // Auto-open wizard for users who haven't completed onboarding
            if (status && !status.user_onboarding_completed && !status.user_onboarding_skipped) {
                openWizard();
            }
        };
        checkStatus();
    }, [checkOnboardingStatus, openWizard]);

    const handleRunSetupWizard = () => {
        resetOnboarding();
        openWizard();
    };

    // Calculate user-specific metrics
    const activeAssessments = assessments.filter(a => !a.completed);
    const completedAssessments = assessments.filter(a => a.completed);

    // Get compliance status from policy analytics
    const complianceData = policyRiskAnalytics.policyStatusDistribution || [];

    const assessmentColumns = [
        {
            title: 'Assessment',
            dataIndex: 'name',
            key: 'name',
            ellipsis: true
        },
        {
            title: 'Framework',
            dataIndex: 'framework',
            key: 'framework',
            ellipsis: true
        },
        {
            title: 'Progress',
            dataIndex: 'progress',
            key: 'progress',
            width: 150,
            render: (progress: number) => (
                <Progress
                    percent={Math.round(progress)}
                    size="small"
                    strokeColor={{
                        '0%': '#0f386a',
                        '100%': '#10b981'
                    }}
                />
            )
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: 120,
            render: (status: string) => (
                <span style={{
                    padding: '4px 12px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 500,
                    backgroundColor: status === 'Completed' ? '#f0fdfa' : '#EBF4FC',
                    color: status === 'Completed' ? '#059669' : '#0f386a'
                }}>
                    {status}
                </span>
            )
        },
        {
            title: 'Action',
            key: 'action',
            width: 100,
            render: (_: any, record: any) => (
                <button
                    className="view-button"
                    onClick={() => setLocation(`/assessments`)}
                    style={{
                        padding: '6px 12px',
                        fontSize: '12px',
                        height: 'auto'
                    }}
                >
                    <PlayCircleOutlined style={{ marginRight: '4px' }} />
                    {record.completed ? 'View' : 'Continue'}
                </button>
            )
        }
    ];

    return (
        <>
            {/* User Onboarding Wizard */}
            <UserOnboardingWizard />

            {/* CyberBridge Tour */}
            <div style={{ marginBottom: '24px' }}>
                <CyberBridgeTourPanel />
            </div>

            {/* Stat Cards */}
            <div data-tour-id="stat-cards" className="stat-cards-grid" style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', marginBottom: '24px' }}>
                <StatCard
                    title="My Active Assessments"
                    value={activeAssessments.length}
                    icon={<FormOutlined />}
                    iconColor="#0f386a"
                    iconBgColor="#EBF4FC"
                    onClick={() => setLocation('/assessments')}
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
                    iconColor="#f59e0b"
                    iconBgColor="#fffbeb"
                    onClick={() => setLocation('/policies_registration')}
                    loading={loading}
                />
                <StatCard
                    title="Active Frameworks"
                    value={metrics.complianceFrameworks}
                    icon={<FileSearchOutlined />}
                    iconColor="#8b5cf6"
                    iconBgColor="#f5f3ff"
                    onClick={() => setLocation('/framework_management')}
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
                    label="View Policies"
                    icon={<EyeOutlined />}
                    onClick={() => setLocation('/policies_registration')}
                    variant="secondary"
                />
                <QuickActionButton
                    label="Check Objectives"
                    icon={<CheckSquareOutlined />}
                    onClick={() => setLocation('/objectives_checklist')}
                    variant="success"
                />
                <QuickActionButton
                    label="Upload Evidence"
                    icon={<UploadOutlined />}
                    onClick={() => setLocation('/evidence')}
                    variant="warning"
                />
                <QuickActionButton
                    label="Run Setup Wizard"
                    icon={<RocketOutlined />}
                    onClick={handleRunSetupWizard}
                    variant="secondary"
                />
            </QuickActionsPanel>
            </div>

            {/* My Active Assessments */}
            <DashboardSection title="My Active Assessments" style={{ marginTop: '24px' }}>
                {activeAssessments.length > 0 ? (
                    <Table
                        columns={assessmentColumns}
                        dataSource={activeAssessments.map(a => ({ ...a, key: a.id }))}
                        pagination={{ pageSize: 5 }}
                        loading={loading}
                        size="small"
                    />
                ) : (
                    <Empty
                        description="No active assessments"
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                    >
                        <button
                            className="add-button"
                            onClick={() => setLocation('/assessments')}
                        >
                            Start Your First Assessment
                        </button>
                    </Empty>
                )}
            </DashboardSection>

            {/* Progress Charts */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '24px' }}>
                <DashboardSection title="Assessment Progress" style={{ flex: '1 1 400px' }}>
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

                <DashboardSection title="Policy Status" style={{ flex: '1 1 400px' }}>
                    {complianceData.length > 0 ? (
                        <Chart
                            chartType="PieChart"
                            data={[
                                ["Status", "Count"],
                                ...complianceData.map(item => [item.status, item.count])
                            ]}
                            options={{
                                legend: { position: 'bottom', textStyle: { fontSize: 12 } },
                                colors: ['#10b981', '#fde68a', '#f87171', '#93c5fd'],
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
                            description="No policy data available"
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                        />
                    )}
                </DashboardSection>
            </div>

            {/* Recently Completed */}
            {completedAssessments.length > 0 && (
                <DashboardSection title="Recently Completed Assessments">
                    <Table
                        columns={assessmentColumns.filter(c => c.key !== 'action')}
                        dataSource={completedAssessments.slice(0, 5).map(a => ({ ...a, key: a.id }))}
                        pagination={false}
                        loading={loading}
                        size="small"
                    />
                </DashboardSection>
            )}
        </>
    );
};

export default OrgUserDashboard;
