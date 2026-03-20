// src/store/useUserOnboardingStore.ts
import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

// LocalStorage keys for persistence
const USER_ONBOARDING_PROGRESS_KEY = 'cyberbridge_user_onboarding_progress';
const USER_ONBOARDING_STATUS_KEY = 'cyberbridge_user_onboarding_status';

export interface UserOnboardingProgress {
    currentStep: number;
    viewedFeatures: string[];
    viewedFrameworks: string[];
}

interface UserOnboardingStatus {
    user_onboarding_completed: boolean;
    user_onboarding_skipped: boolean;
    user_onboarding_completed_at: string | null;
}

interface OnboardingStatusResponse {
    onboarding_completed: boolean;
    onboarding_skipped: boolean;
    onboarding_completed_at: string | null;
    is_admin?: boolean;
}

interface UserOnboardingStore {
    // Wizard state
    isWizardOpen: boolean;
    currentStep: number;
    loading: boolean;
    error: string | null;

    // Wizard data
    viewedFeatures: string[];
    viewedFrameworks: string[];

    // Onboarding status
    onboardingStatus: UserOnboardingStatus | null;

    // Actions
    openWizard: () => void;
    closeWizard: () => void;
    nextStep: () => void;
    prevStep: () => void;
    setStep: (step: number) => void;

    // Data setters
    setViewedFeatures: (features: string[]) => void;
    addViewedFeature: (feature: string) => void;
    setViewedFrameworks: (frameworks: string[]) => void;
    addViewedFramework: (framework: string) => void;

    // API actions
    checkOnboardingStatus: () => Promise<UserOnboardingStatus | null>;
    completeOnboarding: () => Promise<boolean>;
    skipOnboarding: () => Promise<boolean>;
    resetOnboarding: () => void;

    // Progress persistence
    saveProgressToStorage: () => void;
    loadProgressFromStorage: () => void;
    clearProgressFromStorage: () => void;
}

const useUserOnboardingStore = create<UserOnboardingStore>((set, get) => ({
    // Initial state
    isWizardOpen: false,
    currentStep: 0,
    loading: false,
    error: null,
    viewedFeatures: [],
    viewedFrameworks: [],
    onboardingStatus: null,

    // Wizard visibility actions
    openWizard: () => {
        get().loadProgressFromStorage();
        set({ isWizardOpen: true });
    },

    closeWizard: () => {
        get().saveProgressToStorage();
        set({ isWizardOpen: false });
    },

    // Step navigation (4 steps: 0-3)
    nextStep: () => {
        const { currentStep } = get();
        const newStep = Math.min(currentStep + 1, 3);
        set({ currentStep: newStep });
        get().saveProgressToStorage();
    },

    prevStep: () => {
        const { currentStep } = get();
        const newStep = Math.max(currentStep - 1, 0);
        set({ currentStep: newStep });
        get().saveProgressToStorage();
    },

    setStep: (step: number) => {
        set({ currentStep: Math.max(0, Math.min(step, 3)) });
        get().saveProgressToStorage();
    },

    // Data setters
    setViewedFeatures: (features: string[]) => {
        set({ viewedFeatures: features });
        get().saveProgressToStorage();
    },

    addViewedFeature: (feature: string) => {
        const { viewedFeatures } = get();
        if (!viewedFeatures.includes(feature)) {
            set({ viewedFeatures: [...viewedFeatures, feature] });
            get().saveProgressToStorage();
        }
    },

    setViewedFrameworks: (frameworks: string[]) => {
        set({ viewedFrameworks: frameworks });
        get().saveProgressToStorage();
    },

    addViewedFramework: (framework: string) => {
        const { viewedFrameworks } = get();
        if (!viewedFrameworks.includes(framework)) {
            set({ viewedFrameworks: [...viewedFrameworks, framework] });
            get().saveProgressToStorage();
        }
    },

    // API actions
    checkOnboardingStatus: async () => {
        try {
            set({ loading: true, error: null });

            // First check localStorage for completion status
            const savedStatus = localStorage.getItem(USER_ONBOARDING_STATUS_KEY);
            if (savedStatus) {
                const status: UserOnboardingStatus = JSON.parse(savedStatus);
                // If already completed or skipped locally, don't show wizard
                if (status.user_onboarding_completed || status.user_onboarding_skipped) {
                    set({ onboardingStatus: status, loading: false });
                    return status;
                }
            }

            // Try to fetch from API
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(`${cyberbridge_back_end_rest_api}/onboarding/status`, {
                headers: {
                    ...authHeader
                }
            });

            if (!response.ok) {
                // If endpoint doesn't exist, check localStorage or default to not completed for first-time users
                if (response.status === 404) {
                    // If no localStorage status exists, this is first login - show wizard
                    const status: UserOnboardingStatus = savedStatus
                        ? JSON.parse(savedStatus)
                        : {
                            user_onboarding_completed: false,
                            user_onboarding_skipped: false,
                            user_onboarding_completed_at: null
                        };
                    set({ onboardingStatus: status, loading: false });
                    return status;
                }
                throw new Error('Failed to fetch user onboarding status');
            }

            const apiStatus: OnboardingStatusResponse = await response.json();
            const status: UserOnboardingStatus = {
                user_onboarding_completed: apiStatus.onboarding_completed,
                user_onboarding_skipped: apiStatus.onboarding_skipped,
                user_onboarding_completed_at: apiStatus.onboarding_completed_at
            };
            // Save to localStorage for future checks
            localStorage.setItem(USER_ONBOARDING_STATUS_KEY, JSON.stringify(status));
            set({ onboardingStatus: status, loading: false });
            return status;
        } catch (error) {
            console.error('Error checking user onboarding status:', error);
            // Check localStorage first, then default to completed to avoid showing wizard on errors
            const savedStatus = localStorage.getItem(USER_ONBOARDING_STATUS_KEY);
            const status: UserOnboardingStatus = savedStatus
                ? JSON.parse(savedStatus)
                : {
                    user_onboarding_completed: true, // Default to completed on error to avoid annoying users
                    user_onboarding_skipped: false,
                    user_onboarding_completed_at: null
                };
            set({
                onboardingStatus: status,
                error: error instanceof Error ? error.message : 'Failed to check onboarding status',
                loading: false
            });
            return status;
        }
    },

    completeOnboarding: async () => {
        try {
            set({ loading: true, error: null });
            const authHeader = useAuthStore.getState().getAuthHeader();

            const response = await fetch(`${cyberbridge_back_end_rest_api}/onboarding/complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...authHeader
                }
            });

            // If endpoint doesn't exist, just complete locally
            if (!response.ok && response.status !== 404) {
                throw new Error('Failed to complete user onboarding');
            }

            // Clear progress from storage
            get().clearProgressFromStorage();

            const completedStatus: UserOnboardingStatus = {
                user_onboarding_completed: true,
                user_onboarding_skipped: false,
                user_onboarding_completed_at: new Date().toISOString()
            };

            // Save completion status to localStorage
            localStorage.setItem(USER_ONBOARDING_STATUS_KEY, JSON.stringify(completedStatus));

            // Reset wizard state
            set({
                loading: false,
                isWizardOpen: false,
                currentStep: 0,
                viewedFeatures: [],
                viewedFrameworks: [],
                onboardingStatus: completedStatus
            });

            return true;
        } catch (error) {
            console.error('Error completing user onboarding:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to complete onboarding',
                loading: false
            });
            return false;
        }
    },

    skipOnboarding: async () => {
        try {
            set({ loading: true, error: null });
            const authHeader = useAuthStore.getState().getAuthHeader();

            const response = await fetch(`${cyberbridge_back_end_rest_api}/onboarding/skip`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...authHeader
                }
            });

            // If endpoint doesn't exist, just skip locally
            if (!response.ok && response.status !== 404) {
                throw new Error('Failed to skip user onboarding');
            }

            // Clear progress from storage
            get().clearProgressFromStorage();

            const skippedStatus: UserOnboardingStatus = {
                user_onboarding_completed: true,
                user_onboarding_skipped: true,
                user_onboarding_completed_at: new Date().toISOString()
            };

            // Save skipped status to localStorage
            localStorage.setItem(USER_ONBOARDING_STATUS_KEY, JSON.stringify(skippedStatus));

            // Reset wizard state
            set({
                loading: false,
                isWizardOpen: false,
                currentStep: 0,
                viewedFeatures: [],
                viewedFrameworks: [],
                onboardingStatus: skippedStatus
            });

            return true;
        } catch (error) {
            console.error('Error skipping user onboarding:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to skip onboarding',
                loading: false
            });
            return false;
        }
    },

    resetOnboarding: () => {
        // Reset to initial state (local only, no API call needed for users)
        get().clearProgressFromStorage();
        // Also clear status from localStorage so wizard can show again
        localStorage.removeItem(USER_ONBOARDING_STATUS_KEY);
        set({
            loading: false,
            currentStep: 0,
            viewedFeatures: [],
            viewedFrameworks: [],
            onboardingStatus: {
                user_onboarding_completed: false,
                user_onboarding_skipped: false,
                user_onboarding_completed_at: null
            }
        });
    },

    // Progress persistence
    saveProgressToStorage: () => {
        const { currentStep, viewedFeatures, viewedFrameworks } = get();
        const progress: UserOnboardingProgress = {
            currentStep,
            viewedFeatures,
            viewedFrameworks
        };
        try {
            localStorage.setItem(USER_ONBOARDING_PROGRESS_KEY, JSON.stringify(progress));
        } catch (error) {
            console.error('Error saving user onboarding progress:', error);
        }
    },

    loadProgressFromStorage: () => {
        try {
            const saved = localStorage.getItem(USER_ONBOARDING_PROGRESS_KEY);
            if (saved) {
                const progress: UserOnboardingProgress = JSON.parse(saved);
                set({
                    currentStep: progress.currentStep || 0,
                    viewedFeatures: progress.viewedFeatures || [],
                    viewedFrameworks: progress.viewedFrameworks || []
                });
            }
        } catch (error) {
            console.error('Error loading user onboarding progress:', error);
        }
    },

    clearProgressFromStorage: () => {
        try {
            localStorage.removeItem(USER_ONBOARDING_PROGRESS_KEY);
        } catch (error) {
            console.error('Error clearing user onboarding progress:', error);
        }
    }
}));

export default useUserOnboardingStore;
