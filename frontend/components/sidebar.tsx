"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Server,
  Bug,
  ShieldCheck,
  Network,
  AlertTriangle,
  KanbanSquare,
  Gauge,
  FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/assets", label: "Assets", icon: Server },
  { href: "/findings", label: "Findings", icon: Bug },
  { href: "/controls", label: "NIST Controls", icon: ShieldCheck },
  { href: "/mapping", label: "Mapping Engine", icon: Network },
  { href: "/risks", label: "Risk Register", icon: AlertTriangle },
  { href: "/remediation", label: "Remediation", icon: KanbanSquare },
  { href: "/compliance", label: "Compliance", icon: Gauge },
  { href: "/reports", label: "Reports", icon: FileText },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-border bg-surface">
      <div className="flex items-center gap-2 px-5 py-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/15 ring-1 ring-primary/30">
          <ShieldCheck className="h-5 w-5 text-primary" />
        </div>
        <div>
          <p className="text-sm font-bold leading-tight text-foreground">GRC Analyzer</p>
          <p className="text-[10px] font-medium uppercase tracking-wider text-primary">
            Compliance &amp; Risk
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-2">
        {NAV.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-primary/15 text-primary"
                  : "text-muted hover:bg-surface-2 hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
