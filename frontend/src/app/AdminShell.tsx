import type { ReactNode } from "react";
import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";

import { useWebSocket } from "../shared/hooks/useWebSocket";
import { primaryRole, useAuthStore } from "../shared/stores/auth";

export interface NavItem {
    to: string;
    label: string;
}

interface Props {
    brand: string;
    nav: NavItem[];
    topics?: string[];
    children: ReactNode;
}

export default function AdminShell({ brand, nav, topics, children }: Props) {
    const user = useAuthStore((s) => s.user);
    const logout = useAuthStore((s) => s.logout);
    const navigate = useNavigate();
    const { connected } = useWebSocket(topics);
    const role = primaryRole(user?.roles);
    const [drawer, setDrawer] = useState(false);

    const SidebarContent = (
        <>
            <div className="text-base font-semibold mb-1">
                <span className="accent">●</span> {brand}
            </div>
            <div className="text-xs mb-8">
                <span
                    className={`inline-block w-1.5 h-1.5 rounded-full mr-2 ${connected ? "bg-emerald-400" : "bg-red-400"
                        }`}
                />
                <span className="text-dim">{connected ? "Live" : "Offline"}</span>
            </div>

            <nav className="flex-1 flex flex-col gap-1 overflow-auto">
                {nav.map((n) => (
                    <NavLink
                        key={n.to}
                        to={n.to}
                        end
                        onClick={() => setDrawer(false)}
                        className={({ isActive }) =>
                            `px-3 py-2 rounded-lg text-sm transition ${isActive
                                ? "bg-white/5 text-white"
                                : "text-dim hover:bg-white/5 hover:text-white"
                            }`
                        }
                    >
                        {n.label}
                    </NavLink>
                ))}
            </nav>

            <div className="border-t border-white/5 pt-4 text-sm">
                <div className="text-white truncate text-xs">
                    {user?.full_name || user?.email}
                </div>
                <div className="text-dim text-[10px] uppercase tracking-wider truncate mt-0.5">
                    {role?.replace(/_/g, " ")}
                </div>
                <button
                    className="btn btn-ghost mt-2 w-full text-xs"
                    onClick={() => {
                        logout();
                        navigate("/login");
                    }}
                >
                    Sign out
                </button>
            </div>
        </>
    );

    return (
        <div className="min-h-screen flex">
            {/* Desktop sidebar */}
            <aside className="hidden lg:flex w-60 border-r border-white/5 p-5 flex-col">
                {SidebarContent}
            </aside>

            {/* Mobile drawer */}
            {drawer && (
                <div
                    className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
                    onClick={() => setDrawer(false)}
                />
            )}
            <aside
                className={`fixed top-0 left-0 bottom-0 z-50 w-64 bg-[color:var(--bg-elev)] border-r border-white/5 p-5 flex flex-col transition-transform lg:hidden ${drawer ? "translate-x-0" : "-translate-x-full"
                    }`}
            >
                {SidebarContent}
            </aside>

            <main className="flex-1 overflow-auto min-w-0">
                {/* Mobile top bar */}
                <div className="lg:hidden sticky top-0 z-30 border-b border-white/5 bg-[color:var(--bg)]/80 backdrop-blur px-4 py-3 flex items-center justify-between">
                    <button
                        className="btn btn-ghost !py-1.5 !px-3 text-xs"
                        onClick={() => setDrawer(true)}
                    >
                        ☰ Menu
                    </button>
                    <div className="text-sm font-semibold">
                        <span className="accent">●</span> {brand}
                    </div>
                    <div className="w-12" />
                </div>

                <div className="max-w-6xl mx-auto p-4 sm:p-6 lg:p-7 min-w-0">{children}</div>
            </main>
        </div>
    );
}