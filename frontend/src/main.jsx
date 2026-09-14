import { useState } from 'react';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { RequireAdmin, RequireAuth } from './components/RequireAuth.jsx';
import { AuthProvider, useAuth } from './context/AuthContext.jsx';
import { AdminJobs } from './pages/AdminJobs.jsx';
import { Login } from './pages/Login.jsx';

function Shell() {
  const { user, logout } = useAuth();
  const [view, setView] = useState('home');

  return (
    <RequireAuth fallback={<Login onDone={() => setView('home')} />}>
      <div style={{ fontFamily: 'sans-serif', maxWidth: 720, margin: '20px auto' }}>
        <header style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <h1>Movie Explorer</h1>
          <span>{user?.email}</span>
          <button onClick={() => setView('home')}>Home</button>
          {user?.role === 'admin' && (
            <button onClick={() => setView('admin')}>Admin jobs</button>
          )}
          <button onClick={logout}>Log out</button>
        </header>
        {view === 'admin' ? (
          <RequireAdmin fallback={<p>Not authorized.</p>}>
            <AdminJobs />
          </RequireAdmin>
        ) : (
          <p>Trending movies live here (US1 frontend slice builds on this shell).</p>
        )}
      </div>
    </RequireAuth>
  );
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <Shell />
    </AuthProvider>
  </StrictMode>,
);
