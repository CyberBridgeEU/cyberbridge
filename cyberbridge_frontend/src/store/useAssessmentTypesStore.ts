// src/store/useAssessmentTypesStore.ts
import { create } from 'zustand';
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

// Assessment Type interface
export interface AssessmentType {
    id: string;
    type_name: string;
    created_at: string;
}

type AssessmentTypesStore = {
    assessmentTypes: AssessmentType[];
    loading: boolean;
    error: string | null;

    // Actions
    fetchAssessmentTypes: () => Promise<boolean>;
    getAssessmentTypeById: (id: string) => AssessmentType | undefined;
    getAssessmentTypeByName: (name: string) => AssessmentType | undefined;
}

const useAssessmentTypesStore = create<AssessmentTypesStore>((set, get) => ({
    // Variables values initialization
    assessmentTypes: [],
    loading: false,
    error: null,

    // Fetch all assessment types
    fetchAssessmentTypes: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assessment-types/`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                set({ assessmentTypes: data, loading: false });
                return true;
            } else {
                set({ error: 'Failed to fetch assessment types', loading: false });
                return false;
            }
        } catch (error) {
            set({ error: 'Network error', loading: false });
            console.error('Error fetching assessment types:', error);
            return false;
        }
    },

    // Get assessment type by ID
    getAssessmentTypeById: (id: string) => {
        return get().assessmentTypes.find(type => type.id === id);
    },

    // Get assessment type by name
    getAssessmentTypeByName: (name: string) => {
        return get().assessmentTypes.find(type => type.type_name === name);
    }
}));

export default useAssessmentTypesStore;