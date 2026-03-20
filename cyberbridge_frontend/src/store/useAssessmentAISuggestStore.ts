import { create } from 'zustand';
import useAuthStore from './useAuthStore';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import type { AnswerSuggestionItem } from './useAssessmentScanSuggestStore';

export interface PlatformDataPreview {
    scan_findings: Array<{ scanner: string; title: string; severity: string; remediated: boolean }>;
    scan_stats: { total?: number; remediated?: number; by_scanner?: Record<string, number>; by_severity?: Record<string, number> };
    policies: Array<{ code: string; title: string; body: string }>;
    objectives: Array<{ chapter: string; title: string; status: string; requirement: string }>;
    answered_evidence: Array<{ question: string; answer: string; evidence_desc: string; files: string }>;
    evidence_library: Array<{ name: string; description: string; type: string }>;
    org_domain: string;
    compliance_advisor: { company_summary: string; recommendations: Array<{ framework: string; relevance: string; reasoning: string }>; analyzed_url: string } | null;
}

interface UseAssessmentAISuggestStore {
    // Wizard state
    platformData: PlatformDataPreview | null;
    gatherLoading: boolean;
    gatherError: string | null;
    wizardStep: number;
    unansweredCount: number;

    // Sequential generation state
    loading: boolean;
    error: string | null;
    abortController: AbortController | null;
    assessmentId: string | null;
    questionQueue: string[];
    queueIndex: number;
    currentSuggestion: AnswerSuggestionItem | null;
    completedCount: number;
    acceptedCount: number;
    skippedCount: number;
    sequentialDone: boolean;

    // Actions
    gatherPlatformData: (assessmentId: string, questionIds?: string[]) => Promise<void>;
    setWizardStep: (step: number) => void;
    startSequentialGeneration: (assessmentId: string, questionIds: string[]) => void;
    processNextInQueue: () => Promise<void>;
    advanceQueue: (accepted: boolean) => void;
    cancelGeneration: () => void;
    resetAll: () => void;
}

const useAssessmentAISuggestStore = create<UseAssessmentAISuggestStore>((set, get) => ({
    // Wizard state
    platformData: null,
    gatherLoading: false,
    gatherError: null,
    wizardStep: 0,
    unansweredCount: 0,

    // Sequential generation state
    loading: false,
    error: null,
    abortController: null,
    assessmentId: null,
    questionQueue: [],
    queueIndex: 0,
    currentSuggestion: null,
    completedCount: 0,
    acceptedCount: 0,
    skippedCount: 0,
    sequentialDone: false,

    gatherPlatformData: async (assessmentId: string, questionIds?: string[]) => {
        set({ gatherLoading: true, gatherError: null, platformData: null, wizardStep: 0 });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/suggestions/gather-platform-data`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify({
                        assessment_id: assessmentId,
                        engine: 'llm',
                        ...(questionIds?.length ? { question_ids: questionIds } : {}),
                    }),
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to gather platform data');
            }

            const data = await response.json();
            set({
                platformData: data.platform_data,
                unansweredCount: data.unanswered_count,
                gatherLoading: false,
                wizardStep: 0,
            });
        } catch (error: any) {
            console.error('Error gathering platform data:', error);
            set({
                gatherError: error.message || 'Failed to gather platform data',
                gatherLoading: false,
            });
        }
    },

    setWizardStep: (step: number) => set({ wizardStep: step }),

    startSequentialGeneration: (assessmentId: string, questionIds: string[]) => {
        set({
            assessmentId,
            questionQueue: questionIds,
            queueIndex: 0,
            currentSuggestion: null,
            completedCount: 0,
            acceptedCount: 0,
            skippedCount: 0,
            sequentialDone: false,
            error: null,
        });
        get().processNextInQueue();
    },

    processNextInQueue: async () => {
        const { questionQueue, assessmentId, platformData } = get();
        let idx = get().queueIndex;

        while (idx < questionQueue.length) {
            const questionId = questionQueue[idx];
            const controller = new AbortController();
            set({ loading: true, error: null, currentSuggestion: null, abortController: controller });

            try {
                const response = await fetch(
                    `${cyberbridge_back_end_rest_api}/suggestions/answers-from-all-sources`,
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            ...useAuthStore.getState().getAuthHeader(),
                        },
                        body: JSON.stringify({
                            assessment_id: assessmentId,
                            engine: 'llm',
                            question_ids: [questionId],
                            ...(platformData ? { platform_data: platformData } : {}),
                        }),
                        signal: controller.signal,
                    }
                );

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || 'Failed to generate suggestion');
                }

                const data = await response.json();

                if (data.suggestions?.length > 0) {
                    // Got a suggestion — show it and wait for user action
                    set({
                        currentSuggestion: data.suggestions[0],
                        loading: false,
                        abortController: null,
                    });
                    return;
                } else {
                    // No suggestion for this question — auto-skip
                    idx++;
                    set({
                        skippedCount: get().skippedCount + 1,
                        queueIndex: idx,
                    });
                }
            } catch (error: any) {
                if (error.name === 'AbortError') {
                    set({ loading: false, abortController: null });
                    return;
                }
                console.error('Error generating suggestion:', error);
                set({
                    error: error.message || 'Failed to generate suggestion',
                    loading: false,
                    abortController: null,
                });
                return;
            }
        }

        // Queue exhausted
        set({ sequentialDone: true, loading: false, currentSuggestion: null });
    },

    advanceQueue: (accepted: boolean) => {
        set(state => ({
            completedCount: state.completedCount + 1,
            acceptedCount: state.acceptedCount + (accepted ? 1 : 0),
            queueIndex: state.queueIndex + 1,
            currentSuggestion: null,
        }));
        get().processNextInQueue();
    },

    cancelGeneration: () => {
        const controller = get().abortController;
        if (controller) controller.abort();

        // Cancel the backend LLM task
        fetch(`${cyberbridge_back_end_rest_api}/scanners/cancel-llm`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...useAuthStore.getState().getAuthHeader(),
            },
        }).catch(() => {});

        set({ loading: false, abortController: null, sequentialDone: true });
    },

    resetAll: () => {
        const controller = get().abortController;
        if (controller) controller.abort();

        set({
            platformData: null,
            gatherLoading: false,
            gatherError: null,
            wizardStep: 0,
            unansweredCount: 0,
            loading: false,
            error: null,
            abortController: null,
            assessmentId: null,
            questionQueue: [],
            queueIndex: 0,
            currentSuggestion: null,
            completedCount: 0,
            acceptedCount: 0,
            skippedCount: 0,
            sequentialDone: false,
        });
    },
}));

export default useAssessmentAISuggestStore;
