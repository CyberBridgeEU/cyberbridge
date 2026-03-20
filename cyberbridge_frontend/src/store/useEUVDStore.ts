import { create } from "zustand";
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

export interface EUVDVulnerability {
    id: string;
    euvd_id: string;
    description: string | null;
    date_published: string | null;
    date_updated: string | null;
    base_score: number | null;
    base_score_version: string | null;
    base_score_vector: string | null;
    epss: number | null;
    assigner: string | null;
    references: string | null;
    aliases: string | null;
    products: string | null;
    vendors: string | null;
    is_exploited: boolean;
    is_critical: boolean;
    category: string;
}

export interface EUVDStats {
    total_cached: number;
    exploited_count: number;
    critical_count: number;
    last_sync_at: string | null;
    sync_status: string | null;
}

interface EUVDStore {
    exploitedVulns: EUVDVulnerability[];
    exploitedTotal: number;
    criticalVulns: EUVDVulnerability[];
    criticalTotal: number;
    latestVulns: EUVDVulnerability[];
    latestTotal: number;
    searchResults: EUVDVulnerability[];
    searchTotal: number;
    stats: EUVDStats;
    loading: boolean;
    searching: boolean;
    syncing: boolean;

    fetchExploited: (skip?: number, limit?: number, days?: number) => Promise<void>;
    fetchCritical: (skip?: number, limit?: number, days?: number) => Promise<void>;
    fetchLatest: (skip?: number, limit?: number, days?: number) => Promise<void>;
    searchVulns: (params: Record<string, any>) => Promise<void>;
    triggerSync: () => Promise<boolean>;
    deleteByDateRange: (dateFrom?: string, dateTo?: string) => Promise<{ deleted: number } | null>;
    deleteAll: () => Promise<{ deleted: number } | null>;
    fetchStats: () => Promise<void>;
    fetchSyncStatus: () => Promise<any>;
}

const getHeaders = () => {
    const token = useAuthStore.getState().token;
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    };
};

const useEUVDStore = create<EUVDStore>((set) => ({
    exploitedVulns: [],
    exploitedTotal: 0,
    criticalVulns: [],
    criticalTotal: 0,
    latestVulns: [],
    latestTotal: 0,
    searchResults: [],
    searchTotal: 0,
    stats: { total_cached: 0, exploited_count: 0, critical_count: 0, last_sync_at: null, sync_status: null },
    loading: false,
    searching: false,
    syncing: false,

    fetchExploited: async (skip = 0, limit = 50, days?: number) => {
        set({ loading: true });
        try {
            let url = `${cyberbridge_back_end_rest_api}/euvd/exploited?skip=${skip}&limit=${limit}`;
            if (days) url += `&days=${days}`;
            const res = await fetch(url, { headers: getHeaders() });
            if (res.ok) {
                const data = await res.json();
                set({ exploitedVulns: data.items || [], exploitedTotal: data.total || 0 });
            }
        } catch (e) {
            console.error("Failed to fetch exploited vulns:", e);
        } finally {
            set({ loading: false });
        }
    },

    fetchCritical: async (skip = 0, limit = 50, days?: number) => {
        set({ loading: true });
        try {
            let url = `${cyberbridge_back_end_rest_api}/euvd/critical?skip=${skip}&limit=${limit}`;
            if (days) url += `&days=${days}`;
            const res = await fetch(url, { headers: getHeaders() });
            if (res.ok) {
                const data = await res.json();
                set({ criticalVulns: data.items || [], criticalTotal: data.total || 0 });
            }
        } catch (e) {
            console.error("Failed to fetch critical vulns:", e);
        } finally {
            set({ loading: false });
        }
    },

    fetchLatest: async (skip = 0, limit = 50, days?: number) => {
        set({ loading: true });
        try {
            let url = `${cyberbridge_back_end_rest_api}/euvd/latest?skip=${skip}&limit=${limit}`;
            if (days) url += `&days=${days}`;
            const res = await fetch(url, { headers: getHeaders() });
            if (res.ok) {
                const data = await res.json();
                set({ latestVulns: data.items || [], latestTotal: data.total || 0 });
            }
        } catch (e) {
            console.error("Failed to fetch latest vulns:", e);
        } finally {
            set({ loading: false });
        }
    },

    searchVulns: async (params: Record<string, any>) => {
        set({ searching: true });
        try {
            const queryParams = new URLSearchParams();
            Object.entries(params).forEach(([key, value]) => {
                if (value !== undefined && value !== null && value !== '') {
                    queryParams.append(key, String(value));
                }
            });
            const res = await fetch(`${cyberbridge_back_end_rest_api}/euvd/search?${queryParams.toString()}`, {
                headers: getHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                // EUVD search returns items array or direct array
                const items = data.items || data || [];
                set({ searchResults: Array.isArray(items) ? items : [], searchTotal: data.total || items.length || 0 });
            }
        } catch (e) {
            console.error("Failed to search EUVD:", e);
        } finally {
            set({ searching: false });
        }
    },

    triggerSync: async () => {
        set({ syncing: true });
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/euvd/sync`, {
                method: "POST",
                headers: getHeaders()
            });
            if (res.ok) {
                return true;
            }
            return false;
        } catch (e) {
            console.error("Failed to trigger sync:", e);
            return false;
        } finally {
            set({ syncing: false });
        }
    },

    deleteByDateRange: async (dateFrom?: string, dateTo?: string) => {
        try {
            const params = new URLSearchParams();
            if (dateFrom) params.append('date_from', dateFrom);
            if (dateTo) params.append('date_to', dateTo);
            const res = await fetch(`${cyberbridge_back_end_rest_api}/euvd/vulnerabilities?${params.toString()}`, {
                method: "DELETE",
                headers: getHeaders()
            });
            if (res.ok) {
                return await res.json();
            }
            return null;
        } catch (e) {
            console.error("Failed to delete EUVD vulns:", e);
            return null;
        }
    },

    deleteAll: async () => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/euvd/vulnerabilities/all`, {
                method: "DELETE",
                headers: getHeaders()
            });
            if (res.ok) {
                return await res.json();
            }
            return null;
        } catch (e) {
            console.error("Failed to delete all EUVD vulns:", e);
            return null;
        }
    },

    fetchStats: async () => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/euvd/stats`, {
                headers: getHeaders()
            });
            if (res.ok) {
                const data = await res.json();
                set({ stats: data });
            }
        } catch (e) {
            console.error("Failed to fetch EUVD stats:", e);
        }
    },

    fetchSyncStatus: async () => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/euvd/sync/status`, {
                headers: getHeaders()
            });
            if (res.ok) {
                return await res.json();
            }
            return null;
        } catch (e) {
            console.error("Failed to fetch sync status:", e);
            return null;
        }
    }
}));

export default useEUVDStore;
