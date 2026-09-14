// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '../src/context/AuthContext.jsx';
import { AppRoutes } from '../src/App.jsx';

const REFRESH_KEY = 'movie-explorer.refresh-token';

function jsonResponse(status, body) {
  return { ok: status < 400, status, json: async () => body };
}

// routes: { 'POST /api/v1/auth/login': (url, opts) => body | { status, body } }
function setupFetch(routes) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url, opts = {}) => {
      const method = (opts.method || 'GET').toUpperCase();
      const path = new URL(url, 'http://test').pathname;
      const handler = routes[`${method} ${path}`];
      if (!handler) return jsonResponse(404, {});
      const out = await handler(url, opts);
      if (out && typeof out.status === 'number') {
        return jsonResponse(out.status, out.body);
      }
      return jsonResponse(200, out);
    }),
  );
}

function renderAt(path) {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
      </MemoryRouter>
    </AuthProvider>,
  );
}

async function loginAs(email = 'ana@example.com', role = 'user') {
  fireEvent.change(screen.getByPlaceholderText('Email'), {
    target: { value: email },
  });
  fireEvent.change(screen.getByPlaceholderText('Password (8+ chars)'), {
    target: { value: 's3cure-pass' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Log in' }));
  await screen.findByText(email);
}

function authRoutes(role = 'user', email = 'ana@example.com') {
  return {
    'POST /api/v1/auth/login': () => ({
      access_token: 'A1',
      refresh_token: 'R1',
    }),
    'GET /api/v1/auth/me': () => ({ email, role }),
  };
}

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
});

const originalFetch = globalThis.fetch;

afterEach(() => {
  cleanup();
  globalThis.fetch = originalFetch;
  sessionStorage.clear();
});

describe('routes', () => {
  it('redirects logged-out / to /login', async () => {
    setupFetch({});
    renderAt('/');

    await screen.findByPlaceholderText('Email');
    expect(screen.queryByText(/Trending movies/)).toBeNull();
  });

  it('redirects logged-out /admin to /login', async () => {
    setupFetch({});
    renderAt('/admin');

    await screen.findByPlaceholderText('Email');
  });

  it('logs in and lands on home without touching localStorage', async () => {
    setupFetch(authRoutes());
    renderAt('/login');

    await loginAs();

    expect(screen.getByText(/Trending movies/)).not.toBeNull();
    expect(localStorage.length).toBe(0);
  });

  it('stays logged in across reloads via silent refresh', async () => {
    sessionStorage.setItem(REFRESH_KEY, 'R0');
    setupFetch({
      'POST /api/v1/auth/refresh': () => ({
        access_token: 'A1',
        refresh_token: 'R1',
      }),
      'GET /api/v1/auth/me': () => ({ email: 'ana@example.com', role: 'user' }),
    });
    renderAt('/');

    await screen.findByText('ana@example.com');
    expect(screen.queryByPlaceholderText('Email')).toBeNull();
  });

  it('blocks non-admins from /admin (route guard)', async () => {
    sessionStorage.setItem(REFRESH_KEY, 'R0');
    setupFetch({
      'POST /api/v1/auth/refresh': () => ({
        access_token: 'A1',
        refresh_token: 'R1',
      }),
      'GET /api/v1/auth/me': () => ({ email: 'ana@example.com', role: 'user' }),
    });
    renderAt('/admin');

    await screen.findByText('Not authorized.');
  });

  it('shows job history to admins at /admin', async () => {
    sessionStorage.setItem(REFRESH_KEY, 'R0');
    setupFetch({
      'POST /api/v1/auth/refresh': () => ({
        access_token: 'A1',
        refresh_token: 'R1',
      }),
      'GET /api/v1/auth/me': () => ({
        email: 'admin@example.com',
        role: 'admin',
      }),
      'GET /admin/jobs': () => ({
        jobs: [
          {
            id: 'x1',
            job_type: 'sync_trending',
            status: 'completed',
            progress: 100,
            error_info: null,
          },
        ],
        total: 1,
      }),
    });
    renderAt('/admin');

    await screen.findByText('Background jobs (1)');
  });
});
