// scannerHistoryUtils.ts
import { cyberbridge_back_end_rest_api } from '../constants/urls';

export interface ScannerHistoryData {
    scanner_type: 'zap' | 'nmap' | 'semgrep' | 'osv' | 'syft';
    scan_target: string;
    scan_type?: string;
    scan_config?: string;
    results: any; // Will be JSON stringified
    summary?: string;
    status?: string;
    error_message?: string;
    scan_duration?: number;
}

export interface UserDetails {
    id: string;
    email: string;
    organisation_id: string;
    organisation_name: string;
}

/**
 * Serialize scan results safely before sending to backend history storage.
 * Ensures we never persist literal "undefined" or invalid JSON payloads.
 */
const serializeHistoryResults = (results: unknown): string => {
    if (results === undefined || results === null) {
        return '{}';
    }

    if (typeof results === 'string') {
        const trimmed = results.trim();
        if (!trimmed || trimmed === 'undefined' || trimmed === 'null') {
            return '{}';
        }

        try {
            JSON.parse(trimmed);
            return trimmed;
        } catch {
            return JSON.stringify({ output: results });
        }
    }

    try {
        const serialized = JSON.stringify(results);
        return serialized === undefined ? '{}' : serialized;
    } catch {
        return JSON.stringify({ error: 'Unable to serialize scan results' });
    }
};

/**
 * Fetch current user details including organization info
 */
export const fetchCurrentUserDetails = async (userEmail: string): Promise<UserDetails | null> => {
    try {
        // Get token from sessionStorage where it's actually stored
        const authStorage = sessionStorage.getItem('auth-storage');
        const token = authStorage ? JSON.parse(authStorage).state.token : null;

        if (!token) {
            console.error('No authentication token found');
            return null;
        }

        const response = await fetch(`${cyberbridge_back_end_rest_api}/users/get_current_user_by_email`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ email: userEmail })
        });

        if (!response.ok) {
            console.error('Failed to fetch user details');
            return null;
        }

        const data = await response.json();
        return {
            id: data.id,
            email: data.email,
            organisation_id: data.organisation_id,
            organisation_name: data.organisation_name
        };
    } catch (error) {
        console.error('Error fetching user details:', error);
        return null;
    }
};

/**
 * Save scanner history to the backend
 */
export const saveScannerHistory = async (
    historyData: ScannerHistoryData,
    userEmail: string,
    userId: string,
    organisationId?: string,
    organisationName?: string
): Promise<boolean> => {
    try {
        // Get token from sessionStorage where it's actually stored
        const authStorage = sessionStorage.getItem('auth-storage');
        const token = authStorage ? JSON.parse(authStorage).state.token : null;

        if (!token) {
            console.error('No authentication token found');
            return false;
        }

        const payload = {
            scanner_type: historyData.scanner_type,
            user_id: userId,
            user_email: userEmail,
            organisation_id: organisationId || null,
            organisation_name: organisationName || null,
            scan_target: historyData.scan_target,
            scan_type: historyData.scan_type || null,
            scan_config: historyData.scan_config || null,
            results: serializeHistoryResults(historyData.results),
            summary: historyData.summary || null,
            status: historyData.status || 'completed',
            error_message: historyData.error_message || null,
            scan_duration: historyData.scan_duration || null
        };

        const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/history`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            console.error('Failed to save scanner history:', errorData);
            return false;
        }

        return true;
    } catch (error) {
        console.error('Error saving scanner history:', error);
        return false;
    }
};

/**
 * Fetch scanner history for a specific scanner type
 */
export const fetchScannerHistory = async (
    scannerType: 'zap' | 'nmap' | 'semgrep' | 'osv' | 'syft',
    limit: number = 100
): Promise<any[]> => {
    try {
        // Get token from sessionStorage where it's actually stored
        const authStorage = sessionStorage.getItem('auth-storage');
        const token = authStorage ? JSON.parse(authStorage).state.token : null;

        if (!token) {
            console.error('No authentication token found');
            return [];
        }

        const response = await fetch(
            `${cyberbridge_back_end_rest_api}/scanners/history/${scannerType}?limit=${limit}`,
            {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            console.error('Failed to fetch scanner history');
            return [];
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching scanner history:', error);
        return [];
    }
};

/**
 * Parse JSON results safely
 */
export const parseHistoryResults = (resultsInput: unknown): any => {
    if (resultsInput === undefined || resultsInput === null) {
        return null;
    }

    if (typeof resultsInput === 'object') {
        return resultsInput;
    }

    if (typeof resultsInput !== 'string') {
        return null;
    }

    const trimmed = resultsInput.trim();
    if (!trimmed || trimmed === 'undefined' || trimmed === 'null') {
        return null;
    }

    try {
        return JSON.parse(trimmed);
    } catch {
        // Some history entries may contain plain text output instead of JSON.
        return resultsInput;
    }
};

/**
 * Format timestamp for display
 */
export const formatTimestamp = (timestamp: string): string => {
    try {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (error) {
        return timestamp;
    }
};

/**
 * Delete a single scanner history record by ID
 */
export const deleteScannerHistoryRecord = async (
    historyId: string
): Promise<{ success: boolean; error?: string }> => {
    try {
        const authStorage = sessionStorage.getItem('auth-storage');
        const token = authStorage ? JSON.parse(authStorage).state.token : null;

        if (!token) {
            console.error('No authentication token found');
            return { success: false, error: 'No authentication token found' };
        }

        const response = await fetch(
            `${cyberbridge_back_end_rest_api}/scanners/history/${historyId}`,
            {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            console.error('Failed to delete scanner history record:', errorData);
            return { success: false, error: errorData.detail || 'Failed to delete record' };
        }

        return { success: true };
    } catch (error) {
        console.error('Error deleting scanner history record:', error);
        return { success: false, error: String(error) };
    }
};

/**
 * Fetch full details of a specific scanner history record (including results)
 */
export const fetchScannerHistoryDetails = async (
    historyId: string
): Promise<any | null> => {
    try {
        const authStorage = sessionStorage.getItem('auth-storage');
        const token = authStorage ? JSON.parse(authStorage).state.token : null;

        if (!token) {
            console.error('No authentication token found');
            return null;
        }

        const response = await fetch(
            `${cyberbridge_back_end_rest_api}/scanners/history/details/${historyId}`,
            {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            console.error('Failed to fetch scanner history details');
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching scanner history details:', error);
        return null;
    }
};

/**
 * Clear all scanner history for a specific scanner type
 */
export const clearScannerHistory = async (
    scannerType: 'zap' | 'nmap' | 'semgrep' | 'osv' | 'syft'
): Promise<{ success: boolean; deletedCount?: number; error?: string }> => {
    try {
        // Get token from sessionStorage where it's actually stored
        const authStorage = sessionStorage.getItem('auth-storage');
        const token = authStorage ? JSON.parse(authStorage).state.token : null;

        if (!token) {
            console.error('No authentication token found');
            return { success: false, error: 'No authentication token found' };
        }

        const response = await fetch(
            `${cyberbridge_back_end_rest_api}/scanners/history/clear/${scannerType}`,
            {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            console.error('Failed to clear scanner history:', errorData);
            return { success: false, error: errorData.detail || 'Failed to clear history' };
        }

        const data = await response.json();
        return { success: true, deletedCount: data.deleted_count };
    } catch (error) {
        console.error('Error clearing scanner history:', error);
        return { success: false, error: String(error) };
    }
};

/**
 * Assign or unassign an asset to a scanner history record
 */
export const assignAssetToScannerHistory = async (
    historyId: string,
    assetId: string | null
): Promise<{ success: boolean; error?: string }> => {
    try {
        const authStorage = sessionStorage.getItem('auth-storage');
        const token = authStorage ? JSON.parse(authStorage).state.token : null;

        if (!token) {
            console.error('No authentication token found');
            return { success: false, error: 'No authentication token found' };
        }

        const response = await fetch(
            `${cyberbridge_back_end_rest_api}/scanners/history/${historyId}/asset`,
            {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ asset_id: assetId })
            }
        );

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            console.error('Failed to assign asset:', errorData);
            return { success: false, error: errorData.detail || 'Failed to assign asset' };
        }

        return { success: true };
    } catch (error) {
        console.error('Error assigning asset to scanner history:', error);
        return { success: false, error: String(error) };
    }
};

/**
 * Fetch risks linked to a specific scan finding
 */
export const fetchRisksForFinding = async (
    findingId: string
): Promise<Array<{ id: string; risk_code: string | null; risk_category_name: string }>> => {
    try {
        const authStorage = sessionStorage.getItem('auth-storage');
        const token = authStorage ? JSON.parse(authStorage).state.token : null;

        if (!token) {
            console.error('No authentication token found');
            return [];
        }

        const response = await fetch(
            `${cyberbridge_back_end_rest_api}/scanners/findings/${findingId}/risks`,
            {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {
            console.error('Failed to fetch risks for finding');
            return [];
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching risks for finding:', error);
        return [];
    }
};
