import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { fetchMe, register } from "../../shared/api/auth";
import { useAuthStore } from "../../shared/stores/auth";

export default function RegisterPage() {
    const [orgName, setOrgName] = useState("");
    const [slug, setSlug] = useState("");
    const [email, setEmail] = useState("");
    const [fullName, setFullName] = useState("");
    const [password, setPassword] = useState("");
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
            const tokens = await register({
                organization: { name: orgName, slug },
                email,
                password,
                full_name: fullName,
            });
            setTokens(tokens.access_token, tokens.refresh_token);
            const me = await fetchMe();
            setUser({
                id: me.id,
                email: me.email,
                full_name: me.full_name,
                role: me.role,
                organization_id: me.organization_id,
            });
            navigate("/dashboard");
        } catch (err: any) {
            setError(err?.response?.data?.title ?? "Registration failed");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-6">
            <form onSubmit={onSubmit} className="glass p-8 w-full max-w-md">
                <div className="text-center mb-6">
                    <div className="text-2xl font-semibold">
                        <span className="accent">●</span> Create workspace
                    </div>
                    <p className="text-dim text-sm mt-1">Spin up a new organization</p>
                </div>

                {error && (
                    <div className="mb-4 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                        <label className="label">Company</label>
                        <input className="input" value={orgName} onChange={(e) => setOrgName(e.target.value)} required />
                    </div>
                    <div>
                        <label className="label">Slug</label>
                        <input className="input" value={slug} onChange={(e) => setSlug(e.target.value)} placeholder="acme" required />
                    </div>
                </div>
                <div className="mb-3">
                    <label className="label">Your name</label>
                    <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} />
                </div>
                <div className="mb-3">
                    <label className="label">Email</label>
                    <input type="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} required />
                </div>
                <div className="mb-5">
                    <label className="label">Password</label>
                    <input type="password" className="input" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
                </div>

                <button className="btn btn-primary w-full" disabled={loading}>
                    {loading ? "Creating…" : "Create workspace"}
                </button>

                <p className="text-dim text-sm text-center mt-5">
                    Have an account?{" "}
                    <Link to="/login" className="accent hover:underline">
                        Sign in
                    </Link>
                </p>
            </form>
        </div>
    );
}