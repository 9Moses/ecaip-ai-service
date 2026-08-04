"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

export interface DocumentRow {
  id: string;
  file_name: string;
  document_type: string;
  status: "uploaded" | "processing" | "extracted" | "failed";
  extraction_method: string | null;
  page_count: number | null;
  error_message: string | null;
  created_at: string;
}

export interface DocumentExtraction {
  id: string;
  status: string;
  raw_text: string | null;
  extraction_method: string | null;
  page_count: number | null;
}

const IN_PROGRESS_STATUSES = new Set(["uploaded", "processing"]);

async function fetchDocuments(): Promise<DocumentRow[]> {
  const { data } = await apiClient.get<DocumentRow[]>("/api/v1/documents");
  return data;
}

export function useDocuments() {
  return useQuery({
    queryKey: ["documents"],
    queryFn: fetchDocuments,
    // Poll while ANY document is still processing — stop polling once everything settles
    refetchInterval: (query) => {
      const docs = query.state.data as DocumentRow[] | undefined;
      const stillProcessing = docs?.some((d) =>
        IN_PROGRESS_STATUSES.has(d.status)
      );
      return stillProcessing ? 2000 : false;
    },
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.post<DocumentRow>(
        "/api/v1/documents",
        formData,
        {
          headers: { "Content-Type": "multipart/form-data" },
        }
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useDocumentExtraction(documentId: string | null) {
  return useQuery({
    queryKey: ["documents", documentId, "extraction"],
    queryFn: async () => {
      const { data } = await apiClient.get<DocumentExtraction>(
        `/api/v1/documents/${documentId}/extraction`
      );
      return data;
    },
    enabled: !!documentId,
    refetchInterval: (query) => {
      const status = (query.state.data as DocumentExtraction | undefined)
        ?.status;
      return status === "uploaded" || status === "processing" ? 2000 : false;
    },
  });
}
