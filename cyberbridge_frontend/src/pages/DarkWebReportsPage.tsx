import { useEffect, useState, useMemo } from 'react';
import { Row, Col, Card, Statistic, Button, Input, Tag, Space, Empty, Typography, message } from 'antd';
import {
    FileTextOutlined,
    FilePdfOutlined,
    SearchOutlined,
    CheckCircleOutlined,
    WarningOutlined,
    DownloadOutlined,
    FileOutlined,
    ReloadOutlined,
    SafetyOutlined,
} from '@ant-design/icons';
import Sidebar from '../components/Sidebar';
import { useLocation } from 'wouter';
import { useMenuHighlighting } from '../utils/menuUtils';
import useDarkWebStore from '../store/useDarkWebStore';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

const DarkWebReportsPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const [searchText, setSearchText] = useState('');

    const { scans, scansLoading, fetchScans, downloadPdf, downloadJson } = useDarkWebStore();

    useEffect(() => {
        fetchScans('completed', 100);
        const interval = setInterval(() => fetchScans('completed', 100), 5000);
        return () => clearInterval(interval);
    }, []);

    const completedScans = useMemo(() => {
        return scans.filter(s => s.status === 'completed');
    }, [scans]);

    const filteredReports = useMemo(() => {
        if (!searchText) return completedScans;
        const lower = searchText.toLowerCase();
        return completedScans.filter(s => s.keyword.toLowerCase().includes(lower));
    }, [completedScans, searchText]);

    const stats = useMemo(() => ({
        total: completedScans.length,
        pdfsAvailable: completedScans.filter(s => s.files?.pdf_exists).length,
        uniqueKeywords: new Set(completedScans.map(s => s.keyword)).size,
    }), [completedScans]);

    const handleDownloadPdf = async (scanId: string, keyword: string) => {
        try {
            await downloadPdf(scanId, keyword);
        } catch {
            message.error('Failed to download PDF');
        }
    };

    const handleDownloadJson = async (scanId: string, keyword: string) => {
        try {
            await downloadJson(scanId, keyword);
        } catch {
            message.error('Failed to download JSON');
        }
    };

    const getDuration = (startedAt?: string, completedAt?: string) => {
        if (!startedAt || !completedAt) return null;
        const start = new Date(startedAt.endsWith('Z') ? startedAt : startedAt + 'Z');
        const end = new Date(completedAt.endsWith('Z') ? completedAt : completedAt + 'Z');
        return Math.round((end.getTime() - start.getTime()) / 1000);
    };

    return (
        <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--page-background)' }}>
            <Sidebar
                selectedKeys={menuHighlighting.selectedKeys}
                openKeys={menuHighlighting.openKeys}
                onOpenChange={menuHighlighting.onOpenChange}
            />
            <div style={{ flex: 1, padding: '24px', overflow: 'auto' }}>
                {/* Header */}
                <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <Title level={3} style={{ margin: 0 }}>Dark Web Reports</Title>
                        <Text type="secondary">Access and download threat intelligence reports ({completedScans.length} completed)</Text>
                    </div>
                    <Button icon={<ReloadOutlined />} onClick={() => fetchScans('completed', 100)}>
                        Refresh
                    </Button>
                </div>

                {/* Search */}
                <Card style={{ marginBottom: 16 }} bodyStyle={{ padding: '12px 16px' }}>
                    <Input
                        placeholder="Search reports by keyword..."
                        prefix={<SearchOutlined />}
                        value={searchText}
                        onChange={e => setSearchText(e.target.value)}
                        style={{ maxWidth: 400 }}
                        allowClear
                    />
                </Card>

                {/* Stats */}
                <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                    <Col xs={24} sm={8}>
                        <Card>
                            <Statistic title="Completed Reports" value={stats.total} prefix={<FileTextOutlined />} valueStyle={{ color: '#1890ff' }} />
                        </Card>
                    </Col>
                    <Col xs={24} sm={8}>
                        <Card>
                            <Statistic title="PDFs Available" value={stats.pdfsAvailable} prefix={<FilePdfOutlined />} valueStyle={{ color: '#389e0d' }} />
                        </Card>
                    </Col>
                    <Col xs={24} sm={8}>
                        <Card>
                            <Statistic title="Unique Keywords" value={stats.uniqueKeywords} prefix={<SearchOutlined />} valueStyle={{ color: '#722ed1' }} />
                        </Card>
                    </Col>
                </Row>

                {/* Reports Grid */}
                {filteredReports.length > 0 ? (
                    <Row gutter={[16, 16]}>
                        {filteredReports.map(report => {
                            const duration = getDuration(report.started_at, report.completed_at);
                            const hasFindings = report.files?.pdf_exists;
                            return (
                                <Col xs={24} sm={12} lg={8} key={report.scan_id}>
                                    <Card
                                        hoverable
                                        actions={[
                                            <Button
                                                type="primary"
                                                size="small"
                                                icon={<DownloadOutlined />}
                                                disabled={!report.files?.pdf_exists}
                                                onClick={() => handleDownloadPdf(report.scan_id, report.keyword)}
                                            >
                                                PDF
                                            </Button>,
                                            <Button
                                                size="small"
                                                icon={<FileOutlined />}
                                                onClick={() => handleDownloadJson(report.scan_id, report.keyword)}
                                            >
                                                JSON
                                            </Button>,
                                        ]}
                                    >
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                                            <Text strong style={{ fontSize: 16, flex: 1, marginRight: 8 }}>{report.keyword}</Text>
                                            {hasFindings
                                                ? <Tag color="red" icon={<WarningOutlined />}>Breached</Tag>
                                                : <Tag color="green" icon={<SafetyOutlined />}>Secure</Tag>
                                            }
                                        </div>
                                        <div style={{ fontSize: 13, color: '#8c8c8c' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                <span>Scan ID:</span>
                                                <span style={{ fontFamily: 'monospace' }}>{report.scan_id.substring(0, 8)}...</span>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                <span>Status:</span>
                                                <Text type="success">Completed</Text>
                                            </div>
                                            {duration !== null && (
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                    <span>Duration:</span>
                                                    <span>{duration}s</span>
                                                </div>
                                            )}
                                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                                <span>Completed:</span>
                                                <span>
                                                    {report.completed_at
                                                        ? dayjs(report.completed_at.endsWith('Z') ? report.completed_at : report.completed_at + 'Z').format('DD/MM/YYYY HH:mm')
                                                        : '-'}
                                                </span>
                                            </div>
                                        </div>
                                    </Card>
                                </Col>
                            );
                        })}
                    </Row>
                ) : (
                    <Card>
                        <Empty
                            description={
                                searchText
                                    ? `No reports match your search "${searchText}"`
                                    : 'No reports yet. Run your first scan to generate threat intelligence reports.'
                            }
                        />
                    </Card>
                )}
            </div>
        </div>
    );
};

export default DarkWebReportsPage;
