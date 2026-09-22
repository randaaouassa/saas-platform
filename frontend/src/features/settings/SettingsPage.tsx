import { useQuery } from "@tanstack/react-query";

import { api } from "../../shared/api/client";
import { primaryRole, useAuthStore } from "../../shared/stores/auth";

interface Org {
    id: string;
    name: string;
    slug: string;
    plan: string;
    status: string;
    created_at: string;
}

export default function SettingsPage() {
    const user = useAuthStore((s) => s.user);

    const org = useQuery({
        queryKey: ["my-org"],
        queryFn: async () => (await api.get<Org>("/auth/me/organization")).data,
    });

    return (
        <div>
            <h1 className="text-3xl font-semibold mb-6">Settings</h1>

            <div className="grid md:grid-cols-2 gap-4">
                <div className="glass p-6">
                    <div className="text-dim text-xs uppercase tracking-widest mb-4">
                        Organization
                    </div>
                    {org.data ? (
                        <div className="space-y-3 text-sm">
                            <Row label="Name" value={org.data.name} />
                            <Row label="Slug" value={org.data.slug} mono />
                            <Row label="Plan" value={org.data.plan} />
                            <Row label="Status" value={org.data.status} />
                            <Row
                                label="Created"
                                value={new Date(org.data.created_at).toLocaleDateString()}
                            />
                        </div>
                    ) : (
                        <div className="text-dim text-sm">Loading…</div>
                    )}
                </div>

                <div className="glass p-6">
                    <div className="text-dim text-xs uppercase tracking-widest mb-4">
                        Your account
                    </div>
                    {user ? (
                        <div className="space-y-3 text-sm">
                            <Row label="Name" value={user.full_name || "—"} />
                            <Row label="Email" value={user.email} />
                            <Row label="Role" value={primaryRole(user.roles)?.replace(/_/g, " ") ?? "—"} />
                            <Row label="User ID" value={user.id.slice(0, 8)} mono />
                        </div>
                    ) : (
                        <div className="text-dim text-sm">Not signed in.</div>
                    )}
                </div>
            </div>

            <div className="mt-8">
                <div className="glass p-6">
                    <div className="text-dim text-xs uppercase tracking-widest mb-4">
                        Platform
                    </div>
                    <div className="text-sm space-y-2">
                        <div>
                            <span className="text-dim mr-2">API docs:</span>
                            <a
                                className="accent hover:underline"
                                href="http://localhost:8000/docs"
                                target="_blank"
                                rel="noreferrer"
                            >
                                Swagger
                            </a>
                        </div>
                        <div>
                            <span className="text-dim mr-2">Metrics:</span>
                            <a
                                className="accent hover:underline"
                                href="http://localhost:8000/metrics"
                                target="_blank"
                                rel="noreferrer"
                            >
                                Prometheus
                            </a>
                        </div>
                        <div>
                            <span className="text-dim mr-2">Grafana:</span>
                            <a
                                className="accent hover:underline"
                                href="http://localhost:3000"
                                target="_blank"
                                rel="noreferrer"
                            >
                                localhost:3000
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function Row({
    label,
    value,
    mono,
}: {
    label: string;
    value: string;
    mono?: boolean;
}) {
    return (
        <div className="flex items-center justify-between gap-4 border-t border-white/5 pt-3 first:border-0 first:pt-0">
            <span className="text-dim">{label}</span>
            <span className={mono ? "font-mono text-xs" : ""}>{value}</span>
        </div>
    );
}