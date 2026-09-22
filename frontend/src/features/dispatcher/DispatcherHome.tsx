import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { api } from "../../shared/api/client";

interface Delivery {
    id: string;
    status: string;
    dropoff_location: string;
}

interface Driver {
    id: string;
    status: string;
    full_name: string;
}

export default function DispatcherHome() {
    const deliveries = useQuery({
        queryKey: ["deliveries"],
        queryFn: async () => (await api.get<Delivery[]>("/deliveries")).data,
        refetchInterval: 10000,
    });

    const drivers = useQuery({
        queryKey: ["drivers"],
        queryFn: async () => (await api.get<Driver[]>("/drivers")).data,
        refetchInterval: 10000,
    });

    const pending = deliveries.data?.filter((d) => d.status === "pending") ?? [];
    const active = deliveries.data?.filter((d) =>
        ["assigned", "picked_up", "in_transit"].includes(d.status),
    ) ?? [];
    const available = drivers.data?.filter((d) => d.status === "available") ?? [];
    const onDelivery = drivers.data?.filter((d) => d.status === "on_delivery") ?? [];

    return (
        <div>
            <h1 className="text-3xl font-semibold mb-6">Dispatcher overview</h1>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <Stat label="Pending" value={pending.length} accent="warning" />
                <Stat label="In flight" value={active.length} accent="info" />
                <Stat label="Drivers free" value={available.length} accent="success" />
                <Stat label="On delivery" value={onDelivery.length} accent="accent" />
            </div>

            <div className="grid lg:grid-cols-2 gap-4">
                <div className="glass p-5">
                    <div className="flex items-center justify-between mb-4">
                        <div className="font-semibold">Pending queue</div>
                        <Link to="/dispatch" className="text-xs accent hover:underline">
                            Open dispatch →
                        </Link>
                    </div>
                    {pending.length === 0 ? (
                        <div className="text-dim text-sm py-6 text-center">No pending deliveries.</div>
                    ) : (
                        <div className="space-y-2">
                            {pending.slice(0, 6).map((d) => (
                                <div key={d.id} className="flex items-center justify-between text-sm border-t border-white/5 pt-2 first:border-0 first:pt-0">
                                    <span className="truncate">{d.dropoff_location}</span>
                                    <span className="text-dim font-mono text-xs">{d.id.slice(0, 6)}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="glass p-5">
                    <div className="flex items-center justify-between mb-4">
                        <div className="font-semibold">Available drivers</div>
                        <Link to="/drivers" className="text-xs accent hover:underline">
                            Manage →
                        </Link>
                    </div>
                    {available.length === 0 ? (
                        <div className="text-dim text-sm py-6 text-center">No drivers available.</div>
                    ) : (
                        <div className="space-y-2">
                            {available.slice(0, 6).map((d) => (
                                <div key={d.id} className="flex items-center justify-between text-sm border-t border-white/5 pt-2 first:border-0 first:pt-0">
                                    <span className="truncate">{d.full_name}</span>
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
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
    accent,
}: {
    label: string;
    value: number;
    accent: "success" | "warning" | "info" | "accent" | "neutral";
}) {
    const color = {
        success: "text-emerald-300",
        warning: "text-amber-300",
        info: "text-blue-300",
        accent: "text-purple-300",
        neutral: "text-white",
    }[accent];

    return (
        <div className="glass p-5">
            <div className="text-dim text-xs uppercase tracking-widest">{label}</div>
            <div className={`text-3xl font-semibold mt-2 ${color}`}>{value}</div>
        </div>
    );
}