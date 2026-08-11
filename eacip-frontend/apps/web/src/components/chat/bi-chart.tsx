"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import type { ChartDataEntry } from "@/lib/chat/stream-chat-message";

const BAR_COLORS = ["#0f172a", "#64748b", "#94a3b8"];

function toRechartsData(
  entry: ChartDataEntry
): Record<string, string | number>[] {
  const [labelCol, ...valueCols] = entry.columns;
  return entry.rows.map((row) => {
    const record: Record<string, string | number> = {
      [labelCol]: String(row[0]),
    };
    valueCols.forEach((col, idx) => {
      const value = row[idx + 1];
      record[col] = typeof value === "number" ? value : Number(value) || 0;
    });
    return record;
  });
}

export function BIChart({ entry }: { entry: ChartDataEntry }) {
  const data = toRechartsData(entry);
  const [labelCol, ...valueCols] = entry.columns;

  return (
    <div className="mt-3 rounded-lg border bg-white p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-medium text-slate-600">
          {entry.source_label}
        </p>
        {entry.is_mock_data && (
          <Badge variant="secondary" className="text-xs">
            Sample data
          </Badge>
        )}
        {entry.dashboard_url && !entry.is_mock_data && (
          <a
            href={entry.dashboard_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mb-2 inline-block text-xs text-blue-600 underline"
          >
            Open full dashboard →
          </a>
        )}
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey={labelCol} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {valueCols.map((col, idx) => (
            <Bar
              key={col}
              dataKey={col}
              fill={BAR_COLORS[idx % BAR_COLORS.length]}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
