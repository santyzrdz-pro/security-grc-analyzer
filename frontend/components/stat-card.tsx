"use client";

import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon: Icon,
  accent = "primary",
  hint,
}: {
  label: string;
  value: string | number;
  icon: React.ComponentType<{ className?: string }>;
  accent?: "primary" | "danger" | "warning" | "success" | "critical";
  hint?: string;
}) {
  const accentMap: Record<string, string> = {
    primary: "text-primary bg-primary/15",
    danger: "text-danger bg-danger/15",
    warning: "text-warning bg-warning/15",
    success: "text-success bg-success/15",
    critical: "text-critical bg-critical/15",
  };
  return (
    <div className="rounded-xl border border-border bg-surface p-5 card-glow">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-muted">{label}</p>
        <div className={cn("flex h-9 w-9 items-center justify-center rounded-lg", accentMap[accent])}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <p className="mt-3 text-3xl font-bold text-foreground">{value}</p>
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
    </div>
  );
}
