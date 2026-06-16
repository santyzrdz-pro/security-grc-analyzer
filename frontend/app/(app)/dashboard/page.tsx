"use client";

import { useEffect, useState } from "react";
import {
  Server,
  Bug,
  AlertTriangle,
  ShieldAlert,
  Gauge,
  Flame,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import type { DashboardResponse } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { StatCard } from "@/components/stat-card";
import { Card, CardHeader, Spinner } from "@/components/ui/primitives";

const SEVERITY_COLORS: Record<string, string> = {
  Critical: "#dc2626",
  High: "#ef4444",
  Medium: "#f59e0b",
  Low: "#22c55e",
};
const PIE_COLORS = ["#22c55e", "#f59e0b", "#ef4444", "#dc2626", "#3b82f6"];

const chartAxis = { stroke: "#64748b", fontSize: 12 };
const tooltipStyle = {
  backgroundColor: "#1e293b",
  border: "1px solid #334155",
  borderRadius: 8,
  color: "#f8fafc",
};

export default function DashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);

  useEffect(() => {
    api.get<DashboardResponse>("/dashboard").then(setData).catch(() => setData(null));
  }, []);

  if (!data) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  const { stats } = data;

  return (
    <div>
      <PageHeader
        title="Executive Dashboard"
        description="Real-time security posture, risk, and compliance overview."
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
        <StatCard label="Total Assets" value={stats.total_assets} icon={Server} accent="primary" />
        <StatCard label="Open Findings" value={stats.open_findings} icon={Bug} accent="warning" />
        <StatCard
          label="Critical Findings"
          value={stats.critical_findings}
          icon={Flame}
          accent="critical"
        />
        <StatCard label="Total Risks" value={stats.total_risks} icon={AlertTriangle} accent="danger" />
        <StatCard label="High Risks" value={stats.high_risks} icon={ShieldAlert} accent="danger" />
        <StatCard
          label="Compliance"
          value={`${stats.compliance_score}%`}
          icon={Gauge}
          accent="success"
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Findings by Severity" subtitle="Distribution across all findings" />
          <div className="h-72 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.findings_by_severity}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" {...chartAxis} />
                <YAxis allowDecimals={false} {...chartAxis} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#ffffff08" }} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {data.findings_by_severity.map((entry) => (
                    <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] || "#3b82f6"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader title="Risk Distribution" subtitle="Risk register by level" />
          <div className="h-72 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.risk_distribution}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label
                >
                  {data.risk_distribution.map((entry) => (
                    <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] || "#3b82f6"} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader title="Controls by Family" subtitle="NIST 800-53 coverage" />
          <div className="h-72 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.controls_by_family}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" {...chartAxis} />
                <YAxis allowDecimals={false} {...chartAxis} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#ffffff08" }} />
                <Bar dataKey="value" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader title="Remediation Progress" subtitle="Tasks by status" />
          <div className="h-72 p-4">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.remediation_progress}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={90}
                >
                  {data.remediation_progress.map((entry, i) => (
                    <Cell key={entry.name} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
                <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader title="Monthly Findings Trend" subtitle="New findings detected over the last 6 months" />
        <div className="h-72 p-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.monthly_findings_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="month" {...chartAxis} />
              <YAxis allowDecimals={false} {...chartAxis} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#3b82f6"
                strokeWidth={2.5}
                dot={{ r: 4, fill: "#3b82f6" }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}
