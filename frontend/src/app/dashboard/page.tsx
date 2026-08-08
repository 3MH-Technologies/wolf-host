"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Bot, Activity, Layers, ArrowUpRight } from "lucide-react";
import { Card } from "@/components/ui";
import { useLocale } from "@/hooks/useLocale";
import { apiClient } from "@/lib/api-client";
import type { Bot as BotType, Plan } from "@/types";

export default function DashboardPage() {
  const { t } = useLocale();
  const [bots, setBots] = useState<BotType[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);

  useEffect(() => {
    apiClient.get("/bots").then((res) => setBots(res.data));
    apiClient.get("/billing/plans").then((res) => setPlans(res.data));
  }, []);

  const runningCount = bots.filter((b) => b.status === "running").length;

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-slate-100 mb-6">{t.dashboard_title}</h1>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-500 text-xs mb-1">{t.total_bots}</p>
              <p className="text-3xl font-display font-bold text-slate-100">{bots.length}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-ember-500/10 flex items-center justify-center text-ember-400">
              <Bot size={20} />
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-500 text-xs mb-1">{t.running_bots}</p>
              <p className="text-3xl font-display font-bold text-signal-green">{runningCount}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-signal-green/10 flex items-center justify-center text-signal-green">
              <Activity size={20} />
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-500 text-xs mb-1">{t.plan_label}</p>
              <p className="text-lg font-display font-bold text-slate-100">{plans[0]?.name ?? "—"}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-signal-blue/10 flex items-center justify-center text-signal-blue">
              <Layers size={20} />
            </div>
          </div>
        </Card>
      </div>

      <div className="flex items-center justify-between mb-4">
        <h2 className="font-display font-semibold text-slate-200">{t.nav_bots}</h2>
        <Link href="/dashboard/bots" className="text-ember-400 text-sm flex items-center gap-1 hover:text-ember-300">
          {t.nav_bots} <ArrowUpRight size={14} />
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {bots.slice(0, 4).map((bot) => (
          <Link key={bot.id} href={`/dashboard/bots/${bot.id}`}>
            <Card className="hover:border-ember-500/40 transition-colors cursor-pointer">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-200">{bot.name}</span>
                <span className={`w-2 h-2 rounded-full status-dot ${bot.status === "running" ? "bg-signal-green" : "bg-slate-600"}`} />
              </div>
              <p className="text-slate-500 text-xs mt-1 font-mono">{bot.entrypoint}</p>
            </Card>
          </Link>
        ))}
        {bots.length === 0 && (
          <p className="text-slate-500 text-sm col-span-2">لا توجد بوتات بعد. أنشئ أول بوت من صفحة البوتات.</p>
        )}
      </div>
    </div>
  );
}
