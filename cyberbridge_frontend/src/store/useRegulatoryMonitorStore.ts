import { create } from 'zustand';
import useAuthStore from './useAuthStore';
import { cyberbridge_back_end_rest_api } from '../constants/urls';

interface RegulatoryNotification {
    has_findings: boolean;
    scan_run_id: string | null;
    scan_date: string | null;
    frameworks: string[];
    pending_changes: Record<string, { count: number; scan_run_id: string }>;
}

interface RegulatoryChange {
    id: string;
    scan_run_id: string;
    framework_type: string;
    change_type: string;
    entity_identifier: string | null;
    current_value: string | null;
    proposed_value: string | null;
    source_url: string | null;
    source_excerpt: string | null;
    confidence: number | null;
    llm_reasoning: string | null;
    status: string;
    reviewed_by: string | null;
    reviewed_at: string | null;
    created_at: string | null;
}

interface ScanRun {
    id: string;
    status: string;
    started_at: string | null;
    completed_at: string | null;
    frameworks_scanned: number;
    changes_found: number;
    error_message: string | null;
}

interface Snapshot {
    id: string;
    framework_id: string;
    update_version: number;
    snapshot_type: string;
    created_by: string | null;
    created_at: string | null;
}

interface LLMAnalysisResult {
    status: string;
    prompt?: string;
    changes_count?: number;
    changes?: Array<{
        id: string;
        change_type: string;
        entity_identifier: string;
        confidence: number;
        status: string;
    }>;
}

interface RegulatoryMonitorStore {
    // State
    notification: RegulatoryNotification | null;
    changes: RegulatoryChange[];
    scanRuns: ScanRun[];
    snapshots: Snapshot[];
    llmResult: LLMAnalysisResult | null;
    loading: boolean;
    analyzing: boolean;
    error: string | null;

    // Actions
    fetchNotifications: () => Promise<void>;
    fetchChanges: (frameworkType?: string, status?: string) => Promise<void>;
    fetchScanRuns: () => Promise<void>;
    fetchSnapshots: (frameworkId: string) => Promise<void>;
    triggerLLMAnalysis: (scanRunId: string, frameworkType: string, llmResponse?: string) => Promise<LLMAnalysisResult | null>;
    reviewChange: (changeId: string, status: 'approved' | 'rejected') => Promise<boolean>;
    applyChanges: (changeIds: string[], frameworkId: string) => Promise<boolean>;
    applyToSeed: (changeIds: string[], frameworkType: string, description?: string) => Promise<any>;
    revertToSnapshot: (frameworkId: string, snapshotId: string) => Promise<boolean>;
    triggerScan: () => Promise<boolean>;
    cancelAnalysis: () => void;
}

// AbortController for cancellable LLM analysis
let analysisAbortController: AbortController | null = null;

const useRegulatoryMonitorStore = create<RegulatoryMonitorStore>((set) => ({
    notification: null,
    changes: [],
    scanRuns: [],
    snapshots: [],
    llmResult: null,
    loading: false,
    analyzing: false,
    error: null,

    fetchNotifications: async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/regulatory-monitor/notifications`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.ok) {
                const data = await response.json();
                set({ notification: data });
            }
        } catch (error) {
            console.error('Failed to fetch regulatory notifications:', error);
        }
    },

    fetchChanges: async (frameworkType?: string, status?: string) => {
        set({ loading: true, error: null });
        try {
            const params = new URLSearchParams();
            if (frameworkType) params.append('framework_type', frameworkType);
            if (status) params.append('change_status', status);
            const url = `${cyberbridge_back_end_rest_api}/regulatory-monitor/changes?${params}`;
            const response = await fetch(url, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.ok) {
                const data = await response.json();
                set({ changes: data, loading: false });
            } else {
                set({ loading: false, error: 'Failed to fetch changes' });
            }
        } catch (error) {
            set({ loading: false, error: 'Failed to fetch changes' });
        }
    },

    fetchScanRuns: async () => {
        set({ loading: true });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/regulatory-monitor/scan-runs`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.ok) {
                const data = await response.json();
                set({ scanRuns: data, loading: false });
            } else {
                set({ loading: false });
            }
        } catch (error) {
            set({ loading: false });
        }
    },

    fetchSnapshots: async (frameworkId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/${frameworkId}/snapshots`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.ok) {
                const data = await response.json();
                set({ snapshots: data });
            }
        } catch (error) {
            console.error('Failed to fetch snapshots:', error);
        }
    },

    triggerLLMAnalysis: async (scanRunId: string, frameworkType: string, llmResponse?: string) => {
        // Cancel any previous analysis
        if (analysisAbortController) {
            analysisAbortController.abort();
        }
        analysisAbortController = new AbortController();

        set({ analyzing: true, error: null });
        try {
            const body = llmResponse ? { llm_response: llmResponse } : {};
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/regulatory-monitor/analyze/${scanRunId}/${frameworkType}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify(body),
                    signal: analysisAbortController.signal
                }
            );
            if (response.ok) {
                const data = await response.json();
                set({ llmResult: data, analyzing: false });
                return data;
            } else {
                set({ analyzing: false, error: 'LLM analysis failed' });
                return null;
            }
        } catch (error: any) {
            if (error.name === 'AbortError') {
                set({ analyzing: false, error: null });
                return null;
            }
            set({ analyzing: false, error: 'LLM analysis failed' });
            return null;
        }
    },

    reviewChange: async (changeId: string, status: 'approved' | 'rejected') => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/regulatory-monitor/changes/${changeId}/review`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify({ status })
                }
            );
            if (response.ok) {
                set((state) => ({
                    changes: state.changes.map(c =>
                        c.id === changeId ? { ...c, status } : c
                    )
                }));
                return true;
            }
            return false;
        } catch (error) {
            return false;
        }
    },

    applyChanges: async (changeIds: string[], frameworkId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/regulatory-monitor/changes/apply`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify({ change_ids: changeIds, framework_id: frameworkId })
                }
            );
            if (response.ok) {
                set({ loading: false });
                return true;
            }
            set({ loading: false, error: 'Failed to apply changes' });
            return false;
        } catch (error) {
            set({ loading: false, error: 'Failed to apply changes' });
            return false;
        }
    },

    applyToSeed: async (changeIds: string[], frameworkType: string, description?: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/regulatory-monitor/changes/apply-to-seed`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify({ change_ids: changeIds, framework_type: frameworkType, description })
                }
            );
            if (response.ok) {
                const data = await response.json();
                set({ loading: false });
                return data;
            }
            set({ loading: false, error: 'Failed to write seed file' });
            return null;
        } catch (error) {
            set({ loading: false, error: 'Failed to write seed file' });
            return null;
        }
    },

    revertToSnapshot: async (frameworkId: string, snapshotId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/frameworks/${frameworkId}/snapshots/${snapshotId}/revert`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );
            if (response.ok) {
                set({ loading: false });
                return true;
            }
            set({ loading: false, error: 'Failed to revert snapshot' });
            return false;
        } catch (error) {
            set({ loading: false, error: 'Failed to revert snapshot' });
            return false;
        }
    },

    triggerScan: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/regulatory-monitor/scan`,
                {
                    method: 'POST',
                    headers: { ...useAuthStore.getState().getAuthHeader() }
                }
            );
            if (response.ok) {
                set({ loading: false });
                return true;
            }
            set({ loading: false, error: 'Scan failed' });
            return false;
        } catch (error) {
            set({ loading: false, error: 'Scan failed' });
            return false;
        }
    },

    cancelAnalysis: () => {
        if (analysisAbortController) {
            analysisAbortController.abort();
            analysisAbortController = null;
        }
        set({ analyzing: false, error: null });
    }
}));

export default useRegulatoryMonitorStore;
