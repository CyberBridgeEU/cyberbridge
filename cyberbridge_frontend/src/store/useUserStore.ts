import {create} from 'zustand';
import useAuthStore from "./useAuthStore.ts";
import { cyberbridge_back_end_rest_api } from "../constants/urls.ts";

export interface Organisation{
    id: string | null;
    name: string;
    domain: string;
    logo: string;
}

export interface Role{
    id: string;
    role_name: string;
}

export interface User {
    id: string;
    email: string;
    role_id: string;
    organisation_id: string;
    status: string;
    role_name: string;
    organisation_name: string;
    organisation_logo: string | undefined;
    organisation_domain: string | undefined;
    auth_provider: string;  // 'local' | 'google' | 'microsoft'
}

export interface UseUserStore {
    //variables
    organisations: Organisation[];
    roles: Role[];
    current_user: User;
    users: User[];
    loading: boolean;
    error: string | null;
    //functions
    fetchCurrentUser: () => Promise<boolean>;
    fetchUsers: () => Promise<boolean>;
    fetchOrganisationUsers: (id: string) => Promise<boolean>;
    clearUsers: () => void;
    fetchRoles: () => Promise<boolean>;
    fetchOrganisations: () => Promise<boolean>;
    createOrUpdateOrganisation: (name:string, domain:string, logo:string, id: string | null) => Promise<boolean>;
    createUser: (email:string, password:string,role_id:string, organisation_id:string, auth_provider?:string) => Promise<boolean>;
    updateUser: (email:string | null, password:string | null, role_id:string | null, user_id:string) => Promise<boolean>;
    deleteUser: (user_id: string) => Promise<boolean>;
    deleteOrganisation: (organisation_id: string) => Promise<boolean>;
}

const useUserStore = create<UseUserStore>(set => ({
    //variables
    organisations: [],
    roles: [],
    // currentOrg: {} as Organisation,
    current_user: {} as User,
    users: [],
    loading: false,
    error: null,

    fetchCurrentUser: async () => {
        set({ loading: true, error: null });
        const payload = JSON.stringify({...useAuthStore.getState().user})
        console.log('Request payload:', payload);
        console.log(useAuthStore.getState().getAuthHeader())
        try{
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/get_current_user_by_email`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });
            if (!response.ok) {
                return false
            }
            const data = await response.json();
            console.log(data);
            set({current_user: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching user:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch user',
                loading: false
            });
            return false;
        }
    },

    fetchUsers: async () => {
        set({ loading: true, error: null });
        try{
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false
            }
            const data = await response.json();
            console.log(data);
            set({users: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching users:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch users',
                loading: false
            });
            return false;
        }
    },

    fetchOrganisationUsers: async (id: string) => {
        set({loading:true, error: null});
        const payload = JSON.stringify({id: id});
        console.log('Request payload:', payload);
        try{
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/fetch_organisation_users`,{
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if(!response.ok){
                return false;
            }

            const data = await response.json();
            set({users: data, loading: false});
            return true;
        }catch (error){
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch Οrganisation users',
                loading: false
            });
            return false;
        }
    },

    clearUsers: () => {
        set({users: []});
    },

    fetchRoles: async () => {
        set({ loading: true, error: null });
        try{
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/get_all_roles`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false
            }
            const data = await response.json();
            console.log(data);
            set({roles: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching roles:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch roles',
                loading: false
            });
            return false;
        }
    },

    createUser: async (email:string, password:string,role_id:string, organisation_id:string, auth_provider:string = 'local') => {
        set({loading:true, error: null});
        const payload = JSON.stringify({email:email, password: auth_provider === 'local' ? password : null, role_id:role_id, organisation_id:organisation_id, auth_provider: auth_provider});
        console.log('Request payload:', payload);
        try{
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/create_user_in_organisation`,{
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if(!response.ok){
                return false;
            }

            const data = await response.json();
            set(state => ({users: [...state.users, data], loading: false}));
            console.log(useUserStore.getState().users);
            return true;
        }catch (error){
            set({
                error: error instanceof Error ? error.message : 'Failed to create user',
                loading: false
            });
            return false;
        }
    },

    updateUser: async (email:string | null, password:string | null ,role_id:string | null, user_id:string) => {
        const payload = JSON.stringify({email:email, password:password, role_id:role_id, user_id:user_id});
        set({loading:true, error: null});
        console.log('Request payload:', payload);
        try{
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/update_user_in_organisation`,{
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if(!response.ok){
                return false;
            }

            const data = await response.json();
            set(state => ({users: state.users.map(u => u.id === data.id ? data : u), loading: false}));
            console.log(useUserStore.getState().users);
            return true;
        }catch (error){
            set({
                error: error instanceof Error ? error.message : 'Failed to update user',
                loading: false
            });
            return false;
        }
    },

    fetchOrganisations: async () => {
        set({ loading: true, error: null });
        try{
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/get_all_organisations`, {
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });
            if (!response.ok) {
                return false
            }
            const data = await response.json();
            // console.log(data);
            set({organisations: data, loading: false});
            return true;
        } catch (error) {
            console.error('Error fetching users:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to fetch Organisations',
                loading: false
            });
            return false;
        }
    },

    createOrUpdateOrganisation: async (name:string, domain:string, logo:string, id:string | null) => {
        set({loading:true, error: null});
        const payload = JSON.stringify({name: name, domain: domain, logo: logo, id: id});
        console.log('Request payload:', payload);
        try{
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/create_organisation`,{
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...useAuthStore.getState().getAuthHeader()
                },
                body: payload
            });

            if(!response.ok){
                return false;
            }

            const newOrg = await response.json();
            set(state => ({
                organisations: id ? state.organisations.map(org => org.id === id ? newOrg : org) : [...state.organisations, newOrg],
                loading: false
            }));
            return true;
        }catch (error){
            set({
                error: error instanceof Error ? error.message : 'Failed to create Οrganisation',
                loading: false
            });
            return false;
        }
    },

    deleteUser: async (user_id: string) => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/${user_id}`, {
                method: 'DELETE',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to delete user',
                    loading: false
                });
                return false;
            }

            // Remove the user from the users array
            set(state => ({
                users: state.users.filter(user => user.id !== user_id),
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to delete user',
                loading: false
            });
            return false;
        }
    },

    deleteOrganisation: async (organisation_id: string) => {
        set({loading: true, error: null});
        try {
            const response = await fetch(`${cyberbridge_back_end_rest_api}/users/organisation/${organisation_id}`, {
                method: 'DELETE',
                headers: {
                    ...useAuthStore.getState().getAuthHeader()
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                set({
                    error: errorData.detail || 'Failed to delete organisation',
                    loading: false
                });
                return false;
            }

            // Remove the organisation from the organisations array and clear users
            set(state => ({
                organisations: state.organisations.filter(org => org.id !== organisation_id),
                users: [], // Clear users since they belonged to the deleted organization
                loading: false
            }));
            return true;
        } catch (error) {
            set({
                error: error instanceof Error ? error.message : 'Failed to delete organisation',
                loading: false
            });
            return false;
        }
    },

}));

export default useUserStore;
