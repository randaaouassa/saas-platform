import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useState } from "react";

import { api } from "../../shared/api/client";
import { SkeletonBlock } from "../../shared/components/Skeleton";

interface Warehouse {
    id: string;
    name: string;
    code: string;
    address: string;
    timezone: string;
    is_active: boolean;
}

export default function WarehousesPage() {
    const qc = useQueryClient();
    const [showForm, setShowForm] = useState(false);
    const [name, setName] = useState("");
    const [code, setCode] = useState("");
    const [address, setAddress] = useState("");
    const [search, setSearch] = useState("");

    const { data, isLoading } = useQuery({
        queryKey: ["warehouses"],
        queryFn: async () => (await api.get<Warehouse[]>("/warehouses")).data,
    });

    const create = useMutation({
        mutationFn: async () => {
            const { data } = await api.post("/warehouses", {
                name,
                code,
                address,
                timezone: "UTC",
            });
            return data;
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["warehouses"] });
            setShowForm(false);
            setName("");
            setCode("");
            setAddress("");
        },
    });

    function onSubmit(e: FormEvent) {
        e.preventDefault();
        create.mutate();
    }

    const filtered = (data ?? []).filter((w) => {
        if (!search) return true;
        const s = search.toLowerCase();
        return (
            w.name.toLowerCase().includes(s) ||
            w.code.toLowerCase().includes(s) ||
            w.address.toLowerCase().includes(s)
        );
    });

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-semibold">Warehouses</h1>
                <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
                    {showForm ? "Cancel" : "New warehouse"}
                </button>
            </div>

            {showForm && (
                <form onSubmit={onSubmit} className="glass p-6 mb-6 grid grid-cols-3 gap-4">
                    <div>
                        <label className="label">Name</label>
                        <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
                    </div>
                    <div>
                        <label className="label">Code</label>
                        <input className="input" value={code} onChange={(e) => setCode(e.target.value)} required />
                    </div>
                    <div>
                        <label className="label">Address</label>
                        <input className="input" value={address} onChange={(e) => setAddress(e.target.value)} />
                    </div>
                    <div className="col-span-3 flex justify-end">
                        <button className="btn btn-primary" disabled={create.isPending}>
                            {create.isPending ? "Creating…" : "Create"}
                        </button>
                    </div>
                </form>
            )}

            <div className="mb-4">
                <input
                    className="input !w-64"
                    placeholder="Search warehouses…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>

            {isLoading ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Array.from({ length: 6 }).map((_, i) => (
                        <div key={i} className="glass p-5 space-y-3">
                            <SkeletonBlock className="h-4 w-32" />
                            <SkeletonBlock className="h-3 w-20" />
                            <SkeletonBlock className="h-3 w-40" />
                        </div>
                    ))}
                </div>
            ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filtered.map((w) => (
                        <div key={w.id} className="glass glass-hover p-5">
                            <div className="font-semibold">{w.name}</div>
                            <div className="text-dim text-sm mt-1">Code: {w.code}</div>
                            <div className="text-dim text-sm">{w.address || "No address"}</div>
                            <div
                                className={`mt-3 inline-block text-xs px-2 py-1 rounded-full ${w.is_active
                                        ? "bg-emerald-500/15 text-emerald-300"
                                        : "bg-white/5 text-dim"
                                    }`}
                            >
                                {w.is_active ? "Active" : "Inactive"}
                            </div>
                        </div>
                    ))}
                    {filtered.length === 0 && (
                        <div className="glass p-10 col-span-full text-center">
                            {data?.length === 0 ? (
                                <>
                                    <div className="text-dim text-sm">No warehouses yet.</div>
                                    <button
                                        className="btn btn-primary mt-3 !py-1.5 !px-3 text-xs"
                                        onClick={() => setShowForm(true)}
                                    >
                                        Create your first warehouse
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