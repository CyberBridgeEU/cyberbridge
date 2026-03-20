// src/components/onboarding/AIProviderConfigStep.tsx
import React, { useState, useEffect } from 'react';
import { Form, Select, Input, Typography, Card, Alert, Spin, notification, Space } from 'antd';
import {
    RobotOutlined,
    ApiOutlined,
    KeyOutlined,
    LinkOutlined,
    CheckCircleOutlined
} from '@ant-design/icons';
import useOnboardingStore, { AIConfig } from '../../store/useOnboardingStore';
import useAuthStore from '../../store/useAuthStore';
import useUserStore from '../../store/useUserStore';
import { cyberbridge_back_end_rest_api } from '../../constants/urls';

const { Title, Text, Paragraph } = Typography;

interface Provider {
    id: string;
    name: string;
    description: string;
    requiresApiKey: boolean;
    requiresBaseUrl: boolean;
    modelOptions?: string[];
    defaultModel?: string;
}

const providers: Provider[] = [
    {
        id: 'llamacpp',
        name: 'llama.cpp (Self-hosted)',
        description: 'Efficient CPU-optimized inference with llama.cpp. No API key required.',
        requiresApiKey: false,
        requiresBaseUrl: false,
        modelOptions: ['phi-4-Q4_K_M'],
        defaultModel: 'phi-4-Q4_K_M'
    },
    {
        id: 'openai',
        name: 'OpenAI',
        description: 'Access GPT models from OpenAI. Requires API key.',
        requiresApiKey: true,
        requiresBaseUrl: false,
        modelOptions: ['gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
        defaultModel: 'gpt-4o'
    },
    {
        id: 'anthropic',
        name: 'Anthropic',
        description: 'Access Claude models from Anthropic. Requires API key.',
        requiresApiKey: true,
        requiresBaseUrl: false,
        modelOptions: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
        defaultModel: 'claude-3-sonnet'
    },
    {
        id: 'google',
        name: 'Google AI',
        description: 'Access Gemini models from Google. Requires API key.',
        requiresApiKey: true,
        requiresBaseUrl: false,
        modelOptions: ['gemini-pro', 'gemini-pro-vision'],
        defaultModel: 'gemini-pro'
    },
    {
        id: 'xai',
        name: 'X AI (Grok)',
        description: 'Access Grok models from X AI. Requires API key.',
        requiresApiKey: true,
        requiresBaseUrl: false,
        modelOptions: ['grok-1'],
        defaultModel: 'grok-1'
    },
    {
        id: 'qlon',
        name: 'QLON',
        description: 'Custom AI provider with tool integration support.',
        requiresApiKey: true,
        requiresBaseUrl: true,
        modelOptions: [],
        defaultModel: ''
    }
];

const AIProviderConfigStep: React.FC = () => {
    const [form] = Form.useForm();
    const [api, contextHolder] = notification.useNotification();
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);

    const { aiConfig, setAIConfig } = useOnboardingStore();
    const authStore = useAuthStore();
    const { current_user } = useUserStore();

    useEffect(() => {
        // Set initial form values from store
        form.setFieldsValue({
            provider: aiConfig.provider || 'llamacpp',
            apiKey: aiConfig.apiKey || '',
            model: aiConfig.model || '',
            baseUrl: aiConfig.baseUrl || ''
        });
    }, [aiConfig, form]);

    const selectedProvider = providers.find(p => p.id === (form.getFieldValue('provider') || aiConfig.provider)) || providers[0];

    const handleProviderChange = (providerId: string) => {
        const provider = providers.find(p => p.id === providerId);
        if (provider) {
            form.setFieldsValue({
                provider: providerId,
                model: provider.defaultModel || '',
                apiKey: '',
                baseUrl: ''
            });
            setSaved(false);
        }
    };

    const handleSaveConfig = async (values: { provider: string; apiKey?: string; model?: string; baseUrl?: string }) => {
        setSaving(true);
        try {
            const orgId = current_user?.organisation_id;
            if (!orgId) {
                throw new Error('Organization ID not found');
            }

            // Build the request body based on the provider
            const requestBody: Record<string, unknown> = {
                llm_provider: values.provider
            };

            if (values.apiKey) {
                requestBody.api_key = values.apiKey;
            }
            if (values.model) {
                requestBody.model = values.model;
            }
            if (values.baseUrl) {
                requestBody.base_url = values.baseUrl;
            }

            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/org-llm/${orgId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...authStore.getAuthHeader()
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                throw new Error('Failed to save AI configuration');
            }

            // Update the store
            setAIConfig({
                provider: values.provider,
                apiKey: values.apiKey,
                model: values.model,
                baseUrl: values.baseUrl
            });

            setSaved(true);
            api.success({
                message: 'Configuration Saved',
                description: 'AI provider settings have been saved successfully.'
            });
        } catch (error) {
            api.error({
                message: 'Error',
                description: error instanceof Error ? error.message : 'Failed to save AI configuration.'
            });
        } finally {
            setSaving(false);
        }
    };

    return (
        <div>
            {contextHolder}
            <div style={{ marginBottom: '24px' }}>
                <Title level={4} style={{ marginBottom: '8px', color: '#1a365d' }}>
                    Configure AI Provider
                </Title>
                <Text type="secondary">
                    Set up your AI provider for intelligent analysis and recommendations. You can use the built-in llama.cpp or connect an external provider.
                </Text>
            </div>

            {saved && (
                <Alert
                    message="Configuration saved"
                    type="success"
                    showIcon
                    icon={<CheckCircleOutlined />}
                    style={{ marginBottom: '16px' }}
                />
            )}

            <Form
                form={form}
                layout="vertical"
                onFinish={handleSaveConfig}
                initialValues={{
                    provider: aiConfig.provider || 'llamacpp',
                    model: aiConfig.model || 'phi-4-Q4_K_M'
                }}
            >
                <Form.Item
                    name="provider"
                    label="AI Provider"
                    rules={[{ required: true }]}
                >
                    <Select
                        size="large"
                        onChange={handleProviderChange}
                        optionLabelProp="label"
                    >
                        {providers.map(provider => (
                            <Select.Option
                                key={provider.id}
                                value={provider.id}
                                label={provider.name}
                            >
                                <div>
                                    <div style={{ fontWeight: 500 }}>{provider.name}</div>
                                    <div style={{ fontSize: '12px', color: '#8c8c8c' }}>
                                        {provider.description}
                                    </div>
                                </div>
                            </Select.Option>
                        ))}
                    </Select>
                </Form.Item>

                <Card
                    size="small"
                    style={{
                        backgroundColor: '#f5f5f5',
                        border: '1px dashed #d9d9d9',
                        marginBottom: '16px'
                    }}
                >
                    <Space>
                        <RobotOutlined style={{ color: '#0f386a' }} />
                        <Text type="secondary" style={{ fontSize: '13px' }}>
                            {selectedProvider.description}
                        </Text>
                    </Space>
                </Card>

                {selectedProvider.requiresApiKey && (
                    <Form.Item
                        name="apiKey"
                        label="API Key"
                        rules={[{ required: true, message: 'API key is required for this provider' }]}
                    >
                        <Input.Password
                            size="large"
                            prefix={<KeyOutlined style={{ color: '#8c8c8c' }} />}
                            placeholder={`Enter your ${selectedProvider.name} API key`}
                        />
                    </Form.Item>
                )}

                {selectedProvider.requiresBaseUrl && (
                    <Form.Item
                        name="baseUrl"
                        label="Base URL"
                        rules={[{ required: true, message: 'Base URL is required for this provider' }]}
                    >
                        <Input
                            size="large"
                            prefix={<LinkOutlined style={{ color: '#8c8c8c' }} />}
                            placeholder="https://api.example.com"
                        />
                    </Form.Item>
                )}

                {selectedProvider.modelOptions && selectedProvider.modelOptions.length > 0 && (
                    <Form.Item
                        name="model"
                        label="Model"
                    >
                        <Select
                            size="large"
                            placeholder="Select a model"
                        >
                            {selectedProvider.modelOptions.map(model => (
                                <Select.Option key={model} value={model}>
                                    {model}
                                </Select.Option>
                            ))}
                        </Select>
                    </Form.Item>
                )}

                <Form.Item style={{ marginBottom: 0 }}>
                    <button
                        type="submit"
                        disabled={saving}
                        className="view-button"
                        style={{
                            width: '100%',
                            height: '40px',
                            backgroundColor: '#0f386a',
                            border: 'none',
                            cursor: saving ? 'wait' : 'pointer'
                        }}
                    >
                        {saving ? <Spin size="small" /> : 'Save Configuration'}
                    </button>
                </Form.Item>
            </Form>

            <div style={{ marginTop: '16px', textAlign: 'center' }}>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                    This step is optional. You can configure AI providers later from the Settings page.
                </Text>
            </div>
        </div>
    );
};

export default AIProviderConfigStep;
