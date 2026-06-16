"use client";

import { createContext, useCallback, useContext, useState } from "react";
import { CheckCircle2, AlertTriangle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastKind = "success" | "error" | "info";

interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

interface ToastContextValue {
  toast: (message: string, kind?: ToastKind) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const remove = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (message: string, kind: ToastKind = "success") => {
      const id = Date.now() + Math.random();
      setToasts((prev) => [...prev, { id, kind, message }]);
      setTimeout(() => remove(id), 4000);
    },
    [remove]
  );

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-5 right-5 z-[100] flex w-80 flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={cn(
              "flex items-start gap-3 rounded-lg border bg-surface px-4 py-3 shadow-lg animate-in",
              t.kind === "success" && "border-success/40",
              t.kind === "error" && "border-danger/40",
              t.kind === "info" && "border-primary/40"
            )}
          >
            {t.kind === "success" && <CheckCircle2 className="mt-0.5 h-5 w-5 text-success" />}
            {t.kind === "error" && <AlertTriangle className="mt-0.5 h-5 w-5 text-danger" />}
            {t.kind === "info" && <Info className="mt-0.5 h-5 w-5 text-primary" />}
            <p className="flex-1 text-sm text-foreground">{t.message}</p>
            <button onClick={() => remove(t.id)} className="text-muted hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
