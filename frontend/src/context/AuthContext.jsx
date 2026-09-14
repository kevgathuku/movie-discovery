import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { createApiClient } from '../services/api.js';

// Access token in memory (never localStorage). Refresh token in
// sessionStorage: tab-scoped and cleared on close — not localStorage per
// FR-015, good enough until the cookie variant lands (research R4).
const REFRESH_KEY = 'movie-explorer.refresh-token';
const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(null);
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  const getTokens = useCallback(
    () => ({
      access: accessToken,
      refresh: sessionStorage.getItem(REFRESH_KEY),
    }),
    [accessToken],
  );

  const setTokens = useCallback((access, refresh) => {
    setAccessToken(access);
    if (refresh) sessionStorage.setItem(REFRESH_KEY, refresh);
  }, []);

  const clearAuth = useCallback(() => {
    setAccessToken(null);
    setUser(null);
    sessionStorage.removeItem(REFRESH_KEY);
  }, []);

  const api = useMemo(
    () =>
      createApiClient({
        baseUrl: API_BASE,
        getAccessToken: () => getTokens().access,
        getRefreshToken: () => getTokens().refresh,
        setTokens,
        clearAuth,
        fetchFn: fetch,
      }),
    [getTokens, setTokens, clearAuth],
  );

  const loadMe = useCallback(
    async (token) => {
      const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return null;
      return res.json();
    },
    [],
  );

  // Silent refresh on load: stay logged in across reloads.
  useEffect(() => {
    (async () => {
      const refresh = sessionStorage.getItem(REFRESH_KEY);
      if (refresh) {
        const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refresh }),
        });
        if (res.ok) {
          const pair = await res.json();
          setTokens(pair.access_token, pair.refresh_token);
          setUser(await loadMe(pair.access_token));
        } else {
          clearAuth();
        }
      }
      setReady(true);
    })();
  }, [setTokens, clearAuth, loadMe]);

  const login = useCallback(
    async (email, password) => {
      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) return false;
      const pair = await res.json();
      setTokens(pair.access_token, pair.refresh_token);
      setUser(await loadMe(pair.access_token));
      return true;
    },
    [setTokens, loadMe],
  );

  const register = useCallback(async (email, password) => {
    const res = await fetch(`${API_BASE}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return res.ok;
  }, []);

  const logout = useCallback(async () => {
    const refresh = sessionStorage.getItem(REFRESH_KEY);
    if (refresh) {
      await api.request('/api/v1/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refresh }),
      }).catch(() => {});
    }
    clearAuth();
  }, [api, clearAuth]);

  const value = useMemo(
    () => ({ user, ready, api, login, register, logout }),
    [user, ready, api, login, register, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
