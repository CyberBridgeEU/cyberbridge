import { Table, Tag, notification, Tabs, Card, Progress, Row, Col, Input, Button, Select, Modal, Radio, DatePicker, Tooltip, Spin, Empty, Typography } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { PlusOutlined, EditOutlined, DeleteOutlined, ArrowLeftOutlined, SaveOutlined, CheckCircleOutlined, ScheduleOutlined } from '@ant-design/icons';
import useRiskAssessmentStore, { RiskWithAssessment, TreatmentAction } from "../store/useRiskAssessmentStore.ts";
import useRiskStore from "../store/useRiskStore.ts";
import useAssetStore from "../store/useAssetStore.ts";
import useControlStore from "../store/useControlStore.ts";
import { useEffect, useState, useMemo } from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import { RiskAssessmentInfo } from "../constants/infoContent.tsx";
import { useLocation, useRoute } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { scoreToSeverity, severityToColor, getGaugeColor, getGaugePercent, getMatrixCellColor } from "../utils/riskScoreUtils.ts";
import ConnectionBoard from "../components/ConnectionBoard.tsx";
import RiskAssessmentGuideWizard from "../components/RiskAssessmentGuideWizard.tsx";
import dayjs from "dayjs";

const { TextArea } = Input;
const { Text } = Typography;

const RiskAssessmentPage = () => {
    const [api, contextHolder] = notification.useNotification();
    const [location, setLocation] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const [, params] = useRoute("/risk_assessment/:riskId");
    const riskId = params?.riskId;

    // Stores
    const {
        risks, fetchRisksWithAssessments, assessments, currentAssessment,
        fetchAssessments, fetchAssessment,
        createAssessment, updateAssessment, deleteAssessment,
        createAction, updateAction, deleteAction, loading
    } = useRiskAssessmentStore();

    const {
        linkedAssets, linkedControls, linkedObjectives,
        fetchLinkedAssets, fetchLinkedControls, fetchLinkedObjectives,
        linkAsset, unlinkAsset, linkObjective, unlinkObjective
    } = useRiskStore();

    const { assets, fetchAssets } = useAssetStore();
    const { controls, fetchControls, linkControlToRisk, unlinkControlFromRisk } = useControlStore();

    // Local state
    const [activeTab, setActiveTab] = useState<string>('assessment');
    const [isEditing, setIsEditing] = useState(false);
    const [selectedAssessmentId, setSelectedAssessmentId] = useState<string | null>(null);
    const [actionModalOpen, setActionModalOpen] = useState(false);
    const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
    const [editingAction, setEditingAction] = useState<TreatmentAction | null>(null);

    // Form state for assessment
    const [formData, setFormData] = useState({
        description: '',
        inherent_impact: 3,
        inherent_likelihood: 3,
        current_impact: 3,
        current_likelihood: 3,
        target_impact: null as number | null,
        target_likelihood: null as number | null,
        residual_impact: null as number | null,
        residual_likelihood: null as number | null,
        impact_health: '',
        impact_financial: '',
        impact_service: '',
        impact_legal: '',
        impact_reputation: '',
        status: 'Draft',
    });

    // Action form state
    const [actionForm, setActionForm] = useState({
        description: '',
        due_date: null as string | null,
        owner: '',
        status: 'Open',
        completion_notes: '',
    });

    // Load data
    useEffect(() => {
        if (!riskId) {
            fetchRisksWithAssessments();
        }
    }, [riskId]);

    useEffect(() => {
        if (riskId) {
            fetchAssessments(riskId);
            fetchLinkedAssets(riskId);
            fetchLinkedControls(riskId);
            fetchLinkedObjectives(riskId);
            fetchAssets();
            fetchControls();
        }
    }, [riskId]);

    // Populate form when assessment loads
    useEffect(() => {
        if (currentAssessment) {
            setFormData({
                description: currentAssessment.description || '',
                inherent_impact: currentAssessment.inherent_impact,
                inherent_likelihood: currentAssessment.inherent_likelihood,
                current_impact: currentAssessment.current_impact,
                current_likelihood: currentAssessment.current_likelihood,
                target_impact: currentAssessment.target_impact,
                target_likelihood: currentAssessment.target_likelihood,
                residual_impact: currentAssessment.residual_impact,
                residual_likelihood: currentAssessment.residual_likelihood,
                impact_health: currentAssessment.impact_health || '',
                impact_financial: currentAssessment.impact_financial || '',
                impact_service: currentAssessment.impact_service || '',
                impact_legal: currentAssessment.impact_legal || '',
                impact_reputation: currentAssessment.impact_reputation || '',
                status: currentAssessment.status,
            });
            setIsEditing(false);
        }
    }, [currentAssessment]);

    // Handle assessment selection
    const handleSelectAssessment = (assessmentId: string) => {
        setSelectedAssessmentId(assessmentId);
        if (riskId) {
            fetchAssessment(riskId, assessmentId);
        }
    };

    // Save assessment
    const handleSave = async () => {
        if (!riskId) return;

        const data = {
            ...formData,
            target_impact: formData.target_impact || undefined,
            target_likelihood: formData.target_likelihood || undefined,
            residual_impact: formData.residual_impact || undefined,
            residual_likelihood: formData.residual_likelihood || undefined,
        };

        let success: boolean;
        if (currentAssessment && !isEditing) {
            // Update existing
            success = await updateAssessment(riskId, currentAssessment.id, data);
        } else {
            // Create new
            success = await createAssessment(riskId, data);
        }

        if (success) {
            api.success({ message: currentAssessment && !isEditing ? 'Assessment updated' : 'Assessment created' });
            fetchAssessments(riskId);
            setIsEditing(false);
        } else {
            api.error({ message: 'Failed to save assessment' });
        }
    };

    // Create new assessment
    const handleNewAssessment = () => {
        setFormData({
            description: '',
            inherent_impact: currentAssessment?.inherent_impact || 3,
            inherent_likelihood: currentAssessment?.inherent_likelihood || 3,
            current_impact: currentAssessment?.current_impact || 3,
            current_likelihood: currentAssessment?.current_likelihood || 3,
            target_impact: currentAssessment?.target_impact || null,
            target_likelihood: currentAssessment?.target_likelihood || null,
            residual_impact: currentAssessment?.residual_impact || null,
            residual_likelihood: currentAssessment?.residual_likelihood || null,
            impact_health: currentAssessment?.impact_health || '',
            impact_financial: currentAssessment?.impact_financial || '',
            impact_service: currentAssessment?.impact_service || '',
            impact_legal: currentAssessment?.impact_legal || '',
            impact_reputation: currentAssessment?.impact_reputation || '',
            status: 'Draft',
        });
        setIsEditing(true);
    };

    // Delete assessment
    const handleDeleteAssessment = () => {
        if (!riskId || !currentAssessment) return;
        setDeleteConfirmOpen(true);
    };

    const handleConfirmDelete = async () => {
        if (!riskId || !currentAssessment) return;
        const success = await deleteAssessment(riskId, currentAssessment.id);
        setDeleteConfirmOpen(false);
        if (success) {
            api.success({ message: 'Assessment deleted' });
            fetchAssessments(riskId);
        } else {
            api.error({ message: 'Failed to delete assessment' });
        }
    };

    // Treatment action handlers
    const handleSaveAction = async () => {
        if (!riskId || !currentAssessment) return;
        let success: boolean;
        if (editingAction) {
            success = await updateAction(riskId, currentAssessment.id, editingAction.id, actionForm);
        } else {
            success = await createAction(riskId, currentAssessment.id, actionForm);
        }
        if (success) {
            api.success({ message: editingAction ? 'Action updated' : 'Action created' });
            setActionModalOpen(false);
            setEditingAction(null);
            setActionForm({ description: '', due_date: null, owner: '', status: 'Open', completion_notes: '' });
        } else {
            api.error({ message: 'Failed to save action' });
        }
    };

    const handleDeleteAction = async (actionId: string) => {
        if (!riskId || !currentAssessment) return;
        const success = await deleteAction(riskId, currentAssessment.id, actionId);
        if (success) {
            api.success({ message: 'Action deleted' });
        } else {
            api.error({ message: 'Failed to delete action' });
        }
    };

    // Score gauge component
    const ScoreGauge = ({ label, score, impact, likelihood }: { label: string; score: number | null; impact: number | null; likelihood: number | null }) => (
        <div style={{ textAlign: 'center' }}>
            <Text strong style={{ fontSize: 14, marginBottom: 8, display: 'block' }}>{label}</Text>
            <Progress
                type="circle"
                percent={getGaugePercent(score)}
                format={() => score != null ? `${score}` : '—'}
                strokeColor={getGaugeColor(score)}
                size={120}
            />
            <div style={{ marginTop: 8 }}>
                <Tag color={severityToColor(scoreToSeverity(score))} style={{ color: '#fff' }}>
                    {scoreToSeverity(score) || 'N/A'}
                </Tag>
            </div>
            <div style={{ marginTop: 4, fontSize: 12, color: '#888' }}>
                Impact: {impact ?? '—'} × Likelihood: {likelihood ?? '—'}
            </div>
        </div>
    );

    // Impact/Likelihood selector
    const ScoreSelector = ({ label, impactValue, likelihoodValue, onImpactChange, onLikelihoodChange, disabled }: {
        label: string;
        impactValue: number;
        likelihoodValue: number;
        onImpactChange: (v: number) => void;
        onLikelihoodChange: (v: number) => void;
        disabled?: boolean;
    }) => (
        <Card size="small" title={label} style={{ marginBottom: 16 }}>
            <Row gutter={16}>
                <Col span={12}>
                    <Text style={{ display: 'block', marginBottom: 4 }}>Impact (1-5)</Text>
                    <Radio.Group
                        buttonStyle="solid"
                        value={impactValue}
                        onChange={e => onImpactChange(e.target.value)}
                        disabled={disabled}
                    >
                        {[1, 2, 3, 4, 5].map(v => (
                            <Radio.Button key={v} value={v}>{v}</Radio.Button>
                        ))}
                    </Radio.Group>
                </Col>
                <Col span={12}>
                    <Text style={{ display: 'block', marginBottom: 4 }}>Likelihood (1-5)</Text>
                    <Radio.Group
                        buttonStyle="solid"
                        value={likelihoodValue}
                        onChange={e => onLikelihoodChange(e.target.value)}
                        disabled={disabled}
                    >
                        {[1, 2, 3, 4, 5].map(v => (
                            <Radio.Button key={v} value={v}>{v}</Radio.Button>
                        ))}
                    </Radio.Group>
                </Col>
            </Row>
            <div style={{ marginTop: 8 }}>
                Score: <Tag color={severityToColor(scoreToSeverity(impactValue * likelihoodValue))} style={{ color: '#fff' }}>
                    {impactValue * likelihoodValue} — {scoreToSeverity(impactValue * likelihoodValue)}
                </Tag>
            </div>
        </Card>
    );

    // 5x5 Risk Matrix
    const RiskMatrix = () => {
        const labels = ['Rare (1)', 'Unlikely (2)', 'Possible (3)', 'Likely (4)', 'Almost Certain (5)'];
        const impactLabels = ['Insignificant (1)', 'Minor (2)', 'Moderate (3)', 'Major (4)', 'Catastrophic (5)'];
        return (
            <Card size="small" title="5×5 Risk Matrix Reference" style={{ marginTop: 16 }}>
                <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                        <thead>
                            <tr>
                                <th style={{ border: '1px solid #d9d9d9', padding: '6px 8px', background: '#fafafa' }}>Impact ↓ / Likelihood →</th>
                                {labels.map((l, i) => (
                                    <th key={i} style={{ border: '1px solid #d9d9d9', padding: '6px 8px', background: '#fafafa', textAlign: 'center' }}>{l}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {[5, 4, 3, 2, 1].map(impact => (
                                <tr key={impact}>
                                    <td style={{ border: '1px solid #d9d9d9', padding: '6px 8px', fontWeight: 600, background: '#fafafa' }}>
                                        {impactLabels[impact - 1]}
                                    </td>
                                    {[1, 2, 3, 4, 5].map(likelihood => {
                                        const score = impact * likelihood;
                                        const color = getMatrixCellColor(impact, likelihood);
                                        return (
                                            <td key={likelihood} style={{
                                                border: '1px solid #d9d9d9', padding: '6px 8px', textAlign: 'center',
                                                background: color, color: '#fff', fontWeight: 600
                                            }}>
                                                {score}
                                            </td>
                                        );
                                    })}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </Card>
        );
    };

    // Current risk info for detail view header
    const currentRisk = useMemo(() => {
        if (!riskId) return null;
        return risks.find(r => r.id === riskId) || null;
    }, [riskId, risks]);

    const isReadOnly = false;

    // ===========================
    // LIST MODE
    // ===========================
    if (!riskId) {
        const listColumns = [
            {
                title: 'Code',
                dataIndex: 'risk_code',
                key: 'risk_code',
                width: 90,
                sorter: (a: RiskWithAssessment, b: RiskWithAssessment) => {
                    const numA = parseInt(a.risk_code?.replace('RSK-', '') || '999');
                    const numB = parseInt(b.risk_code?.replace('RSK-', '') || '999');
                    return numA - numB;
                },
                render: (text: string) => text ? <Tag color="blue">{text}</Tag> : <span style={{ color: '#bfbfbf' }}>—</span>,
                defaultSortOrder: 'ascend' as const,
            },
            {
                title: 'Risk Name',
                dataIndex: 'risk_category_name',
                key: 'risk_category_name',
                width: 200,
                ellipsis: true,
                sorter: (a: RiskWithAssessment, b: RiskWithAssessment) => a.risk_category_name.localeCompare(b.risk_category_name),
            },
            {
                title: 'Inherent',
                dataIndex: 'inherent_risk_score',
                key: 'inherent_risk_score',
                width: 100,
                sorter: (a: RiskWithAssessment, b: RiskWithAssessment) => (a.inherent_risk_score || 0) - (b.inherent_risk_score || 0),
                render: (score: number | null, record: RiskWithAssessment) => score != null
                    ? <Tag color={severityToColor(record.inherent_severity as any)}  style={{ color: '#fff' }}>{score}</Tag>
                    : <span style={{ color: '#bfbfbf' }}>—</span>,
            },
            {
                title: 'Current',
                dataIndex: 'current_risk_score',
                key: 'current_risk_score',
                width: 100,
                sorter: (a: RiskWithAssessment, b: RiskWithAssessment) => (a.current_risk_score || 0) - (b.current_risk_score || 0),
                render: (score: number | null, record: RiskWithAssessment) => score != null
                    ? <Tag color={severityToColor(record.current_severity as any)} style={{ color: '#fff' }}>{score}</Tag>
                    : <span style={{ color: '#bfbfbf' }}>—</span>,
            },
            {
                title: 'Target',
                dataIndex: 'target_risk_score',
                key: 'target_risk_score',
                width: 100,
                sorter: (a: RiskWithAssessment, b: RiskWithAssessment) => (a.target_risk_score || 0) - (b.target_risk_score || 0),
                render: (score: number | null, record: RiskWithAssessment) => score != null
                    ? <Tag color={severityToColor(record.target_severity as any)} style={{ color: '#fff' }}>{score}</Tag>
                    : <span style={{ color: '#bfbfbf' }}>—</span>,
            },
            {
                title: 'Residual',
                dataIndex: 'residual_risk_score',
                key: 'residual_risk_score',
                width: 100,
                sorter: (a: RiskWithAssessment, b: RiskWithAssessment) => (a.residual_risk_score || 0) - (b.residual_risk_score || 0),
                render: (score: number | null, record: RiskWithAssessment) => score != null
                    ? <Tag color={severityToColor(record.residual_severity as any)} style={{ color: '#fff' }}>{score}</Tag>
                    : <span style={{ color: '#bfbfbf' }}>—</span>,
            },
            {
                title: 'Assessment Status',
                dataIndex: 'assessment_status',
                key: 'assessment_status',
                width: 160,
                render: (text: string | null) => {
                    if (!text) return <Tag>Not Assessed</Tag>;
                    const color = text.includes('Assessed') ? 'green' : text.includes('progress') ? 'orange' : 'default';
                    return <Tag color={color}>{text}</Tag>;
                },
            },
            {
                title: 'Last Assessed',
                dataIndex: 'last_assessed_at',
                key: 'last_assessed_at',
                width: 140,
                render: (text: string | null) => text ? new Date(text).toLocaleDateString() : <span style={{ color: '#bfbfbf' }}>—</span>,
                sorter: (a: RiskWithAssessment, b: RiskWithAssessment) => {
                    const da = a.last_assessed_at ? new Date(a.last_assessed_at).getTime() : 0;
                    const db = b.last_assessed_at ? new Date(b.last_assessed_at).getTime() : 0;
                    return da - db;
                },
            },
        ];

        return (
            <div>
                {contextHolder}
                <div className={'page-parent'}>
                    <Sidebar
                        selectedKeys={menuHighlighting.selectedKeys}
                        openKeys={menuHighlighting.openKeys}
                        onOpenChange={menuHighlighting.onOpenChange}
                    />
                    <div className={'page-content'}>
                        <div className="page-header">
                            <div className="page-header-left">
                                <ScheduleOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                                <InfoTitle title="Risk Assessment" infoContent={RiskAssessmentInfo} className="page-title" />
                            </div>
                            <div className="page-header-right">
                                <RiskAssessmentGuideWizard />
                            </div>
                        </div>
                        <Table
                            columns={listColumns}
                            dataSource={risks}
                            rowKey="id"
                            loading={loading}
                            size="small"
                            pagination={{ pageSize: 20 }}
                            onRow={(record) => ({
                                onClick: () => setLocation(`/risk_assessment/${record.id}`),
                                style: { cursor: 'pointer' }
                            })}
                        />
                    </div>
                </div>
            </div>
        );
    }

    // ===========================
    // DETAIL MODE (3-tab view)
    // ===========================

    // Action columns for treatment actions table
    const actionColumns = [
        {
            title: 'Description',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true,
        },
        {
            title: 'Due Date',
            dataIndex: 'due_date',
            key: 'due_date',
            width: 120,
            render: (text: string | null) => text ? new Date(text).toLocaleDateString() : '—',
        },
        {
            title: 'Owner',
            dataIndex: 'owner',
            key: 'owner',
            width: 150,
            render: (text: string | null) => text || '—',
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: 120,
            render: (text: string) => {
                const colors: Record<string, string> = { 'Open': 'blue', 'In Progress': 'orange', 'Completed': 'green', 'Cancelled': 'default' };
                return <Tag color={colors[text] || 'default'}>{text}</Tag>;
            },
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 100,
            render: (_: unknown, record: TreatmentAction) => (
                <div style={{ display: 'flex', gap: 4 }}>
                    <Tooltip title="Edit">
                        <Button
                            type="text"
                            size="small"
                            icon={<EditOutlined />}
                            onClick={() => {
                                setEditingAction(record);
                                setActionForm({
                                    description: record.description,
                                    due_date: record.due_date,
                                    owner: record.owner || '',
                                    status: record.status,
                                    completion_notes: record.completion_notes || '',
                                });
                                setActionModalOpen(true);
                            }}
                        />
                    </Tooltip>
                    <Tooltip title="Delete">
                        <Button
                            type="text"
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                            onClick={() => handleDeleteAction(record.id)}
                        />
                    </Tooltip>
                </div>
            ),
        },
    ];

    const tabItems = [
        {
            key: 'assessment',
            label: 'Assessment',
            children: (
                <Spin spinning={loading}>
                    {/* Risk Info Header */}
                    <Card size="small" style={{ marginBottom: 16 }}>
                        <Row gutter={16}>
                            <Col span={4}><Text type="secondary">Code:</Text> <Text strong>{currentAssessment?.risk_code || currentRisk?.risk_code || '—'}</Text></Col>
                            <Col span={10}><Text type="secondary">Risk Name:</Text> <Text strong>{currentAssessment?.risk_category_name || currentRisk?.risk_category_name || '—'}</Text></Col>
                            <Col span={10}><Text type="secondary">Description:</Text> <Text>{currentRisk?.risk_category_description || '—'}</Text></Col>
                        </Row>
                    </Card>

                    {/* Assessment History Selector + Actions */}
                    <Row gutter={16} style={{ marginBottom: 16 }}>
                        <Col span={12}>
                            {assessments.length > 0 && (
                                <Select
                                    style={{ width: '100%' }}
                                    value={currentAssessment?.id || undefined}
                                    onChange={handleSelectAssessment}
                                    placeholder="Select assessment"
                                >
                                    {assessments.map(a => (
                                        <Select.Option key={a.id} value={a.id}>
                                            Assessment #{a.assessment_number} — {new Date(a.created_at).toLocaleDateString()} — {a.status}
                                        </Select.Option>
                                    ))}
                                </Select>
                            )}
                        </Col>
                        <Col span={12} style={{ textAlign: 'right' }}>
                            <Button type="primary" icon={<PlusOutlined />} onClick={handleNewAssessment} style={{ marginRight: 8 }}>
                                New Assessment
                            </Button>
                            {currentAssessment && (
                                <>
                                    <Button icon={<SaveOutlined />} onClick={handleSave} style={{ marginRight: 8 }}>Save</Button>
                                    <Button danger icon={<DeleteOutlined />} onClick={handleDeleteAssessment}>Delete</Button>
                                </>
                            )}
                            {isEditing && (
                                <Button icon={<SaveOutlined />} type="primary" onClick={handleSave} style={{ marginLeft: 8 }}>
                                    Save New Assessment
                                </Button>
                            )}
                        </Col>
                    </Row>

                    {/* Score Gauges */}
                    <Row gutter={24} style={{ marginBottom: 24 }}>
                        <Col span={6}>
                            <ScoreGauge
                                label="Inherent Risk"
                                score={formData.inherent_impact * formData.inherent_likelihood}
                                impact={formData.inherent_impact}
                                likelihood={formData.inherent_likelihood}
                            />
                        </Col>
                        <Col span={6}>
                            <ScoreGauge
                                label="Current Risk"
                                score={formData.current_impact * formData.current_likelihood}
                                impact={formData.current_impact}
                                likelihood={formData.current_likelihood}
                            />
                        </Col>
                        <Col span={6}>
                            <ScoreGauge
                                label="Target Risk"
                                score={formData.target_impact && formData.target_likelihood ? formData.target_impact * formData.target_likelihood : null}
                                impact={formData.target_impact}
                                likelihood={formData.target_likelihood}
                            />
                        </Col>
                        <Col span={6}>
                            <ScoreGauge
                                label="Residual Risk"
                                score={formData.residual_impact && formData.residual_likelihood ? formData.residual_impact * formData.residual_likelihood : null}
                                impact={formData.residual_impact}
                                likelihood={formData.residual_likelihood}
                            />
                        </Col>
                    </Row>

                    {/* Score Selectors */}
                    <Row gutter={16}>
                        <Col span={12}>
                            <ScoreSelector
                                label="Inherent Risk (Before Controls)"
                                impactValue={formData.inherent_impact}
                                likelihoodValue={formData.inherent_likelihood}
                                onImpactChange={v => setFormData(d => ({ ...d, inherent_impact: v }))}
                                onLikelihoodChange={v => setFormData(d => ({ ...d, inherent_likelihood: v }))}
                                disabled={isReadOnly}
                            />
                        </Col>
                        <Col span={12}>
                            <ScoreSelector
                                label="Current Risk (With Existing Controls)"
                                impactValue={formData.current_impact}
                                likelihoodValue={formData.current_likelihood}
                                onImpactChange={v => setFormData(d => ({ ...d, current_impact: v }))}
                                onLikelihoodChange={v => setFormData(d => ({ ...d, current_likelihood: v }))}
                                disabled={isReadOnly}
                            />
                        </Col>
                    </Row>
                    <Row gutter={16}>
                        <Col span={12}>
                            <ScoreSelector
                                label="Target Risk (Desired State)"
                                impactValue={formData.target_impact || 1}
                                likelihoodValue={formData.target_likelihood || 1}
                                onImpactChange={v => setFormData(d => ({ ...d, target_impact: v }))}
                                onLikelihoodChange={v => setFormData(d => ({ ...d, target_likelihood: v }))}
                                disabled={isReadOnly}
                            />
                        </Col>
                        <Col span={12}>
                            <Card size="small" title="Status" style={{ marginBottom: 16 }}>
                                <Select
                                    value={formData.status}
                                    onChange={v => setFormData(d => ({ ...d, status: v }))}
                                    style={{ width: '100%' }}
                                    disabled={isReadOnly}
                                >
                                    <Select.Option value="Draft">Draft</Select.Option>
                                    <Select.Option value="In Progress">In Progress</Select.Option>
                                    <Select.Option value="Completed">Completed</Select.Option>
                                </Select>
                            </Card>
                        </Col>
                    </Row>

                    {/* Description */}
                    <Card size="small" title="Assessment Notes" style={{ marginBottom: 16 }}>
                        <TextArea
                            rows={3}
                            value={formData.description}
                            onChange={e => setFormData(d => ({ ...d, description: e.target.value }))}
                            placeholder="Enter assessment notes..."
                            disabled={isReadOnly}
                        />
                    </Card>

                    {/* Impact Loss Analysis */}
                    <Card size="small" title="Impact Loss Analysis" style={{ marginBottom: 16 }}>
                        <Row gutter={16}>
                            <Col span={12}>
                                <Text style={{ display: 'block', marginBottom: 4 }}>Health & Safety</Text>
                                <TextArea rows={2} value={formData.impact_health} onChange={e => setFormData(d => ({ ...d, impact_health: e.target.value }))} disabled={isReadOnly} />
                            </Col>
                            <Col span={12}>
                                <Text style={{ display: 'block', marginBottom: 4 }}>Financial</Text>
                                <TextArea rows={2} value={formData.impact_financial} onChange={e => setFormData(d => ({ ...d, impact_financial: e.target.value }))} disabled={isReadOnly} />
                            </Col>
                        </Row>
                        <Row gutter={16} style={{ marginTop: 12 }}>
                            <Col span={8}>
                                <Text style={{ display: 'block', marginBottom: 4 }}>Service Delivery</Text>
                                <TextArea rows={2} value={formData.impact_service} onChange={e => setFormData(d => ({ ...d, impact_service: e.target.value }))} disabled={isReadOnly} />
                            </Col>
                            <Col span={8}>
                                <Text style={{ display: 'block', marginBottom: 4 }}>Legal & Regulatory</Text>
                                <TextArea rows={2} value={formData.impact_legal} onChange={e => setFormData(d => ({ ...d, impact_legal: e.target.value }))} disabled={isReadOnly} />
                            </Col>
                            <Col span={8}>
                                <Text style={{ display: 'block', marginBottom: 4 }}>Reputation</Text>
                                <TextArea rows={2} value={formData.impact_reputation} onChange={e => setFormData(d => ({ ...d, impact_reputation: e.target.value }))} disabled={isReadOnly} />
                            </Col>
                        </Row>
                    </Card>

                    <RiskMatrix />

                    {!currentAssessment && !isEditing && (
                        <Empty description="No assessments yet. Click 'New Assessment' to start." style={{ marginTop: 32 }} />
                    )}
                </Spin>
            ),
        },
        {
            key: 'connections',
            label: 'Controls & Connections',
            children: (
                <div>
                    <ConnectionBoard
                        title="Assets"
                        sourceLabel="Asset"
                        targetLabel="Risk"
                        relationshipLabel="exposed to"
                        availableItems={assets.map(a => ({ id: a.id, name: a.name, description: a.description }))}
                        linkedItems={linkedAssets.map(a => ({ id: a.id, name: a.name, description: a.description }))}
                        getItemDisplayName={(item: any) => item.name}
                        getItemDescription={(item: any) => item.description}
                        onLink={async (ids) => { for (const id of ids) { await linkAsset(riskId!, id); } await fetchLinkedAssets(riskId!); }}
                        onUnlink={async (ids) => { for (const id of ids) { await unlinkAsset(riskId!, id); } await fetchLinkedAssets(riskId!); }}
                        height={300}
                    />
                    <div style={{ marginTop: 16 }} />
                    <ConnectionBoard
                        title="Controls"
                        sourceLabel="Control"
                        targetLabel="Risk"
                        relationshipLabel="mitigates"
                        availableItems={controls.map(c => ({ id: c.id, name: c.name, description: c.description, code: c.code }))}
                        linkedItems={linkedControls.map(c => ({ id: c.id, name: c.name, description: c.description, code: c.code }))}
                        getItemDisplayName={(item: any) => item.code ? `${item.code} — ${item.name}` : item.name}
                        getItemDescription={(item: any) => item.description}
                        onLink={async (ids) => {
                            for (const id of ids) { await linkControlToRisk(id, riskId!); }
                            await fetchLinkedControls(riskId!);
                        }}
                        onUnlink={async (ids) => {
                            for (const id of ids) { await unlinkControlFromRisk(id, riskId!); }
                            await fetchLinkedControls(riskId!);
                        }}
                        height={300}
                    />
                    <div style={{ marginTop: 16 }} />
                    <ConnectionBoard
                        title="Objectives"
                        sourceLabel="Objective"
                        targetLabel="Risk"
                        relationshipLabel="linked to"
                        availableItems={linkedObjectives.map(o => ({ id: o.id, name: o.title, description: o.subchapter }))}
                        linkedItems={linkedObjectives.map(o => ({ id: o.id, name: o.title, description: o.subchapter }))}
                        getItemDisplayName={(item: any) => item.name}
                        getItemDescription={(item: any) => item.description}
                        onLink={async (ids) => { for (const id of ids) { await linkObjective(riskId!, id); } await fetchLinkedObjectives(riskId!); }}
                        onUnlink={async (ids) => { for (const id of ids) { await unlinkObjective(riskId!, id); } await fetchLinkedObjectives(riskId!); }}
                        height={300}
                    />
                </div>
            ),
        },
        {
            key: 'treatment',
            label: 'Treatment',
            children: (
                <Spin spinning={loading}>
                    {/* Residual Risk Section */}
                    <Row gutter={24} style={{ marginBottom: 24 }}>
                        <Col span={8}>
                            <ScoreGauge
                                label="Residual Risk"
                                score={formData.residual_impact && formData.residual_likelihood ? formData.residual_impact * formData.residual_likelihood : null}
                                impact={formData.residual_impact}
                                likelihood={formData.residual_likelihood}
                            />
                        </Col>
                        <Col span={16}>
                            <ScoreSelector
                                label="Residual Risk (After Treatment)"
                                impactValue={formData.residual_impact || 1}
                                likelihoodValue={formData.residual_likelihood || 1}
                                onImpactChange={v => setFormData(d => ({ ...d, residual_impact: v }))}
                                onLikelihoodChange={v => setFormData(d => ({ ...d, residual_likelihood: v }))}
                            />
                            {currentAssessment && (
                                <Button type="primary" icon={<SaveOutlined />} onClick={async () => {
                                    const data = {
                                        ...formData,
                                        target_impact: formData.target_impact || undefined,
                                        target_likelihood: formData.target_likelihood || undefined,
                                        residual_impact: formData.residual_impact || undefined,
                                        residual_likelihood: formData.residual_likelihood || undefined,
                                    };
                                    const success = await updateAssessment(riskId!, currentAssessment.id, data);
                                    if (success) {
                                        api.success({ message: 'Residual score saved' });
                                        fetchAssessments(riskId!);
                                    } else {
                                        api.error({ message: 'Failed to save residual score' });
                                    }
                                }} style={{ marginTop: 8 }}>
                                    Save Residual Score
                                </Button>
                            )}
                        </Col>
                    </Row>

                    {/* Treatment Actions */}
                    <Card
                        size="small"
                        title="Treatment Actions"
                        extra={
                            <Button
                                type="primary"
                                size="small"
                                icon={<PlusOutlined />}
                                onClick={() => {
                                    setEditingAction(null);
                                    setActionForm({ description: '', due_date: null, owner: '', status: 'Open', completion_notes: '' });
                                    setActionModalOpen(true);
                                }}
                                disabled={!currentAssessment}
                            >
                                Add Action
                            </Button>
                        }
                    >
                        <Table
                            columns={actionColumns}
                            dataSource={currentAssessment?.treatment_actions || []}
                            rowKey="id"
                            size="small"
                            pagination={false}
                            locale={{ emptyText: <Empty description="No treatment actions" /> }}
                        />
                    </Card>

                    {currentAssessment && (
                        <div style={{ marginTop: 16, textAlign: 'right' }}>
                            <Button
                                type="primary"
                                icon={<CheckCircleOutlined />}
                                onClick={async () => {
                                    const data = {
                                        ...formData,
                                        target_impact: formData.target_impact || undefined,
                                        target_likelihood: formData.target_likelihood || undefined,
                                        residual_impact: formData.residual_impact || undefined,
                                        residual_likelihood: formData.residual_likelihood || undefined,
                                        status: 'Completed',
                                    };
                                    const success = await updateAssessment(riskId!, currentAssessment.id, data);
                                    if (success) {
                                        api.success({ message: 'Assessment marked as completed' });
                                        fetchAssessments(riskId!);
                                    } else {
                                        api.error({ message: 'Failed to complete assessment' });
                                    }
                                }}
                            >
                                Complete Assessment
                            </Button>
                        </div>
                    )}
                </Spin>
            ),
        },
    ];

    return (
        <div>
            {contextHolder}
            <div className={'page-parent'}>
                <Sidebar
                    selectedKeys={menuHighlighting.selectedKeys}
                    openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange}
                />
                <div className={'page-content'}>
                    <div className="page-header">
                        <div className="page-header-left">
                            <Button
                                type="text"
                                icon={<ArrowLeftOutlined />}
                                onClick={() => setLocation('/risk_assessment')}
                                style={{ marginRight: 8 }}
                            />
                            <ScheduleOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title={`Risk Assessment — ${currentAssessment?.risk_code || currentRisk?.risk_code || ''}`}
                                infoContent={RiskAssessmentInfo}
                                className="page-title"
                            />
                        </div>
                    </div>
                    <Tabs
                        activeKey={activeTab}
                        onChange={setActiveTab}
                        items={tabItems}
                    />
                </div>
            </div>

            {/* Treatment Action Modal */}
            <Modal
                title={editingAction ? 'Edit Treatment Action' : 'New Treatment Action'}
                open={actionModalOpen}
                onCancel={() => { setActionModalOpen(false); setEditingAction(null); }}
                onOk={handleSaveAction}
                okText="Save"
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div>
                        <Text style={{ display: 'block', marginBottom: 4 }}>Description *</Text>
                        <TextArea
                            rows={3}
                            value={actionForm.description}
                            onChange={e => setActionForm(f => ({ ...f, description: e.target.value }))}
                        />
                    </div>
                    <div>
                        <Text style={{ display: 'block', marginBottom: 4 }}>Due Date</Text>
                        <DatePicker
                            style={{ width: '100%' }}
                            value={actionForm.due_date ? dayjs(actionForm.due_date) : null}
                            onChange={(date) => setActionForm(f => ({ ...f, due_date: date?.toISOString() || null }))}
                        />
                    </div>
                    <div>
                        <Text style={{ display: 'block', marginBottom: 4 }}>Owner</Text>
                        <Input
                            value={actionForm.owner}
                            onChange={e => setActionForm(f => ({ ...f, owner: e.target.value }))}
                        />
                    </div>
                    <div>
                        <Text style={{ display: 'block', marginBottom: 4 }}>Status</Text>
                        <Select
                            value={actionForm.status}
                            onChange={v => setActionForm(f => ({ ...f, status: v }))}
                            style={{ width: '100%' }}
                        >
                            <Select.Option value="Open">Open</Select.Option>
                            <Select.Option value="In Progress">In Progress</Select.Option>
                            <Select.Option value="Completed">Completed</Select.Option>
                            <Select.Option value="Cancelled">Cancelled</Select.Option>
                        </Select>
                    </div>
                    {editingAction && (
                        <div>
                            <Text style={{ display: 'block', marginBottom: 4 }}>Completion Notes</Text>
                            <TextArea
                                rows={2}
                                value={actionForm.completion_notes}
                                onChange={e => setActionForm(f => ({ ...f, completion_notes: e.target.value }))}
                            />
                        </div>
                    )}
                </div>
            </Modal>

            {/* Delete Assessment Confirmation Modal */}
            <Modal
                title="Delete Assessment"
                open={deleteConfirmOpen}
                onCancel={() => setDeleteConfirmOpen(false)}
                onOk={handleConfirmDelete}
                okText="Delete"
                okButtonProps={{ danger: true }}
            >
                <p>Are you sure you want to delete Assessment #{currentAssessment?.assessment_number}? This action cannot be undone.</p>
            </Modal>
        </div>
    );
};

export default RiskAssessmentPage;
