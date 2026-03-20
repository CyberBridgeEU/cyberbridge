// src/components/onboarding/FrameworkSelectionStep.tsx
import React, { useEffect, useState } from 'react';
import { Card, Checkbox, Spin, Empty, notification, Row, Col, Typography, Alert } from 'antd';
import { CheckCircleFilled } from '@ant-design/icons';
import useFrameworksStore, { FrameworkTemplate } from '../../store/useFrameworksStore';
import useOnboardingStore from '../../store/useOnboardingStore';

// Import framework logos
import craLogo from '../../assets/cra_logo.svg';
import iso27001Logo from '../../assets/iso27001_logo.png';
import nis2Logo from '../../assets/nis2_logo.png';
import nistCsfLogo from '../../assets/nist_csf_logo.webp';
import pciDssLogo from '../../assets/pci_dss_logo.png';
import soc2Logo from '../../assets/soc_2_logo.png';
import hipaaLogo from '../../assets/hippa_logo.png';
import ccpaLogo from '../../assets/ccpa_logo.webp';
import gdprLogo from '../../assets/gdpr_logo.jpg';
import cmmc20Logo from '../../assets/cmmc_2_0_logo.jpeg';
import doraLogo from '../../assets/dora_logo.webp';
import aescsfLogo from '../../assets/australia_energy_aescsf_logo.svg';
import ftcSafeguardsLogo from '../../assets/ftc_safeguards_logo.png';
import cobit2019Logo from '../../assets/cobit_2019_logo.webp';

const { Title, Text } = Typography;

// Helper function to get framework logo
const getFrameworkLogo = (frameworkName: string): string | null => {
    const name = frameworkName.toLowerCase();
    if (name.includes('cra') || name.includes('cyber resilience act')) return craLogo;
    if (name.includes('iso27001') || name.includes('iso 27001')) return iso27001Logo;
    if (name.includes('nis2') || name.includes('nis 2')) return nis2Logo;
    if (name.includes('aescsf') || name.includes('australia energy')) return aescsfLogo;
    if (name.includes('nist') || name.includes('csf')) return nistCsfLogo;
    if (name.includes('pci') || name.includes('dss')) return pciDssLogo;
    if (name.includes('soc') || name.includes('soc 2') || name.includes('soc2')) return soc2Logo;
    if (name.includes('hipaa') || name.includes('hippa') || name.includes('privacy rule')) return hipaaLogo;
    if (name.includes('ccpa') || name.includes('california consumer privacy act')) return ccpaLogo;
    if (name.includes('gdpr') || name.includes('general data protection regulation')) return gdprLogo;
    if (name.includes('cmmc') || name.includes('cybersecurity maturity model certification')) return cmmc20Logo;
    if (name.includes('dora') || name.includes('digital operational resilience act')) return doraLogo;
    if (name.includes('ftc') || name.includes('safeguards') || name.includes('federal trade commission')) return ftcSafeguardsLogo;
    if (name.includes('cobit')) return cobit2019Logo;
    return null;
};

const FrameworkSelectionStep: React.FC = () => {
    const [api, contextHolder] = notification.useNotification();
    const [seeding, setSeeding] = useState<string | null>(null);

    const { frameworkTemplates, loading, fetchFrameworkTemplates, seedFrameworkTemplate } = useFrameworksStore();
    const { selectedFrameworks, setSelectedFrameworks } = useOnboardingStore();

    useEffect(() => {
        fetchFrameworkTemplates();
    }, [fetchFrameworkTemplates]);

    const handleFrameworkToggle = async (templateId: string) => {
        const isSelected = selectedFrameworks.includes(templateId);

        if (!isSelected) {
            // Seed the framework
            setSeeding(templateId);
            const result = await seedFrameworkTemplate(templateId);

            if (result.success) {
                setSelectedFrameworks([...selectedFrameworks, templateId]);
                api.success({
                    message: 'Framework Added',
                    description: 'The framework has been added to your organization.'
                });
            } else {
                api.error({
                    message: 'Error',
                    description: result.error || 'Failed to add framework. It may already exist.'
                });
            }
            setSeeding(null);
        } else {
            // Just deselect (don't delete the framework)
            setSelectedFrameworks(selectedFrameworks.filter(id => id !== templateId));
        }
    };

    if (loading && frameworkTemplates.length === 0) {
        return (
            <div style={{ textAlign: 'center', padding: '60px 0' }}>
                <Spin size="large" />
                <p style={{ marginTop: '16px', color: '#8c8c8c' }}>Loading available frameworks...</p>
            </div>
        );
    }

    return (
        <div>
            {contextHolder}
            <div style={{ marginBottom: '24px' }}>
                <Title level={4} style={{ marginBottom: '8px', color: '#1a365d' }}>
                    Select Compliance Frameworks
                </Title>
                <Text type="secondary">
                    Choose the compliance frameworks relevant to your organization. Selected frameworks will be added to your workspace.
                </Text>
            </div>

            {selectedFrameworks.length > 0 && (
                <Alert
                    message={`${selectedFrameworks.length} framework${selectedFrameworks.length > 1 ? 's' : ''} selected`}
                    type="success"
                    showIcon
                    style={{ marginBottom: '16px' }}
                />
            )}

            {frameworkTemplates.length === 0 ? (
                <Empty
                    description="No framework templates available"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
            ) : (
                <div style={{ maxHeight: '400px', overflowY: 'auto', paddingRight: '4px' }}>
                <Row gutter={[16, 16]}>
                    {frameworkTemplates.map((template: FrameworkTemplate) => {
                        const isSelected = selectedFrameworks.includes(template.id);
                        const isSeeding = seeding === template.id;
                        const logo = getFrameworkLogo(template.name);

                        return (
                            <Col xs={24} sm={12} key={template.id}>
                                <Card
                                    hoverable
                                    onClick={() => !isSeeding && handleFrameworkToggle(template.id)}
                                    style={{
                                        cursor: isSeeding ? 'wait' : 'pointer',
                                        border: isSelected ? '2px solid #0f386a' : '1px solid #e8e8e8',
                                        backgroundColor: isSelected ? '#f0f7ff' : '#ffffff',
                                        transition: 'all 0.3s ease',
                                        height: '100%'
                                    }}
                                    bodyStyle={{
                                        padding: '16px',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        height: '100%'
                                    }}
                                >
                                    <div style={{
                                        display: 'flex',
                                        alignItems: 'flex-start',
                                        gap: '12px'
                                    }}>
                                        {logo ? (
                                            <img
                                                src={logo}
                                                alt={`${template.name} logo`}
                                                style={{
                                                    width: '48px',
                                                    height: '48px',
                                                    objectFit: 'contain',
                                                    flexShrink: 0
                                                }}
                                            />
                                        ) : (
                                            <div style={{
                                                width: '48px',
                                                height: '48px',
                                                backgroundColor: '#0f386a',
                                                borderRadius: '8px',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                color: 'white',
                                                fontWeight: 'bold',
                                                fontSize: '18px',
                                                flexShrink: 0
                                            }}>
                                                {template.name.charAt(0)}
                                            </div>
                                        )}
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <div style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'space-between',
                                                marginBottom: '4px'
                                            }}>
                                                <h4 style={{
                                                    margin: 0,
                                                    fontSize: '14px',
                                                    fontWeight: 600,
                                                    color: '#262626',
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    whiteSpace: 'nowrap'
                                                }}>
                                                    {template.name}
                                                </h4>
                                                {isSeeding ? (
                                                    <Spin size="small" />
                                                ) : isSelected ? (
                                                    <CheckCircleFilled style={{ color: '#0f386a', fontSize: '18px' }} />
                                                ) : (
                                                    <Checkbox
                                                        checked={false}
                                                        onClick={(e) => e.stopPropagation()}
                                                    />
                                                )}
                                            </div>
                                            <Text
                                                type="secondary"
                                                style={{
                                                    fontSize: '12px',
                                                    display: '-webkit-box',
                                                    WebkitLineClamp: 2,
                                                    WebkitBoxOrient: 'vertical',
                                                    overflow: 'hidden'
                                                }}
                                            >
                                                {template.description || 'Compliance framework template'}
                                            </Text>
                                        </div>
                                    </div>
                                </Card>
                            </Col>
                        );
                    })}
                </Row>
                </div>
            )}

            <div style={{ marginTop: '16px', textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                    You can add more frameworks later from the Framework Management page.
                </Text>
            </div>
        </div>
    );
};

export default FrameworkSelectionStep;
