import { useState } from 'react';
import { Drawer, Button, Tag, Radio, Spin, Empty, Collapse, Typography } from 'antd';
import {
    ExperimentOutlined,
    RobotOutlined,
    CheckOutlined,
    CloseOutlined,
    LoadingOutlined,
    StopOutlined,
    ThunderboltOutlined,
} from '@ant-design/icons';
import useAssessmentScanSuggestStore, { AnswerSuggestionItem } from '../store/useAssessmentScanSuggestStore';

const { Text } = Typography;

interface ScanSuggestionsDrawerProps {
    open: boolean;
    onClose: () => void;
    assessmentId: string | undefined;
    onApplySuggestion: (questionId: string, answer: string, evidenceDescription: string) => void;
}

const answerColors: Record<string, string> = {
    yes: 'green',
    no: 'red',
    partially: 'orange',
    'n/a': 'default',
};

const confidenceColor = (c: number) => {
    if (c >= 80) return '#52c41a';
    if (c >= 60) return '#faad14';
    return '#ff4d4f';
};

export default function ScanSuggestionsDrawer({ open, onClose, assessmentId, onApplySuggestion }: ScanSuggestionsDrawerProps) {
    const { suggestions, loading, error, fetchSuggestions, clearSuggestions, removeSuggestion, cancelGeneration } = useAssessmentScanSuggestStore();
    const [engine, setEngine] = useState<string>('rule');

    const handleGenerate = () => {
        if (!assessmentId) return;
        fetchSuggestions(assessmentId, engine);
    };

    const handleAccept = (item: AnswerSuggestionItem) => {
        onApplySuggestion(item.question_id, item.suggested_answer, item.evidence_description);
        removeSuggestion(item.question_id);
    };

    const handleReject = (questionId: string) => {
        removeSuggestion(questionId);
    };

    const handleClose = () => {
        clearSuggestions();
        onClose();
    };

    return (
        <Drawer
            title={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <ExperimentOutlined style={{ color: '#8b5cf6' }} />
                    <span>Suggest Answers from Scans</span>
                </div>
            }
            placement="right"
            width={520}
            open={open}
            onClose={handleClose}
            destroyOnClose
        >
            {/* Engine Toggle */}
            <div style={{ marginBottom: '16px' }}>
                <Text strong style={{ display: 'block', marginBottom: '8px' }}>Engine</Text>
                <Radio.Group value={engine} onChange={(e) => setEngine(e.target.value)} disabled={loading}>
                    <Radio.Button value="rule">
                        <ThunderboltOutlined /> Rule-based
                    </Radio.Button>
                    <Radio.Button value="llm">
                        <RobotOutlined /> AI (LLM)
                    </Radio.Button>
                </Radio.Group>
            </div>

            {/* Generate / Cancel Button */}
            <div style={{ marginBottom: '16px', display: 'flex', gap: '8px' }}>
                {!loading ? (
                    <Button
                        type="primary"
                        onClick={handleGenerate}
                        disabled={!assessmentId}
                        style={{ backgroundColor: '#8b5cf6', borderColor: '#8b5cf6' }}
                    >
                        Generate Suggestions
                    </Button>
                ) : (
                    <Button
                        danger
                        icon={<StopOutlined />}
                        onClick={cancelGeneration}
                    >
                        Cancel
                    </Button>
                )}
            </div>

            {/* Loading */}
            {loading && (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <Spin indicator={<LoadingOutlined style={{ fontSize: 32, color: '#8b5cf6' }} spin />} />
                    <div style={{ marginTop: '12px', color: '#666' }}>
                        {engine === 'llm' ? 'AI is analyzing scan findings...' : 'Matching scan data to questions...'}
                    </div>
                </div>
            )}

            {/* Error */}
            {error && (
                <div style={{ padding: '12px', backgroundColor: '#fff2f0', borderRadius: '6px', marginBottom: '12px', border: '1px solid #ffccc7' }}>
                    <Text type="danger">{error}</Text>
                </div>
            )}

            {/* Results */}
            {!loading && suggestions && (
                <>
                    <div style={{ marginBottom: '12px', padding: '8px 12px', backgroundColor: '#f6f0ff', borderRadius: '6px' }}>
                        <Text>
                            <strong>{suggestions.total_suggestions}</strong> suggestion{suggestions.total_suggestions !== 1 ? 's' : ''} for{' '}
                            <strong>{suggestions.total_questions}</strong> unanswered question{suggestions.total_questions !== 1 ? 's' : ''}
                        </Text>
                    </div>

                    {suggestions.suggestions.length === 0 ? (
                        <Empty
                            description="No suggestions could be generated. Scans may not be relevant to the assessment questions."
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                        />
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {suggestions.suggestions.map((item) => (
                                <div
                                    key={item.question_id}
                                    style={{
                                        border: '1px solid #e8e8e8',
                                        borderRadius: '8px',
                                        padding: '12px',
                                        backgroundColor: '#fafafa',
                                    }}
                                >
                                    {/* Question */}
                                    <div style={{ marginBottom: '8px', fontSize: '13px', fontWeight: 500 }}>
                                        <Tag style={{ marginRight: '6px', fontWeight: 600 }}>Q{item.question_number}</Tag>
                                        {item.question_text}
                                    </div>

                                    {/* Answer + Confidence */}
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                        <Tag color={answerColors[item.suggested_answer] || 'default'} style={{ textTransform: 'uppercase', fontWeight: 600 }}>
                                            {item.suggested_answer}
                                        </Tag>
                                        <Tag style={{ color: confidenceColor(item.confidence), borderColor: confidenceColor(item.confidence) }}>
                                            {item.confidence}% confidence
                                        </Tag>
                                    </div>

                                    {/* Evidence */}
                                    <div style={{ fontSize: '12px', color: '#555', marginBottom: '8px', lineHeight: '1.5' }}>
                                        {item.evidence_description}
                                    </div>

                                    {/* Reasoning (collapsible) */}
                                    <Collapse
                                        size="small"
                                        ghost
                                        items={[{
                                            key: '1',
                                            label: <span style={{ fontSize: '11px', color: '#888' }}>Reasoning</span>,
                                            children: <div style={{ fontSize: '12px', color: '#666' }}>{item.reasoning}</div>,
                                        }]}
                                    />

                                    {/* Accept / Reject */}
                                    <div style={{ display: 'flex', gap: '8px', marginTop: '8px', justifyContent: 'flex-end' }}>
                                        <Button
                                            size="small"
                                            icon={<CloseOutlined />}
                                            onClick={() => handleReject(item.question_id)}
                                        >
                                            Reject
                                        </Button>
                                        <Button
                                            size="small"
                                            type="primary"
                                            icon={<CheckOutlined />}
                                            onClick={() => handleAccept(item)}
                                            style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
                                        >
                                            Accept
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}
        </Drawer>
    );
}
