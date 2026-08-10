import { SourceCitations } from "@/components/chat/source-citations";
import type { ChatSource } from "@/lib/chat/stream-chat-message";

export function MessageBubble({
  role,
  content,
  sources,
  isStreaming,
}: {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  isStreaming?: boolean;
}) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2.5 text-sm ${
          isUser ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-900"
        }`}
      >
        <p className="whitespace-pre-wrap">
          {content}
          {isStreaming && (
            <span className="ml-0.5 inline-block animate-pulse">▍</span>
          )}
        </p>
        {!isUser && sources && <SourceCitations sources={sources} />}
      </div>
    </div>
  );
}
