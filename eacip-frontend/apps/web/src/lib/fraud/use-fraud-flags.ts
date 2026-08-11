"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

export interface FraudEvidence {
  source: "rule" | "llm";
  field: string;
  message: string;
  severity: "low" | "medium" | "high";
}

export interface FraudFlag {
  id: string;
  document_id: string | null;
  claim_reference: string | null;
  score: number;
  rationale: string;
  evidence: FraudEvidence[];
  status: "open" | "under_review" | "cleared" | "confirmed_fraud";
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
}

export function useFraudFlags(statusFilter?: string) {
  return useQuery({
    queryKey: ["fraud", "flags", statusFilter ?? "all"],
    queryFn: async () => {
      const { data } = await apiClient.get<FraudFlag[]>("/api/v1/fraud/flags", {
        params: statusFilter ? { status_filter: statusFilter } : undefined,
      });
      return data;
    },
  });
}

export function useFraudFlag(flagId: string | null) {
  return useQuery({
    queryKey: ["fraud", "flags", flagId],
    queryFn: async () => {
      const { data } = await apiClient.get<FraudFlag>(
        `/api/v1/fraud/flags/${flagId}`
      );
      return data;
    },
    enabled: !!flagId,
  });
}

export function useUpdateFraudFlag(flagId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (updates: { status?: string; assigned_to?: string }) => {
      const { data } = await apiClient.patch<FraudFlag>(
        `/api/v1/fraud/flags/${flagId}`,
        updates
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fraud", "flags"] });
    },
  });
}
