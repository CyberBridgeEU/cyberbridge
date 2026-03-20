import {Select, Table, notification, Modal, Tag, Card, Row, Col, Input, Empty, Tabs, Progress, Tooltip, Button, Collapse} from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { AuditOutlined, PlusOutlined, EditOutlined, AppstoreOutlined, UnorderedListOutlined, SearchOutlined, LinkOutlined, ImportOutlined, SafetyCertificateOutlined, BulbOutlined, AlertOutlined } from '@ant-design/icons';
import usePolicyStore from "../store/usePolicyStore.ts";
import useControlStore from "../store/useControlStore.ts";
import {useEffect, useState, useMemo} from "react";
import {PolicyGridColumns, onPolicyTableChange} from "../constants/PolicyGridColumns.tsx";
import {exportPoliciesToPdf} from "../utils/policyPdfUtils.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import { PoliciesInfo } from "../constants/infoContent.tsx";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import ConnectionBoard from "../components/ConnectionBoard.tsx";
import PolicyTemplatesSection from "../components/PolicyTemplatesSection.tsx";
import { filterByRelevance } from "../utils/recommendationUtils.ts";
import useCRAFilteredFrameworks from "../hooks/useCRAFilteredFrameworks.ts";
import useCRAModeStore from "../store/useCRAModeStore.ts";

const PolicyRegistrationPage = () => {
    // Menu highlighting
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // View mode state
    const [policyViewMode, setPolicyViewMode] = useState<'grid' | 'list'>('list');
    const [policySearchText, setPolicySearchText] = useState('');

    // Store access
    const {
        policies,
        policyStatuses,
        frameworks,
        chapters,
        policyFiles,
        selectedFilePreview,
        fetchPolicies,
        fetchPolicyStatuses,
        fetchChaptersWithObjectives,
        fetchPolicyFiles,
        fetchPolicyFilePreview,
        clearFilePreview,
        createPolicy,
        updatePolicy,
        deletePolicy,
        fetchPolicyTemplates,
        loading,
        error
    } = usePolicyStore();

    const { controls, fetchControls } = useControlStore();
    const { filteredFrameworks, craFrameworkId, isCRAModeActive } = useCRAFilteredFrameworks(frameworks);
    const { craOperatorRole } = useCRAModeStore();

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    // Filtered data state for PDF export
    const [filteredPolicies, setFilteredPolicies] = useState(policies);

    // Update filtered policies when policies change
    useEffect(() => {
        setFilteredPolicies(policies);
    }, [policies]);

    // Selected policy state
    const [selectedPolicy, setSelectedPolicy] = useState<string | null>(null);

    // Form visibility state
    const [showForm, setShowForm] = useState<boolean>(false);

    // Form state
    const [policyTitle, setPolicyTitle] = useState('');
    const [policyCode, setPolicyCode] = useState('');
    const [policyBody, setPolicyBody] = useState('');
    const [statusId, setStatusId] = useState<string | undefined>(undefined);
    // Parameters state
    const [companyName, setCompanyName] = useState('');

    // Policy file selection state
    const [selectedPolicyFile, setSelectedPolicyFile] = useState<string | undefined>(undefined);

    // Connection tab state
    const [selectedConnectionPolicy, setSelectedConnectionPolicy] = useState<string | undefined>(undefined);
    const [activeTab, setActiveTab] = useState<string>('policies');
    const [connectionFrameworkId, setConnectionFrameworkId] = useState<string | undefined>(undefined);
    const [connectionChapterId, setConnectionChapterId] = useState<string | undefined>(undefined);
    const [connectionSubchapter, setConnectionSubchapter] = useState<string | undefined>(undefined);
    const [policyRecommendationLoading, setPolicyRecommendationLoading] = useState<Record<string, boolean>>({});
    const [policyRecommendationFrameworkFilter, setPolicyRecommendationFrameworkFilter] = useState<string | undefined>(undefined);

    // Fetch dropdown options and policies on component mount
    useEffect(() => {
        const fetchData = async () => {
            await fetchPolicyStatuses();
            // fetchPolicies now also fetches frameworks, objectives, and their relationships
            await fetchPolicies();
            // Fetch policy files
            await fetchPolicyFiles();
            // Fetch controls for connections
            await fetchControls();
        };
        fetchData();
    }, [fetchPolicyStatuses, fetchPolicies, fetchPolicyFiles, fetchControls]);

    // Fetch linked data when connection policy changes
    const { fetchLinkedObjectives, fetchLinkedControls, linkedObjectives, linkedControls } = usePolicyStore();
    useEffect(() => {
        if (selectedConnectionPolicy) {
            fetchLinkedObjectives(selectedConnectionPolicy);
        }
    }, [selectedConnectionPolicy, fetchLinkedObjectives]);

    // Fetch linked controls when policy or framework changes (controls are framework-scoped)
    useEffect(() => {
        if (selectedConnectionPolicy && connectionFrameworkId) {
            fetchLinkedControls(selectedConnectionPolicy, connectionFrameworkId);
        }
    }, [selectedConnectionPolicy, connectionFrameworkId, fetchLinkedControls]);

    useEffect(() => {
        if (!selectedConnectionPolicy) {
            setPolicyRecommendationFrameworkFilter(undefined);
            return;
        }

        const connectionPolicy = policies.find((policy) => policy.id === selectedConnectionPolicy);
        if (connectionPolicy?.frameworks && connectionPolicy.frameworks.length > 0) {
            const firstFrameworkId = connectionPolicy.frameworks[0];
            setPolicyRecommendationFrameworkFilter(firstFrameworkId);
            fetchChaptersWithObjectives(firstFrameworkId, craOperatorRole || undefined);
        } else {
            setPolicyRecommendationFrameworkFilter(undefined);
        }
    }, [selectedConnectionPolicy, policies, fetchChaptersWithObjectives, craOperatorRole]);

    // Connection filters for objectives
    const handleConnectionFrameworkChange = async (value: string | undefined) => {
        setConnectionFrameworkId(value);
        setConnectionChapterId(undefined);
        setConnectionSubchapter(undefined);

        if (value) {
            await fetchChaptersWithObjectives(value, craOperatorRole || undefined);
        }
    };

    const handleConnectionChapterChange = (value: string | undefined) => {
        setConnectionChapterId(value);
        setConnectionSubchapter(undefined);
    };

    const handleConnectionSubchapterChange = (value: string | undefined) => {
        setConnectionSubchapter(value);
    };

    // Auto-select CRA framework in connections tab when CRA mode is active
    useEffect(() => {
        if (isCRAModeActive && craFrameworkId && !connectionFrameworkId) {
            handleConnectionFrameworkChange(craFrameworkId);
        }
    }, [isCRAModeActive, craFrameworkId]);

    const handleLinkRecommendedObjective = async (objectiveId: string) => {
        if (!selectedConnectionPolicy) {
            api.warning({
                message: 'No Policy Selected',
                description: 'Select a policy in the Connections tab before linking objectives.',
                duration: 4,
            });
            return;
        }

        setPolicyRecommendationLoading((prev) => ({ ...prev, [objectiveId]: true }));
        try {
            const { addObjectiveToPolicy } = usePolicyStore.getState();
            const success = await addObjectiveToPolicy(
                selectedConnectionPolicy,
                objectiveId,
                linkedObjectives.length + 1
            );
            if (success) {
                await fetchLinkedObjectives(selectedConnectionPolicy);
                api.success({
                    message: 'Objective Linked',
                    description: 'Objective linked to policy successfully',
                    duration: 4,
                });
            } else {
                api.error({
                    message: 'Link Failed',
                    description: 'Failed to link objective to policy',
                    duration: 4,
                });
            }
        } catch {
            api.error({
                message: 'Link Failed',
                description: 'An unexpected error occurred',
                duration: 4,
            });
        } finally {
            setPolicyRecommendationLoading((prev) => ({ ...prev, [objectiveId]: false }));
        }
    };

    // Handle form submission
    const handleSave = async () => {
        const normalizedPolicyTitle = policyTitle.trim();
        const normalizedPolicyCode = policyCode.trim();

        if (!normalizedPolicyTitle || !normalizedPolicyCode || !statusId) {
            api.error({
                message: 'Policy Operation Failed',
                description: 'Please fill in all required fields (Code, Title, Status)',
                duration: 4,
            });
            return;
        }

        const duplicateCode = policies.some(
            (policy) =>
                policy.id !== selectedPolicy &&
                (policy.policy_code || '').trim().toLowerCase() === normalizedPolicyCode.toLowerCase()
        );

        if (duplicateCode) {
            api.error({
                message: 'Policy Operation Failed',
                description: `Policy code "${normalizedPolicyCode}" already exists.`,
                duration: 4,
            });
            return;
        }

        let success;
        const isUpdate = selectedPolicy !== null;

        if (isUpdate && selectedPolicy) {
            // Update existing policy
            success = await updatePolicy(
                selectedPolicy,
                normalizedPolicyTitle,
                null, // owner - not implemented in UI yet
                statusId,
                policyBody,
                undefined,
                undefined,
                companyName,
                normalizedPolicyCode
            );
        } else {
            // Create new policy with user-provided code
            success = await createPolicy(
                normalizedPolicyTitle,
                null, // owner - not implemented in UI yet
                statusId,
                policyBody,
                undefined,
                undefined,
                companyName,
                normalizedPolicyCode
            );
        }

        if (success) {
            api.success({
                message: isUpdate ? 'Policy Update Success' : 'Policy Creation Success',
                description: isUpdate ? 'Policy updated successfully' : 'Policy created successfully',
                duration: 4,
            });
            handleClear(true); // Hide form after successful save
            // Refresh policies to show the newly created/updated policy with full relations
            await fetchPolicies();
        } else {
            const latestError = usePolicyStore.getState().error;
            api.error({
                message: isUpdate ? 'Policy Update Failed' : 'Policy Creation Failed',
                description: latestError || (isUpdate ? 'Failed to update policy' : 'Failed to create policy'),
                duration: 4,
            });
        }
    };

    // Clear form
    const handleClear = (hideForm: boolean = false) => {
        setPolicyTitle('');
        setPolicyCode('');
        setPolicyBody('');
        setStatusId(undefined);
        setCompanyName('');
        setSelectedPolicy(null);
        setSelectedPolicyFile(undefined);
        clearFilePreview();
        if (hideForm) {
            setShowForm(false);
        }
    };

    // Handle policy deletion
    const handleDelete = async () => {
        if (!selectedPolicy) {
            api.error({
                message: 'Policy Deletion Failed',
                description: 'Please select a policy to delete',
                duration: 4,
            });
            return;
        }

        const success = await deletePolicy(selectedPolicy);

        if (success) {
            api.success({
                message: 'Policy Deletion Success',
                description: 'Policy deleted successfully',
                duration: 4,
            });
            handleClear(true); // Hide form after successful delete
            // Refresh policies to update the table
            await fetchPolicies();
        } else {
            api.error({
                message: 'Policy Deletion Failed',
                description: error || 'Failed to delete policy. Maybe this policy is assigned to user\'s assessment\'s answers of this organization or maybe you don\'t have the permissions to delete other user\'s records',
                duration: 4,
            });
        }
    };

    // Handle parameters save
    const handleSaveParameters = () => {
        // This would typically save parameters to the policy
        // For now, just show a notification
        api.success({
            message: 'Parameters Saved',
            description: 'Parameters saved successfully',
            duration: 4,
        });
    };

    // Handle PDF export
    const handleExportToPdf = async () => {
        try {
            await exportPoliciesToPdf(filteredPolicies, 'policies-report');
            api.success({
                message: 'Export Success',
                description: `${filteredPolicies.length} polic(y/ies) have been exported to PDF successfully.`,
                duration: 4,
            });
        } catch (error) {
            console.error('PDF export error:', error);
            api.error({
                message: 'Export Failed',
                description: 'Failed to export policies to PDF. Please try again.',
                duration: 4,
            });
        }
    };

    // Handle table change to track filtered data
    const handleTableChange = (pagination: any, filters: any, sorter: any, extra: any) => {
        // Update filtered policies based on the current filtered data
        if (extra.currentDataSource) {
            setFilteredPolicies(extra.currentDataSource);
        }
        // Call original handler for logging
        onPolicyTableChange(pagination, filters, sorter, extra);
    };

    // Handle policy file selection
    const handlePolicyFileChange = async (filename: string | undefined) => {
        setSelectedPolicyFile(filename);
        if (filename) {
            await fetchPolicyFilePreview(filename);
        } else {
            clearFilePreview();
        }
    };



    // Handle copy content directly to body textarea (with formatting indicators)
    const handleCopyToBody = () => {
        if (selectedFilePreview?.html_content) {
            const formattedText = convertHtmlToFormattedTextWithIndicators(selectedFilePreview.html_content);
            setPolicyBody(formattedText);
            api.success({
                message: 'Content Copied to Body',
                description: 'Policy content has been copied to the body field with formatting indicators',
                duration: 3,
            });
        }
    };

    // Convert HTML to formatted plain text with bold/italic indicators
    const convertHtmlToFormattedTextWithIndicators = (html: string): string => {
        // First, decode HTML entities to get proper characters
        let processedHtml = html
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");
        
        // Identify template placeholders (text inside < > that aren't HTML tags)
        const htmlTags = [
            'p', 'div', 'span', 'br', 'hr', 'a', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'strong', 'b', 'em', 'i', 'u', 'table', 'tr', 'td', 'th',
            'thead', 'tbody', 'tfoot', 'blockquote', 'pre', 'code', 'sub', 'sup'
        ];
        
        // Replace template placeholders with * markers
        processedHtml = processedHtml.replace(/<([^>]+)>/g, (match, content) => {
            const tagMatch = content.match(/^\/?\s*(\w+)(?:\s|\/|$)/);
            if (tagMatch && htmlTags.includes(tagMatch[1].toLowerCase())) {
                return match; // Keep HTML tags as-is
            }
            return `*${content}*`; // Use * markers for template placeholders
        });
        
        // Convert HTML patterns to text with markdown-style indicators
        processedHtml = processedHtml
            .replace(/<br\s*\/?>/gi, '\n')
            .replace(/<\/p>/gi, '\n\n')
            .replace(/<p[^>]*>/gi, '')
            .replace(/<\/div>/gi, '\n')
            .replace(/<div[^>]*>/gi, '')
            .replace(/<li[^>]*>/gi, '• ')
            .replace(/<\/li>/gi, '\n')
            .replace(/<\/ul>/gi, '\n')
            .replace(/<ul[^>]*>/gi, '')
            .replace(/<\/ol>/gi, '\n')
            .replace(/<ol[^>]*>/gi, '')
            .replace(/<h[1-6][^>]*>/gi, '')
            .replace(/<\/h[1-6]>/gi, '\n\n')
            // Convert bold and italic to markdown-style indicators
            .replace(/<(strong|b)[^>]*>/gi, '**')
            .replace(/<\/(strong|b)>/gi, '**')
            .replace(/<(em|i)[^>]*>/gi, '*')
            .replace(/<\/(em|i)>/gi, '*');
        
        // Remove any remaining HTML tags
        processedHtml = processedHtml.replace(/<[^>]+>/g, '');
        
        // Clean up whitespace and newlines
        processedHtml = processedHtml
            .replace(/\n{3,}/g, '\n\n') // Replace 3+ newlines with 2
            .replace(/[ \t]+/g, ' ')     // Replace multiple spaces/tabs with single space
            .replace(/\n /g, '\n')       // Remove spaces at start of new lines
            .replace(/ \n/g, '\n')       // Remove spaces at end of lines
            .trim();
        
        return processedHtml;
    };

    // Filter options for Select components
    const filterOption = (input: string, option?: { label: string; value: string }) =>
        (option?.label ?? '').toLowerCase().includes(input.toLowerCase());

    // Convert data for Select components
    const statusOptions = policyStatuses.map(status => ({
        label: status.status,
        value: status.id
    }));

    const frameworkOptions = filteredFrameworks.map(framework => ({
        label: framework.organisation_domain ? `${framework.name}(${framework.organisation_domain})` : framework.name,
        value: framework.id
    }));

    const connectionChapterOptions = chapters.map(chapter => ({
        label: chapter.title,
        value: chapter.id
    }));

    const connectionSelectedChapter = chapters.find(ch => ch.id === connectionChapterId);
    const connectionSubchapterOptions = connectionSelectedChapter
        ? [...new Set(connectionSelectedChapter.objectives.map(obj => obj.subchapter).filter(Boolean))].map(subchapter => ({
            label: subchapter as string,
            value: subchapter as string
        }))
        : [];

    const connectionObjectiveItems = connectionFrameworkId
        ? (connectionSelectedChapter ? [connectionSelectedChapter] : chapters)
            .flatMap(chapter =>
                chapter.objectives
                    .filter(obj => !connectionSubchapter || obj.subchapter === connectionSubchapter)
                    .map(obj => ({
                        id: obj.id,
                        title: obj.title,
                        subchapter: obj.subchapter,
                        chapter_title: chapter.title
                    }))
            )
        : [];

    // Filter linked objectives by the selected framework (via chapters which are framework-scoped)
    const frameworkFilteredLinkedObjectives = useMemo(() => {
        if (!connectionFrameworkId || chapters.length === 0) return linkedObjectives;
        const frameworkObjectiveIds = new Set(chapters.flatMap(ch => ch.objectives.map(o => o.id)));
        return linkedObjectives.filter(o => frameworkObjectiveIds.has(o.id));
    }, [connectionFrameworkId, chapters, linkedObjectives]);

    const policyFileOptions = policyFiles.map(file => ({
        label: file.filename,
        value: file.filename
    }));

    // Search filtered policies
    const searchFilteredPolicies = policies.filter(policy =>
        policy.policy_code?.toLowerCase().includes(policySearchText.toLowerCase()) ||
        policy.title?.toLowerCase().includes(policySearchText.toLowerCase()) ||
        policy.status_name?.toLowerCase().includes(policySearchText.toLowerCase()) ||
        policy.body?.toLowerCase().includes(policySearchText.toLowerCase())
    );

    // Status color mapping
    const getStatusColor = (status: string): string => {
        switch (status?.toLowerCase()) {
            case 'approved': return '#52c41a';
            case 'draft': return '#faad14';
            case 'pending': return '#1890ff';
            case 'rejected': return '#ff4d4f';
            case 'archived': return '#8c8c8c';
            default: return '#8c8c8c';
        }
    };

    // Policy Card component
    const PolicyCard = ({ policy }: { policy: any }) => {
        const handleCardClick = () => {
            setSelectedPolicy(policy.id);
            setPolicyTitle(policy.title);
            setPolicyCode(policy.policy_code || '');
            setPolicyBody(policy.body || '');
            setStatusId(policy.status_id);
            setCompanyName(policy.company_name || '');
            if (policy.frameworks && policy.frameworks.length > 0) {
                const selectedFrameworkId = policy.frameworks[0];
                setFrameworkIds(selectedFrameworkId);
            }
            setShowForm(true);
        };

        return (
            <Card
                hoverable
                style={{ height: '100%' }}
                bodyStyle={{ padding: '16px' }}
                onClick={handleCardClick}
            >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 500, flex: 1, marginRight: '8px' }}>
                        {policy.policy_code ? `${policy.policy_code}: ${policy.title}` : policy.title}
                    </h4>
                    <Tag color={getStatusColor(policy.status_name)} style={{ marginLeft: 'auto' }}>
                        {policy.status_name}
                    </Tag>
                </div>

                {policy.framework_names && policy.framework_names.length > 0 && (
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '8px' }}>
                        {policy.framework_names.map((fw: string, idx: number) => (
                            <Tag key={idx} color="blue">{fw}</Tag>
                        ))}
                    </div>
                )}

                {policy.objective_titles && policy.objective_titles.length > 0 && (
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '8px' }}>
                        {policy.objective_titles.slice(0, 2).map((obj: string, idx: number) => (
                            <Tag key={idx} color="purple">{obj}</Tag>
                        ))}
                        {policy.objective_titles.length > 2 && (
                            <Tag color="default">+{policy.objective_titles.length - 2} more</Tag>
                        )}
                    </div>
                )}

                {policy.body && (
                    <p style={{
                        margin: '8px 0 0 0',
                        color: '#8c8c8c',
                        fontSize: '13px',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 3,
                        WebkitBoxOrient: 'vertical',
                    }}>
                        {policy.body}
                    </p>
                )}
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
                            <AuditOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Policy Registration"
                                infoContent={PoliciesInfo}
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
                                key: 'policies',
                                label: (
                                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <UnorderedListOutlined />
                                        Policies
                                        <Tag color="blue">{policies.length}</Tag>
                                    </span>
                                ),
                                children: (
                                    <div className="page-section">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <Input
                                    placeholder="Search policies..."
                                    prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                    value={policySearchText}
                                    onChange={(e) => setPolicySearchText(e.target.value)}
                                    style={{ width: '250px' }}
                                />
                                <div style={{ display: 'flex', border: '1px solid #d9d9d9', borderRadius: '6px', overflow: 'hidden' }}>
                                    <button
                                        onClick={() => setPolicyViewMode('grid')}
                                        style={{
                                            border: 'none',
                                            padding: '6px 12px',
                                            cursor: 'pointer',
                                            backgroundColor: policyViewMode === 'grid' ? '#1890ff' : 'white',
                                            color: policyViewMode === 'grid' ? 'white' : '#595959',
                                        }}
                                    >
                                        <AppstoreOutlined />
                                    </button>
                                    <button
                                        onClick={() => setPolicyViewMode('list')}
                                        style={{
                                            border: 'none',
                                            borderLeft: '1px solid #d9d9d9',
                                            padding: '6px 12px',
                                            cursor: 'pointer',
                                            backgroundColor: policyViewMode === 'list' ? '#1890ff' : 'white',
                                            color: policyViewMode === 'list' ? 'white' : '#595959',
                                        }}
                                    >
                                        <UnorderedListOutlined />
                                    </button>
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                {!showForm && (
                                    <button
                                        className="add-button"
                                        data-tour-id="qs-policy-add-button"
                                        onClick={() => {
                                            handleClear(false);
                                            setShowForm(true);
                                        }}
                                        style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                    >
                                        <PlusOutlined /> Add New Policy
                                    </button>
                                )}
                                <button
                                    className="export-button"
                                    onClick={handleExportToPdf}
                                    disabled={loading || filteredPolicies.length === 0}
                                >
                                    Export to PDF ({filteredPolicies.length})
                                </button>
                            </div>
                        </div>

                        {searchFilteredPolicies.length === 0 ? (
                            <Empty description="No policies found" />
                        ) : policyViewMode === 'grid' ? (
                            <Row gutter={[16, 16]}>
                                {searchFilteredPolicies.map(policy => (
                                    <Col key={policy.id} xs={24} sm={12} md={8} lg={6}>
                                        <PolicyCard policy={policy} />
                                    </Col>
                                ))}
                            </Row>
                        ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <Table
                                columns={PolicyGridColumns(searchFilteredPolicies)}
                                dataSource={searchFilteredPolicies}
                                onChange={handleTableChange}
                                showSorterTooltip={{ target: 'sorter-icon' }}
                                onRow={(record) => {
                                    return {
                                        onClick: () => {
                                            console.log(record);
                                            // Set selected policy
                                            setSelectedPolicy(record.id);
                                            // Populate form fields
                                            setPolicyTitle(record.title);
                                            setPolicyCode(record.policy_code || '');
                                            setPolicyBody(record.body || '');
                                            setStatusId(record.status_id);
                                            setCompanyName(record.company_name || '');

                                            // Show the form when clicking a row to edit
                                            setShowForm(true);
                                        },
                                        style: {
                                            cursor: 'pointer',
                                            backgroundColor: selectedPolicy === record.id ? '#e6f7ff' : undefined
                                        }
                                    };
                                }}
                                rowKey="id"
                                pagination={{
                                    showSizeChanger: true,
                                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} policies`,
                                }}
                            />
                        </div>
                        )}
                                    </div>
                                ),
                            },
                            {
                                key: 'import',
                                label: (
                                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <ImportOutlined />
                                        Import Policies
                                    </span>
                                ),
                                children: (
                                    <div className="page-section">
                                        <PolicyTemplatesSection
                                            onImportComplete={async () => {
                                                await fetchPolicies();
                                                await fetchPolicyTemplates();
                                                setActiveTab('policies');
                                            }}
                                        />
                                    </div>
                                ),
                            },
                            {
                                key: 'connections',
                                label: (
                                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <LinkOutlined />
                                        Connections
                                    </span>
                                ),
                                children: (() => {
                                    const selectedPolicyObj = policies.find(p => p.id === selectedConnectionPolicy);
                                    const policyControlStats = (() => {
                                        const total = linkedControls.length;
                                        const implemented = linkedControls.filter((c: any) => c.control_status_name === 'Implemented').length;
                                        const partial = linkedControls.filter((c: any) => c.control_status_name === 'Partially Implemented').length;
                                        const notImpl = total - implemented - partial;
                                        const coverage = total > 0 ? Math.round((implemented / total) * 100) : 0;
                                        return { total, implemented, partial, notImpl, coverage };
                                    })();

                                    return (
                                    <div className="page-section">
                                        {/* Policy Selector */}
                                        <div style={{ marginBottom: 24 }}>
                                            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                                                Select Policy to Manage Connections
                                            </label>
                                            <Select
                                                showSearch
                                                placeholder="Select a policy..."
                                                options={policies.map(policy => ({
                                                    label: policy.policy_code ? `${policy.policy_code}: ${policy.title}` : policy.title,
                                                    value: policy.id,
                                                }))}
                                                value={selectedConnectionPolicy}
                                                onChange={(value) => setSelectedConnectionPolicy(value)}
                                                filterOption={(input, option) =>
                                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                                }
                                                style={{ width: '100%', maxWidth: 500 }}
                                                allowClear
                                            />
                                        </div>

                                        {selectedConnectionPolicy && selectedPolicyObj ? (
                                            <>
                                                {/* Policy Context Banner */}
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
                                                        <AuditOutlined style={{ fontSize: 22, color: '#fff' }} />
                                                        <div>
                                                            <div style={{ color: '#fff', fontWeight: 600, fontSize: '15px' }}>
                                                                {selectedPolicyObj.policy_code && <span>{selectedPolicyObj.policy_code} — </span>}
                                                                {selectedPolicyObj.title}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                                        {selectedPolicyObj.status_name && (
                                                            <Tag color={getStatusColor(selectedPolicyObj.status_name)} style={{ fontWeight: 600 }}>
                                                                {selectedPolicyObj.status_name}
                                                            </Tag>
                                                        )}
                                                        <Tag color="green">{linkedControls.length} Control{linkedControls.length !== 1 ? 's' : ''}</Tag>
                                                        <Tag color="purple">{linkedObjectives.length} Objective{linkedObjectives.length !== 1 ? 's' : ''}</Tag>
                                                    </div>
                                                </div>

                                                <Row gutter={[24, 24]} align="top">
                                                    {/* Left Column: Stacked Connection Boards */}
                                                    <Col xs={24} lg={12}>
                                                        <div style={{ marginBottom: 16 }}>
                                                            <ConnectionBoard
                                                                title="Controls Governed by Policy"
                                                                sourceLabel="Policy"
                                                                targetLabel="Control"
                                                                relationshipLabel="governs"
                                                                availableItems={controls.map(control => ({
                                                                    id: control.id, code: control.code, name: control.name,
                                                                    category: control.category, control_status_name: control.control_status_name,
                                                                }))}
                                                                linkedItems={linkedControls.map(control => ({
                                                                    id: control.id, code: control.code, name: control.name,
                                                                    category: control.category, control_status_name: control.control_status_name,
                                                                }))}
                                                                loading={false}
                                                                getItemDisplayName={(item) => { const c = item as { code: string; name: string }; return `${c.code}: ${c.name}`; }}
                                                                getItemDescription={(item) => { const c = item as { category?: string | null }; return c.category || null; }}
                                                                getItemTags={(item) => {
                                                                    const c = item as { control_status_name?: string | null };
                                                                    const tags: { label: string; color: string }[] = [];
                                                                    if (c.control_status_name) {
                                                                        const sc: Record<string, string> = { 'Implemented': 'green', 'Partially Implemented': 'orange', 'Not Implemented': 'red', 'N/A': 'default' };
                                                                        tags.push({ label: c.control_status_name, color: sc[c.control_status_name] || 'default' });
                                                                    }
                                                                    return tags;
                                                                }}
                                                                onLink={async (controlIds) => {
                                                                    if (!connectionFrameworkId) { api.warning({ message: 'No Framework Selected', description: 'Select a framework below to manage control connections', duration: 4 }); return; }
                                                                    const { linkControlToPolicy: linkCtrlToPol } = useControlStore.getState();
                                                                    for (const controlId of controlIds) {
                                                                        const success = await linkCtrlToPol(controlId, selectedConnectionPolicy, connectionFrameworkId);
                                                                        if (!success) { api.error({ message: 'Link Failed', description: 'Failed to link control to policy', duration: 4 }); return; }
                                                                    }
                                                                    api.success({ message: 'Controls Linked', description: `Successfully linked ${controlIds.length} control(s) to the policy`, duration: 4 });
                                                                    fetchLinkedControls(selectedConnectionPolicy, connectionFrameworkId);
                                                                }}
                                                                onUnlink={async (controlIds) => {
                                                                    if (!connectionFrameworkId) { api.warning({ message: 'No Framework Selected', description: 'Select a framework below to manage control connections', duration: 4 }); return; }
                                                                    const { unlinkControlFromPolicy: unlinkCtrlFromPol } = useControlStore.getState();
                                                                    for (const controlId of controlIds) {
                                                                        const success = await unlinkCtrlFromPol(controlId, selectedConnectionPolicy, connectionFrameworkId);
                                                                        if (!success) { api.error({ message: 'Unlink Failed', description: 'Failed to unlink control from policy', duration: 4 }); return; }
                                                                    }
                                                                    api.success({ message: 'Controls Unlinked', description: `Successfully unlinked ${controlIds.length} control(s) from the policy`, duration: 4 });
                                                                    fetchLinkedControls(selectedConnectionPolicy, connectionFrameworkId);
                                                                }}
                                                                height={250}
                                                            />
                                                        </div>
                                                        <ConnectionBoard
                                                            title="Objectives Addressed by Policy"
                                                            sourceLabel="Policy"
                                                            targetLabel="Objective"
                                                            relationshipLabel="addresses"
                                                            headerContent={(
                                                                <div className="form-row" style={{ marginBottom: 0 }}>
                                                                    <div className="form-group">
                                                                        <label className="form-label">Framework</label>
                                                                        <Select showSearch placeholder="Select framework" onChange={handleConnectionFrameworkChange} options={frameworkOptions} filterOption={filterOption} value={connectionFrameworkId} allowClear style={{ width: '100%' }} />
                                                                    </div>
                                                                    <div className="form-group">
                                                                        <label className="form-label">Chapter</label>
                                                                        <Select showSearch placeholder="Select chapter" onChange={handleConnectionChapterChange} options={connectionChapterOptions} filterOption={filterOption} value={connectionChapterId} disabled={!connectionFrameworkId} allowClear style={{ width: '100%' }} />
                                                                    </div>
                                                                    <div className="form-group">
                                                                        <label className="form-label">Subchapter</label>
                                                                        <Select showSearch placeholder="Select subchapter" onChange={handleConnectionSubchapterChange} options={connectionSubchapterOptions} filterOption={filterOption} value={connectionSubchapter} disabled={!connectionChapterId} allowClear style={{ width: '100%' }} />
                                                                    </div>
                                                                </div>
                                                            )}
                                                            availableItems={connectionObjectiveItems}
                                                            linkedItems={frameworkFilteredLinkedObjectives.map(objective => ({ id: objective.id, title: objective.title, subchapter: objective.subchapter, chapter_title: objective.chapter_title }))}
                                                            loading={false}
                                                            getItemDisplayName={(item) => { const o = item as { title: string }; return o.title; }}
                                                            getItemDescription={(item) => {
                                                                const o = item as { subchapter?: string | null; chapter_title?: string | null };
                                                                if (o.chapter_title && o.subchapter) return `${o.chapter_title} • ${o.subchapter}`;
                                                                return o.subchapter || o.chapter_title || null;
                                                            }}
                                                            getItemTags={() => []}
                                                            onLink={async (objectiveIds) => {
                                                                const { addObjectiveToPolicy } = usePolicyStore.getState();
                                                                let nextOrder = linkedObjectives.length + 1;
                                                                for (const objectiveId of objectiveIds) {
                                                                    const success = await addObjectiveToPolicy(selectedConnectionPolicy as string, objectiveId, nextOrder);
                                                                    if (!success) { api.error({ message: 'Link Failed', description: 'Failed to link objective to policy', duration: 4 }); return; }
                                                                    nextOrder += 1;
                                                                }
                                                                api.success({ message: 'Objectives Linked', description: `Successfully linked ${objectiveIds.length} objective(s) to the policy`, duration: 4 });
                                                                fetchLinkedObjectives(selectedConnectionPolicy as string);
                                                            }}
                                                            onUnlink={async (objectiveIds) => {
                                                                const { removeObjectiveFromPolicy } = usePolicyStore.getState();
                                                                for (const objectiveId of objectiveIds) {
                                                                    const success = await removeObjectiveFromPolicy(selectedConnectionPolicy as string, objectiveId);
                                                                    if (!success) { api.error({ message: 'Unlink Failed', description: 'Failed to unlink objective from policy', duration: 4 }); return; }
                                                                }
                                                                api.success({ message: 'Objectives Unlinked', description: `Successfully unlinked ${objectiveIds.length} objective(s) from the policy`, duration: 4 });
                                                                fetchLinkedObjectives(selectedConnectionPolicy as string);
                                                            }}
                                                            height={250}
                                                        />
                                                    </Col>

                                                    {/* Right Column: Intelligence Panel */}
                                                    <Col xs={24} lg={12}>
                                                        <Card style={{ borderRadius: '10px', height: '100%' }} bodyStyle={{ padding: 0 }}>
                                                            <Tabs
                                                                defaultActiveKey="controlPosture"
                                                                style={{ padding: '0 16px' }}
                                                                items={[
                                                                    {
                                                                        key: 'controlPosture',
                                                                        label: (
                                                                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                                                <SafetyCertificateOutlined />
                                                                                Control Posture
                                                                                {policyControlStats.total > 0 && <Tag color="green" style={{ marginLeft: 4 }}>{policyControlStats.total}</Tag>}
                                                                            </span>
                                                                        ),
                                                                        children: (
                                                                            <div style={{ paddingBottom: 16 }}>
                                                                                {policyControlStats.total > 0 ? (
                                                                                    <>
                                                                                        <div style={{ marginBottom: 16 }}>
                                                                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                                                                <span style={{ fontWeight: 500, fontSize: 13 }}>Implementation Coverage</span>
                                                                                                <span style={{ fontSize: 13, color: '#8c8c8c' }}>{policyControlStats.coverage}%</span>
                                                                                            </div>
                                                                                            <Progress
                                                                                                percent={policyControlStats.coverage}
                                                                                                strokeColor={policyControlStats.coverage === 100 ? '#52c41a' : policyControlStats.coverage >= 50 ? '#faad14' : '#ff4d4f'}
                                                                                                showInfo={false}
                                                                                                size="small"
                                                                                            />
                                                                                            <div style={{ display: 'flex', gap: '12px', marginTop: 8, fontSize: 12, color: '#595959' }}>
                                                                                                <span><span style={{ color: '#52c41a', fontWeight: 600 }}>{policyControlStats.implemented}</span> Implemented</span>
                                                                                                <span><span style={{ color: '#fa8c16', fontWeight: 600 }}>{policyControlStats.partial}</span> Partial</span>
                                                                                                <span><span style={{ color: '#ff4d4f', fontWeight: 600 }}>{policyControlStats.notImpl}</span> Not Impl.</span>
                                                                                            </div>
                                                                                        </div>
                                                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                                                            {linkedControls.map((control: any) => {
                                                                                                const statusColors: Record<string, string> = { 'Implemented': 'green', 'Partially Implemented': 'orange', 'Not Implemented': 'red', 'N/A': 'default' };
                                                                                                return (
                                                                                                    <div key={control.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', background: '#fafafa', borderRadius: 6, border: '1px solid #f0f0f0' }}>
                                                                                                        <div style={{ flex: 1, minWidth: 0 }}>
                                                                                                            <div style={{ fontWeight: 500, fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{control.code}: {control.name}</div>
                                                                                                            {control.category && <div style={{ fontSize: 11, color: '#8c8c8c', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{control.category}</div>}
                                                                                                        </div>
                                                                                                        <Tag color={statusColors[control.control_status_name] || 'default'} style={{ marginLeft: 8, flexShrink: 0 }}>{control.control_status_name || 'N/A'}</Tag>
                                                                                                    </div>
                                                                                                );
                                                                                            })}
                                                                                        </div>
                                                                                    </>
                                                                                ) : (
                                                                                    <Empty description="No controls linked. Use the board on the left to link controls." image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ margin: '24px 0' }} />
                                                                                )}
                                                                            </div>
                                                                        ),
                                                                    },
                                                                    {
                                                                        key: 'objectives',
                                                                        label: (
                                                                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                                                <BulbOutlined />
                                                                                Objectives
                                                                                {linkedObjectives.length > 0 && <Tag color="purple" style={{ marginLeft: 4 }}>{linkedObjectives.length}</Tag>}
                                                                            </span>
                                                                        ),
                                                                        children: (
                                                                            <div style={{ paddingBottom: 16 }}>
                                                                                {linkedObjectives.length > 0 ? (
                                                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                                                                        {linkedObjectives.map((obj: any) => (
                                                                                            <div key={obj.id} style={{ padding: '8px 12px', background: '#fafafa', borderRadius: 6, border: '1px solid #f0f0f0' }}>
                                                                                                <div style={{ fontWeight: 500, fontSize: 13 }}>{obj.title}</div>
                                                                                                {(obj.chapter_title || obj.subchapter) && (
                                                                                                    <div style={{ fontSize: 11, color: '#8c8c8c', marginTop: 2 }}>
                                                                                                        {obj.chapter_title}{obj.chapter_title && obj.subchapter ? ' • ' : ''}{obj.subchapter}
                                                                                                    </div>
                                                                                                )}
                                                                                            </div>
                                                                                        ))}
                                                                                    </div>
                                                                                ) : (
                                                                                    <Empty description="No objectives linked. Use the board on the left to link objectives." image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ margin: '24px 0' }} />
                                                                                )}
                                                                            </div>
                                                                        ),
                                                                    },
                                                                    {
                                                                        key: 'profile',
                                                                        label: (
                                                                            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                                                                <AuditOutlined />
                                                                                Policy Profile
                                                                            </span>
                                                                        ),
                                                                        children: (
                                                                            <div style={{ paddingBottom: 16 }}>
                                                                                <div style={{ display: 'flex', gap: '8px', marginBottom: 16, flexWrap: 'wrap' }}>
                                                                                    <Tag color="green">{linkedControls.length} Control{linkedControls.length !== 1 ? 's' : ''}</Tag>
                                                                                    <Tag color="purple">{linkedObjectives.length} Objective{linkedObjectives.length !== 1 ? 's' : ''}</Tag>
                                                                                </div>

                                                                                <div style={{ marginBottom: 16 }}>
                                                                                    <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Status</div>
                                                                                    <Tag color={getStatusColor(selectedPolicyObj.status_name || '')}>{selectedPolicyObj.status_name || 'Unknown'}</Tag>
                                                                                </div>

                                                                                {selectedPolicyObj.body && (
                                                                                    <div style={{ marginBottom: 16 }}>
                                                                                        <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Body</div>
                                                                                        <div style={{ fontSize: 13, color: '#262626', lineHeight: 1.6, maxHeight: 200, overflow: 'auto' }}>{selectedPolicyObj.body}</div>
                                                                                    </div>
                                                                                )}

                                                                                {selectedPolicyObj.framework_names && selectedPolicyObj.framework_names.length > 0 && (
                                                                                    <div style={{ marginBottom: 16 }}>
                                                                                        <div style={{ fontWeight: 600, fontSize: 13, color: '#8c8c8c', marginBottom: 4 }}>Frameworks</div>
                                                                                        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                                                                                            {selectedPolicyObj.framework_names.map((fw: string, idx: number) => (
                                                                                                <Tag key={idx} color="blue">{fw}</Tag>
                                                                                            ))}
                                                                                        </div>
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
                                                                        children: (() => {
                                                                            const linkedObjectiveIds = new Set(linkedObjectives.map((o: any) => o.id));

                                                                            const unlinkedObjectives = chapters.flatMap(chapter =>
                                                                                chapter.objectives
                                                                                    .filter(obj => !linkedObjectiveIds.has(obj.id))
                                                                                    .map(obj => ({
                                                                                        id: obj.id,
                                                                                        title: obj.title,
                                                                                        subchapter: obj.subchapter,
                                                                                        chapter_title: chapter.title,
                                                                                    }))
                                                                            );

                                                                            // Keyword relevance filtering
                                                                            const sourceTexts = [
                                                                                selectedPolicyObj?.title,
                                                                                selectedPolicyObj?.body,
                                                                                selectedPolicyObj?.policy_code,
                                                                            ];
                                                                            const { relevant: relevantObjectives, other: otherObjectives } = filterByRelevance(
                                                                                unlinkedObjectives,
                                                                                sourceTexts,
                                                                                (obj) => [obj.title, obj.chapter_title, obj.subchapter],
                                                                            );

                                                                            // Framework selector options from the policy's linked frameworks
                                                                            const policyFrameworkOptions = (selectedPolicyObj?.frameworks || []).map((fwId: string) => {
                                                                                const fw = frameworks.find(f => f.id === fwId);
                                                                                return { label: fw ? fw.name : fwId, value: fwId };
                                                                            });

                                                                            const renderObjectiveItem = (obj: typeof unlinkedObjectives[number]) => (
                                                                                <div key={obj.id} style={{
                                                                                    border: '1px solid #f0f0f0',
                                                                                    borderRadius: 8,
                                                                                    padding: '12px 16px',
                                                                                    display: 'flex',
                                                                                    alignItems: 'center',
                                                                                    justifyContent: 'space-between',
                                                                                    gap: 12,
                                                                                }}>
                                                                                    <div style={{ flex: 1, minWidth: 0 }}>
                                                                                        <div style={{ fontWeight: 500, fontSize: 13 }}>{obj.title}</div>
                                                                                        {(obj.chapter_title || obj.subchapter) && (
                                                                                            <div style={{ fontSize: 11, color: '#8c8c8c' }}>
                                                                                                {obj.chapter_title}{obj.chapter_title && obj.subchapter ? ' - ' : ''}{obj.subchapter}
                                                                                            </div>
                                                                                        )}
                                                                                    </div>
                                                                                    <Button
                                                                                        type="primary"
                                                                                        ghost
                                                                                        size="small"
                                                                                        loading={policyRecommendationLoading[obj.id]}
                                                                                        onClick={() => handleLinkRecommendedObjective(obj.id)}
                                                                                        style={{ flexShrink: 0 }}
                                                                                    >
                                                                                        Link
                                                                                    </Button>
                                                                                </div>
                                                                            );

                                                                            return (
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
                                                                                            Link framework objectives to this policy to define compliance scope. Objectives matching this policy's content are shown first.
                                                                                        </div>
                                                                                    </div>

                                                                                    {selectedPolicyObj?.frameworks && selectedPolicyObj.frameworks.length > 0 ? (
                                                                                        <>
                                                                                            {/* Framework Filter */}
                                                                                            {policyFrameworkOptions.length > 1 && (
                                                                                                <div style={{ marginBottom: 12 }}>
                                                                                                    <Select
                                                                                                        placeholder="Filter by framework"
                                                                                                        options={policyFrameworkOptions}
                                                                                                        value={policyRecommendationFrameworkFilter}
                                                                                                        onChange={(value) => {
                                                                                                            setPolicyRecommendationFrameworkFilter(value);
                                                                                                            if (value) fetchChaptersWithObjectives(value, craOperatorRole || undefined);
                                                                                                        }}
                                                                                                        style={{ width: '100%' }}
                                                                                                        size="small"
                                                                                                    />
                                                                                                </div>
                                                                                            )}

                                                                                            {/* Unlinked Objectives */}
                                                                                            {unlinkedObjectives.length > 0 ? (
                                                                                                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                                                                    {relevantObjectives.length > 0 && (
                                                                                                        <>
                                                                                                            <div style={{ fontSize: 12, fontWeight: 600, color: '#1890ff', marginBottom: 4 }}>
                                                                                                                Relevant to this policy ({relevantObjectives.length})
                                                                                                            </div>
                                                                                                            {relevantObjectives.map(renderObjectiveItem)}
                                                                                                        </>
                                                                                                    )}
                                                                                                    {otherObjectives.length > 0 && (
                                                                                                        <Collapse
                                                                                                            ghost
                                                                                                            size="small"
                                                                                                            style={{ marginTop: relevantObjectives.length > 0 ? 8 : 0 }}
                                                                                                            items={[{
                                                                                                                key: 'other',
                                                                                                                label: <span style={{ fontSize: 12, color: '#8c8c8c' }}>
                                                                                                                    {relevantObjectives.length > 0 ? `Other objectives (${otherObjectives.length})` : `All objectives (${otherObjectives.length})`}
                                                                                                                </span>,
                                                                                                                children: (
                                                                                                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                                                                                                                        {otherObjectives.map(renderObjectiveItem)}
                                                                                                                    </div>
                                                                                                                ),
                                                                                                            }]}
                                                                                                        />
                                                                                                    )}
                                                                                                </div>
                                                                                            ) : (
                                                                                                <Empty description="All objectives from this framework are already linked" image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ margin: '24px 0' }} />
                                                                                            )}
                                                                                        </>
                                                                                    ) : (
                                                                                        <Empty description="No frameworks linked to this policy. Link frameworks first using the Objectives board." image={Empty.PRESENTED_IMAGE_SIMPLE} style={{ margin: '24px 0' }} />
                                                                                    )}
                                                                                </div>
                                                                            );
                                                                        })(),
                                                                    },
                                                                ]}
                                                            />
                                                        </Card>
                                                    </Col>
                                                </Row>
                                            </>
                                        ) : (
                                            <Empty
                                                description="Select a policy to manage its connections"
                                                style={{ marginTop: 60 }}
                                            />
                                        )}
                                    </div>
                                    );
                                })(),
                            },
                        ]}
                    />

                    {/* Policy Registration Modal */}
                    <Modal
                        title={
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {selectedPolicy ? (
                                    <EditOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                                ) : (
                                    <PlusOutlined style={{ fontSize: '20px', color: '#52c41a' }} />
                                )}
                                <span>{selectedPolicy ? 'Edit Policy' : 'Add New Policy'}</span>
                                {selectedPolicy && <Tag color="blue">Editing</Tag>}
                            </div>
                        }
                        open={showForm}
                        onCancel={() => handleClear(true)}
                        width={1000}
                        footer={
                            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                {selectedPolicy && (
                                    <button
                                        className="delete-button"
                                        onClick={handleDelete}
                                        disabled={loading}
                                        style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f', color: 'white' }}
                                    >
                                        Delete Policy
                                    </button>
                                )}
                                {selectedPolicy && (
                                    <button
                                        className="secondary-button"
                                        onClick={() => handleClear(false)}
                                        disabled={loading}
                                    >
                                        Create New Instead
                                    </button>
                                )}
                                <button
                                    className="secondary-button"
                                    onClick={() => handleClear(true)}
                                    disabled={loading}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="add-button"
                                    onClick={handleSave}
                                    disabled={loading}
                                    style={{
                                        backgroundColor: selectedPolicy ? '#1890ff' : '#52c41a',
                                        borderColor: selectedPolicy ? '#1890ff' : '#52c41a'
                                    }}
                                >
                                    {loading ? 'Saving...' : selectedPolicy ? 'Update Policy' : 'Save Policy'}
                                </button>
                            </div>
                        }
                    >
                        <p style={{ color: '#8c8c8c', fontSize: '14px', marginBottom: '24px' }}>
                            {selectedPolicy
                                ? 'Update the policy details below and click "Update Policy" to save changes.'
                                : 'Fill out the form below to register a new policy.'}
                        </p>

                        <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap' }}>
                            <div style={{ flex: '1 1 500px', minWidth: '0', maxWidth: '100%' }}>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label required">Status</label>
                                        <Select
                                            showSearch
                                            placeholder="Select status"
                                            onChange={(value) => setStatusId(value)}
                                            options={statusOptions}
                                            filterOption={filterOption}
                                            value={statusId}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label required">Code</label>
                                        <input
                                            type="text"
                                            className="form-input"
                                            placeholder="e.g., HRM-1 or ORG-POL-01"
                                            value={policyCode}
                                            onChange={(e) => setPolicyCode(e.target.value)}
                                        />
                                    </div>
                                </div>
                                <div style={{ marginTop: '6px', color: '#8c8c8c', fontSize: '12px' }}>
                                    Link this policy to frameworks and objectives from the Connections tab after saving.
                                </div>
                                {/* Policy Content */}
                                <div className="form-row">
                                    <div className="form-group" style={{ width: '100%' }}>
                                        <label className="form-label required">Title</label>
                                        <input
                                            type="text"
                                            className="form-input"
                                            placeholder="Enter policy title"
                                            value={policyTitle}
                                            onChange={(e) => setPolicyTitle(e.target.value)}
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group" style={{ width: '100%' }}>
                                        <label className="form-label">Body</label>
                                        <textarea
                                            className="large-textarea"
                                            placeholder="Enter policy body content"
                                            value={policyBody}
                                            onChange={(e) => setPolicyBody(e.target.value)}
                                            style={{
                                                fontFamily: 'inherit',
                                                lineHeight: '1.6'
                                            }}
                                        />
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group" style={{ width: '100%' }}>
                                        <label className="form-label">Policy Templates</label>
                                        <Select
                                            showSearch
                                            placeholder="Select a policy template to preview"
                                            onChange={handlePolicyFileChange}
                                            options={policyFileOptions}
                                            filterOption={filterOption}
                                            value={selectedPolicyFile}
                                            allowClear
                                            style={{ width: '100%' }}
                                        />
                                    </div>
                                </div>

                                {selectedFilePreview && (
                                    <div style={{ marginTop: '24px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                                            <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>
                                                Policy Preview - {selectedFilePreview.filename}
                                            </h4>
                                            <div style={{ display: 'flex', gap: '8px' }}>
                                                <button
                                                    className="add-button"
                                                    onClick={handleCopyToBody}
                                                    style={{ fontSize: '12px', padding: '6px 12px' }}
                                                >
                                                    Copy to Body
                                                </button>
                                            </div>
                                        </div>
                                        <div
                                            style={{
                                                width: '100%',
                                                height: '300px',
                                                border: '1px solid #e8e8e8',
                                                borderRadius: '6px',
                                                padding: '16px',
                                                overflow: 'auto',
                                                backgroundColor: '#fafafa',
                                                fontSize: '14px',
                                                lineHeight: '1.6'
                                            }}
                                            dangerouslySetInnerHTML={{ __html: selectedFilePreview.html_content }}
                                        />
                                        {selectedFilePreview.conversion_messages.length > 0 && (
                                            <div style={{ marginTop: '12px', padding: '12px', backgroundColor: '#f0f8ff', border: '1px solid #d6e7ff', borderRadius: '6px' }}>
                                                <strong style={{ fontSize: '14px', color: '#0f386a' }}>Conversion notes:</strong>
                                                <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px', fontSize: '13px', color: '#8c8c8c' }}>
                                                    {selectedFilePreview.conversion_messages.map((message, index) => (
                                                        <li key={index}>{message}</li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Parameters Section */}
                            <div style={{ flex: '0 0 280px', minWidth: '0', maxWidth: '100%' }}>
                                <div style={{ border: '1px solid #e8e8e8', borderRadius: '8px', padding: '20px', backgroundColor: '#fafafa' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                        <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '600', color: '#262626' }}>
                                            Parameters
                                        </h4>
                                        <button
                                            className="secondary-button"
                                            onClick={handleSaveParameters}
                                            disabled={loading}
                                            style={{ fontSize: '12px', padding: '6px 12px' }}
                                        >
                                            Save
                                        </button>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Company Name</label>
                                        <input
                                            type="text"
                                            className="form-input"
                                            placeholder="Enter company name parameter"
                                            value={companyName}
                                            onChange={(e) => setCompanyName(e.target.value)}
                                            style={{ width: '100%' }}
                                        />
                                        <p style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '4px', marginBottom: 0 }}>
                                            This parameter will be used to replace automatically all 'p_company_name' that will be found inside the body.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Modal>
                </div>
            </div>
        </div>
    );
};

export default PolicyRegistrationPage;
