import Link from "next/link";
import { Badge } from "@/components/ui/badge";

export function TopNav() {
  return (
    <header className="flex items-center justify-between border-b px-6 py-4">
      <div className="flex items-center gap-2">
        <span className="text-lg font-semibold">EACIP</span>
        <Badge variant="secondary">MVP</Badge>
      </div>
      <nav className="text-muted-foreground flex items-center gap-4 text-sm">
        <Link href="/" className="hover:text-foreground">
          Home
        </Link>
        <Link href="/documents" className="hover:text-foreground">
          Documents
        </Link>
        <Link href="/chat" className="hover:text-foreground">
          Chat
        </Link>
      </nav>
    </header>
  );
}
