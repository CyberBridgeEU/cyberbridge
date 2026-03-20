import { notification, Card, Table, Tag, Alert, Spin, Button, Modal, List, Typography, Space, Empty, Row, Col, Statistic } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { DatabaseOutlined, CheckCircleOutlined, CloseCircleOutlined, ImportOutlined, EyeOutlined, SafetyCertificateOutlined, BookOutlined, DownloadOutlined } from '@ant-design/icons';
import useControlStore from "../store/useControlStore.ts";
import { useEffect, useState } from "react";
import InfoTitle from "../components/InfoTitle.tsx";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const { Text, Title } = Typography;

const ControlsLibraryInfo = {
    title: "Controls Library",
    description: "Browse and import pre-loaded control sets from industry standards and best practices. Select a control set to preview its controls, then import them into your Control Register.",
    features: [
        "Pre-loaded control sets from industry standards (NIST, ISO 27001, CIS, etc.)",
        "Preview all controls in a set before importing",
        "Import entire control sets with one click",
        "All imported controls start with 'Not Implemented' status",
        "View and manage imported control sets"
    ]
};

interface ControlTemplate {
    code: string;
    name: string;
    description?: string;
}

interface ControlSetTemplate {
    name: string;
    description: string;
    control_count: number;
}

interface ControlSetTemplateDetail {
    name: string;
    description: string;
    controls: ControlTemplate[];
}

const ControlsLibraryPage = () => {
    // Menu highlighting
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Store access
    const {
        controlSets,
        controls,
        fetchControlSets,
        fetchControls,
        fetchControlTemplates,
        fetchControlTemplateDetail,
        importControlsFromTemplate,
        controlTemplates
    } = useControlStore();

    // Initialize notification API
    const [api, contextHolder] = notification.useNotification();

    // State
    const [loading, setLoading] = useState(false);
    const [importing, setImporting] = useState(false);
    const [previewModalVisible, setPreviewModalVisible] = useState(false);
    const [selectedTemplate, setSelectedTemplate] = useState<ControlSetTemplateDetail | null>(null);
    const [loadingPreview, setLoadingPreview] = useState(false);
    const [importResult, setImportResult] = useState<{
        success: boolean;
        imported_count: number;
        failed_count: number;
        message: string;
        errors: string[];
    } | null>(null);

    // Fetch data on component mount
    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                await Promise.all([
                    fetchControlSets(),
                    fetchControls(),
                    fetchControlTemplates()
                ]);
            } catch (error) {
                console.error('Error fetching data:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [fetchControlSets, fetchControls, fetchControlTemplates]);

    // Handle preview template
    const handlePreviewTemplate = async (templateName: string) => {
        setLoadingPreview(true);
        try {
            const detail = await fetchControlTemplateDetail(templateName);
            setSelectedTemplate(detail);
            setPreviewModalVisible(true);
        } catch (error) {
            console.error('Error fetching template detail:', error);
            api.error({
                message: 'Error',
                description: 'Failed to load template details',
            });
        } finally {
            setLoadingPreview(false);
        }
    };

    // Handle import template
    const handleImportTemplate = async (templateName: string) => {
        setImporting(true);
        setImportResult(null);

        try {
            const result = await importControlsFromTemplate(templateName);
            setImportResult(result);

            if (result.success) {
                api.success({
                    message: 'Import Successful',
                    description: result.message,
                    duration: 5,
                });
                // Refresh data
                await fetchControlSets();
                await fetchControls();
                // Close modal if open
                setPreviewModalVisible(false);
            } else {
                api.error({
                    message: 'Import Failed',
                    description: result.message || 'Failed to import controls',
                    duration: 5,
                });
            }
        } catch (error) {
            console.error('Error importing controls:', error);
            api.error({
                message: 'Import Failed',
                description: 'An unexpected error occurred during import',
                duration: 5,
            });
        } finally {
            setImporting(false);
        }
    };

    // Check if a template is already imported
    const isTemplateImported = (templateName: string) => {
        return controlSets.some(cs => cs.name === templateName);
    };

    // Control sets table columns
    const controlSetsColumns = [
        {
            title: 'Control Set Name',
            dataIndex: 'name',
            key: 'name',
            render: (text: string) => <strong>{text}</strong>
        },
        {
            title: 'Description',
            dataIndex: 'description',
            key: 'description',
            render: (text: string) => text || '-'
        },
        {
            title: 'Controls Count',
            key: 'controls_count',
            render: (_: any, record: any) => {
                const count = controls.filter(c => c.control_set_id === record.id).length;
                return <Tag color="blue">{count} controls</Tag>;
            }
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (text: string) => new Date(text).toLocaleDateString()
        }
    ];

    // Preview modal columns
    const previewColumns = [
        {
            title: 'Code',
            dataIndex: 'code',
            key: 'code',
            width: 100,
            render: (text: string) => <Tag>{text}</Tag>
        },
        {
            title: 'Control Name',
            dataIndex: 'name',
            key: 'name',
        },
        {
            title: 'Description',
            dataIndex: 'description',
            key: 'description',
            ellipsis: true,
            render: (text: string) => text || '-'
        }
    ];

    return (
        <div>
            {contextHolder}
            <div className={'page-parent controls-library-page'}>
                <Sidebar
                    selectedKeys={menuHighlighting.selectedKeys}
                    openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange}
                />
                <div className={'page-content'}>
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <DatabaseOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Controls Library"
                                infoContent={ControlsLibraryInfo}
                                className="page-title"
                            />
                        </div>
                    </div>

                    {/* Available Templates Section */}
                    <Card
                        title={
                            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <BookOutlined />
                                Available Control Set Templates
                                {controlTemplates && <Tag color="green">{controlTemplates.length} templates</Tag>}
                            </span>
                        }
                        style={{ marginBottom: '24px' }}
                        loading={loading}
                    >
                        <Alert
                            message="Pre-loaded Control Sets"
                            description="These are industry-standard control sets embedded in the application. Click 'Preview' to see all controls in a set, then 'Import' to add them to your Control Register."
                            type="info"
                            showIcon
                            style={{ marginBottom: '16px' }}
                        />

                        {controlTemplates && controlTemplates.length > 0 ? (
                            <Row gutter={[16, 16]}>
                                {controlTemplates.map((template: ControlSetTemplate, index: number) => {
                                    const imported = isTemplateImported(template.name);
                                    return (
                                        <Col xs={24} sm={12} lg={8} key={index}>
                                            <Card
                                                size="small"
                                                title={
                                                    <Space>
                                                        <SafetyCertificateOutlined style={{ color: '#1890ff' }} />
                                                        <Text strong style={{ fontSize: '14px' }}>{template.name}</Text>
                                                    </Space>
                                                }
                                                extra={
                                                    imported && (
                                                        <Tag color="success" icon={<CheckCircleOutlined />}>
                                                            Imported
                                                        </Tag>
                                                    )
                                                }
                                                actions={[
                                                    <Button
                                                        key="preview"
                                                        type="text"
                                                        icon={<EyeOutlined />}
                                                        onClick={() => handlePreviewTemplate(template.name)}
                                                        loading={loadingPreview}
                                                    >
                                                        Preview
                                                    </Button>,
                                                    <Button
                                                        key="import"
                                                        type="text"
                                                        icon={<ImportOutlined />}
                                                        onClick={() => handleImportTemplate(template.name)}
                                                        loading={importing}
                                                        disabled={imported}
                                                    >
                                                        {imported ? 'Imported' : 'Import'}
                                                    </Button>
                                                ]}
                                            >
                                                <div style={{ minHeight: '80px' }}>
                                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                                        {template.description || 'No description available'}
                                                    </Text>
                                                    <div style={{ marginTop: '12px' }}>
                                                        <Statistic
                                                            title="Controls"
                                                            value={template.control_count}
                                                            valueStyle={{ fontSize: '16px', color: '#1890ff' }}
                                                        />
                                                    </div>
                                                </div>
                                            </Card>
                                        </Col>
                                    );
                                })}
                            </Row>
                        ) : (
                            <Empty
                                description="No control templates available"
                                image={Empty.PRESENTED_IMAGE_SIMPLE}
                            />
                        )}
                    </Card>

                    {/* Import Result */}
                    {importResult && (
                        <Alert
                            message={importResult.success ? "Import Completed" : "Import Failed"}
                            description={
                                <div>
                                    <p>{importResult.message}</p>
                                    <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
                                        <span style={{ color: '#52c41a' }}>
                                            <CheckCircleOutlined /> {importResult.imported_count} imported
                                        </span>
                                        {importResult.failed_count > 0 && (
                                            <span style={{ color: '#ff4d4f' }}>
                                                <CloseCircleOutlined /> {importResult.failed_count} failed
                                            </span>
                                        )}
                                    </div>
                                    {importResult.errors && importResult.errors.length > 0 && (
                                        <div style={{ marginTop: '8px' }}>
                                            <strong>Errors:</strong>
                                            <ul style={{ marginTop: '4px', paddingLeft: '20px' }}>
                                                {importResult.errors.slice(0, 5).map((error, index) => (
                                                    <li key={index} style={{ color: '#ff4d4f' }}>{error}</li>
                                                ))}
                                                {importResult.errors.length > 5 && (
                                                    <li>... and {importResult.errors.length - 5} more errors</li>
                                                )}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            }
                            type={importResult.success ? "success" : "error"}
                            showIcon
                            closable
                            onClose={() => setImportResult(null)}
                            style={{ marginBottom: '24px' }}
                        />
                    )}

                    {/* Imported Control Sets */}
                    <Card
                        title={
                            <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <DatabaseOutlined />
                                Imported Control Sets
                                <Tag color="blue">{controlSets.length}</Tag>
                            </span>
                        }
                    >
                        {controlSets.length === 0 ? (
                            <div style={{ textAlign: 'center', padding: '40px', color: '#8c8c8c' }}>
                                <DatabaseOutlined style={{ fontSize: 48, marginBottom: '16px' }} />
                                <p>No control sets imported yet. Select a template above to get started.</p>
                            </div>
                        ) : (
                            <Table
                                columns={controlSetsColumns}
                                dataSource={controlSets}
                                rowKey="id"
                                pagination={{
                                    showSizeChanger: true,
                                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} control sets`,
                                }}
                                onRow={(record) => ({
                                    onClick: () => {
                                        window.location.href = `/control_registration?control_set=${record.id}`;
                                    },
                                    style: { cursor: 'pointer' }
                                })}
                            />
                        )}
                    </Card>

                    {/* Quick Navigation */}
                    <div style={{ marginTop: '24px', textAlign: 'center' }}>
                        <button
                            className="add-button"
                            onClick={() => window.location.href = '/control_registration'}
                            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
                        >
                            Go to Control Register
                        </button>
                    </div>

                    {/* Preview Modal */}
                    <Modal
                        title={
                            <Space>
                                <SafetyCertificateOutlined style={{ color: '#1890ff' }} />
                                <span>{selectedTemplate?.name}</span>
                            </Space>
                        }
                        open={previewModalVisible}
                        onCancel={() => setPreviewModalVisible(false)}
                        width={900}
                        footer={[
                            <Button key="close" onClick={() => setPreviewModalVisible(false)}>
                                Close
                            </Button>,
                            <Button
                                key="import"
                                type="primary"
                                icon={<DownloadOutlined />}
                                onClick={() => selectedTemplate && handleImportTemplate(selectedTemplate.name)}
                                loading={importing}
                                disabled={selectedTemplate ? isTemplateImported(selectedTemplate.name) : false}
                            >
                                {selectedTemplate && isTemplateImported(selectedTemplate.name) ? 'Already Imported' : 'Import All Controls'}
                            </Button>
                        ]}
                    >
                        {selectedTemplate && (
                            <>
                                <Alert
                                    message={selectedTemplate.description}
                                    type="info"
                                    showIcon
                                    style={{ marginBottom: '16px' }}
                                />
                                <div style={{ marginBottom: '16px' }}>
                                    <Text strong>Total Controls: </Text>
                                    <Tag color="blue">{selectedTemplate.controls.length}</Tag>
                                </div>
                                <Table
                                    columns={previewColumns}
                                    dataSource={selectedTemplate.controls}
                                    rowKey="code"
                                    size="small"
                                    scroll={{ y: 400 }}
                                    pagination={{
                                        pageSize: 50,
                                        showSizeChanger: true,
                                        showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} controls`,
                                    }}
                                />
                            </>
                        )}
                    </Modal>
                </div>
            </div>
        </div>
    );
};

export default ControlsLibraryPage;
