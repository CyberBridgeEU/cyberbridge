import { create } from "zustand";
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

// Evidence type options
export type EvidenceType = 'Screenshot' | 'Report' | 'Log' | 'Export' | 'AI Generated' | 'Document' | 'Other';

// Collection method options
export type CollectionMethod = 'Manual' | 'Automated' | 'AI Generated';

// Evidence status options
export type EvidenceStatus = 'Valid' | 'Expiring' | 'Expired' | 'Pending Review';

// Interfaces for Evidence
export interface Evidence {
    id: string;
    name: string;
    description: string | null;
    evidence_type: EvidenceType;
    file_name: string | null;
    file_url: string | null;
    file_size: number | null;
    framework_ids: string[];
    framework_names: string[];
    control_ids: string[];
    control_names: string[];
    owner: string | null;
    collected_date: string;
    valid_until: string | null;
    status: EvidenceStatus;
    collection_method: CollectionMethod;
    audit_notes: string | null;
    created_at: string;
    updated_at: string;
    organisation_id?: string;
}

export interface EvidenceStore {
    // State
    evidence: Evidence[];
    loading: boolean;
    error: string | null;

    // Actions
    fetchEvidence: () => Promise<boolean>;
    createEvidence: (
        name: string,
        description: string | null,
        evidence_type: EvidenceType,
        framework_ids: string[],
        control_ids: string[],
        owner: string | null,
        collected_date: string,
        valid_until: string | null,
        status: EvidenceStatus,
        collection_method: CollectionMethod,
        audit_notes: string | null,
        file?: File
    ) => Promise<boolean>;
    updateEvidence: (
        id: string,
        name: string,
        description: string | null,
        evidence_type: EvidenceType,
        framework_ids: string[],
        control_ids: string[],
        owner: string | null,
        collected_date: string,
        valid_until: string | null,
        status: EvidenceStatus,
        collection_method: CollectionMethod,
        audit_notes: string | null,
        file?: File
    ) => Promise<boolean>;
    deleteEvidence: (id: string) => Promise<boolean>;

    // Local state management (for when backend is not yet implemented)
    addEvidenceLocal: (evidence: Evidence) => void;
    updateEvidenceLocal: (id: string, updates: Partial<Evidence>) => void;
    deleteEvidenceLocal: (id: string) => void;
}

const useEvidenceStore = create<EvidenceStore>((set, get) => ({
    // State
    evidence: [],
    loading: false,
    error: null,

    // Fetch all evidence
    fetchEvidence: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/evidence`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                // If endpoint doesn't exist yet, return empty array
                if (response.status === 404) {
                    set({ evidence: [], loading: false });
                    return true;
                }
                return false;
            }
            const data = await response.json();
            set({ evidence: data, loading: false });
            return true;
        } catch (error) {
            console.error('Error fetching evidence:', error);
            // Don't show error if backend endpoint doesn't exist yet
            set({ evidence: [], loading: false });
            return true;
        }
    },

    // Create new evidence
    createEvidence: async (
        name: string,
        description: string | null,
        evidence_type: EvidenceType,
        framework_ids: string[],
        control_ids: string[],
        owner: string | null,
        collected_date: string,
        valid_until: string | null,
        status: EvidenceStatus,
        collection_method: CollectionMethod,
        audit_notes: string | null,
        file?: File
    ) => {
        set({ loading: true, error: null });
        try {
            const formData = new FormData();
            formData.append('name', name);
            if (description) formData.append('description', description);
            formData.append('evidence_type', evidence_type);
            formData.append('framework_ids', JSON.stringify(framework_ids));
            formData.append('control_ids', JSON.stringify(control_ids));
            if (owner) formData.append('owner', owner);
            formData.append('collected_date', collected_date);
            if (valid_until) formData.append('valid_until', valid_until);
            formData.append('status', status);
            formData.append('collection_method', collection_method);
            if (audit_notes) formData.append('audit_notes', audit_notes);
            if (file) formData.append('file', file);

            const response = await fetch(`${cyberbridge_back_end_rest_api}/evidence`, {
                method: 'POST',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: formData
            });

            if (!response.ok) {
                return false;
            }

            const newEvidence = await response.json();
            set(state => ({ evidence: [...state.evidence, newEvidence], loading: false }));
            return true;
        } catch (error) {
            console.error('Error creating evidence:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to create evidence',
                loading: false
            });
            return false;
        }
    },

    // Update existing evidence
    updateEvidence: async (
        id: string,
        name: string,
        description: string | null,
        evidence_type: EvidenceType,
        framework_ids: string[],
        control_ids: string[],
        owner: string | null,
        collected_date: string,
        valid_until: string | null,
        status: EvidenceStatus,
        collection_method: CollectionMethod,
        audit_notes: string | null,
        file?: File
    ) => {
        set({ loading: true, error: null });
        try {
            const formData = new FormData();
            formData.append('name', name);
            if (description) formData.append('description', description);
            formData.append('evidence_type', evidence_type);
            formData.append('framework_ids', JSON.stringify(framework_ids));
            formData.append('control_ids', JSON.stringify(control_ids));
            if (owner) formData.append('owner', owner);
            formData.append('collected_date', collected_date);
            if (valid_until) formData.append('valid_until', valid_until);
            formData.append('status', status);
            formData.append('collection_method', collection_method);
            if (audit_notes) formData.append('audit_notes', audit_notes);
            if (file) formData.append('file', file);

            const response = await fetch(`${cyberbridge_back_end_rest_api}/evidence/${id}`, {
                method: 'PUT',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: formData
            });

            if (!response.ok) {
                return false;
            }

            const updatedEvidence = await response.json();
            set(state => ({
                evidence: state.evidence.map(e => e.id === id ? updatedEvidence : e),
                loading: false
            }));
            return true;
        } catch (error) {
            console.error('Error updating evidence:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to update evidence',
                loading: false
            });
            return false;
        }
    },

    // Delete evidence
    deleteEvidence: async (id: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/evidence/${id}`, {
                method: 'DELETE',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                return false;
            }

            set(state => ({
                evidence: state.evidence.filter(e => e.id !== id),
                loading: false
            }));
            return true;
        } catch (error) {
            console.error('Error deleting evidence:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to delete evidence',
                loading: false
            });
            return false;
        }
    },

    // Local state management (for frontend-only operations before backend is ready)
    addEvidenceLocal: (evidence: Evidence) => {
        set(state => ({ evidence: [...state.evidence, evidence] }));
    },

    updateEvidenceLocal: (id: string, updates: Partial<Evidence>) => {
        set(state => ({
            evidence: state.evidence.map(e => e.id === id ? { ...e, ...updates } : e)
        }));
    },

    deleteEvidenceLocal: (id: string) => {
        set(state => ({ evidence: state.evidence.filter(e => e.id !== id) }));
    }
}));

export default useEvidenceStore;
