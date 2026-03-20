import { useLocation } from 'wouter';
import useThemeStore from '../store/useThemeStore';
import cyberbridgeLogo from '../assets/cyberbridge_logo.svg';

export default function VerifySuccessPage() {
    const [, setLocation] = useLocation();
    const { theme } = useThemeStore();

    const params = new URLSearchParams(window.location.search);
    const email = params.get('email');
    const organization = params.get('organization');
    const role = params.get('role');
    const error = params.get('error');

    if (error) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: '100vh',
                background: 'url(/login_bg.png) no-repeat center / cover',
                position: 'relative',
                overflow: 'hidden',
            }}>
                {/* Dotted pattern overlay */}
                <div style={{
                    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                    backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.08) 1px, transparent 1px)',
                    backgroundSize: '24px 24px', pointerEvents: 'none', zIndex: 1,
                }} />

                <div style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    borderRadius: '24px',
                    padding: '48px',
                    maxWidth: '500px',
                    width: '90%',
                    textAlign: 'center',
                    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
                    position: 'relative',
                    zIndex: 2,
                }}>
                    <img src={cyberbridgeLogo} alt="CyberBridge" style={{ width: '200px', marginBottom: '24px' }} />

                    <div style={{
                        width: '64px', height: '64px', borderRadius: '50%',
                        backgroundColor: '#fff2f0', border: '2px solid #ffccc7',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        margin: '0 auto 20px',
                    }}>
                        <span style={{ fontSize: '28px' }}>&#10007;</span>
                    </div>

                    <h2 style={{ color: '#1a365d', fontSize: '22px', fontWeight: 700, margin: '0 0 12px' }}>
                        Verification Failed
                    </h2>
                    <p style={{ color: '#dc2626', fontSize: '15px', lineHeight: 1.6, margin: '0 0 28px' }}>
                        {decodeURIComponent(error)}
                    </p>
                    <button
                        onClick={() => setLocation('/login')}
                        style={{
                            padding: '14px 40px',
                            background: 'linear-gradient(135deg, #0f386a, #0a2d55)',
                            color: 'white', border: 'none', borderRadius: '8px',
                            fontSize: '16px', fontWeight: 600, cursor: 'pointer',
                            transition: 'all 0.2s ease',
                            boxShadow: '0 4px 15px rgba(15, 56, 106, 0.4)',
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
            background: 'url(/login_bg.png) no-repeat center / cover',
            position: 'relative',
            overflow: 'hidden',
        }}>
            {/* Dotted pattern overlay */}
            <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
                backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.08) 1px, transparent 1px)',
                backgroundSize: '24px 24px', pointerEvents: 'none', zIndex: 1,
            }} />

            <div style={{
                backgroundColor: theme === 'dark-glass' ? 'rgba(30, 41, 59, 0.4)' : (theme === 'dark' ? '#1a1a2e' : 'rgba(255, 255, 255, 0.95)'),
                backdropFilter: theme === 'dark-glass' ? 'blur(20px) saturate(160%)' : 'none',
                border: theme === 'dark-glass' ? '1px solid rgba(255, 255, 255, 0.15)' : (theme === 'dark' ? '1px solid #2a3a5c' : 'none'),
                borderRadius: '24px',
                padding: '48px',
                maxWidth: '500px',
                width: '90%',
                textAlign: 'center',
                boxShadow: theme === 'dark-glass' ? '0 25px 50px -12px rgba(0, 0, 0, 0.5)' : '0 20px 60px rgba(0, 0, 0, 0.3)',
                position: 'relative',
                zIndex: 2,
            }}>
                <img
                    src={cyberbridgeLogo}
                    alt="CyberBridge"
                    style={{
                        width: '200px',
                        marginBottom: '24px',
                        filter: theme !== 'light' ? 'brightness(0) invert(1)' : 'none',
                    }}
                />

                {/* Success checkmark circle */}
                <div style={{
                    width: '72px', height: '72px', borderRadius: '50%',
                    backgroundColor: '#f6ffed', border: '3px solid #52c41a',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 24px',
                }}>
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#52c41a" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                    </svg>
                </div>

                <h2 style={{
                    color: theme !== 'light' ? '#f1f5f9' : '#1a365d',
                    fontSize: '24px',
                    fontWeight: 700,
                    margin: '0 0 8px',
                }}>
                    Email Verified Successfully
                </h2>
                <p style={{
                    color: theme !== 'light' ? '#94a3b8' : '#64748b',
                    fontSize: '15px',
                    lineHeight: 1.6,
                    margin: '0 0 28px',
                }}>
                    {role === 'org_admin'
                        ? 'Your account has been created and is pending super administrator approval. You will be able to log in once approved.'
                        : 'Your account has been created and is pending administrator approval. You will be able to log in once approved.'}
                </p>

                {/* Account details card */}
                <div style={{
                    backgroundColor: theme !== 'light' ? 'rgba(255,255,255,0.05)' : '#f8fafc',
                    border: theme !== 'light' ? '1px solid rgba(255,255,255,0.1)' : '1px solid #e2e8f0',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '28px',
                    textAlign: 'left',
                }}>
                    <div style={{ marginBottom: '12px' }}>
                        <span style={{ color: theme !== 'light' ? '#94a3b8' : '#94a3b8', fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Email
                        </span>
                        <p style={{ color: theme !== 'light' ? '#f1f5f9' : '#1e293b', fontSize: '15px', margin: '4px 0 0', fontWeight: 500 }}>
                            {email || '—'}
                        </p>
                    </div>
                    <div style={{ marginBottom: '12px' }}>
                        <span style={{ color: theme !== 'light' ? '#94a3b8' : '#94a3b8', fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Organization
                        </span>
                        <p style={{ color: theme !== 'light' ? '#f1f5f9' : '#1e293b', fontSize: '15px', margin: '4px 0 0', fontWeight: 500 }}>
                            {organization || '—'}
                        </p>
                    </div>
                    <div style={{ marginBottom: '12px' }}>
                        <span style={{ color: theme !== 'light' ? '#94a3b8' : '#94a3b8', fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Role
                        </span>
                        <p style={{ color: theme !== 'light' ? '#f1f5f9' : '#1e293b', fontSize: '15px', margin: '4px 0 0', fontWeight: 500 }}>
                            {role === 'org_admin' ? 'Organization Admin' : role === 'org_user' ? 'Organization User' : role || '—'}
                        </p>
                    </div>
                    <div>
                        <span style={{ color: theme !== 'light' ? '#94a3b8' : '#94a3b8', fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            Status
                        </span>
                        <p style={{ color: '#f59e0b', fontSize: '15px', margin: '4px 0 0', fontWeight: 600 }}>
                            Pending Approval
                        </p>
                    </div>
                </div>

                <button
                    onClick={() => setLocation('/login')}
                    style={{
                        width: '100%',
                        padding: '14px 24px',
                        background: 'linear-gradient(135deg, #0f386a, #0a2d55)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '16px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        boxShadow: '0 4px 15px rgba(15, 56, 106, 0.4)',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(15, 56, 106, 0.5)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 15px rgba(15, 56, 106, 0.4)'; }}
                >
                    Login
                </button>
            </div>
        </div>
    );
}
