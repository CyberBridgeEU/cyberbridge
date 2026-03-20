import { useEffect, useState, useMemo } from 'react';
import { Card, Spin, Empty, Tag, Tooltip, Row, Col, Statistic, Select, Button } from 'antd';
import Sidebar from '../components/Sidebar.tsx';
import { PartitionOutlined, DatabaseOutlined, WarningOutlined, SafetyCertificateOutlined, FileProtectOutlined, AimOutlined, FilterOutlined, PlusOutlined, MinusOutlined } from '@ant-design/icons';
import useAssetStore from '../store/useAssetStore.ts';
import useRiskStore from '../store/useRiskStore.ts';
import useControlStore from '../store/useControlStore.ts';
import usePolicyStore from '../store/usePolicyStore.ts';
import useFrameworksStore from '../store/useFrameworksStore.ts';
import useAuthStore from '../store/useAuthStore.ts';
import useCRAFilteredFrameworks from '../hooks/useCRAFilteredFrameworks.ts';
import InfoTitle from '../components/InfoTitle.tsx';
import { useLocation } from 'wouter';
import { useMenuHighlighting } from '../utils/menuUtils.ts';
import { cyberbridge_back_end_rest_api } from '../constants/urls.ts';
import {
    ReactFlow,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    Node,
    Edge,
    MarkerType,
    Position,
    Panel,
    Handle,
    useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Custom node colors
const nodeColors = {
    asset: '#1890ff',      // Blue
    risk: '#faad14',       // Gold/Yellow
    control: '#52c41a',    // Green
    policy: '#722ed1',     // Purple
    objective: '#eb2f96',  // Pink/Magenta
};

// Info content for the Compliance Chain Map page
const ComplianceChainMapInfo = (
    <div>
        <p><strong>Compliance Chain Map</strong> provides a visual overview of your GRC compliance relationships.</p>
        <p>This read-only view shows:</p>
        <ul>
            <li><span style={{ color: nodeColors.asset }}>Assets</span> - Your valuable resources</li>
            <li><span style={{ color: nodeColors.risk }}>Risks</span> - Threats to your assets</li>
            <li><span style={{ color: nodeColors.control }}>Controls</span> - Measures to mitigate risks</li>
            <li><span style={{ color: nodeColors.policy }}>Policies</span> - Governance documents</li>
            <li><span style={{ color: nodeColors.objective }}>Objectives</span> - Compliance goals</li>
        </ul>
        <p>Use the mouse wheel to zoom, and drag to pan around the map.</p>
    </div>
);

// Custom node component for better styling
const CustomNode = ({ data }: { data: { label: string; type: string; details?: string; count?: number; categoryLabel?: string; metaLines?: string[]; isSelected?: boolean; onSelect?: () => void } }) => {
    const color = nodeColors[data.type as keyof typeof nodeColors] || '#1890ff';
    const icons: Record<string, React.ReactNode> = {
        asset: <DatabaseOutlined />,
        risk: <WarningOutlined />,
        control: <SafetyCertificateOutlined />,
        policy: <FileProtectOutlined />,
        objective: <AimOutlined />,
    };

    const tooltipContent = data.details || [data.label, ...(data.metaLines || [])].filter(Boolean).join(' • ');

    return (
        <Tooltip title={tooltipContent}>
            <div
                onClick={(event) => {
                    event.stopPropagation();
                    data.onSelect?.();
                }}
                style={{
                    padding: '10px 16px',
                    borderRadius: '8px',
                    background: `linear-gradient(135deg, ${color}22 0%, ${color}11 100%)`,
                    border: `${data.isSelected ? 3 : 2}px solid ${color}`,
                    minWidth: '180px',
                    maxWidth: '300px',
                    textAlign: 'center',
                    boxShadow: data.isSelected ? `0 0 0 3px ${color}33, 0 4px 14px rgba(0,0,0,0.2)` : '0 2px 8px rgba(0,0,0,0.1)',
                    cursor: 'pointer',
                }}
            >
                <Handle type="target" position={Position.Left} style={{ opacity: 0, pointerEvents: 'none' }} />
                <Handle type="source" position={Position.Right} style={{ opacity: 0, pointerEvents: 'none' }} />
                {data.categoryLabel && (
                    <div style={{ fontSize: '10px', color: '#8c8c8c', textTransform: 'uppercase', letterSpacing: '0.6px' }}>
                        {data.categoryLabel}
                    </div>
                )}
                <div style={{ marginBottom: 4, color: color, fontSize: '18px' }}>
                    {icons[data.type]}
                </div>
                <div style={{
                    fontWeight: 500,
                    fontSize: '12px',
                    color: '#262626',
                    whiteSpace: 'normal',
                    wordBreak: 'break-word',
                    lineHeight: 1.35,
                }}>
                    {data.label}
                </div>
                {data.metaLines && data.metaLines.length > 0 && (
                    <div style={{ marginTop: 4, fontSize: '10px', color: '#666', lineHeight: 1.4 }}>
                        {data.metaLines.slice(0, 4).map((line, index) => (
                            <div key={index} style={{ whiteSpace: 'normal', wordBreak: 'break-word' }}>
                                {line}
                            </div>
                        ))}
                    </div>
                )}
                {data.count !== undefined && (
                    <Tag color={color} style={{ marginTop: 4, fontSize: '10px' }}>
                        {data.count} linked
                    </Tag>
                )}
            </div>
        </Tooltip>
    );
};

const nodeTypes = {
    custom: CustomNode,
};

const MapZoomButtons = () => {
    const { zoomIn, zoomOut } = useReactFlow();

    return (
        <Panel position="top-right">
            <div
                style={{
                    background: 'rgba(255,255,255,0.95)',
                    border: '1px solid #d9d9d9',
                    borderRadius: 8,
                    padding: 6,
                    display: 'flex',
                    gap: 6,
                    boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
                }}
            >
                <Button
                    size="small"
                    icon={<PlusOutlined />}
                    onClick={() => zoomIn({ duration: 180 })}
                    title="Zoom In"
                />
                <Button
                    size="small"
                    icon={<MinusOutlined />}
                    onClick={() => zoomOut({ duration: 180 })}
                    title="Zoom Out"
                />
            </div>
        </Panel>
    );
};

interface ChapterSummary {
    id: string;
    framework_id: string;
}

const ComplianceChainMapPage = () => {
    // Menu highlighting
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Store access
    const { assets, fetchAssets } = useAssetStore();
    const { risks, fetchRisks } = useRiskStore();
    const { controls, fetchControls } = useControlStore();
    const { policies, objectives, fetchPolicies, fetchObjectives } = usePolicyStore();
    const { frameworks, fetchFrameworks } = useFrameworksStore();
    const { getAuthHeader } = useAuthStore();
    const { filteredFrameworks, craFrameworkId, isCRAModeActive } = useCRAFilteredFrameworks();

    // State
    const [loading, setLoading] = useState(true);
    const [connectionsLoading, setConnectionsLoading] = useState(false);
    const [mapInitialized, setMapInitialized] = useState(false);
    const [mapRefreshNonce, setMapRefreshNonce] = useState(0);
    const [selectedAssetIds, setSelectedAssetIds] = useState<string[]>([]);
    const [selectedRiskIds, setSelectedRiskIds] = useState<string[]>([]);
    const [selectedControlIds, setSelectedControlIds] = useState<string[]>([]);
    const [selectedPolicyIds, setSelectedPolicyIds] = useState<string[]>([]);
    const [selectedFrameworkId, setSelectedFrameworkId] = useState<string | undefined>(undefined);
    const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
    const [chapterFrameworkMap, setChapterFrameworkMap] = useState<Record<string, string>>({});
    const [nodes, setNodes, onNodesChange] = useNodesState([] as Node[]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([] as Edge[]);
    const [connectionData, setConnectionData] = useState<{
        assetRisks: Record<string, string[]>;
        riskControls: Record<string, string[]>;
        controlPolicies: Record<string, string[]>;
        policyObjectives: Record<string, string[]>;
    }>({
        assetRisks: {},
        riskControls: {},
        controlPolicies: {},
        policyObjectives: {},
    });

    // Fetch all data on mount
    useEffect(() => {
        const loadAllData = async () => {
            setLoading(true);
            await Promise.all([
                fetchAssets(),
                fetchRisks(),
                fetchControls(),
                fetchPolicies(),
                fetchObjectives(),
                fetchFrameworks(),
            ]);

            try {
                const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/get_all_chapters?skip=0&limit=5000`, {
                    headers: {
                        ...getAuthHeader(),
                    },
                });

                if (response.ok) {
                    const chapters: ChapterSummary[] = await response.json();
                    const nextMap: Record<string, string> = {};
                    chapters.forEach((chapter) => {
                        if (chapter.id && chapter.framework_id) {
                            nextMap[String(chapter.id)] = String(chapter.framework_id);
                        }
                    });
                    setChapterFrameworkMap(nextMap);
                }
            } catch (error) {
                console.error('Error fetching chapter-framework map:', error);
            }

            setLoading(false);
        };
        loadAllData();
    }, []);

    // Auto-select CRA framework filter when CRA mode is active
    useEffect(() => {
        if (isCRAModeActive && craFrameworkId && !selectedFrameworkId) {
            setSelectedFrameworkId(craFrameworkId);
        }
    }, [isCRAModeActive, craFrameworkId]);

    // Fetch connection data in a single bulk request
    useEffect(() => {
        const fetchConnectionData = async () => {
            if (loading || !mapInitialized) return;
            if (!selectedFrameworkId) {
                setConnectionData({
                    assetRisks: {},
                    riskControls: {},
                    controlPolicies: {},
                    policyObjectives: {},
                });
                return;
            }
            setConnectionsLoading(true);

            try {
                const authHeader = getAuthHeader();
                const response = await fetch(
                    `${cyberbridge_back_end_rest_api}/chain-map/connections?framework_id=${selectedFrameworkId}`,
                    { headers: { ...authHeader } }
                );
                if (response.ok) {
                    const data = await response.json();
                    setConnectionData(data);
                } else {
                    setConnectionData({
                        assetRisks: {},
                        riskControls: {},
                        controlPolicies: {},
                        policyObjectives: {},
                    });
                }
            } finally {
                setConnectionsLoading(false);
            }
        };

        if (!loading && mapInitialized) {
            fetchConnectionData();
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [loading, mapInitialized, mapRefreshNonce, selectedFrameworkId]);

    // Build nodes and edges when data changes
    useEffect(() => {
        if (loading || !mapInitialized || connectionsLoading) return;

        // Get connected entity IDs
        const connectedAssetIds = new Set(Object.keys(connectionData.assetRisks));
        const connectedRiskIds = new Set([
            ...Object.values(connectionData.assetRisks).flat(),
            ...Object.keys(connectionData.riskControls),
        ]);
        const connectedControlIds = new Set([
            ...Object.values(connectionData.riskControls).flat(),
            ...Object.keys(connectionData.controlPolicies),
        ]);
        const connectedPolicyIds = new Set([
            ...Object.values(connectionData.controlPolicies).flat(),
            ...Object.keys(connectionData.policyObjectives),
        ]);
        const connectedObjectiveIds = new Set(Object.values(connectionData.policyObjectives).flat());

        const hasAssetFilter = selectedAssetIds.length > 0;
        const hasRiskFilter = selectedRiskIds.length > 0;
        const hasControlFilter = selectedControlIds.length > 0;
        const hasPolicyFilter = selectedPolicyIds.length > 0;
        const hasFrameworkFilter = !!selectedFrameworkId;
        const hasAnyFilter = hasAssetFilter || hasRiskFilter || hasControlFilter || hasPolicyFilter || hasFrameworkFilter;

        let finalAssetIds: Set<string>;
        let finalRiskIds: Set<string>;
        let finalControlIds: Set<string>;
        let finalPolicyIds: Set<string>;
        let finalObjectiveIds: Set<string>;

        if (!hasAnyFilter) {
            // No filters: use original connected sets (original behavior)
            finalAssetIds = connectedAssetIds;
            finalRiskIds = connectedRiskIds;
            finalControlIds = connectedControlIds;
            finalPolicyIds = connectedPolicyIds;
            finalObjectiveIds = connectedObjectiveIds;
        } else {
            // Start with all connected, then narrow by each entity filter
            let candidateAssetIds = hasAssetFilter
                ? new Set(selectedAssetIds.filter(id => connectedAssetIds.has(id)))
                : connectedAssetIds;
            let candidateRiskIds = hasRiskFilter
                ? new Set(selectedRiskIds.filter(id => connectedRiskIds.has(id)))
                : connectedRiskIds;
            let candidateControlIds = hasControlFilter
                ? new Set(selectedControlIds.filter(id => connectedControlIds.has(id)))
                : connectedControlIds;
            let candidatePolicyIds = hasPolicyFilter
                ? new Set(selectedPolicyIds.filter(id => connectedPolicyIds.has(id)))
                : connectedPolicyIds;

            // Apply framework filter on policies
            if (hasFrameworkFilter) {
                const frameworkFiltered = new Set<string>();
                candidatePolicyIds.forEach(policyId => {
                    const policy = policies.find(p => p.id === policyId);
                    if (policy?.frameworks && policy.frameworks.includes(selectedFrameworkId!)) {
                        frameworkFiltered.add(policyId);
                    }
                });
                candidatePolicyIds = frameworkFiltered;
            }

            // Propagate constraints through the chain in both directions
            // Forward pass: narrow downstream based on upstream selections
            if (hasAssetFilter) {
                // Only keep risks linked from selected assets
                const reachableRisks = new Set<string>();
                candidateAssetIds.forEach(assetId => {
                    (connectionData.assetRisks[assetId] || []).forEach(rid => {
                        if (candidateRiskIds.has(rid)) reachableRisks.add(rid);
                    });
                });
                candidateRiskIds = reachableRisks;
            }

            if (hasAssetFilter || hasRiskFilter) {
                // Only keep controls linked from candidate risks
                const reachableControls = new Set<string>();
                candidateRiskIds.forEach(riskId => {
                    (connectionData.riskControls[riskId] || []).forEach(cid => {
                        if (candidateControlIds.has(cid)) reachableControls.add(cid);
                    });
                });
                candidateControlIds = reachableControls;
            }

            if (hasAssetFilter || hasRiskFilter || hasControlFilter) {
                // Only keep policies linked from candidate controls
                const reachablePolicies = new Set<string>();
                candidateControlIds.forEach(controlId => {
                    (connectionData.controlPolicies[controlId] || []).forEach(pid => {
                        if (candidatePolicyIds.has(pid)) reachablePolicies.add(pid);
                    });
                });
                candidatePolicyIds = reachablePolicies;
            }

            // Backward pass: narrow upstream based on downstream selections
            if (hasPolicyFilter || hasFrameworkFilter) {
                // Only keep controls that lead to candidate policies
                const reachableControls = new Set<string>();
                candidateControlIds.forEach(controlId => {
                    const policyLinks = connectionData.controlPolicies[controlId] || [];
                    if (policyLinks.some(pid => candidatePolicyIds.has(pid))) {
                        reachableControls.add(controlId);
                    }
                });
                candidateControlIds = reachableControls;
            }

            if (hasPolicyFilter || hasFrameworkFilter || hasControlFilter) {
                // Only keep risks that lead to candidate controls
                const reachableRisks = new Set<string>();
                candidateRiskIds.forEach(riskId => {
                    const controlLinks = connectionData.riskControls[riskId] || [];
                    if (controlLinks.some(cid => candidateControlIds.has(cid))) {
                        reachableRisks.add(riskId);
                    }
                });
                candidateRiskIds = reachableRisks;
            }

            if (hasPolicyFilter || hasFrameworkFilter || hasControlFilter || hasRiskFilter) {
                // Only keep assets that lead to candidate risks
                const reachableAssets = new Set<string>();
                candidateAssetIds.forEach(assetId => {
                    const riskLinks = connectionData.assetRisks[assetId] || [];
                    if (riskLinks.some(rid => candidateRiskIds.has(rid))) {
                        reachableAssets.add(assetId);
                    }
                });
                candidateAssetIds = reachableAssets;
            }

            finalAssetIds = candidateAssetIds;
            finalRiskIds = candidateRiskIds;
            finalControlIds = candidateControlIds;
            finalPolicyIds = candidatePolicyIds;

            // Trace objectives downstream from final policies
            finalObjectiveIds = new Set<string>();
            finalPolicyIds.forEach(policyId => {
                (connectionData.policyObjectives[policyId] || []).forEach(objectiveId => {
                    if (!connectedObjectiveIds.has(objectiveId)) return;
                    if (!hasFrameworkFilter) {
                        finalObjectiveIds.add(objectiveId);
                        return;
                    }
                    const objective = objectives.find(o => o.id === objectiveId);
                    if (!objective) return;
                    const objectiveFrameworkId = chapterFrameworkMap[String(objective.chapter_id)];
                    if (objectiveFrameworkId === selectedFrameworkId) {
                        finalObjectiveIds.add(objectiveId);
                    }
                });
            });
        }

        // Filter to only show connected + filtered entities
        const finalAssets = assets.filter(a => finalAssetIds.has(a.id));
        const finalRisks = risks.filter(r => finalRiskIds.has(r.id));
        const finalControls = controls.filter(c => finalControlIds.has(c.id));
        const finalPolicies = policies.filter(p => finalPolicyIds.has(p.id));
        const finalObjectives = objectives.filter(o => finalObjectiveIds.has(o.id));

        const frameworkNameById = new Map(frameworks.map(framework => [framework.id, framework.name]));
        const objectiveFrameworkNames = new Map<string, string>();
        objectives.forEach((objective) => {
            const frameworkId = chapterFrameworkMap[String(objective.chapter_id)];
            if (!frameworkId) return;
            const frameworkName = frameworkNameById.get(frameworkId);
            if (!frameworkName) return;
            objectiveFrameworkNames.set(objective.id, frameworkName);
        });

        const getAssetMetaLines = (asset: typeof assets[number]) => ([
            asset.asset_type_name ? `Type: ${asset.asset_type_name}` : '',
            asset.version ? `Version: ${asset.version}` : '',
        ].filter(Boolean));

        const getRiskMetaLines = (risk: typeof risks[number]) => ([
            risk.risk_code ? `Code: ${risk.risk_code}` : '',
            risk.asset_category_name ? `Type: ${risk.asset_category_name}` : '',
            risk.risk_severity ? `Severity: ${risk.risk_severity}` : '',
            risk.risk_status ? `Status: ${risk.risk_status}` : '',
        ].filter(Boolean));

        const getControlMetaLines = (control: typeof controls[number]) => ([
            control.code ? `Code: ${control.code}` : '',
            control.category ? `Category: ${control.category}` : '',
            control.control_set_name ? `Set: ${control.control_set_name}` : '',
            control.control_status_name ? `Status: ${control.control_status_name}` : '',
        ].filter(Boolean));

        const getPolicyMetaLines = (policy: typeof policies[number]) => ([
            policy.policy_code ? `Code: ${policy.policy_code}` : '',
            policy.status_name || policy.status ? `Status: ${policy.status_name || policy.status}` : '',
            policy.framework_names && policy.framework_names.length > 0
                ? `Frameworks: ${policy.framework_names.slice(0, 2).join(', ')}${policy.framework_names.length > 2 ? '…' : ''}`
                : '',
        ].filter(Boolean));

        const getObjectiveMetaLines = (objective: typeof objectives[number]) => {
            const frameworkLabel = objectiveFrameworkNames.get(objective.id) || '';
            const chapterName = objective.chapter_name || '';
            return [
                frameworkLabel ? `Framework: ${frameworkLabel}` : '',
                chapterName ? `Chapter: ${chapterName}` : '',
                objective.subchapter ? `Subchapter: ${objective.subchapter}` : '',
            ].filter(Boolean);
        };

        const maxMetaLines = Math.max(
            0,
            ...finalAssets.map(asset => getAssetMetaLines(asset).length),
            ...finalRisks.map(risk => getRiskMetaLines(risk).length),
            ...finalControls.map(control => getControlMetaLines(control).length),
            ...finalPolicies.map(policy => getPolicyMetaLines(policy).length),
            ...finalObjectives.map(objective => getObjectiveMetaLines(objective).length)
        );

        // Build nodes with hierarchical layout
        const newNodes: Node[] = [];
        const columnWidth = 440;
        const rowHeight = 170 + Math.min(3, maxMetaLines) * 22;
        const rowGap = 64;
        const rowStep = rowHeight + rowGap;
        const startX = 50;
        const startY = 50;

        // Column 1: Assets
        finalAssets.forEach((asset, i) => {
            const riskCount = connectionData.assetRisks[asset.id]?.length || 0;
            const nodeId = `asset-${asset.id}`;
            newNodes.push({
                id: nodeId,
                type: 'custom',
                position: { x: startX, y: startY + i * rowStep },
                data: {
                    label: asset.name,
                    type: 'asset',
                    categoryLabel: 'Assets',
                    details: `${asset.name}${asset.asset_type_name ? ` (${asset.asset_type_name})` : ''}`,
                    metaLines: getAssetMetaLines(asset),
                    count: riskCount > 0 ? riskCount : undefined,
                    isSelected: selectedNodeId === nodeId,
                    onSelect: () => setSelectedNodeId((prev) => (prev === nodeId ? null : nodeId)),
                },
                sourcePosition: Position.Right,
                targetPosition: Position.Left,
            });
        });

        // Column 2: Risks
        finalRisks.forEach((risk, i) => {
            const controlCount = connectionData.riskControls[risk.id]?.length || 0;
            const nodeId = `risk-${risk.id}`;
            const riskLabel = (risk.risk_code && risk.risk_category_name)
                ? `${risk.risk_code}: ${risk.risk_category_name}`
                : (risk.risk_category_name || risk.risk_code || 'Risk');
            newNodes.push({
                id: nodeId,
                type: 'custom',
                position: { x: startX + columnWidth, y: startY + i * rowStep },
                data: {
                    label: riskLabel,
                    type: 'risk',
                    categoryLabel: 'Risks',
                    details: `${risk.risk_category_name || risk.risk_code || 'Risk'}${risk.risk_code ? ` (${risk.risk_code})` : ''}`,
                    metaLines: getRiskMetaLines(risk),
                    count: controlCount > 0 ? controlCount : undefined,
                    isSelected: selectedNodeId === nodeId,
                    onSelect: () => setSelectedNodeId((prev) => (prev === nodeId ? null : nodeId)),
                },
                sourcePosition: Position.Right,
                targetPosition: Position.Left,
            });
        });

        // Column 3: Controls
        finalControls.forEach((control, i) => {
            const policyCount = connectionData.controlPolicies[control.id]?.length || 0;
            const nodeId = `control-${control.id}`;
            const controlLabel = (control.code && control.name)
                ? `${control.code}: ${control.name}`
                : (control.name || control.code || 'Control');
            newNodes.push({
                id: nodeId,
                type: 'custom',
                position: { x: startX + columnWidth * 2, y: startY + i * rowStep },
                data: {
                    label: controlLabel,
                    type: 'control',
                    categoryLabel: 'Controls',
                    details: `${control.name || control.code || 'Control'}${control.code ? ` (${control.code})` : ''}`,
                    metaLines: getControlMetaLines(control),
                    count: policyCount > 0 ? policyCount : undefined,
                    isSelected: selectedNodeId === nodeId,
                    onSelect: () => setSelectedNodeId((prev) => (prev === nodeId ? null : nodeId)),
                },
                sourcePosition: Position.Right,
                targetPosition: Position.Left,
            });
        });

        // Column 4: Policies
        finalPolicies.forEach((policy, i) => {
            const objectiveCount = connectionData.policyObjectives[policy.id]?.length || 0;
            const policyLabel = policy.policy_code ? `${policy.policy_code}: ${policy.title}` : policy.title;
            const nodeId = `policy-${policy.id}`;
            newNodes.push({
                id: nodeId,
                type: 'custom',
                position: { x: startX + columnWidth * 3, y: startY + i * rowStep },
                data: {
                    label: policyLabel,
                    type: 'policy',
                    categoryLabel: 'Policies',
                    details: policy.policy_code ? `${policy.title} (${policy.policy_code})` : policyLabel,
                    metaLines: getPolicyMetaLines(policy),
                    count: objectiveCount > 0 ? objectiveCount : undefined,
                    isSelected: selectedNodeId === nodeId,
                    onSelect: () => setSelectedNodeId((prev) => (prev === nodeId ? null : nodeId)),
                },
                sourcePosition: Position.Right,
                targetPosition: Position.Left,
            });
        });

        // Column 5: Objectives
        finalObjectives.forEach((objective, i) => {
            const nodeId = `objective-${objective.id}`;
            const objectiveLabel = objective.title || 'Objective';
            newNodes.push({
                id: nodeId,
                type: 'custom',
                position: { x: startX + columnWidth * 4, y: startY + i * rowStep },
                data: {
                    label: objectiveLabel,
                    type: 'objective',
                    categoryLabel: 'Objectives',
                    details: objectiveLabel,
                    metaLines: getObjectiveMetaLines(objective),
                    isSelected: selectedNodeId === nodeId,
                    onSelect: () => setSelectedNodeId((prev) => (prev === nodeId ? null : nodeId)),
                },
                sourcePosition: Position.Right,
                targetPosition: Position.Left,
            });
        });

        // Build edges
        const newEdges: Edge[] = [];

        // Asset -> Risk edges
        Object.entries(connectionData.assetRisks).forEach(([assetId, riskIds]) => {
            riskIds.forEach(riskId => {
                if (newNodes.find(n => n.id === `asset-${assetId}`) && newNodes.find(n => n.id === `risk-${riskId}`)) {
                    newEdges.push({
                        id: `edge-asset-${assetId}-risk-${riskId}`,
                        source: `asset-${assetId}`,
                        target: `risk-${riskId}`,
                        animated: true,
                        style: { stroke: nodeColors.asset, strokeWidth: 2 },
                        markerEnd: { type: MarkerType.ArrowClosed, color: nodeColors.asset },
                    });
                }
            });
        });

        // Risk -> Control edges
        Object.entries(connectionData.riskControls).forEach(([riskId, controlIds]) => {
            controlIds.forEach(controlId => {
                if (newNodes.find(n => n.id === `risk-${riskId}`) && newNodes.find(n => n.id === `control-${controlId}`)) {
                    newEdges.push({
                        id: `edge-risk-${riskId}-control-${controlId}`,
                        source: `risk-${riskId}`,
                        target: `control-${controlId}`,
                        animated: true,
                        style: { stroke: nodeColors.risk, strokeWidth: 2 },
                        markerEnd: { type: MarkerType.ArrowClosed, color: nodeColors.risk },
                    });
                }
            });
        });

        // Control -> Policy edges
        Object.entries(connectionData.controlPolicies).forEach(([controlId, policyIds]) => {
            policyIds.forEach(policyId => {
                if (newNodes.find(n => n.id === `control-${controlId}`) && newNodes.find(n => n.id === `policy-${policyId}`)) {
                    newEdges.push({
                        id: `edge-control-${controlId}-policy-${policyId}`,
                        source: `control-${controlId}`,
                        target: `policy-${policyId}`,
                        animated: true,
                        style: { stroke: nodeColors.control, strokeWidth: 2 },
                        markerEnd: { type: MarkerType.ArrowClosed, color: nodeColors.control },
                    });
                }
            });
        });

        // Policy -> Objective edges
        Object.entries(connectionData.policyObjectives).forEach(([policyId, objectiveIds]) => {
            objectiveIds.forEach(objectiveId => {
                if (newNodes.find(n => n.id === `policy-${policyId}`) && newNodes.find(n => n.id === `objective-${objectiveId}`)) {
                    newEdges.push({
                        id: `edge-policy-${policyId}-objective-${objectiveId}`,
                        source: `policy-${policyId}`,
                        target: `objective-${objectiveId}`,
                        animated: true,
                        style: { stroke: nodeColors.policy, strokeWidth: 2 },
                        markerEnd: { type: MarkerType.ArrowClosed, color: nodeColors.policy },
                    });
                }
            });
        });

        if (selectedNodeId) {
            const nodeIdSet = new Set(newNodes.map((node) => node.id));
            if (!nodeIdSet.has(selectedNodeId)) {
                setSelectedNodeId(null);
                setNodes(newNodes);
                setEdges(newEdges);
                return;
            }

            // Focus mode: selected node + directly connected neighbors.
            const focusedNodeIds = new Set<string>([selectedNodeId]);
            newEdges.forEach((edge) => {
                if (edge.source === selectedNodeId) {
                    focusedNodeIds.add(edge.target);
                }
                if (edge.target === selectedNodeId) {
                    focusedNodeIds.add(edge.source);
                }
            });

            const focusedNodes = newNodes.filter((node) => focusedNodeIds.has(node.id));
            const focusedEdges = newEdges.filter(
                (edge) =>
                    focusedNodeIds.has(edge.source) &&
                    focusedNodeIds.has(edge.target) &&
                    (edge.source === selectedNodeId || edge.target === selectedNodeId)
            );

            setNodes(focusedNodes);
            setEdges(focusedEdges);
            return;
        }

        setNodes(newNodes);
        setEdges(newEdges);
    }, [loading, connectionsLoading, mapInitialized, connectionData, assets, risks, controls, policies, objectives, frameworks, selectedAssetIds, selectedRiskIds, selectedControlIds, selectedPolicyIds, selectedFrameworkId, chapterFrameworkMap, selectedNodeId]);

    // Legend component
    const Legend = () => (
        <div style={{
            background: 'white',
            padding: '12px 16px',
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            display: 'flex',
            gap: 16,
            flexWrap: 'wrap',
        }}>
            {Object.entries(nodeColors).map(([type, color]) => (
                <div key={type} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{
                        width: 12,
                        height: 12,
                        borderRadius: 3,
                        backgroundColor: color,
                    }} />
                    <span style={{ fontSize: 12, textTransform: 'capitalize' }}>{type.endsWith('y') ? type.slice(0, -1) + 'ies' : type + 's'}</span>
                </div>
            ))}
        </div>
    );

    // Statistics
    const stats = useMemo(() => ({
        totalConnections:
            Object.values(connectionData.assetRisks).flat().length +
            Object.values(connectionData.riskControls).flat().length +
            Object.values(connectionData.controlPolicies).flat().length +
            Object.values(connectionData.policyObjectives).flat().length,
        assetRiskLinks: Object.values(connectionData.assetRisks).flat().length,
        riskControlLinks: Object.values(connectionData.riskControls).flat().length,
        controlPolicyLinks: Object.values(connectionData.controlPolicies).flat().length,
        policyObjectiveLinks: Object.values(connectionData.policyObjectives).flat().length,
    }), [connectionData]);

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
                            <InfoTitle
                                icon={<PartitionOutlined />}
                                title="Compliance Chain - Map"
                                infoContent={ComplianceChainMapInfo}
                            />
                        </div>
                    </div>

                    {/* Filters */}
                    <Card style={{ marginBottom: 16 }}>
                        <Row gutter={[12, 12]} align="middle">
                            <Col>
                                <FilterOutlined style={{ color: '#8c8c8c', fontSize: 14 }} />
                            </Col>
                            <Col flex="1">
                                <Select
                                    mode="multiple"
                                    showSearch
                                    placeholder="Filter by assets..."
                                    options={assets.map(asset => ({
                                        label: `${asset.name}${asset.asset_type_name ? ` (${asset.asset_type_name})` : ''}`,
                                        value: asset.id,
                                    }))}
                                    value={selectedAssetIds}
                                    onChange={(values) => setSelectedAssetIds(values)}
                                    filterOption={(input, option) =>
                                        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                    }
                                    style={{ width: '100%' }}
                                    allowClear
                                    maxTagCount="responsive"
                                />
                            </Col>
                            <Col flex="1">
                                <Select
                                    mode="multiple"
                                    showSearch
                                    placeholder="Filter by risks..."
                                    options={risks.map(risk => ({
                                        label: `${risk.risk_code || risk.risk_category_name}${risk.risk_severity ? ` (${risk.risk_severity})` : ''}`,
                                        value: risk.id,
                                    }))}
                                    value={selectedRiskIds}
                                    onChange={(values) => setSelectedRiskIds(values)}
                                    filterOption={(input, option) =>
                                        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                    }
                                    style={{ width: '100%' }}
                                    allowClear
                                    maxTagCount="responsive"
                                />
                            </Col>
                            <Col flex="1">
                                <Select
                                    mode="multiple"
                                    showSearch
                                    placeholder="Filter by controls..."
                                    options={controls.map(control => ({
                                        label: `${control.code} - ${control.name}`,
                                        value: control.id,
                                    }))}
                                    value={selectedControlIds}
                                    onChange={(values) => setSelectedControlIds(values)}
                                    filterOption={(input, option) =>
                                        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                    }
                                    style={{ width: '100%' }}
                                    allowClear
                                    maxTagCount="responsive"
                                />
                            </Col>
                            <Col flex="1">
                                <Select
                                    mode="multiple"
                                    showSearch
                                    placeholder="Filter by policies..."
                                    options={policies.map(policy => ({
                                        label: policy.policy_code ? `${policy.policy_code}: ${policy.title}` : policy.title,
                                        value: policy.id,
                                    }))}
                                    value={selectedPolicyIds}
                                    onChange={(values) => setSelectedPolicyIds(values)}
                                    filterOption={(input, option) =>
                                        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                    }
                                    style={{ width: '100%' }}
                                    allowClear
                                    maxTagCount="responsive"
                                />
                            </Col>
                            <Col flex="1">
                                <Select
                                    showSearch
                                    placeholder="Select a framework..."
                                    options={filteredFrameworks.map(fw => ({
                                        label: fw.name,
                                        value: fw.id,
                                    }))}
                                    value={selectedFrameworkId}
                                    onChange={(value) => setSelectedFrameworkId(value)}
                                    filterOption={(input, option) =>
                                        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                    }
                                    style={{ width: '100%' }}
                                    allowClear
                                />
                            </Col>
                        </Row>
                    </Card>

                    {/* Statistics Summary */}
                    <Card style={{ marginBottom: 16 }}>
                        {selectedFrameworkId && (
                            <div style={{ marginBottom: 12, color: '#8c8c8c', fontSize: 13 }}>
                                Many-to-many connections between entities for the selected framework
                            </div>
                        )}
                        <Row gutter={16}>
                            <Col span={4}>
                                <Statistic
                                    title="Total Connections"
                                    value={stats.totalConnections}
                                    valueStyle={{ color: '#1890ff' }}
                                />
                            </Col>
                            <Col span={5}>
                                <Statistic
                                    title={<span><DatabaseOutlined /> → <WarningOutlined /></span>}
                                    value={stats.assetRiskLinks}
                                    suffix="links"
                                    valueStyle={{ color: nodeColors.asset }}
                                />
                            </Col>
                            <Col span={5}>
                                <Statistic
                                    title={<span><WarningOutlined /> → <SafetyCertificateOutlined /></span>}
                                    value={stats.riskControlLinks}
                                    suffix="links"
                                    valueStyle={{ color: nodeColors.risk }}
                                />
                            </Col>
                            <Col span={5}>
                                <Statistic
                                    title={<span><SafetyCertificateOutlined /> → <FileProtectOutlined /></span>}
                                    value={stats.controlPolicyLinks}
                                    suffix="links"
                                    valueStyle={{ color: nodeColors.control }}
                                />
                            </Col>
                            <Col span={5}>
                                <Statistic
                                    title={<span><FileProtectOutlined /> → <AimOutlined /></span>}
                                    value={stats.policyObjectiveLinks}
                                    suffix="links"
                                    valueStyle={{ color: nodeColors.policy }}
                                />
                            </Col>
                        </Row>
                        <div style={{ marginTop: 12, display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 12 }}>
                            {!selectedFrameworkId && (
                                <span style={{ color: '#8c8c8c', fontSize: 13 }}>Select a framework to load the map</span>
                            )}
                            <Button
                                type="primary"
                                disabled={!selectedFrameworkId}
                                onClick={() => {
                                    if (!mapInitialized) {
                                        setMapInitialized(true);
                                        return;
                                    }
                                    setMapRefreshNonce((prev) => prev + 1);
                                }}
                                loading={connectionsLoading}
                            >
                                {mapInitialized ? 'Reload All Nodes' : 'Load All Nodes'}
                            </Button>
                        </div>
                    </Card>

                    {/* Map View */}
                    <Card bodyStyle={{ padding: 0, height: 'calc(100vh - 340px)', minHeight: 500 }}>
                        {loading || connectionsLoading ? (
                            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                                <Spin size="large" tip="Loading compliance chain data..." />
                            </div>
                        ) : !mapInitialized ? (
                            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                                <Empty
                                    description="Set optional filters, then click 'Load All Nodes' to render the map."
                                />
                            </div>
                        ) : nodes.length === 0 ? (
                            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                                <Empty description="No compliance chain data to display. Create some entities and link them to see the map." />
                            </div>
                        ) : (
                            <ReactFlow
                                nodes={nodes}
                                edges={edges}
                                onNodesChange={onNodesChange}
                                onEdgesChange={onEdgesChange}
                                onPaneClick={() => setSelectedNodeId(null)}
                                nodeTypes={nodeTypes}
                                fitView
                                fitViewOptions={{ padding: 0.2 }}
                                minZoom={0.1}
                                maxZoom={2}
                                nodesDraggable={false}
                                nodesConnectable={false}
                                elementsSelectable={true}
                                panOnScroll
                                zoomOnScroll
                            >
                                <Background color="#f0f0f0" gap={20} />
                                <Controls showInteractive={false} />
                                <MapZoomButtons />
                                <MiniMap
                                    nodeColor={(node) => {
                                        const type = node.data?.type as string;
                                        return nodeColors[type as keyof typeof nodeColors] || '#1890ff';
                                    }}
                                    maskColor="rgba(0,0,0,0.1)"
                                    style={{ backgroundColor: '#fafafa' }}
                                />
                                <Panel position="top-left">
                                    <Legend />
                                </Panel>
                                <Panel position="bottom-center">
                                    <div style={{
                                        background: 'rgba(255,255,255,0.9)',
                                        padding: '8px 16px',
                                        borderRadius: 8,
                                        fontSize: 12,
                                        color: '#8c8c8c',
                                    }}>
                                        Scroll to zoom | Drag to pan | Click a node to focus connected items
                                    </div>
                                </Panel>
                            </ReactFlow>
                        )}
                    </Card>
                </div>
            </div>
        </div>
    );
};

export default ComplianceChainMapPage;
