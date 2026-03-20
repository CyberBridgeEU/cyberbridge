import type { TableColumnsType } from "antd";

export interface CorrelationData {
    id: string;
    question_a: {
        id: string;
        text: string;
        framework: string;
        assessment_type: string;
    };
    question_b: {
        id: string;
        text: string;
        framework: string;
        assessment_type: string;
    };
    organisation: string;
    organisation_id: string;
    scope: {
        scope_name: string;
        scope_id: string | null;
        scope_entity_id: string | null;
        entity_name: string | null;
    };
    created_by: string;
    created_at: string;
}

export const CorrelationsGridColumns = (correlations: CorrelationData[]): TableColumnsType<CorrelationData> => {
    const getScopeLabel = (scopeName: string) =>
        scopeName === 'Product' || scopeName === 'Asset' ? 'Asset / Product' : scopeName;

    // Extract distinct values for filters
    const distinctFrameworksA = [...new Set(correlations.map(c => c.question_a.framework))];
    const distinctFrameworksB = [...new Set(correlations.map(c => c.question_b.framework))];
    const distinctOrganisations = [...new Set(correlations.map(c => c.organisation))];
    const distinctCreatedBy = [...new Set(correlations.map(c => c.created_by))];
    const distinctAssessmentTypesA = [...new Set(correlations.map(c => c.question_a.assessment_type))];
    const distinctAssessmentTypesB = [...new Set(correlations.map(c => c.question_b.assessment_type))];
    const distinctScopeTypes = [...new Set(correlations.map(c => c.scope.scope_name))];
    const distinctScopeEntities = [...new Set(correlations.map(c => c.scope.entity_name).filter(Boolean))];

    return [
        {
            title: 'Framework A Name',
            dataIndex: ['question_a', 'framework'],
            key: 'framework_a_name',
            sorter: (a, b) => a.question_a.framework.localeCompare(b.question_a.framework),
            filters: distinctFrameworksA.map(framework => ({
                text: framework,
                value: framework,
            })),
            onFilter: (value, record) => record.question_a.framework === value,
            width: 150,
            ellipsis: true,
        },
        {
            title: 'Assessment Type A',
            dataIndex: ['question_a', 'assessment_type'],
            key: 'assessment_type_a',
            sorter: (a, b) => a.question_a.assessment_type.localeCompare(b.question_a.assessment_type),
            filters: distinctAssessmentTypesA.map(type => ({
                text: type,
                value: type,
            })),
            onFilter: (value, record) => record.question_a.assessment_type === value,
            width: 120,
        },
        {
            title: 'Question A',
            dataIndex: ['question_a', 'text'],
            key: 'question_a_text',
            sorter: (a, b) => a.question_a.text.localeCompare(b.question_a.text),
            ellipsis: {
                showTitle: true,
            },
            width: 300,
            render: (text: string) => (
                <div title={text} style={{ cursor: 'help' }}>
                    {text.length > 100 ? `${text.substring(0, 100)}...` : text}
                </div>
            ),
        },
        {
            title: 'Framework B Name',
            dataIndex: ['question_b', 'framework'],
            key: 'framework_b_name',
            sorter: (a, b) => a.question_b.framework.localeCompare(b.question_b.framework),
            filters: distinctFrameworksB.map(framework => ({
                text: framework,
                value: framework,
            })),
            onFilter: (value, record) => record.question_b.framework === value,
            width: 150,
            ellipsis: true,
        },
        {
            title: 'Assessment Type B',
            dataIndex: ['question_b', 'assessment_type'],
            key: 'assessment_type_b',
            sorter: (a, b) => a.question_b.assessment_type.localeCompare(b.question_b.assessment_type),
            filters: distinctAssessmentTypesB.map(type => ({
                text: type,
                value: type,
            })),
            onFilter: (value, record) => record.question_b.assessment_type === value,
            width: 120,
        },
        {
            title: 'Question B',
            dataIndex: ['question_b', 'text'],
            key: 'question_b_text',
            sorter: (a, b) => a.question_b.text.localeCompare(b.question_b.text),
            ellipsis: {
                showTitle: true,
            },
            width: 300,
            render: (text: string) => (
                <div title={text} style={{ cursor: 'help' }}>
                    {text.length > 100 ? `${text.substring(0, 100)}...` : text}
                </div>
            ),
        },
        {
            title: 'Scope Type',
            dataIndex: ['scope', 'scope_name'],
            key: 'scope_type',
            sorter: (a, b) => a.scope.scope_name.localeCompare(b.scope.scope_name),
            filters: distinctScopeTypes.map(type => ({
                text: getScopeLabel(type),
                value: type,
            })),
            onFilter: (value, record) => record.scope.scope_name === value,
            width: 120,
            ellipsis: true,
            render: (text: string) => getScopeLabel(text),
        },
        {
            title: 'Scope Entity',
            dataIndex: ['scope', 'entity_name'],
            key: 'scope_entity',
            sorter: (a, b) => {
                const nameA = a.scope.entity_name || '';
                const nameB = b.scope.entity_name || '';
                return nameA.localeCompare(nameB);
            },
            filters: distinctScopeEntities.map(entity => ({
                text: entity as string,
                value: entity as string,
            })),
            onFilter: (value, record) => record.scope.entity_name === value,
            width: 150,
            ellipsis: true,
            render: (text: string | null) => text || 'Not required',
        },
        {
            title: 'Organization',
            dataIndex: 'organisation',
            key: 'organisation',
            sorter: (a, b) => a.organisation.localeCompare(b.organisation),
            filters: distinctOrganisations.map(org => ({
                text: org,
                value: org,
            })),
            onFilter: (value, record) => record.organisation === value,
            width: 150,
            ellipsis: true,
        },
        {
            title: 'Created By',
            dataIndex: 'created_by',
            key: 'created_by',
            sorter: (a, b) => a.created_by.localeCompare(b.created_by),
            filters: distinctCreatedBy.map(creator => ({
                text: creator,
                value: creator,
            })),
            onFilter: (value, record) => record.created_by === value,
            width: 150,
            ellipsis: true,
        },
        {
            title: 'Created At',
            dataIndex: 'created_at',
            key: 'created_at',
            sorter: (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
            width: 150,
            render: (text: string) => {
                if (!text) return '-';
                const date = new Date(text);
                return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            },
        },
    ];
};
