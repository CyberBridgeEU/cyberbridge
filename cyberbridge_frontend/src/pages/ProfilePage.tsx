// src/pages/ProfilePage.tsx
import { useEffect, useState, useRef } from "react";
import { notification, Input, Button, Select, Switch, Divider, Avatar, Upload, message } from 'antd';
import { UserOutlined, MailOutlined, SafetyOutlined, PhoneOutlined, IdcardOutlined, TeamOutlined, GlobalOutlined, BellOutlined, LockOutlined, CameraOutlined, SaveOutlined, DeleteOutlined } from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import useUserStore from "../store/useUserStore.ts";
import useAuthStore from "../store/useAuthStore.ts";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
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
        account_status_change: boolean;
    } | null;
    profile_picture: string | null;
    email: string;
    role_name: string;
    organisation_name: string;
}

const ProfilePage = () => {
    const [location, setLocation] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const { current_user, fetchCurrentUserDetails } = useUserStore();
    const { getAuthHeader, user } = useAuthStore();
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
            account_status_change: true,
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

    // Fetch profile on mount
    useEffect(() => {
        fetchProfile();
    }, []);

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
                        account_status_change: data.notification_preferences?.account_status_change ?? true,
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

    if (isLoading) {
        return (
            <div style={{ display: 'flex', height: '100vh' }}>
                <Sidebar onClick={() => {}} selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys} onOpenChange={menuHighlighting.onOpenChange} />
                <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <div>Loading profile...</div>
                </div>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', height: '100vh' }}>
            {contextHolder}
            <Sidebar onClick={() => {}} selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys} onOpenChange={menuHighlighting.onOpenChange} />

            <div className="page-content" style={{ flex: 1, padding: '24px', overflowY: 'auto', backgroundColor: '#f5f5f5' }}>
                <div style={{ maxWidth: '900px', margin: '0 auto' }}>
                    <h2 style={{ marginBottom: '24px', color: '#1a365d', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <UserOutlined /> My Profile
                    </h2>

                    {/* Profile Picture Section */}
                    <div className="page-section" style={{ marginBottom: '24px' }}>
                        <h3 className="section-title">Profile Picture</h3>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
                            <div style={{ position: 'relative' }}>
                                <Avatar
                                    size={120}
                                    src={profile.profile_picture}
                                    icon={!profile.profile_picture && <UserOutlined />}
                                    style={{ backgroundColor: profile.profile_picture ? 'transparent' : '#0f386a' }}
                                />
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    onChange={handleProfilePictureUpload}
                                    accept="image/jpeg,image/png,image/gif,image/webp"
                                    style={{ display: 'none' }}
                                />
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                <Button
                                    icon={<CameraOutlined />}
                                    onClick={() => fileInputRef.current?.click()}
                                    loading={isUploadingPicture}
                                >
                                    Upload New Picture
                                </Button>
                                {profile.profile_picture && (
                                    <Button
                                        icon={<DeleteOutlined />}
                                        danger
                                        onClick={handleDeleteProfilePicture}
                                    >
                                        Remove Picture
                                    </Button>
                                )}
                                <p style={{ fontSize: '12px', color: '#8c8c8c', margin: 0 }}>
                                    Allowed: JPEG, PNG, GIF, WebP. Max 5MB.
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Personal Information Section */}
                    <div className="page-section" style={{ marginBottom: '24px' }}>
                        <h3 className="section-title">Personal Information</h3>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                            <div>
                                <label className="styled-label">First Name</label>
                                <Input
                                    prefix={<UserOutlined style={{ color: '#999' }} />}
                                    placeholder="Enter first name"
                                    value={profile.first_name || ''}
                                    onChange={(e) => setProfile(prev => ({ ...prev, first_name: e.target.value }))}
                                    className="framework-input"
                                />
                            </div>
                            <div>
                                <label className="styled-label">Last Name</label>
                                <Input
                                    prefix={<UserOutlined style={{ color: '#999' }} />}
                                    placeholder="Enter last name"
                                    value={profile.last_name || ''}
                                    onChange={(e) => setProfile(prev => ({ ...prev, last_name: e.target.value }))}
                                    className="framework-input"
                                />
                            </div>
                            <div>
                                <label className="styled-label">Email Address</label>
                                <Input
                                    prefix={<MailOutlined style={{ color: '#999' }} />}
                                    value={profile.email}
                                    disabled
                                    className="framework-input"
                                    style={{ backgroundColor: '#f5f5f5' }}
                                />
                            </div>
                            <div>
                                <label className="styled-label">Role</label>
                                <Input
                                    prefix={<SafetyOutlined style={{ color: '#999' }} />}
                                    value={formatRoleName(profile.role_name)}
                                    disabled
                                    className="framework-input"
                                    style={{ backgroundColor: '#f5f5f5' }}
                                />
                            </div>
                            <div>
                                <label className="styled-label">Phone Number</label>
                                <Input
                                    prefix={<PhoneOutlined style={{ color: '#999' }} />}
                                    placeholder="Enter phone number"
                                    value={profile.phone || ''}
                                    onChange={(e) => setProfile(prev => ({ ...prev, phone: e.target.value }))}
                                    className="framework-input"
                                />
                            </div>
                            <div>
                                <label className="styled-label">Organisation</label>
                                <Input
                                    prefix={<TeamOutlined style={{ color: '#999' }} />}
                                    value={profile.organisation_name}
                                    disabled
                                    className="framework-input"
                                    style={{ backgroundColor: '#f5f5f5' }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Work Information Section */}
                    <div className="page-section" style={{ marginBottom: '24px' }}>
                        <h3 className="section-title">Work Information</h3>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                            <div>
                                <label className="styled-label">Job Title</label>
                                <Input
                                    prefix={<IdcardOutlined style={{ color: '#999' }} />}
                                    placeholder="Enter job title"
                                    value={profile.job_title || ''}
                                    onChange={(e) => setProfile(prev => ({ ...prev, job_title: e.target.value }))}
                                    className="framework-input"
                                />
                            </div>
                            <div>
                                <label className="styled-label">Department</label>
                                <Input
                                    prefix={<TeamOutlined style={{ color: '#999' }} />}
                                    placeholder="Enter department"
                                    value={profile.department || ''}
                                    onChange={(e) => setProfile(prev => ({ ...prev, department: e.target.value }))}
                                    className="framework-input"
                                />
                            </div>
                            <div>
                                <label className="styled-label">Timezone</label>
                                <Select
                                    style={{ width: '100%' }}
                                    placeholder="Select timezone"
                                    value={profile.timezone}
                                    onChange={(value) => setProfile(prev => ({ ...prev, timezone: value }))}
                                    options={TIMEZONES}
                                    className="standard-dropdown"
                                    showSearch
                                    optionFilterProp="label"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Notification Preferences Section */}
                    <div className="page-section" style={{ marginBottom: '24px' }}>
                        <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <BellOutlined /> Notification Preferences
                        </h3>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                                <div>
                                    <div style={{ fontWeight: 500 }}>Email Notifications</div>
                                    <div style={{ fontSize: '12px', color: '#8c8c8c' }}>Receive general email notifications (master toggle)</div>
                                </div>
                                <Switch
                                    checked={profile.notification_preferences?.email_notifications ?? true}
                                    onChange={(checked) => updateNotificationPreference('email_notifications', checked)}
                                />
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                                <div>
                                    <div style={{ fontWeight: 500 }}>Assessment Reminders</div>
                                    <div style={{ fontSize: '12px', color: '#8c8c8c' }}>Get reminders for pending assessments</div>
                                </div>
                                <Switch
                                    checked={profile.notification_preferences?.assessment_reminders ?? true}
                                    onChange={(checked) => updateNotificationPreference('assessment_reminders', checked)}
                                />
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                                <div>
                                    <div style={{ fontWeight: 500 }}>Security Alerts</div>
                                    <div style={{ fontSize: '12px', color: '#8c8c8c' }}>Receive security-related alerts and notifications</div>
                                </div>
                                <Switch
                                    checked={profile.notification_preferences?.security_alerts ?? true}
                                    onChange={(checked) => updateNotificationPreference('security_alerts', checked)}
                                />
                            </div>

                            {/* New notification toggles */}
                            <div style={{ marginTop: '8px', paddingTop: '16px', borderTop: '1px solid #e8e8e8' }}>
                                <div style={{ fontSize: '13px', fontWeight: 500, color: '#595959', marginBottom: '12px' }}>Specific Notifications</div>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                                <div>
                                    <div style={{ fontWeight: 500 }}>Security Scan Completed</div>
                                    <div style={{ fontSize: '12px', color: '#8c8c8c' }}>Get notified when security scans complete with results summary</div>
                                </div>
                                <Switch
                                    checked={profile.notification_preferences?.scan_completed ?? true}
                                    onChange={(checked) => updateNotificationPreference('scan_completed', checked)}
                                    disabled={!profile.notification_preferences?.email_notifications}
                                />
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                                <div>
                                    <div style={{ fontWeight: 500 }}>Assessment Incomplete Reminder</div>
                                    <div style={{ fontSize: '12px', color: '#8c8c8c' }}>Receive reminders for assessments that have been incomplete for 7+ days</div>
                                </div>
                                <Switch
                                    checked={profile.notification_preferences?.assessment_incomplete_reminder ?? true}
                                    onChange={(checked) => updateNotificationPreference('assessment_incomplete_reminder', checked)}
                                    disabled={!profile.notification_preferences?.email_notifications}
                                />
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                                <div>
                                    <div style={{ fontWeight: 500 }}>Risk Status Critical Alert</div>
                                    <div style={{ fontSize: '12px', color: '#8c8c8c' }}>Get notified when a risk status changes to High or Critical severity</div>
                                </div>
                                <Switch
                                    checked={profile.notification_preferences?.risk_status_critical ?? true}
                                    onChange={(checked) => updateNotificationPreference('risk_status_critical', checked)}
                                    disabled={!profile.notification_preferences?.email_notifications}
                                />
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px', backgroundColor: '#fafafa', borderRadius: '8px' }}>
                                <div>
                                    <div style={{ fontWeight: 500 }}>Account Status Change</div>
                                    <div style={{ fontSize: '12px', color: '#8c8c8c' }}>Get notified when your account is approved, deactivated, or set to pending</div>
                                </div>
                                <Switch
                                    checked={profile.notification_preferences?.account_status_change ?? true}
                                    onChange={(checked) => updateNotificationPreference('account_status_change', checked)}
                                    disabled={!profile.notification_preferences?.email_notifications}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Save Profile Button */}
                    <div style={{ marginBottom: '24px' }}>
                        <Button
                            type="primary"
                            icon={<SaveOutlined />}
                            onClick={handleSaveProfile}
                            loading={isSaving}
                            size="large"
                            style={{ backgroundColor: '#0f386a' }}
                        >
                            Save Profile Changes
                        </Button>
                    </div>

                    <Divider />

                    {/* Change Password Section */}
                    <div className="page-section" style={{ marginBottom: '24px' }}>
                        <h3 className="section-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <LockOutlined /> Change Password
                        </h3>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                            <div>
                                <label className="styled-label">Current Password</label>
                                <Input.Password
                                    placeholder="Enter current password"
                                    value={currentPassword}
                                    onChange={(e) => setCurrentPassword(e.target.value)}
                                    className="framework-input"
                                />
                            </div>
                            <div>
                                <label className="styled-label">New Password</label>
                                <Input.Password
                                    placeholder="Enter new password"
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    className="framework-input"
                                />
                            </div>
                            <div>
                                <label className="styled-label">Confirm New Password</label>
                                <Input.Password
                                    placeholder="Confirm new password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="framework-input"
                                />
                            </div>
                        </div>
                        <p style={{ fontSize: '12px', color: '#8c8c8c', marginBottom: '16px' }}>
                            Password must be at least 8 characters long.
                        </p>
                        <Button
                            type="primary"
                            icon={<LockOutlined />}
                            onClick={handleChangePassword}
                            loading={isChangingPassword}
                            style={{ backgroundColor: '#fa8c16' }}
                        >
                            Change Password
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProfilePage;
