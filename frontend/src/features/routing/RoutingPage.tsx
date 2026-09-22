import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useState } from "react";

import { api } from "../../shared/api/client";
import { SkeletonBlock } from "../../shared/components/Skeleton";
import StatusBadge from "../../shared/components/StatusBadge";

interface Delivery {
    id: string;
    status: string;
    dropoff_location: string;
}

interface Driver {
    id: string;
    full_name: string;
    status: string;
}

interface RouteStop {
    id: string;
    delivery_id: string;
    sequence: number;
    eta: string | null;
    status: string;
}

interface Route {
    id: string;
    driver_id: string;
    date: string;
    status: string;
    total_distance_m: string | null;
    total_duration_s: string | null;
    stops: RouteStop[];
}

export default function RoutingPage() {
    const qc = useQueryClient();
    const [showForm, setShowForm] = useState(false);
    const [driverId, setDriverId] = useState("");
    const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
    const [selected, setSelected] = useState<string[]>([]);

    const routes = useQuery({
        queryKey: ["routes"],
        queryFn: async () => (await api.get<Route[]>("/routes")).data,
    });
    const drivers = useQuery({
        queryKey: ["drivers"],
        queryFn: async () => (await api.get<Driver[]>("/drivers")).data,
    });
    const deliveries = useQuery({
        queryKey: ["deliveries"],
        queryFn: async () => (await api.get<Delivery[]>("/deliveries")).data,
    });

    const create = useMutation({
        mutationFn: async () =>
            (await api.post("/routes", { driver_id: driverId, date, delivery_ids: selected })).data,
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["routes"] });
            setShowForm(false);
            setDriverId("");
            setSelected([]);
        },
    });

    const recalc = useMutation({
        mutationFn: async (id: string) =>
            (await api.post(`/routes/${id}/recalculate`, { reason: "dispatcher request" })).data,
        onSuccess: () => qc.invalidateQueries({ queryKey: ["routes"] }),
    });

    const setStopStatus = useMutation({
        mutationFn: async ({ stopId, status }: { stopId: string; status: string }) => {
            await api.patch(`/routes/stops/${stopId}/status`, { status });
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ["routes"] }),
    });

    const eligible =
        deliveries.data?.filter((d) =>
            ["pending", "assigned", "rescheduled"].includes(d.status),
        ) ?? [];

    function toggle(id: string) {
        setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
    }

    function onSubmit(e: FormEvent) {
        e.preventDefault();
        if (selected.length === 0) return;
        create.mutate();
    }

    function driverName(id: string) {
        return drivers.data?.find((d) => d.id === id)?.full_name ?? id.slice(0, 8);
    }

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-semibold">Routing</h1>
                <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
                    {showForm ? "Cancel" : "New route"}
                </button>
            </div>

            {showForm && (
                <form onSubmit={onSubmit} className="glass p-6 mb-6">
                    <div className="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <label className="label">Driver</label>
                            <select className="input" value={driverId} onChange={(e) => setDriverId(e.target.value)} required>
                                <option value="">Select…</option>
                                {drivers.data?.map((d) => (
                                    <option key={d.id} value={d.id}>{d.full_name} ({d.status})</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="label">Date</label>
                            <input className="input" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
                        </div>
                    </div>
                    <div className="mb-4">
                        <label className="label">Deliveries</label>
                        <div className="flex flex-wrap gap-2">
                            {eligible.map((d) => (
                                <button
                                    type="button"
                                    key={d.id}
                                    onClick={() => toggle(d.id)}
                                    className={`text-xs px-3 py-1 rounded-full border transition ${selected.includes(d.id)
                                            ? "bg-purple-500/25 border-purple-400/50"
                                            : "border-white/10 bg-white/5"
                                        }`}
                                >
                                    {d.dropoff_location}
                                </button>
                            ))}
                            {eligible.length === 0 && <span className="text-dim text-sm">No eligible deliveries.</span>}
                        </div>
                    </div>
                    <div className="flex justify-end">
                        <button className="btn btn-primary" disabled={create.isPending || selected.length === 0}>
                            Build route
                        </button>
                    </div>
                </form>
            )}

            {routes.isLoading ? (
                <div className="space-y-4">
                    {Array.from({ length: 3 }).map((_, i) => (
                        <div key={i} className="glass p-6 space-y-4">
                            <div className="flex items-center justify-between">
                                <div className="space-y-2">
                                    <SkeletonBlock className="h-4 w-40" />
                                    <SkeletonBlock className="h-3 w-24" />
                                </div>
                                <SkeletonBlock className="h-6 w-20 rounded-full" />
                            </div>
                            <SkeletonBlock className="h-4" />
                            <SkeletonBlock className="h-4 w-3/4" />
                        </div>
                    ))}
                </div>
            ) : routes.data && routes.data.length > 0 ? (
                <div className="space-y-4">
                    {routes.data.map((r) => (
                        <div key={r.id} className="glass p-6">
                            <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
                                <div>
                                    <div className="font-semibold">Driver: {driverName(r.driver_id)}</div>
                                    <div className="text-dim text-xs">
                                        {r.date} · <StatusBadge domain="route" value={r.status} />
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm">
                                        {r.total_distance_m ? `${(Number(r.total_distance_m) / 1000).toFixed(1)} km` : "—"}
                                    </div>
                                    <div className="text-dim text-xs">
                                        {r.total_duration_s ? `${(Number(r.total_duration_s) / 60).toFixed(0)} min` : ""}
                                    </div>
                                </div>
                            </div>
                            <ol className="space-y-2 mb-4">
                                {r.stops.map((s) => (
                                    <li key={s.id} className="flex items-center justify-between text-sm border-t border-white/5 pt-2 flex-wrap gap-2">
                                        <div className="flex items-center gap-2">
                                            <span className="text-dim">#{s.sequence}</span>
                                            <span className="font-mono text-xs">{s.delivery_id.slice(0, 8)}</span>
                                            {s.eta && (
                                                <span className="text-dim text-xs">
                                                    ETA {new Date(s.eta).toLocaleTimeString()}
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className="status status-neutral">{s.status}</span>
                                            {s.status === "pending" && (
                                                <button
                                                    className="btn btn-ghost !py-1 !px-2 text-xs"
                                                    onClick={() => setStopStatus.mutate({ stopId: s.id, status: "arrived" })}
                                                >
                                                    arrived
                                                </button>
                                            )}
                                            {s.status === "arrived" && (
                                                <button
                                                    className="btn btn-ghost !py-1 !px-2 text-xs"
                                                    onClick={() => setStopStatus.mutate({ stopId: s.id, status: "completed" })}
                                                >
                                                    done
                                                </button>
                                            )}
                                        </div>
                                    </li>
                                ))}
                            </ol>
                            <div className="flex justify-end">
                                <button
                                    className="btn btn-ghost !py-1 !px-3 text-xs"
                                    disabled={recalc.isPending}
                                    onClick={() => recalc.mutate(r.id)}
                                >
                                    Recalculate
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="glass p-10 text-center">
                    <div className="text-dim text-sm">No routes yet.</div>
                    <button
                        className="btn btn-primary mt-3 !py-1.5 !px-3 text-xs"
                        onClick={() => setShowForm(true)}
                    >
                        Build your first route
                    </button>
                </div>
            )}
        </div>
    );
}