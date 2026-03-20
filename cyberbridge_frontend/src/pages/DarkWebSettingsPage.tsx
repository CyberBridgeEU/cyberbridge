import { useEffect, useState } from 'react';
import { Card, Slider, Button, Row, Col, Typography, message, Spin, Alert } from 'antd';
import {
    SettingOutlined,
    TeamOutlined,
    GlobalOutlined,
    SaveOutlined,
    CheckCircleOutlined,
} from '@ant-design/icons';
import Sidebar from '../components/Sidebar';
import { useLocation } from 'wouter';
import { useMenuHighlighting } from '../utils/menuUtils';
import useDarkWebStore from '../store/useDarkWebStore';
import useUserStore from '../store/useUserStore';

const { Title, Text, Paragraph } = Typography;

const DarkWebSettingsPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const { current_user } = useUserStore();

    const {
        workers,
        engines,
        workersLoading,
        enginesLoading,
        fetchWorkers,
        updateWorkers,
        fetchEngines,
        updateEngines,
    } = useDarkWebStore();

    const [maxWorkers, setMaxWorkers] = useState(1);
    const [localEngines, setLocalEngines] = useState<{ name: string; display_name: string; enabled: boolean }[]>([]);
    const [savingWorkers, setSavingWorkers] = useState(false);
    const [savingEngines, setSavingEngines] = useState(false);

    useEffect(() => {
        fetchWorkers();
        fetchEngines();
    }, []);

    useEffect(() => {
        if (workers) setMaxWorkers(workers.max_workers);
    }, [workers]);

    useEffect(() => {
        if (engines.length > 0) setLocalEngines([...engines]);
    }, [engines]);

    const isAdmin = current_user?.role_name === 'super_admin' || current_user?.role_name === 'org_admin';

    const handleSaveWorkers = async () => {
        setSavingWorkers(true);
        try {
            await updateWorkers(maxWorkers);
            message.success(`Max workers updated to ${maxWorkers}`);
        } catch {
            message.error('Failed to update workers');
        } finally {
            setSavingWorkers(false);
        }
    };

    const toggleEngine = (engineName: string) => {
        setLocalEngines(prev => {
            const updated = prev.map(e =>
                e.name === engineName ? { ...e, enabled: !e.enabled } : e
            );
            const enabledCount = updated.filter(e => e.enabled).length;
            if (enabledCount === 0) {
                message.warning('At least one engine must be enabled');
                return prev;
            }
            return updated;
        });
    };

    const handleSaveEngines = async () => {
        setSavingEngines(true);
        try {
            const enabledNames = localEngines.filter(e => e.enabled).map(e => e.name);
            await updateEngines(enabledNames);
            message.success(`Search engines saved! ${enabledNames.length} engines enabled.`);
        } catch {
            message.error('Failed to save engine configuration');
        } finally {
            setSavingEngines(false);
        }
    };

    if (!isAdmin) {
        return (
            <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--page-background)' }}>
                <Sidebar
                    selectedKeys={menuHighlighting.selectedKeys}
                    openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange}
                />
                <div style={{ flex: 1, padding: '24px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <Alert
                        type="warning"
                        showIcon
                        message="Access Denied"
                        description="Dark Web Settings is only available to administrators."
                    />
                </div>
            </div>
        );
    }

    const enabledCount = localEngines.filter(e => e.enabled).length;

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--page-background)' }}>
            <style>{`
                .dw-toggle-container {
                    display: inline-flex;
                    align-items: center;
                    gap: 10px;
                    cursor: pointer;
                }
                .dw-custom-toggle {
                    position: relative;
                    width: 44px;
                    height: 24px;
                    background: #d9d9d9;
                    border-radius: 12px;
                    transition: background 0.2s ease;
                    cursor: pointer;
                    flex-shrink: 0;
                }
                .dw-custom-toggle.active {
                    background: #1890ff;
                }
                .dw-custom-toggle.disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
                .dw-custom-toggle-handle {
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
                .dw-custom-toggle.active .dw-custom-toggle-handle {
                    left: 22px;
                }
                .dw-toggle-label {
                    font-size: 14px;
                    color: #555;
                }
            `}</style>
            <Sidebar
                selectedKeys={menuHighlighting.selectedKeys}
                openKeys={menuHighlighting.openKeys}
                onOpenChange={menuHighlighting.onOpenChange}
            />
            <div style={{ flex: 1, padding: '24px', overflow: 'auto' }}>
                {/* Header */}
                <div style={{ marginBottom: 24 }}>
                    <Title level={3} style={{ margin: 0 }}>
                        <SettingOutlined style={{ marginRight: 8 }} />
                        Dark Web Scanner Settings
                    </Title>
                    <Text type="secondary">Configure scan defaults and system preferences</Text>
                </div>

                <Row gutter={[24, 24]}>
                    {/* Worker Configuration */}
                    <Col xs={24} lg={12}>
                        <Card
                            title={
                                <span>
                                    <TeamOutlined style={{ marginRight: 8 }} />
                                    Worker Configuration
                                </span>
                            }
                            extra={
                                <Button
                                    type="primary"
                                    icon={<SaveOutlined />}
                                    onClick={handleSaveWorkers}
                                    loading={savingWorkers}
                                    size="small"
                                >
                                    Save
                                </Button>
                            }
                        >
                            {workersLoading ? (
                                <div style={{ textAlign: 'center', padding: 24 }}>
                                    <Spin tip="Loading worker configuration..." />
                                </div>
                            ) : (
                                <div>
                                    <Text strong>Max Concurrent Scans (System-wide)</Text>
                                    <Paragraph type="secondary" style={{ fontSize: 12, marginBottom: 16, marginTop: 4 }}>
                                        How many scans can run at the same time (1-10). This controls the MAX_SCAN_WORKERS setting.
                                    </Paragraph>
                                    <Slider
                                        min={1}
                                        max={10}
                                        value={maxWorkers}
                                        onChange={setMaxWorkers}
                                        marks={{ 1: '1', 3: '3', 5: '5', 8: '8', 10: '10' }}
                                    />
                                    <div style={{
                                        textAlign: 'center',
                                        marginTop: 16,
                                        padding: '8px 16px',
                                        background: '#f6ffed',
                                        border: '1px solid #b7eb8f',
                                        borderRadius: 6,
                                    }}>
                                        <Text strong style={{ fontSize: 18, color: '#389e0d' }}>{maxWorkers}</Text>
                                        <Text type="secondary" style={{ marginLeft: 8 }}>concurrent worker{maxWorkers !== 1 ? 's' : ''}</Text>
                                    </div>
                                    <Alert
                                        type="success"
                                        showIcon
                                        icon={<CheckCircleOutlined />}
                                        message="Changes take effect immediately when saved. No restart required."
                                        style={{ marginTop: 16 }}
                                    />
                                </div>
                            )}
                        </Card>
                    </Col>

                    {/* Search Engines */}
                    <Col xs={24} lg={12}>
                        <Card
                            title={
                                <span>
                                    <GlobalOutlined style={{ marginRight: 8 }} />
                                    Search Engines Configuration
                                </span>
                            }
                            extra={
                                <Button
                                    type="primary"
                                    icon={<SaveOutlined />}
                                    onClick={handleSaveEngines}
                                    loading={savingEngines}
                                    size="small"
                                >
                                    Save Engines
                                </Button>
                            }
                        >
                            {enginesLoading ? (
                                <div style={{ textAlign: 'center', padding: 24 }}>
                                    <Spin tip="Loading engines..." />
                                </div>
                            ) : localEngines.length === 0 ? (
                                <Alert type="warning" message="No engines configured" showIcon />
                            ) : (
                                <div>
                                    <Alert
                                        type="info"
                                        showIcon
                                        message={`${enabledCount} of ${localEngines.length} engines enabled`}
                                        style={{ marginBottom: 16 }}
                                    />
                                    <Row gutter={[12, 12]}>
                                        {localEngines.map(engine => (
                                            <Col xs={24} sm={12} key={engine.name}>
                                                <div
                                                    style={{
                                                        display: 'flex',
                                                        justifyContent: 'space-between',
                                                        alignItems: 'center',
                                                        padding: '10px 12px',
                                                        border: `1px solid ${engine.enabled ? '#b7eb8f' : '#d9d9d9'}`,
                                                        borderRadius: 6,
                                                        background: engine.enabled ? '#f6ffed' : '#fafafa',
                                                    }}
                                                >
                                                    <Text
                                                        style={{
                                                            fontWeight: 500,
                                                            fontSize: 13,
                                                            color: engine.enabled ? '#389e0d' : '#8c8c8c',
                                                        }}
                                                        ellipsis
                                                    >
                                                        {engine.display_name || engine.name}
                                                    </Text>
                                                    <div
                                                        className="dw-toggle-container"
                                                        onClick={() => toggleEngine(engine.name)}
                                                    >
                                                        <div className={`dw-custom-toggle ${engine.enabled ? 'active' : ''}`}>
                                                            <div className="dw-custom-toggle-handle" />
                                                        </div>
                                                    </div>
                                                </div>
                                            </Col>
                                        ))}
                                    </Row>
                                </div>
                            )}
                        </Card>
                    </Col>
                </Row>
            </div>
        </div>
    );
};

export default DarkWebSettingsPage;
