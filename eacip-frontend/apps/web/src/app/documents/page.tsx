"use client";

import Link from "next/link";

import { ProtectedRoute } from "@/components/auth/protected-route";
import { TopNav } from "@/components/layout/top-nav";
import { DocumentStatusBadge } from "@/components/documents/status-badge";
import { UploadDropzone } from "@/components/documents/upload-dropzone";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDocuments } from "@/lib/documents/use-documents";

function DocumentsContent() {
  const { data: documents, isLoading } = useDocuments();

  return (
    <>
      <TopNav />
      <main className="mx-auto max-w-3xl p-6">
        <div className="flex flex-col gap-6">
          <UploadDropzone />

          <Card>
            <CardHeader>
              <CardTitle>Your Documents</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading && (
                <p className="text-muted-foreground text-sm">Loading…</p>
              )}
              {documents?.length === 0 && (
                <p className="text-muted-foreground text-sm">
                  No documents uploaded yet.
                </p>
              )}
              <div className="flex flex-col divide-y">
                {documents?.map((doc) => (
                  <Link
                    key={doc.id}
                    href={`/documents/${doc.id}`}
                    className="flex items-center justify-between py-3 hover:bg-slate-50"
                  >
                    <div>
                      <p className="text-sm font-medium">{doc.file_name}</p>
                      <p className="text-muted-foreground text-xs">
                        {doc.document_type} ·{" "}
                        {new Date(doc.created_at).toLocaleString()}
                      </p>
                    </div>
                    <DocumentStatusBadge status={doc.status} />
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </>
  );
}

export default function DocumentsPage() {
  return (
    <ProtectedRoute>
      <DocumentsContent />
    </ProtectedRoute>
  );
}
