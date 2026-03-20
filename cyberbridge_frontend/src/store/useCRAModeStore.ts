// src/store/useCRAModeStore.ts
import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

type CRAModeValue = 'focused' | 'extended' | null;

interface CRAModeStore {
    craMode: CRAModeValue;
    craOperatorRole: string | null; // 'Manufacturer' | 'Importer' | 'Distributor' | null
    loading: boolean;
    setCRAMode: (mode: CRAModeValue) => void;
    setCRAOperatorRole: (role: string | null) => void;
    fetchCRAMode: (organisationId: string) => Promise<void>;
    saveCRAMode: (organisationId: string, mode: CRAModeValue) => Promise<void>;
    saveCRAOperatorRole: (organisationId: string, role: string | null) => Promise<void>;
}

const useCRAModeStore = create<CRAModeStore>((set) => ({
    craMode: null,
    craOperatorRole: null,
    loading: false,
    setCRAMode: (mode: CRAModeValue) => {
        if (mode === null) {
            set({ craMode: null, craOperatorRole: null });
        } else {
            set({ craMode: mode });
        }
    },
    setCRAOperatorRole: (role: string | null) => {
        set({ craOperatorRole: role });
    },
    fetchCRAMode: async (organisationId: string) => {
        try {
            set({ loading: true });
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/org-cra-mode/${organisationId}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...authHeader
                }
            });
            if (response.ok) {
                const data = await response.json();
                set({
                    craMode: data.cra_mode || null,
                    craOperatorRole: data.cra_operator_role ?? null
                });
            }
        } catch (error) {
            console.error('Failed to fetch CRA mode:', error);
        } finally {
            set({ loading: false });
        }
    },
    saveCRAMode: async (organisationId: string, mode: CRAModeValue) => {
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/org-cra-mode/${organisationId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...authHeader
                },
                body: JSON.stringify({ cra_mode: mode ?? '' })
            });
            if (response.ok) {
                const data = await response.json();
                set({
                    craMode: data.cra_mode || null,
                    craOperatorRole: data.cra_operator_role
                });
            }
        } catch (error) {
            console.error('Failed to save CRA mode:', error);
        }
    },
    saveCRAOperatorRole: async (organisationId: string, role: string | null) => {
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/org-cra-mode/${organisationId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...authHeader
                },
                body: JSON.stringify({ cra_operator_role: role || '' })
            });
            if (response.ok) {
                const data = await response.json();
                set({
                    craOperatorRole: data.cra_operator_role
                });
            }
        } catch (error) {
            console.error('Failed to save CRA operator role:', error);
        }
    },
}));

export default useCRAModeStore;
