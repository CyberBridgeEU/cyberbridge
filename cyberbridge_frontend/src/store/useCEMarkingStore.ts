import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

export interface CEProductType {
    id: string;
    name: string;
    recommended_placement: string | null;
}

export interface CEDocumentType {
    id: string;
    name: string;
    description: string | null;
    is_mandatory: boolean;
    sort_order: number;
}

export interface CEChecklistItem {
    id: string;
    checklist_id: string;
    template_item_id: string | null;
    category: string;
    title: string;
    description: string | null;
    is_completed: boolean;
    completed_at: string | null;
    notes: string | null;
    sort_order: number;
    is_mandatory: boolean;
}

export interface CEDocumentStatus {
    id: string;
    checklist_id: string;
    document_type_id: string;
    document_type_name: string | null;
    status: string;
    document_reference: string | null;
    notes: string | null;
    completed_at: string | null;
}

export interface CEChecklist {
    id: string;
    asset_id: string;
    asset_name: string | null;
    ce_product_type_id: string | null;
    ce_product_type_name: string | null;
    ce_placement: string | null;
    ce_placement_notes: string | null;
    notified_body_required: boolean;
    notified_body_name: string | null;
    notified_body_number: string | null;
    notified_body_certificate_ref: string | null;
    version_identifier: string | null;
    build_identifier: string | null;
    doc_publication_url: string | null;
    product_variants: string | null;
    status: string;
    readiness_score: number;
    organisation_id: string | null;
    created_at: string;
    updated_at: string;
    items_completed: number;
    items_total: number;
    docs_completed: number;
    docs_total: number;
    items?: CEChecklistItem[];
    document_statuses?: CEDocumentStatus[];
}

interface CEMarkingState {
    checklists: CEChecklist[];
    currentChecklist: CEChecklist | null;
    productTypes: CEProductType[];
    documentTypes: CEDocumentType[];
    loading: boolean;
    error: string | null;
    fetchChecklists: () => Promise<void>;
    fetchChecklist: (id: string) => Promise<void>;
    fetchChecklistForAsset: (assetId: string) => Promise<CEChecklist | null>;
    fetchProductTypes: () => Promise<void>;
    fetchDocumentTypes: () => Promise<void>;
    createChecklist: (assetId: string, ceProductTypeId?: string) => Promise<CEChecklist | null>;
    updateChecklist: (id: string, data: Partial<CEChecklist>) => Promise<void>;
    deleteChecklist: (id: string) => Promise<void>;
    toggleChecklistItem: (itemId: string, isCompleted: boolean, notes?: string) => Promise<void>;
    addCustomItem: (checklistId: string, data: { category: string; title: string; description?: string; is_mandatory?: boolean }) => Promise<void>;
    deleteCustomItem: (itemId: string) => Promise<void>;
    updateDocumentStatus: (statusId: string, data: { status?: string; document_reference?: string; notes?: string }) => Promise<void>;
}

const useCEMarkingStore = create<CEMarkingState>((set, get) => ({
    checklists: [],
    currentChecklist: null,
    productTypes: [],
    documentTypes: [],
    loading: false,
    error: null,

    fetchChecklists: async () => {
        set({ loading: true, error: null });
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/ce-marking/checklists`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to fetch checklists');
            const data = await res.json();
            set({ checklists: data, loading: false });
        } catch (e: any) {
            set({ error: e.message, loading: false });
        }
    },

    fetchChecklist: async (id: string) => {
        set({ loading: true, error: null });
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/ce-marking/checklists/${id}`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to fetch checklist');
            const data = await res.json();
            set({ currentChecklist: data, loading: false });
        } catch (e: any) {
            set({ error: e.message, loading: false });
        }
    },

    fetchChecklistForAsset: async (assetId: string) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/ce-marking/checklists/asset/${assetId}`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) return null;
            return await res.json();
        } catch {
            return null;
        }
    },

    fetchProductTypes: async () => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/ce-marking/product-types`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to fetch product types');
            const data = await res.json();
            set({ productTypes: data });
        } catch (e: any) {
            set({ error: e.message });
        }
    },

    fetchDocumentTypes: async () => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/ce-marking/document-types`, {
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to fetch document types');
            const data = await res.json();
            set({ documentTypes: data });
        } catch (e: any) {
            set({ error: e.message });
        }
    },

    createChecklist: async (assetId: string, ceProductTypeId?: string) => {
        try {
            const body: any = { asset_id: assetId };
            if (ceProductTypeId) body.ce_product_type_id = ceProductTypeId;
            const res = await fetch(`${cyberbridge_back_end_rest_api}/ce-marking/checklists`, {
                method: 'POST',
                headers: { ...useAuthStore.getState().getAuthHeader(), 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to create checklist');
            }
            const data = await res.json();
            await get().fetchChecklists();
            return data;
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },

    updateChecklist: async (id: string, data: Partial<CEChecklist>) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/ce-marking/checklists/${id}`, {
                method: 'PUT',
                headers: { ...useAuthStore.getState().getAuthHeader(), 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (!res.ok) throw new Error('Failed to update checklist');
            const updated = await res.json();
            set({ currentChecklist: updated });
            await get().fetchChecklists();
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },

    deleteChecklist: async (id: string) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/ce-marking/checklists/${id}`, {
                method: 'DELETE',
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to delete checklist');
            set({ currentChecklist: null });
            await get().fetchChecklists();
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },

    toggleChecklistItem: async (itemId: string, isCompleted: boolean, notes?: string) => {
        try {
            const body: any = { is_completed: isCompleted };
            if (notes !== undefined) body.notes = notes;
            const res = await fetch(`${cyberbridge_back_end_rest_api}/ce-marking/items/${itemId}`, {
                method: 'PUT',
                headers: { ...useAuthStore.getState().getAuthHeader(), 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!res.ok) throw new Error('Failed to update item');
            const { currentChecklist } = get();
            if (currentChecklist) await get().fetchChecklist(currentChecklist.id);
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },

    addCustomItem: async (checklistId: string, data) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/ce-marking/checklists/${checklistId}/items`, {
                method: 'POST',
                headers: { ...useAuthStore.getState().getAuthHeader(), 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (!res.ok) throw new Error('Failed to add custom item');
            await get().fetchChecklist(checklistId);
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },

    deleteCustomItem: async (itemId: string) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/ce-marking/items/${itemId}`, {
                method: 'DELETE',
                headers: useAuthStore.getState().getAuthHeader(),
            });
            if (!res.ok) throw new Error('Failed to delete custom item');
            const { currentChecklist } = get();
            if (currentChecklist) await get().fetchChecklist(currentChecklist.id);
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },

    updateDocumentStatus: async (statusId: string, data) => {
        try {
            const res = await fetch(`${cyberbridge_back_end_rest_api}/ce-marking/documents/${statusId}`, {
                method: 'PUT',
                headers: { ...useAuthStore.getState().getAuthHeader(), 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });
            if (!res.ok) throw new Error('Failed to update document status');
            const { currentChecklist } = get();
            if (currentChecklist) await get().fetchChecklist(currentChecklist.id);
        } catch (e: any) {
            set({ error: e.message });
            throw e;
        }
    },
}));

export default useCEMarkingStore;
