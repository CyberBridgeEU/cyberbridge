// useScanScheduleStore.ts
import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

export interface ScanSchedule {
    id: string;
    scanner_type: string;
    scan_target: string;
    scan_type: string | null;
    scan_config: string | null;
    schedule_type: string; // 'interval' | 'cron'
    interval_months: number;
    interval_days: number;
    interval_hours: number;
    interval_minutes: number;
    interval_seconds: number;
    cron_day_of_week: string | null;
    cron_hour: number | null;
    cron_minute: number | null;
    is_enabled: boolean;
    last_run_at: string | null;
    next_run_at: string | null;
    last_status: string | null;
    last_error: string | null;
    run_count: number;
    user_id: string;
    user_email: string;
    organisation_id: string | null;
    organisation_name: string | null;
    created_at: string | null;
    updated_at: string | null;
}

export interface ScanScheduleCreateData {
    scanner_type: string;
    scan_target: string;
    scan_type?: string;
    scan_config?: string;
    schedule_type: string;
    interval_months?: number;
    interval_days?: number;
    interval_hours?: number;
    interval_minutes?: number;
    interval_seconds?: number;
    cron_day_of_week?: string;
    cron_hour?: number;
    cron_minute?: number;
    is_enabled?: boolean;
}

export interface ScanScheduleUpdateData {
    scan_target?: string;
    scan_type?: string;
    scan_config?: string;
    schedule_type?: string;
    interval_months?: number;
    interval_days?: number;
    interval_hours?: number;
    interval_minutes?: number;
    interval_seconds?: number;
    cron_day_of_week?: string;
    cron_hour?: number;
    cron_minute?: number;
    is_enabled?: boolean;
}

interface ScanScheduleStore {
    schedules: ScanSchedule[];
    loading: boolean;
    error: string | null;
    fetchSchedules: (scannerType?: string) => Promise<void>;
    createSchedule: (data: ScanScheduleCreateData) => Promise<ScanSchedule | null>;
    updateSchedule: (id: string, data: ScanScheduleUpdateData) => Promise<ScanSchedule | null>;
    deleteSchedule: (id: string) => Promise<boolean>;
    toggleSchedule: (id: string) => Promise<ScanSchedule | null>;
}

const useScanScheduleStore = create<ScanScheduleStore>((set, get) => ({
    schedules: [],
    loading: false,
    error: null,

    fetchSchedules: async (scannerType?: string) => {
        set({ loading: true, error: null });
        try {
            const headers = useAuthStore.getState().getAuthHeader();
            const params = scannerType ? `?scanner_type=${scannerType}` : '';
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/scanners/schedules${params}`,
                { headers }
            );
            if (response.ok) {
                const data = await response.json();
                set({ schedules: data, loading: false });
            } else {
                set({ error: 'Failed to fetch schedules', loading: false });
            }
        } catch (error) {
            set({ error: 'Failed to fetch schedules', loading: false });
        }
    },

    createSchedule: async (data: ScanScheduleCreateData) => {
        try {
            const headers = useAuthStore.getState().getAuthHeader();
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/scanners/schedules`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...headers },
                    body: JSON.stringify(data)
                }
            );
            if (response.ok) {
                const schedule = await response.json();
                set(state => ({ schedules: [schedule, ...state.schedules] }));
                return schedule;
            }
            return null;
        } catch {
            return null;
        }
    },

    updateSchedule: async (id: string, data: ScanScheduleUpdateData) => {
        try {
            const headers = useAuthStore.getState().getAuthHeader();
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/scanners/schedules/${id}`,
                {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json', ...headers },
                    body: JSON.stringify(data)
                }
            );
            if (response.ok) {
                const updated = await response.json();
                set(state => ({
                    schedules: state.schedules.map(s => s.id === id ? updated : s)
                }));
                return updated;
            }
            return null;
        } catch {
            return null;
        }
    },

    deleteSchedule: async (id: string) => {
        try {
            const headers = useAuthStore.getState().getAuthHeader();
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/scanners/schedules/${id}`,
                { method: 'DELETE', headers }
            );
            if (response.ok) {
                set(state => ({
                    schedules: state.schedules.filter(s => s.id !== id)
                }));
                return true;
            }
            return false;
        } catch {
            return false;
        }
    },

    toggleSchedule: async (id: string) => {
        try {
            const headers = useAuthStore.getState().getAuthHeader();
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/scanners/schedules/${id}/toggle`,
                { method: 'PUT', headers }
            );
            if (response.ok) {
                const toggled = await response.json();
                set(state => ({
                    schedules: state.schedules.map(s => s.id === id ? toggled : s)
                }));
                return toggled;
            }
            return null;
        } catch {
            return null;
        }
    }
}));

export default useScanScheduleStore;
