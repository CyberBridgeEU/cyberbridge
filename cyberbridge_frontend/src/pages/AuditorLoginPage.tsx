// src/pages/AuditorLoginPage.tsx
import { useEffect, useState } from 'react';
import { useLocation, useSearch } from 'wouter';
import { notification, Spin, Input, Button, Card, Steps, Alert, Typography, Space, Divider } from 'antd';
import {
    MailOutlined,
    SafetyOutlined,
    CheckCircleOutlined,
    LoadingOutlined,
    LockOutlined,
    QrcodeOutlined
} from '@ant-design/icons';
import useAuditorStore from '../store/useAuditorStore';
import cyberbridgeLogo from '../assets/cyberbridge_logo.svg';

const { Title, Text, Paragraph } = Typography;

type LoginStep = 'verify_token' | 'request_link' | 'mfa_setup' | 'mfa_verify' | 'complete';

export default function AuditorLoginPage() {
    const [, setLocation] = useLocation();
    const searchString = useSearch();
    const searchParams = new URLSearchParams(searchString);
    const token = searchParams.get('token');

    const {
        verifyToken,
        setupMFA,
        verifyMFA,
        login,
        requestMagicLink,
        isLoading,
        error,
        clearError,
        isAuthenticated,
        invitationId,
        email: storedEmail,
        name: storedName
    } = useAuditorStore();

    const [currentStep, setCurrentStep] = useState<LoginStep>(token ? 'verify_token' : 'request_link');
    const [email, setEmail] = useState('');
    const [mfaCode, setMfaCode] = useState('');
    const [accessToken, setAccessToken] = useState(token || '');
    const [engagementName, setEngagementName] = useState<string | null>(null);
    const [mfaSetupData, setMfaSetupData] = useState<{
        secret: string;
        qrCodeBase64: string;
    } | null>(null);
    const [verificationError, setVerificationError] = useState<string | null>(null);

    const [api, contextHolder] = notification.useNotification();

    // Redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated) {
            setLocation('/auditor/review');
        }
    }, [isAuthenticated, setLocation]);

    // Handle token verification on mount
    useEffect(() => {
        if (token && currentStep === 'verify_token') {
            handleTokenVerification(token);
        }
    }, [token]);

    const handleTokenVerification = async (tokenToVerify: string) => {
        setVerificationError(null);
        const result = await verifyToken(tokenToVerify);

        if (result.valid) {
            setAccessToken(tokenToVerify);
            setEngagementName(result.engagementName);

            if (result.mfaSetupRequired) {
                // MFA is enabled but not set up yet
                setCurrentStep('mfa_setup');
                await handleMFASetup(tokenToVerify);
            } else if (result.mfaEnabled) {
                // MFA is enabled and set up, need code
                setCurrentStep('mfa_verify');
            } else {
                // No MFA, proceed to login
                await handleLogin(tokenToVerify);
            }
        } else {
            setVerificationError(result.message);
            setCurrentStep('request_link');
        }
    };

    const handleMFASetup = async (tokenForSetup: string) => {
        try {
            const setupResult = await setupMFA(tokenForSetup);
            setMfaSetupData({
                secret: setupResult.secret,
                qrCodeBase64: setupResult.qrCodeBase64
            });
        } catch (err) {
            api.error({
                message: 'MFA Setup Failed',
                description: error || 'Unable to set up two-factor authentication. Please try again.',
            });
        }
    };

    const handleMFAVerify = async () => {
        if (!invitationId || !mfaCode || mfaCode.length !== 6) {
            api.warning({
                message: 'Invalid Code',
                description: 'Please enter a valid 6-digit code from your authenticator app.',
            });
            return;
        }

        const verified = await verifyMFA(invitationId, mfaCode);
        if (verified) {
            // After MFA verification, proceed to login
            await handleLogin(accessToken, mfaCode);
        } else {
            api.error({
                message: 'Invalid Code',
                description: 'The code you entered is incorrect. Please try again.',
            });
            setMfaCode('');
        }
    };

    const handleLogin = async (tokenForLogin: string, mfaCodeForLogin?: string) => {
        const result = await login(tokenForLogin, mfaCodeForLogin);

        if (result.success) {
            setCurrentStep('complete');
            api.success({
                message: 'Login Successful',
                description: 'Redirecting to the audit review portal...',
            });
            setTimeout(() => {
                setLocation('/auditor/review');
            }, 1500);
        } else if (result.error === 'MFA_SETUP_REQUIRED') {
            setCurrentStep('mfa_setup');
            await handleMFASetup(tokenForLogin);
        } else if (result.error === 'MFA_CODE_REQUIRED') {
            setCurrentStep('mfa_verify');
        } else {
            api.error({
                message: 'Login Failed',
                description: result.error || 'Unable to complete login. Please try again.',
            });
        }
    };

    const handleRequestMagicLink = async () => {
        if (!email || !email.includes('@')) {
            api.warning({
                message: 'Invalid Email',
                description: 'Please enter a valid email address.',
            });
            return;
        }

        const result = await requestMagicLink(email);
        if (result.success) {
            api.success({
                message: 'Login Link Sent',
                description: result.message,
                duration: 8,
            });
        } else {
            api.error({
                message: 'Request Failed',
                description: result.message,
            });
        }
    };

    const getStepStatus = (step: LoginStep) => {
        const stepOrder: LoginStep[] = ['verify_token', 'request_link', 'mfa_setup', 'mfa_verify', 'complete'];
        const currentIndex = stepOrder.indexOf(currentStep);
        const stepIndex = stepOrder.indexOf(step);

        if (step === currentStep) return 'process';
        if (stepIndex < currentIndex) return 'finish';
        return 'wait';
    };

    const renderContent = () => {
        switch (currentStep) {
            case 'verify_token':
                return (
                    <div style={{ textAlign: 'center', padding: '40px 0' }}>
                        <Spin indicator={<LoadingOutlined style={{ fontSize: 48, color: '#0f386a' }} spin />} />
                        <Title level={4} style={{ marginTop: 24, color: '#1a365d' }}>
                            Verifying Access Link
                        </Title>
                        <Text type="secondary">
                            Please wait while we verify your access credentials...
                        </Text>
                    </div>
                );

            case 'request_link':
                return (
                    <div style={{ padding: '20px 0' }}>
                        {verificationError && (
                            <Alert
                                message="Access Link Invalid"
                                description={verificationError}
                                type="error"
                                showIcon
                                style={{ marginBottom: 24 }}
                            />
                        )}
                        <Title level={4} style={{ textAlign: 'center', color: '#1a365d', marginBottom: 8 }}>
                            Auditor Portal Access
                        </Title>
                        <Paragraph style={{ textAlign: 'center', color: '#6b7280', marginBottom: 24 }}>
                            Enter your email address to receive a secure login link
                        </Paragraph>
                        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                            <Input
                                size="large"
                                prefix={<MailOutlined style={{ color: '#9ca3af' }} />}
                                placeholder="your.email@company.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                onPressEnter={handleRequestMagicLink}
                            />
                            <Button
                                type="primary"
                                size="large"
                                block
                                loading={isLoading}
                                onClick={handleRequestMagicLink}
                                style={{
                                    background: 'linear-gradient(135deg, #0f386a, #0a2d55)',
                                    borderColor: '#0f386a',
                                    height: 48
                                }}
                            >
                                Send Login Link
                            </Button>
                        </Space>
                        <Divider />
                        <Paragraph style={{ textAlign: 'center', color: '#9ca3af', fontSize: 13 }}>
                            If you have an active audit engagement invitation, a secure login link will be sent to your email.
                        </Paragraph>
                    </div>
                );

            case 'mfa_setup':
                return (
                    <div style={{ padding: '20px 0' }}>
                        <Title level={4} style={{ textAlign: 'center', color: '#1a365d', marginBottom: 8 }}>
                            Set Up Two-Factor Authentication
                        </Title>
                        <Paragraph style={{ textAlign: 'center', color: '#6b7280', marginBottom: 24 }}>
                            Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.)
                        </Paragraph>

                        {engagementName && (
                            <Alert
                                message={`Engagement: ${engagementName}`}
                                type="info"
                                showIcon
                                style={{ marginBottom: 24 }}
                            />
                        )}

                        {mfaSetupData ? (
                            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{
                                        display: 'inline-block',
                                        padding: 16,
                                        background: 'white',
                                        borderRadius: 8,
                                        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                                    }}>
                                        <img
                                            src={`data:image/png;base64,${mfaSetupData.qrCodeBase64}`}
                                            alt="MFA QR Code"
                                            style={{ width: 200, height: 200 }}
                                        />
                                    </div>
                                </div>

                                <Alert
                                    message="Manual Entry Code"
                                    description={
                                        <Text code copyable style={{ fontSize: 12 }}>
                                            {mfaSetupData.secret}
                                        </Text>
                                    }
                                    type="info"
                                    showIcon
                                    icon={<QrcodeOutlined />}
                                />

                                <Text style={{ display: 'block', textAlign: 'center' }}>
                                    After scanning, enter the 6-digit code from your app:
                                </Text>

                                <Input
                                    size="large"
                                    prefix={<LockOutlined style={{ color: '#9ca3af' }} />}
                                    placeholder="000000"
                                    value={mfaCode}
                                    onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                    maxLength={6}
                                    style={{ textAlign: 'center', letterSpacing: 8, fontSize: 24 }}
                                    onPressEnter={handleMFAVerify}
                                />

                                <Button
                                    type="primary"
                                    size="large"
                                    block
                                    loading={isLoading}
                                    onClick={handleMFAVerify}
                                    disabled={mfaCode.length !== 6}
                                    style={{
                                        background: 'linear-gradient(135deg, #0f386a, #0a2d55)',
                                        borderColor: '#0f386a',
                                        height: 48
                                    }}
                                >
                                    Verify & Continue
                                </Button>
                            </Space>
                        ) : (
                            <div style={{ textAlign: 'center', padding: '40px 0' }}>
                                <Spin indicator={<LoadingOutlined style={{ fontSize: 32, color: '#0f386a' }} spin />} />
                                <Text style={{ display: 'block', marginTop: 16 }}>Loading MFA setup...</Text>
                            </div>
                        )}
                    </div>
                );

            case 'mfa_verify':
                return (
                    <div style={{ padding: '20px 0' }}>
                        <Title level={4} style={{ textAlign: 'center', color: '#1a365d', marginBottom: 8 }}>
                            Two-Factor Authentication
                        </Title>
                        <Paragraph style={{ textAlign: 'center', color: '#6b7280', marginBottom: 24 }}>
                            Enter the 6-digit code from your authenticator app
                        </Paragraph>

                        {engagementName && (
                            <Alert
                                message={`Engagement: ${engagementName}`}
                                description={storedName ? `Welcome back, ${storedName}` : undefined}
                                type="info"
                                showIcon
                                style={{ marginBottom: 24 }}
                            />
                        )}

                        <Space direction="vertical" size="large" style={{ width: '100%' }}>
                            <Input
                                size="large"
                                prefix={<LockOutlined style={{ color: '#9ca3af' }} />}
                                placeholder="000000"
                                value={mfaCode}
                                onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                maxLength={6}
                                style={{ textAlign: 'center', letterSpacing: 8, fontSize: 24 }}
                                onPressEnter={handleMFAVerify}
                                autoFocus
                            />

                            <Button
                                type="primary"
                                size="large"
                                block
                                loading={isLoading}
                                onClick={handleMFAVerify}
                                disabled={mfaCode.length !== 6}
                                style={{
                                    background: 'linear-gradient(135deg, #0f386a, #0a2d55)',
                                    borderColor: '#0f386a',
                                    height: 48
                                }}
                            >
                                Verify & Login
                            </Button>
                        </Space>
                    </div>
                );

            case 'complete':
                return (
                    <div style={{ textAlign: 'center', padding: '40px 0' }}>
                        <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a' }} />
                        <Title level={4} style={{ marginTop: 24, color: '#1a365d' }}>
                            Login Successful
                        </Title>
                        <Text type="secondary">
                            Redirecting to the audit review portal...
                        </Text>
                    </div>
                );

            default:
                return null;
        }
    };

    // Background words configuration
    const backgroundWords = [
        { text: 'AUDIT', top: '10%', left: '8%', size: '3.5rem' },
        { text: 'REVIEW', top: '12%', right: '10%', size: '3.2rem' },
        { text: 'COMPLIANCE', top: '35%', left: '5%', size: '3rem' },
        { text: 'EVIDENCE', top: '32%', right: '5%', size: '2.8rem' },
        { text: 'CONTROLS', bottom: '30%', left: '6%', size: '3rem' },
        { text: 'FINDINGS', bottom: '28%', right: '8%', size: '3rem' },
        { text: 'SECURE', bottom: '12%', left: '25%', size: '3.2rem' },
        { text: 'VERIFY', bottom: '10%', right: '12%', size: '3.2rem' },
    ];

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            padding: '20px',
            background: 'url(/login_bg.png) no-repeat center / cover',
            position: 'relative',
            overflow: 'hidden'
        }}>
            {/* Dotted pattern overlay */}
            <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                backgroundImage: `radial-gradient(circle, rgba(255,255,255,0.08) 1px, transparent 1px)`,
                backgroundSize: '24px 24px',
                pointerEvents: 'none',
                zIndex: 1
            }} />

            {/* Background words */}
            {backgroundWords.map((word, index) => (
                <div
                    key={index}
                    style={{
                        position: 'absolute',
                        top: word.top,
                        left: word.left,
                        right: word.right,
                        bottom: word.bottom,
                        fontSize: word.size,
                        fontWeight: 800,
                        color: 'rgba(255, 255, 255, 0.06)',
                        letterSpacing: '0.15em',
                        textTransform: 'uppercase',
                        whiteSpace: 'nowrap',
                        pointerEvents: 'none',
                        userSelect: 'none',
                        zIndex: 1,
                        fontFamily: 'system-ui, -apple-system, sans-serif'
                    }}
                >
                    {word.text}
                </div>
            ))}

            {contextHolder}

            <Card
                style={{
                    width: '100%',
                    maxWidth: 480,
                    borderRadius: 16,
                    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
                    position: 'relative',
                    zIndex: 2
                }}
                styles={{ body: { padding: '32px' } }}
            >
                <div style={{ textAlign: 'center', marginBottom: 24 }}>
                    <img
                        src={cyberbridgeLogo}
                        alt="CyberBridge Logo"
                        style={{ width: '100%', maxWidth: 280, marginBottom: 8 }}
                    />
                    <Text type="secondary" style={{ fontSize: 14 }}>
                        Audit Engagement Portal
                    </Text>
                </div>

                {currentStep !== 'request_link' && currentStep !== 'verify_token' && (
                    <Steps
                        size="small"
                        current={currentStep === 'mfa_setup' ? 0 : currentStep === 'mfa_verify' ? 1 : 2}
                        style={{ marginBottom: 24 }}
                        items={[
                            {
                                title: 'Setup MFA',
                                icon: <SafetyOutlined />,
                                status: currentStep === 'mfa_setup' ? 'process' :
                                    (currentStep === 'mfa_verify' || currentStep === 'complete') ? 'finish' : 'wait'
                            },
                            {
                                title: 'Verify',
                                icon: <LockOutlined />,
                                status: currentStep === 'mfa_verify' ? 'process' :
                                    currentStep === 'complete' ? 'finish' : 'wait'
                            },
                            {
                                title: 'Complete',
                                icon: <CheckCircleOutlined />,
                                status: currentStep === 'complete' ? 'finish' : 'wait'
                            }
                        ]}
                    />
                )}

                {renderContent()}

                {error && currentStep !== 'verify_token' && (
                    <Alert
                        message="Error"
                        description={error}
                        type="error"
                        showIcon
                        closable
                        onClose={clearError}
                        style={{ marginTop: 16 }}
                    />
                )}
            </Card>

            <Text style={{ color: 'rgba(255,255,255,0.6)', marginTop: 24, zIndex: 2 }}>
                CyberBridge - Cybersecurity Compliance Platform
            </Text>
        </div>
    );
}
