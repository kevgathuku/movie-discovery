import { useState } from 'react';
import { useAuth } from '../context/AuthContext.jsx';

export function Login({ onDone }) {
  const { login, register } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState('login');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      if (mode === 'register') {
        const ok = await register(email, password);
        if (!ok) {
          setError('Registration failed (email taken or invalid input).');
          return;
        }
      }
      const ok = await login(email, password);
      if (!ok) setError('Invalid email or password.');
      else onDone();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: 320, margin: '50px auto' }}>
      <h1>Movie Explorer</h1>
      <form onSubmit={submit}>
        <input
          type="email" required placeholder="Email" value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ display: 'block', width: '100%', marginBottom: 8 }}
        />
        <input
          type="password" required minLength={8} placeholder="Password (8+ chars)"
          value={password} onChange={(e) => setPassword(e.target.value)}
          style={{ display: 'block', width: '100%', marginBottom: 8 }}
        />
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? '…' : mode === 'login' ? 'Log in' : 'Register & log in'}
        </button>
      </form>
      <button onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
        {mode === 'login' ? 'Need an account? Register' : 'Have an account? Log in'}
      </button>
    </div>
  );
}
