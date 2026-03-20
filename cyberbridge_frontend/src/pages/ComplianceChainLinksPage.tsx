import { Select, notification, Tabs, Card, Row, Col, Empty, Statistic, Alert, Button, Modal, Tooltip } from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { LinkOutlined, DatabaseOutlined, WarningOutlined, SafetyCertificateOutlined, FileProtectOutlined, AimOutlined, ArrowRightOutlined, ImportOutlined, SyncOutlined } from '@ant-design/icons';
import useAssetStore from "../store/useAssetStore.ts";
import useRiskStore from "../store/useRiskStore.ts";
import useControlStore from "../store/useControlStore.ts";
import usePolicyStore from "../store/usePolicyStore.ts";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import useCRAFilteredFrameworks from "../hooks/useCRAFilteredFrameworks.ts";
import { useEffect, useState, useMemo, useCallback } from "react";
import useAuthStore from "../store/useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import ConnectionBoard from "../components/ConnectionBoard.tsx";
import SuggestionPanel from "../components/SuggestionPanel.tsx";
import useSuggestionStore from "../store/useSuggestionStore.ts";
import { useLocation } from "wouter";
import { useMenuHighlighting } from "../utils/menuUtils.ts";

// Info content for the Compliance Chain Links page
const ComplianceChainLinksInfo = (
    <div>
        <p><strong>Compliance Chain Links</strong> provides a unified view of all connections in your GRC compliance chain.</p>
        <p>The compliance chain flows as follows:</p>
        <ul>
            <li><strong>Assets</strong> are exposed to <strong>Risks</strong></li>
            <li><strong>Risks</strong> are mitigated by <strong>Controls</strong></li>
            <li><strong>Controls</strong> are governed by <strong>Policies</strong></li>
            <li><strong>Policies</strong> address <strong>Objectives</strong></li>
        </ul>
        <p>Use this page to manage connections at any level of the chain.</p>
    </div>
);

const ComplianceChainLinksPage = () => {
    // Menu highlighting
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    // Notification & Modal
    const [api, contextHolder] = notification.useNotification();
    const [modal, modalContextHolder] = Modal.useModal();

    // Tab state
    const [activeTab, setActiveTab] = useState('asset-risk');

    // Asset store
    const {
        assets,
        linkedRisks: assetLinkedRisks,
        fetchAssets,
        fetchLinkedRisks: fetchAssetLinkedRisks,
        linkAssetToRisk,
        unlinkAssetFromRisk,
    } = useAssetStore();

    // Risk store
    const {
        risks,
        linkedControls: riskLinkedControls,
        fetchRisks,
        fetchLinkedControls: fetchRiskLinkedControls,
    } = useRiskStore();

    // Control store
    const {
        controls,
        linkedPolicies: controlLinkedPolicies,
        fetchControls,
        fetchLinkedPolicies: fetchControlLinkedPolicies,
        linkControlToRisk,
        unlinkControlFromRisk,
        linkControlToPolicy,
        unlinkControlFromPolicy,
    } = useControlStore();

    // Policy store
    const {
        policies,
        objectives,
        linkedObjectives: policyLinkedObjectives,
        fetchPolicies,
        fetchObjectives,
        fetchLinkedObjectives: fetchPolicyLinkedObjectives,
        addObjectiveToPolicy,
        removeObjectiveFromPolicy,
    } = usePolicyStore();

    // Framework store
    const { fetchFrameworks, fetchChainLinksStatus, importChainLinks, fetchEntityCounts, checkChainLinksUpdates, applyChainLinksUpdates } = useFrameworksStore();
    const { filteredFrameworks, craFrameworkId, isCRAModeActive } = useCRAFilteredFrameworks();

    // Auth store (for direct API calls)
    const { getAuthHeader } = useAuthStore();

    // Chapter → framework mapping (for filtering objectives by framework)
    const [chapterFrameworkMap, setChapterFrameworkMap] = useState<Record<string, string>>({});

    // Framework selection for framework-scoped connections
    const [selectedFrameworkId, setSelectedFrameworkId] = useState<string | undefined>(undefined);

    // Selection state for each connection type
    const [selectedAsset, setSelectedAsset] = useState<string | undefined>(undefined);
    const [selectedRiskForControls, setSelectedRiskForControls] = useState<string | undefined>(undefined);
    const [selectedControl, setSelectedControl] = useState<string | undefined>(undefined);
    const [selectedPolicy, setSelectedPolicy] = useState<string | undefined>(undefined);

    // Pre-filter state for cascading filters (per-tab, independent)
    // Risk→Controls tab: Asset(s) → Select Risk
    const [selectedAssetFilterRC, setSelectedAssetFilterRC] = useState<string[]>([]);
    const [assetFilteredRiskIdsRC, setAssetFilteredRiskIdsRC] = useState<Set<string> | null>(null);

    // Controls→Policies tab: Asset(s) → Risk(s) → Select Control
    const [selectedAssetFilterCP, setSelectedAssetFilterCP] = useState<string[]>([]);
    const [assetFilteredRiskIdsCP, setAssetFilteredRiskIdsCP] = useState<Set<string> | null>(null);
    const [selectedRiskFilterCP, setSelectedRiskFilterCP] = useState<string[]>([]);
    const [riskFilteredControlIdsCP, setRiskFilteredControlIdsCP] = useState<Set<string> | null>(null);

    // Policies→Objectives tab: Asset(s) → Risk(s) → Control(s) → Select Policy
    const [selectedAssetFilterPO, setSelectedAssetFilterPO] = useState<string[]>([]);
    const [assetFilteredRiskIdsPO, setAssetFilteredRiskIdsPO] = useState<Set<string> | null>(null);
    const [selectedRiskFilterPO, setSelectedRiskFilterPO] = useState<string[]>([]);
    const [riskFilteredControlIdsPO, setRiskFilteredControlIdsPO] = useState<Set<string> | null>(null);
    const [selectedControlFilterPO, setSelectedControlFilterPO] = useState<string[]>([]);
    const [controlFilteredPolicyIdsPO, setControlFilteredPolicyIdsPO] = useState<Set<string> | null>(null);

    // AI suggestion external selection state (per-tab)
    const [suggestedAvailableAR, setSuggestedAvailableAR] = useState<string[]>([]);
    const [suggestedAvailableRC, setSuggestedAvailableRC] = useState<string[]>([]);
    const [suggestedAvailableCP, setSuggestedAvailableCP] = useState<string[]>([]);
    const [suggestedAvailablePO, setSuggestedAvailablePO] = useState<string[]>([]);
    const { clearSuggestions, cancelAllRequests } = useSuggestionStore();

    // Cancel all pending suggestion requests when leaving the page
    useEffect(() => {
        return () => {
            cancelAllRequests();
        };
    }, [cancelAllRequests]);

    // Helper to add suggested IDs to external selection (merges, not replaces)
    const handleSuggestionSelectAR = useCallback((ids: string[]) => {
        setSuggestedAvailableAR(prev => Array.from(new Set([...prev, ...ids])));
    }, []);
    const handleSuggestionSelectRC = useCallback((ids: string[]) => {
        setSuggestedAvailableRC(prev => Array.from(new Set([...prev, ...ids])));
    }, []);
    const handleSuggestionSelectCP = useCallback((ids: string[]) => {
        setSuggestedAvailableCP(prev => Array.from(new Set([...prev, ...ids])));
    }, []);
    const handleSuggestionSelectPO = useCallback((ids: string[]) => {
        setSuggestedAvailablePO(prev => Array.from(new Set([...prev, ...ids])));
    }, []);

    // Loading state
    const [loading, setLoading] = useState(false);

    // Chain links import state
    const [chainLinksStatus, setChainLinksStatus] = useState<{
        has_mapping: boolean;
        already_imported: boolean;
        framework_name: string;
    } | null>(null);
    const [importLoading, setImportLoading] = useState(false);

    // Framework-scoped entity counts
    const [entityCounts, setEntityCounts] = useState<{
        objectives: number; risks: number; controls: number; policies: number;
    } | null>(null);

    // Check for updates state
    const [updateCheckLoading, setUpdateCheckLoading] = useState(false);
    const [updateCheckResult, setUpdateCheckResult] = useState<any>(null);
    const [updateModalVisible, setUpdateModalVisible] = useState(false);
    const [applyUpdateLoading, setApplyUpdateLoading] = useState(false);

    // Initial data fetch
    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            await Promise.all([
                fetchAssets(),
                fetchRisks(),
                fetchControls(),
                fetchPolicies(),
                fetchObjectives(),
                fetchFrameworks(),
            ]);

            // Build chapter → framework mapping for objective filtering
            try {
                const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/get_all_chapters?skip=0&limit=5000`, {
                    headers: { ...getAuthHeader() },
                });
                if (response.ok) {
                    const chapters: { id: string; framework_id: string }[] = await response.json();
                    const nextMap: Record<string, string> = {};
                    chapters.forEach((ch) => {
                        if (ch.id && ch.framework_id) nextMap[String(ch.id)] = String(ch.framework_id);
                    });
                    setChapterFrameworkMap(nextMap);
                }
            } catch (error) {
                console.error('Error fetching chapter-framework map:', error);
            }

            setLoading(false);
        };
        loadData();
    }, []);

    // Auto-select CRA framework when CRA mode is active
    useEffect(() => {
        if (isCRAModeActive && craFrameworkId && !selectedFrameworkId) {
            setSelectedFrameworkId(craFrameworkId);
        }
    }, [isCRAModeActive, craFrameworkId]);

    // Fetch chain links status and entity counts when framework selection changes
    useEffect(() => {
        if (selectedFrameworkId) {
            fetchChainLinksStatus(selectedFrameworkId).then(status => {
                setChainLinksStatus(status);
            });
            fetchEntityCounts(selectedFrameworkId).then(counts => {
                setEntityCounts(counts);
            });
        } else {
            setChainLinksStatus(null);
            setEntityCounts(null);
        }
    }, [selectedFrameworkId]);

    // Handle import chain links
    const handleImportChainLinks = () => {
        if (!selectedFrameworkId || !chainLinksStatus) return;
        const frameworkName = chainLinksStatus.framework_name;

        modal.confirm({
            title: 'Import Chain Links',
            content: (
                <div>
                    <p>This will import the pre-defined chain links mapping for <strong>{frameworkName}</strong>.</p>
                    <p>The following will be created if they don't already exist:</p>
                    <ul>
                        <li>Risks from risk templates</li>
                        <li>Controls in the Baseline Controls set</li>
                        <li>Policies from policy templates</li>
                    </ul>
                    <p>All 6 junction tables (objective-risk, objective-control, policy-objective, control-risk, control-policy, policy-framework) will be wired.</p>
                    <p>This operation is idempotent — running it again won't create duplicates.</p>
                </div>
            ),
            okText: 'Import',
            cancelText: 'Cancel',
            onOk: async () => {
                setImportLoading(true);
                const result = await importChainLinks(selectedFrameworkId);
                setImportLoading(false);

                if (result.success && result.data) {
                    const d = result.data;
                    const totalLinks = Object.values(d.links_created as Record<string, number>).reduce((a: number, b: number) => a + b, 0);
                    api.success({
                        message: 'Chain Links Imported',
                        description: `${totalLinks} links created (${d.risks_created} risks, ${d.controls_created} controls, ${d.policies_created} policies)`,
                        duration: 8,
                    });

                    // Refresh chain links status and entity counts
                    const newStatus = await fetchChainLinksStatus(selectedFrameworkId);
                    setChainLinksStatus(newStatus);
                    const newCounts = await fetchEntityCounts(selectedFrameworkId);
                    setEntityCounts(newCounts);

                    // Refresh store data
                    await Promise.all([
                        fetchRisks(),
                        fetchControls(),
                        fetchPolicies(),
                        fetchObjectives(),
                    ]);
                } else {
                    api.error({
                        message: 'Import Failed',
                        description: result.error || 'Failed to import chain links',
                    });
                }
            },
        });
    };

    // Handle check for updates
    const handleCheckForUpdates = async () => {
        if (!selectedFrameworkId) return;
        setUpdateCheckLoading(true);
        const result = await checkChainLinksUpdates(selectedFrameworkId);
        setUpdateCheckLoading(false);

        if (!result) {
            api.error({ message: 'Check Failed', description: 'Failed to check for updates' });
            return;
        }

        if (!result.has_updates) {
            api.success({ message: 'Up to Date', description: `${result.framework_name} chain links are already up to date.` });
            return;
        }

        setUpdateCheckResult(result);
        setUpdateModalVisible(true);
    };

    // Handle apply updates
    const handleApplyUpdates = async () => {
        if (!selectedFrameworkId) return;
        setApplyUpdateLoading(true);
        const result = await applyChainLinksUpdates(selectedFrameworkId);
        setApplyUpdateLoading(false);

        if (result.success && result.data) {
            const d = result.data;
            const totalLinks = Object.values(d.links_created as Record<string, number>).reduce((a: number, b: number) => a + b, 0);
            api.success({
                message: 'Updates Applied',
                description: `${d.risks_created} risks, ${d.controls_created} controls, ${d.policies_created} policies created. ${totalLinks} links added. ${d.objectives_updated} objectives updated.`,
                duration: 8,
            });

            setUpdateModalVisible(false);
            setUpdateCheckResult(null);

            // Refresh all data
            const [newStatus, newCounts] = await Promise.all([
                fetchChainLinksStatus(selectedFrameworkId),
                fetchEntityCounts(selectedFrameworkId),
            ]);
            setChainLinksStatus(newStatus);
            setEntityCounts(newCounts);

            await Promise.all([
                fetchRisks(),
                fetchControls(),
                fetchPolicies(),
                fetchObjectives(),
            ]);
        } else {
            api.error({
                message: 'Update Failed',
                description: result.error || 'Failed to apply updates',
            });
        }
    };

    // Fetch linked data when selections change + clear suggestions
    useEffect(() => {
        if (selectedAsset) {
            fetchAssetLinkedRisks(selectedAsset);
        }
        clearSuggestions('asset-risk');
        setSuggestedAvailableAR([]);
    }, [selectedAsset]);

    useEffect(() => {
        if (selectedRiskForControls && selectedFrameworkId) {
            fetchRiskLinkedControls(selectedRiskForControls, selectedFrameworkId);
        }
        clearSuggestions('risk-control');
        setSuggestedAvailableRC([]);
    }, [selectedRiskForControls, selectedFrameworkId]);

    useEffect(() => {
        if (selectedControl && selectedFrameworkId) {
            fetchControlLinkedPolicies(selectedControl, selectedFrameworkId);
        }
        clearSuggestions('control-policy');
        setSuggestedAvailableCP([]);
    }, [selectedControl, selectedFrameworkId]);

    useEffect(() => {
        if (selectedPolicy) {
            fetchPolicyLinkedObjectives(selectedPolicy);
        }
        clearSuggestions('policy-objective');
        setSuggestedAvailablePO([]);
    }, [selectedPolicy]);

    // --- Helper: fetch linked risks for a set of asset IDs ---
    const fetchRiskIdsForAssets = async (assetIds: string[]): Promise<Set<string>> => {
        const riskIdSet = new Set<string>();
        for (const assetId of assetIds) {
            try {
                const response = await fetch(`${cyberbridge_back_end_rest_api}/assets/${assetId}/risks`, {
                    headers: { ...getAuthHeader() },
                });
                if (response.ok) {
                    const linked: { id: string }[] = await response.json();
                    linked.forEach(r => riskIdSet.add(r.id));
                }
            } catch (err) {
                console.error('Error fetching linked risks for asset filter:', err);
            }
        }
        return riskIdSet;
    };

    // --- Helper: fetch linked controls for a set of risk IDs ---
    const fetchControlIdsForRisks = async (riskIds: string[]): Promise<Set<string>> => {
        const controlIdSet = new Set<string>();
        const params = selectedFrameworkId ? `?framework_id=${selectedFrameworkId}` : '';
        for (const riskId of riskIds) {
            try {
                const response = await fetch(`${cyberbridge_back_end_rest_api}/risks/${riskId}/controls${params}`, {
                    headers: { ...getAuthHeader() },
                });
                if (response.ok) {
                    const linked: { id: string }[] = await response.json();
                    linked.forEach(c => controlIdSet.add(c.id));
                }
            } catch (err) {
                console.error('Error fetching linked controls for risk filter:', err);
            }
        }
        return controlIdSet;
    };

    // --- Helper: fetch linked policies for a set of control IDs ---
    const fetchPolicyIdsForControls = async (controlIds: string[]): Promise<Set<string>> => {
        const policyIdSet = new Set<string>();
        const params = selectedFrameworkId ? `?framework_id=${selectedFrameworkId}` : '';
        for (const controlId of controlIds) {
            try {
                const response = await fetch(`${cyberbridge_back_end_rest_api}/controls/${controlId}/policies${params}`, {
                    headers: { ...getAuthHeader() },
                });
                if (response.ok) {
                    const linked: { id: string }[] = await response.json();
                    linked.forEach(p => policyIdSet.add(p.id));
                }
            } catch (err) {
                console.error('Error fetching linked policies for control filter:', err);
            }
        }
        return policyIdSet;
    };

    // ===== Risk→Controls tab: Asset(s) → Select Risk =====
    useEffect(() => {
        if (selectedAssetFilterRC.length === 0) { setAssetFilteredRiskIdsRC(null); return; }
        fetchRiskIdsForAssets(selectedAssetFilterRC).then(setAssetFilteredRiskIdsRC);
    }, [selectedAssetFilterRC]);

    useEffect(() => {
        if (assetFilteredRiskIdsRC !== null && selectedRiskForControls && !assetFilteredRiskIdsRC.has(selectedRiskForControls)) {
            setSelectedRiskForControls(undefined);
        }
    }, [assetFilteredRiskIdsRC]);

    const filteredRisksForControlTab = useMemo(() => {
        if (assetFilteredRiskIdsRC === null) return risks;
        return risks.filter(r => assetFilteredRiskIdsRC.has(r.id));
    }, [risks, assetFilteredRiskIdsRC]);

    // ===== Controls→Policies tab: Asset(s) → Risk(s) → Select Control =====
    useEffect(() => {
        if (selectedAssetFilterCP.length === 0) { setAssetFilteredRiskIdsCP(null); return; }
        fetchRiskIdsForAssets(selectedAssetFilterCP).then(setAssetFilteredRiskIdsCP);
    }, [selectedAssetFilterCP]);

    // Reset risk filter when asset filter narrows available risks
    useEffect(() => {
        if (assetFilteredRiskIdsCP !== null) {
            setSelectedRiskFilterCP(prev => prev.filter(id => assetFilteredRiskIdsCP.has(id)));
        }
    }, [assetFilteredRiskIdsCP]);

    const filteredRisksForPolicyTab = useMemo(() => {
        if (assetFilteredRiskIdsCP === null) return risks;
        return risks.filter(r => assetFilteredRiskIdsCP.has(r.id));
    }, [risks, assetFilteredRiskIdsCP]);

    useEffect(() => {
        if (selectedRiskFilterCP.length === 0) { setRiskFilteredControlIdsCP(null); return; }
        fetchControlIdsForRisks(selectedRiskFilterCP).then(setRiskFilteredControlIdsCP);
    }, [selectedRiskFilterCP, selectedFrameworkId]);

    useEffect(() => {
        if (riskFilteredControlIdsCP !== null && selectedControl && !riskFilteredControlIdsCP.has(selectedControl)) {
            setSelectedControl(undefined);
        }
    }, [riskFilteredControlIdsCP]);

    const filteredControlsForPolicyTab = useMemo(() => {
        if (riskFilteredControlIdsCP === null) return controls;
        return controls.filter(c => riskFilteredControlIdsCP.has(c.id));
    }, [controls, riskFilteredControlIdsCP]);

    // ===== Policies→Objectives tab: Asset(s) → Risk(s) → Control(s) → Select Policy =====
    useEffect(() => {
        if (selectedAssetFilterPO.length === 0) { setAssetFilteredRiskIdsPO(null); return; }
        fetchRiskIdsForAssets(selectedAssetFilterPO).then(setAssetFilteredRiskIdsPO);
    }, [selectedAssetFilterPO]);

    // Reset risk filter when asset filter narrows available risks
    useEffect(() => {
        if (assetFilteredRiskIdsPO !== null) {
            setSelectedRiskFilterPO(prev => prev.filter(id => assetFilteredRiskIdsPO.has(id)));
        }
    }, [assetFilteredRiskIdsPO]);

    const filteredRisksForObjectiveTab = useMemo(() => {
        if (assetFilteredRiskIdsPO === null) return risks;
        return risks.filter(r => assetFilteredRiskIdsPO.has(r.id));
    }, [risks, assetFilteredRiskIdsPO]);

    useEffect(() => {
        if (selectedRiskFilterPO.length === 0) { setRiskFilteredControlIdsPO(null); return; }
        fetchControlIdsForRisks(selectedRiskFilterPO).then(setRiskFilteredControlIdsPO);
    }, [selectedRiskFilterPO, selectedFrameworkId]);

    // Reset control filter when risk filter narrows available controls
    useEffect(() => {
        if (riskFilteredControlIdsPO !== null) {
            setSelectedControlFilterPO(prev => prev.filter(id => riskFilteredControlIdsPO.has(id)));
        }
    }, [riskFilteredControlIdsPO]);

    const filteredControlsForObjectiveTab = useMemo(() => {
        if (riskFilteredControlIdsPO === null) return controls;
        return controls.filter(c => riskFilteredControlIdsPO.has(c.id));
    }, [controls, riskFilteredControlIdsPO]);

    useEffect(() => {
        if (selectedControlFilterPO.length === 0) { setControlFilteredPolicyIdsPO(null); return; }
        fetchPolicyIdsForControls(selectedControlFilterPO).then(setControlFilteredPolicyIdsPO);
    }, [selectedControlFilterPO, selectedFrameworkId]);

    useEffect(() => {
        if (controlFilteredPolicyIdsPO !== null && selectedPolicy && !controlFilteredPolicyIdsPO.has(selectedPolicy)) {
            setSelectedPolicy(undefined);
        }
    }, [controlFilteredPolicyIdsPO]);

    const filteredPoliciesForObjectiveTab = useMemo(() => {
        if (controlFilteredPolicyIdsPO === null) return policies;
        return policies.filter(p => controlFilteredPolicyIdsPO.has(p.id));
    }, [policies, controlFilteredPolicyIdsPO]);

    // Link/Unlink handlers for Asset-Risk (handles array of IDs)
    const handleLinkAssetRisks = async (riskIds: string[]) => {
        if (!selectedAsset) return;
        for (const riskId of riskIds) {
            const result = await linkAssetToRisk(selectedAsset, riskId);
            if (!result.success) {
                api.error({ message: 'Link failed', description: result.error || 'Failed to link asset to risk' });
                return;
            }
        }
        api.success({ message: 'Links created', description: `Asset linked to ${riskIds.length} risk(s) successfully` });
        fetchAssetLinkedRisks(selectedAsset);
    };

    const handleUnlinkAssetRisks = async (riskIds: string[]) => {
        if (!selectedAsset) return;
        for (const riskId of riskIds) {
            const result = await unlinkAssetFromRisk(selectedAsset, riskId);
            if (!result.success) {
                api.error({ message: 'Unlink failed', description: result.error || 'Failed to unlink asset from risk' });
                return;
            }
        }
        api.success({ message: 'Links removed', description: `Asset unlinked from ${riskIds.length} risk(s) successfully` });
        fetchAssetLinkedRisks(selectedAsset);
    };

    // Link/Unlink handlers for Risk-Control (handles array of IDs)
    const handleLinkRiskControls = async (controlIds: string[]) => {
        if (!selectedRiskForControls || !selectedFrameworkId) return;
        for (const controlId of controlIds) {
            const success = await linkControlToRisk(controlId, selectedRiskForControls, selectedFrameworkId);
            if (!success) {
                api.error({ message: 'Link failed', description: 'Failed to link control to risk' });
                return;
            }
        }
        api.success({ message: 'Links created', description: `Risk linked to ${controlIds.length} control(s) successfully` });
        fetchRiskLinkedControls(selectedRiskForControls, selectedFrameworkId);
    };

    const handleUnlinkRiskControls = async (controlIds: string[]) => {
        if (!selectedRiskForControls || !selectedFrameworkId) return;
        for (const controlId of controlIds) {
            const success = await unlinkControlFromRisk(controlId, selectedRiskForControls, selectedFrameworkId);
            if (!success) {
                api.error({ message: 'Unlink failed', description: 'Failed to unlink control from risk' });
                return;
            }
        }
        api.success({ message: 'Links removed', description: `Risk unlinked from ${controlIds.length} control(s) successfully` });
        fetchRiskLinkedControls(selectedRiskForControls, selectedFrameworkId);
    };

    // Link/Unlink handlers for Control-Policy (handles array of IDs)
    const handleLinkControlPolicies = async (policyIds: string[]) => {
        if (!selectedControl || !selectedFrameworkId) return;
        for (const policyId of policyIds) {
            const success = await linkControlToPolicy(selectedControl, policyId, selectedFrameworkId);
            if (!success) {
                api.error({ message: 'Link failed', description: 'Failed to link control to policy' });
                return;
            }
        }
        api.success({ message: 'Links created', description: `Control linked to ${policyIds.length} policy(ies) successfully` });
        fetchControlLinkedPolicies(selectedControl, selectedFrameworkId);
    };

    const handleUnlinkControlPolicies = async (policyIds: string[]) => {
        if (!selectedControl || !selectedFrameworkId) return;
        for (const policyId of policyIds) {
            const success = await unlinkControlFromPolicy(selectedControl, policyId, selectedFrameworkId);
            if (!success) {
                api.error({ message: 'Unlink failed', description: 'Failed to unlink control from policy' });
                return;
            }
        }
        api.success({ message: 'Links removed', description: `Control unlinked from ${policyIds.length} policy(ies) successfully` });
        fetchControlLinkedPolicies(selectedControl, selectedFrameworkId);
    };

    // Link/Unlink handlers for Policy-Objective (handles array of IDs)
    const handleLinkPolicyObjectives = async (objectiveIds: string[]) => {
        if (!selectedPolicy) return;
        let nextOrder = policyLinkedObjectives.length + 1;
        for (const objectiveId of objectiveIds) {
            const success = await addObjectiveToPolicy(selectedPolicy, objectiveId, nextOrder);
            if (!success) {
                api.error({ message: 'Link failed', description: 'Failed to link objective to policy' });
                return;
            }
            nextOrder += 1;
        }
        api.success({ message: 'Links created', description: `Policy linked to ${objectiveIds.length} objective(s) successfully` });
        fetchPolicyLinkedObjectives(selectedPolicy);
    };

    const handleUnlinkPolicyObjectives = async (objectiveIds: string[]) => {
        if (!selectedPolicy) return;
        for (const objectiveId of objectiveIds) {
            const success = await removeObjectiveFromPolicy(selectedPolicy, objectiveId);
            if (!success) {
                api.error({ message: 'Unlink failed', description: 'Failed to unlink objective from policy' });
                return;
            }
        }
        api.success({ message: 'Links removed', description: `Policy unlinked from ${objectiveIds.length} objective(s) successfully` });
        fetchPolicyLinkedObjectives(selectedPolicy);
    };

    // Filter objectives by selected framework (via chapter → framework chain)
    const frameworkFilteredObjectives = useMemo(() => {
        if (!selectedFrameworkId) return [];
        return objectives.filter(o => {
            const fwId = chapterFrameworkMap[String(o.chapter_id)];
            return fwId === selectedFrameworkId;
        });
    }, [objectives, selectedFrameworkId, chapterFrameworkMap]);

    // Filter linked objectives by selected framework
    const frameworkFilteredLinkedObjectives = useMemo(() => {
        if (!selectedFrameworkId) return policyLinkedObjectives;
        return policyLinkedObjectives.filter(lo => {
            // Look up the full objective to get chapter_id
            const obj = objectives.find(o => o.id === lo.id);
            if (!obj) return false;
            const fwId = chapterFrameworkMap[String(obj.chapter_id)];
            return fwId === selectedFrameworkId;
        });
    }, [policyLinkedObjectives, selectedFrameworkId, objectives, chapterFrameworkMap]);

    // Render summary statistics (framework-scoped when a framework is selected)
    const renderChainSummary = () => {
        if (!selectedFrameworkId) {
            return (
                <Card style={{ marginBottom: 24 }}>
                    <Empty description="Select a framework to view chain link statistics" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                </Card>
            );
        }

        const riskCount = entityCounts?.risks ?? 0;
        const controlCount = entityCounts?.controls ?? 0;
        const policyCount = entityCounts?.policies ?? 0;
        const objectiveCount = entityCounts?.objectives ?? 0;

        return (
            <Card style={{ marginBottom: 24 }}>
                <div style={{ textAlign: 'center', marginBottom: 12, color: '#8c8c8c', fontSize: 13 }}>
                    Unique entities linked to this framework
                </div>
                <Row gutter={16} align="middle" justify="center">
                    <Col>
                        <Statistic
                            title={<span><DatabaseOutlined style={{ marginRight: 4 }} />Assets</span>}
                            value={assets.length}
                            valueStyle={{ color: '#1890ff' }}
                        />
                    </Col>
                    <Col>
                        <ArrowRightOutlined style={{ fontSize: 20, color: '#d9d9d9' }} />
                    </Col>
                    <Col>
                        <Statistic
                            title={<span><WarningOutlined style={{ marginRight: 4 }} />Risks</span>}
                            value={riskCount}
                            valueStyle={{ color: '#faad14' }}
                        />
                    </Col>
                    <Col>
                        <ArrowRightOutlined style={{ fontSize: 20, color: '#d9d9d9' }} />
                    </Col>
                    <Col>
                        <Statistic
                            title={<span><SafetyCertificateOutlined style={{ marginRight: 4 }} />Controls</span>}
                            value={controlCount}
                            valueStyle={{ color: '#52c41a' }}
                        />
                    </Col>
                    <Col>
                        <ArrowRightOutlined style={{ fontSize: 20, color: '#d9d9d9' }} />
                    </Col>
                    <Col>
                        <Statistic
                            title={<span><FileProtectOutlined style={{ marginRight: 4 }} />Policies</span>}
                            value={policyCount}
                            valueStyle={{ color: '#722ed1' }}
                        />
                    </Col>
                    <Col>
                        <ArrowRightOutlined style={{ fontSize: 20, color: '#d9d9d9' }} />
                    </Col>
                    <Col>
                        <Statistic
                            title={<span><AimOutlined style={{ marginRight: 4 }} />Objectives</span>}
                            value={objectiveCount}
                            valueStyle={{ color: '#eb2f96' }}
                        />
                    </Col>
                </Row>
            </Card>
        );
    };

    const tabItems = [
        {
            key: 'asset-risk',
            label: (
                <span>
                    <DatabaseOutlined style={{ marginRight: 4 }} />
                    Assets
                    <ArrowRightOutlined style={{ margin: '0 8px', fontSize: 12 }} />
                    <WarningOutlined style={{ marginRight: 4 }} />
                    Risks
                </span>
            ),
            children: (
                <div className="page-section">
                    <div style={{ marginBottom: 24 }}>
                        <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                            Select Asset
                        </label>
                        <Select
                            showSearch
                            placeholder="Select an asset to manage its risk connections..."
                            options={assets.map(asset => ({
                                label: `${asset.name}${asset.asset_type_name ? ` (${asset.asset_type_name})` : ''}`,
                                value: asset.id,
                            }))}
                            value={selectedAsset}
                            onChange={(value) => setSelectedAsset(value)}
                            filterOption={(input, option) =>
                                (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                            }
                            style={{ width: '100%', maxWidth: 500 }}
                            allowClear
                        />
                    </div>

                    {selectedAsset ? (
                        <ConnectionBoard
                            title="Asset → Risk Connections"
                            sourceLabel="Asset"
                            targetLabel="Risk"
                            relationshipLabel="exposed to"
                            headerContent={
                                <SuggestionPanel
                                    tab="asset-risk"
                                    entityId={selectedAsset}
                                    availableItemIds={risks.map(r => r.id)}
                                    onSelectItems={handleSuggestionSelectAR}
                                />
                            }
                            availableItems={risks.map(risk => ({
                                id: risk.id,
                                risk_code: risk.risk_code,
                                risk_category_name: risk.risk_category_name,
                                risk_category_description: risk.risk_category_description,
                                risk_severity: risk.risk_severity,
                                risk_status: risk.risk_status,
                            }))}
                            linkedItems={assetLinkedRisks.map(risk => ({
                                id: risk.id,
                                risk_code: risk.risk_code,
                                risk_category_name: risk.risk_category_name,
                                risk_category_description: risk.risk_category_description,
                                risk_severity: risk.risk_severity,
                                risk_status: risk.risk_status,
                            }))}
                            loading={loading}
                            getItemDisplayName={(item) => {
                                const risk = item as { risk_code?: string | null; risk_category_name?: string };
                                return risk.risk_code
                                    ? `${risk.risk_code}: ${risk.risk_category_name || 'Unknown'}`
                                    : risk.risk_category_name || 'Unknown Risk';
                            }}
                            getItemDescription={(item) => {
                                const risk = item as { risk_category_description?: string };
                                return risk.risk_category_description || null;
                            }}
                            getItemTags={(item) => {
                                const risk = item as { risk_severity?: string | null; risk_status?: string | null };
                                const tags: { label: string; color: string }[] = [];
                                if (risk.risk_severity) {
                                    const severityColors: Record<string, string> = {
                                        'Severe': 'red', 'High': 'orange', 'Medium': 'gold', 'Low': 'green',
                                    };
                                    tags.push({ label: risk.risk_severity, color: severityColors[risk.risk_severity] || 'default' });
                                }
                                if (risk.risk_status) {
                                    tags.push({ label: risk.risk_status, color: 'blue' });
                                }
                                return tags;
                            }}
                            onLink={handleLinkAssetRisks}
                            onUnlink={handleUnlinkAssetRisks}
                            externalSelectedAvailable={suggestedAvailableAR}
                            onExternalSelectAvailable={setSuggestedAvailableAR}
                        />
                    ) : (
                        <Empty description="Select an asset to manage its risk connections" />
                    )}
                </div>
            ),
        },
        {
            key: 'risk-control',
            label: (
                <span>
                    <WarningOutlined style={{ marginRight: 4 }} />
                    Risks
                    <ArrowRightOutlined style={{ margin: '0 8px', fontSize: 12 }} />
                    <SafetyCertificateOutlined style={{ marginRight: 4 }} />
                    Controls
                </span>
            ),
            children: (
                <div className="page-section">
                    <div style={{ marginBottom: 24, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                        <div style={{ flex: '1 1 240px', maxWidth: 350 }}>
                            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                                Filter by Asset(s)
                            </label>
                            <Select
                                mode="multiple"
                                showSearch
                                placeholder="Filter risks by linked assets..."
                                options={assets.map(asset => ({
                                    label: `${asset.name}${asset.asset_type_name ? ` (${asset.asset_type_name})` : ''}`,
                                    value: asset.id,
                                }))}
                                value={selectedAssetFilterRC}
                                onChange={(values) => setSelectedAssetFilterRC(values)}
                                filterOption={(input, option) =>
                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                }
                                style={{ width: '100%' }}
                                allowClear
                                maxTagCount="responsive"
                            />
                        </div>
                        <div style={{ flex: '1 1 300px', maxWidth: 500 }}>
                            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                                Select Risk
                            </label>
                            <Select
                                showSearch
                                placeholder="Select a risk to manage its control connections..."
                                options={filteredRisksForControlTab.map(risk => ({
                                    label: risk.risk_code
                                        ? `${risk.risk_code}: ${risk.risk_category_name}`
                                        : risk.risk_category_name,
                                    value: risk.id,
                                }))}
                                value={selectedRiskForControls}
                                onChange={(value) => setSelectedRiskForControls(value)}
                                filterOption={(input, option) =>
                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                }
                                style={{ width: '100%' }}
                                allowClear
                            />
                        </div>
                    </div>

                    {selectedRiskForControls && selectedFrameworkId ? (
                        <ConnectionBoard
                            title="Risk → Control Connections"
                            sourceLabel="Risk"
                            targetLabel="Control"
                            relationshipLabel="mitigated by"
                            headerContent={
                                <SuggestionPanel
                                    tab="risk-control"
                                    entityId={selectedRiskForControls}
                                    frameworkId={selectedFrameworkId}
                                    availableItemIds={controls.map(c => c.id)}
                                    onSelectItems={handleSuggestionSelectRC}
                                />
                            }
                            availableItems={controls.map(control => ({
                                id: control.id,
                                code: control.code,
                                name: control.name,
                                description: control.description,
                                control_status_name: control.control_status_name,
                            }))}
                            linkedItems={riskLinkedControls.map(control => ({
                                id: control.id,
                                code: control.code,
                                name: control.name,
                                description: control.description,
                                control_status_name: control.control_status_name,
                            }))}
                            loading={loading}
                            getItemDisplayName={(item) => {
                                const control = item as { code?: string; name?: string };
                                return control.code ? `${control.code}: ${control.name}` : control.name || 'Unknown Control';
                            }}
                            getItemDescription={(item) => {
                                const control = item as { description?: string };
                                return control.description || null;
                            }}
                            getItemTags={(item) => {
                                const control = item as { control_status_name?: string };
                                const tags: { label: string; color: string }[] = [];
                                if (control.control_status_name) {
                                    tags.push({ label: control.control_status_name, color: 'green' });
                                }
                                return tags;
                            }}
                            onLink={handleLinkRiskControls}
                            onUnlink={handleUnlinkRiskControls}
                            externalSelectedAvailable={suggestedAvailableRC}
                            onExternalSelectAvailable={setSuggestedAvailableRC}
                        />
                    ) : (
                        <Empty description={!selectedFrameworkId ? "Select a framework above to manage connections" : "Select a risk to manage its control connections"} />
                    )}
                </div>
            ),
        },
        {
            key: 'control-policy',
            label: (
                <span>
                    <SafetyCertificateOutlined style={{ marginRight: 4 }} />
                    Controls
                    <ArrowRightOutlined style={{ margin: '0 8px', fontSize: 12 }} />
                    <FileProtectOutlined style={{ marginRight: 4 }} />
                    Policies
                </span>
            ),
            children: (
                <div className="page-section">
                    <div style={{ marginBottom: 24, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                        <div style={{ flex: '1 1 200px', maxWidth: 280 }}>
                            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                                Filter by Asset(s)
                            </label>
                            <Select
                                mode="multiple"
                                showSearch
                                placeholder="Filter by assets..."
                                options={assets.map(asset => ({
                                    label: `${asset.name}${asset.asset_type_name ? ` (${asset.asset_type_name})` : ''}`,
                                    value: asset.id,
                                }))}
                                value={selectedAssetFilterCP}
                                onChange={(values) => setSelectedAssetFilterCP(values)}
                                filterOption={(input, option) =>
                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                }
                                style={{ width: '100%' }}
                                allowClear
                                maxTagCount="responsive"
                            />
                        </div>
                        <div style={{ flex: '1 1 200px', maxWidth: 280 }}>
                            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                                Filter by Risk(s)
                            </label>
                            <Select
                                mode="multiple"
                                showSearch
                                placeholder="Filter by risks..."
                                options={filteredRisksForPolicyTab.map(risk => ({
                                    label: risk.risk_code
                                        ? `${risk.risk_code}: ${risk.risk_category_name}`
                                        : risk.risk_category_name,
                                    value: risk.id,
                                }))}
                                value={selectedRiskFilterCP}
                                onChange={(values) => setSelectedRiskFilterCP(values)}
                                filterOption={(input, option) =>
                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                }
                                style={{ width: '100%' }}
                                allowClear
                                maxTagCount="responsive"
                            />
                        </div>
                        <div style={{ flex: '1 1 280px', maxWidth: 400 }}>
                            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                                Select Control
                            </label>
                            <Select
                                showSearch
                                placeholder="Select a control to manage its policy connections..."
                                options={filteredControlsForPolicyTab.map(control => ({
                                    label: control.code ? `${control.code}: ${control.name}` : control.name,
                                    value: control.id,
                                }))}
                                value={selectedControl}
                                onChange={(value) => setSelectedControl(value)}
                                filterOption={(input, option) =>
                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                }
                                style={{ width: '100%' }}
                                allowClear
                            />
                        </div>
                    </div>

                    {selectedControl && selectedFrameworkId ? (
                        <ConnectionBoard
                            title="Control → Policy Connections"
                            sourceLabel="Control"
                            targetLabel="Policy"
                            relationshipLabel="governed by"
                            headerContent={
                                <SuggestionPanel
                                    tab="control-policy"
                                    entityId={selectedControl}
                                    frameworkId={selectedFrameworkId}
                                    availableItemIds={policies.map(p => p.id)}
                                    onSelectItems={handleSuggestionSelectCP}
                                />
                            }
                            availableItems={policies.map(policy => ({
                                id: policy.id,
                                title: policy.title,
                                policy_code: policy.policy_code,
                                body: policy.body,
                                status: policy.status,
                            }))}
                            linkedItems={controlLinkedPolicies.map(policy => ({
                                id: policy.id,
                                title: policy.title,
                                policy_code: policy.policy_code,
                                body: policy.body,
                                status: policy.status,
                            }))}
                            loading={loading}
                            getItemDisplayName={(item) => {
                                const policy = item as { title?: string; policy_code?: string | null };
                                return policy.policy_code ? `${policy.policy_code}: ${policy.title}` : (policy.title || 'Unknown Policy');
                            }}
                            getItemDescription={(item) => {
                                const policy = item as { body?: string | null };
                                return policy.body || null;
                            }}
                            getItemTags={(item) => {
                                const policy = item as { status?: string | null };
                                const tags: { label: string; color: string }[] = [];
                                if (policy.status) {
                                    const statusColors: Record<string, string> = {
                                        'Active': 'green', 'Draft': 'orange', 'Archived': 'default', 'Under Review': 'blue',
                                    };
                                    tags.push({ label: policy.status, color: statusColors[policy.status] || 'default' });
                                }
                                return tags;
                            }}
                            onLink={handleLinkControlPolicies}
                            onUnlink={handleUnlinkControlPolicies}
                            externalSelectedAvailable={suggestedAvailableCP}
                            onExternalSelectAvailable={setSuggestedAvailableCP}
                        />
                    ) : (
                        <Empty description={!selectedFrameworkId ? "Select a framework above to manage connections" : "Select a control to manage its policy connections"} />
                    )}
                </div>
            ),
        },
        {
            key: 'policy-objective',
            label: (
                <span>
                    <FileProtectOutlined style={{ marginRight: 4 }} />
                    Policies
                    <ArrowRightOutlined style={{ margin: '0 8px', fontSize: 12 }} />
                    <AimOutlined style={{ marginRight: 4 }} />
                    Objectives
                </span>
            ),
            children: (
                <div className="page-section">
                    <div style={{ marginBottom: 24, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                        <div style={{ flex: '1 1 180px', maxWidth: 240 }}>
                            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                                Filter by Asset(s)
                            </label>
                            <Select
                                mode="multiple"
                                showSearch
                                placeholder="Filter by assets..."
                                options={assets.map(asset => ({
                                    label: `${asset.name}${asset.asset_type_name ? ` (${asset.asset_type_name})` : ''}`,
                                    value: asset.id,
                                }))}
                                value={selectedAssetFilterPO}
                                onChange={(values) => setSelectedAssetFilterPO(values)}
                                filterOption={(input, option) =>
                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                }
                                style={{ width: '100%' }}
                                allowClear
                                maxTagCount="responsive"
                            />
                        </div>
                        <div style={{ flex: '1 1 180px', maxWidth: 240 }}>
                            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                                Filter by Risk(s)
                            </label>
                            <Select
                                mode="multiple"
                                showSearch
                                placeholder="Filter by risks..."
                                options={filteredRisksForObjectiveTab.map(risk => ({
                                    label: risk.risk_code
                                        ? `${risk.risk_code}: ${risk.risk_category_name}`
                                        : risk.risk_category_name,
                                    value: risk.id,
                                }))}
                                value={selectedRiskFilterPO}
                                onChange={(values) => setSelectedRiskFilterPO(values)}
                                filterOption={(input, option) =>
                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                }
                                style={{ width: '100%' }}
                                allowClear
                                maxTagCount="responsive"
                            />
                        </div>
                        <div style={{ flex: '1 1 180px', maxWidth: 240 }}>
                            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                                Filter by Control(s)
                            </label>
                            <Select
                                mode="multiple"
                                showSearch
                                placeholder="Filter by controls..."
                                options={filteredControlsForObjectiveTab.map(control => ({
                                    label: control.code ? `${control.code}: ${control.name}` : control.name,
                                    value: control.id,
                                }))}
                                value={selectedControlFilterPO}
                                onChange={(values) => setSelectedControlFilterPO(values)}
                                filterOption={(input, option) =>
                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                }
                                style={{ width: '100%' }}
                                allowClear
                                maxTagCount="responsive"
                            />
                        </div>
                        <div style={{ flex: '1 1 250px', maxWidth: 350 }}>
                            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                                Select Policy
                            </label>
                            <Select
                                showSearch
                                placeholder="Select a policy to manage its objective connections..."
                                options={filteredPoliciesForObjectiveTab.map(policy => ({
                                    label: policy.policy_code ? `${policy.policy_code}: ${policy.title}` : policy.title,
                                    value: policy.id,
                                }))}
                                value={selectedPolicy}
                                onChange={(value) => setSelectedPolicy(value)}
                                filterOption={(input, option) =>
                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                }
                                style={{ width: '100%' }}
                                allowClear
                            />
                        </div>
                    </div>

                    {selectedPolicy && selectedFrameworkId ? (
                        <ConnectionBoard
                            title="Policy → Objective Connections"
                            sourceLabel="Policy"
                            targetLabel="Objective"
                            relationshipLabel="addresses"
                            headerContent={
                                <SuggestionPanel
                                    tab="policy-objective"
                                    entityId={selectedPolicy}
                                    frameworkId={selectedFrameworkId}
                                    availableItemIds={frameworkFilteredObjectives.map(o => o.id)}
                                    onSelectItems={handleSuggestionSelectPO}
                                />
                            }
                            availableItems={frameworkFilteredObjectives.map(objective => ({
                                id: objective.id,
                                title: objective.title,
                                requirement_description: objective.requirement_description,
                                chapter_name: objective.chapter_name,
                            }))}
                            linkedItems={frameworkFilteredLinkedObjectives.map(objective => ({
                                id: objective.id,
                                title: objective.title,
                                subchapter: objective.subchapter,
                                chapter_title: objective.chapter_title,
                            }))}
                            loading={loading}
                            getItemDisplayName={(item) => {
                                const objective = item as { title?: string };
                                return objective.title || 'Unknown Objective';
                            }}
                            getItemDescription={(item) => {
                                const objective = item as { requirement_description?: string | null; subchapter?: string | null };
                                return objective.requirement_description || objective.subchapter || null;
                            }}
                            getItemTags={(item) => {
                                const objective = item as { chapter_name?: string; chapter_title?: string | null };
                                const tags: { label: string; color: string }[] = [];
                                const chapter = objective.chapter_name || objective.chapter_title;
                                if (chapter) {
                                    tags.push({ label: chapter, color: 'purple' });
                                }
                                return tags;
                            }}
                            onLink={handleLinkPolicyObjectives}
                            onUnlink={handleUnlinkPolicyObjectives}
                            externalSelectedAvailable={suggestedAvailablePO}
                            onExternalSelectAvailable={setSuggestedAvailablePO}
                        />
                    ) : (
                        <Empty description={!selectedFrameworkId ? "Select a framework above to manage connections" : "Select a policy to view its objective connections"} />
                    )}
                </div>
            ),
        },
    ];

    return (
        <div>
            {contextHolder}
            {modalContextHolder}
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
                                icon={<LinkOutlined />}
                                title="Compliance Chain - All Links"
                                infoContent={ComplianceChainLinksInfo}
                            />
                        </div>
                    </div>

                    {/* Chain Summary */}
                    {renderChainSummary()}

                    {/* Framework Selector - always shown */}
                    <Card style={{ marginBottom: 16 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                            <label style={{ fontWeight: 500, whiteSpace: 'nowrap' }}>
                                Framework:
                            </label>
                            <Select
                                showSearch
                                placeholder="Select a framework to scope connections..."
                                options={filteredFrameworks.map(fw => ({
                                    label: fw.name,
                                    value: fw.id,
                                }))}
                                value={selectedFrameworkId}
                                onChange={(value) => setSelectedFrameworkId(value)}
                                filterOption={(input, option) =>
                                    (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                }
                                style={{ width: '100%', maxWidth: 400 }}
                                allowClear
                            />
                            <Tooltip
                                title={
                                    !selectedFrameworkId
                                        ? 'Select a framework first'
                                        : chainLinksStatus && !chainLinksStatus.has_mapping
                                            ? 'No chain links mapping available for this framework'
                                            : chainLinksStatus && chainLinksStatus.already_imported
                                                ? 'Chain links already imported for this framework'
                                                : ''
                                }
                            >
                                <Button
                                    icon={<ImportOutlined />}
                                    onClick={handleImportChainLinks}
                                    loading={importLoading}
                                    disabled={
                                        !selectedFrameworkId ||
                                        !chainLinksStatus?.has_mapping ||
                                        chainLinksStatus?.already_imported
                                    }
                                >
                                    Import Chain Links
                                </Button>
                            </Tooltip>
                            {selectedFrameworkId && chainLinksStatus?.has_mapping && chainLinksStatus?.already_imported && (
                                <Button
                                    icon={<SyncOutlined />}
                                    onClick={handleCheckForUpdates}
                                    loading={updateCheckLoading}
                                >
                                    Check for Updates
                                </Button>
                            )}
                            {!selectedFrameworkId && activeTab !== 'asset-risk' && (
                                <Alert
                                    message="Select a framework to manage connections"
                                    type="info"
                                    showIcon
                                    style={{ flex: 1 }}
                                />
                            )}
                        </div>
                    </Card>

                    {/* Connection Tabs */}
                    <Card>
                        <Tabs
                            activeKey={activeTab}
                            onChange={setActiveTab}
                            items={tabItems}
                            size="large"
                        />
                    </Card>
                </div>
            </div>

            {/* Check for Updates Modal */}
            <Modal
                title="Chain Links Updates Available"
                open={updateModalVisible}
                onCancel={() => setUpdateModalVisible(false)}
                footer={[
                    <Button key="cancel" onClick={() => setUpdateModalVisible(false)}>
                        Cancel
                    </Button>,
                    <Button key="apply" type="primary" loading={applyUpdateLoading} onClick={handleApplyUpdates}>
                        Apply Updates
                    </Button>,
                ]}
                width={600}
            >
                {updateCheckResult && (
                    <div>
                        <Alert
                            message="This operation is non-destructive. Existing data will not be removed — only new entities, links, and field updates will be applied."
                            type="info"
                            showIcon
                            style={{ marginBottom: 16 }}
                        />

                        {(updateCheckResult.new_risks > 0 || updateCheckResult.new_controls > 0 || updateCheckResult.new_policies > 0) && (
                            <div style={{ marginBottom: 12 }}>
                                <strong>New entities to create:</strong>
                                <ul style={{ marginTop: 4, marginBottom: 0 }}>
                                    {updateCheckResult.new_risks > 0 && <li>{updateCheckResult.new_risks} risk(s)</li>}
                                    {updateCheckResult.new_controls > 0 && <li>{updateCheckResult.new_controls} control(s)</li>}
                                    {updateCheckResult.new_policies > 0 && <li>{updateCheckResult.new_policies} policy/policies</li>}
                                </ul>
                            </div>
                        )}

                        {updateCheckResult.new_links && Object.values(updateCheckResult.new_links as Record<string, number>).some((v: unknown) => (v as number) > 0) && (
                            <div style={{ marginBottom: 12 }}>
                                <strong>New links to add:</strong>
                                <ul style={{ marginTop: 4, marginBottom: 0 }}>
                                    {Object.entries(updateCheckResult.new_links as Record<string, number>)
                                        .filter(([, v]) => v > 0)
                                        .map(([k, v]) => (
                                            <li key={k}>{v} {k.replace(/_/g, '-')} link(s)</li>
                                        ))}
                                </ul>
                            </div>
                        )}

                        {updateCheckResult.objective_field_changes?.length > 0 && (
                            <div style={{ marginBottom: 12 }}>
                                <strong>Objective field updates ({updateCheckResult.objective_field_changes.length}):</strong>
                                <div style={{ maxHeight: 200, overflow: 'auto', marginTop: 4, border: '1px solid #f0f0f0', borderRadius: 4, padding: 8 }}>
                                    {updateCheckResult.objective_field_changes.map((change: any, idx: number) => (
                                        <div key={idx} style={{ marginBottom: idx < updateCheckResult.objective_field_changes.length - 1 ? 8 : 0 }}>
                                            <div style={{ fontWeight: 500 }}>{change.objective_title}</div>
                                            <div style={{ fontSize: 12, color: '#888' }}>
                                                Fields: {Object.keys(change.changes).join(', ')}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </Modal>
        </div>
    );
};

export default ComplianceChainLinksPage;
