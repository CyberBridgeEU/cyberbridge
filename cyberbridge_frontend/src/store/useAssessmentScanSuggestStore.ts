import { create } from 'zustand';
import useAuthStore from './useAuthStore';
import { cyberbridge_back_end_rest_api } from '../constants/urls';

export interface AnswerSuggestionItem {
    question_id: string;
    question_text: string;
    question_number: number;
    suggested_answer: string;       // "yes", "no", "partially", "n/a"
    evidence_description: string;
    confidence: number;             // 0-100
    reasoning: string;
}

export interface AssessmentAnswerSuggestionResponse {
    suggestions: AnswerSuggestionItem[];
    engine: string;
    assessment_id: string;
    total_questions: number;
    total_suggestions: number;
}

export interface UseAssessmentScanSuggestStore {
    // State
    suggestions: AssessmentAnswerSuggestionResponse | null;
    loading: boolean;
    error: string | null;
    abortController: AbortController | null;

    // Actions
    fetchSuggestions: (assessmentId: string, engine: string) => Promise<AssessmentAnswerSuggestionResponse | null>;
    clearSuggestions: () => void;
    removeSuggestion: (questionId: string) => void;
    cancelGeneration: () => void;
}

const useAssessmentScanSuggestStore = create<UseAssessmentScanSuggestStore>((set, get) => ({
    // Initial State
    suggestions: null,
    loading: false,
    error: null,
    abortController: null,

    fetchSuggestions: async (assessmentId: string, engine: string) => {
        // Cancel any existing request
        const currentController = get().abortController;
        if (currentController) {
            currentController.abort();
        }

        const controller = new AbortController();
        set({ loading: true, error: null, abortController: controller });

        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/suggestions/answers-from-scans`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify({
                        assessment_id: assessmentId,
                        engine: engine,
                    }),
                    signal: controller.signal
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to generate suggestions',
                    loading: false,
                    abortController: null
                });
                return null;
            }

            const data: AssessmentAnswerSuggestionResponse = await response.json();
            set({
                suggestions: data,
                loading: false,
                error: null,
                abortController: null
            });
            return data;

        } catch (error: any) {
            if (error.name === 'AbortError') {
                console.log('Scan suggestions request was aborted');
                set({ loading: false, abortController: null });
                return null;
            }

            console.error('Error generating scan suggestions:', error);
            set({
                error: error.message || 'Failed to generate suggestions',
                loading: false,
                abortController: null
            });
            return null;
        }
    },

    clearSuggestions: () => {
        set({ suggestions: null, error: null });
    },

    removeSuggestion: (questionId: string) => {
        const current = get().suggestions;
        if (!current) return;

        set({
            suggestions: {
                ...current,
                suggestions: current.suggestions.filter(
                    (s) => s.question_id !== questionId
                ),
                total_suggestions: current.suggestions.filter(
                    (s) => s.question_id !== questionId
                ).length,
            }
        });
    },

    cancelGeneration: () => {
        const controller = get().abortController;
        if (controller) {
            controller.abort();
        }
        set({ loading: false, abortController: null });
    },
}));

export default useAssessmentScanSuggestStore;
