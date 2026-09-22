import { useQuery } from "@tanstack/react-query";
import type { FormEvent } from "react";
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { fetchMe } from "../../shared/api/auth";
import { acceptInvite, validateInvite } from "../../shared/api/users";
import { homePathForRoles, useAuthStore } from "../../shared/stores/auth";

export default function AcceptInvitePage() {
    const [params] = useSearchParams();
    const token = params.get("token") ?? "";
    const navigate = useNavigate();
    const setTokens = useAuthStore((s) => s.setTokens);
    const setUser = useAuthStore((s) => s.setUser);

    const [password, setPassword] = useState("");
    const [fullName, setFullName] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const invite = useQuery({
        queryKey: ["invite", token],
        queryFn: () => validateInvite(token),
        enabled: !!token,
        retry: false,
    });

    async function onSubmit(e: FormEvent) {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            const tokens = await acceptInvite(token, password, fullName);
            setTokens(tokens.access_token, tokens.refresh_token);
            const me = await fetchMe();
            setUser({
                id: me.id,
                email: me.email,
                full_name: me.full_name,
                roles: me.roles,
                organization_id: me.organization_id,
            });
            navigate(homePathForRoles(me.roles));
        } catch (err: any) {
            setError(err?.response?.data?.title ?? "Invalid or expired invitation");
        } finally {
            setLoading(false);
        }
    }

    if (!token) {
        return (
            <div className="min-h-screen flex items-center justify-center p-6">
                <div className="glass p-8 max-w-sm text-center">
                    <div className="text-red-300 text-sm">Missing invitation token.</div>
                    <Link to="/login" className="accent text-sm mt-4 inline-block hover:underline">
                        Back to sign in
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-6">
            <form onSubmit={onSubmit} className="glass p-8 w-full max-w-sm">
                <div className="text-center mb-6">
                    <div className="text-2xl font-semibold">
                        <span className="accent">●</span> Join workspace
                    </div>
                    {invite.data ? (
                        <div className="mt-3 text-sm">
                            <div className="text-dim text-xs uppercase tracking-widest">
                                You're joining
                            </div>
                            <div className="text-white font-medium mt-1">
                                {invite.data.org_name}
                            </div>
                            <div className="text-dim text-xs mt-1">
                                as{" "}
                                <span className="text-purple-300">
                                    {invite.data.role_name.replace(/_/g, " ")}
                                </span>
                            </div>
                            <div className="text-dim text-xs mt-2">{invite.data.email}</div>
                        </div>
                    ) : (
                        <p className="text-dim text-sm mt-1">Set a password to continue</p>
                    )}
                </div>

                {invite.isError && (
                    <div className="mb-4 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
                        This invitation is invalid or expired.
                    </div>
                )}

                {error && (
                    <div className="mb-4 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
                        {error}
                    </div>
                )}

                <div className="mb-3">
                    <label className="label">Your name</label>
                    <input
                        className="input"
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                    />
                </div>
                <div className="mb-5">
                    <label className="label">Password</label>
                    <input
                        type="password"
                        className="input"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="new-password"
                        minLength={8}
                        required
                    />
                </div>

                <button
                    className="btn btn-primary w-full"
                    disabled={loading || !invite.data}
                >
                    {loading ? "Joining…" : "Accept & sign in"}
                </button>

                <p className="text-dim text-sm text-center mt-5">
                    Already have an account?{" "}
                    <Link to="/login" className="accent hover:underline">
                        Sign in
                    </Link>
                </p>
            </form>
        </div>
    );
}