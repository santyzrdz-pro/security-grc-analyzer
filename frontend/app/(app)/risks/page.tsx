"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Search, Wand2, Pencil, Trash2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { Asset, Page, Risk } from "@/lib/types";
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
import { classForSeverity } from "@/lib/utils";
import { RISK_LEVELS } from "@/lib/constants";

const EMPTY: Partial<Risk> = {
  title: "",
  description: "",
  likelihood: 3,
  impact: 3,
  mitigation_plan: "",
  owner: "",
  asset_id: null,
};

const SCALE = [1, 2, 3, 4, 5];

export default function RisksPage() {
  const { can } = useAuth();
  const { toast } = useToast();
  const canWrite = can("risk:write");

  const [data, setData] = useState<Page<Risk> | null>(null);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [level, setLevel] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<Partial<Risk> | null>(null);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), page_size: "10" });
    if (search) params.set("search", search);
    if (level) params.set("risk_level", level);
    try {
      setData(await api.get<Page<Risk>>(`/risks?${params.toString()}`));
    } finally {
      setLoading(false);
    }
  }, [page, search, level]);

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
      likelihood: Number(editing.likelihood),
      impact: Number(editing.impact),
      mitigation_plan: editing.mitigation_plan,
      owner: editing.owner,
      asset_id: editing.asset_id || null,
    };
    try {
      if (editing.id) {
        await api.patch(`/risks/${editing.id}`, payload);
        toast("Risk updated");
      } else {
        await api.post("/risks", payload);
        toast("Risk created");
      }
      setEditing(null);
      load();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Save failed", "error");
    } finally {
      setSaving(false);
    }
  }

  async function generate() {
    setGenerating(true);
    try {
      const res = await api.post<{ created: number; skipped: number }>(
        "/risks/generate-from-findings"
      );
      toast(`Generated ${res.created} risk(s), skipped ${res.skipped}`, "success");
      load();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Generation failed", "error");
    } finally {
      setGenerating(false);
    }
  }

  async function remove(r: Risk) {
    if (!confirm(`Delete risk "${r.title}"?`)) return;
    try {
      await api.del(`/risks/${r.id}`);
      toast("Risk deleted");
      load();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Delete failed", "error");
    }
  }

  const score = Number(editing?.likelihood || 0) * Number(editing?.impact || 0);

  return (
    <div>
      <PageHeader
        title="Risk Register"
        description="Risk Score = Likelihood × Impact (1–5 scale). Auto-generate risks from open findings."
        action={
          canWrite && (
            <div className="flex gap-2">
              <Button variant="secondary" onClick={generate} loading={generating}>
                <Wand2 className="h-4 w-4" /> Generate from Findings
              </Button>
              <Button onClick={() => setEditing({ ...EMPTY })}>
                <Plus className="h-4 w-4" /> New Risk
              </Button>
            </div>
          )
        }
      />

      <Card className="mb-4">
        <div className="flex flex-wrap items-center gap-3 p-4">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted" />
            <Input
              className="pl-9"
              placeholder="Search risks..."
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
            />
          </div>
          <Select
            className="w-40"
            value={level}
            onChange={(e) => {
              setPage(1);
              setLevel(e.target.value);
            }}
          >
            <option value="">All Levels</option>
            {RISK_LEVELS.map((l) => (
              <option key={l}>{l}</option>
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
                  <TH>Risk</TH>
                  <TH>Asset</TH>
                  <TH>Likelihood</TH>
                  <TH>Impact</TH>
                  <TH>Score</TH>
                  <TH>Level</TH>
                  <TH>Owner</TH>
                  {canWrite && <TH className="text-right">Actions</TH>}
                </tr>
              </THead>
              <tbody>
                {data?.items.map((r) => (
                  <TR key={r.id}>
                    <TD className="font-medium">{r.title}</TD>
                    <TD className="text-muted">{r.asset_name || "-"}</TD>
                    <TD>{r.likelihood}</TD>
                    <TD>{r.impact}</TD>
                    <TD className="font-semibold">{r.risk_score}</TD>
                    <TD>
                      <Badge className={classForSeverity(r.risk_level)}>{r.risk_level}</Badge>
                    </TD>
                    <TD className="text-muted">{r.owner || "-"}</TD>
                    {canWrite && (
                      <TD className="text-right">
                        <div className="flex justify-end gap-1">
                          <button
                            onClick={() => setEditing({ ...r })}
                            className="rounded-md p-1.5 text-muted hover:bg-surface-2 hover:text-primary"
                          >
                            <Pencil className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => remove(r)}
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
                    <td colSpan={8} className="py-12 text-center text-muted">
                      No risks yet. Use &quot;Generate from Findings&quot; to populate the register.
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

      <Modal
        open={!!editing}
        onClose={() => setEditing(null)}
        title={editing?.id ? "Edit Risk" : "New Risk"}
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
              />
            </div>
            <div className="col-span-2">
              <Label>Description</Label>
              <Textarea
                rows={2}
                value={editing.description || ""}
                onChange={(e) => setEditing({ ...editing, description: e.target.value })}
              />
            </div>
            <div>
              <Label>Likelihood (1–5)</Label>
              <Select
                value={editing.likelihood}
                onChange={(e) => setEditing({ ...editing, likelihood: Number(e.target.value) })}
              >
                {SCALE.map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Impact (1–5)</Label>
              <Select
                value={editing.impact}
                onChange={(e) => setEditing({ ...editing, impact: Number(e.target.value) })}
              >
                {SCALE.map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </Select>
            </div>
            <div className="col-span-2 rounded-lg border border-border bg-surface-2 p-3 text-sm">
              Calculated Risk Score:{" "}
              <span className="font-bold text-foreground">{score}</span>{" "}
              <span className="text-muted">(Likelihood × Impact)</span>
            </div>
            <div>
              <Label>Owner</Label>
              <Input
                value={editing.owner || ""}
                onChange={(e) => setEditing({ ...editing, owner: e.target.value })}
              />
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
            <div className="col-span-2">
              <Label>Mitigation Plan</Label>
              <Textarea
                rows={2}
                value={editing.mitigation_plan || ""}
                onChange={(e) => setEditing({ ...editing, mitigation_plan: e.target.value })}
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
