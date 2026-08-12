"use client";

// Admin session state: access token + user, held only in React state (never
// localStorage/sessionStorage) - see the top-of-file comment in lib/adminApi.ts
// for why a hard page reload deliberately requires logging in again rather
// than silently restoring a session.

import { createContext, ReactNode, useCallback, useContext, useMemo, useState } from "react";

import { adminLogin, adminLogout } from "@/lib/adminApi";
import { AdminPermission, AdminUser, ROLE_PERMISSIONS } from "@/lib/adminTypes";

interface AdminAuthContextValue {
  user: AdminUser | null;
  accessToken: string | null;
  status: "unauthenticated" | "authenticating" | "authenticated";
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (permission: AdminPermission) => boolean;
}

const AdminAuthContext = createContext<AdminAuthContextValue | null>(null);

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AdminUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  // csrfToken is intentionally never exposed outside this provider - it's
  // only ever needed internally, by a future silent-refresh call.
  const [, setCsrfToken] = useState<string | null>(null);
  const [status, setStatus] = useState<AdminAuthContextValue["status"]>("unauthenticated");
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (email: string, password: string) => {
    setStatus("authenticating");
    setError(null);
    try {
      const response = await adminLogin(email, password);
      setUser(response.user);
      setAccessToken(response.access_token);
      setCsrfToken(response.csrf_token);
      setStatus("authenticated");
    } catch (err) {
      setStatus("unauthenticated");
      setError(err instanceof Error ? err.message : "Login failed");
      throw err;
    }
  }, []);

  const logout = useCallback(async () => {
    await adminLogout();
    setUser(null);
    setAccessToken(null);
    setCsrfToken(null);
    setStatus("unauthenticated");
  }, []);

  const hasPermission = useCallback(
    (permission: AdminPermission) => {
      if (!user) return false;
      return ROLE_PERMISSIONS[user.role].includes(permission);
    },
    [user]
  );

  const value = useMemo(
    () => ({ user, accessToken, status, error, login, logout, hasPermission }),
    [user, accessToken, status, error, login, logout, hasPermission]
  );

  return <AdminAuthContext.Provider value={value}>{children}</AdminAuthContext.Provider>;
}

export function useAdminAuth(): AdminAuthContextValue {
  const context = useContext(AdminAuthContext);
  if (!context) throw new Error("useAdminAuth must be used within AdminAuthProvider");
  return context;
}
