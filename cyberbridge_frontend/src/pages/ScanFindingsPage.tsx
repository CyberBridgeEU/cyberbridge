import { useEffect, useState } from "react";
import { Card, Row, Col, Statistic, Table, Tag, Select, Input, Button, Space, Descriptions, Popconfirm, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import {
    FileSearchOutlined,
    ReloadOutlined,
    LinkOutlined,
    BugOutlined,
    SearchOutlined,
    CheckCircleOutlined,
    DeleteOutlined,
    RightOutlined,
    DownOutlined,
} from "@ant-design/icons";
import Sidebar from "../components/Sidebar.tsx";
import InfoTitle from "../components/InfoTitle.tsx";
import { ScanFindingsInfo } from "../constants/infoContent.tsx";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import useScanFindingStore, { ScanFindingWithCVE } from "../store/useScanFindingStore.ts";
import useAuthStore from "../store/useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import { deleteScannerHistoryRecord } from "../utils/scannerHistoryUtils.ts";

const severityColorMap: Record<string, string> = {
    critical: "red",
    high: "volcano",
    medium: "orange",
    low: "blue",
    info: "default",
    informational: "default",
};

const scannerColorMap: Record<string, string> = {
    zap: "purple",
    nmap: "cyan",
    semgrep: "geekblue",
    osv: "green",
};

const scannerLabelMap: Record<string, string> = {
    zap: "Web App Scanner",
    nmap: "Network Scanner",
    semgrep: "Code Scanner",
    osv: "Dependency Scanner",
};

interface ScanGroup {
    key: string;
    scan_history_id: string;
    scanner_type: string;
    scan_target: string | null;
    scan_timestamp: string | null;
    findings: ScanFindingWithCVE[];
    finding_count: number;
}

const ScanFindingsPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const [expandedScanKeys, setExpandedScanKeys] = useState<string[]>([]);
    const [expandedFindingKeys, setExpandedFindingKeys] = useState<Record<string, string[]>>({});
    const [risksCache, setRisksCache] = useState<Record<string, { id: string; risk_code: string | null; risk_category_name: string }[]>>({});
    const [deletingScans, setDeletingScans] = useState<Set<string>>(new Set());

    const {
        findings,
        total,
        offset,
        limit,
        loading,
        stats,
        statsLoading,
        filters,
        fetchFindings,
        fetchStats,
        toggleRemediation,
        setFilters,
        resetFilters,
        setOffset,
    } = useScanFindingStore();

    useEffect(() => {
        fetchStats();
        fetchFindings();
    }, []);

    // Re-fetch when filters or offset change
    useEffect(() => {
        fetchFindings();
    }, [filters, offset]);

    // Group findings by scan_history_id
    const scanGroups: ScanGroup[] = (() => {
        const groupMap = new Map<string, ScanFindingWithCVE[]>();
        for (const f of findings) {
            const key = f.scan_history_id;
            if (!groupMap.has(key)) groupMap.set(key, []);
            groupMap.get(key)!.push(f);
        }
        const groups: ScanGroup[] = [];
        for (const [scanHistoryId, groupFindings] of groupMap) {
            const first = groupFindings[0];
            groups.push({
                key: scanHistoryId,
                scan_history_id: scanHistoryId,
                scanner_type: first.scanner_type,
                scan_target: first.scan_target,
                scan_timestamp: first.scan_timestamp,
                findings: groupFindings,
                finding_count: groupFindings.length,
            });
        }
        // Sort by timestamp descending
        groups.sort((a, b) => {
            const tA = a.scan_timestamp ? new Date(a.scan_timestamp).getTime() : 0;
            const tB = b.scan_timestamp ? new Date(b.scan_timestamp).getTime() : 0;
            return tB - tA;
        });
        return groups;
    })();

    // Delete an entire scan (cascade-deletes all its findings)
    const handleDeleteScan = async (group: ScanGroup) => {
        setDeletingScans((prev) => new Set(prev).add(group.scan_history_id));
        try {
            const result = await deleteScannerHistoryRecord(group.scan_history_id);
            if (result.success) {
                message.success(`Deleted scan and ${group.finding_count} finding(s).`);
                fetchFindings();
                fetchStats();
            } else {
                message.error(result.error || "Failed to delete scan.");
            }
        } catch {
            message.error("Failed to delete scan.");
        } finally {
            setDeletingScans((prev) => {
                const next = new Set(prev);
                next.delete(group.scan_history_id);
                return next;
            });
        }
    };

    // Fetch linked risks when a finding row is expanded
    const handleFindingExpand = async (expanded: boolean, record: ScanFindingWithCVE, scanKey: string) => {
        if (expanded) {
            setExpandedFindingKeys((prev) => ({
                ...prev,
                [scanKey]: [...(prev[scanKey] || []), record.id],
            }));
            if (!risksCache[record.id]) {
                try {
                    const response = await fetch(
                        `${cyberbridge_back_end_rest_api}/scanners/findings/${record.id}/risks`,
                        { headers: { ...useAuthStore.getState().getAuthHeader() } }
                    );
                    if (response.ok) {
                        const data = await response.json();
                        setRisksCache((prev) => ({ ...prev, [record.id]: data }));
                    }
                } catch (e) {
                    console.error("Failed to fetch risks for finding", e);
                }
            }
        } else {
            setExpandedFindingKeys((prev) => ({
                ...prev,
                [scanKey]: (prev[scanKey] || []).filter((k) => k !== record.id),
            }));
        }
    };

    // Outer table columns (scan groups)
    const scanGroupColumns: ColumnsType<ScanGroup> = [
        {
            title: "Scanner",
            dataIndex: "scanner_type",
            key: "scanner_type",
            width: 160,
            render: (val: string) => (
                <Tag color={scannerColorMap[val] || "default"}>
                    {scannerLabelMap[val] || val}
                </Tag>
            ),
        },
        {
            title: "Target",
            dataIndex: "scan_target",
            key: "scan_target",
            ellipsis: true,
        },
        {
            title: "Findings",
            dataIndex: "finding_count",
            key: "finding_count",
            width: 100,
            align: "center" as const,
            render: (count: number) => <Tag color="blue">{count}</Tag>,
        },
        {
            title: "Date",
            dataIndex: "scan_timestamp",
            key: "scan_timestamp",
            width: 180,
            render: (val: string | null) => {
                if (!val) return "-";
                return new Date(val).toLocaleString();
            },
        },
        {
            title: "",
            key: "actions",
            width: 50,
            align: "center" as const,
            render: (_: unknown, record: ScanGroup) => (
                <Popconfirm
                    title="Delete this scan?"
                    description={`This will permanently delete ${record.finding_count} finding(s) from this scan.`}
                    onConfirm={() => handleDeleteScan(record)}
                    okText="Delete"
                    okButtonProps={{ danger: true }}
                >
                    <Button
                        type="text"
                        danger
                        icon={<DeleteOutlined />}
                        size="small"
                        loading={deletingScans.has(record.scan_history_id)}
                    />
                </Popconfirm>
            ),
        },
    ];

    // Inner table columns (individual findings)
    const findingColumns: ColumnsType<ScanFindingWithCVE> = [
        {
            title: "Title",
            dataIndex: "title",
            key: "title",
            ellipsis: true,
        },
        {
            title: "Severity",
            dataIndex: "normalized_severity",
            key: "normalized_severity",
            width: 110,
            render: (val: string | null) => {
                const s = val || "unknown";
                return <Tag color={severityColorMap[s] || "default"}>{s.toUpperCase()}</Tag>;
            },
        },
        {
            title: "Identifier",
            dataIndex: "identifier",
            key: "identifier",
            width: 160,
            ellipsis: true,
        },
        {
            title: "CVE Score",
            key: "cvss",
            width: 110,
            render: (_: unknown, record: ScanFindingWithCVE) => {
                if (record.cvss_v31_score == null) return "-";
                const sev = (record.cvss_v31_severity || "").toLowerCase();
                return (
                    <Tag color={severityColorMap[sev] || "default"}>
                        {record.cvss_v31_score.toFixed(1)} {record.cvss_v31_severity}
                    </Tag>
                );
            },
        },
        {
            title: "Risks",
            key: "risks",
            width: 80,
            align: "center" as const,
            render: (_: unknown, record: ScanFindingWithCVE) => {
                if (record.linked_risks_count === 0)
                    return <Tag>0</Tag>;
                return <Tag color="blue">{record.linked_risks_count}</Tag>;
            },
        },
        {
            title: "Remediated",
            key: "is_remediated",
            width: 110,
            align: "center" as const,
            render: (_: unknown, record: ScanFindingWithCVE) => (
                <div
                    className={`scan-findings-remediated-toggle ${record.is_remediated ? "is-active" : ""}`}
                    role="switch"
                    aria-checked={record.is_remediated}
                    tabIndex={0}
                    onClick={() => void toggleRemediation(record.id)}
                    onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                            event.preventDefault();
                            void toggleRemediation(record.id);
                        }
                    }}
                >
                    <span className="scan-findings-remediated-toggle-thumb" />
                </div>
            ),
        },
    ];

    const findingExpandedRowRender = (record: ScanFindingWithCVE) => {
        const linkedRisks = risksCache[record.id] || [];
        return (
            <div style={{ padding: "8px 16px" }}>
                <Descriptions column={1} size="small" bordered>
                    {record.description && (
                        <Descriptions.Item label="Description">
                            <div style={{ whiteSpace: "pre-wrap", maxHeight: 200, overflow: "auto" }}>
                                {record.description}
                            </div>
                        </Descriptions.Item>
                    )}
                    {record.solution && (
                        <Descriptions.Item label="Solution">
                            <div style={{ whiteSpace: "pre-wrap", maxHeight: 200, overflow: "auto" }}>
                                {record.solution}
                            </div>
                        </Descriptions.Item>
                    )}
                    {record.url_or_target && (
                        <Descriptions.Item label="URL / Target">{record.url_or_target}</Descriptions.Item>
                    )}
                    {record.cve_description && (
                        <Descriptions.Item label="CVE Details">
                            <div style={{ whiteSpace: "pre-wrap", maxHeight: 200, overflow: "auto" }}>
                                {record.cve_description}
                            </div>
                            {record.cve_published && (
                                <div style={{ marginTop: 4, color: "rgba(255,255,255,0.45)", fontSize: 12 }}>
                                    Published: {new Date(record.cve_published).toLocaleDateString()}
                                </div>
                            )}
                        </Descriptions.Item>
                    )}
                    {record.cvss_v31_score != null && (
                        <Descriptions.Item label="CVSS v3.1">
                            <Tag color={severityColorMap[(record.cvss_v31_severity || "").toLowerCase()] || "default"}>
                                {record.cvss_v31_score.toFixed(1)} - {record.cvss_v31_severity}
                            </Tag>
                        </Descriptions.Item>
                    )}
                    <Descriptions.Item label="Linked Risks">
                        {linkedRisks.length === 0 ? (
                            <span style={{ color: "rgba(255,255,255,0.45)" }}>No linked risks</span>
                        ) : (
                            <Space wrap>
                                {linkedRisks.map((r: { id: string; risk_code: string | null; risk_category_name: string }) => (
                                    <Tag key={r.id} color="blue">
                                        {r.risk_code || r.risk_category_name}
                                    </Tag>
                                ))}
                            </Space>
                        )}
                    </Descriptions.Item>
                </Descriptions>
            </div>
        );
    };

    const currentPage = Math.floor(offset / limit) + 1;

    return (
        <div>
            <div className="page-parent">
                <Sidebar
                    selectedKeys={menuHighlighting.selectedKeys}
                    openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange}
                />
                <div className="page-content">
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <FileSearchOutlined style={{ fontSize: 22, color: "#0f386a" }} />
                            <InfoTitle
                                title="Scan Findings"
                                infoContent={ScanFindingsInfo}
                                className="page-title"
                            />
                        </div>
                    </div>

                    {/* Stats Row */}
                    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                        <Col xs={12} sm={8} md={5}>
                            <Card size="small" loading={statsLoading}>
                                <Statistic
                                    title="Total Findings"
                                    value={stats?.total ?? 0}
                                    prefix={<BugOutlined />}
                                />
                            </Card>
                        </Col>
                        <Col xs={12} sm={8} md={5}>
                            <Card size="small" loading={statsLoading}>
                                <Statistic
                                    title="Remediated"
                                    value={stats?.remediated ?? 0}
                                    suffix={stats && stats.total > 0 ? `/ ${stats.total} (${Math.round((stats.remediated / stats.total) * 100)}%)` : ""}
                                    prefix={<CheckCircleOutlined />}
                                    valueStyle={{ color: (stats?.remediated ?? 0) > 0 ? "#52c41a" : undefined }}
                                />
                            </Card>
                        </Col>
                        <Col xs={12} sm={8} md={5}>
                            <Card size="small" loading={statsLoading}>
                                <Statistic
                                    title="Linked to Risks"
                                    value={stats?.linked_to_risks ?? 0}
                                    suffix={stats && stats.total > 0 ? `/ ${stats.total} (${Math.round((stats.linked_to_risks / stats.total) * 100)}%)` : ""}
                                    prefix={<LinkOutlined />}
                                />
                            </Card>
                        </Col>
                        <Col xs={12} sm={12} md={4}>
                            <Card size="small" loading={statsLoading}>
                                <div style={{ marginBottom: 4, color: "rgba(255,255,255,0.45)", fontSize: 14 }}>By Scanner</div>
                                <Space wrap size={4}>
                                    {stats?.by_scanner && Object.entries(stats.by_scanner).map(([key, val]) => (
                                        <Tag key={key} color={scannerColorMap[key] || "default"}>
                                            {scannerLabelMap[key] || key}: {val}
                                        </Tag>
                                    ))}
                                    {(!stats?.by_scanner || Object.keys(stats.by_scanner).length === 0) && (
                                        <span style={{ color: "rgba(255,255,255,0.35)" }}>No data</span>
                                    )}
                                </Space>
                            </Card>
                        </Col>
                        <Col xs={24} sm={12} md={5}>
                            <Card size="small" loading={statsLoading}>
                                <div style={{ marginBottom: 4, color: "rgba(255,255,255,0.45)", fontSize: 14 }}>By Severity</div>
                                <Space wrap size={4}>
                                    {stats?.by_severity && Object.entries(stats.by_severity).map(([key, val]) => (
                                        <Tag key={key} color={severityColorMap[key] || "default"}>
                                            {key.toUpperCase()}: {val}
                                        </Tag>
                                    ))}
                                    {(!stats?.by_severity || Object.keys(stats.by_severity).length === 0) && (
                                        <span style={{ color: "rgba(255,255,255,0.35)" }}>No data</span>
                                    )}
                                </Space>
                            </Card>
                        </Col>
                    </Row>

                    {/* Filters Row */}
                    <Card size="small" style={{ marginBottom: 16 }}>
                        <Space wrap size={12}>
                            <Select
                                placeholder="Scanner Type"
                                allowClear
                                style={{ width: 180 }}
                                value={filters.scanner_type}
                                onChange={(val) => setFilters({ scanner_type: val || null })}
                                options={[
                                    { value: "zap", label: "Web App Scanner" },
                                    { value: "nmap", label: "Network Scanner" },
                                    { value: "semgrep", label: "Code Scanner" },
                                    { value: "osv", label: "Dependency Scanner" },
                                ]}
                            />
                            <Select
                                placeholder="Severity"
                                allowClear
                                style={{ width: 140 }}
                                value={filters.severity}
                                onChange={(val) => setFilters({ severity: val || null })}
                                options={[
                                    { value: "critical", label: "Critical" },
                                    { value: "high", label: "High" },
                                    { value: "medium", label: "Medium" },
                                    { value: "low", label: "Low" },
                                    { value: "info", label: "Info" },
                                ]}
                            />
                            <Select
                                placeholder="Risk Link"
                                allowClear
                                style={{ width: 140 }}
                                value={filters.has_risks === null ? undefined : filters.has_risks ? "linked" : "unlinked"}
                                onChange={(val) => {
                                    if (val === "linked") setFilters({ has_risks: true });
                                    else if (val === "unlinked") setFilters({ has_risks: false });
                                    else setFilters({ has_risks: null });
                                }}
                                options={[
                                    { value: "linked", label: "Linked" },
                                    { value: "unlinked", label: "Unlinked" },
                                ]}
                            />
                            <Select
                                placeholder="Remediated"
                                allowClear
                                style={{ width: 150 }}
                                value={filters.is_remediated === null ? undefined : filters.is_remediated ? "yes" : "no"}
                                onChange={(val) => {
                                    if (val === "yes") setFilters({ is_remediated: true });
                                    else if (val === "no") setFilters({ is_remediated: false });
                                    else setFilters({ is_remediated: null });
                                }}
                                options={[
                                    { value: "yes", label: "Remediated" },
                                    { value: "no", label: "Not Remediated" },
                                ]}
                            />
                            <Input.Search
                                placeholder="Search title, identifier..."
                                allowClear
                                style={{ width: 260 }}
                                prefix={<SearchOutlined />}
                                onSearch={(val) => setFilters({ search: val || null })}
                                defaultValue={filters.search || ""}
                            />
                            <Button onClick={() => { resetFilters(); fetchStats(); }}>
                                Reset
                            </Button>
                            <Button
                                icon={<ReloadOutlined />}
                                onClick={() => { fetchFindings(); fetchStats(); }}
                            >
                                Refresh
                            </Button>
                        </Space>
                    </Card>

                    {/* Grouped Findings Table */}
                    <Table<ScanGroup>
                        dataSource={scanGroups}
                        columns={scanGroupColumns}
                        rowKey="key"
                        loading={loading}
                        size="small"
                        expandable={{
                            expandedRowKeys: expandedScanKeys,
                            onExpand: (expanded, record) => {
                                setExpandedScanKeys((prev) =>
                                    expanded ? [...prev, record.key] : prev.filter((k) => k !== record.key)
                                );
                            },
                            expandIcon: ({ expanded, onExpand, record }) => (
                                <span onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#1890ff', padding: '4px' }}>
                                    {expanded ? <DownOutlined /> : <RightOutlined />}
                                </span>
                            ),
                            expandedRowRender: (scanGroup) => (
                                <Table<ScanFindingWithCVE>
                                    dataSource={scanGroup.findings}
                                    columns={findingColumns}
                                    rowKey="id"
                                    size="small"
                                    pagination={scanGroup.findings.length > 10 ? { pageSize: 10, size: "small" } : false}
                                    expandable={{
                                        expandedRowKeys: expandedFindingKeys[scanGroup.key] || [],
                                        expandedRowRender: findingExpandedRowRender,
                                        onExpand: (expanded, record) => handleFindingExpand(expanded, record, scanGroup.key),
                                        expandIcon: ({ expanded, onExpand, record }) => (
                                            <span onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#1890ff', padding: '4px' }}>
                                                {expanded ? <DownOutlined /> : <RightOutlined />}
                                            </span>
                                        ),
                                    }}
                                />
                            ),
                        }}
                        pagination={{
                            current: currentPage,
                            pageSize: limit,
                            total,
                            showSizeChanger: false,
                            showTotal: (t, range) => `${range[0]}-${range[1]} of ${t} findings`,
                            onChange: (page) => setOffset((page - 1) * limit),
                        }}
                    />
                </div>
            </div>
        </div>
    );
};

export default ScanFindingsPage;
