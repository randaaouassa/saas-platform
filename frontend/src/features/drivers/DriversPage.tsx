import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../shared/api/client";
import { SkeletonBlock } from "../../shared/components/Skeleton";
import StatusBadge from "../../shared/components/StatusBadge";

interface Driver {
    id: string;
    full_name: string;
    phone: string | null;
    license_no: string | null;
    status: string;
    rating: string | null;
}

export default function DriversPage() {
    const qc = useQueryClient();
    const navigate = useNavigate();
    const [showForm, setShowForm] = useState(false);
    const [fullName, setFullName] = useState("");
    const [phone, setPhone] = useState("");
    const [license, setLicense] = useState("");
    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState("");

    const { data, isLoading } = useQuery({
        queryKey: ["drivers"],
        queryFn: async () => (await api.get<Driver[]>("/drivers")).data,
    });

    const create = useMutation({
        mutationFn: async () =>
            (
                await api.post("/drivers", {
                    full_name: fullName,
                    phone: phone || null,
                    license_no: license || null,
                })
            ).data,
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["drivers"] });
            setShowForm(false);
            setFullName("");
            setPhone("");
            setLicense("");
        },
    });

    const startShift = useMutation({
        mutationFn: async (id: string) => {
            await api.post("/drivers/shifts/start", { driver_id: id });
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ["drivers"] }),
    });

    function onSubmit(e: FormEvent) {
        e.preventDefault();
        create.mutate();
    }

    const filtered = (data ?? []).filter((d) => {
        if (statusFilter && d.status !== statusFilter) return false;
        if (search && !d.full_name.toLowerCase().includes(search.toLowerCase()))
            return false;
        return true;
    });

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-semibold">Drivers</h1>
                <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
                    {showForm ? "Cancel" : "New driver"}
                </button>
            </div>

            {showForm && (
                <form onSubmit={onSubmit} className="glass p-6 mb-6 grid grid-cols-3 gap-4">
                    <div>
                        <label className="label">Full name</label>
                        <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
                    </div>
                    <div>
                        <label className="label">Phone</label>
                        <input className="input" value={phone} onChange={(e) => setPhone(e.target.value)} />
                    </div>
                    <div>
                        <label className="label">License #</label>
                        <input className="input" value={license} onChange={(e) => setLicense(e.target.value)} />
                    </div>
                    <div className="col-span-3 flex justify-end">
                        <button className="btn btn-primary" disabled={create.isPending}>Create</button>
                    </div>
                </form>
            )}

            <div className="flex gap-2 mb-4 flex-wrap">
                <input
                    className="input !w-64"
                    placeholder="Search by name…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
                <select
                    className="input !w-40"
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                >
                    <option value="">All statuses</option>
                    {["offline", "available", "assigned", "on_delivery", "on_break"].map((s) => (
                        <option key={s} value={s}>
                            {s.replace(/_/g, " ")}
                        </option>
                    ))}
                </select>
            </div>

            {isLoading ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Array.from({ length: 6 }).map((_, i) => (
                        <div key={i} className="glass p-5 space-y-3">
                            <div className="flex justify-between items-start">
                                <div className="space-y-2 flex-1">
                                    <SkeletonBlock className="h-4 w-32" />
                                    <SkeletonBlock className="h-3 w-24" />
                                </div>
                                <SkeletonBlock className="h-6 w-16 rounded-full" />
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filtered.map((d) => (
                        <div
                            key={d.id}
                            className="glass glass-hover p-5 cursor-pointer"
                            onClick={() => navigate(`/drivers/${d.id}`)}
                        >
                            <div className="flex items-start justify-between">
                                <div>
                                    <div className="font-semibold">{d.full_name}</div>
                                    <div className="text-dim text-xs mt-1">{d.phone || "no phone"}</div>
                                </div>
                                <StatusBadge domain="driver" value={d.status} />
                            </div>
                            {d.status === "offline" && (
                                <button
                                    className="btn btn-ghost mt-4 !py-1 !px-3 text-xs"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        startShift.mutate(d.id);
                                    }}
                                >
                                    Start shift
                                </button>
                            )}
                        </div>
                    ))}
                    {filtered.length === 0 && (
                        <div className="glass p-10 col-span-full text-center">
                            {data?.length === 0 ? (
                                <>
                                    <div className="text-dim text-sm">No drivers yet.</div>
                                    <button
                                        className="btn btn-primary mt-3 !py-1.5 !px-3 text-xs"
                                        onClick={() => setShowForm(true)}
                                    >
                                        Add your first driver
                                    </button>
                                </>
                            ) : (
                                <div className="text-dim text-sm">No matches.</div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}