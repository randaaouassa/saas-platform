import { api } from "./client";

export interface UserWithRoles {
    id: string;
    organization_id: string;
    email: string;
    full_name: string;
    phone: string | null;
    is_active: boolean;
    mfa_enabled: boolean;
    created_at: string;
    roles: string[];
}

export interface Role {
    id: string;
    name: string;
    is_system: boolean;
}

export interface Invitation {
    id: string;
    email: string;
    role_id: string;
    expires_at: string;
    accepted_at: string | null;
}

export async function listUsers(): Promise<UserWithRoles[]> {
    const { data } = await api.get<UserWithRoles[]>("/users");
    return data;
}

export async function listRoles(): Promise<Role[]> {
    const { data } = await api.get<Role[]>("/roles");
    return data;
}

export async function inviteUser(email: string, role_name: string): Promise<Invitation> {
    const { data } = await api.post<Invitation>("/auth/invitations", { email, role_name });
    return data;
}

export async function deactivateUser(id: string) {
    await api.post(`/users/${id}/deactivate`);
}

export async function assignRole(id: string, role_name: string): Promise<UserWithRoles> {
    const { data } = await api.post<UserWithRoles>(`/users/${id}/roles`, { role_name });
    return data;
}

export async function revokeRole(id: string, role_name: string): Promise<UserWithRoles> {
    const { data } = await api.delete<UserWithRoles>(`/users/${id}/roles/${role_name}`);
    return data;
}

export async function acceptInvite(token: string, password: string, full_name: string) {
    const { data } = await api.post("/auth/invitations/accept", {
        token,
        password,
        full_name,
    });
    return data;
}