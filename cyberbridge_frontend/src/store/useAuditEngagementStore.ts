import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

// Types
export interface AuditorRole {
    id: string;
    role_name: string;
    can_comment: boolean;
    can_request_evidence: boolean;
    can_add_findings: boolean;
    can_sign_off: boolean;
    created_at: string;
    updated_at: string;
}

export interface AuditEngagement {
    id: string;
    name: string;
    description: string | null;
    assessment_id: string;
    audit_period_start: string | null;
    audit_period_end: string | null;
    status: 'draft' | 'planned' | 'in_progress' | 'review' | 'completed' | 'closed';
    planned_start_date: string | null;
    actual_start_date: string | null;
    planned_end_date: string | null;
    actual_end_date: string | null;
    owner_id: string;
    organisation_id: string;
    prior_engagement_id: string | null;
    in_scope_controls: string[] | null;
    in_scope_policies: string[] | null;
    in_scope_chapters: string[] | null;
    created_at: string;
    updated_at: string;
    // Enriched fields
    assessment_name?: string;
    framework_name?: string;
    framework_id?: string;
    owner_name?: string;
    owner_email?: string;
    organisation_name?: string;
    invitation_count?: number;
    active_invitation_count?: number;
}

export interface AuditorInvitation {
    id: string;
    engagement_id: string;
    email: string;
    name: string | null;
    company: string | null;
    auditor_role_id: string;
    access_start: string | null;
    access_end: string | null;
    mfa_enabled: boolean;
    ip_allowlist: string[] | null;
    download_restricted: boolean;
    watermark_downloads: boolean;
    status: 'pending' | 'accepted' | 'expired' | 'revoked';
    invited_by: string;
    accepted_at: string | null;
    last_accessed_at: string | null;
    token_expires_at: string | null;
    created_at: string;
    updated_at: string;
    // Enriched fields
    role_name?: string;
    can_comment?: boolean;
    can_request_evidence?: boolean;
    can_add_findings?: boolean;
    can_sign_off?: boolean;
    engagement_name?: string;
    engagement_status?: string;
    invited_by_name?: string;
    invited_by_email?: string;
    token_expired?: boolean;
    within_access_window?: boolean;
    // Token only returned on creation/regeneration
    access_token?: string;
}

export interface CreateEngagementRequest {
    name: string;
    description?: string;
    assessment_id: string;
    audit_period_start?: string;
    audit_period_end?: string;
    planned_start_date?: string;
    planned_end_date?: string;
    in_scope_controls?: string[];
    in_scope_policies?: string[];
    in_scope_chapters?: string[];
    prior_engagement_id?: string;
}

export interface UpdateEngagementRequest {
    name?: string;
    description?: string;
    audit_period_start?: string;
    audit_period_end?: string;
    planned_start_date?: string;
    planned_end_date?: string;
    actual_start_date?: string;
    actual_end_date?: string;
    in_scope_controls?: string[];
    in_scope_policies?: string[];
    in_scope_chapters?: string[];
    prior_engagement_id?: string;
}

export interface CreateInvitationRequest {
    email: string;
    name?: string;
    company?: string;
    auditor_role_id: string;
    access_start?: string;
    access_end?: string;
    mfa_enabled?: boolean;
    ip_allowlist?: string[];
    download_restricted?: boolean;
    watermark_downloads?: boolean;
}

export interface UpdateInvitationRequest {
    name?: string;
    company?: string;
    auditor_role_id?: string;
    access_start?: string;
    access_end?: string;
    mfa_enabled?: boolean;
    ip_allowlist?: string[];
    download_restricted?: boolean;
    watermark_downloads?: boolean;
}

// Dashboard Types
export interface DashboardData {
    engagement_summary: {
        id: string;
        name: string;
        status: string;
        owner_name: string | null;
        framework_name: string | null;
        audit_period: { start: string | null; end: string | null };
        dates: {
            planned_start: string | null;
            actual_start: string | null;
            planned_end: string | null;
            actual_end: string | null;
        };
        active_auditors: number;
        pending_invitations: number;
    };
    findings_by_severity: {
        total: number;
        by_severity: { critical: number; high: number; medium: number; low: number };
        by_status: Record<string, number>;
        open_count: number;
        closed_count: number;
    };
    comments_summary: {
        total: number;
        by_type: Record<string, number>;
        by_status: Record<string, number>;
        open_count: number;
        resolved_count: number;
        overdue_count: number;
        evidence_requests_pending: number;
    };
    review_progress: {
        total_controls: number;
        reviewed: number;
        pending: number;
        percentage: number;
    };
    recent_activity: Array<{
        id: string;
        action: string;
        actor_name: string;
        target_type: string | null;
        created_at: string | null;
    }>;
    sign_off_status: {
        total: number;
        by_type: Record<string, number>;
        by_status: Record<string, number>;
        has_final_sign_off: boolean;
        final_sign_off: { status: string; signed_at: string | null } | null;
    };
    timeline: {
        milestones: Array<{
            event: string;
            date: string | null;
            completed: boolean;
        }>;
        current_status: string;
        days_info: { days_remaining: number; is_overdue: boolean } | null;
    };
}

export interface EngagementComment {
    id: string;
    targetType: string;
    targetId: string;
    content: string;
    commentType: string;
    status: string;
    authorName: string;
    authorType: 'user' | 'auditor';
    createdAt: string;
    replyCount: number;
    replies?: EngagementComment[];
}

export interface ChangeRadarData {
    current_engagement: { id: string; name: string; assessment_id: string | null };
    prior_engagement: { id: string; name: string; assessment_id: string | null };
    generated_at: string;
    summary: {
        total_answer_changes: number;
        new_answers: number;
        modified_answers: number;
        deleted_answers: number;
        unchanged_answers: number;
        total_evidence_changes: number;
        new_evidence: number;
        updated_evidence: number;
        removed_evidence: number;
        unchanged_evidence: number;
        has_significant_changes: boolean;
    };
    answers: {
        new: Array<{ question_id: string; answer_id: string; current_value: string }>;
        modified: Array<{
            question_id: string;
            prior_value: string;
            current_value: string;
            value_changed: boolean;
            status_changed: boolean;
        }>;
        deleted: Array<{ question_id: string; prior_value: string }>;
        unchanged: number;
    };
    evidence: {
        new: Array<{ id: string; filename: string; file_type: string; file_size: number }>;
        updated: Array<{ filename: string; prior_size: number; current_size: number }>;
        removed: Array<{ id: string; filename: string }>;
        unchanged: number;
    };
}

interface UseAuditEngagementStore {
    // State
    engagements: AuditEngagement[];
    selectedEngagement: AuditEngagement | null;
    invitations: AuditorInvitation[];
    auditorRoles: AuditorRole[];
    comments: EngagementComment[];
    dashboard: DashboardData | null;
    changeRadar: ChangeRadarData | null;
    totalCount: number;
    loading: boolean;
    error: string | null;

    // Engagement Actions
    loadEngagements: (statusFilter?: string, ownerOnly?: boolean, skip?: number, limit?: number) => Promise<void>;
    loadEngagement: (engagementId: string) => Promise<AuditEngagement | null>;
    createEngagement: (data: CreateEngagementRequest) => Promise<AuditEngagement>;
    updateEngagement: (engagementId: string, data: UpdateEngagementRequest) => Promise<AuditEngagement>;
    updateEngagementStatus: (engagementId: string, status: string) => Promise<AuditEngagement>;
    deleteEngagement: (engagementId: string) => Promise<void>;
    setSelectedEngagement: (engagement: AuditEngagement | null) => void;

    // Invitation Actions
    loadInvitations: (engagementId: string, statusFilter?: string) => Promise<void>;
    createInvitation: (engagementId: string, data: CreateInvitationRequest) => Promise<AuditorInvitation>;
    updateInvitation: (engagementId: string, invitationId: string, data: UpdateInvitationRequest) => Promise<AuditorInvitation>;
    revokeInvitation: (engagementId: string, invitationId: string) => Promise<void>;
    resendInvitation: (engagementId: string, invitationId: string) => Promise<AuditorInvitation>;

    // Auditor Role Actions
    loadAuditorRoles: () => Promise<void>;

    // Comment Actions
    loadComments: (engagementId: string) => Promise<void>;

    // Dashboard & Analytics Actions
    loadDashboard: (engagementId: string) => Promise<DashboardData | null>;
    loadChangeRadar: (engagementId: string, priorEngagementId?: string) => Promise<ChangeRadarData | null>;
    downloadReviewPack: (engagementId: string) => Promise<void>;
    downloadEvidencePackage: (engagementId: string) => Promise<void>;
    downloadActivityLog: (engagementId: string, format?: 'csv' | 'json') => Promise<void>;

    // Utility
    clearError: () => void;
    clearDashboard: () => void;
    getStatusColor: (status: string) => string;
    getStatusLabel: (status: string) => string;
}

const useAuditEngagementStore = create<UseAuditEngagementStore>((set, get) => ({
    // Initial state
    engagements: [],
    selectedEngagement: null,
    invitations: [],
    auditorRoles: [],
    comments: [],
    dashboard: null,
    changeRadar: null,
    totalCount: 0,
    loading: false,
    error: null,

    // Load all engagements
    loadEngagements: async (statusFilter?: string, ownerOnly: boolean = false, skip: number = 0, limit: number = 100) => {
        set({ loading: true, error: null });
        try {
            const params = new URLSearchParams();
            if (statusFilter) params.append('status_filter', statusFilter);
            if (ownerOnly) params.append('owner_only', 'true');
            params.append('skip', skip.toString());
            params.append('limit', limit.toString());

            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/?${params.toString()}`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to load audit engagements');
            }

            const data = await response.json();
            set({
                engagements: data.engagements,
                totalCount: data.total_count,
                loading: false
            });
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to load audit engagements';
            set({ error: errorMessage, loading: false });
            throw error;
        }
    },

    // Load a single engagement
    loadEngagement: async (engagementId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to load audit engagement');
            }

            const engagement = await response.json();
            set({ selectedEngagement: engagement, loading: false });
            return engagement;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to load audit engagement';
            set({ error: errorMessage, loading: false });
            return null;
        }
    },

    // Create a new engagement
    createEngagement: async (data: CreateEngagementRequest) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify(data)
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to create audit engagement');
            }

            const engagement = await response.json();
            set(state => ({
                engagements: [engagement, ...state.engagements],
                totalCount: state.totalCount + 1,
                loading: false
            }));
            return engagement;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to create audit engagement';
            set({ error: errorMessage, loading: false });
            throw error;
        }
    },

    // Update an engagement
    updateEngagement: async (engagementId: string, data: UpdateEngagementRequest) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify(data)
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to update audit engagement');
            }

            const engagement = await response.json();
            set(state => ({
                engagements: state.engagements.map(e => e.id === engagementId ? engagement : e),
                selectedEngagement: state.selectedEngagement?.id === engagementId ? engagement : state.selectedEngagement,
                loading: false
            }));
            return engagement;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to update audit engagement';
            set({ error: errorMessage, loading: false });
            throw error;
        }
    },

    // Update engagement status
    updateEngagementStatus: async (engagementId: string, status: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}/status`,
                {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify({ status })
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to update engagement status');
            }

            const engagement = await response.json();
            set(state => ({
                engagements: state.engagements.map(e => e.id === engagementId ? engagement : e),
                selectedEngagement: state.selectedEngagement?.id === engagementId ? engagement : state.selectedEngagement,
                loading: false
            }));
            return engagement;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to update engagement status';
            set({ error: errorMessage, loading: false });
            throw error;
        }
    },

    // Delete an engagement
    deleteEngagement: async (engagementId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}`,
                {
                    method: 'DELETE',
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to delete audit engagement');
            }

            set(state => ({
                engagements: state.engagements.filter(e => e.id !== engagementId),
                totalCount: state.totalCount - 1,
                selectedEngagement: state.selectedEngagement?.id === engagementId ? null : state.selectedEngagement,
                loading: false
            }));
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to delete audit engagement';
            set({ error: errorMessage, loading: false });
            throw error;
        }
    },

    setSelectedEngagement: (engagement: AuditEngagement | null) => {
        set({ selectedEngagement: engagement });
    },

    // Load invitations for an engagement
    loadInvitations: async (engagementId: string, statusFilter?: string) => {
        set({ loading: true, error: null });
        try {
            const params = new URLSearchParams();
            if (statusFilter) params.append('status_filter', statusFilter);

            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}/invitations?${params.toString()}`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to load invitations');
            }

            const data = await response.json();
            set({ invitations: data.invitations, loading: false });
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to load invitations';
            set({ error: errorMessage, loading: false });
            throw error;
        }
    },

    // Create a new invitation
    createInvitation: async (engagementId: string, data: CreateInvitationRequest) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}/invitations`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify(data)
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to create invitation');
            }

            const invitation = await response.json();
            set(state => ({
                invitations: [invitation, ...state.invitations],
                loading: false
            }));
            return invitation;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to create invitation';
            set({ error: errorMessage, loading: false });
            throw error;
        }
    },

    // Update an invitation
    updateInvitation: async (engagementId: string, invitationId: string, data: UpdateInvitationRequest) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}/invitations/${invitationId}`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify(data)
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to update invitation');
            }

            const invitation = await response.json();
            set(state => ({
                invitations: state.invitations.map(i => i.id === invitationId ? invitation : i),
                loading: false
            }));
            return invitation;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to update invitation';
            set({ error: errorMessage, loading: false });
            throw error;
        }
    },

    // Revoke an invitation
    revokeInvitation: async (engagementId: string, invitationId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}/invitations/${invitationId}`,
                {
                    method: 'DELETE',
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to revoke invitation');
            }

            set(state => ({
                invitations: state.invitations.map(i =>
                    i.id === invitationId ? { ...i, status: 'revoked' as const } : i
                ),
                loading: false
            }));
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to revoke invitation';
            set({ error: errorMessage, loading: false });
            throw error;
        }
    },

    // Resend an invitation
    resendInvitation: async (engagementId: string, invitationId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}/invitations/${invitationId}/resend`,
                {
                    method: 'POST',
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to resend invitation');
            }

            const invitation = await response.json();
            set(state => ({
                invitations: state.invitations.map(i => i.id === invitationId ? invitation : i),
                loading: false
            }));
            return invitation;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to resend invitation';
            set({ error: errorMessage, loading: false });
            throw error;
        }
    },

    // Load auditor roles
    loadAuditorRoles: async () => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/roles`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to load auditor roles');
            }

            const roles = await response.json();
            set({ auditorRoles: roles });
        } catch (error) {
            console.error('Error loading auditor roles:', error);
        }
    },

    // Load comments for an engagement
    loadComments: async (engagementId: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}/comments`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to load comments');
            }

            const data = await response.json();
            const commentsArray = data.comments || [];

            const mapComment = (c: any): EngagementComment => ({
                id: c.id,
                targetType: c.target_type,
                targetId: c.target_id,
                content: c.content,
                commentType: c.comment_type,
                status: c.status,
                authorName: c.author_name || 'Unknown',
                authorType: c.author_type || (c.author_auditor_id ? 'auditor' : 'user'),
                createdAt: c.created_at,
                replyCount: c.reply_count || 0,
                replies: (c.replies || []).map(mapComment)
            });

            const mappedComments: EngagementComment[] = commentsArray.map(mapComment);
            set({ comments: mappedComments });
        } catch (error) {
            console.error('Error loading comments:', error);
        }
    },

    // Dashboard & Analytics Actions
    loadDashboard: async (engagementId: string) => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}/dashboard`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to load dashboard');
            }

            const dashboard = await response.json();
            set({ dashboard, loading: false });
            return dashboard;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to load dashboard';
            set({ error: errorMessage, loading: false });
            return null;
        }
    },

    loadChangeRadar: async (engagementId: string, priorEngagementId?: string) => {
        set({ loading: true, error: null });
        try {
            const params = new URLSearchParams();
            if (priorEngagementId) {
                params.append('prior_engagement_id', priorEngagementId);
            }

            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}/change-radar?${params.toString()}`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to load change radar');
            }

            const changeRadar = await response.json();
            set({ changeRadar, loading: false });
            return changeRadar;
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to load change radar';
            set({ error: errorMessage, loading: false });
            return null;
        }
    },

    downloadReviewPack: async (engagementId: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}/export/review-pack`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to download review pack');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `review_pack_${engagementId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to download review pack';
            set({ error: errorMessage });
            throw error;
        }
    },

    downloadEvidencePackage: async (engagementId: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}/export/evidence-package`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to download evidence package');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `evidence_package_${engagementId}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to download evidence package';
            set({ error: errorMessage });
            throw error;
        }
    },

    downloadActivityLog: async (engagementId: string, format: 'csv' | 'json' = 'csv') => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit-engagements/${engagementId}/export/activity-log?format=${format}`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to download activity log');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `activity_log_${engagementId}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to download activity log';
            set({ error: errorMessage });
            throw error;
        }
    },

    clearError: () => set({ error: null }),
    clearDashboard: () => set({ dashboard: null, changeRadar: null }),

    // Utility functions
    getStatusColor: (status: string) => {
        const colors: Record<string, string> = {
            draft: 'default',
            planned: 'blue',
            in_progress: 'processing',
            review: 'orange',
            completed: 'success',
            closed: 'default'
        };
        return colors[status] || 'default';
    },

    getStatusLabel: (status: string) => {
        const labels: Record<string, string> = {
            draft: 'Draft',
            planned: 'Planned',
            in_progress: 'In Progress',
            review: 'Under Review',
            completed: 'Completed',
            closed: 'Closed'
        };
        return labels[status] || status;
    }
}));

export default useAuditEngagementStore;
