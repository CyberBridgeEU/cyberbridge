import {notification, Select, SelectProps, Upload, message, Checkbox, Input} from "antd";
import Sidebar from "../components/Sidebar.tsx";
import {useEffect, useState} from "react";
import useUserStore from "../store/useUserStore.ts";
import { useLocation } from 'wouter';
import InfoTitle from "../components/InfoTitle.tsx";
import { ManageOrganisationsInfo } from "../constants/infoContent.tsx";
import { UploadOutlined, DeleteOutlined, TeamOutlined, RobotOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import useAuthStore from "../store/useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const { Option } = Select;

const UserManagementPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const [, setLocation] = useLocation();
    const {createOrUpdateOrganisation, fetchOrganisations, organisations, error, users, roles, fetchRoles, fetchOrganisationUsers, clearUsers, createUser, updateUser, deleteUser, deleteOrganisation, current_user} = useUserStore();
    const { getAuthHeader } = useAuthStore();

    const [api, contextHolder] = notification.useNotification();
    const [orgName, setOrgName] = useState<string>('');
    const [orgDomain, setOrgDomain] = useState<string>('');


    // State Declarations
    const [orgSelectedId, setOrgSelectedId] = useState<string>('');
    const [userSelectedId, setUserSelectedId] = useState<string>('');
    const [userEmail, setUserEmail] = useState<string>('');
    const [userPassword, setUserPassword] = useState<string>('');
    const [roleSelectedId, setRoleSelectedId] = useState<string>('');
    const [, setUserRole] = useState<string>('');
    const [elementIsDisabled, setElementIsDisabled] = useState<boolean>(true);
    const [deleteOrgDisabled, setDeleteOrgDisabled] = useState<boolean>(true);
    const [deleteUserDisabled, setDeleteUserDisabled] = useState<boolean>(true);

    // State for logo management
    const [currentLogo, setCurrentLogo] = useState<string | null>(null);
    const [isUploadingLogo, setIsUploadingLogo] = useState<boolean>(false);
    const [isDeletingLogo, setIsDeletingLogo] = useState<boolean>(false);

    // State to track if selected organization has users (for domain field disabling)
    const [selectedOrgHasUsers, setSelectedOrgHasUsers] = useState<boolean>(false);

    // History cleanup configuration states
    const [historyCleanupEnabled, setHistoryCleanupEnabled] = useState<boolean>(false);
    const [historyRetentionDays, setHistoryRetentionDays] = useState<number>(30);
    const [historyCleanupIntervalHours, setHistoryCleanupIntervalHours] = useState<number>(24);
    const [isLoadingHistoryConfig, setIsLoadingHistoryConfig] = useState<boolean>(false);
    const [isSavingHistoryConfig, setIsSavingHistoryConfig] = useState<boolean>(false);
    const [isCleaningHistory, setIsCleaningHistory] = useState<boolean>(false);
    const [selectedHistoryConfigOrgId, setSelectedHistoryConfigOrgId] = useState<string>('');
    const [allOrganisationsForHistory, setAllOrganisationsForHistory] = useState<any[]>([]);

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

    useEffect(() => {
        // Check if user is super_admin or org_admin, if not redirect to home
        if (current_user && !['super_admin', 'org_admin'].includes(current_user.role_name)) {
            setLocation('/home');
            return;
        }
        if (current_user && current_user.role_name === 'super_admin') {
            fetchOrganisations();
            fetchRoles();
        }
        if (current_user && current_user.role_name === 'org_admin') {
            // For org_admin, automatically set their organization and fetch organization data
            fetchOrganisations(); // Fetch organization data so logo logic works consistently
            setOrgSelectedId(current_user.organisation_id);
            setOrgName(current_user.organisation_name || '');
            setOrgDomain(current_user.organisation_domain || '');
            fetchOrganisationUsers(current_user.organisation_id);
            fetchRoles();
        }
    }, [current_user]);

    // Initialize current logo with user's organization logo
    useEffect(() => {
        if (current_user && current_user.organisation_logo) {
            setCurrentLogo(current_user.organisation_logo);
        }
    }, [current_user]);

    // Initialize selected history config org and fetch organizations for super_admin
    useEffect(() => {
        if (current_user) {
            if (current_user.role_name === 'super_admin') {
                // For super_admin, fetch all organizations
                fetchAllOrganisationsForHistory();
                // Set default to current user's org
                setSelectedHistoryConfigOrgId(current_user.organisation_id);
            } else if (current_user.role_name === 'org_admin') {
                // For org_admin, set to their org only
                setSelectedHistoryConfigOrgId(current_user.organisation_id);
            }
        }
    }, [current_user]);

    // Fetch history cleanup configuration when selected org changes
    useEffect(() => {
        if (selectedHistoryConfigOrgId) {
            fetchHistoryCleanupConfig();
        }
    }, [selectedHistoryConfigOrgId]);

    // Fetch org AI configuration when organization is selected
    useEffect(() => {
        if (orgSelectedId) {
            fetchOrgAiConfig(orgSelectedId);
        } else {
            // Reset AI config state when no org is selected
            resetOrgAiConfigState();
        }
    }, [orgSelectedId]);

    useEffect(() => {
        if(!orgSelectedId) {
            setElementIsDisabled(true);
        } else {
            setElementIsDisabled(false);
        }
    }, [orgSelectedId]);

    useEffect(() => {
        // Check if delete org button should be enabled
        const canDeleteOrg = () => {
            // Rule 1: User must be from "clone-systems.com" domain organization
            if (!current_user || current_user.organisation_domain !== 'clone-systems.com') {
                return false;
            }
            
            // Rule 2: Must have an organization selected
            if (!orgSelectedId) {
                return false;
            }
            
            // Rule 3: Cannot delete own organization
            if (orgSelectedId === current_user.organisation_id) {
                return false;
            }
            
            // Rule 4: Cannot delete if it's the last organization
            if (organisations.length <= 1) {
                return false;
            }
            
            return true;
        };

        setDeleteOrgDisabled(!canDeleteOrg());
    }, [orgSelectedId, current_user, organisations]);

    // Update selectedOrgHasUsers when users array changes, but only if an organization is selected
    useEffect(() => {
        setSelectedOrgHasUsers(orgSelectedId ? users.length > 0 : false);
    }, [users, orgSelectedId]);

    useEffect(() => {
        // Check if delete user button should be enabled
        const canDeleteUser = () => {
            // Rule 1: Only super_admin can delete users
            if (current_user?.role_name !== 'super_admin') {
                return false;
            }

            // Rule 2: Must have a user selected
            if (!userSelectedId) {
                return false;
            }

            // Rule 3: Cannot delete yourself
            if (userSelectedId === current_user?.id) {
                return false;
            }

            return true;
        };

        setDeleteUserDisabled(!canDeleteUser());
    }, [userSelectedId, current_user]);

    useEffect(() => {
        // Set current organization logo when organization is selected
        if (orgSelectedId) {
            const selectedOrg = organisations.find(org => org.id === orgSelectedId);
            if (selectedOrg && selectedOrg.logo) {
                setCurrentLogo(selectedOrg.logo);
            } else {
                setCurrentLogo(null);
            }
        } else {
            setCurrentLogo(null);
        }
    }, [orgSelectedId, organisations]);

    // Don't render the page if user is not super_admin or org_admin
    if (!current_user || !['super_admin', 'org_admin'].includes(current_user.role_name)) {
        return <div>Access Denied. Only super admins and organization admins can access this page.</div>;
    }

    //====Constants
    const optionsOrg = organisations.map(org => ({
        value: org.id,
        label: org.name,
    }));

    const optionsUser = users.map(user => ({
        value: user.id,
        label: user.email,
    }));

    // Filter roles based on current user's permissions
    const optionsRole = roles
        .filter(role => {
            // Super admin can assign any role
            if (current_user?.role_name === 'super_admin') {
                return true;
            }
            // Org admin can only assign org_admin and org_user roles (not super_admin)
            if (current_user?.role_name === 'org_admin') {
                return ['org_admin', 'org_user'].includes(role.role_name);
            }
            return false;
        })
        .map(role => ({
            value: role.id,
            label: role.role_name,
        }));

    //Component Functions
    const filterOption: SelectProps['filterOption'] = (input, option) =>
        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase());

    const handleOrgChange = async (value: string) => {
        setOrgSelectedId(value);
        console.log(organisations);
        const selectedOrg = organisations.find(org => org.id === value);
        setOrgName(selectedOrg?.name ?? '');
        setOrgDomain(selectedOrg?.domain ?? '');
        setCurrentLogo(selectedOrg?.logo ?? null); // Set the logo for the selected organization
        clearUser(); // Clear all user fields when organization changes
        const success = await fetchOrganisationUsers(value);
        console.log('users: ', users);
        if(!success){
            api.error({message: 'fetch organisation users failed!', description: error, duration: 4,});
        }
    };

    const handleUserChange = (value: string) => {
        setUserSelectedId(value);
        setUserEmail(users.find(user => user.id === value)?.email ?? '');
        setRoleSelectedId(users.find(user => user.id === value)?.role_id ?? '');
        setUserRole(users.find(user => user.id === value)?.role_name ?? '');
    }

    const handleRoleChange = (value: string) => {
        setRoleSelectedId(value);
        setUserRole(roles.find(role => role.id === value)?.role_name ?? '');
    }


    const handleUpdateOrg = async (orgId: string) => {
        if(!orgId){
            api.error({message: 'No Organisation Selected', description: 'Choose an Organisation to update!', duration: 4,});
            return;
        }
        handleAddNewOrg(orgId);
    }

    const handleAddNewOrg = async (orgId: string | null) => {
        if(!orgName || orgName.trim() === '' || !orgDomain || orgDomain.trim() === '') {
            api.error({message: 'Fill Organisation Fields.', description: 'Org Name and Domain cannot be empty!', duration: 4,});
            return;
        }

        // Check for duplicate domain
        const duplicateDomain = organisations.find(org =>
            org.domain === orgDomain && (!orgId || org.id !== orgId)
        );
        if (duplicateDomain) {
            api.error({
                message: 'Duplicate Domain',
                description: `An organization with domain '${orgDomain}' already exists (${duplicateDomain.name}). Domains must be unique.`,
                duration: 6
            });
            return;
        }

        //api call
        const success = await createOrUpdateOrganisation(orgName, orgDomain, '', orgId);

        if (success) {
            api.success({message: 'Organisation Creation Success', description: 'Organisation created/updated.', duration: 4,});
        } else {
            api.error({message: 'Organisation Creation Failed', description: error, duration: 4,});
        }

        // Clear the input fields
        setOrgName('');
        setOrgDomain('');
    }

    const handleAddUser = async () => {
        if(!userEmail || userEmail.trim() === '' || !userPassword || userPassword.trim() === '' || !roleSelectedId || roleSelectedId.trim() === '' || !orgSelectedId || orgSelectedId.trim() === '') {
            api.error({message: 'Fill User Fields.', description: 'Email, Password, Role cannot be empty!', duration: 4,});
            return;
        }

        console.log('userSelectedId: ', userSelectedId);

        if(userSelectedId) {
            api.error({message: 'There is a user selected.', description: 'Only update action allowed on existing user!', duration: 4,});
            return;
        }

        const success = await createUser(userEmail, userPassword, roleSelectedId, orgSelectedId); //create user
        if (success) {
            api.success({message: 'User Creation Success', description: 'User created.', duration: 4,});
        } else {
            api.error({message: 'User Creation Failed', description: error, duration: 4,});
        }
        clearUser()

    }

    const handleUpdateUser = async () => {
        if(!userSelectedId || userSelectedId.trim() === ''){
            api.error({message: 'No User selected.', description: 'You must select an existing user to update!', duration: 4,});
            return;
        }
        console.log('userSelectedId: ', userSelectedId);
        const success = await updateUser(userEmail, userPassword, roleSelectedId, userSelectedId);
        if (success) {
            api.success({message: 'Success', description: 'User updated.', duration: 4,});
        } else {
            api.error({message: 'Fail to update user', description: error, duration: 4,});
        }
        clearUser()

    }

    const clearOrg = () => {
        setOrgSelectedId('');
        setOrgName('');
        setOrgDomain('');
        setCurrentLogo(null);
        clearUsers(); // Clear users from store to ensure domain field is enabled
        clearUser();
    }

    const clearUser = () => {
        setUserSelectedId('');
        setUserEmail('');
        setRoleSelectedId('');
        setUserRole('');
        setUserPassword('');
    }

    const handleDeleteUser = async () => {
        // Validation checks
        if (!userSelectedId || userSelectedId.trim() === '') {
            api.error({message: 'No User selected.', description: 'You must select a user to delete!', duration: 4,});
            return;
        }

        if (userSelectedId === current_user?.id) {
            api.error({message: 'Cannot Delete Yourself', description: 'You cannot delete your own user account!', duration: 4,});
            return;
        }

        // Show confirmation dialog
        const userToDelete = users.find(user => user.id === userSelectedId);
        if (!window.confirm(`Are you sure you want to delete user "${userToDelete?.email}"? This will also delete all their assessments and answers. This action cannot be undone.`)) {
            return;
        }

        const success = await deleteUser(userSelectedId);
        if (success) {
            api.success({message: 'User Deleted', description: 'User and all associated data deleted successfully.', duration: 4,});
            clearUser(); // Clear the form after successful deletion
        } else {
            api.error({message: 'Delete User Failed', description: error, duration: 4,});
        }
    }

    const handleDeleteOrg = async () => {
        // Validation checks
        if (!orgSelectedId || orgSelectedId.trim() === '') {
            api.error({message: 'No Organisation selected.', description: 'You must select an organisation to delete!', duration: 4,});
            return;
        }

        if (!current_user || current_user.organisation_domain !== 'clone-systems.com') {
            api.error({message: 'Access Denied', description: 'Only users from Clone Systems organisation can delete organisations!', duration: 4,});
            return;
        }

        if (orgSelectedId === current_user.organisation_id) {
            api.error({message: 'Cannot Delete Own Organisation', description: 'You cannot delete your own organisation!', duration: 4,});
            return;
        }

        if (organisations.length <= 1) {
            api.error({message: 'Cannot Delete Last Organisation', description: 'Cannot delete the last organisation in the system!', duration: 4,});
            return;
        }

        // Show confirmation dialog
        const orgToDelete = organisations.find(org => org.id === orgSelectedId);
        if (!window.confirm(`Are you sure you want to delete organisation "${orgToDelete?.name}"? This will permanently delete:\n\n• All users in this organisation\n• All assessments and answers by these users\n• All frameworks, chapters, and objectives\n• All associated data\n\nThis action cannot be undone.`)) {
            return;
        }

        const success = await deleteOrganisation(orgSelectedId);
        if (success) {
            api.success({message: 'Organisation Deleted', description: 'Organisation and all associated data deleted successfully.', duration: 4,});
            clearOrg(); // Clear the form after successful deletion
        } else {
            api.error({message: 'Delete Organisation Failed', description: error, duration: 4,});
        }
    }

    // Logo management handlers
    const handleLogoUpload = async (file: File) => {
        if (!current_user || !current_user.organisation_id) {
            api.error({
                message: 'Organization Not Found',
                description: 'Unable to determine your organization. Please try logging in again.',
                duration: 4,
            });
            return false;
        }

        const authHeader = getAuthHeader();
        if (!authHeader) {
            api.error({
                message: 'Authentication Error',
                description: 'You must be logged in to upload a logo.',
                duration: 4,
            });
            return false;
        }

        setIsUploadingLogo(true);
        try {
            // Convert file to base64
            const base64Logo = await new Promise<string>((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result as string);
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });

            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/create_organisation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...authHeader,
                },
                body: JSON.stringify({
                    id: current_user.organisation_id,
                    name: current_user.organisation_name,
                    domain: current_user.organisation_domain,
                    logo: base64Logo,
                }),
            });

            if (response.ok) {
                setCurrentLogo(base64Logo);
                api.success({
                    message: 'Logo Uploaded Successfully',
                    description: 'Organization logo has been updated.',
                    duration: 4,
                });
                // Refresh organizations to get updated logo
                fetchOrganisations();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to upload logo');
            }
        } catch (error) {
            api.error({
                message: 'Logo Upload Failed',
                description: error instanceof Error ? error.message : 'Failed to upload logo. Please try again.',
                duration: 4,
            });
        } finally {
            setIsUploadingLogo(false);
        }
        return false; // Prevent default upload behavior
    };

    const handleLogoDelete = async () => {
        if (!current_user || !current_user.organisation_id) {
            api.error({
                message: 'Organization Not Found',
                description: 'Unable to determine your organization. Please try logging in again.',
                duration: 4,
            });
            return;
        }

        const authHeader = getAuthHeader();
        if (!authHeader) {
            api.error({
                message: 'Authentication Error',
                description: 'You must be logged in to delete a logo.',
                duration: 4,
            });
            return;
        }

        setIsDeletingLogo(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/create_organisation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...authHeader,
                },
                body: JSON.stringify({
                    id: orgSelectedId,
                    name: orgName,
                    domain: orgDomain,
                    logo: null,
                }),
            });

            if (response.ok) {
                api.success({
                    message: 'Logo Deleted Successfully',
                    description: 'Organization logo has been removed.',
                    duration: 4,
                });
                // Refresh organizations to get updated logo, useEffect will handle logo state
                setTimeout(async () => {
                    await fetchOrganisations();
                }, 100);
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to delete logo');
            }
        } catch (error) {
            api.error({
                message: 'Logo Deletion Failed',
                description: error instanceof Error ? error.message : 'Failed to delete logo. Please try again.',
                duration: 4,
            });
        } finally {
            setIsDeletingLogo(false);
        }
    };

    // History cleanup configuration functions
    const fetchAllOrganisationsForHistory = async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/get_all_organisations`, {
                headers: {
                    ...getAuthHeader()
                }
            });

            if (response.ok) {
                const data = await response.json();
                setAllOrganisationsForHistory(data);
            }
        } catch (error) {
            console.error('Error fetching organizations for history config:', error);
        }
    };

    const fetchHistoryCleanupConfig = async () => {
        if (!selectedHistoryConfigOrgId) return;

        setIsLoadingHistoryConfig(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/admin/organizations/${selectedHistoryConfigOrgId}/history-cleanup-config`,
                {
                    headers: {
                        ...getAuthHeader()
                    }
                }
            );
            if (response.ok) {
                const config = await response.json();
                setHistoryCleanupEnabled(config.history_cleanup_enabled);
                setHistoryRetentionDays(config.history_retention_days);
                setHistoryCleanupIntervalHours(config.history_cleanup_interval_hours);
            }
        } catch (error) {
            console.error('Error fetching history cleanup configuration:', error);
        } finally {
            setIsLoadingHistoryConfig(false);
        }
    };

    const handleSaveHistoryConfig = async () => {
        if (!selectedHistoryConfigOrgId) return;

        setIsSavingHistoryConfig(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/admin/organizations/${selectedHistoryConfigOrgId}/history-cleanup-config`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        ...getAuthHeader()
                    },
                    body: JSON.stringify({
                        history_cleanup_enabled: historyCleanupEnabled,
                        history_retention_days: historyRetentionDays,
                        history_cleanup_interval_hours: historyCleanupIntervalHours
                    })
                }
            );

            if (response.ok) {
                api.success({
                    message: 'History Cleanup Configuration Updated',
                    description: 'Your history cleanup settings have been saved successfully.',
                    duration: 4,
                });
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update history cleanup configuration');
            }
        } catch (error) {
            api.error({
                message: 'Update Failed',
                description: error instanceof Error ? error.message : 'Failed to update history cleanup configuration. Please try again.',
                duration: 4,
            });
        } finally {
            setIsSavingHistoryConfig(false);
        }
    };

    const handleCleanupHistoryNow = async () => {
        if (!selectedHistoryConfigOrgId) return;

        setIsCleaningHistory(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/admin/organizations/${selectedHistoryConfigOrgId}/cleanup-history-now`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...getAuthHeader()
                    }
                }
            );

            if (response.ok) {
                const result = await response.json();
                api.success({
                    message: 'History Cleanup Completed',
                    description: result.message,
                    duration: 6,
                });
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to cleanup history');
            }
        } catch (error) {
            api.error({
                message: 'Cleanup Failed',
                description: error instanceof Error ? error.message : 'Failed to cleanup history. Please try again.',
                duration: 4,
            });
        } finally {
            setIsCleaningHistory(false);
        }
    };

    // Organization AI Configuration functions
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
        // Reset AI Remediator states
        setOrgAiRemediatorEnabled(false);
        setOrgRemediatorPromptZap('');
        setOrgRemediatorPromptNmap('');
        setShowZapPromptEditor(false);
        setShowNmapPromptEditor(false);
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
                setOrgHasAiConfig(true);
            } else if (response.status === 404) {
                // No config exists yet for this org
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
        if (!orgSelectedId) {
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
                `${cyberbridge_back_end_rest_api}/settings/org-llm/${orgSelectedId}`,
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
                        remediator_prompt_nmap: orgRemediatorPromptNmap || null
                    })
                }
            );

            if (response.ok) {
                setOrgHasAiConfig(true);
                api.success({
                    message: 'AI Configuration Saved',
                    description: `AI provider settings for this organization have been saved successfully.`,
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
        if (!orgSelectedId) return;

        if (!window.confirm('Are you sure you want to delete this organization\'s AI configuration? The organization will use global default settings instead.')) {
            return;
        }

        setIsSavingOrgAiConfig(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/settings/org-llm/${orgSelectedId}`,
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

    const uploadProps: UploadProps = {
        name: 'logo',
        beforeUpload: (file) => {
            const isImage = file.type.startsWith('image/');
            const isLt5M = file.size / 1024 / 1024 < 5;

            if (!isImage) {
                message.error('You can only upload image files!');
                return false;
            }
            if (!isLt5M) {
                message.error('Image must be smaller than 5MB!');
                return false;
            }

            handleLogoUpload(file);
            return false;
        },
        showUploadList: false,
        accept: 'image/*',
    };

    return (
        <div>
            {contextHolder}
            <div className={'page-parent'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys} onOpenChange={menuHighlighting.onOpenChange} />
                <div className="page-content">
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <InfoTitle
                                title="Organizations Management"
                                infoContent={ManageOrganisationsInfo}
                                className="page-title"
                                icon={<TeamOutlined style={{ color: '#1a365d' }} />}
                            />
                        </div>
                    </div>

                    {/* Manage Organizations Section */}
                    <div className="page-section">
                        <h3 className="section-title">Manage Organizations</h3>
                        {/* Organization selection - Only visible to super_admin */}
                        {current_user?.role_name === 'super_admin' && (
                        <div className="form-row">
                            <div className="form-group" style={{ minWidth: '300px' }}>
                                <label className="form-label">Select Organization</label>
                                <Select
                                    showSearch
                                    placeholder="Choose an organization"
                                    onChange={handleOrgChange}
                                    options={optionsOrg}
                                    filterOption={filterOption}
                                    value={orgSelectedId || undefined}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="control-group">
                                <button className="add-button" onClick={clearOrg}>Clear Organization</button>
                                <button className="delete-button" onClick={handleDeleteOrg} disabled={deleteOrgDisabled}>Delete Organization</button>
                            </div>
                        </div>
                        )}

                        {/* Organization info display for org_admin */}
                        {current_user?.role_name === 'org_admin' && (
                        <div className="form-row">
                            <div className="form-group" style={{ minWidth: '300px' }}>
                                <div style={{ padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '6px', border: '1px solid #e9ecef' }}>
                                    <p style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: '#495057' }}>
                                        Managing Organization: {current_user.organisation_name}
                                    </p>
                                    <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#6c757d' }}>
                                        Domain: {current_user.organisation_domain}
                                    </p>
                                </div>
                            </div>
                        </div>
                        )}
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label required">Organization Name</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="Enter organization name"
                                    value={orgName}
                                    onChange={(e) => setOrgName(e.target.value)}
                                />
                                {/* Empty space to match the domain field height when warning message appears */}
                                {selectedOrgHasUsers && (
                                    <div style={{ height: '20px' }}></div>
                                )}
                            </div>
                            <div className="form-group">
                                <label className="form-label required">Organization Domain</label>
                                <input
                                    type="text"
                                    className={`form-input ${selectedOrgHasUsers ? 'disabled' : ''}`}
                                    placeholder={selectedOrgHasUsers ? "Domain cannot be changed (organization has users)" : "Enter organization domain"}
                                    value={orgDomain}
                                    onChange={(e) => setOrgDomain(e.target.value)}
                                    disabled={selectedOrgHasUsers}
                                    title={selectedOrgHasUsers ? "Organization domain cannot be changed because it has associated users. The domain is derived from user email addresses." : ""}
                                />
                                {selectedOrgHasUsers && (
                                    <div style={{ marginTop: '8px', fontSize: '12px', color: '#ff6b6b', fontStyle: 'italic', height: '12px' }}>
                                        ⚠️ Domain is immutable when organization has users
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="control-group">
                                {/* Super admin can add new organizations and update selected ones */}
                                {current_user?.role_name === 'super_admin' && (
                                    <>
                                        <button className="add-button" onClick={()=>handleAddNewOrg(null)}>Add New Organization</button>
                                        <button className="add-button" onClick={()=>handleUpdateOrg(orgSelectedId)}>Update Organization</button>
                                    </>
                                )}
                                {/* Org admin can only update their own organization */}
                                {current_user?.role_name === 'org_admin' && (
                                    <button className="add-button" onClick={()=>handleUpdateOrg(orgSelectedId)}>Update Organization</button>
                                )}
                            </div>
                        </div>

                    </div>

                    {/* Organization Logo Section */}
                    <div className="page-section">
                        <h3 className="section-title">Organization Logo</h3>
                        <div style={{ padding: '20px', border: '1px solid #f0f0f0', borderRadius: '8px', backgroundColor: '#fafafa' }}>
                            <p style={{ marginBottom: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.5' }}>
                                Upload and manage your organization's logo that will appear on login screens, headers, and throughout the application.
                            </p>

                            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '24px', marginBottom: '16px' }}>
                                {/* Current Logo Display */}
                                <div style={{ minWidth: '200px' }}>
                                    <label className="form-label" style={{ marginBottom: '8px', display: 'block' }}>Current Logo</label>
                                    <div style={{
                                        width: '200px',
                                        height: '120px',
                                        border: '2px dashed #d9d9d9',
                                        borderRadius: '8px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        backgroundColor: '#fafafa',
                                        overflow: 'hidden'
                                    }}>
                                        {currentLogo ? (
                                            <img
                                                src={currentLogo}
                                                alt="Organization Logo"
                                                style={{
                                                    maxWidth: '100%',
                                                    maxHeight: '100%',
                                                    objectFit: 'contain'
                                                }}
                                            />
                                        ) : (
                                            <div style={{
                                                textAlign: 'center',
                                                color: '#8c8c8c',
                                                fontSize: '14px'
                                            }}>
                                                <div style={{ marginBottom: '8px' }}>📷</div>
                                                No logo uploaded
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Upload Controls */}
                                <div style={{ flex: 1 }}>
                                    <label className="form-label" style={{ marginBottom: '16px', display: 'block' }}>Logo Management</label>

                                    <div style={{ marginBottom: '16px' }}>
                                        <Upload {...uploadProps}>
                                            <button
                                                className="add-button"
                                                style={{
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '8px',
                                                    opacity: isUploadingLogo || isDeletingLogo ? 0.6 : 1,
                                                    cursor: isUploadingLogo || isDeletingLogo ? 'not-allowed' : 'pointer'
                                                }}
                                                disabled={isUploadingLogo || isDeletingLogo}
                                            >
                                                <UploadOutlined />
                                                {isUploadingLogo ? 'Uploading...' : 'Upload New Logo'}
                                            </button>
                                        </Upload>
                                    </div>

                                    {currentLogo && (
                                        <div>
                                            <button
                                                className="delete-button"
                                                onClick={handleLogoDelete}
                                                disabled={isUploadingLogo || isDeletingLogo}
                                                style={{
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '8px',
                                                    opacity: isUploadingLogo || isDeletingLogo ? 0.6 : 1,
                                                    cursor: isUploadingLogo || isDeletingLogo ? 'not-allowed' : 'pointer'
                                                }}
                                            >
                                                <DeleteOutlined />
                                                {isDeletingLogo ? 'Removing...' : 'Remove Logo'}
                                            </button>
                                        </div>
                                    )}

                                    <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f0f8ff', borderRadius: '6px', border: '1px solid #d6e4ff' }}>
                                        <h4 style={{ margin: '0 0 8px 0', color: '#1890ff', fontSize: '14px', fontWeight: '600' }}>Upload Guidelines:</h4>
                                        <ul style={{ margin: 0, paddingLeft: '20px', color: '#595959', fontSize: '13px', lineHeight: '1.6' }}>
                                            <li>Supported formats: PNG, JPG, JPEG, GIF, SVG</li>
                                            <li>Maximum file size: 5MB</li>
                                            <li>Recommended dimensions: 200x120px or similar aspect ratio</li>
                                            <li>Logo will appear on login pages, headers, and throughout the application</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Organization AI Provider Section */}
                    {orgSelectedId && (
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
                            Configure the AI provider for this organization. Each organization can have its own AI settings, or use the global default.
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
                                                {orgAiEnabled ? 'AI is Enabled for this Organization' : 'AI is Disabled for this Organization'}
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
                                                        { value: 'openai', label: 'OpenAI (ChatGPT)' },
                                                        { value: 'anthropic', label: 'Anthropic (Claude)' },
                                                        { value: 'xai', label: 'X AI (Grok)' },
                                                        { value: 'google', label: 'Google (Gemini)' },
                                                        { value: 'qlon', label: 'QLON Ai' }
                                                    ]}
                                                />
                                            </div>
                                        </div>

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
                                            ? `✓ This organization has custom AI settings configured (Provider: ${
                                                orgAiProvider === 'openai' ? 'OpenAI (ChatGPT)' :
                                                orgAiProvider === 'anthropic' ? 'Anthropic (Claude)' :
                                                orgAiProvider === 'xai' ? 'X AI (Grok)' :
                                                orgAiProvider === 'google' ? 'Google (Gemini)' :
                                                'QLON Ai'
                                            })`
                                            : '○ This organization is using global default AI settings. Save configuration to customize.'}
                                    </p>
                                </div>
                            </>
                        )}
                    </div>
                    </>
                    )}

                    {/* Manage Users Section */}
                    <div className="page-section">
                        <h3 className="section-title">Manage Users</h3>
                        <div className="form-row">
                            <div className="form-group" style={{ minWidth: '300px' }}>
                                <label className="form-label">Select User</label>
                                <Select
                                    showSearch
                                    placeholder="Choose a user by email"
                                    onChange={handleUserChange}
                                    options={optionsUser}
                                    filterOption={filterOption}
                                    value={userSelectedId || undefined}
                                    disabled={elementIsDisabled}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="control-group">
                                <button className="add-button" onClick={clearUser}>Clear User</button>
                                {current_user?.role_name === 'super_admin' && (
                                    <button className="delete-button" onClick={handleDeleteUser} disabled={deleteUserDisabled}>Delete User</button>
                                )}
                            </div>
                        </div>
                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label required">User Email</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="Enter user email"
                                    value={userEmail}
                                    onChange={(e) => setUserEmail(e.target.value)}
                                    disabled={elementIsDisabled}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label required">User Password</label>
                                <input
                                    type="password"
                                    className="form-input"
                                    placeholder="Enter user password"
                                    value={userPassword}
                                    onChange={(e) => setUserPassword(e.target.value)}
                                    disabled={elementIsDisabled}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label required">User Role</label>
                                <Select
                                    showSearch
                                    placeholder="Choose user role"
                                    onChange={handleRoleChange}
                                    options={optionsRole}
                                    filterOption={filterOption}
                                    value={roleSelectedId || undefined}
                                    disabled={elementIsDisabled}
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="control-group">
                                <button className="add-button" onClick={handleAddUser}>Add New User</button>
                                <button className="add-button" onClick={handleUpdateUser}>Update User</button>
                            </div>
                        </div>
                    </div>

                    {/* History Configuration Section */}
                    <div className="page-section" style={{marginTop: '32px'}}>
                        <h3 className="section-title">History Configuration</h3>
                        <p className="section-subtitle">
                            Configure automatic cleanup of old audit history records for your organization. Set retention periods and enable scheduled cleanup tasks.
                        </p>

                        {/* Organization Selector (Super Admin Only) */}
                        {current_user?.role_name === 'super_admin' && allOrganisationsForHistory.length > 0 && (
                            <div className="form-row" style={{ marginBottom: '20px', padding: '16px', backgroundColor: '#f0f8ff', borderRadius: '6px', border: '1px solid #0f386a' }}>
                                <div className="form-group" style={{ width: '300px' }}>
                                    <label className="form-label" style={{ color: '#0f386a', fontWeight: '600' }}>
                                        Select Organization
                                    </label>
                                    <Select
                                        placeholder="Select organization"
                                        value={selectedHistoryConfigOrgId || undefined}
                                        onChange={(value) => setSelectedHistoryConfigOrgId(value)}
                                        style={{ width: '100%' }}
                                    >
                                        {allOrganisationsForHistory.map((org) => (
                                            <Option key={org.id} value={org.id}>
                                                {org.name}
                                            </Option>
                                        ))}
                                    </Select>
                                </div>
                            </div>
                        )}

                        {isLoadingHistoryConfig ? (
                            <div style={{ padding: '20px', textAlign: 'center', color: '#8c8c8c' }}>
                                Loading configuration...
                            </div>
                        ) : (
                            <>
                                <div className="form-row">
                                    <div className="form-group">
                                        <Checkbox
                                            checked={historyCleanupEnabled}
                                            onChange={(e) => setHistoryCleanupEnabled(e.target.checked)}
                                            style={{ fontSize: '14px' }}
                                        >
                                            Enable Automatic History Cleanup
                                        </Checkbox>
                                    </div>
                                </div>

                                <div className="form-row">
                                    <div className="form-group" style={{ minWidth: '200px' }}>
                                        <label className="form-label">Retention Period (Days)</label>
                                        <Input
                                            type="number"
                                            min={1}
                                            value={historyRetentionDays}
                                            onChange={(e) => setHistoryRetentionDays(parseInt(e.target.value) || 30)}
                                            placeholder="30"
                                            className="form-input"
                                        />
                                    </div>
                                    <div className="form-group" style={{ minWidth: '200px' }}>
                                        <label className="form-label">Cleanup Check Interval (Hours)</label>
                                        <Input
                                            type="number"
                                            min={1}
                                            value={historyCleanupIntervalHours}
                                            onChange={(e) => setHistoryCleanupIntervalHours(parseInt(e.target.value) || 24)}
                                            placeholder="24"
                                            className="form-input"
                                        />
                                    </div>
                                </div>

                                <div className="control-group" style={{ marginTop: '16px' }}>
                                    <button
                                        className="add-button"
                                        onClick={handleSaveHistoryConfig}
                                        disabled={isSavingHistoryConfig}
                                        style={{ marginRight: '8px' }}
                                    >
                                        {isSavingHistoryConfig ? 'Saving...' : 'Save Configuration'}
                                    </button>
                                    <button
                                        className="delete-button"
                                        onClick={handleCleanupHistoryNow}
                                        disabled={isCleaningHistory}
                                        style={{
                                            backgroundColor: '#ff4d4f',
                                            borderColor: '#ff4d4f',
                                            color: 'white'
                                        }}
                                    >
                                        {isCleaningHistory ? 'Cleaning...' : 'Cleanup History Now'}
                                    </button>
                                </div>

                                <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#e6f7ff', borderRadius: '6px', border: '1px solid #91d5ff' }}>
                                    <h4 style={{ margin: '0 0 12px 0', color: '#0050b3', fontSize: '14px', fontWeight: '600' }}>Current Configuration:</h4>
                                    <p style={{ margin: '0 0 8px 0', color: '#0050b3', fontSize: '13px', lineHeight: '1.6' }}>
                                        <strong>Status:</strong> {historyCleanupEnabled ? 'Enabled ✓' : 'Disabled ✗'}
                                    </p>
                                    <p style={{ margin: '0 0 8px 0', color: '#0050b3', fontSize: '13px', lineHeight: '1.6' }}>
                                        <strong>Records older than:</strong> {historyRetentionDays} days will be deleted
                                    </p>
                                    <p style={{ margin: '0', color: '#0050b3', fontSize: '13px', lineHeight: '1.6' }}>
                                        <strong>Cleanup frequency:</strong> Every {historyCleanupIntervalHours} hours (note: scheduler checks every hour)
                                    </p>
                                </div>

                                <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                                    <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Instructions:</h4>
                                    <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                                        <li><strong>Enable Automatic Cleanup:</strong> Toggle to enable/disable scheduled cleanup for your organization</li>
                                        <li><strong>Retention Period:</strong> Number of days to keep history records before deletion (minimum: 1 day)</li>
                                        <li><strong>Cleanup Check Interval:</strong> How often the system should check and cleanup old records (minimum: 1 hour)</li>
                                        <li><strong>Manual Cleanup:</strong> Click "Cleanup History Now" to immediately delete old records based on current retention settings</li>
                                        <li>Changes take effect immediately after saving</li>
                                        <li>Each organization can configure its own cleanup settings independently</li>
                                        <li>The scheduler runs every hour and checks if cleanup is needed based on your interval setting</li>
                                    </ul>
                                </div>
                            </>
                        )}
                    </div>

                </div>

            </div>
        </div>
    );
};

export default UserManagementPage;
