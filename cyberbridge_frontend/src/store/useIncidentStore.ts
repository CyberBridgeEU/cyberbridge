import {create} from "zustand";
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

export interface IncidentStatus {
    id: string;
    incident_status_name: string;
}

export interface RiskSeverity {
    id: string;
    risk_severity_name: string;
}

export interface Incident {
    id: string;
    incident_code: string | null;
    title: string;
    description: string | null;
    incident_severity_id: string;
    incident_status_id: string;
    reported_by: string | null;
    assigned_to: string | null;
    discovered_at: string | null;
    resolved_at: string | null;
    containment_actions: string | null;
    root_cause: string | null;
    remediation_steps: string | null;
    ai_analysis: string | null;
    vulnerability_source: string | null;
    cvss_score: number | null;
    cve_id: string | null;
    cwe_id: string | null;
    euvd_vulnerability_id: string | null;
    triage_status: string | null;
    sla_deadline: string | null;
    sla_status: string | null;
    affected_products: string | null;
    organisation_id: string | null;
    created_at: string;
    updated_at: string;
    incident_severity: string | null;
    incident_status: string | null;
    last_updated_by_email: string | null;
    linked_frameworks_count: number;
    linked_risks_count: number;
    linked_assets_count: number;
}

export interface LinkedFramework {
    id: string;
    name: string;
    description: string | null;
}

export interface LinkedRisk {
    id: string;
    risk_code: string | null;
    risk_category_name: string;
    risk_severity: string | null;
    risk_status: string | null;
}

export interface LinkedAsset {
    id: string;
    name: string;
    description: string | null;
    ip_address: string | null;
    asset_type_name: string | null;
    status_name: string | null;
}

export interface IncidentPatch {
    id: string;
    incident_id: string;
    patch_version: string;
    description: string | null;
    release_date: string | null;
    target_sla_date: string | null;
    actual_resolution_date: string | null;
    sla_compliance: string | null;
    organisation_id: string | null;
    created_at: string;
    updated_at: string;
}

export interface ENISANotification {
    id: string;
    incident_id: string;
    early_warning_required: boolean;
    early_warning_deadline: string | null;
    early_warning_submitted: boolean;
    early_warning_submitted_at: string | null;
    early_warning_content: string | null;
    vuln_notification_required: boolean;
    vuln_notification_deadline: string | null;
    vuln_notification_submitted: boolean;
    vuln_notification_submitted_at: string | null;
    vuln_notification_content: string | null;
    final_report_required: boolean;
    final_report_deadline: string | null;
    final_report_submitted: boolean;
    final_report_submitted_at: string | null;
    final_report_content: string | null;
    reporting_status: string | null;
    organisation_id: string | null;
    created_at: string;
    updated_at: string;
}

export interface ForensicTimelineEvent {
    timestamp: string | null;
    event_type: 'incident_created' | 'field_updated' | 'patch_released' | 'enisa_notification' | 'advisory_published' | 'evidence_linked';
    title: string;
    description: string;
    actor: string | null;
    metadata: Record<string, any>;
}

export interface LinkedEvidence {
    id: string;
    name: string;
    evidence_type: string;
    custody_status: string | null;
    collection_method: string | null;
    status: string;
    linked_at: string | null;
}

export interface PostMarketMetrics {
    total_incidents: number;
    open_vulnerabilities: number;
    overdue_count: number;
    at_risk_count: number;
    avg_resolution_hours: number | null;
    sla_compliance_rate: number | null;
    patches_released: number;
    advisories_published: number;
    enisa_pending: number;
    enisa_complete: number;
    aging_0_24h: number;
    aging_24_72h: number;
    aging_72h_7d: number;
    aging_7d_plus: number;
}

export interface IncidentStore {
    incidents: Incident[];
    incidentStatuses: IncidentStatus[];
    riskSeverities: RiskSeverity[];
    linkedFrameworks: LinkedFramework[];
    linkedRisks: LinkedRisk[];
    linkedAssets: LinkedAsset[];
    analyzing: boolean;
    error: string | null;
    patches: IncidentPatch[];
    enisaNotification: ENISANotification | null;
    postMarketMetrics: PostMarketMetrics | null;
    metricsLoading: boolean;
    forensicTimeline: ForensicTimelineEvent[];
    timelineLoading: boolean;
    linkedEvidence: LinkedEvidence[];

    fetchIncidents: () => Promise<boolean>;
    fetchIncidentStatuses: () => Promise<boolean>;
    fetchRiskSeverities: () => Promise<boolean>;
    createIncident: (incident: Partial<Incident>) => Promise<boolean>;
    updateIncident: (id: string, incident: Partial<Incident>) => Promise<boolean>;
    deleteIncident: (id: string) => Promise<boolean>;
    analyzeIncident: (id: string) => Promise<string | null>;

    fetchLinkedFrameworks: (incidentId: string) => Promise<void>;
    linkFramework: (incidentId: string, frameworkId: string) => Promise<boolean>;
    unlinkFramework: (incidentId: string, frameworkId: string) => Promise<boolean>;
    fetchLinkedRisks: (incidentId: string) => Promise<void>;
    linkRisk: (incidentId: string, riskId: string) => Promise<boolean>;
    unlinkRisk: (incidentId: string, riskId: string) => Promise<boolean>;
    fetchLinkedAssets: (incidentId: string) => Promise<void>;
    linkAsset: (incidentId: string, assetId: string) => Promise<boolean>;
    unlinkAsset: (incidentId: string, assetId: string) => Promise<boolean>;

    fetchPatches: (incidentId: string) => Promise<void>;
    createPatch: (incidentId: string, data: any) => Promise<boolean>;
    updatePatch: (patchId: string, data: any) => Promise<boolean>;
    deletePatch: (patchId: string) => Promise<boolean>;
    fetchENISANotification: (incidentId: string) => Promise<void>;
    createENISANotification: (incidentId: string, data?: any) => Promise<boolean>;
    updateENISANotification: (notificationId: string, data: any) => Promise<boolean>;
    fetchPostMarketMetrics: () => Promise<void>;
    fetchForensicTimeline: (incidentId: string) => Promise<void>;
    fetchLinkedEvidence: (incidentId: string) => Promise<void>;
    linkEvidence: (incidentId: string, evidenceId: string) => Promise<boolean>;
    unlinkEvidence: (incidentId: string, evidenceId: string) => Promise<boolean>;
}

const useIncidentStore = create<IncidentStore>((set) => ({
    incidents: [],
    incidentStatuses: [],
    riskSeverities: [],
    linkedFrameworks: [],
    linkedRisks: [],
    linkedAssets: [],
    analyzing: false,
    error: null,
    patches: [],
    enisaNotification: null,
    postMarketMetrics: null,
    metricsLoading: false,
    forensicTimeline: [],
    timelineLoading: false,
    linkedEvidence: [],

    fetchIncidents: async () => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (!response.ok) return false;
            const data = await response.json();
            set({incidents: data});
            return true;
        } catch (error) {
            console.error('Error fetching incidents:', error);
            set({ error: error instanceof Error ? error.message : 'Failed to fetch incidents' });
            return false;
        }
    },

    fetchIncidentStatuses: async () => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/statuses`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (!response.ok) return false;
            const data = await response.json();
            set({incidentStatuses: data});
            return true;
        } catch (error) {
            console.error('Error fetching incident statuses:', error);
            set({ error: error instanceof Error ? error.message : 'Failed to fetch incident statuses' });
            return false;
        }
    },

    fetchRiskSeverities: async () => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/severities`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (!response.ok) return false;
            const data = await response.json();
            set({riskSeverities: data});
            return true;
        } catch (error) {
            console.error('Error fetching risk severities:', error);
            set({ error: error instanceof Error ? error.message : 'Failed to fetch risk severities' });
            return false;
        }
    },

    createIncident: async (incident) => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify(incident)
            });
            if (!response.ok) {
                try {
                    const data = await response.json();
                    set({ error: data?.detail || 'Failed to create incident' });
                } catch {
                    set({ error: 'Failed to create incident' });
                }
                return false;
            }
            const newIncident = await response.json();
            set(state => ({incidents: [...state.incidents, newIncident], error: null}));
            return true;
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to create incident' });
            return false;
        }
    },

    updateIncident: async (id, incident) => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify(incident)
            });
            if (!response.ok) {
                try {
                    const data = await response.json();
                    set({ error: data?.detail || 'Failed to update incident' });
                } catch {
                    set({ error: 'Failed to update incident' });
                }
                return false;
            }
            const updatedIncident = await response.json();
            set(state => ({
                incidents: state.incidents.map(i => i.id === id ? updatedIncident : i),
                error: null
            }));
            return true;
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to update incident' });
            return false;
        }
    },

    deleteIncident: async (id) => {
        set({error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${id}`, {
                method: 'DELETE',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (!response.ok) {
                try {
                    const errorData = await response.json();
                    set({ error: errorData.detail || 'Failed to delete incident' });
                } catch {
                    set({ error: 'Failed to delete incident' });
                }
                return false;
            }
            set(state => ({ incidents: state.incidents.filter(i => i.id !== id) }));
            return true;
        } catch (error) {
            set({ error: error instanceof Error ? error.message : 'Failed to delete incident' });
            return false;
        }
    },

    analyzeIncident: async (id) => {
        set({analyzing: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${id}/analyze`, {
                method: 'POST',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (!response.ok) {
                set({ error: 'Failed to analyze incident', analyzing: false });
                return null;
            }
            const data = await response.json();
            // Update the incident in the store with the analysis
            set(state => ({
                incidents: state.incidents.map(i => i.id === id ? {...i, ai_analysis: data.analysis} : i),
                analyzing: false
            }));
            return data.analysis;
        } catch (error) {
            console.error('Error analyzing incident:', error);
            set({ error: error instanceof Error ? error.message : 'Failed to analyze incident', analyzing: false });
            return null;
        }
    },

    // Connection actions
    fetchLinkedFrameworks: async (incidentId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/frameworks`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.ok) {
                const data = await response.json();
                set({linkedFrameworks: data});
            }
        } catch (error) {
            console.error('Error fetching linked frameworks:', error);
            set({linkedFrameworks: []});
        }
    },

    linkFramework: async (incidentId, frameworkId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/frameworks/${frameworkId}`, {
                method: 'POST',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            return response.ok;
        } catch (error) {
            console.error('Error linking framework:', error);
            return false;
        }
    },

    unlinkFramework: async (incidentId, frameworkId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/frameworks/${frameworkId}`, {
                method: 'DELETE',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            return response.ok;
        } catch (error) {
            console.error('Error unlinking framework:', error);
            return false;
        }
    },

    fetchLinkedRisks: async (incidentId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/risks`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.ok) {
                const data = await response.json();
                set({linkedRisks: data});
            }
        } catch (error) {
            console.error('Error fetching linked risks:', error);
            set({linkedRisks: []});
        }
    },

    linkRisk: async (incidentId, riskId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/risks/${riskId}`, {
                method: 'POST',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            return response.ok;
        } catch (error) {
            console.error('Error linking risk:', error);
            return false;
        }
    },

    unlinkRisk: async (incidentId, riskId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/risks/${riskId}`, {
                method: 'DELETE',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            return response.ok;
        } catch (error) {
            console.error('Error unlinking risk:', error);
            return false;
        }
    },

    fetchLinkedAssets: async (incidentId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/assets`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.ok) {
                const data = await response.json();
                set({linkedAssets: data});
            }
        } catch (error) {
            console.error('Error fetching linked assets:', error);
            set({linkedAssets: []});
        }
    },

    linkAsset: async (incidentId, assetId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/assets/${assetId}`, {
                method: 'POST',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            return response.ok;
        } catch (error) {
            console.error('Error linking asset:', error);
            return false;
        }
    },

    unlinkAsset: async (incidentId, assetId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/assets/${assetId}`, {
                method: 'DELETE',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            return response.ok;
        } catch (error) {
            console.error('Error unlinking asset:', error);
            return false;
        }
    },

    // Patch tracking
    fetchPatches: async (incidentId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/patches`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.ok) {
                const data = await response.json();
                set({ patches: data });
            }
        } catch (error) {
            console.error('Error fetching patches:', error);
            set({ patches: [] });
        }
    },

    createPatch: async (incidentId, data) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/patches`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...useAuthStore.getState().getAuthHeader() },
                body: JSON.stringify(data)
            });
            if (!response.ok) return false;
            const patch = await response.json();
            set(state => ({ patches: [...state.patches, patch] }));
            return true;
        } catch (error) {
            console.error('Error creating patch:', error);
            return false;
        }
    },

    updatePatch: async (patchId, data) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/patches/${patchId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...useAuthStore.getState().getAuthHeader() },
                body: JSON.stringify(data)
            });
            if (!response.ok) return false;
            const updated = await response.json();
            set(state => ({ patches: state.patches.map(p => p.id === patchId ? updated : p) }));
            return true;
        } catch (error) {
            console.error('Error updating patch:', error);
            return false;
        }
    },

    deletePatch: async (patchId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/patches/${patchId}`, {
                method: 'DELETE',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (!response.ok) return false;
            set(state => ({ patches: state.patches.filter(p => p.id !== patchId) }));
            return true;
        } catch (error) {
            console.error('Error deleting patch:', error);
            return false;
        }
    },

    // ENISA notifications
    fetchENISANotification: async (incidentId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/enisa`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.ok) {
                const data = await response.json();
                set({ enisaNotification: data });
            } else {
                set({ enisaNotification: null });
            }
        } catch (error) {
            console.error('Error fetching ENISA notification:', error);
            set({ enisaNotification: null });
        }
    },

    createENISANotification: async (incidentId, data = {}) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/enisa`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...useAuthStore.getState().getAuthHeader() },
                body: JSON.stringify(data)
            });
            if (!response.ok) return false;
            const notification = await response.json();
            set({ enisaNotification: notification });
            return true;
        } catch (error) {
            console.error('Error creating ENISA notification:', error);
            return false;
        }
    },

    updateENISANotification: async (notificationId, data) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/enisa/${notificationId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...useAuthStore.getState().getAuthHeader() },
                body: JSON.stringify(data)
            });
            if (!response.ok) return false;
            const updated = await response.json();
            set({ enisaNotification: updated });
            return true;
        } catch (error) {
            console.error('Error updating ENISA notification:', error);
            return false;
        }
    },

    // Forensic timeline
    fetchForensicTimeline: async (incidentId) => {
        set({ timelineLoading: true });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/timeline`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.ok) {
                const data = await response.json();
                set({ forensicTimeline: data.events || [], timelineLoading: false });
            } else {
                set({ forensicTimeline: [], timelineLoading: false });
            }
        } catch (error) {
            console.error('Error fetching forensic timeline:', error);
            set({ forensicTimeline: [], timelineLoading: false });
        }
    },

    fetchLinkedEvidence: async (incidentId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/evidence`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.ok) {
                const data = await response.json();
                set({ linkedEvidence: data });
            } else {
                set({ linkedEvidence: [] });
            }
        } catch (error) {
            console.error('Error fetching linked evidence:', error);
            set({ linkedEvidence: [] });
        }
    },

    linkEvidence: async (incidentId, evidenceId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/evidence/${evidenceId}`, {
                method: 'POST',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            return response.ok;
        } catch (error) {
            console.error('Error linking evidence:', error);
            return false;
        }
    },

    unlinkEvidence: async (incidentId, evidenceId) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/${incidentId}/evidence/${evidenceId}`, {
                method: 'DELETE',
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            return response.ok;
        } catch (error) {
            console.error('Error unlinking evidence:', error);
            return false;
        }
    },

    // Post-market metrics
    fetchPostMarketMetrics: async () => {
        set({ metricsLoading: true });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/incidents/metrics/post-market`, {
                headers: { ...useAuthStore.getState().getAuthHeader() }
            });
            if (response.ok) {
                const data = await response.json();
                set({ postMarketMetrics: data, metricsLoading: false });
            } else {
                set({ metricsLoading: false });
            }
        } catch (error) {
            console.error('Error fetching post-market metrics:', error);
            set({ metricsLoading: false });
        }
    }
}));

export default useIncidentStore;
