import { useEffect, useState, useMemo, useRef, useCallback } from "react";
import { Spin, Empty, Dropdown, message } from "antd";
import type { MenuProps } from "antd";
import {
    BookOutlined,
    ApiOutlined,
    UserOutlined,
    TeamOutlined,
    CrownOutlined,
    RocketOutlined,
    ThunderboltOutlined,
    SafetyCertificateOutlined,
    DownloadOutlined,
    PlayCircleOutlined,
    FileTextOutlined,
    FileMarkdownOutlined,
    FilePdfOutlined
} from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import useAuthStore from '../store/useAuthStore';
import useUserStore from '../store/useUserStore';
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { downloadAsText, downloadAsMarkdown, downloadAsPdf } from '../utils/docExportUtils';

interface DocItem {
    key: string;
    label: string;
    icon: React.ReactNode;
    file: string;
    roles: string[];
    downloadFile?: string;
}

// Define available documentation based on roles
const documentationItems: DocItem[] = [
    {
        key: 'user_guide',
        label: 'User Guide',
        icon: <BookOutlined />,
        file: 'USER_GUIDE.md',
        roles: ['org_user', 'org_admin', 'super_admin']
    },
    {
        key: 'user_flow_examples',
        label: 'User Flow Examples',
        icon: <RocketOutlined />,
        file: 'USER_FLOW_EXAMPLES.md',
        roles: ['org_user', 'org_admin', 'super_admin']
    },
    {
        key: 'quick_start_example',
        label: 'Quick Start Example',
        icon: <ThunderboltOutlined />,
        file: 'QUICK_START_EXAMPLE.md',
        roles: ['org_user', 'org_admin', 'super_admin']
    },
    {
        key: 'cra_start_example',
        label: 'CRA Start Example',
        icon: <SafetyCertificateOutlined />,
        file: 'CRA_START_EXAMPLE.md',
        roles: ['org_user', 'org_admin', 'super_admin'],
        downloadFile: '/docs/examples/Wazuh_SIEM_AI_CyberBridge_Compliance_Mapping.xlsx'
    },
    {
        key: 'onboarding_training',
        label: 'Onboarding Training',
        icon: <PlayCircleOutlined />,
        file: 'ONBOARDING_TRAINING.md',
        roles: ['org_user', 'org_admin', 'super_admin']
    },
    {
        key: 'user_api',
        label: 'User API Reference',
        icon: <ApiOutlined />,
        file: 'USER_API.md',
        roles: ['org_user', 'org_admin', 'super_admin']
    },
    {
        key: 'admin_guide',
        label: 'Admin Guide',
        icon: <TeamOutlined />,
        file: 'ADMIN_GUIDE.md',
        roles: ['org_admin', 'super_admin']
    },
    {
        key: 'admin_api',
        label: 'Admin API Reference',
        icon: <ApiOutlined />,
        file: 'ADMIN_API.md',
        roles: ['org_admin', 'super_admin']
    },
    {
        key: 'superadmin_guide',
        label: 'Super Admin Guide',
        icon: <CrownOutlined />,
        file: 'SUPERADMIN_GUIDE.md',
        roles: ['super_admin']
    },
    {
        key: 'superadmin_api',
        label: 'Super Admin API',
        icon: <ApiOutlined />,
        file: 'SUPERADMIN_API.md',
        roles: ['super_admin']
    }
];

interface TocItem {
    id: string;
    text: string;
    level: number;
}

const DocumentationPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const { user } = useAuthStore();
    const { current_user } = useUserStore();

    // Read ?doc= query parameter to allow deep-linking to a specific document
    const queryDoc = new URLSearchParams(window.location.search).get('doc');
    const [selectedDoc, setSelectedDoc] = useState<string>(queryDoc || 'user_guide');
    const [markdownContent, setMarkdownContent] = useState<string>('');
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [exportingDoc, setExportingDoc] = useState<string | null>(null);
    const contentRef = useRef<HTMLDivElement>(null);
    const markdownCache = useRef<Record<string, string>>({});

    // Sync selectedDoc when navigating with ?doc= query parameter
    useEffect(() => {
        const docParam = new URLSearchParams(window.location.search).get('doc');
        if (docParam && documentationItems.some(d => d.key === docParam)) {
            setSelectedDoc(docParam);
        }
    }, [location]);

    // Get user role
    const userRole = current_user?.role_name || 'org_user';

    // Filter documentation items based on user role
    const availableDocs = useMemo(() => {
        return documentationItems.filter(doc => doc.roles.includes(userRole));
    }, [userRole]);

    // Generate table of contents from markdown
    const tableOfContents = useMemo((): TocItem[] => {
        if (!markdownContent) return [];

        const headingRegex = /^(#{1,3})\s+(.+)$/gm;
        const toc: TocItem[] = [];
        let match;

        while ((match = headingRegex.exec(markdownContent)) !== null) {
            const level = match[1].length;
            const text = match[2];
            const id = text.toLowerCase().replace(/[^\w]+/g, '-');
            toc.push({ id, text, level });
        }

        return toc;
    }, [markdownContent]);

    // Load markdown content
    useEffect(() => {
        const loadMarkdown = async () => {
            setLoading(true);
            setError(null);

            const doc = documentationItems.find(d => d.key === selectedDoc);
            if (!doc) {
                setError('Documentation not found');
                setLoading(false);
                return;
            }

            try {
                const response = await fetch(`/docs/${doc.file}`);
                if (!response.ok) {
                    throw new Error('Failed to load documentation');
                }
                const content = await response.text();
                markdownCache.current[doc.key] = content;
                setMarkdownContent(content);
            } catch (err) {
                setError('Failed to load documentation. Please try again.');
                console.error('Error loading documentation:', err);
            } finally {
                setLoading(false);
            }
        };

        loadMarkdown();
    }, [selectedDoc]);

    // Handle doc selection
    const handleDocSelect = (key: string) => {
        setSelectedDoc(key);
    };

    // Scroll to section
    const scrollToSection = (id: string) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    };

    // Fetch markdown for a specific doc (uses cache)
    const fetchMarkdownForDoc = useCallback(async (docKey: string): Promise<string | null> => {
        if (markdownCache.current[docKey]) return markdownCache.current[docKey];

        const doc = documentationItems.find(d => d.key === docKey);
        if (!doc) return null;

        try {
            const response = await fetch(`/docs/${doc.file}`);
            if (!response.ok) return null;
            const content = await response.text();
            markdownCache.current[docKey] = content;
            return content;
        } catch {
            return null;
        }
    }, []);

    // Handle export for any doc in any format
    const handleExport = useCallback(async (docKey: string, format: 'txt' | 'md' | 'pdf') => {
        const doc = documentationItems.find(d => d.key === docKey);
        if (!doc) return;

        const filename = doc.label.replace(/\s+/g, '_');
        setExportingDoc(docKey);

        try {
            if (format === 'txt') {
                const content = await fetchMarkdownForDoc(docKey);
                if (content) {
                    downloadAsText(content, filename);
                    message.success(`Downloaded ${doc.label}.txt`);
                }
            } else if (format === 'md') {
                const content = await fetchMarkdownForDoc(docKey);
                if (content) {
                    downloadAsMarkdown(content, filename);
                    message.success(`Downloaded ${doc.label}.md`);
                }
            } else if (format === 'pdf') {
                // For PDF: if this is the currently viewed doc, use the rendered content
                if (docKey === selectedDoc && contentRef.current) {
                    await downloadAsPdf(contentRef.current, filename);
                    message.success(`Downloaded ${doc.label}.pdf`);
                } else {
                    // Need to select the doc first, then export after render
                    setSelectedDoc(docKey);
                    // Wait for content to render, then export
                    setTimeout(async () => {
                        if (contentRef.current) {
                            await downloadAsPdf(contentRef.current, filename);
                            message.success(`Downloaded ${doc.label}.pdf`);
                        }
                        setExportingDoc(null);
                    }, 1000);
                    return;
                }
            }
        } catch (err) {
            console.error('Export failed:', err);
            message.error(`Failed to export ${doc.label}`);
        } finally {
            setExportingDoc(null);
        }
    }, [selectedDoc, fetchMarkdownForDoc]);

    // Build dropdown menu items for a doc
    const getExportMenuItems = useCallback((docKey: string): MenuProps['items'] => [
        {
            key: 'txt',
            icon: <FileTextOutlined />,
            label: 'Download as .txt',
            onClick: (e) => { e.domEvent.stopPropagation(); handleExport(docKey, 'txt'); }
        },
        {
            key: 'md',
            icon: <FileMarkdownOutlined />,
            label: 'Download as .md',
            onClick: (e) => { e.domEvent.stopPropagation(); handleExport(docKey, 'md'); }
        },
        {
            key: 'pdf',
            icon: <FilePdfOutlined />,
            label: 'Download as .pdf',
            onClick: (e) => { e.domEvent.stopPropagation(); handleExport(docKey, 'pdf'); }
        }
    ], [handleExport]);

    // Get role display info
    const getRoleInfo = () => {
        switch (userRole) {
            case 'super_admin':
                return { icon: <CrownOutlined />, label: 'Super Admin', color: '#722ed1' };
            case 'org_admin':
                return { icon: <TeamOutlined />, label: 'Organization Admin', color: '#1890ff' };
            default:
                return { icon: <UserOutlined />, label: 'User', color: '#52c41a' };
        }
    };

    const roleInfo = getRoleInfo();

    // Custom heading renderer to add IDs for TOC linking
    const HeadingRenderer = ({ level, children }: { level: number; children: React.ReactNode }) => {
        const text = String(children);
        const id = text.toLowerCase().replace(/[^\w]+/g, '-');
        const Tag = `h${level}` as keyof JSX.IntrinsicElements;
        return <Tag id={id} style={{ scrollMarginTop: '20px' }}>{children}</Tag>;
    };

    return (
        <div>
            <div className={'page-parent'}>
                <Sidebar selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys} onOpenChange={menuHighlighting.onOpenChange} />
                <div className={'page-content'}>
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <BookOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Documentation</h1>
                        </div>
                        <div className="page-header-right">
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                padding: '4px 10px',
                                backgroundColor: '#f5f5f5',
                                borderRadius: '4px',
                                fontSize: '13px'
                            }}>
                                <span style={{ color: roleInfo.color }}>{roleInfo.icon}</span>
                                <span style={{ color: '#666' }}>Viewing as:</span>
                                <span style={{ fontWeight: 500, color: roleInfo.color }}>{roleInfo.label}</span>
                            </div>
                        </div>
                    </div>

                    {/* Documentation Layout */}
                    <div style={{ display: 'flex', gap: '24px', marginTop: '20px' }}>
                        {/* Left Panel - Document Selection & TOC */}
                        <div style={{
                            width: '280px',
                            flexShrink: 0,
                            backgroundColor: '#fff',
                            borderRadius: '8px',
                            border: '1px solid #f0f0f0',
                            overflow: 'hidden'
                        }}>
                            {/* Document Selection */}
                            <div style={{
                                padding: '16px',
                                borderBottom: '1px solid #f0f0f0',
                                backgroundColor: '#fafafa'
                            }}>
                                <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 600, color: '#0f386a' }}>
                                    Available Documentation
                                </h3>
                                <div>
                                    {availableDocs.map(doc => (
                                        <div
                                            key={doc.key}
                                            onClick={() => handleDocSelect(doc.key)}
                                            style={{
                                                padding: '6px 8px',
                                                fontSize: '14px',
                                                fontWeight: selectedDoc === doc.key ? 500 : 400,
                                                color: selectedDoc === doc.key ? '#333' : '#666',
                                                cursor: 'pointer',
                                                borderRadius: '4px',
                                                transition: 'background-color 0.2s',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '8px'
                                            }}
                                            onMouseEnter={(e) => {
                                                e.currentTarget.style.backgroundColor = '#f0f7ff';
                                            }}
                                            onMouseLeave={(e) => {
                                                e.currentTarget.style.backgroundColor = 'transparent';
                                            }}
                                        >
                                            <span style={{ color: selectedDoc === doc.key ? '#0f386a' : '#999' }}>{doc.icon}</span>
                                            <span style={{ flex: 1 }}>{doc.label}</span>
                                            {doc.downloadFile && (
                                                <a
                                                    href={doc.downloadFile}
                                                    download
                                                    title="Download full example (.xlsx)"
                                                    onClick={(e) => e.stopPropagation()}
                                                    style={{
                                                        display: 'inline-flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center',
                                                        width: '24px',
                                                        height: '24px',
                                                        borderRadius: '4px',
                                                        color: '#10b981',
                                                        fontSize: '13px',
                                                        transition: 'all 0.2s',
                                                        flexShrink: 0
                                                    }}
                                                    onMouseEnter={(e) => {
                                                        e.currentTarget.style.backgroundColor = '#ecfdf5';
                                                        e.currentTarget.style.color = '#059669';
                                                    }}
                                                    onMouseLeave={(e) => {
                                                        e.currentTarget.style.backgroundColor = 'transparent';
                                                        e.currentTarget.style.color = '#10b981';
                                                    }}
                                                >
                                                    <DownloadOutlined />
                                                </a>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Table of Contents */}
                            {tableOfContents.length > 0 && (
                                <div style={{ padding: '16px' }}>
                                    <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 600, color: '#0f386a' }}>
                                        Table of Contents
                                    </h3>
                                    <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                                        {tableOfContents.map((item, index) => (
                                            <div
                                                key={index}
                                                onClick={() => scrollToSection(item.id)}
                                                style={{
                                                    padding: '6px 8px',
                                                    paddingLeft: `${(item.level - 1) * 16 + 8}px`,
                                                    fontSize: item.level === 1 ? '14px' : '13px',
                                                    fontWeight: item.level === 1 ? 500 : 400,
                                                    color: item.level === 1 ? '#333' : '#666',
                                                    cursor: 'pointer',
                                                    borderRadius: '4px',
                                                    transition: 'background-color 0.2s',
                                                    whiteSpace: 'nowrap',
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis'
                                                }}
                                                onMouseEnter={(e) => {
                                                    e.currentTarget.style.backgroundColor = '#f0f7ff';
                                                }}
                                                onMouseLeave={(e) => {
                                                    e.currentTarget.style.backgroundColor = 'transparent';
                                                }}
                                            >
                                                {item.text}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Right Panel - Content */}
                        <div style={{
                            flex: 1,
                            backgroundColor: '#fff',
                            borderRadius: '8px',
                            border: '1px solid #f0f0f0',
                            padding: '32px',
                            minHeight: '600px',
                            overflow: 'auto'
                        }}>
                            {loading ? (
                                <div style={{
                                    display: 'flex',
                                    justifyContent: 'center',
                                    alignItems: 'center',
                                    height: '400px'
                                }}>
                                    <Spin size="large" tip="Loading documentation..." />
                                </div>
                            ) : error ? (
                                <Empty
                                    description={error}
                                    style={{ marginTop: '100px' }}
                                />
                            ) : (
                                <div className="markdown-content">
                                    {(() => {
                                        const currentDoc = documentationItems.find(d => d.key === selectedDoc);
                                        return (
                                            <div style={{
                                                display: 'flex',
                                                justifyContent: 'flex-end',
                                                gap: '8px',
                                                marginBottom: '8px'
                                            }}>
                                                {currentDoc?.downloadFile && (
                                                    <a
                                                        href={currentDoc.downloadFile}
                                                        download
                                                        style={{
                                                            display: 'inline-flex',
                                                            alignItems: 'center',
                                                            gap: '6px',
                                                            padding: '6px 14px',
                                                            backgroundColor: '#ecfdf5',
                                                            color: '#059669',
                                                            border: '1px solid #a7f3d0',
                                                            borderRadius: '6px',
                                                            fontSize: '13px',
                                                            fontWeight: 500,
                                                            textDecoration: 'none',
                                                            transition: 'all 0.2s',
                                                            cursor: 'pointer'
                                                        }}
                                                        onMouseEnter={(e) => {
                                                            e.currentTarget.style.backgroundColor = '#d1fae5';
                                                            e.currentTarget.style.borderColor = '#6ee7b7';
                                                        }}
                                                        onMouseLeave={(e) => {
                                                            e.currentTarget.style.backgroundColor = '#ecfdf5';
                                                            e.currentTarget.style.borderColor = '#a7f3d0';
                                                        }}
                                                    >
                                                        <DownloadOutlined />
                                                        Download Full Example (.xlsx)
                                                    </a>
                                                )}
                                                <Dropdown
                                                    menu={{ items: getExportMenuItems(selectedDoc) }}
                                                    trigger={['click']}
                                                    placement="bottomRight"
                                                >
                                                    <span
                                                        style={{
                                                            display: 'inline-flex',
                                                            alignItems: 'center',
                                                            gap: '6px',
                                                            padding: '6px 14px',
                                                            backgroundColor: '#f0f7ff',
                                                            color: '#0f386a',
                                                            border: '1px solid #bdd7ee',
                                                            borderRadius: '6px',
                                                            fontSize: '13px',
                                                            fontWeight: 500,
                                                            transition: 'all 0.2s',
                                                            cursor: 'pointer'
                                                        }}
                                                        onMouseEnter={(e) => {
                                                            e.currentTarget.style.backgroundColor = '#dbe9f7';
                                                            e.currentTarget.style.borderColor = '#91bcdf';
                                                        }}
                                                        onMouseLeave={(e) => {
                                                            e.currentTarget.style.backgroundColor = '#f0f7ff';
                                                            e.currentTarget.style.borderColor = '#bdd7ee';
                                                        }}
                                                    >
                                                        {exportingDoc === selectedDoc ? <Spin size="small" /> : <DownloadOutlined />}
                                                        Download As...
                                                    </span>
                                                </Dropdown>
                                            </div>
                                        );
                                    })()}
                                    <div ref={contentRef}>
                                    <ReactMarkdown
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                            h1: ({ children }) => <HeadingRenderer level={1}>{children}</HeadingRenderer>,
                                            h2: ({ children }) => <HeadingRenderer level={2}>{children}</HeadingRenderer>,
                                            h3: ({ children }) => <HeadingRenderer level={3}>{children}</HeadingRenderer>,
                                            h4: ({ children }) => <HeadingRenderer level={4}>{children}</HeadingRenderer>,
                                            h5: ({ children }) => <HeadingRenderer level={5}>{children}</HeadingRenderer>,
                                            h6: ({ children }) => <HeadingRenderer level={6}>{children}</HeadingRenderer>,
                                            code: ({ className, children, ...props }) => {
                                                const match = /language-(\w+)/.exec(className || '');
                                                const isInline = !match;
                                                return isInline ? (
                                                    <code
                                                        style={{
                                                            backgroundColor: '#f5f5f5',
                                                            padding: '2px 6px',
                                                            borderRadius: '4px',
                                                            fontSize: '0.9em',
                                                            fontFamily: 'monospace'
                                                        }}
                                                        {...props}
                                                    >
                                                        {children}
                                                    </code>
                                                ) : (
                                                    <pre style={{
                                                        backgroundColor: '#1e1e1e',
                                                        color: '#d4d4d4',
                                                        padding: '16px',
                                                        borderRadius: '8px',
                                                        overflow: 'auto',
                                                        fontSize: '13px',
                                                        lineHeight: '1.5'
                                                    }}>
                                                        <code className={className} {...props}>
                                                            {children}
                                                        </code>
                                                    </pre>
                                                );
                                            },
                                            table: ({ children }) => (
                                                <div style={{ overflowX: 'auto', marginBottom: '16px' }}>
                                                    <table style={{
                                                        width: '100%',
                                                        borderCollapse: 'collapse',
                                                        fontSize: '14px'
                                                    }}>
                                                        {children}
                                                    </table>
                                                </div>
                                            ),
                                            th: ({ children }) => (
                                                <th style={{
                                                    backgroundColor: '#fafafa',
                                                    padding: '12px',
                                                    borderBottom: '2px solid #e8e8e8',
                                                    textAlign: 'left',
                                                    fontWeight: 600
                                                }}>
                                                    {children}
                                                </th>
                                            ),
                                            td: ({ children }) => (
                                                <td style={{
                                                    padding: '12px',
                                                    borderBottom: '1px solid #f0f0f0'
                                                }}>
                                                    {children}
                                                </td>
                                            ),
                                            blockquote: ({ children }) => (
                                                <blockquote style={{
                                                    borderLeft: '4px solid #0f386a',
                                                    margin: '16px 0',
                                                    padding: '12px 20px',
                                                    backgroundColor: '#f0f7ff',
                                                    borderRadius: '0 8px 8px 0'
                                                }}>
                                                    {children}
                                                </blockquote>
                                            ),
                                            ul: ({ children }) => (
                                                <ul style={{ paddingLeft: '24px', marginBottom: '16px' }}>
                                                    {children}
                                                </ul>
                                            ),
                                            ol: ({ children }) => (
                                                <ol style={{ paddingLeft: '24px', marginBottom: '16px' }}>
                                                    {children}
                                                </ol>
                                            ),
                                            li: ({ children }) => (
                                                <li style={{ marginBottom: '8px', lineHeight: '1.6' }}>
                                                    {children}
                                                </li>
                                            ),
                                            p: ({ children }) => (
                                                <p style={{ marginBottom: '16px', lineHeight: '1.7' }}>
                                                    {children}
                                                </p>
                                            ),
                                            a: ({ children, href }) => (
                                                <a
                                                    href={href}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    style={{ color: '#0f386a', textDecoration: 'none' }}
                                                    onMouseEnter={(e) => {
                                                        e.currentTarget.style.textDecoration = 'underline';
                                                    }}
                                                    onMouseLeave={(e) => {
                                                        e.currentTarget.style.textDecoration = 'none';
                                                    }}
                                                >
                                                    {children}
                                                </a>
                                            ),
                                            hr: () => (
                                                <hr style={{
                                                    border: 'none',
                                                    borderTop: '1px solid #e8e8e8',
                                                    margin: '24px 0'
                                                }} />
                                            )
                                        }}
                                    >
                                        {markdownContent}
                                    </ReactMarkdown>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            <style>{`
                .markdown-content h1 {
                    font-size: 2em;
                    font-weight: 600;
                    color: #1a1a1a;
                    margin-bottom: 16px;
                    padding-bottom: 12px;
                    border-bottom: 2px solid #0f386a;
                }
                .markdown-content h2 {
                    font-size: 1.5em;
                    font-weight: 600;
                    color: #333;
                    margin-top: 32px;
                    margin-bottom: 16px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid #e8e8e8;
                }
                .markdown-content h3 {
                    font-size: 1.25em;
                    font-weight: 600;
                    color: #444;
                    margin-top: 24px;
                    margin-bottom: 12px;
                }
                .markdown-content h4 {
                    font-size: 1.1em;
                    font-weight: 600;
                    color: #555;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }
                .markdown-content strong {
                    font-weight: 600;
                    color: #333;
                }
            `}</style>
        </div>
    );
};

export default DocumentationPage;
