// src/components/user-onboarding/UserOnboardingWizard.tsx
import React from 'react';
import { Modal, Steps, Button, Space, notification } from 'antd';
import {
    SmileOutlined,
    CompassOutlined,
    AppstoreOutlined,
    CheckCircleOutlined
} from '@ant-design/icons';
import useUserOnboardingStore from '../../store/useUserOnboardingStore';
import WelcomeStep from './WelcomeStep';
import ExploreFeaturesStep from './ExploreFeaturesStep';
import ViewFrameworksStep from './ViewFrameworksStep';
import UserOnboardingComplete from './UserOnboardingComplete';

const UserOnboardingWizard: React.FC = () => {
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
    } = useUserOnboardingStore();

    const steps = [
        {
            title: 'Welcome',
            icon: <SmileOutlined />,
            content: <WelcomeStep />
        },
        {
            title: 'Features',
            icon: <CompassOutlined />,
            content: <ExploreFeaturesStep />
        },
        {
            title: 'Frameworks',
            icon: <AppstoreOutlined />,
            content: <ViewFrameworksStep />
        },
        {
            title: 'Ready',
            icon: <CheckCircleOutlined />,
            content: <UserOnboardingComplete />
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
                description: "You're all set! Start exploring CyberBridge."
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
                                Getting Started with CyberBridge
                            </h3>
                            <p style={{ margin: 0, fontSize: '13px', color: '#8c8c8c' }}>
                                Let's help you get familiar with the platform
                            </p>
                        </div>
                    </div>
                }
            >
                <Steps
                    current={currentStep}
                    style={{ marginBottom: '32px' }}
                    items={steps.map(step => ({
                        title: step.title,
                        icon: step.icon
                    }))}
                />

                <div style={{
                    minHeight: '350px',
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

export default UserOnboardingWizard;
