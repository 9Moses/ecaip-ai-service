"use client";

import { useParams } from "next/navigation";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { TopNav } from "@/components/layout/top-nav";
import { DocumentStatusBadge } from "@/components/documents/status-badge";
import { EditableFieldsForm } from "@/components/documents/editable-fields-form";
import { InconsistencyList } from "@/components/documents/inconsistency-list";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useDocumentExtraction } from "@/lib/documents/use-documents";
import {
  useAIExtraction,
  useConfirmExtraction,
} from "@/lib/documents/use-ai-extraction";

function AIReviewSection({ documentId }: { documentId: string }) {
  const { data: aiExtraction, isLoading } = useAIExtraction(documentId);
  const { mutate: confirm, isPending: isConfirming } =
    useConfirmExtraction(documentId);

  if (isLoading || !aiExtraction) {
    return (
      <p className="text-muted-foreground text-sm">
        Waiting for AI extraction to start…
      </p>
    );
  }

  if (
    aiExtraction.status === "pending" ||
    aiExtraction.status === "processing"
  ) {
    return (
      <p className="text-muted-foreground text-sm">
        AI is extracting structured fields — this page updates automatically…
      </p>
    );
  }

  if (aiExtraction.status === "failed") {
    return (
      <Alert variant="destructive">
        <AlertTitle>AI extraction failed</AlertTitle>
        <AlertDescription>
          Structured extraction could not be completed for this document. The
          raw extracted text above is still available.
        </AlertDescription>
      </Alert>
    );
  }

  if (aiExtraction.status === "needs_review") {
    return (
      <Alert>
        <AlertTitle>Needs manual review</AlertTitle>
        <AlertDescription>
          The AI could not produce a confidently structured result for this
          document. Please review the raw extracted text above and enter key
          fields manually in your core system for now.
        </AlertDescription>
      </Alert>
    );
  }

  const isConfirmed = !!aiExtraction.confirmed_at;

  return (
    <div className="flex flex-col gap-6">
      {aiExtraction.summary && (
        <div>
          <h3 className="mb-1 text-sm font-semibold">AI Summary</h3>
          <p className="text-muted-foreground text-sm">
            {aiExtraction.summary}
          </p>
        </div>
      )}

      <Separator />

      <div>
        <h3 className="mb-2 text-sm font-semibold">Inconsistency Findings</h3>
        <InconsistencyList findings={aiExtraction.inconsistencies} />
      </div>

      <Separator />

      <div>
        <h3 className="mb-2 text-sm font-semibold">
          {isConfirmed
            ? "Confirmed Fields"
            : "Review & Confirm Extracted Fields"}
        </h3>
        {isConfirmed && (
          <p className="text-muted-foreground mb-3 text-xs">
            Confirmed {new Date(aiExtraction.confirmed_at!).toLocaleString()}
          </p>
        )}
        <EditableFieldsForm
          fields={aiExtraction.extracted_fields}
          onConfirm={(fields) => confirm(fields)}
          isConfirming={isConfirming}
        />
      </div>
    </div>
  );
}

function DocumentDetailContent() {
  const params = useParams<{ id: string }>();
  const { data: extraction, isLoading } = useDocumentExtraction(params.id);

  return (
    <>
      <TopNav />
      <main className="mx-auto flex max-w-3xl flex-col gap-6 p-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Raw Extracted Text</CardTitle>
            {extraction && <DocumentStatusBadge status={extraction.status} />}
          </CardHeader>
          <CardContent>
            {isLoading && (
              <p className="text-muted-foreground text-sm">Loading…</p>
            )}
            {extraction?.status === "extracted" && (
              <pre className="max-h-[40vh] overflow-auto rounded-md bg-slate-50 p-4 text-sm whitespace-pre-wrap">
                {extraction.raw_text || "(No text was found in this document.)"}
              </pre>
            )}
            {extraction && extraction.status !== "extracted" && (
              <p className="text-muted-foreground text-sm">
                Waiting for OCR/text extraction to complete…
              </p>
            )}
          </CardContent>
        </Card>

        {extraction?.status === "extracted" && (
          <Card>
            <CardHeader>
              <CardTitle>AI Document Intelligence</CardTitle>
            </CardHeader>
            <CardContent>
              <AIReviewSection documentId={params.id} />
            </CardContent>
          </Card>
        )}
      </main>
    </>
  );
}

export default function DocumentDetailPage() {
  return (
    <ProtectedRoute>
      <DocumentDetailContent />
    </ProtectedRoute>
  );
}
