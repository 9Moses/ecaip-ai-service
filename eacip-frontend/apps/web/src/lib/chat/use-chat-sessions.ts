"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type {
  ChartDataEntry,
  ChatSource,
} from "@/lib/chat/stream-chat-message";

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: ChatSource[];
  chart_data: ChartDataEntry[];
  created_at: string;
}

export function useChatSessions() {
  return useQuery({
    queryKey: ["chat", "sessions"],
    queryFn: async () => {
      const { data } = await apiClient.get<ChatSession[]>(
        "/api/v1/chat/sessions"
      );
      return data;
    },
  });
}

export function useCreateChatSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post<ChatSession>(
        "/api/v1/chat/sessions"
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] });
    },
  });
}

export function useChatMessages(sessionId: string | null) {
  return useQuery({
    queryKey: ["chat", "sessions", sessionId, "messages"],
    queryFn: async () => {
      const { data } = await apiClient.get<ChatMessage[]>(
        `/api/v1/chat/sessions/${sessionId}/messages`
      );
      return data;
    },
    enabled: !!sessionId,
  });
}
