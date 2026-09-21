import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../shared/api/client";

interface Delivery {
    id: string;
    status: string;
    dropoff_location: string;
}

interface Candidate {
    driver_id: string;
    full_name: string;
    status: string;
    distance_km: number | null;
    active_deliveries: number;
    score: number;
}

export default function DispatchPage() {
    const qc = useQueryClient();
    const [deliveryId, setDeliveryId] = useState("");
    const [candidates, setCandidates] = useState<Candidate[] | null>(null);

    const deliveries = useQuery({
        queryKey: ["deliveries"],
        queryFn: async () => (await api.get<Delivery[]>("/deliveries")).data,
    });

    const rank = useMutation({
        mutationFn: async (id: string) => {
            const { data } = await api.post<{ candidates: Candidate[] }>("/dispatch/candidates", {
                delivery_id: id,
            });
            return data.candidates;
        },
        onSuccess: (c) => setCandidates(c),
    });

    const assign = useMutation({
        mutationFn: async ({ id, driverId }: { id: string; driverId?: string }) => {
            await api.post("/dispatch/assign", { delivery_id: id, driver_id: driverId ?? null });
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["deliveries"] });
            setCandidates(null);
            setDeliveryId("");
        },
    });

    const pending = deliveries.data?.filter((d) => d.status === "pending") ?? [];

    return (
        <div>
            <h1 className="text-3xl font-semibold mb-6">Dispatch</h1>

            <div className="glass p-6 mb-6">
                <label className="label">Delivery to assign</label>
                <div className="flex gap-3">
                    <select className="input" value={deliveryId} onChange={(e) => setDeliveryId(e.target.value)}>
                        <option value="">Select a pending delivery…</option>
                        {pending.map((d) => (
                            <option key={d.id} value={d.id}>{d.dropoff_location}</option>
                        ))}
                    </select>
                    <button
                        className="btn btn-ghost"
                        disabled={!deliveryId || rank.isPending}
                        onClick={() => rank.mutate(deliveryId)}
                    >
                        Rank candidates
                    </button>
                    <button
                        className="btn btn-primary"
                        disabled={!deliveryId || assign.isPending}
                        onClick={() => assign.mutate({ id: deliveryId })}
                    >
                        Auto-assign
                    </button>
                </div>
            </div>

            {candidates && (
                <div className="glass overflow-hidden">
                    <table className="w-full text-sm">
                        <thead className="text-dim text-xs uppercase tracking-widest">
                            <tr>
                                <th className="text-left px-4 py-3">Driver</th>
                                <th className="text-left px-4 py-3">Status</th>
                                <th className="text-right px-4 py-3">Distance (km)</th>
                                <th className="text-right px-4 py-3">Active</th>
                                <th className="text-right px-4 py-3">Score</th>
                                <th className="text-right px-4 py-3">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {candidates.map((c) => (
                                <tr key={c.driver_id} className="border-t border-white/5">
                                    <td className="px-4 py-3">{c.full_name}</td>
                                    <td className="px-4 py-3 text-dim">{c.status}</td>
                                    <td className="px-4 py-3 text-right">{c.distance_km?.toFixed(2) ?? "—"}</td>
                                    <td className="px-4 py-3 text-right">{c.active_deliveries}</td>
                                    <td className="px-4 py-3 text-right font-semibold">{c.score.toFixed(1)}</td>
                                    <td className="px-4 py-3 text-right">
                                        <button
                                            className="btn btn-ghost !py-1 !px-3 text-xs"
                                            disabled={assign.isPending}
                                            onClick={() => assign.mutate({ id: deliveryId, driverId: c.driver_id })}
                                        >
                                            Assign
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {candidates.length === 0 && (
                                <tr><td colSpan={6} className="px-4 py-8 text-center text-dim">No candidates.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}