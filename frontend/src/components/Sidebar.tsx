"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Bot, CreditCard, Settings, ShieldCheck, LogOut, Languages } from "lucide-react";
import clsx from "clsx";
import { WolfLogo } from "./WolfLogo";
import { useLocale } from "@/hooks/useLocale";
import { useAuth } from "@/hooks/useAuth";

export function Sidebar() {
  const pathname = usePathname();
  const { t, toggleLocale, locale } = useLocale();
  const { user, logout } = useAuth();

  const links = [
    { href: "/dashboard", label: t.nav_dashboard, icon: LayoutDashboard },
    { href: "/dashboard/bots", label: t.nav_bots, icon: Bot },
    { href: "/dashboard/billing", label: t.nav_billing, icon: CreditCard },
    { href: "/dashboard/settings", label: t.nav_settings, icon: Settings },
  ];

  if (user?.role === "admin" || user?.role === "super_admin") {
    links.push({ href: "/dashboard/admin", label: t.nav_admin, icon: ShieldCheck });
  }

  return (
    <aside className="w-64 shrink-0 h-screen sticky top-0 border-e border-slate-800 bg-slate-950/80 backdrop-blur-sm flex flex-col">
      <div className="flex items-center gap-2 px-6 py-6">
        <WolfLogo className="w-8 h-8" />
        <span className="font-display font-bold text-lg text-slate-100 tracking-tight">{t.brand}</span>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {links.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
                active ? "bg-ember-500/10 text-ember-400 border border-ember-500/20" : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              )}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-3 pb-6 space-y-1 border-t border-slate-800 pt-4">
        <button onClick={toggleLocale} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 w-full">
          <Languages size={18} />
          {locale === "ar" ? "English" : "العربية"}
        </button>
        <button onClick={() => logout()} className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-signal-red/80 hover:text-signal-red hover:bg-signal-red/5 w-full">
          <LogOut size={18} />
          {t.nav_logout}
        </button>
      </div>
    </aside>
  );
}
