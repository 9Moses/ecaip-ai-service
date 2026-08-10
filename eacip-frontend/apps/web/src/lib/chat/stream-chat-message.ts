import { env } from "@/lib/env";
import { getAccessToken } from "../auth/token-storages";

export type ChatStreamEvent =
  | { type: "notice"; content: string }
  | { type: "delta"; content: string }
  | { type: "done"; sources: ChatSource[] };

export interface ChatSource {
  document_id: string;
  chunk_index: number;
  relevance_score: number;
}

export async function streamChatMessage(
  sessionId: string,
  content: string,
  onEvent: (event: ChatStreamEvent) => void
): Promise<void> {
  const token = getAccessToken();

  const response = await fetch(
    `${env.NEXT_PUBLIC_API_BASE_URL}/api/v1/chat/sessions/${sessionId}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: token ? `Bearer ${token}` : "",
      },
      body: JSON.stringify({ content }),
    }
  );

  if (!response.ok || !response.body) {
    throw new Error(`Chat request failed: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE events are separated by a blank line ("\n\n")
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? ""; // keep the last, possibly-incomplete event in the buffer

    for (const rawEvent of events) {
      const line = rawEvent.trim();
      if (!line.startsWith("data:")) continue;
      const jsonStr = line.slice("data:".length).trim();
      try {
        const parsed = JSON.parse(jsonStr) as ChatStreamEvent;
        onEvent(parsed);
      } catch {
        // Malformed/partial event — skip rather than crash the whole stream
        continue;
      }
    }
  }
}
