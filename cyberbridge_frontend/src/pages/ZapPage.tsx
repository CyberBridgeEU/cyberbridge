import { notification, Select, SelectProps, Progress, Table, Tag, Card, Collapse, List, Divider, Button, Modal } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { useEffect, useState } from "react";
import useZapStore from "../store/useZapStore.ts";
import useAuthStore from "../store/useAuthStore.ts";
import useSettingsStore from "../store/useSettingsStore.ts";
import useUserStore from "../store/useUserStore.ts";
import { ZapGridColumns, prepareZapTableData } from "../constants/ZapGridColumns.tsx";
import { ScannerHistoryGridColumns, prepareHistoryTableData, ScannerHistoryRecord } from "../constants/ScannerHistoryGridColumns.tsx";
import { ExclamationCircleOutlined, LayoutOutlined, SyncOutlined, DeleteOutlined, RightOutlined, DownOutlined, RobotOutlined } from '@ant-design/icons';
import { exportZapResultsToPdf } from "../utils/zapPdfUtils.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import { WebAppScannerInfo } from "../constants/infoContent.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import {
    saveScannerHistory,
    fetchScannerHistory,
    fetchScannerHistoryDetails,
    fetchCurrentUserDetails,
    parseHistoryResults,
    clearScannerHistory
} from "../utils/scannerHistoryUtils.ts";
import RemediationModal from "../components/RemediationModal.tsx";

const { Panel } = Collapse;

const ZapPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Get functions and state from the store
    const {
        targetUrl,
        scanType,
        scanStatus,
        activeScanState,
        alerts,
        loading,
        polling,
        error,
        setTargetUrl,
        setScanType,
        startSpiderScan,
        startActiveScan,
        startFullScan,
        startApiScan,
        clearResults,
        clearAlerts,
        emergencyStop
    } = useZapStore();

    const { user } = useAuthStore();
    const { current_user } = useUserStore();
    const { loadAIFeatureSettings, aiFeatureSettings } = useSettingsStore();

    // State for scan control modals
    const [emergencyStopModalVisible, setEmergencyStopModalVisible] = useState(false);

    // State for AI Remediator
    const [remediationModalVisible, setRemediationModalVisible] = useState(false);
    const [selectedHistoryForRemediation, setSelectedHistoryForRemediation] = useState<{ id: string; target: string } | null>(null);

    // Scanner history state
    const [scannerHistory, setScannerHistory] = useState<ScannerHistoryRecord[]>([]);
    const [historyLoading, setHistoryLoading] = useState(false);
    const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([]);

    // Track when scan starts for duration calculation
    const [scanStartTime, setScanStartTime] = useState<number | null>(null);

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    // Display error notifications when they occur
    useEffect(() => {
        if (error) {
            api.error({
                message: 'Scan Failed',
                description: error,
                duration: 4,
            });
        }
    }, [error, api]);

    // Load scanner history on mount
    useEffect(() => {
        loadScannerHistory();
    }, []);

    // Load AI feature settings
    useEffect(() => {
        if (current_user?.organisation_id) {
            loadAIFeatureSettings(current_user.organisation_id);
        }
    }, [current_user?.organisation_id, loadAIFeatureSettings]);

    // Save history when scan completes
    useEffect(() => {
        const saveHistoryOnCompletion = async () => {
            // Simplified logic: save when scan completes and alerts are available
            if (alerts.length > 0 && !polling && user?.email && scanStartTime) {
                const duration = (Date.now() - scanStartTime) / 1000;
                const userDetails = await fetchCurrentUserDetails(user.email);

                if (userDetails) {
                    await saveScannerHistory(
                        {
                            scanner_type: 'zap',
                            scan_target: targetUrl,
                            scan_type: scanType,
                            results: alerts,
                            status: 'completed',
                            scan_duration: duration
                        },
                        userDetails.email,
                        userDetails.id,
                        userDetails.organisation_id,
                        userDetails.organisation_name
                    );
                    api.success({
                        message: 'History Saved',
                        description: 'Scan results have been saved to history.',
                        duration: 3
                    });
                    loadScannerHistory();
                }
                setScanStartTime(null);
            }
        };

        saveHistoryOnCompletion();
    }, [alerts, polling, user, scanStartTime, targetUrl, scanType, api]);

    // Track when scan starts
    useEffect(() => {
        if (polling && !scanStartTime) {
            setScanStartTime(Date.now());
        }
    }, [polling, scanStartTime]);

    // Load scanner history
    const loadScannerHistory = async () => {
        setHistoryLoading(true);
        try {
            const history = await fetchScannerHistory('zap', 100);
            setScannerHistory(history);
        } catch (error) {
            console.error('Error loading scanner history:', error);
        } finally {
            setHistoryLoading(false);
        }
    };

    // Toggle expanded row
    const handleToggleExpand = (recordKey: string) => {
        setExpandedRowKeys(prev =>
            prev.includes(recordKey)
                ? prev.filter(key => key !== recordKey)
                : [...prev, recordKey]
        );
    };

    // Clear all scanner history
    const handleClearHistory = async () => {
        const confirmed = window.confirm(
            'Are you sure you want to delete all Web App scan history records?\n\nThis action cannot be undone.'
        );

        if (confirmed) {
            setHistoryLoading(true);
            const result = await clearScannerHistory('zap');

            if (result.success) {
                api.success({
                    message: 'History Cleared',
                    description: `Successfully deleted ${result.deletedCount || 0} record(s).`,
                    duration: 4
                });
                loadScannerHistory();
            } else {
                api.error({
                    message: 'Clear Failed',
                    description: result.error || 'Failed to clear history.',
                    duration: 4
                });
            }

            setHistoryLoading(false);
        }
    };

    // Handle AI Remediator button click
    const handleOpenRemediation = (record: ScannerHistoryRecord) => {
        setSelectedHistoryForRemediation({
            id: record.id,
            target: record.scan_target
        });
        setRemediationModalVisible(true);
    };

    // Handle export history record to PDF
    const handleExportHistory = async (record: ScannerHistoryRecord) => {
        try {
            // Fetch full record details (results not included in history list)
            const details = await fetchScannerHistoryDetails(record.id);
            if (!details?.results) {
                api.error({ message: 'Export Failed', description: 'No scan results available for this record.', duration: 4 });
                return;
            }
            const alerts = parseHistoryResults(details.results);

            // Generate filename with timestamp
            const timestamp = new Date(record.timestamp).toISOString().replace(/[:.]/g, '-').slice(0, 19);
            const filename = `webapp-scan-${record.scan_target.replace(/[^a-z0-9]/gi, '_')}-${timestamp}`;

            // Export to PDF
            await exportZapResultsToPdf(alerts, record.scan_target, filename);

            api.success({
                message: 'Export Successful',
                description: 'Scan results have been exported to PDF.',
                duration: 3
            });
        } catch (error) {
            console.error('Error exporting to PDF:', error);
            api.error({
                message: 'Export Failed',
                description: 'Failed to export scan results to PDF.',
                duration: 4
            });
        }
    };

    // Options for the scan type dropdown
    const scanOptions = [
        { value: 'spider', label: 'Spider Scan (Crawl Only)' },
        { value: 'active', label: 'Active Scan (Attack Only)' },
        { value: 'full', label: 'Full Scan (Crawl & Attack)' },
        { value: 'api', label: 'API Scan' }
    ];

    // Filter function for the select dropdown
    const filterOption: SelectProps['filterOption'] = (input, option) =>
        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase());

    // Handle scan type change
    const handleScanTypeChange = (value: string) => {
        setScanType(value);

        // Show legal warning for full and active scans
        if (value === 'full' || value === 'active') {
            api.warning({
                message: 'Legal Considerations',
                description: `${value === 'full' ? 'Full scans' : 'Active scans'} perform security attacks against the target system. Ensure you have explicit written authorization to test this target. Unauthorized security testing is illegal and may violate terms of service or local laws.`,
                duration: 8,
                placement: 'topRight'
            });
        }
    };

    // Run the selected scan
    const handleRunScan = async () => {
        if (!targetUrl || targetUrl.trim() === '') {
            api.error({
                message: 'Missing Target',
                description: 'Please enter a target URL.',
                duration: 4,
            });
            return;
        }

        // Show additional legal warning before starting full or active scans
        if (scanType === 'full' || scanType === 'active') {
            api.warning({
                message: 'Security Testing Warning',
                description: `You are about to initiate a ${scanType} scan which includes penetration testing techniques. Only proceed if you have proper authorization. Unauthorized testing may be illegal.`,
                duration: 6,
                placement: 'topRight'
            });
        }

        let success = false;

        switch (scanType) {
            case 'spider':
                success = await startSpiderScan();
                break;
            case 'active':
                success = await startActiveScan();
                break;
            case 'full':
                success = await startFullScan();
                break;
            case 'api':
                success = await startApiScan();
                break;
            default:
                api.error({
                    message: 'Invalid Scan Type',
                    description: 'Please select a valid scan type.',
                    duration: 4,
                });
                return;
        }

        if (success) {
            api.success({
                message: 'Scan Started',
                description: 'The scan has been started successfully.',
                duration: 4,
            });
        }
    };

    // Clear form and results
    const handleClear = async () => {
        setTargetUrl('');
        setScanType('spider');
        clearResults();
        await clearAlerts();
    };

    const handleEmergencyStop = async () => {
        const response = await emergencyStop();
        setEmergencyStopModalVisible(false);

        if (response) {
            api.success({
                message: 'Scans Stopped',
                description: 'All scans stopped and data cleared.',
                duration: 4,
            });
        }
    };

    // Handle Active Scan Details PDF export
    const handleExportActiveScanToPdf = async () => {
        try {
            const { exportActiveScanDetailsToPdf } = await import('../utils/activeScanPdfUtils');
            await exportActiveScanDetailsToPdf(activeScanState, targetUrl, 'zap-active-scan-details');
            api.success({
                message: 'Export Success',
                description: 'Active scan details have been exported to PDF successfully.',
                duration: 4,
            });
        } catch (error) {
            console.error('PDF export error:', error);
            api.error({
                message: 'Export Failed',
                description: 'Failed to export active scan details to PDF. Please try again.',
                duration: 4,
            });
        }
    };

    // Prepare table data from history
    const historyTableData = prepareHistoryTableData(scannerHistory);

    // Get status text based on scan status
    const getStatusText = () => {
        if (!scanStatus) return 'No scan in progress';
        if (scanStatus.isCompleted) return 'Scan completed';
        return `Scan in progress: ${scanStatus.status}%`;
    };

    // Get status color based on scan status
    const getStatusColor = () => {
        if (!scanStatus) return 'gray';
        if (scanStatus.isCompleted) return 'green';
        return 'blue';
    };

    return (
        <div>
            {contextHolder}
            <div className={'page-parent'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys} onOpenChange={menuHighlighting.onOpenChange} />
                <div className={'page-content'}>
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <LayoutOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Web Application Scanner"
                                infoContent={WebAppScannerInfo}
                                className="page-title"
                            />
                        </div>
                    </div>

                    {/* Scan Configuration Section */}
                    <div className="page-section">
                        <h3 className="section-title">Scan Configuration</h3>

                        <div className="form-row">
                            <div className="form-group" style={{ maxWidth: '300px' }}>
                                <label className="form-label required">Scan Type</label>
                                <Select
                                    showSearch
                                    placeholder="Choose scan type"
                                    onChange={handleScanTypeChange}
                                    options={scanOptions}
                                    filterOption={filterOption}
                                    value={scanType || undefined}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="control-group">
                                <button className="add-button" onClick={handleClear}>Clear Configuration</button>
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label required">Target URL</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="Enter target URL (e.g., https://example.com)"
                                    value={targetUrl}
                                    onChange={(e) => setTargetUrl(e.target.value)}
                                />
                            </div>
                            <div className="control-group">
                                <button
                                    className="add-button"
                                    onClick={handleRunScan}
                                    disabled={loading || polling}
                                >
                                    {loading ? 'Starting Scan...' : polling ? 'Scanning...' : 'Run Scan'}
                                </button>
                                <Button
                                    type="primary"
                                    danger
                                    onClick={() => setEmergencyStopModalVisible(true)}
                                    style={{ height: '40px', marginLeft: '8px' }}
                                >
                                    Stop Scans
                                </Button>
                            </div>
                        </div>
                    </div>

                    {(scanStatus || polling) && (
                        <div className="page-section">
                            <h3 className="section-title">Scan Status</h3>
                            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
                                <Tag color={getStatusColor()} style={{ marginRight: '16px', fontSize: '14px' }}>
                                    {getStatusText()}
                                </Tag>
                                {polling && !scanStatus?.isCompleted && (
                                    <span style={{ color: '#8c8c8c', fontSize: '14px' }}>
                                        Checking status every second...
                                    </span>
                                )}
                            </div>
                            <Progress
                                percent={scanStatus?.status || 0}
                                status={scanStatus?.isCompleted ? "success" : "active"}
                                strokeColor={scanStatus?.isCompleted ? "#52c41a" : "#0f386a"}
                                style={{ maxWidth: '600px' }}
                            />
                        </div>
                    )}

                    {/* Active Scan State Details */}
                    {activeScanState && (scanType === 'active' || scanType === 'full') && (
                        <div className="page-section">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                                <h3 className="section-title" style={{ margin: 0 }}>Active Scan Details</h3>
                                <button
                                    className="add-button"
                                    onClick={handleExportActiveScanToPdf}
                                    disabled={!activeScanState}
                                >
                                    Export to PDF
                                </button>
                            </div>
                            <Collapse defaultActiveKey={['1', '2']}>
                                {/* Active Scans Overview */}
                                <Panel header="Active Scans Overview" key="1">
                                    <List
                                        grid={{ gutter: 16, column: 3 }}
                                        dataSource={activeScanState.active_scans.scans}
                                        renderItem={(scan) => (
                                            <List.Item>
                                                <Card title={`Scan ID: ${scan.id}`} size="small">
                                                    <p><strong>State:</strong> {scan.state}</p>
                                                    <p><strong>Progress:</strong> {scan.progress}%</p>
                                                    <p><strong>Requests:</strong> {scan.reqCount}</p>
                                                    <p><strong>Alerts:</strong> {scan.alertCount} (New: {scan.newAlertCount})</p>
                                                </Card>
                                            </List.Item>
                                        )}
                                    />
                                </Panel>

                                {/* Scanner Progress Details */}
                                <Panel header="Scanner Progress Details" key="2">
                                    {activeScanState.scanner_progress.scanProgress && activeScanState.scanner_progress.scanProgress.length > 1 ? (
                                        <div>
                                            <h4>Target: {activeScanState.scanner_progress.scanProgress[0]}</h4>
                                            <Divider style={{ margin: '12px 0' }} />

                                            <List
                                                dataSource={activeScanState.scanner_progress.scanProgress[1].HostProcess}
                                                renderItem={(hostProcess) => {
                                                    if (!hostProcess.Plugin || hostProcess.Plugin.length < 7) return null;

                                                    const pluginName = hostProcess.Plugin[0];
                                                    const pluginId = hostProcess.Plugin[1];
                                                    const pluginQuality = hostProcess.Plugin[2];
                                                    const pluginStatus = hostProcess.Plugin[3];
                                                    const pluginTimeInMs = hostProcess.Plugin[4];
                                                    const pluginReqCount = hostProcess.Plugin[5];
                                                    const pluginAlertCount = hostProcess.Plugin[6];

                                                    // Determine status color
                                                    let statusColor = 'blue';
                                                    if (pluginStatus === 'Pending') {
                                                        statusColor = 'default';
                                                    } else if (pluginStatus.includes('%')) {
                                                        const percent = parseInt(pluginStatus, 10);
                                                        if (percent < 30) statusColor = 'orange';
                                                        else if (percent < 70) statusColor = 'blue';
                                                        else statusColor = 'green';
                                                    }

                                                    return (
                                                        <List.Item>
                                                            <div style={{ width: '100%' }}>
                                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                                    <div>
                                                                        <strong>{pluginName}</strong> <small>(ID: {pluginId}, Quality: {pluginQuality})</small>
                                                                    </div>
                                                                    <Tag color={statusColor}>{pluginStatus}</Tag>
                                                                </div>
                                                                {pluginStatus !== 'Pending' && (
                                                                    <div style={{ display: 'flex', gap: '20px', marginTop: '5px' }}>
                                                                        <small>Time: {pluginTimeInMs}ms</small>
                                                                        <small>Requests: {pluginReqCount}</small>
                                                                        <small>Alerts: {pluginAlertCount}</small>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </List.Item>
                                                    );
                                                }}
                                            />
                                        </div>
                                    ) : (
                                        <p style={{ color: '#8c8c8c', padding: '20px', textAlign: 'center' }}>
                                            Scanner progress details will appear here once the active scan starts processing plugins...
                                        </p>
                                    )}
                                </Panel>
                            </Collapse>
                        </div>
                    )}

                    {/* Scan Results & History Section */}
                    <div className="page-section">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <h3 className="section-title" style={{ margin: 0 }}>Scan Results</h3>
                                {polling && (
                                    <Tag icon={<SyncOutlined spin />} color="processing">
                                        Scan in Progress
                                    </Tag>
                                )}
                                {polling && alerts.length > 0 && (
                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <Tag color="red">High: {alerts.filter(a => a.risk === 'High').length}</Tag>
                                        <Tag color="orange">Medium: {alerts.filter(a => a.risk === 'Medium').length}</Tag>
                                        <Tag color="gold">Low: {alerts.filter(a => a.risk === 'Low').length}</Tag>
                                        <Tag color="blue">Info: {alerts.filter(a => a.risk === 'Informational').length}</Tag>
                                    </div>
                                )}
                            </div>
                            <div style={{ display: 'flex', gap: '10px' }}>
                                <Button
                                    icon={<SyncOutlined />}
                                    onClick={loadScannerHistory}
                                    loading={historyLoading}
                                >
                                    Refresh
                                </Button>
                                <Button
                                    icon={<DeleteOutlined />}
                                    danger
                                    onClick={handleClearHistory}
                                    disabled={historyLoading || scannerHistory.length === 0}
                                >
                                    Clear History
                                </Button>
                            </div>
                        </div>

                        <Table<ScannerHistoryRecord & { key: string }>
                            columns={ScannerHistoryGridColumns(handleExportHistory) as any}
                            dataSource={historyTableData}
                            loading={historyLoading}
                            expandable={{
                                expandIcon: ({ expanded, onExpand, record }) => (
                                    <span onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#1890ff', padding: '4px' }}>
                                        {expanded ? <DownOutlined /> : <RightOutlined />}
                                    </span>
                                ),
                                expandedRowKeys,
                                onExpand: (expanded, record) => handleToggleExpand(record.key),
                                expandedRowRender: (record) => {
                                    const results = parseHistoryResults(record.results);
                                    if (!results || results.length === 0) {
                                        return <p style={{ padding: '16px', color: '#8c8c8c' }}>No results available.</p>;
                                    }
                                    const alertsData = prepareZapTableData(results);
                                    return (
                                        <div style={{ padding: '16px', backgroundColor: '#fafafa' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                                    <span style={{ fontWeight: 500 }}>Vulnerabilities Found:</span>
                                                    <Tag color="red">High: {results.filter((a: any) => a.risk === 'High').length}</Tag>
                                                    <Tag color="orange">Medium: {results.filter((a: any) => a.risk === 'Medium').length}</Tag>
                                                    <Tag color="gold">Low: {results.filter((a: any) => a.risk === 'Low').length}</Tag>
                                                    <Tag color="blue">Info: {results.filter((a: any) => a.risk === 'Informational').length}</Tag>
                                                </div>
                                                {aiFeatureSettings?.aiRemediatorEnabled && (
                                                    <Button
                                                        type="primary"
                                                        icon={<RobotOutlined />}
                                                        onClick={() => handleOpenRemediation(record)}
                                                        style={{ backgroundColor: '#1890ff' }}
                                                    >
                                                        AI Remediator
                                                    </Button>
                                                )}
                                            </div>
                                            <Table
                                                columns={ZapGridColumns()}
                                                dataSource={alertsData}
                                                pagination={{
                                                    pageSize: 5,
                                                    showSizeChanger: true,
                                                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} alerts`
                                                }}
                                                expandable={{
                                                    expandIcon: ({ expanded, onExpand, record }) => (
                                                        <span onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#1890ff', padding: '4px' }}>
                                                            {expanded ? <DownOutlined /> : <RightOutlined />}
                                                        </span>
                                                    ),
                                                    expandedRowRender: (alertRecord) => (
                                                        <div style={{ padding: '16px' }}>
                                                            <h4 style={{ marginTop: 0 }}>Description</h4>
                                                            <p>{alertRecord.description}</p>
                                                            <h4>Solution</h4>
                                                            <p>{alertRecord.solution}</p>
                                                            {alertRecord.evidence && (
                                                                <>
                                                                    <h4>Evidence</h4>
                                                                    <p>{alertRecord.evidence}</p>
                                                                </>
                                                            )}
                                                            {alertRecord.reference && (
                                                                <>
                                                                    <h4>References</h4>
                                                                    <p style={{ whiteSpace: 'pre-line' }}>{alertRecord.reference}</p>
                                                                </>
                                                            )}
                                                        </div>
                                                    ),
                                                }}
                                                size="small"
                                                scroll={{ x: 700 }}
                                            />
                                        </div>
                                    );
                                },
                            }}
                            pagination={{
                                pageSize: 10,
                                showSizeChanger: true,
                                showQuickJumper: true,
                                showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} scans`
                            }}
                            scroll={{ x: 1200 }}
                            style={{
                                border: '1px solid #f0f0f0',
                                borderRadius: '6px'
                            }}
                        />
                    </div>
                </div>
            </div>

            {/* Modals */}

            {/* Stop Scans Modal */}
            <Modal
                title="Stop Scans"
                open={emergencyStopModalVisible}
                onOk={handleEmergencyStop}
                onCancel={() => setEmergencyStopModalVisible(false)}
                okText="Stop Scans"
                cancelText="Cancel"
                okButtonProps={{ danger: true }}
            >
                <p style={{ marginBottom: '10px' }}>
                    <ExclamationCircleOutlined style={{ color: '#6366f1', marginRight: '8px' }} />
                    <strong>WARNING:</strong> This will forcefully stop all scans and clear all data!
                </p>
                <p style={{ color: 'gray' }}>
                    Emergency stop should only be used in critical situations. This action:
                </p>
                <ul style={{ color: 'gray' }}>
                    <li>Stops all active and spider scans</li>
                    <li>Clears all alerts</li>
                    <li>Creates a new session (clears all data)</li>
                </ul>
                <p style={{ color: '#6366f1' }}>This action cannot be undone!</p>
            </Modal>

            {/* AI Remediation Modal */}
            {selectedHistoryForRemediation && (
                <RemediationModal
                    visible={remediationModalVisible}
                    onClose={() => {
                        setRemediationModalVisible(false);
                        setSelectedHistoryForRemediation(null);
                    }}
                    scannerType="zap"
                    historyId={selectedHistoryForRemediation.id}
                    scanTarget={selectedHistoryForRemediation.target}
                />
            )}

        </div>
    );
};

export default ZapPage;
