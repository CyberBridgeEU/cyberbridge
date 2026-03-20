import React, {useEffect, useState, useMemo, useCallback} from 'react';
import {Select, notification, Tag, Empty, Spin, Checkbox} from "antd";
import {AppstoreOutlined, CheckCircleOutlined, PlusCircleOutlined, DatabaseOutlined, RobotOutlined, ReloadOutlined} from "@ant-design/icons";
import Sidebar from "../components/Sidebar.tsx";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import useUserStore from "../store/useUserStore.ts";
import useAuthStore from "../store/useAuthStore.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import ExcelFrameworkSeedSection from "../components/ExcelFrameworkSeedSection.tsx";
import {
    AddFrameworkFromTemplateInfo,
    ManageSourcesInfo
} from "../constants/infoContent.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

const ManageFrameworks: React.FC = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Global State
    const {current_user} = useUserStore();
    const {frameworks, fetchFrameworks, createFramework, deleteFramework, frameworkTemplates, fetchFrameworkTemplates, seedFrameworkTemplate, loading: frameworkLoading} = useFrameworksStore();

    // Local State
    const [newFrameworkName, setNewFrameworkName] = useState<string>('');
    const [newFrameworkDescription, setNewFrameworkDescription] = useState<string>('');
    const [frameworkSelectedIds, setFrameworkSelectedIds] = useState<string[]>([]);
    const [api, contextHolder] = notification.useNotification();
    const [frameworkNameError, setFrameworkNameError] = useState<string>('');
    const [selectedTemplateId, setSelectedTemplateId] = useState<string>('');
    const [wireConnections, setWireConnections] = useState<boolean>(true);
    const [allowedScopeTypes, setAllowedScopeTypes] = useState<string[]>([]);
    const [scopeSelectionMode, setScopeSelectionMode] = useState<string>('optional');

    // AI Policy Aligner State
    const [selectedAlignmentFramework, setSelectedAlignmentFramework] = useState<string>('');
    const [alignmentStatus, setAlignmentStatus] = useState<{has_alignments: boolean, alignment_count: number, last_updated: string | null} | null>(null);
    const [isLoadingAlignment, setIsLoadingAlignment] = useState<boolean>(false);
    const [isGeneratingAlignment, setIsGeneratingAlignment] = useState<boolean>(false);
    const [aiPolicyAlignerEnabled, setAiPolicyAlignerEnabled] = useState<boolean>(false);
    const { getAuthHeader } = useAuthStore();

    // Fetch AI Policy Aligner global settings (super_admin controlled)
    const fetchAiPolicyAlignerSettings = useCallback(async () => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/settings/llm`,
                {
                    headers: {
                        ...getAuthHeader()
                    }
                }
            );
            if (response.ok) {
                const data = await response.json();
                setAiPolicyAlignerEnabled(data.ai_policy_aligner_enabled ?? false);
            }
        } catch (error) {
            console.error('Error fetching AI Policy Aligner settings:', error);
        }
    }, [getAuthHeader]);

    // On Component Mount
    useEffect(() => {
        fetchFrameworks();
        fetchFrameworkTemplates();
        // Fetch AI Policy Aligner global settings
        fetchAiPolicyAlignerSettings();
    }, [fetchAiPolicyAlignerSettings]);

    // Fetch alignment status for a framework
    const fetchAlignmentStatus = useCallback(async (frameworkId: string) => {
        if (!frameworkId) {
            setAlignmentStatus(null);
            return;
        }
        setIsLoadingAlignment(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/policy-aligner/status/${frameworkId}`,
                {
                    headers: {
                        ...getAuthHeader()
                    }
                }
            );
            if (response.ok) {
                const data = await response.json();
                setAlignmentStatus(data);
            } else {
                setAlignmentStatus(null);
            }
        } catch (error) {
            console.error('Error fetching alignment status:', error);
            setAlignmentStatus(null);
        } finally {
            setIsLoadingAlignment(false);
        }
    }, [getAuthHeader]);

    // Handle framework selection for alignment
    const handleAlignmentFrameworkChange = (frameworkId: string) => {
        setSelectedAlignmentFramework(frameworkId);
        if (frameworkId) {
            fetchAlignmentStatus(frameworkId);
        } else {
            setAlignmentStatus(null);
        }
    };

    // Generate policy alignments
    const handleGenerateAlignments = async () => {
        if (!selectedAlignmentFramework) {
            api.error({
                message: 'No Framework Selected',
                description: 'Please select a framework to generate alignments.',
                duration: 4,
            });
            return;
        }

        setIsGeneratingAlignment(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/policy-aligner/align`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...getAuthHeader()
                    },
                    body: JSON.stringify({
                        framework_id: selectedAlignmentFramework
                    })
                }
            );

            if (response.ok) {
                const data = await response.json();
                api.success({
                    message: 'Alignments Generated',
                    description: `Successfully created ${data.alignments_created} policy alignments.`,
                    duration: 4,
                });
                // Refresh alignment status
                fetchAlignmentStatus(selectedAlignmentFramework);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to generate alignments');
            }
        } catch (error) {
            api.error({
                message: 'Generation Failed',
                description: error instanceof Error ? error.message : 'Failed to generate policy alignments. Please try again.',
                duration: 4,
            });
        } finally {
            setIsGeneratingAlignment(false);
        }
    };

    // Delete alignments for re-run
    const handleDeleteAlignments = async () => {
        if (!selectedAlignmentFramework) return;

        if (!window.confirm('Are you sure you want to delete existing alignments? You can re-generate them afterward.')) {
            return;
        }

        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/policy-aligner/alignments/${selectedAlignmentFramework}`,
                {
                    method: 'DELETE',
                    headers: {
                        ...getAuthHeader()
                    }
                }
            );

            if (response.ok) {
                api.success({
                    message: 'Alignments Deleted',
                    description: 'Existing alignments have been removed. You can now re-generate them.',
                    duration: 4,
                });
                setAlignmentStatus(null);
                fetchAlignmentStatus(selectedAlignmentFramework);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to delete alignments');
            }
        } catch (error) {
            api.error({
                message: 'Deletion Failed',
                description: error instanceof Error ? error.message : 'Failed to delete alignments. Please try again.',
                duration: 4,
            });
        }
    };

    // Framework options for selection
    const options = frameworks.map(framework => ({
        value: framework.id,
        label: framework.organisation_domain ? `${framework.name} (${framework.organisation_domain})` : framework.name,
    }));

    // Scope type options
    const scopeTypeOptions = [
        { value: 'Product', label: 'Asset / Product' },
        { value: 'Organization', label: 'Organization' },
        { value: 'Other', label: 'Other' },
        { value: 'Asset', label: 'Asset / Product (Reserved)', disabled: true },
        { value: 'Project', label: 'Project (Coming Soon)', disabled: true },
        { value: 'Process', label: 'Process (Coming Soon)', disabled: true }
    ];

    // Scope selection mode options
    const scopeSelectionModeOptions = [
        { value: 'optional', label: 'Optional' },
        { value: 'required', label: 'Required' }
    ];

    // Compute available templates (not yet seeded) vs active frameworks
    const availableTemplates = useMemo(() => {
        const activeFrameworkNames = frameworks.map(fw => fw.name.toLowerCase().trim());
        return frameworkTemplates.filter(template =>
            !activeFrameworkNames.includes(template.name.toLowerCase().trim())
        );
    }, [frameworks, frameworkTemplates]);

    // Check if the currently selected template has chain links available
    const selectedTemplateHasChainLinks = useMemo(() => {
        if (!selectedTemplateId) return false;
        const template = frameworkTemplates.find(t => t.id === selectedTemplateId);
        return template?.has_chain_links ?? false;
    }, [selectedTemplateId, frameworkTemplates]);

    // Filter template options to only show available (not yet seeded) templates
    const availableTemplateOptions = availableTemplates.map(template => ({
        value: template.id,
        label: template.name,
    }));

    // Validation Functions
    const validateFrameworkName = (name: string): string => {
        if (!name || name.trim() === '') {
            return '';
        }
        const existingFramework = frameworks.find(fw =>
            fw.name.toLowerCase() === name.trim().toLowerCase()
        );
        return existingFramework ? `Framework name "${name}" already exists in your organization` : '';
    };

    const handleFrameworkNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setNewFrameworkName(value);
        setFrameworkNameError(validateFrameworkName(value));
    };

    const handleTemplateChange = (value: string) => {
        setSelectedTemplateId(value);
        setWireConnections(true);
    };

    const handleSeedTemplate = async () => {
        if (!selectedTemplateId) {
            api.error({
                message: 'No Template Selected',
                description: 'Please select a framework template to seed!',
                duration: 4,
            });
            return;
        }

        const result = await seedFrameworkTemplate(selectedTemplateId, wireConnections);
        if (result.success) {
            const chainLinksNote = selectedTemplateHasChainLinks
                ? (wireConnections
                    ? ' Chain links (risks, controls, policies) were included.'
                    : ' Chain links were skipped — you can import them later from the Chain Links page.')
                : '';
            api.success({
                message: 'Framework Template Seeded Successfully',
                description: `${selectedTemplateId} framework has been seeded to your organization with all questions, chapters, and objectives.${chainLinksNote}`,
                duration: 4,
            });
            setSelectedTemplateId('');
            setWireConnections(true);
            fetchFrameworks();
        } else {
            const errorMessage = result.error || 'Unknown error occurred while seeding framework template.';
            api.error({
                message: 'Framework Seeding Failed',
                description: errorMessage,
                duration: 4,
            });
        }
    };

    const handleCreateFramework = async () => {
        if (!newFrameworkName || newFrameworkName.trim() === '') {
            api.error({message: 'Framework Creation Failed', description: 'Framework name cannot be empty!', duration: 4});
            return;
        }

        const existingFramework = frameworks.find(fw =>
            fw.name.toLowerCase() === newFrameworkName.trim().toLowerCase()
        );

        if (existingFramework) {
            api.warning({
                message: 'Framework Name Already Exists',
                description: `A framework named "${newFrameworkName}" already exists in your organization. Please choose a different name.`,
                duration: 6
            });
            return;
        }

        const result = await createFramework(
            newFrameworkName,
            newFrameworkDescription,
            false,
            allowedScopeTypes.length > 0 ? allowedScopeTypes : undefined,
            scopeSelectionMode || 'optional'
        );

        if (result.success) {
            api.success({message: 'Framework Creation Success', description: 'Framework created.', duration: 4});
        } else {
            const errorMessage = result.error || 'Api not responding...';
            if (errorMessage.includes('already exists')) {
                const confirmed = window.confirm(
                    `Framework name "${newFrameworkName}" already exists in your organization.\n\n` +
                    `Click OK to create it with a unique name (e.g., "${newFrameworkName} (1)"), or Cancel to choose a different name.`
                );

                if (confirmed) {
                    const forceResult = await createFramework(
                        newFrameworkName,
                        newFrameworkDescription,
                        true,
                        allowedScopeTypes.length > 0 ? allowedScopeTypes : undefined,
                        scopeSelectionMode || 'optional'
                    );
                    if (forceResult.success) {
                        api.success({message: 'Framework Creation Success', description: 'Framework created with unique name.', duration: 4});
                    } else {
                        api.error({message: 'Framework Creation Failed', description: forceResult.error || 'Failed to create framework', duration: 4});
                    }
                } else {
                    api.info({message: 'Framework Creation Cancelled', description: 'Please choose a different framework name.', duration: 4});
                    return;
                }
            } else {
                api.error({message: 'Framework Creation Failed', description: errorMessage, duration: 4});
            }
        }

        setNewFrameworkName('');
        setNewFrameworkDescription('');
        setAllowedScopeTypes([]);
        setScopeSelectionMode('optional');
    };

    const handleFrameworkChange = (value: string[]) => {
        const selectedIds = value.filter(Boolean);
        setFrameworkSelectedIds(selectedIds);
    };

    const handleDeleteFramework = async () => {
        if (frameworkSelectedIds.length === 0) {
            api.error({
                message: 'No Framework Selected',
                description: 'Please select at least one framework to delete!',
                duration: 4,
            });
            return;
        }

        const confirmed = window.confirm(
            `Are you sure you want to delete the selected framework(s)?\n\n` +
            `This action will permanently delete the framework(s) and all associated questions, assessments, and answers.\n\n` +
            `This action cannot be undone.`
        );

        if (confirmed) {
            let deleteSuccessCount = 0;
            let deleteFailCount = 0;

            for (const frameworkId of frameworkSelectedIds) {
                const success = await deleteFramework(frameworkId);
                if (success) {
                    deleteSuccessCount++;
                } else {
                    deleteFailCount++;
                }
            }

            if (deleteSuccessCount > 0) {
                api.success({
                    message: 'Framework Deletion Success',
                    description: `${deleteSuccessCount} framework(s) deleted successfully.`,
                    duration: 4,
                });
                setFrameworkSelectedIds([]);
                fetchFrameworks();
            }

            if (deleteFailCount > 0) {
                api.error({
                    message: 'Framework Deletion Failed',
                    description: `Failed to delete ${deleteFailCount} framework(s). Please try again.`,
                    duration: 4,
                });
            }
        } else {
            api.info({
                message: 'Framework Deletion Cancelled',
                description: 'No frameworks were deleted.',
                duration: 3,
            });
        }
    };

    return (
        <div>
            {contextHolder}
            <div className={'page-parent'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
                <div className="page-content">

                    {/* Page Header */}
                    <div className="page-header" data-tour-id="qs-framework-page-header">
                        <div className="page-header-left">
                            <AppstoreOutlined style={{ fontSize: 22, color: '#1a365d' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Manage Frameworks</h1>
                        </div>
                    </div>

                    {/* Framework Overview Section */}
                    <div className="page-section" data-tour-id="qs-framework-template-section">
                        <InfoTitle
                            title="Framework Overview"
                            infoContent={AddFrameworkFromTemplateInfo}
                            className="section-title"
                        />
                        <p className="section-subtitle">
                            View your active frameworks and add new ones from available templates
                        </p>

                        {/* Two-column layout for Active and Available frameworks */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '16px' }}>
                            {/* Active Frameworks Column */}
                            <div style={{
                                background: '#f6ffed',
                                border: '1px solid #b7eb8f',
                                borderRadius: '8px',
                                padding: '20px'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                                    <CheckCircleOutlined style={{ fontSize: '20px', color: '#52c41a' }} />
                                    <h4 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#135200' }}>
                                        Active Frameworks
                                    </h4>
                                    <Tag color="green" style={{ marginLeft: 'auto' }}>{frameworks.length}</Tag>
                                </div>
                                <p style={{ fontSize: '13px', color: '#52c41a', marginBottom: '12px' }}>
                                    Frameworks currently enabled in your organization
                                </p>
                                <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                                    {frameworks.length > 0 ? (
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                            {frameworks.map(fw => (
                                                <div key={fw.id} style={{
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '10px',
                                                    padding: '10px 12px',
                                                    background: 'white',
                                                    borderRadius: '6px',
                                                    border: '1px solid #d9f7be'
                                                }}>
                                                    <DatabaseOutlined style={{ color: '#52c41a' }} />
                                                    <span style={{ fontWeight: 500, color: '#262626' }}>{fw.name}</span>
                                                    {fw.organisation_domain && (
                                                        <Tag color="default" style={{ marginLeft: 'auto', fontSize: '11px' }}>
                                                            {fw.organisation_domain}
                                                        </Tag>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <Empty
                                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                                            description="No active frameworks yet"
                                            style={{ margin: '20px 0' }}
                                        />
                                    )}
                                </div>
                            </div>

                            {/* Available Templates Column */}
                            <div style={{
                                background: '#e6f7ff',
                                border: '1px solid #91d5ff',
                                borderRadius: '8px',
                                padding: '20px'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                                    <PlusCircleOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                                    <h4 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#003a8c' }}>
                                        Available Templates
                                    </h4>
                                    <Tag color="blue" style={{ marginLeft: 'auto' }}>{availableTemplates.length}</Tag>
                                </div>
                                <p style={{ fontSize: '13px', color: '#1890ff', marginBottom: '12px' }}>
                                    Templates ready to be added to your organization
                                </p>
                                <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                                    {availableTemplates.length > 0 ? (
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                            {availableTemplates.map(template => (
                                                <div key={template.id} style={{
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '10px',
                                                    padding: '10px 12px',
                                                    background: 'white',
                                                    borderRadius: '6px',
                                                    border: '1px solid #bae7ff',
                                                    cursor: 'pointer',
                                                    transition: 'all 0.2s ease'
                                                }}
                                                onMouseEnter={(e) => {
                                                    e.currentTarget.style.borderColor = '#1890ff';
                                                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(24, 144, 255, 0.15)';
                                                }}
                                                onMouseLeave={(e) => {
                                                    e.currentTarget.style.borderColor = '#bae7ff';
                                                    e.currentTarget.style.boxShadow = 'none';
                                                }}
                                                onClick={() => { setSelectedTemplateId(template.id); setWireConnections(true); }}
                                                >
                                                    <DatabaseOutlined style={{ color: '#1890ff' }} />
                                                    <span style={{ fontWeight: 500, color: '#262626', flex: 1 }}>{template.name}</span>
                                                    {selectedTemplateId === template.id ? (
                                                        <Tag color="blue">Selected</Tag>
                                                    ) : (
                                                        <span style={{ fontSize: '12px', color: '#1890ff' }}>Click to select</span>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <Empty
                                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                                            description="All templates have been added"
                                            style={{ margin: '20px 0' }}
                                        />
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Add Framework Button */}
                        {availableTemplates.length > 0 && (
                            <div style={{ marginTop: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                                <div style={{ flex: 1 }}>
                                    <Select
                                        className="framework-dropdown"
                                        placeholder="Or select a template from dropdown..."
                                        onChange={handleTemplateChange}
                                        options={availableTemplateOptions}
                                        value={selectedTemplateId || undefined}
                                        showSearch
                                        filterOption={(input, option) =>
                                            (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                        }
                                        style={{ width: '100%' }}
                                    />
                                </div>
                                <button
                                    className="add-button"
                                    onClick={handleSeedTemplate}
                                    disabled={frameworkLoading || !selectedTemplateId}
                                    style={{
                                        opacity: (!selectedTemplateId || frameworkLoading) ? 0.6 : 1,
                                        cursor: (!selectedTemplateId || frameworkLoading) ? 'not-allowed' : 'pointer'
                                    }}
                                >
                                    {frameworkLoading ? 'Adding...' : 'Add Selected Framework'}
                                </button>
                            </div>
                        )}
                        {selectedTemplateHasChainLinks && (
                            <div style={{ marginTop: '12px', padding: '10px 14px', backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: '6px' }}>
                                <Checkbox
                                    checked={wireConnections}
                                    onChange={(e) => setWireConnections(e.target.checked)}
                                >
                                    <span style={{ fontWeight: 500 }}>Include pre-built chain links</span>
                                    <span style={{ color: '#8c8c8c', marginLeft: '6px', fontSize: '12px' }}>
                                        (risks, controls, policies)
                                    </span>
                                </Checkbox>
                                <div style={{ marginTop: '4px', marginLeft: '24px', fontSize: '12px', color: '#8c8c8c' }}>
                                    You can also import these later from the Chain Links page
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Excel Framework Seed Generation Section - Superadmin Only */}
                    {current_user?.email === 'superadmin@clone-systems.com' && (
                        <div className="page-section">
                            <InfoTitle
                                title="Create Framework Seed from Excel"
                                infoContent="Upload an Excel file in the same format as ISO 27001 or NIS2 Directive to create a new framework seed template. This feature analyzes the file for duplicates and generates a Python seed file with unique questions and objectives."
                                className="section-title"
                            />
                            <p className="section-subtitle">
                                Generate framework seed files from Excel templates with automatic deduplication
                            </p>
                            <div style={{
                                padding: '12px 16px',
                                marginBottom: '16px',
                                backgroundColor: '#fff3cd',
                                border: '1px solid #ffc107',
                                borderRadius: '4px',
                                color: '#856404'
                            }}>
                                <strong>Warning:</strong> You must not use this section on production!
                            </div>
                            <ExcelFrameworkSeedSection onSeedGenerated={fetchFrameworkTemplates} />
                        </div>
                    )}

                    {/* Create Custom Framework Section */}
                    <div className="page-section">
                        <InfoTitle
                            title="Create Custom Framework"
                            infoContent={ManageSourcesInfo}
                            className="section-title"
                        />
                        <p className="section-subtitle">
                            Create a new custom framework for your organization
                        </p>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label required">Framework Name</label>
                                <input
                                    type="text"
                                    className="framework-input"
                                    placeholder="Enter framework name"
                                    value={newFrameworkName}
                                    onChange={handleFrameworkNameChange}
                                    style={{ borderColor: frameworkNameError ? '#ff4d4f' : undefined }}
                                    title={frameworkNameError || ''}
                                />
                                {frameworkNameError && (
                                    <span style={{ color: '#ff4d4f', fontSize: '12px', marginTop: '4px' }}>
                                        {frameworkNameError}
                                    </span>
                                )}
                            </div>
                            <div className="form-group">
                                <label className="form-label">Description</label>
                                <input
                                    type="text"
                                    className="framework-input"
                                    placeholder="Enter framework description"
                                    value={newFrameworkDescription}
                                    onChange={(e) => setNewFrameworkDescription(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Scope Configuration */}
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Allowed Scope Types</label>
                                <Select
                                    mode="multiple"
                                    className="framework-dropdown"
                                    placeholder="Select allowed scope types (optional)"
                                    onChange={setAllowedScopeTypes}
                                    options={scopeTypeOptions}
                                    value={allowedScopeTypes}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Scope Selection Mode</label>
                                <Select
                                    className="framework-dropdown"
                                    placeholder="Select scope selection mode"
                                    onChange={setScopeSelectionMode}
                                    options={scopeSelectionModeOptions}
                                    value={scopeSelectionMode}
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <button
                                className="add-button"
                                onClick={handleCreateFramework}
                                disabled={!!frameworkNameError || !newFrameworkName.trim()}
                                style={{
                                    opacity: (frameworkNameError || !newFrameworkName.trim()) ? 0.5 : 1,
                                    cursor: (frameworkNameError || !newFrameworkName.trim()) ? 'not-allowed' : 'pointer'
                                }}
                            >
                                Create Framework
                            </button>
                        </div>
                    </div>

                    {/* Delete Frameworks Section */}
                    <div className="page-section">
                        <InfoTitle
                            title="Delete Frameworks"
                            infoContent="Select one or more frameworks to delete. This will permanently remove the framework and all associated data."
                            className="section-title"
                        />
                        <p className="section-subtitle">
                            Remove frameworks that are no longer needed
                        </p>

                        <div className="form-row">
                            <div className="form-group" style={{ flex: 1 }}>
                                <label className="form-label">Select Frameworks to Delete</label>
                                <Select
                                    mode="multiple"
                                    className="framework-dropdown"
                                    placeholder="Select frameworks to delete"
                                    onChange={handleFrameworkChange}
                                    options={options}
                                    value={frameworkSelectedIds}
                                    style={{ width: '100%' }}
                                />
                                {/* Display allowed scope types for selected frameworks */}
                                {frameworkSelectedIds.length > 0 && (
                                    <div style={{
                                        marginTop: '8px',
                                        padding: '8px 12px',
                                        backgroundColor: '#fff2f0',
                                        border: '1px solid #ffccc7',
                                        borderRadius: '4px',
                                        fontSize: '13px'
                                    }}>
                                        {frameworkSelectedIds.map(frameworkId => {
                                            const framework = frameworks.find(fw => fw.id === frameworkId);
                                            if (!framework) return null;
                                            return (
                                                <div key={frameworkId} style={{ marginBottom: frameworkSelectedIds.length > 1 ? '4px' : '0' }}>
                                                    <strong>{framework.name}</strong> will be deleted
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                            <button
                                className="delete-button"
                                onClick={handleDeleteFramework}
                                disabled={frameworkSelectedIds.length === 0}
                                style={{ alignSelf: 'flex-start', marginTop: '28px' }}
                            >
                                Delete Selected
                            </button>
                        </div>
                    </div>

                    {/* AI Policy Aligner Section - Only visible when enabled */}
                    {aiPolicyAlignerEnabled && (
                        <div className="page-section">
                            <InfoTitle
                                title="AI Policy Aligner"
                                infoContent="Use AI to automatically align policies with framework questions. When enabled, new assessments will have policies pre-populated based on AI analysis."
                                className="section-title"
                            />
                            <p className="section-subtitle">
                                Generate AI-powered alignments between your policies and framework questions
                            </p>

                            <div style={{
                                padding: '20px',
                                backgroundColor: '#f6ffed',
                                border: '1px solid #b7eb8f',
                                borderRadius: '8px',
                                marginTop: '16px'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                                    <RobotOutlined style={{ fontSize: '20px', color: '#52c41a' }} />
                                    <h4 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#135200' }}>
                                        Generate Policy Alignments
                                    </h4>
                                </div>
                                <p style={{ fontSize: '13px', color: '#52c41a', marginBottom: '16px' }}>
                                    Select a framework and click "Generate AI Alignments" to analyze your policies and create automatic mappings. This process uses AI to match policies to framework questions with 80%+ confidence.
                                </p>

                                <div className="form-row" style={{ gap: '16px' }}>
                                    <div className="form-group" style={{ flex: 1 }}>
                                        <label className="form-label">Select Framework</label>
                                        <Select
                                            className="framework-dropdown"
                                            placeholder="Select a framework to align..."
                                            onChange={handleAlignmentFrameworkChange}
                                            options={options}
                                            value={selectedAlignmentFramework || undefined}
                                            showSearch
                                            filterOption={(input, option) =>
                                                (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                            }
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                    <button
                                        className="add-button"
                                        onClick={handleGenerateAlignments}
                                        disabled={!selectedAlignmentFramework || isGeneratingAlignment}
                                        style={{
                                            alignSelf: 'flex-end',
                                            opacity: (!selectedAlignmentFramework || isGeneratingAlignment) ? 0.6 : 1,
                                            cursor: (!selectedAlignmentFramework || isGeneratingAlignment) ? 'not-allowed' : 'pointer',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '8px'
                                        }}
                                    >
                                        {isGeneratingAlignment ? (
                                            <>
                                                <Spin size="small" />
                                                Generating...
                                            </>
                                        ) : (
                                            <>
                                                <RobotOutlined />
                                                Generate AI Alignments
                                            </>
                                        )}
                                    </button>
                                </div>

                                {/* Alignment Status */}
                                {selectedAlignmentFramework && (
                                    <div style={{
                                        marginTop: '16px',
                                        padding: '12px 16px',
                                        backgroundColor: 'white',
                                        border: '1px solid #d9f7be',
                                        borderRadius: '6px'
                                    }}>
                                        {isLoadingAlignment ? (
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <Spin size="small" />
                                                <span style={{ color: '#666' }}>Loading alignment status...</span>
                                            </div>
                                        ) : alignmentStatus?.has_alignments ? (
                                            <div>
                                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                    <div>
                                                        <Tag color="green">{alignmentStatus.alignment_count} Alignments</Tag>
                                                        <span style={{ fontSize: '13px', color: '#52c41a', marginLeft: '8px' }}>
                                                            Policies are mapped to framework questions
                                                        </span>
                                                    </div>
                                                    <button
                                                        onClick={handleDeleteAlignments}
                                                        style={{
                                                            background: 'transparent',
                                                            border: '1px solid #ff4d4f',
                                                            color: '#ff4d4f',
                                                            padding: '4px 12px',
                                                            borderRadius: '4px',
                                                            cursor: 'pointer',
                                                            fontSize: '12px',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            gap: '4px'
                                                        }}
                                                    >
                                                        <ReloadOutlined />
                                                        Re-generate
                                                    </button>
                                                </div>
                                                {alignmentStatus.last_updated && (
                                                    <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: '#8c8c8c' }}>
                                                        Last updated: {new Date(alignmentStatus.last_updated).toLocaleString()}
                                                    </p>
                                                )}
                                            </div>
                                        ) : (
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <Tag color="default">No Alignments</Tag>
                                                <span style={{ fontSize: '13px', color: '#8c8c8c' }}>
                                                    Click "Generate AI Alignments" to create policy mappings
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                )}

                                <p style={{ marginTop: '16px', fontSize: '12px', color: '#52c41a' }}>
                                    <strong>Note:</strong> Alignments with 80%+ confidence will automatically populate policy fields when creating new assessments for this framework.
                                </p>
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
};

export default ManageFrameworks;
