// src/store/useAuditorStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

// Types
export interface AuditorSession {
    token: string;
    expiresInHours: number;
    engagementId: string;
    engagementName: string | null;
    roleName: string | null;
    canComment: boolean;
    canRequestEvidence: boolean;
    canAddFindings: boolean;
    canSignOff: boolean;
    mfaRequired: boolean;
    mfaSetupRequired: boolean;
    downloadRestricted: boolean;
    watermarkDownloads: boolean;
}

export interface TokenVerificationResult {
    valid: boolean;
    invitationId: string | null;
    email: string | null;
    name: string | null;
    engagementName: string | null;
    mfaEnabled: boolean;
    mfaSetupRequired: boolean;
    message: string;
}

export interface MFASetupResult {
    secret: string;
    provisioningUri: string;
    qrCodeBase64: string;
}

export interface EngagementReviewData {
    id: string;
    name: string;
    description: string | null;
    assessmentId: string;
    assessmentName: string | null;
    frameworkId: string | null;
    frameworkName: string | null;
    status: string;
    auditPeriodStart: string | null;
    auditPeriodEnd: string | null;
    inScopeControls: string[];
    inScopePolicies: string[];
    inScopeChapters: string[];
    organisationName: string | null;
}

export interface ReviewControl {
    id: string;
    questionId: string;
    questionText: string;
    chapterId: string;
    chapterName: string;
    answerId: string | null;
    answerStatus: string | null;
    answerNotes: string | null;
    evidenceCount: number;
    commentCount: number;
    reviewStatus: 'not_reviewed' | 'in_progress' | 'reviewed' | 'signed_off';
}

export interface ReviewEvidence {
    id: string;
    name: string;
    description: string | null;
    filePath: string;
    fileType: string;
    fileSize: number;
    uploadedAt: string;
    answerId: string;
    questionText: string;
}

export interface ReviewPolicy {
    id: string;
    name: string;
    description: string | null;
    version: string | null;
    status: string;
    reviewDate: string | null;
    filePath: string | null;
}

export interface ReviewObjective {
    id: string;
    name: string;
    description: string | null;
    chapterId: string;
    chapterName: string;
    complianceStatus: string | null;
    linkedPoliciesCount: number;
}

export interface ReviewQueueItem {
    id: string;
    type: 'control' | 'evidence' | 'policy' | 'objective';
    name: string;
    status: string;
    priority: 'high' | 'medium' | 'low';
    dueDate: string | null;
    assignedTo: string | null;
}

export interface AuditComment {
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
    replies?: AuditComment[];
}

export interface AuditorNotification {
    id: string;
    engagementId: string;
    notificationType: string;
    sourceType: string;
    sourceId: string;
    relatedAnswerId: string | null;
    title: string;
    message: string | null;
    senderName: string | null;
    isRead: boolean;
    readAt: string | null;
    createdAt: string;
}

export interface ReviewStatusCounts {
    not_started: number;
    pending_review: number;
    information_requested: number;
    response_provided: number;
    in_review: number;
    approved: number;
    approved_with_exceptions: number;
    needs_remediation: number;
}

export interface ControlReviewStatus {
    id: string;
    engagementId: string;
    answerId: string;
    status: string;
    statusNote: string | null;
    lastUpdatedByName: string | null;
    createdAt: string | null;
    updatedAt: string | null;
}

type AuditorStore = {
    // Auth state
    isAuthenticated: boolean;
    session: AuditorSession | null;
    invitationId: string | null;
    email: string | null;
    name: string | null;

    // Review data
    engagement: EngagementReviewData | null;
    controls: ReviewControl[];
    evidence: ReviewEvidence[];
    policies: ReviewPolicy[];
    objectives: ReviewObjective[];
    reviewQueue: ReviewQueueItem[];
    comments: AuditComment[];

    // Notifications
    notifications: AuditorNotification[];
    unreadCount: number;
    reviewStatusCounts: ReviewStatusCounts | null;

    // Loading states
    isLoading: boolean;
    error: string | null;

    // Auth actions
    verifyToken: (accessToken: string) => Promise<TokenVerificationResult>;
    setupMFA: (accessToken: string) => Promise<MFASetupResult>;
    verifyMFA: (invitationId: string, code: string) => Promise<boolean>;
    login: (accessToken: string, mfaCode?: string) => Promise<{success: boolean, error?: string}>;
    logout: () => void;
    requestMagicLink: (email: string) => Promise<{success: boolean, message: string}>;

    // Review data actions
    loadEngagement: () => Promise<void>;
    loadControls: () => Promise<void>;
    loadEvidence: () => Promise<void>;
    loadPolicies: () => Promise<void>;
    loadObjectives: () => Promise<void>;
    loadReviewQueue: () => Promise<void>;
    getEvidencePreviewUrl: (evidenceId: string) => string;

    // Comment actions
    loadComments: (targetType?: string, targetId?: string) => Promise<void>;
    createComment: (targetType: string, targetId: string, content: string, commentType?: string) => Promise<{success: boolean, error?: string}>;

    // Notification actions
    loadNotifications: (unreadOnly?: boolean) => Promise<void>;
    loadUnreadCount: () => Promise<number>;
    markNotificationsAsRead: (notificationIds?: string[]) => Promise<void>;

    // Review status actions
    loadReviewStatusCounts: () => Promise<ReviewStatusCounts | null>;
    getControlReviewStatus: (answerId: string) => Promise<ControlReviewStatus | null>;
    updateControlReviewStatus: (answerId: string, status: string, statusNote?: string) => Promise<ControlReviewStatus | null>;

    // Helpers
    getAuthHeader: () => { Authorization: string } | undefined;
    clearError: () => void;
    getReviewStatusLabel: (status: string) => string;
    getReviewStatusColor: (status: string) => string;
}

// Helper function to check if token is expired
function isTokenExpired(token: string): boolean {
    if (!token) return true;
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.exp) {
            return payload.exp * 1000 < Date.now();
        }
        return false;
    } catch (error) {
        console.error('Error parsing JWT:', error);
        return true;
    }
}

const useAuditorStore = create<AuditorStore>()(
    persist(
        (set, get) => ({
            // Initial state
            isAuthenticated: false,
            session: null,
            invitationId: null,
            email: null,
            name: null,
            engagement: null,
            controls: [],
            evidence: [],
            policies: [],
            objectives: [],
            reviewQueue: [],
            comments: [],
            notifications: [],
            unreadCount: 0,
            reviewStatusCounts: null,
            isLoading: false,
            error: null,

            // Verify magic link token
            verifyToken: async (accessToken: string): Promise<TokenVerificationResult> => {
                set({ isLoading: true, error: null });
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/auditor/auth/verify-token`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ access_token: accessToken })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        set({
                            invitationId: data.invitation_id,
                            email: data.email,
                            name: data.name,
                            isLoading: false
                        });
                        return {
                            valid: data.valid,
                            invitationId: data.invitation_id,
                            email: data.email,
                            name: data.name,
                            engagementName: data.engagement_name,
                            mfaEnabled: data.mfa_enabled,
                            mfaSetupRequired: data.mfa_setup_required,
                            message: data.message
                        };
                    } else {
                        set({ isLoading: false, error: data.detail || 'Token verification failed' });
                        return {
                            valid: false,
                            invitationId: null,
                            email: null,
                            name: null,
                            engagementName: null,
                            mfaEnabled: false,
                            mfaSetupRequired: false,
                            message: data.detail || 'Token verification failed'
                        };
                    }
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                    return {
                        valid: false,
                        invitationId: null,
                        email: null,
                        name: null,
                        engagementName: null,
                        mfaEnabled: false,
                        mfaSetupRequired: false,
                        message
                    };
                }
            },

            // Setup MFA
            setupMFA: async (accessToken: string): Promise<MFASetupResult> => {
                set({ isLoading: true, error: null });
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/auditor/auth/mfa/setup`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ access_token: accessToken })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        set({ isLoading: false });
                        return {
                            secret: data.secret,
                            provisioningUri: data.provisioning_uri,
                            qrCodeBase64: data.qr_code_base64
                        };
                    } else {
                        set({ isLoading: false, error: data.detail || 'MFA setup failed' });
                        throw new Error(data.detail || 'MFA setup failed');
                    }
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                    throw error;
                }
            },

            // Verify MFA code
            verifyMFA: async (invitationId: string, code: string): Promise<boolean> => {
                set({ isLoading: true, error: null });
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/auditor/auth/mfa/verify`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ invitation_id: invitationId, code })
                    });

                    const data = await response.json();
                    set({ isLoading: false });

                    if (response.ok && data.success) {
                        return true;
                    } else {
                        set({ error: data.detail || 'Invalid MFA code' });
                        return false;
                    }
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                    return false;
                }
            },

            // Login with token and optional MFA code
            login: async (accessToken: string, mfaCode?: string): Promise<{success: boolean, error?: string}> => {
                set({ isLoading: true, error: null });
                try {
                    const url = new URL(`${cyberbridge_back_end_rest_api}/auditor/auth/login`);
                    if (mfaCode) {
                        url.searchParams.append('mfa_code', mfaCode);
                    }

                    const response = await fetch(url.toString(), {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ access_token: accessToken })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        // Check if MFA setup is required
                        if (data.mfa_setup_required) {
                            set({ isLoading: false });
                            return { success: false, error: 'MFA_SETUP_REQUIRED' };
                        }

                        // Check if MFA code is required but not provided
                        if (data.mfa_required && !data.token) {
                            set({ isLoading: false });
                            return { success: false, error: 'MFA_CODE_REQUIRED' };
                        }

                        const session: AuditorSession = {
                            token: data.token,
                            expiresInHours: data.expires_in_hours,
                            engagementId: data.engagement_id,
                            engagementName: data.engagement_name,
                            roleName: data.role_name,
                            canComment: data.can_comment,
                            canRequestEvidence: data.can_request_evidence,
                            canAddFindings: data.can_add_findings,
                            canSignOff: data.can_sign_off,
                            mfaRequired: data.mfa_required,
                            mfaSetupRequired: data.mfa_setup_required,
                            downloadRestricted: data.download_restricted || false,
                            watermarkDownloads: data.watermark_downloads || false
                        };

                        set({
                            isAuthenticated: true,
                            session,
                            isLoading: false
                        });

                        return { success: true };
                    } else {
                        set({ isLoading: false, error: data.detail || 'Login failed' });
                        return { success: false, error: data.detail || 'Login failed' };
                    }
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                    return { success: false, error: message };
                }
            },

            // Logout
            logout: () => {
                set({
                    isAuthenticated: false,
                    session: null,
                    invitationId: null,
                    email: null,
                    name: null,
                    engagement: null,
                    controls: [],
                    evidence: [],
                    policies: [],
                    objectives: [],
                    reviewQueue: [],
                    comments: [],
                    notifications: [],
                    unreadCount: 0,
                    reviewStatusCounts: null,
                    error: null
                });
                sessionStorage.removeItem('auditor-storage');
            },

            // Request magic link
            requestMagicLink: async (email: string): Promise<{success: boolean, message: string}> => {
                set({ isLoading: true, error: null });
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/auditor/auth/request-magic-link`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email })
                    });

                    const data = await response.json();
                    set({ isLoading: false });

                    return {
                        success: data.success || response.ok,
                        message: data.message || 'If you have an active invitation, a login link has been sent to your email.'
                    };
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                    return { success: false, message };
                }
            },

            // Load engagement details
            loadEngagement: async () => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return;

                set({ isLoading: true, error: null });
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/auditor/review/engagement`, {
                        headers: { ...authHeader }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        set({
                            engagement: {
                                id: data.id,
                                name: data.name,
                                description: data.description,
                                assessmentId: data.assessment_id,
                                assessmentName: data.assessment_name,
                                frameworkId: data.framework_id,
                                frameworkName: data.framework_name,
                                status: data.status,
                                auditPeriodStart: data.audit_period_start,
                                auditPeriodEnd: data.audit_period_end,
                                inScopeControls: data.in_scope_controls || [],
                                inScopePolicies: data.in_scope_policies || [],
                                inScopeChapters: data.in_scope_chapters || [],
                                organisationName: data.organisation_name
                            },
                            isLoading: false
                        });
                    } else {
                        const data = await response.json();
                        set({ isLoading: false, error: data.detail || 'Failed to load engagement' });
                    }
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                }
            },

            // Load controls
            loadControls: async () => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return;

                set({ isLoading: true, error: null });
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/auditor/review/controls`, {
                        headers: { ...authHeader }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        // Ensure data is an array
                        const controlsArray = Array.isArray(data) ? data : [];
                        set({
                            controls: controlsArray.map((c: any) => ({
                                id: c.id,
                                questionId: c.question_id || c.id,
                                questionText: c.question_text,
                                chapterId: c.chapter_id || '',
                                chapterName: c.chapter_name || 'General',
                                answerId: c.id, // The control id is the answer id
                                answerStatus: c.answer_value ? 'answered' : 'not_answered',
                                answerNotes: c.evidence_description || c.answer_notes,
                                evidenceCount: c.evidence_count || 0,
                                commentCount: c.comment_count || 0,
                                reviewStatus: c.review_status || 'not_reviewed'
                            })),
                            isLoading: false
                        });
                    } else {
                        const data = await response.json();
                        set({ isLoading: false, error: data.detail || 'Failed to load controls' });
                    }
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                }
            },

            // Load evidence
            loadEvidence: async () => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return;

                set({ isLoading: true, error: null });
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/auditor/review/evidence`, {
                        headers: { ...authHeader }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        // Ensure data is an array
                        const evidenceArray = Array.isArray(data) ? data : [];
                        set({
                            evidence: evidenceArray.map((e: any) => ({
                                id: e.id,
                                name: e.filename || e.name,
                                description: e.description,
                                filePath: e.filepath || e.file_path,
                                fileType: e.file_type,
                                fileSize: e.file_size,
                                uploadedAt: e.uploaded_at,
                                answerId: e.answer_id,
                                questionText: e.question_text
                            })),
                            isLoading: false
                        });
                    } else {
                        const data = await response.json();
                        set({ isLoading: false, error: data.detail || 'Failed to load evidence' });
                    }
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                }
            },

            // Load policies
            loadPolicies: async () => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return;

                set({ isLoading: true, error: null });
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/auditor/review/policies`, {
                        headers: { ...authHeader }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        // API returns { policies: [...], total_count: n }
                        const policiesArray = data.policies || [];
                        set({
                            policies: policiesArray.map((p: any) => ({
                                id: p.id,
                                name: p.title || p.name,
                                description: p.body_preview || p.description,
                                version: p.version,
                                status: p.status,
                                reviewDate: p.updated_at || p.review_date,
                                filePath: p.file_path
                            })),
                            isLoading: false
                        });
                    } else {
                        const data = await response.json();
                        set({ isLoading: false, error: data.detail || 'Failed to load policies' });
                    }
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                }
            },

            // Load objectives
            loadObjectives: async () => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return;

                set({ isLoading: true, error: null });
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/auditor/review/objectives`, {
                        headers: { ...authHeader }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        // API returns { chapters: [...] } where each chapter has objectives array
                        const chapters = data.chapters || [];
                        const flattenedObjectives: any[] = [];

                        chapters.forEach((chapter: any) => {
                            const chapterObjectives = chapter.objectives || [];
                            chapterObjectives.forEach((obj: any) => {
                                flattenedObjectives.push({
                                    id: obj.id,
                                    name: obj.title || obj.name,
                                    description: obj.requirement_description || obj.description,
                                    chapterId: chapter.id,
                                    chapterName: chapter.title,
                                    complianceStatus: obj.compliance_status,
                                    linkedPoliciesCount: obj.linked_policies_count || 0
                                });
                            });
                        });

                        set({
                            objectives: flattenedObjectives,
                            isLoading: false
                        });
                    } else {
                        const data = await response.json();
                        set({ isLoading: false, error: data.detail || 'Failed to load objectives' });
                    }
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                }
            },

            // Load review queue
            loadReviewQueue: async () => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return;

                set({ isLoading: true, error: null });
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/auditor/review/queue`, {
                        headers: { ...authHeader }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        // Ensure data is an array
                        const queueArray = Array.isArray(data) ? data : [];
                        set({
                            reviewQueue: queueArray.map((item: any) => ({
                                id: item.id,
                                type: item.item_type || item.type,
                                name: item.title || item.name,
                                status: item.status,
                                priority: item.priority || 'medium',
                                dueDate: item.due_date,
                                assignedTo: item.assigned_to
                            })),
                            isLoading: false
                        });
                    } else {
                        const data = await response.json();
                        set({ isLoading: false, error: data.detail || 'Failed to load review queue' });
                    }
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                }
            },

            // Get evidence preview URL
            getEvidencePreviewUrl: (evidenceId: string): string => {
                const session = get().session;
                if (!session) return '';
                return `${cyberbridge_back_end_rest_api}/auditor/review/evidence/${evidenceId}/preview?token=${session.token}`;
            },

            // Load comments
            loadComments: async (targetType?: string, targetId?: string) => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return;

                set({ isLoading: true, error: null });
                try {
                    let url = `${cyberbridge_back_end_rest_api}/auditor/review/comments`;
                    const params = new URLSearchParams();
                    if (targetType) params.append('target_type', targetType);
                    if (targetId) params.append('target_id', targetId);
                    if (params.toString()) url += `?${params.toString()}`;

                    const response = await fetch(url, {
                        headers: { ...authHeader }
                    });

                    if (response.ok) {
                        const data = await response.json();
                        const commentsArray = Array.isArray(data) ? data : [];

                        const mapComment = (c: any): AuditComment => ({
                            id: c.id,
                            targetType: c.target_type,
                            targetId: c.target_id,
                            content: c.content,
                            commentType: c.comment_type,
                            status: c.status,
                            authorName: c.author_name,
                            authorType: c.author_type,
                            createdAt: c.created_at,
                            replyCount: c.reply_count || 0,
                            replies: (c.replies || []).map(mapComment)
                        });

                        set({
                            comments: commentsArray.map(mapComment),
                            isLoading: false
                        });
                    } else {
                        const data = await response.json();
                        set({ isLoading: false, error: data.detail || 'Failed to load comments' });
                    }
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                }
            },

            // Create a comment
            createComment: async (targetType: string, targetId: string, content: string, commentType: string = 'observation'): Promise<{success: boolean, error?: string}> => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return { success: false, error: 'Not authenticated' };

                set({ isLoading: true, error: null });
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/auditor/review/comments`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            ...authHeader
                        },
                        body: JSON.stringify({
                            target_type: targetType,
                            target_id: targetId,
                            content,
                            comment_type: commentType
                        })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        // Add the new comment to the list
                        const newComment = {
                            id: data.id,
                            targetType: data.target_type,
                            targetId: data.target_id,
                            content: data.content,
                            commentType: data.comment_type,
                            status: data.status,
                            authorName: data.author_name,
                            authorType: data.author_type as 'user' | 'auditor',
                            createdAt: data.created_at,
                            replyCount: data.reply_count || 0
                        };

                        set((state) => ({
                            comments: [newComment, ...state.comments],
                            isLoading: false
                        }));

                        return { success: true };
                    } else {
                        set({ isLoading: false, error: data.detail || 'Failed to create comment' });
                        return { success: false, error: data.detail || 'Failed to create comment' };
                    }
                } catch (error) {
                    const message = error instanceof Error ? error.message : 'Network error';
                    set({ isLoading: false, error: message });
                    return { success: false, error: message };
                }
            },

            // Load notifications
            loadNotifications: async (unreadOnly: boolean = false) => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return;

                try {
                    const params = new URLSearchParams();
                    if (unreadOnly) params.append('unread_only', 'true');

                    const response = await fetch(
                        `${cyberbridge_back_end_rest_api}/auditor/review/notifications?${params.toString()}`,
                        { headers: authHeader }
                    );

                    if (response.ok) {
                        const data = await response.json();
                        const mappedNotifications = (data.notifications || []).map((n: any) => ({
                            id: n.id,
                            engagementId: n.engagement_id,
                            notificationType: n.notification_type,
                            sourceType: n.source_type,
                            sourceId: n.source_id,
                            relatedAnswerId: n.related_answer_id,
                            title: n.title,
                            message: n.message,
                            senderName: n.sender_name,
                            isRead: n.is_read,
                            readAt: n.read_at,
                            createdAt: n.created_at
                        }));
                        set({
                            notifications: mappedNotifications,
                            unreadCount: data.unread_count || 0
                        });
                    }
                } catch (error) {
                    console.error('Error loading notifications:', error);
                }
            },

            // Load unread count
            loadUnreadCount: async () => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return 0;

                try {
                    const response = await fetch(
                        `${cyberbridge_back_end_rest_api}/auditor/review/notifications/count`,
                        { headers: authHeader }
                    );

                    if (response.ok) {
                        const data = await response.json();
                        const count = data.unread_count || 0;
                        set({ unreadCount: count });
                        return count;
                    }
                    return 0;
                } catch (error) {
                    console.error('Error loading unread count:', error);
                    return 0;
                }
            },

            // Mark notifications as read
            markNotificationsAsRead: async (notificationIds?: string[]) => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return;

                try {
                    const response = await fetch(
                        `${cyberbridge_back_end_rest_api}/auditor/review/notifications/mark-read`,
                        {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', ...authHeader },
                            body: JSON.stringify(notificationIds || null)
                        }
                    );

                    if (response.ok) {
                        if (notificationIds) {
                            set(state => ({
                                notifications: state.notifications.map(n =>
                                    notificationIds.includes(n.id) ? { ...n, isRead: true } : n
                                ),
                                unreadCount: Math.max(0, state.unreadCount - notificationIds.length)
                            }));
                        } else {
                            set(state => ({
                                notifications: state.notifications.map(n => ({ ...n, isRead: true })),
                                unreadCount: 0
                            }));
                        }
                    }
                } catch (error) {
                    console.error('Error marking notifications as read:', error);
                }
            },

            // Load review status counts
            loadReviewStatusCounts: async () => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return null;

                try {
                    const response = await fetch(
                        `${cyberbridge_back_end_rest_api}/auditor/review/review-status/summary`,
                        { headers: authHeader }
                    );

                    if (response.ok) {
                        const counts = await response.json();
                        set({ reviewStatusCounts: counts });
                        return counts;
                    }
                    return null;
                } catch (error) {
                    console.error('Error loading review status counts:', error);
                    return null;
                }
            },

            // Get control review status
            getControlReviewStatus: async (answerId: string) => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return null;

                try {
                    const response = await fetch(
                        `${cyberbridge_back_end_rest_api}/auditor/review/controls/${answerId}/review-status`,
                        { headers: authHeader }
                    );

                    if (response.ok) {
                        const data = await response.json();
                        return {
                            id: data.id,
                            engagementId: data.engagement_id,
                            answerId: data.answer_id,
                            status: data.status,
                            statusNote: data.status_note,
                            lastUpdatedByName: data.last_updated_by_name,
                            createdAt: data.created_at,
                            updatedAt: data.updated_at
                        };
                    }
                    return null;
                } catch (error) {
                    console.error('Error getting control review status:', error);
                    return null;
                }
            },

            // Update control review status
            updateControlReviewStatus: async (answerId: string, status: string, statusNote?: string) => {
                const authHeader = get().getAuthHeader();
                if (!authHeader) return null;

                try {
                    const response = await fetch(
                        `${cyberbridge_back_end_rest_api}/auditor/review/controls/${answerId}/review-status`,
                        {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json', ...authHeader },
                            body: JSON.stringify({ status, status_note: statusNote })
                        }
                    );

                    if (response.ok) {
                        const data = await response.json();
                        // Reload review status counts
                        get().loadReviewStatusCounts();
                        return {
                            id: data.id,
                            engagementId: data.engagement_id,
                            answerId: data.answer_id,
                            status: data.status,
                            statusNote: data.status_note,
                            lastUpdatedByName: data.last_updated_by_name,
                            createdAt: data.created_at,
                            updatedAt: data.updated_at
                        };
                    }
                    return null;
                } catch (error) {
                    console.error('Error updating control review status:', error);
                    return null;
                }
            },

            // Get auth header
            getAuthHeader: () => {
                const session = get().session;
                if (session?.token && !isTokenExpired(session.token)) {
                    return { Authorization: `Bearer ${session.token}` };
                } else if (session?.token && isTokenExpired(session.token)) {
                    get().logout();
                }
                return undefined;
            },

            // Clear error
            clearError: () => {
                set({ error: null });
            },

            // Helper functions
            getReviewStatusLabel: (status: string) => {
                const labels: Record<string, string> = {
                    not_started: 'Not Started',
                    pending_review: 'Pending Review',
                    information_requested: 'Info Requested',
                    response_provided: 'Response Provided',
                    in_review: 'In Review',
                    approved: 'Approved',
                    approved_with_exceptions: 'Approved*',
                    needs_remediation: 'Needs Remediation'
                };
                return labels[status] || status;
            },

            getReviewStatusColor: (status: string) => {
                const colors: Record<string, string> = {
                    not_started: 'default',
                    pending_review: 'processing',
                    information_requested: 'warning',
                    response_provided: 'cyan',
                    in_review: 'blue',
                    approved: 'success',
                    approved_with_exceptions: 'orange',
                    needs_remediation: 'error'
                };
                return colors[status] || 'default';
            }
        }),
        {
            name: 'auditor-storage',
            storage: {
                getItem: (name) => {
                    const value = sessionStorage.getItem(name);
                    return value ? JSON.parse(value) : null;
                },
                setItem: (name, value) => {
                    sessionStorage.setItem(name, JSON.stringify(value));
                },
                removeItem: (name) => {
                    sessionStorage.removeItem(name);
                }
            }
        }
    )
);

export default useAuditorStore;
