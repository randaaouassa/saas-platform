import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useWebSocket } from "../shared/hooks/useWebSocket";
import { useAuthStore } from "../shared/stores/auth";

const NAV = [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/warehouses", label: "Warehouses" },
    { to: "/inventory", label: "Inventory" },
    { to: "/orders", label: "Orders" },
    { to: "/deliveries", label: "Deliveries" },
    { to: "/drivers", label: "Drivers" },
    { to: "/dispatch", label: "Dispatch" },
    { to: "/routing", label: "Routing" },
    { to: "/notifications", label: "Notifications" },
];

export default function Layout() {
    const user = useAuthStore((s) => s.user);
    const logout = useAuthStore((s) => s.logout);
    const navigate = useNavigate();
    const { connected } = useWebSocket();

    return (
        <div className="min-h-screen flex">
            <aside className="w-64 border-r border-white/5 p-6 flex flex-col">
                <div className="text-lg font-semibold mb-2">
                    <span className="accent">●</span> SaaS Platform
                </div>
                <div className="text-xs mb-8">
                    <span
                        className={`inline-block w-2 h-2 rounded-full mr-2 ${connected
                                ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
                                : "bg-red-400"
                            }`}
                    />
                    <span className="text-dim">{connected ? "Live" : "Offline"}</span>
                </div>

                <nav className="flex-1 flex flex-col gap-1">
                    {NAV.map((n) => (
                        <NavLink
                            key={n.to}
                            to={n.to}
                            className={({ isActive }) =>
                                `px-3 py-2 rounded-lg text-sm transition ${isActive
                                    ? "bg-white/5 text-white"
                                    : "text-[color:var(--text-dim)] hover:bg-white/5 hover:text-white"
                                }`
                            }
                        >
                            {n.label}
                        </NavLink>
                    ))}
                </nav>

                <div className="border-t border-white/5 pt-4 text-sm">
                    <div className="text-white truncate">{user?.full_name || user?.email}</div>
                    <div className="text-dim text-xs truncate">{user?.role}</div>
                    <button
                        className="btn btn-ghost mt-3 w-full text-xs"
                        onClick={() => {
                            logout();
                            navigate("/login");
                        }}
                    >
                        Sign out
                    </button>
                </div>
            </aside>
            <main className="flex-1 overflow-auto">
                <div className="max-w-6xl mx-auto p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}