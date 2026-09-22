import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useState } from "react";

import { api } from "../../shared/api/client";
import { SkeletonTable } from "../../shared/components/Skeleton";

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
    const [search, setSearch] = useState("");

    return (
        <div>
            <h1 className="text-3xl font-semibold mb-6">Inventory</h1>
            <div className="flex gap-2 mb-6 items-center">
                <button
                    className={`btn ${tab === "products" ? "btn-primary" : "btn-ghost"}`}
                    onClick={() => setTab("products")}
                >
                    Products
                </button>
                <button
                    className={`btn ${tab === "stock" ? "btn-primary" : "btn-ghost"}`}
                    onClick={() => setTab("stock")}
                >
                    Stock
                </button>
                <input
                    className="input !w-64 ml-2"
                    placeholder="Search…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>
            {tab === "products" ? (
                <ProductsTab qc={qc} search={search} />
            ) : (
                <StockTab qc={qc} search={search} />
            )}
        </div>
    );
}

function ProductsTab({ qc, search }: { qc: any; search: string }) {
    const [showForm, setShowForm] = useState(false);
    const [sku, setSku] = useState("");
    const [name, setName] = useState("");
    const [unit, setUnit] = useState("pc");

    const { data, isLoading } = useQuery({
        queryKey: ["products"],
        queryFn: async () => (await api.get<Product[]>("/inventory/products")).data,
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

    const filtered = (data ?? []).filter((p) => {
        if (!search) return true;
        const s = search.toLowerCase();
        return p.sku.toLowerCase().includes(s) || p.name.toLowerCase().includes(s);
    });

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
                <SkeletonTable rows={6} cols={4} />
            ) : (
                <div className="glass overflow-hidden">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>SKU</th>
                                <th>Name</th>
                                <th>Unit</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((p) => (
                                <tr key={p.id}>
                                    <td className="font-mono text-xs">{p.sku}</td>
                                    <td>{p.name}</td>
                                    <td className="text-dim">{p.unit}</td>
                                    <td>
                                        <span
                                            className={`text-xs px-2 py-1 rounded-full ${p.is_active
                                                    ? "bg-emerald-500/15 text-emerald-300"
                                                    : "bg-white/5 text-dim"
                                                }`}
                                        >
                                            {p.is_active ? "Active" : "Inactive"}
                                        </span>
                                    </td>
                                </tr>
                            ))}
                            {filtered.length === 0 && (
                                <tr>
                                    <td colSpan={4} className="text-center py-10">
                                        {data?.length === 0 ? (
                                            <>
                                                <div className="text-dim text-sm">No products yet.</div>
                                                <button
                                                    className="btn btn-primary mt-3 !py-1.5 !px-3 text-xs"
                                                    onClick={() => setShowForm(true)}
                                                >
                                                    Create your first product
                                                </button>
                                            </>
                                        ) : (
                                            <div className="text-dim text-sm">No matches.</div>
                                        )}
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

function StockTab({ qc, search }: { qc: any; search: string }) {
    const [showForm, setShowForm] = useState(false);
    const [productId, setProductId] = useState("");
    const [warehouseId, setWarehouseId] = useState("");
    const [quantity, setQuantity] = useState("1");

    const products = useQuery({
        queryKey: ["products"],
        queryFn: async () => (await api.get<Product[]>("/inventory/products")).data,
    });

    const warehouses = useQuery({
        queryKey: ["warehouses"],
        queryFn: async () => (await api.get<Warehouse[]>("/warehouses")).data,
    });

    const stock = useQuery({
        queryKey: ["stock"],
        queryFn: async () => (await api.get<Stock[]>("/inventory/stock")).data,
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

    const filtered = (stock.data ?? []).filter((s) => {
        if (!search) return true;
        const t = search.toLowerCase();
        return (
            productName(s.product_id).toLowerCase().includes(t) ||
            warehouseName(s.warehouse_id).toLowerCase().includes(t)
        );
    });

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

            {stock.isLoading ? (
                <SkeletonTable rows={6} cols={5} />
            ) : (
                <div className="glass overflow-hidden">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Product</th>
                                <th>Warehouse</th>
                                <th className="text-right">Qty</th>
                                <th className="text-right">Reserved</th>
                                <th className="text-right">Available</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map((s) => (
                                <tr key={s.id}>
                                    <td>{productName(s.product_id)}</td>
                                    <td className="text-dim">{warehouseName(s.warehouse_id)}</td>
                                    <td className="text-right">{s.quantity}</td>
                                    <td className="text-right text-dim">{s.reserved_quantity}</td>
                                    <td className="text-right font-semibold">{s.available}</td>
                                </tr>
                            ))}
                            {filtered.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="text-center py-10">
                                        {stock.data?.length === 0 ? (
                                            <>
                                                <div className="text-dim text-sm">No stock yet.</div>
                                                <button
                                                    className="btn btn-primary mt-3 !py-1.5 !px-3 text-xs"
                                                    onClick={() => setShowForm(true)}
                                                >
                                                    Receive stock
                                                </button>
                                            </>
                                        ) : (
                                            <div className="text-dim text-sm">No matches.</div>
                                        )}
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