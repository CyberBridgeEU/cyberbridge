import { useState, useEffect } from 'react';
import {
    SendOutlined, SafetyCertificateOutlined, MailOutlined, PlusOutlined,
    DeleteOutlined, CheckCircleOutlined, ClockCircleOutlined,
    ExclamationCircleOutlined, MessageOutlined, EditOutlined
} from '@ant-design/icons';
import { Table, Select, Tag, Modal, Input, Spin, message, Tooltip } from 'antd';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import { DashboardSection } from "../components/dashboard";
import useAuthStore from "../store/useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

const { TextArea } = Input;

interface Certificate {
    id: string;
    certificate_number: string;
    framework_name: string;
    organisation_name: string;
    overall_score: number;
    issued_at: string;
    expires_at: string;
    revoked: boolean;
    verification_hash: string;
}

interface Submission {
    id: string;
    certificate_id: string;
    certificate_number: string;
    framework_name: string;
    authority_name: string;
    recipient_emails: string[];
    submission_method: string;
    status: string;
    subject: string | null;
    body: string | null;
    feedback: string | null;
    feedback_received_at: string | null;
    sent_at: string | null;
    submitted_by_name: string | null;
    created_at: string;
}

interface EmailConfig {
    id: string;
    authority_name: string;
    email: string;
    is_default: boolean;
}

const statusConfig: Record<string, { color: string; label: string; icon: React.ReactNode }> = {
    draft: { color: '#d9d9d9', label: 'Draft', icon: <EditOutlined /> },
    sent: { color: '#1890ff', label: 'Sent', icon: <SendOutlined /> },
    acknowledged: { color: '#52c41a', label: 'Acknowledged', icon: <CheckCircleOutlined /> },
    feedback_received: { color: '#722ed1', label: 'Feedback Received', icon: <MessageOutlined /> },
};

const RegulatorySubmissionPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const getAuthHeader = useAuthStore((s) => s.getAuthHeader);
    const getUserRole = useAuthStore((s) => s.getUserRole);

    const [loading, setLoading] = useState(true);
    const [certificates, setCertificates] = useState<Certificate[]>([]);
    const [submissions, setSubmissions] = useState<Submission[]>([]);
    const [emailConfigs, setEmailConfigs] = useState<EmailConfig[]>([]);

    // New submission modal
    const [showSubmitModal, setShowSubmitModal] = useState(false);
    const [selectedCertId, setSelectedCertId] = useState<string | undefined>(undefined);
    const [selectedAuthority, setSelectedAuthority] = useState<string | undefined>(undefined);
    const [selectedEmails, setSelectedEmails] = useState<string[]>([]);
    const [customSubject, setCustomSubject] = useState('');
    const [customBody, setCustomBody] = useState('');
    const [submitting, setSubmitting] = useState(false);

    // Add email modal
    const [showAddEmail, setShowAddEmail] = useState(false);
    const [newEmailAuthority, setNewEmailAuthority] = useState('');
    const [newEmailAddress, setNewEmailAddress] = useState('');

    // Feedback modal
    const [showFeedbackModal, setShowFeedbackModal] = useState(false);
    const [feedbackSubId, setFeedbackSubId] = useState<string | null>(null);
    const [feedbackText, setFeedbackText] = useState('');

    const userRole = getUserRole();
    const isAdmin = userRole === 'org_admin' || userRole === 'super_admin';

    const fetchAll = async () => {
        const headers = getAuthHeader();
        if (!headers) return;
        setLoading(true);
        try {
            const [certsRes, subsRes, emailsRes] = await Promise.all([
                fetch(`${cyberbridge_back_end_rest_api}/certificates`, { headers }),
                fetch(`${cyberbridge_back_end_rest_api}/submissions`, { headers }),
                fetch(`${cyberbridge_back_end_rest_api}/submissions/email-configs`, { headers }),
            ]);
            if (certsRes.ok) setCertificates(await certsRes.json());
            if (subsRes.ok) setSubmissions(await subsRes.json());
            if (emailsRes.ok) setEmailConfigs(await emailsRes.json());
        } catch (err) {
            console.error('Failed to fetch data:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchAll(); }, [getAuthHeader]);

    // When authority is selected, auto-populate emails
    useEffect(() => {
        if (selectedAuthority) {
            const matching = emailConfigs.filter(c => c.authority_name === selectedAuthority).map(c => c.email);
            setSelectedEmails(matching);
        }
    }, [selectedAuthority, emailConfigs]);

    const handleSubmit = async () => {
        if (!selectedCertId || !selectedAuthority || selectedEmails.length === 0) {
            message.warning('Please select a certificate, authority, and at least one email');
            return;
        }
        setSubmitting(true);
        try {
            const headers = getAuthHeader();
            if (!headers) return;
            const res = await fetch(`${cyberbridge_back_end_rest_api}/submissions`, {
                method: 'POST',
                headers: { ...headers, 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    certificate_id: selectedCertId,
                    authority_name: selectedAuthority,
                    recipient_emails: selectedEmails,
                    subject: customSubject || undefined,
                    body: customBody || undefined,
                }),
            });
            if (res.ok) {
                const data = await res.json();
                message.success(data.message);
                setShowSubmitModal(false);
                resetSubmitForm();
                fetchAll();
            } else {
                const err = await res.json();
                message.error(err.detail || 'Failed to create submission');
            }
        } catch (err) {
            message.error('Failed to create submission');
        } finally {
            setSubmitting(false);
        }
    };

    const resetSubmitForm = () => {
        setSelectedCertId(undefined);
        setSelectedAuthority(undefined);
        setSelectedEmails([]);
        setCustomSubject('');
        setCustomBody('');
    };

    const handleAddEmail = async () => {
        if (!newEmailAuthority || !newEmailAddress) {
            message.warning('Please fill in both fields');
            return;
        }
        const headers = getAuthHeader();
        if (!headers) return;
        const res = await fetch(`${cyberbridge_back_end_rest_api}/submissions/email-configs`, {
            method: 'POST',
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ authority_name: newEmailAuthority, email: newEmailAddress }),
        });
        if (res.ok) {
            message.success('Email added');
            setShowAddEmail(false);
            setNewEmailAuthority('');
            setNewEmailAddress('');
            fetchAll();
        } else {
            const err = await res.json();
            message.error(err.detail || 'Failed to add email');
        }
    };

    const handleDeleteEmail = async (configId: string) => {
        const headers = getAuthHeader();
        if (!headers) return;
        const res = await fetch(`${cyberbridge_back_end_rest_api}/submissions/email-configs/${configId}`, {
            method: 'DELETE',
            headers,
        });
        if (res.ok) {
            message.success('Email removed');
            fetchAll();
        } else {
            const err = await res.json();
            message.error(err.detail || 'Cannot delete');
        }
    };

    const handleMarkSent = async (subId: string) => {
        const headers = getAuthHeader();
        if (!headers) return;
        const res = await fetch(`${cyberbridge_back_end_rest_api}/submissions/${subId}/mark-sent`, {
            method: 'POST', headers,
        });
        if (res.ok) { message.success('Marked as sent'); fetchAll(); }
    };

    const handleMarkAcknowledged = async (subId: string) => {
        const headers = getAuthHeader();
        if (!headers) return;
        const res = await fetch(`${cyberbridge_back_end_rest_api}/submissions/${subId}/mark-acknowledged`, {
            method: 'POST', headers,
        });
        if (res.ok) { message.success('Marked as acknowledged'); fetchAll(); }
    };

    const handleSaveFeedback = async () => {
        if (!feedbackSubId || !feedbackText) return;
        const headers = getAuthHeader();
        if (!headers) return;
        const res = await fetch(`${cyberbridge_back_end_rest_api}/submissions/${feedbackSubId}/feedback`, {
            method: 'POST',
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ feedback: feedbackText }),
        });
        if (res.ok) {
            message.success('Feedback recorded');
            setShowFeedbackModal(false);
            setFeedbackSubId(null);
            setFeedbackText('');
            fetchAll();
        }
    };

    const uniqueAuthorities = [...new Set(emailConfigs.map(c => c.authority_name))];
    const validCertificates = certificates.filter(c => !c.revoked && new Date(c.expires_at) > new Date());

    const submissionColumns = [
        {
            title: 'Certificate',
            dataIndex: 'certificate_number',
            key: 'certificate_number',
            width: 170,
        },
        {
            title: 'Framework',
            dataIndex: 'framework_name',
            key: 'framework_name',
            width: 140,
        },
        {
            title: 'Authority',
            dataIndex: 'authority_name',
            key: 'authority_name',
            width: 140,
        },
        {
            title: 'Recipients',
            dataIndex: 'recipient_emails',
            key: 'recipient_emails',
            render: (emails: string[]) => (
                <div style={{ fontSize: '12px' }}>
                    {emails.map((e, i) => <div key={i}>{e}</div>)}
                </div>
            ),
        },
        {
            title: 'Status',
            dataIndex: 'status',
            key: 'status',
            width: 160,
            render: (status: string) => {
                const cfg = statusConfig[status] || { color: '#d9d9d9', label: status, icon: <ClockCircleOutlined /> };
                return <Tag color={cfg.color} icon={cfg.icon}>{cfg.label}</Tag>;
            },
        },
        {
            title: 'Sent',
            dataIndex: 'sent_at',
            key: 'sent_at',
            width: 110,
            render: (val: string | null) => val ? new Date(val).toLocaleDateString() : '-',
        },
        {
            title: 'Feedback',
            key: 'feedback',
            width: 200,
            render: (_: unknown, record: Submission) => record.feedback
                ? <Tooltip title={record.feedback}><span style={{ fontSize: '12px', color: '#722ed1' }}>{record.feedback.substring(0, 50)}{record.feedback.length > 50 ? '...' : ''}</span></Tooltip>
                : <span style={{ color: '#999', fontSize: '12px' }}>None</span>,
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 200,
            render: (_: unknown, record: Submission) => (
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' as const }}>
                    {isAdmin && record.status === 'draft' && (
                        <button onClick={() => handleMarkSent(record.id)} style={actionBtnStyle('#1890ff')}>
                            <SendOutlined /> Mark Sent
                        </button>
                    )}
                    {isAdmin && record.status === 'sent' && (
                        <button onClick={() => handleMarkAcknowledged(record.id)} style={actionBtnStyle('#52c41a')}>
                            <CheckCircleOutlined /> Acknowledged
                        </button>
                    )}
                    {isAdmin && (
                        <button onClick={() => { setFeedbackSubId(record.id); setFeedbackText(record.feedback || ''); setShowFeedbackModal(true); }} style={actionBtnStyle('#722ed1')}>
                            <MessageOutlined /> Feedback
                        </button>
                    )}
                </div>
            ),
        },
    ];

    const emailColumns = [
        { title: 'Authority', dataIndex: 'authority_name', key: 'authority_name' },
        { title: 'Email', dataIndex: 'email', key: 'email' },
        {
            title: 'Type',
            key: 'type',
            width: 100,
            render: (_: unknown, record: EmailConfig) => record.is_default
                ? <Tag color="blue">Default</Tag>
                : <Tag color="green">Custom</Tag>,
        },
        {
            title: '',
            key: 'actions',
            width: 60,
            render: (_: unknown, record: EmailConfig) => !record.is_default && isAdmin ? (
                <button onClick={() => handleDeleteEmail(record.id)} style={{ ...actionBtnStyle('#ff4d4f'), padding: '2px 6px' }}>
                    <DeleteOutlined />
                </button>
            ) : null,
        },
    ];

    return (
        <div>
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
                            <SendOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <h1 className="page-title" style={{ margin: 0 }}>Regulatory Submissions</h1>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            {isAdmin && (
                                <Tooltip title={validCertificates.length === 0 ? 'No valid certificates available' : ''}>
                                    <span>
                                        <button
                                            onClick={() => setShowSubmitModal(true)}
                                            disabled={validCertificates.length === 0}
                                            style={{
                                                display: 'inline-flex', alignItems: 'center', gap: '6px',
                                                padding: '6px 16px', backgroundColor: '#52c41a', color: '#fff',
                                                border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 500,
                                                cursor: validCertificates.length === 0 ? 'not-allowed' : 'pointer',
                                                opacity: validCertificates.length === 0 ? 0.45 : 1,
                                                transition: 'all 0.2s',
                                            }}
                                        >
                                            <SendOutlined /> New Submission
                                        </button>
                                    </span>
                                </Tooltip>
                            )}
                        </div>
                    </div>

                    {loading ? (
                        <div style={{ textAlign: 'center', padding: '60px 0' }}><Spin size="large" /></div>
                    ) : (
                        <>
                            {/* Submissions Table */}
                            <DashboardSection title="Submission History" style={{ marginTop: '24px' }}>
                                {submissions.length > 0 ? (
                                    <Table
                                        dataSource={submissions}
                                        columns={submissionColumns}
                                        rowKey="id"
                                        pagination={false}
                                        size="small"
                                        style={{ backgroundColor: '#fff', borderRadius: '8px' }}
                                    />
                                ) : (
                                    <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
                                        <SafetyCertificateOutlined style={{ fontSize: 40, marginBottom: 12, opacity: 0.3 }} />
                                        <p>No regulatory submissions yet. Generate a compliance certificate from Gap Analysis, then submit it here.</p>
                                    </div>
                                )}
                            </DashboardSection>

                            {/* Email Configuration */}
                            <DashboardSection title="Recipient Email Directory" style={{ marginTop: '24px' }}>
                                <div style={{ marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontSize: '13px', color: '#888' }}>
                                        Default emails are pre-configured for EU regulatory authorities. Add custom emails for your national CSIRTs or other authorities.
                                    </span>
                                    {isAdmin && (
                                        <button
                                            onClick={() => setShowAddEmail(true)}
                                            style={{
                                                display: 'inline-flex', alignItems: 'center', gap: '6px',
                                                padding: '4px 12px', backgroundColor: '#0f386a', color: '#fff',
                                                border: 'none', borderRadius: '6px', fontSize: '12px',
                                                cursor: 'pointer',
                                            }}
                                        >
                                            <PlusOutlined /> Add Email
                                        </button>
                                    )}
                                </div>
                                <Table
                                    dataSource={emailConfigs}
                                    columns={emailColumns}
                                    rowKey="id"
                                    pagination={false}
                                    size="small"
                                    style={{ backgroundColor: '#fff', borderRadius: '8px' }}
                                />
                            </DashboardSection>

                            <div style={{ marginBottom: '28px' }} />
                        </>
                    )}
                </div>
            </div>

            {/* New Submission Modal */}
            <Modal
                title={<div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><SendOutlined style={{ color: '#0f386a' }} /><span>Submit Certificate to Authority</span></div>}
                open={showSubmitModal}
                onCancel={() => { setShowSubmitModal(false); resetSubmitForm(); }}
                onOk={handleSubmit}
                okText={submitting ? 'Submitting...' : 'Submit'}
                okButtonProps={{ disabled: submitting || !selectedCertId || !selectedAuthority || selectedEmails.length === 0 }}
                width={700}
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px' }}>
                    <div>
                        <label style={labelStyle}>Certificate *</label>
                        <Select
                            placeholder="Select a certificate"
                            style={{ width: '100%' }}
                            value={selectedCertId}
                            onChange={setSelectedCertId}
                            options={validCertificates.map(c => ({
                                label: `${c.certificate_number} — ${c.framework_name} (${c.overall_score}%)`,
                                value: c.id,
                            }))}
                        />
                    </div>
                    <div>
                        <label style={labelStyle}>Authority *</label>
                        <Select
                            placeholder="Select or type authority name"
                            style={{ width: '100%' }}
                            value={selectedAuthority}
                            onChange={setSelectedAuthority}
                            options={uniqueAuthorities.map(a => ({ label: a, value: a }))}
                            showSearch
                        />
                    </div>
                    <div>
                        <label style={labelStyle}>Recipient Emails *</label>
                        <Select
                            mode="tags"
                            placeholder="Select or type email addresses"
                            style={{ width: '100%' }}
                            value={selectedEmails}
                            onChange={setSelectedEmails}
                            options={emailConfigs
                                .filter(c => !selectedAuthority || c.authority_name === selectedAuthority)
                                .map(c => ({ label: `${c.email} (${c.authority_name})`, value: c.email }))
                            }
                        />
                    </div>
                    <div>
                        <label style={labelStyle}>Subject (optional — auto-generated if empty)</label>
                        <Input
                            value={customSubject}
                            onChange={e => setCustomSubject(e.target.value)}
                            placeholder="Custom email subject..."
                        />
                    </div>
                    <div>
                        <label style={labelStyle}>Body (optional — auto-generated if empty)</label>
                        <TextArea
                            value={customBody}
                            onChange={e => setCustomBody(e.target.value)}
                            rows={5}
                            placeholder="Custom email body..."
                        />
                    </div>
                    <div style={{ backgroundColor: '#fffbe6', border: '1px solid #ffe58f', borderRadius: '6px', padding: '10px 14px', fontSize: '12px', color: '#ad8b00' }}>
                        <ExclamationCircleOutlined style={{ marginRight: 6 }} />
                        If SMTP is configured, the certificate PDF will be sent via email automatically. Otherwise, the submission will be saved as a draft for manual sending.
                    </div>
                </div>
            </Modal>

            {/* Add Email Modal */}
            <Modal
                title={<div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><MailOutlined style={{ color: '#0f386a' }} /><span>Add Recipient Email</span></div>}
                open={showAddEmail}
                onCancel={() => { setShowAddEmail(false); setNewEmailAuthority(''); setNewEmailAddress(''); }}
                onOk={handleAddEmail}
                okText="Add"
            >
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '16px' }}>
                    <div>
                        <label style={labelStyle}>Authority Name *</label>
                        <Select
                            placeholder="Select existing or type new"
                            style={{ width: '100%' }}
                            value={newEmailAuthority || undefined}
                            onChange={setNewEmailAuthority}
                            options={[
                                ...uniqueAuthorities.map(a => ({ label: a, value: a })),
                            ]}
                            showSearch
                            allowClear
                        />
                    </div>
                    <div>
                        <label style={labelStyle}>Email Address *</label>
                        <Input
                            value={newEmailAddress}
                            onChange={e => setNewEmailAddress(e.target.value)}
                            placeholder="authority@example.eu"
                            type="email"
                        />
                    </div>
                </div>
            </Modal>

            {/* Feedback Modal */}
            <Modal
                title={<div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><MessageOutlined style={{ color: '#722ed1' }} /><span>Record Authority Feedback</span></div>}
                open={showFeedbackModal}
                onCancel={() => { setShowFeedbackModal(false); setFeedbackSubId(null); setFeedbackText(''); }}
                onOk={handleSaveFeedback}
                okText="Save Feedback"
            >
                <div style={{ marginTop: '16px' }}>
                    <label style={labelStyle}>Feedback from Authority</label>
                    <TextArea
                        value={feedbackText}
                        onChange={e => setFeedbackText(e.target.value)}
                        rows={6}
                        placeholder="Enter feedback received from the regulatory authority..."
                    />
                </div>
            </Modal>
        </div>
    );
};

const labelStyle: React.CSSProperties = {
    display: 'block', fontSize: '13px', fontWeight: 500, color: '#555', marginBottom: '4px',
};

const actionBtnStyle = (bg: string): React.CSSProperties => ({
    padding: '2px 8px', fontSize: '11px', cursor: 'pointer',
    backgroundColor: bg, color: '#fff', border: 'none', borderRadius: '4px',
    display: 'inline-flex', alignItems: 'center', gap: '4px',
});

export default RegulatorySubmissionPage;
