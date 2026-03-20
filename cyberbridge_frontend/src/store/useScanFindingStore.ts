import { create } from "zustand";
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

export interface ScanFindingWithCVE {
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
    extra_data: string | null;
    cve_description: string | null;
    cvss_v31_score: number | null;
    cvss_v31_severity: string | null;
    cve_published: string | null;
    linked_risks_count: number;
    is_remediated: boolean;
    remediated_at: string | null;
    remediated_by: string | null;
    scan_target: string | null;
    scan_timestamp: string | null;
    created_at: string | null;
}

export interface ScanFindingsStats {
    total: number;
    by_scanner: Record<string, number>;
    by_severity: Record<string, number>;
    linked_to_risks: number;
    remediated: number;
}

interface Filters {
    scanner_type: string | null;
    severity: string | null;
    has_risks: boolean | null;
    is_remediated: boolean | null;
    search: string | null;
}

interface ScanFindingStore {
    findings: ScanFindingWithCVE[];
    total: number;
    offset: number;
    limit: number;
    loading: boolean;
    stats: ScanFindingsStats | null;
    statsLoading: boolean;
    filters: Filters;
    error: string | null;

    fetchFindings: () => Promise<void>;
    fetchStats: () => Promise<void>;
    toggleRemediation: (findingId: string) => Promise<void>;
    setFilters: (filters: Partial<Filters>) => void;
    resetFilters: () => void;
    setOffset: (offset: number) => void;
}

const defaultFilters: Filters = {
    scanner_type: null,
    severity: null,
    has_risks: null,
    is_remediated: null,
    search: null,
};

const useScanFindingStore = create<ScanFindingStore>((set, get) => ({
    findings: [],
    total: 0,
    offset: 0,
    limit: 50,
    loading: false,
    stats: null,
    statsLoading: false,
    filters: { ...defaultFilters },
    error: null,

    fetchFindings: async () => {
        set({ loading: true, error: null });
        try {
            const { filters, offset, limit } = get();
            const params = new URLSearchParams();
            if (filters.scanner_type) params.set("scanner_type", filters.scanner_type);
            if (filters.severity) params.set("severity", filters.severity);
            if (filters.has_risks !== null) params.set("has_risks", String(filters.has_risks));
            if (filters.is_remediated !== null) params.set("is_remediated", String(filters.is_remediated));
            if (filters.search) params.set("search", filters.search);
            params.set("offset", String(offset));
            params.set("limit", String(limit));

            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/scanners/findings?${params.toString()}`,
                { headers: { ...useAuthStore.getState().getAuthHeader() } }
            );

            if (!response.ok) throw new Error("Failed to fetch findings");

            const data = await response.json();
            set({
                findings: data.findings,
                total: data.total,
                offset: data.offset,
                limit: data.limit,
                loading: false,
            });
        } catch (error) {
            console.error("Error fetching findings:", error);
            set({
                error: error instanceof Error ? error.message : "Failed to fetch findings",
                loading: false,
            });
        }
    },

    fetchStats: async () => {
        set({ statsLoading: true });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/scanners/findings/stats`,
                { headers: { ...useAuthStore.getState().getAuthHeader() } }
            );

            if (!response.ok) throw new Error("Failed to fetch stats");

            const data = await response.json();
            set({ stats: data, statsLoading: false });
        } catch (error) {
            console.error("Error fetching findings stats:", error);
            set({ statsLoading: false });
        }
    },

    toggleRemediation: async (findingId: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/scanners/findings/${findingId}/remediate`,
                {
                    method: "PATCH",
                    headers: { ...useAuthStore.getState().getAuthHeader() },
                }
            );

            if (!response.ok) throw new Error("Failed to toggle remediation");

            const data = await response.json();
            // Update the finding in-place without re-fetching
            set((state) => ({
                findings: state.findings.map((f) =>
                    f.id === findingId
                        ? { ...f, is_remediated: data.is_remediated, remediated_at: data.remediated_at, remediated_by: data.remediated_by }
                        : f
                ),
            }));
        } catch (error) {
            console.error("Error toggling remediation:", error);
        }
    },

    setFilters: (partial) => {
        set((state) => ({
            filters: { ...state.filters, ...partial },
            offset: 0,
        }));
    },

    resetFilters: () => {
        set({ filters: { ...defaultFilters }, offset: 0 });
    },

    setOffset: (offset) => {
        set({ offset });
    },
}));

export default useScanFindingStore;
