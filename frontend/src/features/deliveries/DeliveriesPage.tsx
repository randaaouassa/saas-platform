import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import type { FormEvent } from "react";

import { api } from "../../shared/api/client";

interface Delivery {
    id: string;
    status: string;
    dropoff_location: string;
    dropoff_lat: number | null;
    dropoff_lng: number | null;
    created_at: string;
    delivered_at: string | null;
}

const NEXT: Record<string, string[]> = {
    pending: ["assigned", "cancelled"],
    assigned: ["picked_up", "cancelled"],
    picked_up: ["in_transit", "failed"],
    in_transit: ["delivered", "failed"],
    failed: ["rescheduled", "returned"],
    rescheduled: ["assigned", "cancelled"],
};

export default function DeliveriesPage() {
    const qc = useQueryClient();
    const [showForm, setShowForm] = useState(false);
    const [dropoff, setDropoff] = useState("");
    const [lat, setLat] = useState("");
    const [lng, setLng] = useState("");

    const { data } = useQuery({
        queryKey: ["deliveries"],
        queryFn: async () => (await api.get<Delivery[]>("/deliveries")).data,
    });

    const create = useMutation({
        mutationFn: async () =>
            (
                await api.post("/deliveries", {
                    dropoff_location: dropoff,
                    dropoff_lat: lat ? parseFloat(lat) : null,
                    dropoff_lng: lng ? parseFloat(lng) : null,
                })
            ).data,
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["deliveries"] });
            setShowForm(false);
            setDropoff("");
            setLat("");
            setLng("");
        },
    });

    const transition = useMutation({
        mutationFn: async ({ id, status, reason }: { id: string; status: string; reason?: string }) => {
            await api.post(`/deliveries/${id}/status`, { status, failed_reason: reason });
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ["deliveries"] }),
    });

    function onSubmit(e: FormEvent) {
        e.preventDefault();
        create.mutate();
    }

    function advance(d: Delivery, target: string) {
        let reason: string | undefined;
        if (target === "failed") {
            reason = window.prompt("Reason for failure?") ?? undefined;
            if (!reason) return;
        }
        transition.mutate({ id: d.id, status: target, reason });
    }

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-semibold">Deliveries</h1>
                <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
                    {showForm ? "Cancel" : "New delivery"}
                </button>
            </div>

            {showForm && (
                <form onSubmit={onSubmit} className="glass p-6 mb-6 grid grid-cols-3 gap-4">
                    <div className="col-span-3">
                        <label className="label">Dropoff address</label>
                        <input className="input" value={dropoff} onChange={(e) => setDropoff(e.target.value)} required />
                    </div>
                    <div>
                        <label className="label">Latitude</label>
                        <input className="input" value={lat} onChange={(e) => setLat(e.target.value)} />
                    </div>
                    <div>
                        <label className="label">Longitude</label>
                        <input className="input" value={lng} onChange={(e) => setLng(e.target.value)} />
                    </div>
                    <div className="col-span-3 flex justify-end">
                        <button className="btn btn-primary" disabled={create.isPending}>Create</button>
                    </div>
                </form>
            )}

            <div className="glass overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="text-dim text-xs uppercase tracking-widest">
                        <tr>
                            <th className="text-left px-4 py-3">Dropoff</th>
                            <th className="text-left px-4 py-3">Status</th>
                            <th className="text-left px-4 py-3">Coords</th>
                            <th className="text-right px-4 py-3">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data?.map((d) => (
                            <tr key={d.id} className="border-t border-white/5">
                                <td className="px-4 py-3">{d.dropoff_location}</td>
                                <td className="px-4 py-3">
                                    <span className="text-xs px-2 py-1 rounded-full bg-purple-500/15 text-purple-200">
                                        {d.status}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-dim text-xs font-mono">
                                    {d.dropoff_lat != null ? `${d.dropoff_lat.toFixed(3)}, ${d.dropoff_lng?.toFixed(3)}` : "—"}
                                </td>
                                <td className="px-4 py-3 text-right space-x-2">
                                    {(NEXT[d.status] ?? []).map((a) => (
                                        <button
                                            key={a}
                                            className="btn btn-ghost !py-1 !px-3 text-xs"
                                            onClick={() => advance(d, a)}
                                            disabled={transition.isPending}
                                        >
                                            → {a}
                                        </button>
                                    ))}
                                </td>
                            </tr>
                        ))}
                        {(!data || data.length === 0) && (
                            <tr><td colSpan={4} className="px-4 py-8 text-center text-dim">No deliveries yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}