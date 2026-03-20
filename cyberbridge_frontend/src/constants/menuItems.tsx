// src/constants/menuItems.tsx
import {
    DashboardOutlined,
    FormOutlined,
    AppstoreOutlined,
    CheckSquareOutlined,
    AlertOutlined,
    FileTextOutlined,
    FolderOutlined,
    FileProtectOutlined,
    MonitorOutlined,
    RadarChartOutlined,
    SafetyOutlined,
    SafetyCertificateOutlined,
    SettingOutlined,
    ToolOutlined,
    TeamOutlined,
    LinkOutlined,
    HistoryOutlined,
    CodeOutlined,
    BugOutlined,
    BookOutlined,
    QuestionCircleOutlined,
    SyncOutlined,
    DeploymentUnitOutlined,
    FileSearchOutlined,
    BankOutlined,
    UserOutlined,
    AuditOutlined,
    ScheduleOutlined,
    DatabaseOutlined,
    PartitionOutlined,
    ProfileOutlined,
    BulbOutlined,
    WarningOutlined,
    FundOutlined,
    FileDoneOutlined,
    NotificationOutlined,
    BarChartOutlined,
    SearchOutlined,
    EyeOutlined,
    EyeInvisibleOutlined,
    AimOutlined,
    GlobalOutlined,
    NodeIndexOutlined,
    ThunderboltOutlined,
    RobotOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import { Badge } from 'antd';
import useAuthStore from '../store/useAuthStore';
import useUserStore from '../store/useUserStore';
import useSettingsStore from '../store/useSettingsStore';
import useAuditNotificationStore from '../store/useAuditNotificationStore';
import useCRAModeStore from '../store/useCRAModeStore';
import useFrameworksStore from '../store/useFrameworksStore';
import {Link} from "wouter";

export type MenuItem = Required<MenuProps>['items'][number];

export const MenuItems = () => {
    const { isAuthenticated } = useAuthStore();
    const { current_user } = useUserStore();
    const { canUserAccessScanners, superAdminFocusedMode } = useSettingsStore();
    const { unreadCount } = useAuditNotificationStore();
    const { craMode } = useCRAModeStore();
    const { frameworks } = useFrameworksStore();

    const items: MenuItem[] = [];

    // Check if super admin focused mode is enabled for super_admin
    const isSuperAdminFocused = current_user?.role_name === 'super_admin' && superAdminFocusedMode;

    // If super admin focused mode is enabled, show simplified menu
    if (isSuperAdminFocused) {
        // Dashboard
        items.push({
            key: 'dashboard',
            label: <Link href="/home"><span data-tour-id="sidebar-dashboard">Dashboard</span></Link>,
            icon: <DashboardOutlined />
        });

        // Frameworks with all submenu items
        items.push({
            key: 'frameworks',
            label: <span data-tour-id="sidebar-frameworks">Frameworks</span>,
            icon: <AppstoreOutlined />,
            children: [
                {
                    key: 'frameworks.compliance_advisor',
                    label: <Link href="/compliance_advisor">Compliance Advisor</Link>,
                    icon: <BulbOutlined />
                },
                {
                    key: 'frameworks.objectives',
                    label: <Link href="/objectives_checklist">Objectives</Link>,
                    icon: <CheckSquareOutlined />
                },
                {
                    key: 'frameworks.config',
                    label: 'Configuration',
                    icon: <ToolOutlined />,
                    children: [
                        {
                            key: 'frameworks.management',
                            label: <Link href="/framework_management">Manage Frameworks</Link>,
                            icon: <AppstoreOutlined />
                        },
                        {
                            key: 'frameworks.chapters',
                            label: <Link href="/chapters_objectives">Chapters & Objectives</Link>,
                            icon: <BookOutlined />
                        },
                        {
                            key: 'frameworks.questions',
                            label: <Link href="/framework_questions">Framework Questions</Link>,
                            icon: <QuestionCircleOutlined />
                        },
                        {
                            key: 'frameworks.updates',
                            label: <Link href="/framework_updates">Framework Updates</Link>,
                            icon: <SyncOutlined />
                        }
                    ]
                }
            ]
        });

        // Organizations (top-level)
        items.push({
            key: 'admin.organizations',
            label: <Link href="/organizations">Organizations</Link>,
            icon: <BankOutlined />
        });

        // Users (top-level)
        items.push({
            key: 'admin.users',
            label: <Link href="/users">Users</Link>,
            icon: <UserOutlined />
        });

        // Activity Log (top-level)
        items.push({
            key: 'admin.history',
            label: <Link href="/history">Activity Log</Link>,
            icon: <HistoryOutlined />
        });

        // Correlations (top-level)
        items.push({
            key: 'admin.correlations',
            label: <Link href="/correlations">Correlations</Link>,
            icon: <LinkOutlined />
        });

        // Background Jobs (top-level)
        items.push({
            key: 'admin.background-jobs',
            label: <Link href="/background-jobs">Background Jobs</Link>,
            icon: <ScheduleOutlined />
        });

        // System Settings (top-level)
        items.push({
            key: 'admin.config',
            label: <Link href="/settings">System Settings</Link>,
            icon: <SettingOutlined />
        });

        // Documentation
        items.push({
            key: 'documentation',
            label: <Link href="/documentation">Documentation</Link>,
            icon: <BookOutlined />
        });

        // AI Assistant
        items.push({
            key: 'ai-assistant',
            label: 'AI Assistant',
            icon: <RobotOutlined />
        });

        return items;
    }

    // CRA Mode - simplified menu showing only CRA-relevant pages
    const craFrameworkExists = frameworks.some(f => f.name.toLowerCase() === 'cra');

    if (craMode === 'focused' && craFrameworkExists) {
        // Dashboard
        items.push({
            key: 'dashboard',
            label: <Link href="/home"><span data-tour-id="sidebar-dashboard">Dashboard</span></Link>,
            icon: <DashboardOutlined />
        });

        // Assessments (parent menu with children)
        items.push({
            key: 'assessments',
            label: <span data-tour-id="sidebar-assessments">Assessments</span>,
            icon: <FormOutlined />,
            children: [
                {
                    key: 'assessments.main',
                    label: <Link href="/assessments">Assessments</Link>,
                    icon: <FormOutlined />
                },
                {
                    key: 'assessments.cra_scope',
                    label: <Link href="/cra-scope-assessment">CRA Scope Assessment</Link>,
                    icon: <FileSearchOutlined />
                },
                {
                    key: 'assessments.cra_readiness',
                    label: <Link href="/cra-readiness-assessment">CRA Readiness Assessment</Link>,
                    icon: <SafetyCertificateOutlined />
                }
            ]
        });

        // Frameworks - trimmed: Objectives (all) + Configuration with Chapters & Objectives (admin)
        const craFrameworksChildren: MenuItem[] = [];

        craFrameworksChildren.push({
            key: 'frameworks.objectives',
            label: <Link href="/objectives_checklist">Objectives</Link>,
            icon: <CheckSquareOutlined />
        });

        if (isAuthenticated && current_user && (current_user.role_name === 'super_admin' || current_user.role_name === 'org_admin')) {
            craFrameworksChildren.push({
                key: 'frameworks.config',
                label: 'Configuration',
                icon: <ToolOutlined />,
                children: [
                    {
                        key: 'frameworks.chapters',
                        label: <Link href="/chapters_objectives">Chapters & Objectives</Link>,
                        icon: <BookOutlined />
                    }
                ]
            });
        }

        items.push({
            key: 'frameworks',
            label: <span data-tour-id="sidebar-frameworks">Frameworks</span>,
            icon: <AppstoreOutlined />,
            children: craFrameworksChildren
        });

        // Assets / Products
        items.push({
            key: 'assets',
            label: <span data-tour-id="sidebar-assets">Assets / Products</span>,
            icon: <DatabaseOutlined />,
            children: [
                {
                    key: 'assets.management',
                    label: <Link href="/assets">Manage Assets</Link>,
                    icon: <DatabaseOutlined />
                },
                {
                    key: 'assets.ce_marking',
                    label: <Link href="/ce_marking_checklist">CE Marking Checklist</Link>,
                    icon: <SafetyCertificateOutlined />
                }
            ]
        });

        // Risks
        items.push({
            key: 'risks',
            label: 'Risks',
            icon: <AlertOutlined />,
            children: [
                {
                    key: 'risks.register',
                    label: <Link href="/risk_registration">Risk Register</Link>,
                    icon: <FileTextOutlined />
                },
                {
                    key: 'risks.assessment',
                    label: <Link href="/risk_assessment">Risk Assessment</Link>,
                    icon: <FundOutlined />
                },
                {
                    key: 'risks.incidents',
                    label: <Link href="/incidents">Incident Registration</Link>,
                    icon: <WarningOutlined />
                },
                {
                    key: 'risks.advisories',
                    label: <Link href="/advisories">Security Advisories</Link>,
                    icon: <NotificationOutlined />
                }
            ]
        });

        // Controls
        items.push({
            key: 'controls',
            label: 'Controls',
            icon: <SafetyCertificateOutlined />,
            children: [
                {
                    key: 'controls.register',
                    label: <Link href="/control_registration">Control Register</Link>,
                    icon: <FileTextOutlined />
                },
                {
                    key: 'controls.library',
                    label: <Link href="/controls_library">Controls Library</Link>,
                    icon: <DatabaseOutlined />
                }
            ]
        });

        // Documents
        items.push({
            key: 'documents',
            label: 'Documents',
            icon: <FolderOutlined />,
            children: [
                {
                    key: 'documents.policies',
                    label: <Link href="/policies_registration">Policies</Link>,
                    icon: <FileProtectOutlined />
                },
                {
                    key: 'documents.architecture',
                    label: <Link href="/architecture">Architecture</Link>,
                    icon: <DeploymentUnitOutlined />
                },
                {
                    key: 'documents.evidence',
                    label: <Link href="/evidence">Evidence</Link>,
                    icon: <FileSearchOutlined />
                },
                {
                    key: 'documents.eu_doc',
                    label: <Link href="/eu_declaration_of_conformity">EU Declaration of Conformity</Link>,
                    icon: <FileDoneOutlined />
                },
                {
                    key: 'documents.technical_file',
                    label: 'Technical File',
                    icon: <MonitorOutlined />,
                    children: [
                        {
                            key: 'documents.patch_support',
                            label: <Link href="/patch_support_policy">Patch & Support Policy</Link>,
                            icon: <ToolOutlined />
                        },
                        {
                            key: 'documents.vuln_disclosure',
                            label: <Link href="/vulnerability_disclosure_policy">Vulnerability Disclosure</Link>,
                            icon: <AlertOutlined />
                        },
                        {
                            key: 'documents.sbom_mgmt',
                            label: <Link href="/sbom_management">SBOM Management</Link>,
                            icon: <ProfileOutlined />
                        },
                        {
                            key: 'documents.sdlc_evidence',
                            label: <Link href="/secure_sdlc_evidence">Secure SDLC Evidence</Link>,
                            icon: <SafetyOutlined />
                        },
                        {
                            key: 'documents.security_design',
                            label: <Link href="/security_design_documentation">Security Design</Link>,
                            icon: <DeploymentUnitOutlined />
                        },
                        {
                            key: 'documents.dependency_policy',
                            label: <Link href="/dependency_policy">Dependency Policy</Link>,
                            icon: <BugOutlined />
                        }
                    ]
                }
            ]
        });

        // Compliance Chain
        items.push({
            key: 'compliance-chain',
            label: 'Compliance Chain',
            icon: <LinkOutlined />,
            children: [
                {
                    key: 'compliance-chain.links',
                    label: <Link href="/compliance_chain_links">All Links</Link>,
                    icon: <LinkOutlined />
                },
                {
                    key: 'compliance-chain.map',
                    label: <Link href="/compliance_chain_map">Map</Link>,
                    icon: <PartitionOutlined />
                },
                {
                    key: 'compliance-chain.gap-analysis',
                    label: <Link href="/gap_analysis">Gap Analysis</Link>,
                    icon: <BarChartOutlined />
                }
            ]
        });

        // Security Tools (if accessible)
        if (current_user && current_user.organisation_domain) {
            const userHasAccess = canUserAccessScanners(current_user.organisation_domain);

            if (userHasAccess) {
                items.push({
                    key: 'monitoring',
                    label: <span data-tour-id="sidebar-monitoring">Security Tools</span>,
                    icon: <SafetyOutlined />,
                    children: [
                        {
                            key: 'monitoring.security_scanners',
                            label: <Link href="/security_scanners">Security Scanners</Link>,
                            icon: <RadarChartOutlined />
                        },
                        {
                            key: 'monitoring.code_analysis',
                            label: <Link href="/code_analysis">Code Analysis</Link>,
                            icon: <CodeOutlined />
                        },
                        {
                            key: 'monitoring.dependency_check',
                            label: <Link href="/dependency_check">Dependency Check</Link>,
                            icon: <BugOutlined />
                        },
                        {
                            key: 'monitoring.sbom',
                            label: <Link href="/sbom_generator">SBOM Generator</Link>,
                            icon: <ProfileOutlined />
                        },
                        {
                            key: 'monitoring.scan_findings',
                            label: <Link href="/scan_findings">Scan Findings</Link>,
                            icon: <FileSearchOutlined />
                        }
                    ]
                });
            }
        }

        // Threat Intelligence (CTI Dashboard) - CRA mode
        items.push({
            key: 'threat-intel',
            label: <span data-tour-id="sidebar-threat-intel">Threat Intelligence</span>,
            icon: <ThunderboltOutlined />,
            children: [
                {
                    key: 'threat-intel.overview',
                    label: <Link href="/cti/overview">Overview</Link>,
                    icon: <EyeOutlined />
                },
                {
                    key: 'threat-intel.mitre',
                    label: <Link href="/cti/threat-intel">MITRE ATT&CK</Link>,
                    icon: <AimOutlined />
                },
                {
                    key: 'threat-intel.network',
                    label: <Link href="/cti/network">Network Scan</Link>,
                    icon: <GlobalOutlined />
                },
                {
                    key: 'threat-intel.web-vulns',
                    label: <Link href="/cti/web-vulns">Web Vulnerabilities</Link>,
                    icon: <BugOutlined />
                },
                {
                    key: 'threat-intel.code-analysis',
                    label: <Link href="/cti/code-analysis">Code Analysis</Link>,
                    icon: <CodeOutlined />
                },
                {
                    key: 'threat-intel.dependencies',
                    label: <Link href="/cti/dependencies">Dependencies</Link>,
                    icon: <NodeIndexOutlined />
                }
            ]
        });

        // Dark Web Intelligence
        items.push({
            key: 'dark-web',
            label: 'Dark Web Intelligence',
            icon: <EyeInvisibleOutlined />,
            children: [
                {
                    key: 'dark-web.dashboard',
                    label: <Link href="/dark-web/dashboard">Dashboard</Link>,
                    icon: <DashboardOutlined />
                },
                {
                    key: 'dark-web.scans',
                    label: <Link href="/dark-web/scans">Scans</Link>,
                    icon: <SearchOutlined />
                },
                {
                    key: 'dark-web.reports',
                    label: <Link href="/dark-web/reports">Reports</Link>,
                    icon: <FileTextOutlined />
                },
                ...(isAuthenticated && current_user && (current_user.role_name === 'super_admin' || current_user.role_name === 'org_admin') ? [{
                    key: 'dark-web.settings',
                    label: <Link href="/dark-web/settings">Settings</Link>,
                    icon: <SettingOutlined />
                }] : [])
            ]
        });

        // Audit Engagements (admin only)
        if (isAuthenticated && current_user && (current_user.role_name === 'super_admin' || current_user.role_name === 'org_admin')) {
            items.push({
                key: 'audit-engagements',
                label: (
                    <Link href="/audit-engagements" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                        <span>Audit Engagements</span>
                        {unreadCount > 0 && (
                            <span style={{
                                backgroundColor: '#faad14',
                                color: '#000',
                                fontSize: 10,
                                fontWeight: 600,
                                minWidth: 18,
                                height: 18,
                                borderRadius: 9,
                                display: 'inline-flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                padding: '0 5px',
                                marginLeft: 8
                            }}>
                                {unreadCount > 99 ? '99+' : unreadCount}
                            </span>
                        )}
                    </Link>
                ),
                icon: <AuditOutlined />
            });
        }

        // Administration (admin only) - still visible in CRA mode for super_admin and org_admin
        if (isAuthenticated && current_user && (current_user.role_name === 'super_admin' || current_user.role_name === 'org_admin')) {
            const adminChildren: MenuItem[] = [];

            if (current_user.role_name === 'super_admin') {
                adminChildren.push({ key: 'admin.organizations', label: <Link href="/organizations">Organizations</Link>, icon: <BankOutlined /> });
            } else {
                adminChildren.push({ key: 'admin.organizations', label: <Link href="/organizations">Organization Settings</Link>, icon: <BankOutlined /> });
            }

            adminChildren.push({ key: 'admin.users', label: <Link href="/users">Users</Link>, icon: <UserOutlined /> });
            adminChildren.push({ key: 'admin.history', label: <Link href="/history">Activity Log</Link>, icon: <HistoryOutlined /> });
            adminChildren.push({ key: 'admin.correlations', label: <Link href="/correlations">Correlations</Link>, icon: <LinkOutlined /> });
            adminChildren.push({ key: 'admin.background-jobs', label: <Link href="/background-jobs">Background Jobs</Link>, icon: <ScheduleOutlined /> });
            adminChildren.push({ key: 'admin.config', label: <Link href="/settings">System Settings</Link>, icon: <SettingOutlined /> });

            if (adminChildren.length > 0) {
                items.push({
                    key: 'admin',
                    label: 'Administration',
                    icon: <SettingOutlined />,
                    children: adminChildren
                });
            }
        }

        // Documentation
        items.push({
            key: 'documentation',
            label: <Link href="/documentation">Documentation</Link>,
            icon: <BookOutlined />
        });

        // AI Assistant
        items.push({
            key: 'ai-assistant',
            label: 'AI Assistant',
            icon: <RobotOutlined />
        });

        return items;
    }

    // Normal menu for non-focused mode or non-super-admin users

    // 1. Dashboard (standalone)
    items.push({
        key: 'dashboard',
        label: <Link href="/home"><span data-tour-id="sidebar-dashboard">Dashboard</span></Link>,
        icon: <DashboardOutlined />
    });

    // 2. Assessments (parent menu with children)
    items.push({
        key: 'assessments',
        label: <span data-tour-id="sidebar-assessments">Assessments</span>,
        icon: <FormOutlined />,
        children: [
            {
                key: 'assessments.main',
                label: <Link href="/assessments">Assessments</Link>,
                icon: <FormOutlined />
            },
            {
                key: 'assessments.cra_scope',
                label: <Link href="/cra-scope-assessment">CRA Scope Assessment</Link>,
                icon: <FileSearchOutlined />
            },
            {
                key: 'assessments.cra_readiness',
                label: <Link href="/cra-readiness-assessment">CRA Readiness Assessment</Link>,
                icon: <SafetyCertificateOutlined />
            }
        ]
    });

    // 3. Frameworks with Objectives submenu (admin only for framework management)
    const frameworksChildren: MenuItem[] = [];

    if (isAuthenticated && current_user && (current_user.role_name === 'super_admin' || current_user.role_name === 'org_admin')) {
        frameworksChildren.push({
            key: 'frameworks.compliance_advisor',
            label: <Link href="/compliance_advisor">Compliance Advisor</Link>,
            icon: <BulbOutlined />
        });
    }

    frameworksChildren.push({
        key: 'frameworks.objectives',
        label: <Link href="/objectives_checklist">Objectives</Link>,
        icon: <CheckSquareOutlined />
    });

    if (isAuthenticated && current_user && (current_user.role_name === 'super_admin' || current_user.role_name === 'org_admin')) {
        frameworksChildren.push({
            key: 'frameworks.config',
            label: 'Configuration',
            icon: <ToolOutlined />,
            children: [
                {
                    key: 'frameworks.management',
                    label: <Link href="/framework_management">Manage Frameworks</Link>,
                    icon: <AppstoreOutlined />
                },
                {
                    key: 'frameworks.chapters',
                    label: <Link href="/chapters_objectives">Chapters & Objectives</Link>,
                    icon: <BookOutlined />
                },
                {
                    key: 'frameworks.questions',
                    label: <Link href="/framework_questions">Framework Questions</Link>,
                    icon: <QuestionCircleOutlined />
                },
                {
                    key: 'frameworks.updates',
                    label: <Link href="/framework_updates">Framework Updates</Link>,
                    icon: <SyncOutlined />
                }
            ]
        });
    }

    items.push({
        key: 'frameworks',
        label: <span data-tour-id="sidebar-frameworks">Frameworks</span>,
        icon: <AppstoreOutlined />,
        children: frameworksChildren
    });

    // 4. Assets / Products with Manage Assets submenu
    items.push({
        key: 'assets',
        label: <span data-tour-id="sidebar-assets">Assets / Products</span>,
        icon: <DatabaseOutlined />,
        children: [
            {
                key: 'assets.management',
                label: <Link href="/assets">Manage Assets</Link>,
                icon: <DatabaseOutlined />
            },
            ...(craMode === 'extended' ? [{
                key: 'assets.ce_marking',
                label: <Link href="/ce_marking_checklist">CE Marking Checklist</Link>,
                icon: <SafetyCertificateOutlined />
            }] : [])
        ]
    });

    // 5. Risks with Risk Register and Incident Registration submenu
    items.push({
        key: 'risks',
        label: 'Risks',
        icon: <AlertOutlined />,
        children: [
            {
                key: 'risks.register',
                label: <Link href="/risk_registration">Risk Register</Link>,
                icon: <FileTextOutlined />
            },
            {
                key: 'risks.assessment',
                label: <Link href="/risk_assessment">Risk Assessment</Link>,
                icon: <FundOutlined />
            },
            {
                key: 'risks.incidents',
                label: <Link href="/incidents">Incident Registration</Link>,
                icon: <WarningOutlined />
            },
            {
                key: 'risks.advisories',
                label: <Link href="/advisories">Security Advisories</Link>,
                icon: <NotificationOutlined />
            }
        ]
    });

    // 5.5. Controls with Control Register and Controls Library submenu
    items.push({
        key: 'controls',
        label: 'Controls',
        icon: <SafetyCertificateOutlined />,
        children: [
            {
                key: 'controls.register',
                label: <Link href="/control_registration">Control Register</Link>,
                icon: <FileTextOutlined />
            },
            {
                key: 'controls.library',
                label: <Link href="/controls_library">Controls Library</Link>,
                icon: <DatabaseOutlined />
            }
        ]
    });

    // 6. Documents with Policies, Architecture, and Evidence submenu
    items.push({
        key: 'documents',
        label: 'Documents',
        icon: <FolderOutlined />,
        children: [
            {
                key: 'documents.policies',
                label: <Link href="/policies_registration">Policies</Link>,
                icon: <FileProtectOutlined />
            },
            {
                key: 'documents.architecture',
                label: <Link href="/architecture">Architecture</Link>,
                icon: <DeploymentUnitOutlined />
            },
            {
                key: 'documents.evidence',
                label: <Link href="/evidence">Evidence</Link>,
                icon: <FileSearchOutlined />
            },
            ...(craMode === 'extended' ? [{
                key: 'documents.eu_doc',
                label: <Link href="/eu_declaration_of_conformity">EU Declaration of Conformity</Link>,
                icon: <FileDoneOutlined />
            }] : []),
            ...(craMode === 'extended' ? [{
                key: 'documents.technical_file',
                label: 'Technical File',
                icon: <MonitorOutlined />,
                children: [
                    {
                        key: 'documents.patch_support',
                        label: <Link href="/patch_support_policy">Patch & Support Policy</Link>,
                        icon: <ToolOutlined />
                    },
                    {
                        key: 'documents.vuln_disclosure',
                        label: <Link href="/vulnerability_disclosure_policy">Vulnerability Disclosure</Link>,
                        icon: <AlertOutlined />
                    },
                    {
                        key: 'documents.sbom_mgmt',
                        label: <Link href="/sbom_management">SBOM Management</Link>,
                        icon: <ProfileOutlined />
                    },
                    {
                        key: 'documents.sdlc_evidence',
                        label: <Link href="/secure_sdlc_evidence">Secure SDLC Evidence</Link>,
                        icon: <SafetyOutlined />
                    },
                    {
                        key: 'documents.security_design',
                        label: <Link href="/security_design_documentation">Security Design</Link>,
                        icon: <DeploymentUnitOutlined />
                    },
                    {
                        key: 'documents.dependency_policy',
                        label: <Link href="/dependency_policy">Dependency Policy</Link>,
                        icon: <BugOutlined />
                    }
                ]
            }] : [])
        ]
    });

    // 6.5. Compliance Chain with All Links and Map submenu
    items.push({
        key: 'compliance-chain',
        label: 'Compliance Chain',
        icon: <LinkOutlined />,
        children: [
            {
                key: 'compliance-chain.links',
                label: <Link href="/compliance_chain_links">All Links</Link>,
                icon: <LinkOutlined />
            },
            {
                key: 'compliance-chain.map',
                label: <Link href="/compliance_chain_map">Map</Link>,
                icon: <PartitionOutlined />
            },
            {
                key: 'compliance-chain.gap-analysis',
                label: <Link href="/gap_analysis">Gap Analysis</Link>,
                icon: <BarChartOutlined />
            }
        ]
    });

    // 6. Security Tools with Security Scanners, Code Analysis, and Dependency Check (only if user has access)
    if (current_user && current_user.organisation_domain) {
        const userHasAccess = canUserAccessScanners(current_user.organisation_domain);

        if (userHasAccess) {
            items.push({
                key: 'monitoring',
                label: <span data-tour-id="sidebar-monitoring">Security Tools</span>,
                icon: <SafetyOutlined />,
                children: [
                    {
                        key: 'monitoring.security_scanners',
                        label: <Link href="/security_scanners">Security Scanners</Link>,
                        icon: <RadarChartOutlined />
                    },
                    {
                        key: 'monitoring.code_analysis',
                        label: <Link href="/code_analysis">Code Analysis</Link>,
                        icon: <CodeOutlined />
                    },
                    {
                        key: 'monitoring.dependency_check',
                        label: <Link href="/dependency_check">Dependency Check</Link>,
                        icon: <BugOutlined />
                    },
                    {
                        key: 'monitoring.sbom',
                        label: <Link href="/sbom_generator">SBOM Generator</Link>,
                        icon: <ProfileOutlined />
                    },
                    {
                        key: 'monitoring.scan_findings',
                        label: <Link href="/scan_findings">Scan Findings</Link>,
                        icon: <FileSearchOutlined />
                    }
                ]
            });
        }
    }

    // Threat Intelligence (CTI Dashboard)
    items.push({
        key: 'threat-intel',
        label: <span data-tour-id="sidebar-threat-intel">Threat Intelligence</span>,
        icon: <ThunderboltOutlined />,
        children: [
            {
                key: 'threat-intel.overview',
                label: <Link href="/cti/overview">Overview</Link>,
                icon: <EyeOutlined />
            },
            {
                key: 'threat-intel.mitre',
                label: <Link href="/cti/threat-intel">MITRE ATT&CK</Link>,
                icon: <AimOutlined />
            },
            {
                key: 'threat-intel.network',
                label: <Link href="/cti/network">Network Scan</Link>,
                icon: <GlobalOutlined />
            },
            {
                key: 'threat-intel.web-vulns',
                label: <Link href="/cti/web-vulns">Web Vulnerabilities</Link>,
                icon: <BugOutlined />
            },
            {
                key: 'threat-intel.code-analysis',
                label: <Link href="/cti/code-analysis">Code Analysis</Link>,
                icon: <CodeOutlined />
            },
            {
                key: 'threat-intel.dependencies',
                label: <Link href="/cti/dependencies">Dependencies</Link>,
                icon: <NodeIndexOutlined />
            }
        ]
    });

    // Dark Web Intelligence
    items.push({
        key: 'dark-web',
        label: 'Dark Web Intelligence',
        icon: <EyeInvisibleOutlined />,
        children: [
            {
                key: 'dark-web.dashboard',
                label: <Link href="/dark-web/dashboard">Dashboard</Link>,
                icon: <DashboardOutlined />
            },
            {
                key: 'dark-web.scans',
                label: <Link href="/dark-web/scans">Scans</Link>,
                icon: <SearchOutlined />
            },
            {
                key: 'dark-web.reports',
                label: <Link href="/dark-web/reports">Reports</Link>,
                icon: <FileTextOutlined />
            },
            ...(isAuthenticated && current_user && (current_user.role_name === 'super_admin' || current_user.role_name === 'org_admin') ? [{
                key: 'dark-web.settings',
                label: <Link href="/dark-web/settings">Settings</Link>,
                icon: <SettingOutlined />
            }] : [])
        ]
    });

    // 7. Audit Engagements (org_admin and super_admin only)
    if (isAuthenticated && current_user && (current_user.role_name === 'super_admin' || current_user.role_name === 'org_admin')) {
        items.push({
            key: 'audit-engagements',
            label: (
                <Link href="/audit-engagements" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
                    <span>Audit Engagements</span>
                    {unreadCount > 0 && (
                        <span style={{
                            backgroundColor: '#faad14',
                            color: '#000',
                            fontSize: 10,
                            fontWeight: 600,
                            minWidth: 18,
                            height: 18,
                            borderRadius: 9,
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: '0 5px',
                            marginLeft: 8
                        }}>
                            {unreadCount > 99 ? '99+' : unreadCount}
                        </span>
                    )}
                </Link>
            ),
            icon: <AuditOutlined />
        });
    }

    // 8. Administration (admin only - combines former Settings and Workflow)
    if (isAuthenticated && current_user && (current_user.role_name === 'super_admin' || current_user.role_name === 'org_admin')) {
        const adminChildren: MenuItem[] = [];

        // Super admin sees Organizations, org_admin sees Organization Settings
        if (current_user.role_name === 'super_admin') {
            adminChildren.push({ key: 'admin.organizations', label: <Link href="/organizations">Organizations</Link>, icon: <BankOutlined /> });
        } else {
            adminChildren.push({ key: 'admin.organizations', label: <Link href="/organizations">Organization Settings</Link>, icon: <BankOutlined /> });
        }

        adminChildren.push({ key: 'admin.users', label: <Link href="/users">Users</Link>, icon: <UserOutlined /> });
        adminChildren.push({ key: 'admin.history', label: <Link href="/history">Activity Log</Link>, icon: <HistoryOutlined /> });
        adminChildren.push({ key: 'admin.correlations', label: <Link href="/correlations">Correlations</Link>, icon: <LinkOutlined /> });
        adminChildren.push({ key: 'admin.background-jobs', label: <Link href="/background-jobs">Background Jobs</Link>, icon: <ScheduleOutlined /> });

        // Both super_admin and org_admin see System Settings
        adminChildren.push({ key: 'admin.config', label: <Link href="/settings">System Settings</Link>, icon: <SettingOutlined /> });

        if (adminChildren.length > 0) {
            items.push({
                key: 'admin',
                label: 'Administration',
                icon: <SettingOutlined />,
                children: adminChildren
            });
        }
    }

    // Documentation
    items.push({
        key: 'documentation',
        label: <Link href="/documentation">Documentation</Link>,
        icon: <BookOutlined />
    });

    // AI Assistant
    items.push({
        key: 'ai-assistant',
        label: 'AI Assistant',
        icon: <RobotOutlined />
    });

    return items;
};
