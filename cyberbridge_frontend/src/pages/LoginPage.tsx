// src/pages/LoginPage.tsx
import {useEffect, useState, useRef, useCallback} from 'react'
import { useLocation } from 'wouter'
import useAuthStore from '../store/useAuthStore'
import useUserStore from '../store/useUserStore'
import useThemeStore from '../store/useThemeStore'
import { notification } from 'antd'
import { cyberbridge_back_end_rest_api } from '../constants/urls'
import * as React from "react";
import '../index.css'
import cyberbridgeLogo from '../assets/cyberbridge_logo.svg'
import ecccLogo from '../assets/eccc_logo.svg'
import euLogo from '../assets/eu_logo.svg'

export default function LoginPage() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [forgotPasswordLoading, setForgotPasswordLoading] = useState(false)
    const [customLogo, setCustomLogo] = useState<string | null>(null)
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
    const [ssoStatus, setSsoStatus] = useState<{ sso_enabled: boolean; google_configured: boolean; microsoft_configured: boolean; providers: string[] }>({
        sso_enabled: false,
        google_configured: false,
        microsoft_configured: false,
        providers: [],
    })
    const login = useAuthStore((state) => state.login)
    const { fetchCurrentUser } = useUserStore()
    const [location, setLocation] = useLocation()
    const [api, contextHolder] = notification.useNotification()

    const fetchLoginLogo = useCallback((domain?: string) => {
        const url = domain
            ? `${cyberbridge_back_end_rest_api}/auth/login-logo?domain=${encodeURIComponent(domain)}`
            : `${cyberbridge_back_end_rest_api}/auth/login-logo`;
        fetch(url)
            .then(res => res.json())
            .then(data => { if (data.logo) setCustomLogo(data.logo); else if (!domain) setCustomLogo(null); })
            .catch(() => {});
    }, []);

    useEffect(() => {
        console.log(location)
    })

    useEffect(() => {
        // Fetch global login logo on mount
        fetchLoginLogo();

        fetch(`${cyberbridge_back_end_rest_api}/auth/sso/providers`)
            .then(res => res.json())
            .then(data => setSsoStatus({
                sso_enabled: data.sso_enabled || false,
                google_configured: data.google_configured || false,
                microsoft_configured: data.microsoft_configured || false,
                providers: data.providers || [],
            }))
            .catch(() => setSsoStatus({ sso_enabled: false, google_configured: false, microsoft_configured: false, providers: [] }))
    }, [])

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        try {
            const result = await login(email, password)
            if (result.success) {
                // Check if user must change password before proceeding
                const currentMustChange = useAuthStore.getState().mustChangePassword
                if (currentMustChange) {
                    setLocation('/force-change-password')
                    return
                }
                // Fetch current user information after successful login
                const userFetched = await fetchCurrentUser()
                if (userFetched) {
                    setLocation('/home')
                } else {
                    setError('Failed to fetch user information. Please try again.')
                }
            } else {
                setError(result.error || 'Login failed. Please try again.')
            }
        } catch (error) {
            console.error('Login error:', error)
            setError('Login failed. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    const handleForgotPassword = async () => {
        // Basic email validation
        if (!email || email.trim() === '') {
            api.error({
                message: 'Email Required',
                description: 'Please enter your email address to reset your password.',
                duration: 4,
            });
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            api.error({
                message: 'Invalid Email',
                description: 'Please enter a valid email address.',
                duration: 4,
            });
            return;
        }

        setForgotPasswordLoading(true);

        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/auth/forgot-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email })
            });

            if (response.ok) {
                api.success({
                    message: 'Password Reset Email Sent',
                    description: 'If your email address exists in our system, a temporary password has been sent. Please check your inbox.',
                    duration: 8,
                });
                // Password reset success
            } else {
                api.error({
                    message: 'Request Failed',
                    description: 'Unable to process password reset request. Please try again.',
                    duration: 4,
                });
            }
        } catch (error) {
            console.error('Forgot password error:', error);
            api.error({
                message: 'Request Failed',
                description: 'Network error. Please try again.',
                duration: 4,
            });
        } finally {
            setForgotPasswordLoading(false);
        }
    };

    const { theme } = useThemeStore();

    return (
        <div 
            data-theme={theme}
            style={{
                display:'flex',
                flexDirection: 'column',
                justifyContent:'space-between',
                alignItems:'center',
                minHeight:'100vh',
                padding: '0px',
                margin: '0px',
                background: theme === 'dark-glass' ? 'transparent' : (theme === 'dark' ? '#0b1420' : 'url(/login_bg.png) no-repeat center / cover'),
                position: 'relative',
                overflow: 'hidden'
            }}
        >
            {contextHolder}
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'center', position: 'relative', zIndex: 2 }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '300px', width: '90%', maxWidth: '450px' }}>
            <form onSubmit={handleSubmit} style={{
                width: '100%',
                padding: '3rem 2rem',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                background: theme === 'dark-glass' ? 'rgba(30, 41, 59, 0.4)' : (theme === 'dark' ? '#1a1a2e' : 'rgba(255, 255, 255, 0.55)'),
                backdropFilter: theme === 'dark-glass' ? 'blur(20px) saturate(160%)' : 'blur(12px)',
                border: theme === 'dark-glass' ? '1px solid rgba(255, 255, 255, 0.15)' : (theme === 'dark' ? '1px solid #2a3a5c' : 'none'),
                borderRadius: '24px',
                boxShadow: theme === 'dark-glass' ? '0 25px 50px -12px rgba(0, 0, 0, 0.5)' : '0 20px 60px rgba(0, 0, 0, 0.3)'
            }}>
                <img src={customLogo || cyberbridgeLogo} alt="Logo" style={{width: '80%', maxWidth: '300px', marginBottom: '24px', filter: !customLogo && theme !== 'light' ? 'brightness(0) invert(1)' : 'none'}} />

                <p style={{
                    margin: '0 0 24px 0',
                    color: theme !== 'light' ? '#f1f5f9' : '#1a365d',
                    fontSize: '16px',
                    textAlign: 'center',
                    fontWeight: 500
                }}>Your cross-border AI-powered cybersecurity platform</p>

                <input
                    className={'login-input'}
                    type="text"
                    id="email"
                    placeholder={"Email"}
                    value={email}
                    onChange={(e) => {
                        const val = e.target.value;
                        setEmail(val);
                        if (debounceRef.current) clearTimeout(debounceRef.current);
                        debounceRef.current = setTimeout(() => {
                            const atIdx = val.indexOf('@');
                            if (atIdx > 0 && val.length > atIdx + 1) {
                                const domain = val.split('@')[1];
                                if (domain && domain.includes('.')) fetchLoginLogo(domain);
                            } else if (!val) {
                                fetchLoginLogo();
                            }
                        }, 500);
                    }}
                    required
                    style={{
                        width: '100%',
                        padding: '14px 16px',
                        marginBottom: '16px',
                        backgroundColor: theme === 'dark-glass' ? 'rgba(15, 23, 42, 0.25)' : (theme === 'dark' ? '#16213e' : '#ffffff'),
                        color: theme !== 'light' ? '#ffffff' : '#374151',
                        border: theme !== 'light' ? '1px solid rgba(255, 255, 255, 0.1)' : '2px solid #e5e7eb',
                        borderRadius: '10px',
                        fontSize: '15px',
                        transition: 'border-color 0.2s ease',
                        outline: 'none',
                        boxSizing: 'border-box'
                    }}
                />
                <input
                    className={'login-input'}
                    type="password"
                    id="password"
                    placeholder={'Password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    style={{
                        width: '100%',
                        padding: '14px 16px',
                        marginBottom: '24px',
                        backgroundColor: theme === 'dark-glass' ? 'rgba(15, 23, 42, 0.25)' : (theme === 'dark' ? '#16213e' : '#ffffff'),
                        color: theme !== 'light' ? '#ffffff' : '#374151',
                        border: theme !== 'light' ? '1px solid rgba(255, 255, 255, 0.1)' : '2px solid #e5e7eb',
                        borderRadius: '10px',
                        fontSize: '15px',
                        transition: 'border-color 0.2s ease',
                        outline: 'none',
                        boxSizing: 'border-box'
                    }}
                />
                <button
                    className={'login-button'}
                    type="submit"
                    disabled={loading}
                    style={{
                        width: '100%',
                        padding: '14px 24px',
                        background: 'linear-gradient(135deg, #0f386a, #0a2d55)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '16px',
                        fontWeight: 600,
                        cursor: loading ? 'not-allowed' : 'pointer',
                        opacity: loading ? 0.7 : 1,
                        transition: 'all 0.2s ease',
                        boxShadow: '0 4px 15px rgba(15, 56, 106, 0.4)'
                    }}
                >
                    {loading ? 'Signing in...' : 'Sign In'}
                </button>

                {/* SSO Buttons - Always visible, disabled when not configured */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    margin: '20px 0',
                    gap: '12px',
                }}>
                    <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.15)' }} />
                    <span style={{ color: '#6b7280', fontSize: '13px', whiteSpace: 'nowrap' }}>or sign in with</span>
                    <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.15)' }} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%' }}>
                    <button
                        type="button"
                        disabled={!ssoStatus.sso_enabled || !ssoStatus.google_configured}
                        onClick={() => { window.location.href = `${cyberbridge_back_end_rest_api}/auth/sso/google/login`; }}
                        title={!ssoStatus.sso_enabled || !ssoStatus.google_configured ? 'Not configured' : 'Sign in with Google'}
                        style={{
                            width: '100%',
                            padding: '12px 24px',
                            backgroundColor: (!ssoStatus.sso_enabled || !ssoStatus.google_configured) ? '#e8e8e8' : '#e2e8f0',
                            color: (!ssoStatus.sso_enabled || !ssoStatus.google_configured) ? '#9ca3af' : '#475569',
                            border: 'none',
                            borderRadius: '8px',
                            fontSize: '15px',
                            fontWeight: 500,
                            cursor: (!ssoStatus.sso_enabled || !ssoStatus.google_configured) ? 'not-allowed' : 'pointer',
                            opacity: (!ssoStatus.sso_enabled || !ssoStatus.google_configured) ? 0.6 : 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '10px',
                            transition: 'all 0.2s ease',
                        }}
                        onMouseEnter={(e) => { if (ssoStatus.sso_enabled && ssoStatus.google_configured) { e.currentTarget.style.backgroundColor = '#cbd5e1'; } }}
                        onMouseLeave={(e) => { if (ssoStatus.sso_enabled && ssoStatus.google_configured) { e.currentTarget.style.backgroundColor = '#e2e8f0'; } }}
                    >
                        <svg width="18" height="18" viewBox="0 0 18 18"><path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/><path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/><path d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/><path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.462.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/></svg>
                        Sign in with Google
                    </button>
                    <button
                        type="button"
                        disabled={!ssoStatus.sso_enabled || !ssoStatus.microsoft_configured}
                        onClick={() => { window.location.href = `${cyberbridge_back_end_rest_api}/auth/sso/microsoft/login`; }}
                        title={!ssoStatus.sso_enabled || !ssoStatus.microsoft_configured ? 'Not configured' : 'Sign in with Microsoft'}
                        style={{
                            width: '100%',
                            padding: '12px 24px',
                            backgroundColor: (!ssoStatus.sso_enabled || !ssoStatus.microsoft_configured) ? '#e8e8e8' : '#e2e8f0',
                            color: (!ssoStatus.sso_enabled || !ssoStatus.microsoft_configured) ? '#9ca3af' : '#475569',
                            border: 'none',
                            borderRadius: '8px',
                            fontSize: '15px',
                            fontWeight: 500,
                            cursor: (!ssoStatus.sso_enabled || !ssoStatus.microsoft_configured) ? 'not-allowed' : 'pointer',
                            opacity: (!ssoStatus.sso_enabled || !ssoStatus.microsoft_configured) ? 0.6 : 1,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '10px',
                            transition: 'all 0.2s ease',
                        }}
                        onMouseEnter={(e) => { if (ssoStatus.sso_enabled && ssoStatus.microsoft_configured) { e.currentTarget.style.backgroundColor = '#cbd5e1'; } }}
                        onMouseLeave={(e) => { if (ssoStatus.sso_enabled && ssoStatus.microsoft_configured) { e.currentTarget.style.backgroundColor = '#e2e8f0'; } }}
                    >
                        <svg width="18" height="18" viewBox="0 0 21 21"><rect x="1" y="1" width="9" height="9" fill="#f25022"/><rect x="11" y="1" width="9" height="9" fill="#7fba00"/><rect x="1" y="11" width="9" height="9" fill="#00a4ef"/><rect x="11" y="11" width="9" height="9" fill="#ffb900"/></svg>
                        Sign in with Microsoft
                    </button>
                </div>

                <div style={{
                    marginTop: '24px',
                    textAlign: 'center',
                }}>
                    <p style={{
                        margin: '0 0 12px 0',
                        color: '#6b7280',
                        fontSize: '12px',
                    }}>
                        Don't have an account?{' '}
                        <a
                            href="#"
                            onClick={() => setLocation('/register')}
                            style={{
                                color: '#0f386a',
                                textDecoration: 'none',
                                fontWeight: 600
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'}
                            onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
                        >
                            Register here
                        </a>
                    </p>
                    <p style={{
                        margin: 0,
                        color: '#6b7280',
                        fontSize: '12px',
                    }}>
                        Forgot your password?{' '}
                        <a
                            href="#"
                            onClick={handleForgotPassword}
                            style={{
                                color: forgotPasswordLoading ? '#9ca3af' : '#4a6d8c',
                                textDecoration: 'none',
                                cursor: forgotPasswordLoading ? 'not-allowed' : 'pointer',
                                fontWeight: 600
                            }}
                            onMouseEnter={(e) => !forgotPasswordLoading && (e.currentTarget.style.textDecoration = 'underline')}
                            onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
                        >
                            {forgotPasswordLoading ? 'Sending...' : 'Reset password'}
                        </a>
                    </p>
                </div>
                {error && <p style={{ color: '#dc2626', marginTop: '16px', fontSize: '14px', textAlign: 'center' }}>{error}</p>}
            </form>
            </div>
            </div>

            {/* Partner Logos Section - At Very Bottom */}
            <div style={{
                width: '100%',
                padding: '1.5rem 0',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                gap: '2rem',
                flexWrap: 'nowrap',
                background: 'rgba(0, 0, 0, 0.45)',
                position: 'relative',
                zIndex: 2
            }}>
                <img src={cyberbridgeLogo} alt="CyberBridge Logo" style={{ height: '50px', objectFit: 'contain' }} />
                <img src={euLogo} alt="European Union Logo" style={{ height: '40px', objectFit: 'contain' }} />
                <img src={ecccLogo} alt="ECCC Logo" style={{ height: '40px', objectFit: 'contain' }} />
            </div>
        </div>
    )
}
