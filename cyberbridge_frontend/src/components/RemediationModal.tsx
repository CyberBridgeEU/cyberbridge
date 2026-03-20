// src/components/RemediationModal.tsx
import { useState, useEffect, useRef } from 'react';
import { Modal, Spin, Button, notification } from 'antd';
import { RobotOutlined, DownloadOutlined, CopyOutlined, CheckOutlined } from '@ant-design/icons';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from '../store/useAuthStore';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface RemediationModalProps {
    visible: boolean;
    onClose: () => void;
    scannerType: 'zap' | 'nmap';
    historyId: string;
    scanTarget?: string;
}

const RemediationModal = ({ visible, onClose, scannerType, historyId, scanTarget }: RemediationModalProps) => {
    const [loading, setLoading] = useState(false);
    const [remediation, setRemediation] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);
    const { getAuthHeader } = useAuthStore();
    const [api, contextHolder] = notification.useNotification();

    // Track the current historyId to detect changes
    const currentHistoryIdRef = useRef<string>(historyId);

    const scannerName = scannerType === 'zap' ? 'Web App Scanner' : 'Network Scanner';

    // Reset state when historyId changes
    useEffect(() => {
        if (historyId !== currentHistoryIdRef.current) {
            setRemediation(null);
            setError(null);
            setLoading(false);
            setCopied(false);
            currentHistoryIdRef.current = historyId;
        }
    }, [historyId]);

    const fetchRemediation = async () => {
        setLoading(true);
        setError(null);
        setRemediation(null);

        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scanners/remediate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader()
                },
                body: JSON.stringify({
                    scanner_type: scannerType,
                    history_id: historyId
                })
            });

            const data = await response.json();

            if (data.success && data.remediation) {
                setRemediation(data.remediation);
            } else {
                setError(data.error || 'Failed to generate remediation guidance');
            }
        } catch (err) {
            setError('Failed to connect to the server. Please try again.');
            console.error('Error fetching remediation:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleOpen = () => {
        if (!remediation && !loading) {
            fetchRemediation();
        }
    };

    const handleClose = () => {
        // Reset state when modal closes
        setRemediation(null);
        setError(null);
        setLoading(false);
        setCopied(false);
        onClose();
    };

    const handleCopy = async () => {
        if (remediation) {
            try {
                await navigator.clipboard.writeText(remediation);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
                api.success({
                    message: 'Copied',
                    description: 'Remediation guidance copied to clipboard',
                    duration: 2,
                });
            } catch (err) {
                api.error({
                    message: 'Copy Failed',
                    description: 'Failed to copy to clipboard',
                    duration: 2,
                });
            }
        }
    };

    const convertMarkdownToHtml = (markdown: string): string => {
        // Convert markdown tables to HTML tables
        const lines = markdown.split('\n');
        let html = '';
        let inTable = false;
        let tableRows: string[] = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();

            // Check if this is a table row (starts and ends with |)
            if (line.startsWith('|') && line.endsWith('|')) {
                // Check if it's a separator row (|---|---|)
                if (line.match(/^\|[\s\-:]+\|$/)) {
                    continue; // Skip separator rows
                }

                if (!inTable) {
                    inTable = true;
                    tableRows = [];
                }
                tableRows.push(line);
            } else {
                // If we were in a table, output it now
                if (inTable && tableRows.length > 0) {
                    html += '<table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px;">';
                    tableRows.forEach((row, rowIndex) => {
                        const cells = row.split('|').filter(cell => cell.trim() !== '');
                        const tag = rowIndex === 0 ? 'th' : 'td';
                        const bgColor = rowIndex === 0 ? 'background-color: #fafafa;' : '';
                        const borderBottom = rowIndex === 0 ? 'border-bottom: 2px solid #1890ff;' : 'border-bottom: 1px solid #e8e8e8;';
                        const fontWeight = rowIndex === 0 ? 'font-weight: 600; color: #1890ff;' : '';
                        html += `<tr style="${bgColor}">`;
                        cells.forEach(cell => {
                            html += `<${tag} style="padding: 10px 12px; text-align: left; ${borderBottom} ${fontWeight}">${cell.trim()}</${tag}>`;
                        });
                        html += '</tr>';
                    });
                    html += '</table>';
                    tableRows = [];
                    inTable = false;
                }

                // Process regular markdown
                let processedLine = line;

                // Headers
                if (processedLine.startsWith('#### ')) {
                    processedLine = `<h4>${processedLine.slice(5)}</h4>`;
                } else if (processedLine.startsWith('### ')) {
                    processedLine = `<h3>${processedLine.slice(4)}</h3>`;
                } else if (processedLine.startsWith('## ')) {
                    processedLine = `<h2>${processedLine.slice(3)}</h2>`;
                } else if (processedLine.startsWith('# ')) {
                    processedLine = `<h1 style="color: #1890ff; border-bottom: 2px solid #1890ff; padding-bottom: 8px;">${processedLine.slice(2)}</h1>`;
                }
                // Bold
                processedLine = processedLine.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #1890ff;">$1</strong>');
                // Inline code
                processedLine = processedLine.replace(/`([^`]+)`/g, '<code style="background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-family: monospace;">$1</code>');
                // List items
                if (processedLine.startsWith('- ') || processedLine.startsWith('* ')) {
                    processedLine = `<li>${processedLine.slice(2)}</li>`;
                } else if (processedLine.match(/^\d+\. /)) {
                    processedLine = `<li>${processedLine.replace(/^\d+\. /, '')}</li>`;
                }

                html += processedLine + (line === '' ? '<br/>' : ' ');
            }
        }

        // Handle table at end of content
        if (inTable && tableRows.length > 0) {
            html += '<table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px;">';
            tableRows.forEach((row, rowIndex) => {
                const cells = row.split('|').filter(cell => cell.trim() !== '');
                const tag = rowIndex === 0 ? 'th' : 'td';
                const bgColor = rowIndex === 0 ? 'background-color: #fafafa;' : '';
                const borderBottom = rowIndex === 0 ? 'border-bottom: 2px solid #1890ff;' : 'border-bottom: 1px solid #e8e8e8;';
                const fontWeight = rowIndex === 0 ? 'font-weight: 600; color: #1890ff;' : '';
                html += `<tr style="${bgColor}">`;
                cells.forEach(cell => {
                    html += `<${tag} style="padding: 10px 12px; text-align: left; ${borderBottom} ${fontWeight}">${cell.trim()}</${tag}>`;
                });
                html += '</tr>';
            });
            html += '</table>';
        }

        return html;
    };

    const handleExportPdf = () => {
        if (!remediation) return;

        // Create a simple text-based PDF export using print functionality
        const printWindow = window.open('', '_blank');
        if (printWindow) {
            const htmlContent = convertMarkdownToHtml(remediation);
            printWindow.document.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>AI Remediation Report - ${scannerName}</title>
                    <style>
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                            max-width: 900px;
                            margin: 0 auto;
                            padding: 40px;
                            line-height: 1.6;
                            color: #333;
                        }
                        h1 { color: #1890ff; border-bottom: 2px solid #1890ff; padding-bottom: 10px; margin-top: 24px; }
                        h2, h3, h4 { color: #333; margin-top: 20px; margin-bottom: 12px; }
                        pre { background: #f5f5f5; padding: 16px; border-radius: 8px; overflow-x: auto; }
                        code { background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
                        ul, ol { padding-left: 24px; }
                        li { margin-bottom: 8px; }
                        table { border: 1px solid #e8e8e8; }
                        .header { margin-bottom: 24px; }
                        .meta { color: #666; font-size: 14px; margin-bottom: 24px; }
                        @media print {
                            body { padding: 20px; }
                            table { page-break-inside: avoid; }
                        }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1 style="margin-top: 0;">AI Remediation Report</h1>
                        <div class="meta">
                            <p><strong>Scanner:</strong> ${scannerName}</p>
                            ${scanTarget ? `<p><strong>Target:</strong> ${scanTarget}</p>` : ''}
                            <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
                        </div>
                    </div>
                    <div class="content">
                        ${htmlContent}
                    </div>
                </body>
                </html>
            `);
            printWindow.document.close();
            printWindow.print();
        }
    };

    return (
        <>
            {contextHolder}
            <Modal
                title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <RobotOutlined style={{ color: '#1890ff' }} />
                        <span>AI Remediation Guidance - {scannerName}</span>
                    </div>
                }
                open={visible}
                onCancel={handleClose}
                afterOpenChange={(open) => {
                    if (open) handleOpen();
                }}
                width={800}
                footer={
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <div>
                            {remediation && (
                                <>
                                    <Button
                                        icon={copied ? <CheckOutlined /> : <CopyOutlined />}
                                        onClick={handleCopy}
                                        style={{ marginRight: '8px' }}
                                    >
                                        {copied ? 'Copied!' : 'Copy'}
                                    </Button>
                                    <Button
                                        icon={<DownloadOutlined />}
                                        onClick={handleExportPdf}
                                    >
                                        Export PDF
                                    </Button>
                                </>
                            )}
                        </div>
                        <div>
                            {error && (
                                <Button
                                    type="primary"
                                    onClick={fetchRemediation}
                                    loading={loading}
                                    style={{ marginRight: '8px' }}
                                >
                                    Retry
                                </Button>
                            )}
                            <Button onClick={handleClose}>Close</Button>
                        </div>
                    </div>
                }
            >
                {scanTarget && (
                    <div style={{
                        marginBottom: '16px',
                        padding: '12px',
                        backgroundColor: '#f5f5f5',
                        borderRadius: '6px',
                        fontSize: '14px'
                    }}>
                        <strong>Scan Target:</strong> {scanTarget}
                    </div>
                )}

                {loading && (
                    <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        padding: '60px 20px',
                        textAlign: 'center'
                    }}>
                        <Spin size="large" />
                        <p style={{ marginTop: '16px', color: '#666' }}>
                            Generating AI remediation guidance...
                        </p>
                        <p style={{ color: '#999', fontSize: '13px' }}>
                            This may take a moment depending on the scan results size.
                        </p>
                    </div>
                )}

                {error && (
                    <div style={{
                        padding: '20px',
                        backgroundColor: '#fff2f0',
                        border: '1px solid #ffccc7',
                        borderRadius: '6px',
                        textAlign: 'center'
                    }}>
                        <p style={{ color: '#ff4d4f', margin: 0 }}>{error}</p>
                    </div>
                )}

                {remediation && (
                    <div style={{
                        maxHeight: '500px',
                        overflowY: 'auto',
                        padding: '16px',
                        backgroundColor: '#fafafa',
                        borderRadius: '6px',
                        border: '1px solid #e8e8e8'
                    }}>
                        <div className="remediation-content" style={{
                            fontSize: '14px',
                            lineHeight: '1.6',
                            color: '#333'
                        }}>
                            <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    h1: ({children}) => <h1 style={{ color: '#1890ff', fontSize: '20px', marginTop: '16px', marginBottom: '12px' }}>{children}</h1>,
                                    h2: ({children}) => <h2 style={{ color: '#333', fontSize: '18px', marginTop: '16px', marginBottom: '10px' }}>{children}</h2>,
                                    h3: ({children}) => <h3 style={{ color: '#333', fontSize: '16px', marginTop: '14px', marginBottom: '8px' }}>{children}</h3>,
                                    h4: ({children}) => <h4 style={{ color: '#333', fontSize: '14px', marginTop: '12px', marginBottom: '6px', fontWeight: '600' }}>{children}</h4>,
                                    p: ({children}) => <p style={{ marginBottom: '12px' }}>{children}</p>,
                                    ul: ({children}) => <ul style={{ paddingLeft: '24px', marginBottom: '12px' }}>{children}</ul>,
                                    ol: ({children}) => <ol style={{ paddingLeft: '24px', marginBottom: '12px' }}>{children}</ol>,
                                    li: ({children}) => <li style={{ marginBottom: '6px' }}>{children}</li>,
                                    table: ({children}) => (
                                        <div style={{ overflowX: 'auto', marginBottom: '16px' }}>
                                            <table style={{
                                                width: '100%',
                                                borderCollapse: 'collapse',
                                                border: '1px solid #e8e8e8',
                                                fontSize: '13px'
                                            }}>
                                                {children}
                                            </table>
                                        </div>
                                    ),
                                    thead: ({children}) => (
                                        <thead style={{ backgroundColor: '#fafafa' }}>
                                            {children}
                                        </thead>
                                    ),
                                    tbody: ({children}) => <tbody>{children}</tbody>,
                                    tr: ({children}) => (
                                        <tr style={{ borderBottom: '1px solid #e8e8e8' }}>
                                            {children}
                                        </tr>
                                    ),
                                    th: ({children}) => (
                                        <th style={{
                                            padding: '10px 12px',
                                            textAlign: 'left',
                                            fontWeight: '600',
                                            color: '#1890ff',
                                            borderBottom: '2px solid #1890ff',
                                            whiteSpace: 'nowrap'
                                        }}>
                                            {children}
                                        </th>
                                    ),
                                    td: ({children}) => (
                                        <td style={{
                                            padding: '10px 12px',
                                            borderBottom: '1px solid #f0f0f0',
                                            verticalAlign: 'top'
                                        }}>
                                            {children}
                                        </td>
                                    ),
                                    code: ({className, children}) => {
                                        const isBlock = className?.includes('language-');
                                        if (isBlock) {
                                            return (
                                                <pre style={{
                                                    backgroundColor: '#f0f0f0',
                                                    padding: '12px',
                                                    borderRadius: '6px',
                                                    overflow: 'auto',
                                                    fontSize: '13px',
                                                    fontFamily: 'monospace'
                                                }}>
                                                    <code>{children}</code>
                                                </pre>
                                            );
                                        }
                                        return (
                                            <code style={{
                                                backgroundColor: '#f0f0f0',
                                                padding: '2px 6px',
                                                borderRadius: '4px',
                                                fontSize: '13px',
                                                fontFamily: 'monospace'
                                            }}>
                                                {children}
                                            </code>
                                        );
                                    },
                                    pre: ({children}) => <>{children}</>,
                                    strong: ({children}) => <strong style={{ fontWeight: '600', color: '#1890ff' }}>{children}</strong>,
                                }}
                            >
                                {remediation}
                            </ReactMarkdown>
                        </div>
                    </div>
                )}
            </Modal>
        </>
    );
};

export default RemediationModal;
