import { useEffect, useState } from 'react';
import { Table, Button, Modal, Input, InputNumber, Tag, Popconfirm, notification, Form } from 'antd';
import { PlusOutlined, DeleteOutlined, CopyOutlined, KeyOutlined } from '@ant-design/icons';
import useApiKeyStore, { ApiKeyInfo } from '../store/useApiKeyStore';

const ApiKeyManagement = () => {
    const { apiKeys, loading, fetchApiKeys, createApiKey, revokeApiKey } = useApiKeyStore();
    const [createModalOpen, setCreateModalOpen] = useState(false);
    const [newKeyResult, setNewKeyResult] = useState<string | null>(null);
    const [form] = Form.useForm();
    const [api, contextHolder] = notification.useNotification();

    useEffect(() => {
        fetchApiKeys();
    }, []);

    const handleCreate = async () => {
        try {
            const values = await form.validateFields();
            const fullKey = await createApiKey(
                values.name,
                values.description,
                values.expiresInDays,
            );
            if (fullKey) {
                setNewKeyResult(fullKey);
                form.resetFields();
                setCreateModalOpen(false);
            }
        } catch {
            // validation error
        }
    };

    const handleCopyKey = () => {
        if (newKeyResult) {
            navigator.clipboard.writeText(newKeyResult);
            api.success({ message: 'API key copied to clipboard' });
        }
    };

    const handleRevoke = async (keyId: string) => {
        const success = await revokeApiKey(keyId);
        if (success) {
            api.success({ message: 'API key revoked' });
        } else {
            api.error({ message: 'Failed to revoke API key' });
        }
    };

    const columns = [
        {
            title: 'Name',
            dataIndex: 'name',
            key: 'name',
        },
        {
            title: 'Key Prefix',
            dataIndex: 'key_prefix',
            key: 'key_prefix',
            render: (prefix: string) => <code>{prefix}...</code>,
        },
        {
            title: 'Status',
            dataIndex: 'is_active',
            key: 'is_active',
            render: (active: boolean, record: ApiKeyInfo) => (
                record.revoked_at
                    ? <Tag color="red">Revoked</Tag>
                    : active
                        ? <Tag color="green">Active</Tag>
                        : <Tag color="default">Inactive</Tag>
            ),
        },
        {
            title: 'Created',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string | null) =>
                date ? new Date(date).toLocaleDateString() : '-',
        },
        {
            title: 'Expires',
            dataIndex: 'expires_at',
            key: 'expires_at',
            render: (date: string | null) =>
                date ? new Date(date).toLocaleDateString() : 'Never',
        },
        {
            title: 'Last Used',
            dataIndex: 'last_used_at',
            key: 'last_used_at',
            render: (date: string | null) =>
                date ? new Date(date).toLocaleDateString() : 'Never',
        },
        {
            title: 'Actions',
            key: 'actions',
            render: (_: any, record: ApiKeyInfo) => (
                record.is_active && !record.revoked_at ? (
                    <Popconfirm
                        title="Revoke this API key?"
                        description="This action cannot be undone."
                        onConfirm={() => handleRevoke(record.id)}
                        okText="Revoke"
                        okButtonProps={{ danger: true }}
                    >
                        <Button danger size="small" icon={<DeleteOutlined />}>
                            Revoke
                        </Button>
                    </Popconfirm>
                ) : null
            ),
        },
    ];

    return (
        <div>
            {contextHolder}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                    <p style={{ color: '#8c8c8c', margin: 0 }}>
                        API keys allow programmatic access to CyberBridge without a browser session.
                    </p>
                </div>
                <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setCreateModalOpen(true)}
                >
                    Create API Key
                </Button>
            </div>

            <Table
                dataSource={apiKeys}
                columns={columns}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 10 }}
                size="small"
                locale={{ emptyText: 'No API keys. Create one to get started.' }}
            />

            {/* Create Modal */}
            <Modal
                title="Create API Key"
                open={createModalOpen}
                onOk={handleCreate}
                onCancel={() => { setCreateModalOpen(false); form.resetFields(); }}
                okText="Create"
                confirmLoading={loading}
            >
                <Form form={form} layout="vertical">
                    <Form.Item
                        name="name"
                        label="Key Name"
                        rules={[{ required: true, message: 'Please enter a name' }]}
                    >
                        <Input placeholder="e.g. CI/CD Pipeline" />
                    </Form.Item>
                    <Form.Item name="description" label="Description">
                        <Input.TextArea placeholder="What is this key for?" rows={2} />
                    </Form.Item>
                    <Form.Item name="expiresInDays" label="Expires In (days)">
                        <InputNumber
                            min={1}
                            max={365}
                            placeholder="Leave empty for no expiration"
                            style={{ width: '100%' }}
                        />
                    </Form.Item>
                </Form>
            </Modal>

            {/* Show Key Modal — displayed once after creation */}
            <Modal
                title={<span><KeyOutlined style={{ marginRight: 8 }} />API Key Created</span>}
                open={!!newKeyResult}
                onOk={() => setNewKeyResult(null)}
                onCancel={() => setNewKeyResult(null)}
                okText="Done"
                cancelButtonProps={{ style: { display: 'none' } }}
            >
                <p style={{ color: '#ff4d4f', fontWeight: 600, marginBottom: 12 }}>
                    Copy this key now. You will not be able to see it again.
                </p>
                <div style={{
                    display: 'flex',
                    gap: 8,
                    padding: '12px',
                    backgroundColor: '#f5f5f5',
                    borderRadius: '6px',
                    border: '1px solid #d9d9d9',
                    alignItems: 'center',
                }}>
                    <code style={{ flex: 1, wordBreak: 'break-all', fontSize: '13px' }}>
                        {newKeyResult}
                    </code>
                    <Button
                        icon={<CopyOutlined />}
                        onClick={handleCopyKey}
                        type="primary"
                        size="small"
                    >
                        Copy
                    </Button>
                </div>
                <div style={{ marginTop: 16, padding: '12px', backgroundColor: '#f0f8ff', borderRadius: '6px' }}>
                    <p style={{ margin: 0, fontSize: '13px', color: '#595959' }}>
                        <strong>Usage:</strong> Include this key in the <code>X-API-Key</code> header of your HTTP requests:
                    </p>
                    <code style={{ display: 'block', marginTop: 8, fontSize: '12px', color: '#333' }}>
                        curl -H "X-API-Key: {newKeyResult?.slice(0, 10)}..." {window.location.origin}/api/endpoint
                    </code>
                </div>
            </Modal>
        </div>
    );
};

export default ApiKeyManagement;
