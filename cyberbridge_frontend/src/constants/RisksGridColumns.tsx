import type { TableColumnsType } from "antd";
import { Tag } from "antd";
import { Risk } from "../store/useRiskStore";

// Helper function to get color based on severity name
const getSeverityColor = (severityName: string | undefined): string => {
    if (!severityName) return 'default';
    const name = severityName.toLowerCase();
    if (name.includes('critical') || name.includes('very high')) return 'red';
    if (name.includes('high')) return 'orange';
    if (name.includes('medium') || name.includes('moderate')) return 'gold';
    if (name.includes('low')) return 'green';
    if (name.includes('very low') || name.includes('minimal')) return 'cyan';
    return 'default';
};

// Helper function to get color based on status name
const getStatusColor = (statusName: string | undefined): string => {
    if (!statusName) return 'default';
    const name = statusName.toLowerCase();
    if (name.includes('accept') || name.includes('remediated')) return 'green';
    if (name.includes('reduce') || name.includes('mitigate')) return 'blue';
    if (name.includes('transfer') || name.includes('share')) return 'purple';
    if (name.includes('avoid')) return 'orange';
    return 'default';
};

const getAssessmentStatusColor = (assessmentStatus: string | undefined): string => {
    if (!assessmentStatus) return 'default';
    const name = assessmentStatus.toLowerCase();
    if (name.includes('not assessed')) return 'default';
    if (name.includes('in progress')) return 'orange';
    if (name.includes('assessed')) return 'green';
    if (name.includes('needs remediation')) return 'red';
    if (name.includes('remediated')) return 'cyan';
    if (name.includes('closed')) return 'blue';
    return 'default';
};

interface RisksGridColumnsParams {
    risks: Risk[];
    riskStatuses: Array<{ id: string; risk_status_name?: string }>;
    riskSeverities: Array<{ id: string; risk_severity_name?: string }>;
}

export const RisksGridColumns = ({ risks, riskStatuses, riskSeverities }: RisksGridColumnsParams): TableColumnsType<Risk> => {
    const getScopeLabel = (scopeName?: string | null) =>
        scopeName === 'Product' || scopeName === 'Asset' ? 'Asset / Product' : (scopeName || '');

    // Extract distinct values for filtering
    const distinctCategories = [...new Set(risks.map(risk => risk.risk_category_name))];
    const distinctAssetCategories = [...new Set(risks.map(risk => risk.asset_category).filter(Boolean))];
    const distinctStatuses = [...new Set(risks.map(risk => risk.risk_status).filter(Boolean))];
    const distinctAssessmentStatuses = [...new Set(risks.map(risk => risk.assessment_status).filter(Boolean))];
    const distinctSeverities = [...new Set(risks.map(risk => risk.risk_severity).filter(Boolean))];
    // Map likelihood and residual risk UUIDs to display names for filters
    const distinctLikelihoods = [...new Set(risks.map(risk => {
        const severity = riskSeverities.find(s => s.id === risk.likelihood);
        return severity?.risk_severity_name;
    }).filter(Boolean))];
    const distinctResidualRisks = [...new Set(risks.map(risk => {
        const severity = riskSeverities.find(s => s.id === risk.residual_risk);
        return severity?.risk_severity_name;
    }).filter(Boolean))];
    const distinctOrganisations = [...new Set(risks.map(risk => risk.organisation_name).filter(Boolean))];
    const distinctScopes = [...new Set(
        risks
            .map(risk => risk.scope_display_name ? `${getScopeLabel(risk.scope_name)}: ${risk.scope_display_name}` : null)
            .filter(Boolean)
    )];

    // Create filters array from distinct values
    const categoryFilter = distinctCategories.map(category => ({
        text: category,
        value: category,
    }));

    const assetCategoryFilter = distinctAssetCategories.map(type => ({
        text: type,
        value: type,
    }));

    const statusFilter = distinctStatuses.map(status => ({
        text: status,
        value: status,
    }));

    const severityFilter = distinctSeverities.map(severity => ({
        text: severity,
        value: severity,
    }));

    const assessmentStatusFilter = distinctAssessmentStatuses.map(status => ({
        text: status,
        value: status,
    }));

    const likelihoodFilter = distinctLikelihoods.map(likelihood => ({
        text: likelihood,
        value: likelihood,
    }));

    const residualRiskFilter = distinctResidualRisks.map(residualRisk => ({
        text: residualRisk,
        value: residualRisk,
    }));

    const organisationFilter = distinctOrganisations.map(org => ({
        text: org,
        value: org,
    }));

    const scopeFilter = distinctScopes.map(scope => ({
        text: scope,
        value: scope,
    }));

    return [
        {
            title: 'Code',
            dataIndex: 'risk_code',
            key: 'risk_code',
            width: 90,
            showSorterTooltip: { target: 'full-header' },
            sorter: (a, b) => {
                const numA = parseInt(a.risk_code?.replace('RSK-', '') || '999');
                const numB = parseInt(b.risk_code?.replace('RSK-', '') || '999');
                return numA - numB;
            },
            render: (text: string) => text ? <Tag color="blue">{text}</Tag> : <span style={{ color: '#bfbfbf' }}>—</span>,
            sortDirections: ['descend', 'ascend'] as const,
            defaultSortOrder: 'ascend' as const,
        },
        {
            title: 'Risk Category',
            dataIndex: 'risk_category_name',
            key: 'risk_category_name',
            width: 180,
            showSorterTooltip: { target: 'full-header' },
            filters: categoryFilter,
            onFilter: (value, record) => record.risk_category_name.indexOf(value as string) === 0,
            sorter: (a, b) => a.risk_category_name.localeCompare(b.risk_category_name),
            sortDirections: ['descend', 'ascend'],
            ellipsis: true,
        },
        {
            title: 'Description',
            dataIndex: 'risk_category_description',
            key: 'risk_category_description',
            width: 250,
            showSorterTooltip: { target: 'full-header' },
            sorter: (a, b) => {
                const aDesc = a.risk_category_description || '';
                const bDesc = b.risk_category_description || '';
                return aDesc.localeCompare(bDesc);
            },
            render: (text) => {
                if (!text) return <span style={{ color: '#bfbfbf' }}>-</span>;
                return text.length > 50 ? `${text.substring(0, 50)}...` : text;
            },
            sortDirections: ['descend', 'ascend'],
            ellipsis: true,
        },
        {
            title: 'Status (Treatment)',
            dataIndex: 'risk_status_id',
            key: 'risk_status',
            width: 145,
            showSorterTooltip: { target: 'full-header' },
            filters: statusFilter,
            onFilter: (value, record) => {
                const status = riskStatuses.find(s => s.id === record.risk_status_id);
                return status?.risk_status_name?.indexOf(value as string) === 0;
            },
            sorter: (a, b) => {
                const aStatus = riskStatuses.find(s => s.id === a.risk_status_id)?.risk_status_name || '';
                const bStatus = riskStatuses.find(s => s.id === b.risk_status_id)?.risk_status_name || '';
                return aStatus.localeCompare(bStatus);
            },
            render: (text, record) => {
                const status = riskStatuses.find(s => s.id === record.risk_status_id);
                const statusName = status?.risk_status_name;
                return statusName ? <Tag color={getStatusColor(statusName)}>{statusName}</Tag> : '-';
            },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Severity',
            dataIndex: 'risk_severity_id',
            key: 'risk_severity',
            width: 120,
            showSorterTooltip: { target: 'full-header' },
            filters: severityFilter,
            onFilter: (value, record) => {
                const severity = riskSeverities.find(s => s.id === record.risk_severity_id);
                return severity?.risk_severity_name?.indexOf(value as string) === 0;
            },
            sorter: (a, b) => {
                const aSeverity = riskSeverities.find(s => s.id === a.risk_severity_id)?.risk_severity_name || '';
                const bSeverity = riskSeverities.find(s => s.id === b.risk_severity_id)?.risk_severity_name || '';
                return aSeverity.localeCompare(bSeverity);
            },
            render: (text, record) => {
                const severity = riskSeverities.find(s => s.id === record.risk_severity_id);
                const severityName = severity?.risk_severity_name;
                return severityName ? <Tag color={getSeverityColor(severityName)}>{severityName}</Tag> : '-';
            },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Assessment',
            dataIndex: 'assessment_status',
            key: 'assessment_status',
            width: 170,
            showSorterTooltip: { target: 'full-header' },
            filters: assessmentStatusFilter,
            onFilter: (value, record) => (record.assessment_status || '').indexOf(value as string) === 0,
            sorter: (a, b) => (a.assessment_status || '').localeCompare(b.assessment_status || ''),
            render: (text) => text ? <Tag color={getAssessmentStatusColor(text)}>{text}</Tag> : '-',
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Likelihood',
            dataIndex: 'likelihood',
            key: 'likelihood',
            width: 130,
            showSorterTooltip: { target: 'full-header' },
            filters: likelihoodFilter,
            onFilter: (value, record) => {
                const severity = riskSeverities.find(s => s.id === record.likelihood);
                return severity?.risk_severity_name?.indexOf(value as string) === 0;
            },
            sorter: (a, b) => {
                const aLikelihood = riskSeverities.find(s => s.id === a.likelihood)?.risk_severity_name || '';
                const bLikelihood = riskSeverities.find(s => s.id === b.likelihood)?.risk_severity_name || '';
                return aLikelihood.localeCompare(bLikelihood);
            },
            render: (text) => {
                const severity = riskSeverities.find(s => s.id === text);
                const severityName = severity?.risk_severity_name;
                return severityName ? <Tag color={getSeverityColor(severityName)}>{severityName}</Tag> : '-';
            },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Residual',
            dataIndex: 'residual_risk',
            key: 'residual_risk',
            width: 120,
            showSorterTooltip: { target: 'full-header' },
            filters: residualRiskFilter,
            onFilter: (value, record) => {
                const severity = riskSeverities.find(s => s.id === record.residual_risk);
                return severity?.risk_severity_name?.indexOf(value as string) === 0;
            },
            sorter: (a, b) => {
                const aResidualRisk = riskSeverities.find(s => s.id === a.residual_risk)?.risk_severity_name || '';
                const bResidualRisk = riskSeverities.find(s => s.id === b.residual_risk)?.risk_severity_name || '';
                return aResidualRisk.localeCompare(bResidualRisk);
            },
            render: (text) => {
                const severity = riskSeverities.find(s => s.id === text);
                const severityName = severity?.risk_severity_name;
                return severityName ? <Tag color={getSeverityColor(severityName)}>{severityName}</Tag> : '-';
            },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Findings',
            dataIndex: 'linked_findings_count',
            key: 'linked_findings_count',
            width: 100,
            showSorterTooltip: { target: 'full-header' },
            sorter: (a, b) => (a.linked_findings_count || 0) - (b.linked_findings_count || 0),
            render: (count: number | undefined) => {
                const val = count || 0;
                if (val === 0) return <span style={{ color: '#bfbfbf' }}>0</span>;
                let color = 'blue';
                if (val > 5) color = 'red';
                else if (val > 2) color = 'orange';
                return <Tag color={color}>{val}</Tag>;
            },
            sortDirections: ['descend', 'ascend'],
        },
    ];
};

export const onRisksTableChange = (pagination: any, filters: any, sorter: any, extra: any) => {
    console.log('Table params:', pagination, filters, sorter, extra);
};
