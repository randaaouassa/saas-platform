import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useWebSocket } from "../shared/hooks/useWebSocket";
import { useAuthStore } from "../shared/stores/auth";

const NAV = [
    { to: "/driver", label: "Today" },
    { to: "/driver/notifications", label: "Notifications" },
];

export default function DriverLayout() {
    const user = useAuthStore((s) => s.user);
    const logout = useAuthStore((s) => s.logout);
    const navigate = useNavigate();
    const { connected } = useWebSocket(["driver", "delivery", "notification"]);

    return (
        <div className="min-h-screen flex flex-col">
            <header className="border-b border-white/5 px-4 sm:px-6 py-3 sm:py-4 flex items-center justify-between max-w-5xl w-full mx-auto">
                <div className="text-base sm:text-lg font-semibold">
                    <span className="accent">●</span> Driver
                </div>
                <div className="flex items-center gap-3">
                    <div className="text-xs">
                        <span
                            className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${connected ? "bg-emerald-400" : "bg-red-400"
                                }`}
                        />
                        <span className="text-dim hidden sm:inline">
                            {connected ? "Live" : "Offline"}
                        </span>
                    </div>
                    <button
                        className="btn btn-ghost !py-1.5 !px-3 text-xs"
                        onClick={() => {
                            logout();
                            navigate("/login");
                        }}
                    >
                        Sign out
                    </button>
                </div>
            </header>

            <div className="px-4 sm:px-6 max-w-5xl w-full mx-auto pt-3">
                <div className="text-dim text-xs truncate">
                    {user?.full_name || user?.email}
                </div>
            </div>

            <nav className="border-b border-white/5 px-2 sm:px-6 max-w-5xl w-full mx-auto flex gap-1 mt-2">
                {NAV.map((n) => (
                    <NavLink
                        key={n.to}
                        to={n.to}
                        end
                        className={({ isActive }) =>
                            `px-3 sm:px-4 py-3 text-sm border-b-2 -mb-px transition flex-1 sm:flex-none text-center ${isActive
                                ? "border-purple-400 text-white"
                                : "border-transparent text-dim hover:text-white"
                            }`
                        }
                    >
                        {n.label}
                    </NavLink>
                ))}
            </nav>

            <main className="flex-1 px-4 sm:px-6 py-6 sm:py-8 max-w-5xl w-full mx-auto">
                <Outlet />
            </main>
        </div>
    );
}