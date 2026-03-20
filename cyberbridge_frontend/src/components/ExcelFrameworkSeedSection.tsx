import React, { useState } from 'react';
import { Upload, notification, Card, Statistic, Row, Col, Input, Button, Alert, Select } from 'antd';
import { UploadOutlined, FileExcelOutlined, InfoCircleOutlined, FileImageOutlined } from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd';
import { cyberbridge_back_end_rest_api } from '../constants/urls.ts';
import useAuthStore from '../store/useAuthStore.ts';

interface AnalysisMetrics {
    conformity_questions: {
        total: number;
        unique: number;
        reduction_percent: number;
    };
    audit_questions: {
        total: number;
        unique: number;
        reduction_percent: number;
    };
    objectives: {
        total: number;
        unique: number;
        reduction_percent: number;
    };
}

interface AnalysisResponse {
    success: boolean;
    filename: string;
    column_mapping: Record<string, string>;
    metrics: AnalysisMetrics;
    total_rows: number;
}

interface GenerateResponse {
    success: boolean;
    message: string;
    filename: string;
    file_path: string;
    metrics: AnalysisMetrics;
}

interface ExcelFrameworkSeedSectionProps {
    onSeedGenerated?: () => void;
}

const ExcelFrameworkSeedSection: React.FC<ExcelFrameworkSeedSectionProps> = ({ onSeedGenerated }) => {
    const [api, contextHolder] = notification.useNotification();
    const [fileList, setFileList] = useState<UploadFile[]>([]);
    const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [frameworkName, setFrameworkName] = useState('');
    const [frameworkDescription, setFrameworkDescription] = useState('');
    const [logoFile, setLogoFile] = useState<UploadFile[]>([]);
    const [allowedScopeTypes, setAllowedScopeTypes] = useState<string[]>([]);
    const [scopeSelectionMode, setScopeSelectionMode] = useState<string>('optional');
    const getAuthHeader = useAuthStore(state => state.getAuthHeader);

    const handleAnalyze: UploadProps['customRequest'] = async (options) => {
        const { file, onSuccess, onError } = options;

        setLoading(true);
        const formData = new FormData();
        formData.append('file', file as File);

        try {
            const authHeader = getAuthHeader();
            if (!authHeader) {
                throw new Error('Not authenticated. Please log in again.');
            }

            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/frameworks/analyze-excel`,
                {
                    method: 'POST',
                    headers: authHeader,
                    body: formData,
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to analyze Excel file');
            }

            const data: AnalysisResponse = await response.json();
            setAnalysisResult(data);

            // Pre-fill framework name with filename (without extension)
            const fileNameWithoutExt = data.filename.replace(/\.(xlsx|xls)$/i, '');
            setFrameworkName(fileNameWithoutExt);

            if (onSuccess) onSuccess(data);

            api.success({
                message: 'Analysis Complete',
                description: 'Excel file analyzed successfully. Review the metrics below.',
                duration: 4,
            });
        } catch (error: any) {
            console.error('Analysis error:', error);
            if (onError) onError(error);

            const errorMessage = error.message || 'Failed to analyze Excel file';
            api.error({
                message: 'Analysis Failed',
                description: errorMessage,
                duration: 4,
            });
        } finally {
            setLoading(false);
        }
    };

    const handleFileChange: UploadProps['onChange'] = (info) => {
        let newFileList = [...info.fileList];

        // Limit to only one file
        newFileList = newFileList.slice(-1);

        // Update file list
        setFileList(newFileList);

        // Clear analysis result when file changes
        if (info.fileList.length === 0) {
            setAnalysisResult(null);
        }
    };

    const handleRemoveFile = () => {
        setFileList([]);
        setAnalysisResult(null);
    };

    const handleGenerateSeed = async () => {
        if (!analysisResult) {
            api.warning({
                message: 'No Analysis Available',
                description: 'Please analyze an Excel file first!',
                duration: 4,
            });
            return;
        }

        if (!frameworkName || frameworkName.trim() === '') {
            api.error({
                message: 'Validation Error',
                description: 'Framework name is required!',
                duration: 4,
            });
            return;
        }

        if (!fileList[0]?.originFileObj) {
            api.error({
                message: 'File Missing',
                description: 'Please upload an Excel file first!',
                duration: 4,
            });
            return;
        }

        setLoading(true);
        const formData = new FormData();
        formData.append('file', fileList[0].originFileObj);
        formData.append('framework_name', frameworkName.trim());
        formData.append('framework_description', frameworkDescription.trim() || '');

        // Add scope configuration
        if (allowedScopeTypes.length > 0) {
            formData.append('allowed_scope_types', JSON.stringify(allowedScopeTypes));
        }
        formData.append('scope_selection_mode', scopeSelectionMode);

        // Add logo file if uploaded
        if (logoFile.length > 0 && logoFile[0].originFileObj) {
            formData.append('logo', logoFile[0].originFileObj);
        }

        try {
            const authHeader = getAuthHeader();
            if (!authHeader) {
                throw new Error('Not authenticated. Please log in again.');
            }

            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/frameworks/generate-seed-file`,
                {
                    method: 'POST',
                    headers: authHeader,
                    body: formData,
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to generate seed file');
            }

            const data: GenerateResponse = await response.json();

            // Prepare description with logo instructions if logo was uploaded
            let description = data.message;
            if (logoFile.length > 0) {
                description += '\n\nTo make the new logo appear, you need to:\n• Manually add the import statement for the new logo in HomePage.tsx\n• Manually add the mapping in the getFrameworkLogo() function';
            }

            api.success({
                message: 'Seed File Generated',
                description: description,
                duration: 8,
            });

            // Clear state
            setFileList([]);
            setAnalysisResult(null);
            setFrameworkName('');
            setFrameworkDescription('');
            setLogoFile([]);
            setAllowedScopeTypes([]);
            setScopeSelectionMode('optional');

            // Trigger callback to refetch templates
            if (onSeedGenerated) {
                onSeedGenerated();
            }

        } catch (error: any) {
            console.error('Generation error:', error);
            const errorMessage = error.message || 'Failed to generate seed file';

            api.error({
                message: 'Seed File Generation Failed',
                description: errorMessage,
                duration: 6,
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            {contextHolder}
            <div style={{ marginBottom: '20px' }}>
                <Alert
                    message="Superadmin Feature"
                    description="This section is only accessible to superadmin@clone-systems.com account. Upload an Excel file in the same format as ISO 27001 or NIS2 Directive to create a new framework seed template."
                    type="info"
                    icon={<InfoCircleOutlined />}
                    showIcon
                    closable
                />
            </div>

            <div style={{ marginBottom: '20px' }}>
                <Upload
                    accept=".xlsx,.xls"
                    fileList={fileList}
                    onChange={handleFileChange}
                    customRequest={handleAnalyze}
                    onRemove={handleRemoveFile}
                    maxCount={1}
                >
                    <Button
                        icon={<UploadOutlined />}
                        loading={loading}
                        disabled={loading}
                    >
                        {loading ? 'Analyzing...' : 'Upload and Analyze Excel'}
                    </Button>
                </Upload>
            </div>

            {analysisResult && (
                <div style={{ marginTop: '24px' }}>
                    <Card
                        title={
                            <span>
                                <FileExcelOutlined style={{ marginRight: '8px', color: '#52c41a' }} />
                                Analysis Results: {analysisResult.filename}
                            </span>
                        }
                        style={{ marginBottom: '20px' }}
                    >
                        <Row gutter={[16, 16]}>
                            <Col xs={24} sm={12} md={8}>
                                <Card>
                                    <Statistic
                                        title="Conformity Questions"
                                        value={analysisResult.metrics.conformity_questions.unique}
                                        suffix={`/ ${analysisResult.metrics.conformity_questions.total}`}
                                        valueStyle={{ color: '#3f8600' }}
                                    />
                                    <div style={{ marginTop: '8px', fontSize: '14px', color: '#8c8c8c' }}>
                                        {analysisResult.metrics.conformity_questions.reduction_percent}% reduction
                                    </div>
                                </Card>
                            </Col>

                            {analysisResult.metrics.audit_questions.total > 0 && (
                                <Col xs={24} sm={12} md={8}>
                                    <Card>
                                        <Statistic
                                            title="Audit Questions"
                                            value={analysisResult.metrics.audit_questions.unique}
                                            suffix={`/ ${analysisResult.metrics.audit_questions.total}`}
                                            valueStyle={{ color: '#1890ff' }}
                                        />
                                        <div style={{ marginTop: '8px', fontSize: '14px', color: '#8c8c8c' }}>
                                            {analysisResult.metrics.audit_questions.reduction_percent}% reduction
                                        </div>
                                    </Card>
                                </Col>
                            )}

                            <Col xs={24} sm={12} md={8}>
                                <Card>
                                    <Statistic
                                        title="Objectives"
                                        value={analysisResult.metrics.objectives.unique}
                                        suffix={`/ ${analysisResult.metrics.objectives.total}`}
                                        valueStyle={{ color: '#cf1322' }}
                                    />
                                    <div style={{ marginTop: '8px', fontSize: '14px', color: '#8c8c8c' }}>
                                        {analysisResult.metrics.objectives.reduction_percent}% reduction
                                    </div>
                                </Card>
                            </Col>

                            <Col xs={24} sm={12} md={8}>
                                <Card>
                                    <Statistic
                                        title="Total Rows Processed"
                                        value={analysisResult.total_rows}
                                        valueStyle={{ color: '#722ed1' }}
                                    />
                                </Card>
                            </Col>
                        </Row>

                        <div style={{ marginTop: '24px' }}>
                            <Row gutter={[16, 16]}>
                                <Col xs={24} md={12}>
                                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                                        Framework Name <span style={{ color: 'red' }}>*</span>
                                    </label>
                                    <Input
                                        placeholder="Enter framework name (e.g., GDPR, NIST)"
                                        value={frameworkName}
                                        onChange={(e) => setFrameworkName(e.target.value)}
                                        maxLength={100}
                                        size="large"
                                    />
                                </Col>
                                <Col xs={24} md={12}>
                                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                                        Framework Description
                                    </label>
                                    <Input.TextArea
                                        placeholder="Enter framework description"
                                        value={frameworkDescription}
                                        onChange={(e) => setFrameworkDescription(e.target.value)}
                                        rows={1}
                                        maxLength={500}
                                        size="large"
                                        autoSize={{ minRows: 1, maxRows: 4 }}
                                    />
                                </Col>
                                <Col xs={24} md={12}>
                                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                                        Framework Logo (Optional)
                                    </label>
                                    <Upload
                                        accept="image/*"
                                        fileList={logoFile}
                                        onChange={({ fileList }) => setLogoFile(fileList.slice(-1))}
                                        beforeUpload={() => false}
                                        maxCount={1}
                                        listType="picture"
                                    >
                                        <Button icon={<FileImageOutlined />} size="large">
                                            Upload Logo
                                        </Button>
                                    </Upload>
                                    <div style={{ marginTop: '4px', fontSize: '12px', color: '#8c8c8c' }}>
                                        Supported formats: PNG, JPG, SVG, WEBP
                                    </div>
                                </Col>
                            </Row>

                            <div style={{ marginTop: '24px' }}>
                                <Row gutter={[16, 16]}>
                                    <Col xs={24} md={12}>
                                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                                            Allowed Scope Types (Optional)
                                        </label>
                                        <Select
                                            mode="multiple"
                                            placeholder="Select allowed scope types"
                                            value={allowedScopeTypes}
                                            onChange={setAllowedScopeTypes}
                                            size="large"
                                            style={{ width: '100%' }}
                                            options={[
                                                { label: 'Asset / Product', value: 'Product' },
                                                { label: 'Organization', value: 'Organization' },
                                                { label: 'Other', value: 'Other' },
                                                { label: 'Asset / Product (Reserved)', value: 'Asset', disabled: true },
                                                { label: 'Project (Coming Soon)', value: 'Project', disabled: true },
                                                { label: 'Process (Coming Soon)', value: 'Process', disabled: true }
                                            ]}
                                        />
                                        <div style={{ marginTop: '4px', fontSize: '12px', color: '#8c8c8c' }}>
                                            Which scope types can be used with this framework
                                        </div>
                                    </Col>
                                    <Col xs={24} md={12}>
                                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>
                                            Scope Selection Mode
                                        </label>
                                        <Select
                                            placeholder="Select scope selection mode"
                                            value={scopeSelectionMode}
                                            onChange={setScopeSelectionMode}
                                            size="large"
                                            style={{ width: '100%' }}
                                            options={[
                                                { label: 'Optional', value: 'optional' },
                                                { label: 'Required', value: 'required' }
                                            ]}
                                        />
                                        <div style={{ marginTop: '4px', fontSize: '12px', color: '#8c8c8c' }}>
                                            Whether scope selection is required for assessments
                                        </div>
                                    </Col>
                                </Row>
                            </div>
                        </div>

                        <div style={{ marginTop: '24px', textAlign: 'center' }}>
                            <Button
                                type="primary"
                                size="large"
                                onClick={handleGenerateSeed}
                                loading={loading}
                                disabled={loading || !frameworkName.trim()}
                            >
                                Generate Seed File
                            </Button>
                        </div>
                    </Card>

                    <Alert
                        message="Detected Columns"
                        description={
                            <div>
                                {Object.entries(analysisResult.column_mapping).map(([field, column]) => (
                                    <div key={field} style={{ marginBottom: '4px' }}>
                                        <strong>{field}:</strong> {column}
                                    </div>
                                ))}
                            </div>
                        }
                        type="success"
                        showIcon
                    />
                </div>
            )}
        </div>
    );
};

export default ExcelFrameworkSeedSection;
