import { useQuery } from "@tanstack/react-query";

import { api } from "../../shared/api/client";

interface Overview {
    orders: any;
    deliveries: any;
    drivers: any[];
    inventory: any[];
}

export default function DashboardPage() {
    const today = new Date().toISOString().slice(0, 10);
    const { data, isLoading } = useQuery({
        queryKey: ["overview", today],
        queryFn: async () => {
            const { data } = await api.get<Overview>(`/analytics/overview?day=${today}`);
            return data;
        },
    });

    return (
        <div>
            <h1 className="text-3xl font-semibold mb-6">Dashboard</h1>
            {isLoading ? (
                <div className="text-dim">Loading…</div>
            ) : (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <Stat label="Orders today" value={data?.orders?.orders_count ?? 0} />
                    <Stat label="Delivered" value={data?.orders?.delivered_count ?? 0} />
                    <Stat label="Revenue" value={`$${data?.orders?.revenue ?? 0}`} />
                    <Stat label="Drivers" value={data?.drivers?.length ?? 0} />
                </div>
            )}
        </div>
    );
}

function Stat({ label, value }: { label: string; value: number | string }) {
    return (
        <div className="glass p-5">
            <div className="text-dim text-xs uppercase tracking-widest">{label}</div>
            <div className="text-2xl font-semibold mt-2">{value}</div>
        </div>
    );
}