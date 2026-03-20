// src/store/useGuidedTourStore.ts
import { create } from 'zustand';

const TOUR_COMPLETION_KEY = 'cyberbridge_quickstart_tour_completed';
const TOUR_PROGRESS_KEY = 'cyberbridge_quickstart_tour_progress';

interface GuidedTourStore {
    qsIsRunning: boolean;
    qsStepIndex: number;
    qsIsNavigating: boolean;
    startQuickStartTour: () => void;
    stopQuickStartTour: () => void;
    completeQuickStartTour: () => void;
    setQsStepIndex: (index: number) => void;
    setQsIsNavigating: (value: boolean) => void;
}

const useGuidedTourStore = create<GuidedTourStore>((set, get) => ({
    qsIsRunning: false,
    qsStepIndex: 0,
    qsIsNavigating: false,

    startQuickStartTour: () => {
        localStorage.removeItem(TOUR_PROGRESS_KEY);
        set({ qsIsRunning: true, qsStepIndex: 0, qsIsNavigating: false });
    },

    stopQuickStartTour: () => {
        const { qsStepIndex } = get();
        try {
            localStorage.setItem(TOUR_PROGRESS_KEY, JSON.stringify({ stepIndex: qsStepIndex }));
        } catch {
            // ignore storage errors
        }
        set({ qsIsRunning: false, qsIsNavigating: false });
    },

    completeQuickStartTour: () => {
        try {
            localStorage.setItem(TOUR_COMPLETION_KEY, JSON.stringify({
                completed: true,
                completedAt: new Date().toISOString()
            }));
            localStorage.removeItem(TOUR_PROGRESS_KEY);
        } catch {
            // ignore storage errors
        }
        set({ qsIsRunning: false, qsStepIndex: 0, qsIsNavigating: false });
    },

    setQsStepIndex: (index: number) => {
        set({ qsStepIndex: index });
        try {
            localStorage.setItem(TOUR_PROGRESS_KEY, JSON.stringify({ stepIndex: index }));
        } catch {
            // ignore storage errors
        }
    },

    setQsIsNavigating: (value: boolean) => {
        set({ qsIsNavigating: value });
    }
}));

export default useGuidedTourStore;
