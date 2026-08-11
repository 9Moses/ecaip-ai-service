import { Badge } from "@/components/ui/badge";

export function FraudScoreBadge({ score }: { score: number }) {
  const variant =
    score >= 0.7 ? "destructive" : score >= 0.4 ? "secondary" : "default";
  return <Badge variant={variant}>{Math.round(score * 100)}% risk</Badge>;
}
