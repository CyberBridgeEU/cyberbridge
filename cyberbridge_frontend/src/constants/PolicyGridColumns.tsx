import type { TableColumnsType } from "antd";
import type { Policy } from "../store/usePolicyStore";

export const PolicyGridColumns = (policies: Policy[]): TableColumnsType<Policy> => {
    // Extract distinct values for filtering
    const distinctCodes = [...new Set(policies.map(policy => policy.policy_code).filter(Boolean))];
    const distinctTitles = [...new Set(policies.map(policy => policy.title))];
    const distinctStatuses = [...new Set(policies.map(policy => policy.status).filter(Boolean))];
    const distinctOrganisations = [...new Set(policies.map(policy => policy.organisation_name).filter(Boolean))];
    const distinctFrameworks = [...new Set(policies.flatMap(policy => policy.framework_names || []))];
    // Note: distinctObjectives and distinctChapters are available for future filtering implementation
    // const distinctObjectives = [...new Set(policies.flatMap(policy => policy.objectives || []))];
    // const distinctChapters = [...new Set(policies.flatMap(policy => policy.chapters || []))];

    // Create filters array from distinct values
    const codeFilter = distinctCodes.map(code => ({
        text: code,
        value: code,
    }));

    const titleFilter = distinctTitles.map(title => ({
        text: title,
        value: title,
    }));

    const statusFilter = distinctStatuses.map(status => ({
        text: status,
        value: status,
    }));

    const organisationFilter = distinctOrganisations.map(org => ({
        text: org,
        value: org,
    }));

    const frameworkFilter = distinctFrameworks.map(framework => ({
        text: framework,
        value: framework,
    }));

    return [
        {
            title: 'Code',
            dataIndex: 'policy_code',
            key: 'policy_code',
            showSorterTooltip: { target: 'full-header' },
            filters: codeFilter,
            onFilter: (value, record) => record.policy_code === value,
            sorter: (a, b) => {
                const aCode = a.policy_code || '';
                const bCode = b.policy_code || '';
                // Sort numerically by POL-N
                const aNum = parseInt(aCode.replace(/\D/g, '') || '0');
                const bNum = parseInt(bCode.replace(/\D/g, '') || '0');
                return aNum - bNum;
            },
            render: (text: string | null | undefined) => text || '-',
            sortDirections: ['descend', 'ascend'] as const,
            width: 100,
        },
        {
            title: 'Title',
            dataIndex: 'title',
            key: 'title',
            showSorterTooltip: { target: 'full-header' },
            filters: titleFilter,
            onFilter: (value, record) => record.title.indexOf(value as string) === 0,
            sorter: (a, b) => a.title.localeCompare(b.title),
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Body',
            dataIndex: 'body',
            key: 'body',
            showSorterTooltip: { target: 'full-header' },
            sorter: (a, b) => {
                const aBody = a.body || '';
                const bBody = b.body || '';
                return aBody.localeCompare(bBody);
            },
            render: (text) => text || '-',
            sortDirections: ['descend', 'ascend'],
            ellipsis: true,
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            showSorterTooltip: { target: 'full-header' },
            filters: statusFilter,
            onFilter: (value, record) => record.status?.indexOf(value as string) === 0,
            sorter: (a, b) => {
                const aStatus = a.status || '';
                const bStatus = b.status || '';
                return aStatus.localeCompare(bStatus);
            },
            render: (text) => text || '-',
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Organisation',
            dataIndex: 'organisation_name',
            key: 'organisation_name',
            showSorterTooltip: { target: 'full-header' },
            filters: organisationFilter,
            onFilter: (value, record) => record.organisation_name?.indexOf(value as string) === 0,
            sorter: (a, b) => {
                const aOrg = a.organisation_name || '';
                const bOrg = b.organisation_name || '';
                return aOrg.localeCompare(bOrg);
            },
            render: (text) => text || '-',
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Frameworks',
            dataIndex: 'framework_names',
            key: 'framework_names',
            showSorterTooltip: { target: 'full-header' },
            filters: frameworkFilter,
            onFilter: (value, record) => {
                const frameworks = record.framework_names || [];
                return frameworks.includes(value as string);
            },
            sorter: (a, b) => {
                const aFrameworks = a.framework_names && a.framework_names.length > 0 ? a.framework_names.join(', ') : '';
                const bFrameworks = b.framework_names && b.framework_names.length > 0 ? b.framework_names.join(', ') : '';
                return aFrameworks.localeCompare(bFrameworks);
            },
            render: (framework_names) => framework_names && framework_names.length > 0 ? framework_names.join(', ') : '-',
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Chapters',
            dataIndex: 'chapters',
            key: 'chapters',
            showSorterTooltip: { target: 'full-header' },
            render: (chapters) => chapters ? chapters.join(', ') : '-',
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Objectives',
            dataIndex: 'objectives',
            key: 'objectives',
            showSorterTooltip: { target: 'full-header' },
            render: (objectives) => {
                if (!objectives || objectives.length === 0) return '-';
                const text = objectives.join(', ');
                return text.length > 50 ? `${text.substring(0, 50)}...` : text;
            },
            sortDirections: ['descend', 'ascend'],
            width: 200,
        },
    ];
};

export const onPolicyTableChange = (pagination: any, filters: any, sorter: any, extra: any) => {
    console.log('Table params:', pagination, filters, sorter, extra);
};
