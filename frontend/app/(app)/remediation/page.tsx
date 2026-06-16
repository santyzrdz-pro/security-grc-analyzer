"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Calendar, User } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { Remediation } from "@/lib/types";
import { useAuth } from "@/lib/auth";
import { useToast } from "@/components/ui/toast";
import { PageHeader } from "@/components/page-header";
import {
  Badge,
  Button,
  Input,
  Label,
  Select,
  Spinner,
  Textarea,
} from "@/components/ui/primitives";
import { Modal } from "@/components/ui/modal";
import { classForSeverity } from "@/lib/utils";
import { REMEDIATION_STATUSES, SEVERITIES } from "@/lib/constants";

const COLUMNS = [
  { key: "Not Started", color: "border-danger/40" },
  { key: "In Progress", color: "border-warning/40" },
  { key: "Blocked", color: "border-critical/40" },
  { key: "Completed", color: "border-success/40" },
];

const EMPTY: Partial<Remediation> = {
  task: "",
  description: "",
  owner: "",
  status: "Not Started",
  priority: "Medium",
  due_date: null,
};

export default function RemediationPage() {
  const { can } = useAuth();
  const { toast } = useToast();
  const canWrite = can("remediation:write");

  const [items, setItems] = useState<Remediation[] | null>(null);
  const [editing, setEditing] = useState<Partial<Remediation> | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setItems(await api.get<Remediation[]>("/remediations"));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function move(item: Remediation, status: string) {
    setItems((prev) =>
      prev ? prev.map((i) => (i.id === item.id ? { ...i, status } : i)) : prev
    );
    try {
      await api.patch(`/remediations/${item.id}`, { status });
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Update failed", "error");
      load();
    }
  }

  async function save() {
    if (!editing?.task) {
      toast("Task is required", "error");
      return;
    }
    setSaving(true);
    const payload = {
      task: editing.task,
      description: editing.description,
      owner: editing.owner,
      status: editing.status,
      priority: editing.priority,
      due_date: editing.due_date || null,
    };
    try {
      if (editing.id) {
        await api.patch(`/remediations/${editing.id}`, payload);
        toast("Task updated");
      } else {
        await api.post("/remediations", payload);
        toast("Task created");
      }
      setEditing(null);
      load();
    } catch (e) {
      toast(e instanceof ApiError ? e.message : "Save failed", "error");
    } finally {
      setSaving(false);
    }
  }

  if (!items) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Remediation Tracking"
        description="Kanban board for managing remediation tasks across their lifecycle."
        action={
          canWrite && (
            <Button onClick={() => setEditing({ ...EMPTY })}>
              <Plus className="h-4 w-4" /> New Task
            </Button>
          )
        }
      />

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {COLUMNS.map((col) => {
          const colItems = items.filter((i) => i.status === col.key);
          return (
            <div key={col.key} className="rounded-xl border border-border bg-surface/50">
              <div className="flex items-center justify-between border-b border-border px-4 py-3">
                <h3 className="text-sm font-semibold text-foreground">{col.key}</h3>
                <Badge className="border-border bg-surface-2 text-muted">{colItems.length}</Badge>
              </div>
              <div className="space-y-3 p-3">
                {colItems.map((item) => (
                  <div
                    key={item.id}
                    className={`rounded-lg border-l-4 ${col.color} border border-border bg-surface p-3`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p
                        className="text-sm font-medium text-foreground"
                        onClick={() => canWrite && setEditing({ ...item })}
                        role={canWrite ? "button" : undefined}
                      >
                        {item.task}
                      </p>
                      <Badge className={classForSeverity(item.priority)}>{item.priority}</Badge>
                    </div>
                    {item.description && (
                      <p className="mt-1 line-clamp-2 text-xs text-muted">{item.description}</p>
                    )}
                    <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-muted">
                      {item.owner && (
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3" /> {item.owner}
                        </span>
                      )}
                      {item.due_date && (
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" /> {item.due_date}
                        </span>
                      )}
                    </div>
                    {canWrite && (
                      <Select
                        className="mt-2 py-1 text-xs"
                        value={item.status}
                        onChange={(e) => move(item, e.target.value)}
                      >
                        {REMEDIATION_STATUSES.map((s) => (
                          <option key={s}>{s}</option>
                        ))}
                      </Select>
                    )}
                  </div>
                ))}
                {colItems.length === 0 && (
                  <p className="py-6 text-center text-xs text-muted">No tasks</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <Modal
        open={!!editing}
        onClose={() => setEditing(null)}
        title={editing?.id ? "Edit Task" : "New Task"}
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
              <Label>Task</Label>
              <Input
                value={editing.task || ""}
                onChange={(e) => setEditing({ ...editing, task: e.target.value })}
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
              <Label>Owner</Label>
              <Input
                value={editing.owner || ""}
                onChange={(e) => setEditing({ ...editing, owner: e.target.value })}
              />
            </div>
            <div>
              <Label>Priority</Label>
              <Select
                value={editing.priority}
                onChange={(e) => setEditing({ ...editing, priority: e.target.value })}
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
                {REMEDIATION_STATUSES.map((s) => (
                  <option key={s}>{s}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label>Due Date</Label>
              <Input
                type="date"
                value={editing.due_date || ""}
                onChange={(e) => setEditing({ ...editing, due_date: e.target.value })}
              />
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
