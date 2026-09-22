import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../shared/api/client";
import StatusBadge from "../../shared/components/StatusBadge";

interface Delivery {
    id: string;
    status: string;
    dropoff_location: string;
    dropoff_lat: number | null;
    dropoff_lng: number | null;
    scheduled_at: string | null;
    public_token: string | null;
}

const NEXT: Record<string, string[]> = {
    assigned: ["picked_up"],
    picked_up: ["in_transit"],
    in_transit: ["delivered", "failed"],
};

export default function DriverHome() {
    const qc = useQueryClient();

    const { data, isLoading } = useQuery({
        queryKey: ["my-deliveries"],
        queryFn: async () => (await api.get<Delivery[]>("/deliveries/mine")).data,
        refetchInterval: 15000,
    });

    const advance = useMutation({
        mutationFn: async ({ id, status, reason }: { id: string; status: string; reason?: string }) => {
            await api.post(`/deliveries/${id}/status`, {
                status,
                failed_reason: reason,
            });
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ["my-deliveries"] }),
    });

    function onAdvance(d: Delivery, target: string) {
        let reason: string | undefined;
        if (target === "failed") {
            reason = window.prompt("Reason?") ?? undefined;
            if (!reason) return;
        }
        advance.mutate({ id: d.id, status: target, reason });
    }

    return (
        <div>
            <h1 className="text-2xl font-semibold mb-6">Today's deliveries</h1>

            {isLoading ? (
                <div className="space-y-3">
                    {[1, 2].map((i) => (
                        <div key={i} className="glass p-5 h-24 skeleton" />
                    ))}
                </div>
            ) : !data || data.length === 0 ? (
                <div className="glass p-10 text-center text-dim">
                    <div className="text-3xl mb-2">🛻</div>
                    <div className="text-sm">No deliveries assigned yet.</div>
                </div>
            ) : (
                <div className="space-y-3">
                    {data.map((d) => (
                        <div key={d.id} className="glass glass-hover p-5">
                            <div className="flex items-start justify-between gap-4">
                                <div className="min-w-0">
                                    <div className="font-medium truncate">{d.dropoff_location}</div>
                                    <div className="text-dim text-xs mt-1 font-mono truncate">
                                        {d.id.slice(0, 8)}
                                    </div>
                                    {d.scheduled_at && (
                                        <div className="text-dim text-xs mt-1">
                                            Scheduled {new Date(d.scheduled_at).toLocaleString()}
                                        </div>
                                    )}
                                </div>
                                <StatusBadge domain="delivery" value={d.status} />
                            </div>

                            <div className="mt-4 flex flex-wrap gap-2">
                                {(NEXT[d.status] ?? []).map((s) => (
                                    <button
                                        key={s}
                                        className={`btn ${s === "failed" ? "btn-danger" : "btn-primary"} !py-1.5 !px-3 text-xs`}
                                        disabled={advance.isPending}
                                        onClick={() => onAdvance(d, s)}
                                    >
                                        {s.replace("_", " ")}
                                    </button>
                                ))}
                                {d.dropoff_lat != null && (
                                    <a
                                        className="btn btn-ghost !py-1.5 !px-3 text-xs"
                                        href={`https://www.google.com/maps?q=${d.dropoff_lat},${d.dropoff_lng}`}
                                        target="_blank"
                                        rel="noreferrer"
                                    >
                                        Map
                                    </a>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}