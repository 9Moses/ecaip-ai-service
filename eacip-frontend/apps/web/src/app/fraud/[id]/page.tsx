"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { TopNav } from "@/components/layout/top-nav";
import { FraudScoreBadge } from "@/components/fraud/score-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/lib/auth/use-auth";
import { useFraudFlag, useUpdateFraudFlag } from "@/lib/fraud/use-fraud-flags";

const SEVERITY_VARIANT: Record<string, "default" | "destructive"> = {
  high: "destructive",
  medium: "destructive",
  low: "default",
};

const STATUS_ACTIONS = [
  { status: "under_review", label: "Mark Under Review" },
  { status: "cleared", label: "Clear Flag" },
  { status: "confirmed_fraud", label: "Confirm Fraud" },
] as const;

function FraudFlagDetailContent() {
  const params = useParams<{ id: string }>();
  const { user } = useAuth();
  const { data: flag, isLoading } = useFraudFlag(params.id);
  const { mutate: updateFlag, isPending } = useUpdateFraudFlag(params.id);

  const canTakeAction =
    user?.role === "Fraud Analyst" ||
    user?.role === "Admin" ||
    user?.role === "Super Admin";

  if (isLoading || !flag) {
    return (
      <>
        <TopNav />
        <main className="mx-auto max-w-3xl p-6">
          <p className="text-muted-foreground text-sm">Loading…</p>
        </main>
      </>
    );
  }

  return (
    <>
      <TopNav />
      <main className="mx-auto max-w-3xl p-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>{flag.claim_reference ?? "Unlinked claim"}</CardTitle>
              <p className="text-muted-foreground mt-1 text-xs">
                Flagged {new Date(flag.created_at).toLocaleString()}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="secondary">{flag.status.replace("_", " ")}</Badge>
              <FraudScoreBadge score={flag.score} />
            </div>
          </CardHeader>
          <CardContent className="flex flex-col gap-6">
            {flag.document_id && (
              <Link
                href={`/documents/${flag.document_id}`}
                className="text-sm text-blue-600 underline"
              >
                View source document →
              </Link>
            )}

            <div>
              <h3 className="mb-1 text-sm font-semibold">Rationale</h3>
              <p className="text-muted-foreground text-sm">{flag.rationale}</p>
            </div>

            <Separator />

            <div>
              <h3 className="mb-2 text-sm font-semibold">
                Evidence ({flag.evidence.length})
              </h3>
              <div className="flex flex-col gap-2">
                {flag.evidence.map((finding, idx) => (
                  <Alert
                    key={idx}
                    variant={SEVERITY_VARIANT[finding.severity] ?? "default"}
                  >
                    <AlertTitle className="flex items-center gap-2 text-sm">
                      {finding.field}
                      <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs font-normal text-slate-700">
                        {finding.severity} · {finding.source}
                      </span>
                    </AlertTitle>
                    <AlertDescription className="text-sm">
                      {finding.message}
                    </AlertDescription>
                  </Alert>
                ))}
              </div>
            </div>

            {canTakeAction ? (
              <>
                <Separator />
                <div>
                  <h3 className="mb-2 text-sm font-semibold">Actions</h3>
                  <div className="flex gap-2">
                    {STATUS_ACTIONS.map((action) => (
                      <Button
                        key={action.status}
                        size="sm"
                        variant={
                          flag.status === action.status ? "default" : "outline"
                        }
                        disabled={isPending || flag.status === action.status}
                        onClick={() => updateFlag({ status: action.status })}
                      >
                        {action.label}
                      </Button>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <p className="text-muted-foreground text-xs">
                You have read-only access to this flag. Status changes require
                the Fraud Analyst or Admin role.
              </p>
            )}
          </CardContent>
        </Card>
      </main>
    </>
  );
}

export default function FraudFlagDetailPage() {
  return (
    <ProtectedRoute
      allowedRoles={["Fraud Analyst", "Claims Manager", "Admin", "Super Admin"]}
    >
      <FraudFlagDetailContent />
    </ProtectedRoute>
  );
}
