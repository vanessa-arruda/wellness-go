"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { apiFetch, ApiError } from "@/lib/api-client";

interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}

interface AuthContextValue {
  accessToken: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchWithAuth: <T>(path: string, options?: Parameters<typeof apiFetch>[2]) => Promise<T>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  // A ref mirrors the token for use inside callbacks that must always read
  // the latest value without needing to be recreated on every token change.
  const accessTokenRef = useRef<string | null>(null);
  useEffect(() => {
    accessTokenRef.current = accessToken;
  }, [accessToken]);

  const refresh = useCallback(async (): Promise<string | null> => {
    try {
      const data = await apiFetch<AccessTokenResponse>("/auth/refresh", null, { method: "POST" });
      setAccessToken(data.access_token);
      return data.access_token;
    } catch {
      setAccessToken(null);
      return null;
    }
  }, []);

  // On mount, try to restore a session from the httpOnly refresh cookie —
  // this is what keeps a user logged in across page reloads even though the
  // access token itself only ever lives in memory.
  useEffect(() => {
    let cancelled = false;
    async function initialize() {
      await refresh();
      if (!cancelled) {
        setIsLoading(false);
      }
    }
    initialize();
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    const data = await apiFetch<AccessTokenResponse>("/auth/login", null, {
      method: "POST",
      body: { email, password },
    });
    setAccessToken(data.access_token);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const data = await apiFetch<AccessTokenResponse>("/auth/register", null, {
      method: "POST",
      body: { email, password },
    });
    setAccessToken(data.access_token);
  }, []);

  const logout = useCallback(async () => {
    await apiFetch("/auth/logout", accessTokenRef.current, { method: "POST" }).catch(() => undefined);
    setAccessToken(null);
  }, []);

  const fetchWithAuth = useCallback(
    async <T,>(path: string, options?: Parameters<typeof apiFetch>[2]): Promise<T> => {
      try {
        return await apiFetch<T>(path, accessTokenRef.current, options);
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          const newToken = await refresh();
          if (newToken) {
            return apiFetch<T>(path, newToken, options);
          }
        }
        throw error;
      }
    },
    [refresh],
  );

  return (
    <AuthContext.Provider value={{ accessToken, isLoading, login, register, logout, fetchWithAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
