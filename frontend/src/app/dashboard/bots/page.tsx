"use client";

import { useEffect, useState, FormEvent } from "react";
import Link from "next/link";
import { Plus, X } from "lucide-react";
import { Card, Button, Input, StatusBadge } from "@/components/ui";
import { useLocale } from "@/hooks/useLocale";
import { apiClient } from "@/lib/api-client";
import type { Bot, BotSourceType } from "@/types";

export default function BotsPage() {
  const { t } = useLocale();
  const [bots, setBots] = useState<Bot[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState("");
  const [sourceType, setSourceType] = useState<BotSourceType>("zip");
  const [entrypoint, setEntrypoint] = useState("main.py");
  const [gitUrl, setGitUrl] = useState("");
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  const loadBots = () => apiClient.get("/bots").then((res) => setBots(res.data));

  useEffect(() => {
    loadBots();
  }, []);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setCreating(true);
    try {
      await apiClient.post("/bots", { name, source_type: sourceType, entrypoint, git_url: sourceType === "git" ? gitUrl : null });
      setShowModal(false);
      setName("");
      setGitUrl("");
      loadBots();
    } catch (err: any) {
      setError(err.response?.data?.detail || "create_failed");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-display text-2xl font-bold text-slate-100">{t.nav_bots}</h1>
        <Button onClick={() => setShowModal(true)} className="flex items-center gap-2">
          <Plus size={16} /> {t.create_bot}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {bots.map((bot) => (
          <Link key={bot.id} href={`/dashboard/bots/${bot.id}`}>
            <Card className="hover:border-ember-500/40 transition-colors cursor-pointer h-full">
              <div className="flex items-center justify-between mb-3">
                <span className="font-medium text-slate-200">{bot.name}</span>
                <StatusBadge status={bot.status} />
              </div>
              <p className="text-slate-500 text-xs font-mono mb-3">{bot.entrypoint}</p>
              <div className="flex gap-3 text-xs text-slate-500">
                <span>{bot.cpu_limit} CPU</span>
                <span>{bot.ram_limit_mb} MB</span>
                <span>{bot.restart_count} restarts</span>
              </div>
            </Card>
          </Link>
        ))}
        {bots.length === 0 && <p className="text-slate-500 text-sm">لا توجد بوتات بعد.</p>}
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 px-4">
          <div className="card-surface rounded-2xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-5">
              <h2 className="font-display font-semibold text-slate-100">{t.create_bot}</h2>
              <button onClick={() => setShowModal(false)} className="text-slate-500 hover:text-slate-300">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              <Input placeholder={t.bot_name} value={name} onChange={(e) => setName(e.target.value)} required />

              <select
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value as BotSourceType)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-ember-500"
              >
                <option value="zip">ZIP</option>
                <option value="single_file">Single File</option>
                <option value="git">Git Repository</option>
              </select>

              {sourceType === "git" && (
                <Input placeholder="https://github.com/user/repo.git" value={gitUrl} onChange={(e) => setGitUrl(e.target.value)} required />
              )}

              <Input placeholder={t.bot_entrypoint} value={entrypoint} onChange={(e) => setEntrypoint(e.target.value)} required />

              {error && <p className="text-signal-red text-xs">{error}</p>}

              <div className="flex gap-3 pt-2">
                <Button type="submit" className="flex-1" disabled={creating}>
                  {creating ? "..." : t.create_bot}
                </Button>
                <Button type="button" variant="secondary" onClick={() => setShowModal(false)}>
                  {t.cancel}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
