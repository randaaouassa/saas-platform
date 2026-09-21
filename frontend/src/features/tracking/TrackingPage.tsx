import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { api } from "../../shared/api/client";

interface Delivery {
    id: string;
    status: string;
    dropoff_location: string;
    created_at: string;
    delivered_at: string | null;
}

const STEPS = ["pending", "assigned", "picked_up", "in_transit", "delivered"];

export default function TrackingPage() {
    const { id } = useParams<{ id: string }>();

    const { data, isLoading, error } = useQuery({
        queryKey: ["tracking", id],
        queryFn: async () => (await api.get<Delivery>(`/deliveries/${id}`)).data,
        enabled: !!id,
        refetchInterval: 10000,
    });

    const currentIdx = data ? STEPS.indexOf(data.status) : -1;

    return (
        <div className="min-h-screen flex items-center justify-center p-6">
            <div className="glass p-8 w-full max-w-lg">
                <div className="text-center mb-8">
                    <div className="text-2xl font-semibold">
                        <span className="accent">●</span> Track your delivery
                    </div>
                    <div className="text-dim text-xs font-mono mt-2">{id}</div>
                </div>

                {isLoading && <div className="text-dim text-center">Loading…</div>}
                {error && <div className="text-red-300 text-center">Delivery not found.</div>}

                {data && (
                    <>
                        <div className="mb-8">
                            <div className="text-dim text-xs uppercase tracking-widest mb-1">Destination</div>
                            <div className="text-lg">{data.dropoff_location}</div>
                        </div>

                        <ol className="space-y-3">
                            {STEPS.map((step, i) => (
                                <li key={step} className="flex items-center gap-3">
                                    <div
                                        className={`w-3 h-3 rounded-full ${i <= currentIdx ? "bg-purple-400 shadow-[0_0_12px_rgba(168,85,247,0.8)]" : "bg-white/10"
                                            }`}
                                    />
                                    <span className={i <= currentIdx ? "text-white" : "text-dim"}>
                                        {step.replace("_", " ")}
                                    </span>
                                </li>
                            ))}
                        </ol>

                        {data.delivered_at && (
                            <div className="text-dim text-sm mt-8 text-center">
                                Delivered {new Date(data.delivered_at).toLocaleString()}
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}