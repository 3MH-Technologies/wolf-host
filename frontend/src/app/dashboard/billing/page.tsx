"use client";

import { useEffect, useState } from "react";
import { Check, Copy } from "lucide-react";
import { Card, Button } from "@/components/ui";
import { useLocale } from "@/hooks/useLocale";
import { apiClient } from "@/lib/api-client";
import type { Plan } from "@/types";

interface Invoice {
  id: string;
  status: string;
  amount: number;
  currency: string;
  provider: string;
  crypto_address: string | null;
  created_at: string;
  expires_at: string;
}

const PROVIDERS = [
  { value: "stripe", label: "Stripe" },
  { value: "paypal", label: "PayPal" },
  { value: "usdt_trc20", label: "USDT (TRC20)" },
  { value: "usdt_bep20", label: "USDT (BEP20)" },
];

export default function BillingPage() {
  const { t } = useLocale();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [provider, setProvider] = useState("usdt_trc20");
  const [coupon, setCoupon] = useState("");
  const [txHash, setTxHash] = useState("");
  const [activeInvoice, setActiveInvoice] = useState<Invoice | null>(null);
  const [error, setError] = useState("");

  const loadInvoices = () => apiClient.get("/billing/invoices").then((res) => setInvoices(res.data));

  useEffect(() => {
    apiClient.get("/billing/plans").then((res) => setPlans(res.data));
    loadInvoices();
  }, []);

  const handleSubscribe = async (plan: Plan) => {
    setSelectedPlan(plan);
    setError("");
    try {
      const res = await apiClient.post("/billing/invoices", { plan_id: plan.id, provider, coupon_code: coupon || null });
      setActiveInvoice(res.data);
      loadInvoices();
    } catch (err: any) {
      setError(err.response?.data?.detail || "invoice_failed");
    }
  };

  const confirmCrypto = async () => {
    if (!activeInvoice || !txHash) return;
    try {
      await apiClient.post(`/billing/invoices/${activeInvoice.id}/confirm-crypto`, null, { params: { tx_hash: txHash } });
      setActiveInvoice(null);
      setTxHash("");
      loadInvoices();
    } catch (err: any) {
      setError(err.response?.data?.detail || "confirm_failed");
    }
  };

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-slate-100 mb-6">{t.nav_billing}</h1>

      <div className="mb-6">
        <div className="flex gap-2 mb-4">
          {PROVIDERS.map((p) => (
            <button
              key={p.value}
              onClick={() => setProvider(p.value)}
              className={`px-3 py-1.5 rounded-lg text-xs border ${provider === p.value ? "border-ember-500 text-ember-400 bg-ember-500/10" : "border-slate-700 text-slate-400"}`}
            >
              {p.label}
            </button>
          ))}
          <input
            value={coupon}
            onChange={(e) => setCoupon(e.target.value)}
            placeholder="كود الخصم"
            className="px-3 py-1.5 rounded-lg text-xs bg-slate-900 border border-slate-700 text-slate-300 focus:outline-none focus:border-ember-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {plans.map((plan) => (
          <Card key={plan.id} className="flex flex-col">
            <p className="text-ember-400 text-xs font-semibold uppercase tracking-wide mb-1">{plan.tier}</p>
            <p className="font-display text-xl font-bold text-slate-100 mb-3">{plan.name}</p>
            <p className="text-3xl font-display font-bold text-slate-100 mb-4">${plan.price_monthly}<span className="text-sm text-slate-500">/شهر</span></p>
            <ul className="text-xs text-slate-400 space-y-1.5 mb-5 flex-1">
              <li className="flex items-center gap-2"><Check size={12} className="text-signal-green" /> {plan.max_bots} بوتات</li>
              <li className="flex items-center gap-2"><Check size={12} className="text-signal-green" /> {plan.ram_limit_mb} MB RAM</li>
              <li className="flex items-center gap-2"><Check size={12} className="text-signal-green" /> {plan.storage_limit_mb} MB تخزين</li>
              <li className="flex items-center gap-2"><Check size={12} className="text-signal-green" /> {plan.cpu_limit} CPU</li>
            </ul>
            <Button onClick={() => handleSubscribe(plan)} className="w-full">اشترك</Button>
          </Card>
        ))}
      </div>

      {error && <p className="text-signal-red text-sm mb-4">{error}</p>}

      {activeInvoice && activeInvoice.crypto_address && (
        <Card className="mb-8">
          <h3 className="font-semibold text-slate-100 mb-3">إتمام الدفع عبر {activeInvoice.provider}</h3>
          <p className="text-slate-400 text-sm mb-2">أرسل ${activeInvoice.amount} إلى العنوان التالي:</p>
          <div className="flex items-center gap-2 bg-slate-950 rounded-lg p-3 mb-4">
            <code className="text-xs text-ember-400 flex-1 break-all">{activeInvoice.crypto_address}</code>
            <button onClick={() => navigator.clipboard.writeText(activeInvoice.crypto_address!)} className="text-slate-500 hover:text-slate-300">
              <Copy size={14} />
            </button>
          </div>
          <input
            value={txHash}
            onChange={(e) => setTxHash(e.target.value)}
            placeholder="هاش المعاملة (Transaction Hash)"
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 mb-3 focus:outline-none focus:border-ember-500"
          />
          <Button onClick={confirmCrypto}>تأكيد الدفع</Button>
        </Card>
      )}

      <h2 className="font-display font-semibold text-slate-200 mb-4">الفواتير</h2>
      <div className="space-y-2">
        {invoices.map((inv) => (
          <Card key={inv.id} className="flex items-center justify-between py-3">
            <div>
              <p className="text-slate-200 text-sm">${inv.amount} — {inv.provider}</p>
              <p className="text-slate-500 text-xs">{new Date(inv.created_at).toLocaleDateString("ar")}</p>
            </div>
            <span className={`text-xs px-2 py-1 rounded-full ${inv.status === "paid" ? "bg-signal-green/10 text-signal-green" : "bg-slate-800 text-slate-400"}`}>
              {inv.status}
            </span>
          </Card>
        ))}
        {invoices.length === 0 && <p className="text-slate-500 text-sm">لا توجد فواتير بعد.</p>}
      </div>
    </div>
  );
}
