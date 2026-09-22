import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../../shared/api/client";
import StatusBadge from "../../shared/components/StatusBadge";

interface Task {
    id: string;
    type: string;
    status: string;
    created_at: string;
}

interface Alert {
    id: string;
    product_id: string;
    warehouse_id: string;
    threshold: string;
    triggered_at: string | null;
}

export default function WarehouseHome() {
    const tasks = useQuery({
        queryKey: ["warehouse-tasks"],
        queryFn: async () => (await api.get<Task[]>("/warehouses/tasks/list")).data,
        refetchInterval: 15000,
    });

    const alerts = useQuery({
        queryKey: ["stock-alerts", "triggered"],
        queryFn: async () =>
            (await api.get<Alert[]>("/inventory/alerts?only_triggered=true")).data,
        refetchInterval: 15000,
    });

    const pending = tasks.data?.filter((t) => t.status === "pending") ?? [];
    const inProgress = tasks.data?.filter((t) => t.status === "in_progress") ?? [];

    return (
        <div>
            <h1 className="text-3xl font-semibold mb-6">Warehouse overview</h1>

            <div className="grid grid-cols-3 gap-4 mb-8">
                <Stat label="Pending tasks" value={pending.length} tone="warning" />
                <Stat label="In progress" value={inProgress.length} tone="accent" />
                <Stat
                    label="Low stock alerts"
                    value={alerts.data?.length ?? 0}
                    tone="danger"
                />
            </div>

            <div className="grid lg:grid-cols-2 gap-4">
                <div className="glass p-5">
                    <div className="flex items-center justify-between mb-4">
                        <div className="font-semibold">Tasks</div>
                        <Link to="/warehouses" className="text-xs accent hover:underline">
                            Manage →
                        </Link>
                    </div>
                    {!tasks.data || tasks.data.length === 0 ? (
                        <div className="text-dim text-sm py-6 text-center">No tasks yet.</div>
                    ) : (
                        <div className="space-y-2">
                            {tasks.data.slice(0, 8).map((t) => (
                                <div
                                    key={t.id}
                                    className="flex items-center justify-between text-sm border-t border-white/5 pt-2 first:border-0 first:pt-0"
                                >
                                    <div className="capitalize">{t.type}</div>
                                    <StatusBadge domain="task" value={t.status} />
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="glass p-5">
                    <div className="flex items-center justify-between mb-4">
                        <div className="font-semibold">Low stock</div>
                        <Link to="/inventory" className="text-xs accent hover:underline">
                            Inventory →
                        </Link>
                    </div>
                    {!alerts.data || alerts.data.length === 0 ? (
                        <div className="text-dim text-sm py-6 text-center">
                            All stock healthy.
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {alerts.data.slice(0, 8).map((a) => (
                                <div
                                    key={a.id}
                                    className="flex items-center justify-between text-sm border-t border-white/5 pt-2 first:border-0 first:pt-0"
                                >
                                    <span className="text-dim font-mono text-xs">
                                        {a.product_id.slice(0, 8)}
                                    </span>
                                    <span className="status status-danger">
                                        threshold {a.threshold}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function Stat({
    label,
    value,
    tone,
}: {
    label: string;
    value: number;
    tone: "warning" | "accent" | "danger";
}) {
    const color = {
        warning: "text-amber-300",
        accent: "text-purple-300",
        danger: "text-red-300",
    }[tone];
    return (
        <div className="glass p-5">
            <div className="text-dim text-xs uppercase tracking-widest">{label}</div>
            <div className={`text-3xl font-semibold mt-2 ${color}`}>{value}</div>
        </div>
    );
}