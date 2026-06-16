"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Plus,
  Search,
  Upload,
  Sparkles,
  Network,
  Pencil,
  Trash2,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { Asset, Finding, Page } from "@/lib/types";
import { useAuth } from "@/lib/auth";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  Card,
  Input,
  Label,
  Select,
  Spinner,
  Textarea,
} from "@/components/ui/primitives";
import { Modal } from "@/components/ui/modal";
import { Table, THead, TH, TR, TD, Pagination } from "@/components/ui/table";
import { classForSeverity, classForStatus } from "@/lib/utils";
import { FINDING_STATUSES, SEVERITIES } from "@/lib/constants";

const EMPTY: Partial<Finding> = {
  title: "",
  description: "",
  severity: "Medium",
  status: "Open",
  source: "",
  cve: "",
  evidence: "",
  asset_id: null,
};

export default function FindingsPage() {
  const { can } = useAuth();
  const { toast } = useToast();
  const canWrite = can("finding:write");
  const fileRef = useRef<HTMLInputElement>(null);
  const importKind = useRef<"csv" | "json">("csv");

  const [data, setData] = useState<Page<Finding> | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const [editing, setEditing] = useState<Partial<Finding> | null>(null);
  const [saving, setSaving] = useState(false);
  const [detail, setDetail] = useState<Finding | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), page_size: "10" });
    if (search) params.set("search", search);
    if (severity) params.set("severity", severity);
    if (status) params.set("status", status);
    try {
      setData(await api.get<Page<Finding>>(`/findings?${params.toString()}`));
    } finally {
      setLoading(false);
    }
  }, [page, search, severity, status]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    api
      .get<Page<Asset>>("/assets?page_size=200")
      .then((p) => setAssets(p.items))
      .catch(() => setAssets([]));
  }, []);

  async function save() {
    if (!editing?.title) {
      toast("Title is required", "error");
      return;
    }
    setSaving(true);
    const payload = {
      title: editing.title,
      description: editing.description,
      severity: editing.severity,
      status: editing.status,
      source: editing.source,
      cve: editing.cve,
      evidence: editing.evidence,
      asset_id: editing.asset_id || null,
    };
    try {
      if (editing.id) {
        await api.patch(`/findings/${editing.id}`, payload);
        toast("Finding updated");
      } else {
        await api.post("/findings", payload);
        toast("Finding created & auto-mapped");
      }
      setEditing(null);
      load();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Save failed", "error");
    } finally {
      setSaving(false);
    }
  }

  async function remove(f: Finding) {
    if (!confirm(`Delete finding "${f.title}"?`)) return;
    try {
      await api.del(`/findings/${f.id}`);
      toast("Finding deleted");
      load();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Delete failed", "error");
    }
  }

  function triggerImport(kind: "csv" | "json") {
    importKind.current = kind;
    fileRef.current?.click();
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const res = await api.upload<{ imported: number; failed: number }>(
        `/findings/import/${importKind.current}`,
        file
      );
      toast(`Imported ${res.imported}, failed ${res.failed}`, res.failed ? "info" : "success");
      load();
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Import failed", "error");
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function remap(f: Finding) {
    setBusy(true);
    try {
      const updated = await api.post<Finding>(`/findings/${f.id}/remap`);
      setDetail(updated);
      toast("Re-mapped to controls");
      load();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Mapping failed", "error");
    } finally {
      setBusy(false);
    }
  }

  async function analyze(f: Finding) {
    setBusy(true);
    try {
      const updated = await api.post<Finding>(`/findings/${f.id}/analyze`);
      setDetail(updated);
      toast("AI analysis generated");
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Analysis failed", "error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader
        title="Findings Management"
        description="Track security findings and automatically map them to NIST controls."
        action={
          canWrite && (
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => triggerImport("csv")}>
                <Upload className="h-4 w-4" /> CSV
              </Button>
              <Button variant="secondary" onClick={() => triggerImport("json")}>
                <Upload className="h-4 w-4" /> JSON
              </Button>
              <Button onClick={() => setEditing({ ...EMPTY })}>
                <Plus className="h-4 w-4" /> New Finding
              </Button>
            </div>
          )
        }
      />
      <input
        ref={fileRef}
        type="file"
        accept=".csv,.json,application/json,text/csv"
        className="hidden"
        onChange={onFile}
      />

      <Card className="mb-4">
        <div className="flex flex-wrap items-center gap-3 p-4">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted" />
            <Input
              className="pl-9"
              placeholder="Search title, CVE, source..."
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
            />
          </div>
          <Select
            className="w-40"
            value={severity}
            onChange={(e) => {
              setPage(1);
              setSeverity(e.target.value);
            }}
          >
            <option value="">All Severity</option>
            {SEVERITIES.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </Select>
          <Select
            className="w-44"
            value={status}
            onChange={(e) => {
              setPage(1);
              setStatus(e.target.value);
            }}
          >
            <option value="">All Status</option>
            {FINDING_STATUSES.map((s) => (
              <option key={s}>{s}</option>
            ))}
          </Select>
        </div>
      </Card>

      <Card>
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <Spinner />
          </div>
        ) : (
          <>
            <Table>
              <THead>
                <tr>
                  <TH>Finding</TH>
                  <TH>Severity</TH>
                  <TH>Status</TH>
                  <TH>Asset</TH>
                  <TH>Mapped Controls</TH>
                  <TH>Detected</TH>
                  {canWrite && <TH className="text-right">Actions</TH>}
                </tr>
              </THead>
              <tbody>
                {data?.items.map((f) => (
                  <TR key={f.id} onClick={() => setDetail(f)}>
                    <TD className="font-medium">
                      {f.title}
                      {f.cve && <span className="block text-xs text-primary">{f.cve}</span>}
                    </TD>
                    <TD>
                      <Badge className={classForSeverity(f.severity)}>{f.severity}</Badge>
                    </TD>
                    <TD>
                      <Badge className={classForStatus(f.status)}>{f.status}</Badge>
                    </TD>
                    <TD className="text-muted">{f.asset_name || "-"}</TD>
                    <TD>
                      <div className="flex flex-wrap gap-1">
                        {f.mapped_controls.slice(0, 3).map((m) => (
                          <Badge key={m.control.id} className="border-primary/30 bg-primary/10 text-primary">
                            {m.control.control_id} · {m.confidence}%
                          </Badge>
                        ))}
                        {f.mapped_controls.length === 0 && (
                          <span className="text-xs text-muted">none</span>
                        )}
                      </div>
                    </TD>
                    <TD className="text-muted">{f.detection_date || "-"}</TD>
                    {canWrite && (
                      <TD className="text-right" >
                        <div
                          className="flex justify-end gap-1"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <button
                            onClick={() => setEditing({ ...f })}
                            className="rounded-md p-1.5 text-muted hover:bg-surface-2 hover:text-primary"
                          >
                            <Pencil className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => remove(f)}
                            className="rounded-md p-1.5 text-muted hover:bg-surface-2 hover:text-danger"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </TD>
                    )}
                  </TR>
                ))}
                {data && data.items.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-muted">
                      No findings found.
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
            {data && (
              <Pagination page={data.page} pages={data.pages} total={data.total} onPage={setPage} />
            )}
          </>
        )}
      </Card>

      {/* Create / edit modal */}
      <Modal
        open={!!editing}
        onClose={() => setEditing(null)}
        title={editing?.id ? "Edit Finding" : "New Finding"}
        wide
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditing(null)}>
              Cancel
            </Button>
            <Button onClick={save} loading={saving}>
              Save
            </Button>
          </>
        }
      >
        {editing && (
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <Label>Title</Label>
              <Input
                value={editing.title || ""}
                onChange={(e) => setEditing({ ...editing, title: e.target.value })}
                placeholder="e.g. Firewall Disabled"
              />
            </div>
            <div className="col-span-2">
              <Label>Description</Label>
              <Textarea
                rows={3}
                value={editing.description || ""}
                onChange={(e) => setEditing({ ...editing, description: e.target.value })}
              />
            </div>
            <div>
              <Label>Severity</Label>
              <Select
                value={editing.severity}
                onChange={(e) => setEditing({ ...editing, severity: e.target.value })}
              >
                {SEVERITIES.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Status</Label>
              <Select
                value={editing.status}
                onChange={(e) => setEditing({ ...editing, status: e.target.value })}
              >
                {FINDING_STATUSES.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Asset</Label>
              <Select
                value={editing.asset_id ?? ""}
                onChange={(e) =>
                  setEditing({
                    ...editing,
                    asset_id: e.target.value ? Number(e.target.value) : null,
                  })
                }
              >
                <option value="">— none —</option>
                {assets.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Source</Label>
              <Input
                value={editing.source || ""}
                onChange={(e) => setEditing({ ...editing, source: e.target.value })}
                placeholder="Nessus, Manual Review..."
              />
            </div>
            <div>
              <Label>CVE</Label>
              <Input
                value={editing.cve || ""}
                onChange={(e) => setEditing({ ...editing, cve: e.target.value })}
                placeholder="CVE-2023-0286"
              />
            </div>
            <div className="col-span-2">
              <Label>Evidence</Label>
              <Textarea
                rows={2}
                value={editing.evidence || ""}
                onChange={(e) => setEditing({ ...editing, evidence: e.target.value })}
              />
            </div>
          </div>
        )}
      </Modal>

      {/* Detail modal */}
      <Modal
        open={!!detail}
        onClose={() => setDetail(null)}
        title={detail?.title || "Finding"}
        wide
        footer={
          canWrite && detail ? (
            <>
              <Button variant="secondary" onClick={() => remap(detail)} loading={busy}>
                <Network className="h-4 w-4" /> Re-map
              </Button>
              <Button onClick={() => analyze(detail)} loading={busy}>
                <Sparkles className="h-4 w-4" /> AI Analyze
              </Button>
            </>
          ) : undefined
        }
      >
        {detail && (
          <div className="space-y-5">
            <div className="flex flex-wrap gap-2">
              <Badge className={classForSeverity(detail.severity)}>{detail.severity}</Badge>
              <Badge className={classForStatus(detail.status)}>{detail.status}</Badge>
              {detail.cve && (
                <Badge className="border-primary/30 bg-primary/10 text-primary">{detail.cve}</Badge>
              )}
              {detail.asset_name && (
                <Badge className="border-border bg-surface-2 text-muted">{detail.asset_name}</Badge>
              )}
            </div>

            {detail.description && (
              <p className="text-sm text-muted">{detail.description}</p>
            )}

            <div>
              <h4 className="mb-2 text-sm font-semibold text-foreground">
                Mapped NIST 800-53 Controls
              </h4>
              {detail.mapped_controls.length === 0 ? (
                <p className="text-sm text-muted">No controls mapped yet.</p>
              ) : (
                <div className="space-y-2">
                  {detail.mapped_controls.map((m) => (
                    <div
                      key={m.control.id}
                      className="rounded-lg border border-border bg-surface-2 p-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-primary">
                          {m.control.control_id} — {m.control.title}
                        </span>
                        <Badge className="border-primary/30 bg-primary/10 text-primary">
                          {m.confidence}% · {m.method}
                        </Badge>
                      </div>
                      <p className="mt-1 text-xs text-muted">{m.rationale}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-foreground">
                <Sparkles className="h-4 w-4 text-primary" /> AI Security Analyst
              </h4>
              {detail.ai_analysis ? (
                <div className="space-y-3">
                  <AISection label="Executive Summary" text={detail.ai_analysis.executive_summary} />
                  <AISection label="Business Impact" text={detail.ai_analysis.business_impact} />
                  <AISection
                    label="Technical Explanation"
                    text={detail.ai_analysis.technical_explanation}
                  />
                  <AISection
                    label="Recommended Remediation"
                    text={detail.ai_analysis.recommended_remediation}
                  />
                </div>
              ) : (
                <p className="text-sm text-muted">
                  No AI analysis yet. Click &quot;AI Analyze&quot; to generate.
                </p>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

function AISection({ label, text }: { label: string; text?: string | null }) {
  if (!text) return null;
  return (
    <div className="rounded-lg border border-border bg-surface-2 p-3">
      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-primary">{label}</p>
      <p className="text-sm text-foreground">{text}</p>
    </div>
  );
}
