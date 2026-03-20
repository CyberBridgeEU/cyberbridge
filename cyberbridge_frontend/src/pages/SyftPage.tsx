import { notification, Button, message, Radio, Tag, Table, Tooltip, Badge, Empty, Input, Card, Row, Col, Select } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { useEffect, useState, useRef } from "react";
import useSyftStore from "../store/useSyftStore.ts";
import { UploadOutlined, ProfileOutlined, HistoryOutlined, DeleteOutlined, ReloadOutlined, RadarChartOutlined, RightOutlined, DownOutlined, GithubOutlined, LockOutlined, FolderOpenOutlined, PlayCircleOutlined, ClearOutlined, AppstoreOutlined, UnorderedListOutlined, SearchOutlined, SyncOutlined, ScheduleOutlined, StopOutlined, FileSearchOutlined, SafetyOutlined, BulbOutlined, CheckCircleOutlined, RobotOutlined, TagsOutlined, DatabaseOutlined } from '@ant-design/icons';
import ScannerGuideWizard, { GuideStep } from "../components/ScannerGuideWizard.tsx";
import ScheduleScanModal from "../components/ScheduleScanModal.tsx";
import html2pdf from 'html2pdf.js';
import ScannerLegalModal from "../components/ScannerLegalModal.tsx";
import { useScannerLegalConfirmation } from "../utils/scannerLegalConfirmation.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import { SbomAnalysisInfo } from "../constants/infoContent.tsx";
import { trackPdfDownload } from '../utils/trackPdfDownload';
import useAuthStore from '../store/useAuthStore';
import useAssetStore from '../store/useAssetStore';
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { ScannerHistoryGridColumns, prepareHistoryTableData, ScannerHistoryRecord } from "../constants/ScannerHistoryGridColumns.tsx";
import {
    saveScannerHistory,
    fetchScannerHistory,
    fetchScannerHistoryDetails,
    deleteScannerHistoryRecord,
    fetchCurrentUserDetails,
    parseHistoryResults,
    clearScannerHistory,
    assignAssetToScannerHistory
} from "../utils/scannerHistoryUtils.ts";

const SyftPage = () => {
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
        cancelScan
    } = useSyftStore();

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    const { user } = useAuthStore();
    const { assets, fetchAssets } = useAssetStore();

    // Input method: 'upload' or 'github'
    const [inputMethod, setInputMethod] = useState<'upload' | 'github'>('upload');

    // State for form inputs
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [githubUrl, setGithubUrl] = useState<string>('');
    const [githubToken, setGithubToken] = useState<string>('');
    const [isPrivateRepo, setIsPrivateRepo] = useState<boolean>(false);
    const [useLlm, setUseLlm] = useState<boolean>(false);

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

    const openScheduleModal = (target: string) => {
        setScheduleTarget(target);
        setScheduleModalVisible(true);
    };

    const handleScheduleFromHistory = (record: ScannerHistoryRecord) => {
        openScheduleModal(record.scan_target);
    };

    // ==================== Scanner Guide Steps ====================
    const syftGuideSteps: GuideStep[] = [
        {
            title: 'Overview',
            icon: <ProfileOutlined />,
            description: 'What is SBOM?',
            content: {
                heading: 'Software Bill of Materials (SBOM)',
                body: 'SBOM Generator uses Syft to create a comprehensive inventory of all software components in your project. An SBOM lists every library, package, and dependency — including transitive dependencies — providing full transparency into your software supply chain.',
                tip: 'SBOMs are increasingly required by regulations (EU CRA, US Executive Order 14028). Generating them proactively prepares you for compliance requirements.'
            }
        },
        {
            title: 'Input',
            icon: <FolderOpenOutlined />,
            description: 'How to provide your project',
            content: {
                heading: 'Input Methods',
                body: 'Provide your project for SBOM generation in one of two ways:',
                infoRows: [
                    { icon: <UploadOutlined />, iconBg: '#0f386a', text: <span><strong>ZIP Upload</strong> - Upload a ZIP archive of your project. Syft analyses all package manifests, lock files, and binaries to catalogue components.</span> },
                    { icon: <GithubOutlined />, iconBg: '#1f2937', text: <span><strong>GitHub Repository</strong> - Provide a GitHub repository URL. Supports both public and private repos (with token authentication).</span> },
                    { icon: <LockOutlined />, iconBg: '#8b5cf6', text: <span><strong>Private Repos</strong> - For private repositories, enable the "Private Repository" toggle and provide a GitHub Personal Access Token.</span> }
                ],
                tip: 'Syft detects components across multiple ecosystems (npm, PyPI, Maven, Go modules, etc.) from a single scan.'
            }
        },
        {
            title: 'Analysis',
            icon: <RobotOutlined />,
            description: 'LLM vs Fast mode',
            content: {
                heading: 'Analysis Mode',
                body: 'Choose how your SBOM results are processed:',
                infoRows: [
                    { icon: <RobotOutlined />, iconBg: '#8b5cf6', text: <span><strong>LLM Analysis</strong> - AI analyses the SBOM to identify supply chain risks, licensing concerns, outdated components, and provides a security posture summary.</span> },
                    { icon: <RadarChartOutlined />, iconBg: '#10b981', text: <span><strong>Fast Results</strong> - Returns the raw component inventory immediately. Lists packages, versions, types, PURLs, and licenses without AI interpretation.</span> }
                ],
                tip: 'Use LLM Analysis for supply chain risk assessments. Use Fast Results when you just need the component inventory.'
            }
        },
        {
            title: 'Results',
            icon: <FileSearchOutlined />,
            description: 'Understanding SBOM output',
            content: {
                heading: 'Reading Results',
                body: 'The SBOM output provides a detailed inventory of all discovered software components:',
                infoRows: [
                    { icon: <TagsOutlined />, iconBg: '#0f386a', text: <span><strong>Package Name & Version</strong> - Each component listed with its exact version. Helps track what\'s deployed in your software.</span> },
                    { icon: <DatabaseOutlined />, iconBg: '#8b5cf6', text: <span><strong>Component Type</strong> - Categorised as npm, PyPI, Maven, Go, Gem, etc. Colour-coded tags for easy identification.</span> },
                    { icon: <SafetyOutlined />, iconBg: '#10b981', text: <span><strong>PURL</strong> - Package URL — a universal identifier for the component (e.g. pkg:npm/express@4.18.2). Used for cross-referencing with vulnerability databases.</span> },
                    { icon: <CheckCircleOutlined />, iconBg: '#f59e0b', text: <span><strong>License</strong> - The open source license of each component. Important for legal compliance and IP risk assessment.</span> }
                ],
                tip: 'You can assign SBOM records to registered assets to maintain a clear mapping of which components belong to which product.'
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
                    'Generate SBOMs for every release to maintain an up-to-date inventory of your software components.',
                    'Use the asset assignment feature to link SBOMs to specific products for traceability.',
                    'Cross-reference SBOM components with OSV dependency scanning to identify which components have known vulnerabilities.',
                    'Review component licenses to ensure compliance with your organisation\'s open source policy.',
                    'Enable LLM Analysis for AI-powered supply chain risk insights and licensing conflict detection.',
                    'Export SBOMs to PDF for regulatory compliance documentation (EU CRA, NIST, etc.).'
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
            const history = await fetchScannerHistory('syft', 100);
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
            'Are you sure you want to delete all SBOM scan history records?\n\nThis action cannot be undone.'
        );

        if (confirmed) {
            setHistoryLoading(true);
            const result = await clearScannerHistory('syft');

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

    // Handle asset assignment
    const handleAssetAssign = async (historyId: string, assetId: string | null) => {
        const result = await assignAssetToScannerHistory(historyId, assetId);
        if (result.success) {
            // Optimistically update local state
            setScannerHistory(prev => prev.map(record => {
                if (record.id === historyId) {
                    const asset = assetId ? assets.find(a => a.id === assetId) : null;
                    return { ...record, asset_id: assetId, asset_name: asset?.name || null };
                }
                return record;
            }));
        } else {
            api.error({
                message: 'Assignment Failed',
                description: result.error || 'Failed to assign asset.',
                duration: 4
            });
        }
    };

    // Search filtered history
    const searchFilteredHistory = scannerHistory.filter(record =>
        record.scan_target?.toLowerCase().includes(historySearchText.toLowerCase()) ||
        record.scan_type?.toLowerCase().includes(historySearchText.toLowerCase()) ||
        record.status?.toLowerCase().includes(historySearchText.toLowerCase()) ||
        record.user_email?.toLowerCase().includes(historySearchText.toLowerCase()) ||
        record.asset_name?.toLowerCase().includes(historySearchText.toLowerCase())
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

    // Format timestamp helper
    const formatTimestampLocal = (timestamp: string): string => {
        return new Date(timestamp).toLocaleString();
    };

    // History Card component
    const HistoryCard = ({ record }: { record: ScannerHistoryRecord }) => {
        return (
            <Card
                hoverable
                style={{ height: '100%' }}
                bodyStyle={{ padding: '16px' }}
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
                    {record.asset_name && <Tag color="cyan">{record.asset_name}</Tag>}
                </div>

                <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
                    {record.user_email && <div>By: {record.user_email}</div>}
                    {record.created_at && <div>{formatTimestampLocal(record.created_at)}</div>}
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

    // Load history and assets on mount
    useEffect(() => {
        loadScannerHistory();
        fetchAssets();
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
                            scanner_type: 'syft',
                            scan_target: target,
                            scan_type: 'sbom_scan',
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
    }, [scanResults, loading, user, scanStartTime, selectedFile, inputMethod, githubUrl]);

    // Track scan start
    useEffect(() => {
        if (loading && !scanStartTime) {
            setScanStartTime(Date.now());
        }
    }, [loading, scanStartTime]);

    // Reference to the file input element
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Handle file upload
    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (files && files.length > 0) {
            const file = files[0];
            // Check if the file is a ZIP file
            if (file.type !== 'application/zip' && !file.name.endsWith('.zip')) {
                message.error(`${file.name} is not a ZIP file`);
                // Reset the file input
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
        const accepted = await confirmScanLegalDisclaimer('SBOM Analysis');
        if (!accepted) return;

        if (inputMethod === 'upload') {
            if (!selectedFile) {
                api.error({
                    message: 'Missing File',
                    description: 'Please upload a ZIP file to scan.',
                    duration: 4,
                });
                return;
            }

            const success = await scanZipFile(selectedFile, useLlm);

            if (success) {
                api.success({
                    message: 'SBOM Generated',
                    description: 'The SBOM generation has been completed successfully.',
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
            const success = await scanGithubRepo(githubUrl, useLlm, isPrivateRepo ? githubToken : undefined);
            if (success) {
                api.success({
                    message: 'SBOM Generated',
                    description: 'The GitHub repository SBOM generation has been completed successfully.',
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
        clearResults();

        // Reset the file input
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    // Extract components from scan results for the SBOM table
    const getComponents = () => {
        if (!scanResults) return [];
        const rawData = scanResults.raw_data || scanResults;
        const components = rawData?.components || [];
        return components.map((comp: any, index: number) => ({
            key: index,
            name: comp.name || 'unknown',
            version: comp.version || 'unknown',
            type: comp.type || 'unknown',
            purl: comp.purl || '',
            licenses: (comp.licenses || []).map((l: any) => l?.license?.id || l?.license?.name || '').filter(Boolean).join(', ')
        }));
    };

    // SBOM components table columns
    const sbomColumns = [
        {
            title: 'Package Name',
            dataIndex: 'name',
            key: 'name',
            sorter: (a: any, b: any) => a.name.localeCompare(b.name),
            ellipsis: true,
        },
        {
            title: 'Version',
            dataIndex: 'version',
            key: 'version',
            width: 120,
        },
        {
            title: 'Type',
            dataIndex: 'type',
            key: 'type',
            width: 120,
            render: (type: string) => {
                const colorMap: Record<string, string> = {
                    library: 'blue',
                    framework: 'purple',
                    application: 'green',
                    file: 'orange',
                    'operating-system': 'red',
                };
                return <Tag color={colorMap[type] || 'default'}>{type}</Tag>;
            },
            filters: [
                { text: 'library', value: 'library' },
                { text: 'framework', value: 'framework' },
                { text: 'application', value: 'application' },
                { text: 'file', value: 'file' },
            ],
            onFilter: (value: any, record: any) => record.type === value,
        },
        {
            title: 'PURL',
            dataIndex: 'purl',
            key: 'purl',
            ellipsis: true,
            render: (purl: string) => (
                <Tooltip title={purl}>
                    <span style={{ fontSize: '12px', color: '#8c8c8c' }}>{purl || '-'}</span>
                </Tooltip>
            ),
        },
        {
            title: 'License',
            dataIndex: 'licenses',
            key: 'licenses',
            width: 150,
            render: (licenses: string) => licenses || '-',
        },
    ];

    // Get summary info from scan results
    const getSummary = () => {
        if (!scanResults) return null;
        const summary = scanResults.summary;
        if (summary) return summary;
        // Fallback: compute from raw_data
        const rawData = scanResults.raw_data || scanResults;
        const components = rawData?.components || [];
        const byType: Record<string, number> = {};
        const licenses = new Set<string>();
        for (const comp of components) {
            const t = comp.type || 'unknown';
            byType[t] = (byType[t] || 0) + 1;
            for (const l of comp.licenses || []) {
                const id = l?.license?.id || l?.license?.name;
                if (id) licenses.add(id);
            }
        }
        return {
            total_components: components.length,
            by_type: byType,
            licenses: Array.from(licenses),
        };
    };

    // Format scan results for display (LLM analysis text)
    const formatResults = () => {
        if (!scanResults) return 'No scan results available.';

        if (scanResults.success === false) {
            return `Error: ${scanResults.error || 'Unknown error occurred'}`;
        }

        if (scanResults.analysis) {
            return scanResults.analysis;
        }

        if (scanResults.output) {
            return JSON.stringify(scanResults.output, null, 2);
        }

        return 'No results available';
    };

    // Handle export of scan results to HTML or PDF
    const handleExport = (format: 'html' | 'pdf') => {
        const resultsToExport = scanResults?.analysis || scanResults?.output;
        if (!scanResults || !resultsToExport) {
            api.error({
                message: 'Export Failed',
                description: 'No scan results available to export.',
                duration: 4,
            });
            return;
        }

        const htmlContent = `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SBOM Scan Results</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 20px;
                }
                h1 {
                    color: #0f386a;
                }
                .results {
                    background: #f8f8f8;
                    padding: 15px;
                    border-radius: 8px;
                    white-space: pre-line;
                    word-wrap: break-word;
                    font-family: monospace;
                }
            </style>
        </head>
        <body>
            <h1>SBOM Analysis Results</h1>
            <div class="results">
                ${resultsToExport}
            </div>
        </body>
        </html>
        `;

        if (format === 'html') {
            const blob = new Blob([htmlContent], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'sbom-scan-results.html';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 100);
            api.success({
                message: 'Export Successful',
                description: 'Scan results have been exported to HTML.',
                duration: 4,
            });
        } else if (format === 'pdf') {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = htmlContent;
            document.body.appendChild(tempDiv);

            const options = {
                margin: 10,
                filename: 'sbom-scan-results.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2 },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };

            html2pdf().from(tempDiv).set(options).save().then(async () => {
                const { getAuthHeader } = useAuthStore.getState();
                await trackPdfDownload('syft', getAuthHeader);
                document.body.removeChild(tempDiv);
                api.success({
                    message: 'Export Successful',
                    description: 'Scan results have been exported to PDF.',
                    duration: 4,
                });
            }).catch((error: any) => {
                console.error('PDF generation error:', error);
                document.body.removeChild(tempDiv);
                api.error({
                    message: 'Export Failed',
                    description: 'Failed to generate PDF. Please try HTML format instead.',
                    duration: 4,
                });
            });
        }
    };

    // Handle export history record to PDF
    const handleExportHistory = async (record: ScannerHistoryRecord) => {
        try {
            // Fetch full details if results not already loaded
            let results = loadedResults[record.id];
            if (!results) {
                const fullDetails = await fetchScannerHistoryDetails(record.id);
                if (fullDetails && fullDetails.results) {
                    results = parseHistoryResults(fullDetails.results);
                    setLoadedResults(prev => ({ ...prev, [record.id]: results }));
                }
            }
            const resultsToExport =
                (typeof results === 'string' ? results : null) ||
                results?.analysis ||
                results?.output ||
                results;

            if (!resultsToExport) {
                api.warning({
                    message: 'No Results Available',
                    description: 'This history entry does not include scan results to export.',
                    duration: 4
                });
                return;
            }

            const htmlContent = `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>SBOM Scan Results - ${record.scan_target}</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        margin: 20px;
                    }
                    h1 {
                        color: #0f386a;
                    }
                    .metadata {
                        background: #e7f3ff;
                        padding: 10px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }
                    .results {
                        background: #f8f8f8;
                        padding: 15px;
                        border-radius: 8px;
                        white-space: pre-line;
                        word-wrap: break-word;
                        font-family: monospace;
                    }
                </style>
            </head>
            <body>
                <h1>SBOM Analysis Results</h1>
                <div class="metadata">
                    <strong>Target:</strong> ${record.scan_target}<br>
                    <strong>Scan Type:</strong> ${record.scan_type || 'N/A'}<br>
                    <strong>Timestamp:</strong> ${new Date(record.timestamp).toLocaleString()}<br>
                    <strong>Duration:</strong> ${record.scan_duration ? record.scan_duration.toFixed(2) + 's' : 'N/A'}
                </div>
                <div class="results">
                    ${typeof resultsToExport === 'string' ? resultsToExport : JSON.stringify(resultsToExport, null, 2)}
                </div>
            </body>
            </html>
            `;

            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = htmlContent;
            document.body.appendChild(tempDiv);

            const timestamp = new Date(record.timestamp).toISOString().replace(/[:.]/g, '-').slice(0, 19);
            const filename = `sbom-scan-${record.scan_target.replace(/[^a-z0-9]/gi, '_')}-${timestamp}.pdf`;

            const options = {
                margin: 10,
                filename: filename,
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2 },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };

            await html2pdf().from(tempDiv).set(options).save();
            const { getAuthHeader } = useAuthStore.getState();
            await trackPdfDownload('syft', getAuthHeader);
            document.body.removeChild(tempDiv);
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

    const components = getComponents();
    const summary = getSummary();

    return (
        <div>
            {contextHolder}
            <div className={'page-parent'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys} onOpenChange={menuHighlighting.onOpenChange} />
                <div className={'page-content'}>
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <ProfileOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="SBOM Generator"
                                infoContent={SbomAnalysisInfo}
                                className="page-title"
                            />
                        </div>
                        <div className="page-header-right">
                            <ScannerGuideWizard
                                steps={syftGuideSteps}
                                title="SBOM Generator Guide"
                                icon={<ProfileOutlined />}
                                buttonLabel="Scanner Guide"
                            />
                        </div>
                    </div>

                    {/* Source Code Input Section */}
                    <div className="page-section">
                        <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <FolderOpenOutlined style={{ color: '#1890ff' }} />
                            Source Code
                        </h3>

                        {/* Input Method Tabs */}
                        <div style={{ display: 'flex', gap: 0, marginBottom: '20px' }}>
                            <button
                                onClick={() => setInputMethod('upload')}
                                style={{
                                    padding: '12px 24px',
                                    border: '1px solid #e8e8e8',
                                    background: inputMethod === 'upload' ? '#1890ff' : '#f5f5f5',
                                    cursor: 'pointer',
                                    fontWeight: 500,
                                    color: inputMethod === 'upload' ? 'white' : '#666',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    transition: 'all 0.2s ease',
                                    borderRadius: '8px 0 0 8px',
                                    borderColor: inputMethod === 'upload' ? '#1890ff' : '#e8e8e8'
                                }}
                            >
                                <UploadOutlined /> Upload ZIP File
                            </button>
                            <button
                                onClick={() => setInputMethod('github')}
                                style={{
                                    padding: '12px 24px',
                                    border: '1px solid #e8e8e8',
                                    borderLeft: 'none',
                                    background: inputMethod === 'github' ? '#1890ff' : '#f5f5f5',
                                    cursor: 'pointer',
                                    fontWeight: 500,
                                    color: inputMethod === 'github' ? 'white' : '#666',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    transition: 'all 0.2s ease',
                                    borderRadius: '0 8px 8px 0',
                                    borderColor: inputMethod === 'github' ? '#1890ff' : '#e8e8e8'
                                }}
                            >
                                <GithubOutlined /> GitHub Repository
                            </button>
                        </div>

                        {/* File Upload Section */}
                        {inputMethod === 'upload' && (
                            <div
                                style={{
                                    border: `2px dashed ${selectedFile ? '#52c41a' : '#d9d9d9'}`,
                                    borderRadius: '10px',
                                    padding: '40px 20px',
                                    textAlign: 'center',
                                    backgroundColor: selectedFile ? '#f6ffed' : '#fafafa',
                                    cursor: 'pointer',
                                    transition: 'all 0.3s ease'
                                }}
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <div style={{ fontSize: '48px', color: selectedFile ? '#52c41a' : '#0f386a', marginBottom: '16px' }}>
                                    <UploadOutlined />
                                </div>
                                <p style={{ fontSize: '16px', fontWeight: 'bold', margin: '0 0 8px 0', color: '#262626' }}>
                                    {selectedFile ? selectedFile.name : 'Click to select a ZIP file'}
                                </p>
                                <p style={{ fontSize: '14px', color: '#8c8c8c', margin: 0 }}>
                                    {selectedFile ? 'Click to change file' : 'Upload a ZIP file containing source code to generate a Software Bill of Materials (SBOM)'}
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
                                <div style={{ marginBottom: '16px' }}>
                                    <label style={{ fontSize: '13px', fontWeight: 500, color: '#555', display: 'block', marginBottom: '8px' }}>
                                        GitHub Repository URL<span style={{ color: '#ff4d4f', marginLeft: '4px' }}>*</span>
                                    </label>
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
                                    onClick={() => setIsPrivateRepo(!isPrivateRepo)}
                                    style={{
                                        display: 'inline-flex',
                                        alignItems: 'center',
                                        gap: '10px',
                                        marginBottom: '16px',
                                        cursor: 'pointer'
                                    }}
                                >
                                    <div style={{
                                        position: 'relative',
                                        width: '44px',
                                        height: '24px',
                                        background: isPrivateRepo ? '#1890ff' : '#d9d9d9',
                                        borderRadius: '12px',
                                        transition: 'background 0.2s ease',
                                        flexShrink: 0
                                    }}>
                                        <div style={{
                                            position: 'absolute',
                                            top: '2px',
                                            left: isPrivateRepo ? '22px' : '2px',
                                            width: '20px',
                                            height: '20px',
                                            background: 'white',
                                            borderRadius: '50%',
                                            boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                                            transition: 'left 0.2s ease'
                                        }} />
                                    </div>
                                    <span style={{ fontSize: '14px', color: '#555', userSelect: 'none' }}>
                                        Private repository
                                        {isPrivateRepo && <LockOutlined style={{ marginLeft: '6px', color: '#fa8c16' }} />}
                                    </span>
                                </div>

                                {/* Token Input (shown when private repo is selected) */}
                                {isPrivateRepo && (
                                    <div style={{ marginBottom: '16px' }}>
                                        <label style={{ fontSize: '13px', fontWeight: 500, color: '#555', display: 'block', marginBottom: '8px' }}>
                                            GitHub Personal Access Token<span style={{ color: '#ff4d4f', marginLeft: '4px' }}>*</span>
                                        </label>
                                        <Input.Password
                                            size="large"
                                            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                                            prefix={<LockOutlined style={{ color: '#999' }} />}
                                            value={githubToken}
                                            onChange={(e) => setGithubToken(e.target.value)}
                                            style={{ borderRadius: '8px' }}
                                        />
                                        <p style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '8px' }}>
                                            Create a token at <a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer" style={{ color: '#1890ff' }}>GitHub Settings &rarr; Developer settings &rarr; Personal access tokens</a>.
                                            The token needs <strong>repo</strong> scope for private repositories.
                                        </p>
                                    </div>
                                )}

                                {!isPrivateRepo && (
                                    <p style={{ fontSize: '13px', color: '#8c8c8c', margin: 0 }}>
                                        Enter a public GitHub repository URL. The repository will be cloned and analyzed to generate an SBOM.
                                    </p>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Scan Control Section */}
                    <div className="page-section">
                        <h3 className="section-title">Scan Control</h3>

                        <div className="form-row">
                            <Radio.Group
                                value={useLlm ? 'llm' : 'fast'}
                                onChange={(e) => setUseLlm(e.target.value === 'llm')}
                                size="small"
                                buttonStyle="solid"
                            >
                                <Radio.Button value="llm">LLM Analysis</Radio.Button>
                                <Radio.Button value="fast">Fast Results</Radio.Button>
                            </Radio.Group>
                        </div>

                        <div className="form-row">
                            <div className="control-group">
                                <button
                                    className="add-button"
                                    onClick={handleRunScan}
                                    disabled={loading || (inputMethod === 'upload'
                                        ? !selectedFile
                                        : !githubUrl.trim() || (isPrivateRepo && !githubToken.trim()))}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    <PlayCircleOutlined />
                                    {loading ? 'Generating SBOM...' : 'Generate SBOM'}
                                </button>
                                {loading && (
                                    <button
                                        className="add-button"
                                        onClick={cancelScan}
                                        style={{ display: 'flex', alignItems: 'center', gap: '8px', backgroundColor: '#ff4d4f', borderColor: '#ff4d4f' }}
                                    >
                                        <StopOutlined />
                                        Cancel Scan
                                    </button>
                                )}
                                <button
                                    className="secondary-button"
                                    onClick={handleClear}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    <ClearOutlined />
                                    Clear
                                </button>
                                <button
                                    className="secondary-button"
                                    onClick={() => openScheduleModal(inputMethod === 'github' ? githubUrl : (selectedFile?.name || ''))}
                                    disabled={inputMethod === 'github' ? !githubUrl.trim() : !selectedFile}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#722ed1', borderColor: '#722ed1' }}
                                >
                                    <ScheduleOutlined />
                                    Schedule
                                </button>
                            </div>
                        </div>

                        {loading && (
                            <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f0f8ff', border: '1px solid #91caff', borderRadius: '8px' }}>
                                <p style={{ margin: 0, color: '#1890ff', fontSize: '14px' }}>
                                    {inputMethod === 'github'
                                        ? 'Cloning repository and generating SBOM... This may take several minutes.'
                                        : 'Generating SBOM... Analyzing project dependencies and components.'}
                                </p>
                            </div>
                        )}
                    </div>

                    {/* SBOM Components Table */}
                    {scanResults && components.length > 0 && (
                        <div className="page-section">
                            <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <ProfileOutlined style={{ color: '#1890ff' }} />
                                SBOM Components
                                <Badge count={components.length} style={{ backgroundColor: '#1890ff' }} />
                            </h3>

                            {/* Summary Cards */}
                            {summary && (
                                <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
                                    <Col xs={24} sm={8}>
                                        <Card size="small" style={{ textAlign: 'center' }}>
                                            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#1890ff' }}>
                                                {summary.total_components}
                                            </div>
                                            <div style={{ color: '#8c8c8c', fontSize: '12px' }}>Total Components</div>
                                        </Card>
                                    </Col>
                                    <Col xs={24} sm={8}>
                                        <Card size="small" style={{ textAlign: 'center' }}>
                                            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#52c41a' }}>
                                                {Object.keys(summary.by_type || {}).length}
                                            </div>
                                            <div style={{ color: '#8c8c8c', fontSize: '12px' }}>Component Types</div>
                                        </Card>
                                    </Col>
                                    <Col xs={24} sm={8}>
                                        <Card size="small" style={{ textAlign: 'center' }}>
                                            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#faad14' }}>
                                                {(summary.licenses || []).length}
                                            </div>
                                            <div style={{ color: '#8c8c8c', fontSize: '12px' }}>Unique Licenses</div>
                                        </Card>
                                    </Col>
                                </Row>
                            )}

                            <Table
                                columns={sbomColumns}
                                dataSource={components}
                                pagination={{
                                    pageSize: 15,
                                    showSizeChanger: true,
                                    showQuickJumper: true,
                                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} components`
                                }}
                                scroll={{ x: 900 }}
                                size="small"
                            />

                            {/* LLM Analysis */}
                            {scanResults.analysis && (
                                <div style={{ marginTop: '16px' }}>
                                    <h4 style={{ marginBottom: '8px' }}>AI Supply Chain Analysis</h4>
                                    <div style={{
                                        backgroundColor: '#f5f5f5',
                                        padding: '16px',
                                        borderRadius: '6px',
                                        maxHeight: '400px',
                                        overflow: 'auto',
                                        fontFamily: 'monospace',
                                        fontSize: '13px',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word'
                                    }}>
                                        {scanResults.analysis}
                                    </div>

                                    {/* Export Buttons */}
                                    <div style={{ marginTop: '12px', display: 'flex', gap: '8px' }}>
                                        <Button size="small" onClick={() => handleExport('html')}>Export HTML</Button>
                                        <Button size="small" onClick={() => handleExport('pdf')}>Export PDF</Button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Scan Results / History Section */}
                    <div className="page-section">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                            <h3 className="section-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <HistoryOutlined style={{ color: '#1890ff' }} />
                                Scan Results
                                {scannerHistory.length > 0 && (
                                    <Badge count={scannerHistory.length} style={{ backgroundColor: '#1890ff' }} />
                                )}
                                {loading && (
                                    <Tag icon={<RadarChartOutlined spin />} color="processing">
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
                            <div style={{ display: 'flex', border: '1px solid #d9d9d9', borderRadius: '6px', overflow: 'hidden' }}>
                                <button
                                    onClick={() => setHistoryViewMode('grid')}
                                    style={{
                                        border: 'none',
                                        padding: '6px 12px',
                                        cursor: 'pointer',
                                        backgroundColor: historyViewMode === 'grid' ? '#1890ff' : 'white',
                                        color: historyViewMode === 'grid' ? 'white' : '#595959',
                                    }}
                                >
                                    <AppstoreOutlined />
                                </button>
                                <button
                                    onClick={() => setHistoryViewMode('list')}
                                    style={{
                                        border: 'none',
                                        borderLeft: '1px solid #d9d9d9',
                                        padding: '6px 12px',
                                        cursor: 'pointer',
                                        backgroundColor: historyViewMode === 'list' ? '#1890ff' : 'white',
                                        color: historyViewMode === 'list' ? 'white' : '#595959',
                                    }}
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
                            columns={(() => {
                                const baseCols = ScannerHistoryGridColumns(handleExportHistory, handleDeleteRecord, handleScheduleFromHistory);
                                const actionsIdx = baseCols.findIndex(c => c.key === 'actions');
                                const assignedAssetIds = new Set(
                                    scannerHistory
                                        .filter(r => r.asset_id)
                                        .map(r => r.asset_id!)
                                );
                                const assetColumn = {
                                    title: 'Asset',
                                    key: 'asset',
                                    dataIndex: 'asset_id',
                                    width: 200,
                                    render: (_: any, record: ScannerHistoryRecord) => (
                                        <Select
                                            size="small"
                                            placeholder="Assign asset..."
                                            value={record.asset_id || undefined}
                                            onChange={(value: string) => handleAssetAssign(record.id, value || null)}
                                            onClear={() => handleAssetAssign(record.id, null)}
                                            allowClear
                                            showSearch
                                            optionFilterProp="label"
                                            style={{ width: '100%' }}
                                            options={assets.map(a => ({
                                                value: a.id,
                                                label: a.name,
                                                disabled: assignedAssetIds.has(a.id) && a.id !== record.asset_id
                                            }))}
                                        />
                                    )
                                };
                                const cols = [...baseCols];
                                cols.splice(actionsIdx >= 0 ? actionsIdx : cols.length, 0, assetColumn);
                                return cols;
                            })() as any}
                            dataSource={prepareHistoryTableData(searchFilteredHistory)}
                            loading={historyLoading}
                            pagination={{
                                pageSize: 10,
                                showSizeChanger: true,
                                showQuickJumper: true,
                                showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} scans`
                            }}
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
                                        <div style={{ padding: '16px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                                            <div style={{
                                                backgroundColor: '#f5f5f5',
                                                padding: '16px',
                                                borderRadius: '6px',
                                                maxHeight: '400px',
                                                overflow: 'auto',
                                                fontFamily: 'monospace',
                                                fontSize: '13px',
                                                whiteSpace: 'pre-wrap',
                                                wordBreak: 'break-word'
                                            }}>
                                                {formattedResults}
                                            </div>
                                        </div>
                                    );
                                },
                            }}
                            scroll={{ x: 1000 }}
                            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No scan results yet. Upload a ZIP file and generate an SBOM." /> }}
                        />
                        )}
                    </div>
                </div>
            </div>

            {/* Schedule Scan Modal */}
            <ScheduleScanModal
                open={scheduleModalVisible}
                onClose={() => setScheduleModalVisible(false)}
                scannerType="syft"
                scanTarget={scheduleTarget}
            />

            {/* Legal Disclaimer Modal */}
            <ScannerLegalModal open={legalModalVisible} scannerName={legalScannerName} onOk={legalHandleOk} onCancel={legalHandleCancel} />
        </div>
    );
};

export default SyftPage;
