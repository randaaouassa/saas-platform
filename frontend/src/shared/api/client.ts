import axios, { AxiosError } from "axios";

import { API_URL } from "../lib/config";
import { useAuthStore } from "../stores/auth";

export const api = axios.create({
    baseURL: API_URL,
    headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
    const refresh = useAuthStore.getState().refreshToken;
    if (!refresh) return null;
    try {
        const res = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refresh,
        });
        const { access_token, refresh_token } = res.data;
        useAuthStore.getState().setTokens(access_token, refresh_token);
        return access_token;
    } catch {
        useAuthStore.getState().logout();
        return null;
    }
}

api.interceptors.response.use(
    (r) => r,
    async (error: AxiosError) => {
        const original: any = error.config;
        if (error.response?.status === 401 && !original._retry) {
            original._retry = true;
            if (!refreshing) refreshing = refreshAccessToken();
            const token = await refreshing;
            refreshing = null;
            if (token) {
                original.headers.Authorization = `Bearer ${token}`;
                return api(original);
            }
        }
        return Promise.reject(error);
    },
);