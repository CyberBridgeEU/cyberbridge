import { create } from 'zustand';
import useAuthStore from './useAuthStore';
import { cyberbridge_back_end_rest_api } from '../constants/urls';

export interface ObjectiveAISuggestion {
    objective_id: string;
    objective_title: string;
    recommended_status: string;
    confidence: number;
    supporting_evidence: string[];
    gaps: string[];
    recommended_policies: string[];
    suggested_body: string;
}

export interface ObjectivesAIResponse {
    success: boolean;
    objectives_count: number;
    framework_name: string;
    suggestions: ObjectiveAISuggestion[];
    timestamp: string;
}

export interface UseObjectivesAIStore {
    // State
    aiSuggestions: ObjectivesAIResponse | null;
    loading: boolean;
    error: string | null;
    abortController: AbortController | null;

    // Actions
    generateAISuggestions: (frameworkId: string) => Promise<ObjectivesAIResponse | null>;
    clearSuggestions: () => void;
    removeSuggestion: (objectiveId: string) => void;
}

const useObjectivesAIStore = create<UseObjectivesAIStore>((set, get) => ({
    // Initial State
    aiSuggestions: null,
    loading: false,
    error: null,
    abortController: null,

    // Generate AI suggestions for objectives
    generateAISuggestions: async (frameworkId: string) => {
        // Cancel any existing request
        const currentController = get().abortController;
        if (currentController) {
            currentController.abort();
        }

        // Create new AbortController for this request
        const controller = new AbortController();
        set({ loading: true, error: null, abortController: controller });

        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/objectives/analyze_with_ai`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify({ id: frameworkId }),
                    signal: controller.signal
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to generate AI suggestions',
                    loading: false,
                    abortController: null
                });
                return null;
            }

            const data: ObjectivesAIResponse = await response.json();
            set({
                aiSuggestions: data,
                loading: false,
                error: null,
                abortController: null
            });
            return data;

        } catch (error: any) {
            // Don't show error if request was aborted (user navigated away or started new request)
            if (error.name === 'AbortError') {
                console.log('AI suggestions request was aborted');
                set({ loading: false, abortController: null });
                return null;
            }

            console.error('Error generating AI suggestions:', error);
            set({
                error: error.message || 'Failed to generate AI suggestions',
                loading: false,
                abortController: null
            });
            return null;
        }
    },

    // Clear all suggestions
    clearSuggestions: () => {
        set({
            aiSuggestions: null,
            error: null
        });
    },

    // Remove a specific suggestion from the list
    removeSuggestion: (objectiveId: string) => {
        const currentSuggestions = get().aiSuggestions;
        if (!currentSuggestions) return;

        const updatedSuggestions = {
            ...currentSuggestions,
            suggestions: currentSuggestions.suggestions.filter(
                (suggestion) => suggestion.objective_id !== objectiveId
            )
        };

        set({ aiSuggestions: updatedSuggestions });
    }
}));

export default useObjectivesAIStore;
