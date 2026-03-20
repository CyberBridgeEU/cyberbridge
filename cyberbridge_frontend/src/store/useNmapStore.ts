import {create} from 'zustand';
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

// Vulnerability interface for new structured response
export interface NmapVulnerability {
    id: string;
    severity: 'High' | 'Medium' | 'Low' | 'Info';
    title: string;
    description?: string;
    host?: string;
    port?: number;
    protocol?: string;
    service_name?: string;
    service_version?: string;
    cpe?: string;
    cve_id?: string;
    cvss_score?: number;
    references?: Array<{ url?: string; source?: string; tags?: string[] }>;
    cwe_ids?: string[];
}

// Summary counts by severity
export interface NmapScanSummary {
    high: number;
    medium: number;
    low: number;
    info: number;
    total: number;
}

// Pagination info from server
export interface PaginationInfo {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
}

export interface ScanResult {
    success: boolean;
    scan_id?: string;  // For fetching additional pages
    output?: any;
    error?: string;
    // Vulnerability-based response fields
    vulnerabilities?: NmapVulnerability[];
    summary?: NmapScanSummary;
    pagination?: PaginationInfo;
    raw_data?: any;
    analysis?: string; // Backward-compatible text analysis
}

export interface UseNmapStore {
    // variables
    scanResults: ScanResult | null;
    loading: boolean;
    pageLoading: boolean;  // For pagination loading state
    error: string | null;

    // functions (useLlm parameter kept for backward compatibility but ignored)
    basicScan: (target: string, useLlm?: boolean) => Promise<boolean>;
    portScan: (target: string, ports: string, useLlm?: boolean) => Promise<boolean>;
    allPortsScan: (target: string, useLlm?: boolean) => Promise<boolean>;
    aggressiveScan: (target: string, useLlm?: boolean) => Promise<boolean>;
    osScan: (target: string, useLlm?: boolean) => Promise<boolean>;
    networkScan: (network: string, useLlm?: boolean) => Promise<boolean>;
    stealthScan: (target: string, useLlm?: boolean) => Promise<boolean>;
    noPingScan: (target: string, useLlm?: boolean) => Promise<boolean>;
    fastScan: (target: string, useLlm?: boolean) => Promise<boolean>;
    serviceVersionScan: (target: string, ports?: string, useLlm?: boolean) => Promise<boolean>;
    fetchPage: (page: number, pageSize?: number) => Promise<boolean>;
    clearResults: () => void;
}

const useNmapStore = create<UseNmapStore>((set, get) => ({
    // variables
    scanResults: null,
    loading: false,
    pageLoading: false,
    error: null,

    // Fetch a specific page of results using cached scan_id
    fetchPage: async (page: number, pageSize: number = 10) => {
        const currentResults = get().scanResults;
        if (!currentResults?.scan_id) {
            console.error('No scan_id available for pagination');
            return false;
        }

        set({ pageLoading: true });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/scanners/nmap/results/${currentResults.scan_id}?page=${page}&page_size=${pageSize}`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to fetch page',
                    pageLoading: false
                });
                return false;
            }

            const pageData = await response.json();

            // Update only the vulnerabilities and pagination, keep other data
            set(state => ({
                scanResults: state.scanResults ? {
                    ...state.scanResults,
                    vulnerabilities: pageData.vulnerabilities,
                    pagination: pageData.pagination
                } : null,
                pageLoading: false
            }));
            return true;
        } catch (error) {
            console.error('Error fetching page:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch page',
                pageLoading: false
            });
            return false;
        }
    },

    // functions
    basicScan: async (target: string, useLlm: boolean = true) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/nmap/scan/basic?target=${encodeURIComponent(target)}&use_llm=${useLlm}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                },
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to perform basic scan',
                    loading: false
                });
                return false;
            }

            const scanResults = await response.json();
            set({ scanResults, loading: false });
            return true;
        } catch (error) {
            console.error('Error performing basic scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to perform basic scan',
                loading: false
            });
            return false;
        }
    },

    portScan: async (target: string, ports: string, useLlm: boolean = true) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/nmap/scan/ports?target=${encodeURIComponent(target)}&ports=${encodeURIComponent(ports)}&use_llm=${useLlm}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to perform port scan',
                    loading: false
                });
                return false;
            }

            const scanResults = await response.json();
            set({ scanResults, loading: false });
            return true;
        } catch (error) {
            console.error('Error performing port scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to perform port scan',
                loading: false
            });
            return false;
        }
    },

    allPortsScan: async (target: string, useLlm: boolean = true) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/nmap/scan/all_ports?target=${encodeURIComponent(target)}&use_llm=${useLlm}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to perform all ports scan',
                    loading: false
                });
                return false;
            }

            const scanResults = await response.json();
            set({ scanResults, loading: false });
            return true;
        } catch (error) {
            console.error('Error performing all ports scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to perform all ports scan',
                loading: false
            });
            return false;
        }
    },

    aggressiveScan: async (target: string, useLlm: boolean = true) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/nmap/scan/aggressive?target=${encodeURIComponent(target)}&use_llm=${useLlm}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to perform aggressive scan',
                    loading: false
                });
                return false;
            }

            const scanResults = await response.json();
            set({ scanResults, loading: false });
            return true;
        } catch (error) {
            console.error('Error performing aggressive scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to perform aggressive scan',
                loading: false
            });
            return false;
        }
    },

    osScan: async (target: string, useLlm: boolean = true) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/nmap/scan/os?target=${encodeURIComponent(target)}&use_llm=${useLlm}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to perform OS scan',
                    loading: false
                });
                return false;
            }

            const scanResults = await response.json();
            set({ scanResults, loading: false });
            return true;
        } catch (error) {
            console.error('Error performing OS scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to perform OS scan',
                loading: false
            });
            return false;
        }
    },

    networkScan: async (network: string, useLlm: boolean = true) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/nmap/scan/network?network=${encodeURIComponent(network)}&use_llm=${useLlm}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to perform network scan',
                    loading: false
                });
                return false;
            }

            const scanResults = await response.json();
            set({ scanResults, loading: false });
            return true;
        } catch (error) {
            console.error('Error performing network scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to perform network scan',
                loading: false
            });
            return false;
        }
    },

    stealthScan: async (target: string, useLlm: boolean = true) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/nmap/scan/stealth?target=${encodeURIComponent(target)}&use_llm=${useLlm}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to perform stealth scan',
                    loading: false
                });
                return false;
            }

            const scanResults = await response.json();
            set({ scanResults, loading: false });
            return true;
        } catch (error) {
            console.error('Error performing stealth scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to perform stealth scan',
                loading: false
            });
            return false;
        }
    },

    noPingScan: async (target: string, useLlm: boolean = true) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/nmap/scan/no_ping?target=${encodeURIComponent(target)}&use_llm=${useLlm}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to perform no ping scan',
                    loading: false
                });
                return false;
            }

            const scanResults = await response.json();
            set({ scanResults, loading: false });
            return true;
        } catch (error) {
            console.error('Error performing no ping scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to perform no ping scan',
                loading: false
            });
            return false;
        }
    },

    fastScan: async (target: string, useLlm: boolean = true) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/nmap/scan/fast?target=${encodeURIComponent(target)}&use_llm=${useLlm}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to perform fast scan',
                    loading: false
                });
                return false;
            }

            const scanResults = await response.json();
            set({ scanResults, loading: false });
            return true;
        } catch (error) {
            console.error('Error performing fast scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to perform fast scan',
                loading: false
            });
            return false;
        }
    },

    serviceVersionScan: async (target: string, ports?: string, useLlm: boolean = true) => {
        set({ loading: true, error: null });
        try {
            let url = `${cyberbridge_back_end_rest_api}/scanners/nmap/scan/service_version?target=${encodeURIComponent(target)}&use_llm=${useLlm}`;
            if (ports) {
                url += `&ports=${encodeURIComponent(ports)}`;
            }

            const response = await fetch(url, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to perform service version scan',
                    loading: false
                });
                return false;
            }

            const scanResults = await response.json();
            set({ scanResults, loading: false });
            return true;
        } catch (error) {
            console.error('Error performing service version scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to perform service version scan',
                loading: false
            });
            return false;
        }
    },

    clearResults: () => {
        set({ scanResults: null });
    }
}));

export default useNmapStore;
