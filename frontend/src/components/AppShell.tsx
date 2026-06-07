import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  BarChart2,
  Bell,
  BookOpen,
  Box,
  ChefHat,
  ClipboardCheck,
  ClipboardList,
  FileText,
  Home,
  LogOut,
  Menu,
  Package,
  Search,
  Settings,
  Shield,
  ShoppingBag,
  ShoppingCart,
  Store,
  Truck,
  Upload,
  Users,
  Zap,
} from 'lucide-react';
import { navItems } from '../data/mock';
import { cx } from '../lib/format';

const icons = {
  BarChart2,
  BookOpen,
  Box,
  ChefHat,
  ClipboardCheck,
  ClipboardList,
  FileText,
  Home,
  Package,
  Settings,
  Shield,
  ShoppingBag,
  ShoppingCart,
  Store,
  Truck,
  Upload,
  Users,
  Zap,
};

type IconName = keyof typeof icons;

function SidebarLink({ label, href, icon }: { label: string; href: string; icon: string }) {
  const Icon = icons[icon as IconName] ?? Home;
  return (
    <NavLink
      to={href}
      className={({ isActive }) =>
        cx(
          'focus-ring group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition',
          isActive ? 'bg-brand text-white shadow-sm' : 'text-baker-muted hover:bg-cream hover:text-baker-text',
        )
      }
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="truncate">{label}</span>
    </NavLink>
  );
}

export function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  let currentSection = '';

  function handleLogout() {
    localStorage.clear();
    navigate('/login', { replace: true });
  }
  const active = navItems.find((item) => location.pathname.startsWith(item.href));
  const mobileItems = navItems.filter((item) => ['Dashboard', 'Quotes', 'Orders', 'Production'].includes(item.label));

  return (
    <div className="min-h-screen bg-warm-bg text-baker-text">
      <aside className="no-print fixed inset-y-0 left-0 z-30 hidden w-72 flex-col border-r border-baker-border bg-white/95 backdrop-blur xl:flex">
        <div className="flex h-20 items-center gap-3 border-b border-baker-border px-5">
          <div className="grid h-11 w-11 place-items-center rounded-2xl bg-brand text-lg font-black text-white shadow-sm">BP</div>
          <div>
            <p className="text-base font-extrabold tracking-tight">BakerProfit OS</p>
            <p className="text-xs text-baker-muted">Never undercharge again</p>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto px-4 py-5">
          {navItems.map((item) => {
            const showSection = item.section && item.section !== currentSection;
            if (item.section) currentSection = item.section;
            return (
              <div key={item.href}>
                {showSection ? <p className="mb-2 mt-5 px-3 text-[11px] font-bold uppercase tracking-[0.18em] text-baker-muted/70 first:mt-0">{item.section}</p> : null}
                <SidebarLink label={item.label} href={item.href} icon={item.icon} />
              </div>
            );
          })}
        </nav>

        <div className="border-t border-baker-border p-4">
          <button onClick={handleLogout} className="focus-ring flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium text-baker-muted hover:bg-cream hover:text-baker-text">
            <LogOut className="h-4 w-4" /> Logout
          </button>
        </div>
      </aside>

      <div className="xl:pl-72">
        <header className="no-print sticky top-0 z-20 flex h-20 items-center justify-between border-b border-baker-border bg-warm-bg/90 px-4 backdrop-blur md:px-8">
          <div className="flex items-center gap-3">
            <button className="focus-ring rounded-lg border border-baker-border bg-white p-2 xl:hidden" aria-label="Open menu">
              <Menu className="h-5 w-5" />
            </button>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand">Bold Munch</p>
              <h1 className="text-xl font-bold tracking-tight md:text-2xl">{active?.label ?? 'Dashboard'}</h1>
            </div>
          </div>

          <div className="hidden min-w-80 items-center gap-3 rounded-xl border border-baker-border bg-white px-3 py-2 md:flex">
            <Search className="h-4 w-4 text-baker-muted" />
            <input className="w-full bg-transparent text-sm outline-none placeholder:text-baker-muted" placeholder="Search customers, quotes, products..." />
          </div>

          <div className="flex items-center gap-3">
            <button className="focus-ring relative rounded-xl border border-baker-border bg-white p-2">
              <Bell className="h-5 w-5" />
              <span className="absolute -right-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-red-600 px-1 text-[10px] font-bold text-white">2</span>
            </button>
            <div className="hidden items-center gap-3 rounded-xl border border-baker-border bg-white px-3 py-2 sm:flex">
              <div className="grid h-8 w-8 place-items-center rounded-full bg-cream text-sm font-bold text-brand">CN</div>
              <div className="text-sm">
                <p className="font-semibold">Charles N</p>
                <p className="text-xs text-baker-muted">Owner</p>
              </div>
            </div>
          </div>
        </header>

        <main className="px-4 py-6 pb-24 md:px-8 xl:pb-8">
          <Outlet />
        </main>
      </div>

      <nav className="no-print fixed inset-x-0 bottom-0 z-30 grid grid-cols-4 border-t border-baker-border bg-white xl:hidden">
        {mobileItems.map((item) => {
          const Icon = icons[item.icon as IconName] ?? Home;
          return (
            <NavLink
              key={item.href}
              to={item.href}
              className={({ isActive }) => cx('flex flex-col items-center gap-1 px-2 py-3 text-xs font-semibold', isActive ? 'text-brand' : 'text-baker-muted')}
            >
              <Icon className="h-5 w-5" />
              {item.label.replace('Dashboard', 'Home')}
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}
