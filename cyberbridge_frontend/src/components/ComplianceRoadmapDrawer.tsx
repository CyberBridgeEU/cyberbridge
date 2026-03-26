import React, { useEffect } from 'react';
import { Drawer, Spin, Alert, Tag, Typography, Steps, Collapse, Divider, Button } from 'antd';
import {
    CompassOutlined,
    ThunderboltOutlined,
    WarningOutlined,
    ClockCircleOutlined,
    LinkOutlined,
    LoadingOutlined,
    ToolOutlined,
    FileTextOutlined,
    SafetyCertificateOutlined,
    TeamOutlined,
    ReadOutlined,
    CodeOutlined,
} from '@ant-design/icons';
import useRoadmapStore from '../store/useRoadmapStore';
import type { RoadmapActionStep } from '../store/useRoadmapStore';

const { Text, Paragraph } = Typography;

interface ComplianceRoadmapDrawerProps {
    open: boolean;
    onClose: () => void;
    objectiveId: string | null;
    objectiveTitle: string;
    frameworkId: string;
    currentStatus: string | null;
}

const priorityColors: Record<string, string> = {
    critical: 'red',
    high: 'volcano',
    medium: 'orange',
    low: 'blue',
};

const categoryIcons: Record<string, React.ReactNode> = {
    technical: <CodeOutlined />,
    policy: <FileTextOutlined />,
    evidence: <SafetyCertificateOutlined />,
    process: <ToolOutlined />,
    training: <ReadOutlined />,
};

const categoryColors: Record<string, string> = {
    technical: 'geekblue',
    policy: 'purple',
    evidence: 'cyan',
    process: 'gold',
    training: 'magenta',
};

const ComplianceRoadmapDrawer: React.FC<ComplianceRoadmapDrawerProps> = ({
    open,
    onClose,
    objectiveId,
    objectiveTitle,
    frameworkId,
    currentStatus,
}) => {
    const { roadmap, loading, error, generateRoadmap, clearRoadmap } = useRoadmapStore();

    useEffect(() => {
        if (open && objectiveId && frameworkId) {
            generateRoadmap(objectiveId, frameworkId);
        }
        return () => {
            if (!open) clearRoadmap();
        };
    }, [open, objectiveId, frameworkId]);

    const handleClose = () => {
        clearRoadmap();
        onClose();
    };

    const renderStepContent = (step: RoadmapActionStep) => (
        <div style={{ padding: '4px 0 16px 0' }}>
            <Paragraph style={{ margin: '0 0 8px 0', fontSize: '14px', lineHeight: 1.6 }}>
                {step.description}
            </Paragraph>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: 8 }}>
                <Tag color={priorityColors[step.priority] || 'default'}>
                    {step.priority} priority
                </Tag>
                <Tag icon={<ClockCircleOutlined />} color="default">
                    {step.estimated_effort}
                </Tag>
                <Tag icon={categoryIcons[step.category]} color={categoryColors[step.category] || 'default'}>
                    {step.category}
                </Tag>
            </div>
            {step.platform_action && (
                <div style={{
                    padding: '8px 12px',
                    backgroundColor: '#f0f5ff',
                    borderRadius: '6px',
                    borderLeft: '3px solid #1890ff',
                    fontSize: '13px',
                    marginBottom: 8,
                }}>
                    <ToolOutlined style={{ marginRight: 6, color: '#1890ff' }} />
                    <Text strong style={{ color: '#1890ff' }}>Platform Action: </Text>
                    {step.platform_action}
                </div>
            )}
            {step.references && step.references.length > 0 && (
                <div style={{ fontSize: '13px', color: '#8c8c8c' }}>
                    <LinkOutlined style={{ marginRight: 4 }} />
                    {step.references.join(', ')}
                </div>
            )}
        </div>
    );

    return (
        <Drawer
            title={
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CompassOutlined style={{ color: '#0f386a', fontSize: 18 }} />
                    <span>Compliance Roadmap</span>
                </div>
            }
            placement="right"
            width={600}
            onClose={handleClose}
            open={open}
            destroyOnClose
        >
            {/* Objective header */}
            <div style={{
                padding: '12px 16px',
                backgroundColor: '#fafafa',
                borderRadius: '8px',
                marginBottom: '20px',
                borderLeft: '4px solid #0f386a',
            }}>
                <Text strong style={{ fontSize: '15px', display: 'block', marginBottom: 4 }}>
                    {objectiveTitle}
                </Text>
                <Tag color={currentStatus === 'compliant' ? 'green' : currentStatus === 'partially compliant' ? 'orange' : 'red'}>
                    {currentStatus || 'Not Assessed'}
                </Tag>
                <Tag color="blue" style={{ marginLeft: 4 }}>
                    Target: Compliant
                </Tag>
            </div>

            {/* Loading state */}
            {loading && (
                <div style={{ textAlign: 'center', padding: '80px 20px' }}>
                    <Spin indicator={<LoadingOutlined style={{ fontSize: 36 }} spin />} />
                    <div style={{ marginTop: 20, color: '#8c8c8c', fontSize: '15px' }}>
                        Generating compliance roadmap...
                    </div>
                    <div style={{ marginTop: 8, color: '#bfbfbf', fontSize: '13px' }}>
                        Analyzing objectives, policies, evidence, and security findings
                    </div>
                    <Button
                        danger
                        style={{ marginTop: 20 }}
                        onClick={handleClose}
                    >
                        Cancel
                    </Button>
                </div>
            )}

            {/* Error state */}
            {error && !loading && (
                <Alert
                    message="Roadmap Generation Failed"
                    description={error}
                    type="error"
                    showIcon
                    style={{ marginBottom: '16px' }}
                />
            )}

            {/* Roadmap content */}
            {roadmap && !loading && (
                <div>
                    {/* Gap Summary */}
                    <div style={{
                        padding: '14px 16px',
                        backgroundColor: '#fff7e6',
                        border: '1px solid #ffd591',
                        borderRadius: '8px',
                        marginBottom: '20px',
                    }}>
                        <Text strong style={{ display: 'block', marginBottom: 6, color: '#d46b08' }}>
                            <WarningOutlined style={{ marginRight: 6 }} />
                            Gap Summary
                        </Text>
                        <Paragraph style={{ margin: 0, fontSize: '14px', lineHeight: 1.6 }}>
                            {roadmap.gap_summary}
                        </Paragraph>
                    </div>

                    {/* Quick Wins */}
                    {roadmap.quick_wins && roadmap.quick_wins.length > 0 && (
                        <div style={{ marginBottom: '20px' }}>
                            <Text strong style={{ display: 'block', marginBottom: 8, fontSize: '14px' }}>
                                <ThunderboltOutlined style={{ color: '#52c41a', marginRight: 6 }} />
                                Quick Wins
                            </Text>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                {roadmap.quick_wins.map((win, idx) => (
                                    <Tag key={idx} color="green" style={{ fontSize: '13px', padding: '4px 10px', whiteSpace: 'normal', height: 'auto' }}>
                                        {win}
                                    </Tag>
                                ))}
                            </div>
                        </div>
                    )}

                    <Divider style={{ margin: '16px 0' }} />

                    {/* Action Steps */}
                    <Text strong style={{ display: 'block', marginBottom: 12, fontSize: '15px' }}>
                        Action Steps ({roadmap.action_steps.length})
                    </Text>
                    <Steps
                        direction="vertical"
                        size="small"
                        current={-1}
                        items={roadmap.action_steps.map((step) => ({
                            title: (
                                <Text strong style={{ fontSize: '14px' }}>
                                    {step.title}
                                </Text>
                            ),
                            description: renderStepContent(step),
                            icon: (
                                <div style={{
                                    width: 24,
                                    height: 24,
                                    borderRadius: '50%',
                                    backgroundColor: priorityColors[step.priority] === 'red' ? '#fff1f0' :
                                                     priorityColors[step.priority] === 'volcano' ? '#fff2e8' :
                                                     priorityColors[step.priority] === 'orange' ? '#fffbe6' : '#e6f7ff',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    fontSize: '12px',
                                    fontWeight: 600,
                                    color: priorityColors[step.priority] === 'red' ? '#cf1322' :
                                           priorityColors[step.priority] === 'volcano' ? '#d4380d' :
                                           priorityColors[step.priority] === 'orange' ? '#d48806' : '#096dd9',
                                }}>
                                    {step.step_number}
                                </div>
                            ),
                        }))}
                    />

                    <Divider style={{ margin: '16px 0' }} />

                    {/* Dependencies */}
                    {roadmap.dependencies && roadmap.dependencies.length > 0 && (
                        <Collapse
                            ghost
                            style={{ marginBottom: 12 }}
                            items={[{
                                key: 'deps',
                                label: <Text strong><LinkOutlined style={{ marginRight: 6 }} />Dependencies</Text>,
                                children: (
                                    <ul style={{ paddingLeft: 20, margin: 0 }}>
                                        {roadmap.dependencies.map((dep, idx) => (
                                            <li key={idx} style={{ fontSize: '13px', marginBottom: 4 }}>{dep}</li>
                                        ))}
                                    </ul>
                                )
                            }]}
                        />
                    )}

                    {/* Risk if unaddressed */}
                    {roadmap.risk_if_unaddressed && (
                        <Alert
                            message="Risk if Unaddressed"
                            description={roadmap.risk_if_unaddressed}
                            type="warning"
                            showIcon
                            style={{ marginBottom: '16px' }}
                        />
                    )}

                    {/* Estimated total effort */}
                    <div style={{
                        padding: '12px 16px',
                        backgroundColor: '#f6ffed',
                        border: '1px solid #b7eb8f',
                        borderRadius: '8px',
                        textAlign: 'center',
                    }}>
                        <ClockCircleOutlined style={{ color: '#52c41a', marginRight: 6 }} />
                        <Text strong>Estimated Total Effort: </Text>
                        <Text>{roadmap.estimated_total_effort}</Text>
                    </div>
                </div>
            )}
        </Drawer>
    );
};

export default ComplianceRoadmapDrawer;
