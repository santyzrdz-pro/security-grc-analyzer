"use client";

import { useCallback, useEffect, useState } from "react";
import { FileDown, FileText } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { ReportMeta } from "@/lib/types";
import { useAuth } from "@/lib/auth";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/page-header";
import { Button, Card, CardHeader, Spinner } from "@/components/ui/primitives";
import { Table, THead, TH, TR, TD } from "@/components/ui/table";

const SECTIONS = [
  "Executive Summary",
  "Asset Inventory",
  "Findings",
  "Risk Register",
  "Control Mapping",
  "Compliance Status",
  "Recommendations",
];

export default function ReportsPage() {
  const { can } = useAuth();
  const { toast } = useToast();
  const canWrite = can("report:write");

  const [reports, setReports] = useState<ReportMeta[] | null>(null);
  const [generating, setGenerating] = useState(false);

  const load = useCallback(async () => {
    setReports(await api.get<ReportMeta[]>("/reports"));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function generate() {
    setGenerating(true);
    try {
      const blob = await api.download("/reports");
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "security-grc-audit-report.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast("Audit report generated");
      load();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Generation failed", "error");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Audit Report Generator"
        description="Produce audit-ready PDF reports covering posture, risk, and NIST compliance."
        action={
          canWrite && (
            <Button onClick={generate} loading={generating}>
              <FileDown className="h-4 w-4" /> Export PDF Report
            </Button>
          )
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader title="Report Sections" subtitle="Included in every export" />
          <ul className="space-y-2 p-5">
            {SECTIONS.map((s, i) => (
              <li key={s} className="flex items-center gap-3 text-sm text-foreground">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
                  {i + 1}
                </span>
                {s}
              </li>
            ))}
          </ul>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="Generated Reports" subtitle="History of exported reports" />
          {!reports ? (
            <div className="flex h-48 items-center justify-center">
              <Spinner />
            </div>
          ) : reports.length === 0 ? (
            <div className="flex h-48 flex-col items-center justify-center text-muted">
              <FileText className="mb-2 h-8 w-8" />
              <p className="text-sm">No reports generated yet.</p>
            </div>
          ) : (
            <Table>
              <THead>
                <tr>
                  <TH>Title</TH>
                  <TH>Type</TH>
                  <TH>Compliance</TH>
                  <TH>Summary</TH>
                  <TH>Generated</TH>
                </tr>
              </THead>
              <tbody>
                {reports.map((r) => (
                  <TR key={r.id}>
                    <TD className="font-medium">{r.title}</TD>
                    <TD className="text-muted">{r.report_type}</TD>
                    <TD>{r.compliance_score != null ? `${r.compliance_score}%` : "-"}</TD>
                    <TD className="text-muted">{r.summary}</TD>
                    <TD className="text-muted">
                      {new Date(r.created_at).toLocaleString()}
                    </TD>
                  </TR>
                ))}
              </tbody>
            </Table>
          )}
        </Card>
      </div>
    </div>
  );
}
