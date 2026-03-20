import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

export interface DarkWebScan {
    scan_id: string;
    keyword: string;
    status: 'queued' | 'processing' | 'completed' | 'failed';
    created_at: string;
    started_at?: string;
    completed_at?: string;
    error?: string;
    position?: number;
    estimated_wait_minutes?: number;
    files?: {
        json_exists: boolean;
        pdf_exists: boolean;
        pdf_files: string[];
    };
    owner?: {
        username: string;
        email: string;
    };
    is_admin_view?: boolean;
    results?: {
        findings: any[];
        summary?: {
            total_sites?: number;
            total_keywords?: number;
        };
        categorized_findings?: Record<string, {
            main_category: string;
            found_subcategories: string[];
        }>;
    };
}

export interface QueueOverview {
    queue_length: number;
    processing_count: number;
    active_workers: number;
    max_workers: number;
    currently_processing?: string[];
}

export interface DarkWebEngine {
    name: string;
    display_name: string;
    enabled: boolean;
}

interface DarkWebState {
    queueOverview: QueueOverview | null;
    scans: DarkWebScan[];
    totalScans: number;
    isAdminView: boolean;
    currentScan: DarkWebScan | null;
    workers: { max_workers: number } | null;
    engines: DarkWebEngine[];
    loading: boolean;
    scansLoading: boolean;
    scanDetailLoading: boolean;
    workersLoading: boolean;
    enginesLoading: boolean;
    error: string | null;

    fetchQueueOverview: () => Promise<void>;
    fetchScans: (status?: string, limit?: number) => Promise<void>;
    fetchScanResult: (scanId: string) => Promise<void>;
    createScan: (keyword: string, mpUnits?: number, limit?: number) => Promise<{ scan_id: string; queue_position: number } | null>;
    deleteScan: (scanId: string) => Promise<void>;
    downloadPdf: (scanId: string, keyword: string) => Promise<void>;
    downloadJson: (scanId: string, keyword: string) => Promise<void>;
    fetchWorkers: () => Promise<void>;
    updateWorkers: (maxWorkers: number) => Promise<void>;
    fetchEngines: () => Promise<void>;
    updateEngines: (enabledEngines: string[]) => Promise<void>;
}

const useDarkWebStore = create<DarkWebState>((set, get) => ({
    queueOverview: null,
    scans: [],
    totalScans: 0,
    isAdminView: false,
    currentScan: null,
    workers: null,
    engines: [],
    loading: false,
    scansLoading: false,
    scanDetailLoading: false,
    workersLoading: false,
    enginesLoading: false,
    error: null,

    fetchQueueOverview: async () => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/dark-web/queue/overview`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to fetch queue overview');
            const data = await res.json();
            set({ queueOverview: data });
        } catch (e: any) {
            set({ error: e.message });
        }
    },

    fetchScans: async (status?: string, limit?: number) => {
        set({ scansLoading: true, error: null });
        try {
            let url = `${cyberbridge_back_end_rest_api}/dark-web/scans`;
            const params: string[] = [];
            if (status) params.push(`status=${encodeURIComponent(status)}`);
            if (limit) params.push(`limit=${limit}`);
            if (params.length > 0) url += '?' + params.join('&');

            const res = await fetch(url, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to fetch scans');
            const data = await res.json();
            set({
                scans: data.scans || [],
                totalScans: data.total || 0,
                isAdminView: data.is_admin_view || false,
                scansLoading: false,
            });
        } catch (e: any) {
            set({ error: e.message, scansLoading: false });
        }
    },

    fetchScanResult: async (scanId: string) => {
        set({ scanDetailLoading: true, error: null });
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/dark-web/scan/json/${scanId}`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to fetch scan result');
            const data = await res.json();
            set({ currentScan: data, scanDetailLoading: false });
        } catch (e: any) {
            set({ error: e.message, scanDetailLoading: false });
        }
    },

    createScan: async (keyword: string, mpUnits: number = 2, limit: number = 3) => {
        set({ loading: true, error: null });
        try {
            const params = new URLSearchParams({
                keyword: keyword.trim(),
                mp_units: String(mpUnits),
                limit: String(limit),
                proxy: 'localhost:9050',
                continuous_write: 'false',
            });
            const res = await fetch(`${cyberbridge_back_end_rest_api}/dark-web/scan?${params.toString()}`, {
                method: 'POST',
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to create scan');
            }
            const data = await res.json();
            set({ loading: false });
            await get().fetchScans();
            return data;
        } catch (e: any) {
            set({ error: e.message, loading: false });
            throw e;
        }
    },

    deleteScan: async (scanId: string) => {
        const authHeader = useAuthStore.getState().getAuthHeader();
        if (!authHeader) {
            throw new Error('Not authenticated');
        }
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/dark-web/scan/${scanId}`, {
                method: 'DELETE',
                headers: {
                    ...authHeader,
                    'Content-Type': 'application/json',
                },
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => null);
                throw new Error(errData?.detail || 'Failed to delete scan');
            }
            await get().fetchScans();
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },

    downloadPdf: async (scanId: string, keyword: string) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/dark-web/download/pdf/${scanId}`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to download PDF');
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `security_report_${keyword}_${scanId.substring(0, 8)}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },

    downloadJson: async (scanId: string, keyword: string) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/dark-web/scan/json/${scanId}`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to download JSON');
            const data = await res.json();
            const jsonString = JSON.stringify(data, null, 2);
            const blob = new Blob([jsonString], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `scan_results_${keyword}_${scanId.substring(0, 8)}.json`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },

    fetchWorkers: async () => {
        set({ workersLoading: true });
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/dark-web/settings/workers`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to fetch workers');
            const data = await res.json();
            set({ workers: data, workersLoading: false });
        } catch (e: any) {
            set({ error: e.message, workersLoading: false });
        }
    },

    updateWorkers: async (maxWorkers: number) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/dark-web/settings/workers?max_workers=${maxWorkers}`, {
                method: 'PUT',
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to update workers');
            await get().fetchWorkers();
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },

    fetchEngines: async () => {
        set({ enginesLoading: true });
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/dark-web/settings/engines`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to fetch engines');
            const data = await res.json();
            set({ engines: data.engines || [], enginesLoading: false });
        } catch (e: any) {
            set({ error: e.message, enginesLoading: false });
        }
    },

    updateEngines: async (enabledEngines: string[]) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/dark-web/settings/engines`, {
                method: 'PUT',
                headers: {
                    ...useAuthStore.getState().getAuthHeader(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ enabled_engines: enabledEngines }),
            });
            if (!res.ok) throw new Error('Failed to update engines');
            await get().fetchEngines();
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },
}));

export default useDarkWebStore;
