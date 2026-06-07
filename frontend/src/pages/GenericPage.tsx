import { useMemo, useState } from 'react';
import { Code2, Filter, PanelRightOpen, Plus, Search } from 'lucide-react';
import { Badge, Button, Card, PageHeader } from '../components/ui';
import type { PageConfig } from '../data/mock';

function toneFor(value: string) {
  const text = value.toLowerCase();
  if (['accepted', 'paid', 'completed', 'excellent', 'profitable', 'reviewed', 'imported', 'active', 'purchased'].some((word) => text.includes(word))) return 'success' as const;
  if (['warning', 'draft', 'planned', 'low', 'needs', 'in_progress', 'in production'].some((word) => text.includes(word))) return 'warning' as const;
  if (['critical', 'loss', 'failed', 'cancelled', 'rejected', 'unknown'].some((word) => text.includes(word))) return 'danger' as const;
  if (['converted', 'purple'].some((word) => text.includes(word))) return 'purple' as const;
  if (['info', 'sent', 'confirmed'].some((word) => text.includes(word))) return 'info' as const;
  return 'neutral' as const;
}

export default function GenericPage({ config }: { config: PageConfig }) {
  const [search, setSearch] = useState('');
  const rows = useMemo(() => {
    if (!search.trim()) return config.rows;
    return config.rows.filter((row) => Object.values(row).join(' ').toLowerCase().includes(search.toLowerCase()));
  }, [config.rows, search]);

  return (
    <div>
      <PageHeader eyebrow={config.eyebrow} title={config.title} description={config.description} action={<Button><Plus className="mr-2 h-4 w-4" />{config.primaryAction}</Button>} />

      <div className="mb-4 grid gap-4 xl:grid-cols-[1fr_340px]">
        <Card>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="flex min-w-0 flex-1 items-center gap-2 rounded-xl border border-baker-border bg-warm-bg px-3 py-2">
              <Search className="h-4 w-4 text-baker-muted" />
              <input value={search} onChange={(event) => setSearch(event.target.value)} className="w-full bg-transparent text-sm outline-none" placeholder={`Search ${config.title.toLowerCase()}...`} />
            </div>
            <div className="flex gap-2">
              <Button variant="secondary"><Filter className="mr-2 h-4 w-4" />Filters</Button>
              <Button variant="secondary"><PanelRightOpen className="mr-2 h-4 w-4" />Columns</Button>
            </div>
          </div>

          {config.tabs?.length ? (
            <div className="mt-4 flex flex-wrap gap-2 border-b border-baker-border pb-3">
              {config.tabs.map((tab, index) => (
                <button key={tab} className={index === 0 ? 'rounded-full bg-brand px-3 py-1.5 text-sm font-bold text-white' : 'rounded-full bg-cream px-3 py-1.5 text-sm font-bold text-baker-muted'}>
                  {tab}
                </button>
              ))}
            </div>
          ) : null}

          <div className="mt-4 hidden overflow-x-auto lg:block">
            <table className="w-full min-w-[760px] border-separate border-spacing-0 text-left text-sm">
              <thead>
                <tr>
                  {config.columns.map((column) => (
                    <th key={column} className="border-b border-baker-border bg-cream/80 px-3 py-3 text-xs font-bold uppercase tracking-wide text-baker-muted first:rounded-l-xl last:rounded-r-xl">
                      {column}
                    </th>
                  ))}
                  <th className="border-b border-baker-border bg-cream/80 px-3 py-3 text-right text-xs font-bold uppercase tracking-wide text-baker-muted">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={index} className="group">
                    {config.columns.map((column) => {
                      const value = String(row[column] ?? '—');
                      const looksLikeStatus = ['Status', 'Severity', 'Margin Status', 'Payment Status'].includes(column) || ['Status'].includes(column);
                      return (
                        <td key={column} className="border-b border-baker-border px-3 py-4 align-middle group-hover:bg-warm-bg">
                          {looksLikeStatus ? <Badge tone={toneFor(value)}>{value.replace('_', ' ')}</Badge> : <span className={column.includes('Cost') || column.includes('Price') || column.includes('Profit') || column.includes('Total') ? 'font-mono' : ''}>{value}</span>}
                        </td>
                      );
                    })}
                    <td className="border-b border-baker-border px-3 py-4 text-right group-hover:bg-warm-bg">
                      <button className="font-semibold text-brand hover:text-brand-dark">Open</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 grid gap-3 lg:hidden">
            {rows.map((row, index) => (
              <div key={index} className="rounded-xl border border-baker-border bg-warm-bg p-4">
                {config.columns.slice(0, 5).map((column) => (
                  <div key={column} className="flex justify-between gap-4 border-b border-baker-border/70 py-2 last:border-0">
                    <span className="text-xs font-bold uppercase text-baker-muted">{column}</span>
                    <span className="text-right text-sm font-medium">{String(row[column] ?? '—')}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>

          {!rows.length ? (
            <div className="mt-6 rounded-2xl border border-dashed border-baker-border bg-cream/60 p-8 text-center">
              <p className="font-bold">{config.emptyState}</p>
              <p className="mt-2 text-sm text-baker-muted">Try clearing filters or create a new record.</p>
            </div>
          ) : null}
        </Card>

        <aside className="space-y-4">
          <Card>
            <div className="mb-3 flex items-center gap-2">
              <Code2 className="h-5 w-5 text-brand" />
              <h3 className="font-bold">API wired for this screen</h3>
            </div>
            <div className="space-y-2">
              {config.api.map((endpoint) => (
                <code key={endpoint} className="block rounded-lg bg-baker-text px-3 py-2 text-xs text-white">{endpoint}</code>
              ))}
            </div>
          </Card>

          <Card>
            <h3 className="font-bold">Primary form fields</h3>
            <div className="mt-3 space-y-2">
              {config.formFields.slice(0, 9).map((field) => (
                <label key={field} className="block text-sm font-medium text-baker-muted">
                  {field}
                  <div className="mt-1 rounded-lg border border-baker-border bg-warm-bg px-3 py-2 text-baker-muted">{field.includes('Date') || field.includes('Time') ? 'Select date/time' : `Enter ${field.toLowerCase()}`}</div>
                </label>
              ))}
            </div>
            <p className="mt-4 rounded-xl bg-cream p-3 text-xs leading-5 text-baker-muted">This panel becomes a shadcn/ui Sheet or Dialog for add/edit flows. Accountants can see it read-only; staff only see operational fields.</p>
          </Card>
        </aside>
      </div>
    </div>
  );
}
