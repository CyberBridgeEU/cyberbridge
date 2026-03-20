import { Select, Table, notification, Modal, Input, Tabs, Card, Tag, Dropdown, Row, Col, Empty, Tooltip, Radio, Checkbox, Progress, Collapse, Button } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { DatabaseOutlined, PlusOutlined, EditOutlined, DeleteOutlined, MoreOutlined, SearchOutlined, AppstoreOutlined, UnorderedListOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, MinusCircleOutlined, LinkOutlined, AlertOutlined, SafetyCertificateOutlined, BulbOutlined, ImportOutlined } from '@ant-design/icons';
import useAssetStore, { AssetType, Asset } from "../store/useAssetStore.ts";
import useRiskStore from "../store/useRiskStore.ts";
import useUserStore from "../store/useUserStore.ts";
import useSettingsStore from "../store/useSettingsStore.ts";
import useCRAModeStore from "../store/useCRAModeStore.ts";
import { useEffect, useState, useMemo } from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import ConnectionBoard from "../components/ConnectionBoard.tsx";
import { filterByRelevance } from "../utils/recommendationUtils.ts";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { renderIcon, availableIcons } from "../utils/iconUtils.tsx";

const { TextArea } = Input;

// Info content for the Assets page
const AssetsInfo = (
    <div>
        <p><strong>Assets</strong> represent the valuable resources within your organization that need protection.</p>
        <p>Use this page to:</p>
        <ul>
            <li>Create and manage individual assets</li>
            <li>Organize assets by type</li>
            <li>Track risks associated with each asset type</li>
            <li>Manage asset type categories</li>
        </ul>
    </div>
);

const AssetsPage = () => {
    // Menu highlighting
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Store access
    const {
        assets,
        assetTypes,
        assetStatuses,
        economicOperators,
        criticalities,
        linkedRisks,
        loading,
        fetchAssets,
        fetchAssetTypes,
        fetchAssetStatuses,
        fetchEconomicOperators,
        fetchCriticalities,
        fetchLinkedRisks,
        linkAssetToRisk,
        unlinkAssetFromRisk,
        createAsset,
        updateAsset,
        deleteAsset,
        createAssetType,
        updateAssetType,
        deleteAssetType,
        seedDefaultAssetTypes,
    } = useAssetStore();

    // Risk store for available risks
    const { risks, fetchRisks, riskTemplateCategories, fetchRiskTemplateCategories, fetchRiskTemplateRisks, riskTemplateRisks, importRiskTemplates, riskSeverities, riskStatuses, fetchRiskSeverities, fetchRiskStatuses, assetCategories, fetchAssetCategories } = useRiskStore();

    // Settings store for scanner visibility
    const { scannersEnabled } = useSettingsStore();
    const { craMode } = useCRAModeStore();

    // User store for role check
    const { current_user } = useUserStore();
    const canSeedDefaults = ['super_admin', 'org_admin'].includes(current_user?.role_name);

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    // Seeding state
    const [seedingDefaults, setSeedingDefaults] = useState(false);

    // Tab state
    const [activeTab, setActiveTab] = useState('assets');

    // Asset form state
    const [showAssetModal, setShowAssetModal] = useState(false);
    const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
    const [assetName, setAssetName] = useState('');
    const [assetVersion, setAssetVersion] = useState('');
    const [assetJustification, setAssetJustification] = useState('');
    const [assetLicense, setAssetLicense] = useState('');
    const [assetDescription, setAssetDescription] = useState('');
    const [assetSbom, setAssetSbom] = useState('');
    const [assetIpAddress, setAssetIpAddress] = useState('');
    const [assetTypeId, setAssetTypeId] = useState<string | undefined>(undefined);
    const [assetStatusId, setAssetStatusId] = useState<string | undefined>(undefined);
    const [economicOperatorId, setEconomicOperatorId] = useState<string | undefined>(undefined);
    const [criticalityId, setCriticalityId] = useState<string | undefined>(undefined);

    // Asset CIA state
    const [assetConfidentiality, setAssetConfidentiality] = useState<string | undefined>(undefined);
    const [assetIntegrity, setAssetIntegrity] = useState<string | undefined>(undefined);
    const [assetAvailability, setAssetAvailability] = useState<string | undefined>(undefined);
    const [assetAssetValue, setAssetAssetValue] = useState<string | undefined>(undefined);
    const [assetInheritCia, setAssetInheritCia] = useState(true);
    const [assetModalTab, setAssetModalTab] = useState('details');

    // Asset Type form state
    const [showAssetTypeModal, setShowAssetTypeModal] = useState(false);
    const [selectedAssetType, setSelectedAssetType] = useState<AssetType | null>(null);
    const [assetTypeName, setAssetTypeName] = useState('');
    const [assetTypeDescription, setAssetTypeDescription] = useState('');
    const [assetTypeIcon, setAssetTypeIcon] = useState<string | undefined>(undefined);
    const [assetTypeDefaultC, setAssetTypeDefaultC] = useState<string | undefined>(undefined);
    const [assetTypeDefaultI, setAssetTypeDefaultI] = useState<string | undefined>(undefined);
    const [assetTypeDefaultA, setAssetTypeDefaultA] = useState<string | undefined>(undefined);
    const [assetTypeDefaultAV, setAssetTypeDefaultAV] = useState<string | undefined>(undefined);

    // View state for Assets
    const [assetViewMode, setAssetViewMode] = useState<'grid' | 'list'>('list');
    const [assetSearchText, setAssetSearchText] = useState('');

    // View state for Asset Types
    const [assetTypeViewMode, setAssetTypeViewMode] = useState<'grid' | 'list'>('grid');
    const [assetTypeSearchText, setAssetTypeSearchText] = useState('');

    // Connection tab state
    const [selectedConnectionAsset, setSelectedConnectionAsset] = useState<string | undefined>(undefined);
    const [assetRecommendationLoading, setAssetRecommendationLoading] = useState<Record<string, boolean>>({});

    // Fetch data on component mount
    useEffect(() => {
        fetchAssetTypes();
        fetchAssets();
        fetchAssetStatuses();
        fetchEconomicOperators();
        fetchCriticalities();
        fetchRisks();
    }, [fetchAssetTypes, fetchAssets, fetchAssetStatuses, fetchEconomicOperators, fetchCriticalities, fetchRisks]);

    // Fetch linked risks when connection asset changes
    useEffect(() => {
        if (selectedConnectionAsset) {
            fetchLinkedRisks(selectedConnectionAsset);
        }
    }, [selectedConnectionAsset, fetchLinkedRisks]);

    useEffect(() => {
        if (riskTemplateCategories.length === 0) {
            fetchRiskTemplateCategories();
        }
        if (riskSeverities.length === 0) {
            fetchRiskSeverities();
        }
        if (riskStatuses.length === 0) {
            fetchRiskStatuses();
        }
        if (assetCategories.length === 0) {
            fetchAssetCategories();
        }
    }, [
        riskTemplateCategories.length,
        riskSeverities.length,
        riskStatuses.length,
        assetCategories.length,
        fetchRiskTemplateCategories,
        fetchRiskSeverities,
        fetchRiskStatuses,
        fetchAssetCategories,
    ]);

    // Clear asset form
    const clearAssetForm = () => {
        setAssetName('');
        setAssetVersion('');
        setAssetJustification('');
        setAssetLicense('');
        setAssetDescription('');
        setAssetSbom('');
        setAssetIpAddress('');
        setAssetTypeId(undefined);
        setAssetStatusId(undefined);
        setEconomicOperatorId(undefined);
        setCriticalityId(undefined);
        setAssetConfidentiality(undefined);
        setAssetIntegrity(undefined);
        setAssetAvailability(undefined);
        setAssetAssetValue(undefined);
        setAssetInheritCia(true);
        setAssetModalTab('details');
        setSelectedAsset(null);
    };

    // Clear asset type form
    const clearAssetTypeForm = () => {
        setAssetTypeName('');
        setAssetTypeDescription('');
        setAssetTypeIcon(undefined);
        setAssetTypeDefaultC(undefined);
        setAssetTypeDefaultI(undefined);
        setAssetTypeDefaultA(undefined);
        setAssetTypeDefaultAV(undefined);
        setSelectedAssetType(null);
    };

    // Helper function to extract criticality ID from the combined value
    const getCriticalityIdFromValue = (value: string) => {
        return value ? value.split(':')[0] : undefined;
    };

    // Helper function to extract criticality option value from the combined value
    const getCriticalityOptionValueFromCombinedValue = (value: string) => {
        if (!value) return undefined;
        const [critId, optionId] = value.split(':');
        for (const criticality of criticalities) {
            if (criticality.id === critId) {
                const option = criticality.options.find(opt => opt.id === optionId);
                return option ? option.value : undefined;
            }
        }
        return undefined;
    };

    // Helper function to find the combined value for a given criticality value
    const getCombinedValueForCriticalityValue = (criticalityValue: string) => {
        for (const criticality of criticalities) {
            for (const option of criticality.options) {
                if (option.value === criticalityValue) {
                    return `${criticality.id}:${option.id}`;
                }
            }
        }
        return undefined;
    };

    // Handle asset save
    const handleSaveAsset = async () => {
        if (!assetName || !assetTypeId) {
            api.error({
                message: 'Validation Error',
                description: 'Please fill in all required fields (Name and Asset Type)',
                duration: 4,
            });
            return;
        }

        // Extract the actual criticality ID and option value from the combined value
        const actualCriticalityId = criticalityId ? getCriticalityIdFromValue(criticalityId) : undefined;
        const criticalityOptionValue = criticalityId ? getCriticalityOptionValueFromCombinedValue(criticalityId) : undefined;

        let result;
        if (selectedAsset) {
            result = await updateAsset(
                selectedAsset.id,
                assetName,
                assetTypeId,
                assetDescription,
                assetIpAddress,
                assetVersion,
                assetJustification,
                assetLicense,
                assetSbom,
                assetStatusId,
                economicOperatorId,
                actualCriticalityId,
                criticalityOptionValue,
                assetInheritCia ? undefined : assetConfidentiality,
                assetInheritCia ? undefined : assetIntegrity,
                assetInheritCia ? undefined : assetAvailability,
                assetInheritCia ? undefined : assetAssetValue,
                assetInheritCia
            );
        } else {
            result = await createAsset(
                assetName,
                assetTypeId,
                assetDescription,
                assetIpAddress,
                assetVersion,
                assetJustification,
                assetLicense,
                assetSbom,
                assetStatusId,
                economicOperatorId,
                actualCriticalityId,
                criticalityOptionValue,
                assetInheritCia ? undefined : assetConfidentiality,
                assetInheritCia ? undefined : assetIntegrity,
                assetInheritCia ? undefined : assetAvailability,
                assetInheritCia ? undefined : assetAssetValue,
                assetInheritCia
            );
        }

        if (result.success) {
            api.success({
                message: selectedAsset ? 'Asset Updated' : 'Asset Created',
                description: selectedAsset ? 'Asset updated successfully' : 'Asset created successfully',
                duration: 4,
            });
            setShowAssetModal(false);
            clearAssetForm();
            fetchAssets();
            fetchAssetTypes(); // Refresh counts
        } else {
            api.error({
                message: selectedAsset ? 'Update Failed' : 'Creation Failed',
                description: result.error || 'An error occurred',
                duration: 4,
            });
        }
    };

    // Handle asset delete
    const handleDeleteAsset = async () => {
        if (!selectedAsset) return;

        const result = await deleteAsset(selectedAsset.id);
        if (result.success) {
            api.success({
                message: 'Asset Deleted',
                description: 'Asset deleted successfully',
                duration: 4,
            });
            setShowAssetModal(false);
            clearAssetForm();
            fetchAssets();
            fetchAssetTypes(); // Refresh counts
        } else {
            api.error({
                message: 'Deletion Failed',
                description: result.error || 'An error occurred',
                duration: 4,
            });
        }
    };

    // Handle asset type save
    const handleSaveAssetType = async () => {
        if (!assetTypeName) {
            api.error({
                message: 'Validation Error',
                description: 'Please enter a name for the asset type',
                duration: 4,
            });
            return;
        }

        let result;
        if (selectedAssetType) {
            result = await updateAssetType(selectedAssetType.id, assetTypeName, assetTypeIcon, assetTypeDescription, assetTypeDefaultC, assetTypeDefaultI, assetTypeDefaultA, assetTypeDefaultAV);
        } else {
            result = await createAssetType(assetTypeName, assetTypeIcon, assetTypeDescription, assetTypeDefaultC, assetTypeDefaultI, assetTypeDefaultA, assetTypeDefaultAV);
        }

        if (result.success) {
            api.success({
                message: selectedAssetType ? 'Asset Type Updated' : 'Asset Type Created',
                description: selectedAssetType ? 'Asset type updated successfully' : 'Asset type created successfully',
                duration: 4,
            });
            setShowAssetTypeModal(false);
            clearAssetTypeForm();
            fetchAssetTypes();
        } else {
            api.error({
                message: selectedAssetType ? 'Update Failed' : 'Creation Failed',
                description: result.error || 'An error occurred',
                duration: 4,
            });
        }
    };

    // Handle asset type delete
    const handleDeleteAssetType = async (assetType: AssetType) => {
        if (assetType.asset_count > 0) {
            api.error({
                message: 'Cannot Delete',
                description: `This asset type has ${assetType.asset_count} asset(s). Please delete or reassign them first.`,
                duration: 4,
            });
            return;
        }

        const result = await deleteAssetType(assetType.id);
        if (result.success) {
            api.success({
                message: 'Asset Type Deleted',
                description: 'Asset type deleted successfully',
                duration: 4,
            });
            fetchAssetTypes();
        } else {
            api.error({
                message: 'Deletion Failed',
                description: result.error || 'An error occurred',
                duration: 4,
            });
        }
    };

    const handleImportAndLinkRiskRecommendation = async (categoryId: string, riskTemplate: any) => {
        if (!selectedConnectionAsset) {
            api.warning({
                message: 'No Asset Selected',
                description: 'Select an asset in the Connections tab before importing risks.',
                duration: 4,
            });
            return;
        }

        const riskKey = `${categoryId}-${riskTemplate.risk_code}`;
        setAssetRecommendationLoading((prev) => ({ ...prev, [riskKey]: true }));
        try {
            const defaultAssetCategory = assetCategories.length > 0 ? assetCategories[0].id : '';
            const defaultLikelihood = riskSeverities.length > 0 ? riskSeverities[0].id : '';
            const defaultSeverity = riskSeverities.length > 0 ? riskSeverities[0].id : '';
            const defaultResidual = riskSeverities.length > 0 ? riskSeverities[0].id : '';
            const defaultStatus = riskStatuses.length > 0 ? riskStatuses[0].id : '';

            const result = await importRiskTemplates(
                categoryId,
                [riskTemplate],
                defaultAssetCategory,
                defaultLikelihood,
                defaultSeverity,
                defaultResidual,
                defaultStatus
            );
            if (result.success && result.imported_risk_ids.length > 0) {
                for (const riskId of result.imported_risk_ids) {
                    await linkAssetToRisk(selectedConnectionAsset, riskId);
                }
                await fetchLinkedRisks(selectedConnectionAsset);
                await fetchRisks();
                api.success({
                    message: 'Risk Imported & Linked',
                    description: `Imported ${result.imported_risk_ids.length} risk(s) and linked to asset`,
                    duration: 4,
                });
            } else if (result.success && result.imported_count === 0) {
                api.info({
                    message: 'Already Imported',
                    description: result.message || 'This risk has already been imported.',
                    duration: 4,
                });
            } else {
                api.error({
                    message: 'Import Failed',
                    description: result.message || 'Failed to import risk',
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
            setAssetRecommendationLoading((prev) => ({ ...prev, [riskKey]: false }));
        }
    };

    // Edit asset type
    const handleEditAssetType = (assetType: AssetType) => {
        setSelectedAssetType(assetType);
        setAssetTypeName(assetType.name);
        setAssetTypeDescription(assetType.description || '');
        setAssetTypeIcon(assetType.icon_name || undefined);
        setAssetTypeDefaultC(assetType.default_confidentiality || undefined);
        setAssetTypeDefaultI(assetType.default_integrity || undefined);
        setAssetTypeDefaultA(assetType.default_availability || undefined);
        setAssetTypeDefaultAV(assetType.default_asset_value || undefined);
        setShowAssetTypeModal(true);
    };

    // Get risk level tag color
    const getRiskLevelColor = (level: string) => {
        switch (level) {
            case 'Severe': return 'red';
            case 'Medium': return 'orange';
            case 'Low': return 'green';
            default: return 'default';
        }
    };

    // CIA level color helper
    const getCiaLevelColor = (level: string | null | undefined) => {
        if (!level) return 'default';
        switch (level.toLowerCase()) {
            case 'high': return 'red';
            case 'medium': return 'orange';
            case 'low': return 'green';
            default: return 'default';
        }
    };

    // Compute OAV client-side for preview
    const computeOav = () => {
        const levelOrder: Record<string, number> = { high: 3, medium: 2, low: 1 };
        let currentC = assetConfidentiality;
        let currentI = assetIntegrity;
        let currentA = assetAvailability;
        let currentAV = assetAssetValue;

        if (assetInheritCia && assetTypeId) {
            const at = assetTypes.find(t => t.id === assetTypeId);
            if (at) {
                currentC = at.default_confidentiality || undefined;
                currentI = at.default_integrity || undefined;
                currentA = at.default_availability || undefined;
                currentAV = at.default_asset_value || undefined;
            }
        }

        const values = [currentC, currentI, currentA, currentAV];
        let highest = 0;
        for (const v of values) {
            if (v && levelOrder[v.toLowerCase()]) {
                highest = Math.max(highest, levelOrder[v.toLowerCase()]);
            }
        }
        const reverseMap: Record<number, string> = { 3: 'High', 2: 'Medium', 1: 'Low' };
        return reverseMap[highest] || null;
    };

    // Get effective CIA values (considering inheritance)
    const getEffectiveCiaValues = () => {
        if (assetInheritCia && assetTypeId) {
            const at = assetTypes.find(t => t.id === assetTypeId);
            if (at) {
                return {
                    c: at.default_confidentiality || undefined,
                    i: at.default_integrity || undefined,
                    a: at.default_availability || undefined,
                    av: at.default_asset_value || undefined,
                };
            }
        }
        return {
            c: assetConfidentiality,
            i: assetIntegrity,
            a: assetAvailability,
            av: assetAssetValue,
        };
    };

    // Filter assets by search
    const filteredAssets = assets.filter(asset =>
        asset.name.toLowerCase().includes(assetSearchText.toLowerCase()) ||
        (asset.description && asset.description.toLowerCase().includes(assetSearchText.toLowerCase())) ||
        (asset.asset_type_name && asset.asset_type_name.toLowerCase().includes(assetSearchText.toLowerCase())) ||
        (asset.ip_address && asset.ip_address.toLowerCase().includes(assetSearchText.toLowerCase()))
    );

    // Filter asset types by search
    const filteredAssetTypes = assetTypes.filter(at =>
        at.name.toLowerCase().includes(assetTypeSearchText.toLowerCase()) ||
        (at.description && at.description.toLowerCase().includes(assetTypeSearchText.toLowerCase()))
    );

    // Helper to get individual scan status tag
    const getScanStatusTag = (status: string | null, date: string | null, label: string) => {
        if (!status) {
            return (
                <Tooltip title={`${label}: Not scanned`}>
                    <Tag color="default" style={{ display: 'flex', alignItems: 'center', gap: '2px', fontSize: '11px', padding: '0 4px' }}>
                        <MinusCircleOutlined style={{ fontSize: '10px' }} /> {label}
                    </Tag>
                </Tooltip>
            );
        }

        const scanDate = date ? new Date(date).toLocaleDateString() : '';
        const tooltipText = `${label}: ${scanDate}`;

        switch (status) {
            case 'completed':
                return (
                    <Tooltip title={tooltipText}>
                        <Tag color="green" style={{ display: 'flex', alignItems: 'center', gap: '2px', fontSize: '11px', padding: '0 4px' }}>
                            <CheckCircleOutlined style={{ fontSize: '10px' }} /> {label}
                        </Tag>
                    </Tooltip>
                );
            case 'failed':
                return (
                    <Tooltip title={tooltipText}>
                        <Tag color="red" style={{ display: 'flex', alignItems: 'center', gap: '2px', fontSize: '11px', padding: '0 4px' }}>
                            <CloseCircleOutlined style={{ fontSize: '10px' }} /> {label}
                        </Tag>
                    </Tooltip>
                );
            case 'in_progress':
                return (
                    <Tooltip title={tooltipText}>
                        <Tag color="blue" style={{ display: 'flex', alignItems: 'center', gap: '2px', fontSize: '11px', padding: '0 4px' }}>
                            <SyncOutlined spin style={{ fontSize: '10px' }} /> {label}
                        </Tag>
                    </Tooltip>
                );
            default:
                return (
                    <Tooltip title={tooltipText}>
                        <Tag color="green" style={{ display: 'flex', alignItems: 'center', gap: '2px', fontSize: '11px', padding: '0 4px' }}>
                            <CheckCircleOutlined style={{ fontSize: '10px' }} /> {label}
                        </Tag>
                    </Tooltip>
                );
        }
    };

    // Helper to get scan status display
    const getScanStatusDisplay = (asset: Asset) => {
        if (!asset.ip_address) {
            return (
                <Tooltip title="No IP/URL configured">
                    <Tag color="default" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <MinusCircleOutlined /> N/A
                    </Tag>
                </Tooltip>
            );
        }

        // Show both Network and Application scan status
        return (
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {getScanStatusTag(asset.network_scan_status, asset.network_scan_date, 'Network')}
                {getScanStatusTag(asset.application_scan_status, asset.application_scan_date, 'App')}
            </div>
        );
    };

    // Asset table columns (conditionally include scan status)
    const baseAssetColumns = [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            sorter: (a: Asset, b: Asset) => a.name.localeCompare(b.name),
        },
        {
            title: 'Version',
            dataIndex: 'version',
            key: 'version',
            width: 100,
            render: (text: string) => text || '-',
        },
        {
            title: 'Asset Type',
            dataIndex: 'asset_type_name',
            key: 'asset_type_name',
            render: (text: string, record: Asset) => (
                <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {renderIcon(record.asset_type_icon, { fontSize: '16px', color: '#1890ff' })}
                    {text}
                </span>
            ),
            filters: assetTypes.map(at => ({ text: at.name, value: at.id })),
            onFilter: (value: any, record: Asset) => record.asset_type_id === value,
        },
        {
            title: 'Status',
            dataIndex: 'status_name',
            key: 'status_name',
            width: 120,
            render: (text: string) => text ? <Tag color="blue">{text}</Tag> : '-',
            filters: assetStatuses.map(s => ({ text: s.status, value: s.status })),
            onFilter: (value: any, record: Asset) => record.status_name === value,
        },
        {
            title: 'IP / URL',
            dataIndex: 'ip_address',
            key: 'ip_address',
            ellipsis: true,
            render: (text: string) => text || '-',
        },
        {
            title: 'Economic Operator',
            dataIndex: 'economic_operator_name',
            key: 'economic_operator_name',
            width: 150,
            ellipsis: true,
            render: (text: string) => text || '-',
        },
        ...(craMode !== null ? [{
            title: 'Criticality',
            dataIndex: 'criticality_option',
            key: 'criticality_option',
            width: 150,
            ellipsis: true,
            render: (text: string, record: Asset) => {
                if (!text) return '-';
                return (
                    <Tooltip title={text}>
                        <span>{record.criticality_label ? `${record.criticality_label}: ${text.substring(0, 20)}${text.length > 20 ? '...' : ''}` : text}</span>
                    </Tooltip>
                );
            },
        }] : []),
        {
            title: 'OAV',
            dataIndex: 'overall_asset_value',
            key: 'overall_asset_value',
            width: 80,
            render: (text: string) => text ? <Tag color={getCiaLevelColor(text)}>{text.charAt(0).toUpperCase() + text.slice(1)}</Tag> : '-',
            filters: [
                { text: 'High', value: 'high' },
                { text: 'Medium', value: 'medium' },
                { text: 'Low', value: 'low' },
            ],
            onFilter: (value: any, record: Asset) => record.overall_asset_value === value,
        },
        {
            title: 'Last Updated',
            dataIndex: 'updated_at',
            key: 'updated_at',
            width: 120,
            render: (text: string) => text ? new Date(text).toLocaleDateString() : '-',
            sorter: (a: Asset, b: Asset) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime(),
        },
    ];

    // Scan status column - only shown when scanners are enabled
    const scanStatusColumn = {
        title: 'Scan Status',
        key: 'scan_status',
        width: 180,
        render: (_: any, record: Asset) => getScanStatusDisplay(record),
        filters: [
            { text: 'Both Scanned', value: 'both_scanned' },
            { text: 'Network Only', value: 'network_only' },
            { text: 'Application Only', value: 'app_only' },
            { text: 'Not Scanned', value: 'not_scanned' },
            { text: 'N/A', value: 'na' },
        ],
        onFilter: (value: any, record: Asset) => {
            if (value === 'na') return !record.ip_address;
            if (value === 'both_scanned') return !!record.network_scan_status && !!record.application_scan_status;
            if (value === 'network_only') return !!record.network_scan_status && !record.application_scan_status;
            if (value === 'app_only') return !record.network_scan_status && !!record.application_scan_status;
            if (value === 'not_scanned') return !record.network_scan_status && !record.application_scan_status && !!record.ip_address;
            return true;
        },
    };

    // Conditionally add scan status column when scanners are enabled
    const assetColumns = scannersEnabled
        ? [...baseAssetColumns.slice(0, 2), scanStatusColumn, ...baseAssetColumns.slice(2)]
        : baseAssetColumns;

    // Asset type options for select
    const assetTypeOptions = assetTypes.map(at => ({
        label: at.name,
        value: at.id,
    }));

    // Asset status options for select
    const statusOptions = assetStatuses.map(status => ({
        label: status.status,
        value: status.id,
    }));

    // Economic operator options for select
    const operatorOptions = economicOperators.map(operator => ({
        label: operator.name,
        value: operator.id,
    }));

    // Criticality options for grouped select component
    const criticalityOptions = criticalities.map(criticality => ({
        label: <span>{criticality.label}</span>,
        title: criticality.label,
        options: criticality.options.map(option => ({
            label: (
                <Tooltip title={option.value} placement="topLeft">
                    <span>{option.value}</span>
                </Tooltip>
            ),
            value: `${criticality.id}:${option.id}`
        }))
    }));

    // Custom filter for criticality Select (handles nested structure and title property)
    const filterCriticalityOption = (input: string, option?: any) => {
        if (!option) return false;
        // For group titles (criticality names)
        if (option.title && typeof option.title === 'string') {
            return option.title.toLowerCase().includes(input.toLowerCase());
        }
        // For option labels (criticality option values)
        if (option.options) {
            return option.options.some((nestedOption: any) => {
                const textContent = nestedOption.label?.props?.title ||
                                  nestedOption.label?.props?.children?.props?.children ||
                                  '';
                return typeof textContent === 'string' &&
                       textContent.toLowerCase().includes(input.toLowerCase());
            });
        }
        return false;
    };

    // Asset Type Card component
    const AssetTypeCard = ({ assetType }: { assetType: AssetType }) => {
        const menuItems = [
            {
                key: 'edit',
                label: 'Edit',
                icon: <EditOutlined />,
                onClick: () => handleEditAssetType(assetType),
            },
            {
                key: 'delete',
                label: 'Delete',
                icon: <DeleteOutlined />,
                danger: true,
                onClick: () => handleDeleteAssetType(assetType),
            },
        ];

        return (
            <Card
                hoverable
                style={{ height: '100%' }}
                bodyStyle={{ padding: '16px' }}
                onClick={() => handleEditAssetType(assetType)}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{
                            width: '48px',
                            height: '48px',
                            borderRadius: '8px',
                            backgroundColor: '#f0f5ff',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                        }}>
                            {renderIcon(assetType.icon_name, { fontSize: '24px', color: '#1890ff' })}
                        </div>
                        <div>
                            <h4 style={{ margin: 0, fontSize: '16px', fontWeight: 500 }}>{assetType.name}</h4>
                        </div>
                    </div>
                    <div onClick={(e) => e.stopPropagation()}>
                        <Dropdown menu={{ items: menuItems }} trigger={['click']}>
                            <button
                                style={{
                                    border: 'none',
                                    background: 'transparent',
                                    cursor: 'pointer',
                                    padding: '4px',
                                }}
                            >
                                <MoreOutlined style={{ fontSize: '16px' }} />
                            </button>
                        </Dropdown>
                    </div>
                </div>

                <div style={{ marginTop: '16px', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span style={{ color: '#8c8c8c', fontSize: '13px' }}>Risks:</span>
                        <span style={{ fontWeight: 500 }}>{assetType.risk_count}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <span style={{ color: '#8c8c8c', fontSize: '13px' }}>Assets:</span>
                        <span style={{ fontWeight: 500 }}>{assetType.asset_count}</span>
                    </div>
                    <Tag color={getRiskLevelColor(assetType.risk_level)}>
                        {assetType.risk_level}
                    </Tag>
                </div>

                {assetType.description && (
                    <p style={{
                        marginTop: '12px',
                        marginBottom: 0,
                        color: '#8c8c8c',
                        fontSize: '13px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                    }}>
                        {assetType.description}
                    </p>
                )}
            </Card>
        );
    };

    // Asset Card component
    const AssetCard = ({ asset }: { asset: Asset }) => {
        const handleCardClick = () => {
            setSelectedAsset(asset);
            setAssetName(asset.name);
            setAssetVersion(asset.version || '');
            setAssetJustification(asset.justification || '');
            setAssetLicense(asset.license_model || '');
            setAssetDescription(asset.description || '');
            setAssetSbom(asset.sbom || '');
            setAssetIpAddress(asset.ip_address || '');
            setAssetTypeId(asset.asset_type_id);
            setAssetStatusId(asset.asset_status_id || undefined);
            setEconomicOperatorId(asset.economic_operator_id || undefined);
            setCriticalityId(asset.criticality_option ? getCombinedValueForCriticalityValue(asset.criticality_option) : undefined);
            setAssetConfidentiality(asset.confidentiality || undefined);
            setAssetIntegrity(asset.integrity || undefined);
            setAssetAvailability(asset.availability || undefined);
            setAssetAssetValue(asset.asset_value || undefined);
            setAssetInheritCia(asset.inherit_cia !== false);
            setAssetModalTab('details');
            setShowAssetModal(true);
        };

        return (
            <Card
                hoverable
                style={{ height: '100%' }}
                bodyStyle={{ padding: '16px' }}
                onClick={handleCardClick}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
                        <div style={{
                            width: '48px',
                            height: '48px',
                            borderRadius: '8px',
                            backgroundColor: '#f0f5ff',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flexShrink: 0,
                        }}>
                            {renderIcon(asset.asset_type_icon, { fontSize: '24px', color: '#1890ff' })}
                        </div>
                        <div style={{ overflow: 'hidden' }}>
                            <h4 style={{ margin: 0, fontSize: '16px', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {asset.name}
                            </h4>
                            <span style={{ color: '#8c8c8c', fontSize: '13px' }}>
                                {asset.asset_type_name}
                            </span>
                        </div>
                    </div>
                    {asset.status_name && (
                        <Tag color="blue" style={{ flexShrink: 0 }}>{asset.status_name}</Tag>
                    )}
                </div>

                <div style={{ marginTop: '16px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {asset.version && (
                        <Tag color="default">v{asset.version}</Tag>
                    )}
                    {asset.economic_operator_name && (
                        <Tag color="purple">{asset.economic_operator_name}</Tag>
                    )}
                    {asset.criticality_label && asset.criticality_option && (
                        <Tooltip title={asset.criticality_option}>
                            <Tag color="orange">{asset.criticality_label}</Tag>
                        </Tooltip>
                    )}
                </div>

                {asset.ip_address && (
                    <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ color: '#8c8c8c', fontSize: '12px' }}>IP/URL:</span>
                        <span style={{ fontSize: '13px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {asset.ip_address}
                        </span>
                    </div>
                )}

                {scannersEnabled && asset.ip_address && (
                    <div style={{ marginTop: '8px' }}>
                        {getScanStatusDisplay(asset)}
                    </div>
                )}

                {asset.description && (
                    <p style={{
                        marginTop: '12px',
                        marginBottom: 0,
                        color: '#8c8c8c',
                        fontSize: '13px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                    }}>
                        {asset.description}
                    </p>
                )}

                <div style={{ marginTop: '12px', fontSize: '12px', color: '#bfbfbf' }}>
                    Updated: {asset.updated_at ? new Date(asset.updated_at).toLocaleDateString() : '-'}
                </div>
            </Card>
        );
    };

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
                            <DatabaseOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Asset Management"
                                infoContent={AssetsInfo}
                                className="page-title"
                            />
                        </div>
                    </div>

                    {/* Tabs */}
                    <Tabs
                        activeKey={activeTab}
                        onChange={setActiveTab}
                        items={[
                            {
                                key: 'assets',
                                label: 'Assets',
                                children: (
                                    <div className="page-section">
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                                <Input
                                                    placeholder="Search assets..."
                                                    prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                                    value={assetSearchText}
                                                    onChange={(e) => setAssetSearchText(e.target.value)}
                                                    style={{ width: '250px' }}
                                                />
                                                <div style={{ display: 'flex', border: '1px solid #d9d9d9', borderRadius: '6px', overflow: 'hidden' }}>
                                                    <button
                                                        onClick={() => setAssetViewMode('grid')}
                                                        style={{
                                                            border: 'none',
                                                            padding: '6px 12px',
                                                            cursor: 'pointer',
                                                            backgroundColor: assetViewMode === 'grid' ? '#1890ff' : 'white',
                                                            color: assetViewMode === 'grid' ? 'white' : '#595959',
                                                        }}
                                                    >
                                                        <AppstoreOutlined />
                                                    </button>
                                                    <button
                                                        onClick={() => setAssetViewMode('list')}
                                                        style={{
                                                            border: 'none',
                                                            borderLeft: '1px solid #d9d9d9',
                                                            padding: '6px 12px',
                                                            cursor: 'pointer',
                                                            backgroundColor: assetViewMode === 'list' ? '#1890ff' : 'white',
                                                            color: assetViewMode === 'list' ? 'white' : '#595959',
                                                        }}
                                                    >
                                                        <UnorderedListOutlined />
                                                    </button>
                                                </div>
                                            </div>
                                            <button
                                                className="add-button"
                                                data-tour-id="qs-assets-add-button"
                                                onClick={() => {
                                                    clearAssetForm();
                                                    setShowAssetModal(true);
                                                }}
                                                style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                            >
                                                <PlusOutlined /> Add Asset
                                            </button>
                                        </div>

                                        {filteredAssets.length === 0 ? (
                                            <Empty description="No assets found" />
                                        ) : assetViewMode === 'grid' ? (
                                            <Row gutter={[16, 16]}>
                                                {filteredAssets.map(asset => (
                                                    <Col key={asset.id} xs={24} sm={12} md={8} lg={6}>
                                                        <AssetCard asset={asset} />
                                                    </Col>
                                                ))}
                                            </Row>
                                        ) : (
                                            <Table
                                                columns={assetColumns}
                                                dataSource={filteredAssets}
                                                loading={loading}
                                                rowKey="id"
                                                onRow={(record) => ({
                                                    onClick: () => {
                                                        setSelectedAsset(record);
                                                        setAssetName(record.name);
                                                        setAssetVersion(record.version || '');
                                                        setAssetJustification(record.justification || '');
                                                        setAssetLicense(record.license_model || '');
                                                        setAssetDescription(record.description || '');
                                                        setAssetSbom(record.sbom || '');
                                                        setAssetIpAddress(record.ip_address || '');
                                                        setAssetTypeId(record.asset_type_id);
                                                        setAssetStatusId(record.asset_status_id || undefined);
                                                        setEconomicOperatorId(record.economic_operator_id || undefined);
                                                        setCriticalityId(record.criticality_option ? getCombinedValueForCriticalityValue(record.criticality_option) : undefined);
                                                        setAssetConfidentiality(record.confidentiality || undefined);
                                                        setAssetIntegrity(record.integrity || undefined);
                                                        setAssetAvailability(record.availability || undefined);
                                                        setAssetAssetValue(record.asset_value || undefined);
                                                        setAssetInheritCia(record.inherit_cia !== false);
                                                        setAssetModalTab('details');
                                                        setShowAssetModal(true);
                                                    },
                                                    style: { cursor: 'pointer' }
                                                })}
                                                pagination={{
                                                    showSizeChanger: true,
                                                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} assets`,
                                                }}
                                                scroll={{ x: 800 }}
                                            />
                                        )}
                                    </div>
                                ),
                            },
                            {
                                key: 'asset-types',
                                label: 'Asset Types',
                                children: (
                                    <div className="page-section">
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                                <Input
                                                    placeholder="Search asset types..."
                                                    prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                                    value={assetTypeSearchText}
                                                    onChange={(e) => setAssetTypeSearchText(e.target.value)}
                                                    style={{ width: '250px' }}
                                                />
                                                <div style={{ display: 'flex', border: '1px solid #d9d9d9', borderRadius: '6px', overflow: 'hidden' }}>
                                                    <button
                                                        onClick={() => setAssetTypeViewMode('grid')}
                                                        style={{
                                                            border: 'none',
                                                            padding: '6px 12px',
                                                            cursor: 'pointer',
                                                            backgroundColor: assetTypeViewMode === 'grid' ? '#1890ff' : 'white',
                                                            color: assetTypeViewMode === 'grid' ? 'white' : '#595959',
                                                        }}
                                                    >
                                                        <AppstoreOutlined />
                                                    </button>
                                                    <button
                                                        onClick={() => setAssetTypeViewMode('list')}
                                                        style={{
                                                            border: 'none',
                                                            borderLeft: '1px solid #d9d9d9',
                                                            padding: '6px 12px',
                                                            cursor: 'pointer',
                                                            backgroundColor: assetTypeViewMode === 'list' ? '#1890ff' : 'white',
                                                            color: assetTypeViewMode === 'list' ? 'white' : '#595959',
                                                        }}
                                                    >
                                                        <UnorderedListOutlined />
                                                    </button>
                                                </div>
                                            </div>
                                            <div style={{ display: 'flex', gap: '8px' }}>
                                                {canSeedDefaults && (
                                                    <button
                                                        className="add-button"
                                                        disabled={seedingDefaults}
                                                        onClick={async () => {
                                                            setSeedingDefaults(true);
                                                            const result = await seedDefaultAssetTypes();
                                                            setSeedingDefaults(false);
                                                            if (result.success) {
                                                                api.success({
                                                                    message: 'Default Asset Types',
                                                                    description: result.message || 'Default asset types imported successfully',
                                                                });
                                                            } else {
                                                                api.error({
                                                                    message: 'Import Failed',
                                                                    description: result.error || 'Failed to import default asset types',
                                                                });
                                                            }
                                                        }}
                                                        style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: seedingDefaults ? 0.6 : 1 }}
                                                    >
                                                        <ImportOutlined /> {seedingDefaults ? 'Importing...' : 'Import Default Types'}
                                                    </button>
                                                )}
                                                <button
                                                    className="add-button"
                                                    onClick={() => {
                                                        clearAssetTypeForm();
                                                        setShowAssetTypeModal(true);
                                                    }}
                                                    style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                                >
                                                    <PlusOutlined /> Add Asset Type
                                                </button>
                                            </div>
                                        </div>

                                        {filteredAssetTypes.length === 0 ? (
                                            <Empty description="No asset types found" />
                                        ) : assetTypeViewMode === 'grid' ? (
                                            <Row gutter={[16, 16]}>
                                                {filteredAssetTypes.map(assetType => (
                                                    <Col key={assetType.id} xs={24} sm={12} md={8} lg={6}>
                                                        <AssetTypeCard assetType={assetType} />
                                                    </Col>
                                                ))}
                                            </Row>
                                        ) : (
                                            <Table
                                                columns={[
                                                    {
                                                        title: 'Icon',
                                                        dataIndex: 'icon_name',
                                                        key: 'icon',
                                                        width: 60,
                                                        render: (iconName: string) => renderIcon(iconName, { fontSize: '20px', color: '#1890ff' }),
                                                    },
                                                    {
                                                        title: 'Name',
                                                        dataIndex: 'name',
                                                        key: 'name',
                                                        sorter: (a: AssetType, b: AssetType) => a.name.localeCompare(b.name),
                                                    },
                                                    {
                                                        title: 'Description',
                                                        dataIndex: 'description',
                                                        key: 'description',
                                                        ellipsis: true,
                                                    },
                                                    {
                                                        title: 'Assets',
                                                        dataIndex: 'asset_count',
                                                        key: 'asset_count',
                                                        sorter: (a: AssetType, b: AssetType) => a.asset_count - b.asset_count,
                                                    },
                                                    {
                                                        title: 'Risks',
                                                        dataIndex: 'risk_count',
                                                        key: 'risk_count',
                                                        sorter: (a: AssetType, b: AssetType) => a.risk_count - b.risk_count,
                                                    },
                                                    {
                                                        title: 'Risk Level',
                                                        dataIndex: 'risk_level',
                                                        key: 'risk_level',
                                                        render: (level: string) => <Tag color={getRiskLevelColor(level)}>{level}</Tag>,
                                                        filters: [
                                                            { text: 'Low', value: 'Low' },
                                                            { text: 'Medium', value: 'Medium' },
                                                            { text: 'Severe', value: 'Severe' },
                                                        ],
                                                        onFilter: (value: any, record: AssetType) => record.risk_level === value,
                                                    },
                                                    {
                                                        title: 'Actions',
                                                        key: 'actions',
                                                        width: 100,
                                                        render: (_: any, record: AssetType) => (
                                                            <div style={{ display: 'flex', gap: '8px' }}>
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        handleEditAssetType(record);
                                                                    }}
                                                                    style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#1890ff' }}
                                                                >
                                                                    <EditOutlined />
                                                                </button>
                                                                <button
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        handleDeleteAssetType(record);
                                                                    }}
                                                                    style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#ff4d4f' }}
                                                                >
                                                                    <DeleteOutlined />
                                                                </button>
                                                            </div>
                                                        ),
                                                    },
                                                ]}
                                                dataSource={filteredAssetTypes}
                                                loading={loading}
                                                rowKey="id"
                                                pagination={{
                                                    showSizeChanger: true,
                                                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} asset types`,
                                                }}
                                                scroll={{ x: 800 }}
                                            />
                                        )}
                                    </div>
                                ),
                            },
                            {
                                key: 'connections',
                                label: (
                                    <span>
                                        <LinkOutlined style={{ marginRight: 8 }} />
                                        Connections
                                    </span>
                                ),
                                children: (() => {
                                    const selectedAssetObj = assets.find(a => a.id === selectedConnectionAsset);
                                    const riskStats = (() => {
                                        const stats = { total: 0, severe: 0, high: 0, medium: 0, low: 0 };
                                        linkedRisks.forEach((r: any) => {
                                            stats.total++;
                                            const sev = (r.risk_severity || '').toLowerCase();
                                            if (sev === 'severe' || sev === 'critical') stats.severe++;
                                            else if (sev === 'high') stats.high++;
                                            else if (sev === 'medium') stats.medium++;
                                            else stats.low++;
                                        });
                                        return stats;
                                    })();

                                    return (
                                    <div className="page-section">
                                        {/* Asset Selector */}
                                        <div style={{ marginBottom: 24 }}>
                                            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                                                Select Asset to Manage Connections
                                            </label>
                                            <Select
                                                showSearch
                                                placeholder="Select an asset..."
                                                options={assets.map(asset => ({
                                                    label: `${asset.name}${asset.asset_type_name ? ` (${asset.asset_type_name})` : ''}`,
                                                    value: asset.id,
                                                }))}
                                                value={selectedConnectionAsset}
                                                onChange={(value) => setSelectedConnectionAsset(value)}
                                                filterOption={(input, option) =>
                                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                                }
                                                style={{ width: '100%', maxWidth: 500 }}
                                                allowClear
                                            />
                                        </div>

                                        {selectedConnectionAsset && selectedAssetObj ? (
                                            <>
                                                {/* Asset Context Banner */}
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
                                                        <DatabaseOutlined style={{ fontSize: 22, color: '#fff' }} />
                                                        <div>
                                                            <div style={{ color: '#fff', fontWeight: 600, fontSize: '15px' }}>
                                                                {selectedAssetObj.name}
                                                                {selectedAssetObj.version && <span style={{ fontWeight: 400 }}> v{selectedAssetObj.version}</span>}
                                                            </div>
                                                            {selectedAssetObj.asset_type_name && (
                                                                <Tag color="rgba(255,255,255,0.2)" style={{ color: '#fff', border: '1px solid rgba(255,255,255,0.3)', marginTop: 4 }}>
                                                                    {selectedAssetObj.asset_type_name}
                                                                </Tag>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                                        <Tag color="blue">{linkedRisks.length} Risk{linkedRisks.length !== 1 ? 's' : ''} Linked</Tag>
                                                    </div>
                                                </div>

                                                <Row gutter={[24, 24]} align="top">
                                                    {/* Left Column: Connection Board */}
                                                    <Col xs={24} lg={12}>
                                                        <ConnectionBoard
                                                            title="Asset Risk Connections"
                                                            sourceLabel="Asset"
                                                            targetLabel="Risk"
                                                            relationshipLabel="exposed to"
                                                            availableItems={risks.map(risk => ({
                                                                id: risk.id,
                                                                risk_code: risk.risk_code,
                                                                risk_category_name: risk.risk_category_name,
                                                                risk_category_description: risk.risk_category_description,
                                                                risk_severity: risk.risk_severity,
                                                                risk_status: risk.risk_status,
                                                            }))}
                                                            linkedItems={linkedRisks.map(risk => ({
                                                                id: risk.id,
                                                                risk_code: risk.risk_code,
                                                                risk_category_name: risk.risk_category_name,
                                                                risk_category_description: risk.risk_category_description,
                                                                risk_severity: risk.risk_severity,
                                                                risk_status: risk.risk_status,
                                                            }))}
                                                            loading={loading}
                                                            getItemDisplayName={(item) => {
                                                                const risk = item as { risk_code?: string | null; risk_category_name?: string };
                                                                return risk.risk_code
                                                                    ? `${risk.risk_code}: ${risk.risk_category_name || 'Unknown'}`
                                                                    : risk.risk_category_name || 'Unknown Risk';
                                                            }}
                                                            getItemDescription={(item) => {
                                                                const risk = item as { risk_category_description?: string };
                                                                return risk.risk_category_description || null;
                                                            }}
                                                            getItemTags={(item) => {
                                                                const risk = item as { risk_severity?: string | null; risk_status?: string | null };
                                                                const tags: { label: string; color: string }[] = [];
                                                                if (risk.risk_severity) {
                                                                    const severityColors: Record<string, string> = {
                                                                        'Severe': 'red',
                                                                        'High': 'orange',
                                                                        'Medium': 'gold',
                                                                        'Low': 'green',
                                                                    };
                                                                    tags.push({
                                                                        label: risk.risk_severity,
                                                                        color: severityColors[risk.risk_severity] || 'default',
                                                                    });
                                                                }
                                                                if (risk.risk_status) {
                                                                    tags.push({
                                                                        label: risk.risk_status,
                                                                        color: 'blue',
                                                                    });
                                                                }
                                                                return tags;
                                                            }}
                                                            onLink={async (riskIds) => {
                                                                for (const riskId of riskIds) {
                                                                    const result = await linkAssetToRisk(selectedConnectionAsset, riskId);
                                                                    if (!result.success) {
                                                                        api.error({
                                                                            message: 'Link Failed',
                                                                            description: result.error || 'Failed to link risk to asset',
                                                                            duration: 4,
                                                                        });
                                                                        return;
                                                                    }
                                                                }
                                                                api.success({
                                                                    message: 'Risks Linked',
                                                                    description: `Successfully linked ${riskIds.length} risk(s) to the asset`,
                                                                    duration: 4,
                                                                });
                                                                fetchLinkedRisks(selectedConnectionAsset);
                                                            }}
                                                            onUnlink={async (riskIds) => {
                                                                for (const riskId of riskIds) {
                                                                    const result = await unlinkAssetFromRisk(selectedConnectionAsset, riskId);
                                                                    if (!result.success) {
                                                                        api.error({
                                                                            message: 'Unlink Failed',
                                                                            description: result.error || 'Failed to unlink risk from asset',
                                                                            duration: 4,
                                                                        });
                                                                        return;
                                                                    }
                                                                }
                                                                api.success({
                                                                    message: 'Risks Unlinked',
                                                                    description: `Successfully unlinked ${riskIds.length} risk(s) from the asset`,
                                                                    duration: 4,
                                                                });
                                                                fetchLinkedRisks(selectedConnectionAsset);
                                                            }}
                                                            height={450}
                                                        />
                                                    </Col>

                                                    {/* Right Column: Intelligence Panel */}
                                                    <Col xs={24} lg={12}>
                                                        <Card style={{ borderRadius: '10px', height: '100%' }} bodyStyle={{ padding: 0 }}>
                                                            <Tabs
                                                                defaultActiveKey="exposure"
                                                                style={{ padding: '0 16px' }}
                                                                items={[
                                                                    {
                                                                        key: 'exposure',
                                                                        label: (
                                                                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                                                <AlertOutlined />
                                                                                Risk Exposure
                                                                                {riskStats.total > 0 && <Tag color="red" style={{ marginLeft: 4 }}>{riskStats.total}</Tag>}
                                                                            </span>
                                                                        ),
                                                                        children: (
                                                                            <div style={{ paddingBottom: 16 }}>
                                                                                {/* Stats Row */}
                                                                                <div style={{ display: 'flex', gap: '8px', marginBottom: 16, flexWrap: 'wrap' }}>
                                                                                    <div style={{ flex: 1, minWidth: 70, textAlign: 'center', background: '#f0f5ff', borderRadius: 8, padding: '8px 4px' }}>
                                                                                        <div style={{ fontSize: 20, fontWeight: 700, color: '#1890ff' }}>{riskStats.total}</div>
                                                                                        <div style={{ fontSize: 11, color: '#8c8c8c' }}>Total</div>
                                                                                    </div>
                                                                                    <div style={{ flex: 1, minWidth: 70, textAlign: 'center', background: '#fff1f0', borderRadius: 8, padding: '8px 4px' }}>
                                                                                        <div style={{ fontSize: 20, fontWeight: 700, color: '#ff4d4f' }}>{riskStats.severe}</div>
                                                                                        <div style={{ fontSize: 11, color: '#8c8c8c' }}>Critical</div>
                                                                                    </div>
                                                                                    <div style={{ flex: 1, minWidth: 70, textAlign: 'center', background: '#fff7e6', borderRadius: 8, padding: '8px 4px' }}>
                                                                                        <div style={{ fontSize: 20, fontWeight: 700, color: '#fa8c16' }}>{riskStats.high}</div>
                                                                                        <div style={{ fontSize: 11, color: '#8c8c8c' }}>High</div>
                                                                                    </div>
                                                                                    <div style={{ flex: 1, minWidth: 70, textAlign: 'center', background: '#f6ffed', borderRadius: 8, padding: '8px 4px' }}>
                                                                                        <div style={{ fontSize: 20, fontWeight: 700, color: '#52c41a' }}>{riskStats.medium + riskStats.low}</div>
                                                                                        <div style={{ fontSize: 11, color: '#8c8c8c' }}>Med/Low</div>
                                                                                    </div>
                                                                                </div>

                                                                                {/* Risk List */}
                                                                                {linkedRisks.length > 0 ? (
                                                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                                                        {linkedRisks.map((risk: any) => {
                                                                                            const severityColors: Record<string, string> = { 'Severe': 'red', 'Critical': 'red', 'High': 'orange', 'Medium': 'gold', 'Low': 'green' };
                                                                                            return (
                                                                                                <div key={risk.id} style={{
                                                                                                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                                                                                    padding: '8px 12px', background: '#fafafa', borderRadius: 6, border: '1px solid #f0f0f0',
                                                                                                }}>
                                                                                                    <div style={{ flex: 1, minWidth: 0 }}>
                                                                                                        <div style={{ fontWeight: 500, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                                                            {risk.risk_code ? `${risk.risk_code}: ` : ''}{risk.risk_category_name}
                                                                                                        </div>
                                                                                                        {risk.risk_category_description && (
                                                                                                            <div style={{ fontSize: 11, color: '#8c8c8c', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                                                                {risk.risk_category_description}
                                                                                                            </div>
                                                                                                        )}
                                                                                                    </div>
                                                                                                    <div style={{ display: 'flex', gap: 4, marginLeft: 8, flexShrink: 0 }}>
                                                                                                        {risk.risk_severity && <Tag color={severityColors[risk.risk_severity] || 'default'}>{risk.risk_severity}</Tag>}
                                                                                                        {risk.risk_status && <Tag color="blue">{risk.risk_status}</Tag>}
                                                                                                    </div>
                                                                                                </div>
                                                                                            );
                                                                                        })}
                                                                                    </div>
                                                                                ) : (
                                                                                    <Empty description="No risks linked to this asset." image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ margin: '24px 0' }} />
                                                                                )}
                                                                            </div>
                                                                        ),
                                                                    },
                                                                    {
                                                                        key: 'profile',
                                                                        label: (
                                                                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                                                <SafetyCertificateOutlined />
                                                                                Asset Profile
                                                                            </span>
                                                                        ),
                                                                        children: (
                                                                            <div style={{ paddingBottom: 16 }}>
                                                                                <div style={{ display: 'flex', gap: '8px', marginBottom: 16, flexWrap: 'wrap' }}>
                                                                                    <Tag color="red">{linkedRisks.length} Risk{linkedRisks.length !== 1 ? 's' : ''}</Tag>
                                                                                </div>

                                                                                {selectedAssetObj.asset_type_name && (
                                                                                    <div style={{ marginBottom: 16 }}>
                                                                                        <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Asset Type</div>
                                                                                        <div style={{ fontSize: 13, color: '#262626' }}>{selectedAssetObj.asset_type_name}</div>
                                                                                    </div>
                                                                                )}

                                                                                {selectedAssetObj.version && (
                                                                                    <div style={{ marginBottom: 16 }}>
                                                                                        <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Version</div>
                                                                                        <Tag color="blue">v{selectedAssetObj.version}</Tag>
                                                                                    </div>
                                                                                )}

                                                                                {(selectedAssetObj as any).asset_status_name && (
                                                                                    <div style={{ marginBottom: 16 }}>
                                                                                        <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Status</div>
                                                                                        <Tag color="green">{(selectedAssetObj as any).asset_status_name}</Tag>
                                                                                    </div>
                                                                                )}

                                                                                {(selectedAssetObj as any).description && (
                                                                                    <div style={{ marginBottom: 16 }}>
                                                                                        <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Description</div>
                                                                                        <div style={{ fontSize: 13, color: '#262626', lineHeight: 1.6 }}>{(selectedAssetObj as any).description}</div>
                                                                                    </div>
                                                                                )}

                                                                                {(selectedAssetObj as any).overall_asset_value !== undefined && (selectedAssetObj as any).overall_asset_value !== null && (
                                                                                    <div style={{ marginBottom: 16 }}>
                                                                                        <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Overall Asset Value</div>
                                                                                        <Progress
                                                                                            percent={Math.round(((selectedAssetObj as any).overall_asset_value / 5) * 100)}
                                                                                            strokeColor={(selectedAssetObj as any).overall_asset_value >= 4 ? '#ff4d4f' : (selectedAssetObj as any).overall_asset_value >= 3 ? '#faad14' : '#52c41a'}
                                                                                            format={() => `${(selectedAssetObj as any).overall_asset_value}/5`}
                                                                                            size="small"
                                                                                        />
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
                                                                                    <div style={{ fontSize: 13, color: '#262626' }}>
                                                                                        Import risks from the template library and link them to this asset to track risk exposure.
                                                                                    </div>
                                                                                </div>

                                                                                {/* Risk Template Categories — filtered by keyword relevance */}
                                                                                {(() => {
                                                                                    const assetSourceTexts = [selectedAssetObj.name, selectedAssetObj.asset_type_name, (selectedAssetObj as any).description];
                                                                                    const { relevant: relevantCats, other: otherCats } = filterByRelevance(
                                                                                        riskTemplateCategories,
                                                                                        assetSourceTexts,
                                                                                        (cat) => [cat.name, cat.description]
                                                                                    );
                                                                                    const renderCategoryPanel = (cats: typeof riskTemplateCategories) => cats.map(cat => ({
                                                                                        key: cat.id,
                                                                                        label: (
                                                                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                                                                                                <span style={{ fontWeight: 500, fontSize: 13 }}>{cat.name}</span>
                                                                                                <Tag color="blue" style={{ marginLeft: 8 }}>{cat.risk_count} risks</Tag>
                                                                                            </div>
                                                                                        ),
                                                                                        children: (
                                                                                            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                                                                {riskTemplateRisks[cat.id] ? (
                                                                                                    riskTemplateRisks[cat.id].map((risk, idx) => (
                                                                                                        <div key={`${risk.risk_code}-${idx}`} style={{
                                                                                                            border: '1px solid #f0f0f0',
                                                                                                            borderRadius: 8,
                                                                                                            padding: '12px 16px',
                                                                                                            display: 'flex',
                                                                                                            alignItems: 'center',
                                                                                                            justifyContent: 'space-between',
                                                                                                            gap: 12,
                                                                                                        }}>
                                                                                                            <div style={{ flex: 1, minWidth: 0 }}>
                                                                                                                <div style={{ fontWeight: 500, fontSize: 13 }}>{risk.risk_category_name}</div>
                                                                                                                {risk.risk_category_description && (
                                                                                                                    <div style={{ fontSize: 11, color: '#8c8c8c', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                                                                                        {risk.risk_category_description}
                                                                                                                    </div>
                                                                                                                )}
                                                                                                            </div>
                                                                                                            <Button
                                                                                                                type="primary"
                                                                                                                ghost
                                                                                                                size="small"
                                                                                                                loading={assetRecommendationLoading[`${cat.id}-${risk.risk_code}`]}
                                                                                                                onClick={() => handleImportAndLinkRiskRecommendation(cat.id, risk)}
                                                                                                                style={{ flexShrink: 0 }}
                                                                                                            >
                                                                                                                Import & Link
                                                                                                            </Button>
                                                                                                        </div>
                                                                                                    ))
                                                                                                ) : (
                                                                                                    <div style={{ textAlign: 'center', padding: 16, color: '#8c8c8c' }}>Loading risks...</div>
                                                                                                )}
                                                                                            </div>
                                                                                        ),
                                                                                    }));

                                                                                    if (riskTemplateCategories.length === 0) {
                                                                                        return <Empty description="No risk templates available" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ margin: '24px 0' }} />;
                                                                                    }

                                                                                    return (
                                                                                        <>
                                                                                            {relevantCats.length > 0 ? (
                                                                                                <>
                                                                                                    <Collapse
                                                                                                        accordion
                                                                                                        size="small"
                                                                                                        onChange={(key) => {
                                                                                                            const categoryId = Array.isArray(key) ? key[0] : key;
                                                                                                            if (categoryId && !riskTemplateRisks[categoryId]) {
                                                                                                                fetchRiskTemplateRisks(categoryId);
                                                                                                            }
                                                                                                        }}
                                                                                                        items={renderCategoryPanel(relevantCats)}
                                                                                                    />
                                                                                                    {otherCats.length > 0 && (
                                                                                                        <Collapse size="small" style={{ marginTop: 8 }} items={[{
                                                                                                            key: 'other-cats',
                                                                                                            label: <span style={{ fontSize: 12, color: '#8c8c8c' }}>Other risk categories ({otherCats.length})</span>,
                                                                                                            children: (
                                                                                                                <Collapse
                                                                                                                    accordion
                                                                                                                    size="small"
                                                                                                                    onChange={(key) => {
                                                                                                                        const categoryId = Array.isArray(key) ? key[0] : key;
                                                                                                                        if (categoryId && !riskTemplateRisks[categoryId]) {
                                                                                                                            fetchRiskTemplateRisks(categoryId);
                                                                                                                        }
                                                                                                                    }}
                                                                                                                    items={renderCategoryPanel(otherCats)}
                                                                                                                />
                                                                                                            ),
                                                                                                        }]} />
                                                                                                    )}
                                                                                                </>
                                                                                            ) : (
                                                                                                <Collapse
                                                                                                    accordion
                                                                                                    size="small"
                                                                                                    onChange={(key) => {
                                                                                                        const categoryId = Array.isArray(key) ? key[0] : key;
                                                                                                        if (categoryId && !riskTemplateRisks[categoryId]) {
                                                                                                            fetchRiskTemplateRisks(categoryId);
                                                                                                        }
                                                                                                    }}
                                                                                                    items={renderCategoryPanel(riskTemplateCategories)}
                                                                                                />
                                                                                            )}
                                                                                        </>
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
                                                description="Select an asset to manage its risk connections"
                                                style={{ marginTop: 60 }}
                                            />
                                        )}
                                    </div>
                                    );
                                })(),
                            },
                        ]}
                    />

                    {/* Asset Modal */}
                    <Modal
                        title={
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {selectedAsset ? <EditOutlined style={{ color: '#1890ff' }} /> : <PlusOutlined style={{ color: '#52c41a' }} />}
                                <span>{selectedAsset ? 'Edit Asset' : 'Add New Asset'}</span>
                            </div>
                        }
                        open={showAssetModal}
                        onCancel={() => {
                            setShowAssetModal(false);
                            clearAssetForm();
                        }}
                        footer={
                            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                {selectedAsset && (
                                    <button
                                        className="delete-button"
                                        onClick={handleDeleteAsset}
                                        style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f', color: 'white' }}
                                    >
                                        Delete Asset
                                    </button>
                                )}
                                <button
                                    className="secondary-button"
                                    onClick={() => {
                                        setShowAssetModal(false);
                                        clearAssetForm();
                                    }}
                                >
                                    Cancel
                                </button>
                                <button className="add-button" onClick={handleSaveAsset}>
                                    {selectedAsset ? 'Update Asset' : 'Save Asset'}
                                </button>
                            </div>
                        }
                        width={800}
                    >
                        <Tabs activeKey={assetModalTab} onChange={setAssetModalTab} items={[
                            {
                                key: 'details',
                                label: 'Details',
                                children: (
                                    <>
                                        {/* Row 1: Name and Version */}
                                        <div className="form-row">
                                            <div className="form-group">
                                                <label className="form-label required">Asset Name</label>
                                                <Input
                                                    placeholder="Enter asset name"
                                                    value={assetName}
                                                    onChange={(e) => setAssetName(e.target.value)}
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label className="form-label">Version</label>
                                                <Input
                                                    placeholder="Enter version"
                                                    value={assetVersion}
                                                    onChange={(e) => setAssetVersion(e.target.value)}
                                                />
                                            </div>
                                        </div>

                                        {/* Row 2: Asset Type and Status */}
                                        <div className="form-row">
                                            <div className="form-group">
                                                <label className="form-label required">Asset Type</label>
                                                <Select
                                                    showSearch
                                                    placeholder="Select asset type"
                                                    options={assetTypeOptions}
                                                    value={assetTypeId}
                                                    onChange={(value) => setAssetTypeId(value)}
                                                    filterOption={(input, option) => (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())}
                                                    style={{ width: '100%' }}
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label className="form-label">Status</label>
                                                <Select
                                                    showSearch
                                                    placeholder="Select status"
                                                    options={statusOptions}
                                                    value={assetStatusId}
                                                    onChange={(value) => setAssetStatusId(value)}
                                                    filterOption={(input, option) => (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())}
                                                    style={{ width: '100%' }}
                                                    allowClear
                                                />
                                            </div>
                                        </div>

                                        {/* Row 3: Economic Operator and Criticality */}
                                        <div className="form-row">
                                            <div className="form-group">
                                                <label className="form-label">Economic Operator</label>
                                                <Select
                                                    showSearch
                                                    placeholder="Select economic operator"
                                                    options={operatorOptions}
                                                    value={economicOperatorId}
                                                    onChange={(value) => setEconomicOperatorId(value)}
                                                    filterOption={(input, option) => (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())}
                                                    style={{ width: '100%' }}
                                                    allowClear
                                                />
                                            </div>
                                            {craMode !== null && (
                                            <div className="form-group">
                                                <label className="form-label">Criticality</label>
                                                <Select
                                                    showSearch
                                                    placeholder="Select criticality"
                                                    options={criticalityOptions}
                                                    value={criticalityId}
                                                    onChange={(value) => setCriticalityId(value)}
                                                    filterOption={filterCriticalityOption}
                                                    style={{ width: '100%' }}
                                                    allowClear
                                                />
                                            </div>
                                            )}
                                        </div>

                                        {/* Row 4: License and IP Address */}
                                        <div className="form-row">
                                            <div className="form-group">
                                                <label className="form-label">License</label>
                                                <Input
                                                    placeholder="Enter license information"
                                                    value={assetLicense}
                                                    onChange={(e) => setAssetLicense(e.target.value)}
                                                />
                                            </div>
                                            <div className="form-group">
                                                <label className="form-label">IP Address / IP Range / URL</label>
                                                <Input
                                                    placeholder="e.g., 192.168.1.1, 10.0.0.0/24, https://example.com"
                                                    value={assetIpAddress}
                                                    onChange={(e) => setAssetIpAddress(e.target.value)}
                                                />
                                            </div>
                                        </div>

                                        {/* Row 5: Justification */}
                                        <div className="form-row">
                                            <div className="form-group" style={{ width: '100%' }}>
                                                <label className="form-label">Justification</label>
                                                <TextArea
                                                    placeholder="Enter justification"
                                                    value={assetJustification}
                                                    onChange={(e) => setAssetJustification(e.target.value)}
                                                    rows={2}
                                                />
                                            </div>
                                        </div>

                                        {/* Row 6: Description */}
                                        <div className="form-row">
                                            <div className="form-group" style={{ width: '100%' }}>
                                                <label className="form-label">Description</label>
                                                <TextArea
                                                    placeholder="Enter asset description"
                                                    value={assetDescription}
                                                    onChange={(e) => setAssetDescription(e.target.value)}
                                                    rows={3}
                                                />
                                            </div>
                                        </div>

                                        {/* Row 7: SBOM */}
                                        <div className="form-row">
                                            <div className="form-group" style={{ width: '100%' }}>
                                                <label className="form-label">SBOM (Software Bill of Materials)</label>
                                                <TextArea
                                                    placeholder="Enter SBOM details"
                                                    value={assetSbom}
                                                    onChange={(e) => setAssetSbom(e.target.value)}
                                                    rows={3}
                                                />
                                            </div>
                                        </div>
                                    </>
                                ),
                            },
                            {
                                key: 'cia',
                                label: 'CIA Matrix',
                                children: (
                                    <div>
                                        <div style={{ marginBottom: 16 }}>
                                            <Checkbox
                                                checked={assetInheritCia}
                                                onChange={(e) => setAssetInheritCia(e.target.checked)}
                                            >
                                                Inherit CIA defaults from asset type
                                            </Checkbox>
                                            {assetInheritCia && assetTypeId && (() => {
                                                const at = assetTypes.find(t => t.id === assetTypeId);
                                                if (at && !at.default_confidentiality && !at.default_integrity && !at.default_availability && !at.default_asset_value) {
                                                    return <div style={{ marginTop: 8, color: '#faad14', fontSize: 12 }}>No CIA defaults configured for this asset type. Edit the asset type to set defaults.</div>;
                                                }
                                                return null;
                                            })()}
                                        </div>

                                        {(() => {
                                            const effective = getEffectiveCiaValues();
                                            const isDisabled = assetInheritCia;
                                            return (
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                                                    <div>
                                                        <label className="form-label" style={{ marginBottom: 8, display: 'block' }}>Confidentiality</label>
                                                        <Radio.Group
                                                            value={effective.c}
                                                            onChange={(e) => { if (!isDisabled) setAssetConfidentiality(e.target.value); }}
                                                            buttonStyle="solid"
                                                            disabled={isDisabled}
                                                        >
                                                            <Radio.Button value="low">Low</Radio.Button>
                                                            <Radio.Button value="medium">Medium</Radio.Button>
                                                            <Radio.Button value="high">High</Radio.Button>
                                                        </Radio.Group>
                                                    </div>

                                                    <div>
                                                        <label className="form-label" style={{ marginBottom: 8, display: 'block' }}>Integrity</label>
                                                        <Radio.Group
                                                            value={effective.i}
                                                            onChange={(e) => { if (!isDisabled) setAssetIntegrity(e.target.value); }}
                                                            buttonStyle="solid"
                                                            disabled={isDisabled}
                                                        >
                                                            <Radio.Button value="low">Low</Radio.Button>
                                                            <Radio.Button value="medium">Medium</Radio.Button>
                                                            <Radio.Button value="high">High</Radio.Button>
                                                        </Radio.Group>
                                                    </div>

                                                    <div>
                                                        <label className="form-label" style={{ marginBottom: 8, display: 'block' }}>Availability</label>
                                                        <Radio.Group
                                                            value={effective.a}
                                                            onChange={(e) => { if (!isDisabled) setAssetAvailability(e.target.value); }}
                                                            buttonStyle="solid"
                                                            disabled={isDisabled}
                                                        >
                                                            <Radio.Button value="low">Low</Radio.Button>
                                                            <Radio.Button value="medium">Medium</Radio.Button>
                                                            <Radio.Button value="high">High</Radio.Button>
                                                        </Radio.Group>
                                                    </div>

                                                    <div>
                                                        <label className="form-label" style={{ marginBottom: 8, display: 'block' }}>Asset Value</label>
                                                        <Radio.Group
                                                            value={effective.av}
                                                            onChange={(e) => { if (!isDisabled) setAssetAssetValue(e.target.value); }}
                                                            buttonStyle="solid"
                                                            disabled={isDisabled}
                                                        >
                                                            <Radio.Button value="low">Low</Radio.Button>
                                                            <Radio.Button value="medium">Medium</Radio.Button>
                                                            <Radio.Button value="high">High</Radio.Button>
                                                        </Radio.Group>
                                                    </div>

                                                    <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: 16, display: 'flex', alignItems: 'center', gap: 12 }}>
                                                        <span style={{ fontWeight: 500 }}>Overall Asset Value (OAV):</span>
                                                        {(() => {
                                                            const oav = computeOav();
                                                            return oav
                                                                ? <Tag color={getCiaLevelColor(oav)} style={{ fontSize: 14, padding: '2px 12px' }}>{oav}</Tag>
                                                                : <span style={{ color: '#bfbfbf' }}>Not rated</span>;
                                                        })()}
                                                    </div>
                                                </div>
                                            );
                                        })()}
                                    </div>
                                ),
                            },
                        ]} />
                    </Modal>

                    {/* Asset Type Modal */}
                    <Modal
                        title={
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {selectedAssetType ? <EditOutlined style={{ color: '#1890ff' }} /> : <PlusOutlined style={{ color: '#52c41a' }} />}
                                <span>{selectedAssetType ? 'Edit Asset Type' : 'Add New Asset Type'}</span>
                            </div>
                        }
                        open={showAssetTypeModal}
                        onCancel={() => {
                            setShowAssetTypeModal(false);
                            clearAssetTypeForm();
                        }}
                        footer={
                            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                {selectedAssetType && selectedAssetType.asset_count === 0 && (
                                    <button
                                        className="delete-button"
                                        onClick={() => {
                                            handleDeleteAssetType(selectedAssetType);
                                            setShowAssetTypeModal(false);
                                            clearAssetTypeForm();
                                        }}
                                        style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f', color: 'white' }}
                                    >
                                        Delete Asset Type
                                    </button>
                                )}
                                <button
                                    className="secondary-button"
                                    onClick={() => {
                                        setShowAssetTypeModal(false);
                                        clearAssetTypeForm();
                                    }}
                                >
                                    Cancel
                                </button>
                                <button className="add-button" onClick={handleSaveAssetType}>
                                    {selectedAssetType ? 'Update Asset Type' : 'Save Asset Type'}
                                </button>
                            </div>
                        }
                        width={650}
                    >
                        <div className="form-row">
                            <div className="form-group" style={{ width: '100%' }}>
                                <label className="form-label required">Name</label>
                                <Input
                                    placeholder="Enter asset type name"
                                    value={assetTypeName}
                                    onChange={(e) => setAssetTypeName(e.target.value)}
                                />
                            </div>
                        </div>
                        <div className="form-row">
                            <div className="form-group" style={{ width: '100%' }}>
                                <label className="form-label">Icon</label>
                                <Select
                                    showSearch
                                    placeholder="Select an icon"
                                    options={availableIcons.map(icon => ({
                                        label: (
                                            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                {renderIcon(icon.value, { fontSize: '16px' })}
                                                {icon.label}
                                            </span>
                                        ),
                                        value: icon.value,
                                    }))}
                                    value={assetTypeIcon}
                                    onChange={(value) => setAssetTypeIcon(value)}
                                    filterOption={(input, option) => {
                                        const iconInfo = availableIcons.find(i => i.value === option?.value);
                                        return iconInfo ? iconInfo.label.toLowerCase().includes(input.toLowerCase()) : false;
                                    }}
                                    style={{ width: '100%' }}
                                    allowClear
                                />
                            </div>
                        </div>
                        <div className="form-row">
                            <div className="form-group" style={{ width: '100%' }}>
                                <label className="form-label">Description</label>
                                <TextArea
                                    placeholder="Enter asset type description"
                                    value={assetTypeDescription}
                                    onChange={(e) => setAssetTypeDescription(e.target.value)}
                                    rows={3}
                                />
                            </div>
                        </div>

                        {/* Default CIA Ratings */}
                        <div style={{ borderTop: '1px solid #f0f0f0', marginTop: 16, paddingTop: 16 }}>
                            <h4 style={{ margin: '0 0 12px 0', fontSize: 14, fontWeight: 500, color: '#595959' }}>Default CIA Ratings</h4>
                            <p style={{ margin: '0 0 16px 0', fontSize: 12, color: '#8c8c8c' }}>
                                These defaults will be inherited by assets of this type (unless overridden).
                            </p>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <span style={{ width: 100, fontSize: 13 }}>Confidentiality</span>
                                    <Radio.Group
                                        value={assetTypeDefaultC}
                                        onChange={(e) => setAssetTypeDefaultC(e.target.value)}
                                        buttonStyle="solid"
                                        size="small"
                                    >
                                        <Radio.Button value="low">Low</Radio.Button>
                                        <Radio.Button value="medium">Medium</Radio.Button>
                                        <Radio.Button value="high">High</Radio.Button>
                                    </Radio.Group>
                                    {assetTypeDefaultC && (
                                        <button
                                            onClick={() => setAssetTypeDefaultC(undefined)}
                                            style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#bfbfbf', fontSize: 12 }}
                                        >
                                            Clear
                                        </button>
                                    )}
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <span style={{ width: 100, fontSize: 13 }}>Integrity</span>
                                    <Radio.Group
                                        value={assetTypeDefaultI}
                                        onChange={(e) => setAssetTypeDefaultI(e.target.value)}
                                        buttonStyle="solid"
                                        size="small"
                                    >
                                        <Radio.Button value="low">Low</Radio.Button>
                                        <Radio.Button value="medium">Medium</Radio.Button>
                                        <Radio.Button value="high">High</Radio.Button>
                                    </Radio.Group>
                                    {assetTypeDefaultI && (
                                        <button
                                            onClick={() => setAssetTypeDefaultI(undefined)}
                                            style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#bfbfbf', fontSize: 12 }}
                                        >
                                            Clear
                                        </button>
                                    )}
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <span style={{ width: 100, fontSize: 13 }}>Availability</span>
                                    <Radio.Group
                                        value={assetTypeDefaultA}
                                        onChange={(e) => setAssetTypeDefaultA(e.target.value)}
                                        buttonStyle="solid"
                                        size="small"
                                    >
                                        <Radio.Button value="low">Low</Radio.Button>
                                        <Radio.Button value="medium">Medium</Radio.Button>
                                        <Radio.Button value="high">High</Radio.Button>
                                    </Radio.Group>
                                    {assetTypeDefaultA && (
                                        <button
                                            onClick={() => setAssetTypeDefaultA(undefined)}
                                            style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#bfbfbf', fontSize: 12 }}
                                        >
                                            Clear
                                        </button>
                                    )}
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                    <span style={{ width: 100, fontSize: 13 }}>Asset Value</span>
                                    <Radio.Group
                                        value={assetTypeDefaultAV}
                                        onChange={(e) => setAssetTypeDefaultAV(e.target.value)}
                                        buttonStyle="solid"
                                        size="small"
                                    >
                                        <Radio.Button value="low">Low</Radio.Button>
                                        <Radio.Button value="medium">Medium</Radio.Button>
                                        <Radio.Button value="high">High</Radio.Button>
                                    </Radio.Group>
                                    {assetTypeDefaultAV && (
                                        <button
                                            onClick={() => setAssetTypeDefaultAV(undefined)}
                                            style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#bfbfbf', fontSize: 12 }}
                                        >
                                            Clear
                                        </button>
                                    )}
                                </div>
                            </div>
                        </div>
                    </Modal>
                </div>
            </div>
        </div>
    );
};

export default AssetsPage;
