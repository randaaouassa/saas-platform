import type { FormEvent } from "react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { fetchMe, login } from "../../shared/api/auth";
import { homePathForRoles, useAuthStore } from "../../shared/stores/auth";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [slug, setSlug] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const setTokens = useAuthStore((s) => s.setTokens);
    const setUser = useAuthStore((s) => s.setUser);

    async function onSubmit(e: FormEvent) {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            const tokens = await login({ email, password, organization_slug: slug });
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
            setError(err?.response?.data?.title ?? "Login failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-6">
            <form onSubmit={onSubmit} className="glass p-8 w-full max-w-sm">
                <div className="text-center mb-6">
                    <div className="text-2xl font-semibold">
                        <span className="accent">●</span> SaaS Platform
                    </div>
                    <p className="text-dim text-sm mt-1">Sign in to your workspace</p>
                </div>

                {error && (
                    <div className="mb-4 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
                        {error}
                    </div>
                )}

                <div className="mb-3">
                    <label className="label">Organization</label>
                    <input
                        className="input"
                        value={slug}
                        onChange={(e) => setSlug(e.target.value)}
                        placeholder="acme"
                        required
                    />
                </div>
                <div className="mb-3">
                    <label className="label">Email</label>
                    <input
                        type="email"
                        className="input"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="email"
                        required
                    />
                </div>
                <div className="mb-5">
                    <label className="label">Password</label>
                    <input
                        type="password"
                        className="input"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="current-password"
                        required
                    />
                </div>

                <button className="btn btn-primary w-full" disabled={loading}>
                    {loading ? "Signing in…" : "Sign in"}
                </button>

                <p className="text-dim text-sm text-center mt-5">
                    No account?{" "}
                    <Link to="/register" className="accent hover:underline">
                        Create one
                    </Link>
                </p>
            </form>
        </div>
    );
}