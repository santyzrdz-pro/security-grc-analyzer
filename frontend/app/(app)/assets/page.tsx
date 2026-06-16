"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Search, Pencil, Trash2 } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { Asset, Page } from "@/lib/types";
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
} from "@/components/ui/primitives";
import { Modal } from "@/components/ui/modal";
import { Table, THead, TH, TR, TD, Pagination } from "@/components/ui/table";
import { classForSeverity, classForStatus } from "@/lib/utils";
import {
  ASSET_STATUSES,
  ASSET_TYPES,
  CRITICALITIES,
  ENVIRONMENTS,
} from "@/lib/constants";

const EMPTY: Partial<Asset> = {
  name: "",
  owner: "",
  business_unit: "",
  asset_type: "Server",
  criticality: "Medium",
  operating_system: "",
  ip_address: "",
  environment: "Production",
  status: "Active",
};

export default function AssetsPage() {
  const { can } = useAuth();
  const { toast } = useToast();
  const canWrite = can("asset:write");

  const [data, setData] = useState<Page<Asset> | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [type, setType] = useState("");
  const [criticality, setCriticality] = useState("");
  const [page, setPage] = useState(1);

  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Partial<Asset> | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), page_size: "10" });
    if (search) params.set("search", search);
    if (type) params.set("asset_type", type);
    if (criticality) params.set("criticality", criticality);
    try {
      setData(await api.get<Page<Asset>>(`/assets?${params.toString()}`));
    } finally {
      setLoading(false);
    }
  }, [page, search, type, criticality]);

  useEffect(() => {
    load();
  }, [load]);

  function openCreate() {
    setEditing({ ...EMPTY });
    setModalOpen(true);
  }
  function openEdit(a: Asset) {
    setEditing({ ...a });
    setModalOpen(true);
  }

  async function save() {
    if (!editing?.name) {
      toast("Name is required", "error");
      return;
    }
    setSaving(true);
    try {
      if (editing.id) {
        await api.patch(`/assets/${editing.id}`, editing);
        toast("Asset updated");
      } else {
        await api.post("/assets", editing);
        toast("Asset created");
      }
      setModalOpen(false);
      load();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Save failed", "error");
    } finally {
      setSaving(false);
    }
  }

  async function remove(a: Asset) {
    if (!confirm(`Delete asset "${a.name}"?`)) return;
    try {
      await api.del(`/assets/${a.id}`);
      toast("Asset deleted");
      load();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Delete failed", "error");
    }
  }

  return (
    <div>
      <PageHeader
        title="Asset Inventory"
        description="Manage the assets in scope for security and compliance monitoring."
        action={
          canWrite && (
            <Button onClick={openCreate}>
              <Plus className="h-4 w-4" /> Add Asset
            </Button>
          )
        }
      />

      <Card className="mb-4">
        <div className="flex flex-wrap items-center gap-3 p-4">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted" />
            <Input
              className="pl-9"
              placeholder="Search by name, owner, IP..."
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
            />
          </div>
          <Select
            className="w-44"
            value={type}
            onChange={(e) => {
              setPage(1);
              setType(e.target.value);
            }}
          >
            <option value="">All Types</option>
            {ASSET_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </Select>
          <Select
            className="w-40"
            value={criticality}
            onChange={(e) => {
              setPage(1);
              setCriticality(e.target.value);
            }}
          >
            <option value="">All Criticality</option>
            {CRITICALITIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
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
                  <TH>Name</TH>
                  <TH>Type</TH>
                  <TH>Owner</TH>
                  <TH>Business Unit</TH>
                  <TH>Criticality</TH>
                  <TH>Environment</TH>
                  <TH>Status</TH>
                  {canWrite && <TH className="text-right">Actions</TH>}
                </tr>
              </THead>
              <tbody>
                {data?.items.map((a) => (
                  <TR key={a.id}>
                    <TD className="font-medium">
                      {a.name}
                      {a.ip_address && (
                        <span className="block text-xs text-muted">{a.ip_address}</span>
                      )}
                    </TD>
                    <TD>{a.asset_type}</TD>
                    <TD className="text-muted">{a.owner || "-"}</TD>
                    <TD className="text-muted">{a.business_unit || "-"}</TD>
                    <TD>
                      <Badge className={classForSeverity(a.criticality)}>{a.criticality}</Badge>
                    </TD>
                    <TD className="text-muted">{a.environment}</TD>
                    <TD>
                      <Badge className={classForStatus(a.status)}>{a.status}</Badge>
                    </TD>
                    {canWrite && (
                      <TD className="text-right">
                        <div className="flex justify-end gap-1">
                          <button
                            onClick={() => openEdit(a)}
                            className="rounded-md p-1.5 text-muted hover:bg-surface-2 hover:text-primary"
                          >
                            <Pencil className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => remove(a)}
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
                      No assets found.
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
            {data && (
              <Pagination
                page={data.page}
                pages={data.pages}
                total={data.total}
                onPage={setPage}
              />
            )}
          </>
        )}
      </Card>

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing?.id ? "Edit Asset" : "New Asset"}
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>
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
              <Label>Asset Name</Label>
              <Input
                value={editing.name || ""}
                onChange={(e) => setEditing({ ...editing, name: e.target.value })}
              />
            </div>
            <div>
              <Label>Owner</Label>
              <Input
                value={editing.owner || ""}
                onChange={(e) => setEditing({ ...editing, owner: e.target.value })}
              />
            </div>
            <div>
              <Label>Business Unit</Label>
              <Input
                value={editing.business_unit || ""}
                onChange={(e) => setEditing({ ...editing, business_unit: e.target.value })}
              />
            </div>
            <div>
              <Label>Asset Type</Label>
              <Select
                value={editing.asset_type}
                onChange={(e) => setEditing({ ...editing, asset_type: e.target.value })}
              >
                {ASSET_TYPES.map((t) => (
                  <option key={t}>{t}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Criticality</Label>
              <Select
                value={editing.criticality}
                onChange={(e) => setEditing({ ...editing, criticality: e.target.value })}
              >
                {CRITICALITIES.map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Operating System</Label>
              <Input
                value={editing.operating_system || ""}
                onChange={(e) =>
                  setEditing({ ...editing, operating_system: e.target.value })
                }
              />
            </div>
            <div>
              <Label>IP Address</Label>
              <Input
                value={editing.ip_address || ""}
                onChange={(e) => setEditing({ ...editing, ip_address: e.target.value })}
              />
            </div>
            <div>
              <Label>Environment</Label>
              <Select
                value={editing.environment}
                onChange={(e) => setEditing({ ...editing, environment: e.target.value })}
              >
                {ENVIRONMENTS.map((env) => (
                  <option key={env}>{env}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Status</Label>
              <Select
                value={editing.status}
                onChange={(e) => setEditing({ ...editing, status: e.target.value })}
              >
                {ASSET_STATUSES.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </Select>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
