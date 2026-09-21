import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import type { FormEvent } from "react";

import { api } from "../../shared/api/client";

interface Product {
    id: string;
    sku: string;
    name: string;
    unit: string;
    is_active: boolean;
}

interface Warehouse {
    id: string;
    name: string;
    code: string;
}

interface Stock {
    id: string;
    product_id: string;
    warehouse_id: string;
    quantity: string;
    reserved_quantity: string;
    available: string;
}

export default function InventoryPage() {
    const qc = useQueryClient();
    const [tab, setTab] = useState<"products" | "stock">("products");

    return (
        <div>
            <h1 className="text-3xl font-semibold mb-6">Inventory</h1>
            <div className="flex gap-2 mb-6">
                <Tab active={tab === "products"} onClick={() => setTab("products")}>
                    Products
                </Tab>
                <Tab active={tab === "stock"} onClick={() => setTab("stock")}>
                    Stock
                </Tab>
            </div>
            {tab === "products" ? <ProductsTab qc={qc} /> : <StockTab qc={qc} />}
        </div>
    );
}

function Tab({
    active,
    onClick,
    children,
}: {
    active: boolean;
    onClick: () => void;
    children: React.ReactNode;
}) {
    return (
        <button
            onClick={onClick}
            className={`btn ${active ? "btn-primary" : "btn-ghost"}`}
        >
            {children}
        </button>
    );
}

function ProductsTab({ qc }: { qc: any }) {
    const [showForm, setShowForm] = useState(false);
    const [sku, setSku] = useState("");
    const [name, setName] = useState("");
    const [unit, setUnit] = useState("pc");

    const { data, isLoading } = useQuery({
        queryKey: ["products"],
        queryFn: async () => {
            const { data } = await api.get<Product[]>("/inventory/products");
            return data;
        },
    });

    const create = useMutation({
        mutationFn: async () => {
            const { data } = await api.post("/inventory/products", { sku, name, unit });
            return data;
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["products"] });
            setShowForm(false);
            setSku("");
            setName("");
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
                    {showForm ? "Cancel" : "New product"}
                </button>
            </div>

            {showForm && (
                <form onSubmit={onSubmit} className="glass p-6 mb-6 grid grid-cols-3 gap-4">
                    <div>
                        <label className="label">SKU</label>
                        <input className="input" value={sku} onChange={(e) => setSku(e.target.value)} required />
                    </div>
                    <div>
                        <label className="label">Name</label>
                        <input className="input" value={name} onChange={(e) => setName(e.target.value)} required />
                    </div>
                    <div>
                        <label className="label">Unit</label>
                        <input className="input" value={unit} onChange={(e) => setUnit(e.target.value)} />
                    </div>
                    <div className="col-span-3 flex justify-end">
                        <button className="btn btn-primary" disabled={create.isPending}>
                            Create
                        </button>
                    </div>
                </form>
            )}

            {isLoading ? (
                <div className="text-dim">Loading…</div>
            ) : (
                <div className="glass overflow-hidden">
                    <table className="w-full text-sm">
                        <thead className="text-dim text-xs uppercase tracking-widest">
                            <tr>
                                <th className="text-left px-4 py-3">SKU</th>
                                <th className="text-left px-4 py-3">Name</th>
                                <th className="text-left px-4 py-3">Unit</th>
                                <th className="text-left px-4 py-3">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data?.map((p) => (
                                <tr key={p.id} className="border-t border-white/5">
                                    <td className="px-4 py-3 font-mono">{p.sku}</td>
                                    <td className="px-4 py-3">{p.name}</td>
                                    <td className="px-4 py-3 text-dim">{p.unit}</td>
                                    <td className="px-4 py-3">
                                        <span className={`text-xs px-2 py-1 rounded-full ${p.is_active ? "bg-emerald-500/15 text-emerald-300" : "bg-white/5 text-dim"}`}>
                                            {p.is_active ? "Active" : "Inactive"}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                            {(!data || data.length === 0) && (
                                <tr>
                                    <td colSpan={4} className="px-4 py-8 text-center text-dim">
                                        No products yet.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </>
    );
}

function StockTab({ qc }: { qc: any }) {
    const [showForm, setShowForm] = useState(false);
    const [productId, setProductId] = useState("");
    const [warehouseId, setWarehouseId] = useState("");
    const [quantity, setQuantity] = useState("1");

    const products = useQuery({
        queryKey: ["products"],
        queryFn: async () => {
            const { data } = await api.get<Product[]>("/inventory/products");
            return data;
        },
    });

    const warehouses = useQuery({
        queryKey: ["warehouses"],
        queryFn: async () => {
            const { data } = await api.get<Warehouse[]>("/warehouses");
            return data;
        },
    });

    const stock = useQuery({
        queryKey: ["stock"],
        queryFn: async () => {
            const { data } = await api.get<Stock[]>("/inventory/stock");
            return data;
        },
    });

    const receive = useMutation({
        mutationFn: async () => {
            await api.post("/inventory/stock/receive", {
                product_id: productId,
                warehouse_id: warehouseId,
                quantity,
            });
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["stock"] });
            qc.invalidateQueries({ queryKey: ["movements"] });
            setShowForm(false);
            setQuantity("1");
        },
    });

    function onSubmit(e: FormEvent) {
        e.preventDefault();
        receive.mutate();
    }

    function productName(id: string) {
        return products.data?.find((p) => p.id === id)?.name ?? id.slice(0, 8);
    }
    function warehouseName(id: string) {
        return warehouses.data?.find((w) => w.id === id)?.name ?? id.slice(0, 8);
    }

    return (
        <>
            <div className="flex justify-end mb-4">
                <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
                    {showForm ? "Cancel" : "Receive stock"}
                </button>
            </div>

            {showForm && (
                <form onSubmit={onSubmit} className="glass p-6 mb-6 grid grid-cols-3 gap-4">
                    <div>
                        <label className="label">Product</label>
                        <select className="input" value={productId} onChange={(e) => setProductId(e.target.value)} required>
                            <option value="">Select…</option>
                            {products.data?.map((p) => (
                                <option key={p.id} value={p.id}>
                                    {p.name} ({p.sku})
                                </option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="label">Warehouse</label>
                        <select className="input" value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} required>
                            <option value="">Select…</option>
                            {warehouses.data?.map((w) => (
                                <option key={w.id} value={w.id}>
                                    {w.name}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="label">Quantity</label>
                        <input className="input" type="number" min="0.001" step="0.001" value={quantity} onChange={(e) => setQuantity(e.target.value)} />
                    </div>
                    <div className="col-span-3 flex justify-end">
                        <button className="btn btn-primary" disabled={receive.isPending}>
                            Receive
                        </button>
                    </div>
                </form>
            )}

            <div className="glass overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="text-dim text-xs uppercase tracking-widest">
                        <tr>
                            <th className="text-left px-4 py-3">Product</th>
                            <th className="text-left px-4 py-3">Warehouse</th>
                            <th className="text-right px-4 py-3">Qty</th>
                            <th className="text-right px-4 py-3">Reserved</th>
                            <th className="text-right px-4 py-3">Available</th>
                        </tr>
                    </thead>
                    <tbody>
                        {stock.data?.map((s) => (
                            <tr key={s.id} className="border-t border-white/5">
                                <td className="px-4 py-3">{productName(s.product_id)}</td>
                                <td className="px-4 py-3 text-dim">{warehouseName(s.warehouse_id)}</td>
                                <td className="px-4 py-3 text-right">{s.quantity}</td>
                                <td className="px-4 py-3 text-right text-dim">{s.reserved_quantity}</td>
                                <td className="px-4 py-3 text-right font-semibold">{s.available}</td>
                            </tr>
                        ))}
                        {(!stock.data || stock.data.length === 0) && (
                            <tr>
                                <td colSpan={5} className="px-4 py-8 text-center text-dim">
                                    No stock yet.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </>
    );
}