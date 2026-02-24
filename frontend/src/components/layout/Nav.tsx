"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getFehler, getKonfigs } from "@/lib/api";

const navItems = [
  { href: "/",       label: "Dashboard",         icon: "⬛" },
  { href: "/berufe", label: "Berufe",             icon: "📄" },
  { href: "/fehler", label: "Fehler",             icon: "✗",  badge: "fehler"  },
  { href: "/konfig", label: "Konfig-Bibliothek",  icon: "⚙",  badge: "pending" },
];

export default function Nav() {
  const path = usePathname();
  const [badges, setBadges] = useState({ fehler: 0, pending: 0 });

  useEffect(() => {
    async function load() {
      try {
        const [fehler, konfigs] = await Promise.all([getFehler(), getKonfigs()]);
        setBadges({ fehler: fehler.length, pending: konfigs.pending.length });
      } catch { /* API evtl. noch nicht erreichbar */ }
    }
    load();
    const iv = setInterval(load, 10_000);
    return () => clearInterval(iv);
  }, []);

  return (
    <nav className="w-56 shrink-0 bg-white border-r border-slate-200 flex flex-col py-6 px-3 gap-1">
      <div className="px-3 mb-4">
        <h1 className="text-sm font-bold text-slate-800 leading-tight">BPÜ Pipeline</h1>
        <p className="text-xs text-slate-400">Datenextraktion</p>
      </div>
      {navItems.map((item) => {
        const aktiv = path === item.href || (item.href !== "/" && path.startsWith(item.href));
        const count = item.badge ? badges[item.badge as keyof typeof badges] : 0;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors
              ${aktiv
                ? "bg-blue-50 text-blue-700 font-medium"
                : "text-slate-600 hover:bg-slate-100"
              }`}
          >
            <span className="flex items-center gap-2">
              <span className="text-base">{item.icon}</span>
              {item.label}
            </span>
            {count > 0 && (
              <span className="text-xs bg-red-500 text-white rounded-full px-1.5 py-0.5 leading-none">
                {count}
              </span>
            )}
          </Link>
        );
      })}
    </nav>
  );
}
