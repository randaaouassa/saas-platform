import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../../shared/api/client";
import StatusBadge from "../../shared/components/StatusBadge";

interface Driver {
    id: string;
    full_name: string;
    phone: string | null;
    license_no: string | null;
    status: string;
    rating: string | null;
    created_at: string;
}

interface Vehicle {
    id: string;
    driver_id: string | null;
    plate: string;
    type: string;
    capacity_weight: string | null;
    capacity_volume: string | null;
}

interface Shift {
    id: string;
    driver_id: string;
    started_at: string;
    ended_at: string | null;
    status: string;
}

interface Position {
    id: string;
    lat: number;
    lng: number;
    recorded_at: string;
}

export default function DriverDetailPage() {
    const { id } = useParams<{ id: string }>();
    const qc = useQueryClient();
    const [plate, setPlate] = useState("");
    const [vType, setVType] = useState("van");
    const [capacity, setCapacity] = useState("");

    const driver = useQuery({
        queryKey: ["driver", id],
        queryFn: async () => (await api.get<Driver>(`/drivers/${id}`)).data,
        enabled: !!id,
    });

    const vehicles = useQuery({
        queryKey: ["vehicles"],
        queryFn: async () => (await api.get<Vehicle[]>("/drivers/vehicles/list")).data,
    });

    const shifts = useQuery({
        queryKey: ["shifts", id],
        queryFn: async () =>
            (await api.get<Shift[]>(`/drivers/shifts/list?driver_id=${id}`)).data,
        enabled: !!id,
    });

    const latestPos = useQuery({
        queryKey: ["position-latest", id],
        queryFn: async () =>
            (await api.get<Position | null>(`/drivers/${id}/positions/latest`)).data,
        enabled: !!id,
    });

    const startShift = useMutation({
        mutationFn: async () => {
            await api.post("/drivers/shifts/start", { driver_id: id });
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["shifts", id] });
            qc.invalidateQueries({ queryKey: ["driver", id] });
        },
    });

    const endShift = useMutation({
        mutationFn: async (shiftId: string) => {
            await api.post(`/drivers/shifts/${shiftId}/end`);
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["shifts", id] });
            qc.invalidateQueries({ queryKey: ["driver", id] });
        },
    });

    const createVehicle = useMutation({
        mutationFn: async () => {
            await api.post("/drivers/vehicles", {
                driver_id: id,
                plate,
                type: vType,
                capacity_weight: capacity || null,
            });
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["vehicles"] });
            setPlate("");
            setCapacity("");
        },
    });

    if (driver.isLoading) return <div className="text-dim">Loading…</div>;
    if (driver.isError || !driver.data) {
        return (
            <div className="glass p-8 text-center">
                <div className="text-red-300 text-sm">Driver not found.</div>
                <Link to="/drivers" className="accent text-xs mt-3 inline-block hover:underline">
                    ← Back to drivers
                </Link>
            </div>
        );
    }

    const d = driver.data;
    const myVehicles = vehicles.data?.filter((v) => v.driver_id === d.id) ?? [];
    const activeShift = shifts.data?.find((s) => s.status === "active");

    return (
        <div>
            <Link to="/drivers" className="text-xs text-dim hover:text-white">
                ← Drivers
            </Link>

            <div className="flex items-start justify-between mt-4 mb-6 gap-4 flex-wrap">
                <div>
                    <h1 className="text-3xl font-semibold">{d.full_name}</h1>
                    <div className="text-dim text-xs mt-1 font-mono">{d.id.slice(0, 8)}</div>
                </div>
                <StatusBadge domain="driver" value={d.status} />
            </div>

            <div className="grid lg:grid-cols-3 gap-4">
                <div className="lg:col-span-2 space-y-4">
                    <div className="glass p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div className="text-dim text-xs uppercase tracking-widest">
                                Shifts
                            </div>
                            {activeShift ? (
                                <button
                                    className="btn btn-ghost !py-1 !px-3 text-xs"
                                    onClick={() => endShift.mutate(activeShift.id)}
                                    disabled={endShift.isPending}
                                >
                                    End active shift
                                </button>
                            ) : (
                                <button
                                    className="btn btn-primary !py-1 !px-3 text-xs"
                                    onClick={() => startShift.mutate()}
                                    disabled={startShift.isPending}
                                >
                                    Start shift
                                </button>
                            )}
                        </div>
                        {!shifts.data || shifts.data.length === 0 ? (
                            <div className="text-dim text-sm">No shifts yet.</div>
                        ) : (
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Started</th>
                                        <th>Ended</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {shifts.data.slice(0, 8).map((s) => (
                                        <tr key={s.id}>
                                            <td>{new Date(s.started_at).toLocaleString()}</td>
                                            <td className="text-dim">
                                                {s.ended_at ? new Date(s.ended_at).toLocaleString() : "—"}
                                            </td>
                                            <td>
                                                <span
                                                    className={`status ${s.status === "active" ? "status-success" : "status-neutral"
                                                        }`}
                                                >
                                                    {s.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>

                    <div className="glass p-6">
                        <div className="text-dim text-xs uppercase tracking-widest mb-4">
                            Vehicles
                        </div>
                        {myVehicles.length === 0 ? (
                            <div className="text-dim text-sm mb-4">No vehicles assigned.</div>
                        ) : (
                            <div className="space-y-2 mb-4">
                                {myVehicles.map((v) => (
                                    <div
                                        key={v.id}
                                        className="flex items-center justify-between text-sm border-t border-white/5 pt-2 first:border-0 first:pt-0"
                                    >
                                        <div>
                                            <div className="font-medium">{v.plate}</div>
                                            <div className="text-dim text-xs capitalize">{v.type}</div>
                                        </div>
                                        <div className="text-dim text-xs">
                                            {v.capacity_weight ? `${v.capacity_weight} kg` : "—"}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="grid grid-cols-3 gap-2">
                            <input
                                className="input"
                                placeholder="Plate"
                                value={plate}
                                onChange={(e) => setPlate(e.target.value)}
                            />
                            <select
                                className="input"
                                value={vType}
                                onChange={(e) => setVType(e.target.value)}
                            >
                                <option value="bike">bike</option>
                                <option value="van">van</option>
                                <option value="truck_small">truck small</option>
                                <option value="truck_large">truck large</option>
                            </select>
                            <input
                                className="input"
                                placeholder="Capacity (kg)"
                                value={capacity}
                                onChange={(e) => setCapacity(e.target.value)}
                            />
                        </div>
                        <button
                            className="btn btn-primary mt-3 !py-1.5 !px-3 text-xs"
                            onClick={() => createVehicle.mutate()}
                            disabled={!plate || createVehicle.isPending}
                        >
                            Add vehicle
                        </button>
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="glass p-5 text-sm">
                        <div className="text-dim text-xs uppercase tracking-widest mb-4">
                            Profile
                        </div>
                        <div className="space-y-3">
                            <Row label="Phone" value={d.phone || "—"} />
                            <Row label="License" value={d.license_no || "—"} />
                            <Row label="Rating" value={d.rating ?? "—"} />
                            <Row
                                label="Joined"
                                value={new Date(d.created_at).toLocaleDateString()}
                            />
                        </div>
                    </div>

                    <div className="glass p-5 text-sm">
                        <div className="text-dim text-xs uppercase tracking-widest mb-4">
                            Last position
                        </div>
                        {latestPos.data ? (
                            <>
                                <div className="font-mono text-xs">
                                    {latestPos.data.lat.toFixed(4)}, {latestPos.data.lng.toFixed(4)}
                                </div>
                                <div className="text-dim text-xs mt-1">
                                    {new Date(latestPos.data.recorded_at).toLocaleString()}
                                </div>
                                <a
                                    className="btn btn-ghost w-full text-xs mt-3"
                                    href={`https://www.google.com/maps?q=${latestPos.data.lat},${latestPos.data.lng}`}
                                    target="_blank"
                                    rel="noreferrer"
                                >
                                    Open in Maps
                                </a>
                            </>
                        ) : (
                            <div className="text-dim text-sm">No position recorded.</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

function Row({
    label,
    value,
    mono,
}: {
    label: string;
    value: string;
    mono?: boolean;
}) {
    return (
        <div className="flex items-center justify-between gap-4 border-t border-white/5 pt-3 first:border-0 first:pt-0">
            <span className="text-dim">{label}</span>
            <span className={mono ? "font-mono text-xs" : "text-right"}>{value}</span>
        </div>
    );
}