// src/pages/CorrelationsPage.tsx
import { useEffect, useState, useMemo } from "react";
import { MenuProps, Select, notification, Card, Table, Input, Space } from 'antd';
import { LoadingOutlined, LinkOutlined } from '@ant-design/icons';
import Sidebar from "../components/Sidebar.tsx";
import { useLocation } from 'wouter';
import useUserStore from "../store/useUserStore.ts";
import useAuthStore from "../store/useAuthStore.ts";
import useCorrelationAIStore from "../store/useCorrelationAIStore.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import { CorrelationsGridColumns, type CorrelationData } from "../constants/CorrelationsGridColumns.tsx";
import { SearchOutlined } from '@ant-design/icons';
import { useMenuHighlighting } from "../utils/menuUtils.ts";

const CorrelationsPage = () => {
    const [location, setLocation] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);
    const { current_user } = useUserStore();
    const { getAuthHeader } = useAuthStore();
    const {
        aiSuggestions,
        loading: aiLoading,
        generateAISuggestions,
        removeSuggestion
    } = useCorrelationAIStore();
    const [api, contextHolder] = notification.useNotification();

    // State for question correlation
    const [frameworks, setFrameworks] = useState<any[]>([]);
    const [assessmentTypes, setAssessmentTypes] = useState<any[]>([]);

    // State for scope selection
    const [scopes, setScopes] = useState<any[]>([]);
    const [availableScopes, setAvailableScopes] = useState<any[]>([]); // Filtered by framework compatibility
    const [assets, setAssets] = useState<any[]>([]);
    const [organisations, setOrganisations] = useState<any[]>([]);
    const [selectedScopeType, setSelectedScopeType] = useState<string>('');
    const [selectedScopeEntityId, setSelectedScopeEntityId] = useState<string>('');
    const [frameworksCompatible, setFrameworksCompatible] = useState<boolean>(true);
    const [compatibilityMessage, setCompatibilityMessage] = useState<string>('');

    const isAssetProductScope = (scopeName: string) => scopeName === 'Product' || scopeName === 'Asset';
    const getScopeLabel = (scopeName: string) => (isAssetProductScope(scopeName) ? 'Asset / Product' : scopeName);
    const formatAssetLabel = (asset: { name: string; version: string | null; asset_type_name?: string | null }) => {
        const versionLabel = asset.version ? ` v${asset.version}` : '';
        const typeLabel = asset.asset_type_name ? ` (${asset.asset_type_name})` : '';
        return `${asset.name}${versionLabel}${typeLabel}`;
    };
    const formatScopeTypeList = (scopeTypes: string[] | string | null | undefined) => {
        if (!scopeTypes) return '';
        return Array.isArray(scopeTypes)
            ? scopeTypes.map(getScopeLabel).join(', ')
            : getScopeLabel(scopeTypes);
    };

    // Left side (Framework A)
    const [selectedFrameworkA, setSelectedFrameworkA] = useState<string>('');
    const [selectedAssessmentTypeA, setSelectedAssessmentTypeA] = useState<string>('');
    const [questionsA, setQuestionsA] = useState<any[]>([]);
    const [selectedQuestionA, setSelectedQuestionA] = useState<string>('');

    // Right side (Framework B)
    const [selectedFrameworkB, setSelectedFrameworkB] = useState<string>('');
    const [selectedAssessmentTypeB, setSelectedAssessmentTypeB] = useState<string>('');
    const [questionsB, setQuestionsB] = useState<any[]>([]);
    const [selectedQuestionB, setSelectedQuestionB] = useState<string>('');

    // Loading states
    const [isLoadingQuestionsA, setIsLoadingQuestionsA] = useState<boolean>(false);
    const [isLoadingQuestionsB, setIsLoadingQuestionsB] = useState<boolean>(false);
    const [isCorrelating, setIsCorrelating] = useState<boolean>(false);
    const [isAlreadyCorrelated, setIsAlreadyCorrelated] = useState<boolean>(false);
    const [isCheckingCorrelation, setIsCheckingCorrelation] = useState<boolean>(false);
    const [existingCorrelationId, setExistingCorrelationId] = useState<string | null>(null);
    const [isDecorrelating, setIsDecorrelating] = useState<boolean>(false);
    const [questionAAlreadyCorrelated, setQuestionAAlreadyCorrelated] = useState<string | null>(null);
    const [questionBAlreadyCorrelated, setQuestionBAlreadyCorrelated] = useState<string | null>(null);

    // State for All Correlations section
    const [allCorrelations, setAllCorrelations] = useState<CorrelationData[]>([]);
    const [isLoadingCorrelations, setIsLoadingCorrelations] = useState<boolean>(false);
    const [searchText, setSearchText] = useState<string>('');
    const [isRemovingAll, setIsRemovingAll] = useState<boolean>(false);

    // State for applying individual suggestions
    const [applyingCorrelationId, setApplyingCorrelationId] = useState<string | null>(null);

    // State for LLM Optimization Settings
    const [maxQuestionsPerFramework, setMaxQuestionsPerFramework] = useState<number>(10);
    const [llmTimeoutSeconds, setLlmTimeoutSeconds] = useState<number>(300);
    const [minConfidenceThreshold, setMinConfidenceThreshold] = useState<number>(75);
    const [maxCorrelations, setMaxCorrelations] = useState<number>(10);
    const [isSavingOptimizations, setIsSavingOptimizations] = useState<boolean>(false);

    // State for Correlation Audit
    const [isAuditing, setIsAuditing] = useState<boolean>(false);
    const [auditResults, setAuditResults] = useState<any>(null);
    const [isFixing, setIsFixing] = useState<boolean>(false);

    useEffect(() => {
        // Redirect users who are not administrators
        if (current_user && !['super_admin', 'org_admin'].includes(current_user.role_name)) {
            setLocation('/home');
        }

        if (current_user && ['super_admin', 'org_admin'].includes(current_user.role_name)) {
            fetchFrameworks();
            fetchAssessmentTypes();
            fetchAllCorrelations();
            fetchScopes();
            fetchAssets();
            fetchOrganisations();
            // Only super_admin can access LLM optimization settings
            if (current_user.role_name === 'super_admin') {
                fetchLLMOptimizationSettings();
            }
        }
    }, [current_user, setLocation]);

    // Add beforeunload warning when AI generation is in progress
    useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (aiLoading) {
                e.preventDefault();
                e.returnValue = ''; // Chrome requires returnValue to be set
                return '';
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);

        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
        };
    }, [aiLoading]);

    // Check for existing correlation whenever both questions are selected OR scope changes
    useEffect(() => {
        if (selectedQuestionA && selectedQuestionB) {
            checkQuestionsCorrelation(selectedQuestionA, selectedQuestionB);
        } else {
            setIsAlreadyCorrelated(false);
            setExistingCorrelationId(null);
            // Don't clear individual correlation states here - they should persist
        }
    }, [selectedQuestionA, selectedQuestionB, selectedScopeType, selectedScopeEntityId, assets, organisations]);

    // Fetch common scopes when frameworks are selected
    useEffect(() => {
        fetchCommonScopes();
    }, [selectedFrameworkA, selectedFrameworkB, scopes]);

    // Debug: Log whenever correlation states change
    useEffect(() => {
        console.log('Correlation states updated:', {
            questionAAlreadyCorrelated,
            questionBAlreadyCorrelated,
            isAlreadyCorrelated,
            selectedQuestionA,
            selectedQuestionB
        });
    }, [questionAAlreadyCorrelated, questionBAlreadyCorrelated, isAlreadyCorrelated, selectedQuestionA, selectedQuestionB]);

    // Filter frameworks based on selected scope type
    const filteredFrameworks = useMemo(() => {
        if (!selectedScopeType) {
            return frameworks;
        }

        return frameworks.filter(framework => {
            // If framework has no allowed_scope_types, it allows all scopes (backward compatibility)
            if (!framework.allowed_scope_types || framework.allowed_scope_types.length === 0) {
                return true;
            }

            // Check if the framework's allowed scope types includes the selected scope type
            if (isAssetProductScope(selectedScopeType)) {
                return framework.allowed_scope_types.some((scopeType: string) => isAssetProductScope(scopeType));
            }

            return framework.allowed_scope_types.includes(selectedScopeType);
        });
    }, [frameworks, selectedScopeType]);

    const scopeOptions = useMemo(() => {
        const hasProduct = scopes.some(scope => scope.scope_name === 'Product');
        return scopes
            .filter(scope => !(scope.scope_name === 'Asset' && hasProduct))
            .map(scope => ({
                label: getScopeLabel(scope.scope_name),
                value: scope.scope_name
            }));
    }, [scopes]);

    const fetchFrameworks = async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/`, {
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                const data = await response.json();
                setFrameworks(data);
            }
        } catch (error) {
            console.error('Error fetching frameworks:', error);
        }
    };

    const fetchAssessmentTypes = async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assessment-types/`, {
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                const data = await response.json();
                setAssessmentTypes(data);
            }
        } catch (error) {
            console.error('Error fetching assessment types:', error);
        }
    };

    const fetchScopes = async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/scopes/`, {
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                const data = await response.json();
                setScopes(data);
            }
        } catch (error) {
            console.error('Error fetching scopes:', error);
        }
    };

    const fetchAssets = async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assets`, {
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                const data = await response.json();
                setAssets(data);
            }
        } catch (error) {
            console.error('Error fetching assets:', error);
        }
    };

    const fetchOrganisations = async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/get_all_organisations`, {
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                const data = await response.json();
                setOrganisations(data);
            }
        } catch (error) {
            console.error('Error fetching organisations:', error);
        }
    };

    const fetchCommonScopes = async () => {
        if (!selectedFrameworkA || !selectedFrameworkB) {
            setAvailableScopes(scopes);
            setFrameworksCompatible(true);
            setCompatibilityMessage('');
            return;
        }

        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/ai-tools/frameworks/common-scopes?framework_a_id=${selectedFrameworkA}&framework_b_id=${selectedFrameworkB}`,
                {
                    headers: {
                        ...getAuthHeader()
                    }
                }
            );

            if (response.ok) {
                const data = await response.json();

                if (!data.has_common_scopes) {
                    // No common scope types - show error
                    setFrameworksCompatible(false);
                    setCompatibilityMessage(
                        `⚠️ ${data.framework_a.name} and ${data.framework_b.name} have incompatible scope requirements. ` +
                        `${data.framework_a.name} allows: ${formatScopeTypeList(data.framework_a.allowed_scope_types)}. ` +
                        `${data.framework_b.name} allows: ${formatScopeTypeList(data.framework_b.allowed_scope_types)}. ` +
                        `Please add a common scope type (e.g., 'Other') to one or both frameworks.`
                    );
                    setAvailableScopes([]);
                    setSelectedScopeType('');
                    setSelectedScopeEntityId('');

                    api.warning({
                        message: 'Incompatible Frameworks',
                        description: 'These frameworks have no common scope types. You cannot create correlations between them.',
                        duration: 8
                    });
                } else {
                    // Filter scopes to only show common ones
                    const commonScopeNames = data.common_scope_types || [];
                    const filteredScopes = scopes.filter(scope => {
                        if (isAssetProductScope(scope.scope_name)) {
                            return commonScopeNames.some((name: string) => isAssetProductScope(name));
                        }
                        return commonScopeNames.includes(scope.scope_name);
                    });
                    setAvailableScopes(filteredScopes);
                    setFrameworksCompatible(true);
                    setCompatibilityMessage('');

                    // Reset scope selection if current scope is not in common scopes
                    const selectedScopeCompatible = selectedScopeType
                        ? isAssetProductScope(selectedScopeType)
                            ? commonScopeNames.some((name: string) => isAssetProductScope(name))
                            : commonScopeNames.includes(selectedScopeType)
                        : true;

                    if (selectedScopeType && !selectedScopeCompatible) {
                        setSelectedScopeType('');
                        setSelectedScopeEntityId('');
                    }
                }
            }
        } catch (error) {
            console.error('Error fetching common scopes:', error);
            setAvailableScopes(scopes);
            setFrameworksCompatible(true);
        }
    };

    const fetchAllCorrelations = async () => {
        setIsLoadingCorrelations(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/ai-tools/correlations`, {
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                const data = await response.json();
                setAllCorrelations(data);
            } else {
                console.error('Failed to fetch correlations');
                setAllCorrelations([]);
            }
        } catch (error) {
            console.error('Error fetching correlations:', error);
            setAllCorrelations([]);
        } finally {
            setIsLoadingCorrelations(false);
        }
    };

    const fetchQuestionsForFramework = async (frameworkId: string, assessmentTypeId: string, side: 'A' | 'B') => {
        const setLoading = side === 'A' ? setIsLoadingQuestionsA : setIsLoadingQuestionsB;
        const setQuestions = side === 'A' ? setQuestionsA : setQuestionsB;

        setLoading(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/ai-tools/frameworks/${frameworkId}/questions?assessment_type_id=${assessmentTypeId}`, {
                headers: {
                    ...getAuthHeader()
                }
            });
            if (response.ok) {
                const data = await response.json();
                setQuestions(data);
            } else {
                setQuestions([]);
            }
        } catch (error) {
            console.error('Error fetching questions:', error);
            setQuestions([]);
        } finally {
            setLoading(false);
        }
    };

    const checkQuestionsCorrelation = async (questionAId: string, questionBId: string) => {
        if (!questionAId || !questionBId) {
            setIsAlreadyCorrelated(false);
            return;
        }

        setIsCheckingCorrelation(true);
        try {
            // Check existing correlations for the same question pair AND same scope
            const response = await fetch(`${cyberbridge_back_end_rest_api}/ai-tools/correlations`, {
                headers: {
                    ...getAuthHeader()
                }
            });

            if (response.ok) {
                const correlations = await response.json();

                // Get the selected scope entity name for comparison
                let selectedEntityName: string | null = null;
                if (selectedScopeType !== 'Other' && selectedScopeEntityId) {
                    if (isAssetProductScope(selectedScopeType)) {
                        const selectedEntity = assets.find(asset => asset.id === selectedScopeEntityId);
                        selectedEntityName = selectedEntity ? formatAssetLabel(selectedEntity) : null;
                    } else if (selectedScopeType === 'Organization') {
                        const selectedEntity = organisations.find(o => o.id === selectedScopeEntityId);
                        selectedEntityName = selectedEntity ? selectedEntity.name : null;
                    }
                }

                // Find correlation with matching questions AND matching scope
                const existingCorrelation = correlations.find((correlation: any) => {
                    const questionsMatch = (
                        (correlation.question_a.id === questionAId && correlation.question_b.id === questionBId) ||
                        (correlation.question_a.id === questionBId && correlation.question_b.id === questionAId)
                    );

                    // Also check if scope matches
                    const scopeMatches = isAssetProductScope(selectedScopeType)
                        ? isAssetProductScope(correlation.scope.scope_name) &&
                          correlation.scope.entity_name === selectedEntityName
                        : correlation.scope.scope_name === selectedScopeType &&
                          correlation.scope.entity_name === selectedEntityName;

                    return questionsMatch && scopeMatches;
                });

                setIsAlreadyCorrelated(!!existingCorrelation);
                setExistingCorrelationId(existingCorrelation ? existingCorrelation.id : null);

                if (existingCorrelation) {
                    const scopeDisplay = selectedScopeType === 'Other'
                        ? 'Other scope'
                        : `${getScopeLabel(selectedScopeType)} scope (${selectedEntityName})`;
                    api.info({
                        message: 'Questions Already Correlated',
                        description: `These questions are already correlated for ${scopeDisplay}. You can de-correlate them if needed.`,
                        duration: 4,
                    });
                }
            }
        } catch (error) {
            console.error('Error checking correlation:', error);
            setIsAlreadyCorrelated(false);
        } finally {
            setIsCheckingCorrelation(false);
        }
    };

    const handleFrameworkChangeA = (frameworkId: string) => {
        setSelectedFrameworkA(frameworkId);
        setSelectedQuestionA('');
        setQuestionsA([]);
        setIsAlreadyCorrelated(false);
        setExistingCorrelationId(null);
        setQuestionAAlreadyCorrelated(null); // Only clear Question A's correlation state

        // If Framework A is the same as Framework B, clear Framework B selection
        if (frameworkId === selectedFrameworkB) {
            setSelectedFrameworkB('');
            setSelectedQuestionB('');
            setQuestionsB([]);
            setQuestionBAlreadyCorrelated(null);
        }

        if (frameworkId && selectedAssessmentTypeA) {
            fetchQuestionsForFramework(frameworkId, selectedAssessmentTypeA, 'A');
        }
    };

    const handleAssessmentTypeChangeA = (assessmentTypeId: string) => {
        setSelectedAssessmentTypeA(assessmentTypeId);
        setSelectedQuestionA('');
        setQuestionsA([]);
        setIsAlreadyCorrelated(false);
        setExistingCorrelationId(null);
        setQuestionAAlreadyCorrelated(null); // Only clear Question A's correlation state
        if (selectedFrameworkA && assessmentTypeId) {
            fetchQuestionsForFramework(selectedFrameworkA, assessmentTypeId, 'A');
        }
    };

    const handleFrameworkChangeB = (frameworkId: string) => {
        setSelectedFrameworkB(frameworkId);
        setSelectedQuestionB('');
        setQuestionsB([]);
        setIsAlreadyCorrelated(false);
        setExistingCorrelationId(null);
        setQuestionBAlreadyCorrelated(null); // Only clear Question B's correlation state

        // If Framework B is the same as Framework A, clear Framework A selection
        if (frameworkId === selectedFrameworkA) {
            setSelectedFrameworkA('');
            setSelectedQuestionA('');
            setQuestionsA([]);
            setQuestionAAlreadyCorrelated(null);
        }

        if (frameworkId && selectedAssessmentTypeB) {
            fetchQuestionsForFramework(frameworkId, selectedAssessmentTypeB, 'B');
        }
    };

    const handleAssessmentTypeChangeB = (assessmentTypeId: string) => {
        setSelectedAssessmentTypeB(assessmentTypeId);
        setSelectedQuestionB('');
        setQuestionsB([]);
        setIsAlreadyCorrelated(false);
        setExistingCorrelationId(null);
        setQuestionBAlreadyCorrelated(null); // Only clear Question B's correlation state
        if (selectedFrameworkB && assessmentTypeId) {
            fetchQuestionsForFramework(selectedFrameworkB, assessmentTypeId, 'B');
        }
    };

    // Function to check if a single question is already correlated with any other question
    const checkQuestionCorrelationStatus = async (questionId: string): Promise<string | null> => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/ai-tools/correlations`, {
                headers: {
                    ...getAuthHeader()
                }
            });

            if (response.ok) {
                const correlations = await response.json();
                const existingCorrelation = correlations.find((correlation: any) =>
                    correlation.question_a.id === questionId || correlation.question_b.id === questionId
                );

                if (existingCorrelation) {
                    // Return the ID of the other question this one is correlated with
                    return existingCorrelation.question_a.id === questionId
                        ? existingCorrelation.question_b.id
                        : existingCorrelation.question_a.id;
                }
            }
        } catch (error) {
            console.error('Error checking individual question correlation:', error);
        }
        return null;
    };

    // Custom handler for selecting Question A with validation
    const handleQuestionASelection = async (questionId: string) => {
        setSelectedQuestionA(questionId);

        // Check if this question is already correlated with another question
        const correlatedWithId = await checkQuestionCorrelationStatus(questionId);
        setQuestionAAlreadyCorrelated(correlatedWithId);

        console.log('Question A selected:', questionId);
        console.log('Question A already correlated with:', correlatedWithId);

        // Note: Removed warning for already correlated questions since we now support multiple correlations
    };

    // Custom handler for selecting Question B with validation
    const handleQuestionBSelection = async (questionId: string) => {
        setSelectedQuestionB(questionId);

        // Check if this question is already correlated with another question
        const correlatedWithId = await checkQuestionCorrelationStatus(questionId);
        setQuestionBAlreadyCorrelated(correlatedWithId);

        console.log('Question B selected:', questionId);
        console.log('Question B already correlated with:', correlatedWithId);

        // Note: Removed warning for already correlated questions since we now support multiple correlations
    };

    const handleCorrelate = async () => {
        if (!selectedQuestionA || !selectedQuestionB) {
            api.error({
                message: 'Incomplete Selection',
                description: 'Please select questions from both frameworks to correlate.',
                duration: 4,
            });
            return;
        }

        // Validate scope selection
        if (!selectedScopeType) {
            api.error({
                message: 'Scope Required',
                description: 'Please select a scope type for this correlation.',
                duration: 4,
            });
            return;
        }

        // Validate scope entity for non-Other scopes
        if (selectedScopeType !== 'Other' && !selectedScopeEntityId) {
            api.error({
                message: 'Scope Entity Required',
                description: `Please select a ${getScopeLabel(selectedScopeType).toLowerCase()} for this correlation.`,
                duration: 4,
            });
            return;
        }

        // Framework validation is now handled at UI level, but keep this as a safety check
        if (selectedFrameworkA === selectedFrameworkB) {
            api.error({
                message: 'Invalid Correlation',
                description: 'Cannot correlate questions from the same framework.',
                duration: 4,
            });
            return;
        }

        // Note: Removed check for already correlated questions since we now support multiple correlations

        // Automatically use Framework A's answer for correlation
        setIsCorrelating(true);
        try {
            // Proceed with correlation (backend will automatically sync answers from Question A to Question B)
            const response = await fetch(`${cyberbridge_back_end_rest_api}/ai-tools/correlate-questions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader()
                },
                body: JSON.stringify({
                    question_a_id: selectedQuestionA,
                    question_b_id: selectedQuestionB,
                    framework_id_a: selectedFrameworkA,
                    framework_id_b: selectedFrameworkB,
                    scope_name: selectedScopeType,
                    scope_entity_id: selectedScopeEntityId || null
                })
            });

            if (response.ok) {
                const result = await response.json();
                api.success({
                    message: 'Questions Correlated',
                    description: result.message || 'Questions have been successfully correlated.',
                    duration: 4,
                });

                // Don't reset selections - keep them to show the de-correlate button
                // Re-check correlation status to show de-correlate button
                if (selectedQuestionA && selectedQuestionB) {
                    checkQuestionsCorrelation(selectedQuestionA, selectedQuestionB);
                }

                // Refresh the all correlations list
                fetchAllCorrelations();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to correlate questions');
            }
        } catch (error) {
            api.error({
                message: 'Correlation Failed',
                description: error instanceof Error ? error.message : 'Failed to correlate questions. Please try again.',
                duration: 4,
            });
        } finally {
            setIsCorrelating(false);
        }
    };

    const handleDecorrelate = async () => {
        if (!existingCorrelationId) {
            api.error({
                message: 'No Correlation Found',
                description: 'Cannot find the correlation ID to remove.',
                duration: 4,
            });
            return;
        }

        setIsDecorrelating(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/ai-tools/correlations/${existingCorrelationId}`, {
                method: 'DELETE',
                headers: {
                    ...getAuthHeader()
                }
            });

            if (response.ok) {
                api.success({
                    message: 'Questions De-correlated Successfully',
                    description: 'The correlation between these questions has been removed. Existing answers will remain unchanged.',
                    duration: 4,
                });

                // Reset correlation state
                setIsAlreadyCorrelated(false);
                setExistingCorrelationId(null);

                // Refresh the all correlations list
                fetchAllCorrelations();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to de-correlate questions');
            }
        } catch (error) {
            api.error({
                message: 'De-correlation Failed',
                description: error instanceof Error ? error.message : 'Failed to remove question correlation. Please try again.',
                duration: 4,
            });
        } finally {
            setIsDecorrelating(false);
        }
    };

    const handleRemoveAllCorrelations = async () => {
        console.log('Remove All button clicked');
        console.log('Current correlations count:', allCorrelations.length);

        // Use native confirm for now
        const confirmed = window.confirm(
            'Are you sure you want to remove all question correlations? This action cannot be undone. Existing answers will remain unchanged.'
        );

        if (!confirmed) {
            console.log('User cancelled removal');
            return;
        }

        console.log('User confirmed removal');
        setIsRemovingAll(true);
        try {
            console.log('Sending DELETE request to:', `${cyberbridge_back_end_rest_api}/ai-tools/correlations`);
            const response = await fetch(`${cyberbridge_back_end_rest_api}/ai-tools/correlations`, {
                method: 'DELETE',
                headers: {
                    ...getAuthHeader()
                }
            });

            console.log('Response status:', response.status);

            if (response.ok) {
                const result = await response.json();
                console.log('Response data:', result);
                api.success({
                    message: 'All Correlations Removed',
                    description: result.message || 'All question correlations have been successfully removed.',
                    duration: 4,
                });

                // Reset all correlation-related states
                setIsAlreadyCorrelated(false);
                setExistingCorrelationId(null);
                setQuestionAAlreadyCorrelated(null);
                setQuestionBAlreadyCorrelated(null);

                // Refresh the all correlations list
                fetchAllCorrelations();
            } else {
                const errorData = await response.json();
                console.error('Error response:', errorData);
                throw new Error(errorData.detail || 'Failed to remove all correlations');
            }
        } catch (error) {
            console.error('Error removing correlations:', error);
            api.error({
                message: 'Removal Failed',
                description: error instanceof Error ? error.message : 'Failed to remove all correlations. Please try again.',
                duration: 4,
            });
        } finally {
            setIsRemovingAll(false);
        }
    };

    const fetchLLMOptimizationSettings = async () => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/llm`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader()
                }
            });

            if (response.ok) {
                const data = await response.json();
                setMaxQuestionsPerFramework(data.max_questions_per_framework || 10);
                setLlmTimeoutSeconds(data.llm_timeout_seconds || 300);
                setMinConfidenceThreshold(data.min_confidence_threshold || 75);
                setMaxCorrelations(data.max_correlations || 10);
            }
        } catch (error) {
            console.error('Error fetching LLM optimization settings:', error);
        }
    };

    const handleSaveLLMOptimizations = async () => {
        setIsSavingOptimizations(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/settings/llm`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader()
                },
                body: JSON.stringify({
                    max_questions_per_framework: maxQuestionsPerFramework,
                    llm_timeout_seconds: llmTimeoutSeconds,
                    min_confidence_threshold: minConfidenceThreshold,
                    max_correlations: maxCorrelations
                })
            });

            if (response.ok) {
                api.success({
                    message: 'Settings Saved',
                    description: 'LLM optimization settings have been updated successfully.',
                    duration: 3,
                });
            } else {
                const error = await response.json();
                api.error({
                    message: 'Save Failed',
                    description: error.detail || 'Failed to save LLM optimization settings.',
                    duration: 4,
                });
            }
        } catch (error) {
            api.error({
                message: 'Error',
                description: 'An error occurred while saving LLM optimization settings.',
                duration: 4,
            });
        } finally {
            setIsSavingOptimizations(false);
        }
    };

    const handleGenerateAISuggestions = async () => {
        if (!selectedFrameworkA || !selectedFrameworkB) {
            api.warning({
                message: 'Incomplete Selection',
                description: 'Please select both frameworks to generate AI correlation suggestions.',
                duration: 4,
            });
            return;
        }

        if (!selectedAssessmentTypeA || !selectedAssessmentTypeB) {
            api.warning({
                message: 'Assessment Types Required',
                description: 'Please select assessment types for both frameworks.',
                duration: 4,
            });
            return;
        }

        // Validate that both assessment types are the same
        if (selectedAssessmentTypeA !== selectedAssessmentTypeB) {
            const typeNameA = assessmentTypes.find(t => t.id === selectedAssessmentTypeA)?.type_name || 'Unknown';
            const typeNameB = assessmentTypes.find(t => t.id === selectedAssessmentTypeB)?.type_name || 'Unknown';
            api.error({
                message: 'Assessment Types Must Match',
                description: `Cannot correlate questions from different assessment types. Framework A is '${typeNameA}' and Framework B is '${typeNameB}'. Please select the same assessment type for both frameworks.`,
                duration: 6,
            });
            return;
        }

        // Use the store to generate suggestions
        const success = await generateAISuggestions(
            selectedFrameworkA,
            selectedFrameworkB,
            selectedAssessmentTypeA
        );

        if (success && aiSuggestions) {
            if (aiSuggestions.suggestions.length > 0) {
                api.success({
                    message: 'AI Suggestions Generated',
                    description: `Found ${aiSuggestions.suggestions.length} correlation suggestions between ${aiSuggestions.framework_a_name} and ${aiSuggestions.framework_b_name}.`,
                    duration: 5,
                });
            } else {
                api.info({
                    message: 'No Suggestions Found',
                    description: 'The AI did not find any strong correlations between the selected frameworks.',
                    duration: 4,
                });
            }
        }
    };

    const handleApplyAISuggestion = async (suggestion: any) => {
        // Validate scope selection before applying AI suggestion
        if (!selectedScopeType) {
            api.error({
                message: 'Scope Required',
                description: 'Please select a scope type before applying AI suggestions.',
                duration: 4,
            });
            return;
        }

        // Validate scope entity for non-Other scopes
        if (selectedScopeType !== 'Other' && !selectedScopeEntityId) {
            api.error({
                message: 'Scope Entity Required',
                description: `Please select a ${getScopeLabel(selectedScopeType).toLowerCase()} before applying AI suggestions.`,
                duration: 4,
            });
            return;
        }

        setApplyingCorrelationId(suggestion.question_a_id + suggestion.question_b_id);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/ai-tools/correlate-questions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader()
                },
                body: JSON.stringify({
                    question_a_id: suggestion.question_a_id,
                    question_b_id: suggestion.question_b_id,
                    framework_id_a: selectedFrameworkA,
                    framework_id_b: selectedFrameworkB,
                    scope_name: selectedScopeType,
                    scope_entity_id: selectedScopeEntityId || null
                })
            });

            if (response.ok) {
                api.success({
                    message: 'Correlation Applied',
                    description: 'The suggested correlation has been successfully applied.',
                    duration: 4,
                });

                // Remove the applied suggestion from the store
                removeSuggestion(suggestion.question_a_id, suggestion.question_b_id);

                // Refresh the all correlations list
                fetchAllCorrelations();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to apply correlation');
            }
        } catch (error) {
            api.error({
                message: 'Failed to Apply',
                description: error instanceof Error ? error.message : 'Failed to apply the correlation suggestion.',
                duration: 4,
            });
        } finally {
            setApplyingCorrelationId(null);
        }
    };

    const handleRejectAISuggestion = (suggestion: any) => {
        removeSuggestion(suggestion.question_a_id, suggestion.question_b_id);

        api.info({
            message: 'Suggestion Rejected',
            description: 'The correlation suggestion has been removed from the list.',
            duration: 3,
        });
    };

    const handleAuditCorrelations = async () => {
        setIsAuditing(true);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/ai-tools/correlations/validate`, {
                headers: {
                    ...getAuthHeader()
                }
            });

            if (response.ok) {
                const data = await response.json();
                setAuditResults(data);

                if (data.invalid_correlations_count > 0) {
                    api.warning({
                        message: 'Invalid Correlations Found',
                        description: `Found ${data.invalid_correlations_count} correlation(s) that need attention.`,
                        duration: 5,
                    });
                } else {
                    api.success({
                        message: 'All Correlations Valid',
                        description: 'All existing correlations are properly configured.',
                        duration: 4,
                    });
                }
            } else {
                throw new Error('Failed to audit correlations');
            }
        } catch (error) {
            api.error({
                message: 'Audit Failed',
                description: error instanceof Error ? error.message : 'Failed to audit correlations.',
                duration: 4,
            });
        } finally {
            setIsAuditing(false);
        }
    };

    const handleFixInvalidCorrelations = async (action: 'delete' | 'migrate', targetScope?: string) => {
        setIsFixing(true);
        try {
            const url = new URL(`${cyberbridge_back_end_rest_api}/ai-tools/correlations/fix-invalid`);
            url.searchParams.append('action', action);
            if (action === 'migrate' && targetScope) {
                url.searchParams.append('target_scope', targetScope);
            }

            const response = await fetch(url.toString(), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeader()
                }
            });

            if (response.ok) {
                const data = await response.json();
                api.success({
                    message: 'Correlations Fixed',
                    description: data.message,
                    duration: 4,
                });

                // Refresh audit results
                handleAuditCorrelations();
                // Refresh correlation list
                fetchAllCorrelations();
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to fix correlations');
            }
        } catch (error) {
            api.error({
                message: 'Fix Failed',
                description: error instanceof Error ? error.message : 'Failed to fix invalid correlations.',
                duration: 4,
            });
        } finally {
            setIsFixing(false);
        }
    };

    const onClick: MenuProps['onClick'] = (e) => {
        console.log('click ', e);

        // Warn user if AI generation is in progress
        // Navigation is always allowed - results persist in the store
        return true;
    };

    // Show loading or access denied for non-admin users
    if (!current_user || !['super_admin', 'org_admin'].includes(current_user.role_name)) {
        return (
            <div>
                {contextHolder}
                <div className="page-parent">
                    <Sidebar onClick={onClick} selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
                    <div className="page-content">
                        <h2>Access Denied</h2>
                        <p>This page is only accessible to administrators.</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div>
            {contextHolder}
            <div className="page-parent">
                <Sidebar onClick={onClick} selectedKeys={menuHighlighting.selectedKeys} openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange} />
                <div className="page-content">
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <InfoTitle
                                title="Correlations"
                                infoContent="Advanced AI-powered tools for framework management and question analysis."
                                className="page-title"
                                icon={<LinkOutlined style={{ color: '#1a365d' }} />}
                            />
                        </div>
                    </div>

                    {/* Question Correlation Section */}
                    <div className="page-section">
                            <h3 className="section-title">Correlate Questions between Frameworks</h3>
                            <p className="section-subtitle">
                                Connect similar questions from different frameworks to automatically synchronize answers across assessments.
                            </p>

                            {/* Scope Selection - First Step */}
                            <Card
                                title="Step 1: Select Scope Context"
                                style={{ marginTop: '24px', marginBottom: '24px' }}
                                headStyle={{ backgroundColor: '#f0fdf4', color: '#16a34a', fontWeight: 'bold' }}
                            >
                                <p style={{ marginBottom: '16px', color: '#666' }}>
                                    First, select the scope context for your correlation. This will filter the available frameworks.
                                </p>
                                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                                    <div className="form-group" style={{ flex: '1 1 300px', minWidth: '250px' }}>
                                        <label className="form-label">Scope Type</label>
                                        <Select
                                            placeholder="Select scope type"
                                            style={{ width: '100%' }}
                                            value={selectedScopeType || undefined}
                                            onChange={(value) => {
                                                setSelectedScopeType(value);
                                                setSelectedScopeEntityId('');
                                                // Reset framework selections when scope changes
                                                setSelectedFrameworkA('');
                                                setSelectedFrameworkB('');
                                                setSelectedAssessmentTypeA('');
                                                setSelectedAssessmentTypeB('');
                                                setSelectedQuestionA('');
                                                setSelectedQuestionB('');
                                            }}
                                            options={scopeOptions}
                                        />
                                    </div>

                                    <div className="form-group" style={{ flex: '1 1 300px', minWidth: '250px' }}>
                                        <label className="form-label">Scope Entity</label>
                                        <Select
                                            placeholder={
                                                selectedScopeType === 'Other'
                                                    ? 'Not required for Other scope'
                                                    : isAssetProductScope(selectedScopeType)
                                                    ? 'Select an asset / product'
                                                    : selectedScopeType === 'Organization'
                                                    ? 'Select an organization'
                                                    : 'Select scope type first'
                                            }
                                            style={{ width: '100%' }}
                                            value={selectedScopeEntityId || undefined}
                                            onChange={(value) => {
                                                setSelectedScopeEntityId(value);
                                                // Reset framework selections when scope entity changes
                                                setSelectedFrameworkA('');
                                                setSelectedFrameworkB('');
                                                setSelectedAssessmentTypeA('');
                                                setSelectedAssessmentTypeB('');
                                                setSelectedQuestionA('');
                                                setSelectedQuestionB('');
                                            }}
                                            disabled={!selectedScopeType || selectedScopeType === 'Other'}
                                            options={
                                                isAssetProductScope(selectedScopeType)
                                                    ? assets.map(asset => ({
                                                        label: formatAssetLabel(asset),
                                                        value: asset.id
                                                    }))
                                                    : selectedScopeType === 'Organization'
                                                    ? organisations.map(org => ({
                                                        label: org.name,
                                                        value: org.id
                                                    }))
                                                    : []
                                            }
                                        />
                                    </div>
                                </div>
                            </Card>

                            {/* Framework Selection - Second Step */}
                            <div style={{ display: 'flex', gap: '24px', marginTop: '24px', flexWrap: 'wrap' }}>
                                {/* Framework A */}
                                <Card
                                    title="Step 2: Framework A"
                                    style={{ flex: '1 1 300px', minWidth: '0', maxWidth: '100%' }}
                                    headStyle={{ backgroundColor: '#f0f9ff', color: '#1890ff', fontWeight: 'bold' }}
                                >
                                    <div className="form-group">
                                        <label className="form-label">Framework</label>
                                        <Select
                                            placeholder={selectedScopeType ? "Select a framework" : "Select scope first"}
                                            style={{ width: '100%' }}
                                            value={selectedFrameworkA || undefined}
                                            onChange={handleFrameworkChangeA}
                                            disabled={!selectedScopeType || (selectedScopeType !== 'Other' && !selectedScopeEntityId)}
                                            options={filteredFrameworks
                                                .filter(framework => framework.id !== selectedFrameworkB)
                                                .map(framework => ({
                                                    label: framework.organisation_domain
                                                        ? `${framework.name} (${framework.organisation_domain})`
                                                        : framework.name,
                                                    value: framework.id
                                                }))}
                                        />
                                    </div>

                                    <div className="form-group">
                                        <label className="form-label">Assessment Type</label>
                                        <Select
                                            placeholder="Select assessment type"
                                            style={{ width: '100%' }}
                                            value={selectedAssessmentTypeA || undefined}
                                            onChange={handleAssessmentTypeChangeA}
                                            disabled={!selectedFrameworkA}
                                            options={assessmentTypes.map(type => ({
                                                label: type.type_name.charAt(0).toUpperCase() + type.type_name.slice(1),
                                                value: type.id
                                            }))}
                                        />
                                    </div>

                                    <div className="form-group">
                                        <label className="form-label">Question</label>
                                        <Select
                                            placeholder="Select a question"
                                            style={{ width: '100%' }}
                                            value={selectedQuestionA || undefined}
                                            onChange={handleQuestionASelection}
                                            disabled={!selectedFrameworkA || !selectedAssessmentTypeA}
                                            loading={isLoadingQuestionsA}
                                            options={questionsA.map(question => ({
                                                label: question.text.length > 80 ?
                                                    question.text.substring(0, 80) + '...' :
                                                    question.text,
                                                value: question.id
                                            }))}
                                        />
                                    </div>
                                </Card>

                                {/* Framework B */}
                                <Card
                                    title="Step 3: Framework B"
                                    style={{ flex: '1 1 300px', minWidth: '0', maxWidth: '100%' }}
                                    headStyle={{ backgroundColor: '#EBF4FC', color: '#1a365d', fontWeight: 'bold' }}
                                >
                                    <div className="form-group">
                                        <label className="form-label">Framework</label>
                                        <Select
                                            placeholder={selectedScopeType ? "Select a framework" : "Select scope first"}
                                            style={{ width: '100%' }}
                                            value={selectedFrameworkB || undefined}
                                            onChange={handleFrameworkChangeB}
                                            disabled={!selectedScopeType || (selectedScopeType !== 'Other' && !selectedScopeEntityId)}
                                            options={filteredFrameworks
                                                .filter(framework => framework.id !== selectedFrameworkA)
                                                .map(framework => ({
                                                    label: framework.organisation_domain
                                                        ? `${framework.name} (${framework.organisation_domain})`
                                                        : framework.name,
                                                    value: framework.id
                                                }))}
                                        />
                                    </div>

                                    <div className="form-group">
                                        <label className="form-label">Assessment Type</label>
                                        <Select
                                            placeholder="Select assessment type"
                                            style={{ width: '100%' }}
                                            value={selectedAssessmentTypeB || undefined}
                                            onChange={handleAssessmentTypeChangeB}
                                            disabled={!selectedFrameworkB}
                                            options={assessmentTypes.map(type => ({
                                                label: type.type_name.charAt(0).toUpperCase() + type.type_name.slice(1),
                                                value: type.id
                                            }))}
                                        />
                                    </div>

                                    <div className="form-group">
                                        <label className="form-label">Question</label>
                                        <Select
                                            placeholder="Select a question"
                                            style={{ width: '100%' }}
                                            value={selectedQuestionB || undefined}
                                            onChange={handleQuestionBSelection}
                                            disabled={!selectedFrameworkB || !selectedAssessmentTypeB}
                                            loading={isLoadingQuestionsB}
                                            options={questionsB.map(question => ({
                                                label: question.text.length > 80 ?
                                                    question.text.substring(0, 80) + '...' :
                                                    question.text,
                                                value: question.id
                                            }))}
                                        />
                                    </div>
                                </Card>
                            </div>

                            {/* Framework Compatibility Warning */}
                            {!frameworksCompatible && compatibilityMessage && (
                                <div style={{
                                    marginTop: '16px',
                                    padding: '12px',
                                    backgroundColor: '#fff3cd',
                                    border: '1px solid #ffc107',
                                    borderRadius: '6px',
                                    color: '#856404'
                                }}>
                                    {compatibilityMessage}
                                </div>
                            )}

                            {/* Correlate/De-correlate Button */}
                            <div className="control-group" style={{ textAlign: 'center', marginTop: '24px', display: 'flex', gap: '16px', justifyContent: 'center' }}>
                                {/* Show de-correlate button ONLY when the exact pair (A + B) are correlated together */}
                                {isAlreadyCorrelated ? (
                                    <button
                                        onClick={handleDecorrelate}
                                        disabled={isDecorrelating || isCheckingCorrelation}
                                        style={{
                                            minWidth: '200px',
                                            height: '48px',
                                            fontSize: '16px',
                                            fontWeight: 'bold',
                                            backgroundColor: '#dc2626',
                                            border: '1px solid #dc2626',
                                            color: 'white',
                                            borderRadius: '6px',
                                            cursor: 'pointer',
                                            transition: 'all 0.3s ease'
                                        }}
                                        onMouseEnter={(e) => {
                                            if (!isDecorrelating && !isCheckingCorrelation) {
                                                e.currentTarget.style.backgroundColor = '#b91c1c';
                                                e.currentTarget.style.borderColor = '#b91c1c';
                                            }
                                        }}
                                        onMouseLeave={(e) => {
                                            if (!isDecorrelating && !isCheckingCorrelation) {
                                                e.currentTarget.style.backgroundColor = '#dc2626';
                                                e.currentTarget.style.borderColor = '#dc2626';
                                            }
                                        }}
                                    >
                                        {isDecorrelating ? 'De-correlating...' : 'De-correlate Questions'}
                                    </button>
                                ) : (
                                    <button
                                        className="add-button"
                                        onClick={handleCorrelate}
                                        disabled={isCorrelating || !selectedQuestionA || !selectedQuestionB || isCheckingCorrelation || isAlreadyCorrelated || !selectedScopeType || (selectedScopeType !== 'Other' && !selectedScopeEntityId) || !frameworksCompatible}
                                        onMouseEnter={() => {
                                            console.log('Button state:', {
                                                isCorrelating,
                                                selectedQuestionA,
                                                selectedQuestionB,
                                                isCheckingCorrelation,
                                                questionAAlreadyCorrelated,
                                                questionBAlreadyCorrelated,
                                                frameworksCompatible,
                                                disabled: isCorrelating || !selectedQuestionA || !selectedQuestionB || isCheckingCorrelation || isAlreadyCorrelated || !frameworksCompatible
                                            });
                                        }}
                                        style={{
                                            minWidth: '200px',
                                            height: '48px',
                                            fontSize: '16px',
                                            fontWeight: 'bold',
                                            ...(questionAAlreadyCorrelated || questionBAlreadyCorrelated ? {
                                                backgroundColor: '#fef2f2',
                                                borderColor: '#fca5a5',
                                                color: '#dc2626',
                                                cursor: 'not-allowed',
                                                opacity: 0.8
                                            } : {})
                                        }}
                                    >
                                        {isCorrelating
                                            ? 'Correlating...'
                                            : isCheckingCorrelation
                                            ? 'Checking...'
                                            : !frameworksCompatible
                                            ? 'Incompatible Frameworks'
                                            : !selectedScopeType
                                            ? 'Select Scope First'
                                            : selectedScopeType !== 'Other' && !selectedScopeEntityId
                                            ? `Select ${getScopeLabel(selectedScopeType)} First`
                                            : !selectedQuestionA || !selectedQuestionB
                                            ? 'Select Questions First'
                                            : questionAAlreadyCorrelated || questionBAlreadyCorrelated
                                            ? 'Question Already Correlated'
                                            : 'Correlate Questions'
                                        }
                                    </button>
                                )}
                            </div>

                            {/* AI Suggestions Button - Separate Section */}
                            <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'center' }}>
                                <button
                                    onClick={handleGenerateAISuggestions}
                                    disabled={aiLoading || !selectedFrameworkA || !selectedFrameworkB || !selectedAssessmentTypeA || !selectedAssessmentTypeB}
                                    style={{
                                        minWidth: '250px',
                                        height: '48px',
                                        fontSize: '16px',
                                        fontWeight: 'bold',
                                        backgroundColor: aiLoading ? '#d1d5db' : '#0f386a',
                                        border: `1px solid ${aiLoading ? '#d1d5db' : '#0f386a'}`,
                                        color: 'white',
                                        borderRadius: '6px',
                                        cursor: (aiLoading || !selectedFrameworkA || !selectedFrameworkB || !selectedAssessmentTypeA || !selectedAssessmentTypeB) ? 'not-allowed' : 'pointer',
                                        transition: 'all 0.3s ease',
                                        opacity: (aiLoading || !selectedFrameworkA || !selectedFrameworkB || !selectedAssessmentTypeA || !selectedAssessmentTypeB) ? 0.6 : 1
                                    }}
                                    onMouseEnter={(e) => {
                                        if (!aiLoading && selectedFrameworkA && selectedFrameworkB && selectedAssessmentTypeA && selectedAssessmentTypeB) {
                                            e.currentTarget.style.backgroundColor = '#0a2d55';
                                            e.currentTarget.style.borderColor = '#0a2d55';
                                        }
                                    }}
                                    onMouseLeave={(e) => {
                                        if (!aiLoading) {
                                            e.currentTarget.style.backgroundColor = '#0f386a';
                                            e.currentTarget.style.borderColor = '#0f386a';
                                        }
                                    }}
                                >
                                    {aiLoading ? (
                                        <>
                                            <LoadingOutlined style={{ marginRight: '8px' }} spin />
                                            Finding Correlations with AI...
                                        </>
                                    ) : (
                                        '🤖 Find Correlations with AI'
                                    )}
                                </button>
                            </div>

                            <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                                <h4 style={{ margin: '0 0 12px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>How Question Correlation Works:</h4>
                                <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.6' }}>
                                    <li>Select questions from two different frameworks that have similar intent</li>
                                    <li>Once correlated, answering one question automatically applies the same answer to its correlated question</li>
                                    <li>Policies and evidence files are also synchronized across correlated questions</li>
                                    <li>Synchronization only applies within the same user's assessments</li>
                                    <li>Use the red "De-correlate Questions" button to remove correlations between questions</li>
                                    <li>De-correlation removes the link but preserves existing answers, policies, and evidence</li>
                                </ul>
                            </div>
                        </div>

                    {/* All Correlations Section */}
                    <div className="page-section" style={{ marginTop: '48px' }}>
                        <h3 className="section-title">All Correlations</h3>
                        <p className="section-subtitle">
                            View and manage all existing question correlations across frameworks.
                        </p>

                        <div style={{ marginBottom: '16px' }}>
                            <Space>
                                <Input
                                    placeholder="Search correlations..."
                                    prefix={<SearchOutlined />}
                                    value={searchText}
                                    onChange={(e) => setSearchText(e.target.value)}
                                    style={{ width: 300 }}
                                />
                                <button
                                    className="add-button"
                                    onClick={fetchAllCorrelations}
                                    disabled={isLoadingCorrelations}
                                    style={{
                                        height: '32px',
                                        padding: '0 16px',
                                        fontSize: '14px',
                                        backgroundColor: isLoadingCorrelations ? '#f5f5f5' : undefined
                                    }}
                                >
                                    {isLoadingCorrelations ? 'Refreshing...' : 'Refresh'}
                                </button>
                                <button
                                    onClick={handleRemoveAllCorrelations}
                                    disabled={isRemovingAll || isLoadingCorrelations || allCorrelations.length === 0}
                                    style={{
                                        height: '32px',
                                        padding: '0 16px',
                                        fontSize: '14px',
                                        backgroundColor: '#dc2626',
                                        border: '1px solid #dc2626',
                                        color: 'white',
                                        borderRadius: '6px',
                                        cursor: (isRemovingAll || isLoadingCorrelations || allCorrelations.length === 0) ? 'not-allowed' : 'pointer',
                                        opacity: (isRemovingAll || isLoadingCorrelations || allCorrelations.length === 0) ? 0.5 : 1,
                                        transition: 'all 0.3s ease'
                                    }}
                                    onMouseEnter={(e) => {
                                        if (!isRemovingAll && !isLoadingCorrelations && allCorrelations.length > 0) {
                                            e.currentTarget.style.backgroundColor = '#b91c1c';
                                            e.currentTarget.style.borderColor = '#b91c1c';
                                        }
                                    }}
                                    onMouseLeave={(e) => {
                                        if (!isRemovingAll && !isLoadingCorrelations && allCorrelations.length > 0) {
                                            e.currentTarget.style.backgroundColor = '#dc2626';
                                            e.currentTarget.style.borderColor = '#dc2626';
                                        }
                                    }}
                                >
                                    {isRemovingAll ? 'Removing...' : 'Remove All'}
                                </button>
                            </Space>
                        </div>

                        <Table
                            dataSource={allCorrelations.filter(correlation => {
                                if (!searchText) return true;
                                const searchLower = searchText.toLowerCase();
                                return (
                                    correlation.question_a.framework.toLowerCase().includes(searchLower) ||
                                    correlation.question_b.framework.toLowerCase().includes(searchLower) ||
                                    correlation.question_a.text.toLowerCase().includes(searchLower) ||
                                    correlation.question_b.text.toLowerCase().includes(searchLower) ||
                                    correlation.created_by.toLowerCase().includes(searchLower)
                                );
                            })}
                            columns={CorrelationsGridColumns(allCorrelations)}
                            rowKey="id"
                            loading={isLoadingCorrelations}
                            scroll={{ x: 1500 }}
                            pagination={{
                                pageSize: 10,
                                showTotal: (total, range) =>
                                    `${range[0]}-${range[1]} of ${total} correlations`,
                                showSizeChanger: true,
                                showQuickJumper: true,
                            }}
                            size="middle"
                        />

                        <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                            <h4 style={{ margin: '0 0 8px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>About This Table:</h4>
                            <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.5' }}>
                                <li>Shows all question correlations across all frameworks</li>
                                <li>Use the search box to find specific correlations</li>
                                <li>Click column headers to sort data</li>
                                <li>Use column filters to narrow down results</li>
                                <li>Click "Refresh" to update the table with latest data</li>
                            </ul>
                        </div>
                    </div>

                    {/* Audit Correlations Section */}
                    <div className="page-section" style={{ marginTop: '48px' }}>
                        <h3 className="section-title">Audit Correlations</h3>
                        <p className="section-subtitle">
                            Check for invalid correlations caused by framework scope configuration changes and fix them.
                        </p>

                        <div style={{ marginTop: '24px' }}>
                            <button
                                className="add-button"
                                onClick={handleAuditCorrelations}
                                disabled={isAuditing}
                                style={{
                                    minWidth: '200px',
                                    height: '40px',
                                    fontSize: '16px',
                                    fontWeight: 'bold',
                                }}
                            >
                                {isAuditing ? 'Auditing...' : 'Run Audit'}
                            </button>
                        </div>

                        {/* Audit Results */}
                        {auditResults && (
                            <div style={{ marginTop: '24px' }}>
                                {/* Summary Card */}
                                <Card
                                    style={{
                                        marginBottom: '24px',
                                        backgroundColor: auditResults.summary.has_invalid_correlations ? '#fff3cd' : '#d4edda',
                                        borderColor: auditResults.summary.has_invalid_correlations ? '#ffc107' : '#28a745'
                                    }}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div>
                                            <h4 style={{ margin: '0 0 8px 0', color: auditResults.summary.has_invalid_correlations ? '#856404' : '#155724' }}>
                                                Audit Summary
                                            </h4>
                                            <p style={{ margin: '0', color: auditResults.summary.has_invalid_correlations ? '#856404' : '#155724' }}>
                                                <strong>Total Correlations:</strong> {auditResults.total_correlations}<br />
                                                <strong>Valid:</strong> {auditResults.valid_correlations_count}<br />
                                                <strong>Invalid:</strong> {auditResults.invalid_correlations_count}
                                            </p>
                                        </div>
                                        {auditResults.summary.has_invalid_correlations && (
                                            <div>
                                                <button
                                                    onClick={() => handleFixInvalidCorrelations('delete')}
                                                    disabled={isFixing}
                                                    style={{
                                                        marginRight: '8px',
                                                        padding: '8px 16px',
                                                        backgroundColor: '#dc2626',
                                                        border: '1px solid #dc2626',
                                                        color: 'white',
                                                        borderRadius: '6px',
                                                        cursor: isFixing ? 'not-allowed' : 'pointer',
                                                        opacity: isFixing ? 0.5 : 1
                                                    }}
                                                >
                                                    {isFixing ? 'Fixing...' : 'Delete All Invalid'}
                                                </button>
                                                <button
                                                    onClick={() => handleFixInvalidCorrelations('migrate', 'Other')}
                                                    disabled={isFixing}
                                                    style={{
                                                        padding: '8px 16px',
                                                        backgroundColor: '#2563eb',
                                                        border: '1px solid #2563eb',
                                                        color: 'white',
                                                        borderRadius: '6px',
                                                        cursor: isFixing ? 'not-allowed' : 'pointer',
                                                        opacity: isFixing ? 0.5 : 1
                                                    }}
                                                >
                                                    {isFixing ? 'Fixing...' : 'Migrate to "Other" Scope'}
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </Card>

                                {/* Invalid Correlations List */}
                                {auditResults.invalid_correlations_count > 0 && (
                                    <div>
                                        <h4 style={{ marginBottom: '16px', color: '#595959' }}>Invalid Correlations:</h4>
                                        {auditResults.invalid_correlations.map((correlation: any, index: number) => (
                                            <Card
                                                key={correlation.correlation_id}
                                                style={{
                                                    marginBottom: '16px',
                                                    borderColor: '#ffc107',
                                                    backgroundColor: '#fffbf0'
                                                }}
                                            >
                                                <div style={{ marginBottom: '12px' }}>
                                                    <strong style={{ color: '#d97706' }}>#{index + 1}</strong>
                                                </div>
                                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '12px' }}>
                                                    <div>
                                                        <strong>Framework A:</strong> {correlation.question_a.framework_name}<br />
                                                        <span style={{ fontSize: '12px', color: '#666' }}>{correlation.question_a.text}</span><br />
                                                        <span style={{ fontSize: '12px', color: '#888' }}>
                                                            Allowed scopes: {Array.isArray(correlation.framework_a_allowed_scopes)
                                                                ? correlation.framework_a_allowed_scopes.join(', ')
                                                                : correlation.framework_a_allowed_scopes}
                                                        </span>
                                                    </div>
                                                    <div>
                                                        <strong>Framework B:</strong> {correlation.question_b.framework_name}<br />
                                                        <span style={{ fontSize: '12px', color: '#666' }}>{correlation.question_b.text}</span><br />
                                                        <span style={{ fontSize: '12px', color: '#888' }}>
                                                            Allowed scopes: {Array.isArray(correlation.framework_b_allowed_scopes)
                                                                ? correlation.framework_b_allowed_scopes.join(', ')
                                                                : correlation.framework_b_allowed_scopes}
                                                        </span>
                                                    </div>
                                                </div>
                                                <div style={{ padding: '12px', backgroundColor: '#fff', borderRadius: '4px', border: '1px solid #ffc107' }}>
                                                    <strong>Issue:</strong> {correlation.issue}<br />
                                                    <strong>Current Scope:</strong> {correlation.current_scope}<br />
                                                    <strong>Recommendation:</strong> {correlation.recommendation}
                                                </div>
                                            </Card>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f9f9f9', borderRadius: '6px', border: '1px solid #e8e8e8' }}>
                            <h4 style={{ margin: '0 0 8px 0', color: '#595959', fontSize: '14px', fontWeight: '600' }}>About This Audit:</h4>
                            <ul style={{ margin: 0, paddingLeft: '20px', color: '#8c8c8c', fontSize: '14px', lineHeight: '1.5' }}>
                                <li>Checks all existing correlations for scope compatibility issues</li>
                                <li>Invalid correlations occur when frameworks' allowed scope types have changed</li>
                                <li>You can delete invalid correlations or migrate them to "Other" scope</li>
                                <li>Run this audit after changing framework scope configurations</li>
                            </ul>
                        </div>
                    </div>

                    {/* LLM Optimizations Section - Super Admin Only */}
                    {current_user?.role_name === 'super_admin' && (
                        <div className="page-section" style={{ marginTop: '48px' }}>
                            <h3 className="section-title">LLM Optimizations</h3>
                            <p className="section-subtitle">
                                Configure settings for AI-powered correlation analysis to optimize performance and accuracy.
                            </p>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '24px' }}>
                                {/* Max Questions Per Framework */}
                                <div>
                                    <label style={{ display: 'block', marginBottom: '8px', color: '#595959', fontSize: '14px', fontWeight: '600' }}>
                                        Max Questions Per Framework
                                    </label>
                                    <Input
                                        type="number"
                                        value={maxQuestionsPerFramework}
                                        onChange={(e) => setMaxQuestionsPerFramework(Number(e.target.value))}
                                        min={1}
                                        max={50}
                                        style={{ width: '100%' }}
                                    />
                                    <div style={{ marginTop: '4px', color: '#8c8c8c', fontSize: '12px' }}>
                                        Number of questions to analyze from each framework (1-50). Lower values = faster processing.
                                    </div>
                                </div>

                                {/* LLM Timeout */}
                                <div>
                                    <label style={{ display: 'block', marginBottom: '8px', color: '#595959', fontSize: '14px', fontWeight: '600' }}>
                                        LLM Timeout (seconds)
                                    </label>
                                    <Input
                                        type="number"
                                        value={llmTimeoutSeconds}
                                        onChange={(e) => setLlmTimeoutSeconds(Number(e.target.value))}
                                        min={60}
                                        max={600}
                                        style={{ width: '100%' }}
                                    />
                                    <div style={{ marginTop: '4px', color: '#8c8c8c', fontSize: '12px' }}>
                                        Maximum time to wait for LLM response (60-600 seconds).
                                    </div>
                                </div>

                                {/* Min Confidence Threshold */}
                                <div>
                                    <label style={{ display: 'block', marginBottom: '8px', color: '#595959', fontSize: '14px', fontWeight: '600' }}>
                                        Minimum Confidence Threshold (%)
                                    </label>
                                    <Input
                                        type="number"
                                        value={minConfidenceThreshold}
                                        onChange={(e) => setMinConfidenceThreshold(Number(e.target.value))}
                                        min={0}
                                        max={100}
                                        style={{ width: '100%' }}
                                    />
                                    <div style={{ marginTop: '4px', color: '#8c8c8c', fontSize: '12px' }}>
                                        Only show correlations with confidence {'>='} this value (0-100%). Higher = more selective.
                                    </div>
                                </div>

                                {/* Max Correlations */}
                                <div>
                                    <label style={{ display: 'block', marginBottom: '8px', color: '#595959', fontSize: '14px', fontWeight: '600' }}>
                                        Maximum Correlations
                                    </label>
                                    <Input
                                        type="number"
                                        value={maxCorrelations}
                                        onChange={(e) => setMaxCorrelations(Number(e.target.value))}
                                        min={1}
                                        max={50}
                                        style={{ width: '100%' }}
                                    />
                                    <div style={{ marginTop: '4px', color: '#8c8c8c', fontSize: '12px' }}>
                                        Maximum number of correlation suggestions to return (1-50).
                                    </div>
                                </div>
                            </div>

                            <div style={{ marginTop: '24px' }}>
                                <button
                                    onClick={handleSaveLLMOptimizations}
                                    disabled={isSavingOptimizations}
                                    style={{
                                        padding: '10px 24px',
                                        fontSize: '14px',
                                        fontWeight: '600',
                                        border: '2px solid #10b981',
                                        backgroundColor: '#10b981',
                                        color: 'white',
                                        borderRadius: '6px',
                                        cursor: isSavingOptimizations ? 'not-allowed' : 'pointer',
                                        opacity: isSavingOptimizations ? 0.6 : 1,
                                        transition: 'all 0.3s ease'
                                    }}
                                    onMouseEnter={(e) => {
                                        if (!isSavingOptimizations) {
                                            e.currentTarget.style.backgroundColor = '#059669';
                                            e.currentTarget.style.borderColor = '#059669';
                                        }
                                    }}
                                    onMouseLeave={(e) => {
                                        if (!isSavingOptimizations) {
                                            e.currentTarget.style.backgroundColor = '#10b981';
                                            e.currentTarget.style.borderColor = '#10b981';
                                        }
                                    }}
                                >
                                    {isSavingOptimizations ? 'Saving...' : 'Save Settings'}
                                </button>
                            </div>

                            <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#eff6ff', borderRadius: '6px', border: '1px solid #bfdbfe' }}>
                                <h4 style={{ margin: '0 0 12px 0', color: '#1e40af', fontSize: '14px', fontWeight: '600' }}>💡 Optimization Tips:</h4>
                                <ul style={{ margin: 0, paddingLeft: '20px', color: '#1e40af', fontSize: '14px', lineHeight: '1.6' }}>
                                    <li><strong>Performance:</strong> Reduce max questions and timeout for faster results</li>
                                    <li><strong>Accuracy:</strong> Increase confidence threshold for higher quality suggestions</li>
                                    <li><strong>Coverage:</strong> Increase max questions to analyze more of your frameworks</li>
                                    <li><strong>Suggestions:</strong> Increase max correlations to get more options to review</li>
                                </ul>
                            </div>
                        </div>
                    )}

                    {/* AI Suggestions Results Section */}
                    <div className="page-section">
                        <h3 className="section-title">AI Correlation Suggestions</h3>

                        {aiLoading && (
                            <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f0f8ff', border: '1px solid #0f386a', borderRadius: '6px' }}>
                                <p style={{ margin: 0, color: '#0f386a', fontSize: '14px' }}>
                                    ⏳ Generating AI suggestions... This may take several minutes depending on the number of questions.
                                </p>
                            </div>
                        )}

                        <div style={{
                            minHeight: '300px',
                            padding: '16px',
                            border: '1px solid #e8e8e8',
                            borderRadius: '6px',
                            backgroundColor: '#fafafa',
                            marginTop: '16px'
                        }}>
                            {!aiSuggestions || aiSuggestions.suggestions.length === 0 ? (
                                <div style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    height: '268px',
                                    color: '#8c8c8c',
                                    textAlign: 'center'
                                }}>
                                    <p style={{ fontSize: '16px', marginBottom: '8px' }}>No correlation suggestions yet</p>
                                    <p style={{ fontSize: '14px' }}>Click "Find Correlations with AI" above to generate suggestions</p>
                                </div>
                            ) : (
                                <div>
                                    <p style={{ marginBottom: '16px', color: '#595959', backgroundColor: 'white', padding: '12px', borderRadius: '6px' }}>
                                        Found <strong>{aiSuggestions.suggestions.length}</strong> correlation suggestions between <strong>{aiSuggestions.framework_a_name}</strong> and <strong>{aiSuggestions.framework_b_name}</strong>. Review and apply the ones you agree with.
                                    </p>
                                    <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
                                        {aiSuggestions.suggestions.map((suggestion) => (
                                            <Card
                                                key={`${suggestion.question_a_id}-${suggestion.question_b_id}`}
                                                style={{ marginBottom: '16px' }}
                                                styles={{ body: { padding: '16px' } }}
                                            >
                                                <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start' }}>
                                                    {/* Confidence Badge */}
                                                    <div style={{
                                                        minWidth: '60px',
                                                        textAlign: 'center',
                                                        padding: '8px',
                                                        backgroundColor: suggestion.confidence >= 80 ? '#d1fae5' : suggestion.confidence >= 60 ? '#fef3c7' : '#fee2e2',
                                                        color: suggestion.confidence >= 80 ? '#065f46' : suggestion.confidence >= 60 ? '#92400e' : '#991b1b',
                                                        borderRadius: '8px',
                                                        fontWeight: 'bold',
                                                        fontSize: '16px'
                                                    }}>
                                                        {suggestion.confidence}%
                                                    </div>

                                                    {/* Question Details */}
                                                    <div style={{ flex: 1 }}>
                                                        <div style={{ marginBottom: '12px' }}>
                                                            <div style={{ fontSize: '12px', fontWeight: '600', color: '#1890ff', marginBottom: '4px' }}>
                                                                Framework A Question:
                                                            </div>
                                                            <div style={{ fontSize: '14px', color: '#262626', lineHeight: '1.5' }}>
                                                                {suggestion.question_a_text}
                                                            </div>
                                                        </div>

                                                        <div style={{ marginBottom: '12px' }}>
                                                            <div style={{ fontSize: '12px', fontWeight: '600', color: '#1a365d', marginBottom: '4px' }}>
                                                                Framework B Question:
                                                            </div>
                                                            <div style={{ fontSize: '14px', color: '#262626', lineHeight: '1.5' }}>
                                                                {suggestion.question_b_text}
                                                            </div>
                                                        </div>

                                                        <div style={{ marginBottom: '12px', padding: '12px', backgroundColor: '#fafafa', borderRadius: '6px' }}>
                                                            <div style={{ fontSize: '12px', fontWeight: '600', color: '#595959', marginBottom: '4px' }}>
                                                                AI Reasoning:
                                                            </div>
                                                            <div style={{ fontSize: '13px', color: '#595959', lineHeight: '1.5', fontStyle: 'italic' }}>
                                                                {suggestion.reasoning}
                                                            </div>
                                                        </div>

                                                        {/* Action Buttons */}
                                                        <div style={{ display: 'flex', gap: '8px' }}>
                                                            <button
                                                                onClick={() => handleApplyAISuggestion(suggestion)}
                                                                disabled={applyingCorrelationId === (suggestion.question_a_id + suggestion.question_b_id)}
                                                                style={{
                                                                    padding: '6px 16px',
                                                                    fontSize: '14px',
                                                                    fontWeight: '600',
                                                                    backgroundColor: applyingCorrelationId === (suggestion.question_a_id + suggestion.question_b_id) ? '#d1d5db' : '#10b981',
                                                                    color: 'white',
                                                                    border: 'none',
                                                                    borderRadius: '6px',
                                                                    cursor: applyingCorrelationId === (suggestion.question_a_id + suggestion.question_b_id) ? 'not-allowed' : 'pointer',
                                                                    transition: 'all 0.2s'
                                                                }}
                                                                onMouseEnter={(e) => {
                                                                    if (applyingCorrelationId !== (suggestion.question_a_id + suggestion.question_b_id)) {
                                                                        e.currentTarget.style.backgroundColor = '#059669';
                                                                    }
                                                                }}
                                                                onMouseLeave={(e) => {
                                                                    if (applyingCorrelationId !== (suggestion.question_a_id + suggestion.question_b_id)) {
                                                                        e.currentTarget.style.backgroundColor = '#10b981';
                                                                    }
                                                                }}
                                                            >
                                                                {applyingCorrelationId === (suggestion.question_a_id + suggestion.question_b_id) ? 'Applying...' : '✓ Apply Correlation'}
                                                            </button>
                                                            <button
                                                                onClick={() => handleRejectAISuggestion(suggestion)}
                                                                disabled={applyingCorrelationId === (suggestion.question_a_id + suggestion.question_b_id)}
                                                                style={{
                                                                    padding: '6px 16px',
                                                                    fontSize: '14px',
                                                                    fontWeight: '600',
                                                                    backgroundColor: 'white',
                                                                    color: '#dc2626',
                                                                    border: '1px solid #dc2626',
                                                                    borderRadius: '6px',
                                                                    cursor: applyingCorrelationId === (suggestion.question_a_id + suggestion.question_b_id) ? 'not-allowed' : 'pointer',
                                                                    transition: 'all 0.2s'
                                                                }}
                                                                onMouseEnter={(e) => {
                                                                    if (applyingCorrelationId !== (suggestion.question_a_id + suggestion.question_b_id)) {
                                                                        e.currentTarget.style.backgroundColor = '#fee2e2';
                                                                    }
                                                                }}
                                                                onMouseLeave={(e) => {
                                                                    if (applyingCorrelationId !== (suggestion.question_a_id + suggestion.question_b_id)) {
                                                                        e.currentTarget.style.backgroundColor = 'white';
                                                                    }
                                                                }}
                                                            >
                                                                ✗ Reject
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            </Card>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CorrelationsPage;
