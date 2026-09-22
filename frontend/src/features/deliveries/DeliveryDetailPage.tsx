import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../../shared/api/client";
import StatusBadge from "../../shared/components/StatusBadge";

interface Package {
    id: string;
    code: string;
    weight: string | null;
    length: string | null;
    width: string | null;
    height: string | null;
    volume: string | null;
}

interface Delivery {
    id: string;
    status: string;
    dropoff_location: string;
    dropoff_lat: number | null;
    dropoff_lng: number | null;
    pickup_location: string;
    pickup_lat: number | null;
    pickup_lng: number | null;
    scheduled_at: string | null;
    delivered_at: string | null;
    failed_reason: string | null;
    public_token: string | null;
    created_at: string;
    packages: Package[];
}

interface HistoryEntry {
    id: string;
    from_status: string | null;
    to_status: string;
    actor_id: string | null;
    lat: number | null;
    lng: number | null;
    note: string | null;
    created_at: string;
}

interface POD {
    id: string;
    kind: string;
    s3_key: string | null;
    signer_name: string | null;
    captured_at: string;
}

const NEXT: Record<string, string[]> = {
    pending: ["assigned", "cancelled"],
    assigned: ["picked_up", "cancelled"],
    picked_up: ["in_transit", "failed"],
    in_transit: ["delivered", "failed"],
    failed: ["rescheduled", "returned"],
    rescheduled: ["assigned", "cancelled"],
};

export default function DeliveryDetailPage() {
    const { id } = useParams<{ id: string }>();
    const qc = useQueryClient();
    const [podKind, setPodKind] = useState("photo");
    const [podKey, setPodKey] = useState("");
    const [podSigner, setPodSigner] = useState("");

    const delivery = useQuery({
        queryKey: ["delivery", id],
        queryFn: async () => (await api.get<Delivery>(`/deliveries/${id}`)).data,
        enabled: !!id,
    });

    const history = useQuery({
        queryKey: ["delivery-history", id],
        queryFn: async () =>
            (await api.get<HistoryEntry[]>(`/deliveries/${id}/history`)).data,
        enabled: !!id,
    });

    const pods = useQuery({
        queryKey: ["delivery-pods", id],
        queryFn: async () => (await api.get<POD[]>(`/deliveries/${id}/pod`)).data,
        enabled: !!id,
    });

    const transition = useMutation({
        mutationFn: async ({ target, reason }: { target: string; reason?: string }) => {
            await api.post(`/deliveries/${id}/status`, {
                status: target,
                failed_reason: reason,
            });
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["delivery", id] });
            qc.invalidateQueries({ queryKey: ["delivery-history", id] });
        },
    });

    const reschedule = useMutation({
        mutationFn: async (iso: string) => {
            await api.post(`/deliveries/${id}/reschedule`, { scheduled_at: iso });
        },
        onSuccess: () => qc.invalidateQueries({ queryKey: ["delivery", id] }),
    });

    const addPod = useMutation({
        mutationFn: async () => {
            await api.post(`/deliveries/${id}/pod`, {
                kind: podKind,
                s3_key: podKey || null,
                signer_name: podSigner || null,
            });
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: ["delivery-pods", id] });
            setPodKey("");
            setPodSigner("");
        },
    });

    function advance(target: string) {
        if (target === "failed") {
            const reason = window.prompt("Failure reason?");
            if (!reason) return;
            transition.mutate({ target, reason });
            return;
        }
        if (target === "rescheduled") {
            const iso = window.prompt(
                "New schedule (ISO, e.g. 2026-06-01T10:00:00Z):",
            );
            if (!iso) return;
            reschedule.mutate(iso);
            return;
        }
        transition.mutate({ target });
    }

    if (delivery.isLoading) return <div className="text-dim">Loading…</div>;
    if (delivery.isError || !delivery.data) {
        return (
            <div className="glass p-8 text-center">
                <div className="text-red-300 text-sm">Delivery not found.</div>
                <Link to="/deliveries" className="accent text-xs mt-3 inline-block hover:underline">
                    ← Back to deliveries
                </Link>
            </div>
        );
    }

    const d = delivery.data;
    const trackingUrl = d.public_token
        ? `${window.location.origin}/track/${d.public_token}`
        : null;
    const actions = NEXT[d.status] ?? [];

    return (
        <div>
            <Link to="/deliveries" className="text-xs text-dim hover:text-white">
                ← Deliveries
            </Link>

            <div className="flex items-start justify-between mt-4 mb-6 gap-4 flex-wrap">
                <div>
                    <h1 className="text-3xl font-semibold">{d.dropoff_location}</h1>
                    <div className="text-dim text-xs mt-1 font-mono">{d.id.slice(0, 8)}</div>
                </div>
                <StatusBadge domain="delivery" value={d.status} />
            </div>

            {trackingUrl && (
                <div className="glass p-4 mb-4 flex items-center justify-between gap-3 text-xs">
                    <div className="truncate">
                        <span className="text-dim mr-2">Customer tracking:</span>
                        <span className="font-mono">{trackingUrl}</span>
                    </div>
                    <div className="flex gap-2 shrink-0">
                        <button
                            className="btn btn-ghost !py-1 !px-3 text-xs"
                            onClick={() => navigator.clipboard.writeText(trackingUrl)}
                        >
                            Copy
                        </button>
                        <a
                            href={trackingUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="btn btn-ghost !py-1 !px-3 text-xs"
                        >
                            Open
                        </a>
                    </div>
                </div>
            )}

            <div className="grid lg:grid-cols-3 gap-4">
                <div className="lg:col-span-2 space-y-4">
                    <div className="glass p-6">
                        <div className="text-dim text-xs uppercase tracking-widest mb-4">
                            Packages
                        </div>
                        {d.packages.length === 0 ? (
                            <div className="text-dim text-sm">No packages.</div>
                        ) : (
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Code</th>
                                        <th className="text-right">Weight</th>
                                        <th className="text-right">Dims</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {d.packages.map((p) => (
                                        <tr key={p.id}>
                                            <td className="font-mono text-xs">{p.code}</td>
                                            <td className="text-right">{p.weight ?? "—"}</td>
                                            <td className="text-right text-dim text-xs">
                                                {p.length && p.width && p.height
                                                    ? `${p.length}×${p.width}×${p.height}`
                                                    : "—"}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>

                    <div className="glass p-6">
                        <div className="text-dim text-xs uppercase tracking-widest mb-4">
                            Timeline
                        </div>
                        <ol className="space-y-3 text-sm">
                            {history.data?.map((h) => (
                                <li
                                    key={h.id}
                                    className="flex items-center justify-between border-t border-white/5 pt-3 first:border-0 first:pt-0"
                                >
                                    <div>
                                        <span className="text-dim mr-2">
                                            {h.from_status ? `${h.from_status} →` : "→"}
                                        </span>
                                        <StatusBadge domain="delivery" value={h.to_status} />
                                        {h.note && (
                                            <span className="text-dim text-xs ml-3">“{h.note}”</span>
                                        )}
                                    </div>
                                    <span className="text-dim text-xs">
                                        {new Date(h.created_at).toLocaleString()}
                                    </span>
                                </li>
                            ))}
                        </ol>
                    </div>

                    <div className="glass p-6">
                        <div className="text-dim text-xs uppercase tracking-widest mb-4">
                            Proof of delivery
                        </div>

                        {pods.data && pods.data.length > 0 && (
                            <div className="space-y-2 mb-4">
                                {pods.data.map((p) => (
                                    <div
                                        key={p.id}
                                        className="flex items-center justify-between text-sm border-t border-white/5 pt-2 first:border-0 first:pt-0"
                                    >
                                        <div>
                                            <span className="status status-info mr-2">{p.kind}</span>
                                            {p.signer_name && (
                                                <span className="text-dim text-xs">{p.signer_name}</span>
                                            )}
                                        </div>
                                        <span className="text-dim text-xs">
                                            {new Date(p.captured_at).toLocaleString()}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="grid grid-cols-3 gap-2">
                            <select
                                className="input"
                                value={podKind}
                                onChange={(e) => setPodKind(e.target.value)}
                            >
                                <option value="photo">photo</option>
                                <option value="signature">signature</option>
                                <option value="otp">otp</option>
                                <option value="note">note</option>
                            </select>
                            <input
                                className="input"
                                placeholder="S3 key / URL"
                                value={podKey}
                                onChange={(e) => setPodKey(e.target.value)}
                            />
                            <input
                                className="input"
                                placeholder="Signer name"
                                value={podSigner}
                                onChange={(e) => setPodSigner(e.target.value)}
                            />
                        </div>
                        <button
                            className="btn btn-primary mt-3 !py-1.5 !px-3 text-xs"
                            onClick={() => addPod.mutate()}
                            disabled={addPod.isPending}
                        >
                            Add POD
                        </button>
                    </div>
                </div>

                <div className="space-y-4">
                    <div className="glass p-5">
                        <div className="text-dim text-xs uppercase tracking-widest mb-4">
                            Actions
                        </div>
                        {actions.length === 0 ? (
                            <div className="text-dim text-sm">No actions available.</div>
                        ) : (
                            <div className="flex flex-wrap gap-2">
                                {actions.map((a) => (
                                    <button
                                        key={a}
                                        className={`btn ${a === "cancelled" || a === "failed" ? "btn-danger" : "btn-primary"
                                            } !py-1.5 !px-3 text-xs`}
                                        disabled={transition.isPending || reschedule.isPending}
                                        onClick={() => advance(a)}
                                    >
                                        {a.replace(/_/g, " ")}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className="glass p-5 text-sm">
                        <div className="text-dim text-xs uppercase tracking-widest mb-4">
                            Details
                        </div>
                        <div className="space-y-3">
                            <Row label="Pickup" value={d.pickup_location || "—"} />
                            <Row label="Scheduled" value={d.scheduled_at ? new Date(d.scheduled_at).toLocaleString() : "—"} />
                            <Row label="Delivered" value={d.delivered_at ? new Date(d.delivered_at).toLocaleString() : "—"} />
                            {d.failed_reason && <Row label="Failed" value={d.failed_reason} />}
                            {d.dropoff_lat != null && (
                                <Row
                                    label="Coords"
                                    value={`${d.dropoff_lat.toFixed(4)}, ${d.dropoff_lng?.toFixed(4)}`}
                                    mono
                                />
                            )}
                        </div>
                    </div>

                    {d.dropoff_lat != null && (
                        <a
                            className="btn btn-ghost w-full text-xs"
                            href={`https://www.google.com/maps?q=${d.dropoff_lat},${d.dropoff_lng}`}
                            target="_blank"
                            rel="noreferrer"
                        >
                            Open in Maps
                        </a>
                    )}
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
            <span className={mono ? "font-mono text-xs" : "text-right"}>{value}</span>
        </div>
    );
}