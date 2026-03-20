// src/pages/HomePage.tsx
import { useEffect } from 'react';
import { MenuProps } from 'antd';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import InfoTitle from "../components/InfoTitle.tsx";
import { DashboardInfo } from "../constants/infoContent.tsx";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { DashboardOutlined } from "@ant-design/icons";
import useAuthStore from "../store/useAuthStore.ts";
import useOnboardingStore from "../store/useOnboardingStore.ts";
import useThemeStore from "../store/useThemeStore.ts";
import { SuperAdminDashboard, OrgAdminDashboard, OrgUserDashboard } from "./dashboards";
import OnboardingWizard from "../components/onboarding/OnboardingWizard.tsx";

const HomePage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const authStore = useAuthStore();
    const { theme } = useThemeStore();
    const userRole = authStore.getUserRole();
    const { checkOnboardingStatus, openWizard, onboardingStatus } = useOnboardingStore();

    // Also try to get role from JWT token as fallback
    const getRoleFromToken = (): string | null => {
        const token = authStore.token;
        if (!token) return null;
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.role || null;
        } catch {
            return null;
        }
    };

    const tokenRole = getRoleFromToken();
    const effectiveRole = userRole || tokenRole;

    // Normalize role for comparison (handle different formats)
    const normalizedRole = effectiveRole?.toLowerCase().replace(/[\s-]/g, '_') || '';

    // Debug logging - remove after verification
    console.log('Dashboard Debug:', {
        userFromStore: authStore.user,
        userRole,
        tokenRole,
        effectiveRole,
        normalizedRole,
        token: authStore.token ? 'exists' : 'null'
    });

    // Check onboarding status for admin users
    useEffect(() => {
        const isAdmin = normalizedRole.includes('super') ||
            normalizedRole === 'super_admin' ||
            normalizedRole.includes('org_admin') ||
            normalizedRole === 'admin';

        if (isAdmin && authStore.token) {
            checkOnboardingStatus().then(status => {
                // Open wizard if admin hasn't completed onboarding
                if (status && status.is_admin && !status.onboarding_completed) {
                    openWizard();
                }
            });
        }
    }, [normalizedRole, authStore.token, checkOnboardingStatus, openWizard]);

    const onClick: MenuProps['onClick'] = (e) => {
        console.log('click ', e);
    };

    // Role-based dashboard rendering
    const renderDashboard = () => {
        if (normalizedRole.includes('super') || normalizedRole === 'super_admin') {
            return <SuperAdminDashboard />;
        }
        if (normalizedRole.includes('org_admin') || normalizedRole === 'admin') {
            return <OrgAdminDashboard />;
        }
        return <OrgUserDashboard />;
    };

    // Get role-specific subtitle
    const getRoleSubtitle = () => {
        if (normalizedRole.includes('super') || normalizedRole === 'super_admin') {
            return 'System-wide overview across all organizations';
        }
        if (normalizedRole.includes('org_admin') || normalizedRole === 'admin') {
            return 'Organization management and team overview';
        }
        return 'Your personal compliance workspace';
    };

    // Get role display info
    const getRoleDisplay = () => {
        if (normalizedRole.includes('super') || normalizedRole === 'super_admin') {
            return { bg: '#fef2f2', color: '#dc2626', label: 'Super Admin' };
        }
        if (normalizedRole.includes('org_admin') || normalizedRole === 'admin') {
            return { bg: '#f5f3ff', color: '#8b5cf6', label: 'Org Admin' };
        }
        return { bg: '#f0fdfa', color: '#10b981', label: 'User' };
    };

    const roleDisplay = getRoleDisplay();

    return (
        <div>
            <div className={'page-parent'}>
                <Sidebar
                    onClick={onClick}
                    selectedKeys={menuHighlighting.selectedKeys}
                    openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange}
                />
                <div className={'page-content'}>
                    {/* Page Header */}
                    <div className="page-header" data-tour-id="page-header">
                        <div className="page-header-left">
                            <InfoTitle
                                title="Dashboard"
                                infoContent={DashboardInfo}
                                className="page-title"
                                icon={<DashboardOutlined style={{ color: 'var(--primary-navy)' }} />}
                            />
                            <span style={{
                                marginLeft: '12px',
                                padding: '4px 12px',
                                borderRadius: '12px',
                                fontSize: '12px',
                                fontWeight: 500,
                                backgroundColor: theme === 'dark-glass' ? 'rgba(255, 255, 255, 0.1)' : roleDisplay.bg,
                                color: theme === 'dark-glass' ? 'var(--primary-blue)' : roleDisplay.color,
                                border: theme === 'dark-glass' ? '1px solid rgba(255, 255, 255, 0.1)' : 'none',
                                backdropFilter: theme === 'dark-glass' ? 'blur(4px)' : 'none'
                            }}>
                                {roleDisplay.label}
                            </span>
                        </div>
                        <div className="page-header-right">
                            <span style={{ color: 'var(--text-medium-gray)', fontSize: '13px' }}>
                                {getRoleSubtitle()}
                            </span>
                        </div>
                    </div>

                    {/* Role-based Dashboard Content */}
                    {renderDashboard()}
                </div>
            </div>

            {/* Onboarding Wizard Modal */}
            <OnboardingWizard />
        </div>
    );
};

export default HomePage;
