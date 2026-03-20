import React, {useEffect, useState} from 'react';
import {Select, notification} from "antd";
import {SyncOutlined} from "@ant-design/icons";
import Sidebar from "../components/Sidebar.tsx";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import useUserStore from "../store/useUserStore.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import FrameworkUpdatesSection from "../components/FrameworkUpdatesSection.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const FrameworkUpdatesPage: React.FC = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Global State
    const {frameworks, fetchFrameworks} = useFrameworksStore();
    const {current_user} = useUserStore();

    // Local State
    const [frameworkSelectedId, setFrameworkSelectedId] = useState<string>('');
    const [api, contextHolder] = notification.useNotification();

    // On Component Mount
    useEffect(() => {
        fetchFrameworks();
    }, []);

    // Framework options
    const options = frameworks.map(framework => ({
        value: framework.id,
        label: framework.organisation_domain ? `${framework.name} (${framework.organisation_domain})` : framework.name,
    }));

    // Handle framework change
    const handleFrameworkChange = (value: string) => {
        setFrameworkSelectedId(value);
    };

    return (
        <div>
            {contextHolder}
            <div className={'page-parent'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
                <div className="page-content">

                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <SyncOutlined style={{ fontSize: 22, color: '#1a365d' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Framework Updates</h1>
                        </div>
                    </div>

                    {/* Framework Selection */}
                    <div className="page-section">
                        <div className="form-row">
                            <div className="form-group" style={{ flex: 1 }}>
                                <label className="form-label">Select Framework</label>
                                <Select
                                    className="framework-dropdown"
                                    placeholder="Select a framework to view its updates"
                                    onChange={handleFrameworkChange}
                                    options={options}
                                    value={frameworkSelectedId || undefined}
                                    style={{ width: '100%' }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Framework Updates Section */}
                    <div className="page-section">
                        <InfoTitle
                            title="Available Updates"
                            infoContent="Manage and apply updates to framework questions, chapters, and objectives. Updates preserve all existing data including policies, assessments, and user responses."
                            className="section-title"
                        />
                        <p className="section-subtitle">
                            View available updates and apply them to keep your frameworks current with the latest requirements
                        </p>

                        {frameworkSelectedId ? (
                            <FrameworkUpdatesSection
                                frameworkId={frameworkSelectedId}
                                userRole={current_user?.role_name}
                            />
                        ) : (
                            <div style={{
                                padding: '40px 20px',
                                textAlign: 'center',
                                background: '#fafafa',
                                borderRadius: '8px',
                                border: '1px dashed #d9d9d9'
                            }}>
                                <SyncOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
                                <p style={{ color: '#8c8c8c', fontSize: '14px', margin: 0 }}>
                                    Please select a framework to view and manage its updates
                                </p>
                            </div>
                        )}
                    </div>

                </div>
            </div>
        </div>
    );
};

export default FrameworkUpdatesPage;
