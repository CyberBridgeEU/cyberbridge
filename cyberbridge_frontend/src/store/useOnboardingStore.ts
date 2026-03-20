// src/store/useOnboardingStore.ts
import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

// LocalStorage key for progress persistence
const ONBOARDING_PROGRESS_KEY = 'cyberbridge_onboarding_progress';

export interface OnboardingProgress {
    currentStep: number;
    selectedFrameworks: string[];
    invitedUsers: InvitedUser[];
    aiConfig: AIConfig;
}

export interface InvitedUser {
    email: string;
    roleId: string;
}

export interface AIConfig {
    provider: string;
    apiKey?: string;
    model?: string;
    baseUrl?: string;
}

interface OnboardingStatus {
    onboarding_completed: boolean;
    onboarding_skipped: boolean;
    onboarding_completed_at: string | null;
    is_admin: boolean;
}

interface OnboardingStore {
    // Wizard state
    isWizardOpen: boolean;
    currentStep: number;
    loading: boolean;
    error: string | null;

    // Wizard data
    selectedFrameworks: string[];
    invitedUsers: InvitedUser[];
    aiConfig: AIConfig;

    // Onboarding status
    onboardingStatus: OnboardingStatus | null;

    // Actions
    openWizard: () => void;
    closeWizard: () => void;
    nextStep: () => void;
    prevStep: () => void;
    setStep: (step: number) => void;

    // Data setters
    setSelectedFrameworks: (frameworks: string[]) => void;
    addInvitedUser: (user: InvitedUser) => void;
    removeInvitedUser: (email: string) => void;
    setAIConfig: (config: AIConfig) => void;

    // API actions
    checkOnboardingStatus: () => Promise<OnboardingStatus | null>;
    completeOnboarding: () => Promise<boolean>;
    skipOnboarding: () => Promise<boolean>;
    resetOnboarding: () => Promise<boolean>;

    // Progress persistence
    saveProgressToStorage: () => void;
    loadProgressFromStorage: () => void;
    clearProgressFromStorage: () => void;
}

const useOnboardingStore = create<OnboardingStore>((set, get) => ({
    // Initial state
    isWizardOpen: false,
    currentStep: 0,
    loading: false,
    error: null,
    selectedFrameworks: [],
    invitedUsers: [],
    aiConfig: {
        provider: 'llamacpp',
    },
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

    // Step navigation
    nextStep: () => {
        const { currentStep } = get();
        const newStep = Math.min(currentStep + 1, 3); // 4 steps (0-3)
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
    setSelectedFrameworks: (frameworks: string[]) => {
        set({ selectedFrameworks: frameworks });
        get().saveProgressToStorage();
    },

    addInvitedUser: (user: InvitedUser) => {
        const { invitedUsers } = get();
        // Prevent duplicates
        if (!invitedUsers.find(u => u.email === user.email)) {
            set({ invitedUsers: [...invitedUsers, user] });
            get().saveProgressToStorage();
        }
    },

    removeInvitedUser: (email: string) => {
        const { invitedUsers } = get();
        set({ invitedUsers: invitedUsers.filter(u => u.email !== email) });
        get().saveProgressToStorage();
    },

    setAIConfig: (config: AIConfig) => {
        set({ aiConfig: config });
        get().saveProgressToStorage();
    },

    // API actions
    checkOnboardingStatus: async () => {
        try {
            set({ loading: true, error: null });
            const authHeader = useAuthStore.getState().getAuthHeader();

            const response = await fetch(`${cyberbridge_back_end_rest_api}/onboarding/status`, {
                headers: {
                    ...authHeader
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch onboarding status');
            }

            const status: OnboardingStatus = await response.json();
            set({ onboardingStatus: status, loading: false });
            return status;
        } catch (error) {
            console.error('Error checking onboarding status:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to check onboarding status',
                loading: false
            });
            return null;
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

            if (!response.ok) {
                throw new Error('Failed to complete onboarding');
            }

            // Clear progress from storage
            get().clearProgressFromStorage();

            // Reset wizard state
            set({
                loading: false,
                isWizardOpen: false,
                currentStep: 0,
                selectedFrameworks: [],
                invitedUsers: [],
                aiConfig: { provider: 'llamacpp' },
                onboardingStatus: {
                    onboarding_completed: true,
                    onboarding_skipped: false,
                    onboarding_completed_at: new Date().toISOString(),
                    is_admin: true
                }
            });

            return true;
        } catch (error) {
            console.error('Error completing onboarding:', error);
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

            if (!response.ok) {
                throw new Error('Failed to skip onboarding');
            }

            // Clear progress from storage
            get().clearProgressFromStorage();

            // Reset wizard state
            set({
                loading: false,
                isWizardOpen: false,
                currentStep: 0,
                selectedFrameworks: [],
                invitedUsers: [],
                aiConfig: { provider: 'llamacpp' },
                onboardingStatus: {
                    onboarding_completed: true,
                    onboarding_skipped: true,
                    onboarding_completed_at: new Date().toISOString(),
                    is_admin: true
                }
            });

            return true;
        } catch (error) {
            console.error('Error skipping onboarding:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to skip onboarding',
                loading: false
            });
            return false;
        }
    },

    resetOnboarding: async () => {
        try {
            set({ loading: true, error: null });
            const authHeader = useAuthStore.getState().getAuthHeader();

            const response = await fetch(`${cyberbridge_back_end_rest_api}/onboarding/reset`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...authHeader
                }
            });

            if (!response.ok) {
                throw new Error('Failed to reset onboarding');
            }

            // Reset to initial state
            set({
                loading: false,
                currentStep: 0,
                selectedFrameworks: [],
                invitedUsers: [],
                aiConfig: { provider: 'llamacpp' },
                onboardingStatus: {
                    onboarding_completed: false,
                    onboarding_skipped: false,
                    onboarding_completed_at: null,
                    is_admin: true
                }
            });

            return true;
        } catch (error) {
            console.error('Error resetting onboarding:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to reset onboarding',
                loading: false
            });
            return false;
        }
    },

    // Progress persistence
    saveProgressToStorage: () => {
        const { currentStep, selectedFrameworks, invitedUsers, aiConfig } = get();
        const progress: OnboardingProgress = {
            currentStep,
            selectedFrameworks,
            invitedUsers,
            aiConfig
        };
        try {
            localStorage.setItem(ONBOARDING_PROGRESS_KEY, JSON.stringify(progress));
        } catch (error) {
            console.error('Error saving onboarding progress:', error);
        }
    },

    loadProgressFromStorage: () => {
        try {
            const saved = localStorage.getItem(ONBOARDING_PROGRESS_KEY);
            if (saved) {
                const progress: OnboardingProgress = JSON.parse(saved);
                set({
                    currentStep: progress.currentStep || 0,
                    selectedFrameworks: progress.selectedFrameworks || [],
                    invitedUsers: progress.invitedUsers || [],
                    aiConfig: progress.aiConfig || { provider: 'llamacpp' }
                });
            }
        } catch (error) {
            console.error('Error loading onboarding progress:', error);
        }
    },

    clearProgressFromStorage: () => {
        try {
            localStorage.removeItem(ONBOARDING_PROGRESS_KEY);
        } catch (error) {
            console.error('Error clearing onboarding progress:', error);
        }
    }
}));

export default useOnboardingStore;
