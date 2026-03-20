import { create } from "zustand";
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

// Diagram type options
export type DiagramType = 'System' | 'Network' | 'Data Flow' | 'Infrastructure' | 'Application' | 'Security' | 'Other';

// Interfaces for Architecture Diagrams
export interface ArchitectureDiagram {
    id: string;
    name: string;
    description: string | null;
    diagram_type: DiagramType;
    file_name: string | null;
    file_url: string | null;
    file_size: number | null;
    framework_ids: string[];
    framework_names: string[];
    risk_ids: string[];
    owner: string | null;
    version: string | null;
    created_at: string;
    updated_at: string;
    organisation_id?: string;
}

export interface ArchitectureStore {
    // State
    diagrams: ArchitectureDiagram[];
    loading: boolean;
    error: string | null;

    // Actions
    fetchDiagrams: () => Promise<boolean>;
    createDiagram: (
        name: string,
        description: string | null,
        diagram_type: DiagramType,
        framework_ids: string[],
        risk_ids: string[],
        owner: string | null,
        version: string | null,
        file?: File
    ) => Promise<boolean>;
    updateDiagram: (
        id: string,
        name: string,
        description: string | null,
        diagram_type: DiagramType,
        framework_ids: string[],
        risk_ids: string[],
        owner: string | null,
        version: string | null,
        file?: File
    ) => Promise<boolean>;
    deleteDiagram: (id: string) => Promise<boolean>;

    // Local state management (for when backend is not yet implemented)
    addDiagramLocal: (diagram: ArchitectureDiagram) => void;
    updateDiagramLocal: (id: string, updates: Partial<ArchitectureDiagram>) => void;
    deleteDiagramLocal: (id: string) => void;
}

const useArchitectureStore = create<ArchitectureStore>((set, get) => ({
    // State
    diagrams: [],
    loading: false,
    error: null,

    // Fetch all diagrams
    fetchDiagrams: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/architecture/diagrams`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                // If endpoint doesn't exist yet, return empty array
                if (response.status === 404) {
                    set({ diagrams: [], loading: false });
                    return true;
                }
                return false;
            }
            const data = await response.json();
            set({ diagrams: data, loading: false });
            return true;
        } catch (error) {
            console.error('Error fetching architecture diagrams:', error);
            // Don't show error if backend endpoint doesn't exist yet
            set({ diagrams: [], loading: false });
            return true;
        }
    },

    // Create a new diagram
    createDiagram: async (
        name: string,
        description: string | null,
        diagram_type: DiagramType,
        framework_ids: string[],
        risk_ids: string[],
        owner: string | null,
        version: string | null,
        file?: File
    ) => {
        set({ loading: true, error: null });
        try {
            const formData = new FormData();
            formData.append('name', name);
            if (description) formData.append('description', description);
            formData.append('diagram_type', diagram_type);
            formData.append('framework_ids', JSON.stringify(framework_ids));
            formData.append('risk_ids', JSON.stringify(risk_ids));
            if (owner) formData.append('owner', owner);
            if (version) formData.append('version', version);
            if (file) formData.append('file', file);

            const response = await fetch(`${cyberbridge_back_end_rest_api}/architecture/diagrams`, {
                method: 'POST',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: formData
            });

            if (!response.ok) {
                return false;
            }

            const newDiagram = await response.json();
            set(state => ({ diagrams: [...state.diagrams, newDiagram], loading: false }));
            return true;
        } catch (error) {
            console.error('Error creating diagram:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to create diagram',
                loading: false
            });
            return false;
        }
    },

    // Update an existing diagram
    updateDiagram: async (
        id: string,
        name: string,
        description: string | null,
        diagram_type: DiagramType,
        framework_ids: string[],
        risk_ids: string[],
        owner: string | null,
        version: string | null,
        file?: File
    ) => {
        set({ loading: true, error: null });
        try {
            const formData = new FormData();
            formData.append('name', name);
            if (description) formData.append('description', description);
            formData.append('diagram_type', diagram_type);
            formData.append('framework_ids', JSON.stringify(framework_ids));
            formData.append('risk_ids', JSON.stringify(risk_ids));
            if (owner) formData.append('owner', owner);
            if (version) formData.append('version', version);
            if (file) formData.append('file', file);

            const response = await fetch(`${cyberbridge_back_end_rest_api}/architecture/diagrams/${id}`, {
                method: 'PUT',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: formData
            });

            if (!response.ok) {
                return false;
            }

            const updatedDiagram = await response.json();
            set(state => ({
                diagrams: state.diagrams.map(d => d.id === id ? updatedDiagram : d),
                loading: false
            }));
            return true;
        } catch (error) {
            console.error('Error updating diagram:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to update diagram',
                loading: false
            });
            return false;
        }
    },

    // Delete a diagram
    deleteDiagram: async (id: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/architecture/diagrams/${id}`, {
                method: 'DELETE',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                return false;
            }

            set(state => ({
                diagrams: state.diagrams.filter(d => d.id !== id),
                loading: false
            }));
            return true;
        } catch (error) {
            console.error('Error deleting diagram:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to delete diagram',
                loading: false
            });
            return false;
        }
    },

    // Local state management (for frontend-only operations before backend is ready)
    addDiagramLocal: (diagram: ArchitectureDiagram) => {
        set(state => ({ diagrams: [...state.diagrams, diagram] }));
    },

    updateDiagramLocal: (id: string, updates: Partial<ArchitectureDiagram>) => {
        set(state => ({
            diagrams: state.diagrams.map(d => d.id === id ? { ...d, ...updates } : d)
        }));
    },

    deleteDiagramLocal: (id: string) => {
        set(state => ({ diagrams: state.diagrams.filter(d => d.id !== id) }));
    }
}));

export default useArchitectureStore;
