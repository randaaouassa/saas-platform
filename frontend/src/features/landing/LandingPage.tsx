import { Link } from "react-router-dom";

import {
    IconAdmin,
    IconBrain,
    IconCart,
    IconChart,
    IconDispatcher,
    IconDriver,
    IconPackage,
    IconRoute,
    IconShield,
    IconSignal,
    IconTruck,
    IconWarehouse,
} from "../../shared/components/Icons";

const FEATURES = [
    { t: "Warehouse ops", d: "Receiving, picking, packing, transfers — organized by zone and location.", Icon: IconWarehouse },
    { t: "Inventory", d: "SKUs, stock, movements, reservations, low-stock alerts, and history.", Icon: IconPackage },
    { t: "Orders", d: "Create, import, reserve, pack, dispatch. Full lifecycle with history.", Icon: IconCart },
    { t: "Deliveries", d: "Jobs, packages, status, proof of delivery, failed handling.", Icon: IconTruck },
    { t: "Smart dispatch", d: "Ranked driver matching by distance, capacity, and current workload.", Icon: IconBrain },
    { t: "Route optimization", d: "Multi-stop sequencing with ETA and one-click recalculation.", Icon: IconRoute },
    { t: "Real-time tracking", d: "Live location and status streamed to dispatchers and customers.", Icon: IconSignal },
    { t: "Analytics", d: "Orders, deliveries, drivers, inventory — with CSV exports.", Icon: IconChart },
    { t: "Multi-tenant", d: "Isolated data per organization, RBAC enforced at every layer.", Icon: IconShield },
];

const STEPS = [
    { n: "01", t: "Order arrives", d: "Customer order is created. Inventory is checked and reserved." },
    { n: "02", t: "Pick & pack", d: "Warehouse staff complete the task. Order is packed and ready." },
    { n: "03", t: "Dispatch", d: "Best driver selected by distance, capacity, and workload." },
    { n: "04", t: "Deliver", d: "Optimized route. Customer tracks live. Proof of delivery captured." },
];

const ROLES = [
    { t: "Warehouse", d: "Receive, pick, pack, and transfer stock.", Icon: IconWarehouse },
    { t: "Dispatcher", d: "Queue, assign, and monitor deliveries.", Icon: IconDispatcher },
    { t: "Driver", d: "Mobile console with route and POD.", Icon: IconDriver },
    { t: "Admin", d: "Analytics, users, roles, and settings.", Icon: IconAdmin },
];

export default function LandingPage() {
    return (
        <div className="min-h-screen overflow-x-hidden">
            <nav className="flex items-center justify-between px-4 sm:px-8 py-5 max-w-6xl mx-auto">
                <div className="text-base sm:text-lg font-semibold">
                    <span className="accent">●</span> SaaS Platform
                </div>
                <div className="flex gap-2">
                    <Link to="/login" className="btn btn-ghost !py-1.5 !px-3 sm:!px-4 text-xs sm:text-sm">
                        Sign in
                    </Link>
                    <Link to="/register" className="btn btn-primary !py-1.5 !px-3 sm:!px-4 text-xs sm:text-sm">
                        Get started
                    </Link>
                </div>
            </nav>

            <section className="max-w-4xl mx-auto text-center px-4 sm:px-6 pt-16 sm:pt-24 pb-20 sm:pb-32">
                <div className="inline-block text-xs px-3 py-1 rounded-full border border-white/10 bg-white/5 text-dim mb-6">
                    Multi-tenant B2B Logistics SaaS
                </div>
                <h1 className="text-4xl sm:text-6xl md:text-7xl font-semibold tracking-tight leading-[1.05]">
                    Logistics,
                    <br />
                    <span className="bg-gradient-to-r from-purple-300 via-purple-400 to-purple-600 bg-clip-text text-transparent">
                        beautifully simple.
                    </span>
                </h1>
                <p className="text-dim text-base sm:text-xl mt-6 sm:mt-8 max-w-2xl mx-auto">
                    One platform to run warehouses, inventory, orders, deliveries, and
                    drivers — with smart dispatch, live tracking, and analytics.
                </p>
                <div className="flex justify-center gap-3 mt-8 sm:mt-10 flex-wrap">
                    <Link to="/register" className="btn btn-primary !px-6 !py-3">
                        Start free
                    </Link>
                    <a href="#features" className="btn btn-ghost !px-6 !py-3">
                        See features
                    </a>
                </div>

                <div className="flex items-center justify-center gap-6 mt-10 text-dim text-xs">
                    <div className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                        Live tracking
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                        Smart dispatch
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                        Role-based access
                    </div>
                </div>
            </section>

            <section id="features" className="max-w-6xl mx-auto px-4 sm:px-6 pb-20 sm:pb-32">
                <div className="text-center mb-12">
                    <div className="text-dim text-xs uppercase tracking-widest mb-3">
                        Modules
                    </div>
                    <h2 className="text-3xl sm:text-4xl font-semibold">
                        Everything your operation needs
                    </h2>
                </div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {FEATURES.map((f) => (
                        <div key={f.t} className="glass glass-hover p-5 sm:p-6">
                            <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-300 flex items-center justify-center mb-4">
                                <f.Icon className="w-5 h-5" />
                            </div>
                            <div className="text-base font-semibold">{f.t}</div>
                            <div className="text-dim mt-2 text-sm leading-relaxed">{f.d}</div>
                        </div>
                    ))}
                </div>
            </section>

            <section className="max-w-6xl mx-auto px-4 sm:px-6 pb-20 sm:pb-32">
                <div className="text-center mb-12">
                    <div className="text-dim text-xs uppercase tracking-widest mb-3">
                        Workflow
                    </div>
                    <h2 className="text-3xl sm:text-4xl font-semibold">
                        From order to doorstep
                    </h2>
                </div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {STEPS.map((s) => (
                        <div key={s.n} className="glass p-6">
                            <div className="text-purple-400 text-xs font-mono">{s.n}</div>
                            <div className="text-base font-semibold mt-2">{s.t}</div>
                            <div className="text-dim text-sm mt-2 leading-relaxed">{s.d}</div>
                        </div>
                    ))}
                </div>
            </section>

            <section className="max-w-6xl mx-auto px-4 sm:px-6 pb-20 sm:pb-32">
                <div className="text-center mb-12">
                    <div className="text-dim text-xs uppercase tracking-widest mb-3">
                        Built for
                    </div>
                    <h2 className="text-3xl sm:text-4xl font-semibold">
                        Every role in the operation
                    </h2>
                </div>
                <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {ROLES.map((r) => (
                        <div key={r.t} className="glass p-5 text-center">
                            <div className="w-12 h-12 rounded-2xl bg-purple-500/10 text-purple-300 flex items-center justify-center mx-auto mb-4">
                                <r.Icon className="w-6 h-6" />
                            </div>
                            <div className="font-semibold">{r.t}</div>
                            <div className="text-dim text-xs mt-2">{r.d}</div>
                        </div>
                    ))}
                </div>
            </section>

            <section className="max-w-3xl mx-auto text-center px-4 sm:px-6 pb-24 sm:pb-32">
                <h2 className="text-3xl sm:text-5xl font-semibold tracking-tight">
                    Ready to run your operation
                    <br />
                    <span className="bg-gradient-to-r from-purple-300 to-purple-600 bg-clip-text text-transparent">
                        from one place?
                    </span>
                </h2>
                <p className="text-dim mt-6">
                    Spin up a workspace in seconds. No credit card. No setup.
                </p>
                <div className="flex justify-center gap-3 mt-8 flex-wrap">
                    <Link to="/register" className="btn btn-primary !px-6 !py-3">
                        Create workspace
                    </Link>
                    <Link to="/login" className="btn btn-ghost !px-6 !py-3">
                        Sign in
                    </Link>
                </div>
            </section>

            <footer className="border-t border-white/5 py-8">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-dim">
                    <div>
                        <span className="accent">●</span> SaaS Platform
                    </div>
                    <div className="flex gap-6">
                        <span>Proprietary · All rights reserved</span>
                        <span>© 2026</span>
                    </div>
                </div>
            </footer>
        </div>
    );
}