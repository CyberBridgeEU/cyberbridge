// src/store/useAssetStore.ts
import { create } from 'zustand';
import useAuthStore from './useAuthStore';
import { cyberbridge_back_end_rest_api } from "../constants/urls";

// Asset Type interface
export interface AssetType {
    id: string;
    name: string;
    icon_name: string | null;
    description: string | null;
    default_confidentiality: string | null;
    default_integrity: string | null;
    default_availability: string | null;
    default_asset_value: string | null;
    organisation_id: string;
    asset_count: number;
    risk_count: number;
    risk_level: 'Low' | 'Medium' | 'Severe';
    created_at?: string;
    updated_at?: string;
}

// Asset Status interface
export interface AssetStatus {
    id: string;
    status: string;
}

// Economic Operator interface
export interface EconomicOperator {
    id: string;
    name: string;
}

// Criticality Option interface
export interface CriticalityOption {
    id: string;
    criticality_id: string;
    value: string;
    created_at: string;
    updated_at: string;
}

// Criticality interface
export interface Criticality {
    id: string;
    label: string;
    options: CriticalityOption[];
    created_at: string;
    updated_at: string;
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

// Asset interface
export interface Asset {
    id: string;
    name: string;
    version: string | null;
    justification: string | null;
    license_model: string | null;
    description: string | null;
    sbom: string | null;
    ip_address: string | null;  // IP address, IP range, or URL
    asset_type_id: string;
    asset_type_name: string | null;
    asset_type_icon: string | null;
    asset_status_id: string | null;
    status_name: string | null;
    economic_operator_id: string | null;
    economic_operator_name: string | null;
    criticality_id: string | null;
    criticality_label: string | null;
    criticality_option: string | null;
    // CIA fields
    confidentiality: string | null;
    integrity: string | null;
    availability: string | null;
    asset_value: string | null;
    inherit_cia: boolean;
    overall_asset_value: string | null;
    organisation_id: string;
    created_at: string;
    updated_at: string;
    last_updated_by_email: string | null;
    // Scan status fields
    has_scan: boolean;
    last_scan_date: string | null;
    last_scan_status: string | null;  // 'completed', 'failed', 'in_progress'
    last_scan_type: string | null;  // e.g., 'basic', 'aggressive', 'spider', 'active'
    last_scan_scanner: string | null;  // 'nmap', 'zap', etc.
    // Separate status for Network and Application scans
    network_scan_status: string | null;
    network_scan_date: string | null;
    application_scan_status: string | null;
    application_scan_date: string | null;
}

interface AssetStore {
    assets: Asset[];
    assetTypes: AssetType[];
    assetStatuses: AssetStatus[];
    economicOperators: EconomicOperator[];
    criticalities: Criticality[];
    linkedRisks: LinkedRisk[];
    loading: boolean;
    error: string | null;

    // Asset Type Actions
    fetchAssetTypes: () => Promise<void>;
    createAssetType: (name: string, iconName?: string, description?: string, defaultConfidentiality?: string, defaultIntegrity?: string, defaultAvailability?: string, defaultAssetValue?: string) => Promise<{ success: boolean; error?: string }>;
    updateAssetType: (id: string, name: string, iconName?: string, description?: string, defaultConfidentiality?: string, defaultIntegrity?: string, defaultAvailability?: string, defaultAssetValue?: string) => Promise<{ success: boolean; error?: string }>;
    deleteAssetType: (id: string) => Promise<{ success: boolean; error?: string }>;
    seedDefaultAssetTypes: () => Promise<{ success: boolean; message?: string; error?: string }>;

    // Lookup Data Actions
    fetchAssetStatuses: () => Promise<void>;
    fetchEconomicOperators: () => Promise<void>;
    fetchCriticalities: () => Promise<void>;

    // Asset Actions
    fetchAssets: (assetTypeId?: string) => Promise<void>;
    createAsset: (
        name: string,
        assetTypeId: string,
        description?: string,
        ipAddress?: string,
        version?: string,
        justification?: string,
        licenseModel?: string,
        sbom?: string,
        assetStatusId?: string,
        economicOperatorId?: string,
        criticalityId?: string,
        criticalityOption?: string,
        confidentiality?: string,
        integrity?: string,
        availability?: string,
        assetValue?: string,
        inheritCia?: boolean
    ) => Promise<{ success: boolean; error?: string }>;
    updateAsset: (
        id: string,
        name: string,
        assetTypeId: string,
        description?: string,
        ipAddress?: string,
        version?: string,
        justification?: string,
        licenseModel?: string,
        sbom?: string,
        assetStatusId?: string,
        economicOperatorId?: string,
        criticalityId?: string,
        criticalityOption?: string,
        confidentiality?: string,
        integrity?: string,
        availability?: string,
        assetValue?: string,
        inheritCia?: boolean
    ) => Promise<{ success: boolean; error?: string }>;
    deleteAsset: (id: string) => Promise<{ success: boolean; error?: string }>;

    // Asset-Risk Connection Actions
    fetchLinkedRisks: (assetId: string) => Promise<void>;
    linkAssetToRisk: (assetId: string, riskId: string) => Promise<{ success: boolean; error?: string }>;
    unlinkAssetFromRisk: (assetId: string, riskId: string) => Promise<{ success: boolean; error?: string }>;
}

const useAssetStore = create<AssetStore>((set) => ({
    assets: [],
    assetTypes: [],
    assetStatuses: [],
    economicOperators: [],
    criticalities: [],
    linkedRisks: [],
    loading: false,
    error: null,

    // Asset Type Actions
    fetchAssetTypes: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/types`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch asset types');
            }

            const data = await response.json();
            set({
                assetTypes: data,
                loading: false
            });
        } catch (error) {
            console.error('Error fetching asset types:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch asset types',
                loading: false
            });
        }
    },

    createAssetType: async (name: string, iconName?: string, description?: string, defaultConfidentiality?: string, defaultIntegrity?: string, defaultAvailability?: string, defaultAssetValue?: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/types`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    name,
                    icon_name: iconName,
                    description,
                    default_confidentiality: defaultConfidentiality || null,
                    default_integrity: defaultIntegrity || null,
                    default_availability: defaultAvailability || null,
                    default_asset_value: defaultAssetValue || null
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create asset type');
            }

            const newAssetType = await response.json();
            set(state => ({
                assetTypes: [...state.assetTypes, newAssetType],
                loading: false
            }));
            return { success: true };
        } catch (error) {
            console.error('Error creating asset type:', error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to create asset type';
            set({
                error: errorMessage,
                loading: false
            });
            return { success: false, error: errorMessage };
        }
    },

    updateAssetType: async (id: string, name: string, iconName?: string, description?: string, defaultConfidentiality?: string, defaultIntegrity?: string, defaultAvailability?: string, defaultAssetValue?: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/types/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    name,
                    icon_name: iconName,
                    description,
                    default_confidentiality: defaultConfidentiality || null,
                    default_integrity: defaultIntegrity || null,
                    default_availability: defaultAvailability || null,
                    default_asset_value: defaultAssetValue || null
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update asset type');
            }

            const updatedAssetType = await response.json();
            set(state => ({
                assetTypes: state.assetTypes.map(at =>
                    at.id === updatedAssetType.id ? updatedAssetType : at
                ),
                loading: false
            }));
            return { success: true };
        } catch (error) {
            console.error('Error updating asset type:', error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to update asset type';
            set({
                error: errorMessage,
                loading: false
            });
            return { success: false, error: errorMessage };
        }
    },

    deleteAssetType: async (id: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/types/${id}`, {
                method: 'DELETE',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to delete asset type');
            }

            set(state => ({
                assetTypes: state.assetTypes.filter(at => at.id !== id),
                loading: false
            }));
            return { success: true };
        } catch (error) {
            console.error('Error deleting asset type:', error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to delete asset type';
            set({
                error: errorMessage,
                loading: false
            });
            return { success: false, error: errorMessage };
        }
    },

    seedDefaultAssetTypes: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/types/seed-defaults`, {
                method: 'POST',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to seed default asset types');
            }

            const data = await response.json();

            // Refresh asset types list
            const typesResponse = await fetch(`${cyberbridge_back_end_rest_api}/assets/types`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (typesResponse.ok) {
                const typesData = await typesResponse.json();
                set({ assetTypes: typesData });
            }

            set({ loading: false });
            return { success: true, message: data.message };
        } catch (error) {
            console.error('Error seeding default asset types:', error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to seed default asset types';
            set({
                error: errorMessage,
                loading: false
            });
            return { success: false, error: errorMessage };
        }
    },

    // Lookup Data Actions
    fetchAssetStatuses: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/statuses`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch asset statuses');
            }

            const data = await response.json();
            set({
                assetStatuses: data,
                loading: false
            });
        } catch (error) {
            console.error('Error fetching asset statuses:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch asset statuses',
                loading: false
            });
        }
    },

    fetchEconomicOperators: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/economic-operators`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch economic operators');
            }

            const data = await response.json();
            set({
                economicOperators: data,
                loading: false
            });
        } catch (error) {
            console.error('Error fetching economic operators:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch economic operators',
                loading: false
            });
        }
    },

    fetchCriticalities: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/criticalities`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch criticalities');
            }

            const data = await response.json();
            set({
                criticalities: data,
                loading: false
            });
        } catch (error) {
            console.error('Error fetching criticalities:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch criticalities',
                loading: false
            });
        }
    },

    // Asset Actions
    fetchAssets: async (assetTypeId?: string) => {
        set({ loading: true, error: null });
        try {
            const url = assetTypeId
                ? `${cyberbridge_back_end_rest_api}/assets?asset_type_id=${assetTypeId}`
                : `${cyberbridge_back_end_rest_api}/assets`;

            const response = await fetch(url, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch assets');
            }

            const data = await response.json();
            set({
                assets: data,
                loading: false
            });
        } catch (error) {
            console.error('Error fetching assets:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch assets',
                loading: false
            });
        }
    },

    createAsset: async (
        name: string,
        assetTypeId: string,
        description?: string,
        ipAddress?: string,
        version?: string,
        justification?: string,
        licenseModel?: string,
        sbom?: string,
        assetStatusId?: string,
        economicOperatorId?: string,
        criticalityId?: string,
        criticalityOption?: string,
        confidentiality?: string,
        integrity?: string,
        availability?: string,
        assetValue?: string,
        inheritCia?: boolean
    ) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    name,
                    asset_type_id: assetTypeId,
                    description,
                    ip_address: ipAddress,
                    version,
                    justification,
                    license_model: licenseModel,
                    sbom,
                    asset_status_id: assetStatusId,
                    economic_operator_id: economicOperatorId,
                    criticality_id: criticalityId,
                    criticality_option: criticalityOption,
                    confidentiality: confidentiality || null,
                    integrity: integrity || null,
                    availability: availability || null,
                    asset_value: assetValue || null,
                    inherit_cia: inheritCia !== undefined ? inheritCia : true
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create asset');
            }

            const newAsset = await response.json();
            set(state => ({
                assets: [...state.assets, newAsset],
                loading: false
            }));
            return { success: true };
        } catch (error) {
            console.error('Error creating asset:', error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to create asset';
            set({
                error: errorMessage,
                loading: false
            });
            return { success: false, error: errorMessage };
        }
    },

    updateAsset: async (
        id: string,
        name: string,
        assetTypeId: string,
        description?: string,
        ipAddress?: string,
        version?: string,
        justification?: string,
        licenseModel?: string,
        sbom?: string,
        assetStatusId?: string,
        economicOperatorId?: string,
        criticalityId?: string,
        criticalityOption?: string,
        confidentiality?: string,
        integrity?: string,
        availability?: string,
        assetValue?: string,
        inheritCia?: boolean
    ) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    name,
                    asset_type_id: assetTypeId,
                    description,
                    ip_address: ipAddress,
                    version,
                    justification,
                    license_model: licenseModel,
                    sbom,
                    asset_status_id: assetStatusId,
                    economic_operator_id: economicOperatorId,
                    criticality_id: criticalityId,
                    criticality_option: criticalityOption,
                    confidentiality: confidentiality || null,
                    integrity: integrity || null,
                    availability: availability || null,
                    asset_value: assetValue || null,
                    inherit_cia: inheritCia !== undefined ? inheritCia : true
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update asset');
            }

            const updatedAsset = await response.json();
            set(state => ({
                assets: state.assets.map(a =>
                    a.id === updatedAsset.id ? updatedAsset : a
                ),
                loading: false
            }));
            return { success: true };
        } catch (error) {
            console.error('Error updating asset:', error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to update asset';
            set({
                error: errorMessage,
                loading: false
            });
            return { success: false, error: errorMessage };
        }
    },

    deleteAsset: async (id: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/${id}`, {
                method: 'DELETE',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to delete asset');
            }

            set(state => ({
                assets: state.assets.filter(a => a.id !== id),
                loading: false
            }));
            return { success: true };
        } catch (error) {
            console.error('Error deleting asset:', error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to delete asset';
            set({
                error: errorMessage,
                loading: false
            });
            return { success: false, error: errorMessage };
        }
    },

    // Asset-Risk Connection Actions
    fetchLinkedRisks: async (assetId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/${assetId}/risks`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch linked risks');
            }

            const data = await response.json();
            set({
                linkedRisks: data,
                loading: false
            });
        } catch (error) {
            console.error('Error fetching linked risks:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch linked risks',
                linkedRisks: [],
                loading: false
            });
        }
    },

    linkAssetToRisk: async (assetId: string, riskId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/${assetId}/risks/${riskId}`, {
                method: 'POST',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to link asset to risk');
            }

            set({ loading: false });
            return { success: true };
        } catch (error) {
            console.error('Error linking asset to risk:', error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to link asset to risk';
            set({
                error: errorMessage,
                loading: false
            });
            return { success: false, error: errorMessage };
        }
    },

    unlinkAssetFromRisk: async (assetId: string, riskId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/${assetId}/risks/${riskId}`, {
                method: 'DELETE',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to unlink asset from risk');
            }

            set({ loading: false });
            return { success: true };
        } catch (error) {
            console.error('Error unlinking asset from risk:', error);
            const errorMessage = error instanceof Error ? error.message : 'Failed to unlink asset from risk';
            set({
                error: errorMessage,
                loading: false
            });
            return { success: false, error: errorMessage };
        }
    }
}));

export default useAssetStore;
