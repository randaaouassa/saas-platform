import { Outlet } from "react-router-dom";

import AdminShell from "./AdminShell";

const NAV = [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/analytics", label: "Analytics" },
    { to: "/warehouses", label: "Warehouses" },
    { to: "/inventory", label: "Inventory" },
    { to: "/orders", label: "Orders" },
    { to: "/deliveries", label: "Deliveries" },
    { to: "/drivers", label: "Drivers" },
    { to: "/dispatch", label: "Dispatch" },
    { to: "/routing", label: "Routing" },
    { to: "/notifications", label: "Notifications" },
    { to: "/users", label: "Users" },
    { to: "/settings", label: "Settings" },
];

export default function AppLayout() {
    return (
        <AdminShell brand="SaaS Platform" nav={NAV}>
            <Outlet />
        </AdminShell>
    );
}