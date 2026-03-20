// src/components/onboarding/OnboardingWizard.tsx
import React from 'react';
import { Modal, Steps, Button, Space, notification } from 'antd';
import {
    AppstoreOutlined,
    TeamOutlined,
    RobotOutlined,
    CheckCircleOutlined
} from '@ant-design/icons';
import useOnboardingStore from '../../store/useOnboardingStore';
import FrameworkSelectionStep from './FrameworkSelectionStep';
import UserInvitationStep from './UserInvitationStep';
import AIProviderConfigStep from './AIProviderConfigStep';
import OnboardingComplete from './OnboardingComplete';

const OnboardingWizard: React.FC = () => {
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
    } = useOnboardingStore();

    const steps = [
        {
            title: 'Frameworks',
            icon: <AppstoreOutlined />,
            content: <FrameworkSelectionStep />
        },
        {
            title: 'Team',
            icon: <TeamOutlined />,
            content: <UserInvitationStep />
        },
        {
            title: 'AI Setup',
            icon: <RobotOutlined />,
            content: <AIProviderConfigStep />
        },
        {
            title: 'Complete',
            icon: <CheckCircleOutlined />,
            content: <OnboardingComplete />
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
                description: 'Failed to skip onboarding. Please try again.'
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
                description: 'Welcome to CyberBridge! Your organization is ready to go.'
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
                width={800}
                footer={null}
                centered
                destroyOnClose
                maskClosable={false}
                styles={{
                    body: { maxHeight: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column', overflow: 'hidden' },
                }}
                style={{ maxHeight: 'calc(100vh - 80px)', top: 40 }}
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
                            background: 'linear-gradient(135deg, #0f386a 0%, #1a365d 100%)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                        }}>
                            <span style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>C</span>
                        </div>
                        <div>
                            <h3 style={{ margin: 0, fontSize: '18px', color: '#1a365d' }}>
                                Welcome to CyberBridge
                            </h3>
                            <p style={{ margin: 0, fontSize: '13px', color: '#8c8c8c' }}>
                                Let's set up your organization
                            </p>
                        </div>
                    </div>
                }
            >
                <Steps
                    current={currentStep}
                    style={{ marginBottom: '16px', flexShrink: 0 }}
                    items={steps.map(step => ({
                        title: step.title,
                        icon: step.icon
                    }))}
                />

                <div style={{
                    flex: 1,
                    overflowY: 'auto',
                    padding: '16px 0',
                    minHeight: 0,
                }}>
                    {steps[currentStep].content}
                </div>

                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    borderTop: '1px solid #f0f0f0',
                    paddingTop: '16px',
                    flexShrink: 0,
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
                                    backgroundColor: '#0f386a',
                                    borderColor: '#0f386a'
                                }}
                            >
                                Start Using CyberBridge
                            </Button>
                        ) : (
                            <Button
                                type="primary"
                                onClick={handleNext}
                                disabled={loading}
                                style={{
                                    backgroundColor: '#0f386a',
                                    borderColor: '#0f386a'
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

export default OnboardingWizard;
