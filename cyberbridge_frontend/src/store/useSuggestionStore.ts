import { create } from 'zustand';
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

export interface SuggestionItem {
    item_id: string;
    display_name: string;
    confidence: number;
    reasoning: string;
}

export interface SuggestionResponse {
    suggestions: SuggestionItem[];
    engine: string;
    entity_id: string;
    total_suggestions: number;
}

type TabKey = 'asset-risk' | 'risk-control' | 'control-policy' | 'policy-objective';

interface TabState {
    suggestions: SuggestionItem[];
    loading: boolean;
    error: string | null;
    abortController: AbortController | null;
}

const defaultTabState: TabState = {
    suggestions: [],
    loading: false,
    error: null,
    abortController: null,
};

interface SuggestionStoreState {
    tabs: Record<TabKey, TabState>;
    engine: 'rule' | 'llm';

    setEngine: (engine: 'rule' | 'llm') => void;
    fetchSuggestions: (
        tab: TabKey,
        entityId: string,
        frameworkId?: string,
        availableItemIds?: string[],
    ) => Promise<boolean>;
    clearSuggestions: (tab: TabKey) => void;
    cancelRequest: (tab: TabKey) => void;
    cancelAllRequests: () => void;
}

const TAB_ENDPOINTS: Record<TabKey, string> = {
    'asset-risk': '/suggestions/risks-for-asset',
    'risk-control': '/suggestions/controls-for-risk',
    'control-policy': '/suggestions/policies-for-control',
    'policy-objective': '/suggestions/objectives-for-policy',
};

const useSuggestionStore = create<SuggestionStoreState>((set, get) => ({
    tabs: {
        'asset-risk': { ...defaultTabState },
        'risk-control': { ...defaultTabState },
        'control-policy': { ...defaultTabState },
        'policy-objective': { ...defaultTabState },
    },
    engine: 'rule',

    setEngine: (engine) => set({ engine }),

    fetchSuggestions: async (tab, entityId, frameworkId, availableItemIds) => {
        // Cancel any existing request for this tab
        const currentController = get().tabs[tab].abortController;
        if (currentController) {
            currentController.abort();
        }

        const controller = new AbortController();
        set((state) => ({
            tabs: {
                ...state.tabs,
                [tab]: { ...state.tabs[tab], loading: true, error: null, abortController: controller },
            },
        }));

        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}${TAB_ENDPOINTS[tab]}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader(),
                    },
                    body: JSON.stringify({
                        entity_id: entityId,
                        engine: get().engine,
                        framework_id: frameworkId || null,
                        available_item_ids: availableItemIds || null,
                    }),
                    signal: controller.signal,
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
                set((state) => ({
                    tabs: {
                        ...state.tabs,
                        [tab]: {
                            suggestions: [],
                            loading: false,
                            error: errorData.detail || 'Failed to get suggestions',
                            abortController: null,
                        },
                    },
                }));
                return false;
            }

            const data: SuggestionResponse = await response.json();
            set((state) => ({
                tabs: {
                    ...state.tabs,
                    [tab]: {
                        suggestions: data.suggestions,
                        loading: false,
                        error: null,
                        abortController: null,
                    },
                },
            }));
            return true;
        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                set((state) => ({
                    tabs: {
                        ...state.tabs,
                        [tab]: { ...state.tabs[tab], loading: false, abortController: null },
                    },
                }));
                return false;
            }

            set((state) => ({
                tabs: {
                    ...state.tabs,
                    [tab]: {
                        suggestions: [],
                        loading: false,
                        error: error instanceof Error ? error.message : 'Failed to get suggestions',
                        abortController: null,
                    },
                },
            }));
            return false;
        }
    },

    clearSuggestions: (tab) => {
        const currentController = get().tabs[tab].abortController;
        if (currentController) {
            currentController.abort();
        }
        set((state) => ({
            tabs: {
                ...state.tabs,
                [tab]: { ...defaultTabState },
            },
        }));
    },

    cancelRequest: (tab) => {
        const controller = get().tabs[tab].abortController;
        if (controller) {
            controller.abort();
        }
        set((state) => ({
            tabs: {
                ...state.tabs,
                [tab]: { ...state.tabs[tab], loading: false, abortController: null },
            },
        }));
    },

    cancelAllRequests: () => {
        const { tabs } = get();
        const tabKeys = Object.keys(tabs) as TabKey[];
        for (const tab of tabKeys) {
            const controller = tabs[tab].abortController;
            if (controller) {
                controller.abort();
            }
        }
        set((state) => {
            const updated = { ...state.tabs };
            for (const tab of tabKeys) {
                updated[tab] = { ...defaultTabState };
            }
            return { tabs: updated };
        });
    },
}));

export default useSuggestionStore;
