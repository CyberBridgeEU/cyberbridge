// src/store/useAuthStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

type AuthStore = {
    isAuthenticated: boolean
    user: { email: string, role?: string } | null
    token: string | null
    mustChangePassword: boolean
    login: (email: string, password: string) => Promise<{success: boolean, error?: string}>
    loginWithSSO: (token: string) => void
    logout: () => Promise<void>
    getAuthHeader: () => { Authorization: string } | undefined
    getUserRole: () => string | null
    clearMustChangePassword: () => void
}

// Helper function to check if token is expired
function isTokenExpired(token: string): boolean {
    if (!token) return true;

    try {
        // Get the payload part of the JWT
        const payload = JSON.parse(atob(token.split('.')[1]));

        // Check if the token has an expiration time
        if (payload.exp) {
            // Convert expiration time to milliseconds and compare with current time
            return payload.exp * 1000 < Date.now();
        }

        return false;
    } catch (error) {
        console.error('Error parsing JWT:', error);
        return true;
    }
}

// The `persist` function is used to automatically save and sync the store’s state with the browser’s storage (in this case under the key `"auth-storage"`).
// This ensures that authentication details are preserved across page reloads.
const useAuthStore = create<AuthStore>()(
    persist(
        (set, get) => ({
            isAuthenticated: false,
            user: null,
            token: null,
            mustChangePassword: false,
            login: async (email: string, password: string) => {
                try {
                    const response = await fetch(`${cyberbridge_back_end_rest_api}/auth/token`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded',},
                        body: new URLSearchParams({ username:email, password }),
                    });

                    if (response.ok) {
                        const data = await response.json();
                        console.log('Login response:', data);
                        if (data.access_token) {
                            set({
                                isAuthenticated: true,
                                user: { email, role: data.role },
                                token: data.access_token,
                                mustChangePassword: data.must_change_password || false
                            });
                            return {success: true};
                        }
                    } else {
                        // Handle different HTTP status codes with specific error messages
                        const errorData = await response.json();
                        const errorMessage = errorData.detail || 'Login failed';

                        if (response.status === 400) {
                            // SSO user or other validation error
                            return {success: false, error: errorMessage};
                        } else if (response.status === 403) {
                            // Account not approved or inactive
                            return {success: false, error: errorMessage};
                        } else if (response.status === 401) {
                            // Invalid credentials
                            return {success: false, error: errorMessage};
                        } else {
                            return {success: false, error: 'Login failed. Please try again.'};
                        }
                    }
                    return {success: false, error: 'Login failed. Please try again.'};
                } catch (error) {
                    console.error('Login error:', error);
                    return {success: false, error: 'Network error. Please try again.'};
                }
            },
            loginWithSSO: (token: string) => {
                try {
                    const payload = JSON.parse(atob(token.split('.')[1]));
                    set({
                        isAuthenticated: true,
                        user: { email: payload.sub, role: payload.role },
                        token: token
                    });
                } catch (error) {
                    console.error('Error parsing SSO token:', error);
                }
            },
            logout: async () => {
                // Call backend to update logout timestamp
                try {
                    const token = get().token;
                    if (token && !isTokenExpired(token)) {
                        await fetch(`${cyberbridge_back_end_rest_api}/auth/logout`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Authorization': `Bearer ${token}`
                            }
                        });
                    }
                } catch (error) {
                    console.error('Error calling logout endpoint:', error);
                    // Continue with local logout even if API call fails
                }

                // Update state
                set({ isAuthenticated: false, user: null, token: null, mustChangePassword: false });
                // Remove from sessionStorage
                sessionStorage.removeItem('auth-storage');
            },
            getAuthHeader: () => {
                const token = get().token;

                // Check if token exists and is not expired
                if (token && !isTokenExpired(token)) {
                    return { Authorization: `Bearer ${token}` };
                } else if (token && isTokenExpired(token)) {
                    // If token exists but is expired, logout
                    get().logout();
                }

                return undefined;
            },
            getUserRole: () => {
                const user = get().user;
                return user?.role || null;
            },
            clearMustChangePassword: () => {
                set({ mustChangePassword: false });
            }
        }),
        {
            name: 'auth-storage',
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
)

export default useAuthStore
