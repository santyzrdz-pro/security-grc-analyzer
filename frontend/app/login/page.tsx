"use client";

import { useState } from "react";
import { ShieldCheck } from "lucide-react";
import { useAuth } from "@/lib/auth";
import { useToast } from "@/components/ui/toast";
import { Button, Input, Label } from "@/components/ui/primitives";
import { ApiError } from "@/lib/api";

const DEMO_ACCOUNTS = [
  { label: "Admin", email: "admin@controlmap.ai", password: "Admin123!" },
  { label: "Analyst", email: "analyst@controlmap.ai", password: "Analyst123!" },
  { label: "Auditor", email: "auditor@controlmap.ai", password: "Auditor123!" },
  { label: "Executive", email: "exec@controlmap.ai", password: "Exec123!" },
];

export default function LoginPage() {
  const { login } = useAuth();
  const { toast } = useToast();
  const [email, setEmail] = useState("admin@controlmap.ai");
  const [password, setPassword] = useState("Admin123!");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Login failed";
      toast(msg, "error");
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="absolute inset-0 bg-[radial-gradient(60%_60%_at_50%_0%,hsl(217_91%_60%/0.12),transparent)]" />
      <div className="relative w-full max-w-md">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/15 ring-1 ring-primary/30">
            <ShieldCheck className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-xl font-bold leading-tight text-foreground">
            Security Compliance &amp; Risk Management Analyzer
          </h1>
          <p className="mt-2 text-sm text-muted">
            NIST 800-53 control mapping, risk scoring &amp; compliance
          </p>
        </div>

        <form
          onSubmit={submit}
          className="rounded-xl border border-border bg-surface p-6 card-glow"
        >
          <div className="mb-4">
            <Label>Email</Label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
            />
          </div>
          <div className="mb-6">
            <Label>Password</Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          <Button type="submit" loading={loading} className="w-full">
            Sign in
          </Button>
        </form>

        <div className="mt-6 rounded-xl border border-border bg-surface/60 p-4">
          <p className="mb-2 text-xs font-medium text-muted">Demo accounts (click to fill)</p>
          <div className="grid grid-cols-2 gap-2">
            {DEMO_ACCOUNTS.map((a) => (
              <button
                key={a.email}
                onClick={() => {
                  setEmail(a.email);
                  setPassword(a.password);
                }}
                className="rounded-lg border border-border bg-surface-2 px-3 py-2 text-left text-xs text-foreground hover:border-primary"
              >
                <span className="block font-semibold">{a.label}</span>
                <span className="text-muted">{a.email}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
