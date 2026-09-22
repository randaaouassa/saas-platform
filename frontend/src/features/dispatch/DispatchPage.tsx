import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { api } from "../../shared/api/client";
import Map from "../../shared/components/Map";
import StatusBadge from "../../shared/components/StatusBadge";

interface Delivery {
    id: string;
    status: string;
    dropoff_location: string;
    dropoff_lat: number | null;
    dropoff_lng: number | null;
    pickup_lat: number | null;
    pickup_lng: number | null;
}

interface Driver {
    id: string;
    full_name: string;
    status: string;
}

interface Position {
    lat: number;
    lng: number;
}

interface Candidate {
    driver_id: string;
    full_name: string;
    status: string;
    distance_km: number | null;
    active_deliveries: number;
    package_weight: number;
    vehicle_capacity: number | null;
    capacity_ok: boolean;
    score: number;
}

export default function DispatchPage() {
    const qc = useQueryClient();
    const [deliveryId, setDeliveryId] = useState("");
    const [candidates, setCandidates] = useState<Candidate[] | null>(null);

    const deliveries = useQuery({
        queryKey: ["deliveries"],
        queryFn: async () => (await api.get<Delivery[]>("/deliveries")).data,
        refetchInterval: 15000,
    });

    const drivers = useQuery({
        queryKey: ["drivers"],
        queryFn: async () => (await api.get<Driver[]>("/drivers")).data,
        refetchInterval: 15000,
    });

    const positions = useQuery({
        queryKey: ["driver-positions", drivers.data?.map((d) => d.id).join(",")],
        queryFn: async () => {
            const map: Record<string, Position | null> = {};
            for (const d of drivers.data ?? []) {
                const { data } = await api.get<Position | null>(
                    `/drivers/${d.id}/positions/latest`,
                );
                map[d.id] = data;
            }
            return map;
        },
        enabled: !!drivers.data && drivers.data.length > 0,
        refetchInterval: 15000,
    });

    const rank = useMutation({
        mutationFn: async (id: string) => {
            const { data } = await api.post<{ candidates: Candidate[] }>(
                "/dispatch/candidates",
                { delivery_id: id },
            );
            return data.candidates;
        },
        onSuccess: (c) => setCandidates(c),
    });

    const assign = useMutation({
        mutationFn: async ({ id, driverId }: { id: string; driverId?: string }) => {
            await api.post("/dispatch/assign", {
                delivery_id: id,
                driver_id: driverId ?? null,
            });
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["deliveries"] });
            qc.invalidateQueries({ queryKey: ["drivers"] });
            setCandidates(null);
            setDeliveryId("");
        },
    });

    const pending = deliveries.data?.filter((d) => d.status === "pending") ?? [];
    const selectedDelivery = pending.find((d) => d.id === deliveryId);

    const mapPoints = [
        ...(drivers.data ?? [])
            .map((d) => {
                const pos = positions.data?.[d.id];
                if (!pos) return null;
                return {
                    id: `drv-${d.id}`,
                    lat: pos.lat,
                    lng: pos.lng,
                    label: `${d.full_name} · ${d.status}`,
                    color: d.status === "available" ? ("green" as const) : ("blue" as const),
                };
            })
            .filter(Boolean as unknown as <T>(x: T | null) => x is T),
        ...(pending
            .map((d) =>
                d.dropoff_lat != null && d.dropoff_lng != null
                    ? {
                        id: `del-${d.id}`,
                        lat: d.dropoff_lat,
                        lng: d.dropoff_lng,
                        label: d.dropoff_location,
                        color: "purple" as const,
                    }
                    : null,
            )
            .filter(Boolean) as any),
    ];

    const mapCenter: [number, number] =
        mapPoints.length > 0
            ? [mapPoints[0].lat, mapPoints[0].lng]
            : [0, 0];

    return (
        <div>
            <h1 className="text-3xl font-semibold mb-6">Dispatch</h1>

            <div className="grid lg:grid-cols-2 gap-4 mb-6">
                <div className="glass p-6">
                    <label className="label">Delivery to assign</label>
                    <div className="flex gap-3 flex-wrap">
                        <select
                            className="input !w-auto min-w-[240px]"
                            value={deliveryId}
                            onChange={(e) => setDeliveryId(e.target.value)}
                        >
                            <option value="">Select a pending delivery…</option>
                            {pending.map((d) => (
                                <option key={d.id} value={d.id}>
                                    {d.dropoff_location}
                                </option>
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

                    {selectedDelivery && (
                        <div className="mt-4 text-xs text-dim">
                            Dropoff:{" "}
                            <span className="text-white">
                                {selectedDelivery.dropoff_location}
                            </span>
                        </div>
                    )}
                </div>

                <div className="glass p-4">
                    <div className="text-dim text-xs uppercase tracking-widest mb-3">
                        Live map
                    </div>
                    <Map
                        center={mapCenter}
                        zoom={11}
                        height={280}
                        points={mapPoints}
                    />
                </div>
            </div>

            {candidates && (
                <div className="glass overflow-hidden">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Driver</th>
                                <th>Status</th>
                                <th className="text-right">Distance</th>
                                <th className="text-right">Active</th>
                                <th className="text-right">Capacity</th>
                                <th className="text-right">Score</th>
                                <th className="text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {candidates.map((c) => (
                                <tr key={c.driver_id}>
                                    <td>{c.full_name}</td>
                                    <td>
                                        <StatusBadge domain="driver" value={c.status} />
                                    </td>
                                    <td className="text-right">
                                        {c.distance_km?.toFixed(2) ?? "—"}
                                    </td>
                                    <td className="text-right">{c.active_deliveries}</td>
                                    <td className="text-right">
                                        <span
                                            className={
                                                c.capacity_ok
                                                    ? "status status-success"
                                                    : "status status-danger"
                                            }
                                        >
                                            {c.package_weight} / {c.vehicle_capacity ?? "∞"}
                                        </span>
                                    </td>
                                    <td className="text-right font-semibold">
                                        {c.score.toFixed(1)}
                                    </td>
                                    <td className="text-right">
                                        <button
                                            className="btn btn-ghost !py-1 !px-3 text-xs"
                                            disabled={assign.isPending}
                                            onClick={() =>
                                                assign.mutate({ id: deliveryId, driverId: c.driver_id })
                                            }
                                        >
                                            Assign
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {candidates.length === 0 && (
                                <tr>
                                    <td colSpan={7} className="text-center text-dim py-8">
                                        No candidates.
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