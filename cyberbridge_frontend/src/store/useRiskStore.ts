import {create} from "zustand";
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

// Interfaces based on Python models
export interface AssetCategory {
    id: string;
    name: string; // e.g., Hardware, Software, Cloud Service
}

export interface RiskCategory {
    id: string;
    asset_category_id: string;
    risk_category_name: string;
    risk_category_description: string;
    risk_potential_impact: string;
    risk_control: string;
}

export interface RiskSeverity {
    id: string;
    risk_severity_name: string; // Low, Medium, High, Critical
}

export interface RiskStatus {
    id: string;
    risk_status_name: string; // Reduce, Avoid, Transfer, Share, Accept, Remediated
}

// Risk Template interfaces
export interface RiskTemplateCategory {
    id: string;
    name: string;
    description: string;
    risk_count: number;
}

export interface RiskTemplateItem {
    risk_code: string;
    risk_category_name: string;
    risk_category_description: string;
    risk_potential_impact: string;
    risk_control: string;
}

export interface RiskTemplateRisksResponse {
    category_id: string;
    category_name: string;
    risks: RiskTemplateItem[];
}

export interface RiskTemplateImportResult {
    success: boolean;
    imported_count: number;
    failed_count: number;
    message: string;
    imported_risk_ids: string[];
    errors: string[];
}

export interface Risk {
    id: string;
    asset_category_id: string;
    risk_code?: string | null;
    risk_category_name: string;
    risk_category_description: string;
    risk_potential_impact: string;
    risk_control: string;
    likelihood: string;
    residual_risk: string;
    risk_severity_id: string;
    risk_status_id: string;
    assessment_status?: string;
    organisation_id?: string;
    created_at: string;
    updated_at: string;
    scope_id?: string;
    scope_entity_id?: string;
    scope_name?: string;
    scope_display_name?: string;
    // Additional fields for UI display
    asset_category?: string;
    asset_category_name?: string;
    risk_severity?: string;
    risk_status?: string;
    organisation_name?: string;
    linked_findings_count?: number;
}

// Linked Scan Finding interface
export interface LinkedFinding {
    id: string;
    scan_history_id: string;
    scanner_type: string;
    title: string;
    severity: string | null;
    normalized_severity: string | null;
    identifier: string | null;
    description: string | null;
    solution: string | null;
    url_or_target: string | null;
    is_auto_mapped: boolean | null;
    scan_target: string | null;
    scan_timestamp: string | null;
    created_at: string | null;
}

// Linked Asset interface (simplified for connections)
export interface LinkedAsset {
    id: string;
    name: string;
    description: string | null;
    ip_address: string | null;
    version: string | null;
    asset_type_name: string | null;
    asset_type_icon: string | null;
    status_name: string | null;
    criticality_label: string | null;
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

// Linked Objective interface
export interface LinkedObjective {
    id: string;
    title: string;
    subchapter: string | null;
    chapter_id: string | null;
}

export interface RiskStore {
    // Variables
    risks: Risk[];
    assetCategories: AssetCategory[];
    riskCategories: RiskCategory[];
    riskSeverities: RiskSeverity[];
    riskStatuses: RiskStatus[];
    riskTemplateCategories: RiskTemplateCategory[];
    riskTemplateRisks: Record<string, RiskTemplateItem[]>;
    linkedAssets: LinkedAsset[];
    linkedControls: LinkedControl[];
    linkedFindings: LinkedFinding[];
    linkedObjectives: LinkedObjective[];
    error: string | null;

    // Functions
    fetchRisks: () => Promise<boolean>;
    fetchAssetCategories: () => Promise<boolean>;
    fetchRiskCategories: () => Promise<boolean>;
    fetchRiskSeverities: () => Promise<boolean>;
    fetchRiskStatuses: () => Promise<boolean>;
    fetchRiskTemplateCategories: () => Promise<boolean>;
    fetchRiskTemplateRisks: (categoryId: string) => Promise<RiskTemplateItem[]>;
    importRiskTemplates: (
        categoryId: string,
        selectedRisks: RiskTemplateItem[],
        assetCategoryId: string,
        defaultLikelihood: string,
        defaultSeverity: string,
        defaultResidualRisk: string,
        defaultStatus: string,
        scopeName?: string,
        scopeEntityId?: string
    ) => Promise<RiskTemplateImportResult>;
    createRisk: (
        risk_code: string,
        asset_category_id: string,
        risk_category_name: string,
        risk_category_description: string,
        risk_potential_impact: string,
        risk_control: string,
        likelihood: string,
        residual_risk: string,
        risk_severity_id: string,
        risk_status_id: string,
        assessment_status?: string,
        scope_name?: string,
        scope_entity_id?: string
    ) => Promise<boolean>;
    updateRisk: (
        id: string,
        risk_code: string,
        asset_category_id: string,
        risk_category_name: string,
        risk_category_description: string,
        risk_potential_impact: string,
        risk_control: string,
        likelihood: string,
        residual_risk: string,
        risk_severity_id: string,
        risk_status_id: string,
        assessment_status?: string,
        scope_name?: string,
        scope_entity_id?: string
    ) => Promise<boolean>;
    deleteRisk: (id: string) => Promise<boolean>;

    // Risk Connection Actions
    fetchLinkedAssets: (riskId: string) => Promise<void>;
    fetchLinkedControls: (riskId: string, frameworkId?: string) => Promise<void>;
    fetchLinkedFindings: (riskId: string) => Promise<void>;
    fetchLinkedObjectives: (riskId: string) => Promise<void>;
    unlinkFinding: (riskId: string, findingId: string) => Promise<boolean>;
    linkFinding: (riskId: string, findingId: string) => Promise<boolean>;
    linkAsset: (riskId: string, assetId: string) => Promise<boolean>;
    unlinkAsset: (riskId: string, assetId: string) => Promise<boolean>;
    linkObjective: (riskId: string, objectiveId: string) => Promise<boolean>;
    unlinkObjective: (riskId: string, objectiveId: string) => Promise<boolean>;
}

const useRiskStore = create<RiskStore>((set, get) => ({
    // Variables
    risks: [],
    assetCategories: [],
    riskCategories: [],
    riskSeverities: [],
    riskStatuses: [],
    riskTemplateCategories: [],
    riskTemplateRisks: {},
    linkedAssets: [],
    linkedControls: [],
    linkedFindings: [],
    linkedObjectives: [],
    error: null,

    // Fetch all risks
    fetchRisks: async () => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log(data);
            set({risks: data});
            return true;
        } catch (error) {
            console.error('Error fetching risks:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch risks'
            });
            return false;
        }
    },

    // Fetch all asset categories
    fetchAssetCategories: async () => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/categories`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log(data);
            set({assetCategories: data});
            return true;
        } catch (error) {
            console.error('Error fetching asset categories:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch asset categories'
            });
            return false;
        }
    },

    // Fetch all risk categories
    fetchRiskCategories: async () => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/categories`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log(data);
            set({riskCategories: data});
            return true;
        } catch (error) {
            console.error('Error fetching risk categories:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch risk categories'
            });
            return false;
        }
    },

    // Fetch all risk severities
    fetchRiskSeverities: async () => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/severities`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log(data);
            set({riskSeverities: data});
            return true;
        } catch (error) {
            console.error('Error fetching risk severities:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch risk severities'
            });
            return false;
        }
    },

    // Fetch all risk statuses
    fetchRiskStatuses: async () => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/statuses`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log(data);
            set({riskStatuses: data});
            return true;
        } catch (error) {
            console.error('Error fetching risk statuses:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch risk statuses'
            });
            return false;
        }
    },

    // Fetch risk template categories
    fetchRiskTemplateCategories: async () => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/templates`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            set({riskTemplateCategories: data.categories});
            return true;
        } catch (error) {
            console.error('Error fetching risk template categories:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch risk template categories'
            });
            return false;
        }
    },

    // Fetch risks for a specific template category
    fetchRiskTemplateRisks: async (categoryId: string) => {
        set({error: null});
        try {
            // Check if we already have the risks cached
            const cached = get().riskTemplateRisks[categoryId];
            if (cached) {
                return cached;
            }

            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/templates/${categoryId}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return [];
            }
            const data = await response.json();
            // Cache the risks
            set(state => ({
                riskTemplateRisks: {
                    ...state.riskTemplateRisks,
                    [categoryId]: data.risks
                }
            }));
            return data.risks;
        } catch (error) {
            console.error('Error fetching risk template risks:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch risk template risks'
            });
            return [];
        }
    },

    // Import selected risk templates
    importRiskTemplates: async (
        categoryId: string,
        selectedRisks: RiskTemplateItem[],
        assetCategoryId: string,
        defaultLikelihood: string,
        defaultSeverity: string,
        defaultResidualRisk: string,
        defaultStatus: string,
        scopeName?: string,
        scopeEntityId?: string
    ) => {
        set({error: null});
        const payload = JSON.stringify({
            category_id: categoryId,
            selected_risks: selectedRisks,
            asset_category_id: assetCategoryId,
            default_likelihood: defaultLikelihood,
            default_severity: defaultSeverity,
            default_residual_risk: defaultResidualRisk,
            default_status: defaultStatus,
            scope_name: scopeName,
            scope_entity_id: scopeEntityId
        });
        console.log('Import payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/templates/import`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            const data = await response.json();

            if (!response.ok) {
                set({
                    error: data.detail || 'Failed to import risk templates'
                });
                return {
                    success: false,
                    imported_count: 0,
                    failed_count: selectedRisks.length,
                    message: data.detail || 'Failed to import risk templates',
                    imported_risk_ids: [],
                    errors: [data.detail || 'Failed to import risk templates']
                };
            }

            return data;
        } catch (error) {
            console.error('Error importing risk templates:', error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to import risk templates';
            set({error: errorMessage});
            return {
                success: false,
                imported_count: 0,
                failed_count: selectedRisks.length,
                message: errorMessage,
                imported_risk_ids: [],
                errors: [errorMessage]
            };
        }
    },

    // Create a new risk
    createRisk: async (
        risk_code: string,
        asset_category_id: string,
        risk_category_name: string,
        risk_category_description: string,
        risk_potential_impact: string,
        risk_control: string,
        likelihood: string,
        residual_risk: string,
        risk_severity_id: string,
        risk_status_id: string,
        assessment_status?: string,
        scope_name?: string,
        scope_entity_id?: string
    ) => {
        set({error: null});
        const payload = JSON.stringify({
            risk_code,
            asset_category_id,
            risk_category_name,
            risk_category_description,
            risk_potential_impact,
            risk_control,
            likelihood,
            residual_risk,
            risk_severity_id,
            risk_status_id,
            assessment_status,
            scope_name,
            scope_entity_id
        });
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if (!response.ok) {
                try {
                    const data = await response.json();
                    set({ error: data?.detail || 'Failed to create risk' });
                } catch {
                    set({ error: 'Failed to create risk' });
                }
                return false;
            }

            const newRisk = await response.json();
            set(state => ({risks: [...state.risks, newRisk], error: null}));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to create risk'
            });
            return false;
        }
    },

    // Update an existing risk
    updateRisk: async (
        id: string,
        risk_code: string,
        asset_category_id: string,
        risk_category_name: string,
        risk_category_description: string,
        risk_potential_impact: string,
        risk_control: string,
        likelihood: string,
        residual_risk: string,
        risk_severity_id: string,
        risk_status_id: string,
        assessment_status?: string,
        scope_name?: string,
        scope_entity_id?: string
    ) => {
        set({error: null});
        const payload = JSON.stringify({
            id,
            risk_code,
            asset_category_id,
            risk_category_name,
            risk_category_description,
            risk_potential_impact,
            risk_control,
            likelihood,
            residual_risk,
            risk_severity_id,
            risk_status_id,
            assessment_status,
            scope_name,
            scope_entity_id
        });
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if (!response.ok) {
                try {
                    const data = await response.json();
                    set({ error: data?.detail || 'Failed to update risk' });
                } catch {
                    set({ error: 'Failed to update risk' });
                }
                return false;
            }

            const updatedRisk = await response.json();
            set(state => ({
                risks: state.risks.map(risk => risk.id === id ? updatedRisk : risk),
                error: null
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to update risk'
            });
            return false;
        }
    },

    // Delete a risk
    deleteRisk: async (id: string) => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${id}`, {
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
                        error: errorData.detail || 'Failed to delete risk. Maybe you don\'t have the permissions to delete other user\'s records'
                    });
                } catch {
                    set({
                        error: 'Failed to delete risk. Maybe you don\'t have the permissions to delete other user\'s records'
                    });
                }
                return false;
            }

            set(state => ({
                risks: state.risks.filter(risk => risk.id !== id)
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to delete risk. Maybe you don\'t have the permissions to delete other user\'s records'
            });
            return false;
        }
    },

    // Risk Connection Actions
    fetchLinkedAssets: async (riskId: string) => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/assets`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch linked assets');
            }

            const data = await response.json();
            set({linkedAssets: data});
        } catch (error) {
            console.error('Error fetching linked assets:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch linked assets',
                linkedAssets: []
            });
        }
    },

    fetchLinkedControls: async (riskId: string, frameworkId?: string) => {
        set({error: null});
        try {
            const params = frameworkId ? `?framework_id=${frameworkId}` : '';
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/controls${params}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch linked controls');
            }

            const data = await response.json();
            set({linkedControls: data});
        } catch (error) {
            console.error('Error fetching linked controls:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch linked controls',
                linkedControls: []
            });
        }
    },

    fetchLinkedFindings: async (riskId: string) => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/findings`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch linked findings');
            }

            const data = await response.json();
            set({linkedFindings: data});
        } catch (error) {
            console.error('Error fetching linked findings:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch linked findings',
                linkedFindings: []
            });
        }
    },

    unlinkFinding: async (riskId: string, findingId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/findings/${findingId}`, {
                method: 'DELETE',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            return response.ok;
        } catch (error) {
            console.error('Error unlinking finding:', error);
            return false;
        }
    },

    linkFinding: async (riskId: string, findingId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/findings/${findingId}`, {
                method: 'POST',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            return response.ok;
        } catch (error) {
            console.error('Error linking finding:', error);
            return false;
        }
    },

    fetchLinkedObjectives: async (riskId: string) => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/objectives`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (!response.ok) throw new Error('Failed to fetch linked objectives');
            const data = await response.json();
            set({linkedObjectives: data});
        } catch (error) {
            console.error('Error fetching linked objectives:', error);
            set({ error: error instanceof Error ? error.message : 'Failed to fetch linked objectives', linkedObjectives: [] });
        }
    },

    linkAsset: async (riskId: string, assetId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/assets/${assetId}`, {
                method: 'POST',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            return response.ok;
        } catch (error) {
            console.error('Error linking asset:', error);
            return false;
        }
    },

    unlinkAsset: async (riskId: string, assetId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/assets/${assetId}`, {
                method: 'DELETE',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            return response.ok;
        } catch (error) {
            console.error('Error unlinking asset:', error);
            return false;
        }
    },

    linkObjective: async (riskId: string, objectiveId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/objectives/${objectiveId}`, {
                method: 'POST',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            return response.ok;
        } catch (error) {
            console.error('Error linking objective:', error);
            return false;
        }
    },

    unlinkObjective: async (riskId: string, objectiveId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/objectives/${objectiveId}`, {
                method: 'DELETE',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            return response.ok;
        } catch (error) {
            console.error('Error unlinking objective:', error);
            return false;
        }
    }
}));

export default useRiskStore;
