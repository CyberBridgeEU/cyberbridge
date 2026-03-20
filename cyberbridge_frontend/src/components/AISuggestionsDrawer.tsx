import { Drawer, Button, Tag, Spin, Collapse, Typography, Steps, Progress } from 'antd';
import {
    RobotOutlined,
    CheckOutlined,
    CloseOutlined,
    LoadingOutlined,
    StopOutlined,
    BugOutlined,
    FileProtectOutlined,
    AimOutlined,
    FileSearchOutlined,
    BulbOutlined,
    GlobalOutlined,
    DatabaseOutlined,
    CheckCircleOutlined,
} from '@ant-design/icons';
import useAssessmentAISuggestStore from '../store/useAssessmentAISuggestStore';
import type { PlatformDataPreview } from '../store/useAssessmentAISuggestStore';
import { AnswerSuggestionItem } from '../store/useAssessmentScanSuggestStore';

const { Text } = Typography;

interface AISuggestionsDrawerProps {
    open: boolean;
    onClose: () => void;
    assessmentId: string | undefined;
    onApplySuggestion: (questionId: string, answer: string, evidenceDescription: string) => void;
    currentPage?: number;
    pageQuestionIds?: string[];
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

const severityColor = (sev: string) => {
    switch (sev?.toLowerCase()) {
        case 'critical': return 'red';
        case 'high': return 'volcano';
        case 'medium': return 'orange';
        case 'low': return 'blue';
        case 'info': return 'default';
        default: return 'default';
    }
};

const statusColor = (status: string) => {
    switch (status?.toLowerCase()) {
        case 'compliant': case 'met': return 'green';
        case 'partially compliant': case 'partially met': return 'orange';
        case 'not compliant': case 'not met': return 'red';
        case 'not assessed': return 'default';
        default: return 'default';
    }
};

// ===== Wizard Step Content Components =====

function StepScanFindings({ data }: { data: PlatformDataPreview }) {
    const findings = data.scan_findings || [];
    const stats = data.scan_stats || {};
    if (!findings.length && !stats.total) {
        return <EmptyStep message="No scan findings available" />;
    }
    return (
        <div>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '12px' }}>
                <MiniStat label="Total" value={stats.total ?? 0} />
                <MiniStat label="Remediated" value={stats.remediated ?? 0} />
                {stats.by_scanner && Object.entries(stats.by_scanner).map(([k, v]) => (
                    <MiniStat key={k} label={k.toUpperCase()} value={v} />
                ))}
            </div>
            {stats.by_severity && (
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '12px' }}>
                    {Object.entries(stats.by_severity).map(([sev, count]) => (
                        <Tag key={sev} color={severityColor(sev)}>{sev}: {count}</Tag>
                    ))}
                </div>
            )}
            <div style={{ fontSize: '12px', color: '#555' }}>
                <strong>Top findings:</strong>
                {findings.slice(0, 5).map((f, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 0', borderBottom: '1px solid #f0f0f0' }}>
                        <Tag color={severityColor(f.severity)} style={{ fontSize: '10px', margin: 0 }}>{f.severity}</Tag>
                        <span style={{ flex: 1 }}>{f.title}</span>
                        <Tag color={f.remediated ? 'green' : 'default'} style={{ fontSize: '10px', margin: 0 }}>{f.remediated ? 'Fixed' : 'Open'}</Tag>
                    </div>
                ))}
            </div>
        </div>
    );
}

function StepPolicies({ data }: { data: PlatformDataPreview }) {
    const policies = data.policies || [];
    if (!policies.length) return <EmptyStep message="No approved policies found for this framework" />;
    return (
        <div>
            <Text type="secondary" style={{ fontSize: '12px' }}>{policies.length} approved polic{policies.length === 1 ? 'y' : 'ies'}</Text>
            <div style={{ marginTop: '8px' }}>
                {policies.map((p, i) => (
                    <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                        <div style={{ fontWeight: 500, fontSize: '13px' }}>{p.code ? `${p.code}: ` : ''}{p.title}</div>
                        {p.body && <div style={{ fontSize: '11px', color: '#888', marginTop: '2px' }}>{p.body.length > 120 ? p.body.slice(0, 120) + '...' : p.body}</div>}
                    </div>
                ))}
            </div>
        </div>
    );
}

function StepObjectives({ data }: { data: PlatformDataPreview }) {
    const objectives = data.objectives || [];
    if (!objectives.length) return <EmptyStep message="No objectives found for this framework" />;
    return (
        <div>
            <Text type="secondary" style={{ fontSize: '12px' }}>{objectives.length} objective{objectives.length === 1 ? '' : 's'}</Text>
            <div style={{ marginTop: '8px' }}>
                {objectives.map((o, i) => (
                    <div key={i} style={{ padding: '6px 0', borderBottom: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ flex: 1 }}>
                            <span style={{ fontSize: '11px', color: '#888' }}>{o.chapter}</span>
                            <div style={{ fontSize: '13px' }}>{o.title}</div>
                        </div>
                        <Tag color={statusColor(o.status)} style={{ fontSize: '10px', margin: 0 }}>{o.status}</Tag>
                    </div>
                ))}
            </div>
        </div>
    );
}

function StepEvidence({ data }: { data: PlatformDataPreview }) {
    const answered = data.answered_evidence || [];
    const library = data.evidence_library || [];
    if (!answered.length && !library.length) return <EmptyStep message="No evidence data available" />;
    return (
        <div>
            {answered.length > 0 && (
                <>
                    <Text strong style={{ fontSize: '12px' }}>Answered Evidence ({answered.length})</Text>
                    <div style={{ marginTop: '4px', marginBottom: '12px' }}>
                        {answered.map((e, i) => (
                            <div key={i} style={{ padding: '4px 0', borderBottom: '1px solid #f0f0f0', fontSize: '12px' }}>
                                <div style={{ color: '#333' }}>{e.question}</div>
                                <div style={{ color: '#888' }}>Answer: <Tag style={{ fontSize: '10px', margin: '0 4px' }}>{e.answer}</Tag>{e.evidence_desc}</div>
                            </div>
                        ))}
                    </div>
                </>
            )}
            {library.length > 0 && (
                <>
                    <Text strong style={{ fontSize: '12px' }}>Evidence Library ({library.length})</Text>
                    <div style={{ marginTop: '4px' }}>
                        {library.map((item, i) => (
                            <div key={i} style={{ padding: '4px 0', borderBottom: '1px solid #f0f0f0', fontSize: '12px' }}>
                                <span style={{ fontWeight: 500 }}>{item.name}</span>
                                <Tag style={{ fontSize: '10px', marginLeft: '6px' }}>{item.type}</Tag>
                                {item.description && <div style={{ color: '#888', fontSize: '11px' }}>{item.description}</div>}
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}

function StepAdvisor({ data }: { data: PlatformDataPreview }) {
    const advisor = data.compliance_advisor;
    if (!advisor || !advisor.company_summary) {
        return <EmptyStep message="No compliance advisor analysis found. Run the Compliance Advisor first to include website analysis in suggestions." />;
    }
    return (
        <div>
            <div style={{ marginBottom: '8px', fontSize: '13px', lineHeight: 1.6 }}>{advisor.company_summary}</div>
            {advisor.analyzed_url && <Text type="secondary" style={{ fontSize: '11px' }}>Source: {advisor.analyzed_url}</Text>}
            {advisor.recommendations?.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                    <Text strong style={{ fontSize: '12px' }}>Recommended Frameworks:</Text>
                    <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginTop: '4px' }}>
                        {advisor.recommendations.map((r, i) => (
                            <Tag key={i} color={r.relevance === 'high' ? 'green' : r.relevance === 'medium' ? 'gold' : 'blue'}>
                                {r.framework}
                            </Tag>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function StepSummary({ data, unansweredCount, onGenerate, currentPage }: { data: PlatformDataPreview; unansweredCount: number; onGenerate: () => void; currentPage?: number }) {
    const counts = {
        findings: (data.scan_findings || []).length,
        policies: (data.policies || []).length,
        objectives: (data.objectives || []).length,
        evidence: (data.answered_evidence || []).length + (data.evidence_library || []).length,
        advisor: data.compliance_advisor?.company_summary ? 1 : 0,
    };
    const totalSources = Object.values(counts).reduce((a, b) => a + b, 0);

    return (
        <div>
            {data.org_domain && (
                <div style={{ marginBottom: '10px', fontSize: '13px' }}>
                    <GlobalOutlined style={{ marginRight: '6px', color: '#06b6d4' }} />
                    <strong>Organisation Domain:</strong> {data.org_domain}
                </div>
            )}
            <div style={{ marginBottom: '10px', fontSize: '13px' }}>
                <strong>{unansweredCount}</strong> unanswered question{unansweredCount !== 1 ? 's' : ''} to analyze
                {currentPage && <span style={{ color: '#888' }}> (Page {currentPage})</span>}
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '16px' }}>
                <MiniStat label="Findings" value={counts.findings} />
                <MiniStat label="Policies" value={counts.policies} />
                <MiniStat label="Objectives" value={counts.objectives} />
                <MiniStat label="Evidence" value={counts.evidence} />
                <MiniStat label="Advisor" value={counts.advisor} />
                <MiniStat label="Total" value={totalSources} accent />
            </div>
            {unansweredCount === 0 ? (
                <div style={{ padding: '12px', backgroundColor: '#f6ffed', borderRadius: '6px', border: '1px solid #b7eb8f', textAlign: 'center' }}>
                    <Text type="success">All questions on this page are already answered.</Text>
                </div>
            ) : (
                <Button
                    type="primary"
                    size="large"
                    onClick={onGenerate}
                    icon={<RobotOutlined />}
                    style={{ backgroundColor: '#06b6d4', borderColor: '#06b6d4', width: '100%' }}
                >
                    Generate Suggestions (one by one)
                </Button>
            )}
        </div>
    );
}

function MiniStat({ label, value, accent }: { label: string; value: number; accent?: boolean }) {
    return (
        <div style={{
            padding: '6px 12px',
            borderRadius: '6px',
            backgroundColor: accent ? '#ecfeff' : '#fafafa',
            border: `1px solid ${accent ? '#a5f3fc' : '#e8e8e8'}`,
            textAlign: 'center',
            minWidth: '60px',
        }}>
            <div style={{ fontSize: '16px', fontWeight: 600, color: accent ? '#06b6d4' : '#333' }}>{value}</div>
            <div style={{ fontSize: '10px', color: '#888' }}>{label}</div>
        </div>
    );
}

function EmptyStep({ message }: { message: string }) {
    return <div style={{ padding: '20px 0', color: '#999', fontSize: '13px', textAlign: 'center' }}>{message}</div>;
}

// ===== Main Drawer Component =====

const wizardSteps = [
    { title: 'Scan Findings', icon: <BugOutlined /> },
    { title: 'Policies', icon: <FileProtectOutlined /> },
    { title: 'Objectives', icon: <AimOutlined /> },
    { title: 'Evidence', icon: <FileSearchOutlined /> },
    { title: 'Advisor', icon: <BulbOutlined /> },
    { title: 'Summary', icon: <GlobalOutlined /> },
];

export default function AISuggestionsDrawer({ open, onClose, assessmentId, onApplySuggestion, currentPage, pageQuestionIds }: AISuggestionsDrawerProps) {
    const {
        loading, error,
        platformData, gatherLoading, gatherError, wizardStep, unansweredCount,
        gatherPlatformData, setWizardStep,
        questionQueue, queueIndex, currentSuggestion, completedCount, acceptedCount, skippedCount, sequentialDone,
        startSequentialGeneration, advanceQueue, cancelGeneration, resetAll,
    } = useAssessmentAISuggestStore();

    const isSequentialMode = questionQueue.length > 0 || sequentialDone;
    const processedCount = completedCount + skippedCount;
    const rejectedCount = completedCount - acceptedCount;

    const handleCollectData = () => {
        if (!assessmentId) return;
        gatherPlatformData(assessmentId, pageQuestionIds);
    };

    const handleGenerate = () => {
        if (!assessmentId || !pageQuestionIds?.length) return;
        startSequentialGeneration(assessmentId, pageQuestionIds);
    };

    const handleAccept = (item: AnswerSuggestionItem) => {
        onApplySuggestion(item.question_id, item.suggested_answer, item.evidence_description);
        advanceQueue(true);
    };

    const handleReject = () => {
        advanceQueue(false);
    };

    const handleClose = () => {
        resetAll();
        onClose();
    };

    const renderWizardStepContent = () => {
        if (!platformData) return null;
        switch (wizardStep) {
            case 0: return <StepScanFindings data={platformData} />;
            case 1: return <StepPolicies data={platformData} />;
            case 2: return <StepObjectives data={platformData} />;
            case 3: return <StepEvidence data={platformData} />;
            case 4: return <StepAdvisor data={platformData} />;
            case 5: return <StepSummary data={platformData} unansweredCount={unansweredCount} onGenerate={handleGenerate} currentPage={currentPage} />;
            default: return null;
        }
    };

    return (
        <Drawer
            title={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <RobotOutlined style={{ color: '#06b6d4' }} />
                    <span>AI Suggest Answers</span>
                    {currentPage && <Tag color="cyan" style={{ marginLeft: 'auto', fontSize: '11px' }}>Page {currentPage}</Tag>}
                </div>
            }
            placement="right"
            width={560}
            open={open}
            onClose={handleClose}
            destroyOnClose
        >
            {/* ===== Sequential Generation Mode ===== */}
            {isSequentialMode ? (
                <>
                    {/* Progress Header */}
                    <div style={{ marginBottom: '16px', padding: '12px', backgroundColor: '#ecfeff', borderRadius: '8px', border: '1px solid #a5f3fc' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <Text strong style={{ fontSize: '13px' }}>
                                {sequentialDone
                                    ? 'Generation Complete'
                                    : `Question ${Math.min(queueIndex + 1, questionQueue.length)} of ${questionQueue.length}`
                                }
                            </Text>
                            {currentPage && <Tag color="cyan" style={{ fontSize: '10px', margin: 0 }}>Page {currentPage}</Tag>}
                        </div>
                        <Progress
                            percent={questionQueue.length > 0 ? Math.round((processedCount / questionQueue.length) * 100) : 0}
                            size="small"
                            strokeColor="#06b6d4"
                        />
                        <div style={{ display: 'flex', gap: '12px', marginTop: '6px', fontSize: '12px', color: '#555' }}>
                            <span style={{ color: '#52c41a' }}>Accepted: {acceptedCount}</span>
                            <span style={{ color: '#ff4d4f' }}>Rejected: {rejectedCount}</span>
                            <span style={{ color: '#999' }}>Skipped: {skippedCount}</span>
                        </div>
                    </div>

                    {/* Loading — processing current question */}
                    {loading && (
                        <div style={{ textAlign: 'center', padding: '40px 0' }}>
                            <Spin indicator={<LoadingOutlined style={{ fontSize: 32, color: '#06b6d4' }} spin />} />
                            <div style={{ marginTop: '12px', color: '#666' }}>
                                Analyzing question {queueIndex + 1} of {questionQueue.length}...
                            </div>
                            <Button
                                danger
                                icon={<StopOutlined />}
                                onClick={cancelGeneration}
                                style={{ marginTop: '12px' }}
                            >
                                Cancel
                            </Button>
                        </div>
                    )}

                    {/* Current Suggestion Card */}
                    {currentSuggestion && !loading && (
                        <div style={{
                            border: '1px solid #e8e8e8',
                            borderRadius: '8px',
                            padding: '16px',
                            backgroundColor: '#fafafa',
                        }}>
                            {/* Question */}
                            <div style={{ marginBottom: '10px', fontSize: '13px', fontWeight: 500 }}>
                                <Tag style={{ marginRight: '6px', fontWeight: 600 }}>Q{currentSuggestion.question_number}</Tag>
                                {currentSuggestion.question_text}
                            </div>

                            {/* Answer + Confidence */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                                <Tag color={answerColors[currentSuggestion.suggested_answer] || 'default'} style={{ textTransform: 'uppercase', fontWeight: 600 }}>
                                    {currentSuggestion.suggested_answer}
                                </Tag>
                                <Tag style={{ color: confidenceColor(currentSuggestion.confidence), borderColor: confidenceColor(currentSuggestion.confidence) }}>
                                    {currentSuggestion.confidence}% confidence
                                </Tag>
                            </div>

                            {/* Evidence */}
                            <div style={{ fontSize: '12px', color: '#555', marginBottom: '10px', lineHeight: '1.5' }}>
                                {currentSuggestion.evidence_description}
                            </div>

                            {/* Reasoning (collapsible) */}
                            <Collapse
                                size="small"
                                ghost
                                items={[{
                                    key: '1',
                                    label: <span style={{ fontSize: '11px', color: '#888' }}>Reasoning</span>,
                                    children: <div style={{ fontSize: '12px', color: '#666' }}>{currentSuggestion.reasoning}</div>,
                                }]}
                            />

                            {/* Accept / Reject / Cancel */}
                            <div style={{ display: 'flex', gap: '8px', marginTop: '12px', justifyContent: 'flex-end' }}>
                                <Button
                                    danger
                                    size="small"
                                    icon={<StopOutlined />}
                                    onClick={cancelGeneration}
                                >
                                    Cancel
                                </Button>
                                <Button
                                    size="small"
                                    icon={<CloseOutlined />}
                                    onClick={handleReject}
                                >
                                    Reject
                                </Button>
                                <Button
                                    size="small"
                                    type="primary"
                                    icon={<CheckOutlined />}
                                    onClick={() => handleAccept(currentSuggestion)}
                                    style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
                                >
                                    Accept
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* Error during generation */}
                    {error && !loading && !sequentialDone && (
                        <div style={{ padding: '12px', backgroundColor: '#fff2f0', borderRadius: '6px', marginBottom: '12px', border: '1px solid #ffccc7' }}>
                            <Text type="danger">{error}</Text>
                            <div style={{ marginTop: '8px', display: 'flex', gap: '8px' }}>
                                <Button size="small" danger onClick={cancelGeneration}>Stop</Button>
                            </div>
                        </div>
                    )}

                    {/* Done */}
                    {sequentialDone && !loading && !currentSuggestion && (
                        <div style={{ textAlign: 'center', padding: '30px 0' }}>
                            <CheckCircleOutlined style={{ fontSize: 40, color: '#52c41a', marginBottom: '12px' }} />
                            <div style={{ fontSize: '15px', fontWeight: 500, marginBottom: '16px' }}>
                                {processedCount === 0 && questionQueue.length === 0
                                    ? 'Generation cancelled'
                                    : 'All done!'
                                }
                            </div>
                            <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', marginBottom: '20px', fontSize: '13px' }}>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{ fontSize: '20px', fontWeight: 600, color: '#52c41a' }}>{acceptedCount}</div>
                                    <div style={{ color: '#888' }}>Accepted</div>
                                </div>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{ fontSize: '20px', fontWeight: 600, color: '#ff4d4f' }}>{rejectedCount}</div>
                                    <div style={{ color: '#888' }}>Rejected</div>
                                </div>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{ fontSize: '20px', fontWeight: 600, color: '#999' }}>{skippedCount}</div>
                                    <div style={{ color: '#888' }}>Skipped</div>
                                </div>
                            </div>
                            <Button type="primary" onClick={handleClose} style={{ backgroundColor: '#06b6d4', borderColor: '#06b6d4' }}>
                                Close
                            </Button>
                        </div>
                    )}
                </>
            ) : (
                /* ===== Wizard Mode ===== */
                <>
                    {/* Info Banner */}
                    <div style={{ marginBottom: '16px', padding: '10px 12px', backgroundColor: '#ecfeff', borderRadius: '6px', border: '1px solid #a5f3fc', fontSize: '12px', color: '#155e75' }}>
                        <DatabaseOutlined style={{ marginRight: '6px' }} />
                        Review the platform data that AI will use to generate answer suggestions{currentPage ? ` for Page ${currentPage}` : ''}. Click "Collect Data" to begin.
                    </div>

                    {/* Collect Data Button */}
                    {!platformData && !gatherLoading && (
                        <div style={{ marginBottom: '16px' }}>
                            <Button
                                type="primary"
                                onClick={handleCollectData}
                                disabled={!assessmentId}
                                icon={<DatabaseOutlined />}
                                style={{ backgroundColor: '#06b6d4', borderColor: '#06b6d4' }}
                            >
                                Collect Data
                            </Button>
                        </div>
                    )}

                    {/* Gather Loading */}
                    {gatherLoading && (
                        <div style={{ textAlign: 'center', padding: '40px 0' }}>
                            <Spin indicator={<LoadingOutlined style={{ fontSize: 32, color: '#06b6d4' }} spin />} />
                            <div style={{ marginTop: '12px', color: '#666' }}>
                                Collecting platform data...
                            </div>
                        </div>
                    )}

                    {/* Gather Error */}
                    {gatherError && (
                        <div style={{ padding: '12px', backgroundColor: '#fff2f0', borderRadius: '6px', marginBottom: '12px', border: '1px solid #ffccc7' }}>
                            <Text type="danger">{gatherError}</Text>
                        </div>
                    )}

                    {/* Wizard Steps */}
                    {platformData && !gatherLoading && (
                        <>
                            <Steps
                                current={wizardStep}
                                onChange={setWizardStep}
                                size="small"
                                style={{ marginBottom: '16px' }}
                                items={wizardSteps.map((s) => ({
                                    title: s.title,
                                    icon: s.icon,
                                }))}
                            />

                            {/* Step Content */}
                            <div style={{
                                padding: '12px',
                                backgroundColor: '#fafafa',
                                borderRadius: '8px',
                                border: '1px solid #e8e8e8',
                                maxHeight: '400px',
                                overflowY: 'auto',
                                marginBottom: '12px',
                            }}>
                                {renderWizardStepContent()}
                            </div>

                            {/* Navigation */}
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Button
                                    disabled={wizardStep === 0}
                                    onClick={() => setWizardStep(wizardStep - 1)}
                                >
                                    Previous
                                </Button>
                                {wizardStep < wizardSteps.length - 1 ? (
                                    <Button
                                        type="primary"
                                        onClick={() => setWizardStep(wizardStep + 1)}
                                        style={{ backgroundColor: '#06b6d4', borderColor: '#06b6d4' }}
                                    >
                                        Next
                                    </Button>
                                ) : null}
                            </div>
                        </>
                    )}
                </>
            )}
        </Drawer>
    );
}
