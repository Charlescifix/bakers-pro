import { Link } from 'react-router-dom';
import { ArrowRight, ClipboardList, FileText, Plus, ShoppingCart, Upload, Zap } from 'lucide-react';
import { Card, Badge, Button, SeverityIcon } from '../components/ui';
import { dashboard } from '../data/mock';
import { marginTextClass } from '../lib/format';

export default function Dashboard() {
  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand">Good morning, Charles</p>
          <h2 className="mt-1 text-3xl font-extrabold tracking-tight">Bold Munch command centre</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-baker-muted">
            Your golden workflow stays visible: parse a customer message, build a quote, check profit, accept, convert to order, then generate production and shopping lists.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button>New Quote</Button>
          <Button variant="secondary">Parse Order</Button>
        </div>
      </div>

      <section className="grid gap-4 md:grid-cols-2 2xl:grid-cols-4">
        {dashboard.stats.map((stat, index) => (
          <Link key={stat.label} to={stat.href} className="focus-ring rounded-2xl">
            <Card className="h-full transition hover:-translate-y-0.5 hover:shadow-md">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-baker-muted">{stat.label}</p>
                  <p className={index === 3 ? `mt-3 text-3xl font-extrabold ${marginTextClass(56.2)}` : 'mt-3 text-3xl font-extrabold'}>{stat.value}</p>
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
            <Badge tone="info">live</Badge>
          </div>
          <div className="space-y-3">
            {dashboard.deliveries.map((item) => (
              <div key={item.order} className="rounded-xl border border-baker-border bg-cream/60 p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold">{item.order}</p>
                  <span className="text-xs text-baker-muted">{item.date}</span>
                </div>
                <p className="mt-1 text-sm text-baker-muted">{item.customer}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-bold">Low Margin Products</h3>
            <Badge tone="warning">review</Badge>
          </div>
          <div className="space-y-3">
            {dashboard.lowMargin.map((item) => (
              <div key={item.product} className="rounded-xl border border-baker-border p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold">{item.product}</p>
                  <Badge tone="warning">{item.severity.replace('_', ' ')}</Badge>
                </div>
                <div className="mt-3 h-2 rounded-full bg-stone-100">
                  <div className="h-2 rounded-full bg-orange-500" style={{ width: `${Math.min(item.margin, 100)}%` }} />
                </div>
                <p className="mt-2 text-sm font-bold text-orange-700">{item.margin.toFixed(1)}% margin</p>
              </div>
            ))}
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-white to-cream">
          <h3 className="text-lg font-bold">Most Profitable Product</h3>
          <p className="mt-6 text-sm text-baker-muted">Current winner</p>
          <p className="mt-1 text-3xl font-extrabold">Puff Puff Tray</p>
          <p className="mt-3 text-5xl font-black text-green-700">68.4%</p>
          <p className="mt-2 text-sm text-baker-muted">Net margin after ingredients, packaging, labour and channel fees.</p>
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
            <Badge tone="danger">2 unread</Badge>
          </div>
          <div className="space-y-3">
            {dashboard.events.map((event) => (
              <div key={event.title} className="flex gap-3 rounded-xl border border-baker-border p-4">
                <SeverityIcon severity={event.severity} />
                <div>
                  <p className="font-semibold">{event.title}</p>
                  <p className="mt-1 text-sm text-baker-muted">{event.message}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </section>

      <Link to="/quotes" className="no-print fixed bottom-24 right-4 grid h-14 w-14 place-items-center rounded-full bg-brand text-white shadow-xl xl:hidden" aria-label="New quote">
        <Plus className="h-7 w-7" />
      </Link>
    </div>
  );
}
