// src/store/useFrameworksStore.ts
import { create } from 'zustand';
import useAuthStore from './useAuthStore';
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

// Framework interface
export interface Framework {
    id: string;
    name: string;
    description: string;
    organisation_domain?: string;
    allowed_scope_types?: string[];
    scope_selection_mode?: string;
}

// Framework template interface
export interface FrameworkTemplate {
    id: string;
    name: string;
    description: string;
    has_chain_links?: boolean;
}

interface FrameworksStore {
    frameworks: Framework[];
    selectedFramework: Framework | null;
    clonableFrameworks: Framework[];
    frameworkTemplates: FrameworkTemplate[];
    loading: boolean;
    error: string | null;

    // Actions
    fetchFrameworks: () => Promise<void>;
    fetchClonableFrameworks: () => Promise<void>;
    fetchFrameworkTemplates: () => Promise<void>;
    getFramework: (id: string) => Promise<void>;
    createFramework: (
        name: string,
        description: string,
        forceCreate?: boolean,
        allowedScopeTypes?: string[],
        scopeSelectionMode?: string
    ) => Promise<{ success: boolean; error?: string }>;
    updateFramework: (framework: Framework) => Promise<boolean>;
    deleteFramework: (id: string) => Promise<boolean>;
    cloneFrameworks: (frameworkIds: string[], customName?: string, targetOrganizationId?: string) => Promise<boolean>;
    seedFrameworkTemplate: (templateId: string, wireConnections?: boolean) => Promise<boolean>;
    fetchChainLinksStatus: (frameworkId: string) => Promise<{ has_mapping: boolean; already_imported: boolean; framework_name: string } | null>;
    importChainLinks: (frameworkId: string) => Promise<{ success: boolean; data?: any; error?: string }>;
    fetchEntityCounts: (frameworkId: string) => Promise<{ objectives: number; risks: number; controls: number; policies: number } | null>;
    checkChainLinksUpdates: (frameworkId: string) => Promise<any | null>;
    applyChainLinksUpdates: (frameworkId: string) => Promise<{ success: boolean; data?: any; error?: string }>;
    setSelectedFramework: (framework: Framework | null) => void;
}

const useFrameworksStore = create<FrameworksStore>((set) => ({
    frameworks: [],
    selectedFramework: null,
    clonableFrameworks: [],
    frameworkTemplates: [],
    loading: false,
    error: null,

    fetchFrameworks: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch frameworks');
            }

            const data = await response.json();
            set({
                frameworks: data,
                loading: false
            });
        } catch (error) {
            console.error('Error fetching frameworks:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch frameworks',
                loading: false
            });
        }
    },

    getFramework: async (id: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/${id}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch framework');
            }

            const data = await response.json();
            set({
                selectedFramework: data,
                loading: false
            });
        } catch (error) {
            console.error('Error fetching framework:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch framework',
                loading: false
            });
        }
    },

    createFramework: async (
        name: string,
        description?: string,
        forceCreate: boolean = false,
        allowedScopeTypes?: string[],
        scopeSelectionMode?: string
    ) => {
        set({ loading: true, error: null });
        try {
            const requestBody: any = {
                name,
                description,
                force_create: forceCreate
            };

            // Add scope configuration if provided
            if (allowedScopeTypes && allowedScopeTypes.length > 0) {
                requestBody.allowed_scope_types = allowedScopeTypes;
            }
            if (scopeSelectionMode) {
                requestBody.scope_selection_mode = scopeSelectionMode;
            }

            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                if (response.status === 400) {
                    const errorData = await response.json();
                    set({
                        error: errorData.detail || 'Framework name already exists',
                        loading: false
                    });
                    return { success: false, error: errorData.detail || 'Framework name already exists' };
                }
                set({
                    error: 'Failed to create framework',
                    loading: false
                });
                return { success: false, error: 'Failed to create framework' };
            }

            const newFramework = await response.json();
            set(state => ({
                frameworks: [...state.frameworks, newFramework],
                loading: false
            }));
            return { success: true };
        } catch (error) {
            // console.error('Error creating framework:', error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to create framework';
            set({
                error: errorMessage,
                loading: false
            });
            return { success: false, error: errorMessage };
        }
    },

    updateFramework: async (framework: Framework) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/${framework.id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify(framework)
            });

            if (!response.ok) {
                throw new Error('Failed to update framework');
            }

            const updatedFramework = await response.json();
            set(state => ({
                frameworks: state.frameworks.map(fw =>
                    fw.id === updatedFramework.id ? updatedFramework : fw
                ),
                selectedFramework: updatedFramework,
                loading: false
            }));
            return true;
        } catch (error) {
            console.error('Error updating framework:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to update framework',
                loading: false
            });
            return false;
        }
    },

    deleteFramework: async (id: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/${id}`, {
                method: 'DELETE',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to delete framework');
            }

            set(state => ({
                frameworks: state.frameworks.filter(framework => framework.id !== id),
                selectedFramework: state.selectedFramework?.id === id ? null : state.selectedFramework,
                loading: false
            }));
            return true;
        } catch (error) {
            console.error('Error deleting framework:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to delete framework',
                loading: false
            });
            return false;
        }
    },

    setSelectedFramework: (framework) => {
        set({ selectedFramework: framework });
    },

    fetchClonableFrameworks: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/all-for-cloning`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch clonable frameworks');
            }

            const data = await response.json();
            set({
                clonableFrameworks: data,
                loading: false
            });
        } catch (error) {
            console.error('Error fetching clonable frameworks:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch clonable frameworks',
                loading: false
            });
        }
    },

    cloneFrameworks: async (frameworkIds: string[], customName?: string, targetOrganizationId?: string) => {
        set({ loading: true, error: null });
        try {
            const requestBody: any = { framework_ids: frameworkIds };
            if (customName && customName.trim() !== '') {
                requestBody.custom_name = customName.trim();
            }
            if (targetOrganizationId && targetOrganizationId.trim() !== '') {
                requestBody.target_organization_id = targetOrganizationId.trim();
            }

            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/clone`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                return false;
            }

            const clonedFrameworks = await response.json();
            set(state => ({
                frameworks: [...state.frameworks, ...clonedFrameworks],
                loading: false
            }));
            return true;
        } catch (error) {
            console.error('Error cloning frameworks:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to clone frameworks',
                loading: false
            });
            return false;
        }
    },

    fetchFrameworkTemplates: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/templates`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch framework templates');
            }

            const data = await response.json();
            set({
                frameworkTemplates: data,
                loading: false
            });
        } catch (error) {
            console.error('Error fetching framework templates:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch framework templates',
                loading: false
            });
        }
    },

    fetchChainLinksStatus: async (frameworkId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/${frameworkId}/chain-links-status`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) return null;
            return await response.json();
        } catch (error) {
            console.error('Error fetching chain links status:', error);
            return null;
        }
    },

    importChainLinks: async (frameworkId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/${frameworkId}/import-chain-links`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                return { success: false, error: errorData.detail || 'Failed to import chain links' };
            }
            const data = await response.json();
            return { success: true, data };
        } catch (error) {
            console.error('Error importing chain links:', error);
            return { success: false, error: error instanceof Error ? error.message : 'Failed to import chain links' };
        }
    },

    fetchEntityCounts: async (frameworkId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/${frameworkId}/entity-counts`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) return null;
            return await response.json();
        } catch (error) {
            console.error('Error fetching entity counts:', error);
            return null;
        }
    },

    checkChainLinksUpdates: async (frameworkId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/${frameworkId}/check-chain-links-updates`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) return null;
            return await response.json();
        } catch (error) {
            console.error('Error checking chain links updates:', error);
            return null;
        }
    },

    applyChainLinksUpdates: async (frameworkId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/${frameworkId}/apply-chain-links-updates`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                return { success: false, error: errorData.detail || 'Failed to apply chain links updates' };
            }
            const data = await response.json();
            return { success: true, data };
        } catch (error) {
            console.error('Error applying chain links updates:', error);
            return { success: false, error: error instanceof Error ? error.message : 'Failed to apply chain links updates' };
        }
    },

    seedFrameworkTemplate: async (templateId: string, wireConnections: boolean = true): Promise<{ success: boolean; error?: string }> => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/seed-template?template_id=${encodeURIComponent(templateId)}&wire_connections=${wireConnections}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                // Handle different HTTP status codes properly
                let errorMessage = 'An error occurred while seeding framework template.';

                try {
                    const responseText = await response.text();
                    console.log('Raw response body:', responseText);

                    try {
                        const errorData = JSON.parse(responseText);
                        console.log('Parsed error data:', errorData);
                        errorMessage = errorData.detail || errorMessage;
                    } catch (parseError) {
                        console.error('Failed to parse JSON:', parseError);
                        errorMessage = responseText || errorMessage;
                    }
                } catch (textError) {
                    // If reading text fails, use default message based on status code
                    console.error('Failed to read response text:', textError);
                    if (response.status === 400) {
                        errorMessage = 'This framework template already exists in your organization and cannot be seeded again.';
                    } else if (response.status === 500) {
                        errorMessage = 'Server error occurred while seeding framework template. Please try again.';
                    } else {
                        errorMessage = `Failed to seed framework template. HTTP ${response.status}`;
                    }
                }

                set({
                    error: errorMessage,
                    loading: false
                });
                return { success: false, error: errorMessage };
            }

            // Success case - framework seeded successfully
            const newFramework = await response.json();
            set(state => ({
                frameworks: [...state.frameworks, newFramework],
                loading: false
            }));
            return { success: true };
        } catch (error) {
            // Network or parsing errors
            console.error('Error seeding framework template:', error);
            const errorMessage = error instanceof Error ? error.message : 'Network error occurred while seeding framework template. Please check your connection and try again.';
            set({
                error: errorMessage,
                loading: false
            });
            return { success: false, error: errorMessage };
        }
    }
}));

export default useFrameworksStore;
