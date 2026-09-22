import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useWebSocket } from "../shared/hooks/useWebSocket";
import { useAuthStore } from "../shared/stores/auth";

const NAV = [
    { to: "/warehouse", label: "Overview" },
    { to: "/warehouses", label: "Warehouses" },
    { to: "/inventory", label: "Inventory" },
    { to: "/orders", label: "Orders" },
    { to: "/deliveries", label: "Deliveries" },
    { to: "/notifications", label: "Notifications" },
];

export default function WarehouseLayout() {
    const user = useAuthStore((s) => s.user);
    const logout = useAuthStore((s) => s.logout);
    const navigate = useNavigate();
    const { connected } = useWebSocket(["dispatcher", "delivery"]);

    return (
        <div className="min-h-screen flex">
            <aside className="w-60 border-r border-white/5 p-5 flex flex-col">
                <div className="text-base font-semibold mb-1">
                    <span className="accent">●</span> Warehouse
                </div>
                <div className="text-xs mb-8">
                    <span
                        className={`inline-block w-1.5 h-1.5 rounded-full mr-2 ${connected ? "bg-emerald-400" : "bg-red-400"
                            }`}
                    />
                    <span className="text-dim">{connected ? "Live" : "Offline"}</span>
                </div>

                <nav className="flex-1 flex flex-col gap-1">
                    {NAV.map((n) => (
                        <NavLink
                            key={n.to}
                            to={n.to}
                            end
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
                    <div className="text-white truncate text-xs">{user?.full_name}</div>
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
            </aside>
            <main className="flex-1 overflow-auto">
                <div className="max-w-6xl mx-auto p-7">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}