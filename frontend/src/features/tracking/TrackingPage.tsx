import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { api } from "../../shared/api/client";
import Map from "../../shared/components/Map";
import StatusBadge from "../../shared/components/StatusBadge";

interface TrackingEvent {
    id: string;
    delivery_id: string;
    type: string;
    lat: number | null;
    lng: number | null;
    payload_json: Record<string, unknown>;
    created_at: string;
}

interface PublicTracking {
    delivery_id: string;
    status: string;
    dropoff_location: string;
    dropoff_lat: number | null;
    dropoff_lng: number | null;
    scheduled_at: string | null;
    delivered_at: string | null;
    history: TrackingEvent[];
}

const STEPS = ["pending", "assigned", "picked_up", "in_transit", "delivered"];

export default function TrackingPage() {
    const { token } = useParams<{ token: string }>();

    const { data, isLoading, error } = useQuery({
        queryKey: ["public-tracking", token],
        queryFn: async () =>
            (await api.get<PublicTracking>(`/public/track/${token}`)).data,
        enabled: !!token,
        refetchInterval: 15000,
    });

    const currentIdx = data ? STEPS.indexOf(data.status) : -1;
    const hasCoords = data?.dropoff_lat != null && data?.dropoff_lng != null;

    return (
        <div className="min-h-screen flex items-center justify-center p-6">
            <div className="glass p-8 w-full max-w-2xl">
                <div className="text-center mb-8">
                    <div className="text-2xl font-semibold">
                        <span className="accent">●</span> Track your delivery
                    </div>
                    <div className="text-dim text-xs font-mono mt-2">
                        {data?.delivery_id.slice(0, 8)}
                    </div>
                </div>

                {isLoading && <div className="text-dim text-center">Loading…</div>}
                {error && (
                    <div className="text-red-300 text-center text-sm">
                        Delivery not found.
                    </div>
                )}

                {data && (
                    <>
                        <div className="mb-6 flex items-start justify-between gap-4 flex-wrap">
                            <div>
                                <div className="text-dim text-xs uppercase tracking-widest mb-1">
                                    Destination
                                </div>
                                <div className="text-lg">{data.dropoff_location}</div>
                            </div>
                            <StatusBadge domain="delivery" value={data.status} />
                        </div>

                        <ol className="space-y-3 mb-8">
                            {STEPS.map((step, i) => (
                                <li key={step} className="flex items-center gap-3">
                                    <div
                                        className={`w-3 h-3 rounded-full ${i <= currentIdx
                                                ? "bg-purple-400 shadow-[0_0_12px_rgba(168,85,247,0.8)]"
                                                : "bg-white/10"
                                            }`}
                                    />
                                    <span
                                        className={
                                            i <= currentIdx ? "text-white capitalize" : "text-dim capitalize"
                                        }
                                    >
                                        {step.replace(/_/g, " ")}
                                    </span>
                                </li>
                            ))}
                        </ol>

                        {hasCoords && (
                            <div className="mb-6">
                                <Map
                                    center={[data.dropoff_lat!, data.dropoff_lng!]}
                                    zoom={13}
                                    height={260}
                                    points={[
                                        {
                                            id: "dropoff",
                                            lat: data.dropoff_lat!,
                                            lng: data.dropoff_lng!,
                                            label: data.dropoff_location,
                                            color: "purple",
                                        },
                                    ]}
                                />
                            </div>
                        )}

                        <div>
                            <div className="text-dim text-xs uppercase tracking-widest mb-3">
                                History
                            </div>
                            <ol className="space-y-2 text-sm">
                                {data.history.map((h) => (
                                    <li
                                        key={h.id}
                                        className="flex items-center justify-between border-t border-white/5 pt-2 first:border-0 first:pt-0"
                                    >
                                        <div className="flex items-center gap-2">
                                            <StatusBadge domain="delivery" value={h.type} />
                                            {typeof h.payload_json?.note === "string" && (
                                                <span className="text-dim text-xs">
                                                    “{h.payload_json.note}”
                                                </span>
                                            )}
                                        </div>
                                        <span className="text-dim text-xs">
                                            {new Date(h.created_at).toLocaleString()}
                                        </span>
                                    </li>
                                ))}
                            </ol>
                        </div>

                        {data.delivered_at && (
                            <div className="text-emerald-300 text-sm mt-6 text-center">
                                Delivered {new Date(data.delivered_at).toLocaleString()}
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}