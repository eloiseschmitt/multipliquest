import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchCurrentUser, login as loginRequest, logout as logoutRequest } from "./api";
import { AuthContext } from "./context";
import type { AuthUser } from "./types";

export interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  clearExpiredSession: () => void;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const clearExpiredSession = useCallback(() => {
    setUser(null);
  }, []);

  useEffect(() => {
    let active = true;

    fetchCurrentUser()
      .then((currentUser) => {
        if (active) {
          setUser(currentUser);
        }
      })
      .catch(() => {
        if (active) {
          setUser(null);
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const loggedInUser = await loginRequest(username, password);
    setUser(loggedInUser);
  }, []);

  const logout = useCallback(async () => {
    await logoutRequest();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, isLoading, login, logout, clearExpiredSession }),
    [clearExpiredSession, isLoading, login, logout, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
