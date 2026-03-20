import { create } from 'zustand';
import useAuthStore from './useAuthStore';
import { cyberbridge_back_end_rest_api } from '../constants/urls';

export interface HistoryEntry {
  id: string;
  table_name_changed: string;
  record_id: string;
  initial_user_email: string | null;
  last_user_email: string;
  last_timestamp: string;
  column_name: string | null;
  old_data: any | null;
  new_data: any | null;
  action: string;
  created_at: string;
}

interface HistoryState {
  historyEntries: HistoryEntry[];
  loading: boolean;
  error: string | null;
  fetchHistory: (tableFilter?: string, actionFilter?: string) => Promise<void>;
  fetchRecordHistory: (tableName: string, recordId: string) => Promise<void>;
  clearError: () => void;
}

export const useHistoryStore = create<HistoryState>((set, get) => ({
  historyEntries: [],
  loading: false,
  error: null,

  fetchHistory: async (tableFilter?: string, actionFilter?: string) => {
    set({ loading: true, error: null });

    try {
      const authHeader = useAuthStore.getState().getAuthHeader();
      if (!authHeader) {
        throw new Error('No access token found');
      }

      // Build query params
      const params = new URLSearchParams();
      if (tableFilter && tableFilter !== 'all') {
        params.append('table_name', tableFilter);
      }
      if (actionFilter && actionFilter !== 'all') {
        params.append('action', actionFilter);
      }
      params.append('limit', '500');

      const url = `${cyberbridge_back_end_rest_api}/history/?${params.toString()}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      set({ historyEntries: data, loading: false });
    } catch (error) {
      console.error('Error fetching history:', error);
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch history',
        loading: false
      });
    }
  },

  fetchRecordHistory: async (tableName: string, recordId: string) => {
    set({ loading: true, error: null });

    try {
      const authHeader = useAuthStore.getState().getAuthHeader();
      if (!authHeader) {
        throw new Error('No access token found');
      }

      const response = await fetch(
        `${cyberbridge_back_end_rest_api}/history/record/${tableName}/${recordId}`,
        {
          method: 'GET',
          headers: {
            ...authHeader,
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      set({ historyEntries: data, loading: false });
    } catch (error) {
      console.error('Error fetching record history:', error);
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch record history',
        loading: false
      });
    }
  },

  clearError: () => set({ error: null }),
}));