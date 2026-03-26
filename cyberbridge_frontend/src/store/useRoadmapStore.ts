import { create } from 'zustand';
import useAuthStore from './useAuthStore';
import { cyberbridge_back_end_rest_api } from '../constants/urls';

export interface RoadmapActionStep {
    step_number: number;
    title: string;
    description: string;
    priority: string;
    estimated_effort: string;
    category: string;
    platform_action: string | null;
    references: string[];
}

export interface RoadmapData {
    objective_id: string;
    objective_title: string;
    current_status: string;
    target_status: string;
    gap_summary: string;
    action_steps: RoadmapActionStep[];
    estimated_total_effort: string;
    quick_wins: string[];
    dependencies: string[];
    risk_if_unaddressed: string;
}

interface RoadmapResponse {
    success: boolean;
    roadmap?: RoadmapData;
    error?: string;
}

interface BulkRoadmapResponse {
    success: boolean;
    roadmaps?: RoadmapData[];
    total?: number;
    error?: string;
}

interface UseRoadmapStore {
    roadmap: RoadmapData | null;
    bulkRoadmaps: RoadmapData[];
    loading: boolean;
    bulkLoading: boolean;
    error: string | null;
    abortController: AbortController | null;

    generateRoadmap: (objectiveId: string, frameworkId: string) => Promise<RoadmapData | null>;
    generateBulkRoadmap: (frameworkId: string, objectiveIds: string[]) => Promise<RoadmapData[]>;
    clearRoadmap: () => void;
    clearBulkRoadmaps: () => void;
}

const useRoadmapStore = create<UseRoadmapStore>((set, get) => ({
    roadmap: null,
    bulkRoadmaps: [],
    loading: false,
    bulkLoading: false,
    error: null,
    abortController: null,

    generateRoadmap: async (objectiveId: string, frameworkId: string) => {
        const currentController = get().abortController;
        if (currentController) {
            currentController.abort();
        }

        const controller = new AbortController();
        set({ loading: true, error: null, roadmap: null, abortController: controller });

        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/objectives/roadmap/${objectiveId}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify({ framework_id: frameworkId }),
                    signal: controller.signal
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to generate roadmap',
                    loading: false,
                    abortController: null
                });
                return null;
            }

            const data: RoadmapResponse = await response.json();
            if (!data.success) {
                set({
                    error: data.error || 'Failed to generate roadmap',
                    loading: false,
                    abortController: null
                });
                return null;
            }

            set({
                roadmap: data.roadmap || null,
                loading: false,
                error: null,
                abortController: null
            });
            return data.roadmap || null;

        } catch (error: any) {
            if (error.name === 'AbortError') {
                set({ loading: false, abortController: null });
                return null;
            }
            set({
                error: error.message || 'Failed to generate roadmap',
                loading: false,
                abortController: null
            });
            return null;
        }
    },

    generateBulkRoadmap: async (frameworkId: string, objectiveIds: string[]) => {
        set({ bulkLoading: true, error: null, bulkRoadmaps: [] });

        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/objectives/roadmap/bulk`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify({ framework_id: frameworkId, objective_ids: objectiveIds })
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to generate bulk roadmap',
                    bulkLoading: false
                });
                return [];
            }

            const data: BulkRoadmapResponse = await response.json();
            if (!data.success) {
                set({
                    error: data.error || 'Failed to generate bulk roadmap',
                    bulkLoading: false
                });
                return [];
            }

            const roadmaps = data.roadmaps || [];
            set({ bulkRoadmaps: roadmaps, bulkLoading: false, error: null });
            return roadmaps;

        } catch (error: any) {
            set({
                error: error.message || 'Failed to generate bulk roadmap',
                bulkLoading: false
            });
            return [];
        }
    },

    clearRoadmap: () => {
        const controller = get().abortController;
        if (controller) controller.abort();
        set({ roadmap: null, error: null, loading: false, abortController: null });
    },

    clearBulkRoadmaps: () => {
        set({ bulkRoadmaps: [], error: null, bulkLoading: false });
    }
}));

export default useRoadmapStore;
