"use client";

import { useEffect, useState } from "react";
import { Card, Button, StatusBadge } from "@/components/ui";
import { useLocale } from "@/hooks/useLocale";
import { apiClient } from "@/lib/api-client";

interface AdminStats {
  total_users: number;
  total_bots: number;
  running_bots: number;
  total_revenue: number;
}

interface AdminUser {
  id: string;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  is_suspended: boolean;
  created_at: string;
}

interface AdminBot {
  id: string;
  name: string;
  status: string;
  owner_id: string;
}

export default function AdminPage() {
  const { t } = useLocale();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [bots, setBots] = useState<AdminBot[]>([]);
  const [tab, setTab] = useState<"users" | "bots" | "coupons">("users");
  const [couponCode, setCouponCode] = useState("");
  const [couponDiscount, setCouponDiscount] = useState("10");

  useEffect(() => {
    apiClient.get("/admin/stats").then((res) => setStats(res.data));
    apiClient.get("/admin/users").then((res) => setUsers(res.data));
    apiClient.get("/admin/bots").then((res) => setBots(res.data));
  }, []);

  const toggleSuspend = async (user: AdminUser) => {
    await apiClient.post(`/admin/users/${user.id}/${user.is_suspended ? "unsuspend" : "suspend"}`);
    apiClient.get("/admin/users").then((res) => setUsers(res.data));
  };

  const forceStopBot = async (id: string) => {
    await apiClient.post(`/admin/bots/${id}/force-stop`);
    apiClient.get("/admin/bots").then((res) => setBots(res.data));
  };

  const forceDeleteBot = async (id: string) => {
    if (!confirm(t.confirm_delete)) return;
    await apiClient.delete(`/admin/bots/${id}/force-delete`);
    apiClient.get("/admin/bots").then((res) => setBots(res.data));
  };

  const createCoupon = async () => {
    await apiClient.post("/admin/coupons", null, { params: { code: couponCode, discount_percent: Number(couponDiscount) } });
    setCouponCode("");
  };

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-slate-100 mb-6">{t.nav_admin}</h1>

      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card><p className="text-slate-500 text-xs mb-1">المستخدمون</p><p className="text-2xl font-display font-bold text-slate-100">{stats.total_users}</p></Card>
          <Card><p className="text-slate-500 text-xs mb-1">البوتات</p><p className="text-2xl font-display font-bold text-slate-100">{stats.total_bots}</p></Card>
          <Card><p className="text-slate-500 text-xs mb-1">نشطة الآن</p><p className="text-2xl font-display font-bold text-signal-green">{stats.running_bots}</p></Card>
          <Card><p className="text-slate-500 text-xs mb-1">الإيرادات</p><p className="text-2xl font-display font-bold text-ember-400">${stats.total_revenue}</p></Card>
        </div>
      )}

      <div className="flex gap-1 border-b border-slate-800 mb-5">
        {(["users", "bots", "coupons"] as const).map((tabName) => (
          <button
            key={tabName}
            onClick={() => setTab(tabName)}
            className={`px-4 py-2.5 text-sm border-b-2 transition-colors ${tab === tabName ? "border-ember-500 text-ember-400" : "border-transparent text-slate-500"}`}
          >
            {tabName}
          </button>
        ))}
      </div>

      {tab === "users" && (
        <div className="space-y-2">
          {users.map((u) => (
            <Card key={u.id} className="flex items-center justify-between py-3">
              <div>
                <p className="text-slate-200 text-sm">{u.username} — {u.email}</p>
                <p className="text-slate-500 text-xs">{u.role}</p>
              </div>
              <Button variant={u.is_suspended ? "secondary" : "danger"} onClick={() => toggleSuspend(u)}>
                {u.is_suspended ? "إلغاء الإيقاف" : "إيقاف"}
              </Button>
            </Card>
          ))}
        </div>
      )}

      {tab === "bots" && (
        <div className="space-y-2">
          {bots.map((b) => (
            <Card key={b.id} className="flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                <p className="text-slate-200 text-sm">{b.name}</p>
                <StatusBadge status={b.status} />
              </div>
              <div className="flex gap-2">
                <Button variant="secondary" onClick={() => forceStopBot(b.id)}>{t.stop}</Button>
                <Button variant="danger" onClick={() => forceDeleteBot(b.id)}>{t.delete}</Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {tab === "coupons" && (
        <Card>
          <h3 className="font-semibold text-slate-100 mb-4">إنشاء كوبون خصم</h3>
          <div className="flex gap-2">
            <input
              value={couponCode}
              onChange={(e) => setCouponCode(e.target.value)}
              placeholder="كود الكوبون"
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-ember-500"
            />
            <input
              value={couponDiscount}
              onChange={(e) => setCouponDiscount(e.target.value)}
              type="number"
              placeholder="نسبة الخصم %"
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 w-32 focus:outline-none focus:border-ember-500"
            />
            <Button onClick={createCoupon}>إنشاء</Button>
          </div>
        </Card>
      )}
    </div>
  );
}
