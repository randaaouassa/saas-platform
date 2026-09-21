import { Link } from "react-router-dom";

export default function LandingPage() {
    return (
        <div className="min-h-screen">
            <nav className="flex items-center justify-between px-8 py-6 max-w-6xl mx-auto">
                <div className="text-lg font-semibold">
                    <span className="accent">●</span> SaaS Platform
                </div>
                <div className="flex gap-3">
                    <Link to="/login" className="btn btn-ghost">Sign in</Link>
                    <Link to="/register" className="btn btn-primary">Get started</Link>
                </div>
            </nav>

            <section className="max-w-4xl mx-auto text-center px-6 pt-24 pb-32">
                <h1 className="text-6xl md:text-7xl font-semibold tracking-tight leading-[1.05]">
                    Logistics,
                    <br />
                    <span className="bg-gradient-to-r from-purple-300 to-purple-500 bg-clip-text text-transparent">
                        beautifully simple.
                    </span>
                </h1>
                <p className="text-dim text-xl mt-8 max-w-2xl mx-auto">
                    One platform to run warehouses, inventory, orders, deliveries, and
                    drivers. With smart dispatch, live tracking, and analytics.
                </p>
                <div className="flex justify-center gap-4 mt-10">
                    <Link to="/register" className="btn btn-primary">Start free</Link>
                    <a href="#features" className="btn btn-ghost">See features</a>
                </div>
            </section>

            <section id="features" className="max-w-6xl mx-auto px-6 pb-32">
                <div className="grid md:grid-cols-3 gap-6">
                    {[
                        { t: "Warehouse ops", d: "Receiving, picking, packing, transfers. Organized by zone and location." },
                        { t: "Smart dispatch", d: "Automatic driver ranking by distance, capacity, and workload." },
                        { t: "Live tracking", d: "Real-time status updates streamed to dispatchers and customers." },
                        { t: "Route planning", d: "Efficient multi-stop routes with one-click recalculation." },
                        { t: "Analytics", d: "Daily rollups for orders, deliveries, drivers, and stock." },
                        { t: "Multi-tenant", d: "Isolated data per organization, RBAC enforced at every layer." },
                    ].map((f) => (
                        <div key={f.t} className="glass p-6">
                            <div className="text-lg font-semibold">{f.t}</div>
                            <div className="text-dim mt-2 text-sm">{f.d}</div>
                        </div>
                    ))}
                </div>
            </section>

            <footer className="text-center pb-10 text-dim text-xs">
                © 2026 SaaS Platform - All rights reserved.
            </footer>
        </div>
    );
}