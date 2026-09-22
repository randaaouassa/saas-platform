import { Outlet } from "react-router-dom";

import AdminShell from "./AdminShell";

const NAV = [
    { to: "/dispatcher", label: "Overview" },
    { to: "/dispatcher/dispatch", label: "Dispatch" },
    { to: "/dispatcher/routing", label: "Routes" },
    { to: "/dispatcher/drivers", label: "Drivers" },
    { to: "/dispatcher/deliveries", label: "Deliveries" },
    { to: "/dispatcher/notifications", label: "Notifications" },
];

export default function DispatcherLayout() {
    return (
        <AdminShell
            brand="Dispatcher"
            nav={NAV}
            topics={["dispatcher", "delivery", "driver"]}
        >
            <Outlet />
        </AdminShell>
    );
}