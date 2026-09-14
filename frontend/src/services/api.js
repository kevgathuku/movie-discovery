// Minimal Bearer-token API client with single-flight refresh.
// One contract for web SPA and mobile (contracts/client-auth.md).
// No localStorage: callers own token storage (web: memory + sessionStorage).

export function createApiClient({
  baseUrl,
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearAuth,
  fetchFn = fetch,
}) {
  let refreshPromise = null;

  async function refreshOnce() {
    if (!refreshPromise) {
      const refreshToken = getRefreshToken();
      if (!refreshToken) return false;
      refreshPromise = (async () => {
        const res = await fetchFn(`${baseUrl}/api/v1/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (!res.ok) {
          clearAuth();
          return false;
        }
        const pair = await res.json();
        setTokens(pair.access_token, pair.refresh_token);
        return true;
      })().finally(() => {
        refreshPromise = null;
      });
    }
    return refreshPromise;
  }

  async function request(path, options = {}, retried = false) {
    const token = getAccessToken();
    const res = await fetchFn(`${baseUrl}${path}`, {
      ...options,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(options.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
    if (res.status === 401 && !retried && (await refreshOnce())) {
      return request(path, options, true);
    }
    return res;
  }

  return { request };
}
