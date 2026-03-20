import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import useAuthStore from '../store/useAuthStore';
import useUserStore from '../store/useUserStore';
import { Spin } from 'antd';

export default function SSOCallbackPage() {
    const [error, setError] = useState<string | null>(null);
    const [, setLocation] = useLocation();
    const { loginWithSSO } = useAuthStore();
    const { fetchCurrentUser } = useUserStore();

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const token = params.get('token');
        const errorParam = params.get('error');

        if (token) {
            loginWithSSO(token);
            fetchCurrentUser().then(() => {
                setLocation('/home');
            });
        } else if (errorParam) {
            setError(decodeURIComponent(errorParam));
        } else {
            setError('Invalid SSO callback. No token or error received.');
        }
    }, []);

    if (error) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: '100vh',
                background: 'linear-gradient(135deg, #0f1923 0%, #1a2a3a 50%, #0d1b2a 100%)',
            }}>
                <div style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '16px',
                    padding: '48px',
                    maxWidth: '480px',
                    width: '90%',
                    textAlign: 'center',
                }}>
                    <div style={{
                        fontSize: '48px',
                        marginBottom: '16px',
                    }}>
                        &#9888;
                    </div>
                    <h2 style={{
                        color: '#ffffff',
                        fontSize: '20px',
                        fontWeight: 600,
                        marginBottom: '16px',
                    }}>
                        Sign-In Error
                    </h2>
                    <p style={{
                        color: '#dc2626',
                        fontSize: '15px',
                        lineHeight: 1.6,
                        marginBottom: '24px',
                    }}>
                        {error}
                    </p>
                    <button
                        onClick={() => setLocation('/login')}
                        style={{
                            padding: '12px 32px',
                            background: 'linear-gradient(135deg, #0f386a, #0a2d55)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '8px',
                            fontSize: '15px',
                            fontWeight: 600,
                            cursor: 'pointer',
                            transition: 'all 0.2s ease',
                        }}
                    >
                        Back to Login
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #0f1923 0%, #1a2a3a 50%, #0d1b2a 100%)',
        }}>
            <div style={{ textAlign: 'center' }}>
                <Spin size="large" />
                <p style={{ color: '#ffffff', marginTop: '16px', fontSize: '16px' }}>
                    Completing sign-in...
                </p>
            </div>
        </div>
    );
}
