import { useState, useEffect } from 'react';
import { Tabs, Checkbox, Select, Button, Collapse, Spin, Tag, Tooltip, Empty, notification } from 'antd';
import {
    ImportOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    InfoCircleOutlined,
    DownOutlined,
    UpOutlined,
    DatabaseOutlined
} from '@ant-design/icons';
import useRiskStore, { RiskTemplateItem } from '../store/useRiskStore';

interface RiskTemplatesSectionProps {
    assetCategories: Array<{ id: string; name: string }>;
    riskSeverities: Array<{ id: string; risk_severity_name: string }>;
    riskStatuses: Array<{ id: string; risk_status_name: string }>;
    onImportComplete: () => void;
    isEmbedded?: boolean; // When true, renders without the Collapse wrapper
}

const RiskTemplatesSection = ({
    assetCategories,
    riskSeverities,
    riskStatuses,
    onImportComplete,
    isEmbedded = false
}: RiskTemplatesSectionProps) => {
    const [api, contextHolder] = notification.useNotification();

    // Store access
    const {
        riskTemplateCategories,
        riskTemplateRisks,
        fetchRiskTemplateCategories,
        fetchRiskTemplateRisks,
        importRiskTemplates
    } = useRiskStore();

    // UI state
    const [isExpanded, setIsExpanded] = useState(false);
    const [activeTab, setActiveTab] = useState<string>('');
    const [loading, setLoading] = useState(false);
    const [loadingRisks, setLoadingRisks] = useState(false);
    const [importing, setImporting] = useState(false);

    // Selection state - track selected risks by category
    const [selectedRisks, setSelectedRisks] = useState<Record<string, RiskTemplateItem[]>>({});

    // Default values configuration
    const [assetCategoryId, setAssetCategoryId] = useState<string>('');
    const [defaultLikelihood, setDefaultLikelihood] = useState<string>('');
    const [defaultSeverity, setDefaultSeverity] = useState<string>('');
    const [defaultResidualRisk, setDefaultResidualRisk] = useState<string>('');
    const [defaultStatus, setDefaultStatus] = useState<string>('');

    // Load template categories on mount
    useEffect(() => {
        const loadCategories = async () => {
            setLoading(true);
            await fetchRiskTemplateCategories();
            setLoading(false);
        };
        loadCategories();
    }, [fetchRiskTemplateCategories]);

    // Set default values when severities and statuses are loaded
    useEffect(() => {
        if (riskSeverities.length > 0 && !defaultLikelihood) {
            const medium = riskSeverities.find(s => s.risk_severity_name.toLowerCase() === 'medium');
            if (medium) {
                setDefaultLikelihood(medium.id);
                setDefaultSeverity(medium.id);
                setDefaultResidualRisk(medium.id);
            }
        }
    }, [riskSeverities, defaultLikelihood]);

    useEffect(() => {
        if (riskStatuses.length > 0 && !defaultStatus) {
            const accept = riskStatuses.find(s => s.risk_status_name.toLowerCase() === 'accept');
            if (accept) {
                setDefaultStatus(accept.id);
            }
        }
    }, [riskStatuses, defaultStatus]);

    // Set first category as active when categories load
    useEffect(() => {
        if (riskTemplateCategories.length > 0 && !activeTab) {
            setActiveTab(riskTemplateCategories[0].id);
        }
    }, [riskTemplateCategories, activeTab]);

    // Load risks when tab changes
    useEffect(() => {
        const loadRisks = async () => {
            if (activeTab && !riskTemplateRisks[activeTab]) {
                setLoadingRisks(true);
                await fetchRiskTemplateRisks(activeTab);
                setLoadingRisks(false);
            }
        };
        if (activeTab) {
            loadRisks();
        }
    }, [activeTab, fetchRiskTemplateRisks, riskTemplateRisks]);

    // Get risks for current category
    const currentRisks = activeTab ? (riskTemplateRisks[activeTab] || []) : [];
    const currentSelected = activeTab ? (selectedRisks[activeTab] || []) : [];

    const getRiskKey = (risk: RiskTemplateItem) => {
        if (risk.risk_code) {
            return risk.risk_code;
        }
        return `${risk.risk_category_name}||${risk.risk_category_description}||${risk.risk_potential_impact}||${risk.risk_control}`;
    };

    // Check if a risk is selected
    const isRiskSelected = (risk: RiskTemplateItem) => {
        const riskKey = getRiskKey(risk);
        return currentSelected.some(r => getRiskKey(r) === riskKey);
    };

    // Toggle risk selection
    const toggleRiskSelection = (risk: RiskTemplateItem) => {
        setSelectedRisks(prev => {
            const categoryRisks = prev[activeTab] || [];
            const riskKey = getRiskKey(risk);
            const isSelected = categoryRisks.some(r => getRiskKey(r) === riskKey);

            if (isSelected) {
                return {
                    ...prev,
                    [activeTab]: categoryRisks.filter(r => getRiskKey(r) !== riskKey)
                };
            } else {
                return {
                    ...prev,
                    [activeTab]: [...categoryRisks, risk]
                };
            }
        });
    };

    // Select all risks in current category
    const selectAll = () => {
        setSelectedRisks(prev => ({
            ...prev,
            [activeTab]: [...currentRisks]
        }));
    };

    // Deselect all risks in current category
    const deselectAll = () => {
        setSelectedRisks(prev => ({
            ...prev,
            [activeTab]: []
        }));
    };

    // Get total selected across all categories
    const getTotalSelected = () => {
        return Object.values(selectedRisks).reduce((sum, risks) => sum + risks.length, 0);
    };

    // Handle import
    const handleImport = async () => {
        if (!assetCategoryId) {
            api.error({
                message: 'Import Failed',
                description: 'Please select an Asset Category before importing',
                duration: 4
            });
            return;
        }

        if (currentSelected.length === 0) {
            api.error({
                message: 'Import Failed',
                description: 'Please select at least one risk to import',
                duration: 4
            });
            return;
        }

        if (!defaultLikelihood || !defaultSeverity || !defaultResidualRisk || !defaultStatus) {
            api.error({
                message: 'Import Failed',
                description: 'Please configure all default values before importing',
                duration: 4
            });
            return;
        }

        setImporting(true);

        const result = await importRiskTemplates(
            activeTab,
            currentSelected,
            assetCategoryId,
            defaultLikelihood,
            defaultSeverity,
            defaultResidualRisk,
            defaultStatus
        );

        setImporting(false);

        if (result.success) {
            api.success({
                message: 'Import Successful',
                description: result.message,
                duration: 4
            });
            // Clear selections for this category
            setSelectedRisks(prev => ({
                ...prev,
                [activeTab]: []
            }));
            // Refresh the risks list
            onImportComplete();
        } else {
            api.error({
                message: 'Import Failed',
                description: result.message,
                duration: 4
            });
        }
    };

    // Severity options
    const severityOptions = riskSeverities.map(s => ({
        label: s.risk_severity_name,
        value: s.id
    }));

    // Status options
    const statusOptions = riskStatuses.map(s => ({
        label: s.risk_status_name,
        value: s.id
    }));

    // Asset category options
    const assetCategoryOptions = assetCategories.map(p => ({
        label: p.name,
        value: p.id
    }));

    // Render risk item
    const renderRiskItem = (risk: RiskTemplateItem) => (
        <div
            key={getRiskKey(risk)}
            className="risk-template-item"
            style={{
                padding: '12px 16px',
                borderBottom: '1px solid #f0f0f0',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                cursor: 'pointer',
                backgroundColor: isRiskSelected(risk) ? '#e6f7ff' : 'transparent',
                transition: 'background-color 0.2s'
            }}
            onClick={() => toggleRiskSelection(risk)}
        >
            <Checkbox
                checked={isRiskSelected(risk)}
                onChange={() => toggleRiskSelection(risk)}
                onClick={(e) => e.stopPropagation()}
            />
            <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 500, marginBottom: '4px' }}>
                    {risk.risk_category_name}
                </div>
                <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px' }}>
                    {risk.risk_category_description.length > 150
                        ? `${risk.risk_category_description.substring(0, 150)}...`
                        : risk.risk_category_description}
                </div>
                {risk.risk_control && (
                    <div style={{ fontSize: '11px', color: '#999' }}>
                        <strong>Controls:</strong> {risk.risk_control.length > 100
                            ? `${risk.risk_control.substring(0, 100)}...`
                            : risk.risk_control}
                    </div>
                )}
            </div>
            <Tooltip title="View details">
                <InfoCircleOutlined style={{ color: '#1890ff', cursor: 'pointer' }} />
            </Tooltip>
        </div>
    );

    // Tab items
    const tabItems = riskTemplateCategories.map(category => ({
        key: category.id,
        label: (
            <span>
                {category.name}
                <Tag color="blue" style={{ marginLeft: '8px' }}>
                    {selectedRisks[category.id]?.length || 0}/{category.risk_count}
                </Tag>
            </span>
        ),
        children: (
            <div>
                {loadingRisks && activeTab === category.id ? (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                        <Spin size="large" />
                        <div style={{ marginTop: '16px', color: '#666' }}>Loading risks...</div>
                    </div>
                ) : currentRisks.length === 0 ? (
                    <Empty description="No risks in this category" />
                ) : (
                    <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                        {currentRisks.map(renderRiskItem)}
                    </div>
                )}
            </div>
        )
    }));

    // Render the main content (used both for embedded and collapsible modes)
    const renderContent = () => {
        if (loading) {
            return (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: '16px', color: '#666' }}>Loading template categories...</div>
                </div>
            );
        }

        return (
            <div>
                {/* Configuration Panel */}
                <div style={{
                    backgroundColor: '#fafafa',
                    padding: '16px',
                    borderRadius: '8px',
                    marginBottom: '16px',
                    border: '1px solid #e8e8e8'
                }}>
                    <div style={{ fontWeight: 500, marginBottom: '12px' }}>
                        Default Values for Imported Risks
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
                                Asset Category <span style={{ color: '#ff4d4f' }}>*</span>
                            </label>
                            <Select
                                placeholder="Select asset category"
                                options={assetCategoryOptions}
                                value={assetCategoryId || undefined}
                                onChange={setAssetCategoryId}
                                style={{ width: '100%' }}
                                showSearch
                                filterOption={(input, option) =>
                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                }
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
                                Likelihood
                            </label>
                            <Select
                                placeholder="Select likelihood"
                                options={severityOptions}
                                value={defaultLikelihood || undefined}
                                onChange={setDefaultLikelihood}
                                style={{ width: '100%' }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
                                Severity
                            </label>
                            <Select
                                placeholder="Select severity"
                                options={severityOptions}
                                value={defaultSeverity || undefined}
                                onChange={setDefaultSeverity}
                                style={{ width: '100%' }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
                                Residual Risk
                            </label>
                            <Select
                                placeholder="Select residual risk"
                                options={severityOptions}
                                value={defaultResidualRisk || undefined}
                                onChange={setDefaultResidualRisk}
                                style={{ width: '100%' }}
                            />
                        </div>
                        <div>
                            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
                                Status
                            </label>
                            <Select
                                placeholder="Select status"
                                options={statusOptions}
                                value={defaultStatus || undefined}
                                onChange={setDefaultStatus}
                                style={{ width: '100%' }}
                            />
                        </div>
                    </div>
                </div>

                {/* Category Description */}
                {activeTab && (
                    <div style={{ marginBottom: '12px', color: '#666', fontSize: '13px' }}>
                        {riskTemplateCategories.find(c => c.id === activeTab)?.description}
                    </div>
                )}

                {/* Tabs with risk lists */}
                <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    items={tabItems}
                    tabBarExtraContent={{
                        right: (
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <Button size="small" onClick={selectAll}>
                                    <CheckCircleOutlined /> Select All
                                </Button>
                                <Button size="small" onClick={deselectAll}>
                                    <CloseCircleOutlined /> Deselect All
                                </Button>
                            </div>
                        )
                    }}
                />

                {/* Import Button */}
                <div style={{
                    marginTop: '16px',
                    paddingTop: '16px',
                    borderTop: '1px solid #e8e8e8',
                    display: 'flex',
                    justifyContent: 'flex-end',
                    alignItems: 'center',
                    gap: '12px'
                }}>
                    <span style={{ color: '#666', fontSize: '13px' }}>
                        {currentSelected.length} risk(s) selected from "{riskTemplateCategories.find(c => c.id === activeTab)?.name}"
                    </span>
                    <Button
                        type="primary"
                        icon={<ImportOutlined />}
                        onClick={handleImport}
                        loading={importing}
                        disabled={currentSelected.length === 0 || !assetCategoryId}
                    >
                        Import Selected Risks ({currentSelected.length})
                    </Button>
                </div>
            </div>
        );
    };

    // Embedded mode - render content directly without collapse
    if (isEmbedded) {
        return (
            <div className="risk-templates-section">
                {contextHolder}
                {renderContent()}
            </div>
        );
    }

    // Collapsible mode - render with Collapse wrapper
    return (
        <div className="risk-templates-section">
            {contextHolder}
            <Collapse
                activeKey={isExpanded ? ['1'] : []}
                onChange={() => setIsExpanded(!isExpanded)}
                style={{ marginBottom: '24px' }}
                items={[
                    {
                        key: '1',
                        label: (
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <DatabaseOutlined style={{ fontSize: '18px', color: '#1890ff' }} />
                                    <span style={{ fontWeight: 500, fontSize: '16px' }}>Risk Templates Library</span>
                                    <Tag color="purple">{riskTemplateCategories.reduce((sum, c) => sum + c.risk_count, 0)} templates</Tag>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    {getTotalSelected() > 0 && (
                                        <Tag color="green">{getTotalSelected()} selected</Tag>
                                    )}
                                    {isExpanded ? <UpOutlined /> : <DownOutlined />}
                                </div>
                            </div>
                        ),
                        children: renderContent()
                    }
                ]}
            />
        </div>
    );
};

export default RiskTemplatesSection;
