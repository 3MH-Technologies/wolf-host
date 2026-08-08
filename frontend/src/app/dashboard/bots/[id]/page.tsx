"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { Play, Square, RotateCw, Trash2, Upload } from "lucide-react";
import { Card, Button, StatusBadge } from "@/components/ui";
import { useLocale } from "@/hooks/useLocale";
import { apiClient, API_URL } from "@/lib/api-client";
import type { Bot, BotStats, FileEntry } from "@/types";

type Tab = "logs" | "files" | "console" | "environment" | "stats";

export default function BotDetailPage() {
  const { t } = useLocale();
  const params = useParams();
  const router = useRouter();
  const botId = params.id as string;

  const [bot, setBot] = useState<Bot | null>(null);
  const [tab, setTab] = useState<Tab>("logs");
  const [logs, setLogs] = useState("");
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [currentPath, setCurrentPath] = useState("");
  const [envText, setEnvText] = useState("");
  const [stats, setStats] = useState<BotStats | null>(null);
  const [consoleOutput, setConsoleOutput] = useState<string[]>([]);
  const [consoleInput, setConsoleInput] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadBot = useCallback(async () => {
    const res = await apiClient.get(`/bots/${botId}`);
    setBot(res.data);
    setEnvText(JSON.stringify(res.data.env_vars || {}, null, 2));
  }, [botId]);

  useEffect(() => {
    loadBot();
    const interval = setInterval(loadBot, 8000);
    return () => clearInterval(interval);
  }, [loadBot]);

  useEffect(() => {
    if (tab === "logs") {
      apiClient.get(`/bots/${botId}/logs`).then((res) => setLogs(res.data.logs));
    } else if (tab === "files") {
      apiClient.get(`/bots/${botId}/files`, { params: { path: currentPath } }).then((res) => setFiles(res.data));
    } else if (tab === "stats" && bot?.status === "running") {
      apiClient.get(`/bots/${botId}/stats`).then((res) => setStats(res.data)).catch(() => setStats(null));
    }
  }, [tab, botId, currentPath, bot?.status]);

  const runAction = async (action: "start" | "stop" | "restart") => {
    await apiClient.post(`/bots/${botId}/${action}`);
    loadBot();
  };

  const handleDelete = async () => {
    if (!confirm(t.confirm_delete)) return;
    await apiClient.delete(`/bots/${botId}`);
    router.push("/dashboard/bots");
  };

  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    await apiClient.post(`/bots/${botId}/upload`, formData, { headers: { "Content-Type": "multipart/form-data" } });
    setTab("files");
    apiClient.get(`/bots/${botId}/files`, { params: { path: currentPath } }).then((res) => setFiles(res.data));
  };

  const saveEnv = async () => {
    try {
      const parsed = JSON.parse(envText);
      await apiClient.put(`/bots/${botId}/env`, { env_vars: parsed });
    } catch {
      alert("JSON غير صالح");
    }
  };

  const runConsoleCommand = async () => {
    if (!consoleInput.trim()) return;
    const res = await apiClient.post(`/bots/${botId}/console`, null, { params: { command: consoleInput } });
    setConsoleOutput((prev) => [...prev, `$ ${consoleInput}`, res.data.stdout || res.data.stderr]);
    setConsoleInput("");
  };

  if (!bot) return <div className="text-slate-500">...</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="font-display text-2xl font-bold text-slate-100">{bot.name}</h1>
            <StatusBadge status={bot.status} />
          </div>
          <p className="text-slate-500 text-xs font-mono">{bot.container_name || bot.slug}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => runAction("start")} disabled={bot.status === "running"}>
            <Play size={14} className="inline me-1" /> {t.start}
          </Button>
          <Button variant="secondary" onClick={() => runAction("stop")} disabled={bot.status !== "running"}>
            <Square size={14} className="inline me-1" /> {t.stop}
          </Button>
          <Button variant="secondary" onClick={() => runAction("restart")}>
            <RotateCw size={14} className="inline me-1" /> {t.restart}
          </Button>
          <Button variant="danger" onClick={handleDelete}>
            <Trash2 size={14} className="inline me-1" /> {t.delete}
          </Button>
        </div>
      </div>

      <div className="flex gap-1 border-b border-slate-800 mb-5">
        {(["logs", "files", "console", "environment", "stats"] as Tab[]).map((tabName) => (
          <button
            key={tabName}
            onClick={() => setTab(tabName)}
            className={`px-4 py-2.5 text-sm border-b-2 transition-colors ${
              tab === tabName ? "border-ember-500 text-ember-400" : "border-transparent text-slate-500 hover:text-slate-300"
            }`}
          >
            {t[tabName]}
          </button>
        ))}
      </div>

      {tab === "logs" && (
        <Card>
          <pre className="text-xs font-mono text-slate-300 whitespace-pre-wrap max-h-[500px] overflow-y-auto leading-relaxed">
            {logs || "لا توجد سجلات بعد"}
          </pre>
        </Card>
      )}

      {tab === "files" && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <p className="text-slate-500 text-xs font-mono">/{currentPath}</p>
            <input ref={fileInputRef} type="file" className="hidden" onChange={(e) => e.target.files && handleUpload(e.target.files[0])} />
            <Button variant="secondary" onClick={() => fileInputRef.current?.click()} className="flex items-center gap-2">
              <Upload size={14} /> {t.upload}
            </Button>
          </div>
          <div className="space-y-1">
            {currentPath && (
              <button onClick={() => setCurrentPath(currentPath.split("/").slice(0, -1).join("/"))} className="block text-slate-500 text-sm py-1.5 hover:text-slate-300">
                ..
              </button>
            )}
            {files.map((file) => (
              <button
                key={file.name}
                onClick={() => file.is_dir && setCurrentPath(currentPath ? `${currentPath}/${file.name}` : file.name)}
                className="flex items-center justify-between w-full text-start py-1.5 text-sm text-slate-300 hover:text-ember-400"
              >
                <span>{file.is_dir ? "📁" : "📄"} {file.name}</span>
                {!file.is_dir && <span className="text-slate-600 text-xs">{(file.size / 1024).toFixed(1)} KB</span>}
              </button>
            ))}
          </div>
        </Card>
      )}

      {tab === "console" && (
        <Card>
          <div className="bg-slate-950 rounded-lg p-4 h-80 overflow-y-auto font-mono text-xs text-slate-300 mb-3">
            {consoleOutput.map((line, i) => (
              <div key={i} className="whitespace-pre-wrap">{line}</div>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              value={consoleInput}
              onChange={(e) => setConsoleInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runConsoleCommand()}
              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono text-slate-200 focus:outline-none focus:border-ember-500"
              placeholder="ls / pwd / python --version"
            />
            <Button onClick={runConsoleCommand}>Run</Button>
          </div>
        </Card>
      )}

      {tab === "environment" && (
        <Card>
          <textarea
            value={envText}
            onChange={(e) => setEnvText(e.target.value)}
            className="w-full h-64 bg-slate-950 border border-slate-700 rounded-lg p-4 text-xs font-mono text-slate-300 focus:outline-none focus:border-ember-500"
          />
          <Button onClick={saveEnv} className="mt-3">{t.save}</Button>
        </Card>
      )}

      {tab === "stats" && (
        <div className="grid grid-cols-2 gap-4">
          {stats ? (
            <>
              <Card><p className="text-slate-500 text-xs mb-1">CPU</p><p className="text-2xl font-display font-bold text-slate-100">{stats.cpu_percent}%</p></Card>
              <Card><p className="text-slate-500 text-xs mb-1">Memory</p><p className="text-2xl font-display font-bold text-slate-100">{stats.memory_usage_mb} MB</p></Card>
              <Card><p className="text-slate-500 text-xs mb-1">Network RX</p><p className="text-2xl font-display font-bold text-slate-100">{(stats.network_rx_bytes / 1024).toFixed(1)} KB</p></Card>
              <Card><p className="text-slate-500 text-xs mb-1">Network TX</p><p className="text-2xl font-display font-bold text-slate-100">{(stats.network_tx_bytes / 1024).toFixed(1)} KB</p></Card>
            </>
          ) : (
            <p className="text-slate-500 text-sm col-span-2">شغّل البوت لعرض الإحصائيات المباشرة</p>
          )}
        </div>
      )}
    </div>
  );
}
