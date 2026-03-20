// ScannerHistoryGridColumns.tsx
import { ColumnsType } from 'antd/es/table';
import { Tag, Tooltip, Button, Space } from 'antd';
import { FilePdfOutlined, DeleteOutlined, ScheduleOutlined } from '@ant-design/icons';
import { formatTimestamp } from '../utils/scannerHistoryUtils';

export interface ScannerHistoryRecord {
    id: string;
    scanner_type: string;
    user_email: string;
    organisation_name: string | null;
    scan_target: string;
    scan_type: string | null;
    results?: string; // JSON string - only present when fetching details
    summary: string | null;
    max_severity?: string; // Computed on backend: High, Medium, Low, Info, or N/A
    status: string;
    error_message: string | null;
    scan_duration: number | null;
    timestamp: string;
    asset_id?: string | null;
    asset_name?: string | null;
}

/**
 * Get status tag color based on status
 */
const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
        case 'completed':
            return 'green';
        case 'failed':
            return 'red';
        case 'in_progress':
            return 'blue';
        default:
            return 'default';
    }
};

/**
 * Get severity tag color
 */
const getSeverityColor = (severity: string): string => {
    switch (severity.toLowerCase()) {
        case 'high':
            return 'red';
        case 'medium':
            return 'orange';
        case 'low':
            return 'gold';
        case 'info':
            return 'blue';
        default:
            return 'default';
    }
};

/**
 * Calculate maximum severity from scan results
 */
const getMaxSeverity = (resultsString: string): string => {
    try {
        const results = JSON.parse(resultsString);

        // Check for summary object (new format)
        if (results?.summary) {
            if (results.summary.high > 0) return 'High';
            if (results.summary.medium > 0) return 'Medium';
            if (results.summary.low > 0) return 'Low';
            if (results.summary.info > 0) return 'Info';
        }

        // Check for vulnerabilities array (new format)
        if (results?.vulnerabilities && Array.isArray(results.vulnerabilities)) {
            const severityOrder = ['High', 'Medium', 'Low', 'Info'];
            for (const severity of severityOrder) {
                if (results.vulnerabilities.some((v: any) => v.severity === severity)) {
                    return severity;
                }
            }
        }

        // Check for alerts array (ZAP format)
        if (Array.isArray(results)) {
            const riskOrder = ['High', 'Medium', 'Low', 'Informational'];
            for (const risk of riskOrder) {
                if (results.some((a: any) => a.risk?.toLowerCase() === risk.toLowerCase())) {
                    return risk === 'Informational' ? 'Info' : risk;
                }
            }
        }

        return 'N/A';
    } catch {
        return 'N/A';
    }
};

/**
 * Scanner History Grid Columns
 */
export const ScannerHistoryGridColumns = (
    onExport?: (record: ScannerHistoryRecord) => void,
    onDelete?: (record: ScannerHistoryRecord) => void,
    onSchedule?: (record: ScannerHistoryRecord) => void
): ColumnsType<ScannerHistoryRecord> => [
    {
        title: 'Timestamp',
        dataIndex: 'timestamp',
        key: 'timestamp',
        width: 180,
        sorter: (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
        defaultSortOrder: 'descend',
        render: (timestamp: string) => (
            <Tooltip title={new Date(timestamp).toISOString()}>
                {formatTimestamp(timestamp)}
            </Tooltip>
        )
    },
    {
        title: 'Target',
        dataIndex: 'scan_target',
        key: 'scan_target',
        ellipsis: {
            showTitle: false,
        },
        render: (target: string) => (
            <Tooltip placement="topLeft" title={target}>
                {target}
            </Tooltip>
        )
    },
    {
        title: 'Scan Type',
        dataIndex: 'scan_type',
        key: 'scan_type',
        width: 120,
        render: (scanType: string | null) => scanType || 'N/A'
    },
    {
        title: 'Status',
        dataIndex: 'status',
        key: 'status',
        width: 100,
        filters: [
            { text: 'Completed', value: 'completed' },
            { text: 'Failed', value: 'failed' },
            { text: 'In Progress', value: 'in_progress' }
        ],
        onFilter: (value, record) => record.status === value,
        render: (status: string) => (
            <Tag color={getStatusColor(status)}>
                {status.toUpperCase()}
            </Tag>
        )
    },
    {
        title: 'Severity',
        key: 'severity',
        dataIndex: 'max_severity',
        width: 120,
        filters: [
            { text: 'High', value: 'High' },
            { text: 'Medium', value: 'Medium' },
            { text: 'Low', value: 'Low' },
            { text: 'Info', value: 'Info' }
        ],
        onFilter: (value, record) => (record.max_severity || getMaxSeverity(record.results || '')) === value,
        sorter: (a, b) => {
            const order: { [key: string]: number } = { 'High': 0, 'Medium': 1, 'Low': 2, 'Info': 3, 'N/A': 4 };
            const sevA = a.max_severity || getMaxSeverity(a.results || '');
            const sevB = b.max_severity || getMaxSeverity(b.results || '');
            return (order[sevA] ?? 5) - (order[sevB] ?? 5);
        },
        render: (_: any, record: ScannerHistoryRecord) => {
            // Use max_severity from backend, fallback to computing from results if available
            const severity = record.max_severity || getMaxSeverity(record.results || '');
            return severity !== 'N/A' ? (
                <Tag color={getSeverityColor(severity)}>
                    {severity.toUpperCase()}
                </Tag>
            ) : (
                <span style={{ color: '#999' }}>N/A</span>
            );
        }
    },
    {
        title: 'Duration (s)',
        dataIndex: 'scan_duration',
        key: 'scan_duration',
        width: 110,
        render: (duration: number | null) => duration ? duration.toFixed(2) : 'N/A'
    },
    {
        title: 'User',
        dataIndex: 'user_email',
        key: 'user_email',
        width: 200,
        ellipsis: {
            showTitle: false,
        },
        render: (email: string) => (
            <Tooltip placement="topLeft" title={email}>
                {email}
            </Tooltip>
        )
    },
    {
        title: 'Organization',
        dataIndex: 'organisation_name',
        key: 'organisation_name',
        width: 150,
        ellipsis: {
            showTitle: false,
        },
        render: (orgName: string | null) => (
            <Tooltip placement="topLeft" title={orgName || 'N/A'}>
                {orgName || 'N/A'}
            </Tooltip>
        )
    },
    {
        title: 'Actions',
        key: 'actions',
        width: 120,
        align: 'center',
        render: (_: any, record: ScannerHistoryRecord) => (
            <Space size="small">
                {onSchedule && (
                    <Tooltip title="Schedule recurring scan">
                        <Button
                            type="text"
                            icon={<ScheduleOutlined style={{ color: record.status === 'completed' ? '#722ed1' : '#d9d9d9' }} />}
                            size="small"
                            onClick={() => onSchedule(record)}
                            disabled={record.status !== 'completed'}
                        />
                    </Tooltip>
                )}
                <Tooltip title="Export to PDF">
                    <Button
                        type="text"
                        icon={<FilePdfOutlined style={{ color: record.status === 'completed' ? '#1890ff' : '#d9d9d9' }} />}
                        size="small"
                        onClick={() => onExport?.(record)}
                        disabled={!onExport || record.status !== 'completed'}
                    />
                </Tooltip>
                {onDelete && (
                    <Tooltip title="Delete">
                        <Button
                            type="text"
                            danger
                            icon={<DeleteOutlined />}
                            size="small"
                            onClick={() => onDelete(record)}
                        />
                    </Tooltip>
                )}
            </Space>
        )
    }
];

/**
 * Prepare data for history table
 */
export const prepareHistoryTableData = (history: ScannerHistoryRecord[]) => {
    return history.map((record, index) => ({
        ...record,
        key: record.id || `history-${index}`
    }));
};
