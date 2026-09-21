import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { api } from "../../shared/api/client";

interface Customer {
    id: string;
    name: string;
    email: string | null;
    address: string;
}

interface Product {
    id: string;
    sku: string;
    name: string;
}

interface Warehouse {
    id: string;
    name: string;
}

interface Order {
    id: string;
    number: string;
    status: string;
    currency: string;
    total_amount: string;
    customer_id: string;
    created_at: string;
    items: { id: string; product_id: string; quantity: string }[];
}

const NEXT_ACTIONS: Record<string, string[]> = {
    draft: ["confirmed", "cancelled"],
    confirmed: ["reserved", "cancelled"],
    reserved: ["picking", "cancelled"],
    picking: ["packed", "cancelled"],
    packed: ["ready_for_dispatch", "cancelled"],
    ready_for_dispatch: ["dispatched", "cancelled"],
    dispatched: ["delivered"],
};

export default function OrdersPage() {
    const qc = useQueryClient();
    const [tab, setTab] = useState<"orders" | "customers">("orders");

    return (
        <div>
            <h1 className="text-3xl font-semibold mb-6">Orders</h1>
            <div className="flex gap-2 mb-6">
                <button className={`btn ${tab === "orders" ? "btn-primary" : "btn-ghost"}`} onClick={() => setTab("orders")}>
                    Orders
                </button>
                <button className={`btn ${tab === "customers" ? "btn-primary" : "btn-ghost"}`} onClick={() => setTab("customers")}>
                    Customers
                </button>
            </div>
            {tab === "orders" ? <OrdersTab qc={qc} /> : <CustomersTab qc={qc} />}
        </div>
    );
}

function CustomersTab({ qc }: { qc: any }) {
    const [showForm, setShowForm] = useState(false);
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [address, setAddress] = useState("");
    const [lat, setLat] = useState("");
    const [lng, setLng] = useState("");

    const { data, isLoading } = useQuery({
        queryKey: ["customers"],
        queryFn: async () => (await api.get<Customer[]>("/customers")).data,
    });

    const create = useMutation({
        mutationFn: async () =>
            (
                await api.post("/customers", {
                    name,
                    email: email || null,
                    address,
                    lat: lat ? parseFloat(lat) : null,
                    lng: lng ? parseFloat(lng) : null,
                })
            ).data,
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["customers"] });
            setShowForm(false);
            setName("");
            setEmail("");
            setAddress("");
            setLat("");
            setLng("");
        },
    });

    function onSubmit(e: FormEvent) {
        e.preventDefault();
        create.mutate();
    }

    return (
        <>
            <div className="flex justify-end mb-4">
                <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
                    {showForm ? "Cancel" : "New customer"}
                </button>
            </div>
            {showForm && (
                <form onSubmit={onSubmit} className="glass p-6 mb-6 grid grid-cols-2 gap-4">
                    <div>
                        <label className="label">Name</label>
                        <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
                    </div>
                    <div>
                        <label className="label">Email</label>
                        <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
                    </div>
                    <div className="col-span-2">
                        <label className="label">Address</label>
                        <input className="input" value={address} onChange={(e) => setAddress(e.target.value)} />
                    </div>
                    <div>
                        <label className="label">Latitude</label>
                        <input className="input" value={lat} onChange={(e) => setLat(e.target.value)} placeholder="48.8566" />
                    </div>
                    <div>
                        <label className="label">Longitude</label>
                        <input className="input" value={lng} onChange={(e) => setLng(e.target.value)} placeholder="2.3522" />
                    </div>
                    <div className="col-span-2 flex justify-end">
                        <button className="btn btn-primary" disabled={create.isPending}>Create</button>
                    </div>
                </form>
            )}
            <div className="glass overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="text-dim text-xs uppercase tracking-widest">
                        <tr>
                            <th className="text-left px-4 py-3">Name</th>
                            <th className="text-left px-4 py-3">Email</th>
                            <th className="text-left px-4 py-3">Address</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data?.map((c) => (
                            <tr key={c.id} className="border-t border-white/5">
                                <td className="px-4 py-3">{c.name}</td>
                                <td className="px-4 py-3 text-dim">{c.email || "—"}</td>
                                <td className="px-4 py-3 text-dim">{c.address || "—"}</td>
                            </tr>
                        ))}
                        {(!data || data.length === 0) && !isLoading && (
                            <tr><td colSpan={3} className="px-4 py-8 text-center text-dim">No customers yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </>
    );
}

function OrdersTab({ qc }: { qc: any }) {
    const [showForm, setShowForm] = useState(false);

    const orders = useQuery({
        queryKey: ["orders"],
        queryFn: async () => (await api.get<Order[]>("/orders")).data,
    });

    return (
        <>
            <div className="flex justify-end mb-4">
                <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
                    {showForm ? "Cancel" : "New order"}
                </button>
            </div>
            {showForm && <NewOrderForm qc={qc} onDone={() => setShowForm(false)} />}
            <div className="glass overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="text-dim text-xs uppercase tracking-widest">
                        <tr>
                            <th className="text-left px-4 py-3">Number</th>
                            <th className="text-left px-4 py-3">Status</th>
                            <th className="text-right px-4 py-3">Total</th>
                            <th className="text-left px-4 py-3">Items</th>
                            <th className="text-right px-4 py-3">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {orders.data?.map((o) => (
                            <OrderRow key={o.id} order={o} qc={qc} />
                        ))}
                        {(!orders.data || orders.data.length === 0) && !orders.isLoading && (
                            <tr><td colSpan={5} className="px-4 py-8 text-center text-dim">No orders yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </>
    );
}

function OrderRow({ order, qc }: { order: Order; qc: any }) {
    const [warehouseId, setWarehouseId] = useState<string>("");

    const warehouses = useQuery({
        queryKey: ["warehouses"],
        queryFn: async () => (await api.get<Warehouse[]>("/warehouses")).data,
    });

    const transition = useMutation({
        mutationFn: async (target: string) => {
            const url = `/orders/${order.id}/status${target === "reserved" && warehouseId ? `?warehouse_id=${warehouseId}` : ""}`;
            await api.post(url, { status: target });
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ["orders"] }),
    });

    const actions = NEXT_ACTIONS[order.status] ?? [];

    return (
        <tr className="border-t border-white/5">
            <td className="px-4 py-3 font-mono">{order.number}</td>
            <td className="px-4 py-3">
                <span className="text-xs px-2 py-1 rounded-full bg-purple-500/15 text-purple-200">
                    {order.status}
                </span>
            </td>
            <td className="px-4 py-3 text-right">
                {order.currency} {Number(order.total_amount).toFixed(2)}
            </td>
            <td className="px-4 py-3 text-dim">{order.items.length}</td>
            <td className="px-4 py-3 text-right space-x-2">
                {order.status === "confirmed" && (
                    <select
                        className="input !w-auto !py-1 !px-2 text-xs inline-block"
                        value={warehouseId}
                        onChange={(e) => setWarehouseId(e.target.value)}
                    >
                        <option value="">Warehouse…</option>
                        {warehouses.data?.map((w) => (
                            <option key={w.id} value={w.id}>{w.name}</option>
                        ))}
                    </select>
                )}
                {actions.map((a) => (
                    <button
                        key={a}
                        className="btn btn-ghost !py-1 !px-3 text-xs"
                        disabled={transition.isPending || (a === "reserved" && !warehouseId)}
                        onClick={() => transition.mutate(a)}
                    >
                        → {a}
                    </button>
                ))}
            </td>
        </tr>
    );
}

function NewOrderForm({ qc, onDone }: { qc: any; onDone: () => void }) {
    const [number, setNumber] = useState(`ORD-${Date.now().toString().slice(-6)}`);
    const [customerId, setCustomerId] = useState("");
    const [warehouseId, setWarehouseId] = useState("");
    const [productId, setProductId] = useState("");
    const [quantity, setQuantity] = useState("1");
    const [price, setPrice] = useState("10");

    const customers = useQuery({
        queryKey: ["customers"],
        queryFn: async () => (await api.get<Customer[]>("/customers")).data,
    });
    const warehouses = useQuery({
        queryKey: ["warehouses"],
        queryFn: async () => (await api.get<Warehouse[]>("/warehouses")).data,
    });
    const products = useQuery({
        queryKey: ["products"],
        queryFn: async () => (await api.get<Product[]>("/inventory/products")).data,
    });

    const create = useMutation({
        mutationFn: async () =>
            (
                await api.post("/orders", {
                    customer_id: customerId,
                    number,
                    warehouse_id: warehouseId,
                    currency: "USD",
                    items: [{ product_id: productId, quantity, unit_price: price }],
                })
            ).data,
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["orders"] });
            onDone();
        },
    });

    function onSubmit(e: FormEvent) {
        e.preventDefault();
        create.mutate();
    }

    return (
        <form onSubmit={onSubmit} className="glass p-6 mb-6 grid grid-cols-2 gap-4">
            <div>
                <label className="label">Number</label>
                <input className="input" value={number} onChange={(e) => setNumber(e.target.value)} required />
            </div>
            <div>
                <label className="label">Customer</label>
                <select className="input" value={customerId} onChange={(e) => setCustomerId(e.target.value)} required>
                    <option value="">Select…</option>
                    {customers.data?.map((c) => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                </select>
            </div>
            <div>
                <label className="label">Warehouse</label>
                <select className="input" value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} required>
                    <option value="">Select…</option>
                    {warehouses.data?.map((w) => (
                        <option key={w.id} value={w.id}>{w.name}</option>
                    ))}
                </select>
            </div>
            <div>
                <label className="label">Product</label>
                <select className="input" value={productId} onChange={(e) => setProductId(e.target.value)} required>
                    <option value="">Select…</option>
                    {products.data?.map((p) => (
                        <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
                    ))}
                </select>
            </div>
            <div>
                <label className="label">Quantity</label>
                <input className="input" type="number" step="0.001" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
            </div>
            <div>
                <label className="label">Unit price</label>
                <input className="input" type="number" step="0.01" value={price} onChange={(e) => setPrice(e.target.value)} />
            </div>
            <div className="col-span-2 flex justify-end">
                <button className="btn btn-primary" disabled={create.isPending}>Create order</button>
            </div>
        </form>
    );
}