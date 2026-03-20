import { create } from "zustand";
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

// Risk with latest assessment data (for list view)
export interface RiskWithAssessment {
    id: string;
    risk_code: string | null;
    risk_category_name: string;
    risk_category_description: string | null;
    assessment_status: string | null;
    organisation_id: string | null;
    risk_severity: string | null;
    inherent_risk_score: number | null;
    current_risk_score: number | null;
    target_risk_score: number | null;
    residual_risk_score: number | null;
    inherent_severity: string | null;
    current_severity: string | null;
    target_severity: string | null;
    residual_severity: string | null;
    last_assessed_at: string | null;
    assessment_count: number;
}

// Treatment action
export interface TreatmentAction {
    id: string;
    assessment_id: string;
    description: string;
    due_date: string | null;
    owner: string | null;
    status: string;
    completion_notes: string | null;
    completed_at: string | null;
    created_at: string;
    updated_at: string;
}

// Full assessment
export interface RiskAssessment {
    id: string;
    risk_id: string;
    assessment_number: number;
    description: string | null;
    inherent_impact: number;
    inherent_likelihood: number;
    inherent_risk_score: number;
    current_impact: number;
    current_likelihood: number;
    current_risk_score: number;
    target_impact: number | null;
    target_likelihood: number | null;
    target_risk_score: number | null;
    residual_impact: number | null;
    residual_likelihood: number | null;
    residual_risk_score: number | null;
    impact_health: string | null;
    impact_financial: string | null;
    impact_service: string | null;
    impact_legal: string | null;
    impact_reputation: string | null;
    status: string;
    organisation_id: string;
    assessed_by: string;
    created_at: string;
    updated_at: string;
    inherent_severity: string | null;
    current_severity: string | null;
    target_severity: string | null;
    residual_severity: string | null;
    assessed_by_email: string | null;
    risk_code: string | null;
    risk_category_name: string | null;
    treatment_actions?: TreatmentAction[];
}

interface RiskAssessmentStore {
    // State
    risks: RiskWithAssessment[];
    assessments: RiskAssessment[];
    currentAssessment: RiskAssessment | null;
    loading: boolean;
    error: string | null;

    // Actions
    fetchRisksWithAssessments: () => Promise<boolean>;
    fetchAssessments: (riskId: string) => Promise<void>;
    fetchLatestAssessment: (riskId: string) => Promise<void>;
    fetchAssessment: (riskId: string, assessmentId: string) => Promise<void>;
    createAssessment: (riskId: string, data: Partial<RiskAssessment>) => Promise<boolean>;
    updateAssessment: (riskId: string, assessmentId: string, data: Partial<RiskAssessment>) => Promise<boolean>;
    deleteAssessment: (riskId: string, assessmentId: string) => Promise<boolean>;
    // Treatment actions
    createAction: (riskId: string, assessmentId: string, data: Partial<TreatmentAction>) => Promise<boolean>;
    updateAction: (riskId: string, assessmentId: string, actionId: string, data: Partial<TreatmentAction>) => Promise<boolean>;
    deleteAction: (riskId: string, assessmentId: string, actionId: string) => Promise<boolean>;
}

const useRiskAssessmentStore = create<RiskAssessmentStore>((set) => ({
    risks: [],
    assessments: [],
    currentAssessment: null,
    loading: false,
    error: null,

    fetchRisksWithAssessments: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/assessments`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (!response.ok) {
                set({ loading: false });
                return false;
            }
            const data = await response.json();
            set({ risks: data, loading: false });
            return true;
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to fetch risks', loading: false });
            return false;
        }
    },

    fetchAssessments: async (riskId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/assessments`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (!response.ok) throw new Error('Failed to fetch assessments');
            const data = await response.json();
            const current = useRiskAssessmentStore.getState().currentAssessment;
            // Only reset currentAssessment if it belongs to a different risk or doesn't exist
            const needsReset = !current || current.risk_id !== riskId;
            if (needsReset) {
                set({
                    assessments: data,
                    currentAssessment: data.length > 0 ? data[0] : null,
                    loading: false
                });
            } else {
                set({ assessments: data, loading: false });
            }
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to fetch assessments', loading: false, assessments: [] });
        }
    },

    fetchLatestAssessment: async (riskId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/assessments/latest`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.status === 404) {
                set({ currentAssessment: null, loading: false });
                return;
            }
            if (!response.ok) throw new Error('Failed to fetch latest assessment');
            const data = await response.json();
            set({ currentAssessment: data, loading: false });
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to fetch latest assessment', loading: false, currentAssessment: null });
        }
    },

    fetchAssessment: async (riskId: string, assessmentId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/assessments/${assessmentId}`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (!response.ok) throw new Error('Failed to fetch assessment');
            const data = await response.json();
            set({ currentAssessment: data, loading: false });
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to fetch assessment', loading: false });
        }
    },

    createAssessment: async (riskId: string, data: Partial<RiskAssessment>) => {
        set({ error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/assessments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...useAuthStore.getState().getAuthHeader() },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                set({ error: err.detail || 'Failed to create assessment' });
                return false;
            }
            const newAssessment = await response.json();
            set({ currentAssessment: newAssessment });
            return true;
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to create assessment' });
            return false;
        }
    },

    updateAssessment: async (riskId: string, assessmentId: string, data: Partial<RiskAssessment>) => {
        set({ error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/assessments/${assessmentId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...useAuthStore.getState().getAuthHeader() },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                set({ error: err.detail || 'Failed to update assessment' });
                return false;
            }
            const updated = await response.json();
            set({ currentAssessment: updated });
            return true;
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to update assessment' });
            return false;
        }
    },

    deleteAssessment: async (riskId: string, assessmentId: string) => {
        set({ error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/assessments/${assessmentId}`, {
                method: 'DELETE',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (!response.ok) return false;
            set(state => ({
                assessments: state.assessments.filter(a => a.id !== assessmentId),
                currentAssessment: state.currentAssessment?.id === assessmentId ? null : state.currentAssessment
            }));
            return true;
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to delete assessment' });
            return false;
        }
    },

    createAction: async (riskId: string, assessmentId: string, data: Partial<TreatmentAction>) => {
        set({ error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/assessments/${assessmentId}/actions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...useAuthStore.getState().getAuthHeader() },
                body: JSON.stringify(data)
            });
            if (!response.ok) return false;
            const newAction = await response.json();
            set(state => ({
                currentAssessment: state.currentAssessment ? {
                    ...state.currentAssessment,
                    treatment_actions: [...(state.currentAssessment.treatment_actions || []), newAction]
                } : null
            }));
            return true;
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to create action' });
            return false;
        }
    },

    updateAction: async (riskId: string, assessmentId: string, actionId: string, data: Partial<TreatmentAction>) => {
        set({ error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/assessments/${assessmentId}/actions/${actionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...useAuthStore.getState().getAuthHeader() },
                body: JSON.stringify(data)
            });
            if (!response.ok) return false;
            const updated = await response.json();
            set(state => ({
                currentAssessment: state.currentAssessment ? {
                    ...state.currentAssessment,
                    treatment_actions: (state.currentAssessment.treatment_actions || []).map(a => a.id === actionId ? updated : a)
                } : null
            }));
            return true;
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to update action' });
            return false;
        }
    },

    deleteAction: async (riskId: string, assessmentId: string, actionId: string) => {
        set({ error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/assessments/${assessmentId}/actions/${actionId}`, {
                method: 'DELETE',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (!response.ok) return false;
            set(state => ({
                currentAssessment: state.currentAssessment ? {
                    ...state.currentAssessment,
                    treatment_actions: (state.currentAssessment.treatment_actions || []).filter(a => a.id !== actionId)
                } : null
            }));
            return true;
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to delete action' });
            return false;
        }
    }
}));

export default useRiskAssessmentStore;
