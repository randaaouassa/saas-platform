import { api } from "./client";

export interface TokenPair {
    access_token: string;
    refresh_token: string;
    token_type: string;
    expires_in: number;
}

export interface MeResponse {
    id: string;
    email: string;
    full_name: string;
    role: string;
    organization_id: string;
    is_active: boolean;
    mfa_enabled: boolean;
    created_at: string;
}

export async function register(payload: {
    organization: { name: string; slug: string };
    email: string;
    password: string;
    full_name: string;
}): Promise<TokenPair> {
    const { data } = await api.post<TokenPair>("/auth/register", payload);
    return data;
}

export async function login(payload: {
    email: string;
    password: string;
    organization_slug: string;
}): Promise<TokenPair> {
    const { data } = await api.post<TokenPair>("/auth/login", payload);
    return data;
}

export async function fetchMe(): Promise<MeResponse> {
    const { data } = await api.get<MeResponse>("/auth/me");
    return data;
}