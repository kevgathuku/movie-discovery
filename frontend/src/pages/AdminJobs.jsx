import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext.jsx';

export function AdminJobs() {
  const { api } = useAuth();
  const [state, setState] = useState({ loading: true, jobs: [], total: 0, error: '' });

  useEffect(() => {
    (async () => {
      try {
        const res = await api.request('/admin/jobs?per_page=50');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setState({ loading: false, jobs: data.jobs, total: data.total, error: '' });
      } catch (e) {
        setState({ loading: false, jobs: [], total: 0, error: String(e) });
      }
    })();
  }, [api]);

  if (state.loading) return <p>Loading jobs…</p>;
  if (state.error) return <p style={{ color: 'red' }}>Failed to load jobs: {state.error}</p>;
  if (state.jobs.length === 0) return <p>No background jobs yet.</p>;
  return (
    <div>
      <h2>Background jobs ({state.total})</h2>
      <table>
        <thead>
          <tr><th>ID</th><th>Type</th><th>Status</th><th>Progress</th><th>Error</th></tr>
        </thead>
        <tbody>
          {state.jobs.map((j) => (
            <tr key={j.id}>
              <td>{j.id}</td><td>{j.job_type}</td><td>{j.status}</td>
              <td>{j.progress ?? '—'}</td>
              <td>{j.error_info ? JSON.stringify(j.error_info) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
