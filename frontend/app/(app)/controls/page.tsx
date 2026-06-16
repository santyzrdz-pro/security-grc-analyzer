"use client";

import { useCallback, useEffect, useState } from "react";
import { Search } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { Control, Page } from "@/lib/types";
import { useAuth } from "@/lib/auth";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/page-header";
import { Badge, Card, Input, Select, Spinner } from "@/components/ui/primitives";
import { Table, THead, TH, TR, TD, Pagination } from "@/components/ui/table";
import { classForStatus } from "@/lib/utils";
import { CONTROL_FAMILIES, CONTROL_STATUSES } from "@/lib/constants";

export default function ControlsPage() {
  const { can } = useAuth();
  const { toast } = useToast();
  const canWrite = can("control:write");

  const [data, setData] = useState<Page<Control> | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [family, setFamily] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), page_size: "15" });
    if (search) params.set("search", search);
    if (family) params.set("family", family);
    if (status) params.set("implementation_status", status);
    try {
      setData(await api.get<Page<Control>>(`/controls?${params.toString()}`));
    } finally {
      setLoading(false);
    }
  }, [page, search, family, status]);

  useEffect(() => {
    load();
  }, [load]);

  async function updateStatus(c: Control, value: string) {
    try {
      await api.patch(`/controls/${c.id}`, { implementation_status: value });
      toast(`${c.control_id} set to ${value}`);
      load();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Update failed", "error");
    }
  }

  return (
    <div>
      <PageHeader
        title="NIST 800-53 Control Library"
        description="Reference catalog of security controls and their implementation status."
      />

      <Card className="mb-4">
        <div className="flex flex-wrap items-center gap-3 p-4">
          <div className="relative flex-1 min-w-[220px]">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted" />
            <Input
              className="pl-9"
              placeholder="Search control ID, title, description..."
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
            />
          </div>
          <Select
            className="w-36"
            value={family}
            onChange={(e) => {
              setPage(1);
              setFamily(e.target.value);
            }}
          >
            <option value="">All Families</option>
            {CONTROL_FAMILIES.map((f) => (
              <option key={f}>{f}</option>
            ))}
          </Select>
          <Select
            className="w-52"
            value={status}
            onChange={(e) => {
              setPage(1);
              setStatus(e.target.value);
            }}
          >
            <option value="">All Statuses</option>
            {CONTROL_STATUSES.map((s) => (
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
                  <TH>Control</TH>
                  <TH>Family</TH>
                  <TH>Title</TH>
                  <TH className="w-[28%]">Description</TH>
                  <TH>Status</TH>
                </tr>
              </THead>
              <tbody>
                {data?.items.map((c) => (
                  <TR key={c.id}>
                    <TD className="font-semibold text-primary">{c.control_id}</TD>
                    <TD className="text-muted">
                      {c.family}
                      <span className="block text-xs">{c.family_name}</span>
                    </TD>
                    <TD className="font-medium">{c.title}</TD>
                    <TD className="text-xs text-muted">{c.description}</TD>
                    <TD>
                      {canWrite ? (
                        <Select
                          className="w-48"
                          value={c.implementation_status}
                          onChange={(e) => updateStatus(c, e.target.value)}
                        >
                          {CONTROL_STATUSES.map((s) => (
                            <option key={s}>{s}</option>
                          ))}
                        </Select>
                      ) : (
                        <Badge className={classForStatus(c.implementation_status)}>
                          {c.implementation_status}
                        </Badge>
                      )}
                    </TD>
                  </TR>
                ))}
              </tbody>
            </Table>
            {data && (
              <Pagination page={data.page} pages={data.pages} total={data.total} onPage={setPage} />
            )}
          </>
        )}
      </Card>
    </div>
  );
}
