import { Outlet } from "react-router-dom";

import AdminShell from "./AdminShell";

const NAV = [
    { to: "/warehouse", label: "Overview" },
    { to: "/warehouse/warehouses", label: "Warehouses" },
    { to: "/warehouse/inventory", label: "Inventory" },
    { to: "/warehouse/orders", label: "Orders" },
    { to: "/warehouse/deliveries", label: "Deliveries" },
    { to: "/warehouse/notifications", label: "Notifications" },
];

export default function WarehouseLayout() {
    return (
        <AdminShell
            brand="Warehouse"
            nav={NAV}
            topics={["dispatcher", "delivery"]}
        >
            <Outlet />
        </AdminShell>
    );
}