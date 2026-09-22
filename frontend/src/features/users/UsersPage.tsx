import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import type { UserWithRoles } from "../../shared/api/users";
import {
    assignRole,
    deactivateUser,
    listRoles,
    listUsers,
    revokeRole,
} from "../../shared/api/users";
import InviteModal from "./InviteModal";

export default function UsersPage() {
    const qc = useQueryClient();
    const [inviteOpen, setInviteOpen] = useState(false);
    const [inviteLink, setInviteLink] = useState<string | null>(null);

    const users = useQuery({ queryKey: ["users"], queryFn: listUsers });
    const roles = useQuery({ queryKey: ["roles"], queryFn: listRoles });

    const assign = useMutation({
        mutationFn: ({ id, role }: { id: string; role: string }) => assignRole(id, role),
        onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
    });

    const revoke = useMutation({
        mutationFn: ({ id, role }: { id: string; role: string }) => revokeRole(id, role),
        onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
    });

    const deactivate = useMutation({
        mutationFn: (id: string) => deactivateUser(id),
        onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
    });

    return (
        <div>
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-semibold">Users</h1>
                <button className="btn btn-primary" onClick={() => setInviteOpen(true)}>
                    Invite user
                </button>
            </div>

            {inviteLink && (
                <div className="glass p-4 mb-6 flex items-center justify-between gap-3 text-sm">
                    <div className="truncate">
                        <span className="text-dim mr-2">Invite link:</span>
                        <span className="font-mono text-xs">{inviteLink}</span>
                    </div>
                    <div className="flex gap-2 shrink-0">
                        <button
                            className="btn btn-ghost !py-1 !px-3 text-xs"
                            onClick={() => navigator.clipboard.writeText(inviteLink)}
                        >
                            Copy
                        </button>
                        <button
                            className="btn btn-ghost !py-1 !px-2 text-xs"
                            onClick={() => setInviteLink(null)}
                        >
                            ✕
                        </button>
                    </div>
                </div>
            )}

            <div className="glass overflow-hidden">
                <table className="table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Roles</th>
                            <th>Status</th>
                            <th className="text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.data?.map((u) => (
                            <UserRow
                                key={u.id}
                                user={u}
                                roles={roles.data ?? []}
                                onAssign={(role) => assign.mutate({ id: u.id, role })}
                                onRevoke={(role) => revoke.mutate({ id: u.id, role })}
                                onDeactivate={() => deactivate.mutate(u.id)}
                            />
                        ))}
                        {!users.data && (
                            <tr>
                                <td colSpan={5} className="text-center text-dim py-8">
                                    Loading…
                                </td>
                            </tr>
                        )}
                        {users.data?.length === 0 && (
                            <tr>
                                <td colSpan={5} className="text-center text-dim py-8">
                                    No users yet.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {inviteOpen && roles.data && (
                <InviteModal
                    roles={roles.data}
                    onClose={() => setInviteOpen(false)}
                    onInvited={(link) => setInviteLink(link)}
                />
            )}
        </div>
    );
}

function UserRow({
    user,
    roles,
    onAssign,
    onRevoke,
    onDeactivate,
}: {
    user: UserWithRoles;
    roles: { name: string }[];
    onAssign: (role: string) => void;
    onRevoke: (role: string) => void;
    onDeactivate: () => void;
}) {
    const [newRole, setNewRole] = useState("");
    const candidates = roles.filter((r) => !user.roles.includes(r.name));

    return (
        <tr>
            <td>
                <div className="font-medium">{user.full_name || "—"}</div>
            </td>
            <td className="text-dim">{user.email}</td>
            <td>
                <div className="flex flex-wrap gap-1">
                    {user.roles.map((r) => (
                        <span key={r} className="status status-accent">
                            {r.replace(/_/g, " ")}
                            <button
                                className="ml-1 opacity-60 hover:opacity-100"
                                onClick={() => onRevoke(r)}
                                title="Revoke"
                            >
                                ✕
                            </button>
                        </span>
                    ))}
                    {candidates.length > 0 && (
                        <span className="inline-flex items-center">
                            <select
                                className="input !w-auto !py-0.5 !px-2 text-xs"
                                value={newRole}
                                onChange={(e) => {
                                    setNewRole(e.target.value);
                                    if (e.target.value) {
                                        onAssign(e.target.value);
                                        setNewRole("");
                                    }
                                }}
                            >
                                <option value="">+ add role</option>
                                {candidates.map((r) => (
                                    <option key={r.name} value={r.name}>
                                        {r.name.replace(/_/g, " ")}
                                    </option>
                                ))}
                            </select>
                        </span>
                    )}
                </div>
            </td>
            <td>
                <span className={`status ${user.is_active ? "status-success" : "status-neutral"}`}>
                    {user.is_active ? "active" : "inactive"}
                </span>
            </td>
            <td className="text-right">
                {user.is_active && (
                    <button
                        className="btn btn-ghost !py-1 !px-3 text-xs"
                        onClick={onDeactivate}
                    >
                        Deactivate
                    </button>
                )}
            </td>
        </tr>
    );
}