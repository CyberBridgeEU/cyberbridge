// src/utils/iconUtils.tsx
import React from 'react';
import {
    CloudOutlined,
    UserOutlined,
    DatabaseOutlined,
    TableOutlined,
    MailOutlined,
    TeamOutlined,
    LaptopOutlined,
    MobileOutlined,
    GlobalOutlined,
    DesktopOutlined,
    FolderOutlined,
    BankOutlined,
    SettingOutlined,
    CloudServerOutlined,
    HddOutlined,
    CodeOutlined,
    GithubOutlined,
    CloudUploadOutlined,
    QuestionCircleOutlined,
    WifiOutlined,
    SafetyOutlined,
    ApiOutlined,
    AppstoreOutlined,
    AuditOutlined,
    BugOutlined,
    ContainerOutlined,
    CreditCardOutlined,
    FileProtectOutlined,
    KeyOutlined,
    LockOutlined,
    PrinterOutlined,
    RobotOutlined,
    ShopOutlined,
    ToolOutlined,
    TrophyOutlined,
    VideoCameraOutlined,
} from '@ant-design/icons';

// Map of icon names to icon components
const iconMap: Record<string, React.ComponentType> = {
    CloudOutlined,
    UserOutlined,
    DatabaseOutlined,
    TableOutlined,
    MailOutlined,
    TeamOutlined,
    LaptopOutlined,
    MobileOutlined,
    GlobalOutlined,
    DesktopOutlined,
    FolderOutlined,
    BankOutlined,
    SettingOutlined,
    CloudServerOutlined,
    HddOutlined,
    CodeOutlined,
    GithubOutlined,
    CloudUploadOutlined,
    QuestionCircleOutlined,
    WifiOutlined,
    SafetyOutlined,
    ApiOutlined,
    AppstoreOutlined,
    AuditOutlined,
    BugOutlined,
    ContainerOutlined,
    CreditCardOutlined,
    FileProtectOutlined,
    KeyOutlined,
    LockOutlined,
    PrinterOutlined,
    RobotOutlined,
    ShopOutlined,
    ToolOutlined,
    TrophyOutlined,
    VideoCameraOutlined,
};

/**
 * Get an icon component by its name
 * @param iconName - Name of the Ant Design icon (e.g., "CloudOutlined")
 * @returns The icon component or a default DatabaseOutlined if not found
 */
export const getIconByName = (iconName: string | null | undefined): React.ComponentType => {
    if (!iconName || !iconMap[iconName]) {
        return DatabaseOutlined;
    }
    return iconMap[iconName];
};

/**
 * Render an icon element by its name
 * @param iconName - Name of the Ant Design icon
 * @param style - Optional style object to apply to the icon
 * @returns The rendered icon element
 */
export const renderIcon = (iconName: string | null | undefined, style?: React.CSSProperties): React.ReactElement => {
    const IconComponent = getIconByName(iconName);
    return <IconComponent style={style} />;
};

// List of available icons for selection in forms
export const availableIcons = [
    { value: 'CloudOutlined', label: 'Cloud', icon: CloudOutlined },
    { value: 'UserOutlined', label: 'User', icon: UserOutlined },
    { value: 'DatabaseOutlined', label: 'Database', icon: DatabaseOutlined },
    { value: 'TableOutlined', label: 'Table', icon: TableOutlined },
    { value: 'MailOutlined', label: 'Mail', icon: MailOutlined },
    { value: 'TeamOutlined', label: 'Team', icon: TeamOutlined },
    { value: 'LaptopOutlined', label: 'Laptop', icon: LaptopOutlined },
    { value: 'MobileOutlined', label: 'Mobile', icon: MobileOutlined },
    { value: 'GlobalOutlined', label: 'Global', icon: GlobalOutlined },
    { value: 'DesktopOutlined', label: 'Desktop', icon: DesktopOutlined },
    { value: 'FolderOutlined', label: 'Folder', icon: FolderOutlined },
    { value: 'BankOutlined', label: 'Building', icon: BankOutlined },
    { value: 'SettingOutlined', label: 'Settings', icon: SettingOutlined },
    { value: 'CloudServerOutlined', label: 'Cloud Server', icon: CloudServerOutlined },
    { value: 'HddOutlined', label: 'Server/HDD', icon: HddOutlined },
    { value: 'CodeOutlined', label: 'Code', icon: CodeOutlined },
    { value: 'GithubOutlined', label: 'GitHub', icon: GithubOutlined },
    { value: 'CloudUploadOutlined', label: 'Cloud Upload', icon: CloudUploadOutlined },
    { value: 'QuestionCircleOutlined', label: 'Question', icon: QuestionCircleOutlined },
    { value: 'WifiOutlined', label: 'WiFi', icon: WifiOutlined },
    { value: 'SafetyOutlined', label: 'Security', icon: SafetyOutlined },
    { value: 'ApiOutlined', label: 'API', icon: ApiOutlined },
    { value: 'AppstoreOutlined', label: 'Apps', icon: AppstoreOutlined },
    { value: 'AuditOutlined', label: 'Audit', icon: AuditOutlined },
    { value: 'BugOutlined', label: 'Bug', icon: BugOutlined },
    { value: 'ContainerOutlined', label: 'Container', icon: ContainerOutlined },
    { value: 'CreditCardOutlined', label: 'Credit Card', icon: CreditCardOutlined },
    { value: 'FileProtectOutlined', label: 'Protected File', icon: FileProtectOutlined },
    { value: 'KeyOutlined', label: 'Key', icon: KeyOutlined },
    { value: 'LockOutlined', label: 'Lock', icon: LockOutlined },
    { value: 'PrinterOutlined', label: 'Printer', icon: PrinterOutlined },
    { value: 'RobotOutlined', label: 'Robot', icon: RobotOutlined },
    { value: 'ShopOutlined', label: 'Shop', icon: ShopOutlined },
    { value: 'ToolOutlined', label: 'Tools', icon: ToolOutlined },
    { value: 'TrophyOutlined', label: 'Trophy', icon: TrophyOutlined },
    { value: 'VideoCameraOutlined', label: 'Camera', icon: VideoCameraOutlined },
];

export default iconMap;
