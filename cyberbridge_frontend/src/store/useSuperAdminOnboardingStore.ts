// src/store/useSuperAdminOnboardingStore.ts
import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

// LocalStorage keys for persistence
const SUPERADMIN_ONBOARDING_PROGRESS_KEY = 'cyberbridge_superadmin_onboarding_progress';
const SUPERADMIN_ONBOARDING_STATUS_KEY = 'cyberbridge_superadmin_onboarding_status';

export interface SuperAdminOnboardingProgress {
    currentStep: number;
    viewedSections: string[];
    systemConfigured: boolean;
}

interface SuperAdminOnboardingStatus {
    superadmin_onboarding_completed: boolean;
    superadmin_onboarding_skipped: boolean;
    superadmin_onboarding_completed_at: string | null;
}

interface OnboardingStatusResponse {
    onboarding_completed: boolean;
    onboarding_skipped: boolean;
    onboarding_completed_at: string | null;
    is_admin?: boolean;
}

interface SuperAdminOnboardingStore {
    // Wizard state
    isWizardOpen: boolean;
    currentStep: number;
    loading: boolean;
    error: string | null;

    // Wizard data
    viewedSections: string[];
    systemConfigured: boolean;

    // Onboarding status
    onboardingStatus: SuperAdminOnboardingStatus | null;

    // Actions
    openWizard: () => void;
    closeWizard: () => void;
    nextStep: () => void;
    prevStep: () => void;
    setStep: (step: number) => void;

    // Data setters
    setViewedSections: (sections: string[]) => void;
    addViewedSection: (section: string) => void;
    setSystemConfigured: (configured: boolean) => void;

    // API actions
    checkOnboardingStatus: () => Promise<SuperAdminOnboardingStatus | null>;
    completeOnboarding: () => Promise<boolean>;
    skipOnboarding: () => Promise<boolean>;
    resetOnboarding: () => void;

    // Progress persistence
    saveProgressToStorage: () => void;
    loadProgressFromStorage: () => void;
    clearProgressFromStorage: () => void;
}

const useSuperAdminOnboardingStore = create<SuperAdminOnboardingStore>((set, get) => ({
    // Initial state
    isWizardOpen: false,
    currentStep: 0,
    loading: false,
    error: null,
    viewedSections: [],
    systemConfigured: false,
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

    // Step navigation (5 steps: 0-4)
    nextStep: () => {
        const { currentStep } = get();
        const newStep = Math.min(currentStep + 1, 4);
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
        set({ currentStep: Math.max(0, Math.min(step, 4)) });
        get().saveProgressToStorage();
    },

    // Data setters
    setViewedSections: (sections: string[]) => {
        set({ viewedSections: sections });
        get().saveProgressToStorage();
    },

    addViewedSection: (section: string) => {
        const { viewedSections } = get();
        if (!viewedSections.includes(section)) {
            set({ viewedSections: [...viewedSections, section] });
            get().saveProgressToStorage();
        }
    },

    setSystemConfigured: (configured: boolean) => {
        set({ systemConfigured: configured });
        get().saveProgressToStorage();
    },

    // API actions
    checkOnboardingStatus: async () => {
        try {
            set({ loading: true, error: null });

            // First check localStorage for completion status
            const savedStatus = localStorage.getItem(SUPERADMIN_ONBOARDING_STATUS_KEY);
            if (savedStatus) {
                const status: SuperAdminOnboardingStatus = JSON.parse(savedStatus);
                // If already completed or skipped locally, don't show wizard
                if (status.superadmin_onboarding_completed || status.superadmin_onboarding_skipped) {
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
                    const status: SuperAdminOnboardingStatus = savedStatus
                        ? JSON.parse(savedStatus)
                        : {
                            superadmin_onboarding_completed: false,
                            superadmin_onboarding_skipped: false,
                            superadmin_onboarding_completed_at: null
                        };
                    set({ onboardingStatus: status, loading: false });
                    return status;
                }
                throw new Error('Failed to fetch superadmin onboarding status');
            }

            const apiStatus: OnboardingStatusResponse = await response.json();
            const status: SuperAdminOnboardingStatus = {
                superadmin_onboarding_completed: apiStatus.onboarding_completed,
                superadmin_onboarding_skipped: apiStatus.onboarding_skipped,
                superadmin_onboarding_completed_at: apiStatus.onboarding_completed_at
            };
            // Save to localStorage for future checks
            localStorage.setItem(SUPERADMIN_ONBOARDING_STATUS_KEY, JSON.stringify(status));
            set({ onboardingStatus: status, loading: false });
            return status;
        } catch (error) {
            console.error('Error checking superadmin onboarding status:', error);
            // Check localStorage first, then default to completed to avoid showing wizard on errors
            const savedStatus = localStorage.getItem(SUPERADMIN_ONBOARDING_STATUS_KEY);
            const status: SuperAdminOnboardingStatus = savedStatus
                ? JSON.parse(savedStatus)
                : {
                    superadmin_onboarding_completed: true, // Default to completed on error to avoid annoying users
                    superadmin_onboarding_skipped: false,
                    superadmin_onboarding_completed_at: null
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
                throw new Error('Failed to complete superadmin onboarding');
            }

            // Clear progress from storage
            get().clearProgressFromStorage();

            const completedStatus: SuperAdminOnboardingStatus = {
                superadmin_onboarding_completed: true,
                superadmin_onboarding_skipped: false,
                superadmin_onboarding_completed_at: new Date().toISOString()
            };

            // Save completion status to localStorage
            localStorage.setItem(SUPERADMIN_ONBOARDING_STATUS_KEY, JSON.stringify(completedStatus));

            // Reset wizard state
            set({
                loading: false,
                isWizardOpen: false,
                currentStep: 0,
                viewedSections: [],
                systemConfigured: false,
                onboardingStatus: completedStatus
            });

            return true;
        } catch (error) {
            console.error('Error completing superadmin onboarding:', error);
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
                throw new Error('Failed to skip superadmin onboarding');
            }

            // Clear progress from storage
            get().clearProgressFromStorage();

            const skippedStatus: SuperAdminOnboardingStatus = {
                superadmin_onboarding_completed: true,
                superadmin_onboarding_skipped: true,
                superadmin_onboarding_completed_at: new Date().toISOString()
            };

            // Save skipped status to localStorage
            localStorage.setItem(SUPERADMIN_ONBOARDING_STATUS_KEY, JSON.stringify(skippedStatus));

            // Reset wizard state
            set({
                loading: false,
                isWizardOpen: false,
                currentStep: 0,
                viewedSections: [],
                systemConfigured: false,
                onboardingStatus: skippedStatus
            });

            return true;
        } catch (error) {
            console.error('Error skipping superadmin onboarding:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to skip onboarding',
                loading: false
            });
            return false;
        }
    },

    resetOnboarding: () => {
        // Reset to initial state (local only)
        get().clearProgressFromStorage();
        // Also clear status from localStorage so wizard can show again
        localStorage.removeItem(SUPERADMIN_ONBOARDING_STATUS_KEY);
        set({
            loading: false,
            currentStep: 0,
            viewedSections: [],
            systemConfigured: false,
            onboardingStatus: {
                superadmin_onboarding_completed: false,
                superadmin_onboarding_skipped: false,
                superadmin_onboarding_completed_at: null
            }
        });
    },

    // Progress persistence
    saveProgressToStorage: () => {
        const { currentStep, viewedSections, systemConfigured } = get();
        const progress: SuperAdminOnboardingProgress = {
            currentStep,
            viewedSections,
            systemConfigured
        };
        try {
            localStorage.setItem(SUPERADMIN_ONBOARDING_PROGRESS_KEY, JSON.stringify(progress));
        } catch (error) {
            console.error('Error saving superadmin onboarding progress:', error);
        }
    },

    loadProgressFromStorage: () => {
        try {
            const saved = localStorage.getItem(SUPERADMIN_ONBOARDING_PROGRESS_KEY);
            if (saved) {
                const progress: SuperAdminOnboardingProgress = JSON.parse(saved);
                set({
                    currentStep: progress.currentStep || 0,
                    viewedSections: progress.viewedSections || [],
                    systemConfigured: progress.systemConfigured || false
                });
            }
        } catch (error) {
            console.error('Error loading superadmin onboarding progress:', error);
        }
    },

    clearProgressFromStorage: () => {
        try {
            localStorage.removeItem(SUPERADMIN_ONBOARDING_PROGRESS_KEY);
        } catch (error) {
            console.error('Error clearing superadmin onboarding progress:', error);
        }
    }
}));

export default useSuperAdminOnboardingStore;
