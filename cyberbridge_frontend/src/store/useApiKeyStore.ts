import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

export interface ApiKeyInfo {
    id: string;
    name: string;
    description: string | null;
    key_prefix: string;
    is_active: boolean;
    scopes: string | null;
    created_at: string | null;
    expires_at: string | null;
    last_used_at: string | null;
    revoked_at: string | null;
}

interface UseApiKeyStore {
    apiKeys: ApiKeyInfo[];
    loading: boolean;
    error: string | null;

    fetchApiKeys: () => Promise<void>;
    createApiKey: (name: string, description?: string, expiresInDays?: number) => Promise<string | null>;
    revokeApiKey: (keyId: string) => Promise<boolean>;
}

const useApiKeyStore = create<UseApiKeyStore>((set) => ({
    apiKeys: [],
    loading: false,
    error: null,

    fetchApiKeys: async () => {
        set({ loading: true, error: null });
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(`${cyberbridge_back_end_rest_api}/api-keys/`, {
                headers: { ...authHeader },
            });
            if (!response.ok) throw new Error('Failed to fetch API keys');
            const data = await response.json();
            set({ apiKeys: data.api_keys || [], loading: false });
        } catch (err: any) {
            set({ error: err.message, loading: false });
        }
    },

    createApiKey: async (name: string, description?: string, expiresInDays?: number) => {
        set({ loading: true, error: null });
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const params = new URLSearchParams({ name });
            if (description) params.append('description', description);
            if (expiresInDays) params.append('expires_in_days', String(expiresInDays));

            const response = await fetch(`${cyberbridge_back_end_rest_api}/api-keys/?${params}`, {
                method: 'POST',
                headers: { ...authHeader },
            });
            if (!response.ok) throw new Error('Failed to create API key');
            const data = await response.json();
            set({ loading: false });

            // Refresh list
            useApiKeyStore.getState().fetchApiKeys();

            return data.api_key; // full key, shown only once
        } catch (err: any) {
            set({ error: err.message, loading: false });
            return null;
        }
    },

    revokeApiKey: async (keyId: string) => {
        set({ loading: true, error: null });
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(`${cyberbridge_back_end_rest_api}/api-keys/${keyId}`, {
                method: 'DELETE',
                headers: { ...authHeader },
            });
            if (!response.ok) throw new Error('Failed to revoke API key');
            set({ loading: false });

            // Refresh list
            useApiKeyStore.getState().fetchApiKeys();
            return true;
        } catch (err: any) {
            set({ error: err.message, loading: false });
            return false;
        }
    },
}));

export default useApiKeyStore;
