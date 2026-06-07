import type { ReactNode } from 'react';
import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react';
import { cx } from '../lib/format';

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={cx('rounded-2xl border border-baker-border bg-white p-5 shadow-sm', className)}>{children}</section>;
}

export function Button({ children, variant = 'primary' }: { children: ReactNode; variant?: 'primary' | 'secondary' | 'danger' }) {
  return (
    <button
      className={cx(
        'focus-ring inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold shadow-sm transition',
        variant === 'primary' && 'bg-brand text-white hover:bg-brand-dark',
        variant === 'secondary' && 'border border-baker-border bg-white text-baker-text hover:bg-cream',
        variant === 'danger' && 'bg-red-600 text-white hover:bg-red-700',
      )}
    >
      {children}
    </button>
  );
}

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'purple' }) {
  return (
    <span
      className={cx(
        'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-bold capitalize',
        tone === 'success' && 'bg-green-100 text-green-700',
        tone === 'warning' && 'bg-orange-100 text-orange-700',
        tone === 'danger' && 'bg-red-100 text-red-700',
        tone === 'info' && 'bg-blue-100 text-blue-700',
        tone === 'purple' && 'bg-purple-100 text-purple-700',
        tone === 'neutral' && 'bg-stone-100 text-stone-700',
      )}
    >
      {children}
    </span>
  );
}

export function SeverityIcon({ severity }: { severity: string }) {
  if (severity === 'critical' || severity === 'danger') return <XCircle className="h-5 w-5 text-red-600" />;
  if (severity === 'warning') return <AlertTriangle className="h-5 w-5 text-orange-600" />;
  if (severity === 'success') return <CheckCircle2 className="h-5 w-5 text-green-700" />;
  return <Info className="h-5 w-5 text-blue-700" />;
}

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand">{eyebrow}</p>
        <h2 className="mt-1 text-3xl font-extrabold tracking-tight">{title}</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-baker-muted">{description}</p>
      </div>
      {action}
    </div>
  );
}
