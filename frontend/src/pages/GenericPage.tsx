import { useEffect, useMemo, useState } from 'react';
import { Code2, Filter, Loader2, PanelRightOpen, Plus, Search, X } from 'lucide-react';
import { Badge, Button, Card, PageHeader } from '../components/ui';
import type { FormField, PageConfig } from '../data/mock';
import { api } from '../lib/api';

function toneFor(value: string) {
  const t = value.toLowerCase();
  if (['accepted', 'paid', 'completed', 'excellent', 'profitable', 'reviewed', 'imported', 'active', 'purchased', 'yes'].some((w) => t.includes(w))) return 'success' as const;
  if (['warning', 'draft', 'planned', 'low', 'needs', 'in_progress', 'in production'].some((w) => t.includes(w))) return 'warning' as const;
  if (['critical', 'loss', 'failed', 'cancelled', 'rejected', 'unknown'].some((w) => t.includes(w))) return 'danger' as const;
  if (['converted', 'purple'].some((w) => t.includes(w))) return 'purple' as const;
  if (['info', 'sent', 'confirmed'].some((w) => t.includes(w))) return 'info' as const;
  return 'neutral' as const;
}

function CreateModal({
  config,
  onClose,
  onCreated,
}: {
  config: PageConfig;
  onClose: () => void;
  onCreated: () => void;
}) {
  const [form, setForm] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  if (config.createNote) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
        <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-bold">Create {config.title.replace(/s$/, '')}</h2>
            <button onClick={onClose}><X className="h-5 w-5 text-baker-muted" /></button>
          </div>
          <p className="text-sm text-baker-muted">{config.createNote}</p>
          <Button variant="secondary" className="mt-4 w-full" onClick={onClose}>Close</Button>
        </div>
      </div>
    );
  }

  if (!config.createEndpoint || !config.createFields) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      const payload: Record<string, unknown> = {};
      for (const field of config.createFields!) {
        const raw = form[field.key];
        if (raw === undefined || raw === '') continue;
        payload[field.key] = field.type === 'number' ? parseFloat(raw) : raw;
      }
      await api.post(config.createEndpoint!, payload);
      onCreated();
      onClose();
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Save failed. Check required fields.');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-bold">{config.primaryAction}</h2>
          <button onClick={onClose}><X className="h-5 w-5 text-baker-muted" /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {config.createFields.map((field: FormField) => (
            <label key={field.key} className="block text-sm font-semibold">
              {field.label}{field.required ? ' *' : ''}
              {field.type === 'select' ? (
                <select
                  value={form[field.key] ?? ''}
                  onChange={(e) => setForm({ ...form, [field.key]: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
                >
                  <option value="">Select…</option>
                  {field.options?.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
                </select>
              ) : field.type === 'textarea' ? (
                <textarea
                  rows={3}
                  value={form[field.key] ?? ''}
                  onChange={(e) => setForm({ ...form, [field.key]: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
                />
              ) : (
                <input
                  type={field.type === 'number' ? 'number' : 'text'}
                  step={field.type === 'number' ? 'any' : undefined}
                  required={field.required}
                  value={form[field.key] ?? ''}
                  onChange={(e) => setForm({ ...form, [field.key]: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-baker-border px-3 py-2 text-sm outline-none focus:border-brand"
                />
              )}
            </label>
          ))}
          {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={saving} className="flex-1">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save'}
            </Button>
            <Button type="button" variant="secondary" onClick={onClose}>Cancel</Button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function GenericPage({ config }: { config: PageConfig }) {
  const [search, setSearch] = useState('');
  const [liveRows, setLiveRows] = useState<Array<Record<string, string>>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreate, setShowCreate] = useState(false);

  async function loadData() {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get<unknown>(config.listEndpoint);
      const items = Array.isArray(data) ? data : [];
      setLiveRows(items.map((item) => config.rowMapper(item as Record<string, unknown>)));
    } catch {
      setError('Failed to load data. Please refresh.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [config.listEndpoint]);

  const rows = useMemo(() => {
    if (!search.trim()) return liveRows;
    return liveRows.filter((row) =>
      Object.values(row).join(' ').toLowerCase().includes(search.toLowerCase()),
    );
  }, [liveRows, search]);

  const displayColumns = config.columns;

  return (
    <div>
      <PageHeader
        eyebrow={config.eyebrow}
        title={config.title}
        description={config.description}
        action={
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="mr-2 h-4 w-4" />{config.primaryAction}
          </Button>
        }
      />

      <div className="mb-4 grid gap-4 xl:grid-cols-[1fr_300px]">
        <Card>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="flex min-w-0 flex-1 items-center gap-2 rounded-xl border border-baker-border bg-warm-bg px-3 py-2">
              <Search className="h-4 w-4 text-baker-muted" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-transparent text-sm outline-none"
                placeholder={`Search ${config.title.toLowerCase()}…`}
              />
            </div>
            <div className="flex gap-2">
              <Button variant="secondary"><Filter className="mr-2 h-4 w-4" />Filters</Button>
              <Button variant="secondary"><PanelRightOpen className="mr-2 h-4 w-4" />Columns</Button>
            </div>
          </div>

          {config.tabs?.length ? (
            <div className="mt-4 flex flex-wrap gap-2 border-b border-baker-border pb-3">
              {config.tabs.map((tab, i) => (
                <button
                  key={tab}
                  className={i === 0 ? 'rounded-full bg-brand px-3 py-1.5 text-sm font-bold text-white' : 'rounded-full bg-cream px-3 py-1.5 text-sm font-bold text-baker-muted'}
                >
                  {tab}
                </button>
              ))}
            </div>
          ) : null}

          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="h-6 w-6 animate-spin text-brand" />
            </div>
          ) : error ? (
            <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-6 text-center">
              <p className="font-bold text-red-700">{error}</p>
              <button onClick={loadData} className="mt-2 text-sm font-semibold text-brand hover:underline">Retry</button>
            </div>
          ) : (
            <>
              <div className="mt-4 hidden overflow-x-auto lg:block">
                <table className="w-full border-separate border-spacing-0 text-left text-sm">
                  <thead>
                    <tr>
                      {displayColumns.map((col) => (
                        <th key={col} className="border-b border-baker-border bg-cream/80 px-3 py-3 text-xs font-bold uppercase tracking-wide text-baker-muted first:rounded-l-xl">
                          {col}
                        </th>
                      ))}
                      <th className="border-b border-baker-border bg-cream/80 px-3 py-3 text-right text-xs font-bold uppercase tracking-wide text-baker-muted last:rounded-r-xl">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, i) => (
                      <tr key={row._id ?? i} className="group">
                        {displayColumns.map((col) => {
                          const value = String(row[col] ?? '—');
                          const isStatus = ['Status', 'Severity', 'Margin Status', 'Read'].includes(col);
                          return (
                            <td key={col} className="border-b border-baker-border px-3 py-4 align-middle group-hover:bg-warm-bg">
                              {isStatus ? (
                                <Badge tone={toneFor(value)}>{value.replace(/_/g, ' ')}</Badge>
                              ) : (
                                <span className={col.includes('Cost') || col.includes('Price') || col.includes('Profit') || col.includes('Total') || col.includes('Paid') || col.includes('Balance') ? 'font-mono text-xs' : ''}>
                                  {value}
                                </span>
                              )}
                            </td>
                          );
                        })}
                        <td className="border-b border-baker-border px-3 py-4 text-right group-hover:bg-warm-bg">
                          {config.deleteEndpoint && row._id ? (
                            <button
                              onClick={async () => {
                                if (!confirm('Delete this record?')) return;
                                try {
                                  await api.delete(config.deleteEndpoint!(row._id));
                                  setLiveRows((prev) => prev.filter((r) => r._id !== row._id));
                                } catch {
                                  alert('Delete failed.');
                                }
                              }}
                              className="text-sm font-semibold text-red-500 hover:text-red-700"
                            >
                              Delete
                            </button>
                          ) : (
                            <span className="text-sm font-semibold text-baker-muted">View</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 grid gap-3 lg:hidden">
                {rows.map((row, i) => (
                  <div key={row._id ?? i} className="rounded-xl border border-baker-border bg-warm-bg p-4">
                    {displayColumns.slice(0, 4).map((col) => (
                      <div key={col} className="flex justify-between gap-4 border-b border-baker-border/70 py-2 last:border-0">
                        <span className="text-xs font-bold uppercase text-baker-muted">{col}</span>
                        <span className="text-right text-sm font-medium">{String(row[col] ?? '—')}</span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>

              {!rows.length ? (
                <div className="mt-6 rounded-2xl border border-dashed border-baker-border bg-cream/60 p-8 text-center">
                  <p className="font-bold">{config.emptyState}</p>
                  <p className="mt-2 text-sm text-baker-muted">
                    {search ? 'Try clearing the search filter.' : `Click "${config.primaryAction}" to add the first record.`}
                  </p>
                </div>
              ) : null}
            </>
          )}
        </Card>

        <aside className="space-y-4">
          <Card>
            <div className="mb-3 flex items-center gap-2">
              <Code2 className="h-5 w-5 text-brand" />
              <h3 className="font-bold text-sm">Live endpoints</h3>
            </div>
            <div className="space-y-2">
              {config.api.map((endpoint) => (
                <code key={endpoint} className="block rounded-lg bg-baker-text px-3 py-2 text-xs text-white">{endpoint}</code>
              ))}
            </div>
          </Card>

          <Card>
            <h3 className="font-bold text-sm">{liveRows.length} record{liveRows.length !== 1 ? 's' : ''} loaded</h3>
            {liveRows.length > 0 && (
              <p className="mt-1 text-xs text-baker-muted">Fetched live from your backend.</p>
            )}
            <button onClick={() => setShowCreate(true)} className="mt-3 flex w-full items-center gap-2 rounded-lg bg-brand px-3 py-2 text-sm font-bold text-white hover:bg-brand-dark">
              <Plus className="h-4 w-4" />{config.primaryAction}
            </button>
          </Card>
        </aside>
      </div>

      {showCreate && (
        <CreateModal config={config} onClose={() => setShowCreate(false)} onCreated={loadData} />
      )}
    </div>
  );
}
