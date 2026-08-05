import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import type { InconsistencyFinding } from "@/lib/documents/use-ai-extraction";

const SEVERITY_VARIANT: Record<string, "default" | "destructive"> = {
  high: "destructive",
  medium: "destructive",
  low: "default",
};

export function InconsistencyList({
  findings,
}: {
  findings: InconsistencyFinding[];
}) {
  if (findings.length === 0) {
    return (
      <p className="text-muted-foreground text-sm">
        No inconsistencies detected.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {findings.map((finding, idx) => (
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
  );
}
