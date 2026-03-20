// src/components/ProtectedRoute.tsx
import { ReactNode, useEffect } from 'react'
import { Redirect } from 'wouter'
import useAuthStore from '../store/useAuthStore'
import useUserStore from '../store/useUserStore'
import useFrameworksStore from '../store/useFrameworksStore'
import useCRAModeStore from '../store/useCRAModeStore'

type ProtectedRouteProps = {
    children: ReactNode
    requiresCRAMode?: boolean
}

const ProtectedRoute = ({ children, requiresCRAMode }: ProtectedRouteProps) => {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
    const mustChangePassword = useAuthStore((state) => state.mustChangePassword)
    const getAuthHeader = useAuthStore((state) => state.getAuthHeader)
    const { fetchCurrentUser, current_user } = useUserStore()
    const { frameworks, fetchFrameworks } = useFrameworksStore()
    const { craMode, loading: craModeLoading, fetchCRAMode } = useCRAModeStore()

    useEffect(() => {
        // Fetch current user information if authenticated, has valid token, and current_user is empty
        const authHeader = getAuthHeader()
        if (isAuthenticated && authHeader && (!current_user || !current_user.email)) {
            fetchCurrentUser()
        }
    }, [isAuthenticated, getAuthHeader, current_user, fetchCurrentUser])

    useEffect(() => {
        // Fetch frameworks once at app startup so CRA mode filtering works
        if (isAuthenticated && frameworks.length === 0) {
            fetchFrameworks()
        }
    }, [isAuthenticated, frameworks.length, fetchFrameworks])

    useEffect(() => {
        // Fetch CRA mode from backend once the user and their org are known
        if (isAuthenticated && current_user?.organisation_id) {
            fetchCRAMode(current_user.organisation_id)
        }
    }, [isAuthenticated, current_user?.organisation_id, fetchCRAMode])

    if (!isAuthenticated) {
        return <Redirect to="/login" />
    }

    if (mustChangePassword) {
        return <Redirect to="/force-change-password" />
    }

    // Block CRA-only routes when CRA mode is off
    if (requiresCRAMode && !craModeLoading && craMode === null) {
        return <Redirect to="/home" />
    }

    return <>{children}</>
}

export default ProtectedRoute
