import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiRequest, clearApiKey, getApiKey, setApiKey, ApiError } from "../api/client";
import type { Role } from "../api/types";

interface AuthState {
  apiKey: string | null;
  role: Role | null;
  loading: boolean;
  error: string | null;
  login: (key: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [apiKey, setKey] = useState<string | null>(getApiKey());
  const [role, setRole] = useState<Role | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // On mount, if a key is already stored (e.g. page refresh), re-verify it
  // silently so `role` is populated without forcing a fresh login.
  useEffect(() => {
    const existing = getApiKey();
    if (existing && !role) {
      apiRequest<{ role: Role }>("/admin/whoami")
        .then((res) => setRole(res.role))
        .catch(() => {
          clearApiKey();
          setKey(null);
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function login(key: string) {
    setLoading(true);
    setError(null);
    setApiKey(key);
    try {
      const res = await apiRequest<{ role: Role }>("/admin/whoami");
      setKey(key);
      setRole(res.role);
    } catch (e) {
      clearApiKey();
      setKey(null);
      setRole(null);
      if (e instanceof ApiError) {
        setError(e.status === 401 ? "That API key was not recognized." : e.messages.join(" "));
      } else {
        setError("Could not reach the API. Is the backend running?");
      }
      throw e;
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    clearApiKey();
    setKey(null);
    setRole(null);
  }

  return (
    <AuthContext.Provider value={{ apiKey, role, loading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}