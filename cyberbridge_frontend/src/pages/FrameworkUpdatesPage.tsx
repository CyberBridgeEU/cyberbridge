import React, {useEffect, useState} from 'react';
import {Select, notification, Alert, Button, Space} from "antd";
import {SyncOutlined, RadarChartOutlined, ReloadOutlined, ExperimentOutlined} from "@ant-design/icons";
import Sidebar from "../components/Sidebar.tsx";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import useUserStore from "../store/useUserStore.ts";
import useRegulatoryMonitorStore from "../store/useRegulatoryMonitorStore.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import FrameworkUpdatesSection from "../components/FrameworkUpdatesSection.tsx";
import RegulatoryChangesSection from "../components/RegulatoryChangesSection.tsx";
import SnapshotTimeline from "../components/SnapshotTimeline.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const FrameworkUpdatesPage: React.FC = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Global State
    const {frameworks, fetchFrameworks} = useFrameworksStore();
    const {current_user} = useUserStore();
    const {
        notification: regNotification,
        fetchNotifications,
        triggerLLMAnalysis,
        analyzing,
        triggerScan,
        cancelAnalysis
    } = useRegulatoryMonitorStore();

    // Local State
    const [frameworkSelectedId, setFrameworkSelectedId] = useState<string>('');
    const [analysisFramework, setAnalysisFramework] = useState<string | null>(null);
    const [api, contextHolder] = notification.useNotification();
    const [scanTriggering, setScanTriggering] = useState(false);
    const [analysisCancelled, setAnalysisCancelled] = useState(false);

    // On Component Mount
    // Fetch frameworks on mount
    useEffect(() => {
        fetchFrameworks();
    }, []);

    // Fetch regulatory notifications once user is loaded
    useEffect(() => {
        if (current_user?.role_name === 'super_admin' || current_user?.role_name === 'org_admin') {
            fetchNotifications();
        }
    }, [current_user?.role_name]);

    // Framework options
    const options = frameworks.map(framework => ({
        value: framework.id,
        label: framework.organisation_domain ? `${framework.name} (${framework.organisation_domain})` : framework.name,
    }));

    // Handle framework change
    const handleFrameworkChange = (value: string) => {
        setFrameworkSelectedId(value);
    };

    // Handle LLM analysis trigger
    const handleAnalyze = async () => {
        if (!regNotification?.scan_run_id || !analysisFramework) return;
        setAnalysisCancelled(false);
        api.info({
            message: 'LLM Analysis Started',
            description: `Analyzing regulatory changes for ${analysisFramework.toUpperCase()}. This may take a minute...`,
            duration: 5
        });
        const result = await triggerLLMAnalysis(regNotification.scan_run_id, analysisFramework);
        if (analysisCancelled) return; // User cancelled
        if (result) {
            if (result.status === 'completed') {
                api.success({
                    message: 'LLM Analysis Complete',
                    description: `Found ${result.changes_count} regulatory changes for ${analysisFramework.toUpperCase()}`,
                });
                fetchNotifications();
            } else if (result.status === 'llm_error') {
                api.warning({
                    message: 'LLM Analysis Failed',
                    description: result.message || 'Automatic analysis failed. Check LLM service.',
                    duration: 10
                });
            } else {
                api.info({
                    message: 'No Changes Found',
                    description: `No regulatory changes detected for ${analysisFramework.toUpperCase()}`,
                });
            }
        } else {
            if (!analysisCancelled) {
                api.error({ message: 'Analysis Failed', description: 'Failed to run LLM analysis' });
            }
        }
    };

    // Handle cancel — aborts the fetch request via AbortController
    const handleCancelAnalysis = () => {
        setAnalysisCancelled(true);
        cancelAnalysis();
        api.info({ message: 'Analysis Cancelled', description: 'LLM analysis request was cancelled.' });
    };

    // Handle manual scan trigger
    const handleTriggerScan = async () => {
        setScanTriggering(true);
        const success = await triggerScan();
        setScanTriggering(false);
        if (success) {
            api.success({ message: 'Scan Complete', description: 'Regulatory web scan completed successfully' });
            fetchNotifications();
        } else {
            api.error({ message: 'Scan Failed', description: 'Failed to run regulatory scan' });
        }
    };

    const isAdmin = current_user?.role_name === 'super_admin' || current_user?.role_name === 'org_admin';

    return (
        <div>
            {contextHolder}
            <div className={'page-parent'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
                <div className="page-content">

                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <SyncOutlined style={{ fontSize: 22, color: '#1a365d' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Framework Updates</h1>
                        </div>
                        {current_user?.role_name === 'super_admin' && (
                            <div className="page-header-right">
                                <Button
                                    icon={<ReloadOutlined />}
                                    onClick={handleTriggerScan}
                                    loading={scanTriggering}
                                    style={{ background: '#1a365d', color: '#fff', borderColor: '#1a365d' }}
                                >
                                    Run Regulatory Scan
                                </Button>
                            </div>
                        )}
                    </div>

                    {/* Regulatory Monitor Notification Box */}
                    {isAdmin && regNotification?.has_findings && (
                        <div className="page-section">
                            <Alert
                                type="info"
                                showIcon
                                icon={<RadarChartOutlined />}
                                message="Regulatory changes detected"
                                description={
                                    <div>
                                        <p style={{ margin: '4px 0' }}>
                                            Last scan: {regNotification.scan_date
                                                ? new Date(regNotification.scan_date).toLocaleString()
                                                : 'N/A'}
                                        </p>
                                        <p style={{ margin: '4px 0' }}>
                                            New findings for: {regNotification.frameworks.join(', ').toUpperCase()}
                                        </p>
                                        {Object.keys(regNotification.pending_changes).length > 0 && (
                                            <p style={{ margin: '4px 0', color: '#faad14' }}>
                                                Pending review: {Object.entries(regNotification.pending_changes)
                                                    .map(([fw, info]) => `${fw.toUpperCase()} (${(info as any).count})`)
                                                    .join(', ')}
                                            </p>
                                        )}
                                        <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
                                            <Select
                                                placeholder="Select framework to analyze"
                                                value={analysisFramework || undefined}
                                                onChange={(value) => setAnalysisFramework(value)}
                                                style={{ width: 300 }}
                                                options={regNotification.frameworks.map(fw => ({
                                                    value: fw,
                                                    label: fw.toUpperCase().replace(/_/g, ' ')
                                                }))}
                                                disabled={analyzing}
                                            />
                                            <Button
                                                type="primary"
                                                icon={<ExperimentOutlined />}
                                                onClick={handleAnalyze}
                                                loading={analyzing}
                                                disabled={!analysisFramework || analyzing}
                                                style={{ background: '#1a365d', borderColor: '#1a365d' }}
                                            >
                                                Start LLM Analysis
                                            </Button>
                                            {analyzing && (
                                                <Button
                                                    danger
                                                    onClick={handleCancelAnalysis}
                                                >
                                                    Cancel
                                                </Button>
                                            )}
                                        </div>
                                    </div>
                                }
                                style={{ marginBottom: 0 }}
                            />
                        </div>
                    )}

                    {/* Framework Selection */}
                    <div className="page-section">
                        <div className="form-row">
                            <div className="form-group" style={{ flex: 1 }}>
                                <label className="form-label">Select Framework</label>
                                <Select
                                    className="framework-dropdown"
                                    placeholder="Select a framework to view its updates"
                                    onChange={handleFrameworkChange}
                                    options={options}
                                    value={frameworkSelectedId || undefined}
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Framework Updates Section */}
                    <div className="page-section">
                        <InfoTitle
                            title="Available Updates"
                            infoContent="Manage and apply updates to framework questions, chapters, and objectives. Updates preserve all existing data including policies, assessments, and user responses."
                            className="section-title"
                        />
                        <p className="section-subtitle">
                            View available updates and apply them to keep your frameworks current with the latest requirements
                        </p>

                        {frameworkSelectedId ? (
                            <FrameworkUpdatesSection
                                frameworkId={frameworkSelectedId}
                                userRole={current_user?.role_name}
                            />
                        ) : (
                            <div style={{
                                padding: '40px 20px',
                                textAlign: 'center',
                                background: '#fafafa',
                                borderRadius: '8px',
                                border: '1px dashed #d9d9d9'
                            }}>
                                <SyncOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
                                <p style={{ color: '#8c8c8c', fontSize: '14px', margin: 0 }}>
                                    Please select a framework to view and manage its updates
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Regulatory Changes Section */}
                    {isAdmin && frameworkSelectedId && (
                        <div className="page-section">
                            <RegulatoryChangesSection
                                frameworkId={frameworkSelectedId}
                                userRole={current_user?.role_name}
                            />
                        </div>
                    )}

                    {/* Snapshots & History Section */}
                    {isAdmin && frameworkSelectedId && (
                        <div className="page-section">
                            <SnapshotTimeline
                                frameworkId={frameworkSelectedId}
                            />
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
};

export default FrameworkUpdatesPage;
