"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authApi } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

export default function RegisterPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [error,    setError]    = useState("");
  const [loading,  setLoading]  = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 6) { setError("Password must be at least 6 characters."); return; }
    setLoading(true);
    setError("");
    try {
      await authApi.register(email, password, fullName);
      await login(email, password);
      router.replace("/scan");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="card w-full max-w-sm">
        <div className="text-center mb-6">
          <span className="text-4xl">🥗</span>
          <h1 className="text-2xl font-bold mt-2">Create account</h1>
          <p className="text-gray-500 text-sm mt-1">Free forever — no credit card needed</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700">Full name</label>
            <input className="input mt-1" value={fullName}
              onChange={(e) => setFullName(e.target.value)} placeholder="Optional" />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Email</label>
            <input className="input mt-1" type="email" value={email}
              onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700">Password</label>
            <input className="input mt-1" type="password" value={password}
              onChange={(e) => setPassword(e.target.value)} required />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button className="btn-primary w-full" type="submit" disabled={loading}>
            {loading ? "Creating account…" : "Sign up"}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-4">
          Already have an account?{" "}
          <Link href="/login" className="text-brand-600 hover:underline font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
