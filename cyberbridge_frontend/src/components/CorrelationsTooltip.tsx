import React, { useState, useEffect } from 'react';
import { Tooltip, Table, Spin } from 'antd';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from '../store/useAuthStore';

interface CorrelationData {
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
    scope: {
        scope_name: string;
        scope_id: string | null;
        scope_entity_id: string | null;
        entity_name: string | null;
    };
    created_by: string;
    created_at: string;
}

interface CorrelationsTooltipProps {
    questionId: string;
    children: React.ReactNode;
    scopeType?: string;
    scopeEntityName?: string;
}

const CorrelationsTooltip: React.FC<CorrelationsTooltipProps> = ({ questionId, children, scopeType, scopeEntityName }) => {
    const [correlations, setCorrelations] = useState<CorrelationData[]>([]);
    const [loading, setLoading] = useState(false);
    const { getAuthHeader } = useAuthStore();
    const isAssetProductScope = (scopeName: string) => scopeName === 'Product' || scopeName === 'Asset';
    const getScopeLabel = (scopeName: string) => (isAssetProductScope(scopeName) ? 'Asset / Product' : scopeName);

    const fetchCorrelations = async () => {
        setLoading(true);
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/ai-tools/questions/${questionId}/correlations`,
                {
                    headers: getAuthHeader(),
                }
            );

            if (response.ok) {
                const data = await response.json();

                // Filter correlations by scope
                // If no scopeType is provided (legacy assessment without scope), show no correlations
                let filteredData = [];
                if (scopeType) {
                    filteredData = data.filter((correlation: CorrelationData) => {
                        const scopeMatches = isAssetProductScope(scopeType)
                            ? isAssetProductScope(correlation.scope.scope_name)
                            : correlation.scope.scope_name === scopeType;

                        // If scopeEntityName is provided, also check if entity names match
                        if (scopeEntityName) {
                            return scopeMatches && correlation.scope.entity_name === scopeEntityName;
                        }

                        // If no scopeEntityName provided (Other scope), only check scope type
                        return scopeMatches && !correlation.scope.entity_name;
                    });
                }

                setCorrelations(filteredData);
            } else {
                console.error('Failed to fetch correlations');
                setCorrelations([]);
            }
        } catch (error) {
            console.error('Error fetching correlations:', error);
            setCorrelations([]);
        } finally {
            setLoading(false);
        }
    };


    const columns = [
        {
            title: 'Framework A',
            dataIndex: ['question_a', 'framework'],
            key: 'framework_a',
            width: 120,
            ellipsis: true,
        },
        {
            title: 'Question A',
            dataIndex: ['question_a', 'text'],
            key: 'question_a_text',
            width: 200,
            ellipsis: true,
            render: (text: string) => (
                <div title={text}>
                    {text.length > 50 ? `${text.substring(0, 50)}...` : text}
                </div>
            ),
        },
        {
            title: 'Assessment Type A',
            dataIndex: ['question_a', 'assessment_type'],
            key: 'assessment_type_a',
            width: 140,
            ellipsis: true,
        },
        {
            title: 'Framework B',
            dataIndex: ['question_b', 'framework'],
            key: 'framework_b',
            width: 120,
            ellipsis: true,
        },
        {
            title: 'Question B',
            dataIndex: ['question_b', 'text'],
            key: 'question_b_text',
            width: 200,
            ellipsis: true,
            render: (text: string) => (
                <div title={text}>
                    {text.length > 50 ? `${text.substring(0, 50)}...` : text}
                </div>
            ),
        },
        {
            title: 'Assessment Type B',
            dataIndex: ['question_b', 'assessment_type'],
            key: 'assessment_type_b',
            width: 140,
            ellipsis: true,
        },
        {
            title: 'Scope Type',
            dataIndex: ['scope', 'scope_name'],
            key: 'scope_type',
            width: 120,
            ellipsis: true,
            render: (text: string) => getScopeLabel(text),
        },
        {
            title: 'Scope Entity',
            dataIndex: ['scope', 'entity_name'],
            key: 'scope_entity',
            width: 150,
            ellipsis: true,
            render: (text: string | null) => text || 'Not required',
        },
    ];

    const tooltipContent = (
        <div style={{ width: '1300px', maxHeight: '400px', overflow: 'auto' }}>
            {loading ? (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                    <Spin />
                    <div>Loading correlations...</div>
                </div>
            ) : correlations.length > 0 ? (
                <div>
                    <div style={{ marginBottom: '12px', fontWeight: 'bold' }}>
                        Question Correlations ({correlations.length})
                    </div>
                    <Table
                        columns={columns}
                        dataSource={correlations}
                        pagination={false}
                        size="small"
                        rowKey="id"
                        scroll={{ y: 250 }}
                    />
                </div>
            ) : (
                <div style={{ padding: '12px', textAlign: 'center' }}>
                    No correlations found for this question
                </div>
            )}
        </div>
    );

    return (
        <Tooltip
            title={tooltipContent}
            trigger="hover"
            placement="topLeft"
            styles={{ root: { maxWidth: '1350px' } }}
            onOpenChange={(visible) => {
                if (visible) {
                    fetchCorrelations();
                }
            }}
        >
            {children}
        </Tooltip>
    );
};

export default CorrelationsTooltip;
