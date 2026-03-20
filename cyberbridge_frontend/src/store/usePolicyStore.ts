import {create} from "zustand";
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

// Interfaces based on Python models
export interface PolicyStatus {
    id: string;
    status: string; // Draft, Review, Ready for Approval, Approved
}

export interface Policy {
    id: string;
    title: string;
    policy_code?: string | null;
    owner: string | null;
    status_id: string;
    body: string | null;
    company_name: string | null;
    organisation_id?: string;
    created_at: string;
    // Additional fields for UI display
    status?: string;
    status_name?: string;
    organisation_name?: string;
    frameworks?: string[]; // Framework IDs for filtering
    framework_names?: string[]; // Framework names for display
    objectives?: string[];
    chapters?: string[];
}

export interface Framework {
    id: string;
    name: string;
    description: string;
    organisation_id: string;
    organisation_domain?: string;
    created_at: string;
    updated_at: string;
}

export interface Objective {
    id: string;
    title: string;
    subchapter: string | null;
    chapter_id: string;
    requirement_description: string | null;
    objective_utilities: string | null;
    created_at: string;
    updated_at: string;
    // Additional fields for UI display
    chapter_name?: string;
}

export interface Chapter {
    id: string;
    title: string;
    framework_id: string;
    created_at: string;
    updated_at: string;
    objectives: Objective[];
}

export interface PolicyFramework {
    policy_id: string;
    framework_id: string;
}

export interface PolicyObjective {
    policy_id: string;
    objective_id: string;
    order: number;
}

export interface PolicyFile {
    filename: string;
    size: number;
    modified: number;
}

export interface PolicyFilePreview {
    filename: string;
    html_content: string;
    conversion_messages: string[];
}

export interface PolicyTemplate {
    id: string;
    title: string | null;
    policy_code: string | null;
    filename: string;
    file_size: number | null;
    source: string | null;
}

export interface PolicyTemplateImportResponse {
    success: boolean;
    imported_count: number;
    skipped_count: number;
    message: string;
    imported_policy_codes: string[];
    errors: string[];
}

// Linked Objective interface (simplified for connections)
export interface LinkedObjective {
    id: string;
    title: string;
    subchapter: string | null;
    chapter_title: string | null;
}

// Linked Control interface (simplified for connections)
export interface LinkedControl {
    id: string;
    code: string;
    name: string;
    description: string | null;
    category: string | null;
    owner: string | null;
    control_status_name: string | null;
    control_set_name: string | null;
}

export interface PolicyStore {
    // Variables
    policies: Policy[];
    policyStatuses: PolicyStatus[];
    frameworks: Framework[];
    objectives: Objective[];
    chapters: Chapter[];
    policyFrameworks: PolicyFramework[];
    policyObjectives: PolicyObjective[];
    policyFiles: PolicyFile[];
    selectedFilePreview: PolicyFilePreview | null;
    policyTemplates: PolicyTemplate[];
    linkedObjectives: LinkedObjective[];
    linkedControls: LinkedControl[];
    loading: boolean;
    error: string | null;

    // Functions
    fetchPolicies: () => Promise<boolean>;
    fetchPolicyStatuses: () => Promise<boolean>;
    fetchFrameworks: () => Promise<boolean>;
    fetchObjectives: () => Promise<boolean>;
    fetchObjectivesByFrameworks: (frameworkIds: string[]) => Promise<boolean>;
    fetchChaptersWithObjectives: (frameworkId: string, operatorRole?: string) => Promise<boolean>;
    fetchPolicyFrameworks: () => Promise<boolean>;
    fetchPolicyObjectives: () => Promise<boolean>;

    createPolicy: (
        title: string,
        owner: string | null,
        status_id: string,
        body: string | null,
        framework_ids?: string[],
        objective_ids?: Array<{id: string, order: number}>,
        company_name?: string,
        policy_code?: string | null
    ) => Promise<boolean>;

    updatePolicy: (
        id: string,
        title: string,
        owner: string | null,
        status_id: string,
        body: string | null,
        framework_ids?: string[],
        objective_ids?: Array<{id: string, order: number}>,
        company_name?: string,
        policy_code?: string | null
    ) => Promise<boolean>;

    deletePolicy: (id: string) => Promise<boolean>;

    // Policy Framework relationship management
    addFrameworkToPolicy: (policy_id: string, framework_id: string) => Promise<boolean>;
    removeFrameworkFromPolicy: (policy_id: string, framework_id: string) => Promise<boolean>;

    // Policy Objective relationship management
    addObjectiveToPolicy: (policy_id: string, objective_id: string, order: number) => Promise<boolean>;
    updateObjectiveOrder: (policy_id: string, objective_id: string, order: number) => Promise<boolean>;
    removeObjectiveFromPolicy: (policy_id: string, objective_id: string) => Promise<boolean>;

    // Policy File management
    fetchPolicyFiles: () => Promise<boolean>;
    fetchPolicyFilePreview: (filename: string) => Promise<boolean>;
    clearFilePreview: () => void;

    // Policy Template Actions
    fetchPolicyTemplates: () => Promise<boolean>;
    importPolicyTemplates: (templateIds: string[]) => Promise<PolicyTemplateImportResponse | null>;

    // Policy Status Quick Update
    updatePolicyStatus: (policyId: string, statusId: string) => Promise<boolean>;

    // Policy Connection Query Actions
    fetchLinkedObjectives: (policyId: string) => Promise<void>;
    fetchLinkedControls: (policyId: string, frameworkId?: string) => Promise<void>;
}

const usePolicyStore = create<PolicyStore>(set => ({
    // Variables
    policies: [],
    policyStatuses: [],
    frameworks: [],
    objectives: [],
    chapters: [],
    policyFrameworks: [],
    policyObjectives: [],
    policyFiles: [],
    selectedFilePreview: null,
    policyTemplates: [],
    linkedObjectives: [],
    linkedControls: [],
    loading: false,
    error: null,

    // Fetch all policies
    fetchPolicies: async () => {
        set({loading: true, error: null});
        try {
            // Fetch policies - API now returns policies with frameworks, objectives, and chapters included
            const policiesResponse = await fetch(`${cyberbridge_back_end_rest_api}/policies`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!policiesResponse.ok) {
                return false;
            }
            const policiesData = await policiesResponse.json();

            console.log('Policies from API:', policiesData);

            // Also fetch frameworks and objectives for dropdowns and other functionality
            await usePolicyStore.getState().fetchFrameworks();
            await usePolicyStore.getState().fetchObjectives();

            // The API now includes frameworks, objectives, and chapters directly in the response
            // Use the data as-is - no need for complex merging
            set({policies: policiesData, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching policies:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch policies',
                loading: false
            });
            return false;
        }
    },

    // Fetch all policy statuses
    fetchPolicyStatuses: async () => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/statuses`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log(data);
            set({policyStatuses: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching policy statuses:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch policy statuses',
                loading: false
            });
            return false;
        }
    },

    // Fetch all frameworks
    fetchFrameworks: async () => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log(data);
            set({frameworks: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching frameworks:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch frameworks',
                loading: false
            });
            return false;
        }
    },

    // Fetch all objectives
    fetchObjectives: async () => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/get_all_objectives?skip=0&limit=5000`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log(data);
            set({objectives: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching objectives:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch objectives',
                loading: false
            });
            return false;
        }
    },

    // Fetch objectives by framework IDs
    fetchObjectivesByFrameworks: async (frameworkIds: string[]) => {
        set({loading: true, error: null});
        try {
            if (frameworkIds.length === 0) {
                set({objectives: [], loading: false});
                return true;
            }

            const frameworkIdsParam = frameworkIds.join(',');
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/by_frameworks?framework_ids=${frameworkIdsParam}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log('Objectives by frameworks:', data);
            set({objectives: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching objectives by frameworks:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch objectives by frameworks',
                loading: false
            });
            return false;
        }
    },

    // Fetch chapters with objectives for a specific framework
    fetchChaptersWithObjectives: async (frameworkId: string, operatorRole?: string) => {
        set({loading: true, error: null});
        try {
            let url = `${cyberbridge_back_end_rest_api}/objectives/objectives_checklist?framework_id=${frameworkId}`;
            if (operatorRole) {
                url += `&operator_role=${operatorRole}`;
            }
            const response = await fetch(url, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log('Chapters with objectives:', data);
            set({chapters: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching chapters with objectives:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch chapters with objectives',
                loading: false
            });
            return false;
        }
    },

    // Fetch policy-framework relationships
    fetchPolicyFrameworks: async () => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/frameworks`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log(data);
            set({policyFrameworks: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching policy frameworks:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch policy frameworks',
                loading: false
            });
            return false;
        }
    },

    // Fetch policy-objective relationships
    fetchPolicyObjectives: async () => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/objectives`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log(data);
            set({policyObjectives: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching policy objectives:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch policy objectives',
                loading: false
            });
            return false;
        }
    },

    // Create a new policy
    createPolicy: async (
        title: string,
        owner: string | null,
        status_id: string,
        body: string | null,
        framework_ids?: string[],
        objective_ids?: Array<{id: string, order: number}>,
        company_name?: string,
        policy_code?: string | null
    ) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({
            title,
            policy_code,
            owner,
            status_id,
            body,
            framework_ids,
            objective_ids,
            company_name
        });
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                set({
                    error: errorData?.detail || 'Failed to create policy',
                    loading: false
                });
                return false;
            }

            const newPolicy = await response.json();
            set(state => ({policies: [...state.policies, newPolicy], loading: false, error: null}));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to create policy',
                loading: false
            });
            return false;
        }
    },

    // Update an existing policy
    updatePolicy: async (
        id: string,
        title: string,
        owner: string | null,
        status_id: string,
        body: string | null,
        framework_ids?: string[],
        objective_ids?: Array<{id: string, order: number}>,
        company_name?: string,
        policy_code?: string | null
    ) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({
            id,
            title,
            policy_code,
            owner,
            status_id,
            body,
            framework_ids,
            objective_ids,
            company_name
        });
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                set({
                    error: errorData?.detail || 'Failed to update policy',
                    loading: false
                });
                return false;
            }

            const updatedPolicy = await response.json();
            set(state => ({
                policies: state.policies.map(policy => policy.id === id ? updatedPolicy : policy),
                loading: false,
                error: null
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to update policy',
                loading: false
            });
            return false;
        }
    },

    // Delete a policy
    deletePolicy: async (id: string) => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/${id}`, {
                method: 'DELETE',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                // Try to get the specific error message from the backend
                try {
                    const errorData = await response.json();
                    set({
                        error: errorData.detail || 'Failed to delete policy',
                        loading: false
                    });
                } catch {
                    set({
                        error: 'Failed to delete policy',
                        loading: false
                    });
                }
                return false;
            }

            set(state => ({
                policies: state.policies.filter(policy => policy.id !== id),
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to delete policy',
                loading: false
            });
            return false;
        }
    },

    // Add a framework to a policy
    addFrameworkToPolicy: async (policy_id: string, framework_id: string) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({
            policy_id,
            framework_id
        });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/add_framework`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if (!response.ok) {
                return false;
            }

            const newPolicyFramework = await response.json();
            set(state => ({
                policyFrameworks: [...state.policyFrameworks, newPolicyFramework],
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to add framework to policy',
                loading: false
            });
            return false;
        }
    },

    // Remove a framework from a policy
    removeFrameworkFromPolicy: async (policy_id: string, framework_id: string) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({
            policy_id,
            framework_id
        });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/remove_framework`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if (!response.ok) {
                return false;
            }

            set(state => ({
                policyFrameworks: state.policyFrameworks.filter(
                    pf => !(pf.policy_id === policy_id && pf.framework_id === framework_id)
                ),
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to remove framework from policy',
                loading: false
            });
            return false;
        }
    },

    // Add an objective to a policy
    addObjectiveToPolicy: async (policy_id: string, objective_id: string, order: number) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({
            policy_id,
            objective_id,
            order
        });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/add_objective`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if (!response.ok) {
                return false;
            }

            const newPolicyObjective = await response.json();
            set(state => ({
                policyObjectives: [...state.policyObjectives, newPolicyObjective],
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to add objective to policy',
                loading: false
            });
            return false;
        }
    },

    // Update the order of an objective in a policy
    updateObjectiveOrder: async (policy_id: string, objective_id: string, order: number) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({
            policy_id,
            objective_id,
            order
        });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/update_objective_order`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if (!response.ok) {
                return false;
            }

            const updatedPolicyObjective = await response.json();
            set(state => ({
                policyObjectives: state.policyObjectives.map(
                    po => (po.policy_id === policy_id && po.objective_id === objective_id)
                        ? updatedPolicyObjective
                        : po
                ),
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to update objective order',
                loading: false
            });
            return false;
        }
    },

    // Remove an objective from a policy
    removeObjectiveFromPolicy: async (policy_id: string, objective_id: string) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({
            policy_id,
            objective_id
        });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/remove_objective`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if (!response.ok) {
                return false;
            }

            set(state => ({
                policyObjectives: state.policyObjectives.filter(
                    po => !(po.policy_id === policy_id && po.objective_id === objective_id)
                ),
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to remove objective from policy',
                loading: false
            });
            return false;
        }
    },

    // Fetch policy files from backend
    fetchPolicyFiles: async () => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/files`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log('Policy files:', data);
            set({policyFiles: data.files || [], loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching policy files:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch policy files',
                loading: false
            });
            return false;
        }
    },

    // Fetch policy file preview
    fetchPolicyFilePreview: async (filename: string) => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/files/${encodeURIComponent(filename)}/preview`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log('Policy file preview:', data);
            set({selectedFilePreview: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching policy file preview:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch policy file preview',
                loading: false
            });
            return false;
        }
    },

    // Clear file preview
    clearFilePreview: () => {
        set({selectedFilePreview: null});
    },

    // Policy Template Actions
    fetchPolicyTemplates: async () => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/templates`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            set({policyTemplates: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching policy templates:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch policy templates',
                loading: false
            });
            return false;
        }
    },

    importPolicyTemplates: async (templateIds: string[]) => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/templates/import`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({ template_ids: templateIds })
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                set({
                    error: errorData?.detail || 'Failed to import policy templates',
                    loading: false
                });
                return null;
            }
            const data = await response.json();
            set({loading: false});
            return data;
        } catch (error) {
            console.error('Error importing policy templates:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to import policy templates',
                loading: false
            });
            return null;
        }
    },

    // Policy Status Quick Update
    updatePolicyStatus: async (policyId: string, statusId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/${policyId}/status`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({ status_id: statusId })
            });
            if (!response.ok) {
                return false;
            }
            return true;
        } catch (error) {
            console.error('Error updating policy status:', error);
            return false;
        }
    },

    // Policy Connection Query Actions
    fetchLinkedObjectives: async (policyId: string) => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/${policyId}/objectives`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch linked objectives');
            }

            const data = await response.json();
            set({linkedObjectives: data, loading: false});
        } catch (error) {
            console.error('Error fetching linked objectives:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch linked objectives',
                linkedObjectives: [],
                loading: false
            });
        }
    },

    fetchLinkedControls: async (policyId: string, frameworkId?: string) => {
        set({loading: true, error: null});
        try {
            const params = frameworkId ? `?framework_id=${frameworkId}` : '';
            const response = await fetch(`${cyberbridge_back_end_rest_api}/policies/${policyId}/controls${params}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch linked controls');
            }

            const data = await response.json();
            set({linkedControls: data, loading: false});
        } catch (error) {
            console.error('Error fetching linked controls:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch linked controls',
                linkedControls: [],
                loading: false
            });
        }
    }
}));

export default usePolicyStore;
