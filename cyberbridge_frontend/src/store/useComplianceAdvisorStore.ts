import { create } from 'zustand';
import useAuthStore from './useAuthStore';
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

export interface FrameworkRecommendation {
    template_id: string;
    framework_name: string;
    relevance: 'high' | 'medium' | 'low';
    reasoning: string;
    priority: number;
}

export interface ComplianceAdvisorResult {
    company_summary: string;
    recommendations: FrameworkRecommendation[];
    scraped_pages: number;
}

export interface ComplianceAdvisorHistoryItem {
    id: string;
    scan_target: string;
    summary: string;
    status: string;
    timestamp: string | null;
    user_email: string;
    scan_duration: number | null;
}

interface ComplianceAdvisorStore {
    result: ComplianceAdvisorResult | null;
    loading: boolean;
    error: string | null;
    seedingTemplateId: string | null;
    history: ComplianceAdvisorHistoryItem[];
    historyLoading: boolean;

    analyzeWebsite: (url: string) => Promise<boolean>;
    seedFramework: (templateId: string) => Promise<boolean>;
    clearResult: () => void;
    fetchHistory: () => Promise<void>;
    loadHistoryResult: (id: string) => Promise<void>;
    deleteHistory: (id: string) => Promise<boolean>;
}

const useComplianceAdvisorStore = create<ComplianceAdvisorStore>((set) => ({
    result: null,
    loading: false,
    error: null,
    seedingTemplateId: null,
    history: [],
    historyLoading: false,

    analyzeWebsite: async (url: string) => {
        set({ loading: true, error: null, result: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/compliance-advisor/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({ url })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to analyze website');
            }

            const data = await response.json();
            set({ result: data, loading: false });

            // Auto-refresh history after successful analysis
            useComplianceAdvisorStore.getState().fetchHistory();

            return true;
        } catch (error) {
            console.error('Error analyzing website:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to analyze website',
                loading: false
            });
            return false;
        }
    },

    seedFramework: async (templateId: string) => {
        set({ seedingTemplateId: templateId });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/seed-template?template_id=${encodeURIComponent(templateId)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to seed framework');
            }

            set({ seedingTemplateId: null });
            return true;
        } catch (error) {
            console.error('Error seeding framework:', error);
            set({ seedingTemplateId: null });
            return false;
        }
    },

    clearResult: () => {
        set({ result: null, error: null });
    },

    fetchHistory: async () => {
        set({ historyLoading: true });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/compliance-advisor/history`, {
                headers: useAuthStore.getState().getAuthHeader()
            });
            if (!response.ok) throw new Error('Failed to fetch history');
            const data = await response.json();
            set({ history: data, historyLoading: false });
        } catch (error) {
            console.error('Error fetching compliance advisor history:', error);
            set({ historyLoading: false });
        }
    },

    loadHistoryResult: async (id: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/history/details/${id}`, {
                headers: useAuthStore.getState().getAuthHeader()
            });
            if (!response.ok) throw new Error('Failed to load history result');
            const data = await response.json();
            const parsed = typeof data.results === 'string' ? JSON.parse(data.results) : data.results;
            set({ result: parsed, loading: false });
        } catch (error) {
            console.error('Error loading history result:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to load history result',
                loading: false
            });
        }
    },

    deleteHistory: async (id: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/compliance-advisor/history/${id}`, {
                method: 'DELETE',
                headers: useAuthStore.getState().getAuthHeader()
            });
            if (!response.ok) throw new Error('Failed to delete history');
            // Refresh history list
            useComplianceAdvisorStore.getState().fetchHistory();
            return true;
        } catch (error) {
            console.error('Error deleting compliance advisor history:', error);
            return false;
        }
    },
}));

export default useComplianceAdvisorStore;
