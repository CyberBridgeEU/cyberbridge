// import React from 'react';

import {notification, Select, SelectProps, Spin, Tag, Empty, Progress, Pagination} from "antd";
import Sidebar from "../components/Sidebar.tsx";
import { EditOutlined, LoadingOutlined, CheckCircleOutlined, ClockCircleOutlined, PlusCircleOutlined, FileTextOutlined, ExperimentOutlined, RobotOutlined } from '@ant-design/icons';
import {ChangeEvent, useEffect, useRef, useState} from "react";
import useFrameworksStore from "../store/useFrameworksStore.ts";
import useAssessmentTypesStore from "../store/useAssessmentTypesStore.ts";
import useAssessmentsStore, {
    Answer,
    AnswerUpdateRequest,
    CustomFile,
    FrameworkAndUser,
    FrameworkUserAndAssessmentType
} from "../store/useAssessmentsStore.ts";
import InfoTitle from "../components/InfoTitle.tsx";
import { AssessmentsInfo } from "../constants/infoContent.tsx";
import useUserStore from "../store/useUserStore.ts";
import usePolicyStore from "../store/usePolicyStore.ts";
import useAssetStore from "../store/useAssetStore.ts";
import { useLocation } from 'wouter';
import { useMenuHighlighting } from "../utils/menuUtils.ts";
import {exportToPdf} from "../utils/pdfUtils.ts";
import CorrelationsTooltip from "../components/CorrelationsTooltip.tsx";
import {exportAssessmentToPdf} from "../utils/assessmentPdfUtils.ts";
import {exportAnswersToCSV, parseAnswersFromCSV, validateImportedAnswers} from "../utils/csvUtils.ts";
import ScrollToTopButton from '../components/ScrollToTopButton.tsx';
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";
import useAuthStore from "../store/useAuthStore.ts";
import useCRAFilteredFrameworks from "../hooks/useCRAFilteredFrameworks.ts";
import ScanSuggestionsDrawer from "../components/ScanSuggestionsDrawer.tsx";
import AISuggestionsDrawer from "../components/AISuggestionsDrawer.tsx";

const AssessmentsPage = () => {
    const [location] = useLocation();
    const menuHighlighting = useMenuHighlighting(location);

    //Global State
    const {fetchFrameworks, frameworks} = useFrameworksStore();
    const {assessmentTypes, fetchAssessmentTypes} = useAssessmentTypesStore();
    const {fetchAssessmentsForFrameworkAndUser, fetchAssessmentsForFrameworkUserAndAssessmentType, assessments, createAssessment, error, fetchAssessmentAnswers, answers, updateAnswerLocally, updateAnswerPermanently, clearAnswers, deleteAssessment, removeAssessmentFromState, deleteAnswerPermanently, downloadZip} = useAssessmentsStore();
    const {fetchCurrentUser, current_user, organisations, fetchOrganisations} = useUserStore();
    const {fetchPolicies, policies} = usePolicyStore();
    const {fetchAssets, assets} = useAssetStore();
    const { filteredFrameworks, craFrameworkId, isCRAModeActive } = useCRAFilteredFrameworks();

    //Local State
    const [api, contextHolder] = notification.useNotification();
    const [assessmentName, setAssessmentName] = useState<string>('');
    const [assessmentDropdownIsDisabled, setassessmentDropdownIsDisabled] = useState<boolean>(true);
    const [currentFrameworkId, setCurrentFrameworkId] = useState<string>('');
    const [selectedAssessment, setSelectedAssessment] = useState<string | undefined>(undefined);
    const [selectedAssessmentType, setSelectedAssessmentType] = useState<string>('');
    const [showElement, setShowElement] = useState<boolean>(true);
    const [isImporting, setIsImporting] = useState<boolean>(false);
    const [allUserAssessments, setAllUserAssessments] = useState<any[]>([]);
    const [showCreateForm, setShowCreateForm] = useState<boolean>(false);
    const [currentPage, setCurrentPage] = useState<number>(1);
    const questionsPerPage = 10;
    const [scanSuggestDrawerOpen, setScanSuggestDrawerOpen] = useState<boolean>(false);
    const [aiSuggestDrawerOpen, setAiSuggestDrawerOpen] = useState<boolean>(false);

    // Scope-related state
    const [scopeTypes, setScopeTypes] = useState<Array<{id: string, scope_name: string}>>([]);
    const [selectedScopeType, setSelectedScopeType] = useState<string>('');
    const [selectedScopeEntityId, setSelectedScopeEntityId] = useState<string>('');
    const [frameworkScopeConfig, setFrameworkScopeConfig] = useState<{
        allowed_scope_types: string[];
        scope_selection_mode: string;
        supported_scope_types: string[];
    } | null>(null);

    //Constants
    const framework_options = filteredFrameworks.map(framework => ({
        value:framework.id,
        label: framework.organisation_domain ? `${framework.name}(${framework.organisation_domain})` : framework.name
    }));

    const assessmentType_options = assessmentTypes.map(assessmentType => ({
        value: assessmentType.id,
        label: assessmentType.type_name.charAt(0).toUpperCase() + assessmentType.type_name.slice(1),
    }));

    const assessment_options = assessments.map(assessment => ({
        value:assessment.id,
        label: assessment.name
    }));

    // Filter policies by current framework - only show policies linked to the selected framework
    const filteredPolicies = currentFrameworkId
        ? policies.filter(policy => {
            console.log('DEBUG: Checking policy', policy.title, 'frameworks:', policy.frameworks, 'against frameworkId:', currentFrameworkId);
            return policy.frameworks && policy.frameworks.includes(currentFrameworkId);
        })
        : [];

    console.log('DEBUG: currentFrameworkId:', currentFrameworkId);
    console.log('DEBUG: All policies count:', policies.length);
    console.log('DEBUG: Filtered policies count:', filteredPolicies.length);

    const policy_options = filteredPolicies.map(policy => ({
        value: policy.id,
        label: policy.title
    }));

    const getScopeLabel = (scopeName: string) => (
        scopeName === 'Product' || scopeName === 'Asset' ? 'Asset / Product' : scopeName
    );

    const buildScopeTypeOptions = (types: Array<{id: string; scope_name: string}>) => {
        const hasProduct = types.some(scopeType => scopeType.scope_name === 'Product');
        return types
            .filter(scopeType => !(scopeType.scope_name === 'Asset' && hasProduct))
            .map(scopeType => ({
                value: scopeType.scope_name,
                label: getScopeLabel(scopeType.scope_name)
            }));
    };

    const formatAssetLabel = (asset: { name: string; version: string | null; asset_type_name: string | null }) => {
        const versionLabel = asset.version ? ` v${asset.version}` : '';
        const typeLabel = asset.asset_type_name ? ` (${asset.asset_type_name})` : '';
        return `${asset.name}${versionLabel}${typeLabel}`;
    };

    // Scope type options - show all scope types, or filtered based on framework configuration
    const scope_type_options = frameworkScopeConfig && frameworkScopeConfig.allowed_scope_types && frameworkScopeConfig.allowed_scope_types.length > 0
        ? buildScopeTypeOptions(
            scopeTypes.filter(st => frameworkScopeConfig.allowed_scope_types.includes(st.scope_name))
        )
        : buildScopeTypeOptions(scopeTypes);

    // Scope entity options - depends on selected scope type
    const scope_entity_options = selectedScopeType === 'Product' || selectedScopeType === 'Asset'
        ? assets.map(asset => ({
            value: asset.id,
            label: formatAssetLabel(asset)
        }))
        : selectedScopeType === 'Organization'
        ? organisations.map(org => ({
            value: org.id || '',
            label: org.name
        }))
        : [];

    const exportToPdfRef = useRef<HTMLDivElement>(null);

    //On Component Mount -> YOU SHOULD FETCH FRAMEWORKS AND ASSESSMENTS FROM BACKEND ONLY ON PAGE REFRESH. LOAD THEM FROM THE APP LAUNCH! NOT HERE
    useEffect(() => {
        // fetchCurrentUser() is now handled by ProtectedRoute component
        fetchFrameworks();
        fetchAssessmentTypes();
        fetchPolicies();
        fetchAssets();
        fetchOrganisations();
        clearAnswers();

        // Fetch available scope types
        const fetchScopeTypes = async () => {
            try {
                const response = await fetch(`${cyberbridge_back_end_rest_api}/scopes/`, {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    setScopeTypes(data);
                }
            } catch (error) {
                console.error('Error fetching scope types:', error);
            }
        };
        fetchScopeTypes();
    }, []);

    // Fetch all user assessments for overview
    useEffect(() => {
        const fetchAllUserAssessments = async () => {
            if (!current_user?.id) {
                console.log('No current_user.id available yet');
                return;
            }
            console.log('Fetching assessments for user:', current_user.id);
            try {
                const response = await fetch(`${cyberbridge_back_end_rest_api}/assessments/user/${current_user.id}`, {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                });
                console.log('Assessment fetch response status:', response.status);
                if (response.ok) {
                    const data = await response.json();
                    console.log('Fetched assessments:', data);
                    setAllUserAssessments(data);
                } else {
                    const errorText = await response.text();
                    console.error('Failed to fetch assessments:', response.status, errorText);
                }
            } catch (error) {
                console.error('Error fetching user assessments:', error);
            }
        };
        fetchAllUserAssessments();
    }, [current_user?.id]);

    useEffect(() => {
        if (!currentFrameworkId || currentFrameworkId.length === 0 ||
            !selectedAssessmentType || selectedAssessmentType.length === 0 ||
            !assessments || assessments.length === 0) {
            setassessmentDropdownIsDisabled(true);
        } else {
            setassessmentDropdownIsDisabled(false);
        }
    }, [currentFrameworkId, selectedAssessmentType, assessments]);

    // Fetch framework scope configuration when framework changes
    useEffect(() => {
        if (currentFrameworkId) {
            const fetchFrameworkScopeConfig = async () => {
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/${currentFrameworkId}/scope-config`, {
                        headers: {
                            ...useAuthStore.getState().getAuthHeader()
                        }
                    });
                    if (response.ok) {
                        const data = await response.json();
                        setFrameworkScopeConfig(data);

                        // Reset scope selection when framework changes
                        setSelectedScopeType('');
                        setSelectedScopeEntityId('');
                    }
                } catch (error) {
                    console.error('Error fetching framework scope config:', error);
                }
            };
            fetchFrameworkScopeConfig();
        } else {
            setFrameworkScopeConfig(null);
            setSelectedScopeType('');
            setSelectedScopeEntityId('');
        }
    }, [currentFrameworkId]);

    //Component Functions
    const filterOption: SelectProps['filterOption'] = (input, option) =>
        (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase());

    // Get scope display text for selected assessment
    const getScopeDisplayText = () => {
        if (!selectedAssessment) return '';

        const assessment = assessments.find(a => a.id === selectedAssessment);
        if (!assessment || !assessment.scope_name) return '';

        // If scope_display_name exists, show "ScopeType: DisplayName"
        // Otherwise just show "ScopeType"
        if (assessment.scope_display_name) {
            return `${getScopeLabel(assessment.scope_name)}: ${assessment.scope_display_name}`;
        }
        return getScopeLabel(assessment.scope_name);
    };

    const onAssessmentChange = async (value: string) => {
        console.log(`assessment id : ${value}`);
        // clearAnswers();
        setSelectedAssessment(value);
        setCurrentPage(1);
        const success = await fetchAssessmentAnswers(value);
        if (!success) {
            api.error({message: 'Answers fetching Failed', description: 'Api not responding...' + error, duration: 4,})
        }
    };

    const onFrameworkChange = async (value: string) => {
        // console.log(`framework id : ${value}`);
        setCurrentFrameworkId(value);
        //clear assessments and questions
        setSelectedAssessment(undefined);
        // clearAssessments();
        clearAnswers();

        if (selectedAssessmentType) {
            // If assessment type is selected, fetch filtered assessments
            const request: FrameworkUserAndAssessmentType = {
                framework_id: value,
                user_id: current_user.id,
                assessment_type_id: selectedAssessmentType
            }
            await fetchAssessmentsForFrameworkUserAndAssessmentType(request);
        } else {
            // Otherwise, fetch all assessments for framework
            const request: FrameworkAndUser = {
                framework_id: value,
                user_id: current_user.id,
            }
            await fetchAssessmentsForFrameworkAndUser(request);
        }
    }

    // Auto-select CRA framework when CRA mode is active
    useEffect(() => {
        if (isCRAModeActive && craFrameworkId && !currentFrameworkId) {
            onFrameworkChange(craFrameworkId);
        }
    }, [isCRAModeActive, craFrameworkId]);

    const onAssessmentTypeChange = async (value: string) => {
        setSelectedAssessmentType(value);
        //clear assessments and questions
        setSelectedAssessment(undefined);
        clearAnswers();

        if (currentFrameworkId) {
            // If framework is selected, fetch filtered assessments
            const request: FrameworkUserAndAssessmentType = {
                framework_id: currentFrameworkId,
                user_id: current_user.id,
                assessment_type_id: value
            }
            await fetchAssessmentsForFrameworkUserAndAssessmentType(request);
        }
    }

    const onCreateAssessment = async () => {
        if (!assessmentName || assessmentName.trim() === '' || !currentFrameworkId || currentFrameworkId.trim() === '' || !selectedAssessmentType || selectedAssessmentType.trim() === '' || !current_user || !current_user.id || current_user.id.trim() === '') {
            api.error({message: 'Invalid Assessment Data', description: 'Assessment must include Name, Framework, Assessment Type and User!', duration: 4,})
            return;
        }

        // Validate scope requirements based on framework configuration
        if (frameworkScopeConfig) {
            if (frameworkScopeConfig.scope_selection_mode === 'required') {
                if (!selectedScopeType || selectedScopeType.trim() === '') {
                    api.error({message: 'Scope Required', description: 'This framework requires a scope to be selected.', duration: 4,})
                    return;
                }
                // For Asset / Product and Organization scope types, entity ID is required
                if ((selectedScopeType === 'Product' || selectedScopeType === 'Asset' || selectedScopeType === 'Organization') &&
                    (!selectedScopeEntityId || selectedScopeEntityId.trim() === '')) {
                    api.error({
                        message: 'Scope Entity Required',
                        description: `Please select a ${getScopeLabel(selectedScopeType)} for this assessment.`,
                        duration: 4,
                    })
                    return;
                }
            }
        }

        const newAssessment = {
            name: assessmentName,
            framework_id: currentFrameworkId,
            user_id: current_user.id,
            assessment_type_id: selectedAssessmentType,
            progress: 0,
            status: 'in progress',
            scope_name: selectedScopeType || undefined,
            scope_entity_id: selectedScopeType === 'Other' ? undefined : (selectedScopeEntityId || undefined)
        }
        const success = await createAssessment(newAssessment)
        if (success) {
            api.success({message: 'Assessment Creation Success', description: 'Assessment created.', duration: 4,})
            setAssessmentName('');
            setSelectedScopeType('');
            setSelectedScopeEntityId('');
        }else{
            api.error({message: 'Assessment Creation Failed', description: 'Api not responding...' + error, duration: 4,})
        }

    }

    const saveAnswer = async (answerId: string, answerValue: string | null, files: File[] | null) => {
        console.log(answerId, answerValue, files);
        // Find the current answer to get its policy_id and evidence_description
        const currentAnswer = answers.find(answer => answer.answer_id === answerId);
        const ans: AnswerUpdateRequest = {
            answer_id: answerId,
            answer_value: answerValue,
            files: files,
            policy_id: currentAnswer?.policy_id || null,
            evidence_description: currentAnswer?.evidence_description || null
        };
        const success = await updateAnswerPermanently(ans);
        if (!success) {
            api.error({message: 'Answer Update Failed', description: 'Save Answer Failed!' + error, duration: 4,})
        }else {
            api.success({message: 'Answer Update Success', description: 'Answer updated.', duration: 4,})
        }
    };

    const clearAnswer = async (questionId: string, answerId: string) => {
        const success = await deleteAnswerPermanently(answerId);
        if (!success) {
            api.error({message: 'Answer Cleared Failed', description: 'Clear Answer Failed!' + error, duration: 4,})
        }else {
            // Clear both answer value, files, and policy assignment
            updateAnswerLocally(questionId, null, null, null);
            api.success({message: 'Answer Cleared Success', description: 'Answer Cleared.', duration: 4,})
        }
    }

    const handleApplyScanSuggestion = async (questionId: string, answerValue: string, evidenceDescription: string) => {
        const currentAnswer = answers.find(a => a.question_id === questionId);
        if (!currentAnswer) return;

        updateAnswerLocally(questionId, answerValue, null, null, evidenceDescription);

        const ans: AnswerUpdateRequest = {
            answer_id: currentAnswer.answer_id,
            answer_value: answerValue,
            files: null,
            policy_id: currentAnswer.policy_id || null,
            evidence_description: evidenceDescription,
        };
        const success = await updateAnswerPermanently(ans);
        if (success) {
            api.success({ message: 'Suggestion Applied', description: `Answer set to "${answerValue}" with scan evidence.`, duration: 3 });
        } else {
            api.error({ message: 'Failed to Apply', description: 'Could not save the suggested answer.', duration: 4 });
        }
    };

    // const saveAssessment = async () => {
    //     const success = await saveAssessmentAnswers();
    //     if (!success) {
    //         api.error({message: 'Assessment Update Failed', description: 'Api not responding...' + error, duration: 4,})
    //     }else {
    //         api.success({message: 'Assessment Update Success', description: 'Assessment updated.', duration: 4,})
    //     }
    // }

    const deleteAssessmentAndAnswers = async () => {
        if (!selectedAssessment) {
            api.error({message: 'Invalid Assessment', description: 'Please select an assessment to delete!', duration: 4,});
            return;
        }

        // Use native browser confirm - guaranteed to work regardless of React version
        const confirmed = window.confirm('This action will delete the selected assessment and its answers with all uploaded files! Do you want to proceed?');

        if (confirmed) {
            const success = await deleteAssessment(selectedAssessment);
            if (!success) {
                api.error({message: 'Assessment Deletion Failed', description: 'Api not responding...' + error, duration: 4,});
            } else {
                setSelectedAssessment(undefined);
                removeAssessmentFromState(selectedAssessment);
                clearAnswers();
                api.success({message: 'Assessment Deletion Success', description: 'Assessment deleted.', duration: 4,});
            }
        } else {
            console.log('Deletion cancelled');
        }
    };

    const attachFilesToAnswer = (e: ChangeEvent<HTMLInputElement>, question_id: string) => {
        const files = e.target.files;
        if (files) {
            // Get the current answer value for this question
            const answer = answers.find(a => a.question_id === question_id);
            const currentValue = answer ? answer.answer_value : null;

            // Update the answer with both the current value and new files
            updateAnswerLocally(question_id, currentValue, Array.from(files));
        }
    };

    const downloadAnswerFilesAsZip = async (files: CustomFile[] | null) => {
        if (!files || files.length === 0 || files.some(file => !file.id)){
            api.error({message: 'Download Files Failed!', description: 'There are no files or file(s) id missing!' + error, duration: 4,})
            return;
        }
        const fileIds = files.map(file => file.id);
        console.log('fileIds: ' + fileIds);

        const success = await downloadZip(fileIds);
        if (!success) {
            api.error({message: 'Assessment Update Failed', description: 'Api not responding...' + error, duration: 4,})
        }else {
            api.success({message: 'Assessment Update Success', description: 'Assessment updated.', duration: 4,})
        }
    }

    const onPolicyChange = (questionId: string, policyId: string | null) => {
        // Convert empty string to null for backend consistency
        const actualPolicyId = policyId === '' ? null : policyId;

        // Validate cross-organization assignment for super_admin
        if (actualPolicyId && current_user && current_user.role_name === 'super_admin') {
            const selectedPolicy = policies.find(p => p.id === actualPolicyId);
            if (selectedPolicy) {
                // Compare organization domains instead of IDs
                const policyDomain = selectedPolicy.organisation_name; // Policy has organisation_name not domain
                const userDomain = current_user.organisation_domain;

                // For policies, we need to compare organization names since policies don't have domain field
                const userOrgName = current_user.organisation_name;
                const policyOrgId = selectedPolicy.organisation_id;

                if (policyOrgId && current_user.organisation_id && policyOrgId !== current_user.organisation_id) {
                    api.warning({
                        message: 'Cross-Organization Assignment Blocked',
                        description: `Policy "${selectedPolicy.title}" belongs to a different organization. This assignment can cause data integrity issues and has been prevented.`,
                        duration: 4,
                    });
                    // Prevent the assignment by not updating the answer
                    return;
                }
            }
        }

        // Update the local answer with the selected policy
        updateAnswerLocally(questionId, undefined, undefined, actualPolicyId);
    }

    const hideElements = () => {
        setShowElement(!showElement);
    }

    const clearFormFields = () => {
        setAssessmentName('');
        setCurrentFrameworkId('');
        setSelectedAssessment(undefined);
        setSelectedAssessmentType('');
        setassessmentDropdownIsDisabled(true);
        setSelectedScopeType('');
        setSelectedScopeEntityId('');
        setFrameworkScopeConfig(null);
    }

    const handleExportToPdf = async () => {
        if (!selectedAssessment || answers.length === 0) {
            api.error({
                message: 'Export Failed',
                description: 'Please select an assessment with answers to export.',
                duration: 4,
            });
            return;
        }

        try {
            const assessment = assessments.find(a => a.id === selectedAssessment);
            const framework = frameworks.find(f => f.id === currentFrameworkId);
            const assessmentType = assessmentTypes.find(at => at.id === selectedAssessmentType);

            await exportAssessmentToPdf(
                answers,
                assessment?.name || 'Assessment',
                framework?.name || 'Framework',
                assessmentType?.type_name || 'Assessment',
                `assessment-${assessment?.name || 'report'}`
            );

            api.success({
                message: 'Export Success',
                description: 'Assessment has been exported to PDF successfully.',
                duration: 4,
            });
        } catch (error) {
            console.error('PDF export error:', error);
            api.error({
                message: 'Export Failed',
                description: 'Failed to export assessment to PDF. Please try again.',
                duration: 4,
            });
        }
    }

    const handleExportToCSV = () => {
        if (!selectedAssessment || answers.length === 0) {
            api.error({
                message: 'Export Failed',
                description: 'Please select an assessment with answers to export.',
                duration: 4,
            });
            return;
        }

        if (!currentFrameworkId || !selectedAssessmentType) {
            api.error({
                message: 'Export Failed',
                description: 'Framework or assessment type is missing.',
                duration: 4,
            });
            return;
        }

        try {
            const assessment = assessments.find(a => a.id === selectedAssessment);
            exportAnswersToCSV(
                answers,
                assessment?.name || 'assessment',
                currentFrameworkId,
                selectedAssessmentType
            );

            api.success({
                message: 'Export Success',
                description: 'Answers have been exported to CSV successfully.',
                duration: 4,
            });
        } catch (error) {
            console.error('CSV export error:', error);
            api.error({
                message: 'Export Failed',
                description: 'Failed to export answers to CSV. Please try again.',
                duration: 4,
            });
        }
    }

    const handleImportFromCSV = async (event: ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        if (!selectedAssessment) {
            api.error({
                message: 'Import Failed',
                description: 'Please select an assessment first.',
                duration: 4,
            });
            event.target.value = '';
            return;
        }

        if (!currentFrameworkId || !selectedAssessmentType) {
            api.error({
                message: 'Import Failed',
                description: 'Framework or assessment type is missing.',
                duration: 4,
            });
            event.target.value = '';
            return;
        }

        setIsImporting(true);

        try {
            // Parse CSV file
            const importedAnswers = await parseAnswersFromCSV(file);

            // Validate imported answers
            const { validAnswers, errors } = validateImportedAnswers(
                importedAnswers,
                answers,
                currentFrameworkId,
                selectedAssessmentType
            );

            if (errors.length > 0) {
                api.error({
                    message: 'Import Validation Failed',
                    description: (
                        <div>
                            <p>Found {errors.length} error(s):</p>
                            <ul style={{ maxHeight: '200px', overflow: 'auto', paddingLeft: '20px' }}>
                                {errors.slice(0, 5).map((err, idx) => (
                                    <li key={idx}>{err}</li>
                                ))}
                                {errors.length > 5 && <li>...and {errors.length - 5} more errors</li>}
                            </ul>
                        </div>
                    ),
                    duration: 10,
                });
                setIsImporting(false);
                event.target.value = '';
                return;
            }

            if (validAnswers.length === 0) {
                api.warning({
                    message: 'No Valid Answers',
                    description: 'No valid answers found in the CSV file.',
                    duration: 4,
                });
                setIsImporting(false);
                event.target.value = '';
                return;
            }

            // Update answers via API using updateAnswerPermanently to trigger synchronization
            let successCount = 0;
            let failCount = 0;

            for (const answer of validAnswers) {
                // First update locally (only answer value, no policies)
                updateAnswerLocally(answer.question_id, answer.answer_value, null, null);

                // Then save permanently (this triggers synchronization for correlated questions)
                const updateRequest: AnswerUpdateRequest = {
                    answer_id: answer.answer_id,
                    answer_value: answer.answer_value,
                    policy_id: undefined,
                    files: null
                };

                const success = await updateAnswerPermanently(updateRequest);
                if (success) {
                    successCount++;
                } else {
                    failCount++;
                }
            }

            // Refresh answers to get the synchronized values
            await fetchAssessmentAnswers(selectedAssessment);

            if (failCount === 0) {
                api.success({
                    message: 'Import Success',
                    description: `Successfully imported ${successCount} answer(s).`,
                    duration: 4,
                });
            } else {
                api.warning({
                    message: 'Import Partially Successful',
                    description: `Imported ${successCount} answer(s), failed ${failCount} answer(s).`,
                    duration: 6,
                });
            }
        } catch (error) {
            console.error('CSV import error:', error);
            api.error({
                message: 'Import Failed',
                description: error instanceof Error ? error.message : 'Failed to import answers from CSV.',
                duration: 6,
            });
        } finally {
            setIsImporting(false);
            // Clear file input
            event.target.value = '';
        }
    }

    return (
        <div>
            {/* Add the notification context holder at the top level */}
            {contextHolder}
            <ScrollToTopButton />
            <div className={'page-parent'}>
                <Sidebar
                    selectedKeys={menuHighlighting.selectedKeys}
                    openKeys={menuHighlighting.openKeys}
                    onOpenChange={menuHighlighting.onOpenChange}
                />

                <div className={'page-content'} ref={exportToPdfRef}>
                    {/* Page Header */}
                    <div className="page-header">
                        <div className="page-header-left">
                            <EditOutlined style={{ fontSize: 22, color: '#0f386a' }} />
                            <InfoTitle
                                title="Assessments"
                                infoContent={AssessmentsInfo}
                                className="page-title"
                            />
                        </div>
                        {showElement && (
                            <div className="page-header-right">
                                <button
                                    className="export-button"
                                    onClick={handleExportToPdf}
                                    disabled={!selectedAssessment || answers.length === 0}
                                    style={{
                                        fontSize: '13px',
                                        padding: '6px 12px',
                                        height: '32px',
                                        opacity: (!selectedAssessment || answers.length === 0) ? 0.5 : 1
                                    }}
                                >
                                    Export PDF
                                </button>
                                <button
                                    className="secondary-button"
                                    onClick={handleExportToCSV}
                                    disabled={!selectedAssessment || answers.length === 0}
                                    style={{
                                        fontSize: '13px',
                                        padding: '6px 12px',
                                        height: '32px',
                                        backgroundColor: '#10b981',
                                        borderColor: '#10b981',
                                        color: 'white',
                                        opacity: (!selectedAssessment || answers.length === 0) ? 0.5 : 1
                                    }}
                                >
                                    Export CSV
                                </button>
                                <button
                                    className="secondary-button"
                                    onClick={() => document.getElementById('csv-import')?.click()}
                                    disabled={!selectedAssessment || isImporting}
                                    style={{
                                        fontSize: '13px',
                                        padding: '6px 12px',
                                        height: '32px',
                                        backgroundColor: '#f59e0b',
                                        borderColor: '#f59e0b',
                                        color: 'white',
                                        opacity: (!selectedAssessment || isImporting) ? 0.5 : 1,
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}
                                >
                                    {isImporting && <Spin indicator={<LoadingOutlined style={{ fontSize: 14, color: 'white' }} spin />} />}
                                    {isImporting ? 'Importing...' : 'Import CSV'}
                                </button>
                                <input
                                    id="csv-import"
                                    type="file"
                                    accept=".csv"
                                    onChange={handleImportFromCSV}
                                    disabled={!selectedAssessment || isImporting}
                                    style={{ display: 'none' }}
                                />
                                <button
                                    onClick={() => setScanSuggestDrawerOpen(true)}
                                    disabled={!selectedAssessment}
                                    style={{
                                        fontSize: '13px',
                                        padding: '6px 12px',
                                        height: '32px',
                                        backgroundColor: '#8b5cf6',
                                        borderColor: '#8b5cf6',
                                        color: 'white',
                                        border: '1px solid #8b5cf6',
                                        borderRadius: '6px',
                                        cursor: selectedAssessment ? 'pointer' : 'not-allowed',
                                        opacity: !selectedAssessment ? 0.5 : 1,
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}
                                >
                                    <ExperimentOutlined />
                                    Suggest from Scans
                                </button>
                                <button
                                    onClick={() => setAiSuggestDrawerOpen(true)}
                                    disabled={!selectedAssessment}
                                    style={{
                                        fontSize: '13px',
                                        padding: '6px 12px',
                                        height: '32px',
                                        backgroundColor: '#06b6d4',
                                        borderColor: '#06b6d4',
                                        color: 'white',
                                        border: '1px solid #06b6d4',
                                        borderRadius: '6px',
                                        cursor: selectedAssessment ? 'pointer' : 'not-allowed',
                                        opacity: !selectedAssessment ? 0.5 : 1,
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px'
                                    }}
                                >
                                    <RobotOutlined />
                                    AI Suggest Answers
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Assessment Overview Section */}
                    <div className="page-section">
                        <h3 className="section-title">Assessment Overview</h3>
                        <p className="section-subtitle">
                            View your active assessments or create new ones
                        </p>

                        {/* Two-column layout for Active and Create New */}
                        <div className="assessment-overview-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginTop: '16px' }}>
                            {/* Active Assessments Column */}
                            <div className="assessment-overview-card assessment-overview-card--active" style={{
                                borderRadius: '8px',
                                padding: '20px'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                                    <CheckCircleOutlined style={{ fontSize: '20px', color: '#52c41a' }} />
                                    <h4 className="assessment-overview-card-title" style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>
                                        Active Assessments
                                    </h4>
                                    <Tag color="green" style={{ marginLeft: 'auto' }}>
                                        {allUserAssessments.filter(a => !a.completed_at).length}
                                    </Tag>
                                </div>
                                <p className="assessment-overview-card-subtitle" style={{ fontSize: '13px', marginBottom: '12px' }}>
                                    Assessments currently in progress
                                </p>
                                <div style={{ maxHeight: '250px', overflowY: 'auto' }}>
                                    {allUserAssessments.filter(a => !a.completed_at).length > 0 ? (
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                            {allUserAssessments
                                                .filter(a => !a.completed_at)
                                                .map(assessment => {
                                                    const framework = frameworks.find(f => f.id === assessment.framework_id);
                                                    return (
                                                        <div
                                                            key={assessment.id}
                                                            className={`assessment-entry-card ${selectedAssessment === assessment.id ? 'is-selected' : ''}`}
                                                            style={{
                                                                display: 'flex',
                                                                flexDirection: 'column',
                                                                gap: '8px',
                                                                padding: '12px',
                                                                borderRadius: '6px',
                                                                border: selectedAssessment === assessment.id ? '2px solid #52c41a' : '1px solid var(--assessment-active-item-border, #d9f7be)',
                                                                cursor: 'pointer',
                                                                transition: 'all 0.2s ease'
                                                            }}
                                                            onClick={async () => {
                                                                setCurrentFrameworkId(assessment.framework_id);
                                                                setSelectedAssessmentType(assessment.assessment_type_id || '');
                                                                // Fetch assessments for this framework/type
                                                                if (assessment.assessment_type_id) {
                                                                    const request: FrameworkUserAndAssessmentType = {
                                                                        framework_id: assessment.framework_id,
                                                                        user_id: current_user.id,
                                                                        assessment_type_id: assessment.assessment_type_id
                                                                    };
                                                                    await fetchAssessmentsForFrameworkUserAndAssessmentType(request);
                                                                }
                                                                setSelectedAssessment(assessment.id);
                                                                await fetchAssessmentAnswers(assessment.id);
                                                            }}
                                                            onMouseEnter={(e) => {
                                                                if (selectedAssessment !== assessment.id) {
                                                                    e.currentTarget.style.borderColor = '#52c41a';
                                                                    e.currentTarget.style.boxShadow = 'var(--assessment-active-item-hover-shadow, 0 2px 8px rgba(82, 196, 26, 0.15))';
                                                                }
                                                            }}
                                                            onMouseLeave={(e) => {
                                                                if (selectedAssessment !== assessment.id) {
                                                                    e.currentTarget.style.borderColor = 'var(--assessment-active-item-border, #d9f7be)';
                                                                    e.currentTarget.style.boxShadow = 'none';
                                                                }
                                                            }}
                                                        >
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                                                <FileTextOutlined style={{ color: '#52c41a' }} />
                                                                <span style={{ fontWeight: 500, color: 'var(--text-charcoal)', flex: 1 }}>{assessment.name}</span>
                                                                {selectedAssessment === assessment.id && (
                                                                    <Tag color="green" style={{ fontSize: '11px' }}>Selected</Tag>
                                                                )}
                                                            </div>
                                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text-dark-gray)' }}>
                                                                <span>{framework?.name || 'Unknown Framework'}</span>
                                                                {assessment.scope_name && (
                                                                    <>
                                                                        <span>•</span>
                                                                        <span>{assessment.scope_name}{assessment.scope_display_name ? `: ${assessment.scope_display_name}` : ''}</span>
                                                                    </>
                                                                )}
                                                            </div>
                                                            <Progress
                                                                percent={assessment.progress || 0}
                                                                size="small"
                                                                strokeColor="#52c41a"
                                                                style={{ marginBottom: 0 }}
                                                            />
                                                        </div>
                                                    );
                                                })}
                                        </div>
                                    ) : (
                                        <Empty
                                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                                            description="No active assessments"
                                            style={{ margin: '20px 0' }}
                                        />
                                    )}
                                </div>

                                {/* Completed Assessments */}
                                {allUserAssessments.filter(a => a.completed_at).length > 0 && (
                                    <div className="assessment-completed-panel" style={{ marginTop: '16px', paddingTop: '16px' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                                            <ClockCircleOutlined style={{ fontSize: '16px', color: 'var(--text-dark-gray)' }} />
                                            <span style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-dark-gray)' }}>
                                                Completed ({allUserAssessments.filter(a => a.completed_at).length})
                                            </span>
                                        </div>
                                        <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                                {allUserAssessments
                                                    .filter(a => a.completed_at)
                                                    .slice(0, 5)
                                                    .map(assessment => {
                                                        const framework = frameworks.find(f => f.id === assessment.framework_id);
                                                        return (
                                                            <div
                                                                key={assessment.id}
                                                                className="assessment-completed-item"
                                                                style={{
                                                                    display: 'flex',
                                                                    alignItems: 'center',
                                                                    gap: '10px',
                                                                    padding: '8px 12px',
                                                                    borderRadius: '4px',
                                                                    fontSize: '13px',
                                                                    cursor: 'pointer'
                                                                }}
                                                                onClick={async () => {
                                                                    setCurrentFrameworkId(assessment.framework_id);
                                                                    setSelectedAssessmentType(assessment.assessment_type_id || '');
                                                                    if (assessment.assessment_type_id) {
                                                                        const request: FrameworkUserAndAssessmentType = {
                                                                            framework_id: assessment.framework_id,
                                                                            user_id: current_user.id,
                                                                            assessment_type_id: assessment.assessment_type_id
                                                                        };
                                                                        await fetchAssessmentsForFrameworkUserAndAssessmentType(request);
                                                                    }
                                                                    setSelectedAssessment(assessment.id);
                                                                    await fetchAssessmentAnswers(assessment.id);
                                                                }}
                                                            >
                                                                <CheckCircleOutlined style={{ color: '#52c41a' }} />
                                                                <span style={{ flex: 1 }}>{assessment.name}</span>
                                                                <span style={{ color: 'var(--text-dark-gray)', fontSize: '11px' }}>{framework?.name}</span>
                                                            </div>
                                                        );
                                                    })}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Create New Assessment Column */}
                            <div className="assessment-overview-card assessment-overview-card--create" data-tour-id="qs-assessment-create-card" style={{
                                borderRadius: '8px',
                                padding: '20px'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                                    <PlusCircleOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                                    <h4 className="assessment-overview-card-title" style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>
                                        Create New Assessment
                                    </h4>
                                </div>
                                <p className="assessment-overview-card-subtitle" style={{ fontSize: '13px', marginBottom: '16px' }}>
                                    Start a new assessment for a framework
                                </p>

                                {!showCreateForm ? (
                                    <button
                                        className="add-button"
                                        onClick={() => setShowCreateForm(true)}
                                        style={{ width: '100%', height: '44px' }}
                                    >
                                        + New Assessment
                                    </button>
                                ) : (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                        <div>
                                            <label className="form-label" style={{ fontSize: '13px' }}>Framework</label>
                                            <Select
                                                onChange={onFrameworkChange}
                                                showSearch
                                                placeholder="Select framework"
                                                filterOption={filterOption}
                                                options={framework_options}
                                                value={currentFrameworkId || undefined}
                                                style={{ width: '100%' }}
                                            />
                                        </div>
                                        <div>
                                            <label className="form-label" style={{ fontSize: '13px' }}>Assessment Type</label>
                                            <Select
                                                onChange={onAssessmentTypeChange}
                                                showSearch
                                                placeholder="Select type"
                                                filterOption={filterOption}
                                                options={assessmentType_options}
                                                value={selectedAssessmentType || undefined}
                                                style={{ width: '100%' }}
                                            />
                                        </div>
                                        {/* Scope Selection */}
                                        {scope_type_options.length > 0 && currentFrameworkId && (
                                            <>
                                                <div>
                                                    <label className="form-label" style={{ fontSize: '13px' }}>
                                                        Scope Type
                                                        {frameworkScopeConfig?.scope_selection_mode === 'required' && <span style={{ color: 'red' }}> *</span>}
                                                    </label>
                                                    <Select
                                                        onChange={(value) => {
                                                            setSelectedScopeType(value);
                                                            setSelectedScopeEntityId('');
                                                        }}
                                                        showSearch
                                                        placeholder="Select scope type"
                                                        filterOption={filterOption}
                                                        options={scope_type_options}
                                                        value={selectedScopeType || undefined}
                                                        style={{ width: '100%' }}
                                                    />
                                                </div>
                                                {selectedScopeType && selectedScopeType !== 'Other' && (
                                                    <div>
                                                        <label className="form-label" style={{ fontSize: '13px' }}>
                                                            {getScopeLabel(selectedScopeType)}
                                                            {frameworkScopeConfig?.scope_selection_mode === 'required' && <span style={{ color: 'red' }}> *</span>}
                                                        </label>
                                                        <Select
                                                            onChange={(value) => setSelectedScopeEntityId(value)}
                                                            showSearch
                                                            placeholder={`Select ${getScopeLabel(selectedScopeType).toLowerCase()}`}
                                                            filterOption={filterOption}
                                                            options={scope_entity_options}
                                                            value={selectedScopeEntityId || undefined}
                                                            style={{ width: '100%' }}
                                                        />
                                                    </div>
                                                )}
                                            </>
                                        )}
                                        <div>
                                            <label className="form-label" style={{ fontSize: '13px' }}>Assessment Name</label>
                                            <input
                                                className="form-input"
                                                type="text"
                                                placeholder="Enter assessment name"
                                                value={assessmentName}
                                                onChange={(e) => setAssessmentName(e.target.value)}
                                                style={{ width: '100%', boxSizing: 'border-box' }}
                                            />
                                        </div>
                                        <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                                            <button
                                                className="add-button"
                                                onClick={async () => {
                                                    await onCreateAssessment();
                                                    // Refresh all user assessments after creating
                                                    if (current_user?.id) {
                                                        const response = await fetch(`${cyberbridge_back_end_rest_api}/assessments/user/${current_user.id}`, {
                                                            headers: { ...useAuthStore.getState().getAuthHeader() }
                                                        });
                                                        if (response.ok) {
                                                            const data = await response.json();
                                                            setAllUserAssessments(data);
                                                        }
                                                    }
                                                }}
                                                style={{ flex: 1, height: '40px' }}
                                            >
                                                Create
                                            </button>
                                            <button
                                                className="secondary-button"
                                                onClick={() => {
                                                    setShowCreateForm(false);
                                                    clearFormFields();
                                                }}
                                                style={{ height: '40px' }}
                                            >
                                                Cancel
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {/* Quick Stats */}
                                <div className="assessment-quick-stats" style={{ marginTop: '20px', paddingTop: '16px' }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                                        <div className="assessment-stats-card" style={{
                                            padding: '12px',
                                            borderRadius: '6px',
                                            textAlign: 'center'
                                        }}>
                                            <div style={{ fontSize: '24px', fontWeight: 600, color: '#1890ff' }}>
                                                {allUserAssessments.length}
                                            </div>
                                            <div style={{ fontSize: '12px', color: 'var(--text-dark-gray)' }}>Total</div>
                                        </div>
                                        <div className="assessment-stats-card" style={{
                                            padding: '12px',
                                            borderRadius: '6px',
                                            textAlign: 'center'
                                        }}>
                                            <div style={{ fontSize: '24px', fontWeight: 600, color: '#52c41a' }}>
                                                {allUserAssessments.filter(a => a.completed_at).length}
                                            </div>
                                            <div style={{ fontSize: '12px', color: 'var(--text-dark-gray)' }}>Completed</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Assessment Configuration Section - For selecting existing assessments */}
                    <div className="page-section">
                        <h3 className="section-title">Select Assessment</h3>
                        <p className="section-subtitle">
                            Or browse and select from existing assessments
                        </p>

                        <div className="form-row">
                            <div className="form-group">
                                <label className="form-label">Framework</label>
                                <Select
                                    onChange={onFrameworkChange}
                                    showSearch
                                    placeholder="Select framework"
                                    filterOption={filterOption}
                                    options={framework_options}
                                    value={currentFrameworkId || undefined}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Assessment Type</label>
                                <Select
                                    onChange={onAssessmentTypeChange}
                                    showSearch
                                    placeholder="Select type"
                                    filterOption={filterOption}
                                    options={assessmentType_options}
                                    value={selectedAssessmentType || undefined}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Assessment</label>
                                <Select
                                    onChange={onAssessmentChange}
                                    showSearch
                                    placeholder="Select assessment"
                                    filterOption={filterOption}
                                    options={assessment_options}
                                    value={selectedAssessment}
                                    disabled={assessmentDropdownIsDisabled}
                                    style={{ width: '100%' }}
                                />
                            </div>
                            {selectedAssessment && (
                                <div className="control-group" style={{ alignSelf: 'flex-end' }}>
                                    <button
                                        className="delete-button"
                                        onClick={deleteAssessmentAndAnswers}
                                        style={{ height: '40px' }}
                                    >
                                        Delete Assessment
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Questions and Answers Section */}
                    {answers.length > 0 && (
                        <div className="page-section">
                            <h3 className="section-title">
                                Assessment Questions
                                {getScopeDisplayText() && (
                                    <span style={{ color: '#999', fontWeight: 'normal', fontSize: '0.9em', marginLeft: '8px' }}>
                                        ({getScopeDisplayText()})
                                    </span>
                                )}
                            </h3>

                            {answers
                                .slice((currentPage - 1) * questionsPerPage, currentPage * questionsPerPage)
                                .map((answer: Answer, index) => (
                                <div
                                    key={answer.answer_id}
                                    style={{
                                        border: '1px solid #e8e8e8',
                                        borderRadius: '8px',
                                        padding: '24px',
                                        marginBottom: '24px',
                                        backgroundColor: '#fafafa'
                                    }}
                                >
                                    <div style={{ display: 'flex', gap: '24px' }}>
                                        <div style={{ flex: 1 }}>
                                            {/* Question Header */}
                                            <div style={{ marginBottom: '16px' }}>
                                                <h4 style={{
                                                    margin: '0 0 8px 0',
                                                    color: '#262626',
                                                    fontSize: '16px',
                                                    fontWeight: '600'
                                                }}>
                                                    Question {(currentPage - 1) * questionsPerPage + index + 1}
                                                </h4>
                                                <div style={{ display: 'flex', gap: '16px', fontSize: '12px', marginBottom: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                                                    <span>
                                                        Mandatory: <strong style={{ color: answer.is_question_mandatory ? '#ff4d4f' : '#52c41a' }}>
                                                            {answer.is_question_mandatory ? 'YES' : 'NO'}
                                                        </strong>
                                                    </span>
                                                    <span>
                                                        Completed: <strong style={{ color: answer.answer_value ? '#52c41a' : '#ff4d4f' }}>
                                                            {answer.answer_value ? 'YES' : 'NO'}
                                                        </strong>
                                                    </span>
                                                    <span style={{ color: '#8c8c8c' }}>
                                                        Common in: {answer.framework_names}
                                                    </span>
                                                    {answer.is_correlated && (() => {
                                                        const currentAssessment = assessments.find(a => a.id === selectedAssessment);
                                                        return (
                                                            <CorrelationsTooltip
                                                                questionId={answer.question_id}
                                                                scopeType={currentAssessment?.scope_name}
                                                                scopeEntityName={currentAssessment?.scope_display_name}
                                                            >
                                                                <span
                                                                    style={{
                                                                        color: '#1890ff',
                                                                        cursor: 'pointer',
                                                                        textDecoration: 'underline',
                                                                        fontSize: '12px'
                                                                    }}
                                                                >
                                                                    Correlated
                                                                </span>
                                                            </CorrelationsTooltip>
                                                        );
                                                    })()}
                                                </div>
                                            </div>

                                            {/* Question Text */}
                                            <p style={{
                                                fontWeight: '500',
                                                marginBottom: '16px',
                                                color: '#262626',
                                                lineHeight: '1.5'
                                            }}>
                                                {answer.question_text}
                                            </p>

                                            {/* Answer Options */}
                                            <div style={{ display: 'flex', gap: '16px', marginBottom: '16px', flexWrap: 'wrap' }}>
                                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                                                    <input
                                                        type="radio"
                                                        name={answer.answer_id}
                                                        value="yes"
                                                        checked={answer.answer_value === 'yes'}
                                                        onChange={(e) => updateAnswerLocally(answer.question_id, e.target.value)}
                                                    />
                                                    Yes
                                                </label>
                                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                                                    <input
                                                        type="radio"
                                                        name={answer.answer_id}
                                                        value="no"
                                                        checked={answer.answer_value === 'no'}
                                                        onChange={(e) => updateAnswerLocally(answer.question_id, e.target.value)}
                                                    />
                                                    No
                                                </label>
                                                {answer.assessment_type?.toLowerCase() !== 'audit' && (
                                                    <>
                                                        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                                                            <input
                                                                type="radio"
                                                                name={answer.answer_id}
                                                                value="partially"
                                                                checked={answer.answer_value === 'partially'}
                                                                onChange={(e) => updateAnswerLocally(answer.question_id, e.target.value)}
                                                            />
                                                            Partially
                                                        </label>
                                                        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                                                            <input
                                                                type="radio"
                                                                name={answer.answer_id}
                                                                value="n/a"
                                                                checked={answer.answer_value === 'n/a'}
                                                                onChange={(e) => updateAnswerLocally(answer.question_id, e.target.value)}
                                                            />
                                                            N/A
                                                        </label>
                                                    </>
                                                )}
                                            </div>

                                            {/* Policy Assignment for Conformity Assessment */}
                                            {answer.assessment_type?.toLowerCase() === 'conformity' && (
                                                <div style={{ marginBottom: '16px' }}>
                                                    <label className="form-label">Assign Policy</label>
                                                    <Select
                                                        style={{ width: '100%', maxWidth: '400px' }}
                                                        placeholder="Select a policy"
                                                        value={answer.policy_id || ''}
                                                        onChange={(value) => onPolicyChange(answer.question_id, value)}
                                                        options={[
                                                            { value: '', label: 'No Policy' },
                                                            ...policy_options
                                                        ]}
                                                        showSearch
                                                        filterOption={(input, option) =>
                                                            (option?.label ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                                        }
                                                    />
                                                    {answer.policy_title && (
                                                        <p style={{ marginTop: '8px', fontSize: '14px', color: '#8c8c8c' }}>
                                                            Currently assigned: {answer.policy_title}
                                                        </p>
                                                    )}
                                                </div>
                                            )}

                                            {/* Evidence Description */}
                                            <div style={{ marginBottom: '16px' }}>
                                                <label className="form-label">Evidence Description</label>
                                                <textarea
                                                    style={{
                                                        width: '100%',
                                                        minHeight: '80px',
                                                        padding: '8px 12px',
                                                        border: '1px solid #d9d9d9',
                                                        borderRadius: '6px',
                                                        fontSize: '14px',
                                                        fontFamily: 'inherit',
                                                        resize: 'vertical'
                                                    }}
                                                    placeholder="Describe the evidence supporting this answer..."
                                                    value={answer.evidence_description || ''}
                                                    onChange={(e) => updateAnswerLocally(answer.question_id, undefined, undefined, undefined, e.target.value)}
                                                />
                                            </div>

                                            {/* File Attachments */}
                                            <div>
                                                <p style={{ marginBottom: '8px', fontSize: '14px', color: '#8c8c8c' }}>
                                                    {answer.files?.length || 0} file(s) attached:
                                                </p>
                                                {answer.files && answer.files.length > 0 && (
                                                    <div style={{
                                                        padding: '12px',
                                                        backgroundColor: '#f0f8ff',
                                                        border: '1px solid #d6e7ff',
                                                        borderRadius: '6px',
                                                        fontSize: '14px'
                                                    }}>
                                                        {answer.files.map((file, fileIndex) => (
                                                            <span key={fileIndex}>
                                                                {file.name}
                                                                {fileIndex !== (answer.files?.length ?? 0) - 1 && ', '}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* Action Buttons */}
                                        {showElement && (
                                            <div style={{
                                                display: 'flex',
                                                flexDirection: 'column',
                                                gap: '12px',
                                                minWidth: '200px'
                                            }}>
                                                <button
                                                    className="add-button"
                                                    onClick={() => saveAnswer(answer.answer_id, answer.answer_value, answer.files)}
                                                >
                                                    Save Answer
                                                </button>
                                                <button
                                                    className="secondary-button"
                                                    onClick={() => clearAnswer(answer.question_id, answer.answer_id)}
                                                >
                                                    Clear Answer
                                                </button>
                                                <label
                                                    className="secondary-button"
                                                    style={{
                                                        textAlign: 'center',
                                                        cursor: 'pointer',
                                                        margin: 0
                                                    }}
                                                >
                                                    Attach File(s)
                                                    <input
                                                        type="file"
                                                        multiple
                                                        onChange={(e) => attachFilesToAnswer(e, answer.question_id)}
                                                        style={{display: 'none'}}
                                                    />
                                                </label>
                                                {(answer.files?.length ?? 0) > 0 && answer.files?.some(file => !file.lastModified) && (
                                                    <button
                                                        className="secondary-button"
                                                        onClick={() => downloadAnswerFilesAsZip(answer.files)}
                                                        style={{ backgroundColor: '#6366f1', borderColor: '#6366f1', color: 'white' }}
                                                    >
                                                        Download File(s)
                                                    </button>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {answers.length > questionsPerPage && (
                                <div style={{ display: 'flex', justifyContent: 'center', marginTop: '16px' }}>
                                    <Pagination
                                        current={currentPage}
                                        pageSize={questionsPerPage}
                                        total={answers.length}
                                        onChange={(page) => {
                                            setCurrentPage(page);
                                            window.scrollTo({ top: 0, behavior: 'smooth' });
                                        }}
                                        showSizeChanger={false}
                                        showTotal={(total, range) => `${range[0]}-${range[1]} of ${total} questions`}
                                    />
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
            <ScanSuggestionsDrawer
                open={scanSuggestDrawerOpen}
                onClose={() => setScanSuggestDrawerOpen(false)}
                assessmentId={selectedAssessment}
                onApplySuggestion={handleApplyScanSuggestion}
            />
            <AISuggestionsDrawer
                open={aiSuggestDrawerOpen}
                onClose={() => setAiSuggestDrawerOpen(false)}
                assessmentId={selectedAssessment}
                onApplySuggestion={handleApplyScanSuggestion}
                currentPage={currentPage}
                pageQuestionIds={(() => {
                    const start = (currentPage - 1) * questionsPerPage;
                    return answers
                        .slice(start, start + questionsPerPage)
                        .filter(a => !a.answer_value || a.answer_value.trim() === '')
                        .map(a => a.question_id);
                })()}
            />
        </div>
    );
};

export default AssessmentsPage;
