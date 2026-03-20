import { create } from 'zustand';
import useAuthStore from "./useAuthStore.ts";
import { zap_rest_api_wrapper } from "../constants/urls.ts";

// Define the Alert interface based on the ZAP API response
export interface ZapAlert {
    id: string;
    name: string;
    risk: string;
    confidence: string;
    url: string;
    method: string;
    param: string;
    attack: string;
    evidence: string;
    description: string;
    solution: string;
    reference: string;
    cweid: string;
    wascid: string;
    sourceid: string;
    other: string;
    messageId: string;
    inputVector: string;
    tags: Record<string, string>;
    alert: string;
    alertRef: string;
}

export interface ScanStatus {
    scanId: string;
    status: number;
    isCompleted: boolean;
}

// Interface for Plugin data in active scan state
export interface Plugin {
    name: string;
    id: string;
    quality: string;
    status: string;
    timeInMs: string;
    reqCount: string;
    alertCount: string;
}

// Interface for HostProcess data in active scan state
export interface HostProcess {
    Plugin: string[];
}

// Interface for scanner progress data
export interface ScannerProgress {
    scanProgress: [string, { HostProcess: HostProcess[] }];
}

// Interface for active scan data
export interface ActiveScan {
    reqCount: string;
    alertCount: string;
    progress: string;
    newAlertCount: string;
    id: string;
    state: string;
}

// Interface for active scans data
export interface ActiveScans {
    scans: ActiveScan[];
}

// Interface for the complete active scan state
export interface ActiveScanState {
    scanner_progress: ScannerProgress;
    active_scans: ActiveScans;
}

export interface UseZapStore {
    // variables
    targetUrl: string;
    scanType: string;
    scanId: string | null;
    scanStatus: ScanStatus | null;
    activeScanState: ActiveScanState | null;
    alerts: ZapAlert[];
    loading: boolean;
    polling: boolean;
    error: string | null;
    allScans: any | null;

    // functions
    setTargetUrl: (url: string) => void;
    setScanType: (type: string) => void;
    startSpiderScan: () => Promise<boolean>;
    startActiveScan: () => Promise<boolean>;
    startFullScan: () => Promise<boolean>;
    startApiScan: () => Promise<boolean>;
    checkScanStatus: () => Promise<ScanStatus | null>;
    getActiveScanState: () => Promise<ActiveScanState | null>;
    getAlerts: () => Promise<boolean>;
    clearAlerts: () => Promise<boolean>;
    clearResults: () => void;
    startPolling: () => void;
    stopPolling: () => void;
    stopAllScans: () => Promise<any>;
    listAllScans: () => Promise<any>;
    emergencyStop: () => Promise<any>;
}

const useZapStore = create<UseZapStore>((set, get) => ({
    // variables
    targetUrl: '',
    scanType: 'spider',
    scanId: null,
    scanStatus: null,
    activeScanState: null,
    alerts: [],
    loading: false,
    polling: false,
    error: null,
    allScans: null,

    // functions
    setTargetUrl: (url: string) => set({ targetUrl: url }),

    setScanType: (type: string) => set({ scanType: type }),

    startSpiderScan: async () => {
        const { targetUrl } = get();
        if (!targetUrl) {
            set({ error: 'Target URL is required' });
            return false;
        }

        set({ loading: true, error: null });
        try {
            const response = await fetch(`${zap_rest_api_wrapper}/start-spider/?target_url=${encodeURIComponent(targetUrl)}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to start spider scan',
                    loading: false
                });
                return false;
            }

            const data = await response.json();
            set({
                scanId: data.scan,
                loading: false,
                scanStatus: {
                    scanId: data.scan,
                    status: 0,
                    isCompleted: false
                }
            });

            // Start polling for status
            get().startPolling();
            return true;
        } catch (error) {
            console.error('Error starting spider scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to start spider scan',
                loading: false
            });
            return false;
        }
    },

    startActiveScan: async () => {
        const { targetUrl } = get();
        if (!targetUrl) {
            set({ error: 'Target URL is required' });
            return false;
        }

        set({ loading: true, error: null });
        try {
            const response = await fetch(`${zap_rest_api_wrapper}/start-active-scan/?target_url=${encodeURIComponent(targetUrl)}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to start active scan',
                    loading: false
                });
                return false;
            }

            const data = await response.json();
            set({
                scanId: data.scan,
                loading: false,
                scanStatus: {
                    scanId: data.scan,
                    status: 0,
                    isCompleted: false
                }
            });

            // Start polling for status
            get().startPolling();
            return true;
        } catch (error) {
            console.error('Error starting active scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to start active scan',
                loading: false
            });
            return false;
        }
    },

    startFullScan: async () => {
        const { targetUrl } = get();
        if (!targetUrl) {
            set({ error: 'Target URL is required' });
            return false;
        }

        set({ loading: true, error: null });
        try {
            const response = await fetch(`${zap_rest_api_wrapper}/start-full-scan/?target_url=${encodeURIComponent(targetUrl)}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to start full scan',
                    loading: false
                });
                return false;
            }

            const data = await response.json();
            // For full scan, we get the active scan ID
            const scanId = data.active_scan?.id || '';

            set({
                scanId: scanId,
                loading: false,
                scanStatus: {
                    scanId: scanId,
                    status: 0,
                    isCompleted: false
                }
            });

            // Start polling for status
            get().startPolling();
            return true;
        } catch (error) {
            console.error('Error starting full scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to start full scan',
                loading: false
            });
            return false;
        }
    },

    startApiScan: async () => {
        const { targetUrl } = get();
        if (!targetUrl) {
            set({ error: 'Target URL is required' });
            return false;
        }

        set({ loading: true, error: null });
        try {
            const response = await fetch(`${zap_rest_api_wrapper}/start-api-scan/?api_url=${encodeURIComponent(targetUrl)}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to start API scan',
                    loading: false
                });
                return false;
            }

            const data = await response.json();
            set({
                scanId: data.scan || '0', // API scan might have a different response format
                loading: false,
                scanStatus: {
                    scanId: data.scan || '0',
                    status: 0,
                    isCompleted: false
                }
            });

            // Start polling for status
            get().startPolling();
            return true;
        } catch (error) {
            console.error('Error starting API scan:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to start API scan',
                loading: false
            });
            return false;
        }
    },

    checkScanStatus: async () => {
        const { scanId, scanType } = get();
        if (!scanId) {
            return null;
        }

        try {
            // Determine which status endpoint to use based on scan type
            let statusUrl;
            if (scanType === 'spider') {
                statusUrl = `${zap_rest_api_wrapper}/get-spider-status/?scan_id=${scanId}`;
            } else {
                statusUrl = `${zap_rest_api_wrapper}/get-scan-status/?scan_id=${scanId}`;
            }

            const response = await fetch(statusUrl, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to check scan status');
            }

            const data = await response.json();
            const status = parseInt(data.status, 10);
            const isCompleted = status === 100;

            const scanStatus = {
                scanId: scanId,
                status: status,
                isCompleted: isCompleted
            };

            set({ scanStatus });

            // If scan is complete, get the alerts
            if (isCompleted) {
                // First attempt to get alerts
                await get().getAlerts();

                const { scanType } = get();

                // For full and active scans, wait a bit and fetch alerts again
                // This ensures all vulnerability findings are captured
                if (scanType === 'full' || scanType === 'active') {
                    console.log(`${scanType} scan completed, waiting for alerts to finalize...`);
                    // Wait 2 seconds then fetch alerts again
                    setTimeout(async () => {
                        console.log('Fetching alerts after delay...');
                        await get().getAlerts();
                        // Fetch one more time after another delay to ensure we get everything
                        setTimeout(async () => {
                            console.log('Final alerts fetch...');
                            await get().getAlerts();
                        }, 2000);
                    }, 2000);
                }

                get().stopPolling();
            }

            return scanStatus;
        } catch (error) {
            console.error('Error checking scan status:', error);
            return null;
        }
    },

    getAlerts: async () => {
        const { targetUrl, scanType } = get();
        if (!targetUrl) {
            return false;
        }

        try {
            // Include scanType in the request to help the backend identify the correct alerts
            console.log(`Fetching alerts for ${scanType} scan of ${targetUrl}`);
            const response = await fetch(`${zap_rest_api_wrapper}/get-alerts/?target_url=${encodeURIComponent(targetUrl)}&scan_type=${scanType || ''}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Failed to get alerts:', response.status, errorText);
                throw new Error(`Failed to get alerts: ${response.status}`);
            }

            const data = await response.json();
            let alerts = data.alerts || [];

            console.log(`[${scanType.toUpperCase()} SCAN] Received ${alerts.length} alerts`);

            // Log alert risk levels for debugging
            if (alerts.length > 0) {
                const riskCounts = alerts.reduce((acc: any, alert: ZapAlert) => {
                    acc[alert.risk] = (acc[alert.risk] || 0) + 1;
                    return acc;
                }, {});
                console.log(`[${scanType.toUpperCase()} SCAN] Alert breakdown:`, riskCounts);

                // Log some example alert names
                const sampleAlerts = alerts.slice(0, 5).map((a: ZapAlert) => `${a.name} (${a.risk})`);
                console.log(`[${scanType.toUpperCase()} SCAN] Sample alerts:`, sampleAlerts);
            } else {
                console.log(`[${scanType.toUpperCase()} SCAN] No alerts found for target ${targetUrl}`);
            }

            set({ alerts: alerts });
            return true;
        } catch (error) {
            console.error('Error getting alerts:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to get alerts'
            });
            return false;
        }
    },

    clearAlerts: async () => {
        try {
            const response = await fetch(`${zap_rest_api_wrapper}/clear-alerts/`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to clear alerts');
            }

            set({ alerts: [] });
            return true;
        } catch (error) {
            console.error('Error clearing alerts:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to clear alerts'
            });
            return false;
        }
    },

    getActiveScanState: async () => {
        const { scanId } = get();
        if (!scanId) {
            return null;
        }

        try {
            const response = await fetch(`${zap_rest_api_wrapper}/check-active-scan-state?scan_id=${scanId}`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to get active scan state');
            }

            const data = await response.json();
            set({ activeScanState: data });
            return data;
        } catch (error) {
            console.error('Error getting active scan state:', error);
            return null;
        }
    },

    clearResults: () => {
        set({
            scanId: null,
            scanStatus: null,
            activeScanState: null,
            alerts: [],
            error: null
        });
    },

    startPolling: () => {
        set({ polling: true });

        // Create a polling interval
        const intervalId = setInterval(async () => {
            const { polling } = get();
            if (!polling) {
                clearInterval(intervalId);
                return;
            }

            // Check scan status
            await get().checkScanStatus();

            // Get active scan state for detailed progress information
            if (get().scanType === 'active' || get().scanType === 'full') {
                await get().getActiveScanState();
            }
        }, 1000); // Check every second

        // Store the interval ID in window to be able to clear it later
        (window as any).zapPollingInterval = intervalId;
    },

    stopPolling: () => {
        set({ polling: false });

        // Clear the interval
        if ((window as any).zapPollingInterval) {
            clearInterval((window as any).zapPollingInterval);
            (window as any).zapPollingInterval = null;
        }
    },


    stopAllScans: async () => {
        try {
            const response = await fetch(`${zap_rest_api_wrapper}/stop-all-scans/`, {
                method: 'POST',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to stop all scans');
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error stopping all scans:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to stop all scans'
            });
            return null;
        }
    },

    listAllScans: async () => {
        try {
            const response = await fetch(`${zap_rest_api_wrapper}/list-all-scans/`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to list all scans');
            }

            const data = await response.json();
            set({ allScans: data });
            return data;
        } catch (error) {
            console.error('Error listing all scans:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to list all scans'
            });
            return null;
        }
    },

    emergencyStop: async () => {
        try {
            const response = await fetch(`${zap_rest_api_wrapper}/emergency-stop/`, {
                method: 'POST',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                throw new Error('Failed to execute emergency stop');
            }

            const data = await response.json();
            // Stop polling first to prevent loading spinner
            get().stopPolling();
            // Clear local state after emergency stop
            get().clearResults();
            return data;
        } catch (error) {
            console.error('Error executing emergency stop:', error);
            // Stop polling even on error
            get().stopPolling();
            set({
                error: error instanceof Error ? error.message : 'Failed to execute emergency stop'
            });
            return null;
        }
    }
}));

export default useZapStore;
