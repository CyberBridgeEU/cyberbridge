import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

export interface AdvisoryStatus {
    id: string;
    status_name: string;
}

export interface SecurityAdvisory {
    id: string;
    advisory_code: string | null;
    title: string;
    description: string | null;
    affected_versions: string | null;
    fixed_version: string | null;
    severity: string | null;
    cve_ids: string | null;
    workaround: string | null;
    advisory_status_id: string;
    advisory_status_name: string | null;
    incident_id: string | null;
    incident_code: string | null;
    published_at: string | null;
    organisation_id: string | null;
    created_at: string;
    updated_at: string;
}

interface AdvisoryState {
    advisories: SecurityAdvisory[];
    advisoryStatuses: AdvisoryStatus[];
    loading: boolean;
    error: string | null;
    fetchAdvisories: () => Promise<void>;
    fetchAdvisoryStatuses: () => Promise<void>;
    createAdvisory: (data: any) => Promise<SecurityAdvisory>;
    updateAdvisory: (id: string, data: any) => Promise<void>;
    deleteAdvisory: (id: string) => Promise<void>;
}

const useAdvisoryStore = create<AdvisoryState>((set, get) => ({
    advisories: [],
    advisoryStatuses: [],
    loading: false,
    error: null,

    fetchAdvisories: async () => {
        set({ loading: true, error: null });
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/advisories`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to fetch advisories');
            const data = await res.json();
            set({ advisories: data, loading: false });
        } catch (e: any) {
            set({ error: e.message, loading: false });
        }
    },

    fetchAdvisoryStatuses: async () => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/advisories/statuses`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to fetch advisory statuses');
            const data = await res.json();
            set({ advisoryStatuses: data });
        } catch (e: any) {
            set({ error: e.message });
        }
    },

    createAdvisory: async (data: any) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/advisories`, {
                method: 'POST',
                headers: { ...useAuthStore.getState().getAuthHeader(), 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to create advisory');
            }
            const advisory = await res.json();
            await get().fetchAdvisories();
            return advisory;
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },

    updateAdvisory: async (id: string, data: any) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/advisories/${id}`, {
                method: 'PUT',
                headers: { ...useAuthStore.getState().getAuthHeader(), 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (!res.ok) throw new Error('Failed to update advisory');
            await get().fetchAdvisories();
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },

    deleteAdvisory: async (id: string) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/advisories/${id}`, {
                method: 'DELETE',
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to delete advisory');
            await get().fetchAdvisories();
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },
}));

export default useAdvisoryStore;
