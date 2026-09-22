import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../shared/api/client";
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

    const { data } = useQuery({
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

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {data?.map((d) => (
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
                {(!data || data.length === 0) && (
                    <div className="glass p-8 text-dim col-span-full text-center">No drivers yet.</div>
                )}
            </div>
        </div>
    );
}