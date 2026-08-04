import { Badge } from "@/components/ui/badge";

const STATUS_CONFIG: Record<
  string,
  { label: string; variant: "default" | "secondary" | "destructive" }
> = {
  uploaded: { label: "Uploaded", variant: "secondary" },
  processing: { label: "Processing…", variant: "secondary" },
  extracted: { label: "Extracted", variant: "default" },
  failed: { label: "Failed", variant: "destructive" },
};

export function DocumentStatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] ?? {
    label: status,
    variant: "secondary" as const,
  };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
