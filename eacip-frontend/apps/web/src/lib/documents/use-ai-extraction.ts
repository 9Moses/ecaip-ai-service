"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

export interface InconsistencyFinding {
  source: "rule" | "llm";
  field: string;
  message: string;
  severity: "low" | "medium" | "high";
}

export interface AIExtraction {
  id: string;
  document_id: string;
  status: "pending" | "processing" | "completed" | "needs_review" | "failed";
  extracted_fields: Record<string, unknown>;
  summary: string | null;
  inconsistencies: InconsistencyFinding[];
  confirmed_by: string | null;
  confirmed_at: string | null;
}

const IN_PROGRESS_STATUSES = new Set(["pending", "processing"]);

export function useAIExtraction(documentId: string | null) {
  return useQuery({
    queryKey: ["documents", documentId, "ai-extraction"],
    queryFn: async () => {
      const { data } = await apiClient.get<AIExtraction>(
        `/api/v1/documents/${documentId}/ai-extraction`
      );
      return data;
    },
    enabled: !!documentId,
    retry: (failureCount, error: { response?: { status?: number } }) => {
      // A 404 here just means AI extraction hasn't started yet — keep polling instead of giving up
      if (error?.response?.status === 404) return true;
      return failureCount < 2;
    },
    refetchInterval: (query) => {
      const data = query.state.data as AIExtraction | undefined;
      if (!data) return 2000; // still waiting on the first successful fetch (likely a 404 so far)
      return IN_PROGRESS_STATUSES.has(data.status) ? 2000 : false;
    },
  });
}

export function useConfirmExtraction(documentId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (extractedFields: Record<string, unknown>) => {
      const { data } = await apiClient.post<AIExtraction>(
        `/api/v1/documents/${documentId}/ai-extraction/confirm`,
        { extracted_fields: extractedFields }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["documents", documentId, "ai-extraction"],
      });
    },
  });
}
