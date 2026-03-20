import { notification, Select, SelectProps, Button, message, Radio, Tag, Tooltip, Empty, Input, Table, Badge, Card, Row, Col } from "antd";
import type { ColumnsType } from 'antd/es/table';
import Sidebar from "../components/Sidebar.tsx";
import { useEffect, useState, useRef } from "react";
import useSemgrepStore, { LlmConfig } from "../store/useSemgrepStore.ts";
import {
    UploadOutlined,
    CodeSandboxOutlined,
    HistoryOutlined,
    PlayCircleOutlined,
    ClearOutlined,
    DeleteOutlined,
    ReloadOutlined,
    GithubOutlined,
    FolderOpenOutlined,
    LockOutlined,
    RadarChartOutlined,
    RightOutlined,
    DownOutlined,
    ApiOutlined,
    RobotOutlined,
    ToolOutlined,
    AppstoreOutlined,
    UnorderedListOutlined,
    SearchOutlined,
    SyncOutlined,
    ScheduleOutlined,
    StopOutlined,
    BugOutlined,
    SafetyOutlined,
    BulbOutlined,
    CheckCircleOutlined,
    SettingOutlined
} from '@ant-design/icons';
import ScannerGuideWizard, { GuideStep } from "../components/ScannerGuideWizard.tsx";
import ScheduleScanModal from "../components/ScheduleScanModal.tsx";
import html2pdf from 'html2pdf.js';
import ScannerLegalModal from "../components/ScannerLegalModal.tsx";
import { useScannerLegalConfirmation } from "../utils/scannerLegalConfirmation.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import { CodeAnalysisInfo } from "../constants/infoContent.tsx";
import { trackPdfDownload } from '../utils/trackPdfDownload';
import useAuthStore from '../store/useAuthStore';
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { ScannerHistoryRecord, ScannerHistoryGridColumns, prepareHistoryTableData } from "../constants/ScannerHistoryGridColumns.tsx";
import {
    saveScannerHistory,
    fetchScannerHistory,
    fetchScannerHistoryDetails,
    deleteScannerHistoryRecord,
    fetchCurrentUserDetails,
    parseHistoryResults,
    clearScannerHistory
} from "../utils/scannerHistoryUtils.ts";

const SemgrepPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Legal disclaimer confirmation
    const { visible: legalModalVisible, scannerName: legalScannerName, handleOk: legalHandleOk, handleCancel: legalHandleCancel, confirmScanLegalDisclaimer } = useScannerLegalConfirmation();

    // View mode state
    const [historyViewMode, setHistoryViewMode] = useState<'grid' | 'list'>('list');
    const [historySearchText, setHistorySearchText] = useState('');

    // Get functions and state from the store
    const {
        scanZipFile,
        scanGithubRepo,
        clearResults,
        scanResults,
        loading,
        error,
        configOptions,
        cancelScan
    } = useSemgrepStore();

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    const { user } = useAuthStore();

    // Input method: 'upload' or 'github'
    const [inputMethod, setInputMethod] = useState<'upload' | 'github'>('upload');

    // State for form inputs
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [githubUrl, setGithubUrl] = useState<string>('');
    const [githubToken, setGithubToken] = useState<string>('');
    const [isPrivateRepo, setIsPrivateRepo] = useState<boolean>(false);
    const [config, setConfig] = useState<string>('auto');
    const [useLlm, setUseLlm] = useState<boolean>(false);

    // LLM Provider configuration
    const [llmProvider, setLlmProvider] = useState<'llamacpp' | 'qlon'>('llamacpp');
    const [qlonUrl, setQlonUrl] = useState<string>('');
    const [qlonApiKey, setQlonApiKey] = useState<string>('');
    const [useIntegrationTools, setUseIntegrationTools] = useState<boolean>(true);

    // Scanner history state
    const [scannerHistory, setScannerHistory] = useState<ScannerHistoryRecord[]>([]);
    const [historyLoading, setHistoryLoading] = useState(false);
    const [scanStartTime, setScanStartTime] = useState<number | null>(null);

    // Lazy loading state for expanded row results
    const [loadedResults, setLoadedResults] = useState<Record<string, any>>({});
    const [loadingRows, setLoadingRows] = useState<Set<string>>(new Set());
    const [expandedRowKeys, setExpandedRowKeys] = useState<string[]>([]);

    // Schedule state
    const [scheduleModalVisible, setScheduleModalVisible] = useState(false);
    const [scheduleTarget, setScheduleTarget] = useState('');
    const [scheduleScanConfig, setScheduleScanConfig] = useState<Record<string, any> | undefined>(undefined);

    const openScheduleModal = (target: string, scanConfig?: Record<string, any>) => {
        setScheduleTarget(target);
        setScheduleScanConfig(scanConfig);
        setScheduleModalVisible(true);
    };

    const handleScheduleFromHistory = (record: ScannerHistoryRecord) => {
        openScheduleModal(record.scan_target, record.scan_type ? { config: record.scan_type } : undefined);
    };

    // Reference to the file input element
    const fileInputRef = useRef<HTMLInputElement>(null);

    // ==================== Scanner Guide Steps ====================
    const semgrepGuideSteps: GuideStep[] = [
        {
            title: 'Overview',
            icon: <CodeSandboxOutlined />,
            description: 'What is Code Analysis?',
            content: {
                heading: 'Static Application Security Testing (SAST)',
                body: 'Code Analysis uses Semgrep to scan your source code for security vulnerabilities, bugs, and anti-patterns without executing it. It applies pattern-matching rules to detect issues like SQL injection, XSS, hardcoded secrets, and insecure configurations.',
                tip: 'SAST is most effective when run early in the development cycle — the earlier you catch issues, the cheaper they are to fix.'
            }
        },
        {
            title: 'Configuration',
            icon: <SettingOutlined />,
            description: 'Rulesets and configs',
            content: {
                heading: 'Scan Configurations',
                body: 'Choose a ruleset that matches your codebase and security requirements:',
                infoRows: [
                    { icon: <SafetyOutlined />, iconBg: '#0f386a', text: <span><strong>Auto</strong> - Automatically detects your languages and applies the most relevant rules. Best for most projects.</span> },
                    { icon: <BugOutlined />, iconBg: '#dc2626', text: <span><strong>Security Audit</strong> - Focused on security vulnerabilities: injection flaws, authentication issues, crypto weaknesses.</span> },
                    { icon: <CheckCircleOutlined />, iconBg: '#10b981', text: <span><strong>OWASP Top 10</strong> - Rules specifically targeting the OWASP Top 10 most critical web application security risks.</span> },
                    { icon: <CodeSandboxOutlined />, iconBg: '#8b5cf6', text: <span><strong>Language-Specific</strong> - Targeted rulesets for Python, JavaScript, Java, Go, and other languages.</span> }
                ],
                tip: 'Start with "Auto" to get a broad overview, then use targeted rulesets for deeper analysis of specific vulnerability categories.'
            }
        },
        {
            title: 'Input',
            icon: <FolderOpenOutlined />,
            description: 'How to provide source code',
            content: {
                heading: 'Input Methods',
                body: 'You can provide source code for analysis in two ways:',
                infoRows: [
                    { icon: <UploadOutlined />, iconBg: '#0f386a', text: <span><strong>ZIP Upload</strong> - Upload a ZIP archive of your project source code. The scanner extracts and analyses all supported files.</span> },
                    { icon: <GithubOutlined />, iconBg: '#1f2937', text: <span><strong>GitHub Repository</strong> - Provide a GitHub repository URL. Supports both public and private repos (with token authentication).</span> },
                    { icon: <LockOutlined />, iconBg: '#8b5cf6', text: <span><strong>Private Repos</strong> - For private repositories, toggle "Private Repository" and provide a GitHub Personal Access Token with repo read access.</span> }
                ],
                tip: 'For GitHub repos, ensure the URL points to the repository root (e.g. https://github.com/owner/repo).'
            }
        },
        {
            title: 'Analysis',
            icon: <RobotOutlined />,
            description: 'LLM vs Fast mode',
            content: {
                heading: 'Analysis Mode',
                body: 'Choose between two analysis modes depending on your needs:',
                infoRows: [
                    { icon: <RobotOutlined />, iconBg: '#8b5cf6', text: <span><strong>LLM Analysis</strong> - Sends scan results to the AI model for contextual analysis. Provides detailed explanations, severity assessment, and tailored remediation advice.</span> },
                    { icon: <RadarChartOutlined />, iconBg: '#10b981', text: <span><strong>Fast Results</strong> - Returns raw Semgrep findings immediately without AI processing. Faster but provides less context and no remediation guidance.</span> }
                ],
                tip: 'Use LLM Analysis for thorough security reviews. Use Fast Results when you need quick feedback during development.'
            }
        },
        {
            title: 'Tips',
            icon: <BulbOutlined />,
            description: 'Best practices',
            content: {
                heading: 'Best Practices',
                body: '',
                tips: [
                    'Run code analysis before deploying to production to catch vulnerabilities early in the development pipeline.',
                    'Use the OWASP Top 10 ruleset for compliance-focused scans that map directly to industry standards.',
                    'Enable LLM Analysis for actionable remediation advice — the AI explains not just what the issue is, but how to fix it.',
                    'Combine Semgrep results with dependency scanning (OSV) for comprehensive application security coverage.',
                    'Review findings by severity — focus on Critical and High issues first.',
                    'Export results to PDF for security audit documentation and compliance evidence.'
                ]
            }
        }
    ];

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

    // Load scanner history
    const loadScannerHistory = async () => {
        setHistoryLoading(true);
        try {
            const history = await fetchScannerHistory('semgrep', 100);
            setScannerHistory(history);
        } catch (error) {
            console.error('Error loading scanner history:', error);
        } finally {
            setHistoryLoading(false);
        }
    };

    // Clear all scanner history
    const handleClearHistory = async () => {
        const confirmed = window.confirm(
            'Are you sure you want to delete all Code Analysis scan history records?\n\nThis action cannot be undone.'
        );

        if (confirmed) {
            setHistoryLoading(true);
            const result = await clearScannerHistory('semgrep');

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

    // Search filtered history
    const searchFilteredHistory = scannerHistory.filter(record =>
        record.scan_target?.toLowerCase().includes(historySearchText.toLowerCase()) ||
        record.scan_type?.toLowerCase().includes(historySearchText.toLowerCase()) ||
        record.status?.toLowerCase().includes(historySearchText.toLowerCase()) ||
        record.user_email?.toLowerCase().includes(historySearchText.toLowerCase())
    );

    // Get status color for history cards
    const getHistoryStatusColor = (status: string): string => {
        switch (status?.toLowerCase()) {
            case 'completed': return '#52c41a';
            case 'failed': return '#ff4d4f';
            case 'running': return '#1890ff';
            default: return '#8c8c8c';
        }
    };

    // History Card component
    const HistoryCard = ({ record }: { record: ScannerHistoryRecord }) => {
        return (
            <Card
                hoverable
                style={{ height: '100%' }}
                bodyStyle={{ padding: '16px' }}
                onClick={() => handleExportHistory(record)}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 500, flex: 1, marginRight: '8px', wordBreak: 'break-all' }}>
                        {record.scan_target}
                    </h4>
                    <Tag color={getHistoryStatusColor(record.status)}>{record.status}</Tag>
                </div>

                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '8px' }}>
                    <Tag color="blue">{record.scan_type}</Tag>
                    {record.scan_duration && <Tag>{record.scan_duration.toFixed(1)}s</Tag>}
                </div>

                <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
                    {record.user_email && <div>By: {record.user_email}</div>}
                    {record.created_at && <div>{formatTimestamp(record.created_at)}</div>}
                </div>
            </Card>
        );
    };

    // Handler for expanding history rows - fetches results on demand
    const handleRowExpand = async (expanded: boolean, record: ScannerHistoryRecord & { key: string }) => {
        if (expanded) {
            setExpandedRowKeys(prev => [...prev, record.key]);
            if (!loadedResults[record.id]) {
                setLoadingRows(prev => new Set(prev).add(record.id));
                try {
                    const fullDetails = await fetchScannerHistoryDetails(record.id);
                    if (fullDetails && fullDetails.results) {
                        const results = parseHistoryResults(fullDetails.results);
                        setLoadedResults(prev => ({ ...prev, [record.id]: results }));
                    }
                } catch (error) {
                    console.error('Error loading scan results:', error);
                } finally {
                    setLoadingRows(prev => {
                        const next = new Set(prev);
                        next.delete(record.id);
                        return next;
                    });
                }
            }
        } else {
            setExpandedRowKeys(prev => prev.filter(k => k !== record.key));
        }
    };

    // Load history on mount
    useEffect(() => {
        loadScannerHistory();
    }, []);

    // Save history when scan completes
    useEffect(() => {
        const saveHistoryOnCompletion = async () => {
            if (scanResults && !loading && user?.email && scanStartTime) {
                const duration = (Date.now() - scanStartTime) / 1000;
                const userDetails = await fetchCurrentUserDetails(user.email);

                if (userDetails) {
                    const target = inputMethod === 'github'
                        ? (scanResults.repository || githubUrl)
                        : (selectedFile?.name || 'N/A');

                    await saveScannerHistory(
                        {
                            scanner_type: 'semgrep',
                            scan_target: target,
                            scan_type: config,
                            results: scanResults,
                            status: 'completed',
                            scan_duration: duration
                        },
                        userDetails.email,
                        userDetails.id,
                        userDetails.organisation_id,
                        userDetails.organisation_name
                    );
                    loadScannerHistory();
                }
                setScanStartTime(null);
            }
        };
        saveHistoryOnCompletion();
    }, [scanResults, loading, user, scanStartTime, selectedFile, config, githubUrl, inputMethod]);

    // Track scan start
    useEffect(() => {
        if (loading && !scanStartTime) {
            setScanStartTime(Date.now());
        }
    }, [loading, scanStartTime]);

    // Filter function for the select dropdown
    const filterOption: SelectProps['filterOption'] = (input, option) =>
        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase());

    // Handle file upload
    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (files && files.length > 0) {
            const file = files[0];
            if (file.type !== 'application/zip' && !file.name.endsWith('.zip')) {
                message.error(`${file.name} is not a ZIP file`);
                if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                }
                setSelectedFile(null);
                return;
            }
            message.success(`${file.name} selected successfully`);
            setSelectedFile(file);
        } else {
            setSelectedFile(null);
        }
    };

    // Run the scan
    const handleRunScan = async () => {
        const accepted = await confirmScanLegalDisclaimer('Code Analysis');
        if (!accepted) return;

        // Validate QLON configuration if QLON is selected
        if (useLlm && llmProvider === 'qlon') {
            if (!qlonUrl || qlonUrl.trim() === '') {
                api.error({
                    message: 'Missing QLON URL',
                    description: 'Please enter the QLON Ai URL.',
                    duration: 4,
                });
                return;
            }
            if (!qlonApiKey || qlonApiKey.trim() === '') {
                api.error({
                    message: 'Missing API Key',
                    description: 'Please enter the QLON Ai API key.',
                    duration: 4,
                });
                return;
            }
        }

        // Build LLM configuration
        const llmConfig: LlmConfig | undefined = useLlm ? {
            provider: llmProvider,
            qlon: llmProvider === 'qlon' ? {
                url: qlonUrl.trim(),
                apiKey: qlonApiKey.trim(),
                useIntegrationTools: useIntegrationTools
            } : undefined
        } : undefined;

        if (inputMethod === 'upload') {
            if (!selectedFile) {
                api.error({
                    message: 'Missing File',
                    description: 'Please upload a ZIP file to scan.',
                    duration: 4,
                });
                return;
            }
            const success = await scanZipFile(selectedFile, config, useLlm, llmConfig);
            if (success) {
                api.success({
                    message: 'Scan Completed',
                    description: 'The code analysis has been completed successfully.',
                    duration: 4,
                });
            }
        } else {
            if (!githubUrl || githubUrl.trim() === '') {
                api.error({
                    message: 'Missing Repository URL',
                    description: 'Please enter a GitHub repository URL.',
                    duration: 4,
                });
                return;
            }
            if (isPrivateRepo && (!githubToken || githubToken.trim() === '')) {
                api.error({
                    message: 'Missing Token',
                    description: 'Please enter a GitHub Personal Access Token for private repositories.',
                    duration: 4,
                });
                return;
            }
            const success = await scanGithubRepo(githubUrl, config, useLlm, isPrivateRepo ? githubToken : undefined, llmConfig);
            if (success) {
                api.success({
                    message: 'Scan Completed',
                    description: 'The GitHub repository analysis has been completed successfully.',
                    duration: 4,
                });
            }
        }
    };

    // Clear form and results
    const handleClear = () => {
        setSelectedFile(null);
        setGithubUrl('');
        setGithubToken('');
        setIsPrivateRepo(false);
        setConfig('auto');
        clearResults();
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    // Handle export history record to PDF
    const handleExportHistory = async (record: ScannerHistoryRecord) => {
        try {
            // Fetch full details if results not already loaded
            let parsedResults = loadedResults[record.id];
            if (!parsedResults) {
                const fullDetails = await fetchScannerHistoryDetails(record.id);
                if (fullDetails && fullDetails.results) {
                    parsedResults = parseHistoryResults(fullDetails.results);
                    setLoadedResults(prev => ({ ...prev, [record.id]: parsedResults }));
                }
            }
            if (!parsedResults) {
                api.warning({ message: 'No Results', description: 'No results available to export.', duration: 4 });
                return;
            }
            const resultsToExport = parsedResults?.analysis || parsedResults?.output || parsedResults;
            const htmlContent = `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Code Analysis Scan Results - ${record.scan_target}</title><style>body{font-family:Arial,sans-serif;line-height:1.6;margin:20px}h1{color:#0f386a}.metadata{background:#e7f3ff;padding:10px;border-radius:5px;margin-bottom:20px}.results{background:#f8f8f8;padding:15px;border-radius:8px;white-space:pre-line;word-wrap:break-word;font-family:monospace}</style></head><body><h1>Code Analysis Results</h1><div class="metadata"><strong>Target:</strong> ${record.scan_target}<br><strong>Scan Type:</strong> ${record.scan_type || 'N/A'}<br><strong>Timestamp:</strong> ${new Date(record.timestamp).toLocaleString()}<br><strong>Duration:</strong> ${record.scan_duration ? record.scan_duration.toFixed(2) + 's' : 'N/A'}</div><div class="results">${typeof resultsToExport === 'string' ? resultsToExport : JSON.stringify(resultsToExport, null, 2)}</div></body></html>`;

            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = htmlContent;
            document.body.appendChild(tempDiv);
            const timestamp = new Date(record.timestamp).toISOString().replace(/[:.]/g, '-').slice(0, 19);
            const filename = `code-analysis-scan-${record.scan_target.replace(/[^a-z0-9]/gi, '_')}-${timestamp}.pdf`;
            const options = { margin: 10, filename: filename, image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2 }, jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' } };
            await html2pdf().from(tempDiv).set(options).save();
            const { getAuthHeader } = useAuthStore.getState();
            await trackPdfDownload('semgrep', () => getAuthHeader() || {});
            document.body.removeChild(tempDiv);
            api.success({ message: 'Export Successful', description: 'Scan results exported to PDF.', duration: 3 });
        } catch (error) {
            console.error('Error exporting to PDF:', error);
            api.error({ message: 'Export Failed', description: 'Failed to export scan results.', duration: 4 });
        }
    };

    // Handle delete history record
    const handleDeleteRecord = async (record: ScannerHistoryRecord) => {
        const confirmed = window.confirm(`Are you sure you want to delete this scan result?\n\nTarget: ${record.scan_target}\nTimestamp: ${new Date(record.timestamp).toLocaleString()}\n\nThis action cannot be undone.`);
        if (confirmed) {
            setHistoryLoading(true);
            const result = await deleteScannerHistoryRecord(record.id);
            if (result.success) {
                api.success({ message: 'Record Deleted', description: 'Scan result deleted successfully.', duration: 3 });
                loadScannerHistory();
            } else {
                api.error({ message: 'Delete Failed', description: result.error || 'Failed to delete record.', duration: 4 });
            }
            setHistoryLoading(false);
        }
    };

    // Custom styles
    const pageStyles = `
        .scanner-card {
            background: var(--background-white);
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            padding: 24px;
            margin-bottom: 20px;
        }
        .scanner-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--border-light-gray);
        }
        .scanner-card-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-charcoal);
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .config-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .config-grid-full {
            grid-column: 1 / -1;
        }
        .form-field {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .form-field label {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-dark-gray);
        }
        .form-field label .required {
            color: #ff4d4f;
            margin-left: 4px;
        }
        .private-repo-toggle {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
            cursor: pointer;
        }
        .custom-toggle {
            position: relative;
            width: 44px;
            height: 24px;
            background: var(--border-light-gray);
            border-radius: 12px;
            transition: background 0.2s ease;
            cursor: pointer;
            flex-shrink: 0;
        }
        .custom-toggle.active {
            background: #1890ff;
        }
        .custom-toggle-handle {
            position: absolute;
            top: 2px;
            left: 2px;
            width: 20px;
            height: 20px;
            background: var(--background-white);
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: left 0.2s ease;
        }
        .custom-toggle.active .custom-toggle-handle {
            left: 22px;
        }
        .private-repo-toggle .toggle-label {
            font-size: 14px;
            color: var(--text-dark-gray);
            user-select: none;
        }
        .action-buttons {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        .btn-primary {
            background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
            border: none;
            color: white;
            padding: 10px 24px;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
            font-size: 14px;
        }
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(24, 144, 255, 0.35);
        }
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        .btn-secondary {
            background: var(--background-off-white);
            border: 1px solid var(--border-light-gray);
            color: var(--text-dark-gray);
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
            font-size: 14px;
        }
        .btn-secondary:hover {
            background: var(--background-white);
            border-color: var(--border-light-gray);
        }
        .results-container {
            background: var(--background-off-white);
            border: 1px solid var(--border-light-gray);
            border-radius: 10px;
            min-height: 200px;
            position: relative;
        }
        .results-content {
            padding: 20px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
            color: var(--text-charcoal);
            max-height: 400px;
            overflow-y: auto;
        }
        .history-section {
            margin-top: 24px;
        }
        .history-collapse .ant-collapse-header {
            background: var(--background-off-white);
            border-radius: 10px !important;
            padding: 16px 20px !important;
            font-weight: 500;
        }
        .history-collapse .ant-collapse-content {
            border-top: 1px solid var(--border-light-gray);
        }
        .history-header-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
        }
        .history-badge {
            background: var(--primary-blue-light);
            color: var(--primary-blue);
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 60px 20px;
            color: var(--text-medium-gray);
        }
        .empty-state-icon {
            font-size: 48px;
            color: var(--border-light-gray);
            margin-bottom: 16px;
        }
        .history-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: var(--background-white);
            border: 1px solid var(--border-light-gray);
            border-radius: 8px;
            margin-bottom: 8px;
            transition: all 0.2s ease;
        }
        .history-item:hover {
            border-color: #1890ff;
            box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
        }
        .history-item-info {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        .history-item-target {
            font-weight: 500;
            color: var(--text-charcoal);
        }
        .history-item-meta {
            font-size: 12px;
            color: var(--text-medium-gray);
            display: flex;
            gap: 16px;
        }
        .history-item-actions {
            display: flex;
            gap: 8px;
        }
        .input-method-tabs {
            display: flex;
            gap: 0;
            margin-bottom: 20px;
        }
        .input-method-tab {
            padding: 12px 24px;
            border: 1px solid var(--border-light-gray);
            background: var(--background-off-white);
            cursor: pointer;
            font-weight: 500;
            color: var(--text-dark-gray);
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }
        .input-method-tab:first-child {
            border-radius: 8px 0 0 8px;
        }
        .input-method-tab:last-child {
            border-radius: 0 8px 8px 0;
            border-left: none;
        }
        .input-method-tab.active {
            background: #1890ff;
            border-color: #1890ff;
            color: white;
        }
        .input-method-tab:hover:not(.active) {
            background: var(--background-white);
        }
        .file-upload-box {
            border: 2px dashed var(--border-light-gray);
            border-radius: 10px;
            padding: 40px 20px;
            text-align: center;
            background: var(--background-off-white);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .file-upload-box:hover {
            border-color: #1890ff;
            background: var(--background-white);
        }
        .file-upload-box.has-file {
            border-color: #52c41a;
            background: rgba(82, 196, 26, 0.12);
        }
        .semgrep-inline-panel {
            padding: 16px;
            border-radius: 8px;
            background: var(--background-off-white);
            border: 1px solid var(--border-light-gray);
        }
        .semgrep-inline-panel-title {
            font-weight: 500;
            color: var(--text-charcoal);
        }
        .semgrep-muted-text {
            color: var(--text-medium-gray);
        }
        .semgrep-upload-title {
            color: var(--text-charcoal);
            font-size: 16px;
            font-weight: bold;
            margin: 0 0 8px 0;
        }
        .semgrep-upload-subtitle {
            color: var(--text-medium-gray);
            font-size: 14px;
            margin: 0;
        }
        .semgrep-info-banner {
            margin-top: 16px;
            padding: 12px;
            border-radius: 8px;
            background: var(--primary-blue-light);
            border: 1px solid var(--professional-blue);
        }
        .semgrep-info-banner p {
            margin: 0;
            color: var(--professional-blue);
            font-size: 14px;
        }
        .history-view-toggle {
            display: flex;
            border: 1px solid var(--border-light-gray);
            border-radius: 6px;
            overflow: hidden;
        }
        .history-view-btn {
            border: none;
            padding: 6px 12px;
            cursor: pointer;
            background: var(--background-white);
            color: var(--text-dark-gray);
        }
        .history-view-btn.with-divider {
            border-left: 1px solid var(--border-light-gray);
        }
        .history-view-btn.active {
            background: var(--professional-blue);
            color: #fff;
        }
        .expanded-results-wrapper {
            padding: 16px;
            border-radius: 8px;
            background: var(--background-off-white);
        }
        .expanded-results-content {
            background: var(--background-white);
            border: 1px solid var(--border-light-gray);
            color: var(--text-charcoal);
            padding: 16px;
            border-radius: 6px;
            max-height: 400px;
            overflow: auto;
            font-family: monospace;
            font-size: 13px;
            white-space: pre-wrap;
            word-break: break-word;
        }
        @media (max-width: 768px) {
            .config-grid {
                grid-template-columns: 1fr;
            }
        }
    `;

    return (
        <div>
            {contextHolder}
            <style>{pageStyles}</style>
            <div className={'page-parent semgrep-page'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys} onOpenChange={menuHighlighting.onOpenChange} />
                <div className={'page-content'}>
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <CodeSandboxOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Code Analysis"
                                infoContent={CodeAnalysisInfo}
                                className="page-title"
                            />
                        </div>
                        <div className="page-header-right">
                            <ScannerGuideWizard
                                steps={semgrepGuideSteps}
                                title="Code Analysis Guide"
                                icon={<CodeSandboxOutlined />}
                                buttonLabel="Scanner Guide"
                            />
                        </div>
                    </div>

                    {/* Scan Configuration Card */}
                    <div className="scanner-card">
                        <div className="scanner-card-header">
                            <h3 className="scanner-card-title">
                                <CodeSandboxOutlined style={{ color: '#1890ff' }} />
                                Scan Configuration
                            </h3>
                            {loading && <Tag color="processing">Scanning...</Tag>}
                        </div>

                        <div className="config-grid">
                            <div className="form-field">
                                <label>Configuration<span className="required">*</span></label>
                                <Select
                                    showSearch
                                    placeholder="Analysis Configuration"
                                    onChange={(value) => setConfig(value)}
                                    options={configOptions.map(option => ({ value: option, label: option }))}
                                    filterOption={filterOption}
                                    value={config || undefined}
                                    size="large"
                                />
                            </div>
                            <div className="form-field">
                                <label>Analysis Mode</label>
                                <Radio.Group
                                    value={useLlm ? 'llm' : 'fast'}
                                    onChange={(e) => setUseLlm(e.target.value === 'llm')}
                                    buttonStyle="solid"
                                    style={{ marginTop: '4px' }}
                                >
                                    <Radio.Button value="llm">LLM Analysis</Radio.Button>
                                    <Radio.Button value="fast">Fast Results</Radio.Button>
                                </Radio.Group>
                            </div>
                        </div>

                        {/* LLM Provider Configuration - shown when LLM Analysis is selected */}
                        {useLlm && (
                            <div className="semgrep-inline-panel" style={{ marginTop: '20px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                                    <RobotOutlined style={{ color: '#1890ff', fontSize: '16px' }} />
                                    <span className="semgrep-inline-panel-title">LLM Provider</span>
                                </div>

                                <div className="config-grid">
                                    <div className="form-field">
                                        <label>Select Provider<span className="required">*</span></label>
                                        <Select
                                            value={llmProvider}
                                            onChange={(value) => setLlmProvider(value)}
                                            size="large"
                                            options={[
                                                { value: 'llamacpp', label: 'llama.cpp (Default)' },
                                                { value: 'qlon', label: 'QLON Ai' }
                                            ]}
                                        />
                                    </div>
                                </div>

                                {/* QLON Ai Configuration - shown when QLON is selected */}
                                {llmProvider === 'qlon' && (
                                    <div style={{ marginTop: '16px' }}>
                                        <div className="config-grid">
                                            <div className="form-field">
                                                <label>QLON Ai URL<span className="required">*</span></label>
                                                <Input
                                                    size="large"
                                                    placeholder="https://your-qlon-instance.com"
                                                    prefix={<ApiOutlined style={{ color: '#999' }} />}
                                                    value={qlonUrl}
                                                    onChange={(e) => setQlonUrl(e.target.value)}
                                                    style={{ borderRadius: '8px' }}
                                                />
                                            </div>
                                            <div className="form-field">
                                                <label>API Key<span className="required">*</span></label>
                                                <Input.Password
                                                    size="large"
                                                    placeholder="Enter your QLON API key"
                                                    prefix={<LockOutlined style={{ color: '#999' }} />}
                                                    value={qlonApiKey}
                                                    onChange={(e) => setQlonApiKey(e.target.value)}
                                                    style={{ borderRadius: '8px' }}
                                                />
                                            </div>
                                        </div>

                                        {/* Integration Tools Toggle */}
                                        <div style={{ marginTop: '16px' }}>
                                            <div
                                                className="private-repo-toggle"
                                                onClick={() => setUseIntegrationTools(!useIntegrationTools)}
                                            >
                                                <div className={`custom-toggle ${useIntegrationTools ? 'active' : ''}`}>
                                                    <div className="custom-toggle-handle" />
                                                </div>
                                                <span className="toggle-label">
                                                    <ToolOutlined style={{ marginRight: '6px' }} />
                                                    Enable Integration Tools
                                                    {useIntegrationTools && (
                                                        <Tag color="blue" style={{ marginLeft: '8px' }}>Active</Tag>
                                                    )}
                                                </span>
                                            </div>
                                            <p className="semgrep-muted-text" style={{ fontSize: '12px', margin: '8px 0 0 54px' }}>
                                                When enabled, QLON Ai will use all available integration tools for enhanced analysis.
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Source Code Input Card */}
                    <div className="scanner-card">
                        <div className="scanner-card-header">
                            <h3 className="scanner-card-title">
                                <FolderOpenOutlined style={{ color: '#1890ff' }} />
                                Source Code
                            </h3>
                        </div>

                        {/* Input Method Tabs */}
                        <div className="input-method-tabs">
                            <button
                                className={`input-method-tab ${inputMethod === 'upload' ? 'active' : ''}`}
                                onClick={() => setInputMethod('upload')}
                            >
                                <UploadOutlined /> Upload ZIP File
                            </button>
                            <button
                                className={`input-method-tab ${inputMethod === 'github' ? 'active' : ''}`}
                                onClick={() => setInputMethod('github')}
                            >
                                <GithubOutlined /> GitHub Repository
                            </button>
                        </div>

                        {/* File Upload Section */}
                        {inputMethod === 'upload' && (
                            <div
                                className={`file-upload-box ${selectedFile ? 'has-file' : ''}`}
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <div style={{ fontSize: '48px', color: selectedFile ? '#52c41a' : '#0f386a', marginBottom: '16px' }}>
                                    <UploadOutlined />
                                </div>
                                <p className="semgrep-upload-title">
                                    {selectedFile ? selectedFile.name : 'Click to select a ZIP file'}
                                </p>
                                <p className="semgrep-upload-subtitle">
                                    {selectedFile ? 'Click to change file' : 'Upload a ZIP file containing source code for security analysis'}
                                </p>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    onChange={handleFileChange}
                                    accept=".zip"
                                    style={{ display: 'none' }}
                                />
                            </div>
                        )}

                        {/* GitHub URL Section */}
                        {inputMethod === 'github' && (
                            <div>
                                <div className="form-field" style={{ marginBottom: '16px' }}>
                                    <label>GitHub Repository URL<span className="required">*</span></label>
                                    <Input
                                        size="large"
                                        placeholder="https://github.com/owner/repository"
                                        prefix={<GithubOutlined style={{ color: '#999' }} />}
                                        value={githubUrl}
                                        onChange={(e) => setGithubUrl(e.target.value)}
                                        style={{ borderRadius: '8px' }}
                                    />
                                </div>

                                {/* Private Repository Toggle */}
                                <div
                                    className="private-repo-toggle"
                                    onClick={() => setIsPrivateRepo(!isPrivateRepo)}
                                >
                                    <div className={`custom-toggle ${isPrivateRepo ? 'active' : ''}`}>
                                        <div className="custom-toggle-handle" />
                                    </div>
                                    <span className="toggle-label">
                                        Private repository
                                        {isPrivateRepo && <LockOutlined style={{ marginLeft: '6px', color: '#fa8c16' }} />}
                                    </span>
                                </div>

                                {/* Token Input (shown when private repo is selected) */}
                                {isPrivateRepo && (
                                    <div className="form-field" style={{ marginBottom: '16px' }}>
                                        <label>GitHub Personal Access Token<span className="required">*</span></label>
                                        <Input.Password
                                            size="large"
                                            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                                            prefix={<LockOutlined style={{ color: '#999' }} />}
                                            value={githubToken}
                                            onChange={(e) => setGithubToken(e.target.value)}
                                            style={{ borderRadius: '8px' }}
                                        />
                                        <p className="semgrep-muted-text" style={{ fontSize: '12px', marginTop: '8px' }}>
                                            Create a token at <a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer" style={{ color: '#1890ff' }}>GitHub Settings → Developer settings → Personal access tokens</a>.
                                            The token needs <strong>repo</strong> scope for private repositories.
                                        </p>
                                    </div>
                                )}

                                {!isPrivateRepo && (
                                    <p className="semgrep-muted-text" style={{ fontSize: '13px', margin: 0 }}>
                                        Enter a public GitHub repository URL. The repository will be cloned and scanned.
                                    </p>
                                )}
                            </div>
                        )}

                        {/* Action Buttons */}
                        <div className="action-buttons" style={{ marginTop: '20px' }}>
                            <button
                                className="btn-primary"
                                onClick={handleRunScan}
                                disabled={loading || (inputMethod === 'upload'
                                    ? !selectedFile
                                    : !githubUrl.trim() || (isPrivateRepo && !githubToken.trim()))}
                            >
                                <PlayCircleOutlined />
                                {loading ? 'Scanning...' : 'Run Scan'}
                            </button>
                            {loading && (
                                <button
                                    className="btn-primary"
                                    onClick={cancelScan}
                                    style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f' }}
                                >
                                    <StopOutlined />
                                    Cancel Scan
                                </button>
                            )}
                            <button className="btn-secondary" onClick={handleClear}>
                                <ClearOutlined />
                                Clear
                            </button>
                            <button
                                className="btn-secondary"
                                onClick={() => openScheduleModal(
                                    inputMethod === 'github' ? githubUrl : (selectedFile?.name || ''),
                                    { config }
                                )}
                                disabled={inputMethod === 'github' ? !githubUrl.trim() : !selectedFile}
                                style={{ color: '#722ed1', borderColor: '#722ed1' }}
                            >
                                <ScheduleOutlined />
                                Schedule
                            </button>
                        </div>

                        {loading && (
                            <div className="semgrep-info-banner">
                                <p>
                                    {inputMethod === 'github'
                                        ? 'Cloning repository and running scan... This may take several minutes.'
                                        : 'Scan in progress... This may take several minutes depending on the codebase size.'}
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Unified Scan Results Section */}
                    <div className="scanner-card">
                        <div className="scanner-card-header">
                            <h3 className="scanner-card-title">
                                <HistoryOutlined style={{ color: '#1890ff', marginRight: '8px' }} />
                                Scan Results
                                {scannerHistory.length > 0 && (
                                    <Badge count={scannerHistory.length} style={{ backgroundColor: '#1890ff', marginLeft: '8px' }} />
                                )}
                                {loading && (
                                    <Tag icon={<RadarChartOutlined spin />} color="processing" style={{ marginLeft: '12px' }}>
                                        Scanning...
                                    </Tag>
                                )}
                            </h3>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <Tooltip title="Refresh">
                                    <Button
                                        type="text"
                                        icon={<ReloadOutlined />}
                                        onClick={loadScannerHistory}
                                        loading={historyLoading}
                                    />
                                </Tooltip>
                                <Tooltip title="Clear All History">
                                    <Button
                                        type="text"
                                        danger
                                        icon={<DeleteOutlined />}
                                        onClick={handleClearHistory}
                                        disabled={scannerHistory.length === 0}
                                    />
                                </Tooltip>
                            </div>
                        </div>

                        {/* Search and View Toggle */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
                            <Input
                                placeholder="Search history..."
                                prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                value={historySearchText}
                                onChange={(e) => setHistorySearchText(e.target.value)}
                                style={{ width: '250px' }}
                            />
                            <div className="history-view-toggle">
                                <button
                                    onClick={() => setHistoryViewMode('grid')}
                                    className={`history-view-btn ${historyViewMode === 'grid' ? 'active' : ''}`}
                                >
                                    <AppstoreOutlined />
                                </button>
                                <button
                                    onClick={() => setHistoryViewMode('list')}
                                    className={`history-view-btn with-divider ${historyViewMode === 'list' ? 'active' : ''}`}
                                >
                                    <UnorderedListOutlined />
                                </button>
                            </div>
                        </div>

                        {searchFilteredHistory.length === 0 ? (
                            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No scan results found." />
                        ) : historyViewMode === 'grid' ? (
                            <Row gutter={[16, 16]}>
                                {searchFilteredHistory.map(record => (
                                    <Col key={record.id} xs={24} sm={12} md={8} lg={6}>
                                        <HistoryCard record={record} />
                                    </Col>
                                ))}
                            </Row>
                        ) : (
                        <Table<ScannerHistoryRecord & { key: string }>
                            columns={ScannerHistoryGridColumns(handleExportHistory, handleDeleteRecord, handleScheduleFromHistory) as ColumnsType<ScannerHistoryRecord & { key: string }>}
                            dataSource={prepareHistoryTableData(searchFilteredHistory)}
                            loading={historyLoading}
                            pagination={{ pageSize: 10, showSizeChanger: true, showQuickJumper: true, showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} scans` }}
                            expandable={{
                                expandedRowKeys,
                                onExpand: handleRowExpand,
                                expandIcon: ({ expanded, onExpand, record }) => (
                                    <span onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#1890ff', padding: '4px' }}>
                                        {expanded ? <DownOutlined /> : <RightOutlined />}
                                    </span>
                                ),
                                expandedRowRender: (record) => {
                                    if (loadingRows.has(record.id)) {
                                        return (
                                            <div style={{ padding: '40px', textAlign: 'center' }}>
                                                <SyncOutlined spin style={{ fontSize: '24px', color: '#1890ff' }} />
                                                <p style={{ marginTop: '12px', color: '#666' }}>Loading scan results...</p>
                                            </div>
                                        );
                                    }
                                    const results = loadedResults[record.id];
                                    let formattedResults = 'No results available.';
                                    if (results) {
                                        if (typeof results === 'string') {
                                            formattedResults = results;
                                        } else if (results.analysis) {
                                            formattedResults = results.analysis;
                                        } else if (results.output) {
                                            formattedResults = JSON.stringify(results.output, null, 2);
                                        } else if (results.error) {
                                            formattedResults = `Error: ${results.error}`;
                                        } else {
                                            formattedResults = JSON.stringify(results, null, 2);
                                        }
                                    }
                                    return (
                                        <div className="expanded-results-wrapper">
                                            <div className="expanded-results-content">
                                                {formattedResults}
                                            </div>
                                        </div>
                                    );
                                },
                            }}
                            scroll={{ x: 1000 }}
                            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No scan results yet. Upload a ZIP file or enter a GitHub URL and run a scan." /> }}
                        />
                        )}
                    </div>
                </div>
            </div>

            {/* Schedule Scan Modal */}
            <ScheduleScanModal
                open={scheduleModalVisible}
                onClose={() => setScheduleModalVisible(false)}
                scannerType="semgrep"
                scanTarget={scheduleTarget}
                scanConfig={scheduleScanConfig}
            />

            {/* Legal Disclaimer Modal */}
            <ScannerLegalModal open={legalModalVisible} scannerName={legalScannerName} onOk={legalHandleOk} onCancel={legalHandleCancel} />
        </div>
    );
};

export default SemgrepPage;
