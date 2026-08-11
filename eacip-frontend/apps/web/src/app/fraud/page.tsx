"use client";

import Link from "next/link";
import { useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { TopNav } from "@/components/layout/top-nav";
import { FraudScoreBadge } from "@/components/fraud/score-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useFraudFlags } from "@/lib/fraud/use-fraud-flags";

const STATUS_TABS = [
  { value: undefined, label: "All" },
  { value: "open", label: "Open" },
  { value: "under_review", label: "Under Review" },
  { value: "cleared", label: "Cleared" },
  { value: "confirmed_fraud", label: "Confirmed Fraud" },
] as const;

function FraudQueueContent() {
  const [activeStatus, setActiveStatus] = useState<string | undefined>("open");
  const { data: flags, isLoading } = useFraudFlags(activeStatus);

  return (
    <>
      <TopNav />
      <main className="mx-auto max-w-3xl p-6">
        <Card>
          <CardHeader>
            <CardTitle>Fraud Review Queue</CardTitle>
            <div className="flex gap-2 pt-2">
              {STATUS_TABS.map((tab) => (
                <Button
                  key={tab.label}
                  size="sm"
                  variant={activeStatus === tab.value ? "default" : "outline"}
                  onClick={() => setActiveStatus(tab.value)}
                >
                  {tab.label}
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent>
            {isLoading && (
              <p className="text-muted-foreground text-sm">Loading…</p>
            )}
            {flags?.length === 0 && (
              <p className="text-muted-foreground text-sm">
                No flags in this view.
              </p>
            )}
            <div className="flex flex-col divide-y">
              {flags?.map((flag) => (
                <Link
                  key={flag.id}
                  href={`/fraud/${flag.id}`}
                  className="flex items-center justify-between py-3 hover:bg-slate-50"
                >
                  <div>
                    <p className="text-sm font-medium">
                      {flag.claim_reference ?? "Unlinked claim"}
                    </p>
                    <p className="text-muted-foreground mt-0.5 line-clamp-1 text-xs">
                      {flag.rationale}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">
                      {flag.status.replace("_", " ")}
                    </Badge>
                    <FraudScoreBadge score={flag.score} />
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      </main>
    </>
  );
}

export default function FraudQueuePage() {
  return (
    <ProtectedRoute
      allowedRoles={["Fraud Analyst", "Claims Manager", "Admin", "Super Admin"]}
    >
      <FraudQueueContent />
    </ProtectedRoute>
  );
}
