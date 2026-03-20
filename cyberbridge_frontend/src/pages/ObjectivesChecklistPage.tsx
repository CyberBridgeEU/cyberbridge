import React, { useEffect, useState } from 'react';
import { Table, Select, Card, Typography, Spin, Alert, notification, Tag, Button, Upload, Tooltip, Popconfirm } from 'antd';
import { CheckCircleOutlined, RobotOutlined, LoadingOutlined, CheckOutlined, CloseOutlined, UploadOutlined, PaperClipOutlined, DeleteOutlined } from '@ant-design/icons';
import Sidebar from '../components/Sidebar.tsx';
import useObjectiveStore from '../store/useObjectiveStore.ts';
import type { ChecklistPolicy } from '../store/useObjectiveStore.ts';
import useFrameworksStore from '../store/useFrameworksStore.ts';
import usePolicyStore from '../store/usePolicyStore.ts';
import useObjectivesAIStore from '../store/useObjectivesAIStore.ts';
import useAssetStore from '../store/useAssetStore.ts';
import useUserStore from '../store/useUserStore.ts';
import type { ColumnsType } from 'antd/es/table';
import InfoTitle from '../components/InfoTitle.tsx';
import { ObjectivesChecklistInfo } from '../constants/infoContent.tsx';
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { exportObjectivesChecklistToPdf } from '../utils/objectivesChecklistPdfUtils.ts';
import useAuthStore from "../store/useAuthStore.ts";
import ScrollToTopButton from '../components/ScrollToTopButton.tsx';
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import useCRAFilteredFrameworks from "../hooks/useCRAFilteredFrameworks.ts";
import useCRAModeStore from "../store/useCRAModeStore.ts";

const { Title, Text } = Typography;
const { Option } = Select;

interface ObjectiveTableData {
    key: string;
    subchapter: string | null;
    title: string;
    requirement_description: string | null;
    objective_utilities: string | null;
    compliance_status: string | null;
    compliance_status_id: string | null;
    policies?: ChecklistPolicy[];
    evidence_filename: string | null;
    evidence_file_size: number | null;
}

const ObjectivesChecklistPage: React.FC = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const [selectedFrameworkId, setSelectedFrameworkId] = useState<string | null>(null);
    const [api, contextHolder] = notification.useNotification();
    const [applyingSuggestionId, setApplyingSuggestionId] = useState<string | null>(null);

    // Scope-related state
    const [scopeTypes, setScopeTypes] = useState<Array<{id: string, scope_name: string}>>([]);
    const [selectedScopeType, setSelectedScopeType] = useState<string>('');
    const [selectedScopeEntityId, setSelectedScopeEntityId] = useState<string>('');
    const [frameworkScopeConfig, setFrameworkScopeConfig] = useState<{
        allowed_scope_types: string[];
        scope_selection_mode: string;
        supported_scope_types: string[];
    } | null>(null);

    const {
        chaptersWithObjectives,
        complianceStatuses,
        loading,
        error,
        fetchObjectivesChecklist,
        fetchComplianceStatuses,
        updateObjectiveComplianceStatus,
        uploadObjectiveEvidence,
        deleteObjectiveEvidence,
        clearChecklist
    } = useObjectiveStore();

    const {
        frameworks,
        loading: frameworksLoading,
        fetchFrameworks
    } = useFrameworksStore();

    const {
        aiSuggestions,
        loading: aiLoading,
        error: aiError,
        generateAISuggestions,
        removeSuggestion
    } = useObjectivesAIStore();

    const { fetchAssets, assets } = useAssetStore();
    const { organisations, fetchOrganisations } = useUserStore();
    const { policyStatuses, fetchPolicyStatuses, updatePolicyStatus } = usePolicyStore();
    const { filteredFrameworks, craFrameworkId, isCRAModeActive } = useCRAFilteredFrameworks();
    const { craOperatorRole } = useCRAModeStore();

    const getAuthHeader = useAuthStore((state) => state.getAuthHeader);

    const getScopeDisplayName = (scopeName: string) => {
        if (scopeName === 'Product' || scopeName === 'Asset') {
            return 'Asset / Product';
        }
        return scopeName;
    };

    const buildScopeTypeOptions = (types: Array<{id: string; scope_name: string}>) => {
        const hasProduct = types.some(scopeType => scopeType.scope_name === 'Product');
        return types
            .filter(scopeType => !(scopeType.scope_name === 'Asset' && hasProduct))
            .map(scopeType => ({
                value: scopeType.scope_name,
                label: getScopeDisplayName(scopeType.scope_name)
            }));
    };

    const scope_type_options = frameworkScopeConfig && frameworkScopeConfig.allowed_scope_types && frameworkScopeConfig.allowed_scope_types.length > 0
        ? buildScopeTypeOptions(
            scopeTypes.filter(scopeType => frameworkScopeConfig.allowed_scope_types.includes(scopeType.scope_name))
        )
        : buildScopeTypeOptions(scopeTypes);

    // Scope entity options - depends on selected scope type
    const scope_entity_options = selectedScopeType === 'Product' || selectedScopeType === 'Asset'
        ? assets.map(asset => ({
            value: asset.id,
            label: asset.asset_type_name ? `${asset.name} (${asset.asset_type_name})` : asset.name
        }))
        : selectedScopeType === 'Organization'
        ? organisations.map(org => ({
            value: org.id || '',
            label: org.name
        }))
        : [];

    useEffect(() => {
        fetchFrameworks();
        fetchComplianceStatuses();
        fetchPolicyStatuses();
        fetchAssets();
        fetchOrganisations();

        // Fetch available scope types
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
    }, [fetchFrameworks, fetchComplianceStatuses, fetchAssets, fetchOrganisations]);

    // Auto-select CRA framework when CRA mode is active
    const scopeNeedsEntity = selectedScopeType === 'Product' || selectedScopeType === 'Organization' || selectedScopeType === 'Asset';
    const isScopeSelectionValid = Boolean(
        selectedScopeType && (!scopeNeedsEntity || (selectedScopeEntityId && selectedScopeEntityId.trim() !== ''))
    );

    useEffect(() => {
        if (isCRAModeActive && craFrameworkId && !selectedFrameworkId) {
            setSelectedFrameworkId(craFrameworkId);
        }
    }, [isCRAModeActive, craFrameworkId]);

    useEffect(() => {
        if (selectedFrameworkId && isScopeSelectionValid) {
            fetchObjectivesChecklist(selectedFrameworkId, selectedScopeType || undefined, selectedScopeEntityId || undefined, craOperatorRole || undefined);
        }
    }, [selectedFrameworkId, selectedScopeType, selectedScopeEntityId, craOperatorRole, isScopeSelectionValid, fetchObjectivesChecklist]);

    useEffect(() => {
        if (!selectedFrameworkId) {
            setFrameworkScopeConfig(null);
            setSelectedScopeType('');
            setSelectedScopeEntityId('');
            return;
        }

        const fetchFrameworkScopeConfig = async () => {
            try {
                const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/${selectedFrameworkId}/scope-config`, {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    setFrameworkScopeConfig(data);
                    setSelectedScopeType('');
                    setSelectedScopeEntityId('');
                } else {
                    setFrameworkScopeConfig(null);
                }
            } catch (error) {
                console.error('Error fetching framework scope config:', error);
                setFrameworkScopeConfig(null);
            }
        };

        fetchFrameworkScopeConfig();
    }, [selectedFrameworkId]);

    // Reset scope entity when scope type changes
    const handleScopeTypeChange = (value: string) => {
        setSelectedScopeType(value);
        setSelectedScopeEntityId(''); // Reset entity selection when type changes
        clearChecklist();
    };

    // Warn user before leaving page if AI analysis is in progress
    useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (aiLoading) {
                e.preventDefault();
                e.returnValue = '';
                return '';
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
        };
    }, [aiLoading]);

    const handleComplianceStatusChange = async (objectiveId: string, statusId: string) => {
        await updateObjectiveComplianceStatus(
            objectiveId,
            statusId,
            selectedFrameworkId || undefined,
            selectedScopeType || undefined,
            selectedScopeEntityId || undefined
        );
    };

    const handleEvidenceUpload = async (objectiveId: string, file: File) => {
        const success = await uploadObjectiveEvidence(objectiveId, file);
        if (success) {
            api.success({
                message: 'Evidence Uploaded',
                description: `File "${file.name}" attached successfully.`,
                duration: 3,
            });
        } else {
            api.error({
                message: 'Upload Failed',
                description: 'Failed to upload evidence file. Please try again.',
                duration: 4,
            });
        }
    };

    const handleEvidenceDelete = async (objectiveId: string) => {
        const success = await deleteObjectiveEvidence(objectiveId);
        if (success) {
            api.success({
                message: 'Evidence Removed',
                description: 'Evidence file has been removed.',
                duration: 3,
            });
        } else {
            api.error({
                message: 'Delete Failed',
                description: 'Failed to remove evidence file. Please try again.',
                duration: 4,
            });
        }
    };

    const handleEvidenceDownload = async (objectiveId: string, filename: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/download_evidence/${objectiveId}`, {
                headers: {
                    ...getAuthHeader()
                }
            });
            if (!response.ok) {
                throw new Error('Download failed');
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch {
            api.error({
                message: 'Download Failed',
                description: 'Failed to download evidence file.',
                duration: 4,
            });
        }
    };

    const formatFileSize = (bytes: number | null) => {
        if (!bytes) return '';
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    const getStatusColor = (status: string | null) => {
        switch (status) {
            case 'compliant':
                return '#52c41a';
            case 'partially compliant':
                return '#faad14';
            case 'not compliant':
                return '#6366f1';
            case 'in review':
                return '#1890ff';
            case 'not applicable':
                return '#d9d9d9';
            case 'not assessed':
            default:
                return '#8c8c8c';
        }
    };

    const getPolicyStatusColor = (status: string | null) => {
        switch (status) {
            case 'Approved':
                return '#52c41a';
            case 'Ready for Approval':
                return '#1890ff';
            case 'Review':
                return '#faad14';
            case 'Draft':
            default:
                return '#8c8c8c';
        }
    };

    const handlePolicyStatusChange = async (policyId: string, statusId: string) => {
        const scrollY = window.scrollY;
        const success = await updatePolicyStatus(policyId, statusId);
        if (success) {
            api.success({
                message: 'Policy Status Updated',
                description: 'Policy status has been updated successfully.',
                duration: 3,
            });
            // Refresh checklist to reflect any auto-updated compliance statuses
            if (selectedFrameworkId) {
                await fetchObjectivesChecklist(selectedFrameworkId, selectedScopeType || undefined, selectedScopeEntityId || undefined, craOperatorRole || undefined);
            }
            requestAnimationFrame(() => {
                window.scrollTo(0, scrollY);
            });
        } else {
            api.error({
                message: 'Update Failed',
                description: 'Failed to update policy status. Please try again.',
                duration: 4,
            });
        }
    };

    const handleExportToPdf = async () => {
        if (!selectedFrameworkId || chaptersWithObjectives.length === 0) {
            api.error({
                message: 'Export Failed',
                description: 'Please select a framework with objectives to export.',
                duration: 4,
            });
            return;
        }

        try {
            const framework = frameworks.find(f => f.id === selectedFrameworkId);
            const frameworkName = framework?.name || 'Framework';

            await exportObjectivesChecklistToPdf(
                chaptersWithObjectives,
                frameworkName,
                `objectives-checklist-${frameworkName}`
            );

            api.success({
                message: 'Export Success',
                description: 'Objectives checklist has been exported to PDF successfully.',
                duration: 4,
            });
        } catch (error) {
            console.error('PDF export error:', error);
            api.error({
                message: 'Export Failed',
                description: 'Failed to export objectives checklist to PDF. Please try again.',
                duration: 4,
            });
        }
    };

    const handleAiAnalysis = async () => {
        if (!selectedFrameworkId) {
            api.error({
                message: 'Analysis Failed',
                description: 'Please select a framework first.',
                duration: 4,
            });
            return;
        }

        const result = await generateAISuggestions(selectedFrameworkId);

        if (result) {
            // Successfully got response from backend
            if (result.success) {
                if (result.suggestions && result.suggestions.length > 0) {
                    api.success({
                        message: 'AI Analysis Complete',
                        description: `Generated ${result.suggestions.length} compliance suggestion${result.suggestions.length > 1 ? 's' : ''} for your objectives.`,
                        duration: 4,
                    });
                } else {
                    // Backend returned success but no suggestions - this means answered questions exist but no matches found
                    api.info({
                        message: 'No Matches Found',
                        description: 'No objectives matched your assessment answers based on keyword analysis. This could mean your answers don\'t contain matching keywords from objective titles/subchapters.',
                        duration: 5,
                    });
                }
            } else {
                // Backend returned error response
                const errorMsg = result.error || 'Failed to analyze objectives';
                if (errorMsg.includes('No answered questions') || errorMsg.includes('complete some assessment questions')) {
                    api.warning({
                        message: 'No Assessment Answers',
                        description: 'You haven\'t answered any assessment questions yet. Please complete at least one assessment question to use AI suggestions.',
                        duration: 5,
                    });
                } else {
                    api.error({
                        message: 'Analysis Failed',
                        description: errorMsg,
                        duration: 4,
                    });
                }
            }
        } else {
            // Network error or request was aborted
            if (aiError) {
                api.error({
                    message: 'Analysis Failed',
                    description: aiError || 'Failed to analyze objectives with AI. Please try again.',
                    duration: 4,
                });
            }
        }
    };

    const handleApplySuggestion = async (suggestion: any) => {
        setApplyingSuggestionId(suggestion.objective_id);
        try {
            // Find the compliance status ID that matches the recommended status
            const matchingStatus = complianceStatuses.find(
                status => status.status_name.toLowerCase() === suggestion.recommended_status.toLowerCase()
            );

            if (!matchingStatus) {
                api.error({
                    message: 'Cannot Apply Suggestion',
                    description: `Compliance status "${suggestion.recommended_status}" not found.`,
                    duration: 4,
                });
                return;
            }

            // Apply the compliance status to the objective
            const success = await updateObjectiveComplianceStatus(
                suggestion.objective_id,
                matchingStatus.id,
                selectedFrameworkId || undefined
            );

            if (success) {
                api.success({
                    message: 'Suggestion Applied',
                    description: `Objective compliance status updated to "${suggestion.recommended_status}".`,
                    duration: 4,
                });
                removeSuggestion(suggestion.objective_id);
            } else {
                throw new Error('Failed to update objective');
            }
        } catch (error) {
            console.error('Error applying suggestion:', error);
            api.error({
                message: 'Failed to Apply',
                description: 'Could not apply the AI suggestion. Please try again.',
                duration: 4,
            });
        } finally {
            setApplyingSuggestionId(null);
        }
    };

    const handleRejectSuggestion = (suggestion: any) => {
        removeSuggestion(suggestion.objective_id);
        api.info({
            message: 'Suggestion Rejected',
            description: 'AI suggestion removed from the list.',
            duration: 3,
        });
    };

    const columns: ColumnsType<ObjectiveTableData> = [
        {
            title: 'Subchapter',
            dataIndex: 'subchapter',
            key: 'subchapter',
            width: '10%',
            render: (text: string | null) => text || '-',
        },
        {
            title: 'Objective Title',
            dataIndex: 'title',
            key: 'title',
            width: '15%',
            render: (text: string) => <Text strong>{text}</Text>,
        },
        {
            title: 'Requirement Description',
            dataIndex: 'requirement_description',
            key: 'requirement_description',
            width: '20%',
            render: (text: string | null) => text || '-',
        },
        {
            title: 'Objective Utilities',
            dataIndex: 'objective_utilities',
            key: 'objective_utilities',
            width: '25%',
            render: (text: string | null) => text || '-',
        },
        {
            title: 'Policies',
            dataIndex: 'policies',
            key: 'policies',
            width: '18%',
            render: (policies: ChecklistPolicy[] | null) => {
                if (!policies || policies.length === 0) return '-';
                return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {policies.map((policy) => (
                            <div key={policy.id} style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                fontSize: '13px',
                            }}>
                                <div style={{
                                    width: 8,
                                    height: 8,
                                    borderRadius: '50%',
                                    backgroundColor: getPolicyStatusColor(policy.status),
                                    flexShrink: 0,
                                }} />
                                <span style={{
                                    flex: 1,
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                    color: '#262626',
                                }}>
                                    {policy.title}
                                </span>
                                <Select
                                    value={policy.status_id}
                                    size="small"
                                    style={{ width: '130px', flexShrink: 0 }}
                                    onChange={(value) => handlePolicyStatusChange(policy.id, value)}
                                >
                                    {policyStatuses.map((ps) => (
                                        <Option key={ps.id} value={ps.id}>
                                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                                <div style={{
                                                    width: 6,
                                                    height: 6,
                                                    borderRadius: '50%',
                                                    backgroundColor: getPolicyStatusColor(ps.status),
                                                    marginRight: 6,
                                                }} />
                                                {ps.status}
                                            </div>
                                        </Option>
                                    ))}
                                </Select>
                            </div>
                        ))}
                    </div>
                );
            },
        },
        {
            title: 'Evidence',
            dataIndex: 'evidence_filename',
            key: 'evidence',
            width: '15%',
            render: (_: string | null, record: ObjectiveTableData) => {
                if (record.evidence_filename) {
                    return (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <PaperClipOutlined style={{ color: '#1890ff', flexShrink: 0 }} />
                            <Tooltip title={`${record.evidence_filename} (${formatFileSize(record.evidence_file_size)})`}>
                                <a
                                    onClick={() => handleEvidenceDownload(record.key, record.evidence_filename!)}
                                    style={{
                                        cursor: 'pointer',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        whiteSpace: 'nowrap',
                                        maxWidth: '120px',
                                        display: 'inline-block',
                                        fontSize: '13px',
                                    }}
                                >
                                    {record.evidence_filename}
                                </a>
                            </Tooltip>
                            <Popconfirm
                                title="Remove evidence?"
                                description="This will delete the attached file."
                                onConfirm={() => handleEvidenceDelete(record.key)}
                                okText="Delete"
                                cancelText="Cancel"
                                okButtonProps={{ danger: true }}
                            >
                                <DeleteOutlined
                                    style={{ color: '#ff4d4f', cursor: 'pointer', flexShrink: 0, fontSize: '13px' }}
                                />
                            </Popconfirm>
                        </div>
                    );
                }
                return (
                    <Upload
                        showUploadList={false}
                        beforeUpload={(file) => {
                            handleEvidenceUpload(record.key, file);
                            return false;
                        }}
                        disabled={!isScopeSelectionValid}
                    >
                        <Button
                            size="small"
                            icon={<UploadOutlined />}
                            disabled={!isScopeSelectionValid}
                            style={{ fontSize: '12px' }}
                        >
                            Upload
                        </Button>
                    </Upload>
                );
            },
        },
        {
            title: 'Compliance Status',
            dataIndex: 'compliance_status',
            key: 'compliance_status',
            width: '20%',
            render: (status: string | null, record: ObjectiveTableData) => (
                <Select
                    value={record.compliance_status_id || undefined}
                    placeholder={
                        !selectedScopeType
                            ? 'Select scope first'
                            : scopeNeedsEntity && !selectedScopeEntityId
                            ? `Select ${getScopeDisplayName(selectedScopeType)} first`
                            : 'Select status'
                    }
                    style={{ width: '100%', minWidth: '200px' }}
                    onChange={(value) => handleComplianceStatusChange(record.key, value)}
                    disabled={!isScopeSelectionValid}
                >
                    {complianceStatuses.map((complianceStatus) => (
                        <Option key={complianceStatus.id} value={complianceStatus.id}>
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                                <div
                                    style={{
                                        width: 8,
                                        height: 8,
                                        borderRadius: '50%',
                                        backgroundColor: getStatusColor(complianceStatus.status_name),
                                        marginRight: 8,
                                    }}
                                />
                                {complianceStatus.status_name}
                            </div>
                        </Option>
                    ))}
                </Select>
            ),
        },
    ];

    if (error) {
        return (
            <div>
                {contextHolder}
                <div className={'page-parent'}>
                    <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
                    <div className={'page-content'}>
                        <Alert message="Error" description={error} type="error" showIcon />
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div>
            {contextHolder}
            <ScrollToTopButton />
            <div className={'page-parent'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
                <div className={'page-content'}>

                    {/* Page Header */}
                    <div className="page-header" data-tour-id="qs-objectives-page-header">
                        <div className="page-header-left">
                            <CheckCircleOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Objectives Checklist"
                                infoContent={ObjectivesChecklistInfo}
                                className="page-title"
                            />
                        </div>
                        {selectedFrameworkId && chaptersWithObjectives.length > 0 && (
                            <div className="page-header-right">
                                <button
                                    className="secondary-button"
                                    onClick={handleAiAnalysis}
                                    disabled={aiLoading}
                                    style={{
                                        fontSize: '13px',
                                        padding: '6px 12px',
                                        height: '32px',
                                        backgroundColor: aiLoading ? '#d1d5db' : '#10b981',
                                        borderColor: aiLoading ? '#d1d5db' : '#10b981',
                                        color: 'white',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        gap: '6px',
                                        cursor: aiLoading ? 'not-allowed' : 'pointer',
                                        opacity: aiLoading ? 0.6 : 1
                                    }}
                                >
                                    {aiLoading ? (
                                        <>
                                            <LoadingOutlined spin />
                                            Analyzing...
                                        </>
                                    ) : (
                                        <>
                                            <RobotOutlined />
                                            AI Auto-select
                                        </>
                                    )}
                                </button>
                                <button
                                    className="export-button"
                                    onClick={handleExportToPdf}
                                    style={{
                                        fontSize: '13px',
                                        padding: '6px 12px',
                                        height: '32px'
                                    }}
                                >
                                    Export PDF
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Framework and Scope Selection Section */}
                    <div className="page-section" data-tour-id="qs-objectives-framework-select">
                        <h3 className="section-title">Framework & Scope Selection</h3>
                        <div className="form-row">
                            <div className="form-group" style={{ maxWidth: '500px' }}>
                                <label className="form-label required">Select Framework</label>
                                <Select
                                    value={selectedFrameworkId}
                                    placeholder="Choose a framework to view its objectives"
                                    style={{ width: '100%' }}
                                    onChange={(value) => setSelectedFrameworkId(value)}
                                    loading={frameworksLoading}
                                    showSearch
                                    filterOption={(input, option) =>
                                        (option?.children ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                    }
                                >
                                    {filteredFrameworks.map((framework) => (
                                        <Option key={framework.id} value={framework.id}>
                                            {framework.organisation_domain ? `${framework.name} (${framework.organisation_domain})` : framework.name}
                                        </Option>
                                    ))}
                                </Select>
                            </div>
                            <div className="form-group" style={{ maxWidth: '300px' }}>
                                <label className="form-label required">Scope Type</label>
                                <Select
                                    value={selectedScopeType || undefined}
                                    placeholder="Select scope type"
                                    style={{ width: '100%' }}
                                    onChange={handleScopeTypeChange}
                                >
                                    {scope_type_options.map((option) => (
                                        <Option key={option.value} value={option.value}>
                                            {option.label}
                                        </Option>
                                    ))}
                                </Select>
                            </div>
                            {selectedScopeType && (selectedScopeType === 'Product' || selectedScopeType === 'Asset' || selectedScopeType === 'Organization') && (
                                <div className="form-group" style={{ maxWidth: '400px' }}>
                                    <label className="form-label">
                                        {selectedScopeType === 'Product' || selectedScopeType === 'Asset' ? 'Select Asset / Product' :
                                         selectedScopeType === 'Organization' ? 'Select Organization' : 'Select Entity'}
                                    </label>
                                    <Select
                                        value={selectedScopeEntityId || undefined}
                                        placeholder={
                                            scope_entity_options.length === 0
                                                ? `No ${getScopeDisplayName(selectedScopeType).toLowerCase()} available`
                                                : `Choose a ${getScopeDisplayName(selectedScopeType).toLowerCase()}`
                                        }
                                        style={{ width: '100%' }}
                                        onChange={(value) => setSelectedScopeEntityId(value)}
                                        showSearch
                                        allowClear
                                        onClear={() => setSelectedScopeEntityId('')}
                                        filterOption={(input, option) =>
                                            (option?.children ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                        }
                                        disabled={scope_entity_options.length === 0}
                                    >
                                        {scope_entity_options.map((option) => (
                                            <Option key={option.value} value={option.value}>
                                                {option.label}
                                            </Option>
                                        ))}
                                    </Select>
                                </div>
                            )}
                        </div>
                        {selectedScopeType && (
                            <div style={{ marginTop: '12px' }}>
                                    <Tag color="blue">
                                    Scope: {getScopeDisplayName(selectedScopeType)}
                                    {selectedScopeEntityId && scope_entity_options.find(o => o.value === selectedScopeEntityId) &&
                                        ` - ${scope_entity_options.find(o => o.value === selectedScopeEntityId)?.label}`}
                                </Tag>
                            </div>
                        )}
                    </div>

                    {/* Content Area */}
                    {!selectedFrameworkId ? (
                        <div className="page-section">
                            <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                                <CheckCircleOutlined style={{ fontSize: 64, color: '#d9d9d9', marginBottom: 24 }} />
                                <Title level={3} type="secondary" style={{ marginBottom: 12 }}>Select a Framework</Title>
                                <Text type="secondary" style={{ fontSize: '16px' }}>
                                    Choose a framework from the selection above to view and manage its objectives checklist
                                </Text>
                            </div>
                        </div>
                    ) : !isScopeSelectionValid ? (
                        <div className="page-section">
                            <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                                <CheckCircleOutlined style={{ fontSize: 64, color: '#d9d9d9', marginBottom: 24 }} />
                                <Title level={3} type="secondary" style={{ marginBottom: 12 }}>Select a Scope</Title>
                                <Text type="secondary" style={{ fontSize: '16px' }}>
                                    {scopeNeedsEntity
                                        ? `Choose a ${getScopeDisplayName(selectedScopeType).toLowerCase()} from the options above to view the objectives checklist`
                                        : 'Choose a scope type from the options above to view the objectives checklist'}
                                </Text>
                            </div>
                        </div>
                    ) : loading ? (
                        <div className="page-section">
                            <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                                <Spin size="large" />
                                <div style={{ marginTop: 20, color: '#8c8c8c', fontSize: '16px' }}>
                                    Loading objectives checklist...
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div data-tour-id="qs-objectives-content-area">
                            {chaptersWithObjectives.map((chapter) => (
                                <div key={chapter.id} className="page-section">
                                    <div style={{ display: 'flex', alignItems: 'center', marginBottom: 20 }}>
                                        <h3 className="section-title" style={{ margin: 0, flex: 1 }}>
                                            {chapter.title}
                                        </h3>
                                        <span style={{
                                            color: '#8c8c8c',
                                            fontSize: '14px',
                                            backgroundColor: '#f0f2f5',
                                            padding: '4px 12px',
                                            borderRadius: '12px',
                                            fontWeight: '500'
                                        }}>
                                            {chapter.objectives.length} objective{chapter.objectives.length !== 1 ? 's' : ''}
                                        </span>
                                    </div>

                                    {chapter.objectives.length > 0 ? (
                                        <Table<ObjectiveTableData>
                                            columns={columns}
                                            dataSource={chapter.objectives.map((objective) => ({
                                                    key: objective.id,
                                                    subchapter: objective.subchapter,
                                                    title: objective.title,
                                                    requirement_description: objective.requirement_description,
                                                    objective_utilities: objective.objective_utilities,
                                                    policies: objective.policies,
                                                    evidence_filename: objective.evidence_filename,
                                                    evidence_file_size: objective.evidence_file_size,
                                                    compliance_status: objective.compliance_status,
                                                    compliance_status_id: objective.compliance_status_id,
                                            }))}
                                            pagination={false}
                                            scroll={{ x: 800 }}
                                            style={{
                                                border: '1px solid #f0f0f0',
                                                borderRadius: '6px'
                                            }}
                                        />
                                    ) : (
                                        <div style={{
                                            textAlign: 'center',
                                            padding: '40px',
                                            backgroundColor: '#fafafa',
                                            border: '1px solid #f0f0f0',
                                            borderRadius: '6px'
                                        }}>
                                            <Text type="secondary" style={{ fontSize: '14px' }}>
                                                No objectives found for this chapter
                                            </Text>
                                        </div>
                                    )}
                                </div>
                            ))}

                            {chaptersWithObjectives.length === 0 && (
                                <div className="page-section">
                                    <div style={{ textAlign: 'center', padding: '60px 20px' }}>
                                        <CheckCircleOutlined style={{ fontSize: 64, color: '#d9d9d9', marginBottom: 24 }} />
                                        <Title level={3} type="secondary" style={{ marginBottom: 12 }}>No Chapters Found</Title>
                                        <Text type="secondary" style={{ fontSize: '16px', lineHeight: 1.6 }}>
                                            This framework doesn't have any chapters with objectives yet.<br />
                                            Please add some chapters and objectives in the Framework Management section.
                                        </Text>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* AI Compliance Suggestions Section */}
                    {selectedFrameworkId && (
                        <div className="page-section" style={{ marginTop: '32px' }}>
                            <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <RobotOutlined style={{ color: '#10b981' }} />
                                AI Compliance Suggestions
                            </h3>

                            {aiLoading && (
                                <Alert
                                    message="AI Analysis in Progress"
                                    description="Analyzing your objectives and assessment data to generate compliance suggestions. This may take several minutes depending on the amount of data. You can navigate away and come back later - results will persist."
                                    type="info"
                                    showIcon
                                    icon={<LoadingOutlined spin />}
                                    style={{ marginTop: '16px' }}
                                />
                            )}

                            {aiError && (
                                <Alert
                                    message="Analysis Error"
                                    description={aiError}
                                    type="error"
                                    showIcon
                                    closable
                                    style={{ marginTop: '16px' }}
                                />
                            )}

                            <div style={{ minHeight: '200px', marginTop: '16px' }}>
                                {!aiSuggestions || !aiSuggestions.suggestions || aiSuggestions.suggestions.length === 0 ? (
                                    <div style={{
                                        textAlign: 'center',
                                        padding: '60px 20px',
                                        backgroundColor: '#fafafa',
                                        borderRadius: '8px',
                                        border: '1px dashed #d9d9d9'
                                    }}>
                                        <RobotOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
                                        <Text type="secondary" style={{ display: 'block', fontSize: '16px' }}>
                                            {aiLoading
                                                ? 'AI is analyzing your objectives...'
                                                : 'No AI suggestions yet. Click "Auto-select with AI" to generate compliance recommendations.'}
                                        </Text>
                                    </div>
                                ) : (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                        <Alert
                                            message={`${aiSuggestions.suggestions.length} AI Suggestions Generated`}
                                            description={`Based on analysis of your ${aiSuggestions.framework_name} objectives and assessment answers. Review each suggestion and apply or reject as needed.`}
                                            type="success"
                                            showIcon
                                            style={{ marginBottom: '8px' }}
                                        />

                                        {aiSuggestions.suggestions.map((suggestion, index) => (
                                            <Card
                                                key={suggestion.objective_id}
                                                style={{
                                                    borderLeft: `4px solid ${
                                                        suggestion.confidence >= 80 ? '#10b981' :
                                                        suggestion.confidence >= 60 ? '#f59e0b' : '#ef4444'
                                                    }`
                                                }}
                                            >
                                                {/* Header with title, confidence, and actions */}
                                                <div style={{
                                                    display: 'flex',
                                                    flexDirection: 'column',
                                                    gap: '12px',
                                                    marginBottom: '16px',
                                                    paddingBottom: '12px',
                                                    borderBottom: '1px solid #f0f0f0'
                                                }}>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                                                        <div style={{ flex: 1 }}>
                                                            <Text strong style={{ fontSize: '16px', display: 'block', marginBottom: '8px' }}>
                                                                #{index + 1}: {suggestion.objective_title}
                                                            </Text>
                                                            <Tag color={
                                                                suggestion.confidence >= 80 ? 'green' :
                                                                suggestion.confidence >= 60 ? 'orange' : 'red'
                                                            } style={{ fontSize: '13px' }}>
                                                                {suggestion.confidence}% Match
                                                            </Tag>
                                                        </div>
                                                        <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
                                                            <Button
                                                                type="primary"
                                                                icon={<CheckOutlined />}
                                                                onClick={() => handleApplySuggestion(suggestion)}
                                                                loading={applyingSuggestionId === suggestion.objective_id}
                                                                disabled={applyingSuggestionId !== null}
                                                                style={{ backgroundColor: '#10b981', borderColor: '#10b981' }}
                                                                size="small"
                                                            >
                                                                Apply
                                                            </Button>
                                                            <Button
                                                                icon={<CloseOutlined />}
                                                                onClick={() => handleRejectSuggestion(suggestion)}
                                                                disabled={applyingSuggestionId !== null}
                                                                size="small"
                                                            >
                                                                Reject
                                                            </Button>
                                                        </div>
                                                    </div>
                                                </div>

                                                <div style={{ marginBottom: '12px' }}>
                                                    <Text strong>Recommended Status: </Text>
                                                    <Tag color="blue" style={{ fontSize: '14px' }}>
                                                        {suggestion.recommended_status}
                                                    </Tag>
                                                </div>

                                                {suggestion.suggested_body && (
                                                    <div style={{ marginBottom: '12px' }}>
                                                        <Text strong>AI Analysis:</Text>
                                                        <div style={{
                                                            marginTop: '8px',
                                                            padding: '12px',
                                                            backgroundColor: '#f5f5f5',
                                                            borderRadius: '6px',
                                                            fontSize: '14px',
                                                            lineHeight: '1.6'
                                                        }}>
                                                            {suggestion.suggested_body}
                                                        </div>
                                                    </div>
                                                )}

                                                {suggestion.supporting_evidence && suggestion.supporting_evidence.length > 0 && (
                                                    <div style={{ marginBottom: '12px' }}>
                                                        <Text strong>Supporting Evidence:</Text>
                                                        <ul style={{ marginTop: '8px', marginBottom: 0, paddingLeft: '20px' }}>
                                                            {suggestion.supporting_evidence.map((evidence, idx) => (
                                                                <li key={idx} style={{ marginBottom: '4px', fontSize: '14px' }}>
                                                                    {evidence}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}

                                                {suggestion.gaps && suggestion.gaps.length > 0 && (
                                                    <div style={{ marginBottom: '12px' }}>
                                                        <Text strong style={{ color: '#ef4444' }}>Identified Gaps:</Text>
                                                        <ul style={{ marginTop: '8px', marginBottom: 0, paddingLeft: '20px' }}>
                                                            {suggestion.gaps.map((gap, idx) => (
                                                                <li key={idx} style={{ marginBottom: '4px', fontSize: '14px', color: '#ef4444' }}>
                                                                    {gap}
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    </div>
                                                )}

                                                {suggestion.recommended_policies && suggestion.recommended_policies.length > 0 && (
                                                    <div>
                                                        <Text strong>Recommended Policies:</Text>
                                                        <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                                            {suggestion.recommended_policies.map((policy, idx) => (
                                                                <Tag key={idx} color="purple">
                                                                    {policy}
                                                                </Tag>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </Card>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ObjectivesChecklistPage;
