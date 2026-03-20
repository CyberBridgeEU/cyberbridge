import { Table, notification, Modal, Tag, Upload, message, Select, Input, Checkbox, Spin, InputNumber } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { BankOutlined, PlusOutlined, EditOutlined, UploadOutlined, DeleteOutlined, RobotOutlined, CloudUploadOutlined, DownloadOutlined, ReloadOutlined, SettingOutlined } from '@ant-design/icons';
import useUserStore from "../store/useUserStore.ts";
import useBackupStore from "../store/useBackupStore.ts";
import { useEffect, useState } from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import { ManageOrganisationsInfo } from "../constants/infoContent.tsx";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import useAuthStore from "../store/useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import type { UploadProps } from 'antd';

const OrganizationsPage = () => {
    // Menu highlighting
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Store access
    const {
        organisations,
        fetchOrganisations,
        createOrUpdateOrganisation,
        deleteOrganisation,
        current_user,
        loading,
        error
    } = useUserStore();

    const { getAuthHeader } = useAuthStore();

    // Backup store
    const {
        config: backupConfig,
        backups,
        loading: backupLoading,
        fetchConfig: fetchBackupConfig,
        updateConfig: updateBackupConfig,
        fetchBackups,
        createBackup,
        downloadBackup,
        deleteBackup,
        restoreBackup
    } = useBackupStore();

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    // Selected organization state
    const [selectedOrganization, setSelectedOrganization] = useState<string | null>(null);

    // Form visibility state
    const [showForm, setShowForm] = useState<boolean>(false);

    // Form state
    const [orgName, setOrgName] = useState('');
    const [orgDomain, setOrgDomain] = useState('');
    const [orgLogo, setOrgLogo] = useState('');

    // Organization AI Provider configuration states
    const [orgAiProvider, setOrgAiProvider] = useState<string>('llamacpp');
    const [orgAiEnabled, setOrgAiEnabled] = useState<boolean>(false);
    const [orgQlonUrl, setOrgQlonUrl] = useState<string>('');
    const [orgQlonApiKey, setOrgQlonApiKey] = useState<string>('');
    const [orgQlonUseTools, setOrgQlonUseTools] = useState<boolean>(true);
    // OpenAI (ChatGPT) configuration
    const [orgOpenaiApiKey, setOrgOpenaiApiKey] = useState<string>('');
    const [orgOpenaiModel, setOrgOpenaiModel] = useState<string>('gpt-4o');
    const [orgOpenaiBaseUrl, setOrgOpenaiBaseUrl] = useState<string>('');
    // Anthropic (Claude) configuration
    const [orgAnthropicApiKey, setOrgAnthropicApiKey] = useState<string>('');
    const [orgAnthropicModel, setOrgAnthropicModel] = useState<string>('claude-sonnet-4-20250514');
    // X AI (Grok) configuration
    const [orgXaiApiKey, setOrgXaiApiKey] = useState<string>('');
    const [orgXaiModel, setOrgXaiModel] = useState<string>('grok-3');
    const [orgXaiBaseUrl, setOrgXaiBaseUrl] = useState<string>('');
    // Google (Gemini) configuration
    const [orgGoogleApiKey, setOrgGoogleApiKey] = useState<string>('');
    const [orgGoogleModel, setOrgGoogleModel] = useState<string>('gemini-2.0-flash');
    const [isLoadingOrgAiConfig, setIsLoadingOrgAiConfig] = useState<boolean>(false);
    const [isSavingOrgAiConfig, setIsSavingOrgAiConfig] = useState<boolean>(false);
    const [orgHasAiConfig, setOrgHasAiConfig] = useState<boolean>(false);

    // AI Remediator states
    const [orgAiRemediatorEnabled, setOrgAiRemediatorEnabled] = useState<boolean>(false);
    const [orgRemediatorPromptZap, setOrgRemediatorPromptZap] = useState<string>('');
    const [orgRemediatorPromptNmap, setOrgRemediatorPromptNmap] = useState<string>('');
    const [showZapPromptEditor, setShowZapPromptEditor] = useState<boolean>(false);
    const [showNmapPromptEditor, setShowNmapPromptEditor] = useState<boolean>(false);

    // Org admin logo upload states
    const [isUploadingOrgLogo, setIsUploadingOrgLogo] = useState<boolean>(false);
    const [isDeletingOrgLogo, setIsDeletingOrgLogo] = useState<boolean>(false);

    // Backup & Restore states
    const [backupEnabled, setBackupEnabled] = useState<boolean>(true);
    const [backupFrequency, setBackupFrequency] = useState<string>('monthly');
    const [backupRetentionYears, setBackupRetentionYears] = useState<number>(10);
    const [isCreatingBackup, setIsCreatingBackup] = useState<boolean>(false);
    const [restoreModalVisible, setRestoreModalVisible] = useState<boolean>(false);
    const [selectedBackupForRestore, setSelectedBackupForRestore] = useState<string | null>(null);
    const [isRestoring, setIsRestoring] = useState<boolean>(false);

    // Determine if user is super_admin
    const isSuperAdmin = current_user?.role_name === 'super_admin';
    const isOrgAdmin = current_user?.role_name === 'org_admin';

    // Get current user's organization for org_admin view
    const currentUserOrg = isOrgAdmin
        ? organisations.find(org => org.id === current_user?.organisation_id)
        : null;

    // Fetch organizations on component mount
    useEffect(() => {
        const fetchData = async () => {
            await fetchOrganisations();
        };
        fetchData();
    }, [fetchOrganisations]);

    // For org_admin: automatically load their organization's data
    useEffect(() => {
        if (isOrgAdmin && current_user?.organisation_id) {
            // Load AI config and backup config for org_admin's organization
            fetchOrgAiConfig(current_user.organisation_id);
            fetchBackupConfig(current_user.organisation_id);
            fetchBackups(current_user.organisation_id);
        }
    }, [isOrgAdmin, current_user?.organisation_id]);

    // Update backup state when config is loaded
    useEffect(() => {
        if (backupConfig) {
            setBackupEnabled(backupConfig.backup_enabled);
            setBackupFrequency(backupConfig.backup_frequency);
            setBackupRetentionYears(backupConfig.backup_retention_years);
        }
    }, [backupConfig]);

    // Fetch org AI configuration when organization is selected (for super_admin modal)
    useEffect(() => {
        if (selectedOrganization && showForm) {
            fetchOrgAiConfig(selectedOrganization);
        } else if (!isOrgAdmin) {
            resetOrgAiConfigState();
        }
    }, [selectedOrganization, showForm]);

    // Filter organizations based on role
    const displayedOrganizations = isSuperAdmin
        ? organisations
        : organisations.filter(org => org.id === current_user?.organisation_id);

    // Reset AI config state
    const resetOrgAiConfigState = () => {
        setOrgAiProvider('llamacpp');
        setOrgAiEnabled(false);
        setOrgQlonUrl('');
        setOrgQlonApiKey('');
        setOrgQlonUseTools(true);
        setOrgOpenaiApiKey('');
        setOrgOpenaiModel('gpt-4o');
        setOrgOpenaiBaseUrl('');
        setOrgAnthropicApiKey('');
        setOrgAnthropicModel('claude-sonnet-4-20250514');
        setOrgXaiApiKey('');
        setOrgXaiModel('grok-3');
        setOrgXaiBaseUrl('');
        setOrgGoogleApiKey('');
        setOrgGoogleModel('gemini-2.0-flash');
        setOrgHasAiConfig(false);
        setOrgAiRemediatorEnabled(false);
        setOrgRemediatorPromptZap('');
        setOrgRemediatorPromptNmap('');
        setShowZapPromptEditor(false);
        setShowNmapPromptEditor(false);
    };

    // Fetch org AI config
    const fetchOrgAiConfig = async (organisationId: string) => {
        setIsLoadingOrgAiConfig(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/settings/org-llm/${organisationId}`,
                {
                    headers: {
                        ...getAuthHeader()
                    }
                }
            );

            if (response.ok) {
                const config = await response.json();
                setOrgAiProvider(config.llm_provider || 'llamacpp');
                setOrgAiEnabled(config.is_enabled ?? true);
                setOrgQlonUrl(config.qlon_url || '');
                setOrgQlonApiKey(config.qlon_api_key || '');
                setOrgQlonUseTools(config.qlon_use_tools ?? true);
                setOrgOpenaiApiKey(config.openai_api_key || '');
                setOrgOpenaiModel(config.openai_model || 'gpt-4o');
                setOrgOpenaiBaseUrl(config.openai_base_url || '');
                setOrgAnthropicApiKey(config.anthropic_api_key || '');
                setOrgAnthropicModel(config.anthropic_model || 'claude-sonnet-4-20250514');
                setOrgXaiApiKey(config.xai_api_key || '');
                setOrgXaiModel(config.xai_model || 'grok-3');
                setOrgXaiBaseUrl(config.xai_base_url || '');
                setOrgGoogleApiKey(config.google_api_key || '');
                setOrgGoogleModel(config.google_model || 'gemini-2.0-flash');
                setOrgAiRemediatorEnabled(config.ai_remediator_enabled ?? false);
                setOrgRemediatorPromptZap(config.remediator_prompt_zap || '');
                setOrgRemediatorPromptNmap(config.remediator_prompt_nmap || '');
                setOrgHasAiConfig(true);
            } else if (response.status === 404) {
                resetOrgAiConfigState();
            } else {
                throw new Error('Failed to fetch organization AI configuration');
            }
        } catch (error) {
            console.error('Error fetching org AI config:', error);
            resetOrgAiConfigState();
        } finally {
            setIsLoadingOrgAiConfig(false);
        }
    };

    // Save org AI config
    const handleSaveOrgAiConfig = async (orgId?: string) => {
        const targetOrgId = orgId || selectedOrganization || current_user?.organisation_id;
        if (!targetOrgId) {
            api.error({
                message: 'No Organization Selected',
                description: 'Please select an organization first.',
                duration: 4,
            });
            return;
        }

        // Validate required fields based on selected provider
        if (orgAiProvider === 'qlon' && (!orgQlonUrl || !orgQlonApiKey)) {
            api.error({
                message: 'Missing QLON Configuration',
                description: 'QLON URL and API Key are required when using QLON Ai provider.',
                duration: 4,
            });
            return;
        }

        if (orgAiProvider === 'openai' && !orgOpenaiApiKey) {
            api.error({
                message: 'Missing OpenAI Configuration',
                description: 'OpenAI API Key is required when using ChatGPT provider.',
                duration: 4,
            });
            return;
        }

        if (orgAiProvider === 'anthropic' && !orgAnthropicApiKey) {
            api.error({
                message: 'Missing Anthropic Configuration',
                description: 'Anthropic API Key is required when using Claude provider.',
                duration: 4,
            });
            return;
        }

        if (orgAiProvider === 'xai' && !orgXaiApiKey) {
            api.error({
                message: 'Missing X AI Configuration',
                description: 'X AI API Key is required when using Grok provider.',
                duration: 4,
            });
            return;
        }

        if (orgAiProvider === 'google' && !orgGoogleApiKey) {
            api.error({
                message: 'Missing Google Configuration',
                description: 'Google API Key is required when using Gemini provider.',
                duration: 4,
            });
            return;
        }

        setIsSavingOrgAiConfig(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/settings/org-llm/${targetOrgId}`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        ...getAuthHeader()
                    },
                    body: JSON.stringify({
                        llm_provider: orgAiProvider,
                        is_enabled: orgAiEnabled,
                        qlon_url: orgQlonUrl || null,
                        qlon_api_key: orgQlonApiKey || null,
                        qlon_use_tools: orgQlonUseTools,
                        openai_api_key: orgOpenaiApiKey || null,
                        openai_model: orgOpenaiModel || 'gpt-4o',
                        openai_base_url: orgOpenaiBaseUrl || null,
                        anthropic_api_key: orgAnthropicApiKey || null,
                        anthropic_model: orgAnthropicModel || 'claude-sonnet-4-20250514',
                        xai_api_key: orgXaiApiKey || null,
                        xai_model: orgXaiModel || 'grok-3',
                        xai_base_url: orgXaiBaseUrl || null,
                        google_api_key: orgGoogleApiKey || null,
                        google_model: orgGoogleModel || 'gemini-2.0-flash',
                        ai_remediator_enabled: orgAiRemediatorEnabled,
                        remediator_prompt_zap: orgRemediatorPromptZap || null,
                        remediator_prompt_nmap: orgRemediatorPromptNmap || null
                    })
                }
            );

            if (response.ok) {
                setOrgHasAiConfig(true);
                api.success({
                    message: 'AI Configuration Saved',
                    description: 'AI provider settings for this organization have been saved successfully.',
                    duration: 4,
                });
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to save AI configuration');
            }
        } catch (error) {
            api.error({
                message: 'Save Failed',
                description: error instanceof Error ? error.message : 'Failed to save AI configuration. Please try again.',
                duration: 4,
            });
        } finally {
            setIsSavingOrgAiConfig(false);
        }
    };

    // Delete org AI config
    const handleDeleteOrgAiConfig = async (orgId?: string) => {
        const targetOrgId = orgId || selectedOrganization || current_user?.organisation_id;
        if (!targetOrgId) return;

        if (!window.confirm('Are you sure you want to delete this organization\'s AI configuration? The organization will use global default settings instead.')) {
            return;
        }

        setIsSavingOrgAiConfig(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/settings/org-llm/${targetOrgId}`,
                {
                    method: 'DELETE',
                    headers: {
                        ...getAuthHeader()
                    }
                }
            );

            if (response.ok) {
                resetOrgAiConfigState();
                api.success({
                    message: 'AI Configuration Deleted',
                    description: 'Organization will now use global default AI settings.',
                    duration: 4,
                });
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to delete AI configuration');
            }
        } catch (error) {
            api.error({
                message: 'Delete Failed',
                description: error instanceof Error ? error.message : 'Failed to delete AI configuration. Please try again.',
                duration: 4,
            });
        } finally {
            setIsSavingOrgAiConfig(false);
        }
    };

    // Backup handlers
    const handleSaveBackupConfig = async () => {
        const orgId = current_user?.organisation_id;
        if (!orgId) return;

        const success = await updateBackupConfig(orgId, {
            backup_enabled: backupEnabled,
            backup_frequency: backupFrequency,
            backup_retention_years: backupRetentionYears
        });

        if (success) {
            api.success({
                message: 'Backup Settings Saved',
                description: 'Backup configuration has been updated successfully.',
                duration: 4,
            });
        } else {
            api.error({
                message: 'Save Failed',
                description: 'Failed to save backup settings.',
                duration: 4,
            });
        }
    };

    const handleCreateBackup = async () => {
        const orgId = current_user?.organisation_id;
        if (!orgId) return;

        setIsCreatingBackup(true);
        const result = await createBackup(orgId);
        setIsCreatingBackup(false);

        if (result) {
            api.success({
                message: 'Backup Created',
                description: 'Manual backup has been created successfully.',
                duration: 4,
            });
        } else {
            api.error({
                message: 'Backup Failed',
                description: 'Failed to create backup.',
                duration: 4,
            });
        }
    };

    const handleRestoreBackup = async () => {
        if (!current_user || !selectedBackupForRestore) return;

        setIsRestoring(true);
        const result = await restoreBackup(current_user.organisation_id, selectedBackupForRestore);
        setIsRestoring(false);

        if (result?.success) {
            setRestoreModalVisible(false);
            setSelectedBackupForRestore(null);
            api.success({
                message: 'Restore Completed',
                description: result.message,
                duration: 4,
            });
        } else {
            api.error({
                message: 'Restore Failed',
                description: result?.error || 'Failed to restore from backup.',
                duration: 4,
            });
        }
    };

    // Handle form submission (for super_admin modal)
    const handleSave = async () => {
        if (!orgName) {
            api.error({
                message: 'Organization Operation Failed',
                description: 'Please enter an organization name',
                duration: 4,
            });
            return;
        }

        const isUpdate = selectedOrganization !== null;
        const success = await createOrUpdateOrganisation(
            orgName,
            orgDomain,
            orgLogo,
            isUpdate ? selectedOrganization : null
        );

        if (success) {
            api.success({
                message: isUpdate ? 'Organization Update Success' : 'Organization Creation Success',
                description: isUpdate ? 'Organization updated successfully' : 'Organization created successfully',
                duration: 4,
            });
            handleClear(true);
            await fetchOrganisations();
        } else {
            api.error({
                message: isUpdate ? 'Organization Update Failed' : 'Organization Creation Failed',
                description: error || (isUpdate ? 'Failed to update organization' : 'Failed to create organization'),
                duration: 4,
            });
        }
    };

    // Clear form
    const handleClear = (hideForm: boolean = false) => {
        setOrgName('');
        setOrgDomain('');
        setOrgLogo('');
        setSelectedOrganization(null);
        resetOrgAiConfigState();
        if (hideForm) {
            setShowForm(false);
        }
    };

    // Handle organization deletion
    const handleDelete = async () => {
        if (!selectedOrganization) {
            api.error({
                message: 'Organization Deletion Failed',
                description: 'Please select an organization to delete',
                duration: 4,
            });
            return;
        }

        if (selectedOrganization === current_user?.organisation_id) {
            api.error({
                message: 'Organization Deletion Failed',
                description: 'You cannot delete your own organization',
                duration: 4,
            });
            return;
        }

        const success = await deleteOrganisation(selectedOrganization);

        if (success) {
            api.success({
                message: 'Organization Deletion Success',
                description: 'Organization deleted successfully',
                duration: 4,
            });
            handleClear(true);
            await fetchOrganisations();
        } else {
            api.error({
                message: 'Organization Deletion Failed',
                description: error || 'Failed to delete organization. It may have associated data.',
                duration: 4,
            });
        }
    };

    // Org admin logo upload handler
    const handleOrgAdminLogoUpload = async (file: File) => {
        if (!current_user?.organisation_id) return false;
        const authHeader = getAuthHeader();
        if (!authHeader) return false;

        setIsUploadingOrgLogo(true);
        try {
            const base64Logo = await new Promise<string>((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result as string);
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });

            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/create_organisation`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeader },
                body: JSON.stringify({
                    id: current_user.organisation_id,
                    name: currentUserOrg?.name || '',
                    domain: currentUserOrg?.domain || '',
                    logo: base64Logo,
                }),
            });

            if (response.ok) {
                api.success({ message: 'Logo Uploaded', description: 'Organization logo has been updated.', duration: 4 });
                await fetchOrganisations();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to upload logo');
            }
        } catch (error) {
            api.error({ message: 'Logo Upload Failed', description: error instanceof Error ? error.message : 'Failed to upload logo.', duration: 4 });
        } finally {
            setIsUploadingOrgLogo(false);
        }
        return false;
    };

    // Org admin logo delete handler
    const handleOrgAdminLogoDelete = async () => {
        if (!current_user?.organisation_id) return;
        const authHeader = getAuthHeader();
        if (!authHeader) return;

        setIsDeletingOrgLogo(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/create_organisation`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...authHeader },
                body: JSON.stringify({
                    id: current_user.organisation_id,
                    name: currentUserOrg?.name || '',
                    domain: currentUserOrg?.domain || '',
                    logo: null,
                }),
            });

            if (response.ok) {
                api.success({ message: 'Logo Deleted', description: 'Organization logo has been removed.', duration: 4 });
                await fetchOrganisations();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to delete logo');
            }
        } catch (error) {
            api.error({ message: 'Logo Deletion Failed', description: error instanceof Error ? error.message : 'Failed to delete logo.', duration: 4 });
        } finally {
            setIsDeletingOrgLogo(false);
        }
    };

    // Logo upload props
    const uploadProps: UploadProps = {
        name: 'file',
        accept: 'image/*',
        showUploadList: false,
        beforeUpload(file) {
            if (file.size > 2 * 1024 * 1024) {
                message.error('Logo must be under 2MB.');
                return false;
            }
            const reader = new FileReader();
            reader.onload = () => {
                setOrgLogo(reader.result as string);
                message.success(`${file.name} loaded successfully`);
            };
            reader.onerror = () => message.error(`${file.name} failed to load.`);
            reader.readAsDataURL(file);
            return false; // prevent auto-upload
        },
    };

    // Table columns for super_admin
    const columns = [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            sorter: (a: any, b: any) => a.name.localeCompare(b.name),
        },
        {
            title: 'Domain',
            dataIndex: 'domain',
            key: 'domain',
            sorter: (a: any, b: any) => (a.domain || '').localeCompare(b.domain || ''),
        },
        {
            title: 'Logo',
            dataIndex: 'logo',
            key: 'logo',
            render: (logo: string) => logo ? (
                <img
                    src={logo}
                    alt="Organization Logo"
                    style={{ height: '32px', maxWidth: '80px', objectFit: 'contain' }}
                    onError={(e) => {
                        e.currentTarget.style.display = 'none';
                    }}
                />
            ) : (
                <span style={{ color: '#8c8c8c' }}>No logo</span>
            ),
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 100,
            render: (_: any, record: any) => (
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        className="secondary-button"
                        onClick={(e) => {
                            e.stopPropagation();
                            setSelectedOrganization(record.id);
                            setOrgName(record.name);
                            setOrgDomain(record.domain || '');
                            setOrgLogo(record.logo || '');
                            setShowForm(true);
                        }}
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                    >
                        <EditOutlined />
                    </button>
                </div>
            ),
        },
    ];

    // Backup table columns
    const backupColumns = [
        {
            title: 'Date',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => new Date(date).toLocaleString(),
        },
        {
            title: 'Type',
            dataIndex: 'backup_type',
            key: 'backup_type',
            render: (type: string) => (
                <Tag color={type === 'manual' ? 'blue' : 'green'}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                </Tag>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => (
                <Tag color={status === 'completed' ? 'success' : status === 'failed' ? 'error' : 'processing'}>
                    {status.charAt(0).toUpperCase() + status.slice(1)}
                </Tag>
            ),
        },
        {
            title: 'Size',
            dataIndex: 'file_size',
            key: 'file_size',
            render: (size: number) => {
                if (size < 1024) return `${size} B`;
                if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
                return `${(size / (1024 * 1024)).toFixed(1)} MB`;
            },
        },
        {
            title: 'Expires',
            dataIndex: 'expires_at',
            key: 'expires_at',
            render: (date: string) => new Date(date).toLocaleDateString(),
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_: any, record: any) => (
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        className="secondary-button"
                        onClick={() => downloadBackup(record.id)}
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                        title="Download"
                    >
                        <DownloadOutlined />
                    </button>
                    <button
                        className="secondary-button"
                        onClick={() => {
                            setSelectedBackupForRestore(record.id);
                            setRestoreModalVisible(true);
                        }}
                        style={{ padding: '4px 8px', fontSize: '12px' }}
                        title="Restore"
                    >
                        <ReloadOutlined />
                    </button>
                    <button
                        className="secondary-button"
                        onClick={() => {
                            if (window.confirm('Are you sure you want to delete this backup?')) {
                                deleteBackup(record.id);
                            }
                        }}
                        style={{ padding: '4px 8px', fontSize: '12px', color: '#ff4d4f' }}
                        title="Delete"
                    >
                        <DeleteOutlined />
                    </button>
                </div>
            ),
        },
    ];

    // Render AI Configuration Section (shared between page view and modal)
    const renderAiConfigSection = () => (
        <div style={{ borderTop: '1px solid #e8e8e8', paddingTop: '24px' }}>
            <h4 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px', color: '#333' }}>
                <RobotOutlined style={{ color: '#1890ff' }} />
                AI Provider Configuration
            </h4>
            <p style={{ color: '#8c8c8c', fontSize: '13px', marginBottom: '16px' }}>
                Configure the AI provider for this organization. Each organization can have its own AI settings, or use the global default.
            </p>

            {isLoadingOrgAiConfig ? (
                <div style={{ padding: '20px', textAlign: 'center', color: '#8c8c8c' }}>
                    <Spin size="small" style={{ marginRight: '8px' }} />
                    Loading AI configuration...
                </div>
            ) : (
                <>
                    {/* Enable/Disable AI for this org */}
                    <div style={{ marginBottom: '16px' }}>
                        <div
                            onClick={() => setOrgAiEnabled(!orgAiEnabled)}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
                        >
                            <div style={{
                                position: 'relative',
                                width: '44px',
                                height: '24px',
                                background: orgAiEnabled ? '#1890ff' : '#d9d9d9',
                                borderRadius: '12px',
                                transition: 'background 0.2s ease',
                                flexShrink: 0
                            }}>
                                <div style={{
                                    position: 'absolute',
                                    top: '2px',
                                    left: orgAiEnabled ? '22px' : '2px',
                                    width: '20px',
                                    height: '20px',
                                    background: 'white',
                                    borderRadius: '50%',
                                    boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                                    transition: 'left 0.2s ease'
                                }} />
                            </div>
                            <span style={{ fontSize: '14px', color: '#555', fontWeight: 500 }}>
                                {orgAiEnabled ? 'AI is Enabled for this Organization' : 'AI is Disabled for this Organization'}
                            </span>
                        </div>
                    </div>

                    {orgAiEnabled && (
                        <>
                            {/* Provider Selection */}
                            <div style={{ marginBottom: '16px' }}>
                                <label className="form-label">AI Provider</label>
                                <Select
                                    value={orgAiProvider}
                                    onChange={(value) => setOrgAiProvider(value)}
                                    style={{ width: '100%', maxWidth: '300px' }}
                                    options={[
                                        { value: 'openai', label: 'OpenAI (ChatGPT)' },
                                        { value: 'anthropic', label: 'Anthropic (Claude)' },
                                        { value: 'xai', label: 'X AI (Grok)' },
                                        { value: 'google', label: 'Google (Gemini)' },
                                        { value: 'qlon', label: 'QLON Ai' }
                                    ]}
                                />
                            </div>

                            {/* OpenAI Configuration */}
                            {orgAiProvider === 'openai' && (
                                <div style={{ padding: '16px', backgroundColor: '#f0fff0', borderRadius: '6px', border: '1px solid #74d680', marginBottom: '16px' }}>
                                    <h5 style={{ margin: '0 0 12px 0', color: '#388e3c', fontSize: '13px', fontWeight: '600' }}>OpenAI (ChatGPT) Configuration</h5>
                                    <div className="form-group" style={{ marginBottom: '12px' }}>
                                        <label className="form-label required">OpenAI API Key</label>
                                        <Input.Password placeholder="sk-..." value={orgOpenaiApiKey} onChange={(e) => setOrgOpenaiApiKey(e.target.value)} />
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                        <div className="form-group">
                                            <label className="form-label">Model</label>
                                            <Select value={orgOpenaiModel} onChange={(value) => setOrgOpenaiModel(value)} style={{ width: '100%' }}
                                                options={[
                                                    { value: 'gpt-4o', label: 'GPT-4o (Recommended)' },
                                                    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
                                                    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
                                                    { value: 'gpt-4', label: 'GPT-4' },
                                                    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
                                                    { value: 'o1', label: 'o1' },
                                                    { value: 'o1-mini', label: 'o1-mini' }
                                                ]}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Custom Base URL (optional)</label>
                                            <Input placeholder="https://api.openai.com/v1" value={orgOpenaiBaseUrl} onChange={(e) => setOrgOpenaiBaseUrl(e.target.value)} />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Anthropic Configuration */}
                            {orgAiProvider === 'anthropic' && (
                                <div style={{ padding: '16px', backgroundColor: '#fff5e6', borderRadius: '6px', border: '1px solid #d4a574', marginBottom: '16px' }}>
                                    <h5 style={{ margin: '0 0 12px 0', color: '#b8860b', fontSize: '13px', fontWeight: '600' }}>Anthropic (Claude) Configuration</h5>
                                    <div className="form-group" style={{ marginBottom: '12px' }}>
                                        <label className="form-label required">Anthropic API Key</label>
                                        <Input.Password placeholder="sk-ant-..." value={orgAnthropicApiKey} onChange={(e) => setOrgAnthropicApiKey(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Model</label>
                                        <Select value={orgAnthropicModel} onChange={(value) => setOrgAnthropicModel(value)} style={{ width: '100%', maxWidth: '300px' }}
                                            options={[
                                                { value: 'claude-sonnet-4-20250514', label: 'Claude Sonnet 4 (Recommended)' },
                                                { value: 'claude-opus-4-20250514', label: 'Claude Opus 4' },
                                                { value: 'claude-3-5-sonnet-20241022', label: 'Claude 3.5 Sonnet' },
                                                { value: 'claude-3-5-haiku-20241022', label: 'Claude 3.5 Haiku' },
                                                { value: 'claude-3-opus-20240229', label: 'Claude 3 Opus' }
                                            ]}
                                        />
                                    </div>
                                </div>
                            )}

                            {/* X AI Configuration */}
                            {orgAiProvider === 'xai' && (
                                <div style={{ padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '6px', border: '1px solid #666', marginBottom: '16px' }}>
                                    <h5 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '13px', fontWeight: '600' }}>X AI (Grok) Configuration</h5>
                                    <div className="form-group" style={{ marginBottom: '12px' }}>
                                        <label className="form-label required">X AI API Key</label>
                                        <Input.Password placeholder="xai-..." value={orgXaiApiKey} onChange={(e) => setOrgXaiApiKey(e.target.value)} />
                                    </div>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                        <div className="form-group">
                                            <label className="form-label">Model</label>
                                            <Select value={orgXaiModel} onChange={(value) => setOrgXaiModel(value)} style={{ width: '100%' }}
                                                options={[
                                                    { value: 'grok-3', label: 'Grok 3 (Recommended)' },
                                                    { value: 'grok-3-fast', label: 'Grok 3 Fast' },
                                                    { value: 'grok-2', label: 'Grok 2' },
                                                    { value: 'grok-2-mini', label: 'Grok 2 Mini' }
                                                ]}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Custom Base URL (optional)</label>
                                            <Input placeholder="https://api.x.ai/v1" value={orgXaiBaseUrl} onChange={(e) => setOrgXaiBaseUrl(e.target.value)} />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Google Configuration */}
                            {orgAiProvider === 'google' && (
                                <div style={{ padding: '16px', backgroundColor: '#e8f0fe', borderRadius: '6px', border: '1px solid #4285f4', marginBottom: '16px' }}>
                                    <h5 style={{ margin: '0 0 12px 0', color: '#1a73e8', fontSize: '13px', fontWeight: '600' }}>Google (Gemini) Configuration</h5>
                                    <div className="form-group" style={{ marginBottom: '12px' }}>
                                        <label className="form-label required">Google AI API Key</label>
                                        <Input.Password placeholder="AIza..." value={orgGoogleApiKey} onChange={(e) => setOrgGoogleApiKey(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Model</label>
                                        <Select value={orgGoogleModel} onChange={(value) => setOrgGoogleModel(value)} style={{ width: '100%', maxWidth: '300px' }}
                                            options={[
                                                { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash (Recommended)' },
                                                { value: 'gemini-2.0-flash-lite', label: 'Gemini 2.0 Flash Lite' },
                                                { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
                                                { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
                                                { value: 'gemini-1.5-flash-8b', label: 'Gemini 1.5 Flash 8B' }
                                            ]}
                                        />
                                    </div>
                                </div>
                            )}

                            {/* QLON Configuration */}
                            {orgAiProvider === 'qlon' && (
                                <div style={{ padding: '16px', backgroundColor: '#fff7e6', borderRadius: '6px', border: '1px solid #ffd591', marginBottom: '16px' }}>
                                    <h5 style={{ margin: '0 0 12px 0', color: '#d46b08', fontSize: '13px', fontWeight: '600' }}>QLON Ai Configuration</h5>
                                    <div className="form-group" style={{ marginBottom: '12px' }}>
                                        <label className="form-label required">QLON API URL</label>
                                        <Input placeholder="https://your-qlon-instance.com" value={orgQlonUrl} onChange={(e) => setOrgQlonUrl(e.target.value)} />
                                    </div>
                                    <div className="form-group" style={{ marginBottom: '12px' }}>
                                        <label className="form-label required">QLON API Key</label>
                                        <Input.Password placeholder="Enter QLON API Key" value={orgQlonApiKey} onChange={(e) => setOrgQlonApiKey(e.target.value)} />
                                    </div>
                                    <Checkbox checked={orgQlonUseTools} onChange={(e) => setOrgQlonUseTools(e.target.checked)}>
                                        Enable Integration Tools (recommended)
                                    </Checkbox>
                                </div>
                            )}

                            {/* AI Remediator Section */}
                            <div style={{ padding: '16px', backgroundColor: orgAiRemediatorEnabled ? '#f0f9ff' : '#fafafa', borderRadius: '6px', border: orgAiRemediatorEnabled ? '1px solid #91d5ff' : '1px solid #e8e8e8', marginBottom: '16px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: orgAiRemediatorEnabled ? '16px' : '0' }}>
                                    <div>
                                        <h5 style={{ margin: '0 0 4px 0', color: '#333', fontSize: '13px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <RobotOutlined style={{ color: orgAiRemediatorEnabled ? '#1890ff' : '#999' }} />
                                            AI Remediator
                                            {orgAiRemediatorEnabled && (
                                                <span style={{ backgroundColor: '#52c41a', color: 'white', fontSize: '10px', padding: '2px 6px', borderRadius: '10px', fontWeight: 'normal' }}>
                                                    Enabled
                                                </span>
                                            )}
                                        </h5>
                                        <p style={{ margin: 0, color: '#666', fontSize: '12px' }}>
                                            Enable AI-powered remediation guidance for security scans.
                                        </p>
                                    </div>
                                    <div
                                        onClick={() => setOrgAiRemediatorEnabled(!orgAiRemediatorEnabled)}
                                        style={{
                                            position: 'relative',
                                            width: '44px',
                                            height: '24px',
                                            background: orgAiRemediatorEnabled ? '#1890ff' : '#d9d9d9',
                                            borderRadius: '12px',
                                            transition: 'background 0.2s ease',
                                            cursor: 'pointer',
                                            flexShrink: 0
                                        }}
                                    >
                                        <div style={{
                                            position: 'absolute',
                                            top: '2px',
                                            left: orgAiRemediatorEnabled ? '22px' : '2px',
                                            width: '20px',
                                            height: '20px',
                                            background: 'white',
                                            borderRadius: '50%',
                                            boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                                            transition: 'left 0.2s ease'
                                        }} />
                                    </div>
                                </div>

                                {orgAiRemediatorEnabled && (
                                    <div style={{ borderTop: '1px solid #e8e8e8', paddingTop: '12px' }}>
                                        <p style={{ margin: '0 0 12px 0', color: '#666', fontSize: '12px' }}>
                                            Custom Remediation Prompts (Optional) - Leave empty to use defaults.
                                        </p>

                                        {/* ZAP Prompt */}
                                        <div style={{ marginBottom: '8px' }}>
                                            <div
                                                onClick={() => setShowZapPromptEditor(!showZapPromptEditor)}
                                                style={{ cursor: 'pointer', padding: '8px 12px', backgroundColor: '#fff', border: '1px solid #d9d9d9', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                                            >
                                                <span style={{ fontWeight: 500, color: '#333', fontSize: '12px' }}>
                                                    Web App Scanner Prompt
                                                    {orgRemediatorPromptZap && <span style={{ marginLeft: '8px', fontSize: '10px', color: '#1890ff' }}>(Custom)</span>}
                                                </span>
                                                <span style={{ color: '#999', fontSize: '10px' }}>{showZapPromptEditor ? '▼' : '▶'}</span>
                                            </div>
                                            {showZapPromptEditor && (
                                                <textarea
                                                    className="form-input"
                                                    placeholder="Enter custom Web App Scanner remediation prompt..."
                                                    value={orgRemediatorPromptZap}
                                                    onChange={(e) => setOrgRemediatorPromptZap(e.target.value)}
                                                    style={{ width: '100%', minHeight: '80px', fontFamily: 'monospace', fontSize: '11px', resize: 'vertical', marginTop: '8px' }}
                                                />
                                            )}
                                        </div>

                                        {/* Nmap Prompt */}
                                        <div>
                                            <div
                                                onClick={() => setShowNmapPromptEditor(!showNmapPromptEditor)}
                                                style={{ cursor: 'pointer', padding: '8px 12px', backgroundColor: '#fff', border: '1px solid #d9d9d9', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                                            >
                                                <span style={{ fontWeight: 500, color: '#333', fontSize: '12px' }}>
                                                    Network Scanner Prompt
                                                    {orgRemediatorPromptNmap && <span style={{ marginLeft: '8px', fontSize: '10px', color: '#1890ff' }}>(Custom)</span>}
                                                </span>
                                                <span style={{ color: '#999', fontSize: '10px' }}>{showNmapPromptEditor ? '▼' : '▶'}</span>
                                            </div>
                                            {showNmapPromptEditor && (
                                                <textarea
                                                    className="form-input"
                                                    placeholder="Enter custom Network Scanner remediation prompt..."
                                                    value={orgRemediatorPromptNmap}
                                                    onChange={(e) => setOrgRemediatorPromptNmap(e.target.value)}
                                                    style={{ width: '100%', minHeight: '80px', fontFamily: 'monospace', fontSize: '11px', resize: 'vertical', marginTop: '8px' }}
                                                />
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </>
                    )}

                    {/* Save/Delete AI Config buttons */}
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                        <button
                            className="add-button"
                            onClick={() => handleSaveOrgAiConfig(isOrgAdmin ? current_user?.organisation_id : undefined)}
                            disabled={isSavingOrgAiConfig}
                            style={{ fontSize: '13px' }}
                        >
                            {isSavingOrgAiConfig ? 'Saving...' : 'Save AI Configuration'}
                        </button>
                        {orgHasAiConfig && (
                            <button
                                className="secondary-button"
                                onClick={() => handleDeleteOrgAiConfig(isOrgAdmin ? current_user?.organisation_id : undefined)}
                                disabled={isSavingOrgAiConfig}
                                style={{ fontSize: '13px' }}
                            >
                                Reset to Global Default
                            </button>
                        )}
                    </div>

                    {/* Status info */}
                    <div style={{ padding: '10px 12px', backgroundColor: orgHasAiConfig ? '#e6f7ff' : '#f9f9f9', borderRadius: '4px', border: `1px solid ${orgHasAiConfig ? '#91d5ff' : '#e8e8e8'}` }}>
                        <p style={{ margin: 0, color: orgHasAiConfig ? '#0050b3' : '#8c8c8c', fontSize: '12px' }}>
                            {orgHasAiConfig
                                ? `✓ This organization has custom AI settings (Provider: ${
                                    orgAiProvider === 'openai' ? 'OpenAI (ChatGPT)' :
                                    orgAiProvider === 'anthropic' ? 'Anthropic (Claude)' :
                                    orgAiProvider === 'xai' ? 'X AI (Grok)' :
                                    orgAiProvider === 'google' ? 'Google (Gemini)' :
                                    'QLON Ai'
                                })`
                                : '○ Using global default AI settings. Save to customize.'}
                        </p>
                    </div>
                </>
            )}
        </div>
    );

    // ==================== ORG ADMIN VIEW ====================
    if (isOrgAdmin) {
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
                                <SettingOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                                <InfoTitle
                                    title="Organization Settings"
                                    infoContent="Manage your organization's settings including AI provider configuration and backup options."
                                    className="page-title"
                                />
                            </div>
                        </div>

                        {/* Organization Information Section */}
                        <div className="page-section" style={{ marginBottom: '24px' }}>
                            <h3 className="section-title">Organization Information</h3>
                            <p className="section-subtitle">View your organization's details.</p>

                            <div style={{ padding: '20px', backgroundColor: '#fafafa', borderRadius: '8px', border: '1px solid #e8e8e8' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                                    <div>
                                        <label style={{ display: 'block', color: '#8c8c8c', fontSize: '12px', marginBottom: '4px' }}>Organization Name</label>
                                        <div style={{ fontSize: '16px', fontWeight: 500, color: '#333' }}>
                                            {currentUserOrg?.name || 'N/A'}
                                        </div>
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', color: '#8c8c8c', fontSize: '12px', marginBottom: '4px' }}>Domain</label>
                                        <div style={{ fontSize: '16px', fontWeight: 500, color: '#333' }}>
                                            {currentUserOrg?.domain || 'Not set'}
                                        </div>
                                    </div>
                                </div>
                                <div style={{ marginTop: '20px' }}>
                                    <label style={{ display: 'block', color: '#8c8c8c', fontSize: '12px', marginBottom: '8px' }}>Logo</label>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                        {currentUserOrg?.logo && (
                                            <img
                                                src={currentUserOrg.logo}
                                                alt="Organization Logo"
                                                style={{ height: '60px', maxWidth: '200px', objectFit: 'contain' }}
                                                onError={(e) => {
                                                    e.currentTarget.style.display = 'none';
                                                }}
                                            />
                                        )}
                                        <Upload
                                            showUploadList={false}
                                            beforeUpload={handleOrgAdminLogoUpload}
                                            accept="image/png,image/jpeg,image/gif,image/svg+xml"
                                        >
                                            <button className="secondary-button" disabled={isUploadingOrgLogo} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <UploadOutlined /> {isUploadingOrgLogo ? 'Uploading...' : 'Upload Logo'}
                                            </button>
                                        </Upload>
                                        {currentUserOrg?.logo && (
                                            <button
                                                className="secondary-button"
                                                onClick={handleOrgAdminLogoDelete}
                                                disabled={isDeletingOrgLogo}
                                                style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ff4d4f', borderColor: '#ff4d4f' }}
                                            >
                                                <DeleteOutlined /> {isDeletingOrgLogo ? 'Deleting...' : 'Delete Logo'}
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* AI Provider Configuration Section */}
                        <div className="page-section" style={{ marginBottom: '24px' }}>
                            <h3 className="section-title">AI Provider Configuration</h3>
                            <p className="section-subtitle">Configure the AI provider for your organization.</p>

                            <div style={{ padding: '20px', backgroundColor: '#fafafa', borderRadius: '8px', border: '1px solid #e8e8e8' }}>
                                {renderAiConfigSection()}
                            </div>
                        </div>

                        {/* Backup & Restore Section */}
                        <div className="page-section">
                            <h3 className="section-title">Backup & Restore</h3>
                            <p className="section-subtitle">Configure automatic backups and manage your organization's data backups.</p>

                            <div style={{ padding: '20px', backgroundColor: '#fafafa', borderRadius: '8px', border: '1px solid #e8e8e8' }}>
                                {/* Backup Configuration */}
                                <div style={{ marginBottom: '24px' }}>
                                    <h4 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px', color: '#333' }}>
                                        <CloudUploadOutlined style={{ color: '#52c41a' }} />
                                        Backup Configuration
                                    </h4>

                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '16px' }}>
                                        <div className="form-group">
                                            <label className="form-label">Automatic Backups</label>
                                            <div
                                                onClick={() => setBackupEnabled(!backupEnabled)}
                                                style={{ display: 'inline-flex', alignItems: 'center', gap: '10px', cursor: 'pointer', marginTop: '8px' }}
                                            >
                                                <div style={{
                                                    position: 'relative',
                                                    width: '44px',
                                                    height: '24px',
                                                    background: backupEnabled ? '#52c41a' : '#d9d9d9',
                                                    borderRadius: '12px',
                                                    transition: 'background 0.2s ease'
                                                }}>
                                                    <div style={{
                                                        position: 'absolute',
                                                        top: '2px',
                                                        left: backupEnabled ? '22px' : '2px',
                                                        width: '20px',
                                                        height: '20px',
                                                        background: 'white',
                                                        borderRadius: '50%',
                                                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                                                        transition: 'left 0.2s ease'
                                                    }} />
                                                </div>
                                                <span style={{ fontSize: '13px', color: '#555' }}>{backupEnabled ? 'Enabled' : 'Disabled'}</span>
                                            </div>
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Backup Frequency</label>
                                            <Select
                                                value={backupFrequency}
                                                onChange={(value) => setBackupFrequency(value)}
                                                disabled={!backupEnabled}
                                                style={{ width: '100%' }}
                                                options={[
                                                    { value: 'daily', label: 'Daily' },
                                                    { value: 'weekly', label: 'Weekly' },
                                                    { value: 'monthly', label: 'Monthly' }
                                                ]}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label className="form-label">Retention (Years)</label>
                                            <InputNumber
                                                min={1}
                                                max={100}
                                                value={backupRetentionYears}
                                                onChange={(value) => setBackupRetentionYears(value || 10)}
                                                disabled={!backupEnabled}
                                                style={{ width: '100%' }}
                                            />
                                        </div>
                                    </div>

                                    {/* Last backup status */}
                                    {backupConfig && (
                                        <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: backupConfig.last_backup_status === 'success' ? '#f6ffed' : backupConfig.last_backup_status === 'failed' ? '#fff2f0' : '#f0f0f0', borderRadius: '6px', border: `1px solid ${backupConfig.last_backup_status === 'success' ? '#b7eb8f' : backupConfig.last_backup_status === 'failed' ? '#ffccc7' : '#d9d9d9'}` }}>
                                            <span style={{ fontSize: '13px', color: '#595959' }}>
                                                Last Backup:{' '}
                                                {backupConfig.last_backup_at
                                                    ? new Date(backupConfig.last_backup_at).toLocaleDateString() + ' ' + new Date(backupConfig.last_backup_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                                                    : 'Never'}
                                                {backupConfig.last_backup_status && (
                                                    <Tag
                                                        color={backupConfig.last_backup_status === 'success' ? 'success' : backupConfig.last_backup_status === 'failed' ? 'error' : 'processing'}
                                                        style={{ marginLeft: '8px' }}
                                                    >
                                                        {backupConfig.last_backup_status}
                                                    </Tag>
                                                )}
                                            </span>
                                        </div>
                                    )}

                                    <div style={{ display: 'flex', gap: '8px' }}>
                                        <button
                                            className="add-button"
                                            onClick={handleSaveBackupConfig}
                                            disabled={backupLoading}
                                            style={{ fontSize: '13px' }}
                                        >
                                            Save Backup Settings
                                        </button>
                                        <button
                                            className="secondary-button"
                                            onClick={handleCreateBackup}
                                            disabled={isCreatingBackup || backupLoading}
                                            style={{ fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
                                        >
                                            <CloudUploadOutlined />
                                            {isCreatingBackup ? 'Creating...' : 'Create Manual Backup'}
                                        </button>
                                    </div>
                                </div>

                                {/* Backup List */}
                                <div>
                                    <h4 style={{ margin: '0 0 16px 0', color: '#333' }}>Available Backups</h4>
                                    <Table
                                        columns={backupColumns}
                                        dataSource={backups}
                                        rowKey="id"
                                        loading={backupLoading}
                                        size="small"
                                        pagination={{
                                            pageSize: 5,
                                            showSizeChanger: false,
                                            showTotal: (total) => `${total} backups`
                                        }}
                                        locale={{
                                            emptyText: 'No backups available'
                                        }}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Restore Modal */}
                        <Modal
                            title="Restore from Backup"
                            open={restoreModalVisible}
                            onCancel={() => {
                                setRestoreModalVisible(false);
                                setSelectedBackupForRestore(null);
                            }}
                            footer={
                                <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                    <button className="secondary-button" onClick={() => setRestoreModalVisible(false)}>
                                        Cancel
                                    </button>
                                    <button
                                        className="add-button"
                                        onClick={handleRestoreBackup}
                                        disabled={isRestoring}
                                        style={{ backgroundColor: '#faad14', borderColor: '#faad14' }}
                                    >
                                        {isRestoring ? 'Restoring...' : 'Confirm Restore'}
                                    </button>
                                </div>
                            }
                        >
                            <p style={{ color: '#ff4d4f', fontWeight: 500, marginBottom: '16px' }}>
                                Warning: This will replace all current data with the backup data. This action cannot be undone.
                            </p>
                            <p>Are you sure you want to restore from this backup?</p>
                        </Modal>
                    </div>
                </div>
            </div>
        );
    }

    // ==================== SUPER ADMIN VIEW ====================
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
                            <BankOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Organizations"
                                infoContent={ManageOrganisationsInfo}
                                className="page-title"
                            />
                        </div>
                        <div className="page-header-right">
                            {!showForm && isSuperAdmin && (
                                <button
                                    className="add-button"
                                    onClick={() => {
                                        handleClear(false);
                                        setShowForm(true);
                                    }}
                                    style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                                >
                                    <PlusOutlined /> Add Organization
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Organization Data Table Section */}
                    <div className="page-section">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                            <h3 className="section-title" style={{ margin: 0 }}>Organization Registry</h3>
                        </div>

                        <div style={{ overflowX: 'auto' }}>
                            <Table
                                columns={columns}
                                dataSource={displayedOrganizations}
                                showSorterTooltip={{ target: 'sorter-icon' }}
                                onRow={(record) => {
                                    return {
                                        onClick: () => {
                                            setSelectedOrganization(record.id);
                                            setOrgName(record.name);
                                            setOrgDomain(record.domain || '');
                                            setOrgLogo(record.logo || '');
                                            setShowForm(true);
                                        },
                                        style: {
                                            cursor: 'pointer',
                                            backgroundColor: selectedOrganization === record.id ? '#e6f7ff' : undefined
                                        }
                                    };
                                }}
                                rowKey="id"
                                pagination={{
                                    showSizeChanger: true,
                                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} organizations`,
                                }}
                            />
                        </div>
                    </div>

                    {/* Organization Modal (for super_admin) */}
                    <Modal
                        title={
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {selectedOrganization ? (
                                    <EditOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                                ) : (
                                    <PlusOutlined style={{ fontSize: '20px', color: '#52c41a' }} />
                                )}
                                <span>{selectedOrganization ? 'Edit Organization' : 'Add New Organization'}</span>
                                {selectedOrganization && <Tag color="blue">Editing</Tag>}
                            </div>
                        }
                        open={showForm}
                        onCancel={() => handleClear(true)}
                        width={800}
                        footer={
                            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                {selectedOrganization && isSuperAdmin && selectedOrganization !== current_user?.organisation_id && (
                                    <button
                                        className="delete-button"
                                        onClick={handleDelete}
                                        disabled={loading}
                                        style={{ backgroundColor: '#ff4d4f', borderColor: '#ff4d4f', color: 'white' }}
                                    >
                                        <DeleteOutlined /> Delete Organization
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
                                        backgroundColor: selectedOrganization ? '#1890ff' : '#52c41a',
                                        borderColor: selectedOrganization ? '#1890ff' : '#52c41a',
                                    }}
                                >
                                    {loading ? 'Saving...' : selectedOrganization ? 'Update Organization' : 'Save Organization'}
                                </button>
                            </div>
                        }
                    >
                        <div style={{ maxHeight: '70vh', overflowY: 'auto', paddingRight: '8px' }}>
                            <p style={{ color: '#8c8c8c', fontSize: '14px', marginBottom: '24px' }}>
                                {selectedOrganization
                                    ? 'Update the organization details below and click "Update Organization" to save changes.'
                                    : 'Fill out the form below to create a new organization.'}
                            </p>

                            {/* Basic Organization Details */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
                                <div className="form-group">
                                    <label className="form-label required">Name</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder="Enter organization name"
                                        value={orgName}
                                        onChange={(e) => setOrgName(e.target.value)}
                                        style={{ width: '100%' }}
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Domain</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder="Enter organization domain (e.g., example.com)"
                                        value={orgDomain}
                                        onChange={(e) => setOrgDomain(e.target.value)}
                                        style={{ width: '100%' }}
                                    />
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Logo</label>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                        {orgLogo && (
                                            <img
                                                src={orgLogo}
                                                alt="Organization Logo"
                                                style={{ height: '48px', maxWidth: '120px', objectFit: 'contain' }}
                                                onError={(e) => {
                                                    e.currentTarget.style.display = 'none';
                                                }}
                                            />
                                        )}
                                        <Upload {...uploadProps}>
                                            <button className="secondary-button" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <UploadOutlined /> Upload Logo
                                            </button>
                                        </Upload>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label className="form-label">Logo URL (Alternative)</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder="Or enter a logo URL directly"
                                        value={orgLogo}
                                        onChange={(e) => setOrgLogo(e.target.value)}
                                        style={{ width: '100%' }}
                                    />
                                </div>
                            </div>

                            {/* AI Provider Configuration - Only show when editing */}
                            {selectedOrganization && renderAiConfigSection()}
                        </div>
                    </Modal>
                </div>
            </div>
        </div>
    );
};

export default OrganizationsPage;
