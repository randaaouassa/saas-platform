import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AuthUser {
    id: string;
    email: string;
    full_name: string;
    role: string;
    organization_id: string;
}

interface AuthState {
    accessToken: string | null;
    refreshToken: string | null;
    user: AuthUser | null;
    setTokens: (access: string, refresh: string) => void;
    setUser: (user: AuthUser) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            accessToken: null,
            refreshToken: null,
            user: null,
            setTokens: (access, refresh) =>
                set({ accessToken: access, refreshToken: refresh }),
            setUser: (user) => set({ user }),
            logout: () =>
                set({ accessToken: null, refreshToken: null, user: null }),
        }),
        { name: "auth" },
    ),
);