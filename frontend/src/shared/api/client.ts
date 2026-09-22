import axios, { AxiosError } from "axios";

import { API_URL } from "../lib/config";
import { useAuthStore } from "../stores/auth";
import { toast } from "../stores/toast";

export const api = axios.create({
    baseURL: API_URL,
    headers: { "Content-Type": "application/json" },
});

// DEV: artificial latency so loading UI is visible
// if (import.meta.env.DEV) {
//   api.interceptors.request.use(async (config) => {
//     await new Promise((r) => setTimeout(r, 500));
//     return config;
//   });
// }

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
    async (error: AxiosError<any>) => {
        const original: any = error.config;

        // Auto-refresh on 401
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

        // Toast errors except auth endpoints (login/register handle their own UI)
        const url = original?.url ?? "";
        const silent =
            url.includes("/auth/login") ||
            url.includes("/auth/register") ||
            url.includes("/auth/refresh") ||
            url.includes("/auth/invitations/accept");

        if (!silent) {
            const title =
                error.response?.data?.title ||
                error.response?.data?.message ||
                error.message ||
                "Request failed";
            const status = error.response?.status;
            const desc = status ? `HTTP ${status}` : undefined;
            toast.error(title, desc);
        }

        return Promise.reject(error);
    },
);