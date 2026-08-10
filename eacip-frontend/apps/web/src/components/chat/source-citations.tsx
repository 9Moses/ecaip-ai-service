import Link from "next/link";

import type { ChatSource } from "@/lib/chat/stream-chat-message";

export function SourceCitations({ sources }: { sources: ChatSource[] }) {
  if (sources.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {sources.map((source, idx) => (
        <Link
          key={`${source.document_id}-${source.chunk_index}`}
          href={`/documents/${source.document_id}`}
          className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-0.5 text-xs text-slate-600 hover:bg-slate-100"
        >
          Source {idx + 1} · {Math.round(source.relevance_score * 100)}% match
        </Link>
      ))}
    </div>
  );
}
