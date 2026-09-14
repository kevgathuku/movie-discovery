import { BrowserRouter, Link, Navigate, Outlet, Route, Routes, useNavigate } from 'react-router-dom';
import { RequireAdmin } from './components/RequireAuth.jsx';
import { AuthProvider, useAuth } from './context/AuthContext.jsx';
import { AdminJobs } from './pages/AdminJobs.jsx';
import { Login } from './pages/Login.jsx';

function Protected({ children }) {
  const { user, ready } = useAuth();
  if (!ready) return <p>Loading…</p>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function LoginRoute() {
  const { user, ready } = useAuth();
  const navigate = useNavigate();
  if (!ready) return <p>Loading…</p>;
  if (user) return <Navigate to="/" replace />;
  return <Login onDone={() => navigate('/')} />;
}

function Shell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 720, margin: '20px auto' }}>
      <header style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <h1>Movie Explorer</h1>
        <span>{user?.email}</span>
        <Link to="/">Home</Link>
        {user?.role === 'admin' && <Link to="/admin">Admin jobs</Link>}
        <button
          onClick={async () => {
            await logout();
            navigate('/login');
          }}
        >
          Log out
        </button>
      </header>
      <Outlet />
    </div>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />
      {/* Legacy alias: the API lives at /admin/jobs, the SPA page at /admin. */}
      <Route path="/admin/jobs" element={<Navigate to="/admin" replace />} />
      <Route
        path="/"
        element={
          <Protected>
            <Shell />
          </Protected>
        }
      >
        <Route
          index
          element={
            <p>Trending movies live here (US1 frontend slice builds on this shell).</p>
          }
        />
        <Route
          path="admin"
          element={
            <RequireAdmin fallback={<p>Not authorized.</p>}>
              <AdminJobs />
            </RequireAdmin>
          }
        />
        <Route path="*" element={<p>Not found.</p>} />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
