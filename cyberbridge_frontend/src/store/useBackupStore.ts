import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

export interface BackupConfig {
    backup_enabled: boolean;
    backup_frequency: string;  // daily, weekly, monthly
    backup_retention_years: number;
    last_backup_at: string | null;
    last_backup_status: string | null;
}

export interface Backup {
    id: string;
    organisation_id: string;
    filename: string;
    filepath: string;
    file_size: number;
    backup_type: string;  // scheduled, manual
    status: string;  // completed, failed, in_progress
    error_message: string | null;
    records_count: string | null;  // JSON string
    evidence_files_count: number | null;
    is_encrypted: boolean;
    created_by: string | null;
    created_at: string;
    expires_at: string;
}

export interface RestoreResult {
    success: boolean;
    message: string;
    records_restored: Record<string, number> | null;
    evidence_files_restored: number | null;
    error: string | null;
}

interface UseBackupStore {
    // State
    config: BackupConfig | null;
    backups: Backup[];
    totalCount: number;
    loading: boolean;
    error: string | null;

    // Actions
    fetchConfig: (organisationId: string) => Promise<void>;
    updateConfig: (organisationId: string, config: Partial<BackupConfig>) => Promise<boolean>;
    fetchBackups: (organisationId: string, skip?: number, limit?: number) => Promise<void>;
    createBackup: (organisationId: string) => Promise<Backup | null>;
    downloadBackup: (backupId: string) => Promise<void>;
    deleteBackup: (backupId: string) => Promise<boolean>;
    restoreBackup: (organisationId: string, backupId: string) => Promise<RestoreResult | null>;
    clearError: () => void;
}

const useBackupStore = create<UseBackupStore>((set, get) => ({
    // Initial state
    config: null,
    backups: [],
    totalCount: 0,
    loading: false,
    error: null,

    // Fetch backup configuration for an organization
    fetchConfig: async (organisationId: string) => {
        set({ loading: true, error: null });
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/backups/config/${organisationId}`,
                {
                    headers: {
                        ...authHeader
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to fetch backup configuration');
            }

            const data = await response.json();
            set({ config: data, loading: false });
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to fetch backup configuration';
            set({ error: errorMessage, loading: false });
            console.error('Error fetching backup config:', error);
        }
    },

    // Update backup configuration
    updateConfig: async (organisationId: string, configUpdate: Partial<BackupConfig>) => {
        set({ loading: true, error: null });
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/backups/config/${organisationId}`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        ...authHeader
                    },
                    body: JSON.stringify(configUpdate)
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to update backup configuration');
            }

            const data = await response.json();
            set({ config: data, loading: false });
            return true;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to update backup configuration';
            set({ error: errorMessage, loading: false });
            console.error('Error updating backup config:', error);
            return false;
        }
    },

    // Fetch list of backups for an organization
    fetchBackups: async (organisationId: string, skip: number = 0, limit: number = 100) => {
        set({ loading: true, error: null });
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/backups/list/${organisationId}?skip=${skip}&limit=${limit}`,
                {
                    headers: {
                        ...authHeader
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to fetch backups');
            }

            const data = await response.json();
            set({
                backups: data.backups,
                totalCount: data.total_count,
                loading: false
            });
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to fetch backups';
            set({ error: errorMessage, loading: false });
            console.error('Error fetching backups:', error);
        }
    },

    // Create a manual backup
    createBackup: async (organisationId: string) => {
        set({ loading: true, error: null });
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/backups/create/${organisationId}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...authHeader
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to create backup');
            }

            const data = await response.json();
            // Refresh the backups list
            await get().fetchBackups(organisationId);
            // Refresh the config to get updated last_backup info
            await get().fetchConfig(organisationId);
            set({ loading: false });
            return data;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to create backup';
            set({ error: errorMessage, loading: false });
            console.error('Error creating backup:', error);
            return null;
        }
    },

    // Download a backup file
    downloadBackup: async (backupId: string) => {
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/backups/download/${backupId}`,
                {
                    headers: {
                        ...authHeader
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to download backup');
            }

            // Get the filename from Content-Disposition header or use default
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'backup.zip';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^";\n]+)"?/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1];
                }
            }

            // Create blob and download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to download backup';
            set({ error: errorMessage });
            console.error('Error downloading backup:', error);
        }
    },

    // Delete a backup
    deleteBackup: async (backupId: string) => {
        set({ loading: true, error: null });
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/backups/${backupId}`,
                {
                    method: 'DELETE',
                    headers: {
                        ...authHeader
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to delete backup');
            }

            // Remove from local state
            const { backups } = get();
            set({
                backups: backups.filter(b => b.id !== backupId),
                totalCount: get().totalCount - 1,
                loading: false
            });
            return true;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to delete backup';
            set({ error: errorMessage, loading: false });
            console.error('Error deleting backup:', error);
            return false;
        }
    },

    // Restore from a backup
    restoreBackup: async (organisationId: string, backupId: string) => {
        set({ loading: true, error: null });
        try {
            const authHeader = useAuthStore.getState().getAuthHeader();
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/backups/restore/${organisationId}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...authHeader
                    },
                    body: JSON.stringify({
                        backup_id: backupId,
                        confirm: true
                    })
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to restore backup');
            }

            const data = await response.json();
            set({ loading: false });
            return data;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to restore backup';
            set({ error: errorMessage, loading: false });
            console.error('Error restoring backup:', error);
            return null;
        }
    },

    // Clear error state
    clearError: () => {
        set({ error: null });
    }
}));

export default useBackupStore;
