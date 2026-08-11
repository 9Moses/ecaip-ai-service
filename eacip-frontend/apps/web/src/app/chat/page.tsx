"use client";

import { useEffect, useRef, useState } from "react";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { TopNav } from "@/components/layout/top-nav";
import { MessageBubble } from "@/components/chat/message-bubble";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  useChatMessages,
  useChatSessions,
  useCreateChatSession,
} from "@/lib/chat/use-chat-sessions";
import {
  streamChatMessage,
  type ChartDataEntry,
  type ChatSource,
} from "@/lib/chat/stream-chat-message";
import { useQueryClient } from "@tanstack/react-query";

function ChatContent() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [streamingText, setStreamingText] = useState("");
  const [streamingNotice, setStreamingNotice] = useState<string | null>(null);
  const [streamingChartData, setStreamingChartData] = useState<ChartDataEntry[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const queryClient = useQueryClient();
  const { data: sessions } = useChatSessions();
  const { mutateAsync: createSession } = useCreateChatSession();
  const { data: messages } = useChatMessages(activeSessionId);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  async function handleNewChat() {
    const session = await createSession();
    setActiveSessionId(session.id);
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!inputValue.trim()) return;

    let sessionId = activeSessionId;
    if (!sessionId) {
      const session = await createSession();
      sessionId = session.id;
      setActiveSessionId(sessionId);
    }

    const question = inputValue;
    setInputValue("");
    setIsStreaming(true);
    setStreamingText("");
    setStreamingNotice(null);

    // Optimistically show the user's message immediately by refetching after send completes;
    // for the live view, we track it locally via streamingText/notice until the stream ends.
    let finalSources: ChatSource[] = [];

    try {
      await streamChatMessage(sessionId, question, (event) => {
        if (event.type === "notice") setStreamingNotice(event.content);
        if (event.type === "delta")
          setStreamingText((prev) => prev + event.content);
        if (event.type === "done") {
          finalSources = event.sources;
          setStreamingChartData(event.chart_data);
        }
      });
    } finally {
      setIsStreaming(false);
      setStreamingText("");
      setStreamingNotice(null);
      setStreamingChartData([]);
      // The backend has now persisted both messages — refetch to get the canonical version
      queryClient.invalidateQueries({
        queryKey: ["chat", "sessions", sessionId, "messages"],
      });
      queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
    }
  }

  return (
    <>
      <TopNav />
      <main className="flex h-[calc(100vh-73px)]">
        <aside className="w-64 shrink-0 border-r p-4">
          <Button
            onClick={handleNewChat}
            className="mb-4 w-full"
            variant="outline"
          >
            + New chat
          </Button>
          <div className="flex flex-col gap-1">
            {sessions?.map((session) => (
              <button
                key={session.id}
                onClick={() => setActiveSessionId(session.id)}
                className={`truncate rounded-md px-3 py-2 text-left text-sm hover:bg-slate-100 ${
                  activeSessionId === session.id
                    ? "bg-slate-100 font-medium"
                    : ""
                }`}
              >
                {session.title}
              </button>
            ))}
          </div>
        </aside>

        <section className="flex flex-1 flex-col">
          <div className="flex-1 overflow-y-auto p-6">
            {!activeSessionId && !messages?.length && (
              <p className="text-muted-foreground text-center text-sm">
                Start a new chat or ask about your uploaded documents.
              </p>
            )}
            <div className="flex flex-col gap-4">
              {messages?.map((message) => (
                <MessageBubble
                  key={message.id}
                  role={message.role}
                  content={message.content}
                  sources={message.sources}
                  chartData={message.chart_data}
                />
              ))}
              {isStreaming && (
                <>
                  {streamingNotice && (
                    <p className="text-muted-foreground text-center text-xs italic">
                      {streamingNotice}
                    </p>
                  )}
                  <MessageBubble
                    role="assistant"
                    content={streamingText}
                    chartData={streamingChartData}
                    isStreaming
                  />
                </>
              )}
            </div>
            <div ref={scrollRef} />
          </div>

          <form onSubmit={handleSend} className="flex gap-2 border-t p-4">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about your uploaded documents…"
              disabled={isStreaming}
            />
            <Button type="submit" disabled={isStreaming || !inputValue.trim()}>
              Send
            </Button>
          </form>
        </section>
      </main>
    </>
  );
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <ChatContent />
    </ProtectedRoute>
  );
}
