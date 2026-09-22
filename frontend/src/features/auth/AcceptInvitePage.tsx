import type { FormEvent } from "react";
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { acceptInvite } from "../../shared/api/users";

export default function AcceptInvitePage() {
    const [params] = useSearchParams();
    const token = params.get("token") ?? "";
    const [password, setPassword] = useState("");
    const [fullName, setFullName] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    async function onSubmit(e: FormEvent) {
        e.preventDefault();
        setError(null);
        setLoading(true);
        try {
            await acceptInvite(token, password, fullName);
            navigate("/login");
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
                    <p className="text-dim text-sm mt-1">Set a password to continue</p>
                </div>

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
                        minLength={8}
                        required
                    />
                </div>

                <button className="btn btn-primary w-full" disabled={loading}>
                    {loading ? "Creating account…" : "Accept invitation"}
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