import {create} from 'zustand';
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

export interface CtiStats {
    totals: {
        indicators: number;
        sightings: number;
        malware_families: number;
        attack_patterns: number;
    };
    suricata: {
        indicators: number;
        sightings: number;
    };
    wazuh: {
        indicators: number;
        sightings: number;
    };
    cape: {
        malware_families: number;
        indicators: number;
    };
}

export interface CtiTimelineEntry {
    date: string;
    suricata: number;
    wazuh: number;
    malware: number;
}

export interface CtiAttackPattern {
    id?: string;
    name: string;
    mitre_id?: string;
    source: string;
    count: number;
    created?: string;
}

export interface CtiAttackPatternsData {
    total: number;
    top_techniques: CtiAttackPattern[];
    by_source: Array<{ source: string; count: number }>;
    recent: CtiAttackPattern[];
}

export interface CtiIndicator {
    id?: string;
    name: string;
    confidence?: number;
    source: string;
    labels?: string[];
    created?: string;
}

export interface CtiIndicatorsData {
    total: number;
    recent: CtiIndicator[];
}

export interface CtiNmapData {
    total: number;
    open_ports: Array<{ port: string; count: number }>;
    by_service: Array<{ service: string; count: number }>;
    by_protocol: Array<{ protocol: string; count: number }>;
    hosts: Array<{ ip: string; status: string; ports: string[]; services: string[] }>;
    recent: any[];
}

export interface CtiZapData {
    total: number;
    by_risk: Record<string, number>;
    by_cwe: Array<{ cwe: string; count: number }>;
    top_vulnerabilities: Array<{ name: string; count: number; risk: string }>;
    recent: any[];
}

export interface CtiSemgrepData {
    total: number;
    by_severity: Record<string, number>;
    by_owasp: Array<{ category: string; count: number }>;
    by_check: Array<{ check: string; count: number }>;
    recent: any[];
}

export interface CtiOsvData {
    total: number;
    by_severity: Record<string, number>;
    by_ecosystem: Array<{ ecosystem: string; count: number }>;
    top_packages: Array<{ package: string; count: number }>;
    recent: any[];
}

export interface CtiHealthData {
    status: string;
    opencti?: string;
    connectors?: Record<string, string>;
}

export interface UseCtiStore {
    // state
    stats: CtiStats | null;
    timeline: CtiTimelineEntry[];
    attackPatterns: CtiAttackPatternsData | null;
    indicators: CtiIndicatorsData | null;
    nmap: CtiNmapData | null;
    zap: CtiZapData | null;
    semgrep: CtiSemgrepData | null;
    osv: CtiOsvData | null;
    health: CtiHealthData | null;
    statsLoading: boolean;
    timelineLoading: boolean;
    attackPatternsLoading: boolean;
    indicatorsLoading: boolean;
    nmapLoading: boolean;
    zapLoading: boolean;
    semgrepLoading: boolean;
    osvLoading: boolean;
    healthLoading: boolean;
    error: string | null;

    // actions
    fetchStats: () => Promise<void>;
    fetchTimeline: (days?: number) => Promise<void>;
    fetchAttackPatterns: () => Promise<void>;
    fetchIndicators: () => Promise<void>;
    fetchNmapResults: () => Promise<void>;
    fetchZapResults: () => Promise<void>;
    fetchSemgrepResults: () => Promise<void>;
    fetchOsvResults: () => Promise<void>;
    checkHealth: () => Promise<void>;
}

const CTI_BASE = `${cyberbridge_back_end_rest_api}/cti`;

const useCtiStore = create<UseCtiStore>((set) => ({
    // state
    stats: null,
    timeline: [],
    attackPatterns: null,
    indicators: null,
    nmap: null,
    zap: null,
    semgrep: null,
    osv: null,
    health: null,
    statsLoading: false,
    timelineLoading: false,
    attackPatternsLoading: false,
    indicatorsLoading: false,
    nmapLoading: false,
    zapLoading: false,
    semgrepLoading: false,
    osvLoading: false,
    healthLoading: false,
    error: null,

    // actions
    fetchStats: async () => {
        set({ statsLoading: true, error: null });
        try {
            const response = await fetch(`${CTI_BASE}/stats`, {
                headers: { ...useAuthStore.getState().getAuthHeader() },
            });
            if (!response.ok) throw new Error('Failed to fetch CTI stats');
            const data = await response.json();
            set({ stats: data, statsLoading: false });
        } catch (error) {
            console.error('Error fetching CTI stats:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch CTI stats',
                statsLoading: false,
            });
        }
    },

    fetchTimeline: async (days: number = 7) => {
        set({ timelineLoading: true, error: null });
        try {
            const response = await fetch(`${CTI_BASE}/timeline?days=${days}`, {
                headers: { ...useAuthStore.getState().getAuthHeader() },
            });
            if (!response.ok) throw new Error('Failed to fetch CTI timeline');
            const data = await response.json();
            set({ timeline: Array.isArray(data) ? data : [], timelineLoading: false });
        } catch (error) {
            console.error('Error fetching CTI timeline:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch CTI timeline',
                timelineLoading: false,
            });
        }
    },

    fetchAttackPatterns: async () => {
        set({ attackPatternsLoading: true, error: null });
        try {
            const response = await fetch(`${CTI_BASE}/attack-patterns`, {
                headers: { ...useAuthStore.getState().getAuthHeader() },
            });
            if (!response.ok) throw new Error('Failed to fetch attack patterns');
            const data = await response.json();
            set({ attackPatterns: data, attackPatternsLoading: false });
        } catch (error) {
            console.error('Error fetching attack patterns:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch attack patterns',
                attackPatternsLoading: false,
            });
        }
    },

    fetchIndicators: async () => {
        set({ indicatorsLoading: true, error: null });
        try {
            const response = await fetch(`${CTI_BASE}/indicators`, {
                headers: { ...useAuthStore.getState().getAuthHeader() },
            });
            if (!response.ok) throw new Error('Failed to fetch indicators');
            const data = await response.json();
            set({ indicators: data, indicatorsLoading: false });
        } catch (error) {
            console.error('Error fetching indicators:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch indicators',
                indicatorsLoading: false,
            });
        }
    },

    fetchNmapResults: async () => {
        set({ nmapLoading: true, error: null });
        try {
            const response = await fetch(`${CTI_BASE}/nmap/results`, {
                headers: { ...useAuthStore.getState().getAuthHeader() },
            });
            if (!response.ok) throw new Error('Failed to fetch Nmap results');
            const data = await response.json();
            set({ nmap: data, nmapLoading: false });
        } catch (error) {
            console.error('Error fetching Nmap results:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch Nmap results',
                nmapLoading: false,
            });
        }
    },

    fetchZapResults: async () => {
        set({ zapLoading: true, error: null });
        try {
            const response = await fetch(`${CTI_BASE}/zap/results`, {
                headers: { ...useAuthStore.getState().getAuthHeader() },
            });
            if (!response.ok) throw new Error('Failed to fetch ZAP results');
            const data = await response.json();
            set({ zap: data, zapLoading: false });
        } catch (error) {
            console.error('Error fetching ZAP results:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch ZAP results',
                zapLoading: false,
            });
        }
    },

    fetchSemgrepResults: async () => {
        set({ semgrepLoading: true, error: null });
        try {
            const response = await fetch(`${CTI_BASE}/semgrep/results`, {
                headers: { ...useAuthStore.getState().getAuthHeader() },
            });
            if (!response.ok) throw new Error('Failed to fetch Semgrep results');
            const data = await response.json();
            set({ semgrep: data, semgrepLoading: false });
        } catch (error) {
            console.error('Error fetching Semgrep results:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch Semgrep results',
                semgrepLoading: false,
            });
        }
    },

    fetchOsvResults: async () => {
        set({ osvLoading: true, error: null });
        try {
            const response = await fetch(`${CTI_BASE}/osv/results`, {
                headers: { ...useAuthStore.getState().getAuthHeader() },
            });
            if (!response.ok) throw new Error('Failed to fetch OSV results');
            const data = await response.json();
            set({ osv: data, osvLoading: false });
        } catch (error) {
            console.error('Error fetching OSV results:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch OSV results',
                osvLoading: false,
            });
        }
    },

    checkHealth: async () => {
        set({ healthLoading: true, error: null });
        try {
            const response = await fetch(`${CTI_BASE}/health`, {
                headers: { ...useAuthStore.getState().getAuthHeader() },
            });
            if (!response.ok) throw new Error('Failed to check CTI health');
            const data = await response.json();
            set({ health: data, healthLoading: false });
        } catch (error) {
            console.error('Error checking CTI health:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to check CTI health',
                healthLoading: false,
            });
        }
    },
}));

export default useCtiStore;
