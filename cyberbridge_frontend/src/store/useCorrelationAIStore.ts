import { create } from 'zustand';
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

export interface AICorrelationSuggestion {
    question_a_id: string;
    question_b_id: string;
    question_a_text: string;
    question_b_text: string;
    confidence: number;
    reasoning: string;
}

export interface AICorrelationResponse {
    suggestions: AICorrelationSuggestion[];
    framework_a_name: string;
    framework_b_name: string;
    total_suggestions: number;
}

export interface UseCorrelationAIStore {
    // State
    aiSuggestions: AICorrelationResponse | null;
    loading: boolean;
    error: string | null;
    abortController: AbortController | null;

    // Actions
    generateAISuggestions: (
        frameworkAId: string,
        frameworkBId: string,
        assessmentTypeId: string
    ) => Promise<boolean>;
    clearSuggestions: () => void;
    removeSuggestion: (questionAId: string, questionBId: string) => void;
    cancelGeneration: () => void;
}

const useCorrelationAIStore = create<UseCorrelationAIStore>((set, get) => ({
    // State
    aiSuggestions: null,
    loading: false,
    error: null,
    abortController: null,

    // Actions
    generateAISuggestions: async (
        frameworkAId: string,
        frameworkBId: string,
        assessmentTypeId: string
    ) => {
        // Cancel any existing request
        const currentController = get().abortController;
        if (currentController) {
            currentController.abort();
        }

        // Create new AbortController
        const controller = new AbortController();
        set({ loading: true, error: null, abortController: controller });

        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/ai-tools/suggest-correlations`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify({
                        framework_a_id: frameworkAId,
                        framework_b_id: frameworkBId,
                        assessment_type_id: assessmentTypeId
                    }),
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
                return false;
            }

            const data: AICorrelationResponse = await response.json();
            set({
                aiSuggestions: data,
                loading: false,
                error: null,
                abortController: null
            });
            return true;
        } catch (error) {
            // Don't show error if request was aborted
            if (error instanceof Error && error.name === 'AbortError') {
                console.log('AI correlation request was cancelled');
                set({ loading: false, abortController: null });
                return false;
            }

            console.error('Error generating AI suggestions:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to generate AI suggestions',
                loading: false,
                abortController: null
            });
            return false;
        }
    },

    clearSuggestions: () => {
        set({ aiSuggestions: null, error: null });
    },

    removeSuggestion: (questionAId: string, questionBId: string) => {
        const current = get().aiSuggestions;
        if (!current) return;

        const updatedSuggestions = current.suggestions.filter(
            s => !(s.question_a_id === questionAId && s.question_b_id === questionBId)
        );

        set({
            aiSuggestions: {
                ...current,
                suggestions: updatedSuggestions,
                total_suggestions: updatedSuggestions.length
            }
        });
    },

    cancelGeneration: () => {
        const controller = get().abortController;
        if (controller) {
            controller.abort();
        }
        set({ loading: false, abortController: null });
    }
}));

export default useCorrelationAIStore;
