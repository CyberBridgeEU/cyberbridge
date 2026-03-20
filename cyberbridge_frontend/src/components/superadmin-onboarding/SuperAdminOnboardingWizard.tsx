// src/components/superadmin-onboarding/SuperAdminOnboardingWizard.tsx
import React from 'react';
import { Modal, Steps, Button, Space, notification } from 'antd';
import {
    CrownOutlined,
    SettingOutlined,
    BankOutlined,
    TeamOutlined,
    CheckCircleOutlined
} from '@ant-design/icons';
import useSuperAdminOnboardingStore from '../../store/useSuperAdminOnboardingStore';
import SuperAdminWelcomeStep from './SuperAdminWelcomeStep';
import SystemConfigStep from './SystemConfigStep';
import OrganizationOverviewStep from './OrganizationOverviewStep';
import UserManagementStep from './UserManagementStep';
import SuperAdminOnboardingComplete from './SuperAdminOnboardingComplete';

const SuperAdminOnboardingWizard: React.FC = () => {
    const [api, contextHolder] = notification.useNotification();
    const {
        isWizardOpen,
        currentStep,
        loading,
        closeWizard,
        nextStep,
        prevStep,
        skipOnboarding,
        completeOnboarding
    } = useSuperAdminOnboardingStore();

    const steps = [
        {
            title: 'Welcome',
            icon: <CrownOutlined />,
            content: <SuperAdminWelcomeStep />
        },
        {
            title: 'System',
            icon: <SettingOutlined />,
            content: <SystemConfigStep />
        },
        {
            title: 'Organizations',
            icon: <BankOutlined />,
            content: <OrganizationOverviewStep />
        },
        {
            title: 'Users',
            icon: <TeamOutlined />,
            content: <UserManagementStep />
        },
        {
            title: 'Ready',
            icon: <CheckCircleOutlined />,
            content: <SuperAdminOnboardingComplete />
        }
    ];

    const handleSkip = async () => {
        const success = await skipOnboarding();
        if (success) {
            api.info({
                message: 'Setup Skipped',
                description: 'You can run the setup wizard again from your dashboard.'
            });
        } else {
            api.error({
                message: 'Error',
                description: 'Failed to skip setup. Please try again.'
            });
        }
    };

    const handleNext = () => {
        if (currentStep < steps.length - 1) {
            nextStep();
        }
    };

    const handlePrev = () => {
        if (currentStep > 0) {
            prevStep();
        }
    };

    const handleFinish = async () => {
        const success = await completeOnboarding();
        if (success) {
            api.success({
                message: 'Setup Complete',
                description: "You're ready to manage the CyberBridge platform."
            });
        } else {
            api.error({
                message: 'Error',
                description: 'Failed to complete setup. Please try again.'
            });
        }
    };

    const isLastStep = currentStep === steps.length - 1;

    return (
        <>
            {contextHolder}
            <Modal
                open={isWizardOpen}
                onCancel={handleSkip}
                width={850}
                footer={null}
                centered
                destroyOnClose
                maskClosable={false}
                title={
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        borderBottom: '1px solid #f0f0f0',
                        paddingBottom: '16px',
                        marginBottom: '8px'
                    }}>
                        <div style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '10px',
                            background: 'linear-gradient(135deg, #dc2626 0%, #991b1b 100%)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}>
                            <CrownOutlined style={{ color: 'white', fontSize: '20px' }} />
                        </div>
                        <div>
                            <h3 style={{ margin: 0, fontSize: '18px', color: '#1a365d' }}>
                                Super Admin Setup
                            </h3>
                            <p style={{ margin: 0, fontSize: '13px', color: '#8c8c8c' }}>
                                Configure and manage your CyberBridge platform
                            </p>
                        </div>
                    </div>
                }
            >
                <Steps
                    current={currentStep}
                    style={{ marginBottom: '32px' }}
                    size="small"
                    items={steps.map(step => ({
                        title: step.title,
                        icon: step.icon
                    }))}
                />

                <div style={{
                    minHeight: '380px',
                    padding: '16px 0',
                    marginBottom: '24px'
                }}>
                    {steps[currentStep].content}
                </div>

                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    borderTop: '1px solid #f0f0f0',
                    paddingTop: '16px'
                }}>
                    <Button onClick={handleSkip} disabled={loading}>
                        Skip Setup
                    </Button>
                    <Space>
                        {currentStep > 0 && (
                            <Button onClick={handlePrev} disabled={loading}>
                                Previous
                            </Button>
                        )}
                        {isLastStep ? (
                            <Button
                                type="primary"
                                onClick={handleFinish}
                                loading={loading}
                                style={{
                                    backgroundColor: '#dc2626',
                                    borderColor: '#dc2626'
                                }}
                            >
                                Start Managing CyberBridge
                            </Button>
                        ) : (
                            <Button
                                type="primary"
                                onClick={handleNext}
                                disabled={loading}
                                style={{
                                    backgroundColor: '#dc2626',
                                    borderColor: '#dc2626'
                                }}
                            >
                                Next
                            </Button>
                        )}
                    </Space>
                </div>
            </Modal>
        </>
    );
};

export default SuperAdminOnboardingWizard;
