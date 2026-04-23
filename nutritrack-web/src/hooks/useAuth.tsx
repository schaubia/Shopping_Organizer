"use client";
import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { authApi } from "@/lib/api";
import { User } from "@/types";

interface AuthCtx {
  user:    User | null;
  loading: boolean;
  login:   (email: string, password: string) => Promise<void>;
  logout:  () => void;
}

const AuthContext = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user,    setUser]    = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("nutritrack_token");
    if (!token) { setLoading(false); return; }
    authApi.me()
      .then((r) => setUser(r.data))
      .catch(() => localStorage.removeItem("nutritrack_token"))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await authApi.login(email, password);
    localStorage.setItem("nutritrack_token", data.access_token);
    const me = await authApi.me();
    setUser(me.data);
  };

  const logout = () => {
    localStorage.removeItem("nutritrack_token");
    setUser(null);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
};
