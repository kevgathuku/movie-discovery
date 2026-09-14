import { describe, expect, it, vi } from 'vitest';
import { createApiClient } from '../src/services/api.js';

function mockFetch(responses) {
  const calls = [];
  const fn = vi.fn(async (url, options) => {
    calls.push({ url, options });
    const next = responses.shift();
    return {
      ok: next.status < 400,
      status: next.status,
      json: async () => next.body,
    };
  });
  return { fn, calls };
}

function tokens(access = 'A1', refresh = 'R1') {
  let state = { access, refresh };
  return {
    getAccessToken: () => state.access,
    getRefreshToken: () => state.refresh,
    setTokens: (a, r) => {
      state = { access: a, refresh: r };
    },
    clearAuth: () => {
      state = { access: null, refresh: null };
    },
    state: () => state,
  };
}

describe('api client', () => {
  it('attaches the Bearer token', async () => {
    const { fn, calls } = mockFetch([{ status: 200, body: {} }]);
    const t = tokens();
    const api = createApiClient({ baseUrl: '', ...t, fetchFn: fn });

    await api.request('/api/v1/auth/me');

    expect(calls[0].options.headers.Authorization).toBe('Bearer A1');
  });

  it('refreshes once on 401 and retries', async () => {
    const { fn, calls } = mockFetch([
      { status: 401, body: {} },
      { status: 200, body: { access_token: 'A2', refresh_token: 'R2' } },
      { status: 200, body: { ok: true } },
    ]);
    const t = tokens();
    const api = createApiClient({ baseUrl: '', ...t, fetchFn: fn });

    const res = await api.request('/api/v1/watchlists');

    expect(res.ok).toBe(true);
    expect(t.state()).toEqual({ access: 'A2', refresh: 'R2' });
    expect(calls.filter((c) => c.url.endsWith('/auth/refresh'))).toHaveLength(1);
  });

  it('clears auth when refresh fails', async () => {
    const { fn } = mockFetch([
      { status: 401, body: {} },
      { status: 401, body: {} },
    ]);
    const t = tokens();
    const api = createApiClient({
      baseUrl: '',
      ...t,
      clearAuth: () => {
        t.clearAuth();
        cleared = true;
      },
      fetchFn: fn,
    });
    let cleared = false;

    const res = await api.request('/api/v1/watchlists');

    expect(res.ok).toBe(false);
    expect(cleared).toBe(true);
  });

  it('does not retry twice', async () => {
    const { fn, calls } = mockFetch([
      { status: 401, body: {} },
      { status: 200, body: { access_token: 'A2', refresh_token: 'R2' } },
      { status: 401, body: {} },
    ]);
    const t = tokens();
    const api = createApiClient({ baseUrl: '', ...t, fetchFn: fn });

    const res = await api.request('/api/v1/watchlists');

    expect(res.ok).toBe(false);
    expect(calls).toHaveLength(3);
  });
});
