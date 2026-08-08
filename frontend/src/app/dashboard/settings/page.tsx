"use client";

import { useEffect, useState } from "react";
import { Card, Button, Input } from "@/components/ui";
import { useLocale } from "@/hooks/useLocale";
import { useAuth } from "@/hooks/useAuth";
import { apiClient } from "@/lib/api-client";

interface Session {
  id: string;
  ip_address: string;
  device_label: string;
  created_at: string;
  last_used_at: string;
}

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  created_at: string;
}

export default function SettingsPage() {
  const { t } = useLocale();
  const { user, refetch } = useAuth();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [totpSecret, setTotpSecret] = useState<{ secret: string; otpauth_uri: string } | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [newKeyName, setNewKeyName] = useState("");
  const [generatedKey, setGeneratedKey] = useState("");

  const loadSessions = () => apiClient.get("/users/me/sessions").then((res) => setSessions(res.data));
  const loadApiKeys = () => apiClient.get("/users/me/api-keys").then((res) => setApiKeys(res.data));

  useEffect(() => {
    loadSessions();
    loadApiKeys();
  }, []);

  const changePassword = async () => {
    await apiClient.put("/users/me/password", null, { params: { current_password: currentPassword, new_password: newPassword } });
    setCurrentPassword("");
    setNewPassword("");
  };

  const enable2FA = async () => {
    const res = await apiClient.post("/auth/2fa/enable");
    setTotpSecret(res.data);
  };

  const verify2FA = async () => {
    await apiClient.post("/auth/2fa/verify", { code: totpCode });
    setTotpSecret(null);
    setTotpCode("");
    refetch();
  };

  const disable2FA = async () => {
    await apiClient.post("/auth/2fa/disable");
    refetch();
  };

  const revokeSession = async (id: string) => {
    await apiClient.delete(`/users/me/sessions/${id}`);
    loadSessions();
  };

  const createApiKey = async () => {
    const res = await apiClient.post("/users/me/api-keys", null, { params: { name: newKeyName } });
    setGeneratedKey(res.data.api_key);
    setNewKeyName("");
    loadApiKeys();
  };

  const revokeApiKey = async (id: string) => {
    await apiClient.delete(`/users/me/api-keys/${id}`);
    loadApiKeys();
  };

  return (
    <div className="space-y-6">
      <h1 className="font-display text-2xl font-bold text-slate-100">{t.nav_settings}</h1>

      <Card>
        <h2 className="font-semibold text-slate-100 mb-4">الملف الشخصي</h2>
        <p className="text-slate-400 text-sm">البريد: {user?.email}</p>
        <p className="text-slate-400 text-sm">اسم المستخدم: {user?.username}</p>
      </Card>

      <Card>
        <h2 className="font-semibold text-slate-100 mb-4">تغيير كلمة المرور</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
          <Input type="password" placeholder="كلمة المرور الحالية" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
          <Input type="password" placeholder="كلمة المرور الجديدة" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
        </div>
        <Button onClick={changePassword}>{t.save}</Button>
      </Card>

      <Card>
        <h2 className="font-semibold text-slate-100 mb-4">المصادقة الثنائية (2FA)</h2>
        {user?.totp_enabled ? (
          <Button variant="danger" onClick={disable2FA}>تعطيل 2FA</Button>
        ) : totpSecret ? (
          <div className="space-y-3">
            <p className="text-slate-400 text-xs break-all">أضف هذا السر إلى تطبيق المصادقة: <code className="text-ember-400">{totpSecret.secret}</code></p>
            <Input placeholder="أدخل الرمز للتأكيد" value={totpCode} onChange={(e) => setTotpCode(e.target.value)} maxLength={6} />
            <Button onClick={verify2FA}>تأكيد وتفعيل</Button>
          </div>
        ) : (
          <Button onClick={enable2FA}>تفعيل 2FA</Button>
        )}
      </Card>

      <Card>
        <h2 className="font-semibold text-slate-100 mb-4">الجلسات النشطة</h2>
        <div className="space-y-2">
          {sessions.map((s) => (
            <div key={s.id} className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0">
              <div>
                <p className="text-slate-300 text-sm">{s.device_label}</p>
                <p className="text-slate-500 text-xs">{s.ip_address} — {new Date(s.last_used_at).toLocaleString("ar")}</p>
              </div>
              <Button variant="ghost" onClick={() => revokeSession(s.id)}>إنهاء</Button>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <h2 className="font-semibold text-slate-100 mb-4">مفاتيح API</h2>
        {generatedKey && (
          <div className="bg-slate-950 rounded-lg p-3 mb-4">
            <p className="text-signal-green text-xs mb-1">احفظ هذا المفتاح الآن — لن يظهر مرة أخرى:</p>
            <code className="text-xs text-ember-400 break-all">{generatedKey}</code>
          </div>
        )}
        <div className="flex gap-2 mb-4">
          <Input placeholder="اسم المفتاح" value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)} />
          <Button onClick={createApiKey}>إنشاء</Button>
        </div>
        <div className="space-y-2">
          {apiKeys.map((key) => (
            <div key={key.id} className="flex items-center justify-between py-2 border-b border-slate-800 last:border-0">
              <div>
                <p className="text-slate-300 text-sm">{key.name}</p>
                <p className="text-slate-500 text-xs font-mono">{key.key_prefix}...</p>
              </div>
              {key.is_active && <Button variant="ghost" onClick={() => revokeApiKey(key.id)}>إلغاء</Button>}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
