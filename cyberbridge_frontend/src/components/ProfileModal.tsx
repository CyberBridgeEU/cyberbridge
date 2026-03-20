// src/components/ProfileModal.tsx
import { useEffect, useState, useRef } from "react";
import { Modal, notification, Input, Button, Select, Avatar, Tabs } from 'antd';
import {
    UserOutlined,
    MailOutlined,
    SafetyOutlined,
    PhoneOutlined,
    IdcardOutlined,
    TeamOutlined,
    BellOutlined,
    LockOutlined,
    CameraOutlined,
    SaveOutlined,
    DeleteOutlined,
    BgColorsOutlined,
    CheckCircleFilled
} from '@ant-design/icons';
import useAuthStore from "../store/useAuthStore.ts";
import useThemeStore from "../store/useThemeStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

// Common timezones
const TIMEZONES = [
    { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
    { value: 'Europe/London', label: 'Europe/London (GMT/BST)' },
    { value: 'Europe/Paris', label: 'Europe/Paris (CET/CEST)' },
    { value: 'Europe/Berlin', label: 'Europe/Berlin (CET/CEST)' },
    { value: 'Europe/Athens', label: 'Europe/Athens (EET/EEST)' },
    { value: 'America/New_York', label: 'America/New York (EST/EDT)' },
    { value: 'America/Chicago', label: 'America/Chicago (CST/CDT)' },
    { value: 'America/Denver', label: 'America/Denver (MST/MDT)' },
    { value: 'America/Los_Angeles', label: 'America/Los Angeles (PST/PDT)' },
    { value: 'Asia/Tokyo', label: 'Asia/Tokyo (JST)' },
    { value: 'Asia/Shanghai', label: 'Asia/Shanghai (CST)' },
    { value: 'Asia/Dubai', label: 'Asia/Dubai (GST)' },
    { value: 'Australia/Sydney', label: 'Australia/Sydney (AEST/AEDT)' },
];

interface ProfileData {
    first_name: string | null;
    last_name: string | null;
    phone: string | null;
    job_title: string | null;
    department: string | null;
    timezone: string;
    notification_preferences: {
        email_notifications: boolean;
        assessment_reminders: boolean;
        security_alerts: boolean;
        scan_completed: boolean;
        assessment_incomplete_reminder: boolean;
        risk_status_critical: boolean;
    } | null;
    profile_picture: string | null;
    email: string;
    role_name: string;
    organisation_name: string;
}

interface ProfileModalProps {
    open: boolean;
    onClose: () => void;
}

const ProfileModal = ({ open, onClose }: ProfileModalProps) => {
    const { getAuthHeader } = useAuthStore();
    const { theme, setTheme } = useThemeStore();
    const [api, contextHolder] = notification.useNotification();
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Profile state
    const [profile, setProfile] = useState<ProfileData>({
        first_name: '',
        last_name: '',
        phone: '',
        job_title: '',
        department: '',
        timezone: 'UTC',
        notification_preferences: {
            email_notifications: true,
            assessment_reminders: true,
            security_alerts: true,
            scan_completed: true,
            assessment_incomplete_reminder: true,
            risk_status_critical: true,
        },
        profile_picture: null,
        email: '',
        role_name: '',
        organisation_name: '',
    });

    // Password change state
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    // Loading states
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [isChangingPassword, setIsChangingPassword] = useState(false);
    const [isUploadingPicture, setIsUploadingPicture] = useState(false);

    // Active tab
    const [activeTab, setActiveTab] = useState('profile');

    // Fetch profile when modal opens
    useEffect(() => {
        if (open) {
            fetchProfile();
            setActiveTab('profile');
        }
    }, [open]);

    const fetchProfile = async () => {
        setIsLoading(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/profile`, {
                headers: {
                    ...getAuthHeader(),
                },
            });

            if (response.ok) {
                const data = await response.json();
                setProfile({
                    first_name: data.first_name || '',
                    last_name: data.last_name || '',
                    phone: data.phone || '',
                    job_title: data.job_title || '',
                    department: data.department || '',
                    timezone: data.timezone || 'UTC',
                    notification_preferences: {
                        email_notifications: data.notification_preferences?.email_notifications ?? true,
                        assessment_reminders: data.notification_preferences?.assessment_reminders ?? true,
                        security_alerts: data.notification_preferences?.security_alerts ?? true,
                        scan_completed: data.notification_preferences?.scan_completed ?? true,
                        assessment_incomplete_reminder: data.notification_preferences?.assessment_incomplete_reminder ?? true,
                        risk_status_critical: data.notification_preferences?.risk_status_critical ?? true,
                    },
                    profile_picture: data.profile_picture,
                    email: data.email,
                    role_name: data.role_name,
                    organisation_name: data.organisation_name,
                });
            } else {
                api.error({
                    message: 'Error',
                    description: 'Failed to fetch profile data',
                });
            }
        } catch (error) {
            console.error('Error fetching profile:', error);
            api.error({
                message: 'Error',
                description: 'Failed to fetch profile data',
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSaveProfile = async () => {
        setIsSaving(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/profile`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader(),
                },
                body: JSON.stringify({
                    first_name: profile.first_name || null,
                    last_name: profile.last_name || null,
                    phone: profile.phone || null,
                    job_title: profile.job_title || null,
                    department: profile.department || null,
                    timezone: profile.timezone,
                    notification_preferences: profile.notification_preferences,
                }),
            });

            if (response.ok) {
                api.success({
                    message: 'Success',
                    description: 'Profile updated successfully',
                });
            } else {
                const error = await response.json();
                api.error({
                    message: 'Error',
                    description: error.detail || 'Failed to update profile',
                });
            }
        } catch (error) {
            console.error('Error saving profile:', error);
            api.error({
                message: 'Error',
                description: 'Failed to update profile',
            });
        } finally {
            setIsSaving(false);
        }
    };

    const handleChangePassword = async () => {
        // Validation
        if (!currentPassword || !newPassword || !confirmPassword) {
            api.error({
                message: 'Validation Error',
                description: 'Please fill in all password fields',
            });
            return;
        }

        if (newPassword !== confirmPassword) {
            api.error({
                message: 'Validation Error',
                description: 'New passwords do not match',
            });
            return;
        }

        if (newPassword.length < 8) {
            api.error({
                message: 'Validation Error',
                description: 'New password must be at least 8 characters long',
            });
            return;
        }

        setIsChangingPassword(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/change-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader(),
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword,
                }),
            });

            if (response.ok) {
                api.success({
                    message: 'Success',
                    description: 'Password changed successfully',
                });
                // Clear password fields
                setCurrentPassword('');
                setNewPassword('');
                setConfirmPassword('');
            } else {
                const error = await response.json();
                api.error({
                    message: 'Error',
                    description: error.detail || 'Failed to change password',
                });
            }
        } catch (error) {
            console.error('Error changing password:', error);
            api.error({
                message: 'Error',
                description: 'Failed to change password',
            });
        } finally {
            setIsChangingPassword(false);
        }
    };

    const handleProfilePictureUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            api.error({
                message: 'Invalid File Type',
                description: 'Please upload a JPEG, PNG, GIF, or WebP image',
            });
            return;
        }

        // Validate file size (5MB max)
        if (file.size > 5 * 1024 * 1024) {
            api.error({
                message: 'File Too Large',
                description: 'Image must be less than 5MB',
            });
            return;
        }

        setIsUploadingPicture(true);
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/profile/picture`, {
                method: 'POST',
                headers: {
                    ...getAuthHeader(),
                },
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                setProfile(prev => ({ ...prev, profile_picture: data.profile_picture }));
                api.success({
                    message: 'Success',
                    description: 'Profile picture uploaded successfully',
                });
            } else {
                const error = await response.json();
                api.error({
                    message: 'Error',
                    description: error.detail || 'Failed to upload profile picture',
                });
            }
        } catch (error) {
            console.error('Error uploading profile picture:', error);
            api.error({
                message: 'Error',
                description: 'Failed to upload profile picture',
            });
        } finally {
            setIsUploadingPicture(false);
        }
    };

    const handleDeleteProfilePicture = async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/profile/picture`, {
                method: 'DELETE',
                headers: {
                    ...getAuthHeader(),
                },
            });

            if (response.ok) {
                setProfile(prev => ({ ...prev, profile_picture: null }));
                api.success({
                    message: 'Success',
                    description: 'Profile picture removed',
                });
            } else {
                api.error({
                    message: 'Error',
                    description: 'Failed to remove profile picture',
                });
            }
        } catch (error) {
            console.error('Error deleting profile picture:', error);
            api.error({
                message: 'Error',
                description: 'Failed to remove profile picture',
            });
        }
    };

    const updateNotificationPreference = (key: string, value: boolean) => {
        setProfile(prev => ({
            ...prev,
            notification_preferences: {
                ...prev.notification_preferences!,
                [key]: value,
            },
        }));
    };

    const formatRoleName = (roleName: string) => {
        return roleName
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    };

    // Custom Toggle Component
    const CustomToggle = ({ checked, onChange, label, description }: {
        checked: boolean;
        onChange: (checked: boolean) => void;
        label: string;
        description: string;
    }) => (
        <div
            style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '16px',
                backgroundColor: 'var(--background-off-white)',
                borderRadius: '10px',
                border: '1px solid var(--border-light-gray)'
            }}
        >
            <div>
                <div style={{ fontWeight: 500, color: 'var(--text-charcoal)', marginBottom: '4px' }}>{label}</div>
                <div style={{ fontSize: '13px', color: 'var(--text-dark-gray)' }}>{description}</div>
            </div>
            <div
                className={`custom-toggle ${checked ? 'active' : ''}`}
                onClick={() => onChange(!checked)}
            >
                <div className="custom-toggle-handle" />
            </div>
        </div>
    );

    const modalStyles = `
        .profile-modal .ant-modal-content {
            border-radius: 16px;
            overflow: hidden;
        }
        .profile-modal .ant-modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid #f0f0f0;
        }
        .profile-modal .ant-modal-body {
            padding: 0;
        }
        .profile-modal .ant-tabs-nav {
            padding: 0 24px;
            margin-bottom: 0;
        }
        .profile-modal .ant-tabs-tab {
            padding: 16px 0;
            font-weight: 500;
        }
        .profile-modal .ant-tabs-content {
            padding: 24px;
        }
        .profile-modal .ant-tabs-tabpane {
            height: 500px;
            overflow-y: auto;
        }
        .profile-form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }
        .profile-form-field {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .profile-form-field label {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-dark-gray);
        }
        .profile-form-field .ant-input,
        .profile-form-field .ant-select {
            border-radius: 8px;
        }
        .custom-toggle {
            position: relative;
            width: 44px;
            height: 24px;
            background: #d9d9d9;
            border-radius: 12px;
            transition: background 0.2s ease;
            cursor: pointer;
            flex-shrink: 0;
        }
        .custom-toggle.active {
            background: #1890ff;
        }
        .custom-toggle-handle {
            position: absolute;
            top: 2px;
            left: 2px;
            width: 20px;
            height: 20px;
            background: white;
            border-radius: 50%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            transition: left 0.2s ease;
        }
        .custom-toggle.active .custom-toggle-handle {
            left: 22px;
        }
        .profile-picture-section {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            padding: 20px;
        }
        .profile-picture-actions {
            display: flex;
            gap: 12px;
        }
        .notification-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .password-form {
            display: flex;
            flex-direction: column;
            gap: 16px;
            max-width: 400px;
        }
        .theme-picker-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 16px;
        }
        .theme-card {
            border: 2px solid #e9edf2;
            border-radius: 12px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.25s ease;
            text-align: center;
            position: relative;
        }
        .theme-card:hover {
            border-color: #0f386a;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(15, 56, 106, 0.2);
        }
        .theme-card.active {
            border-color: #0f386a;
            box-shadow: 0 0 0 3px rgba(15, 56, 106, 0.15);
        }
        .theme-card .theme-check {
            position: absolute;
            top: 8px;
            right: 8px;
            color: #0f386a;
            font-size: 18px;
        }
        .theme-preview {
            width: 100%;
            height: 80px;
            border-radius: 8px;
            margin-bottom: 12px;
            overflow: hidden;
            border: 1px solid rgba(0,0,0,0.06);
        }
        .theme-card-name {
            font-weight: 600;
            font-size: 14px;
            margin-bottom: 4px;
        }
        .theme-card-desc {
            font-size: 12px;
            color: var(--text-dark-gray);
            line-height: 1.4;
        }
    `;

    const tabItems = [
        {
            key: 'profile',
            label: (
                <span>
                    <UserOutlined style={{ marginRight: 8 }} />
                    Profile
                </span>
            ),
            children: (
                <div>
                    {/* Profile Picture */}
                    <div className="profile-picture-section" style={{ marginBottom: '24px', backgroundColor: 'var(--background-off-white)', borderRadius: '12px' }}>
                        <Avatar
                            size={100}
                            src={profile.profile_picture}
                            icon={!profile.profile_picture && <UserOutlined />}
                            style={{ backgroundColor: profile.profile_picture ? 'transparent' : 'var(--primary-blue)' }}
                        />
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleProfilePictureUpload}
                            accept="image/jpeg,image/png,image/gif,image/webp"
                            style={{ display: 'none' }}
                        />
                        <div className="profile-picture-actions">
                            <Button
                                icon={<CameraOutlined />}
                                onClick={() => fileInputRef.current?.click()}
                                loading={isUploadingPicture}
                            >
                                Upload Photo
                            </Button>
                            {profile.profile_picture && (
                                <Button
                                    icon={<DeleteOutlined />}
                                    danger
                                    onClick={handleDeleteProfilePicture}
                                >
                                    Remove
                                </Button>
                            )}
                        </div>
                        <p style={{ fontSize: '12px', color: 'var(--text-dark-gray)', margin: 0 }}>
                            JPEG, PNG, GIF, or WebP. Max 5MB.
                        </p>
                    </div>

                    {/* Personal Information */}
                    <h4 style={{ marginBottom: '16px', color: 'var(--primary-navy)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <UserOutlined /> Personal Information
                    </h4>
                    <div className="profile-form-grid">
                        <div className="profile-form-field">
                            <label>First Name</label>
                            <Input
                                prefix={<UserOutlined style={{ color: 'var(--text-medium-gray)' }} />}
                                placeholder="Enter first name"
                                value={profile.first_name || ''}
                                onChange={(e) => setProfile(prev => ({ ...prev, first_name: e.target.value }))}
                            />
                        </div>
                        <div className="profile-form-field">
                            <label>Last Name</label>
                            <Input
                                prefix={<UserOutlined style={{ color: 'var(--text-medium-gray)' }} />}
                                placeholder="Enter last name"
                                value={profile.last_name || ''}
                                onChange={(e) => setProfile(prev => ({ ...prev, last_name: e.target.value }))}
                            />
                        </div>
                        <div className="profile-form-field">
                            <label>Email Address</label>
                            <Input
                                prefix={<MailOutlined style={{ color: 'var(--text-medium-gray)' }} />}
                                value={profile.email}
                                disabled
                                style={{ backgroundColor: 'var(--background-off-white)' }}
                            />
                        </div>
                        <div className="profile-form-field">
                            <label>Phone Number</label>
                            <Input
                                prefix={<PhoneOutlined style={{ color: 'var(--text-medium-gray)' }} />}
                                placeholder="Enter phone number"
                                value={profile.phone || ''}
                                onChange={(e) => setProfile(prev => ({ ...prev, phone: e.target.value }))}
                            />
                        </div>
                    </div>

                    {/* Work Information */}
                    <h4 style={{ marginTop: '24px', marginBottom: '16px', color: 'var(--primary-navy)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <IdcardOutlined /> Work Information
                    </h4>
                    <div className="profile-form-grid">
                        <div className="profile-form-field">
                            <label>Job Title</label>
                            <Input
                                prefix={<IdcardOutlined style={{ color: 'var(--text-medium-gray)' }} />}
                                placeholder="Enter job title"
                                value={profile.job_title || ''}
                                onChange={(e) => setProfile(prev => ({ ...prev, job_title: e.target.value }))}
                            />
                        </div>
                        <div className="profile-form-field">
                            <label>Department</label>
                            <Input
                                prefix={<TeamOutlined style={{ color: 'var(--text-medium-gray)' }} />}
                                placeholder="Enter department"
                                value={profile.department || ''}
                                onChange={(e) => setProfile(prev => ({ ...prev, department: e.target.value }))}
                            />
                        </div>
                        <div className="profile-form-field">
                            <label>Role</label>
                            <Input
                                prefix={<SafetyOutlined style={{ color: 'var(--text-medium-gray)' }} />}
                                value={formatRoleName(profile.role_name)}
                                disabled
                                style={{ backgroundColor: 'var(--background-off-white)' }}
                            />
                        </div>
                        <div className="profile-form-field">
                            <label>Organisation</label>
                            <Input
                                prefix={<TeamOutlined style={{ color: 'var(--text-medium-gray)' }} />}
                                value={profile.organisation_name}
                                disabled
                                style={{ backgroundColor: 'var(--background-off-white)' }}
                            />
                        </div>
                        <div className="profile-form-field">
                            <label>Timezone</label>
                            <Select
                                style={{ width: '100%' }}
                                placeholder="Select timezone"
                                value={profile.timezone}
                                onChange={(value) => setProfile(prev => ({ ...prev, timezone: value }))}
                                options={TIMEZONES}
                                showSearch
                                optionFilterProp="label"
                            />
                        </div>
                    </div>

                    {/* Save Button */}
                    <div style={{ marginTop: '24px' }}>
                        <Button
                            type="primary"
                            icon={<SaveOutlined />}
                            onClick={handleSaveProfile}
                            loading={isSaving}
                            style={{ backgroundColor: 'var(--primary-blue)' }}
                        >
                            Save Changes
                        </Button>
                    </div>
                </div>
            ),
        },
        {
            key: 'notifications',
            label: (
                <span>
                    <BellOutlined style={{ marginRight: 8 }} />
                    Notifications
                </span>
            ),
            children: (
                <div>
                    {/* Header with Master Toggle */}
                    <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '20px',
                        paddingBottom: '16px',
                        borderBottom: '1px solid var(--border-light-gray)'
                    }}>
                        <div>
                            <h4 style={{ margin: 0, color: 'var(--primary-navy)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <BellOutlined /> Email Notifications
                            </h4>
                            <div style={{ fontSize: '13px', color: 'var(--text-dark-gray)', marginTop: '4px' }}>
                                {profile.notification_preferences?.email_notifications
                                    ? 'All email notifications are enabled'
                                    : 'All email notifications are disabled'}
                            </div>
                        </div>
                        <div
                            className={`custom-toggle ${profile.notification_preferences?.email_notifications ? 'active' : ''}`}
                            onClick={() => updateNotificationPreference('email_notifications', !profile.notification_preferences?.email_notifications)}
                            style={{ cursor: 'pointer' }}
                        >
                            <div className="custom-toggle-handle" />
                        </div>
                    </div>

                    {/* Notification Options */}
                    <div style={{
                        opacity: profile.notification_preferences?.email_notifications ? 1 : 0.5,
                        pointerEvents: profile.notification_preferences?.email_notifications ? 'auto' : 'none'
                    }}>
                        <div className="notification-list">
                            <CustomToggle
                                checked={profile.notification_preferences?.scan_completed ?? true}
                                onChange={(checked) => updateNotificationPreference('scan_completed', checked)}
                                label="Security Scan Completed"
                                description="Get notified when security scans complete with results summary"
                            />
                            <CustomToggle
                                checked={profile.notification_preferences?.assessment_incomplete_reminder ?? true}
                                onChange={(checked) => updateNotificationPreference('assessment_incomplete_reminder', checked)}
                                label="Assessment Incomplete Reminder"
                                description="Receive reminders for assessments that have been incomplete for 7+ days"
                            />
                            <CustomToggle
                                checked={profile.notification_preferences?.risk_status_critical ?? true}
                                onChange={(checked) => updateNotificationPreference('risk_status_critical', checked)}
                                label="Risk Status Critical Alert"
                                description="Get notified when a risk status changes to High or Critical severity"
                            />
                        </div>
                    </div>

                    {/* Save Button */}
                    <div style={{ marginTop: '24px' }}>
                        <Button
                            type="primary"
                            icon={<SaveOutlined />}
                            onClick={handleSaveProfile}
                            loading={isSaving}
                            style={{ backgroundColor: 'var(--primary-blue)' }}
                        >
                            Save Preferences
                        </Button>
                    </div>
                </div>
            ),
        },
        {
            key: 'security',
            label: (
                <span>
                    <LockOutlined style={{ marginRight: 8 }} />
                    Security
                </span>
            ),
            children: (
                <div>
                    <h4 style={{ marginBottom: '20px', color: 'var(--primary-navy)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <LockOutlined /> Change Password
                    </h4>
                    <div className="password-form">
                        <div className="profile-form-field">
                            <label>Current Password</label>
                            <Input.Password
                                placeholder="Enter current password"
                                value={currentPassword}
                                onChange={(e) => setCurrentPassword(e.target.value)}
                            />
                        </div>
                        <div className="profile-form-field">
                            <label>New Password</label>
                            <Input.Password
                                placeholder="Enter new password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                            />
                        </div>
                        <div className="profile-form-field">
                            <label>Confirm New Password</label>
                            <Input.Password
                                placeholder="Confirm new password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                status={confirmPassword && newPassword !== confirmPassword ? 'error' : ''}
                            />
                            {confirmPassword && newPassword !== confirmPassword && (
                                <div style={{ color: '#ff4d4f', fontSize: '12px' }}>
                                    Passwords do not match
                                </div>
                            )}
                        </div>
                        <p style={{ fontSize: '12px', color: 'var(--text-dark-gray)', margin: 0 }}>
                            Password must be at least 8 characters long.
                        </p>
                        <Button
                            type="primary"
                            icon={<LockOutlined />}
                            onClick={handleChangePassword}
                            loading={isChangingPassword}
                            style={{ backgroundColor: '#fa8c16', width: 'fit-content' }}
                        >
                            Change Password
                        </Button>
                    </div>
                </div>
            ),
        },
        {
            key: 'themes',
            label: (
                <span>
                    <BgColorsOutlined style={{ marginRight: 8 }} />
                    Themes
                </span>
            ),
            children: (
                <div>
                    <h4 style={{ marginBottom: '4px', color: 'var(--primary-navy)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <BgColorsOutlined /> Appearance
                    </h4>
                    <p style={{ fontSize: '13px', color: 'var(--text-dark-gray)', marginBottom: '20px' }}>
                        Choose a theme to personalize the look and feel of your workspace.
                    </p>

                    <div className="theme-picker-grid">
                        {/* Light Theme Card */}
                        <div
                            className={`theme-card ${theme === 'light' ? 'active' : ''}`}
                            onClick={() => setTheme('light')}
                        >
                            {theme === 'light' && <CheckCircleFilled className="theme-check" />}
                            <div className="theme-preview" style={{
                                background: '#f0f2f5',
                                display: 'flex',
                                flexDirection: 'column' as const,
                            }}>
                                <div style={{ height: '20px', background: '#0f2a44', display: 'flex', alignItems: 'center', padding: '0 6px' }}>
                                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#0f386a', marginRight: '4px' }} />
                                    <div style={{ width: '20px', height: '3px', borderRadius: '2px', background: 'rgba(255,255,255,0.4)' }} />
                                </div>
                                <div style={{ flex: 1, padding: '6px', display: 'flex', gap: '4px' }}>
                                    <div style={{ width: '30%', background: '#0f2a44', borderRadius: '3px' }} />
                                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column' as const, gap: '4px' }}>
                                        <div style={{ height: '12px', background: '#ffffff', borderRadius: '3px', border: '1px solid #e9edf2' }} />
                                        <div style={{ flex: 1, background: '#ffffff', borderRadius: '3px', border: '1px solid #e9edf2' }} />
                                    </div>
                                </div>
                            </div>
                            <div className="theme-card-name">Light</div>
                            <div className="theme-card-desc">Clean and bright. The default look.</div>
                        </div>

                        {/* Dark Theme Card */}
                        <div
                            className={`theme-card ${theme === 'dark' ? 'active' : ''}`}
                            onClick={() => setTheme('dark')}
                        >
                            {theme === 'dark' && <CheckCircleFilled className="theme-check" />}
                            <div className="theme-preview" style={{
                                background: '#0f1923',
                                display: 'flex',
                                flexDirection: 'column' as const,
                            }}>
                                <div style={{ height: '20px', background: '#0a1628', display: 'flex', alignItems: 'center', padding: '0 6px' }}>
                                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#0f386a', marginRight: '4px' }} />
                                    <div style={{ width: '20px', height: '3px', borderRadius: '2px', background: 'rgba(255,255,255,0.2)' }} />
                                </div>
                                <div style={{ flex: 1, padding: '6px', display: 'flex', gap: '4px' }}>
                                    <div style={{ width: '30%', background: '#0a1628', borderRadius: '3px' }} />
                                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column' as const, gap: '4px' }}>
                                        <div style={{ height: '12px', background: '#1a1a2e', borderRadius: '3px', border: '1px solid #2a3a5c' }} />
                                        <div style={{ flex: 1, background: '#1a1a2e', borderRadius: '3px', border: '1px solid #2a3a5c' }} />
                                    </div>
                                </div>
                            </div>
                            <div className="theme-card-name">Dark</div>
                            <div className="theme-card-desc">Easy on the eyes. Great for night.</div>
                        </div>

                        {/* Dark Glass Theme Card */}
                        <div
                            className={`theme-card ${theme === 'dark-glass' ? 'active' : ''}`}
                            onClick={() => setTheme('dark-glass')}
                        >
                            {theme === 'dark-glass' && <CheckCircleFilled className="theme-check" />}
                            <div className="theme-preview" style={{
                                background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #020617 100%)',
                                display: 'flex',
                                flexDirection: 'column' as const,
                            }}>
                                <div style={{ height: '20px', background: 'rgba(10, 20, 40, 0.65)', display: 'flex', alignItems: 'center', padding: '0 6px' }}>
                                    <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#60a5fa', marginRight: '4px' }} />
                                    <div style={{ width: '20px', height: '3px', borderRadius: '2px', background: 'rgba(255,255,255,0.3)' }} />
                                </div>
                                <div style={{ flex: 1, padding: '6px', display: 'flex', gap: '4px' }}>
                                    <div style={{ width: '30%', background: 'rgba(15, 23, 42, 0.5)', borderRadius: '3px', border: '1px solid rgba(255,255,255,0.08)' }} />
                                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column' as const, gap: '4px' }}>
                                        <div style={{ height: '12px', background: 'rgba(30, 41, 59, 0.4)', borderRadius: '3px', border: '1px solid rgba(255,255,255,0.12)' }} />
                                        <div style={{ flex: 1, background: 'rgba(30, 41, 59, 0.4)', borderRadius: '3px', border: '1px solid rgba(255,255,255,0.12)' }} />
                                    </div>
                                </div>
                            </div>
                            <div className="theme-card-name">Dark Glass</div>
                            <div className="theme-card-desc">Frosted surfaces with deep vibrant gradients.</div>
                        </div>
                    </div>

                    <p style={{ fontSize: '12px', color: 'var(--text-dark-gray)', marginTop: '20px' }}>
                        Your theme preference is saved locally and will persist across sessions.
                    </p>
                </div>
            ),
        },
    ];

    return (
        <>
            {contextHolder}
            <style>{modalStyles}</style>
            <Modal
                title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <UserOutlined style={{ color: 'var(--primary-blue)' }} />
                        <span>My Profile</span>
                    </div>
                }
                open={open}
                onCancel={onClose}
                footer={null}
                width={700}
                className="profile-modal"
                centered
                destroyOnClose
            >
                {isLoading ? (
                    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
                        <div>Loading profile...</div>
                    </div>
                ) : (
                    <Tabs
                        activeKey={activeTab}
                        onChange={setActiveTab}
                        items={tabItems}
                    />
                )}
            </Modal>
        </>
    );
};

export default ProfileModal;
