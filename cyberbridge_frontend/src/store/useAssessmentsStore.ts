import {create} from 'zustand';
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

export interface Assessment {
    id:string;
    name:string;
    framework_id:string;
    user_id:string;
    progress:number;
    status:string;
    created_at:string;
    updated_at:string;
    completed_at:string;
    scope_id?:string;
    scope_entity_id?:string;
    scope_name?:string;
    scope_display_name?:string;
}

// Custom File type with path property
export interface CustomFile extends File {
    path?: string;
    id?: string;
}

export interface Answer {
    answer_id: string;
    assessment_id: string;
    question_id: string;
    answer_value: string | null;
    evidence_description: string | null;
    question_text: string;
    question_description: string | null;
    is_question_mandatory: boolean;
    framework_names: string;
    files: CustomFile[] | null;
    assessment_type: string;
    policy_id: string | null;
    policy_title: string | null;
    is_correlated: boolean;
}

export interface AnswerUpdateRequest {
    answer_id: string
    answer_value: string | null;
    evidence_description?: string | null;
    files: CustomFile[] | null;
    policy_id?: string | null;
}

export interface insertAssessment {
    name:string;
    framework_id:string;
    user_id:string;
    assessment_type_id:string;
    progress:number;
    status:string;
    scope_name?:string;
    scope_entity_id?:string;
}

export interface FrameworkAndUser {
    framework_id:string;
    user_id:string;
}

export interface FrameworkUserAndAssessmentType {
    framework_id:string;
    user_id:string;
    assessment_type_id:string;
}

interface AssessmentsStore {
    //variables
    assessments:Assessment[];
    answers:Answer[];
    loading: boolean;
    error: string | null;
    //functions
    fetchAssessments: () => Promise<boolean>;
    fetchAssessmentsForFrameworkAndUser: (request:FrameworkAndUser) => Promise<boolean>;
    fetchAssessmentsForFrameworkUserAndAssessmentType: (request:FrameworkUserAndAssessmentType) => Promise<boolean>;
    createAssessment: (assessment:insertAssessment) => Promise<boolean>; //I could use -> assessment: Partial<Assessment>
    clearAssessments: () => void;
    fetchAssessmentAnswers: (assessment_id:string) => Promise<boolean>;
    clearAnswers: () => void;
    updateAnswerLocally: (questionId: string, value?: string | null, files?: File[] | null, policyId?: string | null, evidenceDescription?: string | null) => void;
    updateAnswerPermanently: (answer: AnswerUpdateRequest) => Promise<boolean>;
    deleteAnswerPermanently: (answer_id: string) => Promise<boolean>;
    saveAssessmentAnswers: () => Promise<boolean>;
    deleteAssessment: (assessment_id:string | undefined) => Promise<boolean>;
    removeAssessmentFromState: (assessment_id:string) => void;
    downloadZip: (fileIds: (string | undefined)[]) => Promise<boolean>;
}

const useAssessmentsStore = create<AssessmentsStore>((set, get) => ({
    //variables
    assessments: [],
    answers: [],
    loading: false,
    error: null,

    //functions
    clearAnswers: () => set({answers: []}),
    clearAssessments: () => set({assessments: []}),
    removeAssessmentFromState: (assessment_id:string) => {
        set(state => ({
            assessments: state.assessments.filter(assessment => assessment.id !== assessment_id)
        }));
    },

    downloadZip : async ( fileIds: (string | undefined)[] ) => {
        set({ loading: true, error: null });
        const payload = JSON.stringify({ids: fileIds});
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/answers/download_zip`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: payload,
            });

            if (!response.ok) {return false;}

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", "files.zip");
            document.body.appendChild(link);
            link.click();
            link.remove();
            set({loading: false});
            return true;
        }
        catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to create assessment',
                loading: false
            });
            return false;
        }
    },

    deleteAssessment: async (assessment_id:string | undefined) => {
        set({ loading: true, error: null });
        const payload = JSON.stringify({id: assessment_id});
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assessments/delete_assessment_answers`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', ...useAuthStore.getState().getAuthHeader()},
                body: payload
            });
            if (!response.ok) {return false;}
            // const data = await response.json();
            set({loading: false});
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to create assessment',
                loading: false
            });
            return false;
        }
    },

    updateAnswerLocally: (questionId: string, value?: string | null, files?: File[] | null, policyId?: string | null, evidenceDescription?: string | null) => {
        set((state) => ({
            answers: state.answers.map(answer =>
                answer.question_id === questionId
                    ? {
                        ...answer,
                        ...(value !== undefined && { answer_value: value }),
                        ...(files !== undefined && { files }),
                        ...(policyId !== undefined && { policy_id: policyId }),
                        ...(evidenceDescription !== undefined && { evidence_description: evidenceDescription })
                    }
                    : answer
            )
        }));
    },

    deleteAnswerPermanently: async (answer_id: string) => {
        set({ loading: true, error: null });
        const payload = JSON.stringify({id: answer_id});
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/answers/delete_answer`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', ...useAuthStore.getState().getAuthHeader()},
                body: payload
            });
            if (!response.ok) {return false;}
            // const data = await response.json();
            set({loading: false});
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to create assessment',
                loading: false
            });
            return false;
        }
    },

    updateAnswerPermanently: async (answer: AnswerUpdateRequest) => {
        set({ loading: true, error: null });

        // const answer_payload = JSON.stringify({answer_id: answer.answer_id, answer_value: answer.answer_value});

        const formData = new FormData();
        formData.append('answer_id', answer.answer_id);
        formData.append('answer_value', answer.answer_value === null ? '' : answer.answer_value);
        if (answer.evidence_description !== undefined) {
            formData.append('evidence_description', answer.evidence_description === null ? '' : answer.evidence_description);
        }
        if (answer.policy_id !== undefined) {
            formData.append('policy_id', answer.policy_id === null ? '' : answer.policy_id);
        }
        if(answer.files && answer.files.length > 0 && answer.files[0].lastModified) {
            answer.files.forEach(file => formData.append('files', file));
        }

        console.log('Request payload:', answer);
        console.log('Files to upload:', answer.files ? answer.files.map(file => ({
            name: file.name,
            type: file.type,
            size: file.size
        })) : 'No files');

        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/answers/update_answer`, {
                method: 'POST',
                headers: {...useAuthStore.getState().getAuthHeader()},
                body: formData
            });
            if (!response.ok) {return false;}
            set({loading: false});
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to save answer!',
                loading: false
            });
            return false;
        }
    },

    saveAssessmentAnswers: async () => {
        set({ loading: true, error: null });
        const payload = JSON.stringify(
            get().answers.map(answer => ({
                answer_id: answer.answer_id,
                answer_value: answer.answer_value
            }))
        );
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/answers/update_assessment_answers`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', ...useAuthStore.getState().getAuthHeader()},
                body: payload
            });
            if (!response.ok) {return false;}
            // const answers = await response.json();
            set({loading: false});
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to create assessment',
                loading: false
            });
            return false;
        }
    },

    fetchAssessments: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assessments`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                return false
            }

            const data = await response.json();
            set({assessments: data, loading: false});
            return true;

        } catch (error) {
            console.error('Error fetching assessments:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch assessments',
                loading: false
            });
            return false;
        }
    },

    fetchAssessmentsForFrameworkAndUser: async (request:FrameworkAndUser) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assessments/assessments_for_framework_and_user`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    framework_id: request.framework_id,
                    user_id: request.user_id
                })
            });

            if (!response.ok) {
                return false;
            }

            const data = await response.json();
            set({assessments: data, loading: false});
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to create assessment',
                loading: false
            });
            return false;
        }
    },

    fetchAssessmentsForFrameworkUserAndAssessmentType: async (request:FrameworkUserAndAssessmentType) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assessments/assessments_for_framework_user_and_assessment_type`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify({
                    framework_id: request.framework_id,
                    user_id: request.user_id,
                    assessment_type_id: request.assessment_type_id
                })
            });

            if (!response.ok) {
                return false;
            }

            const data = await response.json();
            set({assessments: data, loading: false});
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch assessments',
                loading: false
            });
            return false;
        }
    },

    createAssessment: async (assessment:insertAssessment) => {
        set({ loading: true, error: null });
        const payload = JSON.stringify(
            {
                name: assessment.name,
                framework_id: assessment.framework_id,
                user_id: assessment.user_id,
                assessment_type_id: assessment.assessment_type_id,
                progress: assessment.progress,
                status: assessment.status,
                scope_name: assessment.scope_name,
                scope_entity_id: assessment.scope_entity_id
            });
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assessments/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if (!response.ok) {
                return false;
            }

            const newAssessment = await response.json();
            set(state => ({
                assessments: [...state.assessments, newAssessment],
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to create assessment',
                loading: false
            });
            return false;
        }
    },

    fetchAssessmentAnswers: async (assessment_id:string) => {
        set({ loading: true, error: null });
        const payload = JSON.stringify(
            {
                assessment_id: assessment_id,
            });
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/assessments/fetch_assessment_answers`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if (!response.ok) {
                return false;
            }

            const answers = await response.json();
            console.log('Answers:', answers);
            set({
                answers: answers,
                loading: false
            });
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to create assessment',
                loading: false
            });
            return false;
        }
    }


}));

export default useAssessmentsStore;
