import {create} from 'zustand';
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

export interface Framework {
    id: string;
    name: string;
    description: string;
}

export interface Assessment {
    id: string;
    name: string;
    framework: string;
    framework_id: string;
    user: string;
    user_id: string;
    assessment_type: string;
    completed: boolean;
    progress: number;
    status: string;
    organisation: string;
}

export interface DashboardMetrics {
    totalAssessments: number;
    completedAssessments: number;
    complianceFrameworks: number;
    totalUsers: number;
    totalOrganizations: number;
    totalPolicies: number;
    totalRisks: number;
}

export interface PieChartData {
    inProgress: number;
    completed: number;
}

export interface UserAnalytics {
    userRegistrationTrend: { month: string; count: number }[];
    userRoleDistribution: { role: string; count: number }[];
    userStatusDistribution: { status: string; count: number }[];
}

export interface AssessmentAnalytics {
    assessmentTrend: { month: string; completed: number; inProgress: number }[];
    frameworkCompletion: { framework: string; completion: number; total: number }[];
    assessmentsByType: { type: string; count: number }[];
}

export interface PolicyRiskAnalytics {
    policyStatusDistribution: { status: string; count: number }[];
    riskSeverityDistribution: { severity: string; count: number }[];
    riskStatusDistribution: { status: string; count: number }[];
    productTypeDistribution: { type: string; count: number }[]; // Legacy — always empty, kept for backward compat
}

export interface AssessmentFunnelAnalytics {
    assessmentFunnel: { stage: string; count: number; dropoffRate: number }[];
}

export interface UseDashboardStore {
    // variables
    metrics: DashboardMetrics;
    pieChartData: PieChartData;
    frameworks: Framework[];
    assessments: Assessment[];
    userAnalytics: UserAnalytics;
    assessmentAnalytics: AssessmentAnalytics;
    policyRiskAnalytics: PolicyRiskAnalytics;
    assessmentFunnelAnalytics: AssessmentFunnelAnalytics;
    loading: boolean;
    error: string | null;

    // functions
    fetchDashboardMetrics: () => Promise<boolean>;
    fetchPieChartData: () => Promise<boolean>;
    fetchFrameworks: () => Promise<boolean>;
    fetchAssessments: () => Promise<boolean>;
    fetchUserAnalytics: () => Promise<boolean>;
    fetchAssessmentAnalytics: () => Promise<boolean>;
    fetchPolicyRiskAnalytics: () => Promise<boolean>;
    fetchAssessmentFunnelAnalytics: () => Promise<boolean>;
}

const useDashboardStore = create<UseDashboardStore>(set => ({
    // variables
    metrics: {
        totalAssessments: 0,
        completedAssessments: 0,
        complianceFrameworks: 0,
        totalUsers: 0,
        totalOrganizations: 0,
        totalPolicies: 0,
        totalRisks: 0
    },
    pieChartData: {
        inProgress: 0,
        completed: 0
    },
    frameworks: [],
    assessments: [],
    userAnalytics: {
        userRegistrationTrend: [],
        userRoleDistribution: [],
        userStatusDistribution: []
    },
    assessmentAnalytics: {
        assessmentTrend: [],
        frameworkCompletion: [],
        assessmentsByType: []
    },
    policyRiskAnalytics: {
        policyStatusDistribution: [],
        riskSeverityDistribution: [],
        riskStatusDistribution: [],
        productTypeDistribution: []
    },
    assessmentFunnelAnalytics: {
        assessmentFunnel: []
    },
    loading: false,
    error: null,

    fetchDashboardMetrics: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/dashboard/metrics`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            set({ metrics: data, loading: false });
            return true;
        } catch (error) {
            console.error('Error fetching dashboard metrics:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch dashboard metrics',
                loading: false
            });
            return false;
        }
    },

    fetchPieChartData: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/dashboard/pie-chart-data`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            set({ pieChartData: data, loading: false });
            return true;
        } catch (error) {
            console.error('Error fetching pie chart data:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch pie chart data',
                loading: false
            });
            return false;
        }
    },

    fetchFrameworks: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/dashboard/frameworks`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            set({ frameworks: data, loading: false });
            return true;
        } catch (error) {
            console.error('Error fetching frameworks:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch frameworks',
                loading: false
            });
            return false;
        }
    },

    fetchAssessments: async () => {
        set({ loading: true, error: null });
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/dashboard/assessments`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false;
            }
            const data = await response.json();
            // Map the backend data to include status field and use progress from backend
            const mappedData = data.map((assessment: any) => ({
                ...assessment,
                status: assessment.completed ? 'Completed' : 'In Progress'
            }));
            set({ assessments: mappedData, loading: false });
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

    fetchUserAnalytics: async () => {
        console.log('🔍 fetchUserAnalytics called');
        set({ loading: true, error: null });
        try {
            console.log('📡 Making request to:', `${cyberbridge_back_end_rest_api}/dashboard/user-analytics`);
            const response = await fetch(`${cyberbridge_back_end_rest_api}/dashboard/user-analytics`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            console.log('📡 Response status:', response.status);
            if (!response.ok) {
                console.error('❌ User analytics response not ok:', response.status, response.statusText);
                return false;
            }
            const data = await response.json();
            console.log('✅ User analytics data received:', data);
            set({ userAnalytics: data, loading: false });
            return true;
        } catch (error) {
            console.error('Error fetching user analytics:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch user analytics',
                loading: false
            });
            return false;
        }
    },

    fetchAssessmentAnalytics: async () => {
        console.log('🔍 fetchAssessmentAnalytics called');
        set({ loading: true, error: null });
        try {
            console.log('📡 Making request to:', `${cyberbridge_back_end_rest_api}/dashboard/assessment-analytics`);
            const response = await fetch(`${cyberbridge_back_end_rest_api}/dashboard/assessment-analytics`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            console.log('📡 Response status:', response.status);
            if (!response.ok) {
                console.error('❌ Assessment analytics response not ok:', response.status, response.statusText);
                return false;
            }
            const data = await response.json();
            console.log('✅ Assessment analytics data received:', data);
            set({ assessmentAnalytics: data, loading: false });
            return true;
        } catch (error) {
            console.error('Error fetching assessment analytics:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch assessment analytics',
                loading: false
            });
            return false;
        }
    },

    fetchPolicyRiskAnalytics: async () => {
        console.log('🔍 fetchPolicyRiskAnalytics called');
        set({ loading: true, error: null });
        try {
            console.log('📡 Making request to:', `${cyberbridge_back_end_rest_api}/dashboard/policy-risk-analytics`);
            const response = await fetch(`${cyberbridge_back_end_rest_api}/dashboard/policy-risk-analytics`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            console.log('📡 Response status:', response.status);
            if (!response.ok) {
                console.error('❌ Policy risk analytics response not ok:', response.status, response.statusText);
                return false;
            }
            const data = await response.json();
            console.log('✅ Policy risk analytics data received:', data);
            set({ policyRiskAnalytics: data, loading: false });
            return true;
        } catch (error) {
            console.error('Error fetching policy risk analytics:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch policy risk analytics',
                loading: false
            });
            return false;
        }
    },

    fetchAssessmentFunnelAnalytics: async () => {
        console.log('🔍 fetchAssessmentFunnelAnalytics called');
        set({ loading: true, error: null });
        try {
            console.log('📡 Making request to:', `${cyberbridge_back_end_rest_api}/dashboard/assessment-funnel`);
            const response = await fetch(`${cyberbridge_back_end_rest_api}/dashboard/assessment-funnel`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            console.log('📡 Response status:', response.status);
            if (!response.ok) {
                console.error('❌ Assessment funnel analytics response not ok:', response.status, response.statusText);
                return false;
            }
            const data = await response.json();
            console.log('✅ Assessment funnel analytics data received:', data);
            set({ assessmentFunnelAnalytics: data, loading: false });
            return true;
        } catch (error) {
            console.error('Error fetching assessment funnel analytics:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch assessment funnel analytics',
                loading: false
            });
            return false;
        }
    }
}));

export default useDashboardStore;
