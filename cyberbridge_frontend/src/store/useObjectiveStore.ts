import {create} from "zustand";
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

export interface Chapter{
    id: string;
    title: string;
    framework_id: string;
}

export interface ChecklistPolicy {
    id: string;
    title: string;
    status_id: string;
    status: string;
}

export interface Objective {
    id: string;
    title: string;
    subchapter: string | null;
    chapter_id: string;
    requirement_description: string | null;
    objective_utilities: string | null;
    compliance_status_id: string | null;
    compliance_status: string | null;
    policies?: ChecklistPolicy[];
}

export interface ComplianceStatus {
    id: string;
    status_name: string;
}

export interface ObjectiveChecklistItem {
    id: string;
    title: string;
    subchapter: string | null;
    chapter_id: string;
    requirement_description: string | null;
    objective_utilities: string | null;
    compliance_status_id: string | null;
    compliance_status: string | null;
    policies?: ChecklistPolicy[];
    evidence_filename: string | null;
    evidence_file_type: string | null;
    evidence_file_size: number | null;
    created_at: string;
    updated_at: string;
}

export interface ChapterWithObjectives {
    id: string;
    title: string;
    framework_id: string;
    created_at: string;
    updated_at: string;
    objectives: ObjectiveChecklistItem[];
}

export interface ObjectiveStore {
    //variables
    chapters: Chapter[];
    objectives: Objective[];
    complianceStatuses: ComplianceStatus[];
    chaptersWithObjectives: ChapterWithObjectives[];
    loading: boolean;
    error: string | null;

    //functions
    createChapter: (title:string, framework_id:string) => Promise<boolean>;
    updateChapter: (title:string, framework_id:string, id:string) => Promise<boolean>;
    deleteChapter: (id:string) => Promise<boolean>;
    fetchObjectives: () => Promise<boolean>;
    fetchChapters: () => Promise<boolean>;
    createObjective: (title:string, subchapter:string, chapter_id:string, requirement_description:string, objective_utilities:string, compliance_status_id?:string) => Promise<boolean>;
    updateObjective: (title:string, subchapter:string, chapter_id:string, requirement_description:string, objective_utilities:string, id:string, compliance_status_id?:string) => Promise<boolean>;
    deleteObjective: (id:string) => Promise<boolean>;
    fetchComplianceStatuses: () => Promise<boolean>;
    fetchObjectivesChecklist: (frameworkId?: string, scopeName?: string, scopeEntityId?: string, operatorRole?: string) => Promise<boolean>;
    updateObjectiveComplianceStatus: (objectiveId: string, complianceStatusId: string, frameworkId?: string, scopeName?: string, scopeEntityId?: string) => Promise<boolean>;
    uploadObjectiveEvidence: (objectiveId: string, file: File) => Promise<boolean>;
    deleteObjectiveEvidence: (objectiveId: string) => Promise<boolean>;
    clearChecklist: () => void;
}

const useObjectiveStore = create<ObjectiveStore>(set =>({
    //variables
    chapters: [],
    objectives: [],
    complianceStatuses: [],
    chaptersWithObjectives: [],
    loading: false,
    error: null,

    // Chapter management functions
    createChapter: async (title: string, framework_id: string) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({title: title, framework_id: framework_id});
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/create_chapter`, {
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

            const newChapter = await response.json();
            set(state => ({chapters: [...state.chapters, newChapter], loading: false}));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to create chapter',
                loading: false
            });
            return false;
        }
    },

    updateChapter: async (title: string, framework_id: string, id: string) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({title: title, framework_id: framework_id, id: id});
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/update_chapter`, {
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

            const updatedChapter = await response.json();
            set(state => ({
                chapters: state.chapters.map(chapter => chapter.id === id ? updatedChapter : chapter),
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to update chapter',
                loading: false
            });
            return false;
        }
    },

    deleteChapter: async (id: string) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({id: id});
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/delete_chapter`, {
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

            set(state => ({
                chapters: state.chapters.filter(chapter => chapter.id !== id),
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to delete chapter',
                loading: false
            });
            return false;
        }
    },

    fetchChapters: async () => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/get_all_chapters`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log(data);
            set({chapters: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching chapters:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch chapters',
                loading: false
            });
            return false;
        }
    },

    // Objective management functions
    createObjective: async (title: string, subchapter: string, chapter_id: string, requirement_description: string, objective_utilities: string, compliance_status_id?: string) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({
            title: title,
            subchapter: subchapter,
            chapter_id: chapter_id,
            requirement_description: requirement_description,
            objective_utilities: objective_utilities,
            compliance_status_id: compliance_status_id
        });
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/create_objective`, {
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

            const newObjective = await response.json();
            set(state => ({objectives: [...state.objectives, newObjective], loading: false}));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to create objective',
                loading: false
            });
            return false;
        }
    },

    updateObjective: async (title: string, subchapter: string, chapter_id: string, requirement_description: string, objective_utilities: string, id: string, compliance_status_id?: string) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({
            title: title,
            subchapter: subchapter,
            chapter_id: chapter_id,
            requirement_description: requirement_description,
            objective_utilities: objective_utilities,
            compliance_status_id: compliance_status_id,
            id: id
        });
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/update_objective`, {
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

            const updatedObjective = await response.json();
            set(state => ({
                objectives: state.objectives.map(objective => objective.id === id ? updatedObjective : objective),
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to update objective',
                loading: false
            });
            return false;
        }
    },

    deleteObjective: async (id: string) => {
        set({loading: true, error: null});
        const payload = JSON.stringify({id: id});
        console.log('Request payload:', payload);
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/delete_objective`, {
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

            set(state => ({
                objectives: state.objectives.filter(objective => objective.id !== id),
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to delete objective',
                loading: false
            });
            return false;
        }
    },

    fetchObjectives: async () => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/get_all_objectives`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log(data);
            set({objectives: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching objectives:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch objectives',
                loading: false
            });
            return false;
        }
    },

    // Compliance Status functions
    fetchComplianceStatuses: async () => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/get_compliance_statuses`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log('Compliance statuses:', data);
            set({complianceStatuses: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching compliance statuses:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch compliance statuses',
                loading: false
            });
            return false;
        }
    },

    // Objectives Checklist functions
    fetchObjectivesChecklist: async (frameworkId?: string, scopeName?: string, scopeEntityId?: string, operatorRole?: string) => {
        set({loading: true, error: null});
        try {
            let url = `${cyberbridge_back_end_rest_api}/objectives/objectives_checklist`;
            const params = new URLSearchParams();

            if (frameworkId) {
                params.append('framework_id', frameworkId);
            }
            if (scopeName) {
                params.append('scope_name', scopeName);
            }
            if (scopeEntityId) {
                params.append('scope_entity_id', scopeEntityId);
            }
            if (operatorRole) {
                params.append('operator_role', operatorRole);
            }

            if (params.toString()) {
                url += `?${params.toString()}`;
            }

            const response = await fetch(url, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            console.log('Objectives checklist:', data);
            set({chaptersWithObjectives: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching objectives checklist:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch objectives checklist',
                loading: false
            });
            return false;
        }
    },

    updateObjectiveComplianceStatus: async (objectiveId: string, complianceStatusId: string, frameworkId?: string, scopeName?: string, scopeEntityId?: string) => {
        set({loading: true, error: null});
        try {
            // First update the objective with the new compliance status
            const objective = useObjectiveStore.getState().chaptersWithObjectives
                .flatMap(chapter => chapter.objectives)
                .find(obj => obj.id === objectiveId);

            if (!objective) {
                set({error: 'Objective not found', loading: false});
                return false;
            }

            const payload = JSON.stringify({
                title: objective.title,
                subchapter: objective.subchapter,
                chapter_id: objective.chapter_id,
                requirement_description: objective.requirement_description,
                objective_utilities: objective.objective_utilities,
                compliance_status_id: complianceStatusId,
                id: objectiveId
            });

            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/update_objective`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if (!response.ok) {
                set({
                    error: 'Failed to update compliance status',
                    loading: false
                });
                return false;
            }

            // Refresh the objectives checklist to get updated data (with scope parameters)
            await useObjectiveStore.getState().fetchObjectivesChecklist(frameworkId, scopeName, scopeEntityId);
            return true;
        } catch (error) {
            console.error('Error updating objective compliance status:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to update compliance status',
                loading: false
            });
            return false;
        }
    },

    uploadObjectiveEvidence: async (objectiveId: string, file: File) => {
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/upload_evidence/${objectiveId}`, {
                method: 'POST',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: formData
            });

            if (!response.ok) {
                return false;
            }

            const data = await response.json();

            // Update local state
            set(state => ({
                chaptersWithObjectives: state.chaptersWithObjectives.map(chapter => ({
                    ...chapter,
                    objectives: chapter.objectives.map(obj =>
                        obj.id === objectiveId
                            ? {
                                ...obj,
                                evidence_filename: data.evidence_filename,
                                evidence_file_type: data.evidence_file_type,
                                evidence_file_size: data.evidence_file_size,
                            }
                            : obj
                    )
                }))
            }));
            return true;
        } catch (error) {
            console.error('Error uploading objective evidence:', error);
            return false;
        }
    },

    deleteObjectiveEvidence: async (objectiveId: string) => {
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/objectives/delete_evidence/${objectiveId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                return false;
            }

            // Update local state
            set(state => ({
                chaptersWithObjectives: state.chaptersWithObjectives.map(chapter => ({
                    ...chapter,
                    objectives: chapter.objectives.map(obj =>
                        obj.id === objectiveId
                            ? {
                                ...obj,
                                evidence_filename: null,
                                evidence_file_type: null,
                                evidence_file_size: null,
                            }
                            : obj
                    )
                }))
            }));
            return true;
        } catch (error) {
            console.error('Error deleting objective evidence:', error);
            return false;
        }
    },
    clearChecklist: () => {
        set({ chaptersWithObjectives: [] });
    }
}));

export default useObjectiveStore;
