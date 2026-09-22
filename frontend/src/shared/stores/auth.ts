import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AuthUser {
    id: string;
    email: string;
    full_name: string;
    roles: string[];
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

export function primaryRole(roles: string[] | null | undefined): string | null {
    if (!roles || roles.length === 0) return null;
    const order = [
        "org_admin",
        "warehouse_manager",
        "warehouse_staff",
        "dispatcher",
        "driver",
    ];
    for (const r of order) if (roles.includes(r)) return r;
    return roles[0];
}

export function homePathForRoles(roles: string[] | null | undefined): string {
    const r = primaryRole(roles);
    if (r === "driver") return "/driver";
    if (r === "dispatcher") return "/dispatcher";
    if (r === "warehouse_manager" || r === "warehouse_staff") return "/warehouse";
    return "/dashboard";
}

export function isAdmin(roles: string[] | null | undefined): boolean {
    const r = primaryRole(roles);
    return r === "org_admin";
}