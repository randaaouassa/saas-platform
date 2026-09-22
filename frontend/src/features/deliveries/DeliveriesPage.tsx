import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../shared/api/client";
import { SkeletonTable } from "../../shared/components/Skeleton";
import StatusBadge from "../../shared/components/StatusBadge";

interface Delivery {
    id: string;
    status: string;
    dropoff_location: string;
    dropoff_lat: number | null;
    dropoff_lng: number | null;
    created_at: string;
    delivered_at: string | null;
}

export default function DeliveriesPage() {
    const qc = useQueryClient();
    const navigate = useNavigate();
    const [showForm, setShowForm] = useState(false);
    const [dropoff, setDropoff] = useState("");
    const [lat, setLat] = useState("");
    const [lng, setLng] = useState("");
    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState("");

    const { data, isLoading } = useQuery({
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

    function onSubmit(e: FormEvent) {
        e.preventDefault();
        create.mutate();
    }

    const filtered = (data ?? []).filter((d) => {
        if (statusFilter && d.status !== statusFilter) return false;
        if (search && !d.dropoff_location.toLowerCase().includes(search.toLowerCase()))
            return false;
        return true;
    });

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

            <div className="flex gap-2 mb-4 flex-wrap">
                <input
                    className="input !w-64"
                    placeholder="Search dropoff…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
                <select
                    className="input !w-40"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                >
                    <option value="">All statuses</option>
                    {[
                        "pending",
                        "assigned",
                        "picked_up",
                        "in_transit",
                        "delivered",
                        "failed",
                        "rescheduled",
                        "returned",
                        "cancelled",
                    ].map((s) => (
                        <option key={s} value={s}>
                            {s.replace(/_/g, " ")}
                        </option>
                    ))}
                </select>
            </div>

            {isLoading ? (
                <SkeletonTable rows={6} cols={3} />
            ) : (
                <div className="glass overflow-hidden">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Dropoff</th>
                                <th>Status</th>
                                <th>Coords</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((d) => (
                                <tr
                                    key={d.id}
                                    className="cursor-pointer"
                                    onClick={() => navigate(`/deliveries/${d.id}`)}
                                >
                                    <td>{d.dropoff_location}</td>
                                    <td><StatusBadge domain="delivery" value={d.status} /></td>
                                    <td className="text-dim text-xs font-mono">
                                        {d.dropoff_lat != null
                                            ? `${d.dropoff_lat.toFixed(3)}, ${d.dropoff_lng?.toFixed(3)}`
                                            : "—"}
                                    </td>
                                </tr>
                            ))}
                            {filtered.length === 0 && (
                                <tr>
                                    <td colSpan={3} className="text-center py-10">
                                        {data?.length === 0 ? (
                                            <>
                                                <div className="text-dim text-sm">No deliveries yet.</div>
                                                <button
                                                    className="btn btn-primary mt-3 !py-1.5 !px-3 text-xs"
                                                    onClick={() => setShowForm(true)}
                                                >
                                                    Create your first delivery
                                                </button>
                                            </>
                                        ) : (
                                            <div className="text-dim text-sm">No matches.</div>
                                        )}
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}