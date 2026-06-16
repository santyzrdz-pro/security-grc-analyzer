"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";
import type { ComplianceResponse } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { Card, CardHeader, Spinner } from "@/components/ui/primitives";
import { gradeColor } from "@/lib/utils";

const tooltipStyle = {
  backgroundColor: "#1e293b",
  border: "1px solid #334155",
  borderRadius: 8,
  color: "#f8fafc",
};

export default function CompliancePage() {
  const [data, setData] = useState<ComplianceResponse | null>(null);

  useEffect(() => {
    api.get<ComplianceResponse>("/compliance").then(setData).catch(() => setData(null));
  }, []);

  if (!data) {
    return (
      <div className="flex h-96 items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  const pct = data.compliance_percentage;
  const gaugeColor = pct >= 80 ? "#22c55e" : pct >= 60 ? "#f59e0b" : "#ef4444";
  const gaugeData = [{ name: "Compliance", value: pct, fill: gaugeColor }];

  const breakdown = [
    { name: "Implemented", value: data.implemented_controls, color: "#22c55e" },
    { name: "Partial", value: data.partially_implemented, color: "#f59e0b" },
    { name: "Not Implemented", value: data.not_implemented, color: "#ef4444" },
    { name: "Not Applicable", value: data.not_applicable, color: "#64748b" },
  ];

  return (
    <div>
      <PageHeader
        title="Compliance Scoring"
        description="Compliance Score = Implemented Controls / Total Applicable Controls."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader title="Overall Compliance" subtitle="Weighted control implementation" />
          <div className="relative flex h-72 items-center justify-center p-4">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart
                innerRadius="70%"
                outerRadius="100%"
                data={gaugeData}
                startAngle={90}
                endAngle={-270}
              >
                <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                <RadialBar background dataKey="value" cornerRadius={20} />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="absolute flex flex-col items-center">
              <span className="text-5xl font-bold text-foreground">{pct}%</span>
              <span className={`text-2xl font-bold ${gradeColor(data.grade)}`}>
                Grade {data.grade}
              </span>
            </div>
          </div>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader title="Control Implementation Status" subtitle="Across all controls" />
          <div className="grid grid-cols-2 gap-4 p-5 sm:grid-cols-4">
            {breakdown.map((b) => (
              <div key={b.name} className="rounded-lg border border-border bg-surface-2 p-4">
                <div className="mb-1 h-1.5 w-8 rounded-full" style={{ background: b.color }} />
                <p className="text-3xl font-bold text-foreground">{b.value}</p>
                <p className="text-xs text-muted">{b.name}</p>
              </div>
            ))}
          </div>
          <div className="px-5 pb-2 text-sm text-muted">
            {data.implemented_controls} of {data.total_controls} applicable controls fully
            implemented.
          </div>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader title="Compliance by Control Family" subtitle="Percent implemented per NIST family" />
        <div className="h-80 p-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.by_family}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
              <YAxis domain={[0, 100]} stroke="#64748b" fontSize={12} unit="%" />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#ffffff08" }} formatter={(v) => `${v}%`} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {data.by_family.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={entry.value >= 80 ? "#22c55e" : entry.value >= 60 ? "#f59e0b" : "#ef4444"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}
