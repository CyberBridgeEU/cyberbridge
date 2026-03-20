import {useState, useEffect, useRef, useCallback} from 'react'
import { useLocation } from 'wouter'
import useThemeStore from '../store/useThemeStore'
import { notification } from 'antd'
import { cyberbridge_back_end_rest_api } from '../constants/urls'
import '../index.css'
import cyberbridgeLogo from '../assets/cyberbridge_logo.svg'
import ecccLogo from '../assets/eccc_logo.svg'
import euLogo from '../assets/eu_logo.svg'

export default function RegisterPage() {
    const { theme } = useThemeStore();
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const [resendLoading, setResendLoading] = useState(false)
    const [customLogo, setCustomLogo] = useState<string | null>(null)
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    const [, setLocation] = useLocation()
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
        fetchLoginLogo();
    }, []);


    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')

        // Validation
        if (!email || !password || !confirmPassword) {
            setError('All fields are required')
            return
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match')
            return
        }

        if (password.length < 6) {
            setError('Password must be at least 6 characters long')
            return
        }

        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailRegex.test(email)) {
            setError('Please enter a valid email address')
            return
        }

        setLoading(true)

        try {
            // Call registration API with email verification
            const response = await fetch(`${cyberbridge_back_end_rest_api}/auth/register-with-verification`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email,
                    password
                })
            })

            if (response.ok) {
                api.success({
                    message: 'Registration Email Sent',
                    description: 'Please check your email and click the verification link to complete registration.',
                    duration: 6,
                })
                setLocation('/login')
            } else {
                const errorData = await response.json()
                const errorMessage = errorData.detail || 'Registration failed'
                setError(errorMessage)
                api.error({
                    message: 'Registration Failed',
                    description: errorMessage,
                    duration: 6,
                })
            }
        } catch (error) {
            console.error('Registration error:', error)
            setError('Registration failed. Please try again.')
            api.error({
                message: 'Registration Failed',
                description: 'Network error. Please try again.',
                duration: 4,
            })
        } finally {
            setLoading(false)
        }
    }

    const handleResendVerification = async () => {
        // Basic email validation
        if (!email || email.trim() === '') {
            api.error({
                message: 'Email Required',
                description: 'Please enter your email address to resend verification.',
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

        setResendLoading(true);
        setError('');

        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/auth/resend-verification`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email })
            });

            if (response.ok) {
                api.success({
                    message: 'Verification Email Resent',
                    description: 'A new verification email has been sent. Please check your inbox and spam folder.',
                    duration: 6,
                });
            } else {
                const errorData = await response.json();
                api.error({
                    message: 'Resend Failed',
                    description: errorData.detail || 'Failed to resend verification email.',
                    duration: 6,
                });
            }
        } catch (error) {
            console.error('Resend verification error:', error);
            api.error({
                message: 'Resend Failed',
                description: 'Failed to resend verification email. Please try again.',
                duration: 4,
            });
        } finally {
            setResendLoading(false);
        }
    };

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
            }}
        >
            {contextHolder}
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'center' }}>
            <form onSubmit={handleSubmit} style={{
                minWidth: '300px',
                width:'90%',
                maxWidth:'450px',
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
                <img src={customLogo || cyberbridgeLogo} alt="Logo" style={{width: '80%', maxWidth: '300px', marginBottom: '30px', filter: !customLogo && theme !== 'light' ? 'brightness(0) invert(1)' : 'none'}} />

                <h2 style={{
                    margin: '0 0 8px 0',
                    color: theme !== 'light' ? '#ffffff' : '#1a365d',
                    fontSize: '24px',
                    fontWeight: 600
                }}>Create Account</h2>
                <p style={{
                    margin: '0 0 24px 0',
                    color: theme !== 'light' ? '#94a3b8' : '#6b7280',
                    fontSize: '14px',
                    textAlign: 'center'
                }}>Enter your details to register for CyberBridge</p>

                <input
                    className={'login-input'}
                    type="email"
                    placeholder="Email"
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
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
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
                    placeholder="Confirm Password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    style={{
                        width: '100%',
                        padding: '14px 16px',
                        marginBottom: '24px',
                        backgroundColor: theme === 'dark-glass' ? 'rgba(15, 23, 42, 0.25)' : (theme === 'dark' ? '#16213e' : '#ffffff'),
                        color: theme !== 'light' ? '#ffffff' : '#374151',
                        border: confirmPassword && password !== confirmPassword ? '2px solid #dc2626' : (theme !== 'light' ? '1px solid rgba(255, 255, 255, 0.1)' : '2px solid #e5e7eb'),
                        borderRadius: '10px',
                        fontSize: '15px',
                        transition: 'border-color 0.2s ease',
                        outline: 'none',
                        boxSizing: 'border-box'
                    }}
                />
                {confirmPassword && password !== confirmPassword && (
                    <p style={{ color: '#dc2626', fontSize: '12px', margin: '-16px 0 16px 0', alignSelf: 'flex-start' }}>
                        Passwords do not match
                    </p>
                )}

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
                    {loading ? 'Creating Account...' : 'Create Account'}
                </button>

                <div style={{
                    marginTop: '24px',
                    textAlign: 'center',
                }}>
                    <p style={{
                        margin: '0 0 12px 0',
                        color: '#6b7280',
                        fontSize: '12px',
                    }}>
                        Already have an account?{' '}
                        <a
                            href="#"
                            onClick={() => setLocation('/login')}
                            style={{
                                color: '#0f386a',
                                textDecoration: 'none',
                                fontWeight: 600
                            }}
                            onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'}
                            onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
                        >
                            Sign in here
                        </a>
                    </p>
                    <p style={{
                        margin: 0,
                        color: '#6b7280',
                        fontSize: '12px',
                    }}>
                        Didn't receive verification email?{' '}
                        <a
                            href="#"
                            onClick={handleResendVerification}
                            style={{
                                color: resendLoading ? '#9ca3af' : '#4a6d8c',
                                textDecoration: 'none',
                                cursor: resendLoading ? 'not-allowed' : 'pointer',
                                fontWeight: 600
                            }}
                            onMouseEnter={(e) => !resendLoading && (e.currentTarget.style.textDecoration = 'underline')}
                            onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
                        >
                            {resendLoading ? 'Sending...' : 'Resend email'}
                        </a>
                    </p>
                </div>
                {error && <p style={{ color: '#dc2626', marginTop: '16px', fontSize: '14px', textAlign: 'center' }}>{error}</p>}
            </form>
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
                background: 'rgba(0, 0, 0, 0.45)'
            }}>
                <img src={cyberbridgeLogo} alt="CyberBridge Logo" style={{ height: '50px', objectFit: 'contain' }} />
                <img src={euLogo} alt="European Union Logo" style={{ height: '40px', objectFit: 'contain' }} />
                <img src={ecccLogo} alt="ECCC Logo" style={{ height: '40px', objectFit: 'contain' }} />
            </div>
        </div>
    )
}
