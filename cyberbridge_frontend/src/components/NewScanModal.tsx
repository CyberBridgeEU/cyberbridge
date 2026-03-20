import { useState, useEffect } from 'react';
import { Modal, Form, Input, Slider, Typography, Alert, message } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import useDarkWebStore from '../store/useDarkWebStore';

const { Text, Paragraph } = Typography;

interface NewScanModalProps {
    open: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

const NewScanModal: React.FC<NewScanModalProps> = ({ open, onClose, onSuccess }) => {
    const [form] = Form.useForm();
    const { createScan, loading, fetchEngines, engines } = useDarkWebStore();
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (open) {
            form.resetFields();
            fetchEngines();
        }
    }, [open]);

    const handleOk = async () => {
        try {
            const values = await form.validateFields();
            setSubmitting(true);
            const result = await createScan(values.keyword, values.mpUnits, values.pageLimit);
            if (result) {
                message.success(`Scan queued successfully! Queue position: ${result.queue_position}`);
                form.resetFields();
                onClose();
                if (onSuccess) onSuccess();
            }
        } catch (e: any) {
            if (e.errorFields) return; // form validation error
            message.error(e.message || 'Failed to create scan');
        } finally {
            setSubmitting(false);
        }
    };

    const enabledEngines = engines.filter(e => e.enabled);

    return (
        <Modal
            title={
                <span>
                    <SearchOutlined style={{ marginRight: 8 }} />
                    New Dark Web Scan
                </span>
            }
            open={open}
            onOk={handleOk}
            onCancel={onClose}
            okText="Start Scan"
            okButtonProps={{ loading: submitting || loading, icon: <SearchOutlined /> }}
            cancelButtonProps={{ disabled: submitting }}
            destroyOnClose
            width={560}
        >
            <Form
                form={form}
                layout="vertical"
                initialValues={{ keyword: '', mpUnits: 2, pageLimit: 3 }}
            >
                <Form.Item
                    name="keyword"
                    label="Keyword / Search Term"
                    rules={[
                        { required: true, message: 'Please enter a keyword to search' },
                        { max: 200, message: 'Maximum 200 characters' },
                    ]}
                >
                    <Input
                        placeholder="e.g., cybersecurity threats, ransomware, data breach"
                        maxLength={200}
                    />
                </Form.Item>

                <Form.Item
                    name="mpUnits"
                    label="Processing Units (CPU cores per scan)"
                    tooltip="Controls internal processing speed of one scan (1-10)"
                >
                    <Slider min={1} max={10} marks={{ 1: '1', 5: '5', 10: '10' }} />
                </Form.Item>

                <Form.Item
                    name="pageLimit"
                    label="Page Limit per Engine"
                    tooltip="Maximum pages to scan per engine. Higher = more data but slower."
                >
                    <Slider min={1} max={50} marks={{ 1: '1', 10: '10', 25: '25', 50: '50' }} />
                </Form.Item>

                <Alert
                    type="info"
                    showIcon
                    message="About Dark Web Scanning"
                    description={
                        <div>
                            <Paragraph style={{ margin: 0, fontSize: 13 }}>
                                This scan searches the dark web using configured search engines for mentions
                                of your keyword. Results are categorized by type (passwords, credentials,
                                emails, leaks, databases, etc.) and compiled into a report.
                            </Paragraph>
                            {enabledEngines.length > 0 && (
                                <Text type="secondary" style={{ fontSize: 12, marginTop: 8, display: 'block' }}>
                                    Active engines: {enabledEngines.map(e => e.display_name || e.name).join(', ')}
                                </Text>
                            )}
                        </div>
                    }
                    style={{ marginTop: 8 }}
                />
            </Form>
        </Modal>
    );
};

export default NewScanModal;
