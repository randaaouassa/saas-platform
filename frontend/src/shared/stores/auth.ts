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

export function useRole(): string | null {
    return useAuthStore((s) => s.user?.role ?? null);
}

export function isAdmin(role: string | null): boolean {
    return role === "super_admin" || role === "org_admin";
}

export function isDriver(role: string | null): boolean {
    return role === "driver";
}

export function isDispatcher(role: string | null): boolean {
    return role === "dispatcher";
}

export function isWarehouse(role: string | null): boolean {
    return role === "warehouse_manager" || role === "warehouse_staff";
}

export function homePathForRole(role: string | null): string {
    if (isDriver(role)) return "/driver";
    if (isDispatcher(role)) return "/dispatcher";
    if (isWarehouse(role)) return "/warehouse";
    return "/dashboard";
}