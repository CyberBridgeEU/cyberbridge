import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

export interface QlonConfig {
    url: string;
    apiKey: string;
    useIntegrationTools: boolean;
}

export interface AIFeatureSettings {
    aiRemediatorEnabled: boolean;
    remediatorPromptZap: string | null;
    remediatorPromptNmap: string | null;
    defaultPromptZap: string;
    defaultPromptNmap: string;
}

interface UseSettingsStore {
    // Scanner visibility settings
    scannersEnabled: boolean;
    allowedScannerDomains: string[]; // Empty array means all domains allowed

    // LLM URL settings
    customLlmUrl: string | null; // null means use default

    // LLM Payload settings
    customLlmPayload: string | null; // JSON string template with variables like {{prompt}}, {{model}}

    // LLM Provider settings
    llmProvider: 'llamacpp' | 'qlon'; // Which LLM provider to use

    // QLON Ai configuration
    qlonConfig: QlonConfig | null;

    // AI Feature settings
    aiFeatureSettings: AIFeatureSettings | null;

    // Super Admin Focused Mode
    superAdminFocusedMode: boolean;

    // Actions
    setScannersEnabled: (enabled: boolean) => void;
    setAllowedScannerDomains: (domains: string[]) => void;
    setCustomLlmUrl: (url: string | null) => void;
    setCustomLlmPayload: (payload: string | null) => void;
    setLlmProvider: (provider: 'llamacpp' | 'qlon') => void;
    setQlonConfig: (config: QlonConfig | null) => void;
    loadSettings: () => void;
    canUserAccessScanners: (userDomain: string) => boolean;
    getLlmUrl: () => string;
    getLlmPayload: (prompt: string, model?: string) => object;
    getLlmProvider: () => 'llamacpp' | 'qlon';
    getQlonConfig: () => QlonConfig | null;
    // AI Feature actions
    loadAIFeatureSettings: (organisationId: string) => Promise<void>;
    updateAIFeatureSettings: (organisationId: string, settings: Partial<AIFeatureSettings>) => Promise<void>;
    getAIFeatureSettings: () => AIFeatureSettings | null;
    // Super Admin Focused Mode actions
    setSuperAdminFocusedMode: (enabled: boolean) => Promise<void>;
}

const useSettingsStore = create<UseSettingsStore>((set, get) => ({
    // Default state - scanners enabled for all domains
    scannersEnabled: true,
    allowedScannerDomains: [], // Empty means all domains allowed
    customLlmUrl: null, // null means use default
    customLlmPayload: null, // null means use default llama.cpp payload
    llmProvider: 'llamacpp', // Default to llama.cpp
    qlonConfig: null, // QLON configuration
    aiFeatureSettings: null, // AI Feature settings
    superAdminFocusedMode: false, // Super Admin Focused Mode disabled by default

    // Toggle scanners visibility and persist to database
    setScannersEnabled: async (enabled: boolean) => {
        try {
            const { allowedScannerDomains } = get();

            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/scanners`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    scanners_enabled: enabled,
                    allowed_scanner_domains: allowedScannerDomains
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update scanner settings');
            }

            set({ scannersEnabled: enabled });
        } catch (error) {
            console.error('Error setting scanners enabled:', error);
            throw error;
        }
    },

    // Set allowed scanner domains and persist to database
    setAllowedScannerDomains: async (domains: string[]) => {
        try {
            const { scannersEnabled } = get();

            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/scanners`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    scanners_enabled: scannersEnabled,
                    allowed_scanner_domains: domains
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update allowed scanner domains');
            }

            set({ allowedScannerDomains: domains });
        } catch (error) {
            console.error('Error setting allowed scanner domains:', error);
            throw error;
        }
    },

    // Set custom LLM URL and persist to database
    setCustomLlmUrl: async (url: string | null) => {
        try {
            const { customLlmPayload } = get();

            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/llm`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    custom_llm_url: url,
                    custom_llm_payload: customLlmPayload
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update LLM URL');
            }

            set({ customLlmUrl: url });
        } catch (error) {
            console.error('Error setting custom LLM URL:', error);
            throw error;
        }
    },

    // Set custom LLM payload template and persist to database
    setCustomLlmPayload: async (payload: string | null) => {
        try {
            const { customLlmUrl, llmProvider, qlonConfig } = get();

            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/llm`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    custom_llm_url: customLlmUrl,
                    custom_llm_payload: payload,
                    llm_provider: llmProvider,
                    qlon_url: qlonConfig?.url || null,
                    qlon_api_key: qlonConfig?.apiKey || null,
                    qlon_use_tools: qlonConfig?.useIntegrationTools ?? true
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update LLM payload');
            }

            set({ customLlmPayload: payload });
        } catch (error) {
            console.error('Error setting custom LLM payload:', error);
            throw error;
        }
    },

    // Set LLM provider and persist to database
    setLlmProvider: async (provider: 'llamacpp' | 'qlon') => {
        try {
            const { customLlmUrl, customLlmPayload, qlonConfig } = get();

            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/llm`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    custom_llm_url: customLlmUrl,
                    custom_llm_payload: customLlmPayload,
                    llm_provider: provider,
                    qlon_url: qlonConfig?.url || null,
                    qlon_api_key: qlonConfig?.apiKey || null,
                    qlon_use_tools: qlonConfig?.useIntegrationTools ?? true
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update LLM provider');
            }

            set({ llmProvider: provider });
        } catch (error) {
            console.error('Error setting LLM provider:', error);
            throw error;
        }
    },

    // Set QLON configuration and persist to database
    setQlonConfig: async (config: QlonConfig | null) => {
        try {
            const { customLlmUrl, customLlmPayload, llmProvider } = get();

            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/llm`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    custom_llm_url: customLlmUrl,
                    custom_llm_payload: customLlmPayload,
                    llm_provider: llmProvider,
                    qlon_url: config?.url || null,
                    qlon_api_key: config?.apiKey || null,
                    qlon_use_tools: config?.useIntegrationTools ?? true
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update QLON configuration');
            }

            set({ qlonConfig: config });
        } catch (error) {
            console.error('Error setting QLON config:', error);
            throw error;
        }
    },

    // Load settings from API on app initialization
    loadSettings: async () => {
        // Load all settings from API
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            if (authHeader) {
                // Fetch LLM settings
                const llmResponse = await fetch(`${cyberbridge_back_end_rest_api}/settings/llm`, {
                    headers: {
                        ...authHeader
                    }
                });

                // Fetch scanner settings
                const scannerResponse = await fetch(`${cyberbridge_back_end_rest_api}/settings/scanners`, {
                    headers: {
                        ...authHeader
                    }
                });

                // Fetch super admin focused mode setting
                const focusedModeResponse = await fetch(`${cyberbridge_back_end_rest_api}/settings/super-admin-focused-mode`, {
                    headers: {
                        ...authHeader
                    }
                });

                // Process focused mode response
                let superAdminFocusedMode = false;
                if (focusedModeResponse.ok) {
                    const focusedModeData = await focusedModeResponse.json();
                    superAdminFocusedMode = focusedModeData.super_admin_focused_mode ?? false;
                }

                if (llmResponse.ok && scannerResponse.ok) {
                    const llmData = await llmResponse.json();
                    const scannerData = await scannerResponse.json();

                    // Build QLON config if data exists
                    const qlonConfig = llmData.qlon_url ? {
                        url: llmData.qlon_url,
                        apiKey: llmData.qlon_api_key || '',
                        useIntegrationTools: llmData.qlon_use_tools ?? true
                    } : null;

                    set({
                        scannersEnabled: scannerData.scanners_enabled,
                        allowedScannerDomains: scannerData.allowed_scanner_domains || [],
                        customLlmUrl: llmData.custom_llm_url,
                        customLlmPayload: llmData.custom_llm_payload,
                        llmProvider: llmData.llm_provider || 'llamacpp',
                        qlonConfig: qlonConfig,
                        superAdminFocusedMode: superAdminFocusedMode
                    });
                } else if (llmResponse.ok) {
                    // If only LLM settings are available
                    const llmData = await llmResponse.json();

                    // Build QLON config if data exists
                    const qlonConfig = llmData.qlon_url ? {
                        url: llmData.qlon_url,
                        apiKey: llmData.qlon_api_key || '',
                        useIntegrationTools: llmData.qlon_use_tools ?? true
                    } : null;

                    set({
                        customLlmUrl: llmData.custom_llm_url,
                        customLlmPayload: llmData.custom_llm_payload,
                        llmProvider: llmData.llm_provider || 'llamacpp',
                        qlonConfig: qlonConfig,
                        superAdminFocusedMode: superAdminFocusedMode
                    });
                } else if (scannerResponse.ok) {
                    // If only scanner settings are available
                    const scannerData = await scannerResponse.json();
                    set({
                        scannersEnabled: scannerData.scanners_enabled,
                        allowedScannerDomains: scannerData.allowed_scanner_domains || [],
                        superAdminFocusedMode: superAdminFocusedMode
                    });
                } else {
                    // Even if other settings fail, still set focused mode
                    set({ superAdminFocusedMode: superAdminFocusedMode });
                }
            }
        } catch (error) {
            console.error('Error loading settings from API:', error);
        }
    },

    // Check if a user can access scanners based on their domain
    canUserAccessScanners: (userDomain: string) => {
        const { scannersEnabled, allowedScannerDomains } = get();

        // If scanners are globally disabled, no one has access
        if (!scannersEnabled) {
            return false;
        }

        // If no specific domains are set (empty array), all domains have access
        if (allowedScannerDomains.length === 0) {
            return true;
        }

        // Check if user's domain is in the allowed list
        return allowedScannerDomains.includes(userDomain);
    },

    // Get the LLM URL (custom or default)
    getLlmUrl: () => {
        const { customLlmUrl } = get();
        if (customLlmUrl) {
            return customLlmUrl;
        }
        // Return default llama.cpp URL based on environment
        // In production (containerized), use Docker service name 'llamacpp'
        // In development (outside Docker), use 'localhost' to access Docker container
        const isProduction = import.meta.env.PROD;
        if (isProduction) {
            return 'http://llamacpp:11435/v1/chat/completions';
        } else {
            return 'http://localhost:11435/v1/chat/completions';
        }
    },

    // Get the LLM payload (custom or default)
    // Supports variable substitution: {{prompt}}, {{model}}
    getLlmPayload: (prompt: string, model: string = 'phi4:14b') => {
        const { customLlmPayload } = get();

        if (customLlmPayload) {
            try {
                // Replace variables in the template
                const payloadStr = customLlmPayload
                    .replace(/\{\{prompt\}\}/g, prompt)
                    .replace(/\{\{model\}\}/g, model);

                // Parse and return the payload object
                return JSON.parse(payloadStr);
            } catch (error) {
                console.error('Error parsing custom LLM payload:', error);
                // Fall back to default if custom payload is invalid
            }
        }

        // Default llama.cpp payload
        return {
            model: model,
            prompt: prompt,
            stream: false
        };
    },

    // Get the current LLM provider
    getLlmProvider: () => {
        const { llmProvider } = get();
        return llmProvider;
    },

    // Get QLON configuration
    getQlonConfig: () => {
        const { qlonConfig } = get();
        return qlonConfig;
    },

    // Load AI Feature settings for an organization
    loadAIFeatureSettings: async (organisationId: string) => {
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            if (!authHeader) {
                console.error('No auth header available');
                return;
            }

            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/settings/org-llm/${organisationId}/ai-features`,
                {
                    headers: {
                        ...authHeader
                    }
                }
            );

            if (response.ok) {
                const data = await response.json();
                set({
                    aiFeatureSettings: {
                        aiRemediatorEnabled: data.ai_remediator_enabled || false,
                        remediatorPromptZap: data.remediator_prompt_zap || null,
                        remediatorPromptNmap: data.remediator_prompt_nmap || null,
                        defaultPromptZap: data.default_prompt_zap || '',
                        defaultPromptNmap: data.default_prompt_nmap || ''
                    }
                });
            } else {
                console.error('Failed to load AI feature settings');
            }
        } catch (error) {
            console.error('Error loading AI feature settings:', error);
        }
    },

    // Update AI Feature settings for an organization
    updateAIFeatureSettings: async (organisationId: string, settings: Partial<AIFeatureSettings>) => {
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            if (!authHeader) {
                throw new Error('No auth header available');
            }

            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/settings/org-llm/${organisationId}/ai-features`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        ...authHeader
                    },
                    body: JSON.stringify({
                        ai_remediator_enabled: settings.aiRemediatorEnabled,
                        remediator_prompt_zap: settings.remediatorPromptZap,
                        remediator_prompt_nmap: settings.remediatorPromptNmap
                    })
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to update AI feature settings');
            }

            const data = await response.json();
            set({
                aiFeatureSettings: {
                    aiRemediatorEnabled: data.ai_remediator_enabled || false,
                    remediatorPromptZap: data.remediator_prompt_zap || null,
                    remediatorPromptNmap: data.remediator_prompt_nmap || null,
                    defaultPromptZap: data.default_prompt_zap || '',
                    defaultPromptNmap: data.default_prompt_nmap || ''
                }
            });
        } catch (error) {
            console.error('Error updating AI feature settings:', error);
            throw error;
        }
    },

    // Get AI Feature settings
    getAIFeatureSettings: () => {
        const { aiFeatureSettings } = get();
        return aiFeatureSettings;
    },

    // Set Super Admin Focused Mode and persist to database
    setSuperAdminFocusedMode: async (enabled: boolean) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/super-admin-focused-mode`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    super_admin_focused_mode: enabled
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update super admin focused mode');
            }

            set({ superAdminFocusedMode: enabled });
        } catch (error) {
            console.error('Error setting super admin focused mode:', error);
            throw error;
        }
    },
}));

export default useSettingsStore;
