import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
    Area,
    AreaChart,
    Bar,
    BarChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

import { api } from "../../shared/api/client";

interface RangeOrders {
    date: string;
    orders_count: number;
    delivered_count: number;
    cancelled_count: number;
    revenue: number;
}

interface RangeDeliveries {
    date: string;
    deliveries_count: number;
    delivered_count: number;
    failed_count: number;
    success_rate: number;
}

interface RangeResponse {
    from_date: string;
    to_date: string;
    orders: RangeOrders[];
    deliveries: RangeDeliveries[];
    total_revenue: number;
    total_orders: number;
    total_deliveries: number;
    total_delivered: number;
    total_failed: number;
    avg_delivery_time_s: number | null;
    top_products: { product_id: string; quantity: number }[];
}

function isoDaysAgo(n: number): string {
    const d = new Date();
    d.setDate(d.getDate() - n);
    return d.toISOString().slice(0, 10);
}

function isoToday(): string {
    return new Date().toISOString().slice(0, 10);
}

const RANGES = [
    { label: "7d", days: 7 },
    { label: "30d", days: 30 },
    { label: "90d", days: 90 },
];

export default function AnalyticsPage() {
    const [days, setDays] = useState(30);
    const from = isoDaysAgo(days);
    const to = isoToday();

    const range = useQuery({
        queryKey: ["analytics-range", from, to],
        queryFn: async () => {
            const { data } = await api.get<RangeResponse>(
                `/analytics/range?from=${from}&to=${to}`,
            );
            return data;
        },
    });

    async function exportCsv(kind: "orders" | "deliveries") {
        const res = await api.get(`/analytics/export/${kind}.csv?from=${from}&to=${to}`, {
            responseType: "blob",
        });
        const blob = new Blob([res.data], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${kind}-${from}-to-${to}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }

    const avgMin = range.data?.avg_delivery_time_s
        ? Math.round(range.data.avg_delivery_time_s / 60)
        : null;

    const successRate =
        range.data && range.data.total_delivered + range.data.total_failed > 0
            ? Math.round(
                (range.data.total_delivered /
                    (range.data.total_delivered + range.data.total_failed)) *
                100,
            )
            : 0;

    return (
        <div>
            <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
                <h1 className="text-3xl font-semibold">Analytics</h1>
                <div className="flex items-center gap-2">
                    {RANGES.map((r) => (
                        <button
                            key={r.label}
                            className={`btn ${days === r.days ? "btn-primary" : "btn-ghost"} !py-1.5 !px-3 text-xs`}
                            onClick={() => setDays(r.days)}
                        >
                            {r.label}
                        </button>
                    ))}
                    <button
                        className="btn btn-ghost !py-1.5 !px-3 text-xs"
                        onClick={() => exportCsv("orders")}
                    >
                        Export orders
                    </button>
                    <button
                        className="btn btn-ghost !py-1.5 !px-3 text-xs"
                        onClick={() => exportCsv("deliveries")}
                    >
                        Export deliveries
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <Stat
                    label="Revenue"
                    value={range.data ? `$${range.data.total_revenue.toFixed(0)}` : "—"}
                    tone="accent"
                />
                <Stat
                    label="Orders"
                    value={range.data?.total_orders ?? "—"}
                    tone="info"
                />
                <Stat
                    label="Success rate"
                    value={range.data ? `${successRate}%` : "—"}
                    tone="success"
                />
                <Stat
                    label="Avg delivery"
                    value={avgMin != null ? `${avgMin} min` : "—"}
                    tone="warning"
                />
            </div>

            <div className="glass p-6 mb-6">
                <div className="text-dim text-xs uppercase tracking-widest mb-4">
                    Revenue
                </div>
                <div style={{ height: 240 }}>
                    <ResponsiveContainer>
                        <AreaChart data={range.data?.orders ?? []}>
                            <defs>
                                <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#a855f7" stopOpacity={0.5} />
                                    <stop offset="100%" stopColor="#a855f7" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis
                                dataKey="date"
                                stroke="#6e6e73"
                                fontSize={11}
                                tickLine={false}
                                axisLine={false}
                            />
                            <YAxis
                                stroke="#6e6e73"
                                fontSize={11}
                                tickLine={false}
                                axisLine={false}
                            />
                            <Tooltip
                                contentStyle={{
                                    background: "rgba(20,20,22,0.95)",
                                    border: "1px solid rgba(255,255,255,0.08)",
                                    borderRadius: 12,
                                    fontSize: 12,
                                }}
                                labelStyle={{ color: "#a1a1a6" }}
                            />
                            <Area
                                type="monotone"
                                dataKey="revenue"
                                stroke="#a855f7"
                                strokeWidth={2}
                                fill="url(#rev)"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-4 mb-6">
                <div className="glass p-6">
                    <div className="text-dim text-xs uppercase tracking-widest mb-4">
                        Orders / day
                    </div>
                    <div style={{ height: 200 }}>
                        <ResponsiveContainer>
                            <BarChart data={range.data?.orders ?? []}>
                                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    stroke="#6e6e73"
                                    fontSize={11}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis
                                    stroke="#6e6e73"
                                    fontSize={11}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: "rgba(20,20,22,0.95)",
                                        border: "1px solid rgba(255,255,255,0.08)",
                                        borderRadius: 12,
                                        fontSize: 12,
                                    }}
                                    labelStyle={{ color: "#a1a1a6" }}
                                />
                                <Bar dataKey="orders_count" fill="#93c5fd" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="glass p-6">
                    <div className="text-dim text-xs uppercase tracking-widest mb-4">
                        Deliveries / day
                    </div>
                    <div style={{ height: 200 }}>
                        <ResponsiveContainer>
                            <BarChart data={range.data?.deliveries ?? []}>
                                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    stroke="#6e6e73"
                                    fontSize={11}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <YAxis
                                    stroke="#6e6e73"
                                    fontSize={11}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <Tooltip
                                    contentStyle={{
                                        background: "rgba(20,20,22,0.95)",
                                        border: "1px solid rgba(255,255,255,0.08)",
                                        borderRadius: 12,
                                        fontSize: 12,
                                    }}
                                    labelStyle={{ color: "#a1a1a6" }}
                                />
                                <Bar dataKey="delivered_count" fill="#86efac" radius={[4, 4, 0, 0]} />
                                <Bar dataKey="failed_count" fill="#fca5a5" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            <div className="glass p-6">
                <div className="text-dim text-xs uppercase tracking-widest mb-4">
                    Top products
                </div>
                {!range.data || range.data.top_products.length === 0 ? (
                    <div className="text-dim text-sm">No data for this range.</div>
                ) : (
                    <div className="space-y-2">
                        {range.data.top_products.map((p, i) => (
                            <div
                                key={p.product_id}
                                className="flex items-center justify-between text-sm border-t border-white/5 pt-2 first:border-0 first:pt-0"
                            >
                                <div className="flex items-center gap-3">
                                    <span className="text-dim text-xs w-4">#{i + 1}</span>
                                    <span className="font-mono text-xs">
                                        {p.product_id.slice(0, 8)}
                                    </span>
                                </div>
                                <span className="text-purple-300">{p.quantity}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function Stat({
    label,
    value,
    tone,
}: {
    label: string;
    value: string | number;
    tone: "accent" | "info" | "success" | "warning";
}) {
    const color = {
        accent: "text-purple-300",
        info: "text-blue-300",
        success: "text-emerald-300",
        warning: "text-amber-300",
    }[tone];
    return (
        <div className="glass p-5">
            <div className="text-dim text-xs uppercase tracking-widest">{label}</div>
            <div className={`text-2xl font-semibold mt-2 ${color}`}>{value}</div>
        </div>
    );
}