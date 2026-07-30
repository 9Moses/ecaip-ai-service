import { Badge } from "@/components/ui/badge";

export function TopNav() {
  return (
    <header className="flex items-center justify-between border-b px-6 py-4">
      <div className="flex items-center gap-2">
        <span className="text-lg font-semibold">EACIP</span>
        <Badge variant="secondary">MVP</Badge>
      </div>
      <nav className="text-muted-foreground text-sm">
        Claims Intelligence Platform
      </nav>
    </header>
  );
}
