import {create} from "zustand";
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

// Interfaces based on Python models
export interface ControlSet {
    id: string;
    name: string;
    description?: string;
    organisation_id?: string;
    created_at: string;
    updated_at: string;
}

export interface ControlStatus {
    id: string;
    status_name: string; // Not Implemented, Partially Implemented, Implemented, N/A
}

export interface Control {
    id: string;
    code: string;
    name: string;
    description?: string;
    category?: string;
    owner?: string;
    control_set_id: string;
    control_status_id: string;
    organisation_id?: string;
    created_at: string;
    updated_at: string;
    // Additional fields for UI display
    control_set_name?: string;
    control_status_name?: string;
    organisation_name?: string;
    last_updated_by_email?: string;
    linked_risks_count?: number;
    linked_policies_count?: number;
}

export interface ControlImportResult {
    success: boolean;
    imported_count: number;
    failed_count: number;
    message: string;
    imported_control_ids: string[];
    errors: string[];
}

export interface ControlSetTemplate {
    name: string;
    description: string;
    control_count: number;
}

export interface ControlTemplateDetail {
    name: string;
    description: string;
    controls: Array<{
        code: string;
        name: string;
        description?: string;
    }>;
}

// Linked Risk interface (simplified for connections)
export interface LinkedRisk {
    id: string;
    risk_code: string | null;
    risk_category_name: string;
    risk_category_description: string;
    risk_severity: string | null;
    risk_status: string | null;
    risk_potential_impact: string;
}

// Linked Policy interface (simplified for connections)
export interface LinkedPolicy {
    id: string;
    title: string;
    policy_code?: string | null;
    owner: string | null;
    status: string | null;
    body: string | null;
}

export interface ControlStore {
    // Variables
    controls: Control[];
    controlSets: ControlSet[];
    controlStatuses: ControlStatus[];
    controlTemplates: ControlSetTemplate[];
    linkedRisks: LinkedRisk[];
    linkedPolicies: LinkedPolicy[];
    error: string | null;

    // Functions
    fetchControls: (controlSetId?: string) => Promise<boolean>;
    fetchControlSets: () => Promise<boolean>;
    fetchControlStatuses: () => Promise<boolean>;
    fetchControlTemplates: () => Promise<boolean>;
    fetchControlTemplateDetail: (templateName: string) => Promise<ControlTemplateDetail>;
    importControlsFromTemplate: (templateName: string) => Promise<ControlImportResult>;
    createControl: (
        code: string,
        name: string,
        description: string,
        category: string,
        owner: string,
        control_set_id: string,
        control_status_id: string
    ) => Promise<boolean>;
    updateControl: (
        id: string,
        code: string,
        name: string,
        description: string,
        category: string,
        owner: string,
        control_set_id: string,
        control_status_id: string
    ) => Promise<boolean>;
    deleteControl: (id: string) => Promise<boolean>;
    linkControlToRisk: (controlId: string, riskId: string, frameworkId: string) => Promise<boolean>;
    unlinkControlFromRisk: (controlId: string, riskId: string, frameworkId: string) => Promise<boolean>;
    linkControlToPolicy: (controlId: string, policyId: string, frameworkId: string) => Promise<boolean>;
    unlinkControlFromPolicy: (controlId: string, policyId: string, frameworkId: string) => Promise<boolean>;

    // Control Connection Query Actions
    fetchLinkedRisks: (controlId: string, frameworkId?: string) => Promise<void>;
    fetchLinkedPolicies: (controlId: string, frameworkId?: string) => Promise<void>;
}

const useControlStore = create<ControlStore>((set, get) => ({
    // Variables
    controls: [],
    controlSets: [],
    controlStatuses: [],
    controlTemplates: [],
    linkedRisks: [],
    linkedPolicies: [],
    error: null,

    // Functions
    fetchControls: async (controlSetId?: string) => {
        try {
            const url = controlSetId
                ? `${cyberbridge_back_end_rest_api}/controls?control_set_id=${controlSetId}`
                : `${cyberbridge_back_end_rest_api}/controls`;

            const response = await fetch(url, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch controls');
            }

            const data = await response.json();
            set({ controls: data, error: null });
            return true;
        } catch (error) {
            console.error('Error fetching controls:', error);
            set({ error: 'Failed to fetch controls' });
            return false;
        }
    },

    fetchControlSets: async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/controls/control-sets`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch control sets');
            }

            const data = await response.json();
            set({ controlSets: data, error: null });
            return true;
        } catch (error) {
            console.error('Error fetching control sets:', error);
            set({ error: 'Failed to fetch control sets' });
            return false;
        }
    },

    fetchControlStatuses: async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/controls/statuses`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch control statuses');
            }

            const data = await response.json();
            set({ controlStatuses: data, error: null });
            return true;
        } catch (error) {
            console.error('Error fetching control statuses:', error);
            set({ error: 'Failed to fetch control statuses' });
            return false;
        }
    },

    fetchControlTemplates: async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/controls/templates`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch control templates');
            }

            const data = await response.json();
            set({ controlTemplates: data, error: null });
            return true;
        } catch (error) {
            console.error('Error fetching control templates:', error);
            set({ error: 'Failed to fetch control templates' });
            return false;
        }
    },

    fetchControlTemplateDetail: async (templateName: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/controls/templates/${encodeURIComponent(templateName)}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch control template detail');
            }

            const data = await response.json();
            set({ error: null });
            return data;
        } catch (error) {
            console.error('Error fetching control template detail:', error);
            set({ error: 'Failed to fetch control template detail' });
            throw error;
        }
    },

    importControlsFromTemplate: async (templateName: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/controls/import-template`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    template_name: templateName
                })
            });

            if (!response.ok) {
                throw new Error('Failed to import controls from template');
            }

            const data = await response.json();
            set({ error: null });

            // Refresh controls after import
            await get().fetchControls();
            await get().fetchControlSets();

            return data;
        } catch (error) {
            console.error('Error importing controls from template:', error);
            set({ error: 'Failed to import controls from template' });
            return {
                success: false,
                imported_count: 0,
                failed_count: 0,
                message: 'Failed to import controls from template',
                imported_control_ids: [],
                errors: [error instanceof Error ? error.message : 'Unknown error']
            };
        }
    },

    createControl: async (
        code: string,
        name: string,
        description: string,
        category: string,
        owner: string,
        control_set_id: string,
        control_status_id: string
    ) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/controls`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    code,
                    name,
                    description,
                    category,
                    owner,
                    control_set_id,
                    control_status_id
                })
            });

            if (!response.ok) {
                throw new Error('Failed to create control');
            }

            const newControl = await response.json();
            set((state) => ({
                controls: [...state.controls, newControl],
                error: null
            }));
            return true;
        } catch (error) {
            console.error('Error creating control:', error);
            set({ error: 'Failed to create control' });
            return false;
        }
    },

    updateControl: async (
        id: string,
        code: string,
        name: string,
        description: string,
        category: string,
        owner: string,
        control_set_id: string,
        control_status_id: string
    ) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/controls/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    id,
                    code,
                    name,
                    description,
                    category,
                    owner,
                    control_set_id,
                    control_status_id
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update control');
            }

            const updatedControl = await response.json();
            set((state) => ({
                controls: state.controls.map((control) =>
                    control.id === id ? updatedControl : control
                ),
                error: null
            }));
            return true;
        } catch (error) {
            console.error('Error updating control:', error);
            set({ error: 'Failed to update control' });
            return false;
        }
    },

    deleteControl: async (id: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/controls/${id}`, {
                method: 'DELETE',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({ error: errorData.detail || 'Failed to delete control' });
                return false;
            }

            set((state) => ({
                controls: state.controls.filter((control) => control.id !== id),
                error: null
            }));
            return true;
        } catch (error) {
            console.error('Error deleting control:', error);
            set({ error: 'Failed to delete control' });
            return false;
        }
    },

    linkControlToRisk: async (controlId: string, riskId: string, frameworkId: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/controls/${controlId}/risks/${riskId}?framework_id=${frameworkId}`,
                {
                    method: 'POST',
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to link control to risk');
            }

            set({ error: null });
            return true;
        } catch (error) {
            console.error('Error linking control to risk:', error);
            set({ error: 'Failed to link control to risk' });
            return false;
        }
    },

    unlinkControlFromRisk: async (controlId: string, riskId: string, frameworkId: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/controls/${controlId}/risks/${riskId}?framework_id=${frameworkId}`,
                {
                    method: 'DELETE',
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to unlink control from risk');
            }

            set({ error: null });
            return true;
        } catch (error) {
            console.error('Error unlinking control from risk:', error);
            set({ error: 'Failed to unlink control from risk' });
            return false;
        }
    },

    linkControlToPolicy: async (controlId: string, policyId: string, frameworkId: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/controls/${controlId}/policies/${policyId}?framework_id=${frameworkId}`,
                {
                    method: 'POST',
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to link control to policy');
            }

            set({ error: null });
            return true;
        } catch (error) {
            console.error('Error linking control to policy:', error);
            set({ error: 'Failed to link control to policy' });
            return false;
        }
    },

    unlinkControlFromPolicy: async (controlId: string, policyId: string, frameworkId: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/controls/${controlId}/policies/${policyId}?framework_id=${frameworkId}`,
                {
                    method: 'DELETE',
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to unlink control from policy');
            }

            set({ error: null });
            return true;
        } catch (error) {
            console.error('Error unlinking control from policy:', error);
            set({ error: 'Failed to unlink control from policy' });
            return false;
        }
    },

    // Control Connection Query Actions
    fetchLinkedRisks: async (controlId: string, frameworkId?: string) => {
        try {
            const params = frameworkId ? `?framework_id=${frameworkId}` : '';
            const response = await fetch(`${cyberbridge_back_end_rest_api}/controls/${controlId}/risks${params}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch linked risks');
            }

            const data = await response.json();
            set({ linkedRisks: data, error: null });
        } catch (error) {
            console.error('Error fetching linked risks:', error);
            set({ error: 'Failed to fetch linked risks', linkedRisks: [] });
        }
    },

    fetchLinkedPolicies: async (controlId: string, frameworkId?: string) => {
        try {
            const params = frameworkId ? `?framework_id=${frameworkId}` : '';
            const response = await fetch(`${cyberbridge_back_end_rest_api}/controls/${controlId}/policies${params}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch linked policies');
            }

            const data = await response.json();
            set({ linkedPolicies: data, error: null });
        } catch (error) {
            console.error('Error fetching linked policies:', error);
            set({ error: 'Failed to fetch linked policies', linkedPolicies: [] });
        }
    }
}));

export default useControlStore;
