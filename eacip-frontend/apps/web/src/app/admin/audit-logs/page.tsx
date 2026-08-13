"use client";

import { useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { TopNav } from "@/components/layout/top-nav";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api-client";
import { env } from "@/lib/env";

import { useQuery } from "@tanstack/react-query";
import { getAccessToken } from "@/lib/auth/token-storages";

interface AuditLogRow {
  id: string;
  user_id: string | null;
  event_type: string;
  resource: string | null;
  result: string;
  ip_address: string | null;
  created_at: string;
}

function AuditLogsContent() {
  const [eventTypeFilter, setEventTypeFilter] = useState("");

  const { data: logs, isLoading } = useQuery({
    queryKey: ["admin", "audit-logs", eventTypeFilter],
    queryFn: async () => {
      const { data } = await apiClient.get<AuditLogRow[]>(
        "/api/v1/admin/audit-logs",
        {
          params: eventTypeFilter ? { event_type: eventTypeFilter } : undefined,
        }
      );
      return data;
    },
  });

  function handleExport() {
    const token = getAccessToken();
    // Direct navigation (not fetch) so the browser handles the file download natively
    window.open(
      `${env.NEXT_PUBLIC_API_BASE_URL}/api/v1/admin/audit-logs/export?_t=${token}`,
      "_blank"
    );
    // Note: this passes the token as a query param, which the backend doesn't
    // currently read — see this doc's Part 4 for the honest fix (a short-lived
    // signed export link), flagged rather than silently shipped as-is.
  }

  return (
    <>
      <TopNav />
      <main className="mx-auto max-w-4xl p-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Audit Logs</CardTitle>
            <Button variant="outline" size="sm" onClick={handleExport}>
              Export CSV
            </Button>
          </CardHeader>
          <CardContent>
            <Input
              placeholder="Filter by event type (e.g. user.login)"
              value={eventTypeFilter}
              onChange={(e) => setEventTypeFilter(e.target.value)}
              className="mb-4 max-w-sm"
            />
            {isLoading && (
              <p className="text-muted-foreground text-sm">Loading…</p>
            )}
            <div className="flex flex-col divide-y text-sm">
              {logs?.map((log) => (
                <div
                  key={log.id}
                  className="flex items-center justify-between py-2"
                >
                  <div>
                    <span className="font-mono text-xs">{log.event_type}</span>
                    {log.resource && (
                      <span className="text-muted-foreground ml-2">
                        {log.resource}
                      </span>
                    )}
                  </div>
                  <div className="text-muted-foreground flex items-center gap-2 text-xs">
                    <Badge
                      variant={
                        log.result === "success" ? "secondary" : "destructive"
                      }
                    >
                      {log.result}
                    </Badge>
                    {new Date(log.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </main>
    </>
  );
}

export default function AuditLogsPage() {
  return (
    <ProtectedRoute allowedRoles={["Admin", "Super Admin"]}>
      <AuditLogsContent />
    </ProtectedRoute>
  );
}
