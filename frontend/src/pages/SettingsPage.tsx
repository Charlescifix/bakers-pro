import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Card, PageHeader, Button } from '../components/ui';
import { api } from '../lib/api';
import { extractApiError } from '../lib/api-errors';

type Me = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string;
  tenant_name?: string;
};

export default function SettingsPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [fullName, setFullName] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get<Me>('/auth/me')
      .then((r) => {
        setMe(r.data);
        setFullName(r.data.full_name ?? '');
      })
      .catch(() => setError('Failed to load profile.'))
      .finally(() => setLoading(false));
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!me) return;
    setError('');
    setSaved(false);
    setSaving(true);
    try {
      await api.patch('/auth/me', { full_name: fullName.trim() });
      setMe((prev) => prev ? { ...prev, full_name: fullName.trim() } : prev);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err: unknown) {
      setError(extractApiError(err));
    } finally {
      setSaving(false);
    }
  }

  function handleLogout() {
    localStorage.clear();
    window.location.href = '/login';
  }

  return (
    <div>
      <PageHeader
        eyebrow="Account"
        title="Settings"
        description="Manage your profile and bakery details."
      />

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-6 w-6 animate-spin text-brand" />
        </div>
      ) : (
        <div className="grid gap-4 xl:grid-cols-[1fr_300px]">
          <div className="space-y-4">
            <Card>
              <h3 className="mb-4 font-bold">Profile</h3>
              <form onSubmit={handleSave} className="space-y-4">
                <label className="block text-sm font-semibold">
                  Full Name
                  <input
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
                  />
                </label>

                <label className="block text-sm font-semibold">
                  Email
                  <input
                    value={me?.email ?? ''}
                    disabled
                    className="mt-1 w-full rounded-lg border border-baker-border bg-cream/60 px-3 py-2 text-sm text-baker-muted outline-none"
                  />
                </label>

                <label className="block text-sm font-semibold">
                  Role
                  <input
                    value={me?.role ?? ''}
                    disabled
                    className="mt-1 w-full rounded-lg border border-baker-border bg-cream/60 px-3 py-2 text-sm capitalize text-baker-muted outline-none"
                  />
                </label>

                {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
                {saved && <p className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700">Profile saved.</p>}

                <Button type="submit" disabled={saving}>
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save Changes'}
                </Button>
              </form>
            </Card>

            <Card>
              <h3 className="mb-4 font-bold">Bakery</h3>
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="font-semibold text-baker-muted">Bakery Name</span>
                  <span className="font-medium">{me?.tenant_name ?? '—'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="font-semibold text-baker-muted">Tenant ID</span>
                  <span className="font-mono text-xs text-baker-muted">{me?.tenant_id ?? '—'}</span>
                </div>
              </div>
            </Card>
          </div>

          <aside>
            <Card>
              <h3 className="mb-3 font-bold text-sm">Account</h3>
              <button
                onClick={handleLogout}
                className="w-full rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-700 hover:bg-red-100"
              >
                Log Out
              </button>
            </Card>
          </aside>
        </div>
      )}
    </div>
  );
}
