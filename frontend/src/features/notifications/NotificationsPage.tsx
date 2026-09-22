import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../shared/api/client";
import { SkeletonBlock } from "../../shared/components/Skeleton";
import StatusBadge from "../../shared/components/StatusBadge";

interface Notification {
    id: string;
    channel: string;
    template: string;
    status: string;
    read_at: string | null;
    created_at: string;
}

export default function NotificationsPage() {
    const qc = useQueryClient();

    const mine = useQuery({
        queryKey: ["notifications", "mine"],
        queryFn: async () => (await api.get<Notification[]>("/notifications/mine")).data,
        refetchInterval: 20000,
    });

    const markAll = useMutation({
        mutationFn: async () => (await api.post("/notifications/mine/read-all")).data,
        onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
    });

    const markOne = useMutation({
        mutationFn: async (id: string) => (await api.post(`/notifications/${id}/read`)).data,
        onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
    });

    const unread = mine.data?.filter((n) => !n.read_at) ?? [];

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-semibold">Notifications</h1>
                <button
                    className="btn btn-ghost !py-1.5 !px-3 text-xs"
                    onClick={() => markAll.mutate()}
                    disabled={markAll.isPending || unread.length === 0}
                >
                    Mark all read {unread.length > 0 && `(${unread.length})`}
                </button>
            </div>

            {mine.isLoading ? (
                <div className="space-y-2">
                    {Array.from({ length: 5 }).map((_, i) => (
                        <div key={i} className="glass p-4 flex items-center justify-between">
                            <div className="space-y-2 flex-1">
                                <SkeletonBlock className="h-4 w-48" />
                                <SkeletonBlock className="h-3 w-32" />
                            </div>
                            <SkeletonBlock className="h-6 w-20 rounded-full" />
                        </div>
                    ))}
                </div>
            ) : mine.data && mine.data.length > 0 ? (
                <div className="space-y-2">
                    {mine.data.map((n) => (
                        <div
                            key={n.id}
                            className={`glass p-4 flex items-center justify-between ${n.read_at ? "opacity-60" : ""
                                }`}
                        >
                            <div className="min-w-0">
                                <div className="text-sm font-medium truncate">{n.template}</div>
                                <div className="text-dim text-xs">
                                    <StatusBadge domain="channel" value={n.channel} className="!text-[10px]" />
                                    <span className="ml-2">
                                        {new Date(n.created_at).toLocaleString()}
                                    </span>
                                </div>
                            </div>
                            <div className="flex items-center gap-3">
                                <StatusBadge domain="order" value={n.status} className="!text-[10px]" />
                                {!n.read_at && (
                                    <button
                                        className="btn btn-ghost !py-1 !px-3 text-xs"
                                        onClick={() => markOne.mutate(n.id)}
                                    >
                                        Mark read
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="glass p-10 text-center">
                    <div className="text-3xl mb-2">🔔</div>
                    <div className="text-dim text-sm">No notifications yet.</div>
                </div>
            )}
        </div>
    );
}