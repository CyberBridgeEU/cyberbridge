import {Input, notification} from "antd";
import Sidebar from "../components/Sidebar.tsx";
import useUserStore from "../store/useUserStore.ts";
import {useEffect, useState} from "react";
import React from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import {LockOutlined} from "@ant-design/icons";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";


const UpdatePasswordPage = () => {
    // Menu highlighting
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    const { current_user, fetchCurrentUser, updateUser } = useUserStore();
    const [newPassword, setNewPassword] = useState("");
    const [loading, setLoading] = useState(false);

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    useEffect(() => {
        // Fetch current user when component mounts
        fetchCurrentUser();
    }, [fetchCurrentUser]);

    const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setNewPassword(e.target.value);
    };

    const handleUpdatePassword = async () => {
        if (!newPassword.trim()) {
            api.error({
                message: 'Password Update Failed',
                description: 'Please enter a new password',
                duration: 4,
            });
            return;
        }

        setLoading(true);
        try {
            // Update only the password, keeping other fields null to not change them
            const success = await updateUser(null, newPassword, null, current_user.id);

            if (success) {
                api.success({
                    message: 'Password Update Success',
                    description: 'Password updated successfully',
                    duration: 4,
                });
                setNewPassword(""); // Clear the input field
            } else {
                api.error({
                    message: 'Password Update Failed',
                    description: 'Failed to update password',
                    duration: 4,
                });
            }
        } catch (error) {
            console.error("Error updating password:", error);
            api.error({
                message: 'Password Update Failed',
                description: 'An error occurred while updating password',
                duration: 4,
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            {contextHolder}
            <div className={'page-parent'}>
                <Sidebar
                    selectedKeys={menuHighlighting.selectedKeys}
                    openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange}
                />
                <div className={'page-content'}>
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <LockOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Update Password"
                                infoContent="Change your account password. Enter a new secure password and click Update Password to save changes."
                                className="page-title"
                            />
                        </div>
                    </div>

                    {/* Update Password Section */}
                    <div className="page-section">
                        <h3 className="section-title">Password Update</h3>

                        <div className="form-row">
                            <div className="form-group" style={{ maxWidth: '400px' }}>
                                <label className="form-label">Current User</label>
                                <div style={{
                                    height: '40px',
                                    padding: '0 12px',
                                    border: '1px solid #e8e8e8',
                                    borderRadius: '6px',
                                    backgroundColor: '#fafafa',
                                    display: 'flex',
                                    alignItems: 'center',
                                    color: '#8c8c8c',
                                    fontSize: '14px'
                                }}>
                                    {current_user?.email || "Loading..."}
                                </div>
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group" style={{ maxWidth: '400px' }}>
                                <label className="form-label required">New Password</label>
                                <Input.Password
                                    placeholder="Enter your new password"
                                    value={newPassword}
                                    onChange={handlePasswordChange}
                                />
                            </div>
                            <div className="control-group">
                                <button
                                    className="add-button"
                                    onClick={handleUpdatePassword}
                                    disabled={loading || !newPassword.trim()}
                                >
                                    {loading ? "Updating..." : "Update Password"}
                                </button>
                            </div>
                        </div>

                        <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                            <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>Password Requirements:</h4>
                            <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                                <li>Choose a strong, unique password</li>
                                <li>Consider using a mix of letters, numbers, and symbols</li>
                                <li>Avoid using personal information</li>
                                <li>Make sure it's different from your previous passwords</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UpdatePasswordPage;
