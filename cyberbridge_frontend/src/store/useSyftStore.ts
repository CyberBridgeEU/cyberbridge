import {create} from 'zustand';
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api, syft_rest_api_wrapper } from "../constants/urls.ts";

export interface ScanResult {
    output?: any;
    error?: string;
    analysis?: string;
    repository?: string;
    summary?: any;
    raw_data?: any;
    success?: boolean;
}

export interface UseSyftStore {
    // variables
    scanResults: ScanResult | null;
    loading: boolean;
    error: string | null;
    apiHealthStatus: string | null;
    abortController: AbortController | null;

    // functions
    checkHealth: () => Promise<boolean>;
    scanZipFile: (file: File, useLlm?: boolean) => Promise<boolean>;
    scanGithubRepo: (githubUrl: string, useLlm?: boolean, githubToken?: string) => Promise<boolean>;
    clearResults: () => void;
    cancelScan: () => void;
}

const useSyftStore = create<UseSyftStore>((set, get) => ({
    // variables
    scanResults: null,
    loading: false,
    error: null,
    apiHealthStatus: null,
    abortController: null,

    // functions
    checkHealth: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${syft_rest_api_wrapper}/`, {
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
            console.log('Syft API health check response:', data);
            set({
                loading: false,
                apiHealthStatus: data.message || 'API is healthy but no message provided'
            });
            return true;
        } catch (error) {
            console.error('Error checking Syft API health:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to check scanner API health',
                loading: false,
                apiHealthStatus: null
            });
            return false;
        }
    },

    scanZipFile: async (file: File, useLlm: boolean = true) => {
        const controller = new AbortController();
        set({ loading: true, error: null, abortController: controller });
        try {
            // Create a FormData object to send the file
            const formData = new FormData();
            formData.append('file', file);

            // When sending FormData, don't set Content-Type header, browser will set it automatically
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/syft/scan?use_llm=${useLlm}`, {
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

    scanGithubRepo: async (githubUrl: string, useLlm: boolean = true, githubToken?: string) => {
        const controller = new AbortController();
        set({ loading: true, error: null, abortController: controller });
        try {
            // Build URL with query parameters
            let url = `${cyberbridge_back_end_rest_api}/scanners/syft/scan-github?github_url=${encodeURIComponent(githubUrl)}&use_llm=${useLlm}`;

            // Add token if provided (for private repos)
            if (githubToken && githubToken.trim()) {
                url += `&github_token=${encodeURIComponent(githubToken.trim())}`;
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

export default useSyftStore;
