import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, FileText, Loader2, ShoppingCart, Upload, Zap } from 'lucide-react';
import { Card, Badge, Button, SeverityIcon } from '../components/ui';
import { api } from '../lib/api';
import { useUser } from '../lib/user-context';
import { marginTextClass } from '../lib/format';

type DashboardData = {
  orders_today: number;
  open_quotes: number;
  week_revenue: string;
  week_net_profit: string;
  upcoming_deliveries: Array<{ order_number: string; customer_name?: string; due_date?: string }>;
  low_margin_products: Array<{ product_name: string; margin_percent?: number; severity?: string }>;
  most_profitable_product: string | null;
  low_stock_ingredients: Array<{ name: string }>;
};

type IntelligenceEvent = {
  id: string;
  event_type: string;
  severity: string;
  title: string;
  message: string;
  is_read: boolean;
};

function fmt(v: unknown, prefix = ''): string {
  if (v == null) return '—';
  return `${prefix}${v}`;
}

function fmtMoney(v: unknown): string {
  if (v == null) return '—';
  return `£${Number(v).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtDate(v: unknown): string {
  if (!v) return '—';
  return new Date(v as string).toLocaleDateString('en-GB', { weekday: 'short', day: '2-digit', month: 'short' });
}

export default function Dashboard() {
  const user = useUser();
  const [dash, setDash] = useState<DashboardData | null>(null);
  const [events, setEvents] = useState<IntelligenceEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<DashboardData>('/reports/dashboard'),
      api.get<IntelligenceEvent[]>('/intelligence/events'),
    ]).then(([dashRes, eventsRes]) => {
      setDash(dashRes.data);
      setEvents(eventsRes.data.slice(0, 3));
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const firstName = user?.full_name?.split(' ')[0] ?? 'there';
  const bakeryName = user?.tenant_name ?? 'Your Bakery';

  const stats = dash ? [
    { label: 'Orders Today', value: String(dash.orders_today), hint: 'confirmed orders', href: '/orders' },
    { label: 'Open Quotes', value: String(dash.open_quotes), hint: 'awaiting acceptance', href: '/quotes' },
    { label: 'This Week Revenue', value: fmtMoney(dash.week_revenue), hint: 'total invoiced', href: '/reports' },
    { label: 'This Week Net Profit', value: fmtMoney(dash.week_net_profit), hint: 'after all costs', href: '/reports', profitValue: Number(dash.week_revenue) > 0 ? (Number(dash.week_net_profit) / Number(dash.week_revenue)) * 100 : null },
  ] : [];

  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          {loading ? (
            <div className="h-8 w-48 animate-pulse rounded-lg bg-cream" />
          ) : (
            <>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand">Good morning, {firstName}</p>
              <h2 className="mt-1 text-3xl font-extrabold tracking-tight">{bakeryName} command centre</h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-baker-muted">
                Your golden workflow: parse a customer message → quote → check profit → accept → order → production → shopping list.
              </p>
            </>
          )}
        </div>
        <div className="flex flex-wrap gap-3">
          <Link to="/quotes"><Button>New Quote</Button></Link>
          <Link to="/intelligence"><Button variant="secondary">Parse Order</Button></Link>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-brand" />
        </div>
      ) : (
        <>
          <section className="grid gap-4 md:grid-cols-2 2xl:grid-cols-4">
            {stats.map((stat) => (
              <Link key={stat.label} to={stat.href} className="focus-ring rounded-2xl">
                <Card className="h-full transition hover:-translate-y-0.5 hover:shadow-md">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-baker-muted">{stat.label}</p>
                      <p className={stat.profitValue != null ? `mt-3 text-3xl font-extrabold ${marginTextClass(stat.profitValue)}` : 'mt-3 text-3xl font-extrabold'}>
                        {stat.value}
                      </p>
                      <p className="mt-2 text-xs text-baker-muted">{stat.hint}</p>
                    </div>
                    <ArrowRight className="h-5 w-5 text-brand" />
                  </div>
                </Card>
              </Link>
            ))}
          </section>

          <section className="mt-4 grid gap-4 lg:grid-cols-3">
            <Card>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-bold">Upcoming Deliveries</h3>
                <Badge tone="info">{dash?.upcoming_deliveries?.length ?? 0}</Badge>
              </div>
              {dash?.upcoming_deliveries?.length ? (
                <div className="space-y-3">
                  {dash.upcoming_deliveries.slice(0, 5).map((item, i) => (
                    <div key={i} className="rounded-xl border border-baker-border bg-cream/60 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold">{fmt(item.order_number)}</p>
                        <span className="text-xs text-baker-muted">{fmtDate(item.due_date)}</span>
                      </div>
                      {item.customer_name && <p className="mt-1 text-sm text-baker-muted">{item.customer_name}</p>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-baker-muted">No upcoming deliveries.</p>
              )}
            </Card>

            <Card>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-bold">Low Margin Products</h3>
                <Badge tone="warning">{dash?.low_margin_products?.length ?? 0}</Badge>
              </div>
              {dash?.low_margin_products?.length ? (
                <div className="space-y-3">
                  {dash.low_margin_products.slice(0, 4).map((item, i) => (
                    <div key={i} className="rounded-xl border border-baker-border p-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold text-sm">{fmt(item.product_name)}</p>
                        <Badge tone="warning">{(item.severity ?? 'low margin').replace(/_/g, ' ')}</Badge>
                      </div>
                      {item.margin_percent != null && (
                        <>
                          <div className="mt-2 h-2 rounded-full bg-stone-100">
                            <div className="h-2 rounded-full bg-orange-500" style={{ width: `${Math.min(Number(item.margin_percent), 100)}%` }} />
                          </div>
                          <p className="mt-1.5 text-sm font-bold text-orange-700">{Number(item.margin_percent).toFixed(1)}% margin</p>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-baker-muted">No low-margin products detected.</p>
              )}
            </Card>

            <Card className="bg-gradient-to-br from-white to-cream">
              <h3 className="text-lg font-bold">Most Profitable Product</h3>
              {dash?.most_profitable_product ? (
                <>
                  <p className="mt-6 text-sm text-baker-muted">Current winner</p>
                  <p className="mt-1 text-2xl font-extrabold">{dash.most_profitable_product}</p>
                </>
              ) : (
                <p className="mt-6 text-sm text-baker-muted">Complete orders to see your best performer.</p>
              )}
              <Link to="/reports" className="mt-4 block text-sm font-semibold text-brand hover:underline">View full report →</Link>
            </Card>
          </section>

          <section className="mt-4 grid gap-4 xl:grid-cols-[1fr_1.2fr]">
            <Card>
              <h3 className="text-lg font-bold">Quick Actions</h3>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {[
                  { label: 'New Quote', icon: FileText, href: '/quotes' },
                  { label: 'Parse Order Message', icon: Zap, href: '/intelligence' },
                  { label: 'Generate Shopping List', icon: ShoppingCart, href: '/shopping-lists' },
                  { label: 'Import Cost Sheet', icon: Upload, href: '/imports' },
                ].map((action) => {
                  const Icon = action.icon;
                  return (
                    <Link key={action.label} to={action.href} className="focus-ring flex items-center gap-3 rounded-xl border border-baker-border bg-cream/50 p-4 font-semibold hover:bg-cream">
                      <Icon className="h-5 w-5 text-brand" />
                      {action.label}
                    </Link>
                  );
                })}
              </div>
            </Card>

            <Card>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-bold">Recent Intelligence Events</h3>
                {events.filter((e) => !e.is_read).length > 0 && (
                  <Badge tone="danger">{events.filter((e) => !e.is_read).length} unread</Badge>
                )}
              </div>
              {events.length ? (
                <div className="space-y-3">
                  {events.map((event) => (
                    <div key={event.id} className="flex gap-3 rounded-xl border border-baker-border p-4">
                      <SeverityIcon severity={event.severity} />
                      <div>
                        <p className="font-semibold">{event.title}</p>
                        <p className="mt-1 text-sm text-baker-muted">{event.message}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-baker-muted">No intelligence events yet. Generate margin alerts from the Intelligence page.</p>
              )}
            </Card>
          </section>
        </>
      )}
    </div>
  );
}
