import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../../shared/api/client";
import { SkeletonBlock } from "../../shared/components/Skeleton";
import StatusBadge from "../../shared/components/StatusBadge";

interface OrderSummary {
    orders_count: number;
    delivered_count: number;
    cancelled_count: number;
    revenue: number;
}

interface DeliverySummary {
    deliveries_count: number;
    delivered_count: number;
    failed_count: number;
    success_rate: number;
}

interface DriverSummary {
    driver_id: string;
    deliveries_count: number;
    delivered_count: number;
}

interface InventorySummary {
    product_id: string;
    warehouse_id: string;
    on_hand: number;
    reserved: number;
    low_stock: boolean;
}

interface Overview {
    orders: OrderSummary | null;
    deliveries: DeliverySummary | null;
    drivers: DriverSummary[];
    inventory: InventorySummary[];
}

export default function DashboardPage() {
    const qc = useQueryClient();
    const today = new Date().toISOString().slice(0, 10);

    const { data, isLoading } = useQuery({
        queryKey: ["overview", today],
        queryFn: async () => {
            const { data } = await api.get<Overview>(
                `/analytics/overview?day=${today}`,
            );
            return data;
        },
    });

    const rebuild = useMutation({
        mutationFn: async () => {
            await api.post(`/analytics/rebuild?day=${today}`);
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ["overview", today] }),
    });

    const lowStock = data?.inventory.filter((i) => i.low_stock) ?? [];

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-semibold">Dashboard</h1>
                <button
                    className="btn btn-ghost !py-1.5 !px-3 text-xs"
                    onClick={() => rebuild.mutate()}
                    disabled={rebuild.isPending}
                >
                    {rebuild.isPending ? "Rebuilding…" : "Rebuild today"}
                </button>
            </div>

            {isLoading ? (
                <>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                        {Array.from({ length: 4 }).map((_, i) => (
                            <div key={i} className="glass p-5 space-y-3">
                                <SkeletonBlock className="h-3 w-24" />
                                <SkeletonBlock className="h-8 w-20" />
                            </div>
                        ))}
                    </div>
                    <div className="grid lg:grid-cols-2 gap-4">
                        <div className="glass p-5 space-y-3">
                            <SkeletonBlock className="h-4 w-40" />
                            {Array.from({ length: 4 }).map((_, i) => (
                                <SkeletonBlock key={i} className="h-4" />
                            ))}
                        </div>
                        <div className="glass p-5 space-y-3">
                            <SkeletonBlock className="h-4 w-40" />
                            {Array.from({ length: 4 }).map((_, i) => (
                                <SkeletonBlock key={i} className="h-4" />
                            ))}
                        </div>
                    </div>
                </>
            ) : (
                <>
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                        <Stat label="Orders today" value={data?.orders?.orders_count ?? 0} tone="info" />
                        <Stat label="Delivered" value={data?.orders?.delivered_count ?? 0} tone="success" />
                        <Stat
                            label="Revenue"
                            value={`$${(data?.orders?.revenue ?? 0).toFixed(0)}`}
                            tone="accent"
                        />
                        <Stat
                            label="Success rate"
                            value={
                                data?.deliveries
                                    ? `${Math.round((data.deliveries.success_rate ?? 0) * 100)}%`
                                    : "—"
                            }
                            tone="warning"
                        />
                    </div>

                    <div className="grid lg:grid-cols-2 gap-4">
                        <div className="glass p-5">
                            <div className="text-dim text-xs uppercase tracking-widest mb-4">
                                Deliveries today
                            </div>
                            {!data?.deliveries || data.deliveries.deliveries_count === 0 ? (
                                <div className="text-dim text-sm py-6 text-center">
                                    No deliveries today.
                                </div>
                            ) : (
                                <div className="space-y-2 text-sm">
                                    <Row label="Total" value={String(data.deliveries.deliveries_count)} />
                                    <Row label="Delivered" value={String(data.deliveries.delivered_count)} />
                                    <Row label="Failed" value={String(data.deliveries.failed_count)} />
                                </div>
                            )}
                        </div>

                        <div className="glass p-5">
                            <div className="text-dim text-xs uppercase tracking-widest mb-4">
                                Low stock ({lowStock.length})
                            </div>
                            {lowStock.length === 0 ? (
                                <div className="text-dim text-sm py-6 text-center">
                                    All stock healthy.
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {lowStock.slice(0, 5).map((i) => (
                                        <div
                                            key={`${i.product_id}-${i.warehouse_id}`}
                                            className="flex items-center justify-between text-sm border-t border-white/5 pt-2 first:border-0 first:pt-0"
                                        >
                                            <span className="font-mono text-xs text-dim">
                                                {i.product_id.slice(0, 8)}
                                            </span>
                                            <StatusBadge domain="delivery" value="failed" className="!text-[10px]" />
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}

function Stat({
    label,
    value,
    tone,
}: {
    label: string;
    value: number | string;
    tone: "info" | "success" | "accent" | "warning";
}) {
    const color = {
        info: "text-blue-300",
        success: "text-emerald-300",
        accent: "text-purple-300",
        warning: "text-amber-300",
    }[tone];
    return (
        <div className="glass p-5">
            <div className="text-dim text-xs uppercase tracking-widest">{label}</div>
            <div className={`text-3xl font-semibold mt-2 ${color}`}>{value}</div>
        </div>
    );
}

function Row({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex items-center justify-between border-t border-white/5 pt-2 first:border-0 first:pt-0">
            <span className="text-dim">{label}</span>
            <span>{value}</span>
        </div>
    );
}