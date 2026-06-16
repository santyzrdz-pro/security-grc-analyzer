"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, clearToken, getToken } from "@/lib/api";
import type { CurrentUser } from "@/lib/types";

interface AuthContextValue {
  user: CurrentUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  can: (permission: string) => boolean;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.get<CurrentUser>("/auth/me");
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const login = useCallback(
    async (email: string, password: string) => {
      await api.login(email, password);
      await refresh();
      router.push("/dashboard");
    },
    [refresh, router]
  );

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    router.push("/login");
  }, [router]);

  const can = useCallback(
    (permission: string) =>
      !!user && (user.permissions.includes("*") || user.permissions.includes(permission)),
    [user]
  );

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, can, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
