import { useAuth } from '../context/AuthContext.jsx';

// Route guards: UI-level only. The API enforces 401/403 regardless.
export function RequireAuth({ children, fallback }) {
  const { user, ready } = useAuth();
  if (!ready) return <p>Loading…</p>;
  if (!user) return fallback;
  return children;
}

export function RequireAdmin({ children, fallback }) {
  const { user, ready } = useAuth();
  if (!ready) return <p>Loading…</p>;
  if (!user || user.role !== 'admin') return fallback;
  return children;
}
