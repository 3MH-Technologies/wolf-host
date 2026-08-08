"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiClient, setTokens, clearTokens } from "@/lib/api-client";
import type { UserProfile } from "@/types";

export function useAuth() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchProfile = useCallback(async () => {
    try {
      const response = await apiClient.get("/users/me");
      setUser(response.data);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("wolfhost_access_token") : null;
    if (token) {
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, [fetchProfile]);

  const login = async (email: string, password: string, totpCode?: string) => {
    const response = await apiClient.post("/auth/login", { email, password, totp_code: totpCode || null });
    setTokens(response.data.access_token, response.data.refresh_token);
    await fetchProfile();
    router.push("/dashboard");
  };

  const register = async (email: string, username: string, password: string) => {
    const response = await apiClient.post("/auth/register", { email, username, password });
    setTokens(response.data.access_token, response.data.refresh_token);
    await fetchProfile();
    router.push("/dashboard");
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem("wolfhost_refresh_token");
    try {
      if (refreshToken) await apiClient.post("/auth/logout", { refresh_token: refreshToken });
    } finally {
      clearTokens();
      setUser(null);
      router.push("/login");
    }
  };

  return { user, loading, login, register, logout, refetch: fetchProfile };
}
