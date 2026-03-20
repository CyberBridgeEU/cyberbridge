// src/pages/ForceChangePasswordPage.tsx
import { useState } from 'react'
import { useLocation } from 'wouter'
import useAuthStore from '../store/useAuthStore'
import useUserStore from '../store/useUserStore'
import useThemeStore from '../store/useThemeStore'
import { cyberbridge_back_end_rest_api } from '../constants/urls'
import '../index.css'
import cyberbridgeLogo from '../assets/cyberbridge_logo.svg'

export default function ForceChangePasswordPage() {
    const [newPassword, setNewPassword] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const getAuthHeader = useAuthStore((state) => state.getAuthHeader)
    const clearMustChangePassword = useAuthStore((state) => state.clearMustChangePassword)
    const { fetchCurrentUser } = useUserStore()
    const [, setLocation] = useLocation()
    const { theme } = useThemeStore()

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError('')

        if (newPassword.length < 8) {
            setError('Password must be at least 8 characters long.')
            return
        }

        if (newPassword !== confirmPassword) {
            setError('Passwords do not match.')
            return
        }

        setLoading(true)

        try {
            const authHeader = getAuthHeader()
            if (!authHeader) {
                setError('Session expired. Please log in again.')
                setLocation('/login')
                return
            }

            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/force-change-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...authHeader
                },
                body: JSON.stringify({ new_password: newPassword })
            })

            if (response.ok) {
                clearMustChangePassword()
                await fetchCurrentUser()
                setLocation('/home')
            } else {
                const data = await response.json()
                setError(data.detail || 'Failed to change password. Please try again.')
            }
        } catch (err) {
            console.error('Force change password error:', err)
            setError('Network error. Please try again.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div
            data-theme={theme}
            style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: '100vh',
                padding: '0px',
                margin: '0px',
                background: theme === 'dark-glass' ? 'transparent' : (theme === 'dark' ? '#0b1420' : 'url(/login_bg.png) no-repeat center / cover'),
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundRepeat: 'no-repeat',
                position: 'relative',
                overflow: 'hidden'
            }}
        >
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

            <div style={{ position: 'relative', zIndex: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '300px', width: '90%', maxWidth: '520px' }}>
                <form onSubmit={handleSubmit} style={{
                    width: '100%',
                    padding: '3rem 2rem',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    background: theme === 'dark-glass' ? 'rgba(30, 41, 59, 0.4)' : (theme === 'dark' ? '#1a1a2e' : 'rgba(255, 255, 255, 0.95)'),
                    backdropFilter: theme === 'dark-glass' ? 'blur(20px) saturate(160%)' : 'none',
                    border: theme === 'dark-glass' ? '1px solid rgba(255, 255, 255, 0.15)' : (theme === 'dark' ? '1px solid #2a3a5c' : 'none'),
                    borderRadius: '24px',
                    boxShadow: theme === 'dark-glass' ? '0 25px 50px -12px rgba(0, 0, 0, 0.5)' : '0 20px 60px rgba(0, 0, 0, 0.3)'
                }}>
                    <img src={cyberbridgeLogo} alt="CyberBridge Logo" style={{ width: '100%', maxWidth: '380px', marginBottom: '24px', filter: theme !== 'light' ? 'brightness(0) invert(1)' : 'none' }} />

                    <p style={{
                        margin: '0 0 8px 0',
                        color: theme !== 'light' ? '#f1f5f9' : '#1a365d',
                        fontSize: '18px',
                        textAlign: 'center',
                        fontWeight: 600
                    }}>Change Your Password</p>

                    <p style={{
                        margin: '0 0 24px 0',
                        color: '#6b7280',
                        fontSize: '14px',
                        textAlign: 'center',
                    }}>For security, you must set a new password before continuing.</p>

                    <input
                        className={'login-input'}
                        type="password"
                        placeholder="New Password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
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
                        placeholder="Confirm New Password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
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
                        {loading ? 'Updating...' : 'Update Password'}
                    </button>

                    {error && <p style={{ color: '#dc2626', marginTop: '16px', fontSize: '14px', textAlign: 'center' }}>{error}</p>}
                </form>
            </div>
        </div>
    )
}
