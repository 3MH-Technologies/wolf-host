"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { WolfLogo } from "@/components/WolfLogo";
import { Button, Input } from "@/components/ui";
import { useLocale } from "@/hooks/useLocale";
import { apiClient } from "@/lib/api-client";

export default function ForgotPasswordPage() {
  const { t } = useLocale();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await apiClient.post("/auth/forgot-password", { email });
    } finally {
      setSent(true);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-void px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <WolfLogo className="w-14 h-14 mb-3" />
          <h1 className="font-display text-2xl font-bold text-slate-100">{t.brand}</h1>
        </div>

        <div className="card-surface rounded-2xl p-8">
          {sent ? (
            <p className="text-slate-300 text-sm text-center">
              إذا كان هذا البريد مسجلاً، سيصلك رابط لإعادة تعيين كلمة المرور.
            </p>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input type="email" placeholder={t.email} value={email} onChange={(e) => setEmail(e.target.value)} required />
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "..." : t.forgot_password}
              </Button>
            </form>
          )}

          <div className="text-center mt-5 text-xs">
            <Link href="/login" className="text-ember-400 hover:text-ember-300">{t.login_button}</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
