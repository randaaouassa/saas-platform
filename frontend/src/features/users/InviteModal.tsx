import type { FormEvent } from "react";
import { useState } from "react";

import { inviteUser } from "../../shared/api/users";

interface Props {
    roles: { name: string }[];
    onClose: () => void;
    onInvited: (link: string) => void;
}

export default function InviteModal({ roles, onClose, onInvited }: Props) {
    const [email, setEmail] = useState("");
    const [role, setRole] = useState(roles[0]?.name ?? "warehouse_staff");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    async function onSubmit(e: FormEvent) {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            const inv = await inviteUser(email, role);
            const link = `${window.location.origin}/invite?token=${inv.id}`;
            onInvited(link);
            onClose();
        } catch (err: any) {
            setError(err?.response?.data?.title ?? "Failed to send invitation");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={onClose}
        >
            <form
                onSubmit={onSubmit}
                onClick={(e) => e.stopPropagation()}
                className="glass p-6 w-full max-w-md"
            >
                <div className="text-lg font-semibold mb-5">Invite a user</div>

                {error && (
                    <div className="mb-4 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
                        {error}
                    </div>
                )}

                <div className="mb-3">
                    <label className="label">Email</label>
                    <input
                        type="email"
                        className="input"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                </div>
                <div className="mb-6">
                    <label className="label">Role</label>
                    <select
                        className="input"
                        value={role}
                        onChange={(e) => setRole(e.target.value)}
                    >
                        {roles.map((r) => (
                            <option key={r.name} value={r.name}>
                                {r.name.replace(/_/g, " ")}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="flex justify-end gap-2">
                    <button type="button" className="btn btn-ghost" onClick={onClose}>
                        Cancel
                    </button>
                    <button className="btn btn-primary" disabled={loading}>
                        {loading ? "Inviting…" : "Invite"}
                    </button>
                </div>
            </form>
        </div>
    );
}