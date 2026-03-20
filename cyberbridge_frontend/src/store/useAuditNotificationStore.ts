import { create } from 'zustand';
import { cyberbridge_back_end_rest_api } from '../constants/urls';
import useAuthStore from './useAuthStore';

// Types
export interface AuditNotification {
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

interface UseAuditNotificationStore {
    // State
    notifications: AuditNotification[];
    unreadCount: number;
    totalCount: number;
    reviewStatusCounts: ReviewStatusCounts | null;
    loading: boolean;
    error: string | null;

    // Notification Actions
    loadNotifications: (engagementId?: string, unreadOnly?: boolean) => Promise<void>;
    loadUnreadCount: (engagementId?: string) => Promise<number>;
    markAsRead: (notificationIds?: string[], engagementId?: string) => Promise<void>;
    deleteNotification: (notificationId: string) => Promise<void>;

    // Review Status Actions
    loadReviewStatusCounts: (engagementId: string) => Promise<ReviewStatusCounts | null>;
    getControlReviewStatus: (engagementId: string, answerId: string) => Promise<ControlReviewStatus | null>;
    updateControlReviewStatus: (engagementId: string, answerId: string, status: string, statusNote?: string) => Promise<ControlReviewStatus | null>;

    // Utility
    clearNotifications: () => void;
    clearError: () => void;
    getNotificationTypeLabel: (type: string) => string;
    getNotificationTypeColor: (type: string) => string;
    getReviewStatusLabel: (status: string) => string;
    getReviewStatusColor: (status: string) => string;
}

const useAuditNotificationStore = create<UseAuditNotificationStore>((set, get) => ({
    // Initial state
    notifications: [],
    unreadCount: 0,
    totalCount: 0,
    reviewStatusCounts: null,
    loading: false,
    error: null,

    // Load notifications
    loadNotifications: async (engagementId?: string, unreadOnly: boolean = false) => {
        set({ loading: true, error: null });
        try {
            const params = new URLSearchParams();
            if (engagementId) params.append('engagement_id', engagementId);
            if (unreadOnly) params.append('unread_only', 'true');

            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit/notifications?${params.toString()}`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to load notifications');
            }

            const data = await response.json();
            const mappedNotifications: AuditNotification[] = (data.notifications || []).map((n: any) => ({
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
                unreadCount: data.unread_count || 0,
                totalCount: data.total_count || 0,
                loading: false
            });
        } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Failed to load notifications';
            set({ error: errorMessage, loading: false });
        }
    },

    // Load unread count
    loadUnreadCount: async (engagementId?: string) => {
        try {
            const params = new URLSearchParams();
            if (engagementId) params.append('engagement_id', engagementId);

            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit/notifications/count?${params.toString()}`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                return 0;
            }

            const data = await response.json();
            const count = data.unread_count || 0;
            set({ unreadCount: count });
            return count;
        } catch (error) {
            console.error('Error loading unread count:', error);
            return 0;
        }
    },

    // Mark notifications as read
    markAsRead: async (notificationIds?: string[], engagementId?: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit/notifications/mark-read`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify({
                        notification_ids: notificationIds,
                        engagement_id: engagementId
                    })
                }
            );

            if (!response.ok) {
                throw new Error('Failed to mark notifications as read');
            }

            // Update local state
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
        } catch (error) {
            console.error('Error marking notifications as read:', error);
        }
    },

    // Delete notification
    deleteNotification: async (notificationId: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit/notifications/${notificationId}`,
                {
                    method: 'DELETE',
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                throw new Error('Failed to delete notification');
            }

            set(state => ({
                notifications: state.notifications.filter(n => n.id !== notificationId),
                totalCount: state.totalCount - 1,
                unreadCount: state.notifications.find(n => n.id === notificationId && !n.isRead)
                    ? state.unreadCount - 1
                    : state.unreadCount
            }));
        } catch (error) {
            console.error('Error deleting notification:', error);
        }
    },

    // Load review status counts
    loadReviewStatusCounts: async (engagementId: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit/engagements/${engagementId}/review-status`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                return null;
            }

            const counts = await response.json();
            set({ reviewStatusCounts: counts });
            return counts;
        } catch (error) {
            console.error('Error loading review status counts:', error);
            return null;
        }
    },

    // Get control review status
    getControlReviewStatus: async (engagementId: string, answerId: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit/engagements/${engagementId}/controls/${answerId}/review-status`,
                {
                    headers: {
                        ...useAuthStore.getState().getAuthHeader()
                    }
                }
            );

            if (!response.ok) {
                return null;
            }

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
        } catch (error) {
            console.error('Error getting control review status:', error);
            return null;
        }
    },

    // Update control review status
    updateControlReviewStatus: async (engagementId: string, answerId: string, status: string, statusNote?: string) => {
        try {
            const response = await fetch(
                `${cyberbridge_back_end_rest_api}/audit/engagements/${engagementId}/controls/${answerId}/review-status`,
                {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        ...useAuthStore.getState().getAuthHeader()
                    },
                    body: JSON.stringify({ status, status_note: statusNote })
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to update review status');
            }

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
        } catch (error) {
            console.error('Error updating control review status:', error);
            return null;
        }
    },

    // Utility functions
    clearNotifications: () => set({ notifications: [], unreadCount: 0, totalCount: 0 }),
    clearError: () => set({ error: null }),

    getNotificationTypeLabel: (type: string) => {
        const labels: Record<string, string> = {
            new_comment: 'New Comment',
            comment_reply: 'Comment Reply',
            status_change: 'Status Change',
            information_requested: 'Information Requested',
            response_provided: 'Response Provided',
            finding_added: 'Finding Added',
            sign_off_requested: 'Sign-off Requested'
        };
        return labels[type] || type;
    },

    getNotificationTypeColor: (type: string) => {
        const colors: Record<string, string> = {
            new_comment: 'blue',
            comment_reply: 'cyan',
            status_change: 'orange',
            information_requested: 'red',
            response_provided: 'green',
            finding_added: 'purple',
            sign_off_requested: 'gold'
        };
        return colors[type] || 'default';
    },

    getReviewStatusLabel: (status: string) => {
        const labels: Record<string, string> = {
            not_started: 'Not Started',
            pending_review: 'Pending Review',
            information_requested: 'Information Requested',
            response_provided: 'Response Provided',
            in_review: 'In Review',
            approved: 'Approved',
            approved_with_exceptions: 'Approved with Exceptions',
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
}));

export default useAuditNotificationStore;
