// src/pages/BackgroundJobsPage.tsx
import { useEffect, useState } from "react";
import { Card, Table, Button, Tag, Space, notification, Spin, Descriptions, Tabs, Popconfirm, Progress, InputNumber, Tooltip } from 'antd';
import { ScheduleOutlined, PlayCircleOutlined, ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined, DeleteOutlined, CloudSyncOutlined, DatabaseOutlined, HistoryOutlined, BugOutlined, EditOutlined, SaveOutlined, CloseOutlined, RadarChartOutlined, PauseCircleOutlined } from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import useUserStore from "../store/useUserStore.ts";
import useAuthStore from "../store/useAuthStore.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import type { ColumnsType } from 'antd/es/table';
import useScanScheduleStore from "../store/useScanScheduleStore.ts";
import type { ScanSchedule } from "../store/useScanScheduleStore.ts";
import ScheduleScanModal from "../components/ScheduleScanModal.tsx";

interface NvdSyncStatus {
    id: string;
    status: string;
    sync_type: string;
    started_at: string | null;
    completed_at: string | null;
    cves_processed: number;
    cves_added: number;
    cves_updated: number;
    error_message: string | null;
    created_at: string;
}

interface NvdSettings {
    sync_enabled: boolean;
    sync_hour: number;
    sync_minute: number;
    last_sync_at: string | null;
    api_key_configured: boolean;
}

interface NvdStatistics {
    total_cves: number;
    severity_breakdown: Record<string, number>;
    cpe_match_count: number;
    last_sync_at: string | null;
}

interface BackupRecord {
    id: string;
    filename: string;
    file_size: number;
    backup_type: string;
    status: string;
    error_message: string | null;
    records_count: Record<string, number>;
    created_at: string;
    expires_at: string | null;
}

interface HistoryCleanupConfig {
    history_cleanup_enabled: boolean;
    history_retention_days: number;
    history_cleanup_interval_hours: number;
}

interface EuvdSettings {
    id: string;
    sync_enabled: boolean;
    sync_interval_hours: number;
    sync_interval_seconds: number;
    last_sync_at: string | null;
    created_at: string;
    updated_at: string;
}

interface EuvdSyncHistoryItem {
    id: string;
    status: string;
    started_at: string | null;
    completed_at: string | null;
    vulns_processed: number;
    vulns_added: number;
    vulns_updated: number;
    error_message: string | null;
    created_at: string | null;
}

const BackgroundJobsPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const { current_user } = useUserStore();
    const { getAuthHeader } = useAuthStore();
    const [api, contextHolder] = notification.useNotification();

    // NVD Sync state
    const [nvdSettings, setNvdSettings] = useState<NvdSettings | null>(null);
    const [nvdSyncStatus, setNvdSyncStatus] = useState<NvdSyncStatus | null>(null);
    const [nvdSyncHistory, setNvdSyncHistory] = useState<NvdSyncStatus[]>([]);
    const [nvdStatistics, setNvdStatistics] = useState<NvdStatistics | null>(null);
    const [loadingNvd, setLoadingNvd] = useState(false);
    const [triggeringNvdSync, setTriggeringNvdSync] = useState(false);

    // Backup state
    const [backups, setBackups] = useState<BackupRecord[]>([]);
    const [loadingBackups, setLoadingBackups] = useState(false);
    const [triggeringBackup, setTriggeringBackup] = useState(false);

    // History cleanup state
    const [historyConfig, setHistoryConfig] = useState<HistoryCleanupConfig | null>(null);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [triggeringHistoryCleanup, setTriggeringHistoryCleanup] = useState(false);

    // EUVD Sync state
    const [euvdSettings, setEuvdSettings] = useState<EuvdSettings | null>(null);
    const [euvdSyncHistory, setEuvdSyncHistory] = useState<EuvdSyncHistoryItem[]>([]);
    const [euvdStats, setEuvdStats] = useState<{ total_cached: number } | null>(null);
    const [loadingEuvd, setLoadingEuvd] = useState(false);
    const [triggeringEuvdSync, setTriggeringEuvdSync] = useState(false);
    const [editingEuvdInterval, setEditingEuvdInterval] = useState(false);
    const [euvdIntervalHours, setEuvdIntervalHours] = useState(1);
    const [euvdIntervalSeconds, setEuvdIntervalSeconds] = useState(0);
    const [euvdEnabled, setEuvdEnabled] = useState(true);
    const [savingEuvdSettings, setSavingEuvdSettings] = useState(false);

    // Regulatory Monitor state
    const [regMonitorSettings, setRegMonitorSettings] = useState<any>(null);
    const [regScanRuns, setRegScanRuns] = useState<any[]>([]);
    const [loadingRegMonitor, setLoadingRegMonitor] = useState(false);
    const [triggeringRegScan, setTriggeringRegScan] = useState(false);

    // Scan schedule state
    const { schedules, loading: schedulesLoading, fetchSchedules, deleteSchedule, toggleSchedule } = useScanScheduleStore();
    const [editingSchedule, setEditingSchedule] = useState<ScanSchedule | null>(null);
    const [scheduleModalOpen, setScheduleModalOpen] = useState(false);

    const handleEditSchedule = (schedule: ScanSchedule) => {
        setEditingSchedule(schedule);
        setScheduleModalOpen(true);
    };

    const handleDeleteSchedule = async (id: string) => {
        const success = await deleteSchedule(id);
        if (success) {
            api.success({ message: 'Schedule Deleted', description: 'Scan schedule has been removed.' });
        } else {
            api.error({ message: 'Delete Failed', description: 'Failed to delete schedule.' });
        }
    };

    const handleToggleSchedule = async (id: string) => {
        const result = await toggleSchedule(id);
        if (result) {
            api.success({
                message: result.is_enabled ? 'Schedule Enabled' : 'Schedule Disabled',
                description: `Scan schedule has been ${result.is_enabled ? 'enabled' : 'disabled'}.`
            });
        } else {
            api.error({ message: 'Toggle Failed', description: 'Failed to toggle schedule.' });
        }
    };

    const formatScheduleInterval = (schedule: ScanSchedule): string => {
        if (schedule.schedule_type === 'cron') {
            const days = schedule.cron_day_of_week && schedule.cron_day_of_week !== '*'
                ? schedule.cron_day_of_week.split(',').map(d => d.charAt(0).toUpperCase() + d.slice(1)).join(', ')
                : 'Every day';
            return `${days} at ${String(schedule.cron_hour ?? 0).padStart(2, '0')}:${String(schedule.cron_minute ?? 0).padStart(2, '0')}`;
        }
        const parts: string[] = [];
        if (schedule.interval_months > 0) parts.push(`${schedule.interval_months}mo`);
        if (schedule.interval_days > 0) parts.push(`${schedule.interval_days}d`);
        if (schedule.interval_hours > 0) parts.push(`${schedule.interval_hours}h`);
        if (schedule.interval_minutes > 0) parts.push(`${schedule.interval_minutes}m`);
        if (schedule.interval_seconds > 0) parts.push(`${schedule.interval_seconds}s`);
        return parts.length > 0 ? `Every ${parts.join(' ')}` : 'Not set';
    };

    // Load all data on mount
    useEffect(() => {
        if (current_user?.role_name === 'super_admin') {
            loadNvdData();
            loadEuvdData();
            loadRegMonitorData();
        }
        loadBackupData();
        loadHistoryConfig();
        fetchSchedules();
    }, [current_user]);

    // Regulatory Monitor data loading
    const loadRegMonitorData = async () => {
        setLoadingRegMonitor(true);
        try {
            const [settingsRes, runsRes] = await Promise.all([
                fetch(`${cyberbridge_back_end_rest_api}/regulatory-monitor/settings`, {
                    headers: { ...getAuthHeader() }
                }),
                fetch(`${cyberbridge_back_end_rest_api}/regulatory-monitor/scan-runs?limit=5`, {
                    headers: { ...getAuthHeader() }
                })
            ]);
            if (settingsRes.ok) setRegMonitorSettings(await settingsRes.json());
            if (runsRes.ok) setRegScanRuns(await runsRes.json());
        } catch (err) {
            console.error('Failed to load regulatory monitor data:', err);
        } finally {
            setLoadingRegMonitor(false);
        }
    };

    const triggerRegulatoryScan = async () => {
        setTriggeringRegScan(true);
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/regulatory-monitor/scan`, {
                method: 'POST',
                headers: { ...getAuthHeader() }
            });
            if (res.ok) {
                api.success({ message: 'Regulatory Scan Complete', description: 'Web scan finished successfully.' });
                loadRegMonitorData();
            } else {
                api.error({ message: 'Scan Failed', description: 'Regulatory web scan failed.' });
            }
        } catch (err) {
            api.error({ message: 'Scan Failed', description: 'Could not reach the server.' });
        } finally {
            setTriggeringRegScan(false);
        }
    };

    // NVD data loading
    const loadNvdData = async () => {
        setLoadingNvd(true);
        try {
            const headers = getAuthHeader();

            // Load settings, status, history, and statistics in parallel
            const [settingsRes, statusRes, historyRes, statsRes] = await Promise.all([
                fetch(`${cyberbridge_back_end_rest_api}/nvd/settings`, { headers }),
                fetch(`${cyberbridge_back_end_rest_api}/nvd/sync/status`, { headers }),
                fetch(`${cyberbridge_back_end_rest_api}/nvd/sync/history?limit=10`, { headers }),
                fetch(`${cyberbridge_back_end_rest_api}/nvd/statistics`, { headers })
            ]);

            if (settingsRes.ok) {
                const data = await settingsRes.json();
                setNvdSettings({
                    sync_enabled: data.sync_enabled,
                    sync_hour: data.sync_hour,
                    sync_minute: data.sync_minute,
                    last_sync_at: data.last_sync_at,
                    api_key_configured: !!data.api_key
                });
            }

            if (statusRes.ok) {
                setNvdSyncStatus(await statusRes.json());
            }

            if (historyRes.ok) {
                const historyData = await historyRes.json();
                setNvdSyncHistory(historyData.syncs || []);
            }

            if (statsRes.ok) {
                setNvdStatistics(await statsRes.json());
            }
        } catch (error) {
            console.error('Error loading NVD data:', error);
        } finally {
            setLoadingNvd(false);
        }
    };

    // Trigger NVD sync
    const triggerNvdSync = async (fullSync: boolean = false) => {
        setTriggeringNvdSync(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/nvd/sync`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader()
                },
                body: JSON.stringify({ full_sync: fullSync })
            });

            if (response.ok) {
                api.success({
                    message: 'NVD Sync Started',
                    description: `${fullSync ? 'Full' : 'Incremental'} sync has been triggered. This may take several minutes.`
                });
                // Reload data after a short delay
                setTimeout(loadNvdData, 2000);
            } else if (response.status === 409) {
                api.warning({
                    message: 'Sync Already Running',
                    description: 'An NVD sync is already in progress. Please wait for it to complete.'
                });
            } else {
                const error = await response.json();
                api.error({
                    message: 'Sync Failed',
                    description: error.detail || 'Failed to start NVD sync'
                });
            }
        } catch (error) {
            api.error({
                message: 'Error',
                description: 'Failed to trigger NVD sync'
            });
        } finally {
            setTriggeringNvdSync(false);
        }
    };

    // Load backup data
    const loadBackupData = async () => {
        if (!current_user?.organisation_id) return;
        setLoadingBackups(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/backups/list/${current_user.organisation_id}?limit=20`,
                { headers: getAuthHeader() }
            );
            if (response.ok) {
                const data = await response.json();
                setBackups(data.backups || []);
            }
        } catch (error) {
            console.error('Error loading backups:', error);
        } finally {
            setLoadingBackups(false);
        }
    };

    // Trigger manual backup
    const triggerBackup = async () => {
        if (!current_user?.organisation_id) return;
        setTriggeringBackup(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/backups/create/${current_user.organisation_id}`,
                {
                    method: 'POST',
                    headers: getAuthHeader()
                }
            );

            if (response.ok) {
                api.success({
                    message: 'Backup Started',
                    description: 'Manual backup has been triggered. This may take a few minutes.'
                });
                setTimeout(loadBackupData, 3000);
            } else {
                const error = await response.json();
                api.error({
                    message: 'Backup Failed',
                    description: error.detail || 'Failed to create backup'
                });
            }
        } catch (error) {
            api.error({
                message: 'Error',
                description: 'Failed to trigger backup'
            });
        } finally {
            setTriggeringBackup(false);
        }
    };

    // Load history cleanup config
    const loadHistoryConfig = async () => {
        if (!current_user?.organisation_id) return;
        setLoadingHistory(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/admin/organizations/${current_user.organisation_id}/history-cleanup-config`,
                { headers: getAuthHeader() }
            );
            if (response.ok) {
                setHistoryConfig(await response.json());
            }
        } catch (error) {
            console.error('Error loading history config:', error);
        } finally {
            setLoadingHistory(false);
        }
    };

    // Trigger history cleanup
    const triggerHistoryCleanup = async () => {
        if (!current_user?.organisation_id) return;
        setTriggeringHistoryCleanup(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/admin/organizations/${current_user.organisation_id}/cleanup-history-now`,
                {
                    method: 'POST',
                    headers: getAuthHeader()
                }
            );

            if (response.ok) {
                const result = await response.json();
                api.success({
                    message: 'History Cleanup Complete',
                    description: `Deleted ${result.deleted_count} records older than ${result.retention_days} days.`
                });
            } else {
                const error = await response.json();
                api.error({
                    message: 'Cleanup Failed',
                    description: error.detail || 'Failed to run history cleanup'
                });
            }
        } catch (error) {
            api.error({
                message: 'Error',
                description: 'Failed to trigger history cleanup'
            });
        } finally {
            setTriggeringHistoryCleanup(false);
        }
    };

    // Clear EUVD sync history
    const [clearingEuvdHistory, setClearingEuvdHistory] = useState(false);
    const clearEuvdHistory = async () => {
        setClearingEuvdHistory(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/euvd/sync/history`, {
                method: 'DELETE',
                headers: getAuthHeader()
            });
            if (response.ok) {
                const result = await response.json();
                api.success({
                    message: 'History Cleared',
                    description: `Deleted ${result.deleted} sync history records.`
                });
                setEuvdSyncHistory([]);
            } else {
                const error = await response.json();
                api.error({
                    message: 'Clear Failed',
                    description: error.detail || 'Failed to clear EUVD sync history'
                });
            }
        } catch (error) {
            api.error({
                message: 'Error',
                description: 'Failed to clear EUVD sync history'
            });
        } finally {
            setClearingEuvdHistory(false);
        }
    };

    // EUVD data loading
    const loadEuvdData = async () => {
        setLoadingEuvd(true);
        try {
            const headers = getAuthHeader();

            const [settingsRes, historyRes, statsRes] = await Promise.all([
                fetch(`${cyberbridge_back_end_rest_api}/euvd/settings`, { headers }),
                fetch(`${cyberbridge_back_end_rest_api}/euvd/sync/history?limit=20`, { headers }),
                fetch(`${cyberbridge_back_end_rest_api}/euvd/stats`, { headers })
            ]);

            if (settingsRes.ok) {
                const data = await settingsRes.json();
                setEuvdSettings(data);
                setEuvdIntervalHours(data.sync_interval_hours);
                setEuvdIntervalSeconds(data.sync_interval_seconds);
                setEuvdEnabled(data.sync_enabled);
            }

            if (historyRes.ok) {
                const data = await historyRes.json();
                setEuvdSyncHistory(data.syncs || []);
            }

            if (statsRes.ok) {
                setEuvdStats(await statsRes.json());
            }
        } catch (error) {
            console.error('Error loading EUVD data:', error);
        } finally {
            setLoadingEuvd(false);
        }
    };

    // Trigger EUVD sync
    const triggerEuvdSync = async () => {
        setTriggeringEuvdSync(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/euvd/sync`, {
                method: 'POST',
                headers: getAuthHeader()
            });

            if (response.ok) {
                api.success({
                    message: 'EUVD Sync Started',
                    description: 'EUVD sync has been triggered. This may take a few minutes.'
                });
                setTimeout(loadEuvdData, 3000);
            } else if (response.status === 409) {
                api.warning({
                    message: 'Sync Already Running',
                    description: 'An EUVD sync is already in progress.'
                });
            } else {
                const error = await response.json();
                api.error({
                    message: 'Sync Failed',
                    description: error.detail || 'Failed to start EUVD sync'
                });
            }
        } catch (error) {
            api.error({
                message: 'Error',
                description: 'Failed to trigger EUVD sync'
            });
        } finally {
            setTriggeringEuvdSync(false);
        }
    };

    // Save EUVD settings
    const saveEuvdSettings = async () => {
        setSavingEuvdSettings(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/euvd/settings`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader()
                },
                body: JSON.stringify({
                    sync_enabled: euvdEnabled,
                    sync_interval_hours: euvdIntervalHours,
                    sync_interval_seconds: euvdIntervalSeconds
                })
            });

            if (response.ok) {
                const data = await response.json();
                setEuvdSettings(data);
                setEditingEuvdInterval(false);
                api.success({
                    message: 'Settings Saved',
                    description: `EUVD sync ${euvdEnabled ? 'enabled' : 'disabled'}${euvdEnabled ? `, interval: ${euvdIntervalHours}h ${euvdIntervalSeconds}s` : ''}`
                });
            } else {
                const error = await response.json();
                api.error({
                    message: 'Save Failed',
                    description: error.detail || 'Failed to save EUVD settings'
                });
            }
        } catch (error) {
            api.error({
                message: 'Error',
                description: 'Failed to save EUVD settings'
            });
        } finally {
            setSavingEuvdSettings(false);
        }
    };

    const cancelEuvdEdit = () => {
        if (euvdSettings) {
            setEuvdIntervalHours(euvdSettings.sync_interval_hours);
            setEuvdIntervalSeconds(euvdSettings.sync_interval_seconds);
            setEuvdEnabled(euvdSettings.sync_enabled);
        }
        setEditingEuvdInterval(false);
    };

    // Format file size
    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    // Format date
    const formatDate = (dateStr: string | null): string => {
        if (!dateStr) return 'Never';
        return new Date(dateStr).toLocaleString();
    };

    // Get status tag color
    const getStatusColor = (status: string): string => {
        const colors: Record<string, string> = {
            completed: 'success',
            in_progress: 'processing',
            pending: 'warning',
            failed: 'error'
        };
        return colors[status] || 'default';
    };

    // Format EUVD schedule display
    const formatEuvdSchedule = (): string => {
        if (!euvdSettings) return 'Loading...';
        const h = euvdSettings.sync_interval_hours;
        const s = euvdSettings.sync_interval_seconds;
        if (h > 0 && s > 0) return `Every ${h}h ${s}s`;
        if (h > 0) return `Every ${h} hour${h > 1 ? 's' : ''}`;
        if (s > 0) return `Every ${s} seconds`;
        return 'Every 1 hour';
    };

    // NVD sync history columns
    const nvdHistoryColumns: ColumnsType<NvdSyncStatus> = [
        {
            title: 'Started',
            dataIndex: 'started_at',
            key: 'started_at',
            render: (val) => formatDate(val),
            width: 180
        },
        {
            title: 'Type',
            dataIndex: 'sync_type',
            key: 'sync_type',
            render: (val) => <Tag>{val}</Tag>,
            width: 100
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (val) => <Tag color={getStatusColor(val)}>{val.toUpperCase()}</Tag>,
            width: 120
        },
        {
            title: 'CVEs Processed',
            dataIndex: 'cves_processed',
            key: 'cves_processed',
            width: 120
        },
        {
            title: 'Added',
            dataIndex: 'cves_added',
            key: 'cves_added',
            width: 80
        },
        {
            title: 'Updated',
            dataIndex: 'cves_updated',
            key: 'cves_updated',
            width: 80
        },
        {
            title: 'Completed',
            dataIndex: 'completed_at',
            key: 'completed_at',
            render: (val) => formatDate(val),
            width: 180
        },
        {
            title: 'Error',
            dataIndex: 'error_message',
            key: 'error_message',
            ellipsis: true,
            render: (val) => val ? <Tag color="error">{val}</Tag> : '-'
        }
    ];

    // EUVD sync history columns
    const euvdHistoryColumns: ColumnsType<EuvdSyncHistoryItem> = [
        {
            title: 'Started',
            dataIndex: 'started_at',
            key: 'started_at',
            render: (val) => formatDate(val),
            width: 180
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (val) => <Tag color={getStatusColor(val)}>{val.toUpperCase()}</Tag>,
            width: 120
        },
        {
            title: 'Vulns Processed',
            dataIndex: 'vulns_processed',
            key: 'vulns_processed',
            width: 130
        },
        {
            title: 'Added',
            dataIndex: 'vulns_added',
            key: 'vulns_added',
            width: 80
        },
        {
            title: 'Updated',
            dataIndex: 'vulns_updated',
            key: 'vulns_updated',
            width: 80
        },
        {
            title: 'Completed',
            dataIndex: 'completed_at',
            key: 'completed_at',
            render: (val) => formatDate(val),
            width: 180
        },
        {
            title: 'Error',
            dataIndex: 'error_message',
            key: 'error_message',
            ellipsis: true,
            render: (val) => val ? <Tag color="error">{val}</Tag> : '-'
        }
    ];

    // Backup history columns
    const backupColumns: ColumnsType<BackupRecord> = [
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (val) => formatDate(val),
            width: 180
        },
        {
            title: 'Type',
            dataIndex: 'backup_type',
            key: 'backup_type',
            render: (val) => <Tag color={val === 'manual' ? 'blue' : 'green'}>{val}</Tag>,
            width: 100
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            render: (val) => <Tag color={getStatusColor(val)}>{val.toUpperCase()}</Tag>,
            width: 120
        },
        {
            title: 'Size',
            dataIndex: 'file_size',
            key: 'file_size',
            render: (val) => formatFileSize(val),
            width: 100
        },
        {
            title: 'Records',
            key: 'records',
            render: (_, record) => {
                const total = Object.values(record.records_count || {}).reduce((a: number, b: any) => a + (b as number), 0);
                return total.toLocaleString();
            },
            width: 100
        },
        {
            title: 'Expires',
            dataIndex: 'expires_at',
            key: 'expires_at',
            render: (val) => formatDate(val),
            width: 180
        },
        {
            title: 'Error',
            dataIndex: 'error_message',
            key: 'error_message',
            ellipsis: true,
            render: (val) => val ? <Tag color="error">{val}</Tag> : '-'
        }
    ];

    // Scan schedule columns
    const scanScheduleColumns: ColumnsType<ScanSchedule> = [
        {
            title: 'Scanner',
            dataIndex: 'scanner_type',
            key: 'scanner_type',
            width: 100,
            render: (val: string) => <Tag color="purple">{val.toUpperCase()}</Tag>
        },
        {
            title: 'Target',
            dataIndex: 'scan_target',
            key: 'scan_target',
            ellipsis: true,
            render: (val: string) => <Tooltip title={val}>{val}</Tooltip>
        },
        {
            title: 'Schedule',
            key: 'schedule',
            width: 200,
            render: (_: any, record: ScanSchedule) => formatScheduleInterval(record)
        },
        {
            title: 'Status',
            key: 'is_enabled',
            width: 100,
            render: (_: any, record: ScanSchedule) => (
                <Tag color={record.is_enabled ? 'success' : 'default'}>
                    {record.is_enabled ? 'ENABLED' : 'DISABLED'}
                </Tag>
            )
        },
        {
            title: 'Last Run',
            dataIndex: 'last_run_at',
            key: 'last_run_at',
            width: 170,
            render: (val: string | null) => formatDate(val)
        },
        {
            title: 'Last Status',
            dataIndex: 'last_status',
            key: 'last_status',
            width: 110,
            render: (val: string | null) => val ? <Tag color={getStatusColor(val)}>{val.toUpperCase()}</Tag> : '-'
        },
        {
            title: 'Runs',
            dataIndex: 'run_count',
            key: 'run_count',
            width: 70,
            render: (val: number) => val || 0
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 140,
            align: 'center',
            render: (_: any, record: ScanSchedule) => (
                <Space size="small">
                    <Tooltip title={record.is_enabled ? 'Disable' : 'Enable'}>
                        <Button
                            type="text"
                            size="small"
                            icon={record.is_enabled
                                ? <PauseCircleOutlined style={{ color: '#faad14' }} />
                                : <PlayCircleOutlined style={{ color: '#52c41a' }} />
                            }
                            onClick={() => handleToggleSchedule(record.id)}
                        />
                    </Tooltip>
                    <Tooltip title="Edit Schedule">
                        <Button
                            type="text"
                            size="small"
                            icon={<EditOutlined style={{ color: '#1890ff' }} />}
                            onClick={() => handleEditSchedule(record)}
                        />
                    </Tooltip>
                    <Popconfirm
                        title="Delete this schedule?"
                        description="This will permanently remove the scheduled scan."
                        onConfirm={() => handleDeleteSchedule(record.id)}
                        okText="Delete"
                        okButtonProps={{ danger: true }}
                    >
                        <Tooltip title="Delete">
                            <Button
                                type="text"
                                size="small"
                                danger
                                icon={<DeleteOutlined />}
                            />
                        </Tooltip>
                    </Popconfirm>
                </Space>
            )
        }
    ];

    const isSuperAdmin = current_user?.role_name === 'super_admin';

    return (
        <div className="page-parent">
            {contextHolder}
            <style>{`
                .ai-toggle-container {
                    display: inline-flex;
                    align-items: center;
                    gap: 10px;
                    cursor: pointer;
                }
                .ai-custom-toggle {
                    position: relative;
                    width: 44px;
                    height: 24px;
                    background: #d9d9d9;
                    border-radius: 12px;
                    transition: background 0.2s ease;
                    cursor: pointer;
                    flex-shrink: 0;
                }
                .ai-custom-toggle.active {
                    background: #1890ff;
                }
                .ai-custom-toggle-handle {
                    position: absolute;
                    top: 2px;
                    left: 2px;
                    width: 20px;
                    height: 20px;
                    background: white;
                    border-radius: 50%;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    transition: left 0.2s ease;
                }
                .ai-custom-toggle.active .ai-custom-toggle-handle {
                    left: 22px;
                }
                .ai-toggle-label {
                    font-size: 14px;
                    color: #555;
                    user-select: none;
                    font-weight: 500;
                }
            `}</style>
            <Sidebar
                selectedKeys={menuHighlighting.selectedKeys}
                openKeys={menuHighlighting.openKeys}
                onOpenChange={menuHighlighting.onOpenChange}
            />
            <div className="page-content">
                <InfoTitle
                    icon={<ScheduleOutlined />}
                    title="Background Jobs"
                    infoContent={{
                        title: "Background Jobs",
                        description: "View and manage scheduled background jobs including NVD CVE synchronization, EUVD vulnerability sync, automated backups, and history cleanup tasks."
                    }}
                />

                <Tabs
                    defaultActiveKey="overview"
                    items={[
                        {
                            key: 'overview',
                            label: 'Overview',
                            children: (
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 16 }}>
                                    {/* NVD Sync Job - Super Admin Only */}
                                    {isSuperAdmin && (
                                        <Card
                                            title={
                                                <Space>
                                                    <CloudSyncOutlined />
                                                    <span>NVD CVE Sync</span>
                                                    {nvdSettings?.sync_enabled ? (
                                                        <Tag color="success">Enabled</Tag>
                                                    ) : (
                                                        <Tag color="default">Disabled</Tag>
                                                    )}
                                                </Space>
                                            }
                                            extra={
                                                <Space>
                                                    <Button
                                                        size="small"
                                                        icon={<SyncOutlined spin={triggeringNvdSync} />}
                                                        onClick={() => triggerNvdSync(false)}
                                                        loading={triggeringNvdSync}
                                                    >
                                                        Incremental
                                                    </Button>
                                                    <Popconfirm
                                                        title="Run Full Sync?"
                                                        description="Full sync will re-process all CVEs and may take a long time."
                                                        onConfirm={() => triggerNvdSync(true)}
                                                    >
                                                        <Button
                                                            size="small"
                                                            type="primary"
                                                            icon={<PlayCircleOutlined />}
                                                            loading={triggeringNvdSync}
                                                        >
                                                            Full Sync
                                                        </Button>
                                                    </Popconfirm>
                                                </Space>
                                            }
                                            loading={loadingNvd}
                                        >
                                            <Descriptions column={1} size="small">
                                                <Descriptions.Item label="Schedule">
                                                    Daily at {String(nvdSettings?.sync_hour || 3).padStart(2, '0')}:{String(nvdSettings?.sync_minute || 0).padStart(2, '0')} UTC
                                                </Descriptions.Item>
                                                <Descriptions.Item label="Last Sync">
                                                    {formatDate(nvdSettings?.last_sync_at || null)}
                                                </Descriptions.Item>
                                                <Descriptions.Item label="API Key">
                                                    {nvdSettings?.api_key_configured ? (
                                                        <Tag color="success">Configured</Tag>
                                                    ) : (
                                                        <Tag color="warning">Not Set (Rate Limited)</Tag>
                                                    )}
                                                </Descriptions.Item>
                                                <Descriptions.Item label="Current Status">
                                                    {nvdSyncStatus ? (
                                                        <Tag color={getStatusColor(nvdSyncStatus.status)}>
                                                            {nvdSyncStatus.status.toUpperCase()}
                                                        </Tag>
                                                    ) : '-'}
                                                </Descriptions.Item>
                                                <Descriptions.Item label="Total CVEs">
                                                    {nvdStatistics?.total_cves?.toLocaleString() || 0}
                                                </Descriptions.Item>
                                            </Descriptions>
                                        </Card>
                                    )}

                                    {/* EUVD Sync Job - Super Admin Only */}
                                    {isSuperAdmin && (
                                        <Card
                                            title={
                                                <Space>
                                                    <BugOutlined />
                                                    <span>EUVD Sync</span>
                                                    {euvdSettings?.sync_enabled ? (
                                                        <Tag color="success">Enabled</Tag>
                                                    ) : (
                                                        <Tag color="default">Disabled</Tag>
                                                    )}
                                                </Space>
                                            }
                                            extra={
                                                <Space>
                                                    <Button
                                                        size="small"
                                                        type="primary"
                                                        icon={<PlayCircleOutlined />}
                                                        onClick={triggerEuvdSync}
                                                        loading={triggeringEuvdSync}
                                                    >
                                                        Run Now
                                                    </Button>
                                                    {!editingEuvdInterval && (
                                                        <Button
                                                            size="small"
                                                            icon={<EditOutlined />}
                                                            onClick={() => setEditingEuvdInterval(true)}
                                                        />
                                                    )}
                                                </Space>
                                            }
                                            loading={loadingEuvd}
                                        >
                                            {editingEuvdInterval ? (
                                                <div>
                                                    <div style={{ marginBottom: 12 }}>
                                                        <div
                                                            className="ai-toggle-container"
                                                            onClick={() => setEuvdEnabled(!euvdEnabled)}
                                                        >
                                                            <div className={`ai-custom-toggle ${euvdEnabled ? 'active' : ''}`}>
                                                                <div className="ai-custom-toggle-handle" />
                                                            </div>
                                                            <span className="ai-toggle-label">
                                                                {euvdEnabled ? 'Enabled' : 'Disabled'}
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <div style={{ marginBottom: 12 }}>
                                                        <span style={{ marginRight: 8 }}>Interval Hours:</span>
                                                        <InputNumber
                                                            min={0}
                                                            max={168}
                                                            value={euvdIntervalHours}
                                                            onChange={(val) => setEuvdIntervalHours(val || 0)}
                                                            style={{ width: 80 }}
                                                        />
                                                    </div>
                                                    <div style={{ marginBottom: 12 }}>
                                                        <span style={{ marginRight: 8 }}>Interval Seconds:</span>
                                                        <InputNumber
                                                            min={0}
                                                            max={3600}
                                                            value={euvdIntervalSeconds}
                                                            onChange={(val) => setEuvdIntervalSeconds(val || 0)}
                                                            style={{ width: 80 }}
                                                        />
                                                    </div>
                                                    <Space>
                                                        <Button
                                                            type="primary"
                                                            icon={<SaveOutlined />}
                                                            onClick={saveEuvdSettings}
                                                            loading={savingEuvdSettings}
                                                            size="small"
                                                        >
                                                            Save
                                                        </Button>
                                                        <Button
                                                            icon={<CloseOutlined />}
                                                            onClick={cancelEuvdEdit}
                                                            size="small"
                                                        >
                                                            Cancel
                                                        </Button>
                                                    </Space>
                                                </div>
                                            ) : (
                                                <Descriptions column={1} size="small">
                                                    <Descriptions.Item label="Schedule">
                                                        {formatEuvdSchedule()}
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Last Sync">
                                                        {formatDate(euvdSettings?.last_sync_at || null)}
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Status">
                                                        {euvdSyncHistory.length > 0 ? (
                                                            <Tag color={getStatusColor(euvdSyncHistory[0].status)}>
                                                                {euvdSyncHistory[0].status.toUpperCase()}
                                                            </Tag>
                                                        ) : '-'}
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Total Cached">
                                                        {euvdStats?.total_cached?.toLocaleString() || 0}
                                                    </Descriptions.Item>
                                                </Descriptions>
                                            )}
                                        </Card>
                                    )}

                                    {/* Backup Job */}
                                    <Card
                                        title={
                                            <Space>
                                                <DatabaseOutlined />
                                                <span>Automated Backups</span>
                                                <Tag color="success">Enabled</Tag>
                                            </Space>
                                        }
                                        extra={
                                            <Button
                                                size="small"
                                                type="primary"
                                                icon={<PlayCircleOutlined />}
                                                onClick={triggerBackup}
                                                loading={triggeringBackup}
                                            >
                                                Run Now
                                            </Button>
                                        }
                                        loading={loadingBackups}
                                    >
                                        <Descriptions column={1} size="small">
                                            <Descriptions.Item label="Schedule">
                                                Daily at 02:00 UTC
                                            </Descriptions.Item>
                                            <Descriptions.Item label="Last Backup">
                                                {backups.length > 0 ? formatDate(backups[0].created_at) : 'Never'}
                                            </Descriptions.Item>
                                            <Descriptions.Item label="Last Status">
                                                {backups.length > 0 ? (
                                                    <Tag color={getStatusColor(backups[0].status)}>
                                                        {backups[0].status.toUpperCase()}
                                                    </Tag>
                                                ) : '-'}
                                            </Descriptions.Item>
                                            <Descriptions.Item label="Total Backups">
                                                {backups.length}
                                            </Descriptions.Item>
                                        </Descriptions>
                                    </Card>

                                    {/* Backup Cleanup Job - Super Admin Only */}
                                    {isSuperAdmin && (
                                        <Card
                                            title={
                                                <Space>
                                                    <DeleteOutlined />
                                                    <span>Backup Cleanup</span>
                                                    <Tag color="success">Enabled</Tag>
                                                </Space>
                                            }
                                        >
                                            <Descriptions column={1} size="small">
                                                <Descriptions.Item label="Schedule">
                                                    Weekly on Sunday at 03:00 UTC
                                                </Descriptions.Item>
                                                <Descriptions.Item label="Retention">
                                                    Based on organization settings (default: 10 years)
                                                </Descriptions.Item>
                                                <Descriptions.Item label="Description">
                                                    Automatically removes expired backups based on each organization's retention policy.
                                                </Descriptions.Item>
                                            </Descriptions>
                                        </Card>
                                    )}

                                    {/* History Cleanup Job */}
                                    <Card
                                        title={
                                            <Space>
                                                <HistoryOutlined />
                                                <span>History Cleanup</span>
                                                {historyConfig?.history_cleanup_enabled ? (
                                                    <Tag color="success">Enabled</Tag>
                                                ) : (
                                                    <Tag color="default">Disabled</Tag>
                                                )}
                                            </Space>
                                        }
                                        extra={
                                            <Button
                                                size="small"
                                                type="primary"
                                                icon={<PlayCircleOutlined />}
                                                onClick={triggerHistoryCleanup}
                                                loading={triggeringHistoryCleanup}
                                                disabled={!historyConfig?.history_cleanup_enabled}
                                            >
                                                Run Now
                                            </Button>
                                        }
                                        loading={loadingHistory}
                                    >
                                        <Descriptions column={1} size="small">
                                            <Descriptions.Item label="Schedule">
                                                Every {historyConfig?.history_cleanup_interval_hours || 24} hours
                                            </Descriptions.Item>
                                            <Descriptions.Item label="Retention">
                                                {historyConfig?.history_retention_days || 30} days
                                            </Descriptions.Item>
                                            <Descriptions.Item label="Description">
                                                Removes old activity log entries based on retention settings.
                                            </Descriptions.Item>
                                        </Descriptions>
                                    </Card>

                                    {/* Scan Schedules Overview */}
                                    <Card
                                        title={
                                            <Space>
                                                <RadarChartOutlined />
                                                <span>Scan Schedules</span>
                                                {schedules.filter(s => s.is_enabled).length > 0 ? (
                                                    <Tag color="success">{schedules.filter(s => s.is_enabled).length} Active</Tag>
                                                ) : (
                                                    <Tag color="default">None</Tag>
                                                )}
                                            </Space>
                                        }
                                        extra={
                                            <Button
                                                size="small"
                                                icon={<SyncOutlined />}
                                                onClick={() => fetchSchedules()}
                                                loading={schedulesLoading}
                                            >
                                                Refresh
                                            </Button>
                                        }
                                        loading={schedulesLoading}
                                    >
                                        <Descriptions column={1} size="small">
                                            <Descriptions.Item label="Total Schedules">
                                                {schedules.length}
                                            </Descriptions.Item>
                                            <Descriptions.Item label="Active">
                                                {schedules.filter(s => s.is_enabled).length}
                                            </Descriptions.Item>
                                            <Descriptions.Item label="Scanner Types">
                                                {[...new Set(schedules.map(s => s.scanner_type))].map(type => (
                                                    <Tag key={type} color="purple" style={{ marginRight: 4 }}>{type.toUpperCase()}</Tag>
                                                ))}
                                                {schedules.length === 0 && '-'}
                                            </Descriptions.Item>
                                            <Descriptions.Item label="Description">
                                                User-configured recurring security scans running on schedule.
                                            </Descriptions.Item>
                                        </Descriptions>
                                    </Card>

                                    {/* Regulatory Change Monitor - Super Admin Only */}
                                    {isSuperAdmin && (
                                        <Card
                                            title={
                                                <Space>
                                                    <CloudSyncOutlined />
                                                    <span>Regulatory Change Monitor</span>
                                                    {regMonitorSettings?.enabled ? (
                                                        <Tag color="success">Enabled</Tag>
                                                    ) : (
                                                        <Tag color="default">Disabled</Tag>
                                                    )}
                                                </Space>
                                            }
                                            extra={
                                                <Button
                                                    type="primary"
                                                    size="small"
                                                    icon={<PlayCircleOutlined />}
                                                    onClick={triggerRegulatoryScan}
                                                    loading={triggeringRegScan}
                                                    style={{ background: '#1a365d', borderColor: '#1a365d' }}
                                                >
                                                    Run Now
                                                </Button>
                                            }
                                            loading={loadingRegMonitor}
                                        >
                                            <Descriptions column={1} size="small">
                                                <Descriptions.Item label="Schedule">
                                                    {regMonitorSettings ? (
                                                        regMonitorSettings.scan_frequency === 'daily'
                                                            ? `Daily at ${String(regMonitorSettings.scan_hour).padStart(2, '0')}:00 UTC`
                                                            : regMonitorSettings.scan_frequency === 'weekly'
                                                                ? `Weekly on ${(regMonitorSettings.scan_day_of_week || 'mon').charAt(0).toUpperCase() + (regMonitorSettings.scan_day_of_week || 'mon').slice(1)} at ${String(regMonitorSettings.scan_hour).padStart(2, '0')}:00 UTC`
                                                                : `Biweekly on ${(regMonitorSettings.scan_day_of_week || 'mon').charAt(0).toUpperCase() + (regMonitorSettings.scan_day_of_week || 'mon').slice(1)} at ${String(regMonitorSettings.scan_hour).padStart(2, '0')}:00 UTC`
                                                    ) : '-'}
                                                </Descriptions.Item>
                                                <Descriptions.Item label="Last Scan">
                                                    {regMonitorSettings?.last_scan_at
                                                        ? new Date(regMonitorSettings.last_scan_at).toLocaleString()
                                                        : 'Never'}
                                                </Descriptions.Item>
                                                <Descriptions.Item label="Last Status">
                                                    {regScanRuns.length > 0 ? (
                                                        <Tag color={regScanRuns[0].status === 'completed' ? 'success' : regScanRuns[0].status === 'failed' ? 'error' : 'processing'}>
                                                            {regScanRuns[0].status.toUpperCase()}
                                                        </Tag>
                                                    ) : '-'}
                                                </Descriptions.Item>
                                                <Descriptions.Item label="Last Findings">
                                                    {regScanRuns.length > 0 ? `${regScanRuns[0].changes_found} new findings across ${regScanRuns[0].frameworks_scanned} frameworks` : '-'}
                                                </Descriptions.Item>
                                                <Descriptions.Item label="SearXNG URL">
                                                    {regMonitorSettings?.searxng_url || '-'}
                                                </Descriptions.Item>
                                                <Descriptions.Item label="Description">
                                                    Searches the web for regulatory changes across all frameworks using SearXNG, EUR-Lex, and NIST APIs. Results are saved for LLM analysis on the Framework Updates page.
                                                </Descriptions.Item>
                                            </Descriptions>
                                        </Card>
                                    )}
                                </div>
                            )
                        },
                        ...(isSuperAdmin ? [{
                            key: 'nvd-history',
                            label: 'NVD Sync History',
                            children: (
                                <div>
                                    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{ color: '#666' }}>
                                            Recent NVD CVE synchronization jobs
                                        </span>
                                        <Button
                                            icon={<SyncOutlined />}
                                            onClick={loadNvdData}
                                            loading={loadingNvd}
                                        >
                                            Refresh
                                        </Button>
                                    </div>
                                    <Table
                                        columns={nvdHistoryColumns}
                                        dataSource={nvdSyncHistory}
                                        rowKey="id"
                                        loading={loadingNvd}
                                        pagination={false}
                                        size="small"
                                    />

                                    {nvdStatistics && (
                                        <Card title="CVE Statistics" style={{ marginTop: 16 }} size="small">
                                            <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
                                                <div>
                                                    <div style={{ color: '#666', fontSize: 12 }}>Total CVEs</div>
                                                    <div style={{ fontSize: 24, fontWeight: 600 }}>
                                                        {nvdStatistics.total_cves.toLocaleString()}
                                                    </div>
                                                </div>
                                                <div>
                                                    <div style={{ color: '#666', fontSize: 12 }}>CPE Matches</div>
                                                    <div style={{ fontSize: 24, fontWeight: 600 }}>
                                                        {nvdStatistics.cpe_match_count.toLocaleString()}
                                                    </div>
                                                </div>
                                                {Object.entries(nvdStatistics.severity_breakdown || {}).map(([severity, count]) => (
                                                    <div key={severity}>
                                                        <div style={{ color: '#666', fontSize: 12 }}>{severity}</div>
                                                        <div style={{ fontSize: 24, fontWeight: 600 }}>
                                                            {(count as number).toLocaleString()}
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </Card>
                                    )}
                                </div>
                            )
                        }] : []),
                        ...(isSuperAdmin ? [{
                            key: 'euvd-history',
                            label: 'EUVD Sync History',
                            children: (
                                <div>
                                    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{ color: '#666' }}>
                                            Recent EUVD vulnerability synchronization jobs
                                        </span>
                                        <Space>
                                            <Popconfirm
                                                title="Clear all EUVD sync history?"
                                                description="This will permanently delete all sync history records."
                                                onConfirm={clearEuvdHistory}
                                                okText="Clear All"
                                                okButtonProps={{ danger: true }}
                                            >
                                                <Button
                                                    danger
                                                    icon={<DeleteOutlined />}
                                                    loading={clearingEuvdHistory}
                                                    disabled={euvdSyncHistory.length === 0}
                                                >
                                                    Clear
                                                </Button>
                                            </Popconfirm>
                                            <Button
                                                icon={<SyncOutlined />}
                                                onClick={loadEuvdData}
                                                loading={loadingEuvd}
                                            >
                                                Refresh
                                            </Button>
                                        </Space>
                                    </div>
                                    <Table
                                        columns={euvdHistoryColumns}
                                        dataSource={euvdSyncHistory}
                                        rowKey="id"
                                        loading={loadingEuvd}
                                        pagination={false}
                                        size="small"
                                    />
                                </div>
                            )
                        }] : []),
                        {
                            key: 'backup-history',
                            label: 'Backup History',
                            children: (
                                <div>
                                    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{ color: '#666' }}>
                                            Recent backup jobs for your organization
                                        </span>
                                        <Button
                                            icon={<SyncOutlined />}
                                            onClick={loadBackupData}
                                            loading={loadingBackups}
                                        >
                                            Refresh
                                        </Button>
                                    </div>
                                    <Table
                                        columns={backupColumns}
                                        dataSource={backups}
                                        rowKey="id"
                                        loading={loadingBackups}
                                        pagination={{ pageSize: 10 }}
                                        size="small"
                                    />
                                </div>
                            )
                        },
                        {
                            key: 'scan-schedules',
                            label: 'Scan Schedules',
                            children: (
                                <div>
                                    <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <span style={{ color: '#666' }}>
                                            Manage recurring scan schedules across all scanner types
                                        </span>
                                        <Button
                                            icon={<SyncOutlined />}
                                            onClick={() => fetchSchedules()}
                                            loading={schedulesLoading}
                                        >
                                            Refresh
                                        </Button>
                                    </div>
                                    <Table
                                        columns={scanScheduleColumns}
                                        dataSource={schedules.map(s => ({ ...s, key: s.id }))}
                                        rowKey="id"
                                        loading={schedulesLoading}
                                        pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `${total} schedules` }}
                                        size="small"
                                        locale={{ emptyText: 'No scan schedules configured. Use the Schedule button on any scanner page to create one.' }}
                                    />
                                </div>
                            )
                        }
                    ]}
                />

                {/* Edit Schedule Modal */}
                <ScheduleScanModal
                    open={scheduleModalOpen}
                    onClose={() => { setScheduleModalOpen(false); setEditingSchedule(null); fetchSchedules(); }}
                    scannerType={editingSchedule?.scanner_type || ''}
                    scanTarget={editingSchedule?.scan_target || ''}
                    scanType={editingSchedule?.scan_type || undefined}
                    scanConfig={editingSchedule?.scan_config ? JSON.parse(editingSchedule.scan_config) : undefined}
                    editingSchedule={editingSchedule}
                />
            </div>
        </div>
    );
};

export default BackgroundJobsPage;
