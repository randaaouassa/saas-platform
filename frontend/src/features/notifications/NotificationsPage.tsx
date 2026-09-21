import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../shared/api/client";

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
                    className="btn btn-ghost"
                    onClick={() => markAll.mutate()}
                    disabled={markAll.isPending || unread.length === 0}
                >
                    Mark all read ({unread.length})
                </button>
            </div>

            <div className="space-y-2">
                {mine.data?.map((n) => (
                    <div
                        key={n.id}
                        className={`glass p-4 flex items-center justify-between ${n.read_at ? "opacity-60" : ""}`}
                    >
                        <div>
                            <div className="text-sm font-medium">{n.template}</div>
                            <div className="text-dim text-xs">
                                {n.channel} · {new Date(n.created_at).toLocaleString()}
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <span className="text-xs px-2 py-1 rounded-full bg-white/5">{n.status}</span>
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
                {(!mine.data || mine.data.length === 0) && (
                    <div className="glass p-8 text-center text-dim">No notifications.</div>
                )}
            </div>
        </div>
    );
}