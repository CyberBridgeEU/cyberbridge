import { notification, Select, SelectProps, Dropdown, Button, message, Radio, Modal, Tag, Table, Progress, Collapse, List, Card, Divider, Tooltip, Badge, Empty, Spin, Row, Col, Input } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { useEffect, useState, useRef } from "react";
import useZapStore from "../store/useZapStore.ts";
import useNmapStore from "../store/useNmapStore.ts";
import useSemgrepStore from "../store/useSemgrepStore.ts";
import useOsvStore from "../store/useOsvStore.ts";
import useAuthStore from '../store/useAuthStore';
import useUserStore from '../store/useUserStore';
import useSettingsStore from '../store/useSettingsStore';
import useAssetStore from '../store/useAssetStore';
import RemediationModal from "../components/RemediationModal.tsx";
import ScannerLegalModal from "../components/ScannerLegalModal.tsx";
import { useScannerLegalConfirmation } from "../utils/scannerLegalConfirmation.ts";
import {
    ExportOutlined,
    DownOutlined,
    RightOutlined,
    RadarChartOutlined,
    HistoryOutlined,
    ExclamationCircleOutlined,
    GlobalOutlined,
    ApiOutlined,
    PlayCircleOutlined,
    ClearOutlined,
    StopOutlined,
    ClockCircleOutlined,
    DeleteOutlined,
    ReloadOutlined,
    EyeOutlined,
    FilePdfOutlined,
    RobotOutlined,
    QuestionCircleOutlined,
    SyncOutlined,
    AppstoreOutlined,
    UnorderedListOutlined,
    SearchOutlined,
    ScheduleOutlined
} from '@ant-design/icons';
import html2pdf from 'html2pdf.js';
import InfoTitle from "../components/InfoTitle.tsx";
import { SecurityScannersInfo } from "../constants/infoContent.tsx";
import { trackPdfDownload } from '../utils/trackPdfDownload';
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { ZapGridColumns, prepareZapTableData, onZapTableChange } from "../constants/ZapGridColumns.tsx";
import { ScannerHistoryGridColumns, prepareHistoryTableData, ScannerHistoryRecord } from "../constants/ScannerHistoryGridColumns.tsx";
import {
    saveScannerHistory,
    fetchScannerHistory,
    fetchScannerHistoryDetails,
    fetchCurrentUserDetails,
    parseHistoryResults,
    formatTimestamp,
    clearScannerHistory,
    deleteScannerHistoryRecord
} from "../utils/scannerHistoryUtils.ts";
import { exportZapResultsToPdf } from "../utils/zapPdfUtils.ts";
import { exportNmapResultsToPdf } from "../utils/nmapPdfUtils.ts";
import ScheduleScanModal from "../components/ScheduleScanModal.tsx";
import ScannerGuideWizard, { GuideStep } from "../components/ScannerGuideWizard.tsx";
import {
    ThunderboltOutlined,
    AimOutlined,
    BugOutlined,
    SafetyOutlined,
    WifiOutlined,
    LaptopOutlined,
    CloudServerOutlined,
    AlertOutlined,
    DashboardOutlined,
    BulbOutlined,
    CheckCircleOutlined,
    WarningOutlined,
    FileSearchOutlined
} from '@ant-design/icons';

const SecurityScannersPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    // Legal disclaimer confirmation
    const { visible: legalModalVisible, scannerName: legalScannerName, handleOk: legalHandleOk, handleCancel: legalHandleCancel, confirmScanLegalDisclaimer } = useScannerLegalConfirmation();

    const { user } = useAuthStore();
    const { current_user } = useUserStore();
    const { loadAIFeatureSettings, aiFeatureSettings } = useSettingsStore();

    // AI Remediator state
    const [remediationModalVisible, setRemediationModalVisible] = useState(false);
    const [selectedHistoryForRemediation, setSelectedHistoryForRemediation] = useState<ScannerHistoryRecord | null>(null);
    const [remediatorScannerType, setRemediatorScannerType] = useState<'zap' | 'nmap'>('zap');

    // Active scanner tab
    const [activeScannerTab, setActiveScannerTab] = useState('network');

    // View mode state for ZAP and Nmap history
    const [zapHistoryViewMode, setZapHistoryViewMode] = useState<'grid' | 'list'>('list');
    const [zapHistorySearchText, setZapHistorySearchText] = useState('');
    const [nmapHistoryViewMode, setNmapHistoryViewMode] = useState<'grid' | 'list'>('list');
    const [nmapHistorySearchText, setNmapHistorySearchText] = useState('');

    // ==================== ZAP State ====================
    const {
        targetUrl,
        scanType: zapScanType,
        scanStatus,
        activeScanState,
        alerts,
        loading: zapLoading,
        polling,
        error: zapError,
        setTargetUrl,
        setScanType: setZapScanType,
        startSpiderScan,
        startActiveScan,
        startFullScan,
        startApiScan,
        clearResults: clearZapResults,
        clearAlerts,
        emergencyStop
    } = useZapStore();

    const [emergencyStopModalVisible, setEmergencyStopModalVisible] = useState(false);
    const [zapScannerHistory, setZapScannerHistory] = useState<ScannerHistoryRecord[]>([]);
    const [zapHistoryLoading, setZapHistoryLoading] = useState(false);
    const [zapHistoryModalVisible, setZapHistoryModalVisible] = useState(false);
    const [zapSelectedHistoryRecord, setZapSelectedHistoryRecord] = useState<ScannerHistoryRecord | null>(null);
    const [zapHistoricalResults, setZapHistoricalResults] = useState<any[]>([]);
    const [zapScanStartTime, setZapScanStartTime] = useState<number | null>(null);
    const [zapHistoryExpanded, setZapHistoryExpanded] = useState(false);
    const [zapScanTypeHelpVisible, setZapScanTypeHelpVisible] = useState(false);
    const [zapTargetHelpVisible, setZapTargetHelpVisible] = useState(false);
    const [zapTargetMode, setZapTargetMode] = useState<'custom' | 'asset'>('custom');
    const [zapSelectedAssetId, setZapSelectedAssetId] = useState<string | null>(null);
    // Lazy loading state for expanded row results (ZAP)
    const [zapLoadedResults, setZapLoadedResults] = useState<Record<string, any>>({});
    const [zapLoadingRows, setZapLoadingRows] = useState<Set<string>>(new Set());
    const [zapExpandedRowKeys, setZapExpandedRowKeys] = useState<string[]>([]);

    // ==================== Nmap State ====================
    const {
        basicScan,
        portScan,
        allPortsScan,
        aggressiveScan,
        osScan,
        networkScan,
        stealthScan,
        noPingScan,
        fastScan,
        clearResults: clearNmapResults,
        scanResults: nmapScanResults,
        loading: nmapLoading,
        error: nmapError
    } = useNmapStore();

    const [nmapTarget, setNmapTarget] = useState<string>('');
    const [nmapPorts, setNmapPorts] = useState<string>('');
    const [nmapScanType, setNmapScanType] = useState<string>('basic');
    const [nmapScannerHistory, setNmapScannerHistory] = useState<ScannerHistoryRecord[]>([]);
    const [nmapHistoryLoading, setNmapHistoryLoading] = useState(false);
    const [nmapHistoryModalVisible, setNmapHistoryModalVisible] = useState(false);
    const [nmapSelectedHistoryRecord, setNmapSelectedHistoryRecord] = useState<ScannerHistoryRecord | null>(null);
    const [nmapHistoricalResults, setNmapHistoricalResults] = useState<string>('');
    const [nmapScanStartTime, setNmapScanStartTime] = useState<number | null>(null);
    const [nmapHistoryExpanded, setNmapHistoryExpanded] = useState(false);
    const [nmapScanTypeHelpVisible, setNmapScanTypeHelpVisible] = useState(false);
    const [nmapTargetHelpVisible, setNmapTargetHelpVisible] = useState(false);
    // Lazy loading state for expanded row results
    const [nmapLoadedResults, setNmapLoadedResults] = useState<Record<string, any>>({});
    const [nmapLoadingRows, setNmapLoadingRows] = useState<Set<string>>(new Set());
    const [nmapExpandedRowKeys, setNmapExpandedRowKeys] = useState<string[]>([]);
    const [nmapTargetMode, setNmapTargetMode] = useState<'custom' | 'asset'>('custom');
    const [nmapSelectedAssetId, setNmapSelectedAssetId] = useState<string | null>(null);

    // ==================== Asset Store ====================
    const { assets, fetchAssets } = useAssetStore();

    // ==================== Semgrep State ====================
    const {
        scanZipFile: semgrepScanZipFile,
        clearResults: clearSemgrepResults,
        scanResults: semgrepScanResults,
        loading: semgrepLoading,
        error: semgrepError,
        configOptions: semgrepConfigOptions
    } = useSemgrepStore();

    const [semgrepSelectedFile, setSemgrepSelectedFile] = useState<File | null>(null);
    const [semgrepConfig, setSemgrepConfig] = useState<string>('auto');
    const [semgrepUseLlm, setSemgrepUseLlm] = useState<boolean>(true);
    const [semgrepScannerHistory, setSemgrepScannerHistory] = useState<ScannerHistoryRecord[]>([]);
    const [semgrepHistoryLoading, setSemgrepHistoryLoading] = useState(false);
    const [semgrepHistoryModalVisible, setSemgrepHistoryModalVisible] = useState(false);
    const [semgrepSelectedHistoryRecord, setSemgrepSelectedHistoryRecord] = useState<ScannerHistoryRecord | null>(null);
    const [semgrepHistoricalResults, setSemgrepHistoricalResults] = useState<string>('');
    const [semgrepScanStartTime, setSemgrepScanStartTime] = useState<number | null>(null);
    const semgrepFileInputRef = useRef<HTMLInputElement>(null);

    // ==================== OSV State ====================
    const {
        scanZipFile: osvScanZipFile,
        clearResults: clearOsvResults,
        scanResults: osvScanResults,
        loading: osvLoading,
        error: osvError
    } = useOsvStore();

    const [osvSelectedFile, setOsvSelectedFile] = useState<File | null>(null);
    const [osvUseLlm, setOsvUseLlm] = useState<boolean>(true);
    const [osvScannerHistory, setOsvScannerHistory] = useState<ScannerHistoryRecord[]>([]);
    const [osvHistoryLoading, setOsvHistoryLoading] = useState(false);
    const [osvHistoryModalVisible, setOsvHistoryModalVisible] = useState(false);
    const [osvSelectedHistoryRecord, setOsvSelectedHistoryRecord] = useState<ScannerHistoryRecord | null>(null);
    const [osvHistoricalResults, setOsvHistoricalResults] = useState<string>('');
    const [osvScanStartTime, setOsvScanStartTime] = useState<number | null>(null);
    const osvFileInputRef = useRef<HTMLInputElement>(null);

    // ==================== Schedule State ====================
    const [scheduleModalVisible, setScheduleModalVisible] = useState(false);
    const [scheduleModalScannerType, setScheduleModalScannerType] = useState('');
    const [scheduleModalScanTarget, setScheduleModalScanTarget] = useState('');
    const [scheduleModalScanType, setScheduleModalScanType] = useState<string | undefined>(undefined);
    const [scheduleModalScanConfig, setScheduleModalScanConfig] = useState<Record<string, any> | undefined>(undefined);

    const openScheduleModal = (scannerType: string, scanTarget: string, scanType?: string, scanConfig?: Record<string, any>) => {
        setScheduleModalScannerType(scannerType);
        setScheduleModalScanTarget(scanTarget);
        setScheduleModalScanType(scanType);
        setScheduleModalScanConfig(scanConfig);
        setScheduleModalVisible(true);
    };

    const handleZapScheduleFromHistory = (record: ScannerHistoryRecord) => {
        openScheduleModal('zap', record.scan_target, record.scan_type || undefined);
    };

    const handleNmapScheduleFromHistory = (record: ScannerHistoryRecord) => {
        openScheduleModal('nmap', record.scan_target, record.scan_type || undefined);
    };

    // ==================== Scanner Guide Steps ====================

    const nmapGuideSteps: GuideStep[] = [
        {
            title: 'Overview',
            icon: <RadarChartOutlined />,
            description: 'What is Network Scanning?',
            content: {
                heading: 'Network Vulnerability Scanner',
                body: 'The Network Scanner uses Nmap to discover hosts, open ports, running services, and known vulnerabilities on your network targets. It helps identify potential attack surfaces before they can be exploited.',
                tip: 'Always ensure you have proper authorisation before scanning any target. Unauthorised scanning may violate laws and policies.'
            }
        },
        {
            title: 'Scan Types',
            icon: <ThunderboltOutlined />,
            description: 'Available scan configurations',
            content: {
                heading: 'Vulnerability Scanning',
                body: 'These scan types probe your target for open ports, services, and known vulnerabilities. They are grouped by depth and intrusiveness:',
                infoRows: [
                    { icon: <ThunderboltOutlined />, iconBg: '#10b981', text: <span><strong>Fast Scan</strong> - Scans the top 100 most common ports using Nmap's <code>-F</code> flag. Completes in seconds and gives you a quick snapshot of the most likely open services (HTTP, SSH, FTP, etc.). Best for: initial reconnaissance or when you need rapid results.</span> },
                    { icon: <SafetyOutlined />, iconBg: '#0f386a', text: <span><strong>Basic Scan</strong> - Scans the top 1,000 ports with service version detection (<code>-sV</code>). Identifies not just which ports are open, but what software and version is running on each one. This is the recommended default for most assessments.</span> },
                    { icon: <AimOutlined />, iconBg: '#0ea5e9', text: <span><strong>Specific Port Scan</strong> - Scans only the ports you specify (e.g. <code>80,443,8080</code> or <code>1-1024</code>). Use this when you know exactly which services you want to check or when you need to audit specific infrastructure.</span> },
                    { icon: <AimOutlined />, iconBg: '#8b5cf6', text: <span><strong>Stealth Scan (SYN)</strong> - Sends SYN packets but never completes the TCP 3-way handshake. Because the connection is never fully established, many firewalls and IDS systems won't log it. Use this for stealthy reconnaissance on monitored networks.</span> },
                    { icon: <CloudServerOutlined />, iconBg: '#64748b', text: <span><strong>No Ping Scan</strong> - Skips host discovery and treats the target as online. Useful when ICMP ping is blocked by the target's firewall — the scanner goes directly to port scanning without waiting for a ping response.</span> },
                    { icon: <BugOutlined />, iconBg: '#dc2626', text: <span><strong>Aggressive Scan</strong> - The most comprehensive option. Combines OS detection, version detection, Nmap Scripting Engine (NSE) scripts, and traceroute (<code>-A</code>). Identifies operating systems, runs vulnerability-detection scripts, and maps network paths. Produces the most data but is the most detectable.</span> },
                    { icon: <LaptopOutlined />, iconBg: '#f59e0b', text: <span><strong>OS Detection</strong> - Fingerprints the target's operating system by analysing TCP/IP stack behaviour. Reports the OS family, version, and confidence level. Useful for asset inventory and identifying unpatched operating systems.</span> }
                ],
                tip: 'Start with Fast or Basic Scan for a quick overview. Move to Aggressive Scan for full vulnerability assessment. Use Stealth Scan on monitored networks where detection is a concern.'
            }
        },
        {
            title: 'Discovery',
            icon: <WifiOutlined />,
            description: 'Network & port discovery',
            content: {
                heading: 'Port & Network Discovery',
                body: 'These scan types focus on discovering what exists on your network rather than testing for vulnerabilities:',
                infoRows: [
                    { icon: <WifiOutlined />, iconBg: '#f59e0b', text: <span><strong>Network Discovery (Ping Sweep)</strong> - Sends ICMP echo requests and TCP probes across a range of IPs to find live hosts without performing any port scanning. Ideal for mapping out which devices are active on a subnet (e.g. <code>192.168.1.0/24</code>). Fast and non-intrusive.</span> },
                    { icon: <LaptopOutlined />, iconBg: '#0ea5e9', text: <span><strong>All Ports Scan</strong> - Scans all 65,535 TCP ports on the target, not just the common ones. Services sometimes hide on non-standard ports (e.g. an SSH server on port 2222 or a web server on port 8443). This ensures complete coverage but takes significantly longer than a Fast or Basic scan.</span> }
                ],
                tip: 'Use Network Discovery first to identify live hosts in a subnet, then target individual hosts with deeper scans like Basic or Aggressive.'
            }
        },
        {
            title: 'Targets',
            icon: <AimOutlined />,
            description: 'Target format options',
            content: {
                heading: 'Target Formats',
                body: 'You can specify targets in several formats. The scanner accepts IP addresses, domain names, and network ranges:',
                infoRows: [
                    { icon: <LaptopOutlined />, iconBg: '#0f386a', text: <span><strong>Single IP</strong> - e.g. <code>192.168.1.1</code> — scans one specific host.</span> },
                    { icon: <CloudServerOutlined />, iconBg: '#8b5cf6', text: <span><strong>Domain Name</strong> - e.g. <code>example.com</code> — resolves and scans the host.</span> },
                    { icon: <WifiOutlined />, iconBg: '#10b981', text: <span><strong>CIDR Range</strong> - e.g. <code>192.168.1.0/24</code> — scans an entire subnet (256 addresses).</span> },
                    { icon: <GlobalOutlined />, iconBg: '#f59e0b', text: <span><strong>IP Range</strong> - e.g. <code>192.168.1.1-50</code> — scans a specific range of addresses.</span> }
                ],
                tip: 'You can also select targets from your registered assets using the asset dropdown.'
            }
        },
        {
            title: 'Results',
            icon: <FileSearchOutlined />,
            description: 'Understanding scan output',
            content: {
                heading: 'Reading Results',
                body: 'Scan results show discovered hosts, open ports, running services, and any identified vulnerabilities (CVEs):',
                infoRows: [
                    { icon: <CheckCircleOutlined />, iconBg: '#10b981', text: <span><strong>Open Ports</strong> - Ports accepting connections. Each port maps to a service (e.g. port 80 = HTTP, port 443 = HTTPS).</span> },
                    { icon: <DashboardOutlined />, iconBg: '#0f386a', text: <span><strong>Service Versions</strong> - The software and version running on each port (e.g. Apache 2.4.51). Outdated versions may have known CVEs.</span> },
                    { icon: <AlertOutlined />, iconBg: '#dc2626', text: <span><strong>Vulnerabilities</strong> - Known CVEs associated with detected services. Includes CVSS score and severity rating.</span> },
                    { icon: <BulbOutlined />, iconBg: '#f59e0b', text: <span><strong>AI Analysis</strong> - When LLM analysis is enabled, the AI provides contextual remediation advice for findings.</span> }
                ],
                table: {
                    headers: ['CVSS Score', 'Severity', 'Priority'],
                    rows: [
                        { cells: [<strong>0.0 - 3.9</strong>, <span style={{ color: '#52c41a', fontWeight: 600 }}>Low</span>, 'Monitor'] },
                        { cells: [<strong>4.0 - 6.9</strong>, <span style={{ color: '#faad14', fontWeight: 600 }}>Medium</span>, 'Plan fix'] },
                        { cells: [<strong>7.0 - 8.9</strong>, <span style={{ color: '#fa8c16', fontWeight: 600 }}>High</span>, 'Fix soon'] },
                        { cells: [<strong>9.0 - 10.0</strong>, <span style={{ color: '#f5222d', fontWeight: 600 }}>Critical</span>, 'Fix immediately'] }
                    ]
                }
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
                    'Start with a Fast Scan to quickly identify the most common open ports, then drill deeper with targeted scans.',
                    'Use Stealth Scan when you want to minimise your footprint on the target network.',
                    'Enable LLM Analysis to get AI-powered remediation suggestions for each vulnerability found.',
                    'Schedule regular scans to track how your network security posture changes over time.',
                    'Always scan from an authorised network position and document your scanning activities.',
                    'Export results to PDF for compliance reporting and audit trail purposes.'
                ]
            }
        }
    ];

    const zapGuideSteps: GuideStep[] = [
        {
            title: 'Overview',
            icon: <GlobalOutlined />,
            description: 'What is Web App Scanning?',
            content: {
                heading: 'Web Application Scanner',
                body: 'The Web Application Scanner uses OWASP ZAP to test web applications for security vulnerabilities. It crawls your application, identifies endpoints, and tests for common web security issues like XSS, SQL injection, and CSRF.',
                tip: 'ZAP scanning sends real HTTP requests to your target. Only scan applications you own or have explicit permission to test.'
            }
        },
        {
            title: 'Scan Types',
            icon: <ThunderboltOutlined />,
            description: 'Available scan configurations',
            content: {
                heading: 'Scan Types',
                body: 'ZAP offers four scan modes, each with different depth and intrusiveness. Choose based on what you need:',
                infoRows: [
                    { icon: <SearchOutlined />, iconBg: '#10b981', text: <span><strong>Spider Scan (Crawl Only)</strong> - The ZAP spider follows links, submits forms, and parses JavaScript to build a complete site map of your application. It only sends standard GET/POST requests — it does <em>not</em> inject attack payloads. Use this as your first step to discover all pages, forms, API endpoints, and parameters before running active tests. Non-intrusive and safe to run against production.</span> },
                    { icon: <BugOutlined />, iconBg: '#dc2626', text: <span><strong>Active Scan (Attack Only)</strong> - Takes the discovered endpoints and actively tests them for vulnerabilities by injecting attack payloads: SQL injection strings, XSS vectors, path traversal sequences, CSRF tokens, and more. It sends hundreds of crafted requests per endpoint. <strong>Warning:</strong> This is intrusive — it can modify data, trigger errors, or cause unexpected behaviour. Only run against systems you have explicit written authorisation to test.</span> },
                    { icon: <ThunderboltOutlined />, iconBg: '#8b5cf6', text: <span><strong>Full Scan (Crawl & Attack)</strong> - The most comprehensive option. Runs Spider first to discover the full application surface, then automatically follows with an Active Scan on everything found. This gives you complete coverage in a single run — from discovery to vulnerability testing. Takes the longest but produces the most thorough results. Requires the same authorisation as Active Scan.</span> },
                    { icon: <ApiOutlined />, iconBg: '#f59e0b', text: <span><strong>API Scan</strong> - Specialised for testing REST APIs, GraphQL endpoints, and web services. Tests for API-specific vulnerabilities: broken authentication, excessive data exposure, injection via JSON/XML payloads, insecure direct object references (IDOR), and missing rate limiting. Provide the API base URL (e.g. <code>https://api.example.com/v1</code>).</span> }
                ],
                tip: 'Recommended workflow: Start with Spider Scan to map the application → review the sitemap → run Active Scan or Full Scan on targets you have permission to test.'
            }
        },
        {
            title: 'Targets',
            icon: <AimOutlined />,
            description: 'Target URL format',
            content: {
                heading: 'Target URLs',
                body: 'Provide the base URL of the web application you want to scan:',
                infoRows: [
                    { icon: <GlobalOutlined />, iconBg: '#0f386a', text: <span><strong>HTTP/HTTPS URL</strong> - e.g. <code>https://example.com</code> or <code>http://192.168.1.100:8080</code></span> },
                    { icon: <ApiOutlined />, iconBg: '#8b5cf6', text: <span><strong>API Base URL</strong> - e.g. <code>https://api.example.com/v1</code> — for API scan mode.</span> },
                    { icon: <LaptopOutlined />, iconBg: '#10b981', text: <span><strong>Internal Apps</strong> - You can scan internal applications if the scanner has network access to them.</span> }
                ],
                tip: 'Include the full URL with protocol (http:// or https://). You can also select targets from your registered assets.'
            }
        },
        {
            title: 'Results',
            icon: <FileSearchOutlined />,
            description: 'Understanding ZAP alerts',
            content: {
                heading: 'Reading Results',
                body: 'ZAP results are organised as alerts, each representing a potential security issue found in your application:',
                infoRows: [
                    { icon: <WarningOutlined />, iconBg: '#dc2626', text: <span><strong>Alert Name</strong> - The type of vulnerability (e.g. "Cross Site Scripting", "SQL Injection", "Missing Security Header").</span> },
                    { icon: <DashboardOutlined />, iconBg: '#0f386a', text: <span><strong>Risk Level</strong> - Rated as Informational, Low, Medium, or High based on potential impact.</span> },
                    { icon: <AlertOutlined />, iconBg: '#f59e0b', text: <span><strong>Confidence</strong> - How certain ZAP is about the finding (Low, Medium, High). Higher confidence = more likely a true positive.</span> },
                    { icon: <BulbOutlined />, iconBg: '#10b981', text: <span><strong>Solution</strong> - ZAP provides recommended remediation steps for each alert type.</span> }
                ],
                table: {
                    headers: ['Risk Level', 'Colour', 'Action'],
                    rows: [
                        { cells: [<strong>Informational</strong>, <span style={{ color: '#1890ff', fontWeight: 600 }}>Blue</span>, 'Review & note'] },
                        { cells: [<strong>Low</strong>, <span style={{ color: '#52c41a', fontWeight: 600 }}>Green</span>, 'Plan improvement'] },
                        { cells: [<strong>Medium</strong>, <span style={{ color: '#faad14', fontWeight: 600 }}>Orange</span>, 'Fix in next sprint'] },
                        { cells: [<strong>High</strong>, <span style={{ color: '#f5222d', fontWeight: 600 }}>Red</span>, 'Fix immediately'] }
                    ]
                }
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
                    'Start with a Spider Scan to map out the application before running active tests.',
                    'Use Full Scan for the most comprehensive assessment — it combines crawling and active testing.',
                    'Review High and Medium risk alerts first as they represent the most impactful vulnerabilities.',
                    'Cross-reference ZAP findings with your code analysis (Semgrep) results for a complete security picture.',
                    'Schedule regular scans after deployments to catch newly introduced vulnerabilities.',
                    'Use the AI Remediator to get contextual fix suggestions for complex vulnerabilities.'
                ]
            }
        }
    ];

    // ==================== Common Effects ====================

    // Load all scanner histories and assets on mount
    useEffect(() => {
        loadZapScannerHistory();
        loadNmapScannerHistory();
        loadSemgrepScannerHistory();
        loadOsvScannerHistory();
        fetchAssets(); // Load assets for target selection
    }, []);

    // Load AI feature settings for the organization
    useEffect(() => {
        if (current_user?.organisation_id) {
            loadAIFeatureSettings(current_user.organisation_id);
        }
    }, [current_user?.organisation_id, loadAIFeatureSettings]);

    // Handler for opening AI Remediator modal
    const handleOpenRemediation = (record: ScannerHistoryRecord, scannerType: 'zap' | 'nmap') => {
        setSelectedHistoryForRemediation(record);
        setRemediatorScannerType(scannerType);
        setRemediationModalVisible(true);
    };

    // Helper to strip http/https from URL for network scanning
    const stripProtocol = (url: string): string => {
        return url.replace(/^https?:\/\//i, '').replace(/\/.*$/, '');
    };

    // Handle ZAP asset selection
    const handleZapAssetSelect = (assetId: string) => {
        setZapSelectedAssetId(assetId);
        const asset = assets.find(a => a.id === assetId);
        if (asset?.ip_address) {
            setTargetUrl(asset.ip_address);
        }
    };

    // Handle Nmap asset selection
    const handleNmapAssetSelect = (assetId: string) => {
        setNmapSelectedAssetId(assetId);
        const asset = assets.find(a => a.id === assetId);
        if (asset?.ip_address) {
            // Strip http/https for network scanning
            setNmapTarget(stripProtocol(asset.ip_address));
        }
    };

    // Filter assets that have IP addresses
    const assetsWithIp = assets.filter(a => a.ip_address && a.ip_address.trim() !== '');

    // ==================== ZAP Functions ====================

    useEffect(() => {
        if (zapError) {
            api.error({
                message: 'Web App Scan Failed',
                description: zapError,
                duration: 4,
            });
        }
    }, [zapError, api]);

    useEffect(() => {
        const saveHistoryOnCompletion = async () => {
            if (alerts.length > 0 && !polling && user?.email && zapScanStartTime) {
                const duration = (Date.now() - zapScanStartTime) / 1000;
                const userDetails = await fetchCurrentUserDetails(user.email);

                if (userDetails) {
                    await saveScannerHistory(
                        {
                            scanner_type: 'zap',
                            scan_target: targetUrl,
                            scan_type: zapScanType,
                            results: alerts,
                            status: 'completed',
                            scan_duration: duration
                        },
                        userDetails.email,
                        userDetails.id,
                        userDetails.organisation_id,
                        userDetails.organisation_name
                    );
                    loadZapScannerHistory();
                }
                setZapScanStartTime(null);
            }
        };
        saveHistoryOnCompletion();
    }, [alerts, polling, user, zapScanStartTime, targetUrl, zapScanType]);

    useEffect(() => {
        if (polling && !zapScanStartTime) {
            setZapScanStartTime(Date.now());
        }
    }, [polling, zapScanStartTime]);

    const loadZapScannerHistory = async () => {
        setZapHistoryLoading(true);
        try {
            const history = await fetchScannerHistory('zap', 100);
            setZapScannerHistory(history);
        } catch (error) {
            console.error('Error loading ZAP scanner history:', error);
        } finally {
            setZapHistoryLoading(false);
        }
    };

    const handleZapViewHistoryResults = async (record: ScannerHistoryRecord) => {
        // Fetch full details on demand (results are no longer pre-loaded)
        setZapHistoryLoading(true);
        try {
            const fullDetails = await fetchScannerHistoryDetails(record.id);
            if (fullDetails && fullDetails.results) {
                const results = parseHistoryResults(fullDetails.results);
                if (results) {
                    setZapHistoricalResults(results);
                    setZapSelectedHistoryRecord(record);
                    setZapHistoryModalVisible(true);
                }
            } else {
                api.error({ message: 'No Results', description: 'Could not load scan results.', duration: 4 });
            }
        } catch (error) {
            console.error('Error loading scan results:', error);
            api.error({ message: 'Load Error', description: 'Failed to load scan results.', duration: 4 });
        } finally {
            setZapHistoryLoading(false);
        }
    };

    const handleZapClearHistory = async () => {
        const confirmed = window.confirm('Are you sure you want to delete all Web App scan history records?\n\nThis action cannot be undone.');
        if (confirmed) {
            setZapHistoryLoading(true);
            const result = await clearScannerHistory('zap');
            if (result.success) {
                api.success({ message: 'History Cleared', description: `Successfully deleted ${result.deletedCount || 0} record(s).`, duration: 4 });
                loadZapScannerHistory();
            }
            setZapHistoryLoading(false);
        }
    };

    const handleZapDeleteRecord = async (record: ScannerHistoryRecord) => {
        const confirmed = window.confirm(`Are you sure you want to delete this scan result?\n\nTarget: ${record.scan_target}\nTimestamp: ${formatTimestamp(record.timestamp)}\n\nThis action cannot be undone.`);
        if (confirmed) {
            setZapHistoryLoading(true);
            const result = await deleteScannerHistoryRecord(record.id);
            if (result.success) {
                api.success({ message: 'Record Deleted', description: 'Scan result deleted successfully.', duration: 3 });
                loadZapScannerHistory();
            } else {
                api.error({ message: 'Delete Failed', description: result.error || 'Failed to delete record.', duration: 4 });
            }
            setZapHistoryLoading(false);
        }
    };

    const handleZapExportHistory = async (record: ScannerHistoryRecord) => {
        try {
            const details = await fetchScannerHistoryDetails(record.id);
            if (!details?.results) {
                api.error({ message: 'Export Failed', description: 'No scan results available for this record.', duration: 4 });
                return;
            }
            const alerts = parseHistoryResults(details.results);
            const timestamp = new Date(record.timestamp).toISOString().replace(/[:.]/g, '-').slice(0, 19);
            const filename = `webapp-scan-${record.scan_target.replace(/[^a-z0-9]/gi, '_')}-${timestamp}`;
            await exportZapResultsToPdf(alerts, record.scan_target, filename);
            api.success({ message: 'Export Successful', description: 'Scan results exported to PDF.', duration: 3 });
        } catch (error) {
            api.error({ message: 'Export Failed', description: 'Failed to export scan results.', duration: 4 });
        }
    };

    const zapScanOptions = [
        { value: 'spider', label: 'Spider Scan (Crawl Only)' },
        { value: 'active', label: 'Active Scan (Attack Only)' },
        { value: 'full', label: 'Full Scan (Crawl & Attack)' },
        { value: 'api', label: 'API Scan' }
    ];

    const filterOption: SelectProps['filterOption'] = (input, option) =>
        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase());

    const handleZapScanTypeChange = (value: string) => {
        setZapScanType(value);
        if (value === 'full' || value === 'active') {
            api.warning({
                message: 'Legal Considerations',
                description: `${value === 'full' ? 'Full scans' : 'Active scans'} perform security attacks against the target system. Ensure you have explicit written authorization.`,
                duration: 8,
            });
        }
    };

    const handleZapRunScan = async () => {
        const accepted = await confirmScanLegalDisclaimer('Application Vulnerability');
        if (!accepted) return;

        if (!targetUrl || targetUrl.trim() === '') {
            api.error({ message: 'Missing Target', description: 'Please enter a target URL.', duration: 4 });
            return;
        }

        let success = false;
        switch (zapScanType) {
            case 'spider': success = await startSpiderScan(); break;
            case 'active': success = await startActiveScan(); break;
            case 'full': success = await startFullScan(); break;
            case 'api': success = await startApiScan(); break;
            default:
                api.error({ message: 'Invalid Scan Type', description: 'Please select a valid scan type.', duration: 4 });
                return;
        }

        if (success) {
            api.success({ message: 'Scan Started', description: 'The scan has been started successfully.', duration: 4 });
        }
    };

    const handleZapClear = async () => {
        setTargetUrl('');
        setZapScanType('spider');
        clearZapResults();
        await clearAlerts();
    };

    const handleZapEmergencyStop = async () => {
        const response = await emergencyStop();
        setEmergencyStopModalVisible(false);
        if (response) {
            api.success({ message: 'Scans Stopped', description: 'All scans stopped and data cleared.', duration: 4 });
        }
    };

    const handleZapExportToPdf = async () => {
        try {
            await exportZapResultsToPdf(alerts, targetUrl, 'webapp-scan-report');
            api.success({ message: 'Export Success', description: 'Web App scan results exported to PDF.', duration: 4 });
        } catch (error) {
            api.error({ message: 'Export Failed', description: 'Failed to export results.', duration: 4 });
        }
    };

    const handleExportActiveScanToPdf = async () => {
        try {
            const { exportActiveScanDetailsToPdf } = await import('../utils/activeScanPdfUtils');
            await exportActiveScanDetailsToPdf(activeScanState, targetUrl, 'webapp-active-scan-details');
            api.success({ message: 'Export Success', description: 'Active scan details exported to PDF.', duration: 4 });
        } catch (error) {
            api.error({ message: 'Export Failed', description: 'Failed to export active scan details.', duration: 4 });
        }
    };

    const getZapStatusText = () => {
        if (!scanStatus) return 'No scan in progress';
        if (scanStatus.isCompleted) return 'Scan completed';
        return `Scan in progress: ${scanStatus.status}%`;
    };

    const getZapStatusColor = () => {
        if (!scanStatus) return 'gray';
        if (scanStatus.isCompleted) return 'green';
        return 'blue';
    };

    // ==================== Nmap Functions ====================

    useEffect(() => {
        if (nmapError) {
            api.error({ message: 'Network Scan Failed', description: nmapError, duration: 4 });
        }
    }, [nmapError, api]);

    useEffect(() => {
        const saveHistoryOnCompletion = async () => {
            if (nmapScanResults && !nmapLoading && user?.email && nmapScanStartTime) {
                const duration = (Date.now() - nmapScanStartTime) / 1000;
                const userDetails = await fetchCurrentUserDetails(user.email);
                if (userDetails) {
                    await saveScannerHistory(
                        {
                            scanner_type: 'nmap',
                            scan_target: nmapTarget,
                            scan_type: nmapScanType,
                            results: nmapScanResults,
                            status: 'completed',
                            scan_duration: duration
                        },
                        userDetails.email,
                        userDetails.id,
                        userDetails.organisation_id,
                        userDetails.organisation_name
                    );
                    loadNmapScannerHistory();
                }
                setNmapScanStartTime(null);
            }
        };
        saveHistoryOnCompletion();
    }, [nmapScanResults, nmapLoading, user, nmapScanStartTime, nmapTarget, nmapScanType]);

    useEffect(() => {
        if (nmapLoading && !nmapScanStartTime) {
            setNmapScanStartTime(Date.now());
        }
    }, [nmapLoading, nmapScanStartTime]);

    const loadNmapScannerHistory = async () => {
        setNmapHistoryLoading(true);
        try {
            const history = await fetchScannerHistory('nmap', 100);
            setNmapScannerHistory(history);
        } catch (error) {
            console.error('Error loading Nmap scanner history:', error);
        } finally {
            setNmapHistoryLoading(false);
        }
    };

    const handleNmapViewHistoryResults = async (record: ScannerHistoryRecord) => {
        // Fetch full details on demand (results are no longer pre-loaded)
        setNmapHistoryLoading(true);
        try {
            const fullDetails = await fetchScannerHistoryDetails(record.id);
            if (fullDetails && fullDetails.results) {
                const results = parseHistoryResults(fullDetails.results);
                if (results) {
                    let formattedResults = '';
                    if (typeof results === 'string') formattedResults = results;
                    else if (results.analysis) formattedResults = results.analysis;
                    else if (results.output) formattedResults = JSON.stringify(results.output, null, 2);
                    else formattedResults = JSON.stringify(results, null, 2);
                    setNmapHistoricalResults(formattedResults);
                    setNmapSelectedHistoryRecord(record);
                    setNmapHistoryModalVisible(true);
                }
            } else {
                api.error({ message: 'No Results', description: 'Could not load scan results.', duration: 4 });
            }
        } catch (error) {
            console.error('Error loading scan results:', error);
            api.error({ message: 'Load Error', description: 'Failed to load scan results.', duration: 4 });
        } finally {
            setNmapHistoryLoading(false);
        }
    };

    const handleNmapClearHistory = async () => {
        const confirmed = window.confirm('Are you sure you want to delete all Network scan history records?\n\nThis action cannot be undone.');
        if (confirmed) {
            setNmapHistoryLoading(true);
            const result = await clearScannerHistory('nmap');
            if (result.success) {
                api.success({ message: 'History Cleared', description: `Successfully deleted ${result.deletedCount || 0} record(s).`, duration: 4 });
                loadNmapScannerHistory();
            }
            setNmapHistoryLoading(false);
        }
    };

    const handleNmapDeleteRecord = async (record: ScannerHistoryRecord) => {
        const confirmed = window.confirm(`Are you sure you want to delete this scan result?\n\nTarget: ${record.scan_target}\nTimestamp: ${formatTimestamp(record.timestamp)}\n\nThis action cannot be undone.`);
        if (confirmed) {
            setNmapHistoryLoading(true);
            const result = await deleteScannerHistoryRecord(record.id);
            if (result.success) {
                api.success({ message: 'Record Deleted', description: 'Scan result deleted successfully.', duration: 3 });
                loadNmapScannerHistory();
            } else {
                api.error({ message: 'Delete Failed', description: result.error || 'Failed to delete record.', duration: 4 });
            }
            setNmapHistoryLoading(false);
        }
    };

    // Handler for expanding ZAP history rows - fetches results on demand
    const handleZapRowExpand = async (expanded: boolean, record: ScannerHistoryRecord & { key: string }) => {
        if (expanded) {
            setZapExpandedRowKeys(prev => [...prev, record.key]);
            // Only fetch if we don't already have the results cached
            if (!zapLoadedResults[record.id]) {
                setZapLoadingRows(prev => new Set(prev).add(record.id));
                try {
                    const fullDetails = await fetchScannerHistoryDetails(record.id);
                    if (fullDetails && fullDetails.results) {
                        const results = parseHistoryResults(fullDetails.results);
                        setZapLoadedResults(prev => ({ ...prev, [record.id]: results }));
                    }
                } catch (error) {
                    console.error('Error loading ZAP scan results:', error);
                } finally {
                    setZapLoadingRows(prev => {
                        const next = new Set(prev);
                        next.delete(record.id);
                        return next;
                    });
                }
            }
        } else {
            setZapExpandedRowKeys(prev => prev.filter(k => k !== record.key));
        }
    };

    // Handler for expanding nmap history rows - fetches results on demand
    const handleNmapRowExpand = async (expanded: boolean, record: ScannerHistoryRecord & { key: string }) => {
        if (expanded) {
            setNmapExpandedRowKeys(prev => [...prev, record.key]);
            // Only fetch if we don't already have the results cached
            if (!nmapLoadedResults[record.id]) {
                setNmapLoadingRows(prev => new Set(prev).add(record.id));
                try {
                    const fullDetails = await fetchScannerHistoryDetails(record.id);
                    if (fullDetails && fullDetails.results) {
                        const results = parseHistoryResults(fullDetails.results);
                        setNmapLoadedResults(prev => ({ ...prev, [record.id]: results }));
                    }
                } catch (error) {
                    console.error('Error loading scan results:', error);
                } finally {
                    setNmapLoadingRows(prev => {
                        const next = new Set(prev);
                        next.delete(record.id);
                        return next;
                    });
                }
            }
        } else {
            setNmapExpandedRowKeys(prev => prev.filter(k => k !== record.key));
        }
    };

    const nmapScanOptions = [
        {
            label: <span style={{ fontWeight: 'bold', color: '#1890ff' }}>🔍 Vulnerability Scanning</span>,
            options: [
                { value: 'fast', label: 'Fast Scan - Top 100 ports' },
                { value: 'basic', label: 'Basic Scan - Top 1000 ports' },
                { value: 'ports', label: 'Specific Port Scan - Custom ports' },
                { value: 'stealth', label: 'Stealth Scan - SYN scan (less detectable)' },
                { value: 'no_ping', label: 'No Ping Scan - Skip host discovery' },
                { value: 'aggressive', label: 'Aggressive Scan - OS, scripts & traceroute' },
                { value: 'os', label: 'OS Detection - Operating system identification' }
            ]
        },
        {
            label: <span style={{ fontWeight: 'bold', color: '#1890ff' }}>📡 Port & Network Discovery</span>,
            options: [
                { value: 'network', label: 'Network Discovery - Find live hosts (ping sweep)' },
                { value: 'all_ports', label: 'All Ports Scan - Scan all 65535 ports' }
            ]
        }
    ];

    const handleNmapScanTypeChange = (value: string) => {
        setNmapScanType(value);
        if (value !== 'ports') setNmapPorts('');
    };

    const handleNmapRunScan = async () => {
        const accepted = await confirmScanLegalDisclaimer('Network Vulnerability');
        if (!accepted) return;

        if (!nmapTarget || nmapTarget.trim() === '') {
            api.error({ message: 'Missing Target', description: 'Please enter a target IP, domain, or network.', duration: 4 });
            return;
        }

        if (nmapScanType === 'ports' && (!nmapPorts || nmapPorts.trim() === '')) {
            api.error({ message: 'Missing Ports', description: 'Please specify ports for the port scan.', duration: 4 });
            return;
        }

        let success = false;
        switch (nmapScanType) {
            case 'basic': success = await basicScan(nmapTarget); break;
            case 'ports': success = await portScan(nmapTarget, nmapPorts); break;
            case 'all_ports': success = await allPortsScan(nmapTarget); break;
            case 'aggressive': success = await aggressiveScan(nmapTarget); break;
            case 'os': success = await osScan(nmapTarget); break;
            case 'network': success = await networkScan(nmapTarget); break;
            case 'stealth': success = await stealthScan(nmapTarget); break;
            case 'no_ping': success = await noPingScan(nmapTarget); break;
            case 'fast': success = await fastScan(nmapTarget); break;
            default:
                api.error({ message: 'Invalid Scan Type', description: 'Please select a valid scan type.', duration: 4 });
                return;
        }

        if (success) {
            api.success({ message: 'Scan Completed', description: 'The scan has been completed successfully.', duration: 4 });
        }
    };

    const handleNmapClear = () => {
        setNmapTarget('');
        setNmapPorts('');
        setNmapScanType('basic');
        clearNmapResults();
    };

    const formatNmapResults = () => {
        if (!nmapScanResults) return 'No scan results available.';
        if (!nmapScanResults.success) return `Error: ${nmapScanResults.error || 'Unknown error occurred'}`;
        if (nmapScanResults.analysis) return nmapScanResults.analysis;
        if (nmapScanResults.output) return JSON.stringify(nmapScanResults.output, null, 2);
        return 'No results available';
    };

    const handleNmapExport = (format: 'html' | 'pdf') => {
        const resultsToExport = nmapScanResults?.analysis || nmapScanResults?.output;
        if (!nmapScanResults || !resultsToExport) {
            api.error({ message: 'Export Failed', description: 'No scan results available to export.', duration: 4 });
            return;
        }

        const htmlContent = `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Network Scan Results</title><style>body{font-family:Arial,sans-serif;line-height:1.6;margin:20px}h1{color:#0f386a}.results{background:#f8f8f8;padding:15px;border-radius:8px;white-space:pre-line;word-wrap:break-word;font-family:monospace}</style></head><body><h1>Network Scan Results</h1><div class="results">${resultsToExport}</div></body></html>`;

        if (format === 'html') {
            const blob = new Blob([htmlContent], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'network-scan-results.html';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
            api.success({ message: 'Export Successful', description: 'Scan results exported to HTML.', duration: 4 });
        } else if (format === 'pdf') {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = htmlContent;
            document.body.appendChild(tempDiv);
            const options = { margin: 10, filename: 'network-scan-results.pdf', image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2 }, jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' } };
            html2pdf().from(tempDiv).set(options).save().then(async () => {
                const { getAuthHeader } = useAuthStore.getState();
                await trackPdfDownload('nmap', getAuthHeader);
                document.body.removeChild(tempDiv);
                api.success({ message: 'Export Successful', description: 'Scan results exported to PDF.', duration: 4 });
            });
        }
    };

    const handleNmapExportHistory = async (record: ScannerHistoryRecord) => {
        try {
            const details = await fetchScannerHistoryDetails(record.id);
            if (!details?.results) {
                api.error({ message: 'Export Failed', description: 'No scan results available for this record.', duration: 4 });
                return;
            }
            const results = parseHistoryResults(details.results);
            const timestamp = new Date(record.timestamp).toISOString().replace(/[:.]/g, '-').slice(0, 19);
            const filename = `network-scan-${record.scan_target.replace(/[^a-z0-9]/gi, '_')}-${timestamp}`;

            await exportNmapResultsToPdf(
                results,
                record.scan_target,
                record.scan_type || 'N/A',
                record.scan_duration,
                filename
            );

            api.success({ message: 'Export Successful', description: 'Scan results exported to PDF.', duration: 3 });
        } catch (error) {
            console.error('Export error:', error);
            api.error({ message: 'Export Failed', description: 'Failed to export scan results.', duration: 4 });
        }
    };

    // ==================== Semgrep Functions ====================

    useEffect(() => {
        if (semgrepError) {
            api.error({ message: 'Code Analysis Scan Failed', description: semgrepError, duration: 4 });
        }
    }, [semgrepError, api]);

    useEffect(() => {
        const saveHistoryOnCompletion = async () => {
            if (semgrepScanResults && !semgrepLoading && user?.email && semgrepScanStartTime) {
                const duration = (Date.now() - semgrepScanStartTime) / 1000;
                const userDetails = await fetchCurrentUserDetails(user.email);
                if (userDetails) {
                    await saveScannerHistory(
                        {
                            scanner_type: 'semgrep',
                            scan_target: semgrepSelectedFile?.name || 'N/A',
                            scan_type: semgrepConfig,
                            results: semgrepScanResults,
                            status: 'completed',
                            scan_duration: duration
                        },
                        userDetails.email,
                        userDetails.id,
                        userDetails.organisation_id,
                        userDetails.organisation_name
                    );
                    loadSemgrepScannerHistory();
                }
                setSemgrepScanStartTime(null);
            }
        };
        saveHistoryOnCompletion();
    }, [semgrepScanResults, semgrepLoading, user, semgrepScanStartTime, semgrepSelectedFile, semgrepConfig]);

    useEffect(() => {
        if (semgrepLoading && !semgrepScanStartTime) {
            setSemgrepScanStartTime(Date.now());
        }
    }, [semgrepLoading, semgrepScanStartTime]);

    const loadSemgrepScannerHistory = async () => {
        setSemgrepHistoryLoading(true);
        try {
            const history = await fetchScannerHistory('semgrep', 100);
            setSemgrepScannerHistory(history);
        } catch (error) {
            console.error('Error loading Semgrep scanner history:', error);
        } finally {
            setSemgrepHistoryLoading(false);
        }
    };

    const handleSemgrepViewHistoryResults = (record: ScannerHistoryRecord) => {
        const results = parseHistoryResults(record.results);
        if (results) {
            let formattedResults = '';
            if (typeof results === 'string') formattedResults = results;
            else if (results.analysis) formattedResults = results.analysis;
            else if (results.output) formattedResults = JSON.stringify(results.output, null, 2);
            else formattedResults = JSON.stringify(results, null, 2);
            setSemgrepHistoricalResults(formattedResults);
            setSemgrepSelectedHistoryRecord(record);
            setSemgrepHistoryModalVisible(true);
        }
    };

    const handleSemgrepClearHistory = async () => {
        const confirmed = window.confirm('Are you sure you want to delete all Code Analysis scan history records?\n\nThis action cannot be undone.');
        if (confirmed) {
            setSemgrepHistoryLoading(true);
            const result = await clearScannerHistory('semgrep');
            if (result.success) {
                api.success({ message: 'History Cleared', description: `Successfully deleted ${result.deletedCount || 0} record(s).`, duration: 4 });
                loadSemgrepScannerHistory();
            }
            setSemgrepHistoryLoading(false);
        }
    };

    const handleSemgrepFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (files && files.length > 0) {
            const file = files[0];
            if (file.type !== 'application/zip' && !file.name.endsWith('.zip')) {
                message.error(`${file.name} is not a ZIP file`);
                if (semgrepFileInputRef.current) semgrepFileInputRef.current.value = '';
                setSemgrepSelectedFile(null);
                return;
            }
            message.success(`${file.name} selected successfully`);
            setSemgrepSelectedFile(file);
        } else {
            setSemgrepSelectedFile(null);
        }
    };

    const handleSemgrepRunScan = async () => {
        if (!semgrepSelectedFile) {
            api.error({ message: 'Missing File', description: 'Please upload a ZIP file to scan.', duration: 4 });
            return;
        }
        const success = await semgrepScanZipFile(semgrepSelectedFile, semgrepConfig, semgrepUseLlm);
        if (success) {
            api.success({ message: 'Scan Completed', description: 'The code analysis has been completed successfully.', duration: 4 });
        }
    };

    const handleSemgrepClear = () => {
        setSemgrepSelectedFile(null);
        setSemgrepConfig('auto');
        clearSemgrepResults();
        if (semgrepFileInputRef.current) semgrepFileInputRef.current.value = '';
    };

    const formatSemgrepResults = () => {
        if (!semgrepScanResults) return 'No scan results available.';
        if (semgrepScanResults.analysis) return semgrepScanResults.analysis;
        if (semgrepScanResults.output) return JSON.stringify(semgrepScanResults.output, null, 2);
        return 'No results available';
    };

    const handleSemgrepExport = (format: 'html' | 'pdf') => {
        const resultsToExport = semgrepScanResults?.analysis || semgrepScanResults?.output;
        if (!semgrepScanResults || !resultsToExport) {
            api.error({ message: 'Export Failed', description: 'No scan results available to export.', duration: 4 });
            return;
        }

        const htmlContent = `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Code Analysis Scan Results</title><style>body{font-family:Arial,sans-serif;line-height:1.6;margin:20px}h1{color:#0f386a}.results{background:#f8f8f8;padding:15px;border-radius:8px;white-space:pre-line;word-wrap:break-word;font-family:monospace}</style></head><body><h1>Code Analysis Results</h1><div class="results">${resultsToExport}</div></body></html>`;

        if (format === 'html') {
            const blob = new Blob([htmlContent], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'code-analysis-scan-results.html';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
            api.success({ message: 'Export Successful', description: 'Scan results exported to HTML.', duration: 4 });
        } else if (format === 'pdf') {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = htmlContent;
            document.body.appendChild(tempDiv);
            const options = { margin: 10, filename: 'code-analysis-scan-results.pdf', image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2 }, jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' } };
            html2pdf().from(tempDiv).set(options).save().then(async () => {
                const { getAuthHeader } = useAuthStore.getState();
                await trackPdfDownload('semgrep', getAuthHeader);
                document.body.removeChild(tempDiv);
                api.success({ message: 'Export Successful', description: 'Scan results exported to PDF.', duration: 4 });
            });
        }
    };

    const handleSemgrepExportHistory = async (record: ScannerHistoryRecord) => {
        try {
            const details = await fetchScannerHistoryDetails(record.id);
            if (!details?.results) {
                api.error({ message: 'Export Failed', description: 'No scan results available for this record.', duration: 4 });
                return;
            }
            const results = parseHistoryResults(details.results);
            const resultsToExport = results?.analysis || results?.output || results;
            const htmlContent = `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Code Analysis Scan Results - ${record.scan_target}</title><style>body{font-family:Arial,sans-serif;line-height:1.6;margin:20px}h1{color:#0f386a}.metadata{background:#e7f3ff;padding:10px;border-radius:5px;margin-bottom:20px}.results{background:#f8f8f8;padding:15px;border-radius:8px;white-space:pre-line;word-wrap:break-word;font-family:monospace}</style></head><body><h1>Code Analysis Results</h1><div class="metadata"><strong>Target:</strong> ${record.scan_target}<br><strong>Scan Type:</strong> ${record.scan_type || 'N/A'}<br><strong>Timestamp:</strong> ${new Date(record.timestamp).toLocaleString()}<br><strong>Duration:</strong> ${record.scan_duration ? record.scan_duration.toFixed(2) + 's' : 'N/A'}</div><div class="results">${typeof resultsToExport === 'string' ? resultsToExport : JSON.stringify(resultsToExport, null, 2)}</div></body></html>`;
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = htmlContent;
            document.body.appendChild(tempDiv);
            const timestamp = new Date(record.timestamp).toISOString().replace(/[:.]/g, '-').slice(0, 19);
            const filename = `code-analysis-scan-${record.scan_target.replace(/[^a-z0-9]/gi, '_')}-${timestamp}.pdf`;
            const options = { margin: 10, filename: filename, image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2 }, jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' } };
            await html2pdf().from(tempDiv).set(options).save();
            const { getAuthHeader } = useAuthStore.getState();
            await trackPdfDownload('semgrep', getAuthHeader);
            document.body.removeChild(tempDiv);
            api.success({ message: 'Export Successful', description: 'Scan results exported to PDF.', duration: 3 });
        } catch (error) {
            api.error({ message: 'Export Failed', description: 'Failed to export scan results.', duration: 4 });
        }
    };

    // ==================== OSV Functions ====================

    useEffect(() => {
        if (osvError) {
            api.error({ message: 'Dependency Analysis Scan Failed', description: osvError, duration: 4 });
        }
    }, [osvError, api]);

    useEffect(() => {
        const saveHistoryOnCompletion = async () => {
            if (osvScanResults && !osvLoading && user?.email && osvScanStartTime) {
                const duration = (Date.now() - osvScanStartTime) / 1000;
                const userDetails = await fetchCurrentUserDetails(user.email);
                if (userDetails) {
                    await saveScannerHistory(
                        {
                            scanner_type: 'osv',
                            scan_target: osvSelectedFile?.name || 'N/A',
                            scan_type: 'dependency_scan',
                            results: osvScanResults,
                            status: 'completed',
                            scan_duration: duration
                        },
                        userDetails.email,
                        userDetails.id,
                        userDetails.organisation_id,
                        userDetails.organisation_name
                    );
                    loadOsvScannerHistory();
                }
                setOsvScanStartTime(null);
            }
        };
        saveHistoryOnCompletion();
    }, [osvScanResults, osvLoading, user, osvScanStartTime, osvSelectedFile]);

    useEffect(() => {
        if (osvLoading && !osvScanStartTime) {
            setOsvScanStartTime(Date.now());
        }
    }, [osvLoading, osvScanStartTime]);

    const loadOsvScannerHistory = async () => {
        setOsvHistoryLoading(true);
        try {
            const history = await fetchScannerHistory('osv', 100);
            setOsvScannerHistory(history);
        } catch (error) {
            console.error('Error loading OSV scanner history:', error);
        } finally {
            setOsvHistoryLoading(false);
        }
    };

    const handleOsvViewHistoryResults = (record: ScannerHistoryRecord) => {
        const results = parseHistoryResults(record.results);
        if (results) {
            let formattedResults = '';
            if (typeof results === 'string') formattedResults = results;
            else if (results.analysis) formattedResults = results.analysis;
            else if (results.output) formattedResults = JSON.stringify(results.output, null, 2);
            else formattedResults = JSON.stringify(results, null, 2);
            setOsvHistoricalResults(formattedResults);
            setOsvSelectedHistoryRecord(record);
            setOsvHistoryModalVisible(true);
        }
    };

    const handleOsvClearHistory = async () => {
        const confirmed = window.confirm('Are you sure you want to delete all Dependency Analysis scan history records?\n\nThis action cannot be undone.');
        if (confirmed) {
            setOsvHistoryLoading(true);
            const result = await clearScannerHistory('osv');
            if (result.success) {
                api.success({ message: 'History Cleared', description: `Successfully deleted ${result.deletedCount || 0} record(s).`, duration: 4 });
                loadOsvScannerHistory();
            }
            setOsvHistoryLoading(false);
        }
    };

    const handleOsvFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (files && files.length > 0) {
            const file = files[0];
            if (file.type !== 'application/zip' && !file.name.endsWith('.zip')) {
                message.error(`${file.name} is not a ZIP file`);
                if (osvFileInputRef.current) osvFileInputRef.current.value = '';
                setOsvSelectedFile(null);
                return;
            }
            message.success(`${file.name} selected successfully`);
            setOsvSelectedFile(file);
        } else {
            setOsvSelectedFile(null);
        }
    };

    const handleOsvRunScan = async () => {
        if (!osvSelectedFile) {
            api.error({ message: 'Missing File', description: 'Please upload a ZIP file to scan.', duration: 4 });
            return;
        }
        const success = await osvScanZipFile(osvSelectedFile, osvUseLlm);
        if (success) {
            api.success({ message: 'Scan Completed', description: 'The dependency vulnerability analysis has been completed successfully.', duration: 4 });
        }
    };

    const handleOsvClear = () => {
        setOsvSelectedFile(null);
        clearOsvResults();
        if (osvFileInputRef.current) osvFileInputRef.current.value = '';
    };

    const formatOsvResults = () => {
        if (!osvScanResults) return 'No scan results available.';
        if (!osvScanResults.success) return `Error: ${osvScanResults.error || 'Unknown error occurred'}`;
        if (osvScanResults.analysis) return osvScanResults.analysis;
        if (osvScanResults.output) return JSON.stringify(osvScanResults.output, null, 2);
        return 'No results available';
    };

    const handleOsvExport = (format: 'html' | 'pdf') => {
        const resultsToExport = osvScanResults?.analysis || osvScanResults?.output;
        if (!osvScanResults || !resultsToExport) {
            api.error({ message: 'Export Failed', description: 'No scan results available to export.', duration: 4 });
            return;
        }

        const htmlContent = `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Dependency Analysis Scan Results</title><style>body{font-family:Arial,sans-serif;line-height:1.6;margin:20px}h1{color:#0f386a}.results{background:#f8f8f8;padding:15px;border-radius:8px;white-space:pre-line;word-wrap:break-word;font-family:monospace}</style></head><body><h1>Dependency Vulnerability Analysis Results</h1><div class="results">${resultsToExport}</div></body></html>`;

        if (format === 'html') {
            const blob = new Blob([htmlContent], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'dependency-scan-results.html';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
            api.success({ message: 'Export Successful', description: 'Scan results exported to HTML.', duration: 4 });
        } else if (format === 'pdf') {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = htmlContent;
            document.body.appendChild(tempDiv);
            const options = { margin: 10, filename: 'dependency-scan-results.pdf', image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2 }, jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' } };
            html2pdf().from(tempDiv).set(options).save().then(async () => {
                const { getAuthHeader } = useAuthStore.getState();
                await trackPdfDownload('osv', getAuthHeader);
                document.body.removeChild(tempDiv);
                api.success({ message: 'Export Successful', description: 'Scan results exported to PDF.', duration: 4 });
            });
        }
    };

    const handleOsvExportHistory = async (record: ScannerHistoryRecord) => {
        try {
            const details = await fetchScannerHistoryDetails(record.id);
            if (!details?.results) {
                api.error({ message: 'Export Failed', description: 'No scan results available for this record.', duration: 4 });
                return;
            }
            const results = parseHistoryResults(details.results);
            const resultsToExport = results?.analysis || results?.output || results;
            const htmlContent = `<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Dependency Analysis Scan Results - ${record.scan_target}</title><style>body{font-family:Arial,sans-serif;line-height:1.6;margin:20px}h1{color:#0f386a}.metadata{background:#e7f3ff;padding:10px;border-radius:5px;margin-bottom:20px}.results{background:#f8f8f8;padding:15px;border-radius:8px;white-space:pre-line;word-wrap:break-word;font-family:monospace}</style></head><body><h1>Dependency Vulnerability Analysis Results</h1><div class="metadata"><strong>Target:</strong> ${record.scan_target}<br><strong>Scan Type:</strong> ${record.scan_type || 'N/A'}<br><strong>Timestamp:</strong> ${new Date(record.timestamp).toLocaleString()}<br><strong>Duration:</strong> ${record.scan_duration ? record.scan_duration.toFixed(2) + 's' : 'N/A'}</div><div class="results">${typeof resultsToExport === 'string' ? resultsToExport : JSON.stringify(resultsToExport, null, 2)}</div></body></html>`;
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = htmlContent;
            document.body.appendChild(tempDiv);
            const timestamp = new Date(record.timestamp).toISOString().replace(/[:.]/g, '-').slice(0, 19);
            const filename = `dependency-scan-${record.scan_target.replace(/[^a-z0-9]/gi, '_')}-${timestamp}.pdf`;
            const options = { margin: 10, filename: filename, image: { type: 'jpeg', quality: 0.98 }, html2canvas: { scale: 2 }, jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' } };
            await html2pdf().from(tempDiv).set(options).save();
            const { getAuthHeader } = useAuthStore.getState();
            await trackPdfDownload('osv', getAuthHeader);
            document.body.removeChild(tempDiv);
            api.success({ message: 'Export Successful', description: 'Scan results exported to PDF.', duration: 3 });
        } catch (error) {
            api.error({ message: 'Export Failed', description: 'Failed to export scan results.', duration: 4 });
        }
    };

    // ==================== Table Data ====================
    const zapTableData = prepareZapTableData(alerts);
    const zapHistoryTableData = prepareHistoryTableData(zapScannerHistory);
    const nmapHistoryTableData = prepareHistoryTableData(nmapScannerHistory);
    const semgrepHistoryTableData = prepareHistoryTableData(semgrepScannerHistory);
    const osvHistoryTableData = prepareHistoryTableData(osvScannerHistory);

    // Custom styles for the page
    const tabStyles = `
        .scanner-tabs .ant-tabs-nav::before {
            border-bottom: 2px solid #f0f0f0;
        }
        .scanner-tabs .ant-tabs-tab {
            padding: 12px 24px;
            font-size: 15px;
            font-weight: 500;
            color: #666;
            transition: all 0.2s ease;
        }
        .scanner-tabs .ant-tabs-tab:hover {
            color: #1890ff;
        }
        .scanner-tabs .ant-tabs-tab-active {
            color: #1890ff !important;
        }
        .scanner-tabs .ant-tabs-ink-bar {
            background: #1890ff;
            height: 3px;
        }
        .scanner-card {
            background: white;
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
            border-bottom: 1px solid #f0f0f0;
        }
        .scanner-card-title {
            font-size: 16px;
            font-weight: 600;
            color: #1a1a2e;
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
            color: #555;
        }
        .form-field label .required {
            color: #ff4d4f;
            margin-left: 4px;
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
            background: #f5f5f5;
            border: 1px solid #e8e8e8;
            color: #666;
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
            background: #ebebeb;
            border-color: #d9d9d9;
        }
        .btn-danger {
            background: #fff;
            border: 1px solid #ff4d4f;
            color: #ff4d4f;
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
        .btn-danger:hover {
            background: #ff4d4f;
            color: white;
        }
        .results-container {
            background: #fafbfc;
            border: 1px solid #e8e8e8;
            border-radius: 10px;
            min-height: 200px;
            position: relative;
        }
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            border-bottom: 1px solid #e8e8e8;
            background: white;
            border-radius: 10px 10px 0 0;
        }
        .results-content {
            padding: 20px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
            color: #333;
            max-height: 400px;
            overflow-y: auto;
        }
        .history-section {
            margin-top: 24px;
        }
        .history-collapse .ant-collapse-header {
            background: linear-gradient(135deg, #f8f9fa 0%, #fff 100%);
            border-radius: 10px !important;
            padding: 16px 20px !important;
            font-weight: 500;
        }
        .history-collapse .ant-collapse-content {
            border-top: 1px solid #f0f0f0;
        }
        .history-header-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
        }
        .history-badge {
            background: #e6f7ff;
            color: #1890ff;
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .risk-tags {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 60px 20px;
            color: #999;
        }
        .empty-state-icon {
            font-size: 48px;
            color: #d9d9d9;
            margin-bottom: 16px;
        }
        .scan-progress-container {
            background: #f0f8ff;
            border: 1px solid #91caff;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .history-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: white;
            border: 1px solid #f0f0f0;
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
            color: #1a1a2e;
        }
        .history-item-meta {
            font-size: 12px;
            color: #999;
            display: flex;
            gap: 16px;
        }
        .history-item-actions {
            display: flex;
            gap: 8px;
        }
        @media (max-width: 768px) {
            .config-grid {
                grid-template-columns: 1fr;
            }
        }
    `;

    // Render history list items for compact view
    const renderHistoryList = (
        history: ScannerHistoryRecord[],
        onView: (record: ScannerHistoryRecord) => void,
        onExport: (record: ScannerHistoryRecord) => void,
        loading: boolean
    ) => {
        if (loading) {
            return <div style={{ textAlign: 'center', padding: '40px' }}>Loading history...</div>;
        }

        if (history.length === 0) {
            return (
                <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="No scan history yet"
                    style={{ padding: '40px 0' }}
                />
            );
        }

        return (
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                {history.slice(0, 10).map((record, index) => (
                    <div key={record.id || index} className="history-item">
                        <div className="history-item-info">
                            <span className="history-item-target">{record.scan_target}</span>
                            <div className="history-item-meta">
                                <span><ClockCircleOutlined /> {formatTimestamp(record.timestamp)}</span>
                                <span>{record.scan_type || 'N/A'}</span>
                                {record.scan_duration && <span>{record.scan_duration.toFixed(1)}s</span>}
                            </div>
                        </div>
                        <div className="history-item-actions">
                            <Tooltip title="View Results">
                                <Button
                                    type="text"
                                    icon={<EyeOutlined />}
                                    onClick={() => onView(record)}
                                />
                            </Tooltip>
                            <Tooltip title="Export PDF">
                                <Button
                                    type="text"
                                    icon={<FilePdfOutlined />}
                                    onClick={() => onExport(record)}
                                />
                            </Tooltip>
                        </div>
                    </div>
                ))}
                {history.length > 10 && (
                    <div style={{ textAlign: 'center', padding: '12px', color: '#999', fontSize: '13px' }}>
                        Showing 10 of {history.length} records
                    </div>
                )}
            </div>
        );
    };

    // Search filtered ZAP history
    const zapSearchFilteredHistory = zapScannerHistory.filter(record =>
        record.scan_target?.toLowerCase().includes(zapHistorySearchText.toLowerCase()) ||
        record.scan_type?.toLowerCase().includes(zapHistorySearchText.toLowerCase()) ||
        record.status?.toLowerCase().includes(zapHistorySearchText.toLowerCase()) ||
        record.user_email?.toLowerCase().includes(zapHistorySearchText.toLowerCase())
    );

    // Search filtered Nmap history
    const nmapSearchFilteredHistory = nmapScannerHistory.filter(record =>
        record.scan_target?.toLowerCase().includes(nmapHistorySearchText.toLowerCase()) ||
        record.scan_type?.toLowerCase().includes(nmapHistorySearchText.toLowerCase()) ||
        record.status?.toLowerCase().includes(nmapHistorySearchText.toLowerCase()) ||
        record.user_email?.toLowerCase().includes(nmapHistorySearchText.toLowerCase())
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

    // ZAP History Card component
    const ZapHistoryCard = ({ record }: { record: ScannerHistoryRecord }) => {
        return (
            <Card
                hoverable
                style={{ height: '100%' }}
                bodyStyle={{ padding: '16px' }}
                onClick={() => handleZapViewHistoryRecord(record)}
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

    // Nmap History Card component
    const NmapHistoryCard = ({ record }: { record: ScannerHistoryRecord }) => {
        return (
            <Card
                hoverable
                style={{ height: '100%' }}
                bodyStyle={{ padding: '16px' }}
                onClick={() => handleNmapViewHistoryRecord(record)}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 500, flex: 1, marginRight: '8px', wordBreak: 'break-all' }}>
                        {record.scan_target}
                    </h4>
                    <Tag color={getHistoryStatusColor(record.status)}>{record.status}</Tag>
                </div>

                <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '8px' }}>
                    <Tag color="purple">{record.scan_type}</Tag>
                    {record.scan_duration && <Tag>{record.scan_duration.toFixed(1)}s</Tag>}
                </div>

                <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
                    {record.user_email && <div>By: {record.user_email}</div>}
                    {record.created_at && <div>{formatTimestamp(record.created_at)}</div>}
                </div>
            </Card>
        );
    };

    return (
        <div>
            {contextHolder}
            <style>{tabStyles}</style>
            <div className={'page-parent security-scanners-page'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys} onOpenChange={menuHighlighting.onOpenChange} />
                <div className={'page-content'}>
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <RadarChartOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Security Scanners"
                                infoContent={SecurityScannersInfo}
                                className="page-title"
                            />
                        </div>
                        <div className="page-header-right">
                            {activeScannerTab === 'network' && (
                                <ScannerGuideWizard
                                    steps={nmapGuideSteps}
                                    title="Network Scanner Guide"
                                    icon={<RadarChartOutlined />}
                                    buttonLabel="Scanner Guide"
                                />
                            )}
                            {activeScannerTab === 'webapp' && (
                                <ScannerGuideWizard
                                    steps={zapGuideSteps}
                                    title="Web App Scanner Guide"
                                    icon={<GlobalOutlined />}
                                    buttonLabel="Scanner Guide"
                                />
                            )}
                        </div>
                    </div>

                    {/* Scanner Type Tabs - Single underline style */}
                    <div className="scanner-tabs" style={{ marginBottom: '24px' }}>
                        <div style={{ display: 'flex', position: 'relative' }}>
                            <button
                                onClick={() => setActiveScannerTab('network')}
                                style={{
                                    padding: '14px 28px',
                                    background: 'none',
                                    border: 'none',
                                    cursor: 'pointer',
                                    fontSize: '15px',
                                    fontWeight: 500,
                                    color: activeScannerTab === 'network' ? '#1890ff' : '#666',
                                    transition: 'all 0.2s ease',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    position: 'relative'
                                }}
                            >
                                <ApiOutlined /> Network Vulnerability
                                {activeScannerTab === 'network' && (
                                    <span style={{
                                        position: 'absolute',
                                        bottom: 0,
                                        left: 0,
                                        right: 0,
                                        height: '3px',
                                        backgroundColor: '#1890ff',
                                        borderRadius: '3px 3px 0 0'
                                    }} />
                                )}
                            </button>
                            <button
                                onClick={() => setActiveScannerTab('webapp')}
                                style={{
                                    padding: '14px 28px',
                                    background: 'none',
                                    border: 'none',
                                    cursor: 'pointer',
                                    fontSize: '15px',
                                    fontWeight: 500,
                                    color: activeScannerTab === 'webapp' ? '#1890ff' : '#666',
                                    transition: 'all 0.2s ease',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '8px',
                                    position: 'relative'
                                }}
                            >
                                <GlobalOutlined /> Application Vulnerability
                                {activeScannerTab === 'webapp' && (
                                    <span style={{
                                        position: 'absolute',
                                        bottom: 0,
                                        left: 0,
                                        right: 0,
                                        height: '3px',
                                        backgroundColor: '#1890ff',
                                        borderRadius: '3px 3px 0 0'
                                    }} />
                                )}
                            </button>
                        </div>
                        <div style={{ height: '1px', backgroundColor: '#e8e8e8' }} />
                    </div>

                    {/* Web App Scanner Content */}
                    {activeScannerTab === 'webapp' && (
                        <>
                            {/* Scan Configuration Card */}
                            <div className="scanner-card">
                                <div className="scanner-card-header">
                                    <h3 className="scanner-card-title">
                                        <GlobalOutlined style={{ color: '#1890ff' }} />
                                        Scan Configuration
                                    </h3>
                                    <div className="status-badge">
                                        {polling && <Tag color="processing">Scanning...</Tag>}
                                        {scanStatus?.isCompleted && <Tag color="success">Completed</Tag>}
                                    </div>
                                </div>

                                <div className="config-grid">
                                    <div className="form-field">
                                        <label>
                                            Scan Type<span className="required">*</span>
                                            <Tooltip title="Click for help on scan types">
                                                <QuestionCircleOutlined
                                                    style={{ marginLeft: '8px', color: '#1890ff', cursor: 'pointer' }}
                                                    onClick={() => setZapScanTypeHelpVisible(true)}
                                                />
                                            </Tooltip>
                                        </label>
                                        <Select
                                            showSearch
                                            placeholder="Choose scan type"
                                            onChange={handleZapScanTypeChange}
                                            options={zapScanOptions}
                                            filterOption={filterOption}
                                            value={zapScanType || undefined}
                                            size="large"
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>
                                            Target URL<span className="required">*</span>
                                            <Tooltip title="Click for help on target URL formats">
                                                <QuestionCircleOutlined
                                                    style={{ marginLeft: '8px', color: '#1890ff', cursor: 'pointer' }}
                                                    onClick={() => setZapTargetHelpVisible(true)}
                                                />
                                            </Tooltip>
                                        </label>
                                        {zapTargetMode === 'custom' ? (
                                            <input
                                                type="text"
                                                className="form-input"
                                                placeholder="https://example.com"
                                                value={targetUrl}
                                                onChange={(e) => setTargetUrl(e.target.value)}
                                                style={{ height: '40px', borderRadius: '8px', border: '1px solid #d9d9d9', padding: '0 12px', fontSize: '14px', marginBottom: '8px' }}
                                            />
                                        ) : (
                                            <>
                                                <Select
                                                    showSearch
                                                    placeholder="Select an asset"
                                                    value={zapSelectedAssetId || undefined}
                                                    onChange={handleZapAssetSelect}
                                                    style={{ width: '100%', marginBottom: '8px' }}
                                                    size="large"
                                                    filterOption={(input, option) =>
                                                        (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
                                                    }
                                                    options={assetsWithIp.map(asset => ({
                                                        value: asset.id,
                                                        label: `${asset.name} (${asset.ip_address})`
                                                    }))}
                                                    notFoundContent={assetsWithIp.length === 0 ? "No assets with IP/URL found" : "No match"}
                                                />
                                                {targetUrl && (
                                                    <div style={{ marginBottom: '8px', fontSize: '12px', color: '#666' }}>
                                                        Target: {targetUrl}
                                                    </div>
                                                )}
                                            </>
                                        )}
                                        <Radio.Group
                                            value={zapTargetMode}
                                            onChange={(e) => {
                                                setZapTargetMode(e.target.value);
                                                if (e.target.value === 'custom') {
                                                    setZapSelectedAssetId(null);
                                                    setTargetUrl('');
                                                }
                                            }}
                                            style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}
                                        >
                                            <Radio value="custom">Enter Custom URL</Radio>
                                            <Radio value="asset">Select from Assets</Radio>
                                        </Radio.Group>
                                    </div>
                                </div>

                                <div className="action-buttons">
                                    <button className="btn-primary" onClick={handleZapRunScan} disabled={zapLoading || polling}>
                                        <PlayCircleOutlined />
                                        {zapLoading ? 'Starting...' : polling ? 'Scanning...' : 'Run Scan'}
                                    </button>
                                    <button className="btn-secondary" onClick={handleZapClear}>
                                        <ClearOutlined />
                                        Clear
                                    </button>
                                    <button
                                        className="btn-secondary"
                                        onClick={() => openScheduleModal('zap', targetUrl, zapScanType)}
                                        disabled={!targetUrl}
                                        style={{ borderColor: '#722ed1', color: '#722ed1' }}
                                    >
                                        <ScheduleOutlined />
                                        Schedule
                                    </button>
                                    <button className="btn-danger" onClick={() => setEmergencyStopModalVisible(true)}>
                                        <StopOutlined />
                                        Stop All Scans
                                    </button>
                                </div>
                            </div>

                            {/* Scan Progress */}
                            {(scanStatus || polling) && (
                                <div className="scan-progress-container">
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                                        <span style={{ fontWeight: 500, color: '#1890ff' }}>{getZapStatusText()}</span>
                                        {polling && !scanStatus?.isCompleted && (
                                            <span style={{ fontSize: '13px', color: '#999' }}>Checking status every second...</span>
                                        )}
                                    </div>
                                    <Progress
                                        percent={scanStatus?.status || 0}
                                        status={scanStatus?.isCompleted ? "success" : "active"}
                                        strokeColor={scanStatus?.isCompleted ? "#52c41a" : "#1890ff"}
                                    />
                                </div>
                            )}

                            {/* Active Scan Details */}
                            {activeScanState && (zapScanType === 'active' || zapScanType === 'full') && (
                                <div className="scanner-card">
                                    <div className="scanner-card-header">
                                        <h3 className="scanner-card-title">Active Scan Details</h3>
                                        <button className="btn-secondary" onClick={handleExportActiveScanToPdf} disabled={!activeScanState}>
                                            <ExportOutlined /> Export Details
                                        </button>
                                    </div>
                                    <Collapse defaultActiveKey={['1']}>
                                        <Collapse.Panel header="Active Scans Overview" key="1">
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
                                        </Collapse.Panel>
                                        <Collapse.Panel header="Scanner Progress Details" key="2">
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
                                                            let statusColor = 'blue';
                                                            if (pluginStatus === 'Pending') statusColor = 'default';
                                                            else if (pluginStatus.includes('%')) {
                                                                const percent = parseInt(pluginStatus, 10);
                                                                if (percent < 30) statusColor = 'orange';
                                                                else if (percent < 70) statusColor = 'blue';
                                                                else statusColor = 'green';
                                                            }
                                                            return (
                                                                <List.Item>
                                                                    <div style={{ width: '100%' }}>
                                                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                                            <div><strong>{pluginName}</strong> <small>(ID: {pluginId}, Quality: {pluginQuality})</small></div>
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
                                        </Collapse.Panel>
                                    </Collapse>
                                </div>
                            )}

                            {/* Unified Scan Results Section */}
                            <div className="scanner-card">
                                <div className="scanner-card-header">
                                    <h3 className="scanner-card-title">
                                        <HistoryOutlined style={{ color: '#1890ff', marginRight: '8px' }} />
                                        Scan Results
                                        {zapScannerHistory.length > 0 && (
                                            <Badge count={zapScannerHistory.length} style={{ backgroundColor: '#1890ff', marginLeft: '8px' }} />
                                        )}
                                        {polling && (
                                            <Tag icon={<RadarChartOutlined spin />} color="processing" style={{ marginLeft: '12px' }}>
                                                Scanning...
                                            </Tag>
                                        )}
                                    </h3>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        {polling && alerts.length > 0 && (
                                            <div className="risk-tags">
                                                <Tag color="red">High: {alerts.filter(a => a.risk === 'High').length}</Tag>
                                                <Tag color="orange">Medium: {alerts.filter(a => a.risk === 'Medium').length}</Tag>
                                                <Tag color="gold">Low: {alerts.filter(a => a.risk === 'Low').length}</Tag>
                                                <Tag color="blue">Info: {alerts.filter(a => a.risk === 'Informational').length}</Tag>
                                            </div>
                                        )}
                                        <Tooltip title="Refresh">
                                            <Button
                                                type="text"
                                                icon={<ReloadOutlined />}
                                                onClick={loadZapScannerHistory}
                                                loading={zapHistoryLoading}
                                            />
                                        </Tooltip>
                                        <Tooltip title="Clear All History">
                                            <Button
                                                type="text"
                                                danger
                                                icon={<DeleteOutlined />}
                                                onClick={handleZapClearHistory}
                                                disabled={zapScannerHistory.length === 0}
                                            />
                                        </Tooltip>
                                    </div>
                                </div>

                                {/* Search and View Toggle */}
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px', padding: '0 16px' }}>
                                    <Input
                                        placeholder="Search history..."
                                        prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                        value={zapHistorySearchText}
                                        onChange={(e) => setZapHistorySearchText(e.target.value)}
                                        style={{ width: '250px' }}
                                    />
                                    <div style={{ display: 'flex', border: '1px solid #d9d9d9', borderRadius: '6px', overflow: 'hidden' }}>
                                        <button
                                            onClick={() => setZapHistoryViewMode('grid')}
                                            style={{
                                                border: 'none',
                                                padding: '6px 12px',
                                                cursor: 'pointer',
                                                backgroundColor: zapHistoryViewMode === 'grid' ? '#1890ff' : 'white',
                                                color: zapHistoryViewMode === 'grid' ? 'white' : '#595959',
                                            }}
                                        >
                                            <AppstoreOutlined />
                                        </button>
                                        <button
                                            onClick={() => setZapHistoryViewMode('list')}
                                            style={{
                                                border: 'none',
                                                borderLeft: '1px solid #d9d9d9',
                                                padding: '6px 12px',
                                                cursor: 'pointer',
                                                backgroundColor: zapHistoryViewMode === 'list' ? '#1890ff' : 'white',
                                                color: zapHistoryViewMode === 'list' ? 'white' : '#595959',
                                            }}
                                        >
                                            <UnorderedListOutlined />
                                        </button>
                                    </div>
                                </div>

                                {zapSearchFilteredHistory.length === 0 ? (
                                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No scan results found." style={{ padding: '40px' }} />
                                ) : zapHistoryViewMode === 'grid' ? (
                                    <div style={{ padding: '0 16px 16px' }}>
                                        <Row gutter={[16, 16]}>
                                            {zapSearchFilteredHistory.map(record => (
                                                <Col key={record.id} xs={24} sm={12} md={8} lg={6}>
                                                    <ZapHistoryCard record={record} />
                                                </Col>
                                            ))}
                                        </Row>
                                    </div>
                                ) : (
                                <Table
                                    columns={ScannerHistoryGridColumns(handleZapExportHistory, handleZapDeleteRecord, handleZapScheduleFromHistory) as any}
                                    dataSource={prepareHistoryTableData(zapSearchFilteredHistory)}
                                    loading={zapHistoryLoading}
                                    pagination={{ pageSize: 10, showSizeChanger: true, showQuickJumper: true, showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} scans` }}
                                    onRow={() => ({
                                        onClick: (e: React.MouseEvent) => {
                                            e.preventDefault();
                                        }
                                    })}
                                    expandable={{
                                        expandedRowKeys: zapExpandedRowKeys,
                                        onExpand: handleZapRowExpand,
                                        expandIcon: ({ expanded, onExpand, record }) => (
                                            <span
                                                onClick={e => {
                                                    e.preventDefault();
                                                    e.stopPropagation();
                                                    onExpand(record, e);
                                                }}
                                                style={{ cursor: 'pointer', color: '#1890ff', padding: '4px' }}
                                            >
                                                {expanded ? <DownOutlined /> : <RightOutlined />}
                                            </span>
                                        ),
                                        expandedRowRender: (record: ScannerHistoryRecord & { key: string }) => {
                                            // Show loading state if fetching results
                                            if (zapLoadingRows.has(record.id)) {
                                                return (
                                                    <div style={{ padding: '40px', textAlign: 'center', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                                                        <SyncOutlined spin style={{ fontSize: '24px', color: '#1890ff' }} />
                                                        <p style={{ marginTop: '12px', color: '#666' }}>Loading scan results...</p>
                                                    </div>
                                                );
                                            }
                                            // Use lazily loaded results
                                            const results = zapLoadedResults[record.id];
                                            if (!results || results.length === 0) {
                                                return <p style={{ padding: '16px', color: '#8c8c8c' }}>No results available.</p>;
                                            }
                                            const alertsData = prepareZapTableData(results);
                                            return (
                                                <div style={{ padding: '16px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                                        <div className="risk-tags">
                                                            <Tag color="red">High: {results.filter((a: any) => a.risk === 'High').length}</Tag>
                                                            <Tag color="orange">Medium: {results.filter((a: any) => a.risk === 'Medium').length}</Tag>
                                                            <Tag color="gold">Low: {results.filter((a: any) => a.risk === 'Low').length}</Tag>
                                                            <Tag color="blue">Info: {results.filter((a: any) => a.risk === 'Informational').length}</Tag>
                                                        </div>
                                                        {aiFeatureSettings?.aiRemediatorEnabled && (
                                                            <Button
                                                                type="primary"
                                                                icon={<RobotOutlined />}
                                                                onClick={() => handleOpenRemediation(record, 'zap')}
                                                                style={{ backgroundColor: '#1890ff' }}
                                                            >
                                                                AI Remediator
                                                            </Button>
                                                        )}
                                                    </div>
                                                    <Table
                                                        columns={ZapGridColumns()}
                                                        dataSource={alertsData}
                                                        pagination={{ pageSize: 5, showSizeChanger: true, showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} alerts` }}
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
                                                                    {alertRecord.evidence && <><h4>Evidence</h4><p>{alertRecord.evidence}</p></>}
                                                                    {alertRecord.reference && <><h4>References</h4><p style={{ whiteSpace: 'pre-line' }}>{alertRecord.reference}</p></>}
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
                                    scroll={{ x: 1000 }}
                                    locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No scan results yet. Configure and run a scan above." /> }}
                                />
                                )}
                            </div>
                        </>
                    )}

                    {/* Network Scanner Content */}
                    {activeScannerTab === 'network' && (
                        <>
                            {/* Scan Configuration Card */}
                            <div className="scanner-card">
                                <div className="scanner-card-header">
                                    <h3 className="scanner-card-title">
                                        <ApiOutlined style={{ color: '#1890ff' }} />
                                        Scan Configuration
                                    </h3>
                                    {nmapLoading && <Tag color="processing">Scanning...</Tag>}
                                </div>

                                <div className="config-grid">
                                    <div className="form-field">
                                        <label>
                                            Scan Type<span className="required">*</span>
                                            <Tooltip title="Click for help on scan types">
                                                <QuestionCircleOutlined
                                                    style={{ marginLeft: '8px', color: '#1890ff', cursor: 'pointer' }}
                                                    onClick={() => setNmapScanTypeHelpVisible(true)}
                                                />
                                            </Tooltip>
                                        </label>
                                        <Select
                                            showSearch
                                            placeholder="Select scan type"
                                            onChange={handleNmapScanTypeChange}
                                            options={nmapScanOptions}
                                            filterOption={filterOption}
                                            value={nmapScanType || undefined}
                                            size="large"
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label>
                                            Target<span className="required">*</span>
                                            <Tooltip title="Click for help on target formats">
                                                <QuestionCircleOutlined
                                                    style={{ marginLeft: '8px', color: '#1890ff', cursor: 'pointer' }}
                                                    onClick={() => setNmapTargetHelpVisible(true)}
                                                />
                                            </Tooltip>
                                        </label>
                                        {nmapTargetMode === 'custom' ? (
                                            <input
                                                type="text"
                                                placeholder="IP address, domain, or network range"
                                                value={nmapTarget}
                                                onChange={(e) => setNmapTarget(e.target.value)}
                                                style={{ height: '40px', borderRadius: '8px', border: '1px solid #d9d9d9', padding: '0 12px', fontSize: '14px', marginBottom: '8px' }}
                                            />
                                        ) : (
                                            <>
                                                <Select
                                                    showSearch
                                                    placeholder="Select an asset"
                                                    value={nmapSelectedAssetId || undefined}
                                                    onChange={handleNmapAssetSelect}
                                                    style={{ width: '100%', marginBottom: '8px' }}
                                                    size="large"
                                                    filterOption={(input, option) =>
                                                        (option?.label?.toString() || '').toLowerCase().includes(input.toLowerCase())
                                                    }
                                                    options={assetsWithIp.map(asset => ({
                                                        value: asset.id,
                                                        label: `${asset.name} (${asset.ip_address})`
                                                    }))}
                                                    notFoundContent={assetsWithIp.length === 0 ? "No assets with IP/URL found" : "No match"}
                                                />
                                                {nmapTarget && (
                                                    <div style={{ marginBottom: '8px', fontSize: '12px', color: '#666' }}>
                                                        Target: {nmapTarget}
                                                    </div>
                                                )}
                                            </>
                                        )}
                                        <Radio.Group
                                            value={nmapTargetMode}
                                            onChange={(e) => {
                                                setNmapTargetMode(e.target.value);
                                                if (e.target.value === 'custom') {
                                                    setNmapSelectedAssetId(null);
                                                    setNmapTarget('');
                                                }
                                            }}
                                            style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}
                                        >
                                            <Radio value="custom">Enter Custom IP/Domain</Radio>
                                            <Radio value="asset">Select from Assets</Radio>
                                        </Radio.Group>
                                    </div>
                                    {nmapScanType === 'ports' && (
                                        <div className="form-field config-grid-full">
                                            <label>Ports<span className="required">*</span></label>
                                            <input
                                                type="text"
                                                placeholder="e.g., 22,80,443 or 1-1000"
                                                value={nmapPorts}
                                                onChange={(e) => setNmapPorts(e.target.value)}
                                                style={{ height: '40px', borderRadius: '8px', border: '1px solid #d9d9d9', padding: '0 12px', fontSize: '14px' }}
                                            />
                                        </div>
                                    )}
                                </div>

                                <div className="action-buttons">
                                    <button className="btn-primary" onClick={handleNmapRunScan} disabled={nmapLoading}>
                                        <PlayCircleOutlined />
                                        {nmapLoading ? 'Scanning...' : 'Run Scan'}
                                    </button>
                                    <button className="btn-secondary" onClick={handleNmapClear}>
                                        <ClearOutlined />
                                        Clear
                                    </button>
                                    <button
                                        className="btn-secondary"
                                        onClick={() => openScheduleModal('nmap', nmapTarget, nmapScanType, nmapScanType === 'ports' ? { ports: nmapPorts } : undefined)}
                                        disabled={!nmapTarget}
                                        style={{ borderColor: '#722ed1', color: '#722ed1' }}
                                    >
                                        <ScheduleOutlined />
                                        Schedule
                                    </button>
                                </div>

                                {nmapLoading && (
                                    <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f0f8ff', border: '1px solid #91caff', borderRadius: '8px' }}>
                                        <p style={{ margin: 0, color: '#1890ff', fontSize: '14px' }}>
                                            Scan in progress... This may take several minutes depending on the scan type and target.
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
                                        {nmapScannerHistory.length > 0 && (
                                            <Badge count={nmapScannerHistory.length} style={{ backgroundColor: '#1890ff', marginLeft: '8px' }} />
                                        )}
                                        {nmapLoading && (
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
                                                onClick={loadNmapScannerHistory}
                                                loading={nmapHistoryLoading}
                                            />
                                        </Tooltip>
                                        <Tooltip title="Clear All History">
                                            <Button
                                                type="text"
                                                danger
                                                icon={<DeleteOutlined />}
                                                onClick={handleNmapClearHistory}
                                                disabled={nmapScannerHistory.length === 0}
                                            />
                                        </Tooltip>
                                    </div>
                                </div>
                                {/* Severity Summary from latest scan */}
                                {nmapScanResults?.summary && (
                                    <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0', display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                                        <span style={{ fontWeight: 500, color: '#666' }}>Latest Scan:</span>
                                        <Tag color="red">High: {nmapScanResults.summary.high}</Tag>
                                        <Tag color="orange">Medium: {nmapScanResults.summary.medium}</Tag>
                                        <Tag color="gold">Low: {nmapScanResults.summary.low}</Tag>
                                        <Tag color="blue">Info: {nmapScanResults.summary.info}</Tag>
                                        <Tag color="default">Total: {nmapScanResults.summary.total}</Tag>
                                        {nmapScanResults.summary.high === 0 && nmapScanResults.summary.medium === 0 && nmapScanResults.summary.low === 0 && (
                                            <Tooltip title="CPE correlation with NVD database found no known CVEs for the detected service versions. This may indicate patched software or limited CVE data.">
                                                <span style={{ fontSize: '12px', color: '#52c41a', cursor: 'help' }}>
                                                    <ExclamationCircleOutlined style={{ marginRight: '4px' }} />
                                                    No known CVEs detected
                                                </span>
                                            </Tooltip>
                                        )}
                                    </div>
                                )}

                                {/* Search and View Toggle */}
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px', padding: '16px 16px 0' }}>
                                    <Input
                                        placeholder="Search history..."
                                        prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                        value={nmapHistorySearchText}
                                        onChange={(e) => setNmapHistorySearchText(e.target.value)}
                                        style={{ width: '250px' }}
                                    />
                                    <div style={{ display: 'flex', border: '1px solid #d9d9d9', borderRadius: '6px', overflow: 'hidden' }}>
                                        <button
                                            onClick={() => setNmapHistoryViewMode('grid')}
                                            style={{
                                                border: 'none',
                                                padding: '6px 12px',
                                                cursor: 'pointer',
                                                backgroundColor: nmapHistoryViewMode === 'grid' ? '#1890ff' : 'white',
                                                color: nmapHistoryViewMode === 'grid' ? 'white' : '#595959',
                                            }}
                                        >
                                            <AppstoreOutlined />
                                        </button>
                                        <button
                                            onClick={() => setNmapHistoryViewMode('list')}
                                            style={{
                                                border: 'none',
                                                borderLeft: '1px solid #d9d9d9',
                                                padding: '6px 12px',
                                                cursor: 'pointer',
                                                backgroundColor: nmapHistoryViewMode === 'list' ? '#1890ff' : 'white',
                                                color: nmapHistoryViewMode === 'list' ? 'white' : '#595959',
                                            }}
                                        >
                                            <UnorderedListOutlined />
                                        </button>
                                    </div>
                                </div>

                                {nmapSearchFilteredHistory.length === 0 ? (
                                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No scan results found." style={{ padding: '40px' }} />
                                ) : nmapHistoryViewMode === 'grid' ? (
                                    <div style={{ padding: '0 16px 16px' }}>
                                        <Row gutter={[16, 16]}>
                                            {nmapSearchFilteredHistory.map(record => (
                                                <Col key={record.id} xs={24} sm={12} md={8} lg={6}>
                                                    <NmapHistoryCard record={record} />
                                                </Col>
                                            ))}
                                        </Row>
                                    </div>
                                ) : (
                                <Table
                                    columns={ScannerHistoryGridColumns(handleNmapExportHistory, handleNmapDeleteRecord, handleNmapScheduleFromHistory) as any}
                                    dataSource={prepareHistoryTableData(nmapSearchFilteredHistory)}
                                    loading={nmapHistoryLoading}
                                    pagination={{ pageSize: 10, showSizeChanger: true, showQuickJumper: true, showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} scans` }}
                                    expandable={{
                                        expandedRowKeys: nmapExpandedRowKeys,
                                        onExpand: handleNmapRowExpand,
                                        expandIcon: ({ expanded, onExpand, record }) => (
                                            <span onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#1890ff', padding: '4px' }}>
                                                {expanded ? <DownOutlined /> : <RightOutlined />}
                                            </span>
                                        ),
                                        expandedRowRender: (record: ScannerHistoryRecord & { key: string }) => {
                                            // Show loading state if fetching results
                                            if (nmapLoadingRows.has(record.id)) {
                                                return (
                                                    <div style={{ padding: '40px', textAlign: 'center', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                                                        <SyncOutlined spin style={{ fontSize: '24px', color: '#1890ff' }} />
                                                        <p style={{ marginTop: '12px', color: '#666' }}>Loading scan results...</p>
                                                    </div>
                                                );
                                            }

                                            // Get results from lazy-loaded cache
                                            const results = nmapLoadedResults[record.id];

                                            // Check if results contain vulnerabilities (new format)
                                            if (results?.vulnerabilities && Array.isArray(results.vulnerabilities)) {
                                                const vulnerabilities = results.vulnerabilities;
                                                const summary = results.summary || { high: 0, medium: 0, low: 0, info: 0, total: 0 };

                                                const getSeverityColor = (severity: string) => {
                                                    switch (severity) {
                                                        case 'High': return 'red';
                                                        case 'Medium': return 'orange';
                                                        case 'Low': return 'gold';
                                                        default: return 'blue';
                                                    }
                                                };

                                                const vulnColumns = [
                                                    {
                                                        title: 'Severity',
                                                        dataIndex: 'severity',
                                                        key: 'severity',
                                                        width: 100,
                                                        render: (severity: string) => <Tag color={getSeverityColor(severity)}>{severity}</Tag>,
                                                        sorter: (a: any, b: any) => {
                                                            const order = { 'High': 0, 'Medium': 1, 'Low': 2, 'Info': 3 };
                                                            return (order[a.severity as keyof typeof order] || 4) - (order[b.severity as keyof typeof order] || 4);
                                                        },
                                                        defaultSortOrder: 'ascend' as const
                                                    },
                                                    {
                                                        title: 'Title',
                                                        dataIndex: 'title',
                                                        key: 'title',
                                                        ellipsis: true
                                                    },
                                                    {
                                                        title: 'Host:Port',
                                                        key: 'hostport',
                                                        width: 150,
                                                        render: (_: any, rec: any) => rec.port ? `${rec.host || '-'}:${rec.port}` : (rec.host || '-')
                                                    },
                                                    {
                                                        title: 'CVE',
                                                        dataIndex: 'cve_id',
                                                        key: 'cve_id',
                                                        width: 140,
                                                        render: (cve: string) => cve ? <a href={`https://nvd.nist.gov/vuln/detail/${cve}`} target="_blank" rel="noopener noreferrer">{cve}</a> : '-'
                                                    },
                                                    {
                                                        title: 'CVSS',
                                                        dataIndex: 'cvss_score',
                                                        key: 'cvss_score',
                                                        width: 80,
                                                        render: (score: number) => score ? score.toFixed(1) : '-'
                                                    }
                                                ];

                                                return (
                                                    <div style={{ padding: '16px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                                                        {aiFeatureSettings?.aiRemediatorEnabled && (
                                                            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
                                                                <Button type="primary" icon={<RobotOutlined />} onClick={() => handleOpenRemediation(record, 'nmap')} style={{ backgroundColor: '#1890ff' }}>
                                                                    AI Remediator
                                                                </Button>
                                                            </div>
                                                        )}
                                                        <div style={{ marginBottom: '12px', display: 'flex', gap: '12px', alignItems: 'center' }}>
                                                            <Tag color="red">High: {summary.high}</Tag>
                                                            <Tag color="orange">Medium: {summary.medium}</Tag>
                                                            <Tag color="gold">Low: {summary.low}</Tag>
                                                            <Tag color="blue">Info: {summary.info}</Tag>
                                                            <Tag color="default">Total: {summary.total}</Tag>
                                                        </div>
                                                        <Table
                                                            columns={vulnColumns}
                                                            dataSource={vulnerabilities.map((v: any, i: number) => ({ ...v, key: v.id || i }))}
                                                            pagination={{ pageSize: 10, size: 'small' }}
                                                            size="small"
                                                            scroll={{ x: 700 }}
                                                            expandable={{
                                                                expandIcon: ({ expanded, onExpand, record }) => (
                                                                    <span onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#1890ff', padding: '4px' }}>
                                                                        {expanded ? <DownOutlined /> : <RightOutlined />}
                                                                    </span>
                                                                ),
                                                                expandedRowRender: (vuln: any) => (
                                                                    <div style={{ padding: '12px 16px', backgroundColor: '#fff', borderRadius: '6px', border: '1px solid #f0f0f0' }}>
                                                                        <div style={{ marginBottom: '12px' }}>
                                                                            <strong style={{ color: '#333' }}>Description:</strong>
                                                                            <p style={{ margin: '4px 0 0 0', color: '#666', lineHeight: 1.6 }}>{vuln.description || 'No description available'}</p>
                                                                        </div>
                                                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
                                                                            {vuln.service_name && (
                                                                                <div>
                                                                                    <strong style={{ color: '#333' }}>Service:</strong>
                                                                                    <p style={{ margin: '4px 0 0 0', color: '#666' }}>{vuln.service_name} {vuln.service_version || ''}</p>
                                                                                </div>
                                                                            )}
                                                                            {vuln.protocol && (
                                                                                <div>
                                                                                    <strong style={{ color: '#333' }}>Protocol:</strong>
                                                                                    <p style={{ margin: '4px 0 0 0', color: '#666' }}>{vuln.protocol.toUpperCase()}</p>
                                                                                </div>
                                                                            )}
                                                                            {vuln.cpe && (
                                                                                <div style={{ gridColumn: '1 / -1' }}>
                                                                                    <strong style={{ color: '#333' }}>CPE:</strong>
                                                                                    <p style={{ margin: '4px 0 0 0' }}>
                                                                                        <code style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '2px 6px', borderRadius: '4px' }}>{vuln.cpe}</code>
                                                                                    </p>
                                                                                </div>
                                                                            )}
                                                                            {vuln.cwe_ids && vuln.cwe_ids.length > 0 && (
                                                                                <div>
                                                                                    <strong style={{ color: '#333' }}>CWE:</strong>
                                                                                    <p style={{ margin: '4px 0 0 0', color: '#666' }}>{vuln.cwe_ids.join(', ')}</p>
                                                                                </div>
                                                                            )}
                                                                            {vuln.references && vuln.references.length > 0 && (
                                                                                <div style={{ gridColumn: '1 / -1' }}>
                                                                                    <strong style={{ color: '#333' }}>References:</strong>
                                                                                    <div style={{ margin: '4px 0 0 0' }}>
                                                                                        {vuln.references.slice(0, 3).map((ref: any, idx: number) => (
                                                                                            <a key={idx} href={ref.url || ref} target="_blank" rel="noopener noreferrer" style={{ display: 'block', fontSize: '12px', marginBottom: '2px' }}>
                                                                                                {ref.url || ref}
                                                                                            </a>
                                                                                        ))}
                                                                                        {vuln.references.length > 3 && <span style={{ fontSize: '12px', color: '#999' }}>...and {vuln.references.length - 3} more</span>}
                                                                                    </div>
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                    </div>
                                                                )
                                                            }}
                                                        />
                                                    </div>
                                                );
                                            }

                                            // Fallback for old format or text results
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
                                                    {aiFeatureSettings?.aiRemediatorEnabled && (
                                                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
                                                            <Button
                                                                type="primary"
                                                                icon={<RobotOutlined />}
                                                                onClick={() => handleOpenRemediation(record, 'nmap')}
                                                                style={{ backgroundColor: '#1890ff' }}
                                                            >
                                                                AI Remediator
                                                            </Button>
                                                        </div>
                                                    )}
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
                                    locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No scan results yet. Configure and run a scan above." /> }}
                                />
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* ZAP Stop Scans Modal */}
            <Modal
                title={<span><ExclamationCircleOutlined style={{ color: '#ff4d4f', marginRight: '8px' }} /> Stop All Scans</span>}
                open={emergencyStopModalVisible}
                onOk={handleZapEmergencyStop}
                onCancel={() => setEmergencyStopModalVisible(false)}
                okText="Stop All Scans"
                cancelText="Cancel"
                okButtonProps={{ danger: true }}
            >
                <p style={{ marginBottom: '16px' }}>
                    <strong>Warning:</strong> This will forcefully stop all running scans and clear all data.
                </p>
                <ul style={{ color: '#666', paddingLeft: '20px' }}>
                    <li>Stops all active and spider scans</li>
                    <li>Clears all alerts and results</li>
                    <li>Creates a new session</li>
                </ul>
                <p style={{ color: '#ff4d4f', marginTop: '16px', fontWeight: 500 }}>
                    This action cannot be undone.
                </p>
            </Modal>


            {/* Semgrep History Results Modal */}
            <Modal
                title={semgrepSelectedHistoryRecord ? `Scan Results - ${formatTimestamp(semgrepSelectedHistoryRecord.timestamp)}` : 'Scan Results'}
                open={semgrepHistoryModalVisible}
                onCancel={() => { setSemgrepHistoryModalVisible(false); setSemgrepSelectedHistoryRecord(null); setSemgrepHistoricalResults(''); }}
                footer={[<Button key="close" onClick={() => { setSemgrepHistoryModalVisible(false); setSemgrepSelectedHistoryRecord(null); setSemgrepHistoricalResults(''); }}>Close</Button>]}
                width={1000}
            >
                {semgrepSelectedHistoryRecord && (
                    <div>
                        <div style={{ marginBottom: '20px', padding: '16px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                                <div><strong>Target:</strong><br />{semgrepSelectedHistoryRecord.scan_target}</div>
                                <div><strong>Scan Type:</strong><br />{semgrepSelectedHistoryRecord.scan_type || 'N/A'}</div>
                                <div><strong>Status:</strong><br /><Tag color={semgrepSelectedHistoryRecord.status === 'completed' ? 'green' : 'red'}>{semgrepSelectedHistoryRecord.status.toUpperCase()}</Tag></div>
                                <div><strong>Duration:</strong><br />{semgrepSelectedHistoryRecord.scan_duration ? `${semgrepSelectedHistoryRecord.scan_duration.toFixed(2)}s` : 'N/A'}</div>
                            </div>
                        </div>
                        <div style={{ backgroundColor: '#fafafa', padding: '16px', borderRadius: '8px', maxHeight: '500px', overflow: 'auto', fontFamily: 'monospace', fontSize: '13px', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                            {semgrepHistoricalResults}
                        </div>
                    </div>
                )}
            </Modal>

            {/* OSV History Results Modal */}
            <Modal
                title={osvSelectedHistoryRecord ? `Scan Results - ${formatTimestamp(osvSelectedHistoryRecord.timestamp)}` : 'Scan Results'}
                open={osvHistoryModalVisible}
                onCancel={() => { setOsvHistoryModalVisible(false); setOsvSelectedHistoryRecord(null); setOsvHistoricalResults(''); }}
                footer={[<Button key="close" onClick={() => { setOsvHistoryModalVisible(false); setOsvSelectedHistoryRecord(null); setOsvHistoricalResults(''); }}>Close</Button>]}
                width={1000}
            >
                {osvSelectedHistoryRecord && (
                    <div>
                        <div style={{ marginBottom: '20px', padding: '16px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                                <div><strong>Target:</strong><br />{osvSelectedHistoryRecord.scan_target}</div>
                                <div><strong>Scan Type:</strong><br />{osvSelectedHistoryRecord.scan_type || 'N/A'}</div>
                                <div><strong>Status:</strong><br /><Tag color={osvSelectedHistoryRecord.status === 'completed' ? 'green' : 'red'}>{osvSelectedHistoryRecord.status.toUpperCase()}</Tag></div>
                                <div><strong>Duration:</strong><br />{osvSelectedHistoryRecord.scan_duration ? `${osvSelectedHistoryRecord.scan_duration.toFixed(2)}s` : 'N/A'}</div>
                            </div>
                        </div>
                        <div style={{ backgroundColor: '#fafafa', padding: '16px', borderRadius: '8px', maxHeight: '500px', overflow: 'auto', fontFamily: 'monospace', fontSize: '13px', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                            {osvHistoricalResults}
                        </div>
                    </div>
                )}
            </Modal>

            {/* AI Remediation Modal */}
            <RemediationModal
                visible={remediationModalVisible}
                onClose={() => {
                    setRemediationModalVisible(false);
                    setSelectedHistoryForRemediation(null);
                }}
                scannerType={remediatorScannerType}
                historyId={selectedHistoryForRemediation?.id || ''}
                scanTarget={selectedHistoryForRemediation?.scan_target}
            />

            {/* Schedule Scan Modal */}
            <ScheduleScanModal
                open={scheduleModalVisible}
                onClose={() => setScheduleModalVisible(false)}
                scannerType={scheduleModalScannerType}
                scanTarget={scheduleModalScanTarget}
                scanType={scheduleModalScanType}
                scanConfig={scheduleModalScanConfig}
            />

            {/* Nmap Scan Type Help Modal */}
            <Modal
                title={<span><QuestionCircleOutlined style={{ color: '#1890ff', marginRight: '8px' }} />Network Scan Types</span>}
                open={nmapScanTypeHelpVisible}
                onCancel={() => setNmapScanTypeHelpVisible(false)}
                footer={[<Button key="close" type="primary" onClick={() => setNmapScanTypeHelpVisible(false)}>Got it</Button>]}
                width={700}
            >
                <div style={{ maxHeight: '60vh', overflow: 'auto' }}>
                    <h4 style={{ color: '#1890ff', marginBottom: '12px' }}>🔍 Vulnerability Scanning</h4>
                    <p style={{ color: '#666', marginBottom: '16px' }}>These scan types detect service versions and correlate them with the NVD database to find known vulnerabilities (CVEs).</p>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Fast Scan</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Scans the top 100 most common ports. Quick reconnaissance to identify the most likely open services. Good for initial discovery.</p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Basic Scan</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Scans the top 1000 ports. A balanced approach that covers most common services without being too slow.</p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Specific Port Scan</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Scan only specific ports you specify. Use when you know which services you want to check.</p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Stealth Scan</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Uses SYN scan technique which is less likely to be logged by the target. Sends SYN packets without completing the TCP handshake.</p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>No Ping Scan</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Skips host discovery and assumes the target is up. Useful when ICMP ping is blocked by firewalls.</p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Aggressive Scan</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Comprehensive scan including OS detection, version detection, script scanning, and traceroute. More intrusive but provides detailed information.</p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>OS Detection</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Attempts to identify the operating system running on the target by analyzing TCP/IP stack fingerprints.</p>
                    </div>

                    <Divider style={{ margin: '20px 0' }} />

                    <h4 style={{ color: '#1890ff', marginBottom: '12px' }}>📡 Port & Network Discovery</h4>
                    <p style={{ color: '#666', marginBottom: '16px' }}>These scan types focus on network discovery without detailed vulnerability analysis.</p>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Network Discovery</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Ping sweep to find live hosts on a network. Does not scan ports - only identifies which hosts are online. Fast for mapping large networks.</p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>All Ports Scan</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Scans all 65,535 TCP ports. Very thorough but can take a long time. Use when you need to find services on non-standard ports.</p>
                    </div>
                </div>
            </Modal>

            {/* Nmap Target Help Modal */}
            <Modal
                title={<span><QuestionCircleOutlined style={{ color: '#1890ff', marginRight: '8px' }} />Target Input Formats</span>}
                open={nmapTargetHelpVisible}
                onCancel={() => setNmapTargetHelpVisible(false)}
                footer={[<Button key="close" type="primary" onClick={() => setNmapTargetHelpVisible(false)}>Got it</Button>]}
                width={600}
            >
                <div style={{ maxHeight: '60vh', overflow: 'auto' }}>
                    <p style={{ color: '#666', marginBottom: '16px' }}>You can specify targets in several formats:</p>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Single IP Address</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>192.168.1.100</code></p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Domain Name</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>example.com</code> or <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>scanme.example.org</code></p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>CIDR Notation</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Scan an entire subnet.</p>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>192.168.1.0/24</code> (scans 256 addresses)</p>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>10.0.0.0/16</code> (scans 65,536 addresses)</p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>IP Range with Dash</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Scan a range of addresses in the last octet.</p>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>192.168.1.1-50</code> (scans .1 through .50)</p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Multiple Targets (Space-Separated)</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Scan multiple targets at once.</p>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>192.168.1.1 192.168.1.2 example.com</code></p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Wildcard</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Use asterisk to scan all addresses in an octet.</p>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>192.168.1.*</code> (same as /24)</p>
                    </div>

                    <Divider style={{ margin: '16px 0' }} />

                    <div style={{ padding: '12px', backgroundColor: '#fff7e6', borderRadius: '6px', border: '1px solid #ffd591' }}>
                        <strong style={{ color: '#d46b08' }}>⚠️ Important Notes</strong>
                        <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px', color: '#666' }}>
                            <li>Only scan networks you have permission to scan</li>
                            <li>Large network ranges may take a long time to complete</li>
                            <li>Some networks may block or rate-limit scans</li>
                        </ul>
                    </div>
                </div>
            </Modal>

            {/* Legal Disclaimer Modal */}
            <ScannerLegalModal open={legalModalVisible} scannerName={legalScannerName} onOk={legalHandleOk} onCancel={legalHandleCancel} />

            {/* ZAP Scan Type Help Modal */}
            <Modal
                title={<span><QuestionCircleOutlined style={{ color: '#1890ff', marginRight: '8px' }} />Application Scan Types</span>}
                open={zapScanTypeHelpVisible}
                onCancel={() => setZapScanTypeHelpVisible(false)}
                footer={[<Button key="close" type="primary" onClick={() => setZapScanTypeHelpVisible(false)}>Got it</Button>]}
                width={700}
            >
                <div style={{ maxHeight: '60vh', overflow: 'auto' }}>
                    <p style={{ color: '#666', marginBottom: '16px' }}>The Web App Scanner offers different scan types for web application security testing:</p>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Spider Scan</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Crawls the target website to discover all accessible pages and resources. This is a passive scan that maps the application structure without attacking it. Use this first to understand the scope of the application.</p>
                        <p style={{ margin: '8px 0 0 0', color: '#52c41a', fontSize: '12px' }}>✓ Safe - Does not attempt attacks</p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Active Scan</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Actively tests for vulnerabilities by sending malicious payloads to the discovered pages. Tests for common web vulnerabilities including SQL injection, XSS, command injection, and more. Run this after a Spider scan for best results.</p>
                        <p style={{ margin: '8px 0 0 0', color: '#ff4d4f', fontSize: '12px' }}>⚠️ Intrusive - May affect application behavior</p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Full Scan</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Combines Spider and Active scans in sequence. First crawls the entire application, then performs vulnerability testing on all discovered pages. This is the most comprehensive option but takes the longest.</p>
                        <p style={{ margin: '8px 0 0 0', color: '#ff4d4f', fontSize: '12px' }}>⚠️ Intrusive - Comprehensive testing</p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>API Scan</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Specialized scan for REST APIs. Imports an OpenAPI/Swagger specification to understand the API structure and tests each endpoint for vulnerabilities. Ideal for testing backend services and microservices.</p>
                        <p style={{ margin: '8px 0 0 0', color: '#1890ff', fontSize: '12px' }}>📋 Requires OpenAPI/Swagger URL</p>
                    </div>

                    <Divider style={{ margin: '16px 0' }} />

                    <h4 style={{ marginBottom: '12px' }}>Vulnerability Categories Detected</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
                        <div style={{ padding: '8px', backgroundColor: '#fff1f0', borderRadius: '4px', fontSize: '13px' }}>
                            <Tag color="red">High</Tag> SQL Injection, Remote Code Execution
                        </div>
                        <div style={{ padding: '8px', backgroundColor: '#fff7e6', borderRadius: '4px', fontSize: '13px' }}>
                            <Tag color="orange">Medium</Tag> XSS, CSRF, Path Traversal
                        </div>
                        <div style={{ padding: '8px', backgroundColor: '#fffbe6', borderRadius: '4px', fontSize: '13px' }}>
                            <Tag color="gold">Low</Tag> Information Disclosure, Weak Headers
                        </div>
                        <div style={{ padding: '8px', backgroundColor: '#e6f7ff', borderRadius: '4px', fontSize: '13px' }}>
                            <Tag color="blue">Info</Tag> Server Information, Cookie Settings
                        </div>
                    </div>
                </div>
            </Modal>

            {/* ZAP Target URL Help Modal */}
            <Modal
                title={<span><QuestionCircleOutlined style={{ color: '#1890ff', marginRight: '8px' }} />Target URL Formats</span>}
                open={zapTargetHelpVisible}
                onCancel={() => setZapTargetHelpVisible(false)}
                footer={[<Button key="close" type="primary" onClick={() => setZapTargetHelpVisible(false)}>Got it</Button>]}
                width={600}
            >
                <div style={{ maxHeight: '60vh', overflow: 'auto' }}>
                    <p style={{ color: '#666', marginBottom: '16px' }}>Enter the URL of the web application you want to scan:</p>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>Basic Website URL</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>https://example.com</code></p>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>http://192.168.1.100</code></p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>URL with Port</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>For applications running on non-standard ports.</p>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>https://example.com:8443</code></p>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>http://localhost:3000</code></p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>URL with Path</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>To limit scanning to a specific section of the site.</p>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>https://example.com/app</code></p>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>https://example.com/api/v1</code></p>
                    </div>

                    <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
                        <strong>API Specification URL (for API Scan)</strong>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>URL to your OpenAPI/Swagger specification file.</p>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>https://api.example.com/swagger.json</code></p>
                        <p style={{ margin: '4px 0 0 0', color: '#666' }}>Example: <code style={{ backgroundColor: '#e6f7ff', padding: '2px 6px', borderRadius: '4px' }}>https://api.example.com/openapi.yaml</code></p>
                    </div>

                    <Divider style={{ margin: '16px 0' }} />

                    <div style={{ padding: '12px', backgroundColor: '#f6ffed', borderRadius: '6px', border: '1px solid #b7eb8f', marginBottom: '12px' }}>
                        <strong style={{ color: '#389e0d' }}>✓ Best Practices</strong>
                        <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px', color: '#666' }}>
                            <li>Always use HTTPS when available for accurate results</li>
                            <li>Include the full base URL of the application</li>
                            <li>For API scans, provide the direct link to the spec file</li>
                        </ul>
                    </div>

                    <div style={{ padding: '12px', backgroundColor: '#fff7e6', borderRadius: '6px', border: '1px solid #ffd591' }}>
                        <strong style={{ color: '#d46b08' }}>⚠️ Important Notes</strong>
                        <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px', color: '#666' }}>
                            <li>Only scan applications you have permission to test</li>
                            <li>Active scans may affect application performance</li>
                            <li>Test against staging/development environments when possible</li>
                        </ul>
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default SecurityScannersPage;
