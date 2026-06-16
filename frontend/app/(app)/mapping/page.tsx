"use client";

import { useState } from "react";
import { Network, Wand2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { MappingResponse } from "@/lib/types";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/page-header";
import { Badge, Button, Card, CardHeader, Textarea } from "@/components/ui/primitives";

const EXAMPLES = [
  "Firewall Disabled",
  "Weak Password Policy",
  "Excessive Administrator Privileges",
  "Missing Security Logging",
  "MFA not enforced for admin console",
];

export default function MappingPage() {
  const { toast } = useToast();
  const [text, setText] = useState("Firewall Disabled");
  const [result, setResult] = useState<MappingResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    if (!text.trim()) return;
    setLoading(true);
    try {
      setResult(await api.post<MappingResponse>("/mapping", { finding: text }));
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Mapping failed", "error");
    } finally {
      setLoading(false);
    }
  }

  function confidenceColor(c: number) {
    if (c >= 85) return "text-success";
    if (c >= 60) return "text-warning";
    return "text-muted";
  }

  return (
    <div>
      <PageHeader
        title="Automatic Control Mapping Engine"
        description="Rule-based engine that maps finding text to NIST 800-53 controls with confidence scoring."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Finding Text" subtitle="Enter a finding title or description" />
          <div className="space-y-4 p-5">
            <Textarea
              rows={5}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="e.g. The host firewall is disabled on the perimeter device"
            />
            <div className="flex flex-wrap gap-2">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => setText(ex)}
                  className="rounded-full border border-border bg-surface-2 px-3 py-1 text-xs text-muted hover:border-primary hover:text-foreground"
                >
                  {ex}
                </button>
              ))}
            </div>
            <Button onClick={run} loading={loading} className="w-full">
              <Wand2 className="h-4 w-4" /> Run Mapping
            </Button>
          </div>
        </Card>

        <Card>
          <CardHeader title="Mapping Result" subtitle="Suggested controls and confidence" />
          <div className="p-5">
            {!result ? (
              <div className="flex h-48 flex-col items-center justify-center text-muted">
                <Network className="mb-2 h-8 w-8" />
                <p className="text-sm">Run the engine to see mapped controls.</p>
              </div>
            ) : (
              <>
                <div className="mb-4 rounded-lg border border-border bg-surface-2 p-4">
                  <p className="text-xs uppercase tracking-wider text-muted">Overall confidence</p>
                  <p className={`text-3xl font-bold ${confidenceColor(result.confidence)}`}>
                    {result.confidence}%
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {result.controls.map((c) => (
                      <Badge key={c} className="border-primary/30 bg-primary/10 text-primary">
                        {c}
                      </Badge>
                    ))}
                    {result.controls.length === 0 && (
                      <span className="text-sm text-muted">No controls matched.</span>
                    )}
                  </div>
                </div>
                <div className="space-y-2">
                  {result.matches.map((m) => (
                    <div key={m.control_id} className="rounded-lg border border-border bg-surface-2 p-3">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-primary">{m.control_id}</span>
                        <span className={`text-sm font-semibold ${confidenceColor(m.confidence)}`}>
                          {m.confidence}% · {m.method}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-muted">{m.rationale}</p>
                    </div>
                  ))}
                </div>
                <pre className="mt-4 overflow-x-auto rounded-lg border border-border bg-background p-3 text-xs text-muted">
{JSON.stringify(
  { finding: result.finding, controls: result.controls, confidence: result.confidence },
  null,
  2
)}
                </pre>
              </>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
