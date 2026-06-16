"use client";

import { cn } from "@/lib/utils";

export function Table({ children }: { children: React.ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">{children}</table>
    </div>
  );
}

export function THead({ children }: { children: React.ReactNode }) {
  return (
    <thead className="border-b border-border text-left text-xs uppercase tracking-wider text-muted">
      {children}
    </thead>
  );
}

export function TH({ children, className }: { children?: React.ReactNode; className?: string }) {
  return <th className={cn("px-4 py-3 font-medium", className)}>{children}</th>;
}

export function TR({
  children,
  className,
  onClick,
}: {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <tr
      onClick={onClick}
      className={cn(
        "border-b border-border/60 transition-colors hover:bg-surface-2/50",
        onClick && "cursor-pointer",
        className
      )}
    >
      {children}
    </tr>
  );
}

export function TD({ children, className }: { children?: React.ReactNode; className?: string }) {
  return <td className={cn("px-4 py-3 text-foreground", className)}>{children}</td>;
}

export function Pagination({
  page,
  pages,
  total,
  onPage,
}: {
  page: number;
  pages: number;
  total: number;
  onPage: (p: number) => void;
}) {
  return (
    <div className="flex items-center justify-between px-4 py-3 text-sm text-muted">
      <span>
        {total} record{total === 1 ? "" : "s"}
      </span>
      <div className="flex items-center gap-2">
        <button
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
          className="rounded-lg border border-border px-3 py-1 disabled:opacity-40 hover:bg-surface-2"
        >
          Prev
        </button>
        <span className="text-foreground">
          {pages === 0 ? 0 : page} / {pages}
        </span>
        <button
          disabled={page >= pages}
          onClick={() => onPage(page + 1)}
          className="rounded-lg border border-border px-3 py-1 disabled:opacity-40 hover:bg-surface-2"
        >
          Next
        </button>
      </div>
    </div>
  );
}
