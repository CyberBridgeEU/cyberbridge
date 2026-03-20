import type { TableColumnsType, TableProps } from 'antd';
import useDashboardStore, { Assessment } from "../store/useDashboardStore.ts";

// Define the data type for the assessment table
export interface AssessmentTableType {
    key: string;
    name: string;
    framework: string;
    user: string;
    assessment_type: string;
    progress: number;
    status: string;
    organisation: string;
}

export const AssessmentGridColumns = (): TableColumnsType<AssessmentTableType> => {
    const { assessments } = useDashboardStore();

    // Extract distinct values for filtering
    const distinctNames = [...new Set(assessments.map(assessment => assessment.name))];
    const distinctFrameworks = [...new Set(assessments.map(assessment => assessment.framework))];
    const distinctUsers = [...new Set(assessments.map(assessment => assessment.user))];
    const distinctAssessmentTypes = [...new Set(assessments.map(assessment => assessment.assessment_type))];
    const distinctStatuses = [...new Set(assessments.map(assessment => assessment.status))];
    const distinctOrganisations = [...new Set(assessments.map(assessment => assessment.organisation))];

    // Create filters array from distinct values
    const nameFilter = distinctNames.map(name => ({
        text: name,
        value: name,
    }));

    const frameworkFilter = distinctFrameworks.map(framework => ({
        text: framework,
        value: framework,
    }));

    const userFilter = distinctUsers.map(user => ({
        text: user,
        value: user,
    }));

    const assessmentTypeFilter = distinctAssessmentTypes.map(type => ({
        text: type,
        value: type,
    }));

    const statusFilter = distinctStatuses.map(status => ({
        text: status,
        value: status,
    }));

    const organisationFilter = distinctOrganisations.map(organisation => ({
        text: organisation,
        value: organisation,
    }));

    return [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
            sorter: (a, b) => a.name.localeCompare(b.name),
            filters: nameFilter,
            onFilter: (value, record) => record.name.indexOf(value as string) === 0,
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Framework',
            dataIndex: 'framework',
            key: 'framework',
            sorter: (a, b) => a.framework.localeCompare(b.framework),
            filters: frameworkFilter,
            onFilter: (value, record) => record.framework.indexOf(value as string) === 0,
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'User',
            dataIndex: 'user',
            key: 'user',
            sorter: (a, b) => a.user.localeCompare(b.user),
            filters: userFilter,
            onFilter: (value, record) => record.user.indexOf(value as string) === 0,
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Organization',
            dataIndex: 'organisation',
            key: 'organisation',
            sorter: (a, b) => a.organisation.localeCompare(b.organisation),
            filters: organisationFilter,
            onFilter: (value, record) => record.organisation.indexOf(value as string) === 0,
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Assessment Type',
            dataIndex: 'assessment_type',
            key: 'assessment_type',
            sorter: (a, b) => a.assessment_type.localeCompare(b.assessment_type),
            filters: assessmentTypeFilter,
            onFilter: (value, record) => record.assessment_type.indexOf(value as string) === 0,
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Progress',
            dataIndex: 'progress',
            key: 'progress',
            render: (progress) => `${progress.toFixed(2)}%`,
            sorter: (a, b) => a.progress - b.progress,
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            sorter: (a, b) => a.status.localeCompare(b.status),
            filters: statusFilter,
            onFilter: (value, record) => record.status.indexOf(value as string) === 0,
            showSorterTooltip: { target: 'full-header' },
            sortDirections: ['descend', 'ascend'],
        },
    ];
};

export const onAssessmentTableChange: TableProps<AssessmentTableType>['onChange'] = (pagination, filters, sorter, extra) => {
    console.log('Table params:', pagination, filters, sorter, extra);
};
