import {create} from 'zustand';
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api, semgrep_rest_api_wrapper } from "../constants/urls.ts";

export interface ScanResult {
    output?: unknown;
    error?: string;
    analysis?: string;
    repository?: string;
}

export interface QlonConfig {
    url: string;
    apiKey: string;
    useIntegrationTools: boolean;
}

export interface LlmConfig {
    provider: 'llamacpp' | 'qlon';
    qlon?: QlonConfig;
}

export interface UseSemgrepStore {
    // variables
    scanResults: ScanResult | null;
    loading: boolean;
    error: string | null;
    configOptions: string[];
    apiHealthStatus: string | null;
    abortController: AbortController | null;

    // functions
    checkHealth: () => Promise<boolean>;
    scanZipFile: (file: File, config: string, useLlm?: boolean, llmConfig?: LlmConfig) => Promise<boolean>;
    scanGithubRepo: (githubUrl: string, config: string, useLlm?: boolean, githubToken?: string, llmConfig?: LlmConfig) => Promise<boolean>;
    clearResults: () => void;
    cancelScan: () => void;
}

const useSemgrepStore = create<UseSemgrepStore>((set, get) => ({
    // variables
    scanResults: null,
    loading: false,
    error: null,
    apiHealthStatus: null,
    configOptions: ['auto', 'p/ci', 'p/security-audit', 'p/owasp-top-ten'],
    abortController: null,

    // functions
    checkHealth: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${semgrep_rest_api_wrapper}/`, {
                headers: {...useAuthStore.getState().getAuthHeader()},
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to check scanner API health',
                    loading: false,
                    apiHealthStatus: null
                });
                return false;
            }

            const data = await response.json();
            console.log('Semgrep API health check response:', data);
            set({
                loading: false,
                apiHealthStatus: data.message || 'API is healthy but no message provided'
            });
            return true;
        } catch (error) {
            console.error('Error checking Semgrep API health:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to check scanner API health',
                loading: false,
                apiHealthStatus: null
            });
            return false;
        }
    },

    scanZipFile: async (file: File, config: string, useLlm: boolean = true, llmConfig?: LlmConfig) => {
        const controller = new AbortController();
        set({ loading: true, error: null, abortController: controller });
        try {
            // Create a FormData object to send the file
            const formData = new FormData();
            formData.append('file', file);
            formData.append('config', config);

            // Build URL with query parameters
            let url = `${cyberbridge_back_end_rest_api}/scanners/semgrep/scan?use_llm=${useLlm}`;

            // Add LLM provider configuration if using LLM
            if (useLlm && llmConfig) {
                url += `&llm_provider=${llmConfig.provider}`;
                if (llmConfig.provider === 'qlon' && llmConfig.qlon) {
                    url += `&qlon_url=${encodeURIComponent(llmConfig.qlon.url)}`;
                    url += `&qlon_api_key=${encodeURIComponent(llmConfig.qlon.apiKey)}`;
                    url += `&qlon_use_tools=${llmConfig.qlon.useIntegrationTools}`;
                }
            }

            // When sending FormData, don't set Content-Type header, browser will set it automatically
            const response = await fetch(url, {
                method: 'POST',
                headers: {...useAuthStore.getState().getAuthHeader()},
                body: formData,
                signal: controller.signal
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to scan ZIP file',
                    loading: false,
                    abortController: null
                });
                return false;
            }

            const scanResults = await response.json();
            set({ scanResults, loading: false, abortController: null });
            return true;
        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                set({ loading: false, abortController: null });
                return false;
            }
            console.error('Error scanning ZIP file:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to scan ZIP file',
                loading: false,
                abortController: null
            });
            return false;
        }
    },

    scanGithubRepo: async (githubUrl: string, config: string, useLlm: boolean = true, githubToken?: string, llmConfig?: LlmConfig) => {
        const controller = new AbortController();
        set({ loading: true, error: null, abortController: controller });
        try {
            // Build URL with query parameters
            let url = `${cyberbridge_back_end_rest_api}/scanners/semgrep/scan-github?github_url=${encodeURIComponent(githubUrl)}&config=${encodeURIComponent(config)}&use_llm=${useLlm}`;

            // Add token if provided (for private repos)
            if (githubToken && githubToken.trim()) {
                url += `&github_token=${encodeURIComponent(githubToken.trim())}`;
            }

            // Add LLM provider configuration if using LLM
            if (useLlm && llmConfig) {
                url += `&llm_provider=${llmConfig.provider}`;
                if (llmConfig.provider === 'qlon' && llmConfig.qlon) {
                    url += `&qlon_url=${encodeURIComponent(llmConfig.qlon.url)}`;
                    url += `&qlon_api_key=${encodeURIComponent(llmConfig.qlon.apiKey)}`;
                    url += `&qlon_use_tools=${llmConfig.qlon.useIntegrationTools}`;
                }
            }

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    ...useAuthStore.getState().getAuthHeader(),
                    'Content-Type': 'application/json'
                },
                signal: controller.signal
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to scan GitHub repository',
                    loading: false,
                    abortController: null
                });
                return false;
            }

            const scanResults = await response.json();
            set({ scanResults, loading: false, abortController: null });
            return true;
        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                set({ loading: false, abortController: null });
                return false;
            }
            console.error('Error scanning GitHub repository:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to scan GitHub repository',
                loading: false,
                abortController: null
            });
            return false;
        }
    },

    cancelScan: () => {
        const controller = get().abortController;
        if (controller) controller.abort();
        set({ loading: false, abortController: null });
        // Tell the backend to stop llama.cpp generation
        fetch(`${cyberbridge_back_end_rest_api}/scanners/cancel-llm`, {
            method: 'POST',
            headers: { ...useAuthStore.getState().getAuthHeader() },
        }).catch(() => {});
    },

    clearResults: () => {
        set({ scanResults: null });
    }
}));

export default useSemgrepStore;
