"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { WolfLogo } from "@/components/WolfLogo";
import { Button, Input } from "@/components/ui";
import { useLocale } from "@/hooks/useLocale";
import { useAuth } from "@/hooks/useAuth";
import { AxiosError } from "axios";

export default function RegisterPage() {
  const { t } = useLocale();
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, username, password);
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>;
      setError(axiosError.response?.data?.detail || "register_failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-void px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <WolfLogo className="w-14 h-14 mb-3" />
          <h1 className="font-display text-2xl font-bold text-slate-100">{t.brand}</h1>
          <p className="text-slate-500 text-sm mt-1">{t.tagline}</p>
        </div>

        <div className="card-surface rounded-2xl p-8">
          <h2 className="text-lg font-semibold text-slate-100 mb-6">{t.create_account}</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input type="email" placeholder={t.email} value={email} onChange={(e) => setEmail(e.target.value)} required />
            <Input placeholder={t.username} value={username} onChange={(e) => setUsername(e.target.value)} required minLength={3} />
            <Input type="password" placeholder={t.password} value={password} onChange={(e) => setPassword(e.target.value)} required minLength={10} />

            {error && <p className="text-signal-red text-xs">{error}</p>}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "..." : t.register_button}
            </Button>
          </form>

          <div className="text-center mt-5 text-xs">
            <span className="text-slate-500">
              {t.have_account} <Link href="/login" className="text-ember-400 hover:text-ember-300">{t.login_button}</Link>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
