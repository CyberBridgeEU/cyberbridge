// src/components/superadmin-onboarding/SystemConfigStep.tsx
import React from 'react';
import { Typography, Alert, Badge } from 'antd';
import {
    SettingOutlined,
    RobotOutlined,
    CloudServerOutlined,
    SecurityScanOutlined,
    ApiOutlined,
    CheckCircleFilled
} from '@ant-design/icons';
import useSuperAdminOnboardingStore from '../../store/useSuperAdminOnboardingStore';

const { Title, Paragraph } = Typography;

const SystemConfigStep: React.FC = () => {
    const { viewedSections, addViewedSection } = useSuperAdminOnboardingStore();

    const configAreas = [
        {
            id: 'ai-providers',
            icon: <RobotOutlined style={{ fontSize: '26px', color: '#8b5cf6' }} />,
            title: 'AI Provider Configuration',
            description: 'Configure AI providers like llama.cpp, OpenAI, Anthropic, or Google AI for intelligent analysis and remediation suggestions.',
            path: '/settings',
            color: '#8b5cf6',
            bgColor: '#f5f3ff'
        },
        {
            id: 'security-scanners',
            icon: <SecurityScanOutlined style={{ fontSize: '26px', color: '#dc2626' }} />,
            title: 'Security Scanners',
            description: 'Manage integrated security scanning tools for web app, network, code analysis, and dependency vulnerability assessment.',
            path: '/security_scanners',
            color: '#dc2626',
            bgColor: '#fef2f2'
        },
        {
            id: 'integrations',
            icon: <ApiOutlined style={{ fontSize: '26px', color: '#0f386a' }} />,
            title: 'External Integrations',
            description: 'Configure integrations with external services, APIs, and third-party compliance tools.',
            path: '/settings',
            color: '#0f386a',
            bgColor: '#EBF4FC'
        },
        {
            id: 'backup-settings',
            icon: <CloudServerOutlined style={{ fontSize: '26px', color: '#10b981' }} />,
            title: 'Backup & Recovery',
            description: 'Set up automated backups, configure retention policies, and manage system recovery options.',
            path: '/backups',
            color: '#10b981',
            bgColor: '#f0fdfa'
        }
    ];

    const handleConfigClick = (configId: string) => {
        addViewedSection(configId);
    };

    return (
        <div style={{ padding: '0 16px' }}>
            <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                <Title level={4} style={{ margin: 0, color: '#1a365d' }}>
                    System Configuration
                </Title>
                <Paragraph style={{ color: '#8c8c8c', fontSize: '14px', marginTop: '8px' }}>
                    Configure global platform settings and integrations.
                </Paragraph>
            </div>

            <Alert
                message={`${viewedSections.filter(s => configAreas.some(c => c.id === s)).length} of ${configAreas.length} configuration areas reviewed`}
                type={viewedSections.filter(s => configAreas.some(c => c.id === s)).length === configAreas.length ? 'success' : 'info'}
                showIcon
                icon={<SettingOutlined />}
                style={{ marginBottom: '20px' }}
            />

            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '12px'
            }}>
                {configAreas.map((config) => {
                    const isViewed = viewedSections.includes(config.id);

                    return (
                        <div
                            key={config.id}
                            onClick={() => handleConfigClick(config.id)}
                            style={{
                                padding: '16px',
                                borderRadius: '10px',
                                border: `2px solid ${isViewed ? config.color : '#f0f0f0'}`,
                                background: isViewed ? config.bgColor : 'white',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                position: 'relative'
                            }}
                        >
                            {isViewed && (
                                <CheckCircleFilled
                                    style={{
                                        position: 'absolute',
                                        top: '8px',
                                        right: '8px',
                                        color: config.color,
                                        fontSize: '16px'
                                    }}
                                />
                            )}
                            <div style={{
                                width: '48px',
                                height: '48px',
                                borderRadius: '10px',
                                background: isViewed ? 'white' : config.bgColor,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                marginBottom: '12px'
                            }}>
                                {config.icon}
                            </div>
                            <div style={{
                                fontWeight: 600,
                                fontSize: '14px',
                                color: '#1a365d',
                                marginBottom: '6px'
                            }}>
                                {config.title}
                            </div>
                            <div style={{
                                fontSize: '12px',
                                color: '#64748b',
                                lineHeight: '1.4'
                            }}>
                                {config.description}
                            </div>
                        </div>
                    );
                })}
            </div>

            <div style={{
                marginTop: '20px',
                padding: '12px 16px',
                borderRadius: '8px',
                background: '#fef2f2',
                border: '1px solid #fecaca'
            }}>
                <Paragraph style={{ margin: 0, color: '#991b1b', fontSize: '12px' }}>
                    <strong>Note:</strong> System configuration changes affect all organizations. You can access these settings anytime from the Settings page.
                </Paragraph>
            </div>
        </div>
    );
};

export default SystemConfigStep;
