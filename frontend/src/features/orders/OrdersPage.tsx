import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../../shared/api/client";
import StatusBadge from "../../shared/components/StatusBadge";

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

export default function OrdersPage() {
    const qc = useQueryClient();
    const [tab, setTab] = useState<"orders" | "customers">("orders");

    return (
        <div>
            <h1 className="text-3xl font-semibold mb-6">Orders</h1>
            <div className="flex gap-2 mb-6">
                <button
                    className={`btn ${tab === "orders" ? "btn-primary" : "btn-ghost"}`}
                    onClick={() => setTab("orders")}
                >
                    Orders
                </button>
                <button
                    className={`btn ${tab === "customers" ? "btn-primary" : "btn-ghost"}`}
                    onClick={() => setTab("customers")}
                >
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
                <table className="table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Address</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data?.map((c) => (
                            <tr key={c.id}>
                                <td>{c.name}</td>
                                <td className="text-dim">{c.email || "—"}</td>
                                <td className="text-dim">{c.address || "—"}</td>
                            </tr>
                        ))}
                        {(!data || data.length === 0) && !isLoading && (
                            <tr>
                                <td colSpan={3} className="text-center text-dim py-8">No customers yet.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </>
    );
}

function OrdersTab({ qc }: { qc: any }) {
    const [showForm, setShowForm] = useState(false);
    const navigate = useNavigate();

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
                <table className="table">
                    <thead>
                        <tr>
                            <th>Number</th>
                            <th>Status</th>
                            <th className="text-right">Total</th>
                            <th className="text-right">Items</th>
                        </tr>
                    </thead>
                    <tbody>
                        {orders.data?.map((o) => (
                            <tr
                                key={o.id}
                                className="cursor-pointer"
                                onClick={() => navigate(`/orders/${o.id}`)}
                            >
                                <td className="font-mono text-xs">{o.number}</td>
                                <td><StatusBadge domain="order" value={o.status} /></td>
                                <td className="text-right">
                                    {o.currency} {Number(o.total_amount).toFixed(2)}
                                </td>
                                <td className="text-right text-dim">{o.items.length}</td>
                            </tr>
                        ))}
                        {(!orders.data || orders.data.length === 0) && !orders.isLoading && (
                            <tr>
                                <td colSpan={4} className="text-center text-dim py-8">No orders yet.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </>
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