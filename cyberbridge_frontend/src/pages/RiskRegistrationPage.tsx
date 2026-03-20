import {AutoComplete, Select, Table, notification, Tag, Modal, Tabs, Card, Progress, Row, Col, Input, Empty, Collapse, Tooltip, Button} from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { CompassOutlined, PlusOutlined, EditOutlined, DatabaseOutlined, UnorderedListOutlined, DashboardOutlined, WarningOutlined, ExclamationCircleOutlined, InfoCircleOutlined, CheckCircleOutlined, SafetyCertificateOutlined, AlertOutlined, ThunderboltOutlined, ClockCircleOutlined, FilePdfOutlined, AppstoreOutlined, SearchOutlined, LinkOutlined, BulbOutlined, EyeOutlined, SafetyOutlined } from '@ant-design/icons';
import useRiskStore from "../store/useRiskStore.ts";
import useControlStore from "../store/useControlStore.ts";
import {useEffect, useState, useMemo} from "react";
import {RisksGridColumns, onRisksTableChange} from "../constants/RisksGridColumns.tsx";
import {exportRisksToPdf} from "../utils/riskPdfUtils.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import { RisksInfo } from "../constants/infoContent.tsx";
import useAssetStore from "../store/useAssetStore.ts";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import useCRAFilteredFrameworks from "../hooks/useCRAFilteredFrameworks.ts";
import useUserStore from "../store/useUserStore.ts";
import useAuthStore from "../store/useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import RiskTemplatesSection from "../components/RiskTemplatesSection.tsx";
import { StatCard, QuickActionsPanel, QuickActionButton, DashboardSection } from "../components/dashboard";
import ConnectionBoard from "../components/ConnectionBoard.tsx";
import { filterByRelevance } from "../utils/recommendationUtils.ts";

const RiskRegistrationPage = () => {
    // Menu highlighting
    const [location, navigate] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Tab state
    const [activeTab, setActiveTab] = useState<string>('dashboard');

    // View mode state for Risk Registry
    const [riskViewMode, setRiskViewMode] = useState<'grid' | 'list'>('list');
    const [riskSearchText, setRiskSearchText] = useState('');

    // Store access
    const {
        risks,
        assetCategories,
        riskCategories,
        riskSeverities,
        riskStatuses,
        fetchRisks,
        fetchAssetCategories,
        fetchRiskCategories,
        fetchRiskSeverities,
        fetchRiskStatuses,
        createRisk,
        updateRisk,
        deleteRisk,
        error
    } = useRiskStore();

    const {fetchAssets, assets} = useAssetStore();
    const {organisations, fetchOrganisations} = useUserStore();
    const {controls, fetchControls, linkControlToRisk, unlinkControlFromRisk, controlTemplates, fetchControlTemplates, importControlsFromTemplate} = useControlStore();

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    // Filtered data state for PDF export
    const [filteredRisks, setFilteredRisks] = useState(risks);

    // Update filtered risks when risks change
    useEffect(() => {
        setFilteredRisks(risks);
    }, [risks]);

    // Selected risk state
    const [selectedRisk, setSelectedRisk] = useState<string | null>(null);
    const [riskCode, setRiskCode] = useState<string>('');

    // Form visibility state
    const [showForm, setShowForm] = useState<boolean>(false);

    // Form state
    const [assetCategoryId, setAssetCategoryId] = useState<string | undefined>(undefined);
    const [riskCategoryName, setRiskCategoryName] = useState('');
    const [riskDescription, setRiskDescription] = useState('');
    const [potentialImpact, setPotentialImpact] = useState('');
    const [controlsText, setControlsText] = useState('');
    const [statusId, setStatusId] = useState<string | undefined>(undefined);
    const [likelihoodId, setLikelihoodId] = useState<string | undefined>(undefined);
    const [severityId, setSeverityId] = useState<string | undefined>(undefined);
    const [residualRiskId, setResidualRiskId] = useState<string | undefined>(undefined);
    const [assessmentStatus, setAssessmentStatus] = useState<string>('Not Assessed');

    // Scope-related state
    const [scopeTypes, setScopeTypes] = useState<Array<{id: string, scope_name: string}>>([]);
    const [selectedScopeType, setSelectedScopeType] = useState<string>('');
    const [selectedScopeEntityId, setSelectedScopeEntityId] = useState<string>('');

    // Risk categories for autocomplete
    const [filteredRiskCategories, setFilteredRiskCategories] = useState<{ id: string; value: string }[]>([]);

    // Connection tab state
    const [selectedConnectionRisk, setSelectedConnectionRisk] = useState<string | undefined>(undefined);
    const [connectionFrameworkId, setConnectionFrameworkId] = useState<string | undefined>(undefined);
    const [recommendationLoading, setRecommendationLoading] = useState<Record<string, boolean>>({});

    // Framework store
    const { fetchFrameworks } = useFrameworksStore();
    const { filteredFrameworks, craFrameworkId, isCRAModeActive } = useCRAFilteredFrameworks();

    // Fetch scope types on mount
    useEffect(() => {
        const fetchScopeTypes = async () => {
            try {
                const response = await fetch(`${cyberbridge_back_end_rest_api}/scopes/`, {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    setScopeTypes(data);
                }
            } catch (error) {
                console.error('Error fetching scope types:', error);
            }
        };
        fetchScopeTypes();
    }, []);

    // Fetch dropdown options and risks on component mount
    useEffect(() => {
        const fetchData = async () => {
            try {
                // Execute all fetch operations sequentially
                await fetchAssetCategories();
                await fetchRiskSeverities();
                await fetchRiskStatuses();
                await fetchRiskCategories();
                await fetchAssets();
                await fetchOrganisations();
                await fetchRisks();
                await fetchControls();
                await fetchFrameworks();
            } catch (error) {
                console.error('Error fetching data:', error);
            }
        };
        fetchData();
    }, [fetchAssetCategories, fetchRiskSeverities, fetchRiskStatuses, fetchRiskCategories, fetchAssets, fetchOrganisations, fetchRisks, fetchControls, fetchFrameworks]);

    // Auto-select CRA framework when CRA mode is active
    useEffect(() => {
        if (isCRAModeActive && craFrameworkId && !connectionFrameworkId) {
            setConnectionFrameworkId(craFrameworkId);
        }
    }, [isCRAModeActive, craFrameworkId]);

    // Fetch linked data when connection risk changes
    const { fetchLinkedControls, fetchLinkedAssets, linkedControls, linkedAssets, fetchLinkedFindings, linkedFindings, unlinkFinding } = useRiskStore();
    useEffect(() => {
        if (selectedConnectionRisk) {
            fetchLinkedAssets(selectedConnectionRisk);
            fetchLinkedFindings(selectedConnectionRisk);
        }
    }, [selectedConnectionRisk, fetchLinkedAssets, fetchLinkedFindings]);

    // Fetch linked controls when connection risk or framework changes (controls are framework-scoped)
    useEffect(() => {
        if (selectedConnectionRisk && connectionFrameworkId) {
            fetchLinkedControls(selectedConnectionRisk, connectionFrameworkId);
        }
    }, [selectedConnectionRisk, connectionFrameworkId, fetchLinkedControls]);

    useEffect(() => {
        if (controlTemplates.length === 0) {
            fetchControlTemplates();
        }
    }, [controlTemplates.length, fetchControlTemplates]);


    // Update autocomplete options when risk categories or asset category changes
    useEffect(() => {
        // Filter risk categories based on selected asset category
        const filteredCategories = assetCategoryId
            ? riskCategories.filter(category => category.asset_category_id === assetCategoryId)
            : riskCategories;

        const options = filteredCategories.map(category => ({
            id: category.id,
            value: category.risk_category_name
        }));
        setFilteredRiskCategories(options);
    }, [riskCategories, assetCategoryId]);

    // Handle risk category selection
    const handleRiskCategorySelect = (value: string) => {
        const selectedCategory = riskCategories.find(category => category.risk_category_name === value);
        if (selectedCategory) {
            setRiskCategoryName(selectedCategory.risk_category_name);
            setRiskDescription(selectedCategory.risk_category_description || '');
            setPotentialImpact(selectedCategory.risk_potential_impact || '');
            setControlsText(selectedCategory.risk_control || '');
        }
    };

    // Filter options for autocomplete and select components
    const filterOption = (inputValue: string, option: {id: string; value: string} | undefined) => {
        return option!.value.toUpperCase().indexOf(inputValue.toUpperCase()) !== -1;
    };

    const handleImportAndLinkRecommendation = async (templateName: string) => {
        if (!selectedConnectionRisk || !connectionFrameworkId) {
            api.warning({
                message: !selectedConnectionRisk ? 'No Risk Selected' : 'No Framework Selected',
                description: !selectedConnectionRisk
                    ? 'Select a risk in the Connections tab before importing controls.'
                    : 'Select a framework in the Connections tab before importing controls.',
                duration: 4,
            });
            return;
        }

        setRecommendationLoading((prev) => ({ ...prev, [templateName]: true }));
        try {
            const result = await importControlsFromTemplate(templateName);
            if (result.success && result.imported_control_ids.length > 0) {
                for (const controlId of result.imported_control_ids) {
                    await linkControlToRisk(controlId, selectedConnectionRisk, connectionFrameworkId);
                }
                await fetchLinkedControls(selectedConnectionRisk, connectionFrameworkId);
                api.success({
                    message: 'Controls Imported & Linked',
                    description: `Imported ${result.imported_control_ids.length} control(s) and linked to risk`,
                    duration: 4,
                });
            } else if (result.success && result.imported_count === 0) {
                api.info({
                    message: 'Already Imported',
                    description: result.message || 'All controls from this template have already been imported.',
                    duration: 4,
                });
            } else {
                api.error({
                    message: 'Import Failed',
                    description: result.message || 'Failed to import controls from template',
                    duration: 4,
                });
            }
        } catch {
            api.error({
                message: 'Import Failed',
                description: 'An unexpected error occurred',
                duration: 4,
            });
        } finally {
            setRecommendationLoading((prev) => ({ ...prev, [templateName]: false }));
        }
    };

    // Handle form submission
    const handleSave = async () => {
        const normalizedRiskCode = riskCode.trim();
        const normalizedRiskCategoryName = riskCategoryName.trim();

        if (!normalizedRiskCode || !assetCategoryId || !normalizedRiskCategoryName || !statusId || !likelihoodId || !severityId || !residualRiskId) {
            api.error({
                message: 'Risk Operation Failed',
                description: 'Please fill in all required fields (Code, Asset Category, Risk Category, Status, Likelihood, Severity, Residual Risk)',
                duration: 4,
            });
            return;
        }

        const duplicateCode = risks.some(
            (risk) =>
                risk.id !== selectedRisk &&
                (risk.risk_code || '').trim().toLowerCase() === normalizedRiskCode.toLowerCase()
        );

        if (duplicateCode) {
            api.error({
                message: 'Risk Operation Failed',
                description: `Risk code "${normalizedRiskCode}" already exists.`,
                duration: 4,
            });
            return;
        }

        const isValidAssetCategory = assetCategories.some((type) => type.id === assetCategoryId);
        const isValidStatus = riskStatuses.some((status) => status.id === statusId);
        const isValidLikelihood = riskSeverities.some((severity) => severity.id === likelihoodId);
        const isValidSeverity = riskSeverities.some((severity) => severity.id === severityId);
        const isValidResidual = riskSeverities.some((severity) => severity.id === residualRiskId);

        if (!isValidAssetCategory || !isValidStatus || !isValidLikelihood || !isValidSeverity || !isValidResidual) {
            api.error({
                message: 'Risk Operation Failed',
                description: 'One or more selected values are outdated. Refresh the page and reselect status/severity values.',
                duration: 5,
            });
            return;
        }

        const scopeRequiresEntity =
            selectedScopeType === 'Product' ||
            selectedScopeType === 'Asset' ||
            selectedScopeType === 'Organization';

        const shouldIgnoreScope = !!selectedScopeType && scopeRequiresEntity && !selectedScopeEntityId;
        const effectiveScopeType = shouldIgnoreScope ? undefined : (selectedScopeType || undefined);
        const effectiveScopeEntityId = shouldIgnoreScope ? undefined : (selectedScopeEntityId || undefined);

        if (shouldIgnoreScope) {
            api.warning({
                message: 'Scope Not Applied',
                description: `${getScopeLabel(selectedScopeType)} was selected without an entity. Risk will be saved without scope.`,
                duration: 4,
            });
        }

        let success;
        const isUpdate = selectedRisk !== null;

        try {
            if (isUpdate && selectedRisk) {
                // Update existing risk
                success = await updateRisk(
                    selectedRisk,
                    normalizedRiskCode,
                    assetCategoryId,
                    normalizedRiskCategoryName,
                    riskDescription,
                    potentialImpact,
                    controlsText,
                    likelihoodId,
                    residualRiskId,
                    severityId,
                    statusId,
                    assessmentStatus,
                    effectiveScopeType,
                    effectiveScopeEntityId
                );
            } else {
                // Create new risk
                success = await createRisk(
                    normalizedRiskCode,
                    assetCategoryId,
                    normalizedRiskCategoryName,
                    riskDescription,
                    potentialImpact,
                    controlsText,
                    likelihoodId,
                    residualRiskId,
                    severityId,
                    statusId,
                    assessmentStatus,
                    effectiveScopeType,
                    effectiveScopeEntityId
                );
            }

            if (success) {
                api.success({
                    message: isUpdate ? 'Risk Update Success' : 'Risk Creation Success',
                    description: isUpdate ? 'Risk updated successfully' : 'Risk created successfully',
                    duration: 4,
                });
                handleClear(true); // Hide form after successful save
                // Refresh risks to show the newly created/updated risk
                const refreshRisks = async () => {
                    try {
                        // Fetch risks
                        await fetchRisks();
                    } catch (error) {
                        console.error('Error refreshing risks:', error);
                    }
                };
                refreshRisks();
            } else {
                api.error({
                    message: isUpdate ? 'Risk Update Failed' : 'Risk Creation Failed',
                    description: error || (isUpdate ? 'Failed to update risk' : 'Failed to create risk'),
                    duration: 4,
                });
            }
        } catch (error) {
            console.error('Error saving risk:', error);
            api.error({
                message: isUpdate ? 'Risk Update Failed' : 'Risk Creation Failed',
                description: 'An unexpected error occurred',
                duration: 4,
            });
        }
    };

    // Clear form
    const handleClear = (hideForm: boolean = false) => {
        setRiskCode('');
        setAssetCategoryId(undefined);
        setRiskCategoryName('');
        setRiskDescription('');
        setPotentialImpact('');
        setControlsText('');
        setStatusId(undefined);
        setLikelihoodId(undefined);
        setSeverityId(undefined);
        setResidualRiskId(undefined);
        setAssessmentStatus('Not Assessed');
        setSelectedScopeType('');
        setSelectedScopeEntityId('');
        setSelectedRisk(null);
        if (hideForm) {
            setShowForm(false);
        }
    };

    // Handle risk deletion
    const handleDelete = async () => {
        if (!selectedRisk) {
            api.error({
                message: 'Risk Deletion Failed',
                description: 'Please select a risk to delete',
                duration: 4,
            });
            return;
        }

        try {
            const success = await deleteRisk(selectedRisk);

            if (success) {
                api.success({
                    message: 'Risk Deletion Success',
                    description: 'Risk deleted successfully',
                    duration: 4,
                });
                handleClear(true); // Hide form after successful delete
                // Refresh risks to update the table
                const refreshRisks = async () => {
                    try {
                        // Fetch risks
                        await fetchRisks();
                    } catch (error) {
                        console.error('Error refreshing risks:', error);
                    }
                };
                refreshRisks();
            } else {
                api.error({
                    message: 'Risk Deletion Failed',
                    description: error || 'Failed to delete risk. Maybe you don\'t have the permissions to delete other user\'s records',
                    duration: 4,
                });
            }
        } catch (error) {
            console.error('Error deleting risk:', error);
            api.error({
                message: 'Risk Deletion Failed',
                description: 'An unexpected error occurred',
                duration: 4,
            });
        }
    };

    // Handle PDF export
    const handleExportToPdf = async () => {
        try {
            await exportRisksToPdf(filteredRisks, riskSeverities, 'risks-report');
            api.success({
                message: 'Export Success',
                description: `${filteredRisks.length} risk(s) have been exported to PDF successfully.`,
                duration: 4,
            });
        } catch (error) {
            console.error('PDF export error:', error);
            api.error({
                message: 'Export Failed',
                description: 'Failed to export risks to PDF. Please try again.',
                duration: 4,
            });
        }
    };

    // Handle table change to track filtered data
    const handleTableChange = (pagination: any, filters: any, sorter: any, extra: any) => {
        // Update filtered risks based on the current filtered data
        if (extra.currentDataSource) {
            setFilteredRisks(extra.currentDataSource);
        }
        // Call original handler for logging
        onRisksTableChange(pagination, filters, sorter, extra);
    };

    // Handle import complete - switch to registry tab and refresh
    const handleImportComplete = async () => {
        await fetchRisks();
        setActiveTab('registry');
    };

    // Convert data for Select components
    const assetCategoryOptions = assetCategories.map(type => ({
        label: type.name,
        value: type.id
    }));

    const statusOptions = riskStatuses.map(status => ({
        label: status.risk_status_name,
        value: status.id
    }));

    const severityOptions = riskSeverities.map(severity => ({
        label: severity.risk_severity_name,
        value: severity.id
    }));

    const getAssessmentStatusColor = (status?: string): string => {
        switch ((status || '').toLowerCase()) {
            case 'not assessed': return '#8c8c8c';
            case 'assessment in progress': return '#d48806';
            case 'assessed': return '#389e0d';
            case 'needs remediation': return '#cf1322';
            case 'remediated': return '#73d13d';
            case 'closed': return '#595ad4';
            default: return '#8c8c8c';
        }
    };

    const assessmentStatusOptions = [
        'Not Assessed',
        'Assessment in progress',
        'Assessed',
        'Needs Remediation',
        'Remediated',
        'Closed',
    ].map((status) => ({
        value: status,
        label: (
            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                    style={{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        display: 'inline-block',
                        backgroundColor: getAssessmentStatusColor(status),
                    }}
                />
                <span>{status}</span>
            </span>
        ),
    }));

    const getScopeLabel = (scopeName: string) => (
        scopeName === 'Product' || scopeName === 'Asset' ? 'Asset / Product' : scopeName
    );

    const buildScopeTypeOptions = (types: Array<{id: string; scope_name: string}>) => {
        const hasProduct = types.some(scopeType => scopeType.scope_name === 'Product');
        return types
            .filter(scopeType => !(scopeType.scope_name === 'Asset' && hasProduct))
            .map(scopeType => ({
                value: scopeType.scope_name,
                label: getScopeLabel(scopeType.scope_name)
            }));
    };

    const formatAssetLabel = (asset: { name: string; version: string | null; asset_type_name: string | null }) => {
        const versionLabel = asset.version ? ` v${asset.version}` : '';
        const typeLabel = asset.asset_type_name ? ` (${asset.asset_type_name})` : '';
        return `${asset.name}${versionLabel}${typeLabel}`;
    };

    // Scope dropdown options - show all scope types for risks (no framework restrictions)
    const scope_type_options = buildScopeTypeOptions(scopeTypes);

    const scope_entity_options = selectedScopeType === 'Product' || selectedScopeType === 'Asset'
        ? assets.map(asset => ({
            value: asset.id,
            label: formatAssetLabel(asset)
        }))
        : selectedScopeType === 'Organization'
        ? organisations.map(org => ({
            value: org.id,
            label: org.name
        }))
        : [];

    // Dashboard statistics
    const dashboardStats = useMemo(() => {
        const totalRisks = risks.length;

        // Count by severity
        const severityCounts: Record<string, number> = {};
        const statusCounts: Record<string, number> = {};

        risks.forEach(risk => {
            // Count by severity
            const severityName = risk.risk_severity || 'Unknown';
            severityCounts[severityName] = (severityCounts[severityName] || 0) + 1;

            // Count by status
            const statusName = risk.risk_status || 'Unknown';
            statusCounts[statusName] = (statusCounts[statusName] || 0) + 1;
        });

        // Get counts for specific severity levels
        const criticalCount = severityCounts['Critical'] || 0;
        const highCount = severityCounts['High'] || 0;
        const mediumCount = severityCounts['Medium'] || 0;
        const lowCount = severityCounts['Low'] || 0;

        return {
            totalRisks,
            criticalCount,
            highCount,
            mediumCount,
            lowCount,
            severityCounts,
            statusCounts
        };
    }, [risks]);

    // Severity color mapping
    const getSeverityColor = (severity: string): string => {
        switch (severity?.toLowerCase()) {
            case 'critical': return '#ff4d4f';
            case 'high': return '#fa8c16';
            case 'medium': return '#faad14';
            case 'low': return '#52c41a';
            default: return '#8c8c8c';
        }
    };

    // Status color mapping
    const getStatusColor = (status: string): string => {
        switch (status?.toLowerCase()) {
            case 'remediated': return '#52c41a';
            case 'accept': return '#1890ff';
            case 'transfer': return '#722ed1';
            case 'share': return '#13c2c2';
            case 'avoid': return '#eb2f96';
            case 'reduce': return '#fa8c16';
            default: return '#8c8c8c';
        }
    };

    // Status icon mapping
    const getStatusIcon = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'remediated': return <CheckCircleOutlined />;
            case 'accept': return <SafetyCertificateOutlined />;
            case 'transfer': return <ThunderboltOutlined />;
            case 'share': return <InfoCircleOutlined />;
            case 'avoid': return <ExclamationCircleOutlined />;
            case 'reduce': return <ClockCircleOutlined />;
            default: return <WarningOutlined />;
        }
    };

    // Filter risks by search text
    const searchFilteredRisks = risks.filter(risk =>
        risk.risk_category_name?.toLowerCase().includes(riskSearchText.toLowerCase()) ||
        risk.risk_category_description?.toLowerCase().includes(riskSearchText.toLowerCase()) ||
        risk.asset_category_name?.toLowerCase().includes(riskSearchText.toLowerCase()) ||
        risk.risk_status?.toLowerCase().includes(riskSearchText.toLowerCase()) ||
        risk.risk_severity?.toLowerCase().includes(riskSearchText.toLowerCase()) ||
        risk.assessment_status?.toLowerCase().includes(riskSearchText.toLowerCase())
    );

    // Selected risk object for intelligence panel
    const selectedRiskObj = useMemo(() => {
        return risks.find(r => r.id === selectedConnectionRisk);
    }, [risks, selectedConnectionRisk]);

    // Severity stats from linked findings
    const findingStats = useMemo(() => {
        const stats = { total: 0, high: 0, medium: 0, low: 0, info: 0 };
        linkedFindings.forEach(f => {
            stats.total++;
            const sev = (f.normalized_severity || '').toLowerCase();
            if (sev === 'high') stats.high++;
            else if (sev === 'medium') stats.medium++;
            else if (sev === 'low') stats.low++;
            else stats.info++;
        });
        return stats;
    }, [linkedFindings]);

    // Control implementation coverage
    const controlStats = useMemo(() => {
        const total = linkedControls.length;
        const implemented = linkedControls.filter(c => c.control_status_name === 'Implemented').length;
        const partial = linkedControls.filter(c => c.control_status_name === 'Partially Implemented').length;
        const notImpl = total - implemented - partial;
        const coverage = total > 0 ? Math.round((implemented / total) * 100) : 0;
        return { total, implemented, partial, notImpl, coverage };
    }, [linkedControls]);

    // Scanner type color mapping
    const getScannerColor = (type: string): string => {
        const colors: Record<string, string> = { zap: 'orange', nmap: 'blue', semgrep: 'purple', osv: 'green' };
        return colors[type] || 'default';
    };

    // Finding severity color mapping
    const getFindingSeverityColor = (sev: string): string => {
        const colors: Record<string, string> = { high: 'red', medium: 'orange', low: 'green', info: 'blue' };
        return colors[sev] || 'default';
    };

    // Sort findings by severity (high first)
    const sortedLinkedFindings = useMemo(() => {
        const severityOrder: Record<string, number> = { high: 0, medium: 1, low: 2, info: 3 };
        return [...linkedFindings].sort((a, b) => {
            const aOrder = severityOrder[(a.normalized_severity || '').toLowerCase()] ?? 4;
            const bOrder = severityOrder[(b.normalized_severity || '').toLowerCase()] ?? 4;
            return aOrder - bOrder;
        });
    }, [linkedFindings]);

    // Risk Card component
    const RiskCard = ({ risk }: { risk: any }) => {
        const handleCardClick = () => {
            setSelectedRisk(risk.id);
            setRiskCode(risk.risk_code || '');
            setAssetCategoryId(risk.asset_category_id);
            setRiskCategoryName(risk.risk_category_name);
            setRiskDescription(risk.risk_category_description || '');
            setPotentialImpact(risk.risk_potential_impact || '');
            setControlsText(risk.risk_control || '');
            setStatusId(risk.risk_status_id);
            setLikelihoodId(risk.likelihood);
            setSeverityId(risk.risk_severity_id);
            setResidualRiskId(risk.residual_risk);
            setAssessmentStatus(risk.assessment_status || 'Not Assessed');
            setSelectedScopeType(risk.scope_name || '');
            setSelectedScopeEntityId(risk.scope_entity_id || '');
            setShowForm(true);
        };

        return (
            <Card
                hoverable
                style={{ height: '100%' }}
                bodyStyle={{ padding: '16px' }}
                onClick={handleCardClick}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                    <div style={{ flex: 1 }}>
                        <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 500, marginBottom: '4px' }}>
                            {risk.risk_category_name}
                        </h4>
                        <span style={{ color: '#8c8c8c', fontSize: '13px' }}>
                            {risk.asset_category_name}
                        </span>
                    </div>
                    <Tag color={getSeverityColor(risk.risk_severity)} style={{ marginLeft: '8px' }}>
                        {risk.risk_severity}
                    </Tag>
                </div>

                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
                    <Tag color={getStatusColor(risk.risk_status)} icon={getStatusIcon(risk.risk_status)}>
                        {risk.risk_status}
                    </Tag>
                    {risk.assessment_status && (
                        <Tag color={getAssessmentStatusColor(risk.assessment_status)}>
                            Assessment: {risk.assessment_status}
                        </Tag>
                    )}
                    {risk.likelihood_name && (
                        <Tag color="default">Likelihood: {risk.likelihood_name}</Tag>
                    )}
                    {risk.residual_risk_name && (
                        <Tag color="orange">Residual: {risk.residual_risk_name}</Tag>
                    )}
                </div>

                {risk.risk_category_description && (
                    <p style={{
                        margin: 0,
                        marginBottom: '8px',
                        color: '#595959',
                        fontSize: '13px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                    }}>
                        {risk.risk_category_description}
                    </p>
                )}

                {risk.scope_display_name && (
                    <div style={{ marginTop: '8px' }}>
                        <Tag color="blue">{risk.scope_name}: {risk.scope_display_name}</Tag>
                    </div>
                )}

                <div style={{ marginTop: '12px', fontSize: '12px', color: '#bfbfbf' }}>
                    Updated: {risk.updated_at ? new Date(risk.updated_at).toLocaleDateString() : '-'}
                </div>
            </Card>
        );
    };

    // Tab items
    const tabItems = [
        {
            key: 'dashboard',
            label: (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <DashboardOutlined />
                    Dashboard
                </span>
            ),
            children: (
                <div>
                    {/* Summary Statistics Cards */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', marginBottom: '24px' }}>
                        <StatCard
                            title="Total Risks"
                            value={dashboardStats.totalRisks}
                            icon={<AlertOutlined />}
                            iconColor="#0f386a"
                            iconBgColor="#EBF4FC"
                            onClick={() => setActiveTab('registry')}
                        />
                        <StatCard
                            title="Critical"
                            value={dashboardStats.criticalCount}
                            icon={<ExclamationCircleOutlined />}
                            iconColor="#dc2626"
                            iconBgColor="#fef2f2"
                            onClick={() => setActiveTab('registry')}
                        />
                        <StatCard
                            title="High"
                            value={dashboardStats.highCount}
                            icon={<WarningOutlined />}
                            iconColor="#f59e0b"
                            iconBgColor="#fffbeb"
                            onClick={() => setActiveTab('registry')}
                        />
                        <StatCard
                            title="Medium"
                            value={dashboardStats.mediumCount}
                            icon={<InfoCircleOutlined />}
                            iconColor="#eab308"
                            iconBgColor="#fefce8"
                            onClick={() => setActiveTab('registry')}
                        />
                        <StatCard
                            title="Low"
                            value={dashboardStats.lowCount}
                            icon={<CheckCircleOutlined />}
                            iconColor="#10b981"
                            iconBgColor="#f0fdfa"
                            onClick={() => setActiveTab('registry')}
                        />
                    </div>

                    {/* Quick Actions */}
                    <QuickActionsPanel title="Quick Actions">
                        <QuickActionButton
                            label="Add New Risk"
                            icon={<PlusOutlined />}
                            onClick={() => {
                                handleClear(false);
                                setShowForm(true);
                                setActiveTab('registry');
                            }}
                            variant="primary"
                        />
                        <QuickActionButton
                            label="View Risk List"
                            icon={<UnorderedListOutlined />}
                            onClick={() => setActiveTab('registry')}
                            variant="secondary"
                        />
                        <QuickActionButton
                            label="Import Templates"
                            icon={<DatabaseOutlined />}
                            onClick={() => setActiveTab('templates')}
                            variant="success"
                        />
                        <QuickActionButton
                            label={`Export PDF (${filteredRisks.length})`}
                            icon={<FilePdfOutlined />}
                            onClick={handleExportToPdf}
                            variant="warning"
                        />
                    </QuickActionsPanel>

                    {/* Risk Distribution Section */}
                    <Row gutter={[24, 24]} style={{ marginTop: '24px' }}>
                        {/* Severity Distribution */}
                        <Col xs={24} lg={12}>
                            <DashboardSection title="Severity Distribution">
                                {dashboardStats.totalRisks === 0 ? (
                                    <div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>
                                        No risks registered yet
                                    </div>
                                ) : (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                        {['Critical', 'High', 'Medium', 'Low'].map(severity => {
                                            const count = dashboardStats.severityCounts[severity] || 0;
                                            const percent = dashboardStats.totalRisks > 0
                                                ? Math.round((count / dashboardStats.totalRisks) * 100)
                                                : 0;
                                            return (
                                                <div key={severity}>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                        <span style={{ fontWeight: 500, color: getSeverityColor(severity) }}>
                                                            {severity}
                                                        </span>
                                                        <span style={{ color: '#8c8c8c' }}>
                                                            {count} risk{count !== 1 ? 's' : ''} ({percent}%)
                                                        </span>
                                                    </div>
                                                    <Progress
                                                        percent={percent}
                                                        strokeColor={getSeverityColor(severity)}
                                                        showInfo={false}
                                                        size="small"
                                                    />
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </DashboardSection>
                        </Col>

                        {/* Status Distribution */}
                        <Col xs={24} lg={12}>
                            <DashboardSection title="Status Distribution">
                                {dashboardStats.totalRisks === 0 ? (
                                    <div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>
                                        No risks registered yet
                                    </div>
                                ) : (
                                    <Row gutter={[12, 12]}>
                                        {Object.entries(dashboardStats.statusCounts).map(([status, count]) => {
                                            const percent = dashboardStats.totalRisks > 0
                                                ? Math.round((count / dashboardStats.totalRisks) * 100)
                                                : 0;
                                            return (
                                                <Col xs={12} sm={8} key={status}>
                                                    <Card
                                                        size="small"
                                                        style={{
                                                            borderRadius: '8px',
                                                            borderLeft: `4px solid ${getStatusColor(status)}`,
                                                            background: '#fafafa'
                                                        }}
                                                    >
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                                            <span style={{ color: getStatusColor(status) }}>
                                                                {getStatusIcon(status)}
                                                            </span>
                                                            <span style={{ fontWeight: 500, fontSize: '13px' }}>{status}</span>
                                                        </div>
                                                        <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#262626' }}>
                                                            {count}
                                                        </div>
                                                        <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                                                            {percent}% of total
                                                        </div>
                                                    </Card>
                                                </Col>
                                            );
                                        })}
                                    </Row>
                                )}
                            </DashboardSection>
                        </Col>
                    </Row>
                </div>
            )
        },
        {
            key: 'registry',
            label: (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <UnorderedListOutlined />
                    Risk Registry
                    <Tag color="blue">{risks.length}</Tag>
                </span>
            ),
            children: (
                <div>
                    {/* Risk Data Table Section */}
                    <div className="page-section">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <Input
                                    placeholder="Search risks..."
                                    prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                    value={riskSearchText}
                                    onChange={(e) => setRiskSearchText(e.target.value)}
                                    style={{ width: '250px' }}
                                />
                                <div style={{ display: 'flex', border: '1px solid #d9d9d9', borderRadius: '6px', overflow: 'hidden' }}>
                                    <button
                                        onClick={() => setRiskViewMode('grid')}
                                        style={{
                                            border: 'none',
                                            padding: '6px 12px',
                                            cursor: 'pointer',
                                            backgroundColor: riskViewMode === 'grid' ? '#1890ff' : 'white',
                                            color: riskViewMode === 'grid' ? 'white' : '#595959',
                                        }}
                                    >
                                        <AppstoreOutlined />
                                    </button>
                                    <button
                                        onClick={() => setRiskViewMode('list')}
                                        style={{
                                            border: 'none',
                                            borderLeft: '1px solid #d9d9d9',
                                            padding: '6px 12px',
                                            cursor: 'pointer',
                                            backgroundColor: riskViewMode === 'list' ? '#1890ff' : 'white',
                                            color: riskViewMode === 'list' ? 'white' : '#595959',
                                        }}
                                    >
                                        <UnorderedListOutlined />
                                    </button>
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <button
                                    className="add-button"
                                    data-tour-id="qs-risk-add-button"
                                    onClick={() => {
                                        handleClear(false);
                                        setShowForm(true);
                                    }}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    <PlusOutlined /> Add New Risk
                                </button>
                                <button
                                    className="export-button"
                                    onClick={handleExportToPdf}
                                    disabled={filteredRisks.length === 0}
                                >
                                    Export to PDF ({filteredRisks.length})
                                </button>
                            </div>
                        </div>

                        {searchFilteredRisks.length === 0 ? (
                            <Empty description="No risks found" />
                        ) : riskViewMode === 'grid' ? (
                            <Row gutter={[16, 16]}>
                                {searchFilteredRisks.map(risk => (
                                    <Col key={risk.id} xs={24} sm={12} md={8} lg={6}>
                                        <RiskCard risk={risk} />
                                    </Col>
                                ))}
                            </Row>
                        ) : (
                            <div style={{ overflowX: 'auto' }}>
                                <Table
                                    columns={RisksGridColumns({
                                        risks,
                                        riskStatuses,
                                        riskSeverities
                                    })}
                                    dataSource={searchFilteredRisks}
                                    onChange={handleTableChange}
                                    showSorterTooltip={{ target: 'sorter-icon' }}
                                    onRow={(record) => {
                                        return {
                                            onClick: () => {
                                                console.log(record);
                                                setSelectedRisk(record.id);
                                                setRiskCode(record.risk_code || '');
                                                setAssetCategoryId(record.asset_category_id);
                                                setRiskCategoryName(record.risk_category_name);
                                                setRiskDescription(record.risk_category_description || '');
                                                setPotentialImpact(record.risk_potential_impact || '');
                                                setControlsText(record.risk_control || '');
                                                setStatusId(record.risk_status_id);
                                                setLikelihoodId(record.likelihood);
                                                setSeverityId(record.risk_severity_id);
                                                setResidualRiskId(record.residual_risk);
                                                setAssessmentStatus(record.assessment_status || 'Not Assessed');
                                                setSelectedScopeType(record.scope_name || '');
                                                setSelectedScopeEntityId(record.scope_entity_id || '');
                                                setShowForm(true);
                                            },
                                            style: {
                                                cursor: 'pointer',
                                                backgroundColor: selectedRisk === record.id ? '#e6f7ff' : undefined
                                            }
                                        };
                                    }}
                                    rowKey="id"
                                    pagination={{
                                        showSizeChanger: true,
                                        showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} risks`,
                                    }}
                                    scroll={{ x: 900 }}
                                />
                            </div>
                        )}
                    </div>
                </div>
            )
        },
        {
            key: 'templates',
            label: (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <DatabaseOutlined />
                    Risk Templates Library
                    <Tag color="purple">110</Tag>
                </span>
            ),
            children: (
                <div>
                    <RiskTemplatesSection
                        assetCategories={assetCategories}
                        riskSeverities={riskSeverities}
                        riskStatuses={riskStatuses}
                        onImportComplete={handleImportComplete}
                        isEmbedded={true}
                    />
                </div>
            )
        },
        {
            key: 'connections',
            label: (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <LinkOutlined />
                    Connections
                </span>
            ),
            children: (
                <div className="page-section">
                    {/* Risk Selector */}
                    <div style={{ marginBottom: 24 }}>
                        <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                            Select Risk to Manage Connections
                        </label>
                        <Select
                            showSearch
                            placeholder="Select a risk..."
                            options={risks.map(risk => ({
                                label: `${risk.risk_code ? `${risk.risk_code}: ` : ''}${risk.risk_category_name}${risk.asset_category_name ? ` (${risk.asset_category_name})` : ''}`,
                                value: risk.id,
                            }))}
                            value={selectedConnectionRisk}
                            onChange={(value) => setSelectedConnectionRisk(value)}
                            filterOption={(input, option) =>
                                (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                            }
                            style={{ width: '100%', maxWidth: 500 }}
                            allowClear
                        />
                    </div>

                    {selectedConnectionRisk && selectedRiskObj ? (
                        <>
                            {/* Risk Context Banner */}
                            <div style={{
                                background: 'linear-gradient(135deg, #1a365d 0%, #0f386a 100%)',
                                borderRadius: '10px',
                                padding: '16px 24px',
                                marginBottom: 24,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'space-between',
                                flexWrap: 'wrap',
                                gap: '12px',
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <SafetyCertificateOutlined style={{ fontSize: 22, color: '#fff' }} />
                                    <div>
                                        <div style={{ color: '#fff', fontWeight: 600, fontSize: '15px' }}>
                                            {selectedRiskObj.risk_code && <span>{selectedRiskObj.risk_code} — </span>}
                                            {selectedRiskObj.risk_category_name}
                                        </div>
                                        {selectedRiskObj.asset_category_name && (
                                            <Tag color="rgba(255,255,255,0.2)" style={{ color: '#fff', border: '1px solid rgba(255,255,255,0.3)', marginTop: 4 }}>
                                                {selectedRiskObj.asset_category_name}
                                            </Tag>
                                        )}
                                    </div>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                    {selectedRiskObj.risk_severity && (
                                        <Tag color={getSeverityColor(selectedRiskObj.risk_severity)} style={{ fontWeight: 600 }}>
                                            {selectedRiskObj.risk_severity}
                                        </Tag>
                                    )}
                                    {selectedRiskObj.risk_status && (
                                        <Tag color={getStatusColor(selectedRiskObj.risk_status)} icon={getStatusIcon(selectedRiskObj.risk_status)}>
                                            {selectedRiskObj.risk_status}
                                        </Tag>
                                    )}
                                    {selectedRiskObj.likelihood_name && (
                                        <Tag color="default" style={{ background: 'rgba(255,255,255,0.15)', color: '#fff', border: '1px solid rgba(255,255,255,0.3)' }}>
                                            Likelihood: {selectedRiskObj.likelihood_name}
                                        </Tag>
                                    )}
                                </div>
                                {selectedRiskObj.risk_potential_impact && (
                                    <div style={{ width: '100%' }}>
                                        <Tooltip title={selectedRiskObj.risk_potential_impact}>
                                            <div style={{
                                                color: 'rgba(255,255,255,0.85)',
                                                fontSize: '13px',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                whiteSpace: 'nowrap',
                                                maxWidth: '100%',
                                            }}>
                                                <strong>Impact:</strong> {selectedRiskObj.risk_potential_impact}
                                            </div>
                                        </Tooltip>
                                    </div>
                                )}
                            </div>

                            <Row gutter={[24, 24]} align="top">
                                {/* Left Column: Stacked Connection Boards */}
                                <Col xs={24} lg={12}>
                                    {/* Assets Board */}
                                    <div style={{ marginBottom: 16 }}>
                                        <ConnectionBoard
                                            title="Assets Exposed to Risk"
                                            sourceLabel="Asset"
                                            targetLabel="Risk"
                                            relationshipLabel="exposed to"
                                            itemLabel="Asset"
                                            availableItems={assets.map(asset => ({
                                                id: asset.id,
                                                name: asset.name,
                                                asset_type_name: asset.asset_type_name,
                                                version: asset.version,
                                            }))}
                                            linkedItems={linkedAssets.map(asset => ({
                                                id: asset.id,
                                                name: asset.name,
                                                asset_type_name: asset.asset_type_name,
                                                version: asset.version,
                                            }))}
                                            loading={false}
                                            getItemDisplayName={(item) => {
                                                const asset = item as { name: string; asset_type_name?: string | null };
                                                return asset.name;
                                            }}
                                            getItemDescription={(item) => {
                                                const asset = item as { asset_type_name?: string | null };
                                                return asset.asset_type_name || null;
                                            }}
                                            getItemTags={(item) => {
                                                const asset = item as { version?: string | null };
                                                const tags: { label: string; color: string }[] = [];
                                                if (asset.version) {
                                                    tags.push({ label: `v${asset.version}`, color: 'blue' });
                                                }
                                                return tags;
                                            }}
                                            onLink={async (assetIds) => {
                                                const { linkAssetToRisk } = useAssetStore.getState();
                                                for (const assetId of assetIds) {
                                                    const result = await linkAssetToRisk(assetId, selectedConnectionRisk);
                                                    if (!result.success) {
                                                        api.error({
                                                            message: 'Link Failed',
                                                            description: result.error || 'Failed to link asset to risk',
                                                            duration: 4,
                                                        });
                                                        return;
                                                    }
                                                }
                                                api.success({
                                                    message: 'Assets Linked',
                                                    description: `Successfully linked ${assetIds.length} asset(s) to the risk`,
                                                    duration: 4,
                                                });
                                                fetchLinkedAssets(selectedConnectionRisk);
                                            }}
                                            onUnlink={async (assetIds) => {
                                                const { unlinkAssetFromRisk } = useAssetStore.getState();
                                                for (const assetId of assetIds) {
                                                    const result = await unlinkAssetFromRisk(assetId, selectedConnectionRisk);
                                                    if (!result.success) {
                                                        api.error({
                                                            message: 'Unlink Failed',
                                                            description: result.error || 'Failed to unlink asset from risk',
                                                            duration: 4,
                                                        });
                                                        return;
                                                    }
                                                }
                                                api.success({
                                                    message: 'Assets Unlinked',
                                                    description: `Successfully unlinked ${assetIds.length} asset(s) from the risk`,
                                                    duration: 4,
                                                });
                                                fetchLinkedAssets(selectedConnectionRisk);
                                            }}
                                            height={250}
                                        />
                                    </div>

                                    {/* Framework Selector for Controls */}
                                    <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
                                        <label style={{ fontWeight: 500, whiteSpace: 'nowrap', fontSize: 13 }}>Framework:</label>
                                        <Select
                                            showSearch
                                            placeholder="Select framework..."
                                            options={filteredFrameworks.map(fw => ({ label: fw.name, value: fw.id }))}
                                            value={connectionFrameworkId}
                                            onChange={(value) => setConnectionFrameworkId(value)}
                                            filterOption={(input, option) =>
                                                (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                            }
                                            style={{ width: '100%', maxWidth: 300 }}
                                            size="small"
                                            allowClear
                                        />
                                    </div>

                                    {/* Controls Board */}
                                    {connectionFrameworkId ? (
                                    <ConnectionBoard
                                        title="Controls Mitigating Risk"
                                        sourceLabel="Control"
                                        targetLabel="Risk"
                                        relationshipLabel="mitigates"
                                        itemLabel="Control"
                                        availableItems={controls.map(control => ({
                                            id: control.id,
                                            code: control.code,
                                            name: control.name,
                                            category: control.category,
                                            control_status_name: control.control_status_name,
                                        }))}
                                        linkedItems={linkedControls.map(control => ({
                                            id: control.id,
                                            code: control.code,
                                            name: control.name,
                                            category: control.category,
                                            control_status_name: control.control_status_name,
                                        }))}
                                        loading={false}
                                        getItemDisplayName={(item) => {
                                            const control = item as { code: string; name: string };
                                            return `${control.code}: ${control.name}`;
                                        }}
                                        getItemDescription={(item) => {
                                            const control = item as { category?: string | null };
                                            return control.category || null;
                                        }}
                                        getItemTags={(item) => {
                                            const control = item as { control_status_name?: string | null };
                                            const tags: { label: string; color: string }[] = [];
                                            if (control.control_status_name) {
                                                const statusColors: Record<string, string> = {
                                                    'Implemented': 'green',
                                                    'Partially Implemented': 'orange',
                                                    'Not Implemented': 'red',
                                                    'N/A': 'default',
                                                };
                                                tags.push({
                                                    label: control.control_status_name,
                                                    color: statusColors[control.control_status_name] || 'default',
                                                });
                                            }
                                            return tags;
                                        }}
                                        onLink={async (controlIds) => {
                                            if (!connectionFrameworkId) return;
                                            for (const controlId of controlIds) {
                                                const success = await linkControlToRisk(controlId, selectedConnectionRisk, connectionFrameworkId);
                                                if (!success) {
                                                    api.error({
                                                        message: 'Link Failed',
                                                        description: 'Failed to link control to risk',
                                                        duration: 4,
                                                    });
                                                    return;
                                                }
                                            }
                                            api.success({
                                                message: 'Controls Linked',
                                                description: `Successfully linked ${controlIds.length} control(s) to the risk`,
                                                duration: 4,
                                            });
                                            fetchLinkedControls(selectedConnectionRisk, connectionFrameworkId);
                                        }}
                                        onUnlink={async (controlIds) => {
                                            if (!connectionFrameworkId) return;
                                            for (const controlId of controlIds) {
                                                const success = await unlinkControlFromRisk(controlId, selectedConnectionRisk, connectionFrameworkId);
                                                if (!success) {
                                                    api.error({
                                                        message: 'Unlink Failed',
                                                        description: 'Failed to unlink control from risk',
                                                        duration: 4,
                                                    });
                                                    return;
                                                }
                                            }
                                            api.success({
                                                message: 'Controls Unlinked',
                                                description: `Successfully unlinked ${controlIds.length} control(s) from the risk`,
                                                duration: 4,
                                            });
                                            fetchLinkedControls(selectedConnectionRisk, connectionFrameworkId);
                                        }}
                                        height={250}
                                    />
                                    ) : (
                                        <Empty description="Select a framework to manage control connections" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                                    )}
                                </Col>

                                {/* Right Column: Risk Intelligence Panel */}
                                <Col xs={24} lg={12}>
                                    <Card
                                        style={{ borderRadius: '10px', height: '100%' }}
                                        bodyStyle={{ padding: 0 }}
                                    >
                                        <Tabs
                                            defaultActiveKey="findings"
                                            style={{ padding: '0 16px' }}
                                            items={[
                                                {
                                                    key: 'findings',
                                                    label: (
                                                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                            <EyeOutlined />
                                                            Findings & Evidence
                                                            {findingStats.total > 0 && <Tag color="blue" style={{ marginLeft: 4 }}>{findingStats.total}</Tag>}
                                                        </span>
                                                    ),
                                                    children: (
                                                        <div style={{ paddingBottom: 16 }}>
                                                            {/* Stats Row */}
                                                            <div style={{ display: 'flex', gap: '8px', marginBottom: 16, flexWrap: 'wrap' }}>
                                                                <div style={{ flex: 1, minWidth: 70, textAlign: 'center', background: '#f0f5ff', borderRadius: 8, padding: '8px 4px' }}>
                                                                    <div style={{ fontSize: 20, fontWeight: 700, color: '#1890ff' }}>{findingStats.total}</div>
                                                                    <div style={{ fontSize: 11, color: '#8c8c8c' }}>Total</div>
                                                                </div>
                                                                <div style={{ flex: 1, minWidth: 70, textAlign: 'center', background: '#fff1f0', borderRadius: 8, padding: '8px 4px' }}>
                                                                    <div style={{ fontSize: 20, fontWeight: 700, color: '#ff4d4f' }}>{findingStats.high}</div>
                                                                    <div style={{ fontSize: 11, color: '#8c8c8c' }}>High</div>
                                                                </div>
                                                                <div style={{ flex: 1, minWidth: 70, textAlign: 'center', background: '#fff7e6', borderRadius: 8, padding: '8px 4px' }}>
                                                                    <div style={{ fontSize: 20, fontWeight: 700, color: '#fa8c16' }}>{findingStats.medium}</div>
                                                                    <div style={{ fontSize: 11, color: '#8c8c8c' }}>Medium</div>
                                                                </div>
                                                                <div style={{ flex: 1, minWidth: 70, textAlign: 'center', background: '#f6ffed', borderRadius: 8, padding: '8px 4px' }}>
                                                                    <div style={{ fontSize: 20, fontWeight: 700, color: '#52c41a' }}>{findingStats.low + findingStats.info}</div>
                                                                    <div style={{ fontSize: 11, color: '#8c8c8c' }}>Low/Info</div>
                                                                </div>
                                                            </div>

                                                            {/* Findings List */}
                                                            {sortedLinkedFindings.length > 0 ? (
                                                                <Collapse
                                                                    size="small"
                                                                    accordion
                                                                    items={sortedLinkedFindings.map((finding: any) => ({
                                                                        key: finding.id,
                                                                        label: (
                                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                                                                <Tag color={getScannerColor(finding.scanner_type)} style={{ fontSize: 11 }}>
                                                                                    {{ zap: 'Web App', nmap: 'Network', semgrep: 'Code', osv: 'Dependency', syft: 'SBOM' }[finding.scanner_type] || 'Scanner'}
                                                                                </Tag>
                                                                                <span style={{ fontWeight: 500, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                                    {finding.title}
                                                                                </span>
                                                                                <Tag color={getFindingSeverityColor((finding.normalized_severity || '').toLowerCase())}>
                                                                                    {finding.normalized_severity || 'N/A'}
                                                                                </Tag>
                                                                                <Tag color={finding.is_auto_mapped ? 'geekblue' : 'cyan'} style={{ fontSize: 11 }}>
                                                                                    {finding.is_auto_mapped ? 'Auto' : 'Manual'}
                                                                                </Tag>
                                                                            </div>
                                                                        ),
                                                                        children: (
                                                                            <div>
                                                                                {finding.description && (
                                                                                    <div style={{ marginBottom: 8 }}>
                                                                                        <strong style={{ fontSize: 12, color: '#8c8c8c' }}>Description</strong>
                                                                                        <p style={{ margin: '4px 0 0', fontSize: 13 }}>{finding.description}</p>
                                                                                    </div>
                                                                                )}
                                                                                {finding.solution && (
                                                                                    <div style={{ marginBottom: 8 }}>
                                                                                        <strong style={{ fontSize: 12, color: '#8c8c8c' }}>Solution</strong>
                                                                                        <p style={{ margin: '4px 0 0', fontSize: 13 }}>{finding.solution}</p>
                                                                                    </div>
                                                                                )}
                                                                                {finding.scan_target && (
                                                                                    <div style={{ marginBottom: 8 }}>
                                                                                        <strong style={{ fontSize: 12, color: '#8c8c8c' }}>Target</strong>
                                                                                        <p style={{ margin: '4px 0 0', fontSize: 13, wordBreak: 'break-all' }}>{finding.scan_target}</p>
                                                                                    </div>
                                                                                )}
                                                                                <div style={{ textAlign: 'right', marginTop: 8 }}>
                                                                                    <a
                                                                                        onClick={async () => {
                                                                                            if (selectedConnectionRisk) {
                                                                                                const success = await unlinkFinding(selectedConnectionRisk, finding.id);
                                                                                                if (success) {
                                                                                                    fetchLinkedFindings(selectedConnectionRisk);
                                                                                                    fetchRisks();
                                                                                                    api.success({ message: 'Finding unlinked', duration: 3 });
                                                                                                } else {
                                                                                                    api.error({ message: 'Failed to unlink finding', duration: 3 });
                                                                                                }
                                                                                            }
                                                                                        }}
                                                                                        style={{ color: '#ff4d4f', fontSize: 12 }}
                                                                                    >
                                                                                        Unlink Finding
                                                                                    </a>
                                                                                </div>
                                                                            </div>
                                                                        ),
                                                                    }))}
                                                                />
                                                            ) : (
                                                                <Empty
                                                                    description="No vulnerabilities detected. Run security scans to auto-detect."
                                                                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                                                                    style={{ margin: '24px 0' }}
                                                                />
                                                            )}
                                                        </div>
                                                    ),
                                                },
                                                {
                                                    key: 'controls',
                                                    label: (
                                                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                            <SafetyOutlined />
                                                            Control Posture
                                                            {controlStats.total > 0 && <Tag color="green" style={{ marginLeft: 4 }}>{controlStats.total}</Tag>}
                                                        </span>
                                                    ),
                                                    children: (
                                                        <div style={{ paddingBottom: 16 }}>
                                                            {/* Recommended Mitigation */}
                                                            <div style={{
                                                                background: '#e6f7ff',
                                                                border: '1px solid #91d5ff',
                                                                borderRadius: 8,
                                                                padding: '12px 16px',
                                                                marginBottom: 16,
                                                                display: 'flex',
                                                                gap: '10px',
                                                                alignItems: 'flex-start',
                                                            }}>
                                                                <BulbOutlined style={{ fontSize: 18, color: '#1890ff', marginTop: 2 }} />
                                                                <div>
                                                                    <div style={{ fontWeight: 600, fontSize: 13, color: '#0050b3', marginBottom: 4 }}>Recommended Mitigation</div>
                                                                    <div style={{ fontSize: 13, color: '#262626' }}>
                                                                        {selectedRiskObj.risk_control || 'No mitigation guidance defined for this risk.'}
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            {/* Implementation Coverage */}
                                                            {controlStats.total > 0 ? (
                                                                <>
                                                                    <div style={{ marginBottom: 16 }}>
                                                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                                            <span style={{ fontWeight: 500, fontSize: 13 }}>Implementation Coverage</span>
                                                                            <span style={{ fontSize: 13, color: '#8c8c8c' }}>{controlStats.coverage}%</span>
                                                                        </div>
                                                                        <Progress
                                                                            percent={controlStats.coverage}
                                                                            strokeColor={controlStats.coverage === 100 ? '#52c41a' : controlStats.coverage >= 50 ? '#faad14' : '#ff4d4f'}
                                                                            showInfo={false}
                                                                            size="small"
                                                                        />
                                                                        <div style={{ display: 'flex', gap: '12px', marginTop: 8, fontSize: 12, color: '#595959' }}>
                                                                            <span><span style={{ color: '#52c41a', fontWeight: 600 }}>{controlStats.implemented}</span> Implemented</span>
                                                                            <span><span style={{ color: '#fa8c16', fontWeight: 600 }}>{controlStats.partial}</span> Partial</span>
                                                                            <span><span style={{ color: '#ff4d4f', fontWeight: 600 }}>{controlStats.notImpl}</span> Not Impl.</span>
                                                                        </div>
                                                                    </div>

                                                                    {/* Controls List */}
                                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                                        {linkedControls.map((control: any) => {
                                                                            const statusColors: Record<string, string> = {
                                                                                'Implemented': 'green',
                                                                                'Partially Implemented': 'orange',
                                                                                'Not Implemented': 'red',
                                                                                'N/A': 'default',
                                                                            };
                                                                            return (
                                                                                <div key={control.id} style={{
                                                                                    display: 'flex',
                                                                                    alignItems: 'center',
                                                                                    justifyContent: 'space-between',
                                                                                    padding: '8px 12px',
                                                                                    background: '#fafafa',
                                                                                    borderRadius: 6,
                                                                                    border: '1px solid #f0f0f0',
                                                                                }}>
                                                                                    <div style={{ flex: 1, minWidth: 0 }}>
                                                                                        <div style={{ fontWeight: 500, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                                            {control.code}: {control.name}
                                                                                        </div>
                                                                                        {control.category && (
                                                                                            <div style={{ fontSize: 11, color: '#8c8c8c', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                                                {control.category}
                                                                                            </div>
                                                                                        )}
                                                                                    </div>
                                                                                    <Tag color={statusColors[control.control_status_name] || 'default'} style={{ marginLeft: 8, flexShrink: 0 }}>
                                                                                        {control.control_status_name || 'N/A'}
                                                                                    </Tag>
                                                                                </div>
                                                                            );
                                                                        })}
                                                                    </div>
                                                                </>
                                                            ) : (
                                                                <Empty
                                                                    description="No controls linked. Use the board on the left to link controls."
                                                                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                                                                    style={{ margin: '24px 0' }}
                                                                />
                                                            )}
                                                        </div>
                                                    ),
                                                },
                                                {
                                                    key: 'profile',
                                                    label: (
                                                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                            <AlertOutlined />
                                                            Risk Profile
                                                        </span>
                                                    ),
                                                    children: (
                                                        <div style={{ paddingBottom: 16 }}>
                                                            {/* Connection counts */}
                                                            <div style={{ display: 'flex', gap: '8px', marginBottom: 16, flexWrap: 'wrap' }}>
                                                                <Tag color="blue">{linkedAssets.length} Asset{linkedAssets.length !== 1 ? 's' : ''}</Tag>
                                                                <Tag color="green">{linkedControls.length} Control{linkedControls.length !== 1 ? 's' : ''}</Tag>
                                                                <Tag color="orange">{linkedFindings.length} Finding{linkedFindings.length !== 1 ? 's' : ''}</Tag>
                                                            </div>

                                                            {/* Description */}
                                                            {selectedRiskObj.risk_category_description && (
                                                                <div style={{ marginBottom: 16 }}>
                                                                    <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Description</div>
                                                                    <div style={{ fontSize: 13, color: '#262626', lineHeight: 1.6 }}>
                                                                        {selectedRiskObj.risk_category_description}
                                                                    </div>
                                                                </div>
                                                            )}

                                                            {/* Potential Impact */}
                                                            {selectedRiskObj.risk_potential_impact && (
                                                                <div style={{ marginBottom: 16 }}>
                                                                    <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Potential Impact</div>
                                                                    <div style={{ fontSize: 13, color: '#262626', lineHeight: 1.6 }}>
                                                                        {selectedRiskObj.risk_potential_impact}
                                                                    </div>
                                                                </div>
                                                            )}

                                                            {/* Assessment Status */}
                                                            <div style={{ marginBottom: 16 }}>
                                                                <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Assessment Status</div>
                                                                <Tag color={getAssessmentStatusColor(selectedRiskObj.assessment_status)}>
                                                                    {selectedRiskObj.assessment_status || 'Not Assessed'}
                                                                </Tag>
                                                            </div>

                                                            {/* Residual Risk */}
                                                            {selectedRiskObj.residual_risk_name && (
                                                                <div style={{ marginBottom: 16 }}>
                                                                    <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Residual Risk</div>
                                                                    <Tag color="orange">{selectedRiskObj.residual_risk_name}</Tag>
                                                                </div>
                                                            )}

                                                            {/* Scope */}
                                                            {selectedRiskObj.scope_display_name && (
                                                                <div style={{ marginBottom: 16 }}>
                                                                    <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Scope</div>
                                                                    <Tag color="blue">{selectedRiskObj.scope_name}: {selectedRiskObj.scope_display_name}</Tag>
                                                                </div>
                                                            )}
                                                        </div>
                                                    ),
                                                },
                                                {
                                                    key: 'recommendations',
                                                    label: (
                                                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                            <BulbOutlined />
                                                            Recommendations
                                                        </span>
                                                    ),
                                                    children: (
                                                        <div style={{ paddingBottom: 16 }}>
                                                            {/* Guidance Card */}
                                                            <div style={{
                                                                background: '#f0f7ff',
                                                                borderRadius: 8,
                                                                padding: 12,
                                                                marginBottom: 16,
                                                                display: 'flex',
                                                                gap: '10px',
                                                                alignItems: 'flex-start',
                                                            }}>
                                                                <BulbOutlined style={{ fontSize: 18, color: '#1890ff', marginTop: 2 }} />
                                                                <div>
                                                                    <div style={{ fontWeight: 600, fontSize: 13, color: '#0050b3', marginBottom: 4 }}>Recommended Mitigation</div>
                                                                    <div style={{ fontSize: 13, color: '#262626' }}>
                                                                        {selectedRiskObj.risk_control || 'No mitigation guidance defined for this risk.'}
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            {/* Control Template Sets — filtered by keyword relevance */}
                                                            {(() => {
                                                                const { relevant, other } = filterByRelevance(
                                                                    controlTemplates,
                                                                    [selectedRiskObj.risk_category_name, selectedRiskObj.risk_category_description, selectedRiskObj.risk_control, selectedRiskObj.risk_potential_impact, selectedRiskObj.asset_category_name],
                                                                    (t) => [t.name, t.description]
                                                                );
                                                                const renderTemplateCard = (template: typeof controlTemplates[0]) => (
                                                                    <div key={template.name} style={{
                                                                        border: '1px solid #f0f0f0',
                                                                        borderRadius: 8,
                                                                        padding: '12px 16px',
                                                                        display: 'flex',
                                                                        alignItems: 'center',
                                                                        justifyContent: 'space-between',
                                                                        gap: 12,
                                                                    }}>
                                                                        <div style={{ flex: 1, minWidth: 0 }}>
                                                                            <div style={{ fontWeight: 500, fontSize: 13 }}>{template.name}</div>
                                                                            {template.description && (
                                                                                <div style={{ fontSize: 11, color: '#8c8c8c', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                                    {template.description}
                                                                                </div>
                                                                            )}
                                                                        </div>
                                                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                                                                            <Tag color="blue">{template.control_count} controls</Tag>
                                                                            <Button
                                                                                type="primary"
                                                                                ghost
                                                                                size="small"
                                                                                loading={recommendationLoading[template.name]}
                                                                                onClick={() => handleImportAndLinkRecommendation(template.name)}
                                                                            >
                                                                                Import & Link
                                                                            </Button>
                                                                        </div>
                                                                    </div>
                                                                );

                                                                if (controlTemplates.length === 0) {
                                                                    return <Empty description="No control templates available" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ margin: '24px 0' }} />;
                                                                }

                                                                return (
                                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                                        {relevant.length > 0 ? (
                                                                            <>
                                                                                {relevant.map(renderTemplateCard)}
                                                                                {other.length > 0 && (
                                                                                    <Collapse size="small" style={{ marginTop: 8 }} items={[{
                                                                                        key: 'other',
                                                                                        label: <span style={{ fontSize: 12, color: '#8c8c8c' }}>Other control sets ({other.length})</span>,
                                                                                        children: <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>{other.map(renderTemplateCard)}</div>,
                                                                                    }]} />
                                                                                )}
                                                                            </>
                                                                        ) : (
                                                                            controlTemplates.map(renderTemplateCard)
                                                                        )}
                                                                    </div>
                                                                );
                                                            })()}
                                                        </div>
                                                    ),
                                                },
                                            ]}
                                        />
                                    </Card>
                                </Col>
                            </Row>
                        </>
                    ) : (
                        <Empty
                            description="Select a risk to manage its connections"
                            style={{ marginTop: 60 }}
                        />
                    )}
                </div>
            )
        }
    ];

    return (
        <div>
            {contextHolder}
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
                            <CompassOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Risk Management"
                                infoContent={RisksInfo}
                                className="page-title"
                            />
                        </div>
                    </div>

                    {/* Tabbed Content */}
                    <Tabs
                        activeKey={activeTab}
                        onChange={setActiveTab}
                        items={tabItems}
                        size="large"
                        style={{ marginTop: '-8px' }}
                    />

                    {/* Risk Registration Modal */}
                    <Modal
                        title={
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {selectedRisk ? (
                                    <EditOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                                ) : (
                                    <PlusOutlined style={{ fontSize: '20px', color: '#52c41a' }} />
                                )}
                                <span>{selectedRisk ? 'Edit Risk' : 'Add New Risk'}</span>
                                {selectedRisk && <Tag color="blue">Editing</Tag>}
                            </div>
                        }
                        open={showForm}
                        onCancel={() => handleClear(true)}
                        width={900}
                        footer={
                            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                {selectedRisk && (
                                    <button
                                        className="delete-button"
                                        onClick={handleDelete}
                                        style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f', color: 'white' }}
                                    >
                                        Delete Risk
                                    </button>
                                )}
                                {selectedRisk && (
                                    <button
                                        className="secondary-button"
                                        onClick={() => {
                                            handleClear(true);
                                            navigate(`/risk_assessment/${selectedRisk}`);
                                        }}
                                        style={{ backgroundColor: '#0f386a', borderColor: '#0f386a', color: 'white' }}
                                    >
                                        Assess
                                    </button>
                                )}
                                {selectedRisk && (
                                    <button
                                        className="secondary-button"
                                        onClick={() => handleClear(false)}
                                    >
                                        Create New Instead
                                    </button>
                                )}
                                <button
                                    className="secondary-button"
                                    onClick={() => handleClear(true)}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="add-button"
                                    onClick={handleSave}
                                    style={{
                                        backgroundColor: selectedRisk ? '#1890ff' : '#52c41a',
                                        borderColor: selectedRisk ? '#1890ff' : '#52c41a'
                                    }}
                                >
                                    {selectedRisk ? 'Update Risk' : 'Save Risk'}
                                </button>
                            </div>
                        }
                    >
                        <p style={{ color: '#8c8c8c', fontSize: '14px', marginBottom: '24px' }}>
                            {selectedRisk
                                ? 'Update the risk details below and click "Update Risk" to save changes.'
                                : 'Fill out the form below to register a new risk.'}
                        </p>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label required">Code</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="e.g., ORG-RSK-01"
                                    value={riskCode}
                                    onChange={(e) => setRiskCode(e.target.value)}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label required">Asset Category</label>
                                <Select
                                    showSearch
                                    placeholder="Select asset category"
                                    onChange={(value) => setAssetCategoryId(value)}
                                    options={assetCategoryOptions}
                                    filterOption={(input, option) => (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())}
                                    value={assetCategoryId}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label required">Status (Treatment)</label>
                                <Select
                                    showSearch
                                    placeholder="Select treatment"
                                    onChange={(value) => setStatusId(value)}
                                    options={statusOptions}
                                    filterOption={(input, option) => (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())}
                                    value={statusId}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label required">Likelihood</label>
                                <Select
                                    showSearch
                                    placeholder="Select likelihood"
                                    onChange={(value) => setLikelihoodId(value)}
                                    options={severityOptions}
                                    filterOption={(input, option) => (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())}
                                    value={likelihoodId}
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Scope Type</label>
                                <Select
                                    showSearch
                                    placeholder="Select scope type (optional)"
                                    onChange={(value) => {
                                        setSelectedScopeType(value);
                                        setSelectedScopeEntityId(''); // Clear entity when type changes
                                    }}
                                    options={scope_type_options}
                                    filterOption={(input, option) => (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())}
                                    value={selectedScopeType || undefined}
                                    style={{ width: '100%' }}
                                    allowClear
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">
                                    {selectedScopeType === 'Product' || selectedScopeType === 'Asset'
                                        ? 'Asset / Product'
                                        : selectedScopeType === 'Organization'
                                        ? 'Organization'
                                        : 'Scope Entity'}
                                </label>
                                <Select
                                    showSearch
                                    placeholder={
                                        !selectedScopeType
                                            ? 'Select scope type first'
                                            : scope_entity_options.length === 0
                                            ? `No ${getScopeLabel(selectedScopeType).toLowerCase()} available`
                                            : `Select ${getScopeLabel(selectedScopeType).toLowerCase()}`
                                    }
                                    onChange={(value) => setSelectedScopeEntityId(value)}
                                    options={scope_entity_options}
                                    filterOption={(input, option) => (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())}
                                    value={selectedScopeEntityId || undefined}
                                    style={{ width: '100%' }}
                                    disabled={
                                        !selectedScopeType ||
                                        (selectedScopeType !== 'Product' && selectedScopeType !== 'Asset' && selectedScopeType !== 'Organization') ||
                                        scope_entity_options.length === 0
                                    }
                                    allowClear
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label required">Assessment Status</label>
                                <Select
                                    showSearch
                                    placeholder="Select assessment status"
                                    onChange={(value) => setAssessmentStatus(value)}
                                    options={assessmentStatusOptions}
                                    value={assessmentStatus}
                                    style={{ width: '100%' }}
                                    filterOption={(input, option) =>
                                        (option?.value ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                    }
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label required">Severity</label>
                                <Select
                                    showSearch
                                    placeholder="Select severity"
                                    onChange={(value) => setSeverityId(value)}
                                    options={severityOptions}
                                    filterOption={(input, option) => (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())}
                                    value={severityId}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label required">Residual Risk</label>
                                <Select
                                    showSearch
                                    placeholder="Select residual risk"
                                    onChange={(value) => setResidualRiskId(value)}
                                    options={severityOptions}
                                    filterOption={(input, option) => (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())}
                                    value={residualRiskId}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label required">Risk Category</label>
                                <AutoComplete
                                    options={filteredRiskCategories}
                                    placeholder="Enter or select risk category"
                                    filterOption={filterOption}
                                    value={riskCategoryName}
                                    onChange={(value) => setRiskCategoryName(value)}
                                    onSelect={handleRiskCategorySelect}
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Description</label>
                                <AutoComplete
                                    placeholder="Enter risk description"
                                    value={riskDescription}
                                    onChange={(value) => setRiskDescription(value)}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Potential Impact</label>
                                <AutoComplete
                                    placeholder="Enter potential impact"
                                    value={potentialImpact}
                                    onChange={(value) => setPotentialImpact(value)}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Controls</label>
                                <AutoComplete
                                    placeholder="Enter controls"
                                    value={controlsText}
                                    onChange={(value) => setControlsText(value)}
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>
                    </Modal>
                </div>
            </div>
        </div>
    );
};

export default RiskRegistrationPage;
