// src/store/useQuestionsStore.ts
import { create } from 'zustand';
import useAuthStore from "./useAuthStore.ts";
import React from "react";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

// Question interface
interface Question {
    id: string;
    text: string;
    mandatory: boolean;
    assessment_type_id?: string;
}

export type FrameworksQuestions = {
    key: React.Key;
    framework_id: string;
    question_id: string;
    framework_name: string;
    framework_description: string;
    question_text: string;
    is_question_mandatory: string;
    assessment_type: string;
}

type QuestionsStore = {
    questions: Question[];
    frameworks_questions: FrameworksQuestions[];
    count: number;
    loading: boolean;
    error: string | null;

    // Actions
    addQuestion: (text: string, assessmentTypeId?: string) => void;
    removeQuestion: (id: string) => void;
    clearQuestions: () => void;
    toggleMandatory: (id: string) => void;
    addMultipleQuestions: (newQuestions: Question[]) => void;
    setQuestions: (questions: Question[]) => void;
    fetchFrameworksQuestions: (frameworkIds: string[]) => Promise<boolean>;
    saveQuestions: (frameworkIds: string[]) => Promise<boolean>;
    uploadQuestionsFromCSV: (file: File) => Promise<void>;
    deleteQuestion: (questionId: string) => Promise<boolean>;
}

const useQuestionsStore = create<QuestionsStore>((set, get) => ({
    //variables values initialization
    questions: [],
    frameworks_questions: [],
    count: 0,
    loading: false,
    error: null,

    addQuestion: (text, assessmentTypeId) => set((state) => {
        const newQuestion = {
            id: state.count.toString(),
            text,
            mandatory: false,
            assessment_type_id: assessmentTypeId
        };
        return {
            questions: [newQuestion, ...state.questions],
            count: state.count + 1
        };
    }),

    removeQuestion: (id) => set((state) => ({
        questions: state.questions.filter(question => question.id !== id)
    })),


    clearQuestions: () => set({
        questions: [],
        count: 0
    }),

    toggleMandatory: (id) => {
        set((state) => ({
            questions: state.questions.map(question => question.id === id ? { ...question, mandatory: !question.mandatory } : question)
        }));
        console.log('Current questions:', get().questions);
    }
        ,

    addMultipleQuestions: (newQuestions) => set((state) => ({
        questions: [...state.questions, ...newQuestions],
        count: state.count + newQuestions.length
    })),

    setQuestions: (questions) => set({ questions }),

    // Fetch questions for a specific framework
    fetchFrameworksQuestions: async (frameworkIds: string[]) => {
        set({ loading: true, error: null });
        const payload = JSON.stringify({
            framework_ids: frameworkIds
        });
        console.log('Request payload:', payload);
        try {
            // Replace with your API endpoint
            const response = await fetch(`${cyberbridge_back_end_rest_api}/questions/for_frameworks`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                method: 'POST',
                body: payload
            });
            if (!response.ok) {
                return false;
            }

            // Convert is_question_mandatory from boolean to string
            const frameworks_questions: FrameworksQuestions[] = (await response.json()).map((result: FrameworksQuestions) => ({
                ...result,
                is_question_mandatory: result.is_question_mandatory ? 'Yes' : 'No',
            }));

            console.log('Frameworks questions:', frameworks_questions);
            // Update the state with the data
            set({
                frameworks_questions,
                loading: false,
                error: null
            });

            return true;

        } catch (error) {
            console.error('Error fetching questions:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch questions',
                loading: false
            });
            return false;
        }
    },

    saveQuestions: async (frameworkIds: (string)[]) => {
        set({ loading: true, error: null });
        // Create a variable for the payload
        const payload = {
            framework_ids: frameworkIds,
            questions: get().questions
        };

        // Log the payload
        console.log('Request payload:', payload);

        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/frameworks/questions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                return false;
            }

            set({ loading: false });
            return true;
        } catch (error) {
            console.error('Error saving questions:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to save questions',
                loading: false
            });
            return false;
        }
    },


    // New method to handle CSV file uploads
    uploadQuestionsFromCSV: async (file: File) => {
        set({ loading: true, error: null });

        try {
            return new Promise<void>((resolve, reject) => {
                const reader = new FileReader();

                reader.onload = (event) => {
                    try {
                        const csvData = event.target?.result as string;
                        if (!csvData) {
                            throw new Error('Failed to read CSV file');
                        }

                        // Parse CSV data
                        const lines = csvData.split('\n');
                        const newQuestions: Question[] = [];
                        const currentCount = get().count;

                        // Start from index 1 to skip header
                        for (let i = 1; i < lines.length; i++) {
                            const line = lines[i].trim();
                            if (line) {
                                newQuestions.push({
                                    id: (currentCount + i - 1).toString(),
                                    text: line,
                                    mandatory: false
                                });
                            }
                        }

                        // Update state with new questions
                        set(state => ({
                            questions: [...state.questions, ...newQuestions],
                            count: state.count + newQuestions.length,
                            loading: false
                        }));

                        resolve();
                    } catch (error) {
                        set({
                            error: error instanceof Error ? error.message : 'Failed to process CSV file',
                            loading: false
                        });
                        reject(error);
                    }
                };

                reader.onerror = () => {
                    const error = new Error('Error reading file');
                    set({ error: error.message, loading: false });
                    reject(error);
                };

                reader.readAsText(file);
            });

        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to process CSV file',
                loading: false
            });
        }
    },

    // Delete a question from frameworks and potentially from the questions table
    deleteQuestion: async (questionId: string) => {
        set({ loading: true, error: null });

        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/questions/${questionId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                set({
                    error: 'Failed to delete question',
                    loading: false
                });
                return false;
            }

            // Update the local state by removing the question from frameworks_questions
            set(state => ({
                frameworks_questions: state.frameworks_questions.filter(fq => fq.question_id !== questionId),
                loading: false
            }));

            return true;
        } catch (error) {
            console.error('Error deleting question:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to delete question',
                loading: false
            });
            return false;
        }
    }

}));

export default useQuestionsStore;
