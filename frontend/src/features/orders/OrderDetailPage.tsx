import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../../shared/api/client";
import StatusBadge from "../../shared/components/StatusBadge";

interface OrderItem {
    id: string;
    product_id: string;
    quantity: string;
    unit_price: string;
    total_price: string;
}

interface Order {
    id: string;
    customer_id: string;
    number: string;
    status: string;
    currency: string;
    total_amount: string;
    notes: string;
    placed_at: string | null;
    created_at: string;
    items: OrderItem[];
}

interface HistoryEntry {
    id: string;
    from_status: string | null;
    to_status: string;
    actor_id: string | null;
    reason: string | null;
    created_at: string;
}

interface Warehouse {
    id: string;
    name: string;
}

const NEXT: Record<string, string[]> = {
    draft: ["confirmed", "cancelled"],
    confirmed: ["reserved", "cancelled"],
    reserved: ["picking", "cancelled"],
    picking: ["packed", "cancelled"],
    packed: ["ready_for_dispatch", "cancelled"],
    ready_for_dispatch: ["dispatched", "cancelled"],
    dispatched: ["delivered"],
};

export default function OrderDetailPage() {
    const { id } = useParams<{ id: string }>();
    const qc = useQueryClient();
    const navigate = useNavigate();
    const [warehouseId, setWarehouseId] = useState("");

    const order = useQuery({
        queryKey: ["order", id],
        queryFn: async () => (await api.get<Order>(`/orders/${id}`)).data,
        enabled: !!id,
    });

    const history = useQuery({
        queryKey: ["order-history", id],
        queryFn: async () => (await api.get<HistoryEntry[]>(`/orders/${id}/history`)).data,
        enabled: !!id,
    });

    const warehouses = useQuery({
        queryKey: ["warehouses"],
        queryFn: async () => (await api.get<Warehouse[]>("/warehouses")).data,
    });

    const transition = useMutation({
        mutationFn: async ({ target, reason }: { target: string; reason?: string }) => {
            const url = `/orders/${id}/status${target === "reserved" && warehouseId ? `?warehouse_id=${warehouseId}` : ""}`;
            await api.post(url, { status: target, reason });
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["order", id] });
            qc.invalidateQueries({ queryKey: ["order-history", id] });
            qc.invalidateQueries({ queryKey: ["orders"] });
        },
    });

    const cancelOrder = useMutation({
        mutationFn: async (reason: string) => {
            await api.post(`/orders/${id}/cancel`, { reason });
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["order", id] });
            qc.invalidateQueries({ queryKey: ["order-history", id] });
        },
    });

    function advance(target: string) {
        if (target === "cancelled") {
            const reason = window.prompt("Cancellation reason?");
            if (!reason) return;
            cancelOrder.mutate(reason);
            return;
        }
        transition.mutate({ target });
    }

    if (order.isLoading) {
        return <div className="text-dim">Loading…</div>;
    }
    if (order.isError || !order.data) {
        return (
            <div className="glass p-8 text-center">
                <div className="text-red-300 text-sm">Order not found.</div>
                <Link to="/orders" className="accent text-xs mt-3 inline-block hover:underline">
                    ← Back to orders
                </Link>
            </div>
        );
    }

    const o = order.data;
    const actions = NEXT[o.status] ?? [];

    return (
        <div>
            <Link to="/orders" className="text-xs text-dim hover:text-white">
                ← Orders
            </Link>

            <div className="flex items-start justify-between mt-4 mb-6 gap-4 flex-wrap">
                <div>
                    <h1 className="text-3xl font-semibold font-mono">{o.number}</h1>
                    <div className="text-dim text-xs mt-1">
                        Created {new Date(o.created_at).toLocaleString()}
                    </div>
                </div>
                <StatusBadge domain="order" value={o.status} />
            </div>

            <div className="grid lg:grid-cols-3 gap-4">
                <div className="lg:col-span-2 space-y-4">
                    <div className="glass p-6">
                        <div className="text-dim text-xs uppercase tracking-widest mb-4">
                            Items
                        </div>
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th className="text-right">Qty</th>
                                    <th className="text-right">Unit price</th>
                                    <th className="text-right">Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {o.items.map((it) => (
                                    <tr key={it.id}>
                                        <td className="font-mono text-xs">{it.product_id.slice(0, 8)}</td>
                                        <td className="text-right">{it.quantity}</td>
                                        <td className="text-right">{Number(it.unit_price).toFixed(2)}</td>
                                        <td className="text-right font-semibold">
                                            {Number(it.total_price).toFixed(2)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot>
                                <tr>
                                    <td colSpan={3} className="text-right text-dim pt-4">
                                        Total
                                    </td>
                                    <td className="text-right font-semibold pt-4">
                                        {o.currency} {Number(o.total_amount).toFixed(2)}
                                    </td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>

                    <div className="glass p-6">
                        <div className="text-dim text-xs uppercase tracking-widest mb-4">
                            Timeline
                        </div>
                        <ol className="space-y-3 text-sm">
                            {history.data?.map((h) => (
                                <li
                                    key={h.id}
                                    className="flex items-center justify-between border-t border-white/5 pt-3 first:border-0 first:pt-0"
                                >
                                    <div>
                                        <span className="text-dim mr-2">
                                            {h.from_status ? `${h.from_status} →` : "→"}
                                        </span>
                                        <StatusBadge domain="order" value={h.to_status} />
                                        {h.reason && (
                                            <span className="text-dim text-xs ml-3">“{h.reason}”</span>
                                        )}
                                    </div>
                                    <span className="text-dim text-xs">
                                        {new Date(h.created_at).toLocaleString()}
                                    </span>
                                </li>
                            ))}
                        </ol>
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="glass p-5">
                        <div className="text-dim text-xs uppercase tracking-widest mb-4">
                            Actions
                        </div>

                        {actions.length === 0 ? (
                            <div className="text-dim text-sm">No actions available.</div>
                        ) : (
                            <div className="space-y-2">
                                {o.status === "confirmed" && (
                                    <select
                                        className="input"
                                        value={warehouseId}
                                        onChange={(e) => setWarehouseId(e.target.value)}
                                    >
                                        <option value="">Select warehouse…</option>
                                        {warehouses.data?.map((w) => (
                                            <option key={w.id} value={w.id}>
                                                {w.name}
                                            </option>
                                        ))}
                                    </select>
                                )}
                                <div className="flex flex-wrap gap-2">
                                    {actions.map((a) => (
                                        <button
                                            key={a}
                                            className={`btn ${a === "cancelled" ? "btn-danger" : "btn-primary"} !py-1.5 !px-3 text-xs`}
                                            disabled={
                                                transition.isPending ||
                                                cancelOrder.isPending ||
                                                (a === "reserved" && !warehouseId)
                                            }
                                            onClick={() => advance(a)}
                                        >
                                            {a.replace(/_/g, " ")}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="glass p-5 text-sm">
                        <div className="text-dim text-xs uppercase tracking-widest mb-4">
                            Details
                        </div>
                        <div className="space-y-3">
                            <Row label="Customer" value={o.customer_id.slice(0, 8)} mono />
                            <Row label="Currency" value={o.currency} />
                            {o.placed_at && (
                                <Row
                                    label="Placed"
                                    value={new Date(o.placed_at).toLocaleString()}
                                />
                            )}
                            {o.notes && <Row label="Notes" value={o.notes} />}
                        </div>
                    </div>

                    <button
                        className="btn btn-ghost w-full text-xs"
                        onClick={() => navigate("/deliveries")}
                    >
                        View related deliveries →
                    </button>
                </div>
            </div>
        </div>
    );
}

function Row({
    label,
    value,
    mono,
}: {
    label: string;
    value: string;
    mono?: boolean;
}) {
    return (
        <div className="flex items-center justify-between gap-4 border-t border-white/5 pt-3 first:border-0 first:pt-0">
            <span className="text-dim">{label}</span>
            <span className={mono ? "font-mono text-xs" : "text-right"}>{value}</span>
        </div>
    );
}