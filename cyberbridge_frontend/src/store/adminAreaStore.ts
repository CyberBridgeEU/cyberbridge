import { create } from 'zustand';
import useAuthStore from './useAuthStore';
import { cyberbridge_back_end_rest_api } from '../constants/urls';

export interface User {
  id: string;
  email: string;
  role_name: string;
  organisation_name: string;
  status: string;
  created_at: string;
  auth_provider: string;
}

interface AdminAreaState {
  users: User[];
  pendingUsers: User[];
  loading: boolean;
  error: string | null;
  fetchAllUsers: () => Promise<void>;
  fetchPendingUsers: () => Promise<void>;
  updateUserStatus: (userId: string, status: string) => Promise<void>;
  approveUser: (userId: string) => Promise<void>;
  rejectUser: (userId: string) => Promise<void>;
  clearError: () => void;
}

export type PendingUser = User;

export const useAdminAreaStore = create<AdminAreaState>((set, get) => ({
  users: [],
  pendingUsers: [],
  loading: false,
  error: null,

  fetchAllUsers: async () => {
    set({ loading: true, error: null });

    try {
      const authHeader = useAuthStore.getState().getAuthHeader();
      if (!authHeader) {
        throw new Error('No access token found');
      }

      const response = await fetch(`${cyberbridge_back_end_rest_api}/admin/all-users`, {
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
      set({ users: data, loading: false });
    } catch (error) {
      console.error('Error fetching all users:', error);
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch users',
        loading: false
      });
    }
  },

  fetchPendingUsers: async () => {
    set({ loading: true, error: null });

    try {
      const authHeader = useAuthStore.getState().getAuthHeader();
      if (!authHeader) {
        throw new Error('No access token found');
      }

      const response = await fetch(`${cyberbridge_back_end_rest_api}/admin/pending-users`, {
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
      set({ pendingUsers: data, loading: false });
    } catch (error) {
      console.error('Error fetching pending users:', error);
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch pending users',
        loading: false
      });
    }
  },

  updateUserStatus: async (userId: string, status: string) => {
    set({ loading: true, error: null });

    try {
      const authHeader = useAuthStore.getState().getAuthHeader();
      if (!authHeader) {
        throw new Error('No access token found');
      }

      const response = await fetch(`${cyberbridge_back_end_rest_api}/admin/update-user-status/${userId}`, {
        method: 'PUT',
        headers: {
          ...authHeader,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Update the user status in the local state
      const currentUsers = get().users;
      set({
        users: currentUsers.map(user =>
          user.id === userId ? { ...user, status } : user
        ),
        loading: false
      });
    } catch (error) {
      console.error('Error updating user status:', error);
      set({
        error: error instanceof Error ? error.message : 'Failed to update user status',
        loading: false
      });
      throw error;
    }
  },

  approveUser: async (userId: string) => {
    await get().updateUserStatus(userId, 'active');
  },

  rejectUser: async (userId: string) => {
    await get().updateUserStatus(userId, 'inactive');
  },

  clearError: () => set({ error: null }),
}));