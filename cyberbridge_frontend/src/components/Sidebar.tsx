// src/components/Sidebar.tsx
import { Menu, Modal, Input, message, Tooltip } from 'antd';
import { LogoutOutlined, MenuFoldOutlined, MenuUnfoldOutlined, UserOutlined } from '@ant-design/icons';
import { MenuItems } from '../constants/menuItems';
import useAuthStore from '../store/useAuthStore';
import useUserStore from '../store/useUserStore';
import useAuditNotificationStore from '../store/useAuditNotificationStore';
import useCRAModeStore from '../store/useCRAModeStore';
import { useState, useEffect } from 'react';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import { useLocation } from 'wouter';
import cyberbridgeIcon from '../assets/cyberbridge_icon.svg';
import ProfileModal from './ProfileModal';
import ChatbotDrawer from './ChatbotDrawer';

interface SidebarProps {
    selectedKeys?: string[];
    openKeys?: string[];
    onOpenChange?: (keys: string[]) => void;
    onClick?: (info: { key: string }) => void;
    collapsed?: boolean;
    onCollapse?: (collapsed: boolean) => void;
}

// Menu key to route mapping for programmatic navigation
const menuKeyToRoute: Record<string, string> = {
    'dashboard': '/home',
    'assessments.main': '/assessments',
    'assessments.cra_scope': '/cra-scope-assessment',
    'assessments.cra_readiness': '/cra-readiness-assessment',
    'frameworks.management': '/framework_management',
    'frameworks.chapters': '/chapters_objectives',
    'frameworks.questions': '/framework_questions',
    'frameworks.updates': '/framework_updates',
    'frameworks.compliance_advisor': '/compliance_advisor',
    'frameworks.objectives': '/objectives_checklist',
    'assets.management': '/assets',
    'risks.register': '/risk_registration',
    'risks.assessment': '/risk_assessment',
    'risks.incidents': '/incidents',
    'controls.register': '/control_registration',
    'controls.library': '/controls_library',
    'documents.policies': '/policies_registration',
    'documents.architecture': '/architecture',
    'documents.evidence': '/evidence',
    'documents.eu_doc': '/eu_declaration_of_conformity',
    'documents.patch_support': '/patch_support_policy',
    'documents.vuln_disclosure': '/vulnerability_disclosure_policy',
    'documents.sbom_mgmt': '/sbom_management',
    'documents.sdlc_evidence': '/secure_sdlc_evidence',
    'documents.security_design': '/security_design_documentation',
    'documents.dependency_policy': '/dependency_policy',
    'compliance-chain.links': '/compliance_chain_links',
    'compliance-chain.map': '/compliance_chain_map',
    'compliance-chain.gap-analysis': '/gap_analysis',
    'monitoring.security_scanners': '/security_scanners',
    'monitoring.code_analysis': '/code_analysis',
    'monitoring.dependency_check': '/dependency_check',
    'monitoring.sbom': '/sbom_generator',
    'monitoring.scan_findings': '/scan_findings',
    'audit-engagements': '/audit-engagements',
    'admin.history': '/history',
    'admin.config': '/settings',
    'admin.correlations': '/correlations',
    'admin.organizations': '/organizations',
    'admin.users': '/users',
    'admin.background-jobs': '/background-jobs',
    'dark-web.dashboard': '/dark-web/dashboard',
    'dark-web.scans': '/dark-web/scans',
    'dark-web.reports': '/dark-web/reports',
    'dark-web.settings': '/dark-web/settings',
};

export default function Sidebar({ selectedKeys, openKeys, onOpenChange, onClick, collapsed: controlledCollapsed, onCollapse }: SidebarProps) {
    const { logout, token } = useAuthStore();
    const { current_user } = useUserStore();
    const { loadUnreadCount } = useAuditNotificationStore();
    const { craMode } = useCRAModeStore();
    const [, setLocation] = useLocation();
    const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
    const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
    const [isChatbotOpen, setIsChatbotOpen] = useState(false);
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [internalCollapsed, setInternalCollapsed] = useState(false);

    // Load notification count periodically for menu badge
    useEffect(() => {
        if (token && current_user && (current_user.role_name === 'super_admin' || current_user.role_name === 'org_admin')) {
            loadUnreadCount();
            const interval = setInterval(() => {
                loadUnreadCount();
            }, 30000);
            return () => clearInterval(interval);
        }
    }, [token, current_user?.role_name]);

    // Use controlled or internal state
    const collapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;
    const setCollapsed = (value: boolean) => {
        if (onCollapse) {
            onCollapse(value);
        } else {
            setInternalCollapsed(value);
        }
    };

    const handlePasswordChange = async () => {
        // Validation
        if (!currentPassword) {
            message.error('Please enter your current password');
            return;
        }
        if (!newPassword) {
            message.error('Please enter a new password');
            return;
        }
        if (newPassword.length < 8) {
            message.error('New password must be at least 8 characters');
            return;
        }
        if (newPassword !== confirmPassword) {
            message.error('New passwords do not match');
            return;
        }
        if (currentPassword === newPassword) {
            message.error('New password must be different from current password');
            return;
        }

        setLoading(true);
        try {
            console.log('Attempting password change...');
            console.log('API URL:', `${cyberbridge_back_end_rest_api}/users/change-password`);
            console.log('Token exists:', !!token);

            if (!token) {
                message.error('Not authenticated. Please log in again.');
                setLoading(false);
                return;
            }

            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/change-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });

            console.log('Response status:', response.status);

            if (response.ok) {
                message.success('Password changed successfully');
                setIsPasswordModalOpen(false);
                resetForm();
            } else {
                const data = await response.json();
                console.log('Error response:', data);
                message.error(data.detail || 'Failed to change password');
            }
        } catch (error) {
            console.error('Password change error:', error);
            message.error('An error occurred while changing password');
        } finally {
            setLoading(false);
        }
    };

    const resetForm = () => {
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
    };

    const handleModalClose = () => {
        setIsPasswordModalOpen(false);
        resetForm();
    };

    const sidebarWidth = collapsed ? 80 : 256;

    return (
        <div 
            className="sidebar-container"
            style={{
                width: sidebarWidth,
                minWidth: sidebarWidth,
                display: 'flex',
                flexDirection: 'column',
                minHeight: '100vh',
                height: '100%',
                backgroundColor: 'var(--menu-background)',
                position: 'sticky',
                top: 0,
                alignSelf: 'flex-start',
                transition: 'width 0.3s ease, min-width 0.3s ease'
            }}
        >
        <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', flex: 1 }}>
            {/* Collapse/Expand Toggle - positioned at sidebar edge */}
            {!collapsed && (
                <button
                    onClick={() => setCollapsed(true)}
                    style={{
                        position: 'absolute',
                        top: '0px',
                        right: '-6px',
                        zIndex: 100,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '28px',
                        height: '28px',
                        backgroundColor: 'var(--menu-background)',
                        border: 'none',
                        borderRadius: '0',
                        cursor: 'pointer',
                        color: 'rgba(255, 255, 255, 0.7)'
                    }}
                >
                    <MenuFoldOutlined style={{ fontSize: '14px' }} />
                </button>
            )}

            {/* Logo Section */}
            <div style={{
                padding: collapsed ? '12px 8px' : '16px',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '70px'
            }}>
                {collapsed ? (
                    <Tooltip title="CyberBridge" placement="right">
                        <img
                            src={cyberbridgeIcon}
                            alt="CyberBridge"
                            style={{
                                width: '28px',
                                height: '28px',
                                objectFit: 'contain',
                                cursor: 'pointer'
                            }}
                        />
                    </Tooltip>
                ) : (
                    <img
                        src={current_user?.organisation_logo || "/cyberbridge_logo_light.svg"}
                        alt={current_user?.organisation_logo ? `${current_user.organisation_name} Logo` : "CyberBridge Logo"}
                        style={{
                            height: '60px',
                            maxWidth: '230px',
                            objectFit: 'contain',
                            marginLeft: '-8px',
                        }}
                        onError={(e) => {
                            e.currentTarget.src = "/cyberbridge_logo_light.svg";
                        }}
                    />
                )}
            </div>

            {/* Expand button when collapsed */}
            {collapsed && (
                <button
                    onClick={() => setCollapsed(false)}
                    style={{
                        position: 'absolute',
                        top: '0px',
                        right: '-9px',
                        zIndex: 100,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '28px',
                        height: '28px',
                        backgroundColor: 'var(--menu-background)',
                        border: 'none',
                        borderRadius: '0',
                        cursor: 'pointer',
                        color: 'rgba(255, 255, 255, 0.7)'
                    }}
                >
                    <MenuUnfoldOutlined style={{ fontSize: '14px' }} />
                </button>
            )}

            {/* Menu Section */}
            <div style={{ flex: '1 1 auto', overflowY: 'auto', minHeight: 0 }}>
                <Menu
                    style={{ width: sidebarWidth, border: 'none' }}
                    mode="inline"
                    inlineCollapsed={collapsed}
                    selectedKeys={selectedKeys}
                    openKeys={collapsed ? [] : openKeys}
                    {...(!collapsed && { onOpenChange })}
                    onClick={(info) => {
                        // Handle AI Assistant - opens drawer instead of navigating
                        if (info.key === 'ai-assistant') {
                            setIsChatbotOpen(true);
                            return;
                        }
                        // Handle programmatic navigation (especially important when collapsed)
                        const route = menuKeyToRoute[info.key];
                        if (route) {
                            setLocation(route);
                        }
                        // Also call the original onClick if provided
                        if (onClick) {
                            onClick(info);
                        }
                    }}
                    items={MenuItems()}
                />
            </div>

            {/* User Section - Clean Design */}
            <div style={{
                flex: '0 0 auto',
                borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                padding: collapsed ? '12px 8px' : '12px 16px'
            }}>
                {collapsed ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                        <Tooltip title="My Profile" placement="right">
                            <div
                                onClick={() => setIsProfileModalOpen(true)}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'rgba(255, 255, 255, 0.7)',
                                    cursor: 'pointer',
                                    transition: 'color 0.2s ease'
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.color = '#0f386a';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.color = 'rgba(255, 255, 255, 0.7)';
                                }}
                            >
                                <UserOutlined style={{ fontSize: '18px' }} />
                            </div>
                        </Tooltip>
                        <Tooltip title={craMode === 'focused' ? 'CRA Focused' : craMode === 'extended' ? 'CRA Extended' : 'CRA Mode: Off'} placement="right">
                            <span style={{
                                width: '8px',
                                height: '8px',
                                borderRadius: '50%',
                                backgroundColor: craMode === 'focused' ? '#52c41a' : craMode === 'extended' ? '#1677ff' : 'rgba(255, 255, 255, 0.3)',
                                display: 'block',
                                transition: 'background-color 0.3s ease',
                            }} />
                        </Tooltip>
                        <Tooltip title="Sign out" placement="right">
                            <div
                                onClick={logout}
                                style={{
                                    color: 'rgba(255, 255, 255, 0.5)',
                                    cursor: 'pointer',
                                    fontSize: '16px',
                                    transition: 'color 0.2s ease'
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.color = 'rgba(255, 255, 255, 0.8)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.color = 'rgba(255, 255, 255, 0.5)';
                                }}
                            >
                                <LogoutOutlined />
                            </div>
                        </Tooltip>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {/* Top row: Username + CRA Mode side by side */}
                        <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                        }}>
                            <div
                                onClick={() => setIsProfileModalOpen(true)}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '6px',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s ease',
                                    minWidth: 0,
                                    flexShrink: 0,
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.opacity = '0.8';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.opacity = '1';
                                }}
                            >
                                <span style={{
                                    width: '8px',
                                    height: '8px',
                                    borderRadius: '50%',
                                    backgroundColor: '#22c55e',
                                    flexShrink: 0
                                }} />
                                <span style={{
                                    color: 'rgba(255, 255, 255, 0.85)',
                                    fontSize: '13px',
                                    whiteSpace: 'nowrap',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis'
                                }}>
                                    {current_user?.email?.split('@')[0] || 'User'}
                                </span>
                            </div>
                            {/* CRA Mode Indicator */}
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                flexShrink: 0,
                            }}>
                                <span style={{
                                    width: '8px',
                                    height: '8px',
                                    borderRadius: '50%',
                                    backgroundColor: craMode === 'focused' ? '#52c41a' : craMode === 'extended' ? '#1677ff' : 'rgba(255, 255, 255, 0.3)',
                                    display: 'block',
                                    flexShrink: 0,
                                    transition: 'background-color 0.3s ease',
                                }} />
                                <span style={{
                                    fontSize: '12px',
                                    color: 'rgba(255, 255, 255, 0.5)',
                                    whiteSpace: 'nowrap',
                                    transition: 'color 0.3s ease',
                                }}>
                                    {craMode === 'focused' ? 'CRA Focused' : craMode === 'extended' ? 'CRA Extended' : 'CRA Mode'}
                                </span>
                            </div>
                        </div>
                        {/* Sign out button - full width */}
                        <div
                            onClick={logout}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                padding: '8px 0',
                                borderRadius: '6px',
                                backgroundColor: 'rgba(255, 255, 255, 0.06)',
                                color: 'rgba(255, 255, 255, 0.5)',
                                cursor: 'pointer',
                                transition: 'background-color 0.2s ease, color 0.2s ease',
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.12)';
                                e.currentTarget.style.color = 'rgba(255, 255, 255, 0.8)';
                            }}
                            onMouseLeave={(e) => {
                                e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.06)';
                                e.currentTarget.style.color = 'rgba(255, 255, 255, 0.5)';
                            }}
                        >
                            <LogoutOutlined style={{ fontSize: '14px' }} />
                            <span style={{ fontSize: '12px' }}>Sign out</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Password Change Modal */}
            <Modal
                title="Change Password"
                open={isPasswordModalOpen}
                onOk={handlePasswordChange}
                onCancel={handleModalClose}
                okText="Change Password"
                okButtonProps={{ loading, disabled: loading }}
                cancelButtonProps={{ disabled: loading }}
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, color: '#374151' }}>
                            Current Password <span style={{ color: '#dc2626' }}>*</span>
                        </label>
                        <Input.Password
                            placeholder="Enter your current password"
                            value={currentPassword}
                            onChange={(e) => setCurrentPassword(e.target.value)}
                            size="large"
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, color: '#374151' }}>
                            New Password <span style={{ color: '#dc2626' }}>*</span>
                        </label>
                        <Input.Password
                            placeholder="Enter new password (min 8 characters)"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            size="large"
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, color: '#374151' }}>
                            Confirm New Password <span style={{ color: '#dc2626' }}>*</span>
                        </label>
                        <Input.Password
                            placeholder="Confirm new password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            size="large"
                            status={confirmPassword && newPassword !== confirmPassword ? 'error' : ''}
                        />
                        {confirmPassword && newPassword !== confirmPassword && (
                            <div style={{ color: '#dc2626', fontSize: '12px', marginTop: '4px' }}>
                                Passwords do not match
                            </div>
                        )}
                    </div>
                </div>
            </Modal>

            {/* Profile Modal */}
            <ProfileModal
                open={isProfileModalOpen}
                onClose={() => setIsProfileModalOpen(false)}
            />

            {/* AI Chatbot Drawer */}
            <ChatbotDrawer
                open={isChatbotOpen}
                onClose={() => setIsChatbotOpen(false)}
            />
        </div>
        </div>
    );
}
