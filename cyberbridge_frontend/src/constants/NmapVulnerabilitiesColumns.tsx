import { Tag, Tooltip, Button } from "antd";
import { LinkOutlined, BugOutlined } from "@ant-design/icons";
import type { ColumnsType } from 'antd/es/table';

export interface NmapVulnerability {
    id: string;
    severity: 'High' | 'Medium' | 'Low' | 'Info';
    title: string;
    description?: string;
    host?: string;
    port?: number;
    protocol?: string;
    service_name?: string;
    service_version?: string;
    cpe?: string;
    cve_id?: string;
    cvss_score?: number;
    references?: Array<{ url?: string; source?: string; tags?: string[] }>;
    cwe_ids?: string[];
}

export interface NmapScanSummary {
    high: number;
    medium: number;
    low: number;
    info: number;
    total: number;
}

const getSeverityColor = (severity: string): string => {
    switch (severity?.toLowerCase()) {
        case 'high':
            return 'red';
        case 'medium':
            return 'orange';
        case 'low':
            return 'gold';
        case 'info':
        default:
            return 'blue';
    }
};

const getSeverityOrder = (severity: string): number => {
    switch (severity?.toLowerCase()) {
        case 'high':
            return 0;
        case 'medium':
            return 1;
        case 'low':
            return 2;
        case 'info':
        default:
            return 3;
    }
};

export const NmapVulnerabilitiesColumns: ColumnsType<NmapVulnerability> = [
    {
        title: 'Severity',
        dataIndex: 'severity',
        key: 'severity',
        width: 100,
        filters: [
            { text: 'High', value: 'High' },
            { text: 'Medium', value: 'Medium' },
            { text: 'Low', value: 'Low' },
            { text: 'Info', value: 'Info' },
        ],
        onFilter: (value, record) => record.severity === value,
        sorter: (a, b) => getSeverityOrder(a.severity) - getSeverityOrder(b.severity),
        defaultSortOrder: 'ascend',
        render: (severity: string) => (
            <Tag color={getSeverityColor(severity)} style={{ fontWeight: 'bold' }}>
                {severity}
            </Tag>
        ),
    },
    {
        title: 'Title',
        dataIndex: 'title',
        key: 'title',
        ellipsis: true,
        width: 300,
        render: (title: string, record) => (
            <Tooltip title={record.description || title}>
                <span style={{
                    fontWeight: record.cve_id ? 'bold' : 'normal',
                    color: record.cve_id ? '#1890ff' : 'inherit'
                }}>
                    {title}
                </span>
            </Tooltip>
        ),
    },
    {
        title: 'Host',
        dataIndex: 'host',
        key: 'host',
        width: 140,
        render: (host: string, record) => (
            host && record.port ? `${host}:${record.port}` : host || '-'
        ),
    },
    {
        title: 'Service',
        key: 'service',
        width: 150,
        render: (_, record) => {
            if (!record.service_name && !record.service_version) return '-';
            const service = record.service_name || '';
            const version = record.service_version ? ` v${record.service_version}` : '';
            return (
                <Tooltip title={record.cpe || ''}>
                    <span>{service}{version}</span>
                </Tooltip>
            );
        },
    },
    {
        title: 'CVE',
        dataIndex: 'cve_id',
        key: 'cve_id',
        width: 130,
        render: (cve_id: string) => {
            if (!cve_id) return '-';
            return (
                <a
                    href={`https://nvd.nist.gov/vuln/detail/${cve_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ display: 'flex', alignItems: 'center', gap: '4px' }}
                >
                    <BugOutlined style={{ color: '#cf1322' }} />
                    {cve_id}
                </a>
            );
        },
    },
    {
        title: 'CVSS',
        dataIndex: 'cvss_score',
        key: 'cvss_score',
        width: 80,
        sorter: (a, b) => (a.cvss_score || 0) - (b.cvss_score || 0),
        render: (score: number) => {
            if (score === null || score === undefined) return '-';
            let color = '#52c41a'; // green
            if (score >= 7.0) color = '#cf1322'; // red
            else if (score >= 4.0) color = '#fa8c16'; // orange
            return (
                <Tag color={color} style={{ fontWeight: 'bold' }}>
                    {score.toFixed(1)}
                </Tag>
            );
        },
    },
    {
        title: 'CWE',
        dataIndex: 'cwe_ids',
        key: 'cwe_ids',
        width: 100,
        render: (cwe_ids: string[]) => {
            if (!cwe_ids || cwe_ids.length === 0) return '-';
            return (
                <Tooltip title={cwe_ids.join(', ')}>
                    <span>{cwe_ids[0]}{cwe_ids.length > 1 ? ` +${cwe_ids.length - 1}` : ''}</span>
                </Tooltip>
            );
        },
    },
    {
        title: 'References',
        dataIndex: 'references',
        key: 'references',
        width: 100,
        render: (references: Array<{ url?: string }>) => {
            if (!references || references.length === 0) return '-';
            const firstRef = references.find(r => r.url);
            if (!firstRef?.url) return '-';
            return (
                <Tooltip title={`${references.length} reference(s)`}>
                    <a
                        href={firstRef.url}
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        <Button type="link" size="small" icon={<LinkOutlined />}>
                            {references.length}
                        </Button>
                    </a>
                </Tooltip>
            );
        },
    },
];

export const prepareVulnerabilitiesTableData = (
    vulnerabilities: NmapVulnerability[]
): (NmapVulnerability & { key: string })[] => {
    return vulnerabilities.map((vuln, index) => ({
        ...vuln,
        key: vuln.id || `vuln-${index}`,
    }));
};
