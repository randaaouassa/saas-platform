import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../shared/api/client";
import { SkeletonBlock } from "../../shared/components/Skeleton";
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
        mutationFn: async ({
            id,
            status,
            reason,
        }: {
            id: string;
            status: string;
            reason?: string;
        }) => {
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
            <h1 className="text-xl sm:text-2xl font-semibold mb-5 sm:mb-6">
                Today's deliveries
            </h1>

            {isLoading ? (
                <div className="space-y-3">
                    {[1, 2].map((i) => (
                        <div key={i} className="glass p-5 space-y-3">
                            <SkeletonBlock className="h-4 w-40" />
                            <SkeletonBlock className="h-3 w-24" />
                            <SkeletonBlock className="h-8 w-full rounded-full" />
                        </div>
                    ))}
                </div>
            ) : !data || data.length === 0 ? (
                <div className="glass p-10 text-center">
                    <div className="text-3xl mb-2">🛻</div>
                    <div className="text-dim text-sm">No deliveries assigned yet.</div>
                </div>
            ) : (
                <div className="space-y-3">
                    {data.map((d) => (
                        <div key={d.id} className="glass p-4 sm:p-5">
                            <div className="flex items-start justify-between gap-3">
                                <div className="min-w-0 flex-1">
                                    <div className="font-medium truncate text-sm sm:text-base">
                                        {d.dropoff_location}
                                    </div>
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

                            <div className="mt-4 grid grid-cols-2 gap-2">
                                {(NEXT[d.status] ?? []).map((s) => (
                                    <button
                                        key={s}
                                        className={`btn ${s === "failed" ? "btn-danger" : "btn-primary"
                                            } !py-2.5 text-xs w-full ${NEXT[d.status].length === 1 ? "col-span-2" : ""
                                            }`}
                                        disabled={advance.isPending}
                                        onClick={() => onAdvance(d, s)}
                                    >
                                        {s.replace(/_/g, " ")}
                                    </button>
                                ))}
                                {d.dropoff_lat != null && (
                                    <a
                                        className={`btn btn-ghost !py-2.5 text-xs w-full ${(NEXT[d.status] ?? []).length === 0 ? "col-span-2" : ""
                                            }`}
                                        href={`https://www.google.com/maps?q=${d.dropoff_lat},${d.dropoff_lng}`}
                                        target="_blank"
                                        rel="noreferrer"
                                    >
                                        Open in Maps
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