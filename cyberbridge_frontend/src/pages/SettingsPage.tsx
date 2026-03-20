// src/pages/SettingsPage.tsx
import { useEffect, useState } from "react";
import { MenuProps, Select, notification, Input, Button, Form, Checkbox, Table, Modal, InputNumber, Popconfirm, Tag, Segmented, Upload } from 'antd';
import { SettingOutlined, ApiOutlined, LockOutlined, ToolOutlined, RobotOutlined, CloudUploadOutlined, DownloadOutlined, DeleteOutlined, EditOutlined, ReloadOutlined, SafetyCertificateOutlined, PictureOutlined } from '@ant-design/icons';
import { Collapse } from 'antd';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import useUserStore from "../store/useUserStore.ts";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import useAuthStore from "../store/useAuthStore.ts";
import useSettingsStore from "../store/useSettingsStore.ts";
import useBackupStore from "../store/useBackupStore.ts";
import useCRAModeStore from "../store/useCRAModeStore.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import { SettingsInfo } from "../constants/infoContent.tsx";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import ApiKeyManagement from "../components/ApiKeyManagement.tsx";

const SettingsPage = () => {
    const [location, setLocation] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const { current_user, organisations, fetchOrganisations } = useUserStore();
    const { clonableFrameworks, fetchClonableFrameworks, cloneFrameworks } = useFrameworksStore();
    const { getAuthHeader } = useAuthStore();
    const { scannersEnabled, setScannersEnabled, allowedScannerDomains, setAllowedScannerDomains, customLlmUrl, setCustomLlmUrl, getLlmUrl, customLlmPayload, setCustomLlmPayload, loadSettings, superAdminFocusedMode: storeSuperAdminFocusedMode, setSuperAdminFocusedMode } = useSettingsStore();
    const { config: backupConfig, backups, loading: backupLoading, error: backupError, fetchConfig: fetchBackupConfig, updateConfig: updateBackupConfig, fetchBackups, createBackup, downloadBackup, deleteBackup, restoreBackup, clearError: clearBackupError } = useBackupStore();
    const { craMode, craOperatorRole, saveCRAMode, saveCRAOperatorRole, fetchCRAMode } = useCRAModeStore();
    const { frameworks } = useFrameworksStore();
    const craFrameworkExists = frameworks.some(f => f.name.toLowerCase() === 'cra');

    // State for CRA mode
    const [isSavingCRAMode, setIsSavingCRAMode] = useState<boolean>(false);

    // State for framework cloning
    const [selectedClonableFrameworkIds, setSelectedClonableFrameworkIds] = useState<string[]>([]);
    const [selectedOrganizationId, setSelectedOrganizationId] = useState<string>('');
    const [customFrameworkName, setCustomFrameworkName] = useState<string>('');
    const [api, contextHolder] = notification.useNotification();

    // State for SMTP configuration
    const [smtpForm] = Form.useForm();
    const [emailTestForm] = Form.useForm();
    const [isTestingEmail, setIsTestingEmail] = useState<boolean>(false);
    const [isSavingSmtp, setIsSavingSmtp] = useState<boolean>(false);
    const [tlsEnabled, setTlsEnabled] = useState<boolean>(true);
    const [smtpConfigs, setSmtpConfigs] = useState<any[]>([]);
    const [isLoadingSmtpConfigs, setIsLoadingSmtpConfigs] = useState<boolean>(false);

    // State for framework permissions
    const [selectedPermissionOrgId, setSelectedPermissionOrgId] = useState<string>('');
    const [selectedAllowedTemplateIds, setSelectedAllowedTemplateIds] = useState<string[]>([]);
    const [isUpdatingPermissions, setIsUpdatingPermissions] = useState<boolean>(false);
    const [frameworkTemplates, setFrameworkTemplates] = useState<any[]>([]);

    // State for domain blacklist
    const [newBlacklistDomain, setNewBlacklistDomain] = useState<string>('');
    const [blacklistReason, setBlacklistReason] = useState<string>('');
    const [blacklistedDomains, setBlacklistedDomains] = useState<any[]>([]);
    const [isAddingToBlacklist, setIsAddingToBlacklist] = useState<boolean>(false);
    const [csvFile, setCsvFile] = useState<File | null>(null);
    const [isUploadingCsv, setIsUploadingCsv] = useState<boolean>(false);

    // State for LLM URL
    const [llmUrlInput, setLlmUrlInput] = useState<string>('');

    // State for LLM Payload
    const [llmPayloadInput, setLlmPayloadInput] = useState<string>('');
    const [selectedPayloadTemplate, setSelectedPayloadTemplate] = useState<string>('llamacpp');

    // State for global AI settings
    const [aiEnabled, setAiEnabled] = useState<boolean>(true);
    const [isSavingAiEnabled, setIsSavingAiEnabled] = useState<boolean>(false);
    // AI Policy Aligner global state (super_admin)
    const [aiPolicyAlignerGlobalEnabled, setAiPolicyAlignerGlobalEnabled] = useState<boolean>(false);
    const [isSavingAiPolicyAligner, setIsSavingAiPolicyAligner] = useState<boolean>(false);

    // State for super admin focused mode
    const [superAdminFocusedMode, setSuperAdminFocusedModeState] = useState<boolean>(false);
    const [isSavingSuperAdminFocusedMode, setIsSavingSuperAdminFocusedMode] = useState<boolean>(false);

    // State for scanners toggle
    const [isSavingScannersEnabled, setIsSavingScannersEnabled] = useState<boolean>(false);

    // State for SSO settings (super_admin only) - multi-record pattern
    const [ssoForm] = Form.useForm();
    const [ssoEditForm] = Form.useForm();
    const [ssoConfigs, setSsoConfigs] = useState<any[]>([]);
    const [isLoadingSsoConfigs, setIsLoadingSsoConfigs] = useState<boolean>(false);
    const [isSavingSsoConfig, setIsSavingSsoConfig] = useState<boolean>(false);
    const [editingSsoConfig, setEditingSsoConfig] = useState<any>(null);
    const [isSavingSsoEdit, setIsSavingSsoEdit] = useState<boolean>(false);

    // State for org-specific AI configuration (for org_admin)
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

    // AI Remediator states for org_admin
    const [orgAiRemediatorEnabled, setOrgAiRemediatorEnabled] = useState<boolean>(false);
    const [orgRemediatorPromptZap, setOrgRemediatorPromptZap] = useState<string>('');
    const [orgRemediatorPromptNmap, setOrgRemediatorPromptNmap] = useState<string>('');
    const [showZapPromptEditor, setShowZapPromptEditor] = useState<boolean>(false);
    const [showNmapPromptEditor, setShowNmapPromptEditor] = useState<boolean>(false);

    // AI Policy Aligner states for org_admin
    const [orgAiPolicyAlignerEnabled, setOrgAiPolicyAlignerEnabled] = useState<boolean>(false);
    const [orgPolicyAlignerPrompt, setOrgPolicyAlignerPrompt] = useState<string>('');
    const [showPolicyAlignerPromptEditor, setShowPolicyAlignerPromptEditor] = useState<boolean>(false);

    // Backup & Restore states
    const [backupEnabled, setBackupEnabled] = useState<boolean>(true);
    const [backupFrequency, setBackupFrequency] = useState<string>('monthly');
    const [backupRetentionYears, setBackupRetentionYears] = useState<number>(10);
    const [isCreatingBackup, setIsCreatingBackup] = useState<boolean>(false);
    const [isSavingBackupConfig, setIsSavingBackupConfig] = useState<boolean>(false);
    const [restoreModalVisible, setRestoreModalVisible] = useState<boolean>(false);
    const [selectedBackupForRestore, setSelectedBackupForRestore] = useState<string | null>(null);
    const [isRestoring, setIsRestoring] = useState<boolean>(false);

    // State for Login/Register Logo management (super_admin only)
    const [loginLogos, setLoginLogos] = useState<any[]>([]);
    const [isLoadingLoginLogos, setIsLoadingLoginLogos] = useState<boolean>(false);
    const [isSavingLoginLogo, setIsSavingLoginLogo] = useState<boolean>(false);
    const [loginLogoName, setLoginLogoName] = useState<string>('');
    const [loginLogoBase64, setLoginLogoBase64] = useState<string>('');
    const [loginLogoIsGlobal, setLoginLogoIsGlobal] = useState<boolean>(false);
    const [loginLogoOrgIds, setLoginLogoOrgIds] = useState<string[]>([]);
    const [editingLoginLogo, setEditingLoginLogo] = useState<any>(null);
    const [isSavingLoginLogoEdit, setIsSavingLoginLogoEdit] = useState<boolean>(false);
    const [editLoginLogoName, setEditLoginLogoName] = useState<string>('');
    const [editLoginLogoBase64, setEditLoginLogoBase64] = useState<string>('');
    const [editLoginLogoIsGlobal, setEditLoginLogoIsGlobal] = useState<boolean>(false);
    const [editLoginLogoOrgIds, setEditLoginLogoOrgIds] = useState<string[]>([]);

    useEffect(() => {
        // Load settings from localStorage
        loadSettings();

        // Redirect users who are not super_admin or org_admin
        if (current_user && !['super_admin', 'org_admin'].includes(current_user.role_name)) {
            setLocation('/home');
        }

        // Fetch data for super admin
        if (current_user && current_user.role_name === 'super_admin') {
            fetchClonableFrameworks();
            fetchOrganisations();
            fetchFrameworkTemplates();
            fetchBlacklistedDomains();
            fetchGlobalLlmSettings();
            fetchSsoConfigs();
            fetchSmtpConfigs();
            fetchLoginLogos();
            fetchOrgAiConfig(current_user.organisation_id);
        }

        // Fetch org-specific AI config for org_admin
        if (current_user && current_user.role_name === 'org_admin') {
            fetchOrgAiConfig(current_user.organisation_id);
        }

        // Fetch CRA mode for both super_admin and org_admin
        if (current_user && ['org_admin', 'super_admin'].includes(current_user.role_name)) {
            fetchCRAMode(current_user.organisation_id);
        }

        // Fetch backup config and list for org_admin and super_admin
        if (current_user && ['org_admin', 'super_admin'].includes(current_user.role_name)) {
            fetchBackupConfig(current_user.organisation_id);
            fetchBackups(current_user.organisation_id);
        }

    }, [current_user, setLocation, fetchClonableFrameworks, fetchOrganisations, loadSettings]);

    // Update local backup state when config is loaded
    useEffect(() => {
        if (backupConfig) {
            setBackupEnabled(backupConfig.backup_enabled);
            setBackupFrequency(backupConfig.backup_frequency);
            setBackupRetentionYears(backupConfig.backup_retention_years);
        }
    }, [backupConfig]);

    // Fetch global LLM settings from backend
    const fetchGlobalLlmSettings = async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/llm`, {
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                const data = await response.json();
                setAiEnabled(data.ai_enabled ?? true);
                setAiPolicyAlignerGlobalEnabled(data.ai_policy_aligner_enabled ?? false);
            }
        } catch (error) {
            console.error('Error fetching global LLM settings:', error);
        }
    };

    // Handle global AI toggle
    const handleAiEnabledToggle = async (checked: boolean) => {
        setIsSavingAiEnabled(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/llm`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader()
                },
                body: JSON.stringify({
                    ai_enabled: checked
                })
            });

            if (response.ok) {
                setAiEnabled(checked);
                api.success({
                    message: 'AI Settings Updated',
                    description: `AI functionality has been ${checked ? 'enabled' : 'disabled'} globally.`,
                    duration: 4,
                });
            } else {
                throw new Error('Failed to update AI settings');
            }
        } catch (error) {
            api.error({
                message: 'Failed to Update',
                description: 'Failed to update AI settings. Please try again.',
                duration: 4,
            });
        } finally {
            setIsSavingAiEnabled(false);
        }
    };

    // Handle global AI Policy Aligner toggle
    const handleAiPolicyAlignerGlobalToggle = async (checked: boolean) => {
        setIsSavingAiPolicyAligner(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/llm`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader()
                },
                body: JSON.stringify({
                    ai_policy_aligner_enabled: checked
                })
            });

            if (response.ok) {
                setAiPolicyAlignerGlobalEnabled(checked);
                api.success({
                    message: 'AI Policy Aligner Updated',
                    description: `AI Policy Aligner has been ${checked ? 'enabled' : 'disabled'} globally.`,
                    duration: 4,
                });
            } else {
                throw new Error('Failed to update AI Policy Aligner settings');
            }
        } catch (error) {
            api.error({
                message: 'Failed to Update',
                description: 'Failed to update AI Policy Aligner settings. Please try again.',
                duration: 4,
            });
        } finally {
            setIsSavingAiPolicyAligner(false);
        }
    };

    // Handle super admin focused mode toggle
    const handleSuperAdminFocusedModeToggle = async (checked: boolean) => {
        setIsSavingSuperAdminFocusedMode(true);
        try {
            await setSuperAdminFocusedMode(checked);
            setSuperAdminFocusedModeState(checked);
            api.success({
                message: 'Settings Updated',
                description: `Super Admin Focused Mode has been ${checked ? 'enabled' : 'disabled'}.`,
                duration: 4,
            });
        } catch (error) {
            api.error({
                message: 'Failed to Update',
                description: 'Failed to update Super Admin Focused Mode. Please try again.',
                duration: 4,
            });
        } finally {
            setIsSavingSuperAdminFocusedMode(false);
        }
    };

    // Sync super admin focused mode from store
    useEffect(() => {
        setSuperAdminFocusedModeState(storeSuperAdminFocusedMode);
    }, [storeSuperAdminFocusedMode]);

    // Initialize LLM URL input with current custom URL
    useEffect(() => {
        if (customLlmUrl) {
            setLlmUrlInput(customLlmUrl);
        }
    }, [customLlmUrl]);

    // Initialize LLM Payload input with current custom payload or default
    useEffect(() => {
        if (customLlmPayload) {
            setLlmPayloadInput(customLlmPayload);
            setSelectedPayloadTemplate('custom');
        } else {
            // Set to default template
            const defaultPayload = `{
  "model": "{{model}}",
  "prompt": "{{prompt}}",
  "stream": false
}`;
            setLlmPayloadInput(defaultPayload);
        }
    }, [customLlmPayload]);

    // Function to fetch framework templates
    const fetchFrameworkTemplates = async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/templates`, {
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                const templates = await response.json();
                setFrameworkTemplates(templates);
            }
        } catch (error) {
            console.error('Error fetching framework templates:', error);
        }
    };

    // Function to fetch blacklisted domains
    const fetchBlacklistedDomains = async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/domain-blacklist`, {
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                const domains = await response.json();
                setBlacklistedDomains(domains);
            }
        } catch (error) {
            console.error('Error fetching blacklisted domains:', error);
        }
    };

    const onClick: MenuProps['onClick'] = (e) => {
        console.log('click ', e);
    };

    // Helper functions for framework cloning
    const handleClonableFrameworkChange = (value: string[]) => {
        setSelectedClonableFrameworkIds(value);
    };

    const handleOrganizationChange = (value: string) => {
        setSelectedOrganizationId(value);
    };

    const handleCustomFrameworkNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setCustomFrameworkName(e.target.value);
    };

    const handleCloneFrameworks = async () => {
        if (selectedClonableFrameworkIds.length === 0) {
            api.error({
                message: 'No Frameworks Selected',
                description: 'Please select at least one framework to clone!',
                duration: 4,
            });
            return;
        }

        if (!selectedOrganizationId) {
            api.error({
                message: 'No Organization Selected',
                description: 'Please select a target organization to clone frameworks to!',
                duration: 4,
            });
            return;
        }

        const success = await cloneFrameworks(selectedClonableFrameworkIds, customFrameworkName, selectedOrganizationId);
        if (success) {
            api.success({
                message: 'Frameworks Cloned Successfully',
                description: `Selected frameworks have been cloned to the target organization with their questions and objectives.`,
                duration: 4,
            });
            setSelectedClonableFrameworkIds([]);
            setSelectedOrganizationId('');
            setCustomFrameworkName('');
            // Refresh clonable frameworks list
            fetchClonableFrameworks();
        } else {
            api.error({
                message: 'Framework Cloning Failed',
                description: 'Failed to clone the selected frameworks. Please try again.',
                duration: 4,
            });
        }
    };

    // TLS toggle handler
    const handleTlsToggle = (checked: boolean) => {
        setTlsEnabled(checked);
        smtpForm.setFieldsValue({ use_tls: checked });
    };

    // SMTP Configuration handlers
    const handleSaveSmtpConfig = async (values: any) => {
        setIsSavingSmtp(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/smtp-config`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(values),
            });

            if (response.ok) {
                api.success({
                    message: 'SMTP Configuration Saved',
                    description: 'SMTP settings have been saved successfully.',
                    duration: 4,
                });
                smtpForm.resetFields();
                setTlsEnabled(true);
                fetchSmtpConfigs();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to save SMTP configuration');
            }
        } catch (error) {
            api.error({
                message: 'SMTP Configuration Failed',
                description: error instanceof Error ? error.message : 'Failed to save SMTP settings. Please try again.',
                duration: 4,
            });
        } finally {
            setIsSavingSmtp(false);
        }
    };

    const handleTestEmail = async (values: any) => {
        setIsTestingEmail(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/test-email`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(values),
            });

            if (response.ok) {
                api.success({
                    message: 'Test Email Sent',
                    description: `Test email sent successfully to ${values.recipient_email}.`,
                    duration: 4,
                });
                emailTestForm.resetFields();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to send test email');
            }
        } catch (error) {
            api.error({
                message: 'Test Email Failed',
                description: error instanceof Error ? error.message : 'Failed to send test email. Please check SMTP configuration.',
                duration: 4,
            });
        } finally {
            setIsTestingEmail(false);
        }
    };

    // SMTP Configs list handlers
    const fetchSmtpConfigs = async () => {
        setIsLoadingSmtpConfigs(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/smtp-configs`, {
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                const data = await response.json();
                setSmtpConfigs(data);
            }
        } catch (error) {
            console.error('Error fetching SMTP configs:', error);
        } finally {
            setIsLoadingSmtpConfigs(false);
        }
    };

    const handleToggleSmtpActive = async (configId: string, currentlyActive: boolean) => {
        try {
            const endpoint = currentlyActive
                ? `${cyberbridge_back_end_rest_api}/settings/smtp-config/${configId}/deactivate`
                : `${cyberbridge_back_end_rest_api}/settings/smtp-config/${configId}/activate`;
            const response = await fetch(endpoint, {
                method: 'PUT',
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                api.success({
                    message: 'SMTP Configuration Updated',
                    description: currentlyActive ? 'Configuration deactivated.' : 'Configuration activated.',
                    duration: 3,
                });
                fetchSmtpConfigs();
            } else {
                throw new Error('Failed to update SMTP configuration');
            }
        } catch (error) {
            api.error({
                message: 'Update Failed',
                description: 'Failed to update SMTP configuration status.',
                duration: 4,
            });
        }
    };

    const handleDeleteSmtpConfig = async (configId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/smtp-config/${configId}`, {
                method: 'DELETE',
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                api.success({
                    message: 'SMTP Configuration Deleted',
                    description: 'The SMTP configuration has been removed.',
                    duration: 3,
                });
                fetchSmtpConfigs();
            } else {
                throw new Error('Failed to delete SMTP configuration');
            }
        } catch (error) {
            api.error({
                message: 'Delete Failed',
                description: 'Failed to delete SMTP configuration.',
                duration: 4,
            });
        }
    };

    // Domain blacklist handlers
    const handleAddToBlacklist = async () => {
        if (!newBlacklistDomain.trim()) {
            api.error({
                message: 'Domain Required',
                description: 'Please enter a domain to blacklist!',
                duration: 4,
            });
            return;
        }

        setIsAddingToBlacklist(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/domain-blacklist`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader()
                },
                body: JSON.stringify({
                    domain: newBlacklistDomain.trim(),
                    reason: blacklistReason.trim() || undefined,
                }),
            });

            if (response.ok) {
                api.success({
                    message: 'Domain Blacklisted',
                    description: `Domain ${newBlacklistDomain} has been blacklisted and all users deactivated.`,
                    duration: 4,
                });
                setNewBlacklistDomain('');
                setBlacklistReason('');
                fetchBlacklistedDomains(); // Refresh the list
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to blacklist domain');
            }
        } catch (error) {
            api.error({
                message: 'Blacklist Failed',
                description: error instanceof Error ? error.message : 'Failed to blacklist domain. Please try again.',
                duration: 4,
            });
        } finally {
            setIsAddingToBlacklist(false);
        }
    };

    const handleRemoveFromBlacklist = async (domain: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/domain-blacklist/${encodeURIComponent(domain)}`, {
                method: 'DELETE',
                headers: {
                    ...getAuthHeader()
                }
            });

            if (response.ok) {
                api.success({
                    message: 'Domain Whitelisted',
                    description: `Domain ${domain} has been whitelisted and org_admin users reactivated.`,
                    duration: 4,
                });
                fetchBlacklistedDomains(); // Refresh the list
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to whitelist domain');
            }
        } catch (error) {
            api.error({
                message: 'Whitelist Failed',
                description: error instanceof Error ? error.message : 'Failed to whitelist domain. Please try again.',
                duration: 4,
            });
        }
    };

    const handleCsvFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file && file.type === 'text/csv') {
            setCsvFile(file);
        } else {
            api.error({
                message: 'Invalid File',
                description: 'Please select a valid CSV file.',
                duration: 4,
            });
            event.target.value = '';
        }
    };

    const handleUploadCsv = async () => {
        if (!csvFile) {
            api.error({
                message: 'No File Selected',
                description: 'Please select a CSV file to upload.',
                duration: 4,
            });
            return;
        }

        setIsUploadingCsv(true);
        try {
            const formData = new FormData();
            formData.append('file', csvFile);
            formData.append('reason', blacklistReason.trim() || 'Bulk upload from CSV');

            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/domain-blacklist/bulk-csv`, {
                method: 'POST',
                headers: {
                    ...getAuthHeader()
                },
                body: formData,
            });

            if (response.ok) {
                const result = await response.json();
                api.success({
                    message: 'CSV Upload Successful',
                    description: `${result.processed} domains processed. ${result.added} added, ${result.updated} updated, ${result.skipped} skipped.`,
                    duration: 6,
                });
                setCsvFile(null);
                setBlacklistReason('');
                // Clear the file input
                const fileInput = document.getElementById('csvFileInput') as HTMLInputElement;
                if (fileInput) fileInput.value = '';
                fetchBlacklistedDomains(); // Refresh the list
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to upload CSV');
            }
        } catch (error) {
            api.error({
                message: 'CSV Upload Failed',
                description: error instanceof Error ? error.message : 'Failed to upload CSV file. Please try again.',
                duration: 4,
            });
        } finally {
            setIsUploadingCsv(false);
        }
    };

    const handleDownloadSampleCsv = async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/domain-blacklist/sample-csv`, {
                method: 'GET',
                headers: {
                    ...getAuthHeader()
                }
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'domain_blacklist_sample.csv';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);

                api.success({
                    message: 'Sample Downloaded',
                    description: 'Sample CSV file has been downloaded successfully.',
                    duration: 3,
                });
            } else {
                throw new Error('Failed to download sample CSV');
            }
        } catch (error) {
            api.error({
                message: 'Download Failed',
                description: 'Failed to download sample CSV file. Please try again.',
                duration: 4,
            });
        }
    };

    // Framework permissions handlers
    const handlePermissionOrgChange = async (value: string) => {
        setSelectedPermissionOrgId(value);

        // Load existing permissions for this organization
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/framework-template-permissions/${value}`);
            if (response.ok) {
                const permissions = await response.json();
                setSelectedAllowedTemplateIds(permissions);
            } else {
                // No permissions set yet, default to all templates allowed
                setSelectedAllowedTemplateIds(frameworkTemplates.map(t => t.id));
            }
        } catch (error) {
            console.error('Error loading framework permissions:', error);
            // Default to all templates allowed on error
            setSelectedAllowedTemplateIds(frameworkTemplates.map(t => t.id));
        }
    };

    const handleAllowedTemplatesChange = (value: string[]) => {
        setSelectedAllowedTemplateIds(value);
    };

    const handleUpdateFrameworkPermissions = async () => {
        if (!selectedPermissionOrgId) {
            api.error({
                message: 'No Organization Selected',
                description: 'Please select an organization to configure framework permissions!',
                duration: 4,
            });
            return;
        }

        setIsUpdatingPermissions(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/framework-template-permissions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    organization_id: selectedPermissionOrgId,
                    template_ids: selectedAllowedTemplateIds,
                }),
            });

            if (response.ok) {
                api.success({
                    message: 'Framework Permissions Updated',
                    description: 'Framework seeding permissions have been updated successfully.',
                    duration: 4,
                });
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update framework permissions');
            }
        } catch (error) {
            api.error({
                message: 'Framework Permissions Update Failed',
                description: error instanceof Error ? error.message : 'Failed to update framework permissions. Please try again.',
                duration: 4,
            });
        } finally {
            setIsUpdatingPermissions(false);
        }
    };

    // LLM URL handlers
    const handleSaveLlmUrl = async () => {
        if (!llmUrlInput.trim()) {
            api.error({
                message: 'Invalid URL',
                description: 'Please enter a valid LLM URL!',
                duration: 4,
            });
            return;
        }

        try {
            await setCustomLlmUrl(llmUrlInput.trim());
            api.success({
                message: 'LLM URL Updated',
                description: 'Custom LLM URL has been saved successfully.',
                duration: 4,
            });
        } catch (error) {
            api.error({
                message: 'Failed to Save',
                description: 'Failed to save LLM URL. Please try again.',
                duration: 4,
            });
        }
    };

    const handleResetLlmUrl = async () => {
        try {
            await setCustomLlmUrl(null);
            setLlmUrlInput('');
            api.success({
                message: 'LLM URL Reset',
                description: 'LLM URL has been reset to the default URL.',
                duration: 4,
            });
        } catch (error) {
            api.error({
                message: 'Failed to Reset',
                description: 'Failed to reset LLM URL. Please try again.',
                duration: 4,
            });
        }
    };

    // LLM Payload Templates
    const payloadTemplates: Record<string, string> = {
        llamacpp: `{
  "model": "{{model}}",
  "prompt": "{{prompt}}",
  "stream": false
}`,
        openai: `{
  "model": "{{model}}",
  "messages": [
    {
      "role": "user",
      "content": "{{prompt}}"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 2048
}`,
        anthropic: `{
  "model": "{{model}}",
  "messages": [
    {
      "role": "user",
      "content": "{{prompt}}"
    }
  ],
  "max_tokens": 2048,
  "temperature": 0.7
}`,
        custom: llmPayloadInput
    };

    // LLM Payload handlers
    const handlePayloadTemplateChange = (template: string) => {
        setSelectedPayloadTemplate(template);
        if (template !== 'custom') {
            setLlmPayloadInput(payloadTemplates[template]);
        }
    };

    const handleSaveLlmPayload = async () => {
        if (!llmPayloadInput.trim()) {
            api.error({
                message: 'Invalid Payload',
                description: 'Please enter a valid LLM payload template!',
                duration: 4,
            });
            return;
        }

        // Validate JSON syntax
        try {
            // Try parsing with placeholder values to validate structure
            const testPayload = llmPayloadInput
                .replace(/\{\{prompt\}\}/g, 'test prompt')
                .replace(/\{\{model\}\}/g, 'test-model');
            JSON.parse(testPayload);
        } catch (error) {
            api.error({
                message: 'Invalid JSON',
                description: 'The payload template is not valid JSON. Please check the syntax.',
                duration: 4,
            });
            return;
        }

        try {
            await setCustomLlmPayload(llmPayloadInput.trim());
            api.success({
                message: 'LLM Payload Updated',
                description: 'Custom LLM payload template has been saved successfully.',
                duration: 4,
            });
        } catch (error) {
            api.error({
                message: 'Failed to Save',
                description: 'Failed to save LLM payload. Please try again.',
                duration: 4,
            });
        }
    };

    const handleResetLlmPayload = async () => {
        try {
            await setCustomLlmPayload(null);
            setSelectedPayloadTemplate('llamacpp');
            setLlmPayloadInput(payloadTemplates.llamacpp);
            api.success({
                message: 'LLM Payload Reset',
                description: 'LLM payload has been reset to the default template.',
                duration: 4,
            });
        } catch (error) {
            api.error({
                message: 'Failed to Reset',
                description: 'Failed to reset LLM payload. Please try again.',
                duration: 4,
            });
        }
    };

    // Scanner settings handlers
    const handleScannersToggle = async (checked: boolean) => {
        setIsSavingScannersEnabled(true);
        try {
            await setScannersEnabled(checked);
            api.success({
                message: 'Scanner Settings Updated',
                description: `Scanners have been ${checked ? 'enabled' : 'disabled'} globally.`,
                duration: 4,
            });
        } catch (error) {
            api.error({
                message: 'Failed to Update',
                description: 'Failed to update scanner settings. Please try again.',
                duration: 4,
            });
        }
        setIsSavingScannersEnabled(false);
    };

    const handleAllowedDomainsChange = async (values: string[]) => {
        try {
            await setAllowedScannerDomains(values);
            api.success({
                message: 'Allowed Domains Updated',
                description: values.length === 0
                    ? 'All organization domains now have access to scanners.'
                    : `${values.length} domain${values.length > 1 ? 's' : ''} updated successfully.`,
                duration: 4,
            });
        } catch (error) {
            api.error({
                message: 'Failed to Update',
                description: 'Failed to update allowed domains. Please try again.',
                duration: 4,
            });
        }
    };

    // CRA Mode handlers
    const handleCRAModeToggle = async (mode: 'focused' | 'extended') => {
        if (!current_user) return;
        setIsSavingCRAMode(true);
        try {
            // Toggle: if already active, turn off; otherwise set to this mode
            const newMode = craMode === mode ? null : mode;
            await saveCRAMode(current_user.organisation_id, newMode);
            const modeLabel = mode === 'focused' ? 'CRA Focused' : 'CRA Extended';
            api.success({
                message: 'CRA Mode Updated',
                description: newMode
                    ? `${modeLabel} has been enabled for your organization.`
                    : `CRA Mode has been disabled for your organization.`,
                duration: 4,
            });
        } catch (error) {
            api.error({
                message: 'Failed to Update',
                description: 'Failed to update CRA mode. Please try again.',
                duration: 4,
            });
        }
        setIsSavingCRAMode(false);
    };

    const handleCRAOperatorRoleChange = async (value: string) => {
        if (!current_user) return;
        const role = value === 'All' ? null : value;
        try {
            await saveCRAOperatorRole(current_user.organisation_id, role);
            api.success({
                message: 'Operator Role Updated',
                description: role ? `Operator role set to ${role}.` : 'Operator role set to All.',
                duration: 4,
            });
        } catch (error) {
            api.error({
                message: 'Failed to Update',
                description: 'Failed to update operator role. Please try again.',
                duration: 4,
            });
        }
    };

    // Login/Register Logo handlers (super_admin only)
    const fetchLoginLogos = async () => {
        setIsLoadingLoginLogos(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/login-logos`, {
                headers: { ...getAuthHeader() },
            });
            if (response.ok) {
                const data = await response.json();
                setLoginLogos(data);
            }
        } catch (error) {
            console.error('Error fetching login logos:', error);
        } finally {
            setIsLoadingLoginLogos(false);
        }
    };

    const handleLoginLogoFileChange = (file: File, setBase64: (val: string) => void) => {
        if (file.size > 2 * 1024 * 1024) {
            api.error({ message: 'File Too Large', description: 'Logo must be under 2MB.', duration: 4 });
            return false;
        }
        const reader = new FileReader();
        reader.onload = () => setBase64(reader.result as string);
        reader.readAsDataURL(file);
        return false; // prevent auto-upload
    };

    const handleSaveLoginLogo = async () => {
        if (!loginLogoName.trim()) {
            api.error({ message: 'Name Required', description: 'Please enter a logo name.', duration: 4 });
            return;
        }
        if (!loginLogoBase64) {
            api.error({ message: 'Logo Required', description: 'Please upload a logo image.', duration: 4 });
            return;
        }
        setIsSavingLoginLogo(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/login-logos`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
                body: JSON.stringify({
                    name: loginLogoName,
                    logo: loginLogoBase64,
                    is_global: loginLogoIsGlobal,
                    organisation_ids: loginLogoIsGlobal ? [] : loginLogoOrgIds,
                }),
            });
            if (response.ok) {
                api.success({ message: 'Logo Saved', description: 'Login logo created successfully.', duration: 3 });
                setLoginLogoName('');
                setLoginLogoBase64('');
                setLoginLogoIsGlobal(false);
                setLoginLogoOrgIds([]);
                fetchLoginLogos();
            } else {
                const err = await response.json();
                api.error({ message: 'Save Failed', description: err.detail || 'Failed to save logo.', duration: 4 });
            }
        } catch (error) {
            console.error('Error saving login logo:', error);
            api.error({ message: 'Save Failed', description: 'Network error.', duration: 4 });
        } finally {
            setIsSavingLoginLogo(false);
        }
    };

    const handleToggleLoginLogoActive = async (logoId: string, currentActive: boolean) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/login-logos/${logoId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
                body: JSON.stringify({ is_active: !currentActive }),
            });
            if (response.ok) fetchLoginLogos();
        } catch (error) {
            console.error('Error toggling login logo:', error);
        }
    };

    const handleDeleteLoginLogo = async (logoId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/login-logos/${logoId}`, {
                method: 'DELETE',
                headers: { ...getAuthHeader() },
            });
            if (response.ok) {
                api.success({ message: 'Logo Deleted', description: 'Login logo deleted successfully.', duration: 3 });
                fetchLoginLogos();
            }
        } catch (error) {
            console.error('Error deleting login logo:', error);
        }
    };

    const handleOpenLoginLogoEdit = (record: any) => {
        setEditingLoginLogo(record);
        setEditLoginLogoName(record.name);
        setEditLoginLogoBase64('');
        setEditLoginLogoIsGlobal(record.is_global);
        setEditLoginLogoOrgIds(record.organisation_ids || []);
    };

    const handleSaveLoginLogoEdit = async () => {
        if (!editingLoginLogo) return;
        setIsSavingLoginLogoEdit(true);
        try {
            const payload: Record<string, any> = {
                name: editLoginLogoName,
                is_global: editLoginLogoIsGlobal,
                organisation_ids: editLoginLogoIsGlobal ? [] : editLoginLogoOrgIds,
            };
            if (editLoginLogoBase64) {
                payload.logo = editLoginLogoBase64;
            }
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/login-logos/${editingLoginLogo.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
                body: JSON.stringify(payload),
            });
            if (response.ok) {
                api.success({ message: 'Logo Updated', description: 'Login logo updated successfully.', duration: 3 });
                setEditingLoginLogo(null);
                fetchLoginLogos();
            } else {
                const err = await response.json();
                api.error({ message: 'Update Failed', description: err.detail || 'Failed to update logo.', duration: 4 });
            }
        } catch (error) {
            console.error('Error updating login logo:', error);
            api.error({ message: 'Update Failed', description: 'Network error.', duration: 4 });
        } finally {
            setIsSavingLoginLogoEdit(false);
        }
    };

    // SSO settings handlers (super_admin only) - multi-record pattern
    const fetchSsoConfigs = async () => {
        setIsLoadingSsoConfigs(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/sso-configs`, {
                headers: { ...getAuthHeader() },
            });
            if (response.ok) {
                const data = await response.json();
                setSsoConfigs(data);
            }
        } catch (error) {
            console.error('Error fetching SSO configs:', error);
        } finally {
            setIsLoadingSsoConfigs(false);
        }
    };

    const handleSaveSsoConfig = async (values: any) => {
        setIsSavingSsoConfig(true);
        try {
            const payload: Record<string, any> = {
                label: values.label || null,
                google_client_id: values.google_client_id || null,
                google_client_secret: values.google_client_secret || null,
                microsoft_client_id: values.microsoft_client_id || null,
                microsoft_client_secret: values.microsoft_client_secret || null,
                microsoft_tenant_id: values.microsoft_tenant_id || 'common',
            };

            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/sso-config`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader(),
                },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                api.success({
                    message: 'SSO Configuration Saved',
                    description: 'SSO configuration has been created successfully.',
                    duration: 4,
                });
                ssoForm.resetFields();
                fetchSsoConfigs();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create SSO configuration');
            }
        } catch (error) {
            api.error({
                message: 'SSO Configuration Failed',
                description: error instanceof Error ? error.message : 'Failed to save SSO configuration. Please try again.',
                duration: 4,
            });
        } finally {
            setIsSavingSsoConfig(false);
        }
    };

    const handleToggleSsoActive = async (configId: string, currentlyActive: boolean) => {
        try {
            const endpoint = currentlyActive
                ? `${cyberbridge_back_end_rest_api}/settings/sso-config/${configId}/deactivate`
                : `${cyberbridge_back_end_rest_api}/settings/sso-config/${configId}/activate`;
            const response = await fetch(endpoint, {
                method: 'PUT',
                headers: { ...getAuthHeader() },
            });
            if (response.ok) {
                api.success({
                    message: 'SSO Configuration Updated',
                    description: currentlyActive ? 'Configuration deactivated.' : 'Configuration activated.',
                    duration: 3,
                });
                fetchSsoConfigs();
            } else {
                throw new Error('Failed to update SSO configuration');
            }
        } catch (error) {
            api.error({
                message: 'Update Failed',
                description: 'Failed to update SSO configuration status.',
                duration: 4,
            });
        }
    };

    const handleDeleteSsoConfig = async (configId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/sso-config/${configId}`, {
                method: 'DELETE',
                headers: { ...getAuthHeader() },
            });
            if (response.ok) {
                api.success({
                    message: 'SSO Configuration Deleted',
                    description: 'The SSO configuration has been removed.',
                    duration: 3,
                });
                fetchSsoConfigs();
            } else {
                throw new Error('Failed to delete SSO configuration');
            }
        } catch (error) {
            api.error({
                message: 'Delete Failed',
                description: 'Failed to delete SSO configuration.',
                duration: 4,
            });
        }
    };

    const handleOpenSsoEdit = (record: any) => {
        setEditingSsoConfig(record);
        ssoEditForm.setFieldsValue({
            label: record.label || '',
            google_client_id: record.google_client_id || '',
            google_client_secret: '',
            microsoft_client_id: record.microsoft_client_id || '',
            microsoft_client_secret: '',
            microsoft_tenant_id: record.microsoft_tenant_id || 'common',
        });
    };

    const handleSaveSsoEdit = async (values: any) => {
        if (!editingSsoConfig) return;
        setIsSavingSsoEdit(true);
        try {
            const payload: Record<string, any> = {
                label: values.label || null,
                google_client_id: values.google_client_id || null,
                microsoft_client_id: values.microsoft_client_id || null,
                microsoft_tenant_id: values.microsoft_tenant_id || 'common',
            };
            // Only send secrets if the user entered a new value
            if (values.google_client_secret) {
                payload.google_client_secret = values.google_client_secret;
            }
            if (values.microsoft_client_secret) {
                payload.microsoft_client_secret = values.microsoft_client_secret;
            }

            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/sso-config/${editingSsoConfig.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader(),
                },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                api.success({
                    message: 'SSO Configuration Updated',
                    description: 'SSO configuration has been updated successfully.',
                    duration: 4,
                });
                setEditingSsoConfig(null);
                fetchSsoConfigs();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update SSO configuration');
            }
        } catch (error) {
            api.error({
                message: 'Update Failed',
                description: error instanceof Error ? error.message : 'Failed to update SSO configuration.',
                duration: 4,
            });
        } finally {
            setIsSavingSsoEdit(false);
        }
    };

    // Organization AI Configuration functions (for org_admin)
    const resetOrgAiConfigState = () => {
        setOrgAiProvider('llamacpp');
        setOrgAiEnabled(false);
        setOrgQlonUrl('');
        setOrgQlonApiKey('');
        setOrgQlonUseTools(true);
        // Reset OpenAI (ChatGPT) settings
        setOrgOpenaiApiKey('');
        setOrgOpenaiModel('gpt-4o');
        setOrgOpenaiBaseUrl('');
        // Reset Anthropic (Claude) settings
        setOrgAnthropicApiKey('');
        setOrgAnthropicModel('claude-sonnet-4-20250514');
        // Reset X AI (Grok) settings
        setOrgXaiApiKey('');
        setOrgXaiModel('grok-3');
        setOrgXaiBaseUrl('');
        // Reset Google (Gemini) settings
        setOrgGoogleApiKey('');
        setOrgGoogleModel('gemini-2.0-flash');
        setOrgHasAiConfig(false);
        setOrgAiRemediatorEnabled(false);
        setOrgRemediatorPromptZap('');
        setOrgRemediatorPromptNmap('');
        setShowZapPromptEditor(false);
        setShowNmapPromptEditor(false);
        // Reset AI Policy Aligner settings
        setOrgAiPolicyAlignerEnabled(false);
        setOrgPolicyAlignerPrompt('');
        setShowPolicyAlignerPromptEditor(false);
    };

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
                // QLON settings
                setOrgQlonUrl(config.qlon_url || '');
                setOrgQlonApiKey(config.qlon_api_key || '');
                setOrgQlonUseTools(config.qlon_use_tools ?? true);
                // OpenAI (ChatGPT) settings
                setOrgOpenaiApiKey(config.openai_api_key || '');
                setOrgOpenaiModel(config.openai_model || 'gpt-4o');
                setOrgOpenaiBaseUrl(config.openai_base_url || '');
                // Anthropic (Claude) settings
                setOrgAnthropicApiKey(config.anthropic_api_key || '');
                setOrgAnthropicModel(config.anthropic_model || 'claude-sonnet-4-20250514');
                // X AI (Grok) settings
                setOrgXaiApiKey(config.xai_api_key || '');
                setOrgXaiModel(config.xai_model || 'grok-3');
                setOrgXaiBaseUrl(config.xai_base_url || '');
                // Google (Gemini) settings
                setOrgGoogleApiKey(config.google_api_key || '');
                setOrgGoogleModel(config.google_model || 'gemini-2.0-flash');
                // AI Remediator settings
                setOrgAiRemediatorEnabled(config.ai_remediator_enabled ?? false);
                setOrgRemediatorPromptZap(config.remediator_prompt_zap || '');
                setOrgRemediatorPromptNmap(config.remediator_prompt_nmap || '');
                // AI Policy Aligner settings
                setOrgAiPolicyAlignerEnabled(config.ai_policy_aligner_enabled ?? false);
                setOrgPolicyAlignerPrompt(config.policy_aligner_prompt || '');
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

    const handleSaveOrgAiConfig = async () => {
        if (!current_user || !current_user.organisation_id) {
            api.error({
                message: 'No Organization',
                description: 'Unable to determine your organization.',
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
                `${cyberbridge_back_end_rest_api}/settings/org-llm/${current_user.organisation_id}`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        ...getAuthHeader()
                    },
                    body: JSON.stringify({
                        llm_provider: orgAiProvider,
                        is_enabled: orgAiEnabled,
                        // QLON settings
                        qlon_url: orgQlonUrl || null,
                        qlon_api_key: orgQlonApiKey || null,
                        qlon_use_tools: orgQlonUseTools,
                        // OpenAI (ChatGPT) settings
                        openai_api_key: orgOpenaiApiKey || null,
                        openai_model: orgOpenaiModel || 'gpt-4o',
                        openai_base_url: orgOpenaiBaseUrl || null,
                        // Anthropic (Claude) settings
                        anthropic_api_key: orgAnthropicApiKey || null,
                        anthropic_model: orgAnthropicModel || 'claude-sonnet-4-20250514',
                        // X AI (Grok) settings
                        xai_api_key: orgXaiApiKey || null,
                        xai_model: orgXaiModel || 'grok-3',
                        xai_base_url: orgXaiBaseUrl || null,
                        // Google (Gemini) settings
                        google_api_key: orgGoogleApiKey || null,
                        google_model: orgGoogleModel || 'gemini-2.0-flash',
                        // AI Remediator settings
                        ai_remediator_enabled: orgAiRemediatorEnabled,
                        remediator_prompt_zap: orgRemediatorPromptZap || null,
                        remediator_prompt_nmap: orgRemediatorPromptNmap || null,
                        // AI Policy Aligner settings
                        ai_policy_aligner_enabled: orgAiPolicyAlignerEnabled,
                        policy_aligner_prompt: orgPolicyAlignerPrompt || null
                    })
                }
            );

            if (response.ok) {
                setOrgHasAiConfig(true);
                api.success({
                    message: 'AI Configuration Saved',
                    description: 'Your organization\'s AI settings have been saved successfully.',
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

    const handleDeleteOrgAiConfig = async () => {
        if (!current_user || !current_user.organisation_id) return;

        if (!window.confirm('Are you sure you want to reset your AI configuration? Your organization will use global default settings instead.')) {
            return;
        }

        setIsSavingOrgAiConfig(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/settings/org-llm/${current_user.organisation_id}`,
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
                    message: 'AI Configuration Reset',
                    description: 'Your organization will now use global default AI settings.',
                    duration: 4,
                });
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to reset AI configuration');
            }
        } catch (error) {
            api.error({
                message: 'Reset Failed',
                description: error instanceof Error ? error.message : 'Failed to reset AI configuration. Please try again.',
                duration: 4,
            });
        } finally {
            setIsSavingOrgAiConfig(false);
        }
    };

    // Backup & Restore handlers
    const handleSaveBackupConfig = async () => {
        if (!current_user) return;

        setIsSavingBackupConfig(true);
        const success = await updateBackupConfig(current_user.organisation_id, {
            backup_enabled: backupEnabled,
            backup_frequency: backupFrequency,
            backup_retention_years: backupRetentionYears
        });
        setIsSavingBackupConfig(false);

        if (success) {
            api.success({
                message: 'Backup Settings Saved',
                description: 'Your backup configuration has been updated successfully.',
                duration: 4,
            });
        } else {
            api.error({
                message: 'Save Failed',
                description: backupError || 'Failed to save backup configuration. Please try again.',
                duration: 4,
            });
        }
    };

    const handleCreateBackup = async () => {
        if (!current_user) return;

        setIsCreatingBackup(true);
        const backup = await createBackup(current_user.organisation_id);
        setIsCreatingBackup(false);

        if (backup) {
            api.success({
                message: 'Backup Created',
                description: `Backup "${backup.filename}" has been created successfully.`,
                duration: 4,
            });
        } else {
            api.error({
                message: 'Backup Failed',
                description: backupError || 'Failed to create backup. Please try again.',
                duration: 4,
            });
        }
    };

    const handleDownloadBackup = async (backupId: string) => {
        await downloadBackup(backupId);
    };

    const handleDeleteBackup = async (backupId: string) => {
        const success = await deleteBackup(backupId);
        if (success) {
            api.success({
                message: 'Backup Deleted',
                description: 'The backup has been deleted successfully.',
                duration: 4,
            });
        } else {
            api.error({
                message: 'Delete Failed',
                description: backupError || 'Failed to delete backup. Please try again.',
                duration: 4,
            });
        }
    };

    const handleRestoreBackup = async () => {
        if (!current_user || !selectedBackupForRestore) return;

        setIsRestoring(true);
        const result = await restoreBackup(current_user.organisation_id, selectedBackupForRestore);
        setIsRestoring(false);
        setRestoreModalVisible(false);
        setSelectedBackupForRestore(null);

        if (result && result.success) {
            api.success({
                message: 'Restore Completed',
                description: result.message,
                duration: 6,
            });
            // Refresh the backup list
            fetchBackups(current_user.organisation_id);
        } else {
            api.error({
                message: 'Restore Failed',
                description: result?.error || backupError || 'Failed to restore backup. Please try again.',
                duration: 4,
            });
        }
    };

    const formatFileSize = (bytes: number): string => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
    };

    const backupTableColumns = [
        {
            title: 'Filename',
            dataIndex: 'filename',
            key: 'filename',
            width: 200,
        },
        {
            title: 'Size',
            dataIndex: 'file_size',
            key: 'file_size',
            width: 100,
            render: (size: number) => formatFileSize(size),
        },
        {
            title: 'Type',
            dataIndex: 'backup_type',
            key: 'backup_type',
            width: 100,
            render: (type: string) => (
                <Tag color={type === 'manual' ? 'blue' : 'green'}>
                    {type === 'manual' ? 'Manual' : 'Scheduled'}
                </Tag>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: 100,
            render: (status: string) => (
                <Tag color={status === 'completed' ? 'success' : status === 'in_progress' ? 'processing' : 'error'}>
                    {status}
                </Tag>
            ),
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            width: 150,
            render: (date: string) => new Date(date).toLocaleDateString() + ' ' + new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
        {
            title: 'Expires',
            dataIndex: 'expires_at',
            key: 'expires_at',
            width: 120,
            render: (date: string) => new Date(date).toLocaleDateString(),
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 200,
            render: (_: any, record: any) => (
                <div style={{ display: 'flex', gap: '8px' }}>
                    <Button
                        type="link"
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => handleDownloadBackup(record.id)}
                        disabled={record.status !== 'completed'}
                    >
                        Download
                    </Button>
                    <Button
                        type="link"
                        size="small"
                        icon={<ReloadOutlined />}
                        onClick={() => {
                            setSelectedBackupForRestore(record.id);
                            setRestoreModalVisible(true);
                        }}
                        disabled={record.status !== 'completed'}
                    >
                        Restore
                    </Button>
                    <Popconfirm
                        title="Delete Backup"
                        description="Are you sure you want to delete this backup?"
                        onConfirm={() => handleDeleteBackup(record.id)}
                        okText="Delete"
                        cancelText="Cancel"
                        okButtonProps={{ danger: true }}
                    >
                        <Button
                            type="link"
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                        >
                            Delete
                        </Button>
                    </Popconfirm>
                </div>
            ),
        },
    ];

    // Options for dropdowns
    const clonableFrameworkOptions = clonableFrameworks.map(framework => ({
        value: framework.id,
        label: framework.name,
    }));

    const frameworkTemplateOptions = frameworkTemplates.map(template => ({
        value: template.id,
        label: template.name,
    }));

    const organizationOptions = organisations.map(org => ({
        value: org.id,
        label: org.domain || org.name, // Show domain first, fallback to name
    }));

    // Don't render anything if user is not super_admin or org_admin
    if (!current_user || !['super_admin', 'org_admin'].includes(current_user.role_name)) {
        return null;
    }

    return (
        <div>
            {contextHolder}
            <div className={'page-parent'}>
                <Sidebar onClick={onClick} selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
                <div className={'page-content'}>
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <InfoTitle
                                title={current_user.role_name === 'super_admin' ? 'System Settings' : 'Organization Settings'}
                                infoContent={SettingsInfo}
                                className="page-title"
                                icon={<SettingOutlined style={{ color: '#1a365d' }} />}
                            />
                        </div>
                    </div>

                    {/* Activate Scanners Section - Different views for super_admin and org_admin */}
                    <div className="page-section">
                        <h3 className="section-title">Scanner Access</h3>
                        <p className="section-subtitle">
                            {current_user.role_name === 'super_admin'
                                ? 'Control the visibility of the Scanners menu in the navigation sidebar and manage domain-specific access.'
                                : 'View your organization\'s scanner access status.'}
                        </p>

                        {/* Global scanner toggle - Only super_admin can modify */}
                        {current_user.role_name === 'super_admin' && (
                        <div className="form-row">
                            <div className="form-group">
                                <div
                                    className="ai-toggle-container"
                                    onClick={() => !isSavingScannersEnabled && handleScannersToggle(!scannersEnabled)}
                                >
                                    <div className={`ai-custom-toggle ${scannersEnabled ? 'active' : ''} ${isSavingScannersEnabled ? 'disabled' : ''}`}>
                                        <div className="ai-custom-toggle-handle" />
                                    </div>
                                    <span className="ai-toggle-label">
                                        {scannersEnabled ? 'Scanners Enabled' : 'Scanners Disabled'}
                                        {isSavingScannersEnabled && ' (saving...)'}
                                    </span>
                                </div>
                            </div>
                        </div>
                        )}

                        {/* Scanner access status for org_admin */}
                        {current_user.role_name === 'org_admin' && (
                            <div style={{ marginTop: '12px', padding: '16px', backgroundColor: scannersEnabled ? '#f6ffed' : '#fff2f0', borderRadius: '6px', border: `1px solid ${scannersEnabled ? '#b7eb8f' : '#ffccc7'}` }}>
                                <p style={{ margin: 0, color: scannersEnabled ? '#52c41a' : '#ff4d4f', fontSize: '14px', fontWeight: '500' }}>
                                    {scannersEnabled
                                        ? `✓ Scanners are enabled for your organization (${current_user.organisation_domain})`
                                        : `✗ Scanners are currently disabled. Contact your system administrator to enable access.`}
                                </p>
                            </div>
                        )}

                        {/* Domain-specific access control - Only visible to super_admin */}
                        {scannersEnabled && current_user.role_name === 'super_admin' && (
                            <div style={{ marginTop: '20px' }}>
                                <div className="form-row">
                                    <div className="form-group" style={{ minWidth: '400px' }}>
                                        <label className="form-label">
                                            Allowed Organization Domains
                                            <span style={{ color: '#8c8c8c', fontSize: '12px', marginLeft: '8px', fontWeight: 'normal' }}>
                                                (Leave empty to allow all domains)
                                            </span>
                                        </label>
                                        <Select
                                            mode="multiple"
                                            placeholder="Select organization domains with scanner access"
                                            onChange={(values) => handleAllowedDomainsChange(values)}
                                            value={allowedScannerDomains}
                                            options={organisations
                                                .filter(org => org.domain) // Only include orgs with domains
                                                .map(org => ({
                                                    value: org.domain,
                                                    label: org.domain,
                                                }))}
                                            showSearch
                                            filterOption={(input, option) =>
                                                (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                            }
                                            style={{ width: '100%' }}
                                            allowClear
                                        />
                                    </div>
                                </div>

                                <div style={{ marginTop: '12px', padding: '12px', backgroundColor: '#e6f7ff', borderRadius: '6px', border: '1px solid #91d5ff' }}>
                                    <p style={{ margin: 0, color: '#0050b3', fontSize: '13px', lineHeight: '1.6' }}>
                                        <strong>Current Access:</strong> {
                                            allowedScannerDomains.length === 0
                                                ? 'All organization domains have access to scanners'
                                                : `Only ${allowedScannerDomains.length} selected domain${allowedScannerDomains.length > 1 ? 's have' : ' has'} access to scanners`
                                        }
                                    </p>
                                </div>
                            </div>
                        )}

                        <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Instructions:</h4>
                            <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                                <li><strong>Enable Scanners globally:</strong> Master switch to enable/disable scanner access for the entire system</li>
                                <li><strong>Domain-specific access (super_admin only):</strong> Control which organization domains can see the Scanners menu</li>
                                <li>If no domains are selected, all organizations will have access to scanners (when globally enabled)</li>
                                <li>If specific domains are selected, only users from those organizations will see the Scanners menu</li>
                                <li>The Scanners menu provides access to Web App Scanner, Network Scanner, Code Analysis, and Dependency Analysis tools</li>
                                <li>Changes take effect immediately and are stored in your browser's local storage</li>
                            </ul>
                        </div>
                    </div>

                    {/* CRA Mode Section - Visible to super_admin and org_admin */}
                    {craFrameworkExists && (
                    <div className="page-section">
                        <h3 className="section-title">
                            <SafetyCertificateOutlined style={{ marginRight: '8px', color: '#1a365d' }} />
                            CRA Mode
                        </h3>
                        <p className="section-subtitle">
                            Enable Cyber Resilience Act (CRA) compliance mode for your organization. When enabled, the platform filters frameworks, menus, and assessments to focus on CRA requirements.
                        </p>

                        <div className="form-row">
                            <div className="form-group">
                                <div
                                    className="ai-toggle-container"
                                    onClick={() => !isSavingCRAMode && handleCRAModeToggle('focused')}
                                >
                                    <div className={`ai-custom-toggle ${craMode === 'focused' ? 'active' : ''} ${isSavingCRAMode ? 'disabled' : ''}`}>
                                        <div className="ai-custom-toggle-handle" />
                                    </div>
                                    <span className="ai-toggle-label">
                                        CRA Focused
                                        {isSavingCRAMode && ' (saving...)'}
                                    </span>
                                </div>
                            </div>
                            <div className="form-group">
                                <div
                                    className="ai-toggle-container"
                                    onClick={() => !isSavingCRAMode && handleCRAModeToggle('extended')}
                                >
                                    <div className={`ai-custom-toggle ${craMode === 'extended' ? 'active' : ''} ${isSavingCRAMode ? 'disabled' : ''}`}>
                                        <div className="ai-custom-toggle-handle" />
                                    </div>
                                    <span className="ai-toggle-label">
                                        CRA Extended
                                        {isSavingCRAMode && ' (saving...)'}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {craMode !== null && (
                            <div style={{ marginTop: '20px' }}>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label className="form-label">Operator Role</label>
                                        <Segmented
                                            value={craOperatorRole || 'All'}
                                            options={[
                                                { label: 'All', value: 'All' },
                                                { label: 'Manufacturer', value: 'Manufacturer' },
                                                { label: 'Importer', value: 'Importer' },
                                                { label: 'Distributor', value: 'Distributor' },
                                            ]}
                                            onChange={(value) => handleCRAOperatorRoleChange(value as string)}
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        <div style={{ marginTop: '16px', padding: '16px', backgroundColor: craMode === 'focused' ? '#f6ffed' : craMode === 'extended' ? '#e6f4ff' : '#f9f9f9', borderRadius: '6px', border: `1px solid ${craMode === 'focused' ? '#b7eb8f' : craMode === 'extended' ? '#91caff' : '#e8e8e8'}` }}>
                            <p style={{ margin: '0 0 8px 0', color: craMode === 'focused' ? '#52c41a' : craMode === 'extended' ? '#1677ff' : '#595959', fontSize: '14px', fontWeight: '500' }}>
                                {craMode === 'focused'
                                    ? '✓ CRA Focused is active. The menu is filtered to CRA-only pages with a simplified layout.'
                                    : craMode === 'extended'
                                    ? '✓ CRA Extended is active. CRA items are visible alongside the full standard menu.'
                                    : 'CRA Mode is disabled. Enable Focused or Extended to activate CRA compliance features.'}
                            </p>
                            <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '13px', lineHeight: '1.6' }}>
                                <li><strong>CRA Focused:</strong> Strict CRA-only experience — simplified menu showing only CRA-relevant pages</li>
                                <li><strong>CRA Extended:</strong> Full standard menu plus CRA items (Technical File, EU Declaration, CE Marking) visible alongside everything</li>
                                <li>The operator role (Manufacturer, Importer, Distributor) filters objectives to those applicable to your role</li>
                                <li>This setting applies to all users in your organization</li>
                            </ul>
                        </div>
                    </div>
                    )}

                    {/* SSO Configuration Section - Only visible to super_admin */}
                    {current_user.role_name === 'super_admin' && (
                    <div className="page-section">
                        <h3 className="section-title">SSO Configuration</h3>
                        <p className="section-subtitle">
                            Configure Single Sign-On for Google and Microsoft OAuth2 authentication. You can create multiple SSO configurations and activate the one you want to use.
                        </p>

                        {/* Add New SSO Configuration Form */}
                        <Form
                            form={ssoForm}
                            layout="vertical"
                            onFinish={handleSaveSsoConfig}
                            initialValues={{ microsoft_tenant_id: 'common' }}
                        >
                            <div className="form-row">
                                <div className="form-group" style={{ minWidth: '400px' }}>
                                    <Form.Item
                                        name="label"
                                        label="Configuration Label"
                                        rules={[{ required: true, message: 'Please enter a label' }]}
                                    >
                                        <Input placeholder="e.g. My Company SSO" />
                                    </Form.Item>
                                </div>
                            </div>

                            {/* Google OAuth2 */}
                            <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Google OAuth2</h4>
                            <div className="form-row">
                                <div className="form-group" style={{ minWidth: '400px' }}>
                                    <Form.Item name="google_client_id" label="Client ID">
                                        <Input placeholder="Enter Google Client ID" />
                                    </Form.Item>
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group" style={{ minWidth: '400px' }}>
                                    <Form.Item name="google_client_secret" label="Client Secret">
                                        <Input.Password placeholder="Enter Google Client Secret" />
                                    </Form.Item>
                                </div>
                            </div>

                            {/* Microsoft OAuth2 */}
                            <h4 style={{ margin: '20px 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Microsoft OAuth2</h4>
                            <div className="form-row">
                                <div className="form-group" style={{ minWidth: '400px' }}>
                                    <Form.Item name="microsoft_client_id" label="Client ID">
                                        <Input placeholder="Enter Microsoft Client ID" />
                                    </Form.Item>
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group" style={{ minWidth: '400px' }}>
                                    <Form.Item name="microsoft_client_secret" label="Client Secret">
                                        <Input.Password placeholder="Enter Microsoft Client Secret" />
                                    </Form.Item>
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group" style={{ minWidth: '400px' }}>
                                    <Form.Item
                                        name="microsoft_tenant_id"
                                        label={<span>Tenant ID <span style={{ color: '#8c8c8c', fontSize: '12px', fontWeight: 'normal' }}>(Use "common" for multi-tenant)</span></span>}
                                    >
                                        <Input placeholder="common" />
                                    </Form.Item>
                                </div>
                            </div>

                            <div style={{ marginTop: '8px' }}>
                                <Button type="primary" htmlType="submit" loading={isSavingSsoConfig}>
                                    Save SSO Configuration
                                </Button>
                            </div>
                        </Form>

                        {/* Saved SSO Configurations Table */}
                        {ssoConfigs.length > 0 && (
                            <div style={{ marginTop: '24px' }}>
                                <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Saved SSO Configurations</h4>
                                <Table
                                    dataSource={ssoConfigs}
                                    rowKey="id"
                                    loading={isLoadingSsoConfigs}
                                    pagination={false}
                                    size="small"
                                    columns={[
                                        {
                                            title: 'Label',
                                            dataIndex: 'label',
                                            key: 'label',
                                            render: (text: string) => text || '(no label)',
                                        },
                                        {
                                            title: 'Google',
                                            dataIndex: 'google_configured',
                                            key: 'google_configured',
                                            render: (configured: boolean) => (
                                                <Tag color={configured ? 'green' : 'default'}>
                                                    {configured ? 'Configured' : 'Not configured'}
                                                </Tag>
                                            ),
                                        },
                                        {
                                            title: 'Microsoft',
                                            dataIndex: 'microsoft_configured',
                                            key: 'microsoft_configured',
                                            render: (configured: boolean) => (
                                                <Tag color={configured ? 'green' : 'default'}>
                                                    {configured ? 'Configured' : 'Not configured'}
                                                </Tag>
                                            ),
                                        },
                                        {
                                            title: 'Active',
                                            dataIndex: 'is_active',
                                            key: 'is_active',
                                            render: (isActive: boolean, record: any) => (
                                                <div
                                                    className="ai-toggle-container"
                                                    onClick={() => handleToggleSsoActive(record.id, isActive)}
                                                >
                                                    <div className={`ai-custom-toggle ${isActive ? 'active' : ''}`}>
                                                        <div className="ai-custom-toggle-handle" />
                                                    </div>
                                                </div>
                                            ),
                                        },
                                        {
                                            title: '',
                                            key: 'actions',
                                            render: (_: any, record: any) => (
                                                <div style={{ display: 'flex', gap: '4px' }}>
                                                    <Button type="text" icon={<EditOutlined />} size="small" onClick={() => handleOpenSsoEdit(record)} />
                                                    <Popconfirm
                                                        title="Delete this SSO configuration?"
                                                        description="This action cannot be undone."
                                                        onConfirm={() => handleDeleteSsoConfig(record.id)}
                                                        okText="Delete"
                                                        cancelText="Cancel"
                                                    >
                                                        <Button type="text" danger icon={<DeleteOutlined />} size="small" />
                                                    </Popconfirm>
                                                </div>
                                            ),
                                        },
                                    ]}
                                />
                            </div>
                        )}

                        {/* Edit SSO Configuration Modal */}
                        <Modal
                            title="Edit SSO Configuration"
                            open={!!editingSsoConfig}
                            onCancel={() => setEditingSsoConfig(null)}
                            footer={null}
                            width={520}
                        >
                            <Form
                                form={ssoEditForm}
                                layout="vertical"
                                onFinish={handleSaveSsoEdit}
                                style={{ marginTop: '16px' }}
                            >
                                <Form.Item name="label" label="Configuration Label" rules={[{ required: true, message: 'Please enter a label' }]}>
                                    <Input placeholder="e.g. My Company SSO" />
                                </Form.Item>

                                <h4 style={{ margin: '16px 0 8px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Google OAuth2</h4>
                                <Form.Item name="google_client_id" label="Client ID">
                                    <Input placeholder="Enter Google Client ID" />
                                </Form.Item>
                                <Form.Item name="google_client_secret" label="Client Secret">
                                    <Input.Password placeholder="Leave blank to keep current value" />
                                </Form.Item>

                                <h4 style={{ margin: '16px 0 8px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Microsoft OAuth2</h4>
                                <Form.Item name="microsoft_client_id" label="Client ID">
                                    <Input placeholder="Enter Microsoft Client ID" />
                                </Form.Item>
                                <Form.Item name="microsoft_client_secret" label="Client Secret">
                                    <Input.Password placeholder="Leave blank to keep current value" />
                                </Form.Item>
                                <Form.Item
                                    name="microsoft_tenant_id"
                                    label={<span>Tenant ID <span style={{ color: '#8c8c8c', fontSize: '12px', fontWeight: 'normal' }}>(Use "common" for multi-tenant)</span></span>}
                                >
                                    <Input placeholder="common" />
                                </Form.Item>

                                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '16px' }}>
                                    <Button onClick={() => setEditingSsoConfig(null)}>Cancel</Button>
                                    <Button type="primary" htmlType="submit" loading={isSavingSsoEdit}>
                                        Save Changes
                                    </Button>
                                </div>
                            </Form>
                        </Modal>

                        <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Instructions:</h4>
                            <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                                <li><strong>Google:</strong> Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank" rel="noopener noreferrer">console.cloud.google.com</a> &rarr; Create OAuth 2.0 Client ID &rarr; Set redirect URI to <code>{'{'}your-api-url{'}'}/auth/sso/google/callback</code></li>
                                <li><strong>Microsoft:</strong> Go to <a href="https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps" target="_blank" rel="noopener noreferrer">portal.azure.com</a> &rarr; App registrations &rarr; New registration &rarr; Set redirect URI to <code>{'{'}your-api-url{'}'}/auth/sso/microsoft/callback</code></li>
                                <li>Users must be pre-registered with their SSO provider set (Google or Microsoft) before they can sign in via SSO</li>
                                <li>SSO buttons on the login page will only become active when the active configuration has the respective provider credentials configured</li>
                                <li>Only one SSO configuration can be active at a time. Activating one will deactivate the previous.</li>
                            </ul>
                        </div>
                    </div>
                    )}

                    {/* Login/Register Page Logo Section - Only visible to super_admin */}
                    {current_user.role_name === 'super_admin' && (
                    <div className="page-section">
                        <h3 className="section-title">Login/Register Page Logo</h3>
                        <p className="section-subtitle">
                            Upload custom logos to display on the login and registration pages. Assign logos globally or to specific organisations. When a user types their email, the logo will switch to match their organisation's domain.
                        </p>

                        {/* Upload New Logo Form */}
                        <div className="form-row">
                            <div className="form-group" style={{ minWidth: '300px' }}>
                                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500, fontSize: '14px' }}>Logo Name</label>
                                <Input
                                    placeholder="e.g. Company Logo"
                                    value={loginLogoName}
                                    onChange={(e) => setLoginLogoName(e.target.value)}
                                    style={{ marginBottom: '12px' }}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500, fontSize: '14px' }}>Logo Image (max 2MB)</label>
                                <Upload
                                    accept="image/*"
                                    showUploadList={false}
                                    beforeUpload={(file) => handleLoginLogoFileChange(file, setLoginLogoBase64)}
                                >
                                    <Button icon={<CloudUploadOutlined />}>Select Image</Button>
                                </Upload>
                                {loginLogoBase64 && (
                                    <div style={{ marginTop: '8px' }}>
                                        <img src={loginLogoBase64} alt="Preview" style={{ maxHeight: '60px', maxWidth: '200px', objectFit: 'contain', border: '1px solid #d9d9d9', borderRadius: '4px', padding: '4px' }} />
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="form-row" style={{ marginTop: '12px' }}>
                            <div className="form-group">
                                <Checkbox checked={loginLogoIsGlobal} onChange={(e) => setLoginLogoIsGlobal(e.target.checked)}>
                                    Global (applies to all organisations)
                                </Checkbox>
                            </div>
                        </div>

                        {!loginLogoIsGlobal && (
                            <div className="form-row" style={{ marginTop: '12px' }}>
                                <div className="form-group" style={{ minWidth: '400px' }}>
                                    <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500, fontSize: '14px' }}>Assign to Organisations</label>
                                    <Select
                                        mode="multiple"
                                        placeholder="Select organisations"
                                        value={loginLogoOrgIds}
                                        onChange={setLoginLogoOrgIds}
                                        style={{ width: '100%' }}
                                        options={organisations.map((org: any) => ({ label: org.name, value: String(org.id) }))}
                                    />
                                </div>
                            </div>
                        )}

                        <div style={{ marginTop: '16px' }}>
                            <Button type="primary" onClick={handleSaveLoginLogo} loading={isSavingLoginLogo}>
                                Upload Logo
                            </Button>
                        </div>

                        {/* Existing Logos Table */}
                        {loginLogos.length > 0 && (
                            <div style={{ marginTop: '24px' }}>
                                <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Uploaded Logos</h4>
                                <Table
                                    dataSource={loginLogos}
                                    rowKey="id"
                                    loading={isLoadingLoginLogos}
                                    pagination={false}
                                    size="small"
                                    columns={[
                                        {
                                            title: 'Preview',
                                            dataIndex: 'logo',
                                            key: 'logo',
                                            width: 100,
                                            render: (logo: string) => (
                                                <img src={logo} alt="Logo" style={{ maxHeight: '36px', maxWidth: '80px', objectFit: 'contain' }} />
                                            ),
                                        },
                                        {
                                            title: 'Name',
                                            dataIndex: 'name',
                                            key: 'name',
                                        },
                                        {
                                            title: 'Scope',
                                            key: 'scope',
                                            render: (_: any, record: any) => record.is_global
                                                ? <Tag color="blue">Global</Tag>
                                                : (record.organisation_names || []).map((name: string) => <Tag key={name}>{name}</Tag>),
                                        },
                                        {
                                            title: 'Active',
                                            dataIndex: 'is_active',
                                            key: 'is_active',
                                            render: (isActive: boolean, record: any) => (
                                                <div
                                                    className="ai-toggle-container"
                                                    onClick={() => handleToggleLoginLogoActive(record.id, isActive)}
                                                >
                                                    <div className={`ai-custom-toggle ${isActive ? 'active' : ''}`}>
                                                        <div className="ai-custom-toggle-handle" />
                                                    </div>
                                                </div>
                                            ),
                                        },
                                        {
                                            title: '',
                                            key: 'actions',
                                            render: (_: any, record: any) => (
                                                <div style={{ display: 'flex', gap: '4px' }}>
                                                    <Button type="text" icon={<EditOutlined />} size="small" onClick={() => handleOpenLoginLogoEdit(record)} />
                                                    <Popconfirm
                                                        title="Delete this logo?"
                                                        description="This action cannot be undone."
                                                        onConfirm={() => handleDeleteLoginLogo(record.id)}
                                                        okText="Delete"
                                                        cancelText="Cancel"
                                                    >
                                                        <Button type="text" danger icon={<DeleteOutlined />} size="small" />
                                                    </Popconfirm>
                                                </div>
                                            ),
                                        },
                                    ]}
                                />
                            </div>
                        )}

                        {/* Edit Login Logo Modal */}
                        <Modal
                            title="Edit Login Logo"
                            open={!!editingLoginLogo}
                            onCancel={() => setEditingLoginLogo(null)}
                            footer={null}
                            width={520}
                        >
                            <div style={{ marginTop: '16px' }}>
                                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500, fontSize: '14px' }}>Logo Name</label>
                                <Input
                                    placeholder="Logo name"
                                    value={editLoginLogoName}
                                    onChange={(e) => setEditLoginLogoName(e.target.value)}
                                    style={{ marginBottom: '16px' }}
                                />

                                <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500, fontSize: '14px' }}>Replace Image (optional)</label>
                                <Upload
                                    accept="image/*"
                                    showUploadList={false}
                                    beforeUpload={(file) => handleLoginLogoFileChange(file, setEditLoginLogoBase64)}
                                >
                                    <Button icon={<CloudUploadOutlined />}>Select New Image</Button>
                                </Upload>
                                {(editLoginLogoBase64 || editingLoginLogo?.logo) && (
                                    <div style={{ marginTop: '8px', marginBottom: '16px' }}>
                                        <img src={editLoginLogoBase64 || editingLoginLogo?.logo} alt="Preview" style={{ maxHeight: '60px', maxWidth: '200px', objectFit: 'contain', border: '1px solid #d9d9d9', borderRadius: '4px', padding: '4px' }} />
                                    </div>
                                )}

                                <Checkbox checked={editLoginLogoIsGlobal} onChange={(e) => setEditLoginLogoIsGlobal(e.target.checked)} style={{ marginBottom: '16px' }}>
                                    Global (applies to all organisations)
                                </Checkbox>

                                {!editLoginLogoIsGlobal && (
                                    <div style={{ marginBottom: '16px' }}>
                                        <label style={{ display: 'block', marginBottom: '4px', fontWeight: 500, fontSize: '14px' }}>Assign to Organisations</label>
                                        <Select
                                            mode="multiple"
                                            placeholder="Select organisations"
                                            value={editLoginLogoOrgIds}
                                            onChange={setEditLoginLogoOrgIds}
                                            style={{ width: '100%' }}
                                            options={organisations.map((org: any) => ({ label: org.name, value: String(org.id) }))}
                                        />
                                    </div>
                                )}

                                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '16px' }}>
                                    <Button onClick={() => setEditingLoginLogo(null)}>Cancel</Button>
                                    <Button type="primary" onClick={handleSaveLoginLogoEdit} loading={isSavingLoginLogoEdit}>
                                        Save Changes
                                    </Button>
                                </div>
                            </div>
                        </Modal>
                    </div>
                    )}

                    {/* Toggle styles - shared by CRA mode, scanners, AI config, etc. */}
                    <style>{`
                        .ai-toggle-container {
                            display: inline-flex;
                            align-items: center;
                            gap: 10px;
                            cursor: pointer;
                        }
                        .ai-custom-toggle {
                            position: relative;
                            width: 44px;
                            height: 24px;
                            background: #d9d9d9;
                            border-radius: 12px;
                            transition: background 0.2s ease;
                            cursor: pointer;
                            flex-shrink: 0;
                        }
                        .ai-custom-toggle.active {
                            background: #1890ff;
                        }
                        .ai-custom-toggle.disabled {
                            opacity: 0.6;
                            cursor: not-allowed;
                        }
                        .ai-custom-toggle-handle {
                            position: absolute;
                            top: 2px;
                            left: 2px;
                            width: 20px;
                            height: 20px;
                            background: white;
                            border-radius: 50%;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                            transition: left 0.2s ease;
                        }
                        .ai-custom-toggle.active .ai-custom-toggle-handle {
                            left: 22px;
                        }
                        .ai-toggle-label {
                            font-size: 14px;
                            color: #555;
                            user-select: none;
                            font-weight: 500;
                        }
                    `}</style>

                    {/* AI Configuration Section - Only visible to super_admin */}
                    {current_user.role_name === 'super_admin' && (
                    <>
                    <div className="page-section">
                        <h3 className="section-title">AI Configuration</h3>
                        <p className="section-subtitle">
                            Control AI functionality across the entire platform. When disabled, all AI-powered features (scan analysis, correlations, etc.) will use fallback formatting instead.
                        </p>

                        <div className="form-row">
                            <div className="form-group">
                                <div
                                    className="ai-toggle-container"
                                    onClick={() => !isSavingAiEnabled && handleAiEnabledToggle(!aiEnabled)}
                                >
                                    <div className={`ai-custom-toggle ${aiEnabled ? 'active' : ''} ${isSavingAiEnabled ? 'disabled' : ''}`}>
                                        <div className="ai-custom-toggle-handle" />
                                    </div>
                                    <span className="ai-toggle-label">
                                        {aiEnabled ? 'AI is Enabled' : 'AI is Disabled'}
                                        {isSavingAiEnabled && ' (saving...)'}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div style={{ marginTop: '16px', padding: '16px', backgroundColor: aiEnabled ? '#f6ffed' : '#fff2f0', borderRadius: '6px', border: `1px solid ${aiEnabled ? '#b7eb8f' : '#ffccc7'}` }}>
                            <p style={{ margin: 0, color: aiEnabled ? '#52c41a' : '#ff4d4f', fontSize: '14px', fontWeight: '500' }}>
                                {aiEnabled
                                    ? '✓ AI features are active. Scan results will be analyzed and enhanced by AI.'
                                    : '✗ AI features are disabled. Scan results will use basic formatting without AI analysis.'}
                            </p>
                        </div>

                        <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>What this affects:</h4>
                            <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                                <li><strong>Security Scanner Analysis:</strong> AI-powered interpretation of security scan results</li>
                                <li><strong>Framework Correlations:</strong> Automatic correlation generation between policies and framework objectives</li>
                                <li><strong>Per-Organization Settings:</strong> Individual organizations can configure their own AI provider under Organizations management</li>
                            </ul>
                        </div>

                        {/* AI Policy Aligner - Global Toggle */}
                        <div style={{ marginTop: '24px', padding: '20px', backgroundColor: aiPolicyAlignerGlobalEnabled ? '#f6ffed' : '#fafafa', borderRadius: '8px', border: aiPolicyAlignerGlobalEnabled ? '1px solid #b7eb8f' : '1px solid #e8e8e8' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                                <div>
                                    <h4 style={{ margin: '0 0 8px 0', color: '#333', fontSize: '15px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <RobotOutlined style={{ color: aiPolicyAlignerGlobalEnabled ? '#52c41a' : '#999' }} />
                                        AI Policy Aligner
                                        {aiPolicyAlignerGlobalEnabled && (
                                            <span style={{ backgroundColor: '#52c41a', color: 'white', fontSize: '11px', padding: '2px 8px', borderRadius: '10px', fontWeight: 'normal' }}>
                                                Enabled
                                            </span>
                                        )}
                                    </h4>
                                    <p style={{ margin: 0, color: '#666', fontSize: '13px' }}>
                                        Enable AI-powered alignment of policies to framework questions. When enabled, org admins can generate alignments in Framework Management, and policies will be automatically suggested when users start new assessments.
                                    </p>
                                </div>
                                <div
                                    onClick={() => !isSavingAiPolicyAligner && handleAiPolicyAlignerGlobalToggle(!aiPolicyAlignerGlobalEnabled)}
                                    style={{
                                        position: 'relative',
                                        width: '44px',
                                        height: '24px',
                                        background: aiPolicyAlignerGlobalEnabled ? '#52c41a' : '#d9d9d9',
                                        borderRadius: '12px',
                                        transition: 'background 0.2s ease',
                                        cursor: isSavingAiPolicyAligner ? 'not-allowed' : 'pointer',
                                        opacity: isSavingAiPolicyAligner ? 0.6 : 1,
                                        flexShrink: 0
                                    }}
                                >
                                    <div style={{
                                        position: 'absolute',
                                        top: '2px',
                                        left: aiPolicyAlignerGlobalEnabled ? '22px' : '2px',
                                        width: '20px',
                                        height: '20px',
                                        background: 'white',
                                        borderRadius: '50%',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                                        transition: 'left 0.2s ease'
                                    }} />
                                </div>
                            </div>

                            <div style={{ padding: '12px', backgroundColor: aiPolicyAlignerGlobalEnabled ? '#f6ffed' : '#f9f9f9', borderRadius: '6px', border: `1px solid ${aiPolicyAlignerGlobalEnabled ? '#d9f7be' : '#e8e8e8'}` }}>
                                <p style={{ margin: 0, color: aiPolicyAlignerGlobalEnabled ? '#52c41a' : '#8c8c8c', fontSize: '13px' }}>
                                    {aiPolicyAlignerGlobalEnabled
                                        ? '✓ AI Policy Aligner is active. Org admins can generate policy alignments in Framework Management.'
                                        : '○ AI Policy Aligner is disabled. Enable to allow organizations to use AI-powered policy alignment.'}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Super Admin Focused Mode Section */}
                    <div className="page-section">
                        <h3 className="section-title">Super Admin Focused Mode</h3>
                        <p className="section-subtitle">
                            When enabled, the navigation menu will be simplified to show only essential administration items as top-level menu entries (Dashboard, Frameworks, Organizations, Users, Activity Log, Correlations, Background Jobs, System Settings).
                        </p>

                        <div className="form-row">
                            <div className="form-group">
                                <div
                                    className="ai-toggle-container"
                                    onClick={() => !isSavingSuperAdminFocusedMode && handleSuperAdminFocusedModeToggle(!superAdminFocusedMode)}
                                >
                                    <div className={`ai-custom-toggle ${superAdminFocusedMode ? 'active' : ''} ${isSavingSuperAdminFocusedMode ? 'disabled' : ''}`}>
                                        <div className="ai-custom-toggle-handle" />
                                    </div>
                                    <span className="ai-toggle-label">
                                        {superAdminFocusedMode ? 'Focused Mode Enabled' : 'Focused Mode Disabled'}
                                        {isSavingSuperAdminFocusedMode && ' (saving...)'}
                                    </span>
                                </div>
                            </div>
                        </div>

                        <div style={{ marginTop: '16px', padding: '16px', backgroundColor: superAdminFocusedMode ? '#f6ffed' : '#e6f7ff', borderRadius: '6px', border: `1px solid ${superAdminFocusedMode ? '#b7eb8f' : '#91d5ff'}` }}>
                            <p style={{ margin: 0, color: superAdminFocusedMode ? '#52c41a' : '#0050b3', fontSize: '14px', fontWeight: '500' }}>
                                {superAdminFocusedMode
                                    ? '✓ Focused Mode is active. The menu shows only administration-related items.'
                                    : 'Focused Mode is disabled. The menu shows all available items including Assessments, Frameworks, Risks, etc.'}
                            </p>
                        </div>

                        <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>When Focused Mode is enabled:</h4>
                            <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                                <li><strong>Dashboard:</strong> Main dashboard view</li>
                                <li><strong>Frameworks:</strong> Manage Frameworks, Chapters & Objectives, Framework Questions, Updates, Objectives</li>
                                <li><strong>Organizations:</strong> Manage all organizations</li>
                                <li><strong>Users:</strong> User management</li>
                                <li><strong>Activity Log:</strong> System activity history</li>
                                <li><strong>Correlations:</strong> Policy-objective correlations</li>
                                <li><strong>Background Jobs:</strong> Scheduled tasks and jobs</li>
                                <li><strong>System Settings:</strong> This settings page</li>
                            </ul>
                            <p style={{ margin: '12px 0 0 0', color: '#8c8c8c', fontSize: '13px' }}>
                                <em>Hidden items: Assessments, Risks, Documents, Security Tools, Audit Engagements</em>
                            </p>
                        </div>
                    </div>
                    </>
                    )}

                    {/* Organization AI Configuration Section - Visible to org_admin and super_admin */}
                    {['super_admin', 'org_admin'].includes(current_user.role_name) && (
                    <>
                    <style>{`
                        .org-ai-toggle-container {
                            display: inline-flex;
                            align-items: center;
                            gap: 10px;
                            cursor: pointer;
                        }
                        .org-ai-custom-toggle {
                            position: relative;
                            width: 44px;
                            height: 24px;
                            background: #d9d9d9;
                            border-radius: 12px;
                            transition: background 0.2s ease;
                            cursor: pointer;
                            flex-shrink: 0;
                        }
                        .org-ai-custom-toggle.active {
                            background: #1890ff;
                        }
                        .org-ai-custom-toggle.disabled {
                            opacity: 0.6;
                            cursor: not-allowed;
                        }
                        .org-ai-custom-toggle-handle {
                            position: absolute;
                            top: 2px;
                            left: 2px;
                            width: 20px;
                            height: 20px;
                            background: white;
                            border-radius: 50%;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                            transition: left 0.2s ease;
                        }
                        .org-ai-custom-toggle.active .org-ai-custom-toggle-handle {
                            left: 22px;
                        }
                        .org-ai-toggle-label {
                            font-size: 14px;
                            color: #555;
                            user-select: none;
                            font-weight: 500;
                        }
                    `}</style>
                    <div className="page-section">
                        <h3 className="section-title">
                            <RobotOutlined style={{ marginRight: '8px' }} />
                            AI Provider Configuration
                        </h3>
                        <p className="section-subtitle">
                            Configure the AI provider for your organization ({current_user.organisation_name}). You can use the global default settings or configure your own AI provider.
                        </p>

                        {isLoadingOrgAiConfig ? (
                            <div style={{ padding: '20px', textAlign: 'center', color: '#8c8c8c' }}>
                                Loading AI configuration...
                            </div>
                        ) : (
                            <>
                                {/* Enable/Disable AI for this org */}
                                <div className="form-row">
                                    <div className="form-group">
                                        <div
                                            className="org-ai-toggle-container"
                                            onClick={() => setOrgAiEnabled(!orgAiEnabled)}
                                        >
                                            <div className={`org-ai-custom-toggle ${orgAiEnabled ? 'active' : ''}`}>
                                                <div className="org-ai-custom-toggle-handle" />
                                            </div>
                                            <span className="org-ai-toggle-label">
                                                {orgAiEnabled ? 'AI is Enabled for your Organization' : 'AI is Disabled for your Organization'}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {orgAiEnabled && (
                                    <>
                                        {/* Provider Selection */}
                                        <div className="form-row" style={{ marginTop: '16px' }}>
                                            <div className="form-group" style={{ minWidth: '300px' }}>
                                                <label className="form-label">AI Provider</label>
                                                <Select
                                                    value={orgAiProvider}
                                                    onChange={(value) => setOrgAiProvider(value)}
                                                    style={{ width: '100%' }}
                                                    options={[
                                                        { value: 'llamacpp', label: 'llama.cpp (Self-hosted)' },
                                                        { value: 'openai', label: 'OpenAI (ChatGPT)' },
                                                        { value: 'anthropic', label: 'Anthropic (Claude)' },
                                                        { value: 'xai', label: 'X AI (Grok)' },
                                                        { value: 'google', label: 'Google (Gemini)' },
                                                        { value: 'qlon', label: 'QLON Ai' }
                                                    ]}
                                                />
                                            </div>
                                        </div>

                                        {/* llama.cpp Configuration */}
                                        {orgAiProvider === 'llamacpp' && (
                                            <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#f5f0ff', borderRadius: '6px', border: '1px solid #9775c7' }}>
                                                <h4 style={{ margin: '0 0 16px 0', color: '#6b47b8', fontSize: '14px', fontWeight: '600' }}>llama.cpp Configuration</h4>
                                                <p style={{ margin: '0', color: '#666', fontSize: '13px' }}>
                                                    llama.cpp runs as a separate container with the phi-4 model (Q4_K_M quantization). No additional configuration is required — it auto-connects on port 11435.
                                                </p>
                                            </div>
                                        )}

                                        {/* OpenAI (ChatGPT) Configuration */}
                                        {orgAiProvider === 'openai' && (
                                            <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#f0fff0', borderRadius: '6px', border: '1px solid #74d680' }}>
                                                <h4 style={{ margin: '0 0 16px 0', color: '#388e3c', fontSize: '14px', fontWeight: '600' }}>OpenAI (ChatGPT) Configuration</h4>
                                                <div className="form-row">
                                                    <div className="form-group" style={{ minWidth: '400px' }}>
                                                        <label className="form-label required">OpenAI API Key</label>
                                                        <Input.Password
                                                            placeholder="sk-..."
                                                            value={orgOpenaiApiKey}
                                                            onChange={(e) => setOrgOpenaiApiKey(e.target.value)}
                                                        />
                                                    </div>
                                                </div>
                                                <div className="form-row" style={{ marginTop: '12px' }}>
                                                    <div className="form-group" style={{ minWidth: '200px' }}>
                                                        <label className="form-label">Model</label>
                                                        <Select
                                                            value={orgOpenaiModel}
                                                            onChange={(value) => setOrgOpenaiModel(value)}
                                                            style={{ width: '100%' }}
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
                                                    <div className="form-group" style={{ minWidth: '300px' }}>
                                                        <label className="form-label">Custom Base URL (optional)</label>
                                                        <Input
                                                            placeholder="https://api.openai.com/v1"
                                                            value={orgOpenaiBaseUrl}
                                                            onChange={(e) => setOrgOpenaiBaseUrl(e.target.value)}
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* Anthropic (Claude) Configuration */}
                                        {orgAiProvider === 'anthropic' && (
                                            <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#fff5e6', borderRadius: '6px', border: '1px solid #d4a574' }}>
                                                <h4 style={{ margin: '0 0 16px 0', color: '#b8860b', fontSize: '14px', fontWeight: '600' }}>Anthropic (Claude) Configuration</h4>
                                                <div className="form-row">
                                                    <div className="form-group" style={{ minWidth: '400px' }}>
                                                        <label className="form-label required">Anthropic API Key</label>
                                                        <Input.Password
                                                            placeholder="sk-ant-..."
                                                            value={orgAnthropicApiKey}
                                                            onChange={(e) => setOrgAnthropicApiKey(e.target.value)}
                                                        />
                                                    </div>
                                                </div>
                                                <div className="form-row" style={{ marginTop: '12px' }}>
                                                    <div className="form-group" style={{ minWidth: '300px' }}>
                                                        <label className="form-label">Model</label>
                                                        <Select
                                                            value={orgAnthropicModel}
                                                            onChange={(value) => setOrgAnthropicModel(value)}
                                                            style={{ width: '100%' }}
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
                                            </div>
                                        )}

                                        {/* X AI (Grok) Configuration */}
                                        {orgAiProvider === 'xai' && (
                                            <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '6px', border: '1px solid #666' }}>
                                                <h4 style={{ margin: '0 0 16px 0', color: '#333', fontSize: '14px', fontWeight: '600' }}>X AI (Grok) Configuration</h4>
                                                <div className="form-row">
                                                    <div className="form-group" style={{ minWidth: '400px' }}>
                                                        <label className="form-label required">X AI API Key</label>
                                                        <Input.Password
                                                            placeholder="xai-..."
                                                            value={orgXaiApiKey}
                                                            onChange={(e) => setOrgXaiApiKey(e.target.value)}
                                                        />
                                                    </div>
                                                </div>
                                                <div className="form-row" style={{ marginTop: '12px' }}>
                                                    <div className="form-group" style={{ minWidth: '200px' }}>
                                                        <label className="form-label">Model</label>
                                                        <Select
                                                            value={orgXaiModel}
                                                            onChange={(value) => setOrgXaiModel(value)}
                                                            style={{ width: '100%' }}
                                                            options={[
                                                                { value: 'grok-3', label: 'Grok 3 (Recommended)' },
                                                                { value: 'grok-3-fast', label: 'Grok 3 Fast' },
                                                                { value: 'grok-2', label: 'Grok 2' },
                                                                { value: 'grok-2-mini', label: 'Grok 2 Mini' }
                                                            ]}
                                                        />
                                                    </div>
                                                    <div className="form-group" style={{ minWidth: '300px' }}>
                                                        <label className="form-label">Custom Base URL (optional)</label>
                                                        <Input
                                                            placeholder="https://api.x.ai/v1"
                                                            value={orgXaiBaseUrl}
                                                            onChange={(e) => setOrgXaiBaseUrl(e.target.value)}
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* Google (Gemini) Configuration */}
                                        {orgAiProvider === 'google' && (
                                            <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#e8f0fe', borderRadius: '6px', border: '1px solid #4285f4' }}>
                                                <h4 style={{ margin: '0 0 16px 0', color: '#1a73e8', fontSize: '14px', fontWeight: '600' }}>Google (Gemini) Configuration</h4>
                                                <div className="form-row">
                                                    <div className="form-group" style={{ minWidth: '400px' }}>
                                                        <label className="form-label required">Google AI API Key</label>
                                                        <Input.Password
                                                            placeholder="AIza..."
                                                            value={orgGoogleApiKey}
                                                            onChange={(e) => setOrgGoogleApiKey(e.target.value)}
                                                        />
                                                    </div>
                                                </div>
                                                <div className="form-row" style={{ marginTop: '12px' }}>
                                                    <div className="form-group" style={{ minWidth: '300px' }}>
                                                        <label className="form-label">Model</label>
                                                        <Select
                                                            value={orgGoogleModel}
                                                            onChange={(value) => setOrgGoogleModel(value)}
                                                            style={{ width: '100%' }}
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
                                            </div>
                                        )}

                                        {/* QLON Configuration */}
                                        {orgAiProvider === 'qlon' && (
                                            <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#fff7e6', borderRadius: '6px', border: '1px solid #ffd591' }}>
                                                <h4 style={{ margin: '0 0 16px 0', color: '#d46b08', fontSize: '14px', fontWeight: '600' }}>QLON Ai Configuration</h4>
                                                <div className="form-row">
                                                    <div className="form-group" style={{ minWidth: '400px' }}>
                                                        <label className="form-label required">QLON API URL</label>
                                                        <Input
                                                            placeholder="https://your-qlon-instance.com"
                                                            value={orgQlonUrl}
                                                            onChange={(e) => setOrgQlonUrl(e.target.value)}
                                                        />
                                                    </div>
                                                </div>
                                                <div className="form-row" style={{ marginTop: '12px' }}>
                                                    <div className="form-group" style={{ minWidth: '400px' }}>
                                                        <label className="form-label required">QLON API Key</label>
                                                        <Input.Password
                                                            placeholder="Enter QLON API Key"
                                                            value={orgQlonApiKey}
                                                            onChange={(e) => setOrgQlonApiKey(e.target.value)}
                                                        />
                                                    </div>
                                                </div>
                                                <div className="form-row" style={{ marginTop: '12px' }}>
                                                    <div className="form-group">
                                                        <Checkbox
                                                            checked={orgQlonUseTools}
                                                            onChange={(e) => setOrgQlonUseTools(e.target.checked)}
                                                        >
                                                            Enable Integration Tools (recommended)
                                                        </Checkbox>
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* AI Remediator Section */}
                                        <div style={{ marginTop: '24px', padding: '20px', backgroundColor: orgAiRemediatorEnabled ? '#f0f9ff' : '#fafafa', borderRadius: '8px', border: orgAiRemediatorEnabled ? '1px solid #91d5ff' : '1px solid #e8e8e8' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                                                <div>
                                                    <h4 style={{ margin: '0 0 8px 0', color: '#333', fontSize: '15px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                        <RobotOutlined style={{ color: orgAiRemediatorEnabled ? '#1890ff' : '#999' }} />
                                                        AI Remediator
                                                        {orgAiRemediatorEnabled && (
                                                            <span style={{ backgroundColor: '#52c41a', color: 'white', fontSize: '11px', padding: '2px 8px', borderRadius: '10px', fontWeight: 'normal' }}>
                                                                Enabled
                                                            </span>
                                                        )}
                                                    </h4>
                                                    <p style={{ margin: 0, color: '#666', fontSize: '13px' }}>
                                                        Enable AI-powered remediation guidance for Web App and Network security scan results.
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
                                                <div style={{ marginTop: '16px', borderTop: '1px solid #e8e8e8', paddingTop: '16px' }}>
                                                    <h5 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '13px', fontWeight: '600' }}>
                                                        Custom Remediation Prompts (Optional)
                                                    </h5>
                                                    <p style={{ margin: '0 0 12px 0', color: '#666', fontSize: '12px' }}>
                                                        Customize the AI prompts for remediation guidance. Leave empty to use defaults.
                                                    </p>

                                                    {/* ZAP Prompt */}
                                                    <div style={{ marginBottom: '12px' }}>
                                                        <div
                                                            onClick={() => setShowZapPromptEditor(!showZapPromptEditor)}
                                                            style={{ cursor: 'pointer', padding: '10px 14px', backgroundColor: '#fff', border: '1px solid #d9d9d9', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                                                        >
                                                            <span style={{ fontWeight: '500', color: '#333', fontSize: '13px' }}>
                                                                Web App Scanner Prompt
                                                                {orgRemediatorPromptZap && <span style={{ marginLeft: '8px', fontSize: '10px', color: '#1890ff' }}>(Custom)</span>}
                                                            </span>
                                                            <span style={{ color: '#999' }}>{showZapPromptEditor ? '▼' : '▶'}</span>
                                                        </div>
                                                        {showZapPromptEditor && (
                                                            <div style={{ marginTop: '8px' }}>
                                                                <textarea
                                                                    className="form-input"
                                                                    placeholder="Enter custom Web App Scanner remediation prompt..."
                                                                    value={orgRemediatorPromptZap}
                                                                    onChange={(e) => setOrgRemediatorPromptZap(e.target.value)}
                                                                    style={{ width: '100%', minHeight: '120px', fontFamily: 'monospace', fontSize: '12px', resize: 'vertical' }}
                                                                />
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Nmap Prompt */}
                                                    <div>
                                                        <div
                                                            onClick={() => setShowNmapPromptEditor(!showNmapPromptEditor)}
                                                            style={{ cursor: 'pointer', padding: '10px 14px', backgroundColor: '#fff', border: '1px solid #d9d9d9', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                                                        >
                                                            <span style={{ fontWeight: '500', color: '#333', fontSize: '13px' }}>
                                                                Network Scanner Prompt
                                                                {orgRemediatorPromptNmap && <span style={{ marginLeft: '8px', fontSize: '10px', color: '#1890ff' }}>(Custom)</span>}
                                                            </span>
                                                            <span style={{ color: '#999' }}>{showNmapPromptEditor ? '▼' : '▶'}</span>
                                                        </div>
                                                        {showNmapPromptEditor && (
                                                            <div style={{ marginTop: '8px' }}>
                                                                <textarea
                                                                    className="form-input"
                                                                    placeholder="Enter custom Network Scanner remediation prompt..."
                                                                    value={orgRemediatorPromptNmap}
                                                                    onChange={(e) => setOrgRemediatorPromptNmap(e.target.value)}
                                                                    style={{ width: '100%', minHeight: '120px', fontFamily: 'monospace', fontSize: '12px', resize: 'vertical' }}
                                                                />
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* AI Policy Aligner Section */}
                                        <div style={{ marginTop: '24px', padding: '20px', backgroundColor: orgAiPolicyAlignerEnabled ? '#f6ffed' : '#fafafa', borderRadius: '8px', border: orgAiPolicyAlignerEnabled ? '1px solid #b7eb8f' : '1px solid #e8e8e8' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                                                <div>
                                                    <h4 style={{ margin: '0 0 8px 0', color: '#333', fontSize: '15px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                        <RobotOutlined style={{ color: orgAiPolicyAlignerEnabled ? '#52c41a' : '#999' }} />
                                                        AI Policy Aligner
                                                        {orgAiPolicyAlignerEnabled && (
                                                            <span style={{ backgroundColor: '#52c41a', color: 'white', fontSize: '11px', padding: '2px 8px', borderRadius: '10px', fontWeight: 'normal' }}>
                                                                Enabled
                                                            </span>
                                                        )}
                                                    </h4>
                                                    <p style={{ margin: 0, color: '#666', fontSize: '13px' }}>
                                                        Enable AI-powered alignment of policies to framework questions. When enabled, policies will be automatically suggested when starting new assessments.
                                                    </p>
                                                </div>
                                                <div
                                                    onClick={() => setOrgAiPolicyAlignerEnabled(!orgAiPolicyAlignerEnabled)}
                                                    style={{
                                                        position: 'relative',
                                                        width: '44px',
                                                        height: '24px',
                                                        background: orgAiPolicyAlignerEnabled ? '#52c41a' : '#d9d9d9',
                                                        borderRadius: '12px',
                                                        transition: 'background 0.2s ease',
                                                        cursor: 'pointer',
                                                        flexShrink: 0
                                                    }}
                                                >
                                                    <div style={{
                                                        position: 'absolute',
                                                        top: '2px',
                                                        left: orgAiPolicyAlignerEnabled ? '22px' : '2px',
                                                        width: '20px',
                                                        height: '20px',
                                                        background: 'white',
                                                        borderRadius: '50%',
                                                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                                                        transition: 'left 0.2s ease'
                                                    }} />
                                                </div>
                                            </div>

                                            {orgAiPolicyAlignerEnabled && (
                                                <div style={{ marginTop: '16px', borderTop: '1px solid #e8e8e8', paddingTop: '16px' }}>
                                                    <h5 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '13px', fontWeight: '600' }}>
                                                        Custom Alignment Prompt (Optional)
                                                    </h5>
                                                    <p style={{ margin: '0 0 12px 0', color: '#666', fontSize: '12px' }}>
                                                        Customize the AI prompt for policy alignment. Leave empty to use the default prompt.
                                                    </p>

                                                    <div>
                                                        <div
                                                            onClick={() => setShowPolicyAlignerPromptEditor(!showPolicyAlignerPromptEditor)}
                                                            style={{ cursor: 'pointer', padding: '10px 14px', backgroundColor: '#fff', border: '1px solid #d9d9d9', borderRadius: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                                                        >
                                                            <span style={{ fontWeight: '500', color: '#333', fontSize: '13px' }}>
                                                                Policy Alignment Prompt
                                                                {orgPolicyAlignerPrompt && <span style={{ marginLeft: '8px', fontSize: '10px', color: '#52c41a' }}>(Custom)</span>}
                                                            </span>
                                                            <span style={{ color: '#999' }}>{showPolicyAlignerPromptEditor ? '▼' : '▶'}</span>
                                                        </div>
                                                        {showPolicyAlignerPromptEditor && (
                                                            <div style={{ marginTop: '8px' }}>
                                                                <textarea
                                                                    className="form-input"
                                                                    placeholder="Enter custom policy alignment prompt..."
                                                                    value={orgPolicyAlignerPrompt}
                                                                    onChange={(e) => setOrgPolicyAlignerPrompt(e.target.value)}
                                                                    style={{ width: '100%', minHeight: '120px', fontFamily: 'monospace', fontSize: '12px', resize: 'vertical' }}
                                                                />
                                                            </div>
                                                        )}
                                                    </div>

                                                    <p style={{ margin: '16px 0 0 0', color: '#52c41a', fontSize: '12px', fontWeight: '500' }}>
                                                        Tip: Use the "Generate AI Alignments" button in Framework Management to align policies to framework questions.
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                    </>
                                )}

                                {/* Save/Delete buttons */}
                                <div className="control-group" style={{ marginTop: '20px' }}>
                                    <button
                                        className="add-button"
                                        onClick={handleSaveOrgAiConfig}
                                        disabled={isSavingOrgAiConfig}
                                    >
                                        {isSavingOrgAiConfig ? 'Saving...' : 'Save AI Configuration'}
                                    </button>
                                    {orgHasAiConfig && (
                                        <button
                                            className="delete-button"
                                            onClick={handleDeleteOrgAiConfig}
                                            disabled={isSavingOrgAiConfig}
                                            style={{ marginLeft: '8px' }}
                                        >
                                            Reset to Global Default
                                        </button>
                                    )}
                                </div>

                                {/* Status info */}
                                <div style={{ marginTop: '16px', padding: '12px', backgroundColor: orgHasAiConfig ? '#e6f7ff' : '#f9f9f9', borderRadius: '6px', border: `1px solid ${orgHasAiConfig ? '#91d5ff' : '#e8e8e8'}` }}>
                                    <p style={{ margin: 0, color: orgHasAiConfig ? '#0050b3' : '#8c8c8c', fontSize: '13px' }}>
                                        {orgHasAiConfig
                                            ? `✓ Your organization has custom AI settings configured (Provider: ${
                                                orgAiProvider === 'llamacpp' ? 'llama.cpp' :
                                                orgAiProvider === 'openai' ? 'OpenAI (ChatGPT)' :
                                                orgAiProvider === 'anthropic' ? 'Anthropic (Claude)' :
                                                orgAiProvider === 'xai' ? 'X AI (Grok)' :
                                                orgAiProvider === 'google' ? 'Google (Gemini)' :
                                                'QLON Ai'
                                            })`
                                            : '○ Your organization is using global default AI settings. Save configuration to customize.'}
                                    </p>
                                </div>
                            </>
                        )}
                    </div>
                    </>
                    )}

                    {/* Clone Frameworks Section - Only visible to super_admin */}
                    {current_user.role_name === 'super_admin' && (
                    <div className="page-section">
                        <h3 className="section-title">Clone Frameworks from Other Organizations</h3>
                        <p className="section-subtitle">
                            Clone frameworks between organizations with all their questions and objectives.
                        </p>

                        <div className="form-row">
                            <div className="form-group" style={{ minWidth: '300px' }}>
                                <label className="form-label">Select Frameworks</label>
                                <Select
                                    mode="multiple"
                                    placeholder="Select frameworks to clone"
                                    onChange={handleClonableFrameworkChange}
                                    options={clonableFrameworkOptions}
                                    value={selectedClonableFrameworkIds}
                                    showSearch
                                    filterOption={(input, option) =>
                                        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                    }
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group" style={{ minWidth: '250px' }}>
                                <label className="form-label">Target Organization</label>
                                <Select
                                    placeholder="Select target organization"
                                    onChange={handleOrganizationChange}
                                    options={organizationOptions}
                                    value={selectedOrganizationId || undefined}
                                    showSearch
                                    filterOption={(input, option) =>
                                        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                    }
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group" style={{ minWidth: '300px' }}>
                                <label className="form-label">Custom Framework Name</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="Custom framework name (optional)"
                                    value={customFrameworkName}
                                    onChange={handleCustomFrameworkNameChange}
                                />
                            </div>
                            <div className="control-group">
                                <button
                                    className="add-button"
                                    onClick={handleCloneFrameworks}
                                >
                                    Clone Selected Frameworks
                                </button>
                            </div>
                        </div>

                        <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Instructions:</h4>
                            <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                                <li>Select one or more frameworks from any organization</li>
                                <li>Choose the target organization where frameworks should be cloned</li>
                                <li>Optionally provide a custom name for single framework cloning or name prefix for multiple frameworks</li>
                                <li>All questions and objectives will be included in the cloned frameworks</li>
                            </ul>
                        </div>
                    </div>
                    )}

                    {/* SMTP Configuration Section - Only visible to super_admin */}
                    {current_user.role_name === 'super_admin' && (
                    <div className="page-section">
                        <h3 className="section-title">SMTP Email Configuration</h3>
                        <p className="section-subtitle">
                            Add SMTP configurations for sending email notifications. You can manage multiple configurations and toggle which one is active.
                        </p>

                        <div style={{ maxWidth: '600px' }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#0f386a', fontSize: '16px', fontWeight: '600' }}>Add SMTP Configuration</h4>
                            <Form
                                form={smtpForm}
                                layout="vertical"
                                onFinish={handleSaveSmtpConfig}
                            >
                                <div className="form-row">
                                    <div className="form-group">
                                        <Form.Item
                                            label="Label"
                                            name="label"
                                            style={{ marginBottom: 0 }}
                                        >
                                            <Input placeholder="e.g. Gmail (Dev)" className="form-input" />
                                        </Form.Item>
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <Form.Item
                                            label="SMTP Server Host"
                                            name="smtp_server"
                                            rules={[{ required: true, message: 'Please enter SMTP server host' }]}
                                            style={{ marginBottom: 0 }}
                                        >
                                            <Input placeholder="smtp.gmail.com" className="form-input" />
                                        </Form.Item>
                                    </div>
                                    <div className="form-group">
                                        <Form.Item
                                            label="SMTP Port"
                                            name="smtp_port"
                                            rules={[{ required: true, message: 'Please enter SMTP port' }]}
                                            style={{ marginBottom: 0 }}
                                        >
                                            <Input placeholder="587" type="number" className="form-input" />
                                        </Form.Item>
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <Form.Item
                                            label="Sender Email (From address)"
                                            name="sender_email"
                                            style={{ marginBottom: 0 }}
                                        >
                                            <Input placeholder="no-reply@example.com" className="form-input" />
                                        </Form.Item>
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <Form.Item
                                            label="Username (optional)"
                                            name="username"
                                            style={{ marginBottom: 0 }}
                                        >
                                            <Input placeholder="your-email@example.com" className="form-input" />
                                        </Form.Item>
                                    </div>
                                    <div className="form-group">
                                        <Form.Item
                                            label="Password (optional)"
                                            name="password"
                                            style={{ marginBottom: 0 }}
                                        >
                                            <Input.Password placeholder="App password (if auth required)" />
                                        </Form.Item>
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group">
                                        <Form.Item
                                            name="use_tls"
                                            valuePropName="checked"
                                            initialValue={true}
                                            style={{ marginBottom: 0 }}
                                        >
                                            <div
                                                className="ai-toggle-container"
                                                onClick={() => handleTlsToggle(!tlsEnabled)}
                                            >
                                                <div className={`ai-custom-toggle ${tlsEnabled ? 'active' : ''}`}>
                                                    <div className="ai-custom-toggle-handle" />
                                                </div>
                                                <span className="ai-toggle-label">
                                                    {tlsEnabled ? 'TLS/SSL Enabled' : 'TLS/SSL Disabled'}
                                                </span>
                                            </div>
                                        </Form.Item>
                                    </div>
                                    <div className="control-group">
                                        <Form.Item style={{ marginBottom: 0 }}>
                                            <Button
                                                type="primary"
                                                htmlType="submit"
                                                loading={isSavingSmtp}
                                                className="add-button"
                                            >
                                                Save SMTP Configuration
                                            </Button>
                                        </Form.Item>
                                    </div>
                                </div>
                            </Form>
                        </div>

                        {/* Saved SMTP Configurations Table */}
                        <div style={{ marginTop: '24px', padding: '20px', border: '1px solid #f0f0f0', borderRadius: '8px', backgroundColor: '#fafafa' }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#0f386a', fontSize: '16px', fontWeight: '600' }}>Saved SMTP Configurations</h4>
                            <Table
                                dataSource={smtpConfigs}
                                rowKey="id"
                                loading={isLoadingSmtpConfigs}
                                pagination={false}
                                size="small"
                                columns={[
                                    {
                                        title: 'Label',
                                        dataIndex: 'label',
                                        key: 'label',
                                        render: (text: string) => text || '-',
                                    },
                                    {
                                        title: 'Server',
                                        dataIndex: 'smtp_server',
                                        key: 'smtp_server',
                                        render: (text: string, record: any) => `${text}:${record.smtp_port}`,
                                    },
                                    {
                                        title: 'Sender Email',
                                        dataIndex: 'sender_email',
                                        key: 'sender_email',
                                        render: (text: string, record: any) => text || record.username || '-',
                                    },
                                    {
                                        title: 'Active',
                                        dataIndex: 'is_active',
                                        key: 'is_active',
                                        width: 100,
                                        render: (isActive: boolean, record: any) => (
                                            <div
                                                className="ai-toggle-container"
                                                onClick={() => handleToggleSmtpActive(record.id, isActive)}
                                                style={{ cursor: 'pointer' }}
                                            >
                                                <div className={`ai-custom-toggle ${isActive ? 'active' : ''}`}>
                                                    <div className="ai-custom-toggle-handle" />
                                                </div>
                                            </div>
                                        ),
                                    },
                                    {
                                        title: '',
                                        key: 'actions',
                                        width: 60,
                                        render: (_: any, record: any) => (
                                            <Popconfirm
                                                title="Delete this SMTP configuration?"
                                                onConfirm={() => handleDeleteSmtpConfig(record.id)}
                                                okText="Delete"
                                                cancelText="Cancel"
                                            >
                                                <Button type="text" danger icon={<DeleteOutlined />} size="small" />
                                            </Popconfirm>
                                        ),
                                    },
                                ]}
                            />
                        </div>

                        {/* Email Test Section */}
                        <div style={{ marginTop: '24px', padding: '20px', border: '1px solid #f0f0f0', borderRadius: '8px', backgroundColor: '#fafafa' }}>
                            <h4 style={{ margin: '0 0 8px 0', color: '#0f386a', fontSize: '16px', fontWeight: '600' }}>Test Email Configuration</h4>
                            <p style={{ marginBottom: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.5' }}>
                                Send a test email to verify your active SMTP configuration is working correctly.
                            </p>

                            <Form
                                form={emailTestForm}
                                onFinish={handleTestEmail}
                            >
                                <div className="form-row">
                                    <div className="form-group" style={{ maxWidth: '300px' }}>
                                        <Form.Item
                                            name="recipient_email"
                                            rules={[
                                                { required: true, message: 'Please enter recipient email' },
                                                { type: 'email', message: 'Please enter a valid email address' }
                                            ]}
                                            style={{ marginBottom: 0 }}
                                        >
                                            <Input placeholder="recipient@example.com" className="form-input" />
                                        </Form.Item>
                                    </div>
                                    <div className="control-group">
                                        <Form.Item style={{ marginBottom: 0 }}>
                                            <Button
                                                type="primary"
                                                htmlType="submit"
                                                loading={isTestingEmail}
                                                className="add-button"
                                            >
                                                Send Test Email
                                            </Button>
                                        </Form.Item>
                                    </div>
                                </div>
                            </Form>
                        </div>
                    </div>
                    )}

                    {/* Framework Seeding Permissions Section - Only visible to super_admin */}
                    {current_user.role_name === 'super_admin' && (
                    <div className="page-section">
                        <h3 className="section-title">Frameworks Seeding Permissions</h3>
                        <p className="section-subtitle">
                            Control which frameworks each organization's admin can access for seeding. By default, all organizations can seed from all available frameworks.
                        </p>

                        <div className="form-row">
                            <div className="form-group" style={{ minWidth: '250px' }}>
                                <label className="form-label">Select Organization</label>
                                <Select
                                    placeholder="Select organization to configure"
                                    onChange={handlePermissionOrgChange}
                                    options={organizationOptions}
                                    value={selectedPermissionOrgId || undefined}
                                    showSearch
                                    filterOption={(input, option) =>
                                        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                    }
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>

                        {selectedPermissionOrgId && (
                        <div className="form-row">
                            <div className="form-group" style={{ minWidth: '400px' }}>
                                <label className="form-label">Allowed Framework Templates for Seeding</label>
                                <Select
                                    mode="multiple"
                                    placeholder="Select framework templates this organization can seed"
                                    onChange={handleAllowedTemplatesChange}
                                    options={frameworkTemplateOptions}
                                    value={selectedAllowedTemplateIds}
                                    showSearch
                                    filterOption={(input, option) =>
                                        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                    }
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="control-group">
                                <button
                                    className="add-button"
                                    onClick={handleUpdateFrameworkPermissions}
                                    disabled={isUpdatingPermissions}
                                >
                                    {isUpdatingPermissions ? 'Updating...' : 'Update Permissions'}
                                </button>
                            </div>
                        </div>
                        )}

                        <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Instructions:</h4>
                            <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                                <li>Select an organization to configure framework seeding permissions</li>
                                <li>Choose which frameworks the organization's admin can use for seeding</li>
                                <li>If no frameworks are selected, the organization will have no seeding access</li>
                                <li>By default (before any configuration), all organizations can seed from all frameworks</li>
                                <li>Once configured, only selected frameworks will be available in the "Add Framework from Template" dropdown</li>
                            </ul>
                        </div>
                    </div>
                    )}

                    {/* Domain Blacklist Section - Only visible to super_admin */}
                    {current_user.role_name === 'super_admin' && (
                    <div className="page-section">
                        <h3 className="section-title">Add Domains to Blacklist</h3>
                        <p className="section-subtitle">
                            Manage domain access by blacklisting or whitelisting domains. Blacklisted domains cannot register new users and existing users are deactivated.
                        </p>

                        {/* Add to Blacklist Form */}
                        <div className="form-row">
                            <div className="form-group" style={{ minWidth: '200px' }}>
                                <label className="form-label">Domain</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="example.com"
                                    value={newBlacklistDomain}
                                    onChange={(e) => setNewBlacklistDomain(e.target.value)}
                                />
                            </div>
                            <div className="form-group" style={{ minWidth: '300px' }}>
                                <label className="form-label">Reason (Optional)</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="Reason for blacklisting"
                                    value={blacklistReason}
                                    onChange={(e) => setBlacklistReason(e.target.value)}
                                />
                            </div>
                            <div className="control-group">
                                <button
                                    className="add-button"
                                    onClick={handleAddToBlacklist}
                                    disabled={isAddingToBlacklist}
                                >
                                    {isAddingToBlacklist ? 'Adding...' : 'Add to Blacklist'}
                                </button>
                            </div>
                        </div>

                        {/* CSV Bulk Upload Section */}
                        <div style={{
                            marginTop: '24px',
                            padding: '20px',
                            border: '1px solid #e8e8e8',
                            borderRadius: '8px',
                            backgroundColor: '#fafafa'
                        }}>
                            <h4 style={{ margin: '0 0 16px 0', color: '#0f386a', fontSize: '16px', fontWeight: '600' }}>
                                Bulk Upload from CSV File
                            </h4>
                            <p style={{ marginBottom: '16px', color: '#666', fontSize: '14px' }}>
                                Upload a CSV file with domains to blacklist. File should have one domain per line or a 'domain' column.
                            </p>

                            <div className="form-row">
                                <div className="form-group" style={{ minWidth: '300px' }}>
                                    <label className="form-label">CSV File</label>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <input
                                            id="csvFileInput"
                                            type="file"
                                            accept=".csv"
                                            onChange={handleCsvFileChange}
                                            style={{ display: 'none' }}
                                        />
                                        <button
                                            type="button"
                                            onClick={() => document.getElementById('csvFileInput')?.click()}
                                            style={{
                                                backgroundColor: '#fafafa',
                                                border: '1px dashed #d9d9d9',
                                                borderRadius: '6px',
                                                padding: '12px 16px',
                                                cursor: 'pointer',
                                                color: '#666',
                                                fontSize: '14px',
                                                minWidth: '140px',
                                                transition: 'all 0.3s ease',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                gap: '8px'
                                            }}
                                            onMouseOver={(e) => {
                                                e.target.style.backgroundColor = '#f0f9ff';
                                                e.target.style.borderColor = '#1890ff';
                                                e.target.style.color = '#1890ff';
                                            }}
                                            onMouseOut={(e) => {
                                                e.target.style.backgroundColor = '#fafafa';
                                                e.target.style.borderColor = '#d9d9d9';
                                                e.target.style.color = '#666';
                                            }}
                                        >
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                                                <polyline points="14,2 14,8 20,8"/>
                                                <line x1="16" y1="13" x2="8" y2="13"/>
                                                <line x1="16" y1="17" x2="8" y2="17"/>
                                                <polyline points="10,9 9,9 8,9"/>
                                            </svg>
                                            Choose CSV File
                                        </button>
                                        {csvFile && (
                                            <div style={{
                                                padding: '8px 12px',
                                                backgroundColor: '#f6ffed',
                                                border: '1px solid #b7eb8f',
                                                borderRadius: '4px',
                                                fontSize: '12px',
                                                color: '#389e0d',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '6px'
                                            }}>
                                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <polyline points="20,6 9,17 4,12"/>
                                                </svg>
                                                {csvFile.name} ({(csvFile.size / 1024).toFixed(1)} KB)
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <div className="form-group" style={{ minWidth: '250px' }}>
                                    <label className="form-label">Reason (Optional)</label>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder="Bulk security measure"
                                        value={blacklistReason}
                                        onChange={(e) => setBlacklistReason(e.target.value)}
                                    />
                                </div>
                                <div className="control-group">
                                    <button
                                        className="add-button"
                                        onClick={handleUploadCsv}
                                        disabled={isUploadingCsv || !csvFile}
                                    >
                                        {isUploadingCsv ? 'Uploading...' : 'Upload CSV'}
                                    </button>
                                </div>
                            </div>

                            <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ fontSize: '12px', color: '#999' }}>
                                    <strong>CSV Format:</strong> One domain per line, or with headers: domain,reason
                                </div>
                                <button
                                    className="download-sample-button"
                                    onClick={handleDownloadSampleCsv}
                                    style={{
                                        backgroundColor: '#f0f0f0',
                                        border: '1px solid #d9d9d9',
                                        borderRadius: '4px',
                                        padding: '4px 8px',
                                        fontSize: '12px',
                                        color: '#666',
                                        cursor: 'pointer',
                                        textDecoration: 'none'
                                    }}
                                    onMouseOver={(e) => e.target.style.backgroundColor = '#e6f7ff'}
                                    onMouseOut={(e) => e.target.style.backgroundColor = '#f0f0f0'}
                                >
                                    Download Sample
                                </button>
                            </div>
                        </div>

                        {/* Blacklisted Domains List */}
                        {blacklistedDomains.length > 0 && (
                        <div style={{ marginTop: '24px' }}>
                            <h4 style={{ margin: '0 0 16px 0', color: '#0f386a', fontSize: '16px', fontWeight: '600' }}>
                                Currently Blacklisted Domains ({blacklistedDomains.length})
                            </h4>
                            <div style={{
                                border: '1px solid #e8e8e8',
                                borderRadius: '8px',
                                maxHeight: '400px',
                                overflowY: 'auto'
                            }}>
                                {blacklistedDomains.map((entry, index) => (
                                    <div key={entry.id} style={{
                                        padding: '16px',
                                        borderBottom: index < blacklistedDomains.length - 1 ? '1px solid #f0f0f0' : 'none',
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center'
                                    }}>
                                        <div style={{ flex: 1 }}>
                                            <div style={{
                                                fontWeight: '600',
                                                color: '#333',
                                                fontSize: '14px',
                                                marginBottom: '4px'
                                            }}>
                                                {entry.domain}
                                            </div>
                                            {entry.reason && (
                                                <div style={{
                                                    color: '#666',
                                                    fontSize: '12px',
                                                    marginBottom: '4px'
                                                }}>
                                                    Reason: {entry.reason}
                                                </div>
                                            )}
                                            <div style={{
                                                color: '#999',
                                                fontSize: '11px'
                                            }}>
                                                Blacklisted: {new Date(entry.created_at).toLocaleDateString()}
                                            </div>
                                        </div>
                                        <div>
                                            <button
                                                className="delete-button"
                                                onClick={() => handleRemoveFromBlacklist(entry.domain)}
                                                style={{ fontSize: '12px', padding: '6px 12px' }}
                                            >
                                                Whitelist
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        )}

                        <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Instructions:</h4>
                            <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                                <li><strong>Blacklist:</strong> Prevents new user registrations and deactivates all existing users for the domain</li>
                                <li><strong>Whitelist:</strong> Removes domain from blacklist and reactivates org_admin users for that domain</li>
                                <li>Enter domain without @ symbol (e.g., "example.com", not "@example.com")</li>
                                <li>Users with blacklisted domains will be set to "inactive" status</li>
                                <li>Only org_admin users are reactivated when whitelisting (org_user accounts remain inactive)</li>
                            </ul>
                        </div>
                    </div>
                    )}

                    {/* API Keys Section */}
                    <div className="page-section">
                        <h3 className="section-title">
                            <ApiOutlined style={{ marginRight: '8px' }} />
                            API Keys
                        </h3>
                        <p className="section-subtitle">
                            Create and manage API keys for programmatic access to the CyberBridge platform.
                        </p>
                        <ApiKeyManagement />
                    </div>

                    {/* Backup & Restore Section - Available to both org_admin and super_admin */}
                    <div className="page-section">
                        <h3 className="section-title">
                            <CloudUploadOutlined style={{ marginRight: '8px' }} />
                            Backup & Restore
                        </h3>
                        <p className="section-subtitle">
                            Configure automated backups and manage restore points for your organization's data including assessments, policies, frameworks, products, and risks.
                        </p>

                        {/* Backup Configuration */}
                        <div style={{ marginTop: '20px', padding: '20px', backgroundColor: '#f0f8ff', borderRadius: '8px', border: '1px solid #0f386a' }}>
                            <h4 style={{ margin: '0 0 16px 0', color: '#0f386a', fontSize: '16px', fontWeight: '600' }}>
                                Backup Configuration
                            </h4>

                            <div className="form-row" style={{ marginBottom: '20px' }}>
                                <div className="form-group">
                                    <div
                                        className="ai-toggle-container"
                                        onClick={() => !isSavingBackupConfig && setBackupEnabled(!backupEnabled)}
                                    >
                                        <div className={`ai-custom-toggle ${backupEnabled ? 'active' : ''} ${isSavingBackupConfig ? 'disabled' : ''}`}>
                                            <div className="ai-custom-toggle-handle" />
                                        </div>
                                        <span className="ai-toggle-label">
                                            {backupEnabled ? 'Automated Backups Enabled' : 'Automated Backups Disabled'}
                                            {isSavingBackupConfig && ' (saving...)'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <div className="form-row" style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
                                <div className="form-group" style={{ minWidth: '150px' }}>
                                    <label className="form-label">Backup Frequency</label>
                                    <Select
                                        value={backupFrequency}
                                        onChange={(value) => setBackupFrequency(value)}
                                        style={{ width: '100%' }}
                                        disabled={!backupEnabled}
                                        options={[
                                            { value: 'daily', label: 'Daily' },
                                            { value: 'weekly', label: 'Weekly' },
                                            { value: 'monthly', label: 'Monthly' }
                                        ]}
                                    />
                                </div>

                                <div className="form-group" style={{ minWidth: '150px' }}>
                                    <label className="form-label">Retention Period (Years)</label>
                                    <InputNumber
                                        min={1}
                                        max={100}
                                        value={backupRetentionYears}
                                        onChange={(value) => setBackupRetentionYears(value || 10)}
                                        style={{ width: '100%' }}
                                        disabled={!backupEnabled}
                                    />
                                </div>

                                <div className="form-group">
                                    <Button
                                        type="primary"
                                        onClick={handleSaveBackupConfig}
                                        loading={backupLoading}
                                    >
                                        Save Configuration
                                    </Button>
                                </div>
                            </div>

                            {/* Last Backup Status */}
                            {backupConfig && (
                                <div style={{ marginTop: '16px', padding: '12px', backgroundColor: backupConfig.last_backup_status === 'success' ? '#f6ffed' : backupConfig.last_backup_status === 'failed' ? '#fff2f0' : '#f0f0f0', borderRadius: '6px', border: `1px solid ${backupConfig.last_backup_status === 'success' ? '#b7eb8f' : backupConfig.last_backup_status === 'failed' ? '#ffccc7' : '#d9d9d9'}` }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div>
                                            <strong style={{ color: '#333' }}>Last Backup: </strong>
                                            <span style={{ color: '#666' }}>
                                                {backupConfig.last_backup_at
                                                    ? new Date(backupConfig.last_backup_at).toLocaleDateString() + ' ' + new Date(backupConfig.last_backup_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                                                    : 'Never'}
                                            </span>
                                            {backupConfig.last_backup_status && (
                                                <Tag
                                                    color={backupConfig.last_backup_status === 'success' ? 'success' : backupConfig.last_backup_status === 'failed' ? 'error' : 'processing'}
                                                    style={{ marginLeft: '12px' }}
                                                >
                                                    {backupConfig.last_backup_status}
                                                </Tag>
                                            )}
                                        </div>
                                        <Button
                                            type="primary"
                                            icon={<CloudUploadOutlined />}
                                            onClick={handleCreateBackup}
                                            loading={isCreatingBackup}
                                        >
                                            Create Backup Now
                                        </Button>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Backup List */}
                        <div style={{ marginTop: '24px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                                <h4 style={{ margin: 0, color: '#0f386a', fontSize: '16px', fontWeight: '600' }}>
                                    Available Backups ({backups.length})
                                </h4>
                                <Button
                                    icon={<ReloadOutlined />}
                                    onClick={() => current_user && fetchBackups(current_user.organisation_id)}
                                    loading={backupLoading}
                                >
                                    Refresh
                                </Button>
                            </div>

                            <Table
                                dataSource={backups}
                                columns={backupTableColumns}
                                rowKey="id"
                                loading={backupLoading}
                                pagination={{ pageSize: 10 }}
                                size="small"
                                locale={{ emptyText: 'No backups available. Create your first backup using the button above.' }}
                            />
                        </div>

                        {/* Instructions */}
                        <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Instructions:</h4>
                            <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                                <li><strong>Automated Backups:</strong> When enabled, backups are created automatically based on the selected frequency (daily at 2 AM)</li>
                                <li><strong>Retention Period:</strong> Backups are automatically deleted after the specified retention period</li>
                                <li><strong>Manual Backup:</strong> Click "Create Backup Now" to create an immediate backup</li>
                                <li><strong>Download:</strong> Download a backup file for offline storage or transfer</li>
                                <li><strong>Restore:</strong> Restore organization data from a previous backup (requires confirmation)</li>
                                <li><strong>Security:</strong> All backup data is encrypted using AES encryption</li>
                                <li><strong>What's Backed Up:</strong> Frameworks, assessments, answers, policies, products, risks, objectives, and configuration settings</li>
                            </ul>
                        </div>
                    </div>

                    {/* Restore Confirmation Modal */}
                    <Modal
                        title="Confirm Restore"
                        open={restoreModalVisible}
                        onOk={handleRestoreBackup}
                        onCancel={() => {
                            setRestoreModalVisible(false);
                            setSelectedBackupForRestore(null);
                        }}
                        okText="Restore"
                        okButtonProps={{ danger: true, loading: isRestoring }}
                        cancelText="Cancel"
                    >
                        <div style={{ padding: '16px 0' }}>
                            <p style={{ color: '#ff4d4f', fontWeight: '600', marginBottom: '16px' }}>
                                Warning: This operation will replace existing organization data!
                            </p>
                            <p>
                                Restoring from a backup will:
                            </p>
                            <ul style={{ marginLeft: '20px', marginTop: '8px' }}>
                                <li>Replace all frameworks, chapters, and objectives</li>
                                <li>Replace all policies and policy associations</li>
                                <li>Replace all products and risks</li>
                                <li>Replace all question correlations</li>
                                <li>Replace AI configuration settings</li>
                            </ul>
                            <p style={{ marginTop: '16px', color: '#666' }}>
                                <strong>Note:</strong> User accounts and assessments/answers are preserved during restore.
                            </p>
                            <p style={{ marginTop: '16px', fontWeight: '600' }}>
                                Are you sure you want to proceed?
                            </p>
                        </div>
                    </Modal>

                </div>
            </div>
        </div>
    );
};

export default SettingsPage;