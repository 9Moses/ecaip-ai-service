"use client";

import { useParams } from "next/navigation";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { TopNav } from "@/components/layout/top-nav";
import { DocumentStatusBadge } from "@/components/documents/status-badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDocumentExtraction } from "@/lib/documents/use-documents";

function DocumentDetailContent() {
  const params = useParams<{ id: string }>();
  const { data: extraction, isLoading } = useDocumentExtraction(params.id);

  return (
    <>
      <TopNav />
      <main className="mx-auto max-w-3xl p-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Document Extraction</CardTitle>
            {extraction && <DocumentStatusBadge status={extraction.status} />}
          </CardHeader>
          <CardContent>
            {isLoading && (
              <p className="text-muted-foreground text-sm">Loading…</p>
            )}

            {extraction?.status === "uploaded" && (
              <p className="text-muted-foreground text-sm">
                Queued for processing — this page will update automatically.
              </p>
            )}

            {extraction?.status === "processing" && (
              <p className="text-muted-foreground text-sm">
                Extracting text — this usually takes a few seconds…
              </p>
            )}

            {extraction?.status === "failed" && (
              <Alert variant="destructive">
                <AlertTitle>Extraction failed</AlertTitle>
                <AlertDescription>
                  This document could not be processed. Try re-uploading it, or
                  check that it&apos;s a valid PDF/image file.
                </AlertDescription>
              </Alert>
            )}

            {extraction?.status === "extracted" && (
              <div className="flex flex-col gap-3">
                <p className="text-muted-foreground text-xs">
                  Method: {extraction.extraction_method} · Pages:{" "}
                  {extraction.page_count}
                </p>
                <pre className="max-h-[60vh] overflow-auto rounded-md bg-slate-50 p-4 text-sm whitespace-pre-wrap">
                  {extraction.raw_text ||
                    "(No text was found in this document.)"}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>
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
