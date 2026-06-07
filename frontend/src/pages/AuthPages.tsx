import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, Card } from '../components/ui';
import { api } from '../lib/api';

function FieldInput({ label, type = 'text', value, onChange, placeholder, colSpan }: {
  label: string; type?: string; value: string;
  onChange: (v: string) => void; placeholder?: string; colSpan?: boolean;
}) {
  return (
    <label className={`block text-sm font-semibold${colSpan ? ' sm:col-span-2' : ''}`}>
      {label}
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 outline-none focus:border-brand"
      />
    </label>
  );
}

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { data } = await api.post('/auth/login', { email, password });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      navigate('/dashboard', { replace: true });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-cream px-4 py-12">
      <Card className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-brand text-xl font-black text-white">BP</div>
          <h1 className="mt-4 text-3xl font-extrabold">BakerProfit OS</h1>
          <p className="mt-2 text-sm text-baker-muted">Never undercharge for your bakes again.</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <FieldInput label="Email" type="email" value={email} onChange={setEmail} placeholder="owner@boldmunch.co.uk" />
          <FieldInput label="Password" type="password" value={password} onChange={setPassword} placeholder="••••••••" />
          {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-brand px-4 py-2.5 font-bold text-white hover:bg-brand-dark disabled:opacity-60"
          >
            {loading ? 'Signing in…' : 'Login'}
          </button>
        </form>
        <p className="mt-5 text-center text-sm text-baker-muted">
          New bakery?{' '}
          <Link className="font-bold text-brand" to="/register">Create an account</Link>
        </p>
      </Card>
    </div>
  );
}

export function RegisterPage() {
  const navigate = useNavigate();
  const [bakeryName, setBakeryName] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.post('/auth/register', {
        bakery_name: bakeryName,
        full_name: fullName,
        email,
        password,
      });
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      navigate('/dashboard', { replace: true });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail ?? 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-cream px-4 py-12">
      <Card className="w-full max-w-lg">
        <div className="mb-8 text-center">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-brand text-xl font-black text-white">BP</div>
          <h1 className="mt-4 text-3xl font-extrabold">Create BakerProfit OS</h1>
          <p className="mt-2 text-sm text-baker-muted">Set up your bakery workspace.</p>
        </div>
        <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
          <FieldInput colSpan label="Bakery Name" value={bakeryName} onChange={setBakeryName} />
          <FieldInput label="Full Name" value={fullName} onChange={setFullName} />
          <FieldInput colSpan label="Email" type="email" value={email} onChange={setEmail} />
          <FieldInput label="Password" type="password" value={password} onChange={setPassword} />
          <FieldInput label="Confirm Password" type="password" value={confirm} onChange={setConfirm} />
          {error && <p className="sm:col-span-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="sm:col-span-2">
            <Button>{loading ? 'Creating account…' : 'Create account'}</Button>
          </div>
        </form>
        <p className="mt-5 text-center text-sm text-baker-muted">
          Already registered?{' '}
          <Link className="font-bold text-brand" to="/login">Login</Link>
        </p>
      </Card>
    </div>
  );
}
