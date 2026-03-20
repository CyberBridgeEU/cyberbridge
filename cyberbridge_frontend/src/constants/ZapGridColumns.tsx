import type { TableColumnsType, TableProps } from 'antd';
import { Tag } from 'antd';
import { ZapAlert } from '../store/useZapStore';

// Define the data type for the ZAP alerts table
export interface ZapAlertTableType extends ZapAlert {
    key: string;
}

// Helper function to get color based on risk level
const getRiskColor = (risk: string): string => {
    switch (risk.toLowerCase()) {
        case 'high':
            return 'red';
        case 'medium':
            return 'orange';
        case 'low':
            return 'yellow';
        case 'informational':
            return 'blue';
        default:
            return 'default';
    }
};

// Helper function to get color based on confidence level
const getConfidenceColor = (confidence: string): string => {
    switch (confidence.toLowerCase()) {
        case 'high':
            return 'green';
        case 'medium':
            return 'lime';
        case 'low':
            return 'gold';
        default:
            return 'default';
    }
};

export const ZapGridColumns = (): TableColumnsType<ZapAlertTableType> => {
    return [
        {
            title: 'ID',
            dataIndex: 'id',
            key: 'id',
            width: 60,
            sorter: (a, b) => parseInt(a.id) - parseInt(b.id),
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Alert',
            dataIndex: 'name',
            key: 'name',
            sorter: (a, b) => a.name.localeCompare(b.name),
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
            ellipsis: true,
        },
        {
            title: 'Risk',
            dataIndex: 'risk',
            key: 'risk',
            width: 100,
            sorter: (a, b) => {
                const riskOrder = { 'High': 4, 'Medium': 3, 'Low': 2, 'Informational': 1 };
                return (riskOrder[a.risk as keyof typeof riskOrder] || 0) - (riskOrder[b.risk as keyof typeof riskOrder] || 0);
            },
            render: (risk) => (
                <Tag color={getRiskColor(risk)}>
                    {risk}
                </Tag>
            ),
            filters: [
                { text: 'High', value: 'High' },
                { text: 'Medium', value: 'Medium' },
                { text: 'Low', value: 'Low' },
                { text: 'Informational', value: 'Informational' },
            ],
            onFilter: (value, record) => record.risk === value,
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Confidence',
            dataIndex: 'confidence',
            key: 'confidence',
            width: 120,
            sorter: (a, b) => {
                const confidenceOrder = { 'High': 3, 'Medium': 2, 'Low': 1 };
                return (confidenceOrder[a.confidence as keyof typeof confidenceOrder] || 0) - (confidenceOrder[b.confidence as keyof typeof confidenceOrder] || 0);
            },
            render: (confidence) => (
                <Tag color={getConfidenceColor(confidence)}>
                    {confidence}
                </Tag>
            ),
            filters: [
                { text: 'High', value: 'High' },
                { text: 'Medium', value: 'Medium' },
                { text: 'Low', value: 'Low' },
            ],
            onFilter: (value, record) => record.confidence === value,
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'URL',
            dataIndex: 'url',
            key: 'url',
            ellipsis: true,
            sorter: (a, b) => a.url.localeCompare(b.url),
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Method',
            dataIndex: 'method',
            key: 'method',
            width: 100,
            sorter: (a, b) => a.method.localeCompare(b.method),
            filters: [
                { text: 'GET', value: 'GET' },
                { text: 'POST', value: 'POST' },
                { text: 'PUT', value: 'PUT' },
                { text: 'DELETE', value: 'DELETE' },
            ],
            onFilter: (value, record) => record.method === value,
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Parameter',
            dataIndex: 'param',
            key: 'param',
            width: 120,
            ellipsis: true,
        },
        {
            title: 'CWE ID',
            dataIndex: 'cweid',
            key: 'cweid',
            width: 100,
            sorter: (a, b) => parseInt(a.cweid || '0') - parseInt(b.cweid || '0'),
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
    ];
};

export const onZapTableChange: TableProps<ZapAlertTableType>['onChange'] = (pagination, filters, sorter, extra) => {
    console.log('Table params:', pagination, filters, sorter, extra);
};

// Function to prepare table data from ZAP alerts
export const prepareZapTableData = (alerts: ZapAlert[]): ZapAlertTableType[] => {
    return alerts.map((alert, index) => ({
        ...alert,
        key: alert.id || index.toString(),
    }));
};
